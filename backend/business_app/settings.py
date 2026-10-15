from dataclasses import dataclass, field
from pathlib import Path

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

    def __post_init__(self) -> None:
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
