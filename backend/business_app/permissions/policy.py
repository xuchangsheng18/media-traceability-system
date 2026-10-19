"""An explicit policy decision is mandatory; directory facts cannot grant access."""

import math
import re
import time
from collections.abc import Callable
from uuid import UUID

from ..errors import BusinessError
from ..identity.directory import valid_key
from ..types import Actor
from .types import (
    PermissionDecision,
    PermissionFact,
    PermissionPolicy,
    PermissionReader,
    Principal,
)


def validate_principal(principal: Principal, clock: Callable[[], float]) -> None:
    if (
        not isinstance(principal, Principal)
        or not isinstance(principal.actor, Actor)
        or not isinstance(principal.actor.user_id, UUID)
        or not isinstance(principal.actor.org_id, UUID)
        or not valid_key(principal.issuer, 2048)
        or not valid_key(principal.subject, 1024)
        or type(principal.expires_at) is not int
    ):
        raise BusinessError("AUTHORITY_ACTOR_INVALID", 503)
    try:
        current = clock()
        valid_clock = type(current) in (int, float) and math.isfinite(current)
    except Exception:
        valid_clock = False
        current = 0.0
    if not valid_clock:
        raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
    if principal.expires_at <= current:
        raise BusinessError("AUTHENTICATION_REQUIRED", 401)


class DirectoryPermissionAuthority:
    def __init__(
        self,
        reader: PermissionReader,
        policy: PermissionPolicy | None,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.reader, self.policy, self.clock = reader, policy, clock

    def _read_fact(self, principal: Principal, permission: str) -> PermissionFact:
        try:
            fact = self.reader.read(principal, permission)
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        validate_principal(principal, self.clock)
        if (
            not isinstance(fact, PermissionFact)
            or fact.principal != principal
            or fact.permission != permission
            or type(fact.eligible) is not bool
            or not isinstance(fact.version_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", fact.version_digest) is None
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        return fact

    def check(self, principal: Principal, permission: str) -> None:
        validate_principal(principal, self.clock)
        if not valid_key(permission, 1024):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if self.policy is None:
            raise BusinessError("FORMAL_POLICY_UNCONFIGURED", 503)
        try:
            version = self.policy.version
            if not valid_key(version, 1024):
                raise ValueError()
        except Exception:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        fact = self._read_fact(principal, permission)
        if not fact.eligible:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        try:
            decision = self.policy.decide(fact)
            stable_version = self.policy.version == version
        except Exception:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        validate_principal(principal, self.clock)
        if (
            not stable_version
            or not isinstance(decision, PermissionDecision)
            or decision.actor != principal.actor
            or decision.permission != permission
            or type(decision.allowed) is not bool
            or decision.policy_version != version
            or decision.fact_digest != fact.version_digest
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if not decision.allowed:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        # Policy evaluation may perform network work. Never return its ALLOW if
        # the exact directory basis changed while that decision was in flight.
        current = self._read_fact(principal, permission)
        if not current.eligible:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        try:
            stable_version = self.policy.version == version
        except Exception:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        if current.version_digest != fact.version_digest or not stable_version:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
