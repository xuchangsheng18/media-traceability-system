"""Explicit synthetic permissions and isolated HTTP error harnesses, never deployment defaults."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from business_app.errors import BusinessError
from business_app.permissions.types import Principal
from business_app.types import Actor
from fastapi import FastAPI


class FixturePermissions:
    def __init__(self, actors: frozenset[Actor], permissions: frozenset[str]) -> None:
        self.actors, self.permissions = actors, permissions

    def check(self, principal: Principal, permission: str) -> None:
        if principal.actor not in self.actors or permission not in self.permissions:
            raise BusinessError("PERMISSION_REQUIRED", 403)


def isolated_http_harness(application: FastAPI) -> FastAPI:
    """Test actual error middleware/handlers without adding unknown production routes."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            application.state.business_database.close()

    harness = FastAPI(
        exception_handlers=application.exception_handlers, middleware=application.user_middleware, lifespan=lifespan
    )
    harness.state = application.state
    return harness
