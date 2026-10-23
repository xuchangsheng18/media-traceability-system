"""Load an explicitly selected private identity config, never environment defaults."""

import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..settings import BusinessSettings, load_business_settings
from .tokens import IntrospectionSettings, unique_object


@dataclass(frozen=True)
class IdentityRuntimeConfig:
    introspection: IntrospectionSettings
    ca_file: Path
    lookup_dsn: str = field(repr=False)
    business_settings: BusinessSettings = field(repr=False)


def private_file(path: Path, root: Path) -> bytes:
    if not path.is_absolute() or not path.is_relative_to(root) or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError("UNSAFE_PRIVATE_PATH")
    with path.open("rb") as source:
        info = os.fstat(source.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_mode & 0o077
            or info.st_uid != os.geteuid()
            or info.st_size > 65536
        ):
            raise ValueError("UNSAFE_PRIVATE_FILE")
        return source.read(65537)


def load_private_config(path: Path) -> IdentityRuntimeConfig:
    try:
        root = path.parent
        if root.stat().st_mode & 0o077 or root.stat().st_uid != os.geteuid():
            raise ValueError("PRIVATE_DIRECTORY_REQUIRED")
        values = json.loads(private_file(path, root).decode(), object_pairs_hook=unique_object)
        if not isinstance(values, dict) or set(values) != {
            "introspection",
            "ca_file",
            "lookup_dsn",
            "business_environment",
        }:
            raise ValueError("EXACT_CONFIGURATION_REQUIRED")
        introspection: dict[str, Any] = values["introspection"]
        settings = IntrospectionSettings(**introspection)
        if (
            not settings.issuer.startswith("https://")
            or settings.endpoint != settings.issuer + "/protocol/openid-connect/token/introspect"
        ):
            raise ValueError("ISSUER_ENDPOINT_BINDING_REQUIRED")
        ca = Path(values["ca_file"])
        private_file(ca, root)
        environment = values["business_environment"]
        if not isinstance(environment, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in environment.items()
        ):
            raise ValueError("BUSINESS_CONFIGURATION_REQUIRED")
        lookup = values["lookup_dsn"]
        if not isinstance(lookup, str) or not lookup:
            raise ValueError("LOOKUP_CONFIGURATION_REQUIRED")
        return IdentityRuntimeConfig(settings, ca, lookup, load_business_settings(environment))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, RecursionError):
        raise RuntimeError("IDENTITY_PRIVATE_CONFIGURATION_INVALID") from None
