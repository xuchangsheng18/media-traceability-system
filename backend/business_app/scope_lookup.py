"""Exact, read-only authorization bootstrap; never a general business query port."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from .data_scope import AccessMode, DataScope, LookupKey, ScopeMetadata
from .db import Database
from .errors import BusinessError
from .permissions.context import current_authorization
from .permissions.policy import validate_principal
from .permissions.rule_types import ExecutionSubject, RuleTarget
from .permissions.types import Principal
from .permissions.work_subject import WORK_OPERATIONS, validate_execution_subject
from .scope_catalog import lookup_spec
from .scope_context import current_scope_transaction
from .types import JsonValue

if TYPE_CHECKING:
    from .permissions.work import WorkTrust


class SqlScopeLookup:
    def __init__(
        self, database: Database, *, work_trust: WorkTrust | None = None, clock: Callable[[], float] = time.time
    ) -> None:
        self.database, self.work_trust, self.clock = database, work_trust, clock

    def _validate(self, subject: Principal | ExecutionSubject, operation: str, key: LookupKey) -> float:
        current = self.clock()
        if type(current) not in (int, float) or not math.isfinite(current):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        if not isinstance(key, LookupKey) or operation not in lookup_spec(key.kind).operation_ids:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        deadline = float(current) + 5
        if isinstance(subject, Principal):
            validate_principal(subject, self.clock)
            return min(deadline, float(subject.expires_at))
        validate_execution_subject(subject)
        actual = WORK_OPERATIONS.get(operation)
        if (
            self.work_trust is None
            or actual is None
            or actual[1:] != (key.kind, subject.work_kind)
            or key.identifier != subject.work_id
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        trust = self.work_trust.read(subject)
        return min(deadline, trust.valid_until)

    @contextmanager
    def connection(self, subject: Principal | ExecutionSubject, operation: str, key: LookupKey) -> Iterator[Connection]:
        self._validate(subject, operation, key)
        if current_authorization() is not None:
            with self.database.identity_transaction(subject.actor) as connection:
                yield connection
        else:
            scope = DataScope(subject.actor, AccessMode.LOOKUP, operation, None, key, None, None)
            with self.database.scoped_transaction(scope) as connection:
                yield connection

    def load(
        self, subject: Principal | ExecutionSubject, operation: str, key: LookupKey, *, connection: Connection
    ) -> dict[str, Any]:
        self._validate(subject, operation, key)
        root = current_scope_transaction()
        if root is None or root.connection is not connection or connection.engine.url != self.database.engine.url:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if root.scope.actor != subject.actor or root.scope.operation_id != operation:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if root.scope.mode is AccessMode.LOOKUP and root.scope.lookup != key:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        try:
            value = connection.execute(
                text("SELECT mt.lookup_scope_metadata(:kind,:id)"), dict(kind=key.kind, id=key.identifier)
            ).scalar_one()
        except SQLAlchemyError:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
        if value is None:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if not isinstance(value, dict) or set(value) != {"record", "memberships", "related", "sources", "same_org"}:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        record = value["record"]
        spec = lookup_spec(key.kind)
        if (
            not isinstance(record, dict)
            or set(record) - (set(spec.projection) | {"_row_sha256"})
            or record.get(spec.key) != str(key.identifier)
            or record.get("org_id") != str(subject.actor.org_id)
            or value["same_org"] is not True
            or any(not isinstance(value[name], list) for name in ("memberships", "related", "sources"))
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return value

    def read(self, subject: Principal | ExecutionSubject, operation: str, key: LookupKey) -> ScopeMetadata:
        deadline = self._validate(subject, operation, key)
        with self.connection(subject, operation, key) as connection:
            value = self.load(subject, operation, key, connection=connection)
        record = value["record"]
        target = RuleTarget(
            subject.actor.org_id,
            key.kind,
            key.identifier,
            int(record["row_version"]),
            UUID(record["case_id"]) if record.get("case_id") else None,
            record.get("purpose") if isinstance(record.get("purpose"), str) else None,
            record.get("kind") if key.kind == "policy" else None,
        )
        version = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return ScopeMetadata(
            target,
            MappingProxyType(cast(dict[str, JsonValue], record)),
            MappingProxyType({"same_org": True, "case": bool(value["memberships"])}),
            version,
            deadline,
        )
