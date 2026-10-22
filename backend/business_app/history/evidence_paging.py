"""Page a validated immutable evidence projection without granting access."""

import base64
import hashlib
import hmac
import json
from typing import Any
from uuid import UUID

from ..contracts import validate_response
from ..cursor_encoding import decode_cursor
from ..errors import BusinessError
from ..types import ResultKey, Scope


def page_evidence(
    body: dict[str, Any],
    scope: Scope,
    key: ResultKey,
    secret: str,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Slice only a complete projection already loaded under current authority.

    A continuation identifies the exact selected result and projection content.
    It is neither a substitute for repository authorization nor a DB cursor.
    """
    if (
        type(limit) is not int
        or not 1 <= limit <= 100
        or (cursor is not None and (not isinstance(cursor, str) or not 1 <= len(cursor) <= 128))
    ):
        raise BusinessError("PAGE_CURSOR_INVALID", 422)
    if not isinstance(secret, str) or len(secret) < 32:
        raise BusinessError("RESPONSE_CONTRACT_UNAVAILABLE", 503)
    validate_response("EvidencePage", body)
    if body["next_cursor"] is not None:
        raise BusinessError("EVIDENCE_PAGING_SOURCE_INCOMPLETE", 503)
    items = body["items"]
    if len({UUID(item["evidence_id"]) for item in items}) != len(items):
        raise BusinessError("RESPONSE_CONTRACT_UNAVAILABLE", 503)
    try:
        encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError):
        raise BusinessError("RESPONSE_CONTRACT_UNAVAILABLE", 503) from None
    digest = hashlib.sha256(encoded).digest()
    binding = json.dumps(
        [
            "evidence-snapshot-page/1",
            str(scope.actor.user_id),
            str(scope.actor.org_id),
            str(scope.case_id),
            str(key.task_id),
            key.run_version,
            key.result_version,
            limit,
        ],
        separators=(",", ":"),
    ).encode("utf-8")
    offset = 0
    if cursor is not None:
        try:
            raw = decode_cursor(cursor, padded=False)
            if len(raw) != 72 or not hmac.compare_digest(
                raw[40:], hmac.new(secret.encode(), binding + raw[:40], hashlib.sha256).digest()
            ):
                raise ValueError()
            if not hmac.compare_digest(raw[8:40], digest):
                raise BusinessError("PAGE_CURSOR_STALE", 409)
            offset = int.from_bytes(raw[:8], "big")
            if not 0 < offset < len(items) or offset % limit:
                raise ValueError()
        except (TypeError, ValueError):
            raise BusinessError("PAGE_CURSOR_INVALID", 422) from None
    end = offset + limit
    following = None
    if end < len(items):
        value = end.to_bytes(8, "big") + digest
        tag = hmac.new(secret.encode(), binding + value, hashlib.sha256).digest()
        following = base64.urlsafe_b64encode(value + tag).decode("ascii").rstrip("=")
    return dict(body, items=items[offset:end], next_cursor=following)
