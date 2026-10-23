"""Bounded immutable asset downloads; bytes leave only after transaction finalization."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from typing import TYPE_CHECKING
from uuid import UUID

from .errors import BusinessError

if TYPE_CHECKING:
    from fastapi import Request
    from fastapi.responses import Response

    from .auth import AuthorityProvider
    from .db import Database
    from .objects import ObjectStore
    from .settings import BusinessSettings
    from .types import Scope


def validate_download_request(
    has_query: bool, ranges: list[str], conditions: list[str]
) -> tuple[str | None, str | None]:
    if has_query:
        raise BusinessError("READ_PARAMETER_UNSUPPORTED", 422)
    for values in (ranges, conditions):
        if len(values) > 1 or any(
            not 1 <= len(value) <= 128 or any(ord(c) < 32 or ord(c) > 126 for c in value) for value in values
        ):
            raise BusinessError("INPUT_INVALID", 422)
    return (ranges[0] if ranges else None, conditions[0] if conditions else None)


def select_range(size: int, raw: str | None, condition: str | None, tag: str) -> tuple[int, int, int]:
    """Return HTTP status and Python slice bounds for the existing single-range contract."""
    if raw is None or (condition is not None and condition != tag):
        return 200, 0, size
    found = re.fullmatch(r"bytes=([0-9]*)-([0-9]*)", raw)
    if found is None or not any(found.groups()):
        raise BusinessError("RANGE_INVALID", 416)
    left, right = found.groups()
    if left:
        start, end = int(left), min(int(right) if right else size - 1, size - 1)
    else:
        suffix = int(right)
        if suffix <= 0:
            raise BusinessError("RANGE_INVALID", 416)
        start, end = max(0, size - suffix), size - 1
    if start >= size or end < start:
        raise BusinessError("RANGE_INVALID", 416)
    return 206, start, end + 1


def buffer_verified(stream: Iterator[bytes], size: int, sha256: str, limit: int) -> bytes:
    """Never return a prefix of an unverified object, even for a Range request."""
    if type(size) is not int or size < 0 or not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise BusinessError("ASSET_OBJECT_BINDING_INVALID", 503)
    if size > limit:
        raise BusinessError("ASSET_DOWNLOAD_DEVELOPMENT_LIMIT_EXCEEDED", 503)
    data = bytearray()
    digest = hashlib.sha256()
    try:
        for block in stream:
            if not isinstance(block, bytes) or len(data) + len(block) > size:
                raise BusinessError("ASSET_OBJECT_BINDING_INVALID", 503)
            data.extend(block)
            digest.update(block)
        if len(data) != size or digest.hexdigest() != sha256:
            raise BusinessError("ASSET_OBJECT_BINDING_INVALID", 503)
        return bytes(data)
    finally:
        close = getattr(stream, "close", None)
        if callable(close):
            close()


def download_headers(identifier: UUID, tag: str) -> dict[str, str]:
    return {
        "ETag": tag,
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
        "Content-Disposition": f'attachment; filename="asset-{identifier}.bin"',
        "X-Content-Type-Options": "nosniff",
    }


class AssetDownload:
    def __init__(
        self, database: Database, settings: BusinessSettings, store: ObjectStore, authority: AuthorityProvider | None
    ) -> None:
        self.database, self.settings, self.store, self.authority = database, settings, store, authority

    def content(self, scope: Scope, identifier: UUID, request: Request) -> Response:
        # Pure boundary helpers above remain runnable without a web/database installation.
        from fastapi.responses import Response
        from sqlalchemy import text

        from .controls.common import audit
        from .data_scope import AccessMode, ResourceBinding
        from .scope_collections import require_resource, require_root
        from .scope_context import current_data_scope
        from .scoped_objects import ScopedObjects
        from .types import ObjectRef

        raw, condition = validate_download_request(
            bool(request.query_params), request.headers.getlist("Range"), request.headers.getlist("If-Range")
        )
        with self.database.transaction(scope) as connection:
            root = current_data_scope()
            authorization = require_root(connection, root)
            target = authorization.evidence.target
            if (
                root is None
                or root.mode is not AccessMode.CASE
                or root.operation_id != "downloadAsset"
                or root.actor != scope.actor
                or root.case_id != scope.case_id
                or target.kind != "asset"
                or target.object_id != identifier
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            require_resource(connection, root, "asset", identifier)
            item = (
                connection.execute(
                    text(
                        "SELECT a.asset_id,a.object_id,a.state,a.row_version,a.sha256,a.size_bytes,"
                        "o.version_id,o.sha256 AS registered_sha256,o.size_bytes AS registered_size "
                        "FROM mt.media_asset a JOIN mt.object_version o "
                        "ON o.org_id=a.org_id AND o.case_id=a.case_id AND o.object_id=a.object_id "
                        "WHERE a.org_id=:org AND a.case_id=:case AND a.asset_id=:id "
                        "FOR SHARE OF a /* asset_download_projection */"
                    ),
                    dict(org=scope.actor.org_id, case=scope.case_id, id=identifier),
                )
                .mappings()
                .one_or_none()
            )
            if item is None:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            if item["state"] != "VALID":
                raise BusinessError("ASSET_STATE_CONFLICT", 409)
            if (
                item["sha256"] != item["registered_sha256"]
                or item["size_bytes"] != item["registered_size"]
                or type(item["size_bytes"]) is not int
                or item["size_bytes"] < 0
                or not isinstance(item["version_id"], str)
                or not item["version_id"]
                or not isinstance(item["sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
            ):
                raise BusinessError("ASSET_OBJECT_BINDING_INVALID", 503)
            if item["size_bytes"] > self.settings.max_upload_bytes:
                # Explicit memory bound for this development provider, not a business file-size policy.
                raise BusinessError("ASSET_DOWNLOAD_DEVELOPMENT_LIMIT_EXCEEDED", 503)
            reference = ObjectRef(item["object_id"], item["version_id"], item["sha256"])
            tag = (
                '"'
                + hashlib.sha256(
                    json.dumps(
                        [str(reference.object_id), reference.version_id, reference.sha256], separators=(",", ":")
                    ).encode()
                ).hexdigest()
                + '"'
            )
            status, start, stop = select_range(item["size_bytes"], raw, condition, tag)
            try:
                data = buffer_verified(
                    ScopedObjects(self.store, self.authority).read(
                        connection, root, ResourceBinding("asset_content", identifier), reference
                    ),
                    item["size_bytes"],
                    reference.sha256,
                    self.settings.max_upload_bytes,
                )
            except (OSError, RuntimeError, ValueError):
                raise BusinessError("ASSET_OBJECT_UNAVAILABLE", 503) from None
            audit(connection, scope, "asset.download", "asset", identifier, item["row_version"], request)
        # Final authorization, audit insertion and commit must all succeed before any Response is built.
        headers = download_headers(identifier, tag)
        if status == 206:
            headers["Content-Range"] = f"bytes {start}-{stop - 1}/{len(data)}"
        return Response(data[start:stop], status_code=status, media_type="application/octet-stream", headers=headers)
