"""Fenced, atomic task acceptance using an explicitly supplied materials port.

This component neither issues a Proof nor adopts a mapping. There is no default
provider, HTTP entry point, handler execution, message publication or deployment
configuration here. MaterialBudgets bound parsing; aggregate/runtime budgets and
the end-to-end execution deadline require their separate runtime integration.
"""

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any, Protocol, cast
from uuid import UUID, uuid4

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from .contracts import REGISTRY, SCHEMAS, validate_response
from .controls.common import canonical, etag
from .controls.receipts import ControlReceipts
from .data_scope import AccessMode
from .db import Database
from .errors import BusinessError
from .permissions.rule_types import AuthorizationEvidence
from .permissions.task_creation_context import (
    TaskCreationContext,
    _context_copy,
    current_task_creation_context,
)
from .scope_collections import require_root
from .scope_context import current_data_scope, current_scope_transaction
from .settings import BusinessSettings
from .task_creation import _aware, _now, _time, freeze_task_create
from .task_creation_authority import ExecutionMaterials, _execution_copy, recheck_execution_materials
from .task_creation_materials import MaterialBudgets, _limits
from .types import Scope

_RECEIPT_VERSION = "task-create-control-receipt-v1"
_EVENT_TYPE = "workflow.run.accepted.v1"
_REASON = "TASK_ACCEPTED"
_PLAN_FIELDS = (
    "case_id",
    "task_id",
    "run_version",
    "org_id",
    "created_by",
    "created_at",
    "request_body_bytes",
    "request_body_sha256",
    "authorization_request_digest",
    "revision_id",
    "mapping_id",
    "mapping_version",
    "authority_version",
    "head_row_version",
    "policy_id",
    "policy_kind",
    "policy_version",
    "policy_sha256",
    "policy_bytes",
    "plan_id",
    "plan_version",
    "plan_sha256",
    "plan_bytes",
    "capability_id",
    "capability_version",
    "capability_sha256",
    "capability_bytes",
    "input_manifest_bytes",
    "input_sha256",
    "validation_receipt_bytes",
    "validation_receipt_sha256",
    "mapping_valid_from",
    "mapping_valid_until",
    "proof_observed_at",
    "proof_valid_until",
    "recovery_generation",
)
_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "accepted",
        "etag",
        "actor_id",
        "org_id",
        "case_id",
        "task_id",
        "task_run_id",
        "request_id",
        "event_id",
        "audit_event_id",
        "request_sha256",
        "authorization_request_digest",
        "binding",
        "run_plan_sha256",
        "accepted_projection",
        "nodes",
        "idempotency_key",
    }
)


class TaskCreationMaterialsPort(Protocol):
    """Deployment-owned facts and exact bytes; callers must explicitly inject it."""

    def read(self, context: TaskCreationContext, *, connection: Connection) -> ExecutionMaterials: ...


def _unavailable() -> BusinessError:
    return BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)


def _conflict() -> BusinessError:
    return BusinessError("IDEMPOTENCY_CONFLICT", 409)


def _scope_invalid() -> BusinessError:
    return BusinessError("AUTHORITY_SCOPE_INVALID", 503)


def _json_value(value: Any) -> Any:
    """Explicit database normalization, preserving booleans, empty and null values."""
    if type(value) is UUID:
        return str(value)
    if type(value) in (bytes, memoryview):
        return bytes(value).hex()
    if type(value) is datetime:
        if not _aware(value):
            raise _conflict()
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_value(item) for item in value]
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise _conflict()


def _same(left: Any, right: Any) -> bool:
    # canonical equality deliberately distinguishes True/1 and 1/1.0.
    return canonical(_json_value(left)) == canonical(_json_value(right))


def _identifier(value: Any) -> UUID:
    try:
        if type(value) is not str:
            raise ValueError()
        result = UUID(value)
        if result.int == 0 or str(result) != value:
            raise ValueError()
        return result
    except (ValueError, TypeError, AttributeError):
        raise _conflict() from None


def _accepted(task_id: UUID) -> dict[str, Any]:
    result = dict(task_id=str(task_id), state="QUEUED", status_url=f"/api/v1/analysis/tasks/{task_id}/execution")
    validate_response("Accepted", result)
    return result


def _event(
    scope: Scope, execution: ExecutionMaterials, task_id: UUID, event_id: UUID, request_id: UUID, occurred_at: datetime
) -> dict[str, Any]:
    result = dict(
        schema_version="1.0.0",
        event_type=_EVENT_TYPE,
        event_id=str(event_id),
        occurred_at=occurred_at.astimezone(timezone.utc).isoformat(),
        request_id=str(request_id),
        producer_role="scheduler",
        binding=dict(
            org_id=str(scope.actor.org_id),
            case_id=str(scope.case_id),
            task_id=str(task_id),
            run_version=1,
            result_version=None,
            policy_version=execution.binding.policy_version,
            dag_version=execution.materials.plan.version,
        ),
        node_id=None,
        attempt=None,
        fencing_epoch=1,
        state="QUEUED",
        result_snapshot_ref=None,
        reason=_REASON,
    )
    try:
        Draft202012Validator(
            SCHEMAS["urn:media-trace:stage-one:domain-event:0.1.0"],
            registry=REGISTRY,
            format_checker=FormatChecker(),
        ).validate(result)
    except (ValidationError, KeyError, TypeError, ValueError):
        raise BusinessError("RESPONSE_CONTRACT_UNAVAILABLE", 503) from None
    return result


def _plan_values(
    context: TaskCreationContext, execution: ExecutionMaterials, task_id: UUID, observed: datetime
) -> dict[str, Any]:
    binding, bundle, request = execution.binding, execution.materials, context.request
    proof = binding.proof
    return dict(
        case_id=request.case_id,
        task_id=task_id,
        run_version=1,
        org_id=request.actor.org_id,
        created_by=request.actor.user_id,
        request_body_bytes=request.canonical_body,
        request_body_sha256=request.request_sha256,
        authorization_request_digest=context.authorization_request_digest,
        revision_id=binding.revision_id,
        mapping_id=binding.mapping_id,
        mapping_version=binding.mapping_version,
        authority_version=proof.authority_version,
        head_row_version=binding.head_row_version,
        policy_id=binding.policy_id,
        policy_kind=binding.policy_kind,
        policy_version=binding.policy_version,
        policy_sha256=bundle.policy.sha256,
        policy_bytes=bundle.policy.canonical_bytes,
        plan_id=bundle.plan.document_id,
        plan_version=bundle.plan.version,
        plan_sha256=bundle.plan.sha256,
        plan_bytes=bundle.plan.canonical_bytes,
        capability_id=bundle.capability.document_id,
        capability_version=bundle.capability.version,
        capability_sha256=bundle.capability.sha256,
        capability_bytes=bundle.capability.canonical_bytes,
        input_manifest_bytes=bundle.inputs.canonical_bytes,
        input_sha256=bundle.inputs.sha256,
        validation_receipt_bytes=binding.validation_receipt_bytes,
        validation_receipt_sha256=binding.validation_receipt_sha256,
        mapping_valid_from=binding.mapping_valid_from,
        mapping_valid_until=binding.mapping_valid_until,
        proof_observed_at=observed,
        proof_valid_until=proof.valid_until,
        recovery_generation=binding.recovery_generation,
    )


def _binding(execution: ExecutionMaterials) -> dict[str, Any]:
    value = execution.binding
    proof = value.proof
    return cast(
        dict[str, Any],
        _json_value(
            dict(
                revision_id=value.revision_id,
                head_row_version=value.head_row_version,
                mapping_id=value.mapping_id,
                mapping_version=value.mapping_version,
                authority_version=proof.authority_version,
                policy_id=value.policy_id,
                policy_kind=value.policy_kind,
                policy_version=value.policy_version,
                policy_sha256=proof.policy_sha256,
                plan_id=proof.plan_id,
                plan_version=proof.plan_version,
                plan_sha256=proof.plan_sha256,
                capability_id=proof.capability_id,
                capability_version=proof.capability_version,
                capability_sha256=proof.capability_sha256,
                input_sha256=execution.materials.inputs.sha256,
                validation_receipt_sha256=value.validation_receipt_sha256,
                current_state_facts_sha256=value.current_state_facts_sha256,
                mapping_valid_from=value.mapping_valid_from,
                mapping_valid_until=value.mapping_valid_until,
                recovery_generation=value.recovery_generation,
            )
        ),
    )


class TaskCreationService:
    def __init__(
        self,
        database: Database,
        settings: BusinessSettings,
        *,
        materials_reader: TaskCreationMaterialsPort | None = None,
        budgets: MaterialBudgets,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        _limits(budgets)
        self.database, self.settings, self.materials_reader = database, settings, materials_reader
        self.budgets, self.clock = budgets, clock
        self.receipts = ControlReceipts(database, settings)

    def _context(self, scope: Scope, body: dict[str, Any]) -> TaskCreationContext:
        request = freeze_task_create(scope, body)
        context = current_task_creation_context(clock=lambda: _time(self.clock).timestamp())
        if context is None or context.request != request:
            raise _scope_invalid()
        return context

    def _root(self, connection: Connection, scope: Scope, context: TaskCreationContext) -> None:
        data_scope, root = current_data_scope(), current_scope_transaction()
        authorization = require_root(connection, data_scope)
        evidence = authorization.evidence
        if (
            root is None
            or root.database is not self.database
            or data_scope is None
            or data_scope.mode is not AccessMode.CASE
            or data_scope.operation_id != "createTask"
            or data_scope.actor != scope.actor
            or data_scope.case_id != scope.case_id
            or data_scope.task_binding is not None
            or authorization.mutation is not True
            or type(evidence) is not AuthorizationEvidence
            or evidence.principal != context.principal
            or evidence.operation_id != "createTask"
            or (
                evidence.target.org_id,
                evidence.target.case_id,
                evidence.target.kind,
                evidence.target.object_id,
                evidence.target.purpose,
                evidence.target.request_digest,
            )
            != (
                scope.actor.org_id,
                scope.case_id,
                "asset",
                context.request.asset_id,
                "analysis",
                context.authorization_request_digest,
            )
            or evidence.valid_until <= _time(self.clock).timestamp()
        ):
            raise _scope_invalid()

    def _read(self, connection: Connection, context: TaskCreationContext) -> ExecutionMaterials:
        reader = self.materials_reader
        if reader is None:
            raise _unavailable()
        try:
            supplied = reader.read(_context_copy(context, lambda: _time(self.clock).timestamp()), connection=connection)
            return _execution_copy(context, supplied, self.budgets, _time(self.clock))
        except BusinessError:
            raise
        except SQLAlchemyError:
            raise BusinessError("DATABASE_UNAVAILABLE", 503) from None
        except Exception:
            raise _unavailable() from None

    def _asset(
        self, connection: Connection, scope: Scope, context: TaskCreationContext, execution: ExecutionMaterials
    ) -> None:
        row = (
            connection.execute(
                text(
                    "SELECT a.state,a.sha256,a.row_version,a.source_id,o.object_id,o.version_id,o.sha256 AS object_sha256,"
                    "s.authorization_status,s.authorization_version,s.purpose,s.expires_at "
                    "FROM mt.media_asset a JOIN mt.object_version o ON o.case_id=a.case_id AND o.org_id=a.org_id "
                    "AND o.object_id=a.object_id JOIN mt.source_registry s ON s.case_id=a.case_id AND s.org_id=a.org_id "
                    "AND s.source_id=a.source_id WHERE a.org_id=:org AND a.case_id=:case AND a.asset_id=:asset "
                    "FOR SHARE OF a,s"
                ),
                dict(org=scope.actor.org_id, case=scope.case_id, asset=context.request.asset_id),
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if row["state"] != "VALID":
            raise BusinessError("ASSET_STATE_CONFLICT", 409)
        if (
            row["authorization_status"] != "verified"
            or "analysis" not in row["purpose"]
            or (row["expires_at"] is not None and row["expires_at"] <= _time(self.clock))
        ):
            raise BusinessError("PERMISSION_REQUIRED", 403)
        authorization = require_root(connection, current_data_scope())
        target = authorization.evidence.target
        if authorization.evidence.recovery_generation != execution.binding.recovery_generation:
            raise _scope_invalid()
        if (target.object_version is not None and target.object_version != row["row_version"]) or (
            target.source_ids and row["source_id"] not in target.source_ids
        ):
            raise _scope_invalid()
        asset = execution.materials.inputs.as_dict()["asset"]
        if not _same(
            asset,
            dict(
                asset_id=str(context.request.asset_id),
                sha256=row["sha256"],
                object_ref=dict(
                    object_id=str(row["object_id"]), version_id=row["version_id"], sha256=row["object_sha256"]
                ),
                source_authorization_version=row["authorization_version"],
            ),
        ):
            raise _unavailable()

    def create(self, scope: Scope, body: dict[str, Any], *, idempotency_key: str, request_id: UUID) -> dict[str, Any]:
        if (
            type(idempotency_key) is not str
            or not 1 <= len(idempotency_key) <= 128
            or type(request_id) is not UUID
            or request_id.int == 0
        ):
            raise BusinessError("INPUT_INVALID", 422)
        context = self._context(scope, body)
        if self.settings.control_ttl_seconds is None:
            raise BusinessError("CONTROL_RECEIPT_TTL_UNCONFIRMED", 503)
        if type(self.settings.control_ttl_seconds) is not int or self.settings.control_ttl_seconds <= 0:
            raise _unavailable()
        try:
            with self.database.transaction(scope) as connection:
                self._root(connection, scope, context)
                root = current_scope_transaction()
                if root is None:
                    raise _scope_invalid()
                check: Callable[[], None] | None = None
                try:
                    # Registration failure must roll back too, even if an outer
                    # caller catches it and then commits its root transaction.
                    with connection.begin_nested():
                        with connection.begin_nested():
                            # An unlocked, failure-only check preserves an
                            # already known different-A conflict. It cannot
                            # yield acceptance or replace the advisory-locked
                            # authoritative check after the material locks.
                            known = (
                                connection.execute(
                                    text(
                                        "SELECT request_sha256,expires_at FROM mt.idempotency_record "
                                        "WHERE case_id=:case AND actor_id=:actor AND operation='createTask' "
                                        "AND idempotency_key=:key"
                                    ),
                                    dict(case=scope.case_id, actor=scope.actor.user_id, key=idempotency_key),
                                )
                                .mappings()
                                .one_or_none()
                            )
                            if known is not None and (
                                known["request_sha256"] != context.request.request_sha256
                                or known["expires_at"] <= datetime.now(timezone.utc)
                            ):
                                raise _conflict()
                            execution = self._read(connection, context)
                            self._root(connection, scope, context)
                            self._asset(connection, scope, context, execution)
                            replay = self.receipts.replay(
                                connection, scope, "createTask", idempotency_key, context.request.request_sha256
                            )
                            # Advisory waiting may cross a Proof, identity or
                            # source deadline. Revalidate before any new row;
                            # these same asset/source locks are already held.
                            # object_version remains an immutable SELECT-only
                            # observation, never an UPDATE privilege request.
                            self._root(connection, scope, context)
                            execution = _execution_copy(context, execution, self.budgets, _time(self.clock))
                            self._asset(connection, scope, context, execution)
                            if replay is None:
                                receipt = self._write(
                                    connection, scope, context, execution, request_id, idempotency_key
                                )
                                self.receipts.remember(
                                    connection,
                                    scope,
                                    "createTask",
                                    idempotency_key,
                                    context.request.request_sha256,
                                    receipt,
                                )
                            else:
                                receipt = self._validate_receipt(
                                    connection,
                                    scope,
                                    context,
                                    execution,
                                    replay,
                                    idempotency_key=idempotency_key,
                                    initial=False,
                                )
                            # Freeze through canonical bytes; the caller only
                            # receives a separate Accepted object, not this data.
                            receipt_raw = canonical(receipt)
                            result: dict[str, Any] = json.loads(canonical(receipt["accepted"]))
                            validate_response("Accepted", result)

                        def final_check() -> None:
                            try:
                                live = self._context(scope, json.loads(context.request.canonical_body))
                                if live != context:
                                    raise BusinessError("AUTHORIZATION_CHANGED", 503)
                                self._root(connection, scope, live)
                                after = self._read(connection, live)
                                recheck_execution_materials(
                                    context, execution, after, budgets=self.budgets, clock=self.clock
                                )
                                self._asset(connection, scope, live, after)
                                stored = self.receipts.replay(
                                    connection, scope, "createTask", idempotency_key, context.request.request_sha256
                                )
                                if stored is None or canonical(stored) != receipt_raw:
                                    raise BusinessError("AUTHORIZATION_CHANGED", 503)
                                self._validate_receipt(
                                    connection,
                                    scope,
                                    live,
                                    after,
                                    stored,
                                    idempotency_key=idempotency_key,
                                    initial=replay is None,
                                )
                                # Sample once more after persisted collection checks.
                                recheck_execution_materials(
                                    context, execution, after, budgets=self.budgets, clock=self.clock
                                )
                            except SQLAlchemyError:
                                raise BusinessError("DATABASE_UNAVAILABLE", 503) from None
                            except BusinessError as error:
                                if error.code == "DATABASE_UNAVAILABLE":
                                    raise
                                raise BusinessError("AUTHORIZATION_CHANGED", 503) from None
                            except Exception:
                                raise BusinessError("AUTHORIZATION_CHANGED", 503) from None

                        check = final_check
                        self.database.before_commit(connection, check)
                except BaseException:
                    if check is not None:
                        root.commit_checks[:] = [item for item in root.commit_checks if item is not check]
                    raise
                # No fallible response work remains outside the savepoints.
                # Database still completes its root checks/fence/commit before
                # an owned transaction can leave this context manager.
                return result
        except SQLAlchemyError:
            raise BusinessError("DATABASE_UNAVAILABLE", 503) from None

    def _write(
        self,
        connection: Connection,
        scope: Scope,
        context: TaskCreationContext,
        execution: ExecutionMaterials,
        request_id: UUID,
        idempotency_key: str,
    ) -> dict[str, Any]:
        task_id, task_run_id, event_id, audit_id = uuid4(), uuid4(), uuid4(), uuid4()
        request, bundle = context.request, execution.materials
        observed = _time(self.clock)
        plan = _plan_values(context, execution, task_id, observed)
        # No mutation occurs until both public response and event are valid.
        _accepted(task_id)
        payload = _event(scope, execution, task_id, event_id, request_id, observed)
        params = dict(
            task=task_id,
            run_id=task_run_id,
            org=scope.actor.org_id,
            case=scope.case_id,
            actor=scope.actor.user_id,
            asset=request.asset_id,
            scene=request.scene,
            priority=request.priority,
            policy=request.policy_version,
            modules=list(request.modules),
            input=bundle.inputs.sha256,
            dag=bundle.plan.version,
        )
        connection.execute(
            text(
                "INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,progress,run_version,"
                "result_version,policy_version,modules,missing_modalities,report_eligibility,created_by) "
                "VALUES(:task,:org,:case,:asset,:scene,:priority,'CREATED',0,1,1,:policy,:modules,'{}','draft_only',:actor)"
            ),
            params,
        )
        connection.execute(
            text(
                "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,"
                "policy_version,fencing_epoch,created_by) VALUES(:run_id,:org,:case,:task,1,:input,:dag,:policy,1,:actor)"
            ),
            params,
        )
        fields = tuple(name for name in _PLAN_FIELDS if name != "created_at")
        connection.execute(
            text(
                "INSERT INTO mt.task_run_plan("
                + ",".join(fields)
                + ") VALUES("
                + ",".join(":" + name for name in fields)
                + ")"
            ),
            plan,
        )
        definitions = {item["node_code"]: item for item in bundle.plan.as_dict()["nodes"]}
        for snapshot in bundle.node_inputs:
            definition = definitions[snapshot.document_id]
            connection.execute(
                text(
                    "INSERT INTO mt.task_node_run(run_id,org_id,case_id,task_id,run_version,node_code,attempt,input_hash,"
                    "state,required,fencing_epoch,created_by) VALUES(:id,:org,:case,:task,1,:node,1,:hash,:state,:required,1,:actor)"
                ),
                dict(
                    params,
                    id=uuid4(),
                    node=snapshot.document_id,
                    hash=snapshot.sha256,
                    state="PENDING" if definition["dependencies"] else "READY",
                    required=definition["required"],
                ),
            )
        result = connection.execute(
            text(
                "UPDATE mt.analysis_task SET state='QUEUED',row_version=row_version+1,updated_at=now() "
                "WHERE task_id=:task AND org_id=:org AND case_id=:case AND state='CREATED' AND row_version=1"
            ),
            params,
        )
        if result.rowcount != 1:
            raise _unavailable()
        connection.execute(
            text(
                "INSERT INTO mt.task_event(event_id,org_id,case_id,task_id,run_version,from_state,to_state,reason,request_id,created_by) "
                "VALUES(:id,:org,:case,:task,1,'CREATED','QUEUED',:reason,:request,:actor)"
            ),
            dict(params, id=event_id, reason=_REASON, request=request_id),
        )
        connection.execute(
            text(
                "INSERT INTO mt.outbox_event(event_id,org_id,case_id,topic,aggregate_id,aggregate_version,payload,created_by) "
                "VALUES(:id,:org,:case,:topic,:task,2,CAST(:payload AS jsonb),:actor)"
            ),
            dict(params, id=event_id, topic=_EVENT_TYPE, payload=json.dumps(payload)),
        )
        connection.execute(
            text(
                "INSERT INTO mt.audit_event(event_id,org_id,case_id,actor_id,action,object_type,object_id,object_version,"
                "outcome,request_id,occurred_at,details,created_by) "
                "VALUES(:id,:org,:case,:actor,'createTask','task',:task,2,'allowed',:request,:at,CAST(:details AS jsonb),:actor)"
            ),
            dict(
                params,
                id=audit_id,
                request=request_id,
                at=observed,
                details=json.dumps(
                    dict(
                        run_version=1,
                        revision_id=str(execution.binding.revision_id),
                        request_sha256=request.request_sha256,
                        authorization_request_digest=context.authorization_request_digest,
                    )
                ),
            ),
        )
        seed = dict(
            task_id=str(task_id),
            task_run_id=str(task_run_id),
            event_id=str(event_id),
            audit_event_id=str(audit_id),
            request_id=str(request_id),
        )
        return self._collection_receipt(
            connection, scope, context, execution, seed, idempotency_key=idempotency_key, initial=True
        )

    def _validate_receipt(
        self,
        connection: Connection,
        scope: Scope,
        context: TaskCreationContext,
        execution: ExecutionMaterials,
        receipt: dict[str, Any],
        *,
        idempotency_key: str,
        initial: bool,
    ) -> dict[str, Any]:
        try:
            if type(receipt) is not dict or set(receipt) != _RECEIPT_FIELDS:
                raise _conflict()
            expected = self._collection_receipt(
                connection, scope, context, execution, receipt, idempotency_key=idempotency_key, initial=initial
            )
            if not _same(receipt, expected):
                raise _conflict()
            return expected
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise _conflict() from None

    def _collection_receipt(
        self,
        connection: Connection,
        scope: Scope,
        context: TaskCreationContext,
        execution: ExecutionMaterials,
        seed: dict[str, Any],
        *,
        idempotency_key: str,
        initial: bool,
    ) -> dict[str, Any]:
        ids = {
            name: _identifier(seed[name])
            for name in ("task_id", "task_run_id", "event_id", "audit_event_id", "request_id")
        }
        task_id, bundle = ids["task_id"], execution.materials
        params = dict(org=scope.actor.org_id, case=scope.case_id, task=task_id)
        if initial:
            # This task was allocated in this transaction, so extra runs,
            # attempts, synthetic results or duplicate acceptance intents are
            # corruption. Replays intentionally do not impose these counts on
            # a task that may since have legitimately progressed.
            counts = (
                connection.execute(
                    text(
                        "SELECT "
                        "(SELECT count(*) FROM mt.task_run WHERE org_id=:org AND case_id=:case AND task_id=:task) AS runs,"
                        "(SELECT count(*) FROM mt.task_run_plan WHERE org_id=:org AND case_id=:case AND task_id=:task) AS plans,"
                        "(SELECT count(*) FROM mt.task_node_run WHERE org_id=:org AND case_id=:case AND task_id=:task) AS nodes,"
                        "(SELECT count(*) FROM mt.task_result WHERE org_id=:org AND case_id=:case AND task_id=:task) AS results,"
                        "(SELECT count(*) FROM mt.task_event WHERE org_id=:org AND case_id=:case AND task_id=:task) AS events,"
                        "(SELECT count(*) FROM mt.outbox_event WHERE org_id=:org AND case_id=:case AND aggregate_id=:task) AS outbox,"
                        "(SELECT count(*) FROM mt.audit_event WHERE org_id=:org AND case_id=:case AND object_id=:task) AS audits"
                    ),
                    params,
                )
                .mappings()
                .one()
            )
            if dict(counts) != dict(
                runs=1, plans=1, nodes=len(bundle.node_inputs), results=0, events=1, outbox=1, audits=1
            ):
                raise _conflict()

        def one(table: str, where: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
            # Tables/predicates are server constants, never receipt/body text.
            value = (
                connection.execute(
                    text("SELECT * FROM mt." + table + " WHERE org_id=:org AND case_id=:case AND " + where),
                    dict(params, **(extra or {})),
                )
                .mappings()
                .one_or_none()
            )
            if value is None:
                raise _conflict()
            return dict(value)

        task = one("analysis_task", "task_id=:task")
        run = one("task_run", "task_id=:task AND run_version=1")
        saved = one("task_run_plan", "task_id=:task AND run_version=1")
        request = context.request
        for row in (task, run, saved):
            if row["created_by"] != scope.actor.user_id:
                raise _conflict()
        if (
            not _same(
                {name: task[name] for name in ("asset_id", "scene", "priority", "policy_version", "modules")},
                dict(
                    asset_id=request.asset_id,
                    scene=request.scene,
                    priority=request.priority,
                    policy_version=request.policy_version,
                    modules=list(request.modules),
                ),
            )
            or type(task["row_version"]) is not int
            or task["row_version"] < 2
            or (
                initial
                and not _same(
                    {
                        name: task[name]
                        for name in (
                            "state",
                            "progress",
                            "run_version",
                            "result_version",
                            "row_version",
                            "report_eligibility",
                            "missing_modalities",
                        )
                    },
                    dict(
                        state="QUEUED",
                        progress=0.0,
                        run_version=1,
                        result_version=1,
                        row_version=2,
                        report_eligibility="draft_only",
                        missing_modalities=[],
                    ),
                )
            )
        ):
            raise _conflict()
        if not _same(
            {name: run[name] for name in ("task_run_id", "input_sha256", "dag_version", "policy_version")},
            dict(
                task_run_id=ids["task_run_id"],
                input_sha256=bundle.inputs.sha256,
                dag_version=bundle.plan.version,
                policy_version=execution.binding.policy_version,
            ),
        ):
            raise _conflict()
        if set(saved) != set(_PLAN_FIELDS):
            raise _conflict()
        expected_plan = _plan_values(context, execution, task_id, saved["proof_observed_at"])
        historical = {"created_at", "proof_valid_until"}
        if not _same(
            {key: value for key, value in saved.items() if key not in historical},
            {key: value for key, value in expected_plan.items() if key not in historical},
        ):
            raise _conflict()
        if (
            not all(
                _aware(saved[key])
                for key in (
                    "created_at",
                    "proof_observed_at",
                    "proof_valid_until",
                    "mapping_valid_from",
                    "mapping_valid_until",
                )
            )
            or not saved["mapping_valid_from"]
            <= saved["proof_observed_at"]
            < saved["proof_valid_until"]
            <= saved["mapping_valid_until"]
        ):
            raise _conflict()
        node_rows = (
            connection.execute(
                text(
                    "SELECT * FROM mt.task_node_run WHERE org_id=:org AND case_id=:case AND task_id=:task "
                    "AND run_version=1 AND attempt=1"
                ),
                params,
            )
            .mappings()
            .all()
        )
        definitions = {item["node_code"]: item for item in bundle.plan.as_dict()["nodes"]}
        if len(node_rows) != len(bundle.node_inputs):
            raise _conflict()
        by_code = {item["node_code"]: item for item in node_rows}
        nodes = []
        for snapshot in bundle.node_inputs:
            definition = definitions[snapshot.document_id]
            node_row = by_code.get(snapshot.document_id)
            state = "PENDING" if definition["dependencies"] else "READY"
            if node_row is None or not _same(
                {name: node_row[name] for name in ("input_hash", "required", "created_by", "model_version")},
                dict(
                    input_hash=snapshot.sha256,
                    required=definition["required"],
                    created_by=scope.actor.user_id,
                    model_version=None,
                ),
            ):
                raise _conflict()
            if initial and (
                node_row["state"] != state
                or node_row["row_version"] != 1
                or node_row["fencing_epoch"] != 1
                or any(node_row[name] is not None for name in ("reason", "lease_token", "started_at", "ended_at"))
            ):
                raise _conflict()
            nodes.append(
                dict(
                    run_id=str(node_row["run_id"]),
                    node_code=snapshot.document_id,
                    attempt=1,
                    input_hash=snapshot.sha256,
                    required=definition["required"],
                    initial_state=state,
                    snapshot=snapshot.as_dict(),
                )
            )
        event_row = one("task_event", "event_id=:id AND task_id=:task", dict(id=ids["event_id"]))
        outbox = one("outbox_event", "event_id=:id AND aggregate_id=:task", dict(id=ids["event_id"]))
        audit = one("audit_event", "event_id=:id AND object_id=:task", dict(id=ids["audit_event_id"]))
        if not _same(
            {
                name: event_row[name]
                for name in ("run_version", "from_state", "to_state", "reason", "request_id", "created_by")
            },
            dict(
                run_version=1,
                from_state="CREATED",
                to_state="QUEUED",
                reason=_REASON,
                request_id=ids["request_id"],
                created_by=scope.actor.user_id,
            ),
        ):
            raise _conflict()
        try:
            event_time = datetime.fromisoformat(outbox["payload"]["occurred_at"])
            if not _aware(event_time):
                raise ValueError()
        except (TypeError, ValueError, KeyError):
            raise _conflict() from None
        expected_event = _event(scope, execution, task_id, ids["event_id"], ids["request_id"], event_time)
        if (
            outbox["topic"] != _EVENT_TYPE
            or outbox["aggregate_version"] != 2
            or outbox["created_by"] != scope.actor.user_id
            or not _same(outbox["payload"], expected_event)
            or (initial and (outbox["published_at"] is not None or outbox["attempts"] != 0))
        ):
            raise _conflict()
        expected_audit = dict(
            actor_id=scope.actor.user_id,
            action="createTask",
            object_type="task",
            object_version=2,
            outcome="allowed",
            request_id=ids["request_id"],
            created_by=scope.actor.user_id,
            details=dict(
                run_version=1,
                revision_id=str(execution.binding.revision_id),
                request_sha256=request.request_sha256,
                authorization_request_digest=context.authorization_request_digest,
            ),
        )
        if not _same({name: audit[name] for name in expected_audit}, expected_audit):
            raise _conflict()
        accepted = _accepted(task_id)
        return dict(
            schema_version=_RECEIPT_VERSION,
            idempotency_key=idempotency_key,
            accepted=accepted,
            etag=etag(accepted),
            actor_id=str(scope.actor.user_id),
            org_id=str(scope.actor.org_id),
            case_id=str(scope.case_id),
            **{name: str(value) for name, value in ids.items()},
            request_sha256=request.request_sha256,
            authorization_request_digest=context.authorization_request_digest,
            binding=_binding(execution),
            run_plan_sha256=hashlib.sha256(canonical(_json_value(saved))).hexdigest(),
            accepted_projection=dict(
                state="QUEUED",
                row_version=2,
                run_version=1,
                result_version=1,
                progress=0,
                report_eligibility="draft_only",
                missing_modalities=[],
            ),
            nodes=nodes,
        )
