"""Complete, live role facts with distinct lookup and actor-bound transaction ports."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, overload
from uuid import UUID

from sqlalchemy import Connection, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from ..data_scope import LookupKey
from ..db import Database
from ..errors import BusinessError
from ..identity.directory import valid_key
from ..scope_lookup import SqlScopeLookup
from .policy import validate_principal
from .rule_types import ActiveRole, ExecutionSubject, RoleFacts, WorkRoleFacts
from .types import Principal
from .work_subject import WORK_TABLES, validate_execution_subject

if TYPE_CHECKING:
    from .work import WorkTrust


def positive_integer(value: Any) -> bool:
    return type(value) is int and value > 0


class RoleDirectory:
    def __init__(
        self,
        database: Database,
        *,
        clock: Callable[[], float],
        work_database: Database | None = None,
        work_trust: WorkTrust | None = None,
    ) -> None:
        self.database, self.clock, self.work_database = database, clock, work_database
        self.work_trust = work_trust

    def _query(
        self, connection: Connection, principal: Principal, permission: str, transaction: bool
    ) -> RowMapping | None:
        group = "mt_runtime" if transaction else "mt_permission_lookup"
        forbidden = "mt_permission_lookup" if transaction else "mt_runtime"
        unsafe = connection.execute(
            text("""SELECT r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication
            OR NOT pg_has_role(current_user,:wanted,'MEMBER')
            OR EXISTS(SELECT 1 FROM pg_roles danger WHERE danger.rolname IN
              (:forbidden,'mt_directory_manager','mt_identity_lookup','pg_read_all_data','pg_write_all_data',
               'pg_read_server_files','pg_write_server_files','pg_execute_server_program','pg_signal_backend','pg_checkpoint')
              AND pg_has_role(current_user,danger.oid,'MEMBER'))
            FROM pg_roles r WHERE r.rolname=current_user"""),
            dict(wanted=group, forbidden=forbidden),
        ).scalar_one()
        if unsafe is not False:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        statement = (
            "SELECT * FROM mt.lookup_actor_role_facts(:issuer,:subject,:permission)"
            if transaction
            else "SELECT * FROM mt.lookup_role_facts(:issuer,:subject,:user,:org,:permission)"
        )
        return (
            connection.execute(
                text(statement),
                dict(
                    issuer=principal.issuer,
                    subject=principal.subject,
                    user=principal.actor.user_id,
                    org=principal.actor.org_id,
                    permission=permission,
                ),
            )
            .mappings()
            .one_or_none()
        )

    @overload
    def _parse(self, row: RowMapping | None, principal: Principal, permission: str) -> RoleFacts: ...

    @overload
    def _parse(self, row: RowMapping | None, principal: ExecutionSubject, permission: str) -> WorkRoleFacts: ...

    def _parse(
        self, row: RowMapping | None, principal: Principal | ExecutionSubject, permission: str
    ) -> RoleFacts | WorkRoleFacts:
        if row is None:
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        if (
            row["user_id"] != principal.actor.user_id
            or row["org_id"] != principal.actor.org_id
            or row["permission_code"] != permission
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if (
            type(row["eligible"]) is not bool
            or not isinstance(row["active_roles"], list)
            or not isinstance(row["permission_role_ids"], list)
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        roles = []
        for item in row["active_roles"]:
            if not isinstance(item, dict) or set(item) != {
                "role_id",
                "code",
                "binding_id",
                "binding_version",
                "role_version",
                "expires_epoch",
            }:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            if (
                not valid_key(item["code"], 1024)
                or not positive_integer(item["binding_version"])
                or not positive_integer(item["role_version"])
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            expiry = float(item["expires_epoch"]) if item["expires_epoch"] is not None else None
            if expiry is not None and (not math.isfinite(expiry) or expiry <= self.clock()):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            roles.append(
                ActiveRole(
                    UUID(item["role_id"]),
                    item["code"],
                    UUID(item["binding_id"]),
                    item["binding_version"],
                    item["role_version"],
                    expiry,
                )
            )
        roles.sort(key=lambda role: str(role.role_id))
        ids = tuple(sorted((UUID(value) for value in row["permission_role_ids"]), key=str))
        role_ids = {role.role_id for role in roles}
        if (
            len(role_ids) != len(roles)
            or len({role.binding_id for role in roles}) != len(roles)
            or len(ids) != len(set(ids))
            or not set(ids) <= role_ids
            or row["eligible"] != bool(ids)
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        identity_expiry = row["identity_expires_epoch"]
        if identity_expiry is not None and (
            not math.isfinite(float(identity_expiry)) or float(identity_expiry) <= self.clock()
        ):
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        raw = (
            dict(
                row,
                verified_issuer=principal.issuer,
                verified_subject=principal.subject,
                token_expires_at=principal.expires_at,
            )
            if isinstance(principal, Principal)
            else dict(row, work_subject=asdict(principal))
        )
        canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
        digest = hashlib.sha256(canonical.encode("utf8")).hexdigest()
        if isinstance(principal, ExecutionSubject):
            if row["identity_id"] != principal.identity_id or row["mapping_version"] != principal.mapping_version:
                raise BusinessError("AUTHENTICATION_REQUIRED", 401)
            current = self.clock()
            if type(current) not in (int, float) or not math.isfinite(current):
                raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
            deadline = min(
                float(current) + 5, float(identity_expiry) if identity_expiry is not None else float(current) + 5
            )
            return WorkRoleFacts(principal, permission, row["eligible"], tuple(roles), ids, digest, deadline)
        return RoleFacts(principal, permission, row["eligible"], tuple(roles), ids, digest)

    def read_roles(self, principal: Principal, permission: str, *, connection: Connection | None = None) -> RoleFacts:
        validate_principal(principal, self.clock)
        if not valid_key(permission, 1024):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        try:
            if connection is None:
                with self.database.engine.begin() as current:
                    current.execute(text("SET TRANSACTION READ ONLY"))
                    row = self._query(current, principal, permission, False)
            else:
                row = self._query(connection, principal, permission, True)
            validate_principal(principal, self.clock)
            result = self._parse(row, principal, permission)
            validate_principal(principal, self.clock)
            return result
        except BusinessError:
            raise
        except (SQLAlchemyError, ValueError, TypeError, KeyError, OverflowError):
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None

    def read_for_work(
        self, subject: ExecutionSubject, permission: str, *, connection: Connection | None = None
    ) -> WorkRoleFacts:
        validate_execution_subject(subject)
        if not valid_key(permission, 1024):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        try:
            if connection is None:
                if self.work_database is None or self.work_trust is None:
                    raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
                from .work_subject import WORK_OPERATIONS

                operation, value = next(
                    (key, value) for key, value in WORK_OPERATIONS.items() if value[2] == subject.work_kind
                )
                port = SqlScopeLookup(self.work_database, work_trust=self.work_trust, clock=self.clock)
                with port.connection(subject, operation, LookupKey(value[1], subject.work_id)) as current:
                    return self.read_for_work(subject, permission, connection=current)
            unsafe = connection.execute(
                text("""SELECT r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication
                OR NOT pg_has_role(current_user,'mt_runtime','MEMBER') OR EXISTS(SELECT 1 FROM pg_roles d
                WHERE d.rolname IN ('mt_permission_lookup','mt_identity_lookup','mt_directory_manager',
                 'pg_read_all_data','pg_write_all_data','pg_read_server_files','pg_write_server_files','pg_execute_server_program',
                 'pg_signal_backend','pg_checkpoint')
                AND pg_has_role(current_user,d.oid,'MEMBER')) FROM pg_roles r WHERE r.rolname=current_user""")
            ).scalar_one()
            binding = tuple(connection.execute(text("SELECT mt.actor_id(),mt.org_id()")).one())
            if unsafe is not False or binding != (subject.actor.user_id, subject.actor.org_id):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            _, _, owner = WORK_TABLES[subject.work_kind]
            from .work_subject import WORK_OPERATIONS

            kind = next(value[1] for value in WORK_OPERATIONS.values() if value[2] == subject.work_kind)
            metadata = connection.execute(
                text("SELECT mt.lookup_scope_metadata(:kind,:id)"), dict(kind=kind, id=subject.work_id)
            ).scalar_one()
            job = metadata["record"] if isinstance(metadata, dict) else None
            if job is None or (job["org_id"], job.get(owner)) != (
                str(subject.actor.org_id),
                str(subject.actor.user_id),
            ):
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            row = (
                connection.execute(
                    text("SELECT * FROM mt.lookup_actor_work_role_facts(:identity,:mapping,:permission)"),
                    dict(identity=subject.identity_id, mapping=subject.mapping_version, permission=permission),
                )
                .mappings()
                .one_or_none()
            )
            return self._parse(row, subject, permission)
        except BusinessError:
            raise
        except (SQLAlchemyError, RuntimeError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
