"""Fixed limited SQL observations, never adoption, a Proof issuer or execution.

The immutable pure binding module remains independent of database access. This
explicit reader only returns limited metadata or verifies CASE material bytes
against an already supplied PlanBinding. Receipt projection/ACTIVE/declared
references do not establish formal adoption, current licence or availability.
"""

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Connection, text

from .errors import BusinessError
from .permissions.task_creation_context import TaskCreationContext, _context_copy, current_task_creation_context
from .task_creation import TaskCreateRequest, _copy_request
from .task_creation_authority import (
    ExecutionMaterials,
    PlanBinding,
    _binding_copy,
    _changed,
    _final_fresh,
    _now,
    _opaque,
    _reference,
    _time,
    _unavailable,
    _utc,
    freeze_execution_materials,
)
from .task_creation_materials import (
    CAPABILITY_SCHEMA_ID,
    MaterialBudgets,
    _canonical,
    _limits,
    _load,
    parse_capability_manifest,
)

if TYPE_CHECKING:
    from .db import Database


@dataclass(frozen=True)
class TaskPlanMetadataObservation:
    """All 21 limited SQL columns, not a Proof or an adoption decision.

    The receipt field is a limited projection. Its canonical JSON here must
    never be substituted for the original receipt bytes returned only in CASE.
    """

    request: TaskCreateRequest
    authorization_request_digest: str
    canonical_bytes: bytes
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_bytes)
        if type(value) is not dict:
            raise _unavailable()
        return value


_METADATA_COLUMNS = frozenset(
    {
        "revision_id",
        "mapping_id",
        "mapping_version",
        "authority_version",
        "head_row_version",
        "policy_id",
        "policy_kind",
        "policy_version",
        "policy_sha256",
        "plan_id",
        "plan_version",
        "plan_sha256",
        "capability_id",
        "capability_version",
        "capability_sha256",
        "valid_from",
        "valid_until",
        "recovery_generation",
        "validation_receipt",
        "required_capability_refs",
        "current_state_facts",
    }
)
_EXECUTION_COLUMNS = frozenset(
    {
        "revision_id",
        "head_row_version",
        "policy_bytes",
        "plan_bytes",
        "capability_bytes",
        "validation_receipt_bytes",
        "current_state_facts",
        "valid_until",
        "recovery_generation",
    }
)


def _closed(value: Any, fields: set[str] | frozenset[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise _unavailable()
    return value


def _positive(value: Any, *, zero: bool = False) -> None:
    if type(value) is not int or value < (0 if zero else 1):
        raise _unavailable()


def _identifier(value: Any) -> UUID:
    if type(value) is not str:
        raise _unavailable()
    result = UUID(value)
    if result.int == 0 or str(result) != value:
        raise _unavailable()
    return result


def _hash(value: Any) -> None:
    if type(value) is not str or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise _unavailable()


def _sql_timestamp(value: Any) -> datetime:
    # PG16 JSON can use 1..6 fractional digits. Python3.10's fromisoformat
    # accepts only selected fractional lengths, so use the existing strptime
    # compatibility approach without truncation, rounding or a naive fallback.
    if type(value) is not str or re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z", value) is None:
        raise _unavailable()
    pattern = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in value else "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(value, pattern).replace(tzinfo=timezone.utc)


def _stamp(value: datetime) -> str:
    return _utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _fact_text(value: Any, budgets: MaterialBudgets) -> None:
    if type(value) is not str or not value or len(value.encode("utf8")) > budgets.max_bytes:
        raise _unavailable()


def _limited_facts(value: Any, context: TaskCreationContext, row: dict[str, Any], budgets: MaterialBudgets) -> bytes:
    from .contracts import validate_api

    facts = _closed(
        value, {"asset", "source", "policy", "case", "memberships", "actor", "organization", "head", "generation"}
    )
    raw = _canonical(facts)
    _load(raw, budgets)
    asset = _closed(
        facts["asset"],
        {
            "asset_id",
            "org_id",
            "case_id",
            "content_id",
            "source_id",
            "kind",
            "object_ref",
            "mime",
            "size_bytes",
            "duration_ms",
            "width",
            "height",
            "state",
            "version",
            "created_at",
            "mapping_version",
            "sha256",
        },
    )
    validate_api(
        "Asset", {key: item for key, item in asset.items() if key not in {"org_id", "mapping_version", "sha256"}}
    )
    for key in ("asset_id", "org_id", "case_id", "content_id", "source_id"):
        _identifier(asset[key])
    _identifier(asset["object_ref"]["object_id"])
    _positive(asset["version"])
    _positive(asset["size_bytes"])
    for key in ("duration_ms", "width", "height"):
        if asset[key] is not None:
            _positive(asset[key], zero=key == "duration_ms")
    _hash(asset["sha256"])
    _sql_timestamp(asset["created_at"])
    _fact_text(asset["mapping_version"], budgets)
    request = context.request
    if (asset["asset_id"], asset["org_id"], asset["case_id"], asset["sha256"]) != (
        str(request.asset_id),
        str(request.actor.org_id),
        str(request.case_id),
        asset["object_ref"]["sha256"],
    ):
        raise _unavailable()
    source = _closed(
        facts["source"],
        {
            "source_id",
            "org_id",
            "case_id",
            "authorization_status",
            "authorization_version",
            "purpose",
            "expires_at",
            "row_version",
        },
    )
    if any(source[key] != asset[key] for key in ("source_id", "org_id", "case_id")) or source[
        "authorization_status"
    ] not in {"pending", "verified", "expired", "revoked"}:
        raise _unavailable()
    _fact_text(source["authorization_version"], budgets)
    _positive(source["row_version"])
    if (
        type(source["purpose"]) is not list
        or any(type(item) is not str or not item for item in source["purpose"])
        or len(set(source["purpose"])) != len(source["purpose"])
    ):
        raise _unavailable()
    if source["expires_at"] is not None:
        _sql_timestamp(source["expires_at"])
    policy = _closed(facts["policy"], {"policy_id", "kind", "version", "status", "row_version"})
    _positive(policy["row_version"])
    if (policy["policy_id"], policy["kind"], policy["version"]) != (
        row["policy_id"],
        row["policy_kind"],
        row["policy_version"],
    ) or policy["status"] not in {"DRAFT", "APPROVED"}:
        raise _unavailable()
    case = _closed(facts["case"], {"case_id", "status", "row_version"})
    _positive(case["row_version"])
    if case["case_id"] != str(request.case_id) or case["status"] not in {"ACTIVE", "ARCHIVED"}:
        raise _unavailable()
    memberships = facts["memberships"]
    # Existing UNIQUE(case_id,user_id), not a selected business quota.
    if type(memberships) is not list or len(memberships) != 1:
        raise _unavailable()
    for item in memberships:
        _closed(item, {"membership_id", "row_version", "expires_at"})
        _identifier(item["membership_id"])
        _positive(item["row_version"])
        if item["expires_at"] is not None:
            _sql_timestamp(item["expires_at"])
    actor = _closed(facts["actor"], {"user_id", "org_id", "enabled", "row_version"})
    org = _closed(facts["organization"], {"org_id", "enabled", "row_version"})
    if (actor["user_id"], actor["org_id"], org["org_id"]) != (
        str(request.actor.user_id),
        str(request.actor.org_id),
        str(request.actor.org_id),
    ):
        raise _unavailable()
    for item in (actor, org):
        if type(item["enabled"]) is not bool:
            raise _unavailable()
        _positive(item["row_version"])
    head = _closed(facts["head"], {"revision_id", "state", "row_version"})
    _positive(head["row_version"])
    if (head["revision_id"], head["row_version"], head["state"]) != (
        row["revision_id"],
        row["head_row_version"],
        "ACTIVE",
    ):
        raise _unavailable()
    generation = _closed(
        facts["generation"], {"database_oid", "epoch", "policy_version", "policy_sha256", "recovery_generation"}
    )
    _positive(generation["database_oid"])
    _positive(generation["epoch"])
    for key in ("policy_version", "recovery_generation"):
        if generation[key] is not None:
            _reference(generation[key])
    if generation["policy_sha256"] is not None:
        _hash(generation["policy_sha256"])
    # These database values do not replace the fence's independent GenerationReader.
    return memoryview(raw).tobytes()


def _metadata(
    context: TaskCreationContext, value: dict[str, Any], budgets: MaterialBudgets, now: datetime
) -> TaskPlanMetadataObservation:
    try:
        _limits(budgets)
        row = dict(value)
        _closed(row, _METADATA_COLUMNS)
        for key in ("revision_id", "policy_id"):
            if type(row[key]) is not UUID or row[key].int == 0:
                raise _unavailable()
            row[key] = str(row[key])
        for key in (
            "mapping_id",
            "mapping_version",
            "authority_version",
            "policy_kind",
            "policy_version",
            "plan_id",
            "plan_version",
            "capability_id",
            "capability_version",
            "recovery_generation",
        ):
            _reference(row[key])
        for key in ("policy_sha256", "plan_sha256", "capability_sha256"):
            _hash(row[key])
        _positive(row["head_row_version"])
        start, end = _utc(row["valid_from"]), _utc(row["valid_until"])
        if not start <= now < end or row["policy_version"] != context.request.policy_version:
            raise _unavailable()
        row["valid_from"], row["valid_until"] = _stamp(start), _stamp(end)
        receipt = _closed(
            row["validation_receipt"], {"sha256", "validator_id", "validator_version", "schema_id", "schema_version"}
        )
        _hash(receipt["sha256"])
        for key in ("validator_id", "validator_version", "schema_id", "schema_version"):
            if receipt[key] is not None:
                _reference(receipt[key])
        refs = _closed(
            row["required_capability_refs"], {"capability_id", "capability_version", "capability_sha256", "handlers"}
        )
        if any(refs[key] != row[key] for key in ("capability_id", "capability_version", "capability_sha256")):
            raise _unavailable()
        declared = parse_capability_manifest(
            _canonical(
                dict(
                    schema_id=CAPABILITY_SCHEMA_ID,
                    schema_version="1.0.0",
                    capability_id=refs["capability_id"],
                    capability_version=refs["capability_version"],
                    handlers=refs["handlers"],
                )
            ),
            budgets=budgets,
        )
        if declared.sha256 != row["capability_sha256"]:
            raise _unavailable()
        _limited_facts(row["current_state_facts"], context, row, budgets)
        raw = _canonical(row)
        _load(raw, budgets)
        return TaskPlanMetadataObservation(
            context.request, context.authorization_request_digest, raw, hashlib.sha256(raw).hexdigest()
        )
    except Exception:
        raise _unavailable() from None


def _metadata_copy(
    context: TaskCreationContext, value: TaskPlanMetadataObservation, budgets: MaterialBudgets, now: datetime
) -> TaskPlanMetadataObservation:
    """Rebuild even directly constructed or provider-mutated observations."""
    identity = _context_copy(context, lambda: now.timestamp())
    try:
        if (
            type(value) is not TaskPlanMetadataObservation
            or type(value.request) is not TaskCreateRequest
            or _copy_request(value.request) != identity.request
            or value.authorization_request_digest != identity.authorization_request_digest
        ):
            raise _unavailable()
        raw = _opaque(value.canonical_bytes, value.sha256, budgets)
        row = _load(raw, budgets)
        for key in ("revision_id", "policy_id"):
            row[key] = _identifier(row[key])
        for key in ("valid_from", "valid_until"):
            row[key] = _sql_timestamp(row[key])
        result = _metadata(identity, row, budgets, now)
        if result != value:
            raise _unavailable()
        return result
    except Exception:
        raise _unavailable() from None


class SqlTaskPlanAuthority:
    """Fixed limited SQL observations; never a default TaskPlanProof issuer."""

    def __init__(self, database: "Database", *, budgets: MaterialBudgets, clock: Callable[[], datetime] = _now) -> None:
        _limits(budgets)
        self.database, self.budgets, self.clock = database, budgets, clock

    def _context(self, context: TaskCreationContext, connection: Connection, now: datetime) -> TaskCreationContext:
        from .data_scope import AccessMode, LookupKey
        from .permissions.context import current_authorization
        from .permissions.rule_types import AuthorizationEvidence
        from .scope_collections import require_root
        from .scope_context import current_data_scope, current_scope_transaction

        identity = _context_copy(context, lambda: now.timestamp())
        current = current_task_creation_context(clock=lambda: now.timestamp())
        root, scope = current_scope_transaction(), current_data_scope()
        if (
            current is None
            or current != identity
            or root is None
            or root.connection is not connection
            or root.database is not self.database
            or scope is None
            or scope.actor != identity.principal.actor
            or scope.operation_id != "createTask"
            or not connection.in_transaction()
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        request = identity.request
        if scope.mode is AccessMode.LOOKUP:
            if (
                root.scope != scope
                or root.authorization is not None
                or current_authorization() is not None
                or scope.lookup != LookupKey("asset", request.asset_id)
                or scope.case_id is not None
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            try:
                read_only = connection.execute(text("SELECT current_setting('transaction_read_only')")).scalar_one()
            except Exception:
                raise _unavailable() from None
            if read_only != "on":
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        else:
            authorization = require_root(connection, scope)
            evidence = authorization.evidence
            if (
                scope.mode is not AccessMode.CASE
                or scope.case_id != request.case_id
                or scope.task_binding is not None
                or not authorization.mutation
                or not isinstance(evidence, AuthorizationEvidence)
                or evidence.principal != identity.principal
                or evidence.operation_id != "createTask"
                or (
                    evidence.target.org_id,
                    evidence.target.kind,
                    evidence.target.object_id,
                    evidence.target.case_id,
                    evidence.target.purpose,
                    evidence.target.request_digest,
                )
                != (
                    request.actor.org_id,
                    "asset",
                    request.asset_id,
                    request.case_id,
                    "analysis",
                    identity.authorization_request_digest,
                )
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        return identity

    @staticmethod
    def _parameters(context: TaskCreationContext) -> dict[str, Any]:
        request = context.request
        return dict(
            asset=request.asset_id,
            case=request.case_id,
            scene=request.scene,
            policy=request.policy_version,
            modules=list(request.modules),
            priority=request.priority,
        )

    def read_metadata(self, context: TaskCreationContext, *, connection: Connection) -> TaskPlanMetadataObservation:
        now = _time(self.clock)
        identity = self._context(context, connection, now)
        try:
            rows = (
                connection.execute(
                    text("SELECT * FROM mt.task_create_plan_metadata(:asset,:case,:scene,:policy,:modules,:priority)"),
                    self._parameters(identity),
                )
                .mappings()
                .fetchmany(2)
            )
            if len(rows) != 1:
                raise _unavailable()
            result = _metadata(identity, dict(rows[0]), self.budgets, now)
        except Exception:
            raise _unavailable() from None
        final = _time(self.clock)
        self._context(identity, connection, final)
        if _sql_timestamp(result.as_dict()["valid_until"]) <= final:
            raise _changed()
        return result

    def read_execution(
        self, context: TaskCreationContext, expected: PlanBinding, input_raw: bytes, *, connection: Connection
    ) -> ExecutionMaterials:
        from .data_scope import AccessMode
        from .scope_context import current_data_scope

        now = _time(self.clock)
        identity = self._context(context, connection, now)
        scope = current_data_scope()
        if scope is None or scope.mode is not AccessMode.CASE:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        binding = _binding_copy(identity, expected, self.budgets, now)
        observation = _metadata_copy(identity, self.read_metadata(identity, connection=connection), self.budgets, now)
        row = observation.as_dict()
        proof = binding.proof
        wanted = dict(
            revision_id=str(binding.revision_id),
            mapping_id=binding.mapping_id,
            mapping_version=binding.mapping_version,
            authority_version=proof.authority_version,
            head_row_version=binding.head_row_version,
            policy_id=str(binding.policy_id),
            policy_kind=binding.policy_kind,
            policy_version=binding.policy_version,
            policy_sha256=proof.policy_sha256,
            plan_id=proof.plan_id,
            plan_version=proof.plan_version,
            plan_sha256=proof.plan_sha256,
            capability_id=proof.capability_id,
            capability_version=proof.capability_version,
            capability_sha256=proof.capability_sha256,
            valid_from=_stamp(binding.mapping_valid_from),
            valid_until=_stamp(binding.mapping_valid_until),
            recovery_generation=binding.recovery_generation,
        )
        if (
            any(row[key] != value for key, value in wanted.items())
            or row["validation_receipt"]["sha256"] != binding.validation_receipt_sha256
            or _canonical(row["current_state_facts"]) != binding.current_state_facts_bytes
        ):
            raise _changed()
        params = dict(
            self._parameters(identity),
            revision=binding.revision_id,
            policy_sha=proof.policy_sha256,
            plan_sha=proof.plan_sha256,
            capability_sha=proof.capability_sha256,
        )
        try:
            rows = (
                connection.execute(
                    text(
                        "SELECT * FROM mt.task_create_execution_plan(:asset,:case,:scene,:policy,:modules,:priority,:revision,:policy_sha,:plan_sha,:capability_sha)"
                    ),
                    params,
                )
                .mappings()
                .fetchmany(2)
            )
            if len(rows) != 1:
                raise _unavailable()
            execution = dict(rows[0])
            _closed(execution, _EXECUTION_COLUMNS)
            if (
                execution["revision_id"] != binding.revision_id
                or execution["head_row_version"] != binding.head_row_version
                or _stamp(execution["valid_until"]) != row["valid_until"]
                or execution["recovery_generation"] != binding.recovery_generation
                or _canonical(execution["current_state_facts"]) != binding.current_state_facts_bytes
            ):
                raise _changed()
            raw = []
            for key in ("policy_bytes", "plan_bytes", "capability_bytes", "validation_receipt_bytes"):
                item = execution[key]
                if (
                    type(item) not in (bytes, memoryview)
                    or (item.nbytes if type(item) is memoryview else len(item)) > self.budgets.max_bytes
                ):
                    raise _unavailable()
                raw.append(bytes(item))
            if (
                raw[3] != binding.validation_receipt_bytes
                or hashlib.sha256(raw[3]).hexdigest() != binding.validation_receipt_sha256
            ):
                raise _changed()
            receipt = _load(raw[3], self.budgets)
            for key in ("validator_id", "validator_version", "schema_id", "schema_version"):
                projected = receipt.get(key)
                if type(projected) is not str or not 1 <= len(projected) <= 128:
                    projected = None
                if row["validation_receipt"][key] != projected:
                    raise _changed()
            result = freeze_execution_materials(
                identity, binding, raw[0], raw[1], raw[2], input_raw, budgets=self.budgets, clock=self.clock
            )
            inputs = result.materials.inputs.as_dict()["asset"]
            actual, source = row["current_state_facts"]["asset"], row["current_state_facts"]["source"]
            if (
                inputs["sha256"] != actual["sha256"]
                or inputs["object_ref"] != actual["object_ref"]
                or inputs["source_authorization_version"] != source["authorization_version"]
            ):
                raise _changed()
        except BusinessError:
            raise
        except Exception:
            raise _unavailable() from None
        final = _time(self.clock)
        self._context(identity, connection, final)
        _final_fresh(identity, binding, result.binding, final)
        return result
