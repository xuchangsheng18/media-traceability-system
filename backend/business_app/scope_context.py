"""Request-local scope and root connection, with exact nested scope preservation."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from sqlalchemy import Connection

from .data_scope import DataScope, TaskBinding
from .errors import BusinessError
from .permissions.context import RequestAuthorization

_SCOPE: ContextVar[DataScope | None] = ContextVar("media_trace_data_scope", default=None)


@dataclass(frozen=True)
class BoundTransaction:
    database: object
    connection: Connection
    scope: DataScope
    authorization: RequestAuthorization | None
    commit_checks: list[Callable[[], None]] = field(default_factory=list, repr=False, compare=False)


_TRANSACTION: ContextVar[BoundTransaction | None] = ContextVar("media_trace_scope_transaction", default=None)


def current_data_scope() -> DataScope | None:
    return _SCOPE.get()


def current_scope_transaction() -> BoundTransaction | None:
    return _TRANSACTION.get()


def _narrow_task(parent: TaskBinding | None, child: TaskBinding | None) -> bool:
    if parent is None:
        return True
    return (
        child is not None
        and child.task_id == parent.task_id
        and (parent.run_version is None or child.run_version == parent.run_version)
        and (parent.result_version is None or child.result_version == parent.result_version)
    )


def scope_is_subset(parent: DataScope, child: DataScope) -> bool:
    return (
        parent.actor == child.actor
        and parent.mode is child.mode
        and parent.operation_id == child.operation_id
        and parent.case_id == child.case_id
        and parent.lookup == child.lookup
        and parent.evidence_binding == child.evidence_binding
        and _narrow_task(parent.task_binding, child.task_binding)
    )


@contextmanager
def bind_data_scope(scope: DataScope) -> Iterator[None]:
    old = current_data_scope()
    if not isinstance(scope, DataScope) or (old is not None and not scope_is_subset(old, scope)):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    token = _SCOPE.set(scope)
    try:
        yield
    finally:
        _SCOPE.reset(token)


@contextmanager
def bind_scope_transaction(value: BoundTransaction) -> Iterator[None]:
    if current_scope_transaction() is not None:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    token = _TRANSACTION.set(value)
    try:
        with bind_data_scope(value.scope):
            yield
    finally:
        _TRANSACTION.reset(token)
