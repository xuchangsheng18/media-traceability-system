"""Explicit loopback development factory; no implicit identity or policy grants."""

import json
import os
from dataclasses import replace
from pathlib import Path

import psycopg
from fastapi import FastAPI
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from .contracts import ROOT
from .identity.config import private_file
from .identity.tokens import unique_object
from .main import create_app
from .settings import BusinessSettings, load_business_settings


def isolated_loopback_dsn(value: str) -> str:
    target = conninfo_to_dict(value)
    host, port = target.get("host"), target.get("port", "")
    address = target.get("hostaddr")
    if (
        host not in {"127.0.0.1", "localhost", "::1"}
        or not isinstance(port, str)
        or not port.isascii()
        or not port.isdigit()
        or not 1 <= int(port) <= 65535
        or "service" in target
        or (address is not None and address not in {"127.0.0.1", "::1"})
        or (address is not None and host != "localhost" and address != host)
    ):
        raise ValueError("EXPLICIT_ISOLATED_LOOPBACK_TEST_INSTANCE_REQUIRED")
    # libpq PGHOSTADDR overrides DNS even when host is explicitly set. Pin the
    # actual numeric address, rather than trusting the displayed host alone.
    return make_conninfo(value, hostaddr=address or ("::1" if host == "::1" else "127.0.0.1"))


def load_development_settings(path: Path) -> BusinessSettings:
    try:
        root = path.parent
        if root.resolve().is_relative_to(ROOT.resolve()) or root.stat().st_mode & 0o077:
            raise ValueError()
        values = json.loads(private_file(path, root), object_pairs_hook=unique_object)
        if not isinstance(values, dict) or set(values) != {"business_environment"}:
            raise ValueError()
        settings = load_business_settings(values["business_environment"])
        dsn = isolated_loopback_dsn(settings.database_dsn)
        target = conninfo_to_dict(dsn)
        database = target.get("dbname")
        if (
            settings.runtime_profile != "development"
            or not settings.object_root.resolve().is_relative_to(root.resolve())
            or not isinstance(database, str)
            or not database.startswith("mt_business_preview_")
        ):
            raise ValueError()
        return replace(settings, database_dsn=dsn)
    except Exception:
        raise RuntimeError("EXPLICIT_PRIVATE_ISOLATED_DEVELOPMENT_CONFIGURATION_REQUIRED") from None


def create_development_app() -> FastAPI:
    try:
        settings = load_development_settings(Path(os.environ["MT_BUSINESS_DEVELOPMENT_CONFIG"]))
        with psycopg.connect(settings.database_dsn, connect_timeout=5) as connection:
            row = connection.execute(
                "SELECT r.rolsuper,r.rolbypassrls,r.rolcreaterole,r.rolcreatedb,r.rolreplication,"
                "pg_has_role(current_user,'mt_runtime','MEMBER'),pg_has_role(current_user,'mt_directory_manager','MEMBER'),"
                "pg_has_role(current_user,'pg_read_all_data','MEMBER'),pg_has_role(current_user,'pg_write_all_data','MEMBER') "
                "FROM pg_roles r WHERE r.rolname=current_user"
            ).fetchone()
            if row != (False, False, False, False, False, True, False, False, False):
                raise ValueError()
        # Source and SQL are real; missing identity/policy remains an actual 401
        # or 503. This entrypoint never installs test fixtures or approval seeds.
        return create_app(settings)
    except Exception:
        raise RuntimeError("ISOLATED_DEVELOPMENT_STARTUP_FAILED") from None
