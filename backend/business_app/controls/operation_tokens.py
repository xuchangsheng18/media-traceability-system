"""Case-bound one-use confirmation credentials; never independent action authority."""

import base64
import hashlib
import hmac
import re
import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import Connection, text

from ..db import Database
from ..errors import BusinessError
from ..permissions.policy import validate_principal
from ..permissions.rule_types import AuthorizationEvidence
from ..permissions.types import PermissionAuthority
from ..scope_collections import require_root
from ..scope_context import current_data_scope, current_scope_transaction
from ..types import Scope
from .approvals import Approvals
from .common import audit, canonical
from .providers import OperationTokenKey, OperationTokenKeys, OperationTokenRules
from .providers import OperationTokenRule as OperationTokenRule

BINDING_FIELDS = (
    "token_id",
    "org_id",
    "case_id",
    "actor_id",
    "approval_id",
    "approval_version",
    "object_type",
    "object_id",
    "object_version",
    "purpose",
    "action",
    "approval_policy_version",
    "permission_policy_version",
    "rule_version",
    "recovery_generation",
    "key_id",
    "principal_sha256",
    "request_sha256",
    "idempotency_key",
    "storage_version",
    "created_at",
    "expires_at",
)


def resolve_rule(provider: OperationTokenRules | None, scope: Scope, approval: dict[str, Any]) -> OperationTokenRule:
    if (
        provider is None
        or scope.case_id is None
        or approval.get("object_type") != "task"
        or approval.get("purpose") != "seal"
    ):
        raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503)
    try:
        rule = provider.resolve(scope, approval)
        if not isinstance(rule, OperationTokenRule):
            raise ValueError()
        return rule
    except BusinessError:
        raise
    except Exception:
        raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503) from None


def derive_token(item: dict[str, Any], key: OperationTokenKey) -> str:
    if not isinstance(key, OperationTokenKey) or item.get("key_id") != key.key_id or item.get("storage_version") != 1:
        raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503)
    values = {}
    for name in BINDING_FIELDS:
        value = item[name]
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503)
            value = value.astimezone(timezone.utc).isoformat(timespec="microseconds")
        elif isinstance(value, UUID):
            value = str(value)
        values[name] = value
    mac = hmac.new(key.material, b"media-trace/operation-token/v1\0" + canonical(values), hashlib.sha256).digest()
    encoded = base64.urlsafe_b64encode(mac).rstrip(b"=").decode("ascii")
    return "mtop1." + UUID(str(item["token_id"])).hex + "." + encoded


def token_identifier(value: str) -> UUID:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"mtop1\.[0-9a-f]{32}\.[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]", value) is None
    ):
        raise BusinessError("OPERATION_TOKEN_INVALID", 403)
    identifier = UUID(hex=value.split(".")[1])
    if identifier.int == 0:
        raise BusinessError("OPERATION_TOKEN_INVALID", 403)
    return identifier


class OperationTokens:
    def __init__(
        self,
        database: Database,
        approvals: Approvals,
        rules: OperationTokenRules | None,
        keys: OperationTokenKeys | None,
        confirmation_authority: PermissionAuthority | None,
    ) -> None:
        self.database, self.approvals, self.rules, self.keys = database, approvals, rules, keys
        self.confirmation_authority = confirmation_authority

    def _evidence(self, connection: Connection, scope: Scope, operation: str) -> AuthorizationEvidence:
        root = current_scope_transaction()
        if root is None or root.database is not self.database:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        bound = require_root(connection, current_data_scope())
        proof = bound.evidence
        if (
            not isinstance(proof, AuthorizationEvidence)
            or proof.operation_id != operation
            or proof.principal.actor != scope.actor
            or proof.target.case_id != scope.case_id
            or scope.case_id is None
            or not bound.mutation
            or proof.valid_until <= time.time()
        ):
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        validate_principal(proof.principal, time.time)
        if self.confirmation_authority is None:
            raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503)
        try:
            result = cast(Callable[..., object], self.confirmation_authority.check)(
                proof.principal, "operation.confirm"
            )
            if result is not None:
                raise ValueError()
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503) from None
        return proof

    def _key(self, identifier: str | None = None) -> OperationTokenKey:
        if self.keys is None:
            raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503)
        try:
            current = self.keys.current()
            value = current if identifier is None else self.keys.get(identifier)
            if (
                not isinstance(current, OperationTokenKey)
                or not isinstance(value, OperationTokenKey)
                or current.key_id != value.key_id
                or not hmac.compare_digest(current.material, value.material)
            ):
                raise ValueError()
            return value
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503) from None

    def _source_snapshot(self, connection: Connection, scope: Scope, task_id: UUID) -> dict[str, Any]:
        # The current task schema has one asset; bind its actual SQL source chain.
        source = (
            connection.execute(
                text(
                    "SELECT a.asset_id,s.source_id,s.authorization_version,s.authorization_status,s.purpose,s.expires_at,s.row_version FROM mt.analysis_task t JOIN mt.media_asset a ON a.org_id=t.org_id AND a.case_id=t.case_id AND a.asset_id=t.asset_id JOIN mt.source_registry s ON s.org_id=a.org_id AND s.case_id=a.case_id AND s.source_id=a.source_id WHERE t.org_id=:org AND t.case_id=:case AND t.task_id=:task"
                ),
                dict(org=scope.actor.org_id, case=scope.case_id, task=task_id),
            )
            .mappings()
            .one_or_none()
        )
        if (
            source is None
            or source["authorization_status"] != "verified"
            or not source["authorization_version"]
            or "analysis" not in source["purpose"]
            or (source["expires_at"] is not None and source["expires_at"].timestamp() <= time.time())
        ):
            raise BusinessError("OPERATION_TOKEN_STATE_CONFLICT", 409)
        return dict(
            asset_id=str(source["asset_id"]),
            source_id=str(source["source_id"]),
            authorization_version=source["authorization_version"],
            authorization_status=source["authorization_status"],
            purpose=sorted(source["purpose"]),
            expires_at=source["expires_at"].isoformat() if source["expires_at"] else None,
            row_version=int(source["row_version"]),
        )

    def _approval(
        self, connection: Connection, scope: Scope, body: dict[str, Any]
    ) -> tuple[dict[str, Any], OperationTokenRule, str]:
        detail = self.approvals.detail(connection, scope, UUID(body["approval_id"]), shared_binding=True)
        approval, binding = detail["approval"], detail["binding"]
        if approval["state"] != "APPROVED":
            raise BusinessError("OPERATION_TOKEN_STATE_CONFLICT", 409)
        if (
            binding["case_id"] != str(scope.case_id)
            or binding["requested_by"] != str(scope.actor.user_id)
            or (binding["object_id"], approval["object_version"], approval["purpose"])
            != (str(body["object_id"]), body["object_version"], body["purpose"])
        ):
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        rule = resolve_rule(self.rules, scope, dict(approval, **binding))
        sources = self._source_snapshot(connection, scope, UUID(binding["object_id"]))
        request_sha = hashlib.sha256(canonical([body, detail, sources])).hexdigest()
        return detail, rule, request_sha

    @staticmethod
    def _principal_sha(proof: AuthorizationEvidence) -> str:
        # Freshness expiry is not identity. Reauthentication cannot extend token TTL.
        principal = proof.principal
        return hashlib.sha256(
            canonical(
                dict(
                    actor={k: str(v) for k, v in asdict(principal.actor).items()},
                    issuer=principal.issuer,
                    subject=principal.subject,
                )
            )
        ).hexdigest()

    def _validate(
        self,
        connection: Connection,
        scope: Scope,
        item: dict[str, Any],
        proof: AuthorizationEvidence,
        *,
        consumed: bool,
    ) -> str:
        if item["storage_version"] != 1 or (item["org_id"], item["case_id"], item["actor_id"]) != (
            scope.actor.org_id,
            scope.case_id,
            scope.actor.user_id,
        ):
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        if (item["consumed_at"] is not None) != consumed or item["expires_at"].timestamp() <= time.time():
            raise BusinessError("OPERATION_TOKEN_STATE_CONFLICT", 409)
        body = dict(
            approval_id=str(item["approval_id"]),
            object_id=str(item["object_id"]),
            object_version=int(item["object_version"]),
            purpose=item["purpose"],
        )
        detail, rule, request_sha = self._approval(connection, scope, body)
        if (
            item["request_sha256"] != request_sha
            or item["approval_version"] != detail["approval"]["version"]
            or item["approval_policy_version"] != detail["approval"]["policy_version"]
            or item["object_type"] != detail["binding"]["object_type"]
            or item["action"] != rule.action
            or item["rule_version"] != rule.version
            or item["expires_at"] > item["created_at"] + timedelta(seconds=rule.ttl_seconds)
            or item["permission_policy_version"] != proof.policy_version
            or item["recovery_generation"] != proof.recovery_generation
            or item["principal_sha256"] != self._principal_sha(proof)
        ):
            raise BusinessError("OPERATION_TOKEN_STATE_CONFLICT", 409)
        credential = derive_token(item, self._key(item["key_id"]))
        if not hmac.compare_digest(hashlib.sha256(credential.encode()).hexdigest(), item["token_sha256"]):
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        return credential

    @staticmethod
    def _stored(connection: Connection, token_id: UUID, *, lock: bool = True) -> dict[str, Any]:
        found = (
            connection.execute(
                text("SELECT * FROM mt.operation_token WHERE token_id=:id" + (" FOR UPDATE" if lock else "")),
                dict(id=token_id),
            )
            .mappings()
            .one_or_none()
        )
        if found is None:
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        return dict(found)

    def _finish(self, connection: Connection, scope: Scope, identifier: UUID, operation: str, consumed: bool) -> None:
        proof = self._evidence(connection, scope, operation)
        self._validate(connection, scope, self._stored(connection, identifier), proof, consumed=consumed)

    def issue(self, scope: Scope, body: dict[str, Any], request: Request, key: str) -> dict[str, Any]:
        from ..contracts import validate_api

        validate_api("OperationTokenRequest", body)
        body = dict(body, approval_id=str(UUID(body["approval_id"])), object_id=str(UUID(body["object_id"])))
        if not isinstance(key, str) or not 1 <= len(key) <= 128:
            raise BusinessError("INPUT_INVALID", 422)
        with self.database.transaction(scope) as connection:
            proof = self._evidence(connection, scope, "issueOperationToken")
            if proof.target.kind != "approval" or str(proof.target.object_id) != body["approval_id"]:
                raise BusinessError("OPERATION_TOKEN_INVALID", 403)
            detail, rule, request_sha = self._approval(connection, scope, body)
            lock_key = canonical(
                [str(scope.actor.org_id), str(scope.case_id), str(scope.actor.user_id), "issueOperationToken", key]
            )
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:key)"),
                dict(key=int.from_bytes(hashlib.sha256(lock_key).digest()[:8], "big", signed=True)),
            )
            existing = (
                connection.execute(
                    text(
                        "SELECT * FROM mt.operation_token WHERE org_id=:org AND case_id=:case AND actor_id=:actor AND idempotency_key=:key AND storage_version=1 FOR UPDATE"
                    ),
                    dict(org=scope.actor.org_id, case=scope.case_id, actor=scope.actor.user_id, key=key),
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                item = dict(existing)
                if item["request_sha256"] != request_sha:
                    raise BusinessError("IDEMPOTENCY_CONFLICT", 409)
                credential = self._validate(connection, scope, item, proof, consumed=False)
            else:
                current = datetime.now(timezone.utc)
                secret = self._key()
                expires = min(
                    current + timedelta(seconds=rule.ttl_seconds),
                    datetime.fromisoformat(detail["approval"]["expires_at"]),
                    datetime.fromtimestamp(min(proof.valid_until, proof.principal.expires_at), timezone.utc),
                )
                if expires <= current:
                    raise BusinessError("OPERATION_TOKEN_STATE_CONFLICT", 409)
                item = dict(
                    token_id=uuid4(),
                    org_id=scope.actor.org_id,
                    case_id=scope.case_id,
                    actor_id=scope.actor.user_id,
                    approval_id=UUID(body["approval_id"]),
                    approval_version=detail["approval"]["version"],
                    object_type=detail["binding"]["object_type"],
                    object_id=UUID(body["object_id"]),
                    object_version=body["object_version"],
                    purpose=body["purpose"],
                    action=rule.action,
                    approval_policy_version=detail["approval"]["policy_version"],
                    permission_policy_version=proof.policy_version,
                    rule_version=rule.version,
                    recovery_generation=proof.recovery_generation,
                    key_id=secret.key_id,
                    principal_sha256=self._principal_sha(proof),
                    request_sha256=request_sha,
                    idempotency_key=key,
                    storage_version=1,
                    created_at=current,
                    expires_at=expires,
                    created_by=scope.actor.user_id,
                )
                credential = derive_token(item, secret)
                item["token_sha256"] = hashlib.sha256(credential.encode()).hexdigest()
                columns = tuple(item)
                connection.execute(
                    text(
                        "INSERT INTO mt.operation_token("
                        + ",".join(columns)
                        + ") VALUES("
                        + ",".join(":" + column for column in columns)
                        + ")"
                    ),
                    item,
                )
                audit(connection, scope, "operation_token.issue", "operation_token", item["token_id"], 1, request)
            self.database.before_commit(
                connection, lambda: self._finish(connection, scope, item["token_id"], "issueOperationToken", False)
            )
            return dict(
                operation_token=credential,
                expires_at=item["expires_at"].isoformat(),
                object_version=int(item["object_version"]),
            )

    def consume(
        self,
        connection: Connection,
        scope: Scope,
        token: str,
        *,
        approval_id: UUID,
        action: str,
        object_id: UUID,
        object_version: int,
        request: Request,
    ) -> None:
        proof = self._evidence(connection, scope, action)
        if (
            action != "sealEvidence"
            or proof.target.kind != "task"
            or proof.target.object_id != object_id
            or proof.target.object_version != object_version
            or type(object_version) is not int
        ):
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        identifier = token_identifier(token)
        located = self._stored(connection, identifier, lock=False)
        # Approval/task shared locks precede the token row lock in every path.
        # An unlocked locator never authorizes consumption; the locked row and
        # all bindings are checked again below before any mutation.
        self._approval(
            connection,
            scope,
            dict(
                approval_id=str(located["approval_id"]),
                object_id=str(located["object_id"]),
                object_version=int(located["object_version"]),
                purpose=located["purpose"],
            ),
        )
        item = self._stored(connection, identifier)
        if (item["approval_id"], item["action"], item["object_id"], item["object_version"]) != (
            approval_id,
            action,
            object_id,
            object_version,
        ):
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        credential = self._validate(connection, scope, item, proof, consumed=False)
        if not hmac.compare_digest(credential, token):
            raise BusinessError("OPERATION_TOKEN_INVALID", 403)
        updated = connection.execute(
            text(
                "UPDATE mt.operation_token SET consumed_at=clock_timestamp(),updated_at=clock_timestamp(),row_version=row_version+1 WHERE token_id=:id AND consumed_at IS NULL AND expires_at>clock_timestamp() AND storage_version=1 RETURNING token_id"
            ),
            dict(id=item["token_id"]),
        ).scalar_one_or_none()
        if updated is None:
            raise BusinessError("OPERATION_TOKEN_STATE_CONFLICT", 409)
        audit(connection, scope, "operation_token.consume", "operation_token", item["token_id"], 2, request)
        self.database.before_commit(connection, lambda: self._finish(connection, scope, item["token_id"], action, True))
