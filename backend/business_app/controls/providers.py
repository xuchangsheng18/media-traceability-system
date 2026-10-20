"""Trusted integration ports. No development success provider is installed by the app."""

import re
from dataclasses import dataclass, field
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
class OperationTokenRule:
    action: str
    version: str
    ttl_seconds: int

    def __post_init__(self) -> None:
        if (
            self.action != "sealEvidence"
            or not isinstance(self.version, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", self.version) is None
            or type(self.ttl_seconds) is not int
            or self.ttl_seconds <= 0
        ):
            raise ValueError("EXPLICIT_OPERATION_TOKEN_RULE_REQUIRED")


@dataclass(frozen=True)
class OperationTokenKey:
    key_id: str
    material: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.key_id, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", self.key_id) is None
            or type(self.material) is not bytes
            or not 32 <= len(self.material) <= 128
        ):
            raise ValueError("EXPLICIT_INDEPENDENT_OPERATION_TOKEN_KEY_REQUIRED")


class OperationTokenRules(Protocol):
    def resolve(self, scope: Scope, approval: dict[str, Any]) -> OperationTokenRule: ...


class OperationTokenKeys(Protocol):
    def current(self) -> OperationTokenKey: ...

    def get(self, key_id: str) -> OperationTokenKey: ...


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
