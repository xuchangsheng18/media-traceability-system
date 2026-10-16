"""Explicit identity/tenant persistence; no client credentials or token validation here."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

from ..errors import BusinessError


@dataclass(frozen=True)
class IdentityMapping:
    identity_id: UUID
    user_id: UUID
    org_id: UUID
    mapping_version: str
    identity_version: int
    user_version: int
    org_version: int


def valid_key(value: str, limit: int) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= limit
        and value == value.strip()
        and all(ord(char) >= 32 and ord(char) != 127 for char in value)
    )


class IdentityDirectory:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def _manager(self) -> None:
        allowed = self.connection.execute(
            text("SELECT pg_has_role(current_user,'mt_directory_manager','MEMBER')")
        ).scalar_one()
        if not allowed:
            raise BusinessError("DIRECTORY_MANAGEMENT_FORBIDDEN", 403)

    def _insert(self, statement: str, values: dict[str, Any]) -> UUID:
        self._manager()
        try:
            with self.connection.begin_nested():
                value = self.connection.execute(text(statement), values).scalar_one()
        except IntegrityError as error:
            state = getattr(error.orig, "sqlstate", None)
            if state == "23503":
                raise BusinessError("DIRECTORY_RELATION_INVALID", 409) from None
            if state == "23505":
                raise BusinessError("DIRECTORY_CONFLICT", 409) from None
            if state == "23514":
                raise BusinessError("DIRECTORY_INPUT_INVALID", 422) from None
            raise
        return UUID(str(value))

    def create_organization(self, name: str) -> UUID:
        if not valid_key(name, 1024):
            raise BusinessError("DIRECTORY_INPUT_INVALID", 422)
        return self._insert(
            "INSERT INTO mt.organizations(org_id,name) VALUES(:id,:name) RETURNING org_id",
            {"id": uuid4(), "name": name},
        )

    def create_user(self, org_id: UUID, legacy_label: str, *, enabled: bool = False) -> UUID:
        if not valid_key(legacy_label, 1024) or type(enabled) is not bool:
            raise BusinessError("DIRECTORY_INPUT_INVALID", 422)
        return self._insert(
            "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(:id,:org,:label,:enabled) RETURNING user_id",
            {"id": uuid4(), "org": org_id, "label": legacy_label, "enabled": enabled},
        )

    def create_case(self, org_id: UUID, display_code: str) -> UUID:
        if not valid_key(display_code, 1024):
            raise BusinessError("DIRECTORY_INPUT_INVALID", 422)
        return self._insert(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(:id,:org,:code,'ACTIVE') RETURNING case_id",
            {"id": uuid4(), "org": org_id, "code": display_code},
        )

    def add_membership(self, user_id: UUID, org_id: UUID, case_id: UUID, *, expires_at: datetime | None = None) -> UUID:
        self._expiry(expires_at)
        return self._insert(
            "INSERT INTO mt.case_membership(membership_id,user_id,org_id,case_id,expires_at) VALUES(:id,:user,:org,:case,:expiry) RETURNING membership_id",
            {"id": uuid4(), "user": user_id, "org": org_id, "case": case_id, "expiry": expires_at},
        )

    def bind_identity(
        self,
        *,
        user_id: UUID,
        org_id: UUID,
        issuer: str,
        subject: str,
        mapping_version: str,
        enabled: bool = False,
        expires_at: datetime | None = None,
    ) -> UUID:
        if (
            not valid_key(issuer, 2048)
            or not valid_key(subject, 1024)
            or not valid_key(mapping_version, 1024)
            or type(enabled) is not bool
        ):
            raise BusinessError("DIRECTORY_INPUT_INVALID", 422)
        self._expiry(expires_at)
        return self._insert(
            "INSERT INTO mt.user_identities(identity_id,user_id,org_id,issuer,subject,mapping_version,enabled,expires_at) VALUES(:id,:user,:org,:issuer,:subject,:version,:enabled,:expiry) RETURNING identity_id",
            {
                "id": uuid4(),
                "user": user_id,
                "org": org_id,
                "issuer": issuer,
                "subject": subject,
                "version": mapping_version,
                "enabled": enabled,
                "expiry": expires_at,
            },
        )

    @staticmethod
    def _expiry(value: datetime | None) -> None:
        if value is not None and (not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None):
            raise BusinessError("DIRECTORY_INPUT_INVALID", 422)

    def resolve(self, issuer: str, subject: str) -> IdentityMapping:
        if not valid_key(issuer, 2048) or not valid_key(subject, 1024):
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        row = (
            self.connection.execute(
                text("SELECT * FROM mt.resolve_identity(:issuer,:subject)"), {"issuer": issuer, "subject": subject}
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        return IdentityMapping(
            identity_id=UUID(str(row["identity_id"])),
            user_id=UUID(str(row["user_id"])),
            org_id=UUID(str(row["org_id"])),
            mapping_version=str(row["mapping_version"]),
            identity_version=int(row["identity_version"]),
            user_version=int(row["user_version"]),
            org_version=int(row["org_version"]),
        )

    def _change(self, statement: str, identifier: UUID, expected_version: int) -> None:
        self._manager()
        if type(expected_version) is not int or expected_version < 1:
            raise BusinessError("DIRECTORY_INPUT_INVALID", 422)
        row = self.connection.execute(text(statement), {"id": identifier, "version": expected_version}).first()
        if row is None:
            raise BusinessError("DIRECTORY_VERSION_CONFLICT", 409)

    def revoke_identity(self, identity_id: UUID, *, expected_version: int) -> None:
        self._change(
            "UPDATE mt.user_identities SET enabled=false,revoked_at=now(),updated_at=now(),row_version=row_version+1 WHERE identity_id=:id AND row_version=:version AND revoked_at IS NULL RETURNING identity_id",
            identity_id,
            expected_version,
        )

    def disable_user(self, user_id: UUID, *, expected_version: int) -> None:
        self._change(
            "UPDATE mt.users SET enabled=false,updated_at=now(),row_version=row_version+1 WHERE user_id=:id AND row_version=:version RETURNING user_id",
            user_id,
            expected_version,
        )

    def disable_organization(self, org_id: UUID, *, expected_version: int) -> None:
        self._change(
            "UPDATE mt.organizations SET enabled=false,updated_at=now(),row_version=row_version+1 WHERE org_id=:id AND row_version=:version RETURNING org_id",
            org_id,
            expected_version,
        )

    def revoke_membership(self, membership_id: UUID, *, expected_version: int) -> None:
        self._change(
            "UPDATE mt.case_membership SET revoked_at=now(),updated_at=now(),row_version=row_version+1 WHERE membership_id=:id AND row_version=:version AND revoked_at IS NULL RETURNING membership_id",
            membership_id,
            expected_version,
        )

    def revoke_role(self, user_role_id: UUID, *, expected_version: int) -> None:
        self._change(
            "UPDATE mt.user_roles SET revoked_at=now(),updated_at=now(),row_version=row_version+1 WHERE user_role_id=:id AND row_version=:version AND revoked_at IS NULL RETURNING user_role_id",
            user_role_id,
            expected_version,
        )

    def user_state(self, user_id: UUID) -> tuple[UUID, bool, int]:
        self._manager()
        row = self.connection.execute(
            text("SELECT org_id,enabled,row_version FROM mt.users WHERE user_id=:id"), {"id": user_id}
        ).one()
        return UUID(str(row[0])), bool(row[1]), int(row[2])

    def identity_state(self, identity_id: UUID) -> tuple[bool, bool, int]:
        self._manager()
        row = self.connection.execute(
            text("SELECT enabled,revoked_at IS NOT NULL,row_version FROM mt.user_identities WHERE identity_id=:id"),
            {"id": identity_id},
        ).one()
        return bool(row[0]), bool(row[1]), int(row[2])
