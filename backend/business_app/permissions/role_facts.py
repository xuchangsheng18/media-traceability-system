"""Complete, live role facts with distinct lookup and actor-bound transaction ports."""

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from ..db import Database
from ..errors import BusinessError
from ..identity.directory import valid_key
from .policy import validate_principal
from .rule_types import ActiveRole, RoleFacts
from .types import Principal


def positive_integer(value: Any) -> bool:
    return type(value) is int and value > 0


class RoleDirectory:
    def __init__(self, database: Database, *, clock: Callable[[], float]) -> None:
        self.database, self.clock = database, clock

    def _query(
        self, connection: Connection, principal: Principal, permission: str, transaction: bool
    ) -> Mapping[str, Any] | None:
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

    def _parse(self, row: Mapping[str, Any] | None, principal: Principal, permission: str) -> RoleFacts:
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
        raw = dict(
            row,
            verified_issuer=principal.issuer,
            verified_subject=principal.subject,
            token_expires_at=principal.expires_at,
        )
        canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
        digest = hashlib.sha256(canonical.encode("utf8")).hexdigest()
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
