"""Immutable task request/plan bindings, never task creation or an ALLOW decision."""

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import Connection

from .contracts import validate_api
from .controls.common import canonical
from .errors import BusinessError
from .types import Actor, Scope


@dataclass(frozen=True)
class TaskCreateRequest:
    actor: Actor
    case_id: UUID
    asset_id: UUID
    scene: str
    policy_version: str
    modules: tuple[str, ...]
    priority: str
    canonical_body: bytes
    request_sha256: str


@dataclass(frozen=True)
class TaskPlanProof:
    request: TaskCreateRequest
    authority_version: str
    policy_sha256: str
    plan_id: str
    plan_version: str
    plan_sha256: str
    capability_id: str
    capability_version: str
    capability_sha256: str
    authorized: bool
    valid_until: datetime


class TaskPlanAuthority(Protocol):
    """A future deployment supplies actual mappings; no default authority exists."""

    def resolve(self, request: TaskCreateRequest, *, connection: Connection | None) -> TaskPlanProof: ...


def _unavailable() -> BusinessError:
    return BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: object) -> bool:
    return type(value) is datetime and value.tzinfo is not None and value.utcoffset() is not None


def freeze_task_create(scope: Scope, body: dict[str, Any]) -> TaskCreateRequest:
    """Keep existing JSON digest semantics; this does not authorize the asset."""
    if (
        type(scope) is not Scope
        or type(scope.actor) is not Actor
        or any(
            type(value) is not UUID or value.int == 0
            for value in (scope.actor.user_id, scope.actor.org_id, scope.case_id)
        )
    ):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    validate_api("TaskCreate", body)
    try:
        encoded = canonical(body)
        value = json.loads(encoded)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise BusinessError("INPUT_INVALID", 422) from None
    if UUID(value["case_id"]) != scope.case_id:
        raise BusinessError("PERMISSION_REQUIRED", 403)
    return TaskCreateRequest(
        actor=Actor(scope.actor.user_id, scope.actor.org_id),
        case_id=scope.case_id,
        asset_id=UUID(value["asset_id"]),
        scene=value["scene"],
        policy_version=value["policy_version"],
        modules=tuple(value["modules"]),
        priority=value["priority"],
        canonical_body=encoded,
        request_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def _copy_request(request: TaskCreateRequest) -> TaskCreateRequest:
    """Reconstruct and validate even directly constructed or provider-mutated types."""
    try:
        if type(request) is not TaskCreateRequest or type(request.canonical_body) is not bytes:
            raise _unavailable()
        copied = freeze_task_create(Scope(request.actor, request.case_id), json.loads(request.canonical_body))
        if type(request.modules) is not tuple or request != copied:
            raise _unavailable()
        return copied
    except Exception:
        raise _unavailable() from None


def _copy_proof(proof: TaskPlanProof, request: TaskCreateRequest, current: datetime) -> TaskPlanProof:
    try:
        if type(proof) is not TaskPlanProof:
            raise _unavailable()
        copied_request = _copy_request(proof.request)
        references = (
            proof.authority_version,
            proof.plan_id,
            proof.plan_version,
            proof.capability_id,
            proof.capability_version,
        )
        digests = (proof.policy_sha256, proof.plan_sha256, proof.capability_sha256)
        if (
            any(type(value) is not str or not 1 <= len(value) <= 128 for value in references)
            or any(type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None for value in digests)
            or type(proof.authorized) is not bool
            or not _aware(current)
            or not _aware(proof.valid_until)
            or proof.valid_until <= current
        ):
            raise _unavailable()
        deadline = proof.valid_until.astimezone(timezone.utc)
    except Exception:
        raise _unavailable() from None
    if copied_request != request or not proof.authorized:
        raise BusinessError("PERMISSION_REQUIRED", 403)
    return replace(proof, request=copied_request, valid_until=deadline)


def _time(clock: Callable[[], datetime]) -> datetime:
    try:
        value = clock()
        if not _aware(value):
            raise _unavailable()
        return value.astimezone(timezone.utc)
    except Exception:
        raise _unavailable() from None


def resolve_task_plan(
    authority: TaskPlanAuthority | None,
    request: TaskCreateRequest,
    *,
    connection: Connection | None,
    clock: Callable[[], datetime] = _now,
) -> TaskPlanProof:
    """Resolve exact immutable evidence, without writes, execution or fallback plans."""
    expected = _copy_request(request)
    try:
        resolver = getattr(authority, "resolve", None)
        if not callable(resolver):
            raise _unavailable()
        proof = resolver(_copy_request(expected), connection=connection)
    except BusinessError as error:
        if error.http_status == 403:
            raise BusinessError("PERMISSION_REQUIRED", 403) from None
        raise _unavailable() from None
    except Exception:
        raise _unavailable() from None
    return _copy_proof(proof, expected, _time(clock))


def recheck_task_plan(
    authority: TaskPlanAuthority | None,
    expected: TaskPlanProof,
    *,
    connection: Connection | None,
    clock: Callable[[], datetime] = _now,
) -> TaskPlanProof:
    """Future transaction consumers must call inside their authorization fence."""
    if type(expected) is not TaskPlanProof:
        raise _unavailable()
    snapshot = _copy_proof(expected, _copy_request(expected.request), _time(clock))
    current = resolve_task_plan(authority, snapshot.request, connection=connection, clock=clock)
    if (
        snapshot.valid_until <= _time(clock)
        or current.valid_until < snapshot.valid_until
        or replace(current, valid_until=snapshot.valid_until) != snapshot
    ):
        raise BusinessError("AUTHORIZATION_CHANGED", 503)
    return current
