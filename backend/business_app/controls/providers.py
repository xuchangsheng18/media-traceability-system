"""Trusted integration ports. No development success provider is installed by the app."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from ..types import Actor, Scope


@dataclass(frozen=True)
class ApprovalRule:
    version: str
    ttl_seconds: int
    independent_approvers: int

    def __post_init__(self) -> None:
        if not self.version or self.ttl_seconds <= 0 or self.independent_approvers not in (1, 2):
            raise ValueError("EXPLICIT_APPROVAL_RULE_REQUIRED")


@dataclass(frozen=True)
class ExportRule:
    version: str
    expires_at: datetime
    max_events: int
    max_bytes: int
    start_at: datetime
    end_at: datetime


class RuleProvider(Protocol):
    def approval(self, scope: Scope, purpose: str, version: str) -> ApprovalRule: ...

    def review(self, scope: Scope, version: str, decision: str) -> None: ...

    def audit_export(self, scope: Scope, purpose: str) -> ExportRule: ...

    def cancellation(self, scope: Scope, approval_id: UUID | None) -> None: ...


class DefinitionProvider(Protocol):
    def resolve(self, actor: Actor, reference: str, version: str) -> dict[str, Any]: ...


class IdentityDirectory(Protocol):
    def current(self, actor: Actor) -> dict[str, Any]: ...


class DeploymentOperations(Protocol):
    def get(self, actor: Actor, operation_id: UUID) -> dict[str, Any]: ...


class SourceSynchronization(Protocol):
    def current(self, scope: Scope, source_id: UUID) -> dict[str, Any]: ...
