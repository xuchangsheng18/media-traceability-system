"""Explicit synthetic permissions and isolated HTTP error harnesses, never deployment defaults."""

import hashlib
import time
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Any

from business_app.errors import BusinessError
from business_app.permissions.rule_types import AuthorizationEvidence, RuleTarget
from business_app.permissions.types import Principal
from business_app.types import Actor
from fastapi import FastAPI


class FixturePermissions:
    def __init__(self, actors: frozenset[Actor], permissions: frozenset[str]) -> None:
        self.actors, self.permissions = actors, permissions

    def check(self, principal: Principal, permission: str) -> None:
        if principal.actor not in self.actors or permission not in self.permissions:
            raise BusinessError("PERMISSION_REQUIRED", 403)


class FixtureConditionals:
    """Explicit old-business harness, not a six-role rule or production adapter."""

    def __init__(self, actors: frozenset[Actor]) -> None:
        self.actors = actors

    def authorize_http(
        self,
        principal: Principal,
        operation_id: str,
        path: Mapping[str, Any],
        query: Mapping[str, Any],
        body: Mapping[str, Any],
    ) -> AuthorizationEvidence:
        if principal.actor not in self.actors:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        target = RuleTarget(principal.actor.org_id, "explicit-synthetic-http-fixture", None, None, None, None, None)
        sha = hashlib.sha256(b"explicit isolated old-business fixture, not formal policy").hexdigest()
        return AuthorizationEvidence(
            principal,
            operation_id,
            target,
            sha,
            sha,
            "explicit-synthetic-fixture",
            "explicit-synthetic-fixture",
            min(time.time() + 5, principal.expires_at),
        )

    def policy_kinds(self, principal: Principal) -> tuple[str, ...]:
        if principal.actor not in self.actors:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        return ("analysis", "retention", "review", "risk_taxonomy", "threshold")


def isolated_http_harness(application: FastAPI) -> FastAPI:
    """Test actual error middleware/handlers without adding unknown production routes."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            application.state.business_database.close()

    harness = FastAPI(middleware=application.user_middleware, lifespan=lifespan)
    harness.exception_handlers = dict(application.exception_handlers)
    harness.state = application.state
    return harness
