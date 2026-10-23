"""Prepare a new isolated database or serve the default-deny native development API."""

import argparse
import json
import os
import secrets
import shutil
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from business_app.development import isolated_loopback_dsn, load_development_settings  # noqa: E402
from business_app.identity.config import private_file  # noqa: E402
from business_migrations.runner import apply_migrations  # noqa: E402


def prepare(directory: Path, admin_config: Path) -> dict[str, object]:
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    if (
        not directory.is_absolute()
        or directory.exists()
        or directory.resolve().is_relative_to(ROOT.resolve())
        or any(p.is_symlink() for p in [directory, *directory.parents])
        or admin_config.name != "business-test-postgres-private.json"
    ):
        raise RuntimeError("NEW_PRIVATE_ISOLATED_DIRECTORY_AND_TEST_ADMIN_CONFIG_REQUIRED")
    admin_dsn = isolated_loopback_dsn(json.loads(private_file(admin_config, admin_config.parent))["admin_dsn"])
    target = conninfo_to_dict(admin_dsn)
    if target.get("dbname") == "media_trace_poc":
        raise RuntimeError("EXPLICIT_ISOLATED_LOOPBACK_TEST_INSTANCE_REQUIRED")
    identifier = uuid4().hex
    database = "mt_business_preview_" + identifier
    role = "mt_preview_" + identifier
    password = secrets.token_hex(32)
    with psycopg.connect(admin_dsn, autocommit=True) as admin:

        def scalar(query: str) -> str:
            row = admin.execute(query).fetchone()
            if row is None or len(row) != 1 or not isinstance(row[0], str):
                raise RuntimeError("NATIVE_TEST_DATABASE_SETTING_UNAVAILABLE")
            return row[0]

        if admin.info.server_version // 10000 != 16:
            raise RuntimeError("POSTGRESQL16_REQUIRED")
        data_path = Path(scalar("SHOW data_directory"))
        if not data_path.is_dir() or shutil.disk_usage(data_path).free < 5 * 1024**3:
            raise RuntimeError("NATIVE_TEST_DATABASE_STORAGE_NOT_VERIFIED_OR_BELOW_GUARD")
        if scalar("SHOW log_statement") != "none" or scalar("SHOW log_min_duration_statement") != "-1":
            raise RuntimeError("PRIVATE_CREDENTIAL_STATEMENT_LOGGING_MUST_BE_DISABLED")
        directory.mkdir(mode=0o700)
        intent = directory / "setup-intent.json"
        intent.write_text(json.dumps(dict(database=database, role=role, real_business_records_created=False)) + "\n")
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(database)))
        dsn = make_conninfo(admin_dsn, dbname=database)
        versions = apply_migrations(dsn, ROOT / "backend/business_migrations")
        with admin.transaction():
            admin.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}"
                ).format(sql.Identifier(role), sql.Literal(password))
            )
            admin.execute(sql.SQL("GRANT mt_runtime TO {}").format(sql.Identifier(role)))
        values = dict(
            MT_BUSINESS_DATABASE_DSN=make_conninfo(dsn, user=role, password=password),
            MT_BUSINESS_OBJECT_ROOT=str(directory / "objects"),
            MT_BUSINESS_MAX_UPLOAD_BYTES="1048576",
            MT_BUSINESS_PART_SIZE_BYTES="256000",
            MT_BUSINESS_UPLOAD_TTL_SECONDS="3600",
            MT_BUSINESS_CURSOR_SECRET=secrets.token_hex(32),
            MT_RUNTIME_PROFILE="development",
        )
        path = directory / "application.private.json"
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf8") as output:
            json.dump(dict(business_environment=values), output)
        load_development_settings(path)
        return dict(
            status="PREPARED_ISOLATED_DATABASE_NO_IDENTITY_OR_POLICY_GRANTED",
            migration_versions=versions,
            real_business_records_created=False,
            shared_database_migrated=False,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "serve"])
    parser.add_argument("--private-directory", type=Path, required=True)
    parser.add_argument("--admin-config", type=Path)
    parser.add_argument("--create-isolated-database", action="store_true")
    parser.add_argument("--port", type=int, default=14202)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if os.name != "posix" or sys.version_info[:3] != (3, 11, 17):
            raise RuntimeError("APPROVED_LINUX_PY311_17_RUNTIME_REQUIRED")
        if args.action == "prepare":
            if not args.create_isolated_database or args.admin_config is None:
                raise RuntimeError("EXPLICIT_ISOLATED_CREATION_FLAG_REQUIRED")
            print(json.dumps(prepare(args.private_directory, args.admin_config)))
            return 0
        if args.create_isolated_database or args.admin_config or not 1024 <= args.port <= 65535:
            raise RuntimeError("SERVE_FLAGS_INVALID")
        path = args.private_directory / "application.private.json"
        load_development_settings(path)
        os.environ["MT_BUSINESS_DEVELOPMENT_CONFIG"] = str(path)
        import uvicorn

        uvicorn.run(
            "business_app.development:create_development_app",
            factory=True,
            host="127.0.0.1",
            port=args.port,
            workers=1,
            access_log=False,
        )
        return 0
    except Exception:
        print(json.dumps(dict(status="DEVELOPMENT_STARTUP_NOT_COMPLETED", raw_details_withheld=True)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
