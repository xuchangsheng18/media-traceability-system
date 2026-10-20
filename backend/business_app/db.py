import math
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from psycopg.conninfo import conninfo_to_dict
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import URL

from .errors import BusinessError
from .permissions.context import current_authorization
from .types import Actor, Scope


class Database:
    def __init__(
        self,
        dsn: str,
        *,
        connect_timeout_seconds: int = 2,
        statement_timeout_ms: int = 2000,
        pool_timeout_seconds: float = 2.0,
    ) -> None:
        if (
            type(connect_timeout_seconds) is not int
            or not 1 <= connect_timeout_seconds <= 30
            or type(statement_timeout_ms) is not int
            or not 1 <= statement_timeout_ms <= 30000
            or type(pool_timeout_seconds) not in (float, int)
            or not math.isfinite(pool_timeout_seconds)
            or not 0 < pool_timeout_seconds <= 30
        ):
            raise ValueError("DATABASE_TIMEOUT_CONFIGURATION_INVALID")
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
        extra: dict[str, Any] = {
            key: value for key, value in values.items() if key not in {"dbname", "user", "password", "host", "port"}
        }
        extra["connect_timeout"] = connect_timeout_seconds
        extra["options"] = str(extra.get("options", "")) + f" -c statement_timeout={statement_timeout_ms}"
        self.engine = create_engine(
            url, pool_size=1, max_overflow=0, pool_pre_ping=True, pool_timeout=pool_timeout_seconds, connect_args=extra
        )

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
            authorization = current_authorization()
            protected = authorization is not None and (authorization.mutation or authorization.fence is not None)
            if protected and authorization is not None:
                if authorization.evidence.principal.actor != actor:
                    raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
                if authorization.fence is None:
                    raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
                authorization.fence.hold(connection, authorization.evidence)
            yield connection
            if protected and authorization is not None and authorization.fence is not None:
                authorization.fence.finish(connection, authorization.evidence)

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
