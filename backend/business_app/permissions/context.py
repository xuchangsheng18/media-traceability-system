"""Per-request binding propagated by FastAPI to sync handlers, never a global ALLOW."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import Connection

from .rule_types import AuthorizationEvidence


class FencePort(Protocol):
    def hold(self, connection: Connection, evidence: AuthorizationEvidence) -> None: ...
    def finish(self, connection: Connection, evidence: AuthorizationEvidence) -> None: ...


@dataclass(frozen=True)
class RequestAuthorization:
    evidence: AuthorizationEvidence
    fence: FencePort | None
    mutation: bool


_CURRENT: ContextVar[RequestAuthorization | None] = ContextVar("media_trace_request_authorization", default=None)


def current_authorization() -> RequestAuthorization | None:
    return _CURRENT.get()


@contextmanager
def request_authorization(
    evidence: AuthorizationEvidence, fence: FencePort | None, *, mutation: bool
) -> Iterator[None]:
    token = _CURRENT.set(RequestAuthorization(evidence, fence, mutation))
    try:
        yield
    finally:
        _CURRENT.reset(token)
