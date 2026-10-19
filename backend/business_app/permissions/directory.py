"""Read only exact identity-bound permission facts with a dedicated database role."""

import hashlib
import json
import time
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..db import Database
from ..errors import BusinessError
from ..identity.directory import valid_key
from .policy import validate_principal
from .types import PermissionFact, Principal


class PermissionDirectory:
    def __init__(self, database: Database, *, clock: Callable[[], float] = time.time) -> None:
        self.database, self.clock = database, clock

    def read(self, principal: Principal, permission: str) -> PermissionFact:
        validate_principal(principal, self.clock)
        if not valid_key(permission, 1024):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        try:
            with self.database.engine.begin() as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                unsafe = connection.execute(
                    text("""SELECT r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication
                    OR NOT pg_has_role(current_user,'mt_permission_lookup','MEMBER')
                    OR EXISTS(SELECT 1 FROM pg_roles danger WHERE danger.rolname IN
                      ('mt_directory_manager','mt_runtime','mt_identity_lookup','pg_read_all_data','pg_write_all_data',
                       'pg_read_server_files','pg_write_server_files','pg_execute_server_program','pg_signal_backend','pg_checkpoint')
                      AND pg_has_role(current_user,danger.oid,'MEMBER'))
                    FROM pg_roles r WHERE r.rolname=current_user""")
                ).scalar_one()
                if unsafe is not False:
                    raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
                row = (
                    connection.execute(
                        text("""SELECT * FROM mt.lookup_permission(:issuer,:subject,:user,:org,:permission)"""),
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
        except SQLAlchemyError:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        validate_principal(principal, self.clock)
        if row is None:
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        if (
            row["user_id"] != principal.actor.user_id
            or row["org_id"] != principal.actor.org_id
            or row["permission_code"] != permission
            or type(row["eligible"]) is not bool
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        facts = dict(row)
        facts["verified_issuer"] = principal.issuer
        facts["verified_subject"] = principal.subject
        facts["token_expires_at"] = principal.expires_at
        canonical = json.dumps(
            facts,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )
        digest = hashlib.sha256(canonical.encode("utf8")).hexdigest()
        return PermissionFact(principal, permission, row["eligible"], digest)
