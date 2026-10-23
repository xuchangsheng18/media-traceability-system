"""Existing downloadAsset contract, under the application's shared permission guard."""

from typing import cast
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import Response

from .asset_download import AssetDownload
from .history.router import current_scope

router = APIRouter(prefix="/api/v1")


@router.get("/assets/{id}/content", operation_id="downloadAsset")
def download_asset(request: Request, id: UUID) -> Response:
    scope = current_scope(request, id, "asset", "asset.download")
    service = cast(AssetDownload, request.app.state.asset_download)
    return service.content(scope, id, request)
