import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from ..db import Database
from ..errors import BusinessError
from ..objects import StoredObject
from ..settings import BusinessSettings
from ..types import Scope


class UploadRepository:
    def __init__(self, database: Database, settings: BusinessSettings) -> None:
        self.database, self.settings = database, settings

    def session(self, scope: Scope, upload_id: UUID, connection: Connection) -> dict[str, Any]:
        row = (
            connection.execute(
                text("SELECT * FROM mt.upload_session WHERE case_id=:case AND upload_id=:id FOR UPDATE"),
                {"case": scope.case_id, "id": upload_id},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise BusinessError("UPLOAD_NOT_FOUND", 404)
        return dict(row)

    def wire_session(self, row: dict[str, Any]) -> dict[str, Any]:
        state = row["state"]
        if state == "UPLOADING" and row["expires_at"] <= datetime.now(timezone.utc):
            state = "EXPIRED"
        return {
            "upload_id": str(row["upload_id"]),
            "part_size_bytes": int(row["part_size_bytes"]),
            "state": state,
            "expires_at": row["expires_at"].isoformat(),
            "version": int(row["row_version"]),
        }

    def replay(
        self, connection: Connection, scope: Scope, operation: str, key: str, digest: str
    ) -> dict[str, Any] | None:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key": f"{scope.case_id}/{scope.actor.user_id}/{operation}/{key}"},
        )
        row = (
            connection.execute(
                text(
                    "SELECT request_sha256,response_ref,expires_at FROM mt.idempotency_record WHERE case_id=:case AND actor_id=:actor AND operation=:op AND idempotency_key=:key"
                ),
                {"case": scope.case_id, "actor": scope.actor.user_id, "op": operation, "key": key},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if row["request_sha256"] != digest or row["expires_at"] <= datetime.now(timezone.utc):
            raise BusinessError("IDEMPOTENCY_CONFLICT", 409)
        return dict(row["response_ref"])

    def remember(
        self, connection: Connection, scope: Scope, operation: str, key: str, digest: str, response: dict[str, Any]
    ) -> None:
        connection.execute(
            text("""INSERT INTO mt.idempotency_record(idempotency_id,org_id,case_id,actor_id,operation,idempotency_key,request_sha256,response_ref,expires_at,created_by)
            VALUES(:id,:org,:case,:actor,:op,:key,:sha,CAST(:response AS jsonb),:expires,:actor)"""),
            {
                "id": uuid4(),
                "org": scope.actor.org_id,
                "case": scope.case_id,
                "actor": scope.actor.user_id,
                "op": operation,
                "key": key,
                "sha": digest,
                "response": json.dumps(response),
                "expires": datetime.now(timezone.utc) + timedelta(seconds=self.settings.upload_ttl_seconds),
            },
        )

    def create(self, scope: Scope, payload: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        with self.database.transaction(scope) as connection:
            replay = self.replay(connection, scope, "createUpload", idempotency_key, digest)
            if replay is not None:
                return replay
            parameters = dict(
                payload,
                id=uuid4(),
                org=scope.actor.org_id,
                actor=scope.actor.user_id,
                part=self.settings.part_size_bytes,
                expires=datetime.now(timezone.utc) + timedelta(seconds=self.settings.upload_ttl_seconds),
            )
            row = (
                connection.execute(
                    text("""INSERT INTO mt.upload_session(upload_id,org_id,case_id,source_id,filename,size_bytes,sha256,mime,part_size_bytes,state,expires_at,owner_id,created_by)
                VALUES(:id,:org,:case_id,:source_id,:filename,:size_bytes,:sha256,:mime,:part,'UPLOADING',:expires,:actor,:actor) RETURNING *"""),
                    parameters,
                )
                .mappings()
                .one()
            )
            response = self.wire_session(dict(row))
            self.remember(connection, scope, "createUpload", idempotency_key, digest, response)
            return response

    def assert_writable(self, row: dict[str, Any], scope: Scope) -> None:
        if row["expires_at"] <= datetime.now(timezone.utc):
            raise BusinessError("UPLOAD_EXPIRED", 410)
        if row["state"] != "UPLOADING" or row["owner_id"] != scope.actor.user_id:
            raise BusinessError("UPLOAD_STATE_CONFLICT", 409)

    def existing_part(
        self, scope: Scope, upload_id: UUID, number: int, sha256: str, size: int, key: str
    ) -> dict[str, Any] | None:
        signature = hashlib.sha256(f"{upload_id}/{number}/{sha256}/{size}".encode()).hexdigest()
        with self.database.transaction(scope) as connection:
            row = self.session(scope, upload_id, connection)
            self.assert_writable(row, scope)
            expected = min(
                int(row["part_size_bytes"]), int(row["size_bytes"]) - (number - 1) * int(row["part_size_bytes"])
            )
            if number < 1 or expected <= 0 or size != expected:
                raise BusinessError("UPLOAD_PART_SIZE_INVALID", 422)
            replay = self.replay(connection, scope, "putUploadPart", key, signature)
            if replay is not None:
                return replay
            old = (
                connection.execute(
                    text(
                        "SELECT sha256,size_bytes FROM mt.upload_part WHERE case_id=:case AND upload_id=:id AND part_no=:number"
                    ),
                    {"case": scope.case_id, "id": upload_id, "number": number},
                )
                .mappings()
                .one_or_none()
            )
            if old is None:
                return None
            if old["sha256"] != sha256 or old["size_bytes"] != size:
                raise BusinessError("UPLOAD_PART_CONFLICT", 409)
            response = {"part_no": number, "sha256": sha256, "size_bytes": size}
            self.remember(connection, scope, "putUploadPart", key, signature, response)
            return response

    def put_part(
        self, scope: Scope, upload_id: UUID, part_no: int, stored: StoredObject, *, idempotency_key: str
    ) -> dict[str, Any]:
        signature = hashlib.sha256(
            f"{upload_id}/{part_no}/{stored.ref.sha256}/{stored.size_bytes}".encode()
        ).hexdigest()
        with self.database.transaction(scope) as connection:
            row = self.session(scope, upload_id, connection)
            self.assert_writable(row, scope)
            replay = self.replay(connection, scope, "putUploadPart", idempotency_key, signature)
            if replay is not None:
                return replay
            expected = min(
                int(row["part_size_bytes"]), int(row["size_bytes"]) - (part_no - 1) * int(row["part_size_bytes"])
            )
            if part_no < 1 or expected <= 0 or stored.size_bytes != expected:
                raise BusinessError("UPLOAD_PART_SIZE_INVALID", 422)
            old = (
                connection.execute(
                    text(
                        "SELECT sha256,size_bytes FROM mt.upload_part WHERE case_id=:case AND upload_id=:id AND part_no=:number"
                    ),
                    {"case": scope.case_id, "id": upload_id, "number": part_no},
                )
                .mappings()
                .one_or_none()
            )
            response = {"part_no": part_no, "sha256": stored.ref.sha256, "size_bytes": stored.size_bytes}
            if old is not None:
                if old["sha256"] != stored.ref.sha256 or old["size_bytes"] != stored.size_bytes:
                    raise BusinessError("UPLOAD_PART_CONFLICT", 409)
            else:
                connection.execute(
                    text("""INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,size_bytes,created_by)
                    VALUES(:object,:org,:case,'private-development-files',:key,:version,:sha,:size,:actor)"""),
                    {
                        "object": stored.ref.object_id,
                        "org": scope.actor.org_id,
                        "case": scope.case_id,
                        "key": str(stored.ref.object_id) + "/" + stored.ref.version_id,
                        "version": stored.ref.version_id,
                        "sha": stored.ref.sha256,
                        "size": stored.size_bytes,
                        "actor": scope.actor.user_id,
                    },
                )
                connection.execute(
                    text("""INSERT INTO mt.upload_part(part_id,org_id,case_id,upload_id,part_no,sha256,size_bytes,object_id,created_by)
                    VALUES(:part,:org,:case,:id,:number,:sha,:size,:object,:actor)"""),
                    {
                        "part": uuid4(),
                        "org": scope.actor.org_id,
                        "case": scope.case_id,
                        "id": upload_id,
                        "number": part_no,
                        "sha": stored.ref.sha256,
                        "size": stored.size_bytes,
                        "object": stored.ref.object_id,
                        "actor": scope.actor.user_id,
                    },
                )
                connection.execute(
                    text(
                        "UPDATE mt.upload_session SET row_version=row_version+1,updated_at=now() WHERE upload_id=:id AND case_id=:case"
                    ),
                    {"id": upload_id, "case": scope.case_id},
                )
            self.remember(connection, scope, "putUploadPart", idempotency_key, signature, response)
            return response

    def status(self, scope: Scope, upload_id: UUID) -> dict[str, Any]:
        with self.database.transaction(scope) as connection:
            row = self.session(scope, upload_id, connection)
            totals = connection.execute(
                text(
                    "SELECT count(*),coalesce(sum(size_bytes),0) FROM mt.upload_part WHERE upload_id=:id AND case_id=:case"
                ),
                {"id": upload_id, "case": scope.case_id},
            ).one()
            session = self.wire_session(row)
            result = None
            if session["state"] in {"VALIDATING", "COMPLETED", "REJECTED"}:
                result = {
                    "upload_id": str(upload_id),
                    "asset_id": str(row["asset_id"]) if row["asset_id"] else None,
                    "validation": "VALID" if row["state"] == "COMPLETED" else row["state"],
                    "duplicate_of": str(row["duplicate_of"]) if row["duplicate_of"] else None,
                    "request_id": str(uuid4()),
                }
            return {
                "session": session,
                "result": result,
                "received_parts_count": int(totals[0]),
                "received_bytes": int(totals[1]),
                "total_size_bytes": int(row["size_bytes"]),
            }

    def complete(
        self, scope: Scope, upload_id: UUID, payload: dict[str, Any], key: str, request_id: UUID
    ) -> dict[str, Any]:
        signature = hashlib.sha256(
            json.dumps(
                dict(upload_id=str(upload_id), payload=payload), sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        with self.database.transaction(scope) as connection:
            row = self.session(scope, upload_id, connection)
            replay = self.replay(connection, scope, "completeUpload", key, signature)
            if replay is not None:
                return replay
            self.assert_writable(row, scope)
            parts = (
                connection.execute(
                    text(
                        "SELECT part_no,sha256,size_bytes FROM mt.upload_part WHERE case_id=:case AND upload_id=:id ORDER BY part_no"
                    ),
                    {"case": scope.case_id, "id": upload_id},
                )
                .mappings()
                .all()
            )
            actual = [dict(part) for part in parts]
            total = int(row["size_bytes"])
            expected_count = (total + int(row["part_size_bytes"]) - 1) // int(row["part_size_bytes"])
            if (
                payload["parts"] != actual
                or [part["part_no"] for part in actual] != list(range(1, expected_count + 1))
                or sum(part["size_bytes"] for part in actual) != total
            ):
                raise BusinessError("UPLOAD_PART_SET_INVALID", 422)
            source = connection.execute(
                text("SELECT authorization_version FROM mt.source_registry WHERE case_id=:case AND source_id=:source"),
                {"case": scope.case_id, "source": row["source_id"]},
            ).scalar_one()
            version = int(row["row_version"]) + 1
            event = {
                "schema_version": "1.0.0",
                "event_type": "upload.validation.requested.v1",
                "event_id": str(uuid4()),
                "org_id": str(scope.actor.org_id),
                "case_id": str(scope.case_id),
                "actor_id": str(scope.actor.user_id),
                "upload_id": str(upload_id),
                "request_id": str(request_id),
                "session_version": version,
                "source_authorization_version": str(source),
            }
            connection.execute(
                text(
                    "UPDATE mt.upload_session SET state='VALIDATING',row_version=:version,updated_at=now() WHERE upload_id=:id AND case_id=:case"
                ),
                {"version": version, "id": upload_id, "case": scope.case_id},
            )
            connection.execute(
                text("""INSERT INTO mt.outbox_event(event_id,org_id,case_id,topic,aggregate_id,aggregate_version,payload,created_by)
                VALUES(:event,:org,:case,'upload.validation.requested.v1',:upload,:version,CAST(:payload AS jsonb),:actor)"""),
                {
                    "event": UUID(str(event["event_id"])),
                    "org": scope.actor.org_id,
                    "case": scope.case_id,
                    "upload": upload_id,
                    "version": version,
                    "payload": json.dumps(event),
                    "actor": scope.actor.user_id,
                },
            )
            response = {
                "upload_id": str(upload_id),
                "asset_id": None,
                "validation": "VALIDATING",
                "duplicate_of": None,
                "request_id": str(request_id),
            }
            self.remember(connection, scope, "completeUpload", key, signature, response)
            return response

    def parts(self, scope: Scope, upload_id: UUID, cursor: str | None, limit: int) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise BusinessError("INPUT_INVALID", 422)
        with self.database.transaction(scope) as connection:
            session = self.session(scope, upload_id, connection)
            after = 0
            if cursor:
                try:
                    value, signature = cursor.split(".")
                    expected = hmac.new(
                        self.settings.cursor_secret.encode(), value.encode(), hashlib.sha256
                    ).hexdigest()
                    if not hmac.compare_digest(signature, expected):
                        raise ValueError()
                    binding = json.loads(base64.urlsafe_b64decode(value.encode()))
                    if binding["upload_id"] != str(upload_id) or binding["version"] != session["row_version"]:
                        raise BusinessError("UPLOAD_CURSOR_STALE", 409)
                    after = int(binding["after"])
                except (ValueError, KeyError, TypeError):
                    raise BusinessError("INPUT_INVALID", 422) from None
            rows = (
                connection.execute(
                    text(
                        "SELECT part_no,sha256,size_bytes FROM mt.upload_part WHERE case_id=:case AND upload_id=:id AND part_no>:after ORDER BY part_no LIMIT :limit"
                    ),
                    {"case": scope.case_id, "id": upload_id, "after": after, "limit": limit + 1},
                )
                .mappings()
                .all()
            )
            items = [dict(row) for row in rows[:limit]]
            following = None
            if len(rows) > limit:
                value = base64.urlsafe_b64encode(
                    json.dumps(
                        {
                            "upload_id": str(upload_id),
                            "version": int(session["row_version"]),
                            "after": items[-1]["part_no"],
                        },
                        separators=(",", ":"),
                    ).encode()
                ).decode()
                following = (
                    value
                    + "."
                    + hmac.new(self.settings.cursor_secret.encode(), value.encode(), hashlib.sha256).hexdigest()
                )
            return {"items": items, "next_cursor": following, "session_version": int(session["row_version"])}
