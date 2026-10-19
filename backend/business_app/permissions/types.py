"""Identity context shared by authentication and permission adapters."""

from dataclasses import dataclass

from ..types import Actor


@dataclass(frozen=True)
class Principal:
    actor: Actor
    issuer: str
    subject: str
    expires_at: int
