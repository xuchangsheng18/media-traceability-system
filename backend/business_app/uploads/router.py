import hashlib
import re
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Header, Path, Query, Request

from ..errors import BusinessError
from .service import UploadService

router = APIRouter(prefix="/api/v1")


def service(request: Request) -> UploadService:
    return cast(UploadService, request.app.state.upload_service)


@router.post("/uploads", status_code=201, operation_id="createUpload")
def create_upload(
    request: Request, body: dict[str, Any], idempotency_key: Annotated[str, Header(min_length=1, max_length=128)]
) -> dict[str, Any]:
    return service(request).create(request, body, idempotency_key)


@router.put("/uploads/{id}/parts/{part_no}", operation_id="putUploadPart")
async def put_upload_part(
    request: Request,
    id: UUID,
    part_no: Annotated[int, Path(ge=1)],
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
    x_part_sha256: Annotated[str, Header()],
    content_length: Annotated[int, Header(gt=0)],
) -> dict[str, Any]:
    current = service(request)
    scope = current.scope(request, "asset.upload", upload_id=id)
    if not re.fullmatch(r"[0-9a-f]{64}", x_part_sha256):
        raise BusinessError("INPUT_INVALID", 422)
    if content_length > current.repository.settings.part_size_bytes:
        raise BusinessError("UPLOAD_TOO_LARGE", 413)
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > content_length:
            raise BusinessError("UPLOAD_PART_SIZE_INVALID", 422)
        data.extend(chunk)
    if len(data) != content_length or hashlib.sha256(data).hexdigest() != x_part_sha256:
        raise BusinessError("UPLOAD_PART_DIGEST_INVALID", 422)
    return current.put_part(scope, id, part_no, bytes(data), x_part_sha256, idempotency_key)


@router.get("/uploads/{id}", operation_id="getUploadStatus")
def get_status(request: Request, id: UUID) -> dict[str, Any]:
    current = service(request)
    return current.status(request, id)


@router.post("/uploads/{id}/complete", status_code=202, operation_id="completeUpload")
def complete_upload(
    request: Request,
    id: UUID,
    body: dict[str, Any],
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
) -> dict[str, Any]:
    return service(request).complete(request, id, body, idempotency_key)


@router.get("/uploads/{id}/parts", operation_id="listUploadParts")
def list_parts(
    request: Request, id: UUID, cursor: str | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 100
) -> dict[str, Any]:
    current = service(request)
    return current.repository.parts(current.scope(request, "asset.upload", upload_id=id), id, cursor, limit)
