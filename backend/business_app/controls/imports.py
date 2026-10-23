"""Import already registered, source-bound fixed objects; external downloads require a real adapter."""

import hashlib
from typing import Any, Protocol
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import text

from ..auth import AuthorityProvider
from ..data_scope import ResourceBinding
from ..db import Database
from ..errors import BusinessError
from ..objects import FileObjectStore
from ..scope_context import current_data_scope
from ..scoped_objects import ScopedObjects
from ..settings import BusinessSettings
from ..types import ObjectRef, Scope
from ..uploads.repository import UploadRepository
from .common import audit, canonical


class ThirdPartyAdapter(Protocol):
    """A deployment supplies its approved platform identity/signature/retry implementation.

    The adapter must register verified bytes through the normal ingestion boundary.
    A browser URL or client status is never accepted as an existing ObjectRef.
    """

    def register_batch(self, scope: Scope, cursor: str | None, limit: int) -> dict[str, Any]: ...


class Imports:
    def __init__(
        self,
        database: Database,
        receipts: UploadRepository,
        store: FileObjectStore,
        authority: AuthorityProvider | None,
        settings: BusinessSettings,
    ) -> None:
        self.database, self.receipts, self.store, self.authority, self.settings = (
            database,
            receipts,
            store,
            authority,
            settings,
        )

    def create(self, scope: Scope, body: dict[str, Any], request: Request, key: str) -> dict[str, Any]:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        limit = self.settings.max_import_entries
        if limit is None:
            raise BusinessError("IMPORT_BATCH_LIMIT_UNCONFIRMED", 503)
        if len(body["entries"]) > limit:
            raise BusinessError("IMPORT_BATCH_LIMIT_EXCEEDED", 413)
        digest = hashlib.sha256(canonical(body)).hexdigest()
        with self.database.transaction(scope) as connection:
            resolved = []
            for entry in body["entries"]:
                self.authority.authorize_source(scope, UUID(entry["source_id"]), "import")
                ref = entry["object_ref"]
                asset = (
                    connection.execute(
                        text("""SELECT a.asset_id,a.source_id,a.mime,a.size_bytes FROM mt.media_asset a
                    JOIN mt.object_version o ON o.case_id=a.case_id AND o.object_id=a.object_id
                    WHERE a.case_id=:case AND a.source_id=:source AND a.state='VALID' AND o.object_id=:id AND o.version_id=:version AND o.sha256=:sha"""),
                        dict(
                            case=scope.case_id,
                            source=UUID(entry["source_id"]),
                            id=UUID(ref["object_id"]),
                            version=ref["version_id"],
                            sha=ref["sha256"],
                        ),
                    )
                    .mappings()
                    .one_or_none()
                )
                if asset is None:
                    raise BusinessError("REGISTERED_PLATFORM_OBJECT_REQUIRED", 503)
                if asset["mime"] != entry["mime"]:
                    raise BusinessError("IMPORT_MIME_BINDING_INVALID", 422)
                try:
                    size = sum(
                        len(chunk)
                        for chunk in ScopedObjects(self.store, self.authority).read(
                            connection,
                            current_data_scope(),
                            ResourceBinding("media_input", asset["asset_id"]),
                            ObjectRef(UUID(ref["object_id"]), ref["version_id"], ref["sha256"]),
                        )
                    )
                except (OSError, ValueError, RuntimeError):
                    raise BusinessError("IMPORT_OBJECT_UNAVAILABLE", 503) from None
                if size != asset["size_bytes"]:
                    raise BusinessError("IMPORT_OBJECT_SIZE_INVALID", 503)
                resolved.append(dict(asset))
            old = self.receipts.replay(connection, scope, "createImport", key, digest)
            if old is not None:
                return dict(old["response"])
            identifier = uuid4()
            connection.execute(
                text(
                    "INSERT INTO mt.import_job(import_id,org_id,case_id,state,requested_count,created_by) VALUES(:id,:org,:case,'COMPLETED',:count,:actor)"
                ),
                dict(
                    id=identifier,
                    org=scope.actor.org_id,
                    case=scope.case_id,
                    count=len(resolved),
                    actor=scope.actor.user_id,
                ),
            )
            items = []
            for ordinal, resolved_asset in enumerate(resolved):
                connection.execute(
                    text(
                        "INSERT INTO mt.import_item(item_id,org_id,case_id,import_id,ordinal,source_id,asset_id,state,created_by) VALUES(:id,:org,:case,:import_id,:ordinal,:source,:asset,'accepted',:actor)"
                    ),
                    dict(
                        id=uuid4(),
                        org=scope.actor.org_id,
                        case=scope.case_id,
                        import_id=identifier,
                        ordinal=ordinal,
                        source=resolved_asset["source_id"],
                        asset=resolved_asset["asset_id"],
                        actor=scope.actor.user_id,
                    ),
                )
                items.append(
                    dict(ordinal=ordinal, asset_id=str(resolved_asset["asset_id"]), state="accepted", error_code=None)
                )
            value = dict(import_id=str(identifier), state="COMPLETED", items=items)
            # Keep the fixed request references for reconstruction without fabricating a new asset.
            self.receipts.remember(connection, scope, "createImport", key, digest, dict(request=body, response=value))
            audit(connection, scope, "asset.import.registered", "import", identifier, 1, request)
            return value
