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
            self.store.record_orphan(stored)
            raise
        validate_api("UploadPart", response)
        return response
