"""Mandatory object conditions after function eligibility, with no cached ALLOW."""

import math
import re
import time
from collections.abc import Callable, Mapping
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import Connection

from ..contracts import ROOT
from ..errors import BusinessError
from .catalog import load_catalog
from .object_facts import ObjectFactsReader, digest
from .policy import validate_principal
from .rule_types import (
    AuthorizationEvidence,
    ConditionFacts,
    ExecutionSubject,
    RoleFacts,
    RoleFactsReader,
    RuleTarget,
    WorkAuthorizationEvidence,
    WorkConditionFacts,
    WorkRoleFacts,
)
from .six_role import SixRoleRules
from .types import Principal
from .work import WorkTrust
from .work_subject import WORK_OPERATIONS, validate_execution_subject

# Each branch is an AND. A complete branch may allow; half of two branches may not.
REQUIREMENTS: Mapping[str, tuple[str, ...]] = {
    "SELF": ("same_org", "self"),
    "SOURCE": ("same_org", "case"),
    "SOURCE_WRITE": ("same_org", "case", "authoritative_source_sync"),
    "INGEST": ("same_org", "case", "source", "source_purpose", "classification", "purpose_basis"),
    "CASE_READ": ("same_org", "case", "source", "read_purpose", "classification"),
    "CASE_ANALYSIS": ("same_org", "case", "source", "analysis_purpose", "capability", "classification"),
    "TASK_CREATE": (
        "same_org",
        "case",
        "source",
        "analysis_purpose",
        "model_task_version",
        "capability",
        "classification",
    ),
    "TASK_CONTROL": ("same_org", "case", "control_authorized"),
    "REVIEW": ("same_org", "case", "review_assignment", "independent_person", "classification"),
    "REQUEST_CASE": ("same_org", "case", "case_request_purpose", "case_responsibility", "object_binding"),
    "REQUEST_CASE_READ": ("same_org", "case", "own_or_delegated_request", "metadata_scope"),
    "APPROVAL_CASE_READ": ("same_org", "case", "review_assignment", "metadata_scope"),
    "APPROVE_CASE": (
        "same_org",
        "case",
        "case_request_purpose",
        "review_assignment",
        "independent_person",
        "object_binding",
    ),
    "REVOKE_CASE": ("same_org", "case", "review_assignment", "case_responsibility"),
    "REQUEST_DATA": ("same_org", "case", "training_request", "source_purpose", "case_responsibility", "object_binding"),
    "REQUEST_DATA_READ": ("same_org", "case", "own_or_delegated_request", "training_request", "metadata_scope"),
    "FEEDBACK_OWN": ("same_org", "case", "owner", "metadata_scope"),
    "FEEDBACK_REVIEW": ("same_org", "case", "review_assignment", "metadata_scope"),
    "MODEL": ("same_org", "model_metadata_scope"),
    "REQUEST_MODEL": ("same_org", "organization_approval_adapter"),
    "REQUEST_MODEL_READ": ("same_org", "organization_approval_adapter"),
    "APPROVE_MODEL": ("same_org", "organization_approval_adapter", "release_qualification", "independent_person"),
    "REVOKE_MODEL": ("same_org", "organization_approval_adapter", "release_assignment"),
    "POLICY_RETENTION": ("same_org", "policy_retention"),
    "POLICY_ALGORITHM": ("same_org", "policy_algorithm"),
    "POLICY_BUSINESS": ("same_org", "policy_business"),
    "AUDIT_READ": ("same_org", "case", "audit_delegation", "audit_metadata_scope"),
    "AUDIT_EXPORT": (
        "same_org",
        "case",
        "audit_delegation",
        "audit_window_fields_quota",
        "independent_person",
        "object_binding",
    ),
    "REQUEST_AUDIT": ("same_org", "case", "audit_request", "audit_delegation", "object_binding"),
    "REQUEST_AUDIT_READ": ("same_org", "case", "owner", "audit_delegation", "metadata_scope"),
}


class ConditionalPort(Protocol):
    def authorize_http(
        self,
        principal: Principal,
        operation_id: str,
        path: Mapping[str, Any],
        query: Mapping[str, Any],
        body: Mapping[str, Any],
    ) -> AuthorizationEvidence: ...
    def policy_kinds(self, principal: Principal) -> tuple[str, ...]: ...
    def review_ids(
        self, principal: Principal, operation_id: str, case_id: UUID, *, connection: Connection
    ) -> tuple[UUID, ...]: ...


class ConditionalPermissionAuthority:
    def __init__(
        self,
        reader: RoleFactsReader,
        rules: SixRoleRules,
        objects: ObjectFactsReader,
        *,
        clock: Callable[[], float] = time.time,
        work_trust: WorkTrust | None = None,
    ) -> None:
        self.reader, self.rules, self.objects, self.clock = reader, rules, objects, clock
        self.work_trust = work_trust
        self.catalog = load_catalog(ROOT)

    def _roles(self, principal: Principal, permission: str, connection: Connection | None) -> RoleFacts:
        value = self.reader.read_roles(principal, permission, connection=connection)
        if not isinstance(value, RoleFacts) or value.principal != principal or value.permission != permission:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        self.rules.entry(value)
        return value

    def _facts(
        self, principal: Principal, operation_id: str, target: RuleTarget, connection: Connection | None
    ) -> ConditionFacts:
        value = self.objects.read(principal, operation_id, target, connection=connection)
        if (
            not isinstance(value, ConditionFacts)
            or value.principal != principal
            or value.target != target
            or not isinstance(value.version_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", value.version_digest) is None
            or type(value.valid_until) not in (int, float)
            or not math.isfinite(value.valid_until)
            or value.valid_until <= self.clock()
            or not isinstance(value.checks, Mapping)
            or any(not isinstance(k, str) or (v is not None and type(v) is not bool) for k, v in value.checks.items())
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return value

    def authorize(
        self, principal: Principal, operation_id: str, target: RuleTarget, *, connection: Connection | None = None
    ) -> AuthorizationEvidence:
        validate_principal(principal, self.clock)
        operation = self.catalog.get(operation_id)
        if operation is None or operation_id not in self.objects.supported_operation_ids:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        snapshot = self.rules.snapshot
        fact = self._roles(principal, operation.permission, connection)
        branches = self.rules.entry(fact)
        conditions = self._facts(principal, operation_id, target, connection)
        complete = False
        missing = False
        for branch in branches:
            names = REQUIREMENTS.get(branch)
            if names is None:
                missing = True
                continue
            values = tuple(conditions.checks.get(name) for name in names)
            if all(value is True for value in values):
                complete = True
            elif False not in values:
                missing = True
        if not complete:
            raise BusinessError(
                "CONDITIONAL_FACTS_UNAVAILABLE" if missing else "PERMISSION_REQUIRED", 503 if missing else 403
            )
        current_roles = self._roles(principal, operation.permission, connection)
        current_conditions = self._facts(principal, operation_id, target, connection)
        self.rules.validate_snapshot()
        if (
            current_roles.version_digest != fact.version_digest
            or current_conditions.version_digest != conditions.version_digest
            or current_conditions.checks != conditions.checks
            or self.rules.snapshot != snapshot
        ):
            raise BusinessError("AUTHORIZATION_CHANGED", 503)
        return AuthorizationEvidence(
            principal,
            operation_id,
            target,
            fact.version_digest,
            conditions.version_digest,
            snapshot.version,
            snapshot.recovery_generation,
            min(
                conditions.valid_until,
                current_conditions.valid_until,
                float(snapshot.valid_until),
                float(principal.expires_at),
            ),
        )

    def authorize_http(
        self,
        principal: Principal,
        operation_id: str,
        path: Mapping[str, Any],
        query: Mapping[str, Any],
        body: Mapping[str, Any],
    ) -> AuthorizationEvidence:
        target = self.objects.resolve_http(principal, operation_id, path, query, body)
        return self.authorize(principal, operation_id, target)

    def _work_roles(self, subject: ExecutionSubject, permission: str, connection: Connection | None) -> WorkRoleFacts:
        port = getattr(self.reader, "read_for_work", None)
        if not callable(port):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        value = port(subject, permission, connection=connection)
        if not isinstance(value, WorkRoleFacts) or value.subject != subject or value.permission != permission:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        self.rules.entry(value)
        return value

    def _work_facts(
        self, subject: ExecutionSubject, operation_id: str, target: RuleTarget, connection: Connection | None
    ) -> WorkConditionFacts:
        value = self.objects.read_for_work(subject, operation_id, target, connection=connection)
        if (
            not isinstance(value, WorkConditionFacts)
            or value.subject != subject
            or value.target != target
            or not isinstance(value.version_digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", value.version_digest) is None
            or type(value.valid_until) not in (int, float)
            or not math.isfinite(value.valid_until)
            or value.valid_until <= self.clock()
            or not isinstance(value.checks, Mapping)
            or any(not isinstance(k, str) or (v is not None and type(v) is not bool) for k, v in value.checks.items())
        ):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return value

    def authorize_work(
        self, subject: ExecutionSubject, operation_id: str, target: RuleTarget, *, connection: Connection | None = None
    ) -> WorkAuthorizationEvidence:
        validate_execution_subject(subject)
        operation = WORK_OPERATIONS.get(operation_id)
        if (
            operation is None
            or operation[2] != subject.work_kind
            or target.kind != operation[1]
            or target.object_id != subject.work_id
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if self.work_trust is None:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        snapshot = self.rules.snapshot
        trusted = self.work_trust.read(subject)
        roles = self._work_roles(subject, operation[0], connection)
        branches = self.rules.entry(roles)
        conditions = self._work_facts(subject, operation_id, target, connection)
        complete = False
        missing = False
        for branch in branches:
            names = REQUIREMENTS.get(branch)
            if names is None:
                missing = True
                continue
            values = tuple(conditions.checks.get(name) for name in names)
            if all(v is True for v in values):
                complete = True
            elif False not in values:
                missing = True
        if not complete:
            raise BusinessError(
                "CONDITIONAL_FACTS_UNAVAILABLE" if missing else "PERMISSION_REQUIRED", 503 if missing else 403
            )
        current_roles = self._work_roles(subject, operation[0], connection)
        current_conditions = self._work_facts(subject, operation_id, target, connection)
        current_trusted = self.work_trust.read(subject)
        self.rules.validate_snapshot()
        if (
            current_roles.version_digest != roles.version_digest
            or current_conditions.version_digest != conditions.version_digest
            or current_conditions.checks != conditions.checks
            or trusted.version_digest != current_trusted.version_digest
            or self.rules.snapshot != snapshot
        ):
            raise BusinessError("AUTHORIZATION_CHANGED", 503)
        return WorkAuthorizationEvidence(
            subject,
            operation_id,
            target,
            roles.version_digest,
            digest([conditions.version_digest, trusted.version_digest]),
            snapshot.version,
            snapshot.recovery_generation,
            min(
                roles.valid_until,
                current_roles.valid_until,
                conditions.valid_until,
                current_conditions.valid_until,
                trusted.valid_until,
                current_trusted.valid_until,
                float(snapshot.valid_until),
            ),
        )

    def policy_kinds(self, principal: Principal) -> tuple[str, ...]:
        fact = self._roles(principal, "policy.read", None)
        branches = self.rules.entry(fact)
        allowed: set[str] = set()
        kinds = {
            "POLICY_RETENTION": ("retention",),
            "POLICY_ALGORITHM": ("threshold", "analysis"),
            "POLICY_BUSINESS": ("risk_taxonomy", "review"),
        }
        for branch in branches:
            allowed.update(kinds.get(branch, ()))
        fresh = self._roles(principal, "policy.read", None)
        if fresh.version_digest != fact.version_digest:
            raise BusinessError("AUTHORIZATION_CHANGED", 503)
        if not allowed:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        return tuple(sorted(allowed))

    def review_ids(
        self, principal: Principal, operation_id: str, case_id: UUID, *, connection: Connection
    ) -> tuple[UUID, ...]:
        if operation_id not in {"listReviews", "listPendingReviews"}:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        binding = digest(["review_page", operation_id, str(case_id)])
        collection = RuleTarget(
            principal.actor.org_id, "case", case_id, None, case_id, None, None, request_digest=binding
        )
        self.authorize(principal, operation_id, collection, connection=connection)
        kind = "review" if operation_id == "listReviews" else "task"
        allowed: list[UUID] = []
        for item in self.objects.review_candidates(connection, operation_id, principal.actor.org_id, case_id):
            target = RuleTarget(
                principal.actor.org_id,
                kind,
                item["id"],
                item["row_version"],
                case_id,
                None,
                None,
                request_digest=binding,
            )
            try:
                self.authorize(principal, operation_id, target, connection=connection)
            except BusinessError as error:
                if error.http_status not in {403, 404}:
                    raise
            else:
                allowed.append(item["id"])
        return tuple(sorted(allowed, key=str))
