import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.tracing import safe_log
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from sqlalchemy import text

from ..auth import AuthorityProvider
from ..contracts import ROOT
from ..data_scope import ResourceBinding
from ..errors import BusinessError
from ..objects import StoredObject
from ..permissions.context import WorkPort, protected_work
from ..scope_context import current_data_scope
from ..scoped_objects import ScopedObjects
from ..types import Actor, ObjectRef, Scope
from .service import UploadService
from .validator import inspect_uploaded_media


class UploadValidationWorker:
    def __init__(
        self, service: UploadService, authority: AuthorityProvider | None, work_authorization: WorkPort | None = None
    ) -> None:
        self.service, self.authority, self.work_authorization = service, authority, work_authorization

    def consume_validation(self, event: dict[str, Any]) -> None:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        schema = json.loads((ROOT / "schemas/events/upload-validation.requested.v1.schema.json").read_text())
        try:
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(event)
        except ValidationError:
            raise BusinessError("UPLOAD_EVENT_INVALID", 422) from None
        safe_log("upload.validation.started", request_id=event["request_id"], upload_id=event["upload_id"])
        actor = Actor(UUID(event["actor_id"]), UUID(event["org_id"]))
        scope = self.authority.authorize_case(actor, UUID(event["case_id"]), "asset.upload")
        if scope.actor != actor or scope.case_id != UUID(event["case_id"]):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        upload = UUID(event["upload_id"])
        with protected_work(self.work_authorization, scope, "upload_validation", upload, "validateUploadWork"):
            self._consume_bound(event, scope, upload)

    def _consume_bound(self, event: dict[str, Any], scope: Scope, upload: UUID) -> None:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        actor = scope.actor
        repository = self.service.repository
        stored: StoredObject | None = None
        try:
            with repository.database.transaction(scope) as connection:
                recorded = connection.execute(
                    text(
                        "SELECT payload FROM mt.outbox_event WHERE case_id=:case AND event_id=:event AND aggregate_id=:upload"
                    ),
                    {"case": scope.case_id, "event": UUID(event["event_id"]), "upload": upload},
                ).scalar_one_or_none()
                if recorded != event:
                    raise BusinessError("UPLOAD_EVENT_BINDING_INVALID", 409)
                row = repository.session(scope, upload, connection)
                if row["owner_id"] != actor.user_id:
                    raise BusinessError("UPLOAD_EVENT_BINDING_INVALID", 409)
                if row["state"] in {"COMPLETED", "REJECTED", "EXPIRED"}:
                    return
                if row["state"] != "VALIDATING" or row["row_version"] != event["session_version"]:
                    raise BusinessError("UPLOAD_EVENT_STALE", 409)
                if row["expires_at"] <= datetime.now(timezone.utc):
                    connection.execute(
                        text(
                            "UPDATE mt.upload_session SET state='EXPIRED',row_version=row_version+1,updated_at=now() WHERE case_id=:case AND upload_id=:id"
                        ),
                        {"case": scope.case_id, "id": upload},
                    )
                    return
                self.authority.authorize_source(scope, row["source_id"], "upload")
                source_version = connection.execute(
                    text(
                        "SELECT authorization_version FROM mt.source_registry WHERE case_id=:case AND source_id=:source"
                    ),
                    {"case": scope.case_id, "source": row["source_id"]},
                ).scalar_one()
                if source_version != event["source_authorization_version"]:
                    raise BusinessError("SOURCE_AUTHORIZATION_VERSION_CHANGED", 409)
                parts = (
                    connection.execute(
                        text("""SELECT p.part_no,p.size_bytes,p.sha256,o.object_id,o.version_id FROM mt.upload_part p
                    JOIN mt.object_version o ON o.case_id=p.case_id AND o.object_id=p.object_id
                    WHERE p.case_id=:case AND p.upload_id=:upload ORDER BY p.part_no"""),
                        {"case": scope.case_id, "upload": upload},
                    )
                    .mappings()
                    .all()
                )
                data = bytearray()
                bytes_valid = True
                try:
                    for part in parts:
                        ref = ObjectRef(part["object_id"], part["version_id"], part["sha256"])
                        for block in ScopedObjects(self.service.store, self.authority).read(
                            connection,
                            current_data_scope(),
                            ResourceBinding("upload_part", upload, part_no=int(part["part_no"])),
                            ref,
                        ):
                            if len(data) + len(block) > int(row["size_bytes"]):
                                bytes_valid = False
                                break
                            data.extend(block)
                        if not bytes_valid:
                            break
                except (RuntimeError, FileNotFoundError, ValueError):
                    bytes_valid = False
                if not bytes_valid:
                    connection.execute(
                        text(
                            "UPDATE mt.upload_session SET state='REJECTED',row_version=row_version+1,updated_at=now() WHERE case_id=:case AND upload_id=:id"
                        ),
                        {"case": scope.case_id, "id": upload},
                    )
                    return
                metadata = (
                    inspect_uploaded_media(bytes(data), row["sha256"], row["mime"])
                    if len(data) == row["size_bytes"]
                    else None
                )
                self.authority.authorize_source(scope, row["source_id"], "upload")
                if metadata is None:
                    connection.execute(
                        text(
                            "UPDATE mt.upload_session SET state='REJECTED',row_version=row_version+1,updated_at=now() WHERE case_id=:case AND upload_id=:id"
                        ),
                        {"case": scope.case_id, "id": upload},
                    )
                    return
                stored = ScopedObjects(self.service.store, self.authority).put(
                    repository.database, scope, ResourceBinding("upload", upload), io.BytesIO(data)
                )
                asset, content = uuid4(), uuid4()
                # Distinct upload rows do not serialize the same content. Hold
                # this case-scoped lock through publication/commit, then query
                # in a separate statement so a waiting worker sees that commit.
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                    {"key": f"upload-sha256/{actor.org_id}/{scope.case_id}/{stored.ref.sha256}"},
                )
                duplicate = (
                    connection.execute(
                        text(
                            "SELECT asset_id,source_id FROM mt.media_asset WHERE case_id=:case AND sha256=:sha AND state='VALID' ORDER BY created_at,asset_id LIMIT 1"
                        ),
                        {"case": scope.case_id, "sha": stored.ref.sha256},
                    )
                    .mappings()
                    .one_or_none()
                )
                duplicate_id = None
                if duplicate is not None:
                    try:
                        self.authority.authorize_source(scope, duplicate["source_id"], "upload")
                        duplicate_id = duplicate["asset_id"]
                    except BusinessError:
                        duplicate_id = None
                connection.execute(
                    text("""INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,size_bytes,created_by)
                    VALUES(:object,:org,:case,'private-development-files',:key,:version,:sha,:size,:actor)"""),
                    {
                        "object": stored.ref.object_id,
                        "org": actor.org_id,
                        "case": scope.case_id,
                        "key": str(stored.ref.object_id) + "/" + stored.ref.version_id,
                        "version": stored.ref.version_id,
                        "sha": stored.ref.sha256,
                        "size": stored.size_bytes,
                        "actor": actor.user_id,
                    },
                )
                connection.execute(
                    text("""INSERT INTO mt.content_item(content_id,org_id,case_id,source_id,discovered_at,title,status,created_by)
                    VALUES(:content,:org,:case,:source,now(),:filename,'REGISTERED',:actor)"""),
                    {
                        "content": content,
                        "org": actor.org_id,
                        "case": scope.case_id,
                        "source": row["source_id"],
                        "filename": row["filename"],
                        "actor": actor.user_id,
                    },
                )
                connection.execute(
                    text("""INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,width,height,kind,mapping_version,state,created_by)
                    VALUES(:asset,:org,:case,:content,:source,:object,:sha,:mime,:size,:width,:height,'original','upload-bytes/1','VALID',:actor)"""),
                    {
                        "asset": asset,
                        "org": actor.org_id,
                        "case": scope.case_id,
                        "content": content,
                        "source": row["source_id"],
                        "object": stored.ref.object_id,
                        "sha": stored.ref.sha256,
                        "mime": metadata["mime"],
                        "size": stored.size_bytes,
                        "width": metadata["width"],
                        "height": metadata["height"],
                        "actor": actor.user_id,
                    },
                )
                connection.execute(
                    text(
                        "UPDATE mt.upload_session SET state='COMPLETED',asset_id=:asset,duplicate_of=:duplicate,row_version=row_version+1,updated_at=now() WHERE case_id=:case AND upload_id=:id"
                    ),
                    {"asset": asset, "duplicate": duplicate_id, "case": scope.case_id, "id": upload},
                )
        except Exception:
            if stored is not None:
                self.service.store.record_orphan(stored, scope, upload)
            raise
