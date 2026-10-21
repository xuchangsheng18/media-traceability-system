"""Authority-backed registration; no default provider or client approval status."""

import copy
import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import Connection, text

from .contracts import validate_api, validate_response
from .errors import BusinessError
from .types import Scope

if TYPE_CHECKING:
    from .controls.receipts import ControlReceipts
    from .db import Database


@dataclass(frozen=True)
class SourceRegistrationProof:
    """Trusted adapter evidence, separate from the public SourceCreate contract."""

    org_id: UUID
    case_id: UUID
    source_type: str
    authorization_ref: str
    purpose: tuple[str, ...]
    expires_at: datetime | None
    authorization_status: str
    authorization_version: str
    valid_until: datetime


class SourceRegistrationAuthority(Protocol):
    """Deployment supplies real source authority; synthetic providers belong in tests."""

    def resolve(
        self, scope: Scope, body: dict[str, Any], *, connection: Connection | None
    ) -> SourceRegistrationProof: ...


def now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: Any) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _registration_expiry(value: str | None) -> datetime | None:
    """Preserve RFC3339 expiry exactly at the authority's microsecond precision.

    More than six fractional digits remain contract-valid. Trailing zeroes can
    be removed losslessly; nonzero submicroseconds cannot equal a datetime or
    PostgreSQL microsecond proof and therefore fail authority binding with 403.
    Never round or truncate a nonzero digit to obtain an authorization match.
    """
    if value is None:
        return None
    parts = re.fullmatch(
        r"([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]+))?(Z|[+-][0-9]{2}:[0-9]{2})",
        value.upper(),
    )
    if parts is None:
        raise BusinessError("INPUT_INVALID", 422)
    whole, fraction, zone = parts.groups()
    if fraction is not None and fraction[6:].strip("0"):
        raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)
    # Python 3.10 fromisoformat accepts only 3/6 fractional digits. Padding to
    # exactly six changes only representation, including for +HH:MM offsets.
    fractional = "." + fraction[:6].ljust(6, "0") if fraction is not None else ""
    try:
        return datetime.fromisoformat(whole + fractional + zone.replace("Z", "+00:00"))
    except ValueError:
        raise BusinessError("INPUT_INVALID", 422) from None


def resolve_registration_proof(
    authority: SourceRegistrationAuthority | None,
    scope: Scope,
    body: dict[str, Any],
    *,
    connection: Connection | None,
    clock: Callable[[], datetime] = now,
) -> SourceRegistrationProof:
    """Validate exact request bindings and current evidence; never infer an ALLOW."""
    validate_api("SourceCreate", body)
    resolver = getattr(authority, "resolve", None)
    if not callable(resolver):
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)
    try:
        proof = resolver(scope, copy.deepcopy(body), connection=connection)
    except BusinessError as error:
        if error.http_status == 403:
            raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403) from None
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503) from None
    except Exception:
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503) from None
    current = clock()
    if (
        type(proof) is not SourceRegistrationProof
        or not isinstance(proof.org_id, UUID)
        or not isinstance(proof.case_id, UUID)
        or not isinstance(proof.source_type, str)
        or proof.source_type not in {"authorized_business", "public_licensed", "user_submission", "synthetic"}
        or not isinstance(proof.authorization_ref, str)
        or not 1 <= len(proof.authorization_ref) <= 128
        or type(proof.purpose) is not tuple
        or not proof.purpose
        or any(not isinstance(item, str) or not 1 <= len(item) <= 128 for item in proof.purpose)
        or len(set(proof.purpose)) != len(proof.purpose)
        or not isinstance(proof.authorization_version, str)
        or not 1 <= len(proof.authorization_version) <= 128
        or not isinstance(proof.authorization_status, str)
        or proof.authorization_status not in {"pending", "verified", "expired", "revoked"}
        or not _aware(proof.valid_until)
        or not _aware(current)
        or proof.valid_until <= current
        or (proof.expires_at is not None and not _aware(proof.expires_at))
    ):
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)
    expires = _registration_expiry(body["expires_at"])
    if (
        proof.org_id != scope.actor.org_id
        or proof.case_id != scope.case_id
        or scope.case_id != UUID(body["case_id"])
        or proof.source_type != body["source_type"]
        or proof.authorization_ref != body["authorization_ref"]
        or proof.purpose != tuple(body["purpose"])
        or proof.expires_at != expires
        or proof.authorization_status not in {"pending", "verified"}
        or (proof.expires_at is not None and proof.expires_at <= current)
    ):
        raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)
    return proof


def _wire(item: dict[str, Any]) -> dict[str, Any]:
    value = dict(
        source_id=str(item["source_id"]),
        case_id=str(item["case_id"]),
        name=item["name"],
        source_type=item["source_type"],
        authorization_ref=item["authorization_ref"],
        purpose=list(item["purpose"]),
        expires_at=item["expires_at"].isoformat() if item["expires_at"] else None,
        authorization_status=item["authorization_status"],
        version=int(item["row_version"]),
    )
    validate_response("Source", value)
    return value


class SourceRegistration:
    def __init__(
        self,
        database: "Database",
        receipts: "ControlReceipts",
        authority: SourceRegistrationAuthority | None,
        *,
        clock: Callable[[], datetime] = now,
    ) -> None:
        self.database, self.receipts, self.authority, self.clock = database, receipts, authority, clock

    def create(self, scope: Scope, body: dict[str, Any], request: Request, key: str) -> dict[str, Any]:
        from .controls.common import audit, canonical
        from .permissions.object_facts import digest
        from .scope_collections import require_root
        from .scope_context import current_data_scope

        validate_api("SourceCreate", body)
        if not isinstance(key, str) or not 1 <= len(key) <= 128:
            raise BusinessError("INPUT_INVALID", 422)
        body = copy.deepcopy(body)
        request_digest = digest(dict(path=dict(request.path_params), query=dict(request.query_params), body=body))
        request_sha = hashlib.sha256(canonical(body)).hexdigest()
        with self.database.transaction(scope) as connection:
            root = current_data_scope()
            authorization = require_root(connection, root)
            target = authorization.evidence.target
            if (
                root is None
                or root.operation_id != "createSource"
                or root.actor != scope.actor
                or root.case_id != scope.case_id
                or not authorization.mutation
                or target.kind != "case"
                or target.org_id != scope.actor.org_id
                or target.case_id != scope.case_id
                or target.object_id != scope.case_id
                or target.request_digest != request_digest
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            replay = self.receipts.replay(connection, scope, "createSource", key, request_sha)
            proof = resolve_registration_proof(self.authority, scope, body, connection=connection, clock=self.clock)

            def recheck() -> None:
                current = resolve_registration_proof(
                    self.authority, scope, body, connection=connection, clock=self.clock
                )
                if proof.valid_until <= self.clock() or replace(current, valid_until=proof.valid_until) != proof:
                    raise BusinessError("AUTHORIZATION_CHANGED", 503)

            self.database.before_commit(connection, recheck)
            if replay is not None:
                validate_response("Source", replay)
                item = (
                    connection.execute(
                        text(
                            "SELECT * FROM mt.source_registry WHERE org_id=:org AND case_id=:case "
                            "AND source_id=:id FOR SHARE"
                        ),
                        dict(org=scope.actor.org_id, case=scope.case_id, id=UUID(replay["source_id"])),
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    item is None
                    or _wire(dict(item)) != replay
                    or item["authorization_version"] != proof.authorization_version
                    or item["authorization_status"] != proof.authorization_status
                ):
                    raise BusinessError("SOURCE_VERSION_CONFLICT", 409)
                return replay
            identifier = uuid4()
            item = (
                connection.execute(
                    text(
                        "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,"
                        "purpose,authorization_status,authorization_version,expires_at,created_by) "
                        "VALUES(:id,:org,:case,:name,:type,:ref,:purposes,:status,:version,:expires,:actor) RETURNING *"
                    ),
                    dict(
                        id=identifier,
                        org=scope.actor.org_id,
                        case=scope.case_id,
                        name=body["name"],
                        type=proof.source_type,
                        ref=proof.authorization_ref,
                        purposes=list(proof.purpose),
                        status=proof.authorization_status,
                        version=proof.authorization_version,
                        expires=proof.expires_at,
                        actor=scope.actor.user_id,
                    ),
                )
                .mappings()
                .one()
            )
            value = _wire(dict(item))
            self.receipts.remember(connection, scope, "createSource", key, request_sha, value)
            audit(connection, scope, "source.registered", "source", identifier, value["version"], request)
            return value
