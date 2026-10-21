"""Immutable, exactly scoped authority snapshots for source synchronization."""

import copy
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection

from .contracts import validate_response
from .controls.providers import SourceSynchronization
from .errors import BusinessError
from .scope_collections import require_resource, require_root
from .scope_context import current_data_scope
from .types import Scope


def _expiry(value: str | None) -> datetime | None:
    if value is None:
        return None
    parts = re.fullmatch(
        r"([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]+))?(Z|[+-][0-9]{2}:[0-9]{2})",
        value.upper(),
    )
    if parts is None:
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)
    whole, fraction, zone = parts.groups()
    # Python/PostgreSQL store microseconds. Extra zeroes are lossless; a nonzero
    # submicrosecond must never be truncated or rounded into an authority match.
    if fraction is not None and fraction[6:].strip("0"):
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)
    fractional = "." + fraction[:6].ljust(6, "0") if fraction is not None else ""
    try:
        return datetime.fromisoformat(whole + fractional + zone.replace("Z", "+00:00"))
    except ValueError:
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503) from None


@dataclass(frozen=True)
class SourceAuthoritySnapshot:
    source_id: UUID
    case_id: UUID
    authorization_ref: str
    authorization_version: str
    purpose: tuple[str, ...]
    authorization_status: str
    expires_at: datetime | None

    def matches(self, item: dict[str, Any]) -> bool:
        return (
            item["source_id"] == self.source_id
            and item["case_id"] == self.case_id
            and item["authorization_ref"] == self.authorization_ref
            and item["authorization_version"] == self.authorization_version
            and tuple(item["purpose"]) == self.purpose
            and item["authorization_status"] == self.authorization_status
            and item["expires_at"] == self.expires_at
        )


def read_source_authority(
    provider: SourceSynchronization | None, scope: Scope, source_id: UUID, *, connection: Connection
) -> SourceAuthoritySnapshot:
    root = current_data_scope()
    authorization = require_root(connection, root)
    require_resource(connection, root, "source", source_id)
    if (
        root is None
        or root.operation_id != "syncSourceAuthorization"
        or root.actor != scope.actor
        or root.case_id != scope.case_id
        or not authorization.mutation
        or authorization.evidence.target.kind != "source"
        or authorization.evidence.target.object_id != source_id
    ):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    if provider is None:
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)
    try:
        # Providers may return a reused mutable dictionary. Neither SQL params
        # nor the commit comparison may retain that shared mutable object.
        value = copy.deepcopy(provider.current(scope, source_id))
    except Exception:
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503) from None
    validate_response("SourceAuthorizationUpdate", value)
    identifier, case = UUID(value["source_id"]), UUID(value["case_id"])
    if identifier != source_id or case != scope.case_id:
        raise BusinessError("SOURCE_AUTHORITY_BINDING_INVALID", 503)
    return SourceAuthoritySnapshot(
        identifier,
        case,
        value["authorization_ref"],
        value["authorization_version"],
        tuple(value["purpose"]),
        value["authorization_status"],
        _expiry(value["expires_at"]),
    )
