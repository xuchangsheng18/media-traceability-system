"""Internal, immutable rule facts. None of these types grants a business action."""

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


class RoleFactsReader(Protocol):
    def read_roles(
        self, principal: Principal, permission: str, *, connection: Connection | None = None
    ) -> RoleFacts: ...
