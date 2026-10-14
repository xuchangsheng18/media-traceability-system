import io
from typing import Any, cast
from uuid import UUID

from fastapi import Request
from sqlalchemy import text

from ..auth import AuthorityProvider
from ..contracts import validate_api
from ..db import Database
from ..errors import BusinessError
from ..objects import FileObjectStore
from ..types import Scope
from .repository import UploadRepository


class UploadService:
    def __init__(self, database: Database, repository: UploadRepository, store: FileObjectStore) -> None:
        self.database, self.repository, self.store = database, repository, store

    def scope(
        self, request: Request, action: str, *, case_id: UUID | None = None, upload_id: UUID | None = None
    ) -> Scope:
        authority = cast(AuthorityProvider | None, request.app.state.business_authority)
        if authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or not header[7:]:
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        actor = authority.authenticate(header[7:])
        source_id = None
        if upload_id is not None:
            with self.database.identity_transaction(actor) as connection:
                row = connection.execute(
                    text("SELECT case_id,source_id FROM mt.upload_session WHERE upload_id=:id"), {"id": upload_id}
                ).one_or_none()
                if row is None:
                    raise BusinessError("UPLOAD_NOT_FOUND", 404)
                case_id, source_id = row.case_id, row.source_id
        if case_id is None:
            raise BusinessError("INPUT_INVALID", 422)
        scope = authority.authorize_case(actor, case_id, action)
        if scope.actor != actor or scope.case_id != case_id:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if source_id is not None:
            authority.authorize_source(scope, source_id, "upload")
        return scope

    def create(self, request: Request, payload: dict[str, Any], key: str) -> dict[str, Any]:
        validate_api("UploadCreate", payload)
        scope = self.scope(request, "asset.upload", case_id=UUID(payload["case_id"]))
        authority = cast(AuthorityProvider, request.app.state.business_authority)
        authority.authorize_source(scope, UUID(payload["source_id"]), "upload")
        if payload["size_bytes"] > self.repository.settings.max_upload_bytes:
            raise BusinessError("UPLOAD_TOO_LARGE", 413)
        response = self.repository.create(scope, payload, idempotency_key=key)
        validate_api("UploadSession", response)
        return response

    def put_part(
        self, scope: Scope, upload_id: UUID, number: int, data: bytes, claimed_sha: str, key: str
    ) -> dict[str, Any]:
        replay = self.repository.existing_part(scope, upload_id, number, claimed_sha, len(data), key)
        if replay is not None:
            return replay
        stored = self.store.put_part(scope, upload_id, number, io.BytesIO(data))
        if stored.ref.sha256 != claimed_sha:
            raise BusinessError("UPLOAD_PART_DIGEST_INVALID", 422)
        try:
            response = self.repository.put_part(scope, upload_id, number, stored, idempotency_key=key)
        except Exception:
            self.store.record_orphan(stored, scope, upload_id)
            raise
        with self.database.transaction(scope) as connection:
            registered = connection.execute(
                text(
                    "SELECT object_id FROM mt.upload_part WHERE case_id=:case AND upload_id=:upload AND part_no=:number"
                ),
                {"case": scope.case_id, "upload": upload_id, "number": number},
            ).scalar_one_or_none()
        if registered != stored.ref.object_id:
            self.store.record_orphan(stored, scope, upload_id, "UNREFERENCED_CONCURRENT_DUPLICATE")
        validate_api("UploadPart", response)
        return response

    def complete(self, request: Request, upload_id: UUID, payload: dict[str, Any], key: str) -> dict[str, Any]:
        validate_api("UploadComplete", payload)
        scope = self.scope(request, "asset.upload", upload_id=upload_id)
        try:
            request_id = UUID(request.headers.get("X-Request-Id", ""))
        except ValueError:
            from uuid import uuid4

            request_id = uuid4()
        response = self.repository.complete(scope, upload_id, payload, key, request_id)
        validate_api("UploadResult", response)
        return response

    def status(self, request: Request, upload_id: UUID) -> dict[str, Any]:
        scope = self.scope(request, "asset.upload", upload_id=upload_id)
        response = self.repository.status(scope, upload_id)
        result = response["result"]
        if result is not None and result["duplicate_of"] is not None:
            with self.database.transaction(scope) as connection:
                source = connection.execute(
                    text("SELECT source_id FROM mt.media_asset WHERE case_id=:case AND asset_id=:asset"),
                    {"case": scope.case_id, "asset": UUID(result["duplicate_of"])},
                ).scalar_one_or_none()
            authority = cast(AuthorityProvider, request.app.state.business_authority)
            if source is None:
                result["duplicate_of"] = None
            else:
                try:
                    authority.authorize_source(scope, source, "upload")
                except BusinessError as error:
                    if error.http_status not in {403, 404}:
                        raise
                    result["duplicate_of"] = None
        validate_api("UploadStatus", response)
        return response
