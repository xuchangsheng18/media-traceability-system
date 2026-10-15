"""Non-secret correlation metadata; identifiers never grant authority."""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any
from uuid import UUID

_request: ContextVar[str | None] = ContextVar("media_trace_request", default=None)
_logger = logging.getLogger("media_trace")


def trace_id(request_id: str) -> str:
    return UUID(request_id).hex


def trace_headers(request_id: str) -> dict[str, str]:
    return {"X-Request-Id": str(UUID(request_id)), "X-Trace-Id": trace_id(request_id)}


@contextmanager
def trace_context(request_id: str) -> Iterator[None]:
    token = _request.set(str(UUID(request_id)))
    try:
        yield
    finally:
        _request.reset(token)


def safe_log(event: str, *, request_id: str | None = None, **fields: Any) -> None:
    identifier = request_id or _request.get()
    if identifier is None:
        return
    record: dict[str, Any] = {"event": event, "request_id": str(UUID(identifier)), "trace_id": trace_id(identifier)}
    for key in ["task_id", "upload_id"]:
        if fields.get(key) is not None:
            record[key] = str(UUID(str(fields[key])))
    for key in ["run_version", "attempt", "status", "elapsed_ms"]:
        value = fields.get(key)
        if type(value) is int and value >= 0:
            record[key] = value
    for key in ["method", "route"]:
        value = fields.get(key)
        if isinstance(value, str) and len(value) <= 256:
            record[key] = value
    if isinstance(fields.get("accepted"), bool):
        record["accepted"] = fields["accepted"]
    _logger.info(json.dumps(record, ensure_ascii=False))
