"""Identity context shared by authentication and permission adapters."""

from dataclasses import dataclass
from typing import Protocol

from ..types import Actor


@dataclass(frozen=True)
class Principal:
    actor: Actor
    issuer: str
    subject: str
    expires_at: int


@dataclass(frozen=True)
class PermissionFact:
    principal: Principal
    permission: str
    eligible: bool
    version_digest: str


@dataclass(frozen=True)
class PermissionDecision:
    actor: Actor
    permission: str
    allowed: bool
    policy_version: str
    fact_digest: str


class PermissionReader(Protocol):
    def read(self, principal: Principal, permission: str) -> PermissionFact: ...


class PermissionPolicy(Protocol):
    @property
    def version(self) -> str: ...

    def decide(self, fact: PermissionFact) -> PermissionDecision: ...


class PermissionAuthority(Protocol):
    def check(self, principal: Principal, permission: str) -> None: ...
