"""Trusted work delegation and independent service facts, never a stored user Bearer."""

from __future__ import annotations

import math
import re
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from ..data_scope import LookupKey
from ..db import Database
from ..errors import BusinessError
from ..identity.directory import valid_key
from ..scope_lookup import SqlScopeLookup
from ..types import Actor, Scope
from .context import FencePort, request_authorization
from .object_facts import digest
from .rule_types import ExecutionSubject, RuleTarget
from .work_subject import WORK_OPERATIONS, WORK_TABLES, validate_execution_subject

if TYPE_CHECKING:
    from .conditional import ConditionalPermissionAuthority


@dataclass(frozen=True)
class WorkDelegation:
    subject: ExecutionSubject
    version_digest: str
    valid_until: float


@dataclass(frozen=True)
class WorkServiceProof:
    service_id: str
    work_kind: str
    work_id: UUID
    version_digest: str
    valid_until: float


@dataclass(frozen=True)
class WorkTrustFacts:
    subject: ExecutionSubject
    version_digest: str
    valid_until: float


class DelegationReader(Protocol):
    def read(self, actor: Actor, kind: str, identifier: UUID) -> WorkDelegation: ...


class WorkServiceReader(Protocol):
    def read(self, service_id: str, kind: str, identifier: UUID) -> WorkServiceProof: ...


def live(value: float, current: float) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > current


def valid_digest(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


class WorkTrust:
    def __init__(
        self,
        delegations: DelegationReader | None,
        services: WorkServiceReader | None,
        service_ids: Mapping[str, str],
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.delegations, self.services, self.clock = delegations, services, clock
        self.service_ids = MappingProxyType(dict(service_ids))

    def read(self, subject: ExecutionSubject) -> WorkTrustFacts:
        validate_execution_subject(subject)
        try:
            current = self.clock()
            if (
                type(current) not in (int, float)
                or not math.isfinite(current)
                or self.delegations is None
                or self.services is None
            ):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            delegation = self.delegations.read(subject.actor, subject.work_kind, subject.work_id)
            if (
                not isinstance(delegation, WorkDelegation)
                or delegation.subject != subject
                or not valid_digest(delegation.version_digest)
                or not live(delegation.valid_until, current)
            ):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            wanted = self.service_ids.get(subject.work_kind)
            if not isinstance(wanted, str) or not valid_key(wanted, 1024):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            proof = self.services.read(wanted, subject.work_kind, subject.work_id)
            if (
                not isinstance(proof, WorkServiceProof)
                or (proof.service_id, proof.work_kind, proof.work_id) != (wanted, subject.work_kind, subject.work_id)
                or not valid_digest(proof.version_digest)
                or not live(proof.valid_until, current)
            ):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            return WorkTrustFacts(
                subject,
                digest([delegation.version_digest, proof.version_digest, wanted]),
                min(delegation.valid_until, proof.valid_until),
            )
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None

    def resolve(self, scope: Scope, kind: str, identifier: UUID) -> ExecutionSubject:
        try:
            if self.delegations is None:
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            delegation = self.delegations.read(scope.actor, kind, identifier)
            if not isinstance(delegation, WorkDelegation):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            subject = delegation.subject
            validate_execution_subject(subject)
            if (subject.actor, subject.work_kind, subject.work_id) != (scope.actor, kind, identifier):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            self.read(subject)
            return subject
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None


class WorkAuthorizationManager:
    def __init__(
        self, database: Database, authority: ConditionalPermissionAuthority, fence: FencePort, trust: WorkTrust
    ) -> None:
        self.database, self.authority, self.fence, self.trust = database, authority, fence, trust

    @contextmanager
    def open(self, scope: Scope, kind: str, identifier: UUID, operation_id: str) -> Iterator[None]:
        try:
            operation = WORK_OPERATIONS.get(operation_id)
            if operation is None or operation[2] != kind or self.authority.work_trust is not self.trust:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            subject = self.trust.resolve(scope, kind, identifier)
            _, _, owner = WORK_TABLES[kind]
            located = SqlScopeLookup(self.database, work_trust=self.trust).read(
                subject, operation_id, LookupKey(operation[1], identifier)
            )
            job = cast(dict[str, Any], dict(located.projection))
            if (job["org_id"], job.get("case_id"), job.get(owner)) != (
                str(scope.actor.org_id),
                str(scope.case_id),
                str(scope.actor.user_id),
            ):
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            target = RuleTarget(
                scope.actor.org_id,
                operation[1],
                identifier,
                int(job["row_version"]),
                scope.case_id,
                "upload"
                if kind == "upload_validation"
                else "analysis"
                if kind == "task_execution"
                else job.get("purpose"),
                None,
            )
            evidence = self.authority.authorize_work(subject, operation_id, target)
            with request_authorization(evidence, self.fence, mutation=True):
                yield
        except BusinessError:
            raise
        except (SQLAlchemyError, RuntimeError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
