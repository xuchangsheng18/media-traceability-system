from collections.abc import Iterator
from contextlib import contextmanager

from psycopg.conninfo import conninfo_to_dict
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import URL

from .errors import BusinessError
from .types import Actor, Scope


class Database:
    def __init__(self, dsn: str) -> None:
        values = conninfo_to_dict(dsn)
        name = values.get("dbname")
        if not isinstance(name, str) or not name.startswith("mt_business_"):
            raise RuntimeError("EXPLICIT_ISOLATED_BUSINESS_DATABASE_REQUIRED")
        url = URL.create(
            "postgresql+psycopg",
            username=str(values.get("user", "")),
            password=str(values.get("password", "")),
            host=str(values.get("host", "127.0.0.1")),
            port=int(values.get("port", 5432) or 5432),
            database=name,
        )
        self.engine = create_engine(url, pool_size=1, max_overflow=0, pool_pre_ping=True)

    @contextmanager
    def identity_transaction(self, actor: Actor) -> Iterator[Connection]:
        with self.engine.begin() as connection:
            if bool(
                connection.execute(
                    text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user")
                ).scalar_one()
            ):
                raise RuntimeError("PRIVILEGED_BUSINESS_CONNECTION_FORBIDDEN")
            connection.execute(
                text("SELECT set_config('app.actor_id',:actor,true),set_config('app.org_id',:org,true)"),
                {"actor": str(actor.user_id), "org": str(actor.org_id)},
            )
            yield connection

    @contextmanager
    def transaction(self, scope: Scope) -> Iterator[Connection]:
        with self.identity_transaction(scope.actor) as connection:
            if not bool(
                connection.execute(text("SELECT mt.can_access_case(:case)"), {"case": scope.case_id}).scalar_one()
            ):
                raise BusinessError("CASE_NOT_FOUND", 404)
            yield connection

    def close(self) -> None:
        self.engine.dispose()
