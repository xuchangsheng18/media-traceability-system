"""ASGI factory: opt in with MT_IDENTITY_CONFIG, no implicit mock or policy."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from ..main import create_app
from .config import load_private_config
from .runtime import open_identity


def create_identity_app() -> FastAPI:
    try:
        config = load_private_config(Path(os.environ["MT_IDENTITY_CONFIG"]))
    except KeyError:
        raise RuntimeError("EXPLICIT_IDENTITY_CONFIGURATION_REQUIRED") from None
    resources = open_identity(config)
    try:
        app = create_app(config.business_settings, authority=resources.authority)
    except Exception:
        resources.close()
        raise RuntimeError("IDENTITY_APPLICATION_INITIALIZATION_FAILED") from None
    original = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        try:
            async with original(application):
                yield
        finally:
            resources.close()

    app.router.lifespan_context = lifespan
    return app
