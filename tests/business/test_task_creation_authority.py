"""Pure full-binding boundaries on self-owned materials, never real adoption facts."""

import copy
import hashlib
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from business_app.errors import BusinessError
from business_app.permissions.context import current_authorization
from business_app.permissions.task_creation_context import freeze_task_creation_context
from business_app.permissions.types import Principal
from business_app.task_creation import TaskPlanProof
from business_app.task_creation_materials import MaterialBudgets
from business_app.types import Actor

from tests.business.test_task_creation_materials import canonical, material_documents, rebind

NOW = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)


def module():
    assert importlib.util.find_spec("business_app.task_creation_authority") is not None, (
        "Full plan-binding component is not implemented; structural boundary only, not an old authorization bypass"
    )
    return importlib.import_module("business_app.task_creation_authority")


def test_plan_binding_component_exists():
    module()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def limits(**changes):
    return MaterialBudgets(**dict(dict(max_bytes=200_000, max_nodes=20, max_capabilities=20), **changes))


def arranged(documents=None, context=None):
    documents = material_documents() if documents is None else documents
    raw = {key: canonical(documents[key]) for key in ("policy", "plan", "capability", "input")}
    plan, inputs = documents["plan"], documents["input"]
    if context is None:
        p = Principal(
            Actor(uuid4(), uuid4()), "https://self-owned.example.test", "self-owned", int(NOW.timestamp()) + 600
        )
        body = dict(
            case_id=str(uuid4()),
            asset_id=inputs["asset"]["asset_id"],
            scene=plan["scene"],
            modules=plan["modules"],
            priority=plan["priority"],
            policy_version=plan["policy_version"],
        )
        context = freeze_task_creation_context(p, body, clock=NOW.timestamp)
    proof = TaskPlanProof(
        context.request,
        "self-owned/authority/1",
        sha(raw["policy"]),
        plan["plan_id"],
        plan["plan_version"],
        sha(raw["plan"]),
        documents["capability"]["capability_id"],
        documents["capability"]["capability_version"],
        sha(raw["capability"]),
        True,
        NOW + timedelta(seconds=60),
    )
    receipt = canonical(dict(self_owned_fixture=True, note="opaque bytes are not adoption authorization"))
    facts = canonical(dict(self_owned_fixture=True, note="opaque fingerprint is not verified current capability"))
    metadata = dict(
        revision_id=uuid4(),
        head_row_version=1,
        mapping_id="self-owned/mapping",
        mapping_version="1",
        policy_id=uuid4(),
        policy_kind="self-owned/policy",
        policy_version=context.request.policy_version,
        mapping_valid_from=NOW - timedelta(minutes=1),
        mapping_valid_until=NOW + timedelta(minutes=5),
        validation_receipt_bytes=receipt,
        validation_receipt_sha256=sha(receipt),
        recovery_generation="self-owned/recovery/1",
        current_state_facts_bytes=facts,
        current_state_facts_sha256=sha(facts),
    )
    return context, proof, metadata, raw


def freeze(context, proof, metadata, **kwargs):
    return module().freeze_plan_binding(context, proof, **metadata, budgets=limits(), clock=lambda: NOW, **kwargs)


def bind_arranged():
    context, proof, metadata, raw = arranged()
    return context, freeze(context, proof, metadata), metadata, raw


def execution(context, binding, raw):
    return module().freeze_execution_materials(
        context,
        binding,
        *(raw[key] for key in ("policy", "plan", "capability", "input")),
        budgets=limits(),
        clock=lambda: NOW,
    )


def recheck(context, expected, current, clock=lambda: NOW):
    return module().recheck_plan_binding(context, expected, current, budgets=limits(), clock=clock)


def test_full_binding_and_materials_are_detached_frozen_and_not_authorization():
    m = module()
    context, proof, metadata, raw = arranged()
    binding = freeze(context, proof, metadata)
    materials = execution(context, binding, raw)
    assert binding.proof == proof and binding.proof is not proof
    assert binding.proof.request is not proof.request
    assert binding.proof.request.actor.user_id is not context.request.actor.user_id
    assert binding.authorization_request_digest == context.authorization_request_digest
    assert binding.validation_receipt_bytes == metadata["validation_receipt_bytes"]
    assert binding.current_state_facts_sha256 == sha(metadata["current_state_facts_bytes"])
    assert materials.binding == binding and materials.binding is not binding
    assert materials.materials.policy.sha256 == proof.policy_sha256
    assert materials.materials.policy.as_dict()["sha256"] != proof.policy_sha256
    assert materials.materials.inputs.as_dict()["asset"]["asset_id"] == str(context.request.asset_id)
    assert materials.materials.node_inputs and type(materials.materials.node_inputs) is tuple
    with pytest.raises(FrozenInstanceError):
        binding.head_row_version = 2
    object.__setattr__(proof.request.actor.user_id, "int", 0)
    object.__setattr__(binding, "recovery_generation", "changed-after-material-freeze")
    view = materials.materials.inputs.as_dict()
    view["asset"]["source_authorization_version"] = "changed"
    assert materials.binding.recovery_generation == "self-owned/recovery/1"
    assert materials.binding.proof.request.actor.user_id.int != 0
    assert materials.materials.inputs.as_dict()["asset"]["source_authorization_version"] != "changed"
    assert current_authorization() is None and not hasattr(materials, "authorized")
    assert not hasattr(m, "SqlTaskPlanAuthority")


@pytest.mark.parametrize(
    "field,value",
    [
        ("revision_id", UUID(int=0)),
        ("policy_id", UUID(int=0)),
        ("revision_id", "not-uuid"),
        ("head_row_version", True),
        ("head_row_version", 0),
        ("head_row_version", -1),
        ("mapping_id", ""),
        ("mapping_version", "x" * 129),
        ("policy_kind", ""),
        ("policy_version", "other-policy"),
        ("recovery_generation", ""),
    ],
)
def test_invalid_internal_identity_metadata_is_refused(field, value):
    context, proof, metadata, _ = arranged()
    metadata[field] = value
    with pytest.raises(BusinessError) as error:
        freeze(context, proof, metadata)
    assert error.value.http_status == 503


@pytest.mark.parametrize("field", ["validation_receipt_bytes", "current_state_facts_bytes"])
@pytest.mark.parametrize(
    "raw",
    [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b"\xff", b"[]", b"true", b' {"x":1}', None, bytearray(b"{}")],
)
def test_opaque_observations_require_bounded_exact_canonical_json_objects(field, raw):
    context, proof, metadata, _ = arranged()
    metadata[field] = raw
    if type(raw) is bytes:
        metadata[field.removesuffix("_bytes") + ("_sha256" if field == "validation_receipt_bytes" else "_sha256")] = (
            sha(raw)
        )
    with pytest.raises(BusinessError) as error:
        freeze(context, proof, metadata)
    assert error.value.http_status == 503


@pytest.mark.parametrize("field", ["validation_receipt_sha256", "current_state_facts_sha256"])
def test_observation_bytes_cannot_be_substituted_under_a_different_digest(field):
    context, proof, metadata, _ = arranged()
    metadata[field] = "b" * 64
    with pytest.raises(BusinessError) as error:
        freeze(context, proof, metadata)
    assert error.value.http_status == 503


def test_caller_budgets_are_required_and_apply_to_opaque_materials():
    context, proof, metadata, _ = arranged()
    with pytest.raises(TypeError):
        module().freeze_plan_binding(context, proof, **metadata, clock=lambda: NOW)
    for budgets in [None, limits(max_bytes=1)]:
        with pytest.raises(BusinessError) as error:
            module().freeze_plan_binding(context, proof, **metadata, budgets=budgets, clock=lambda: NOW)
        assert error.value.http_status == 503


@pytest.mark.parametrize(
    "change", ["naive-start", "not-started", "expired", "proof-outlives-mapping", "proof-outlives-principal"]
)
def test_proof_is_within_current_explicit_identity_and_mapping_windows(change):
    context, proof, metadata, _ = arranged()
    if change == "naive-start":
        metadata["mapping_valid_from"] = NOW.replace(tzinfo=None)
    elif change == "not-started":
        metadata["mapping_valid_from"] = NOW + timedelta(seconds=1)
    elif change == "expired":
        metadata["mapping_valid_until"] = NOW
    elif change == "proof-outlives-mapping":
        metadata["mapping_valid_until"] = NOW + timedelta(seconds=30)
    else:
        proof = replace(proof, valid_until=NOW + timedelta(seconds=601))
        metadata["mapping_valid_until"] = NOW + timedelta(seconds=700)
    with pytest.raises(BusinessError) as error:
        freeze(context, proof, metadata)
    assert error.value.http_status == 503


@pytest.mark.parametrize("clock", [lambda: None, lambda: NOW.replace(tzinfo=None), lambda: "now"])
def test_invalid_clock_is_refused(clock):
    context, proof, metadata, _ = arranged()
    with pytest.raises(BusinessError) as error:
        module().freeze_plan_binding(context, proof, **metadata, budgets=limits(), clock=clock)
    assert error.value.http_status == 503


@pytest.mark.parametrize(
    "field",
    [
        "revision_id",
        "head_row_version",
        "mapping_id",
        "mapping_version",
        "policy_id",
        "policy_kind",
        "recovery_generation",
        "receipt",
        "facts",
        "window",
    ],
)
def test_identical_plan_hash_does_not_allow_a_different_full_binding(field):
    context, expected, metadata, _ = bind_arranged()
    if field in {"revision_id", "policy_id"}:
        metadata[field] = uuid4()
    elif field == "head_row_version":
        metadata[field] = 2
    elif field == "receipt":
        metadata["validation_receipt_bytes"] = canonical(dict(self_owned_changed_receipt=True))
        metadata["validation_receipt_sha256"] = sha(metadata["validation_receipt_bytes"])
    elif field == "facts":
        metadata["current_state_facts_bytes"] = canonical(dict(self_owned_changed_facts=True))
        metadata["current_state_facts_sha256"] = sha(metadata["current_state_facts_bytes"])
    elif field == "window":
        metadata["mapping_valid_from"] -= timedelta(minutes=1)
    else:
        metadata[field] += "/changed"
    current = freeze(context, expected.proof, metadata)
    assert current.proof.plan_sha256 == expected.proof.plan_sha256
    with pytest.raises(BusinessError) as error:
        recheck(context, expected, current)
    assert (error.value.code, error.value.http_status) == ("AUTHORIZATION_CHANGED", 503)


def test_deadline_extension_is_allowed_but_cannot_hide_other_binding_changes():
    context, expected, metadata, _ = bind_arranged()
    extended = freeze(context, replace(expected.proof, valid_until=NOW + timedelta(seconds=90)), metadata)
    assert recheck(context, expected, extended).proof.valid_until == extended.proof.valid_until
    shortened = freeze(context, replace(expected.proof, valid_until=NOW + timedelta(seconds=30)), metadata)
    with pytest.raises(BusinessError):
        recheck(context, expected, shortened)
    with pytest.raises(BusinessError):
        recheck(context, expected, extended, clock=lambda: NOW + timedelta(seconds=60))
    with pytest.raises(BusinessError):
        recheck(context, expected, replace(extended, head_row_version=2))


@pytest.mark.parametrize(
    "field", ["authorization_request_digest", "policy_version", "validation_receipt_sha256", "head_row_version"]
)
def test_direct_constructed_binding_replacements_are_revalidated(field):
    context, expected, _, _ = bind_arranged()
    value = 0 if field == "head_row_version" else "changed"
    forged = replace(expected, **{field: value})
    with pytest.raises(BusinessError):
        recheck(context, expected, forged)


def test_uninitialized_binding_and_materials_do_not_leak_attribute_error():
    m = module()
    context, expected, _, raw = bind_arranged()
    with pytest.raises(BusinessError):
        recheck(context, expected, object.__new__(m.PlanBinding))
    good = execution(context, expected, raw)
    with pytest.raises(BusinessError):
        m.recheck_execution_materials(
            context, good, object.__new__(m.ExecutionMaterials), budgets=limits(), clock=lambda: NOW
        )


@pytest.mark.parametrize("field", ["scene", "modules", "priority", "policy_version", "asset_id"])
def test_schema_valid_execution_materials_must_match_the_frozen_request(field):
    documents = material_documents()
    context = arranged(documents)[0]
    if field == "scene":
        documents["plan"][field] = "harmful_content"
    elif field == "modules":
        documents["plan"][field].reverse()
    elif field == "priority":
        documents["plan"][field] = "high"
    elif field == "policy_version":
        documents["policy"]["version"] += "/changed"
        documents["plan"][field] += "/changed"
    else:
        documents["input"]["asset"]["asset_id"] = str(uuid4())
    rebind(documents)
    _, proof, metadata, raw = arranged(documents, context)
    binding = freeze(context, proof, metadata)
    with pytest.raises(BusinessError) as error:
        execution(context, binding, raw)
    assert error.value.http_status == 503


@pytest.mark.parametrize("field", ["policy_sha256", "plan_sha256", "capability_sha256"])
def test_materials_bind_whole_canonical_artifact_hashes_to_proof(field):
    context, binding, _, raw = bind_arranged()
    if field == "policy_sha256":
        wrong = json.loads(raw["policy"])["sha256"]
    else:
        wrong = "b" * 64
    bad = replace(binding, proof=replace(binding.proof, **{field: wrong}))
    with pytest.raises(BusinessError):
        execution(context, bad, raw)


@pytest.mark.parametrize("field", ["policy", "plan", "capability", "input"])
def test_execution_materials_refuse_noncanonical_bytes_without_silent_rewrite(field):
    context, binding, _, raw = bind_arranged()
    raw[field] = b" " + raw[field]
    with pytest.raises(BusinessError):
        execution(context, binding, raw)


@pytest.mark.parametrize("change", ["object-version", "source-version", "input-id", "input-version", "asset-sha"])
def test_execution_recheck_detects_input_versions_even_for_the_same_asset_and_plan(change):
    m = module()
    documents = material_documents()
    context, proof, metadata, raw = arranged(documents)
    binding = freeze(context, proof, metadata)
    expected = execution(context, binding, raw)
    altered = copy.deepcopy(documents)
    if change == "object-version":
        altered["input"]["asset"]["object_ref"]["version_id"] += "/changed"
        altered["input"]["nodes"][0]["inputs"][1]["value"] += "/changed"
    elif change == "source-version":
        altered["input"]["asset"]["source_authorization_version"] += "/changed"
    elif change in {"input-id", "input-version"}:
        altered["input"]["input_id" if change == "input-id" else "input_version"] += "/changed"
    else:
        altered["input"]["asset"]["sha256"] = "b" * 64
        altered["input"]["asset"]["object_ref"]["sha256"] = "b" * 64
        altered["input"]["nodes"][0]["inputs"][2]["value"] = "b" * 64
    changed_raw = {key: canonical(altered[key]) for key in raw}
    current = execution(context, binding, changed_raw)
    assert (
        current.materials.inputs.as_dict()["asset"]["asset_id"]
        == expected.materials.inputs.as_dict()["asset"]["asset_id"]
    )
    assert current.materials.plan.sha256 == expected.materials.plan.sha256
    with pytest.raises(BusinessError) as error:
        m.recheck_execution_materials(context, expected, current, budgets=limits(), clock=lambda: NOW)
    assert error.value.code == "AUTHORIZATION_CHANGED"


def test_execution_recheck_is_detached_and_does_not_trust_forged_bundle_fields():
    m = module()
    context, binding, _, raw = bind_arranged()
    expected = execution(context, binding, raw)
    checked = m.recheck_execution_materials(context, expected, expected, budgets=limits(), clock=lambda: NOW)
    assert checked == expected and checked is not expected
    assert checked.materials is not expected.materials
    forged = replace(
        expected, materials=replace(expected.materials, inputs=replace(expected.materials.inputs, sha256="b" * 64))
    )
    with pytest.raises(BusinessError):
        m.recheck_execution_materials(context, expected, forged, budgets=limits(), clock=lambda: NOW)


@pytest.mark.parametrize("boundary", ["binding", "materials"])
def test_recheck_samples_clock_after_work_and_rejects_original_deadline_crossing(boundary):
    m = module()
    context, expected, metadata, raw = bind_arranged()
    extended = freeze(context, replace(expected.proof, valid_until=NOW + timedelta(seconds=90)), metadata)
    ticks = iter((NOW, NOW + timedelta(seconds=60)))
    if boundary == "binding":
        call = lambda: recheck(context, expected, extended, clock=lambda: next(ticks))
    else:
        before, after = execution(context, expected, raw), execution(context, extended, raw)
        call = lambda: m.recheck_execution_materials(
            context, before, after, budgets=limits(), clock=lambda: next(ticks)
        )
    with pytest.raises(BusinessError) as error:
        call()
    assert (error.value.code, error.value.http_status) == ("AUTHORIZATION_CHANGED", 503)


@pytest.mark.parametrize("defect", ["expired-principal", "altered-request", "altered-B", "missing-principal"])
def test_each_check_revalidates_current_context_not_only_the_stored_plan_hash(defect):
    context, expected, _, _ = bind_arranged()
    if defect == "expired-principal":
        context = replace(context, principal=replace(context.principal, expires_at=int(NOW.timestamp())))
    elif defect == "altered-request":
        context = replace(context, request=replace(context.request, modules=("RESOURCE", "INGEST")))
    elif defect == "altered-B":
        context = replace(context, authorization_request_digest="b" * 64)
    else:
        object.__delattr__(context, "principal")
    with pytest.raises(BusinessError) as error:
        recheck(context, expected, expected)
    assert error.value.http_status == (401 if defect == "expired-principal" else 503)


def test_false_proof_remains_permission_denial_and_opaque_flags_never_add_allow():
    context, proof, metadata, _ = arranged()
    with pytest.raises(BusinessError) as error:
        freeze(context, replace(proof, authorized=False), metadata)
    assert (error.value.code, error.value.http_status) == ("PERMISSION_REQUIRED", 403)
    metadata["validation_receipt_bytes"] = canonical(dict(validated=True))
    metadata["validation_receipt_sha256"] = sha(metadata["validation_receipt_bytes"])
    structural = freeze(context, proof, metadata)
    assert structural.validation_receipt_bytes == b'{"validated":true}'
    assert not hasattr(structural, "allowed") and current_authorization() is None


def test_unicode_exact_artifacts_remain_bound_without_rewriting_A_or_B():
    documents = material_documents()
    documents["plan"]["plan_id"] = "self-owned/材料"
    documents["input"]["plan_id"] = documents["plan"]["plan_id"]
    rebind(documents)
    context, proof, metadata, raw = arranged(documents)
    binding = freeze(context, proof, metadata)
    frozen = execution(context, binding, raw)
    assert frozen.materials.plan.canonical_bytes == raw["plan"]
    assert b"\\u6750" not in frozen.materials.plan.canonical_bytes
    assert binding.proof.request.canonical_body == context.request.canonical_body
    assert binding.proof.request.request_sha256 == context.request.request_sha256
    assert binding.authorization_request_digest == context.authorization_request_digest
