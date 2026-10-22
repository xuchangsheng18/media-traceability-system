"""Pure full plan/material observations, never adoption, permission or execution.

No provider, database, handler import or network lookup exists here. Callers must
obtain both observations from the future authoritative, fenced transaction.
Receipt and current-fact documents have no approved semantic Schema/provider in
this tranche: they are only explicit, bounded canonical JSON objects and hashes.
Their contents (including any ``validated`` flag) cannot establish adoption,
licence, current handler availability or source authority. A structurally valid
Proof or self-owned fixture cannot establish those facts either.
"""

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID

from .errors import BusinessError
from .permissions.task_creation_context import TaskCreationContext, _context_copy
from .task_creation import TaskPlanProof, _aware, _copy_proof, _time
from .task_creation_materials import (
    CanonicalMaterial,
    MaterialBudgets,
    MaterialBundle,
    _canonical,
    _limits,
    _load,
    prepare_material_bundle,
)


@dataclass(frozen=True)
class PlanBinding:
    proof: TaskPlanProof
    authorization_request_digest: str
    revision_id: UUID
    head_row_version: int
    mapping_id: str
    mapping_version: str
    policy_id: UUID
    policy_kind: str
    policy_version: str
    mapping_valid_from: datetime
    mapping_valid_until: datetime
    validation_receipt_bytes: bytes
    validation_receipt_sha256: str
    recovery_generation: str
    current_state_facts_bytes: bytes
    current_state_facts_sha256: str


@dataclass(frozen=True)
class ExecutionMaterials:
    binding: PlanBinding
    materials: MaterialBundle


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _unavailable() -> BusinessError:
    return BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)


def _changed() -> BusinessError:
    return BusinessError("AUTHORIZATION_CHANGED", 503)


def _reference(value: str) -> str:
    if type(value) is not str or not 1 <= len(value) <= 128:
        raise _unavailable()
    value.encode("utf8")
    return value


def _utc(value: datetime) -> datetime:
    if not _aware(value):
        raise _unavailable()
    return value.astimezone(timezone.utc)


def _opaque(raw: bytes, digest: str, budgets: MaterialBudgets) -> bytes:
    # I01's strict loader rejects duplicate keys, nonfinite values, invalid UTF-8
    # and non-object documents. Exact byte equality prevents silent rewriting.
    if (
        type(digest) is not str
        or re.fullmatch(r"[a-f0-9]{64}", digest) is None
        or _canonical(_load(raw, budgets)) != raw
        or hashlib.sha256(raw).hexdigest() != digest
    ):
        raise _unavailable()
    return memoryview(raw).tobytes()


def freeze_plan_binding(
    context: TaskCreationContext,
    proof: TaskPlanProof,
    *,
    revision_id: UUID,
    head_row_version: int,
    mapping_id: str,
    mapping_version: str,
    policy_id: UUID,
    policy_kind: str,
    policy_version: str,
    mapping_valid_from: datetime,
    mapping_valid_until: datetime,
    validation_receipt_bytes: bytes,
    validation_receipt_sha256: str,
    recovery_generation: str,
    current_state_facts_bytes: bytes,
    current_state_facts_sha256: str,
    budgets: MaterialBudgets,
    clock: Callable[[], datetime] = _now,
) -> PlanBinding:
    """Freeze supplied observations, without authenticating their provenance."""
    current = _time(clock)
    # Preserve the established identity/expiry mapping, including expired 401.
    identity = _context_copy(context, lambda: current.timestamp())
    copied = _copy_proof(proof, identity.request, current)
    # The old Proof boundary reconstructs the request; replace it with this
    # detached context copy so even provider-owned UUID objects are not shared.
    copied = replace(copied, request=identity.request)
    try:
        _limits(budgets)
        if (
            any(type(value) is not UUID or value.int == 0 for value in (revision_id, policy_id))
            or type(head_row_version) is not int
            or head_row_version <= 0
            or policy_version != identity.request.policy_version
        ):
            raise _unavailable()
        references = tuple(
            _reference(value)
            for value in (mapping_id, mapping_version, policy_kind, policy_version, recovery_generation)
        )
        start, end = _utc(mapping_valid_from), _utc(mapping_valid_until)
        if (
            not start <= current < end
            or copied.valid_until > end
            or copied.valid_until.timestamp() > identity.principal.expires_at
        ):
            raise _unavailable()
        receipt = _opaque(validation_receipt_bytes, validation_receipt_sha256, budgets)
        facts = _opaque(current_state_facts_bytes, current_state_facts_sha256, budgets)
        return PlanBinding(
            copied,
            identity.authorization_request_digest,
            UUID(int=revision_id.int),
            head_row_version,
            references[0],
            references[1],
            UUID(int=policy_id.int),
            references[2],
            references[3],
            start,
            end,
            receipt,
            validation_receipt_sha256,
            references[4],
            facts,
            current_state_facts_sha256,
        )
    except Exception:
        raise _unavailable() from None


def _binding_copy(
    context: TaskCreationContext, value: PlanBinding, budgets: MaterialBudgets, current: datetime
) -> PlanBinding:
    try:
        if type(value) is not PlanBinding:
            raise _unavailable()
        snapshot = freeze_plan_binding(
            context,
            value.proof,
            revision_id=value.revision_id,
            head_row_version=value.head_row_version,
            mapping_id=value.mapping_id,
            mapping_version=value.mapping_version,
            policy_id=value.policy_id,
            policy_kind=value.policy_kind,
            policy_version=value.policy_version,
            mapping_valid_from=value.mapping_valid_from,
            mapping_valid_until=value.mapping_valid_until,
            validation_receipt_bytes=value.validation_receipt_bytes,
            validation_receipt_sha256=value.validation_receipt_sha256,
            recovery_generation=value.recovery_generation,
            current_state_facts_bytes=value.current_state_facts_bytes,
            current_state_facts_sha256=value.current_state_facts_sha256,
            budgets=budgets,
            clock=lambda: current,
        )
    except BusinessError:
        raise
    except Exception:
        raise _unavailable() from None
    try:
        if value != snapshot:
            raise _unavailable()
    except Exception:
        raise _unavailable() from None
    return snapshot


def recheck_plan_binding(
    context: TaskCreationContext,
    expected: PlanBinding,
    current: PlanBinding,
    *,
    budgets: MaterialBudgets,
    clock: Callable[[], datetime] = _now,
) -> PlanBinding:
    """Compare complete supplied observations; this does not read a provider."""
    now = _time(clock)
    before = _binding_copy(context, expected, budgets, now)
    after = _binding_copy(context, current, budgets, now)
    # Only extending the proof's deadline is permitted. Revision/head, mapping,
    # policy, receipt, recovery and stable current-fact fingerprint stay exact.
    if (
        after.proof.valid_until < before.proof.valid_until
        or replace(after, proof=replace(after.proof, valid_until=before.proof.valid_until)) != before
    ):
        raise _changed()
    _final_fresh(context, before, after, _time(clock))
    return after


def _final_fresh(context: TaskCreationContext, before: PlanBinding, after: PlanBinding, now: datetime) -> None:
    # Sampling again after comparisons prevents a slow parser/provider-supplied
    # clock from carrying a formerly fresh proof across its original deadline.
    identity = _context_copy(context, lambda: now.timestamp())
    for binding in (before, after):
        if (
            binding.proof.valid_until <= now
            or not binding.mapping_valid_from <= now < binding.mapping_valid_until
            or binding.proof.request != identity.request
            or binding.authorization_request_digest != identity.authorization_request_digest
        ):
            raise _changed()


def freeze_execution_materials(
    context: TaskCreationContext,
    binding: PlanBinding,
    policy_raw: bytes,
    plan_raw: bytes,
    capability_raw: bytes,
    input_raw: bytes,
    *,
    budgets: MaterialBudgets,
    clock: Callable[[], datetime] = _now,
) -> ExecutionMaterials:
    """Bind strict I01 bytes to the current request and complete plan identity."""
    snapshot = _binding_copy(context, binding, budgets, _time(clock))
    try:
        bundle = prepare_material_bundle(policy_raw, plan_raw, capability_raw, input_raw, budgets=budgets)
        materials = (bundle.policy, bundle.plan, bundle.capability, bundle.inputs)
        if any(
            type(raw) is not bytes or raw != material.canonical_bytes
            for raw, material in zip((policy_raw, plan_raw, capability_raw, input_raw), materials, strict=True)
        ):
            raise _unavailable()
        proof, request = snapshot.proof, snapshot.proof.request
        plan, inputs = bundle.plan.as_dict(), bundle.inputs.as_dict()
        if (
            (plan["scene"], tuple(plan["modules"]), plan["priority"], plan["policy_version"])
            != (request.scene, request.modules, request.priority, request.policy_version)
            or UUID(inputs["asset"]["asset_id"]) != request.asset_id
            or bundle.policy.version != snapshot.policy_version
            or bundle.policy.sha256 != proof.policy_sha256
            or (bundle.plan.document_id, bundle.plan.version, bundle.plan.sha256)
            != (proof.plan_id, proof.plan_version, proof.plan_sha256)
            or (bundle.capability.document_id, bundle.capability.version, bundle.capability.sha256)
            != (proof.capability_id, proof.capability_version, proof.capability_sha256)
        ):
            raise _unavailable()
        return ExecutionMaterials(snapshot, bundle)
    except Exception:
        raise _unavailable() from None


def _execution_copy(
    context: TaskCreationContext, value: ExecutionMaterials, budgets: MaterialBudgets, current: datetime
) -> ExecutionMaterials:
    try:
        if type(value) is not ExecutionMaterials or type(value.materials) is not MaterialBundle:
            raise _unavailable()
        bundle = value.materials
        documents = (bundle.policy, bundle.plan, bundle.capability, bundle.inputs)
        if (
            any(type(item) is not CanonicalMaterial for item in documents)
            or type(bundle.node_inputs) is not tuple
            or any(type(item) is not CanonicalMaterial for item in bundle.node_inputs)
        ):
            raise _unavailable()
        binding = value.binding
        raw = tuple(item.canonical_bytes for item in documents)
    except Exception:
        raise _unavailable() from None
    snapshot = freeze_execution_materials(context, binding, *raw, budgets=budgets, clock=lambda: current)
    try:
        if snapshot != value:
            raise _unavailable()
    except Exception:
        raise _unavailable() from None
    return snapshot


def recheck_execution_materials(
    context: TaskCreationContext,
    expected: ExecutionMaterials,
    current: ExecutionMaterials,
    *,
    budgets: MaterialBudgets,
    clock: Callable[[], datetime] = _now,
) -> ExecutionMaterials:
    """Recheck all input/node bytes too, never just the same asset/plan hash."""
    now = _time(clock)
    before = _execution_copy(context, expected, budgets, now)
    after = _execution_copy(context, current, budgets, now)
    recheck_plan_binding(context, before.binding, after.binding, budgets=budgets, clock=lambda: now)
    if before.materials != after.materials:
        raise _changed()
    _final_fresh(context, before.binding, after.binding, _time(clock))
    return after
