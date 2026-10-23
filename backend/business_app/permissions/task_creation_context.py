"""Immutable createTask request context, never identity authentication or ALLOW.

The future HTTP entry point must bind in its parent async task before conditional
checks and keep the context through the handler/fence. Threadpool readers receive
detached snapshots; child-thread ContextVar writes never update the parent task.
Consumers must still verify the current authenticated Principal, authorization
root, target, expiry and current facts. A structurally valid context proves none
of those institutional facts and does not mount an operation.
"""

import json
import re
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ..contracts import validate_api
from ..errors import BusinessError
from ..task_creation import TaskCreateRequest, freeze_task_create
from ..types import Actor, Scope
from .object_facts import digest
from .policy import validate_principal
from .types import Principal


@dataclass(frozen=True)
class TaskCreationContext:
    principal: Principal
    request: TaskCreateRequest
    authorization_request_digest: str


_CURRENT: ContextVar[TaskCreationContext | None] = ContextVar("media_trace_task_creation_context", default=None)


def _scope_invalid() -> BusinessError:
    return BusinessError("AUTHORITY_SCOPE_INVALID", 503)


def _actor_copy(actor: Actor) -> Actor:
    return Actor(UUID(int=actor.user_id.int), UUID(int=actor.org_id.int))


def _principal_copy(principal: Principal, clock: Callable[[], float]) -> Principal:
    try:
        if (
            type(principal) is not Principal
            or type(principal.actor) is not Actor
            or any(
                type(value) is not UUID or value.int == 0 for value in (principal.actor.user_id, principal.actor.org_id)
            )
            or type(principal.issuer) is not str
            or type(principal.subject) is not str
        ):
            raise ValueError()
        # Identity text must also be representable as UTF-8; no private value is
        # interpolated into errors. Existing key/expiry/clock policy is reused.
        principal.issuer.encode("utf8")
        principal.subject.encode("utf8")
        result = Principal(_actor_copy(principal.actor), principal.issuer, principal.subject, principal.expires_at)
    except Exception:
        raise BusinessError("AUTHORITY_ACTOR_INVALID", 503) from None
    validate_principal(result, clock)
    return result


def _request_copy(principal: Principal, body: dict[str, Any]) -> TaskCreateRequest:
    if type(body) is not dict:
        raise BusinessError("INPUT_INVALID", 422)
    validate_api("TaskCreate", body)
    try:
        case_id, asset_id = UUID(body["case_id"]), UUID(body["asset_id"])
        if case_id.int == 0 or asset_id.int == 0:
            raise ValueError()
        value = freeze_task_create(Scope(_actor_copy(principal.actor), case_id), body)
        return TaskCreateRequest(
            _actor_copy(value.actor),
            UUID(int=value.case_id.int),
            UUID(int=value.asset_id.int),
            value.scene,
            value.policy_version,
            tuple(list(value.modules)),
            value.priority,
            memoryview(value.canonical_body).tobytes(),
            value.request_sha256,
        )
    except BusinessError:
        raise
    except Exception:
        raise BusinessError("INPUT_INVALID", 422) from None


def _authorization_digest(request: TaskCreateRequest) -> str:
    # B is the existing permission envelope digest. A remains the independent
    # request.request_sha256 with its existing Unicode/literal semantics.
    return digest(dict(path={}, query={}, body=json.loads(request.canonical_body)))


def freeze_task_creation_context(
    principal: Principal, body: dict[str, Any], *, clock: Callable[[], float] = time.time
) -> TaskCreationContext:
    """Freeze a shape/time-checked identity and body, without authenticating them."""
    identity = _principal_copy(principal, clock)
    request = _request_copy(identity, body)
    return TaskCreationContext(identity, request, _authorization_digest(request))


def _context_copy(value: TaskCreationContext, clock: Callable[[], float]) -> TaskCreationContext:
    if type(value) is not TaskCreationContext:
        raise _scope_invalid()
    try:
        principal = value.principal
    except Exception:
        raise _scope_invalid() from None
    # Preserve the established identity/expiry/clock BusinessError mapping.
    identity = _principal_copy(principal, clock)
    try:
        request = value.request
        if (
            type(request) is not TaskCreateRequest
            or type(request.actor) is not Actor
            or any(
                type(item) is not UUID
                for item in (request.actor.user_id, request.actor.org_id, request.case_id, request.asset_id)
            )
            or type(request.modules) is not tuple
            or type(request.canonical_body) is not bytes
            or any(
                type(item) is not str
                for item in (request.scene, request.policy_version, request.priority, request.request_sha256)
            )
            or type(value.authorization_request_digest) is not str
            or re.fullmatch(r"[a-f0-9]{64}", value.authorization_request_digest) is None
        ):
            raise ValueError()
        expected = _request_copy(identity, json.loads(request.canonical_body))
        authorization_digest = _authorization_digest(expected)
        if request != expected or value.authorization_request_digest != authorization_digest:
            raise ValueError()
        return TaskCreationContext(identity, expected, authorization_digest)
    except Exception:
        raise _scope_invalid() from None


def current_task_creation_context(*, clock: Callable[[], float] = time.time) -> TaskCreationContext | None:
    """Read a revalidated detached snapshot; its presence is never an ALLOW."""
    value = _CURRENT.get()
    return None if value is None else _context_copy(value, clock)


@contextmanager
def bind_task_creation_context(
    context: TaskCreationContext, *, clock: Callable[[], float] = time.time
) -> Iterator[TaskCreationContext]:
    """Bind in the parent request task and restore its exact prior token finally."""
    snapshot = _context_copy(context, clock)
    token = _CURRENT.set(snapshot)
    try:
        # The value yielded to callers must not expose the ContextVar's object.
        yield _context_copy(snapshot, clock)
    finally:
        _CURRENT.reset(token)
