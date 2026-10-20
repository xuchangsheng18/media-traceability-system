"""Internal, immutable rule facts. None of these types grants a business action."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy import Connection

from .types import Principal


@dataclass(frozen=True)
class ActiveRole:
    role_id: UUID
    code: str
    binding_id: UUID
    binding_version: int
    role_version: int
    expires_at: float | None


@dataclass(frozen=True)
class RoleFacts:
    principal: Principal
    permission: str
    eligible: bool
    active_roles: tuple[ActiveRole, ...]
    permission_role_ids: tuple[UUID, ...]
    version_digest: str


@dataclass(frozen=True)
class RuleSnapshot:
    version: str
    sha256: str
    recovery_generation: str
    valid_until: int


@dataclass(frozen=True)
class RuleTarget:
    org_id: UUID
    kind: str
    object_id: UUID | None
    object_version: int | None
    case_id: UUID | None
    purpose: str | None
    policy_kind: str | None
    source_ids: tuple[UUID, ...] = ()
    request_digest: str | None = None


@dataclass(frozen=True)
class ConditionFacts:
    principal: Principal
    target: RuleTarget
    checks: Mapping[str, bool | None]
    version_digest: str
    valid_until: float


@dataclass(frozen=True)
class AuthorizationEvidence:
    principal: Principal
    operation_id: str
    target: RuleTarget
    role_digest: str
    condition_digest: str
    policy_version: str
    recovery_generation: str
    valid_until: float


class RoleFactsReader(Protocol):
    def read_roles(
        self, principal: Principal, permission: str, *, connection: Connection | None = None
    ) -> RoleFacts: ...
