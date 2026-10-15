from dataclasses import dataclass, field
from pathlib import Path

from psycopg import ProgrammingError
from psycopg.conninfo import conninfo_to_dict


@dataclass(frozen=True)
class BusinessSettings:
    database_dsn: str = field(repr=False)
    object_root: Path
    max_upload_bytes: int
    part_size_bytes: int
    upload_ttl_seconds: int
    cursor_secret: str = field(repr=False)
    control_ttl_seconds: int | None = None
    node_lease_seconds: int | None = None
    max_import_entries: int | None = None
    runtime_profile: str = "development"

    def __post_init__(self) -> None:
        if self.runtime_profile not in {"development", "test", "production"}:
            raise RuntimeError("BUSINESS_CONFIGURATION_INVALID")
        if self.runtime_profile == "production":
            raise RuntimeError("PRODUCTION_PROFILE_NOT_APPROVED")
        database = conninfo_to_dict(self.database_dsn).get("dbname")
        if not isinstance(database, str) or not database.startswith("mt_business_"):
            raise RuntimeError("EXPLICIT_ISOLATED_BUSINESS_DATABASE_REQUIRED")
        if min(self.max_upload_bytes, self.part_size_bytes, self.upload_ttl_seconds) <= 0:
            raise RuntimeError("EXPLICIT_POSITIVE_DEVELOPMENT_LIMITS_REQUIRED")
        if len(self.cursor_secret) < 32:
            raise RuntimeError("PRIVATE_CURSOR_KEY_REQUIRED")
        if any(
            value is not None and value <= 0
            for value in [self.control_ttl_seconds, self.node_lease_seconds, self.max_import_entries]
        ):
            raise RuntimeError("EXPLICIT_POSITIVE_CONTROL_LIMITS_REQUIRED")


import os
from collections.abc import Mapping


def load_business_settings(environment: Mapping[str, str] | None = None) -> BusinessSettings:
    values = os.environ if environment is None else environment
    try:
        root = Path(values["MT_BUSINESS_OBJECT_ROOT"])
        if not root.is_absolute() or root.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
            raise ValueError("PRIVATE_RUNTIME_DIRECTORY_REQUIRED")
        optional = lambda name: int(values[name]) if values.get(name) else None
        return BusinessSettings(
            database_dsn=values["MT_BUSINESS_DATABASE_DSN"],
            object_root=root,
            max_upload_bytes=int(values["MT_BUSINESS_MAX_UPLOAD_BYTES"]),
            part_size_bytes=int(values["MT_BUSINESS_PART_SIZE_BYTES"]),
            upload_ttl_seconds=int(values["MT_BUSINESS_UPLOAD_TTL_SECONDS"]),
            cursor_secret=values["MT_BUSINESS_CURSOR_SECRET"],
            control_ttl_seconds=optional("MT_BUSINESS_CONTROL_TTL_SECONDS"),
            node_lease_seconds=optional("MT_BUSINESS_NODE_LEASE_SECONDS"),
            max_import_entries=optional("MT_BUSINESS_MAX_IMPORT_ENTRIES"),
            runtime_profile=values.get("MT_RUNTIME_PROFILE", "development"),
        )
    except (KeyError, ValueError, TypeError, ProgrammingError):
        raise RuntimeError("BUSINESS_CONFIGURATION_INVALID") from None
