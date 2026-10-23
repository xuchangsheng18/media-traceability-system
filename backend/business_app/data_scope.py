"""Immutable server-side data bindings; a binding is never an ALLOW decision."""

import hashlib
import json
import math
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from uuid import UUID

from .errors import BusinessError
from .identity.directory import valid_key
from .permissions.context import Evidence
from .permissions.policy import validate_principal
from .permissions.rule_types import AuthorizationEvidence, RuleTarget, WorkAuthorizationEvidence
from .permissions.work_subject import WORK_OPERATIONS, validate_execution_subject
from .scope_catalog import LOOKUP_KINDS, RESOURCE_BINDING_KINDS, lookup_spec, registered_operation
from .types import Actor, JsonValue


def _invalid() -> BusinessError:
    return BusinessError("AUTHORITY_SCOPE_INVALID", 503)


def _uuid(value: object) -> bool:
    return isinstance(value, UUID) and value.int != 0


def _version(value: object) -> bool:
    return type(value) is int and value > 0


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _actor(actor: object) -> bool:
    return isinstance(actor, Actor) and _uuid(actor.user_id) and _uuid(actor.org_id)


class AccessMode(str, Enum):
    CASE = "CASE"
    ORGANIZATION = "ORGANIZATION"
    LOOKUP = "LOOKUP"


@dataclass(frozen=True)
class LookupKey:
    kind: str
    identifier: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str) or self.kind not in LOOKUP_KINDS or not _uuid(self.identifier):
            raise _invalid()


@dataclass(frozen=True)
class TaskBinding:
    task_id: UUID
    run_version: int | None = None
    result_version: int | None = None

    def __post_init__(self) -> None:
        if (
            not _uuid(self.task_id)
            or (self.run_version is not None and not _version(self.run_version))
            or (self.result_version is not None and not _version(self.result_version))
            or (self.result_version is not None and self.run_version is None)
        ):
            raise _invalid()


@dataclass(frozen=True)
class ResourceBinding:
    kind: str
    identifier: UUID
    row_version: int | None = None
    task: TaskBinding | None = None
    part_no: int | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.kind, str)
            or self.kind not in RESOURCE_BINDING_KINDS
            or not _uuid(self.identifier)
            or (self.row_version is not None and not _version(self.row_version))
            or (self.task is not None and not isinstance(self.task, TaskBinding))
            or (self.kind == "upload_part" and not _version(self.part_no))
            or (self.kind != "upload_part" and self.part_no is not None)
        ):
            raise _invalid()


@dataclass(frozen=True)
class DataScope:
    actor: Actor
    mode: AccessMode
    operation_id: str
    case_id: UUID | None
    lookup: LookupKey | None
    task_binding: TaskBinding | None
    evidence_binding: str | None

    def __post_init__(self) -> None:
        if not _actor(self.actor) or type(self.mode) is not AccessMode or not registered_operation(self.operation_id):
            raise _invalid()
        if self.mode is AccessMode.CASE:
            valid = _uuid(self.case_id) and self.lookup is None and _digest(self.evidence_binding)
            valid = valid and (self.task_binding is None or isinstance(self.task_binding, TaskBinding))
        elif self.mode is AccessMode.ORGANIZATION:
            valid = (
                self.case_id is None
                and self.lookup is None
                and self.task_binding is None
                and _digest(self.evidence_binding)
            )
        else:
            valid = (
                self.case_id is None
                and isinstance(self.lookup, LookupKey)
                and self.task_binding is None
                and self.evidence_binding is None
            )
            if valid and self.lookup is not None:
                valid = self.operation_id in lookup_spec(self.lookup.kind).operation_ids
        if not valid:
            raise _invalid()


@dataclass(frozen=True)
class ScopeMetadata:
    target: RuleTarget
    projection: Mapping[str, JsonValue]
    condition_checks: Mapping[str, bool | None]
    version_digest: str
    valid_until: float


def from_evidence(evidence: Evidence, *, clock: Callable[[], float] = time.time) -> DataScope:
    """Bind an existing verified proof, without authenticating or granting it."""
    try:
        current = clock()
    except Exception:
        raise _invalid() from None
    if (
        type(current) not in (int, float)
        or not math.isfinite(current)
        or not isinstance(evidence, (AuthorizationEvidence, WorkAuthorizationEvidence))
        or not isinstance(evidence.target, RuleTarget)
        or type(evidence.valid_until) not in (int, float)
        or not math.isfinite(evidence.valid_until)
        or evidence.valid_until <= current
        or not valid_key(evidence.policy_version, 1024)
        or not valid_key(evidence.recovery_generation, 1024)
        or not _digest(evidence.role_digest)
        or not _digest(evidence.condition_digest)
    ):
        raise _invalid()
    if isinstance(evidence, AuthorizationEvidence):
        validate_principal(evidence.principal, lambda: current)
        actor = evidence.principal.actor
        subject: object = dict(
            actor=asdict(actor), issuer=evidence.principal.issuer, subject=evidence.principal.subject
        )
    else:
        validate_execution_subject(evidence.subject)
        actor = evidence.subject.actor
        subject = asdict(evidence.subject)
        operation = WORK_OPERATIONS.get(evidence.operation_id)
        if (
            operation is None
            or operation[2] != evidence.subject.work_kind
            or evidence.target.object_id != evidence.subject.work_id
        ):
            raise _invalid()
    target = evidence.target
    if not isinstance(target, RuleTarget) or not _actor(actor) or target.org_id != actor.org_id:
        raise _invalid()
    from .permissions.object_facts import ObjectFactsReader

    ObjectFactsReader._validate_target(evidence.operation_id, target)
    if (
        (target.object_id is not None and not _uuid(target.object_id))
        or (target.case_id is not None and not _uuid(target.case_id))
        or any(not _uuid(value) for value in target.source_ids)
    ):
        raise _invalid()
    if target.case_id is None and target.kind not in {
        "user",
        "policy",
        "policy_collection",
        "model_release",
        "model_operation",
        "model_collection",
        "model",
        "model_evaluation",
        "approval",
        "feedback",
    }:
        raise _invalid()
    if target.case_id is None and target.kind in {"approval", "feedback"} and target.purpose != "model_release":
        raise _invalid()
    target_binding = asdict(target)
    target_binding["source_ids"] = sorted(str(value) for value in target.source_ids)
    payload = dict(
        subject=subject,
        operation=evidence.operation_id,
        target=target_binding,
        policy=evidence.policy_version,
        recovery_generation=evidence.recovery_generation,
    )
    binding = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False).encode()
    ).hexdigest()
    return DataScope(
        actor,
        AccessMode.CASE if target.case_id is not None else AccessMode.ORGANIZATION,
        evidence.operation_id,
        target.case_id,
        None,
        TaskBinding(target.object_id) if target.kind == "task" and target.object_id is not None else None,
        binding,
    )
