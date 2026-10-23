"""Explicit, read-only directory observations for the T034 adoption handoff.

The request contains identifiers, not a token or proof of the operator's identity.
An observation never grants adoption, licence, classification or task permissions.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text

from .db import Database
from .identity.directory import valid_key


@dataclass(frozen=True)
class IdentityInventoryRequest:
    issuer: str
    subject: str
    user_id: UUID
    org_id: UUID
    case_id: UUID

    def __post_init__(self) -> None:
        if (
            type(self.issuer) is not str
            or not valid_key(self.issuer, 2048)
            or type(self.subject) is not str
            or not valid_key(self.subject, 1024)
            or any(type(value) is not UUID or value.int == 0 for value in (self.user_id, self.org_id, self.case_id))
        ):
            raise ValueError("TASK_IDENTITY_INVENTORY_INVALID")


@dataclass(frozen=True)
class IdentityInventoryObservation:
    canonical_bytes: bytes
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_bytes)
        if type(value) is not dict:
            raise ValueError("TASK_IDENTITY_INVENTORY_UNAVAILABLE")
        return value


_ROLE_QUERY = """SELECT current_user::text AS operator_database_role,
 current_database()::text AS database_name,
 (SELECT oid::bigint FROM pg_catalog.pg_database WHERE datname=current_database()) AS database_oid,
 statement_timestamp() AS observed_at,
 current_setting('transaction_read_only')='on' AS read_only,
 current_user=session_user AND NOT(r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication)
 AND pg_has_role(current_user,'mt_directory_manager','MEMBER')
 AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles danger WHERE danger.rolname IN
 ('mt_runtime','pg_read_all_data','pg_write_all_data','pg_read_server_files','pg_write_server_files',
  'pg_execute_server_program','pg_signal_backend','pg_checkpoint')
 AND pg_has_role(current_user,danger.oid,'MEMBER')) AS safe_operator
 FROM pg_catalog.pg_roles r WHERE r.rolname=current_user"""

_IDENTITY_QUERY = """SELECT i.identity_id,i.user_id,i.org_id,i.mapping_version,
 i.row_version AS identity_version,u.row_version AS user_version,o.row_version AS org_version,
 c.case_id,c.row_version AS case_version,m.membership_id,m.row_version AS membership_version,
 i.expires_at AS identity_expires_at,m.expires_at AS membership_expires_at
 FROM mt.user_identities i
 JOIN mt.users u ON (u.user_id,u.org_id)=(i.user_id,i.org_id)
 JOIN mt.organizations o ON o.org_id=i.org_id
 JOIN mt.cases c ON c.case_id=:case AND c.org_id=i.org_id
 JOIN mt.case_membership m ON (m.case_id,m.org_id,m.user_id)=(c.case_id,i.org_id,i.user_id)
 WHERE i.issuer=:issuer COLLATE "C" AND i.subject=:subject COLLATE "C"
 AND i.user_id=:user AND i.org_id=:org
 AND i.enabled AND i.revoked_at IS NULL
 AND (i.expires_at IS NULL OR i.expires_at>statement_timestamp())
 AND u.enabled AND o.enabled AND c.status='ACTIVE'
 AND m.revoked_at IS NULL AND (m.expires_at IS NULL OR m.expires_at>statement_timestamp())"""


def _normalize(value: Any) -> Any:
    if type(value) is UUID:
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError()
        return value.astimezone(timezone.utc).isoformat()
    if type(value) in (str, int, bool) or value is None:
        return value
    raise ValueError()


def observe_identity_inventory(database: Database, request: IdentityInventoryRequest) -> IdentityInventoryObservation:
    if type(request) is not IdentityInventoryRequest:
        raise ValueError("TASK_IDENTITY_INVENTORY_INVALID")
    request.__post_init__()
    try:
        with database.engine.begin() as connection:
            connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
            state = dict(connection.execute(text(_ROLE_QUERY)).mappings().one())
            if state["safe_operator"] is not True or state["read_only"] is not True:
                raise ValueError()
            rows = (
                connection.execute(
                    text(_IDENTITY_QUERY),
                    dict(
                        issuer=request.issuer,
                        subject=request.subject,
                        user=request.user_id,
                        org=request.org_id,
                        case=request.case_id,
                    ),
                )
                .mappings()
                .fetchmany(2)
            )
            if len(rows) > 1:
                raise ValueError()
            binding = {key: _normalize(value) for key, value in rows[0].items()} if rows else None
            if binding is not None and (
                (binding["user_id"], binding["org_id"], binding["case_id"])
                != tuple(map(str, (request.user_id, request.org_id, request.case_id)))
                or any(
                    type(binding[key]) is not int or binding[key] < 1
                    for key in ("identity_version", "user_version", "org_version", "case_version", "membership_version")
                )
            ):
                raise ValueError()
            value = dict(
                schema_version="task-adoption-identity-inventory-v1",
                status="IDENTITY_MEMBERSHIP_OBSERVED_NOT_ADOPTED" if binding else "DIRECTORY_BINDING_NOT_CURRENT",
                database={
                    key: _normalize(state[key]) for key in ("database_name", "database_oid", "operator_database_role")
                },
                observed_at=_normalize(state["observed_at"]),
                transaction_read_only=True,
                supplied_request={key: _normalize(value) for key, value in vars(request).items()},
                binding=binding,
                external_authentication_verified=False,
                adoption_authorized=False,
                license_verified=False,
                classification_verified=False,
                active_mapping_created=False,
                database_written=False,
                limitations=[
                    "directory observation is not operator authentication",
                    "no adoption/release/license/classification decision",
                    "not a runtime authorization cache or reusable permission proof",
                ],
            )
            raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
                "utf8"
            )
            return IdentityInventoryObservation(raw, hashlib.sha256(raw).hexdigest())
    except Exception:
        raise ValueError("TASK_IDENTITY_INVENTORY_UNAVAILABLE") from None
