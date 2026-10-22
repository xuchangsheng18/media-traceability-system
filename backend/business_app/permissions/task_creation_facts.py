"""Dedicated task-create facts, without a default current capability authority.

Only limited real SQL observations are available in this tranche. An ACTIVE
head, declared capability references and opaque receipt fields are not a formal
adoption decision: model_task_version remains unknown. Classification belongs
to the separate institutional provider. No dictionary can set these core facts.

A future CurrentCapabilityStateReader is a trusted, explicitly configured
adapter, not HTTP data. It must acquire/recheck its actual state through the
same connection and transaction; CASE_SHARE_LOCKED is its contract, not proof
that a Python string itself acquired database locks. No implementation exists
here and remote unleased status is not supported as atomic revocation evidence.
"""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Protocol

from sqlalchemy import Connection

from ..data_scope import AccessMode, LookupKey
from ..errors import BusinessError
from ..scope_context import current_data_scope, current_scope_transaction
from ..scope_lookup import SqlScopeLookup
from ..task_creation_materials import _canonical, _load
from ..task_creation_sql_authority import (
    SqlTaskPlanAuthority,
    TaskPlanMetadataObservation,
    _fact_text,
    _metadata_copy,
    _now,
    _sql_timestamp,
    _time,
    _unavailable,
    _utc,
)
from .context import current_authorization
from .rule_types import ConditionFacts, RuleTarget
from .task_creation_context import TaskCreationContext, _context_copy, _principal_copy, current_task_creation_context
from .types import Principal


class TaskCreationFactsPort(Protocol):
    def read(
        self,
        principal: Principal,
        operation_id: str,
        target: RuleTarget,
        *,
        connection: Connection | None = None,
    ) -> ConditionFacts: ...


@dataclass(frozen=True)
class CurrentCapabilityItem:
    reference_bytes: bytes
    release_current: bool | None
    license_current: bool | None
    available: bool | None
    source_identity: str
    source_version: str
    evidence_ref: str
    valid_until: datetime


@dataclass(frozen=True)
class CurrentCapabilityState:
    connection: Connection
    transaction: object
    mode: str
    items: tuple[CurrentCapabilityItem, ...]


class CurrentCapabilityStateReader(Protocol):
    """Every required handler/model reference, real source and same-root evidence."""

    def read(
        self,
        context: TaskCreationContext,
        observation: TaskPlanMetadataObservation,
        *,
        connection: Connection,
    ) -> CurrentCapabilityState | None: ...


def _references(observation: TaskPlanMetadataObservation) -> tuple[bytes, ...]:
    refs: set[bytes] = set()
    for handler in observation.as_dict()["required_capability_refs"]["handlers"]:
        refs.add(_canonical(dict(kind="handler", reference=handler)))
        for model in handler["model_dependencies"]:
            refs.add(_canonical(dict(kind="model", reference=model)))
    return tuple(sorted(refs))


class TaskCreationFactsReader:
    def __init__(
        self,
        authority: SqlTaskPlanAuthority,
        *,
        capability_reader: CurrentCapabilityStateReader | None = None,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self.authority, self.capability_reader, self.clock = authority, capability_reader, clock

    def _capabilities(
        self,
        context: TaskCreationContext,
        observation: TaskPlanMetadataObservation,
        connection: Connection,
        now: datetime,
    ) -> tuple[bool | None, bytes, datetime | None]:
        if self.capability_reader is None:
            return None, _canonical(dict(provider=None)), None
        try:
            transaction = connection.get_transaction()
            expected = _references(observation)
            detached_context = _context_copy(context, lambda: now.timestamp())
            detached_observation = _metadata_copy(detached_context, observation, self.authority.budgets, now)
            state = self.capability_reader.read(detached_context, detached_observation, connection=connection)
            if state is None:
                return None, _canonical(dict(provider=None)), None
            root, scope = current_scope_transaction(), current_data_scope()
            mode = "LOOKUP_READ_ONLY" if scope is not None and scope.mode is AccessMode.LOOKUP else "CASE_SHARE_LOCKED"
            if (
                type(state) is not CurrentCapabilityState
                or root is None
                or root.connection is not connection
                or not connection.in_transaction()
                or state.connection is not connection
                or state.transaction is not transaction
                or connection.get_transaction() is not transaction
                or state.transaction is None
                or state.mode != mode
                or type(state.items) is not tuple
                or len(state.items) != len(expected)
            ):
                raise _unavailable()
            statuses: list[bool | None] = []
            facts = []
            deadlines = []
            for item, wanted in zip(state.items, expected, strict=True):
                if type(item) is not CurrentCapabilityItem or type(item.reference_bytes) is not bytes:
                    raise _unavailable()
                if (
                    item.reference_bytes != wanted
                    or _canonical(_load(item.reference_bytes, self.authority.budgets)) != wanted
                ):
                    raise _unavailable()
                values = (item.release_current, item.license_current, item.available)
                if any(value is not None and type(value) is not bool for value in values):
                    raise _unavailable()
                for value in (item.source_identity, item.source_version, item.evidence_ref):
                    _fact_text(value, self.authority.budgets)
                deadline = _utc(item.valid_until)
                if deadline <= now:
                    raise _unavailable()
                deadlines.append(deadline)
                statuses.extend(values)
                # The release/licence basis ref is stable and must invalidate
                # authorization when changed. Transaction objects, phase,
                # observed_at and renewable deadlines are not stable facts.
                facts.append(
                    dict(
                        reference=_load(wanted, self.authority.budgets),
                        release_current=item.release_current,
                        license_current=item.license_current,
                        available=item.available,
                        source_identity=item.source_identity,
                        source_version=item.source_version,
                        evidence_ref=item.evidence_ref,
                    )
                )
            raw = _canonical(dict(items=facts))
            _load(raw, self.authority.budgets)
            result = (
                False
                if any(value is False for value in statuses)
                else None
                if any(value is None for value in statuses)
                else True
            )
            return result, raw, min(deadlines)
        except Exception:
            raise _unavailable() from None

    def read(
        self,
        principal: Principal,
        operation_id: str,
        target: RuleTarget,
        *,
        connection: Connection | None = None,
    ) -> ConditionFacts:
        now = _time(self.clock)
        context = current_task_creation_context(clock=lambda: now.timestamp())
        principal = _principal_copy(principal, lambda: now.timestamp())
        if (
            context is None
            or principal != context.principal
            or type(target) is not RuleTarget
            or operation_id != "createTask"
            or (target.org_id, target.kind, target.object_id, target.case_id, target.purpose, target.request_digest)
            != (
                principal.actor.org_id,
                "asset",
                context.request.asset_id,
                context.request.case_id,
                "analysis",
                context.authorization_request_digest,
            )
            or target.policy_kind is not None
            or target.source_ids
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if connection is None:
            if current_scope_transaction() is not None or current_authorization() is not None:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            port = SqlScopeLookup(self.authority.database, clock=lambda: _time(self.clock).timestamp())
            with port.connection(principal, operation_id, LookupKey("asset", context.request.asset_id)) as current:
                return self.read(principal, operation_id, target, connection=current)
        observation = _metadata_copy(
            context, self.authority.read_metadata(context, connection=connection), self.authority.budgets, now
        )
        row = observation.as_dict()
        if target.object_version is not None and (
            type(target.object_version) is not int
            or target.object_version != row["current_state_facts"]["asset"]["version"]
        ):
            raise BusinessError("AUTHORIZATION_OBJECT_STALE", 409)
        capability, capability_bytes, capability_deadline = self._capabilities(context, observation, connection, now)
        # Take the finite database/mapping bound before converting a potentially
        # very large, merely shape-checked Principal epoch value to float.
        deadlines: list[int | float] = [principal.expires_at, _sql_timestamp(row["valid_until"]).timestamp()]
        facts = row["current_state_facts"]
        for item in (facts["source"], *facts["memberships"]):
            if item["expires_at"] is not None:
                deadlines.append(_sql_timestamp(item["expires_at"]).timestamp())
        if capability_deadline is not None:
            deadlines.append(capability_deadline.timestamp())
        deadline = float(min(deadlines))
        # The observation contains only fixed mapping windows, never a sampled
        # time/renewable Proof deadline. A different actual source/version changes it.
        stable = _canonical(
            dict(
                metadata_sha256=observation.sha256,
                authorization_request_digest=context.authorization_request_digest,
                capability_sha256=hashlib.sha256(capability_bytes).hexdigest(),
            )
        )
        final = _time(self.clock)
        self.authority._context(context, connection, final)
        if deadline <= final.timestamp():
            raise _unavailable()
        return ConditionFacts(
            context.principal,
            target,
            MappingProxyType(dict(model_task_version=None, capability=capability)),
            hashlib.sha256(stable).hexdigest(),
            deadline,
        )
