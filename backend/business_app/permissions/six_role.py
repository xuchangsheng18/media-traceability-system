"""Confirmed isolated rule input. This module never installs a shared or formal policy."""

import math
import re
import time
from collections.abc import Callable, Mapping
from types import MappingProxyType
from uuid import UUID

from ..controls.providers import ApprovalRule
from ..errors import BusinessError
from ..identity.directory import valid_key
from .policy import validate_principal
from .rule_types import ActiveRole, RoleFacts, RoleFactsReader, RuleSnapshot
from .types import Principal

INPUT_VERSION = "t014-six-role-proposal-20261020-v1"
INPUT_SHA256 = "bac79b7512c004f657188b4fbfc2832c750b1064c1a42d16d419c789ffb2567d"
ROLE_CODES = frozenset(
    ["system_admin", "data_admin", "algorithm_admin", "business_reviewer", "case_investigator", "auditor"]
)
CELL_CONDITIONS: Mapping[str, Mapping[str, str | None]] = MappingProxyType(
    {
        "approval.decide": MappingProxyType(
            {
                "algorithm_admin": "APPROVE_MODEL",
                "auditor": None,
                "business_reviewer": "APPROVE_CASE",
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "approval.read": MappingProxyType(
            {
                "algorithm_admin": "REQUEST_MODEL_READ",
                "auditor": "REQUEST_AUDIT_READ",
                "business_reviewer": "APPROVAL_CASE_READ",
                "case_investigator": "REQUEST_CASE_READ",
                "data_admin": "REQUEST_DATA_READ",
                "system_admin": None,
            }
        ),
        "approval.request": MappingProxyType(
            {
                "algorithm_admin": "REQUEST_MODEL",
                "auditor": "REQUEST_AUDIT",
                "business_reviewer": "REQUEST_CASE",
                "case_investigator": "REQUEST_CASE",
                "data_admin": "REQUEST_DATA",
                "system_admin": None,
            }
        ),
        "approval.revoke": MappingProxyType(
            {
                "algorithm_admin": "REVOKE_MODEL",
                "auditor": None,
                "business_reviewer": "REVOKE_CASE",
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "asset.download": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_DOWNLOAD",
                "case_investigator": "CASE_DOWNLOAD",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "asset.import": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "INGEST",
                "data_admin": "INGEST",
                "system_admin": None,
            }
        ),
        "asset.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_READ",
                "case_investigator": "CASE_READ",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "asset.search": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "CASE_SEARCH",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "asset.upload": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "INGEST",
                "data_admin": "INGEST",
                "system_admin": None,
            }
        ),
        "audit.export": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": "AUDIT_EXPORT",
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "audit.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": "AUDIT_READ",
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "claim.analyze": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "CASE_ANALYSIS",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "development.login": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "evidence.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_READ",
                "case_investigator": "CASE_READ",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "evidence.seal": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "SEAL",
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "feedback.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "FEEDBACK_REVIEW",
                "case_investigator": "FEEDBACK_OWN",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "feedback.request": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "FEEDBACK_REQUEST",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "health.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": "OPS",
            }
        ),
        "identity.read": MappingProxyType(
            {
                "algorithm_admin": "SELF",
                "auditor": "SELF",
                "business_reviewer": "SELF",
                "case_investigator": "SELF",
                "data_admin": "SELF",
                "system_admin": "SELF",
            }
        ),
        "index.manage": MappingProxyType(
            {
                "algorithm_admin": "INDEX",
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "model.evaluate": MappingProxyType(
            {
                "algorithm_admin": "MODEL",
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "model.manage": MappingProxyType(
            {
                "algorithm_admin": "MODEL",
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "model.read": MappingProxyType(
            {
                "algorithm_admin": "MODEL",
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "model.release": MappingProxyType(
            {
                "algorithm_admin": "MODEL_RELEASE",
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "operation.confirm": MappingProxyType(
            {
                "algorithm_admin": "CONFIRM_MODEL",
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "CONFIRM_CASE",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "origin.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_READ",
                "case_investigator": "CASE_READ",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "policy.manage": MappingProxyType(
            {
                "algorithm_admin": "POLICY_ALGORITHM",
                "auditor": None,
                "business_reviewer": "POLICY_BUSINESS",
                "case_investigator": None,
                "data_admin": "POLICY_RETENTION",
                "system_admin": None,
            }
        ),
        "policy.read": MappingProxyType(
            {
                "algorithm_admin": "POLICY_ALGORITHM",
                "auditor": None,
                "business_reviewer": "POLICY_BUSINESS",
                "case_investigator": None,
                "data_admin": "POLICY_RETENTION",
                "system_admin": None,
            }
        ),
        "propagation.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_READ",
                "case_investigator": "CASE_READ",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "report.draft": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "REPORT_DRAFT",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "report.export": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "REPORT_EXPORT",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "report.generate": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "REPORT_GENERATE",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "report.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_READ",
                "case_investigator": "CASE_READ",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "review.perform": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "REVIEW",
                "case_investigator": None,
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "review.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_READ",
                "case_investigator": "CASE_READ",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "source.manage": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": None,
                "data_admin": "SOURCE_WRITE",
                "system_admin": None,
            }
        ),
        "source.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "SOURCE",
                "data_admin": "SOURCE",
                "system_admin": None,
            }
        ),
        "task.cancel": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "TASK_CONTROL",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "task.create": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "TASK_CREATE",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "task.read": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": "CASE_READ",
                "case_investigator": "CASE_READ",
                "data_admin": None,
                "system_admin": None,
            }
        ),
        "task.rerun": MappingProxyType(
            {
                "algorithm_admin": None,
                "auditor": None,
                "business_reviewer": None,
                "case_investigator": "TASK_CONTROL",
                "data_admin": None,
                "system_admin": None,
            }
        ),
    }
)


class SixRoleRules:
    def __init__(self, snapshot: RuleSnapshot, *, clock: Callable[[], float] = time.time) -> None:
        self.snapshot, self.clock = snapshot, clock

    def current_time(self) -> float:
        try:
            value = self.clock()
        except Exception:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        if type(value) not in (int, float) or not math.isfinite(value):
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        return float(value)

    def validate_snapshot(self) -> None:
        value = self.snapshot
        if (
            not isinstance(value, RuleSnapshot)
            or value.version != INPUT_VERSION
            or value.sha256 != INPUT_SHA256
            or not valid_key(value.recovery_generation, 1024)
            or type(value.valid_until) is not int
            or value.valid_until <= self.current_time()
        ):
            raise BusinessError("FORMAL_POLICY_UNCONFIGURED", 503)

    @property
    def version(self) -> str:
        self.validate_snapshot()
        return self.snapshot.version

    def entry(self, facts: RoleFacts) -> tuple[str, ...]:
        self.validate_snapshot()
        if not isinstance(facts, RoleFacts):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        validate_principal(facts.principal, self.clock)
        if (
            not isinstance(facts.permission, str)
            or facts.permission not in CELL_CONDITIONS
            or type(facts.eligible) is not bool
            or not isinstance(facts.version_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", facts.version_digest) is None
            or type(facts.active_roles) is not tuple
            or type(facts.permission_role_ids) is not tuple
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        current = self.current_time()
        for role in facts.active_roles:
            if (
                not isinstance(role, ActiveRole)
                or not isinstance(role.role_id, UUID)
                or not isinstance(role.binding_id, UUID)
                or not valid_key(role.code, 1024)
                or type(role.binding_version) is not int
                or role.binding_version <= 0
                or type(role.role_version) is not int
                or role.role_version <= 0
                or (
                    role.expires_at is not None
                    and (
                        type(role.expires_at) not in (int, float)
                        or not math.isfinite(role.expires_at)
                        or role.expires_at <= current
                    )
                )
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        ids = {r.role_id for r in facts.active_roles}
        codes = {r.code for r in facts.active_roles}
        if (
            len(ids) != len(facts.active_roles)
            or len(codes) != len(facts.active_roles)
            or len({r.binding_id for r in facts.active_roles}) != len(facts.active_roles)
            or any(not isinstance(value, UUID) for value in facts.permission_role_ids)
            or len(set(facts.permission_role_ids)) != len(facts.permission_role_ids)
            or not set(facts.permission_role_ids) <= ids
            or facts.eligible != bool(facts.permission_role_ids)
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if not facts.eligible or not codes <= ROLE_CODES:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        # Roles absent from the requested permission still participate in conflicts.
        if len(codes) != 1 and codes != {"data_admin", "case_investigator"}:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        branches = {
            CELL_CONDITIONS[facts.permission][role.code]
            for role in facts.active_roles
            if role.role_id in facts.permission_role_ids
        } - {None}
        if not branches:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        return tuple(sorted(str(branch) for branch in branches))

    def approval_rule(self, purpose: str, version: str) -> ApprovalRule:
        self.validate_snapshot()
        counts = dict(review=1, confirmation=1, seal=2, report_export=2, training_feedback=2, model_release=2)
        if purpose not in counts or version != self.snapshot.version:
            raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)
        return ApprovalRule(self.snapshot.version, 1800, counts[purpose])


class SixRoleEntryAuthority:
    def __init__(self, reader: RoleFactsReader, rules: SixRoleRules) -> None:
        self.reader, self.rules = reader, rules

    def _read(self, principal: Principal, permission: str) -> RoleFacts:
        try:
            value = self.reader.read_roles(principal, permission)
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        if not isinstance(value, RoleFacts) or value.principal != principal or value.permission != permission:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        self.rules.entry(value)
        return value

    def check(self, principal: Principal, permission: str) -> None:
        snapshot = self.rules.snapshot
        fact = self._read(principal, permission)
        current = self._read(principal, permission)
        if current.version_digest != fact.version_digest or self.rules.snapshot != snapshot:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        # This confirms only function eligibility. Object conditions remain mandatory.
