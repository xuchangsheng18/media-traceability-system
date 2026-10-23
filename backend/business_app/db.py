import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from psycopg.conninfo import conninfo_to_dict
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import URL

from .data_scope import AccessMode, DataScope, from_evidence
from .errors import BusinessError
from .permissions.context import current_authorization, evidence_actor
from .scope_context import BoundTransaction, bind_data_scope, bind_scope_transaction, current_scope_transaction
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
        authorization = current_authorization()
        if authorization is None:
            if current_scope_transaction() is not None:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            # Preserve the explicit privileged-connection diagnosis even when
            # the caller also omitted authentication. No business query runs.
            with self.engine.begin() as connection:
                self._unprivileged(connection)
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if evidence_actor(authorization.evidence) != actor:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        active = current_scope_transaction()
        if active is not None:
            if (
                active.database is not self
                or active.authorization is None
                or (
                    active.authorization.evidence is not authorization.evidence
                    or active.authorization.fence is not authorization.fence
                    or active.scope.actor != actor
                )
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            yield active.connection
            return
        if authorization.fence is None:
            raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
        clock = getattr(authorization.fence, "clock", time.time)
        scope = from_evidence(authorization.evidence, clock=clock)
        with self.scoped_transaction(scope) as connection:
            yield connection

    @staticmethod
    def _unprivileged(connection: Connection) -> None:
        if bool(
            connection.execute(
                text("""SELECT r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication
                OR NOT pg_has_role(current_user,'mt_runtime','MEMBER')
                OR EXISTS(SELECT 1 FROM pg_namespace n WHERE n.nspname='mt'
                    AND pg_has_role(current_user,n.nspowner,'MEMBER'))
                OR EXISTS(SELECT 1 FROM pg_roles p WHERE p.rolname IN (
                    'mt_directory_manager','mt_identity_lookup','mt_permission_lookup',
                    'mt_task_plan_lookup','mt_task_plan_manager','mt_task_plan_case_reader',
                    'pg_read_all_data','pg_write_all_data','pg_read_server_files','pg_write_server_files',
                    'pg_execute_server_program','pg_signal_backend','pg_checkpoint')
                    AND pg_has_role(current_user,p.oid,'MEMBER'))
                FROM pg_roles r WHERE r.rolname=current_user""")
            ).scalar_one()
        ):
            raise RuntimeError("PRIVILEGED_BUSINESS_CONNECTION_FORBIDDEN")

    @contextmanager
    def scoped_transaction(self, scope: DataScope) -> Iterator[Connection]:
        if not isinstance(scope, DataScope):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        authorization = current_authorization()
        active = current_scope_transaction()
        if active is not None:
            if (
                active.database is not self
                or active.authorization is None
                or authorization is None
                or (
                    active.authorization.evidence is not authorization.evidence
                    or active.authorization.fence is not authorization.fence
                )
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            with bind_data_scope(scope):
                yield active.connection
            return
        if scope.mode is AccessMode.LOOKUP:
            if authorization is not None:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        elif authorization is None or authorization.fence is None:
            raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
        else:
            expected = from_evidence(authorization.evidence, clock=getattr(authorization.fence, "clock", time.time))
            if scope != expected:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        with self.engine.begin() as connection:
            if scope.mode is AccessMode.LOOKUP:
                connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            self._unprivileged(connection)
            values = {
                "app.actor_id": str(scope.actor.user_id),
                "app.org_id": str(scope.actor.org_id),
                "app.scope_mode": scope.mode.value,
                "app.case_id": str(scope.case_id) if scope.case_id is not None else "",
                "app.operation_id": scope.operation_id,
                "app.lookup_kind": scope.lookup.kind if scope.lookup else "",
                "app.lookup_id": str(scope.lookup.identifier) if scope.lookup else "",
            }
            for name, value in values.items():
                connection.execute(text("SELECT set_config(:name,:value,true)"), dict(name=name, value=value))
            root = BoundTransaction(self, connection, scope, authorization)
            with bind_scope_transaction(root):
                if authorization is not None and authorization.fence is not None:
                    authorization.fence.hold(connection, authorization.evidence)
                yield connection
                for check in tuple(root.commit_checks):
                    check()
                if authorization is not None and authorization.fence is not None:
                    authorization.fence.finish(connection, authorization.evidence)

    def before_commit(self, connection: Connection, check: Callable[[], None]) -> None:
        from .scope_collections import require_root
        from .scope_context import current_data_scope

        require_root(connection, current_data_scope())
        root = current_scope_transaction()
        if root is None or root.database is not self or not callable(check):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        root.commit_checks.append(check)

    @contextmanager
    def transaction(self, scope: Scope) -> Iterator[Connection]:
        with self.identity_transaction(scope.actor) as connection:
            active = current_scope_transaction()
            if active is None or active.scope.mode is not AccessMode.CASE or active.scope.case_id != scope.case_id:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            if not bool(
                connection.execute(text("SELECT mt.can_access_case(:case)"), {"case": scope.case_id}).scalar_one()
            ):
                raise BusinessError("CASE_NOT_FOUND", 404)
            yield connection

    def close(self) -> None:
        self.engine.dispose()
