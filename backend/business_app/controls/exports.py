import hashlib
import io
import json
import re
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request
from fastapi.responses import Response
from sqlalchemy import Connection, text

from ..auth import AuthorityProvider
from ..db import Database
from ..errors import BusinessError
from ..objects import FileObjectStore, StoredObject
from ..permissions.context import WorkPort, protected_work
from ..types import ObjectRef, Scope
from ..uploads.repository import UploadRepository
from .approvals import Approvals
from .common import audit, canonical, etag, now, row
from .providers import ExportRule, RuleProvider


def audit_wire(item: dict[str, Any]) -> dict[str, Any]:
    # Only the allowlisted contract fields; details and credential-like free text are excluded.
    return (
        {
            key: str(item[key]) if item[key] is not None else None
            for key in ["event_id", "actor_id", "org_id", "case_id", "object_id", "request_id"]
        }
        | {key: item[key] for key in ["action", "object_type", "object_version", "outcome"]}
        | {"occurred_at": item["occurred_at"].isoformat()}
    )


class Exports:
    def __init__(
        self,
        database: Database,
        receipts: UploadRepository,
        approvals: Approvals,
        store: FileObjectStore,
        rules: RuleProvider | None,
        authority: AuthorityProvider | None,
        work_authorization: WorkPort | None = None,
    ) -> None:
        self.database, self.receipts, self.approvals, self.store, self.rules, self.authority = (
            database,
            receipts,
            approvals,
            store,
            rules,
            authority,
        )
        self.work_authorization = work_authorization

    def check(self, connection: Connection, scope: Scope, item: dict[str, Any]) -> ExportRule:
        if self.rules is None:
            raise BusinessError("EXPORT_RULE_UNAVAILABLE", 503)
        rule = self.rules.audit_export(scope, item["purpose"])
        if (
            min(rule.max_events, rule.max_bytes) <= 0
            or rule.expires_at <= now()
            or rule.start_at.tzinfo is None
            or rule.end_at.tzinfo is None
        ):
            raise BusinessError("EXPORT_RULE_INVALID", 503)
        if not rule.start_at <= item["start_at"] < item["end_at"] <= rule.end_at:
            raise BusinessError("EXPORT_WINDOW_UNAUTHORIZED", 403)
        approved = self.approvals.detail(connection, scope, UUID(str(item["approval_id"])))
        if (
            approved["approval"]["state"] != "APPROVED"
            or approved["approval"]["purpose"] != "report_export"
            or approved["approval"]["policy_version"] != rule.version
            or approved["binding"]["object_type"] != "operation"
            or approved["binding"]["object_id"] != str(scope.case_id)
        ):
            raise BusinessError("EXPORT_APPROVAL_INVALID", 403)
        if item.get("artifact_ref"):
            expires = datetime.fromisoformat(item["artifact_ref"]["expires_at"])
            if expires <= now() or item["artifact_ref"]["rule_version"] != rule.version:
                raise BusinessError("EXPORT_EXPIRED_OR_RULE_CHANGED", 410)
        return rule

    def create(self, scope: Scope, body: dict[str, Any], request: Request, key: str) -> dict[str, Any]:
        digest = hashlib.sha256(canonical(body)).hexdigest()
        params = dict(
            body,
            start_at=datetime.fromisoformat(body["start_at"].replace("Z", "+00:00")),
            end_at=datetime.fromisoformat(body["end_at"].replace("Z", "+00:00")),
        )
        with self.database.transaction(scope) as connection:
            self.check(connection, scope, params)
            old = self.receipts.replay(connection, scope, "exportAudit", key, digest)
            if old is not None:
                return old
            identifier = uuid4()
            connection.execute(
                text("""INSERT INTO mt.audit_export(export_id,org_id,case_id,approval_id,start_at,end_at,purpose,state,created_by)
                VALUES(:id,:org,:case,:approval_id,:start_at,:end_at,:purpose,'REQUESTED',:actor)"""),
                dict(params, id=identifier, org=scope.actor.org_id, case=scope.case_id, actor=scope.actor.user_id),
            )
            result = dict(
                object_id=str(identifier), version=1, state="REQUESTED", request_id=str(request.state.request_id)
            )
            self.receipts.remember(connection, scope, "exportAudit", key, digest, result)
            audit(connection, scope, "audit.export.request", "audit_export", identifier, 1, request)
            return result

    def process(self, scope: Scope, identifier: UUID) -> None:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        authorized = self.authority.authorize_case(scope.actor, scope.case_id, "audit.export")
        if authorized != scope:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        with protected_work(self.work_authorization, scope, "audit_export", identifier, "processAuditExportWork"):
            self._process_bound(scope, identifier)

    def _process_bound(self, scope: Scope, identifier: UUID) -> None:
        stored: StoredObject | None = None
        try:
            with self.database.transaction(scope) as connection:
                item = row(connection, "audit_export", "export_id", identifier, lock=True)
                rule = self.check(connection, scope, item)
                if item["state"] == "READY":
                    return
                if item["state"] != "REQUESTED":
                    raise BusinessError("EXPORT_STATE_CONFLICT", 409)
                values = (
                    connection.execute(
                        text(
                            "SELECT * FROM mt.audit_event WHERE case_id=:case AND occurred_at>=:start AND occurred_at<:end ORDER BY occurred_at,event_id LIMIT :limit"
                        ),
                        dict(case=scope.case_id, start=item["start_at"], end=item["end_at"], limit=rule.max_events + 1),
                    )
                    .mappings()
                    .all()
                )
                data = canonical(
                    dict(
                        schema_version="audit-export/1",
                        case_id=str(scope.case_id),
                        start_at=item["start_at"].isoformat(),
                        end_at=item["end_at"].isoformat(),
                        purpose=item["purpose"],
                        rule_version=rule.version,
                        events=[audit_wire(dict(v)) for v in values],
                    )
                )
                if len(values) > rule.max_events or len(data) > rule.max_bytes:
                    connection.execute(
                        text(
                            "UPDATE mt.audit_export SET state='FAILED',artifact_ref=CAST(:ref AS jsonb),row_version=row_version+1,updated_at=now() WHERE export_id=:id"
                        ),
                        dict(
                            id=identifier,
                            ref=json.dumps(
                                dict(
                                    error_code="EXPORT_LIMIT_EXCEEDED",
                                    expires_at=rule.expires_at.isoformat(),
                                    rule_version=rule.version,
                                )
                            ),
                        ),
                    )
                    return
                stored = self.store.put_part(scope, identifier, 1, io.BytesIO(data))
                ref = dict(
                    object_id=str(stored.ref.object_id),
                    version_id=stored.ref.version_id,
                    sha256=stored.ref.sha256,
                    size_bytes=stored.size_bytes,
                    expires_at=rule.expires_at.isoformat(),
                    rule_version=rule.version,
                )
                # Fixed version and receipt are committed together; retries take the row lock.
                self.check(connection, scope, item)
                connection.execute(
                    text(
                        "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,size_bytes,created_by) VALUES(:id,:org,:case,'private-development-files',:key,:version,:sha,:size,:actor)"
                    ),
                    dict(
                        id=stored.ref.object_id,
                        org=scope.actor.org_id,
                        case=scope.case_id,
                        key=str(stored.ref.object_id) + "/" + stored.ref.version_id,
                        version=stored.ref.version_id,
                        sha=stored.ref.sha256,
                        size=stored.size_bytes,
                        actor=scope.actor.user_id,
                    ),
                )
                connection.execute(
                    text(
                        "UPDATE mt.audit_export SET state='READY',artifact_ref=CAST(:ref AS jsonb),row_version=row_version+1,updated_at=now() WHERE export_id=:id"
                    ),
                    dict(id=identifier, ref=json.dumps(ref)),
                )
        except Exception:
            if stored is not None:
                self.store.record_orphan(stored, scope, reason="EXPORT_RECEIPT_NOT_COMMITTED")
            raise

    def status(self, scope: Scope, identifier: UUID) -> dict[str, Any]:
        with self.database.transaction(scope) as connection:
            item = row(connection, "audit_export", "export_id", identifier)
            self.check(connection, scope, item)
            ref = item["artifact_ref"]
            return dict(
                export_id=str(identifier),
                case_id=str(scope.case_id),
                state=item["state"],
                version=int(item["row_version"]),
                artifact={k: ref[k] for k in ["object_id", "version_id", "sha256"]}
                if item["state"] == "READY"
                else None,
                size_bytes=ref.get("size_bytes"),
                expires_at=ref.get("expires_at"),
                error_code=ref.get("error_code"),
            )

    def content(self, scope: Scope, identifier: UUID, request: Request) -> Response:
        with self.database.transaction(scope) as connection:
            item = row(connection, "audit_export", "export_id", identifier)
            rule = self.check(connection, scope, item)
            if item["state"] != "READY":
                raise BusinessError("EXPORT_NOT_READY", 409)
            ref = item["artifact_ref"]
            registered = connection.execute(
                text(
                    "SELECT size_bytes FROM mt.object_version WHERE case_id=:case AND object_id=:id AND version_id=:version AND sha256=:sha"
                ),
                dict(case=scope.case_id, id=UUID(ref["object_id"]), version=ref["version_id"], sha=ref["sha256"]),
            ).scalar_one_or_none()
            if registered is None or registered != ref["size_bytes"]:
                raise BusinessError("EXPORT_OBJECT_BINDING_INVALID", 503)
            try:
                if ref["size_bytes"] > rule.max_bytes:
                    raise BusinessError("EXPORT_LIMIT_EXCEEDED", 413)
                data = b"".join(self.store.read(ObjectRef(UUID(ref["object_id"]), ref["version_id"], ref["sha256"])))
                if len(data) != ref["size_bytes"]:
                    raise RuntimeError("SIZE_MISMATCH")
            except (OSError, RuntimeError, ValueError):
                raise BusinessError("EXPORT_OBJECT_UNAVAILABLE", 503) from None
            tag = etag([ref["object_id"], ref["version_id"], ref["sha256"]])
            headers = {
                "ETag": tag,
                "Accept-Ranges": "bytes",
                "Cache-Control": "private, no-store",
                "Content-Disposition": f'attachment; filename="audit-{identifier}.json"',
            }
            raw = request.headers.get("Range")
            if raw and request.headers.get("If-Range", tag) == tag:
                found = re.fullmatch(r"bytes=(\d*)-(\d*)", raw)
                if not found or not any(found.groups()):
                    raise BusinessError("RANGE_INVALID", 416)
                left, right = found.groups()
                if left:
                    start, end = int(left), min(int(right) if right else len(data) - 1, len(data) - 1)
                else:
                    suffix = int(right)
                    if suffix <= 0:
                        raise BusinessError("RANGE_INVALID", 416)
                    start, end = max(0, len(data) - suffix), len(data) - 1
                if start >= len(data) or end < start:
                    raise BusinessError("RANGE_INVALID", 416)
                headers["Content-Range"] = f"bytes {start}-{end}/{len(data)}"
                return Response(data[start : end + 1], status_code=206, media_type="application/json", headers=headers)
            return Response(data, media_type="application/json", headers=headers)
