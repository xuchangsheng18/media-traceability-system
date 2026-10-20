"""Per-request binding propagated by FastAPI to sync handlers, never a global ALLOW."""

import math
import time
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy import Connection

from ..errors import BusinessError
from ..types import Actor, Scope
from .rule_types import AuthorizationEvidence, WorkAuthorizationEvidence
from .work_subject import WORK_OPERATIONS

Evidence = AuthorizationEvidence | WorkAuthorizationEvidence


def evidence_actor(evidence: Evidence) -> Actor:
    return evidence.principal.actor if isinstance(evidence, AuthorizationEvidence) else evidence.subject.actor


class FencePort(Protocol):
    def hold(self, connection: Connection, evidence: Evidence) -> None: ...
    def finish(self, connection: Connection, evidence: Evidence) -> None: ...


class WorkPort(Protocol):
    def open(self, scope: Scope, kind: str, identifier: UUID, operation_id: str) -> AbstractContextManager[None]: ...


@contextmanager
def protected_work(
    port: WorkPort | None, scope: Scope, kind: str, identifier: UUID, operation_id: str
) -> Iterator[None]:
    if port is None:
        raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
    with port.open(scope, kind, identifier, operation_id):
        current = current_authorization()
        operation = WORK_OPERATIONS.get(operation_id)
        if (
            current is None
            or not isinstance(current.evidence, WorkAuthorizationEvidence)
            or current.fence is None
            or not current.mutation
            or operation is None
            or (current.evidence.subject.actor, current.evidence.subject.work_kind, current.evidence.subject.work_id)
            != (scope.actor, kind, identifier)
            or current.evidence.operation_id != operation_id
            or (
                current.evidence.target.org_id,
                current.evidence.target.case_id,
                current.evidence.target.object_id,
                current.evidence.target.kind,
            )
            != (scope.actor.org_id, scope.case_id, identifier, operation[1])
            or type(current.evidence.valid_until) not in (int, float)
            or not math.isfinite(current.evidence.valid_until)
            or current.evidence.valid_until <= time.time()
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        yield


@dataclass(frozen=True)
class RequestAuthorization:
    evidence: Evidence
    fence: FencePort | None
    mutation: bool


_CURRENT: ContextVar[RequestAuthorization | None] = ContextVar("media_trace_request_authorization", default=None)


def current_authorization() -> RequestAuthorization | None:
    return _CURRENT.get()


@contextmanager
def request_authorization(evidence: Evidence, fence: FencePort | None, *, mutation: bool) -> Iterator[None]:
    token = _CURRENT.set(RequestAuthorization(evidence, fence, mutation))
    try:
        yield
    finally:
        _CURRENT.reset(token)
