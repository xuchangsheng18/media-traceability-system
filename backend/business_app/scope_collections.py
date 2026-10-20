"""Bound task versions and fixed per-object collection decisions, never client allowlists."""

from __future__ import annotations

import json
import math
import time
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from sqlalchemy import Connection, text

from .data_scope import AccessMode, DataScope, LookupKey, ResourceBinding, TaskBinding
from .errors import BusinessError
from .permissions.context import RequestAuthorization, current_authorization, evidence_actor
from .permissions.object_facts import digest
from .permissions.rule_types import AuthorizationEvidence, RuleTarget
from .scope_catalog import lookup_spec
from .scope_context import current_data_scope, current_scope_transaction, scope_is_subset
from .scope_lookup import SqlScopeLookup

if TYPE_CHECKING:
    from .permissions.conditional import ConditionalPort
    from .permissions.types import Principal

COLLECTION_KINDS = MappingProxyType(
    {
        "listApprovals": "approval",
        "listReviews": "review",
        "listPendingReviews": "task",
        "listAuditEvents": "audit_event",
        "listSources": "source",
        "listPolicies": "policy",
    }
)
COLLECTION_TABLES = MappingProxyType(
    {
        "approval": ("approval_request", "approval_id"),
        "review": ("review_record", "review_id"),
        "task": ("analysis_task", "task_id"),
        "audit_event": ("audit_event", "event_id"),
        "source": ("source_registry", "source_id"),
        "policy": ("policy_registry", "policy_id"),
    }
)


def require_root(connection: Connection, scope: DataScope | None) -> RequestAuthorization:
    root, current, authorization = current_scope_transaction(), current_data_scope(), current_authorization()
    if (
        not isinstance(scope, DataScope)
        or scope.mode is AccessMode.LOOKUP
        or root is None
        or root.connection is not connection
        or not connection.in_transaction()
        or current != scope
        or not scope_is_subset(root.scope, scope)
        or authorization is None
        or root.authorization is None
        or authorization.fence is None
        or authorization.evidence is not root.authorization.evidence
        or authorization.fence is not root.authorization.fence
        or evidence_actor(authorization.evidence) != scope.actor
        or authorization.evidence.operation_id != scope.operation_id
    ):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    return authorization


def require_resource(connection: Connection, scope: DataScope | None, kind: str, identifier: UUID) -> None:
    authorization = require_root(connection, scope)
    target = authorization.evidence.target
    if target.kind == kind and target.object_id is not None and target.object_id != identifier:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)


def bind_task_scope(connection: Connection, scope: DataScope | None, task: TaskBinding) -> DataScope:
    authorization = require_root(connection, scope)
    if scope is None or scope.mode is not AccessMode.CASE or not isinstance(task, TaskBinding):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    parent = scope.task_binding
    if parent is not None and parent.task_id == task.task_id and task.run_version is None:
        task = TaskBinding(task.task_id, parent.run_version, parent.result_version)
    target = authorization.evidence.target
    anchors = {
        "review": ("review_record", "review_id"),
        "report": ("report", "report_id"),
        "evidence_package": ("evidence_package", "package_id"),
        "approval": ("approval_request", "approval_id"),
    }
    if target.kind in anchors:
        table, key = anchors[target.kind]
        fields = (
            "object_type,object_id AS task_id,run_version,result_version"
            if target.kind == "approval"
            else "task_id,run_version,result_version"
        )
        anchor = (
            connection.execute(
                text(f"SELECT {fields} FROM mt.{table} WHERE org_id=:org AND case_id=:case AND {key}=:id"),
                dict(org=scope.actor.org_id, case=scope.case_id, id=target.object_id),
            )
            .mappings()
            .one_or_none()
        )
        if anchor is None:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if target.kind != "approval" or anchor["object_type"] == "task":
            if task.task_id != anchor["task_id"] or any(
                wanted is not None and wanted != anchor[name]
                for name, wanted in (("run_version", task.run_version), ("result_version", task.result_version))
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            task = TaskBinding(task.task_id, int(anchor["run_version"]), int(anchor["result_version"]))
    limited = replace(scope, task_binding=task)
    if not scope_is_subset(scope, limited):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    if target.kind == "task" and target.object_id != task.task_id:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    params = dict(
        org=scope.actor.org_id, case=scope.case_id, task=task.task_id, run=task.run_version, result=task.result_version
    )
    found = connection.execute(
        text("SELECT 1 FROM mt.analysis_task WHERE org_id=:org AND case_id=:case AND task_id=:task"), params
    ).scalar_one_or_none()
    if found is None:
        raise BusinessError("TASK_NOT_FOUND", 404)
    if (
        task.run_version is not None
        and connection.execute(
            text(
                "SELECT 1 FROM mt.task_run WHERE org_id=:org AND case_id=:case AND task_id=:task AND run_version=:run"
            ),
            params,
        ).scalar_one_or_none()
        is None
    ):
        raise BusinessError("TASK_RUN_NOT_FOUND", 404)
    if task.result_version is not None:
        result = connection.execute(
            text(
                "SELECT 1 FROM mt.task_result WHERE org_id=:org AND case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result"
            ),
            params,
        ).scalar_one_or_none()
        if result is None:
            raise BusinessError("RESULT_NOT_FOUND", 404)
        if target.kind in {"asset", "cluster"}:
            selector = json.dumps(
                {
                    "snapshot": {
                        "api_projections": [
                            {
                                "operation_id": scope.operation_id,
                                "resource_id": str(target.object_id),
                            }
                        ]
                    }
                }
            )
            related = connection.execute(
                text(
                    "SELECT 1 FROM mt.task_result WHERE org_id=:org AND case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result AND summary @> CAST(:selector AS jsonb)"
                ),
                dict(params, selector=selector),
            ).scalar_one_or_none()
            if related is None:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
    return limited


def collection_metadata(
    connection: Connection,
    scope: DataScope | None,
    principal: Principal,
    operation: str,
    target: RuleTarget,
) -> dict[str, Any]:
    """Fixed projections inside an existing CASE/ORG root; no new LOOKUP capability."""
    authorization = require_root(connection, scope)
    if (
        scope is None
        or COLLECTION_KINDS.get(operation) != target.kind
        or not isinstance(authorization.evidence, AuthorizationEvidence)
        or authorization.evidence.principal != principal
        or scope.operation_id != operation
        or target.org_id != scope.actor.org_id
        or target.case_id != scope.case_id
        or target.object_id is None
    ):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    root = current_scope_transaction()
    assert root is not None
    database = cast(Any, root.database)
    port = SqlScopeLookup(database)
    if target.kind in {"review", "task"}:
        return port.load(principal, operation, LookupKey(target.kind, target.object_id), connection=connection)
    base = port.load(
        principal,
        operation,
        LookupKey("operation", scope.case_id) if scope.case_id is not None else LookupKey("user", scope.actor.user_id),
        connection=connection,
    )
    table, key = COLLECTION_TABLES[target.kind]
    columns = (
        (
            key,
            "org_id",
            "case_id",
            "row_version",
            "created_by",
            "actor_id",
            "occurred_at",
            "object_type",
            "object_id",
            "object_version",
        )
        if target.kind == "audit_event"
        else lookup_spec(target.kind).projection
    )
    predicate = "t.org_id=:org AND " + ("t.case_id=:case" if scope.case_id is not None else "TRUE")
    if (scope.case_id is None) != (target.kind == "policy"):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    record = (
        connection.execute(
            text(
                "SELECT "
                + ",".join("t." + name for name in columns)
                + ",encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') AS _row_sha256"
                + f" FROM mt.{table} t WHERE {predicate} AND t.{key}=:id"
                + (" FOR SHARE" if target.kind != "audit_event" else "")
            ),
            dict(org=scope.actor.org_id, case=scope.case_id, id=target.object_id),
        )
        .mappings()
        .one_or_none()
    )
    if record is None:
        raise BusinessError("RESOURCE_NOT_FOUND", 404)
    envelope = dict(base, record=json.loads(json.dumps(dict(record), default=str)), related=[], sources=[])
    if target.kind == "source":
        source_fields = (
            "source_id",
            "org_id",
            "case_id",
            "authorization_status",
            "authorization_version",
            "purpose",
            "expires_at",
            "row_version",
        )
        envelope["sources"] = [{name: envelope["record"][name] for name in source_fields}]
    return envelope


class CollectionScope:
    """A request-local receipt; a missing trusted per-item port is a failure."""

    def __init__(self, authority: ConditionalPort) -> None:
        self.authority = authority
        self.fingerprint: str | None = None

    def allowed_ids(
        self,
        connection: Connection,
        scope: DataScope | None,
        candidates: tuple[ResourceBinding, ...],
    ) -> tuple[UUID, ...]:
        bound = require_root(connection, scope)
        if scope is None or not isinstance(bound.evidence, AuthorizationEvidence):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        evidence = bound.evidence
        kind = COLLECTION_KINDS.get(scope.operation_id)
        header = "policy_collection" if scope.operation_id == "listPolicies" else "case"
        if evidence.target.kind != header:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        port = getattr(self.authority, "authorize_collection_item", None)
        if kind is None or not callable(port) or type(candidates) is not tuple:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        if any(not isinstance(item, ResourceBinding) or item.kind != kind for item in candidates) or len(
            {item.identifier for item in candidates}
        ) != len(candidates):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        allowed, versions = [], []
        for item in sorted(candidates, key=lambda value: str(value.identifier)):
            target = RuleTarget(
                scope.actor.org_id,
                kind,
                item.identifier,
                item.row_version,
                scope.case_id,
                None,
                None,
                request_digest=digest(
                    [
                        "collection",
                        scope.operation_id,
                        str(scope.actor.user_id),
                        str(scope.actor.org_id),
                        str(scope.case_id),
                    ]
                ),
            )
            try:
                metadata = collection_metadata(connection, scope, evidence.principal, scope.operation_id, target)
                record = metadata["record"]
                if item.row_version is not None and record["row_version"] != item.row_version:
                    raise BusinessError("AUTHORIZATION_OBJECT_STALE", 409)
                if item.task is not None:
                    actual = (record.get("task_id"), record.get("run_version"), record.get("result_version"))
                    if actual != (str(item.task.task_id), item.task.run_version, item.task.result_version):
                        raise BusinessError("RESOURCE_NOT_FOUND", 404)
                    bind_task_scope(connection, scope, item.task)
                target = replace(
                    target,
                    object_version=int(record["row_version"]),
                    purpose=record.get("purpose") if isinstance(record.get("purpose"), str) else None,
                    policy_kind=record.get("kind") if kind == "policy" else None,
                )
                fresh = port(evidence.principal, scope.operation_id, target, connection=connection)
                current = time.time()
                if (
                    not isinstance(fresh, AuthorizationEvidence)
                    or fresh.principal != evidence.principal
                    or fresh.operation_id != scope.operation_id
                    or fresh.target != target
                    or (fresh.policy_version, fresh.recovery_generation, fresh.role_digest)
                    != (evidence.policy_version, evidence.recovery_generation, evidence.role_digest)
                    or type(fresh.valid_until) not in (int, float)
                    or not math.isfinite(fresh.valid_until)
                    or fresh.valid_until <= current
                ):
                    raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            except BusinessError as error:
                if error.http_status not in {403, 404}:
                    raise
            except Exception:
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
            else:
                allowed.append(item.identifier)
                versions.append(
                    [
                        str(item.identifier),
                        fresh.role_digest,
                        fresh.condition_digest,
                        fresh.policy_version,
                        fresh.recovery_generation,
                    ]
                )
        self.fingerprint = digest(
            [
                str(scope.actor.user_id),
                str(scope.actor.org_id),
                str(scope.case_id),
                scope.operation_id,
                evidence.policy_version,
                evidence.recovery_generation,
                versions,
            ]
        )
        return tuple(allowed)
