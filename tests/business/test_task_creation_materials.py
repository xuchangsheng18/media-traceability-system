"""Pure internal-material tests; every adoption/identity fact is self-owned data only."""

import copy
import hashlib
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError

import pytest


def module():
    assert importlib.util.find_spec("business_app.task_creation_materials") is not None, (
        "Task material boundary missing; not a previously accepted malicious business input"
    )
    return importlib.import_module("business_app.task_creation_materials")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf8")


def material_documents():
    # Exact self-owned bytes and placeholder hashes prove structure only, never real adoption.
    return json.loads(
        '{"policy": {"definition_ref": "urn:sha256:451b1293b25139f2a58e7cb3176f690d4b1dcb4a302305170654f7e83b447928", "version": "self-owned/policy/1", "sha256": "451b1293b25139f2a58e7cb3176f690d4b1dcb4a302305170654f7e83b447928", "values": {"self_owned_fixture": true}}, "plan": {"schema_id": "urn:media-trace:task-execution-plan:1.0.0", "schema_version": "1.0.0", "plan_id": "self-owned/plan", "plan_version": "1", "scene": "accident_rumor", "modules": ["INGEST", "RESOURCE"], "priority": "normal", "policy_version": "self-owned/policy/1", "capability": {"capability_id": "self-owned/capabilities", "capability_version": "1", "capability_sha256": "161dbef5333a5dc1b7b71516f711226bacc7f5b51e74ff81adbd16ed784f0313"}, "nodes": [{"node_code": "retain_ref", "dependencies": [], "required": true, "missing_policy": "FAIL_REQUIRED", "handler": {"handler_id": "self-owned/ref-copy", "handler_version": "1", "release_id": "60000000-0000-4000-8000-000000000001", "code_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", "package_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"}, "model_dependencies": [], "input_schema_id": "urn:media-trace:api:0.1.0#/$defs/ObjectRef", "output_schema_id": "urn:media-trace:api:0.1.0#/$defs/ObjectRef", "input_bindings": [{"field_path": "object_id", "source": "asset", "selector": "asset.object_ref.object_id"}, {"field_path": "version_id", "source": "asset", "selector": "asset.object_ref.version_id"}, {"field_path": "sha256", "source": "asset", "selector": "asset.object_ref.sha256"}], "preprocessing_version": "self-owned/identity/1", "postprocessing_version": "self-owned/identity/1", "output_refs": ["result"], "dispatch_protocol_version": "self-owned/task-dispatch/1"}]}, "capability": {"schema_id": "urn:media-trace:task-capability-manifest:1.0.0", "schema_version": "1.0.0", "capability_id": "self-owned/capabilities", "capability_version": "1", "handlers": [{"handler_id": "self-owned/ref-copy", "handler_version": "1", "release_id": "60000000-0000-4000-8000-000000000001", "code_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", "package_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", "input_schema_id": "urn:media-trace:api:0.1.0#/$defs/ObjectRef", "output_schema_id": "urn:media-trace:api:0.1.0#/$defs/ObjectRef", "license_ref": "self-owned-fixture/license", "status_protocol_version": "self-owned/current-status/1", "model_dependencies": []}]}, "input": {"schema_id": "urn:media-trace:task-input-manifest:1.0.0", "schema_version": "1.0.0", "input_id": "self-owned/input", "input_version": "1", "plan_id": "self-owned/plan", "plan_version": "1", "plan_sha256": "43c6fd492e78e0f9f7235be5f4a2f703686bc0fc37cb95e9aa9c49d6469b9570", "asset": {"asset_id": "70000000-0000-4000-8000-000000000001", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "object_ref": {"object_id": "80000000-0000-4000-8000-000000000001", "version_id": "self-owned/fixed/1", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}, "source_authorization_version": "self-owned/source-auth/1"}, "nodes": [{"node_code": "retain_ref", "inputs": [{"field_path": "object_id", "source": "asset", "selector": "asset.object_ref.object_id", "materialized": true, "value": "80000000-0000-4000-8000-000000000001"}, {"field_path": "version_id", "source": "asset", "selector": "asset.object_ref.version_id", "materialized": true, "value": "self-owned/fixed/1"}, {"field_path": "sha256", "source": "asset", "selector": "asset.object_ref.sha256", "materialized": true, "value": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]}]}}'
    )


def budgets(**changes):
    values = dict(max_bytes=200_000, max_nodes=20, max_capabilities=20)
    values.update(changes)
    return module().MaterialBudgets(**values)


def bundle(documents=None):
    d = material_documents() if documents is None else documents
    return module().prepare_material_bundle(
        *(canonical(d[name]) for name in ("policy", "plan", "capability", "input")), budgets=budgets()
    )


def rebind(d):
    d["plan"]["capability"]["capability_sha256"] = hashlib.sha256(canonical(d["capability"])).hexdigest()
    d["input"]["plan_sha256"] = hashlib.sha256(canonical(d["plan"])).hexdigest()


def test_internal_schema_ids_are_registered_locally():
    from business_app.contracts import SCHEMAS

    assert all(
        f"urn:media-trace:task-{kind}:1.0.0" in SCHEMAS
        for kind in ("execution-plan", "capability-manifest", "input-manifest")
    ), "Internal schema formats not yet provided; not evidence of a business authorization bypass"


def test_strict_material_boundary_is_available_without_default_authority():
    value = bundle()
    assert value.plan.document_id == "self-owned/plan"
    assert value.capability.document_id == "self-owned/capabilities"
    assert value.inputs.document_id == "self-owned/input"
    assert len(value.node_inputs) == 1
    assert value.plan.as_dict()["nodes"][0]["model_dependencies"] == []
    assert not hasattr(value, "authorized") and not hasattr(value, "executable")


def test_materials_are_canonical_frozen_and_detached():
    d = material_documents()
    d["plan"]["plan_id"] = "self-owned/材料"
    d["input"]["plan_id"] = d["plan"]["plan_id"]
    rebind(d)
    raw = json.dumps(d["plan"], ensure_ascii=False, indent=4).encode()
    material = module().parse_execution_plan(raw, budgets=budgets())
    assert material.canonical_bytes == canonical(d["plan"])
    assert material.sha256 == hashlib.sha256(material.canonical_bytes).hexdigest()
    assert material.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert material.canonicalization_version == module().CANONICALIZATION_VERSION
    with pytest.raises(FrozenInstanceError):
        material.version = "changed"
    view = material.as_dict()
    view["nodes"][0]["handler"]["handler_id"] = "untrusted/changed"
    assert material.as_dict()["nodes"][0]["handler"]["handler_id"] == "self-owned/ref-copy"
    assert b"\\u6750" not in material.canonical_bytes


@pytest.mark.parametrize("field", ["max_bytes", "max_nodes", "max_capabilities"])
@pytest.mark.parametrize("value", [None, True, False, 0, -1, 1.5, "100"])
def test_budgets_require_explicit_positive_integers(field, value):
    with pytest.raises(ValueError, match="TASK_MATERIAL_LIMIT_INVALID"):
        budgets(**{field: value})


def test_missing_budgets_have_no_defaults():
    with pytest.raises(TypeError):
        module().MaterialBudgets()


@pytest.mark.parametrize(
    "name,parser",
    [
        ("plan", "parse_execution_plan"),
        ("capability", "parse_capability_manifest"),
        ("input", "parse_input_manifest"),
        ("policy", "parse_policy_artifact"),
    ],
)
@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":{"y":1,"y":2}}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b"\xff",
        b"[]",
        b"null",
        b'{"x":"\\ud800"}',
        b'{"x":1e999}',
    ],
)
def test_strict_json_refuses_ambiguous_nonfinite_or_non_utf8(name, parser, raw):
    with pytest.raises(ValueError, match="TASK_MATERIAL_INVALID"):
        getattr(module(), parser)(raw, budgets=budgets())


@pytest.mark.parametrize(
    "name,parser",
    [
        ("plan", "parse_execution_plan"),
        ("capability", "parse_capability_manifest"),
        ("input", "parse_input_manifest"),
        ("policy", "parse_policy_artifact"),
    ],
)
def test_budget_refuses_oversized_material_bytes(name, parser):
    with pytest.raises(ValueError, match="TASK_MATERIAL_BUDGET_EXCEEDED"):
        getattr(module(), parser)(canonical(material_documents()[name]), budgets=budgets(max_bytes=1))


@pytest.mark.parametrize(
    "defect",
    [
        "extra",
        "schema",
        "empty",
        "duplicate",
        "unknown-dependency",
        "cycle",
        "missing-model-list",
        "required-policy",
        "optional-policy",
        "unknown-schema",
        "unknown-fragment",
        "duplicate-field",
        "missing-required-field",
        "bad-asset-selector",
        "bad-upstream",
        "duplicate-output",
    ],
)
def test_plan_rejects_inconsistent_graph_schema_or_bindings(defect):
    d = material_documents()["plan"]
    n = d["nodes"][0]
    if defect == "extra":
        d["secret_default"] = True
    elif defect == "schema":
        d["schema_id"] = "urn:unregistered"
    elif defect == "empty":
        d["nodes"] = []
    elif defect == "duplicate":
        d["nodes"].append(copy.deepcopy(n))
    elif defect == "unknown-dependency":
        n["dependencies"] = ["missing"]
    elif defect == "cycle":
        n["dependencies"] = [n["node_code"]]
    elif defect == "missing-model-list":
        del n["model_dependencies"]
    elif defect == "required-policy":
        n["missing_policy"] = "SKIP_OPTIONAL"
    elif defect == "optional-policy":
        n["required"] = False
    elif defect == "unknown-schema":
        n["input_schema_id"] = "https://example.invalid/schema"
    elif defect == "unknown-fragment":
        n["output_schema_id"] = "urn:media-trace:api:0.1.0#/$defs/Missing"
    elif defect == "duplicate-field":
        n["input_bindings"].append(copy.deepcopy(n["input_bindings"][0]))
    elif defect == "missing-required-field":
        n["input_bindings"].pop()
    elif defect == "bad-asset-selector":
        n["input_bindings"][0]["selector"] = "asset.storage_url"
    elif defect == "bad-upstream":
        n["input_bindings"][0] = dict(
            field_path="object_id", source="node_output", node_code="missing", output_ref="result", selector="object_id"
        )
    else:
        n["output_refs"].append("result")
    with pytest.raises(ValueError, match="TASK_MATERIAL_(INVALID|BINDING_INVALID)"):
        module().parse_execution_plan(canonical(d), budgets=budgets())


@pytest.mark.parametrize("name", ["plan", "capability", "input"])
def test_nested_extra_fields_are_rejected(name):
    d = material_documents()[name]
    if name == "plan":
        d["nodes"][0]["handler"]["import_path"] = "os.system"
    elif name == "capability":
        d["handlers"][0]["allow"] = True
    else:
        d["asset"]["storage_url"] = "https://example.invalid"
    parser = {
        "plan": "parse_execution_plan",
        "capability": "parse_capability_manifest",
        "input": "parse_input_manifest",
    }[name]
    with pytest.raises(ValueError, match="TASK_MATERIAL_INVALID"):
        getattr(module(), parser)(canonical(d), budgets=budgets())


def test_node_and_capability_counts_obey_explicit_limits():
    d = material_documents()
    second = copy.deepcopy(d["plan"]["nodes"][0])
    second["node_code"] = "second"
    d["plan"]["nodes"].append(second)
    with pytest.raises(ValueError, match="TASK_MATERIAL_BUDGET_EXCEEDED"):
        module().parse_execution_plan(canonical(d["plan"]), budgets=budgets(max_nodes=1))
    handler = copy.deepcopy(d["capability"]["handlers"][0])
    handler["handler_id"] += "/second"
    d["capability"]["handlers"].append(handler)
    with pytest.raises(ValueError, match="TASK_MATERIAL_BUDGET_EXCEEDED"):
        module().parse_capability_manifest(canonical(d["capability"]), budgets=budgets(max_capabilities=1))


@pytest.mark.parametrize(
    "defect",
    [
        "policy-sha",
        "policy-ref",
        "policy-version",
        "capability-id",
        "capability-version",
        "capability-sha",
        "handler-code",
        "handler-package",
        "handler-release",
        "handler-schema",
        "handler-model",
        "duplicate-handler",
        "unused-handler",
        "input-plan",
        "input-sha",
        "input-asset-sha",
        "input-empty-nodes",
        "input-wrong-node",
        "input-missing-field",
        "input-mismatch-value",
        "input-asset-pending",
        "input-extra-value",
    ],
)
def test_bundle_rejects_material_or_execution_binding_changes(defect):
    d = material_documents()
    p = d["plan"]
    c = d["capability"]
    i = d["input"]
    h = c["handlers"][0]
    if defect == "policy-sha":
        d["policy"]["sha256"] = "b" * 64
    elif defect == "policy-ref":
        d["policy"]["definition_ref"] = "urn:sha256:" + "b" * 64
    elif defect == "policy-version":
        d["policy"]["version"] += "/other"
    elif defect == "capability-id":
        c["capability_id"] += "/other"
    elif defect == "capability-version":
        c["capability_version"] += "/other"
    elif defect == "capability-sha":
        p["capability"]["capability_sha256"] = "b" * 64
    elif defect == "handler-code":
        h["code_sha256"] = "b" * 64
    elif defect == "handler-package":
        h["package_sha256"] = "b" * 64
    elif defect == "handler-release":
        h["release_id"] = "90000000-0000-4000-8000-000000000001"
    elif defect == "handler-schema":
        h["output_schema_id"] = "urn:media-trace:api:0.1.0#/$defs/TaskCreate"
    elif defect == "handler-model":
        h["model_dependencies"] = [
            dict(
                model_id="90000000-0000-4000-8000-000000000001",
                model_version="1",
                model_task_version="1",
                release_id="90000000-0000-4000-8000-000000000002",
                artifact_sha256="b" * 64,
            )
        ]
    elif defect == "duplicate-handler":
        c["handlers"].append(copy.deepcopy(h))
    elif defect == "unused-handler":
        extra = copy.deepcopy(h)
        extra["handler_id"] += "/unused"
        c["handlers"].append(extra)
    elif defect == "input-plan":
        i["plan_id"] += "/other"
    elif defect == "input-sha":
        i["plan_sha256"] = "b" * 64
    elif defect == "input-asset-sha":
        i["asset"]["sha256"] = "b" * 64
    elif defect == "input-empty-nodes":
        i["nodes"] = []
    elif defect == "input-wrong-node":
        i["nodes"][0]["node_code"] = "missing"
    elif defect == "input-missing-field":
        i["nodes"][0]["inputs"].pop()
    elif defect == "input-mismatch-value":
        i["nodes"][0]["inputs"][0]["value"] = "90000000-0000-4000-8000-000000000001"
    elif defect == "input-asset-pending":
        i["nodes"][0]["inputs"][0]["materialized"] = False
    else:
        i["nodes"][0]["inputs"][0]["untrusted"] = True
    # Rebind envelope hashes for semantic defects, while retaining deliberately wrong ID/hash cases.
    if defect.startswith("handler-") or defect in {"duplicate-handler", "unused-handler"}:
        rebind(d)
    with pytest.raises(ValueError, match="TASK_MATERIAL_(INVALID|BINDING_INVALID)"):
        bundle(d)


def test_pending_upstream_selectors_are_frozen_without_fake_outputs():
    d = material_documents()
    p = d["plan"]
    i = d["input"]
    next_node = copy.deepcopy(p["nodes"][0])
    next_node["node_code"] = "next"
    next_node["dependencies"] = ["retain_ref"]
    next_node["input_bindings"] = [
        dict(field_path=key, source="node_output", node_code="retain_ref", output_ref="result", selector=key)
        for key in ("object_id", "version_id", "sha256")
    ]
    p["nodes"].append(next_node)
    i["nodes"].append(
        dict(node_code="next", inputs=[dict(binding, materialized=False) for binding in next_node["input_bindings"]])
    )
    rebind(d)
    value = bundle(d)
    pending_node = value.node_inputs[1].as_dict()
    assert pending_node["node"]["inputs"][0]["materialized"] is False
    assert "value" not in pending_node["node"]["inputs"][0]
    assert len(value.node_inputs) == 2
    i["nodes"][1]["inputs"][0]["value"] = "fabricated"
    with pytest.raises(ValueError):
        bundle(d)


def test_ordered_modules_are_not_sorted_or_inferred_as_approved():
    d = material_documents()
    before = bundle(d).plan.sha256
    d["plan"]["modules"].reverse()
    rebind(d)
    after = bundle(d).plan
    assert after.sha256 != before
    assert after.as_dict()["modules"] == ["RESOURCE", "INGEST"]


@pytest.mark.parametrize("nested", [False, True])
def test_duplicate_known_keys_in_an_otherwise_valid_plan_are_not_silently_selected(nested):
    d = material_documents()["plan"]
    raw = canonical(d)
    if nested:
        raw = raw.replace(b'"required":true', b'"required":false,"required":true', 1)
    else:
        raw = raw.replace(b'"plan_version":"1"', b'"plan_version":"old","plan_version":"1"', 1)
    assert raw != canonical(d)
    with pytest.raises(ValueError, match="TASK_MATERIAL_INVALID"):
        module().parse_execution_plan(raw, budgets=budgets())


def test_different_nodes_with_one_code_and_an_actual_two_node_cycle_are_rejected():
    d = material_documents()["plan"]
    second = copy.deepcopy(d["nodes"][0])
    second["preprocessing_version"] = "self-owned/different"
    d["nodes"].append(second)
    with pytest.raises(ValueError, match="TASK_MATERIAL_BINDING_INVALID"):
        module().parse_execution_plan(canonical(d), budgets=budgets())
    second["node_code"] = "second"
    d["nodes"][0]["dependencies"] = ["second"]
    second["dependencies"] = ["retain_ref"]
    with pytest.raises(ValueError, match="TASK_MATERIAL_BINDING_INVALID"):
        module().parse_execution_plan(canonical(d), budgets=budgets())


def test_duplicate_model_identity_with_different_artifact_is_not_an_alternate_capability():
    d = material_documents()["capability"]
    model = dict(
        model_id="90000000-0000-4000-8000-000000000001",
        model_version="1",
        model_task_version="1",
        release_id="90000000-0000-4000-8000-000000000002",
        artifact_sha256="b" * 64,
    )
    d["handlers"][0]["model_dependencies"] = [model, dict(model, artifact_sha256="c" * 64)]
    with pytest.raises(ValueError, match="TASK_MATERIAL_BINDING_INVALID"):
        module().parse_capability_manifest(canonical(d), budgets=budgets())


def test_explicit_model_references_can_freeze_but_do_not_prove_current_release_or_execution():
    d = material_documents()
    model = dict(
        model_id="90000000-0000-4000-8000-000000000001",
        model_version="1",
        model_task_version="1",
        release_id="90000000-0000-4000-8000-000000000002",
        artifact_sha256="b" * 64,
    )
    d["plan"]["nodes"][0]["model_dependencies"] = [model]
    d["capability"]["handlers"][0]["model_dependencies"] = [model]
    rebind(d)
    value = bundle(d)
    assert value.plan.as_dict()["nodes"][0]["model_dependencies"] == [model]
    assert not hasattr(value, "authorized") and not hasattr(value, "executable")


def test_uuid_case_alias_does_not_hide_a_duplicate_model_release_identity():
    d = material_documents()["capability"]
    model = dict(
        model_id="a0000000-0000-4000-8000-000000000001",
        model_version="1",
        model_task_version="1",
        release_id="b0000000-0000-4000-8000-000000000002",
        artifact_sha256="b" * 64,
    )
    alias = dict(model, model_id=model["model_id"].upper(), release_id=model["release_id"].upper())
    d["handlers"][0]["model_dependencies"] = [model, alias]
    with pytest.raises(ValueError, match="TASK_MATERIAL_BINDING_INVALID"):
        module().parse_capability_manifest(canonical(d), budgets=budgets())


@pytest.mark.parametrize("value", [bytearray(b"{}"), "{}", None])
def test_non_bytes_cannot_enter_the_canonical_material_boundary(value):
    with pytest.raises(ValueError, match="TASK_MATERIAL_INVALID"):
        module().parse_execution_plan(value, budgets=budgets())


def test_valid_policy_with_nonfinite_extra_value_still_fails_closed():
    raw = canonical(material_documents()["policy"])
    raw = raw.replace(b'"values":{', b'"values":{"untrusted":1e999,', 1)
    with pytest.raises(ValueError, match="TASK_MATERIAL_INVALID"):
        module().parse_policy_artifact(raw, budgets=budgets())


@pytest.mark.parametrize("schema_name", ["ApprovalCreate", "Relation", "SearchJob"])
def test_existing_combination_schemas_refuse_unsupported_root_constraints(schema_name):
    # These registered real schemas have root allOf relationships. A field-only
    # mapper cannot claim that selecting their properties validates that rule.
    from business_app.contracts import SCHEMAS

    assert "allOf" in SCHEMAS["urn:media-trace:api:0.1.0"]["$defs"][schema_name]
    plan = material_documents()["plan"]
    plan["nodes"][0]["output_schema_id"] = "urn:media-trace:api:0.1.0#/$defs/" + schema_name
    with pytest.raises(ValueError, match="TASK_MATERIAL_BINDING_INVALID"):
        module().parse_execution_plan(canonical(plan), budgets=budgets())


@pytest.mark.parametrize(
    "keyword,constraint",
    [
        ("allOf", []),
        ("oneOf", [{}]),
        ("anyOf", [{}]),
        ("if", {}),
        ("then", {}),
        ("else", {}),
        ("dependentRequired", {"sha256": ["version_id"]}),
        ("dependentSchemas", {"sha256": {}}),
        ("patternProperties", {".*": {}}),
        ("additionalProperties", {}),
        ("additionalProperties", True),
        ("unevaluatedProperties", False),
        ("propertyNames", {"minLength": 1}),
        ("minProperties", 1),
        ("maxProperties", 3),
        ("not", {}),
        ("const", {}),
        ("enum", [{}]),
        ("$defs", {}),
        ("unimplemented_keyword", True),
    ],
)
def test_registered_root_constraints_cannot_be_ignored_by_a_field_mapper(monkeypatch, keyword, constraint):
    from business_app.contracts import SCHEMAS

    schema = copy.deepcopy(SCHEMAS["urn:media-trace:api:0.1.0"])
    schema["$defs"]["ObjectRef"][keyword] = constraint
    monkeypatch.setitem(SCHEMAS, "urn:media-trace:api:0.1.0", schema)
    with pytest.raises(ValueError, match="TASK_MATERIAL_BINDING_INVALID"):
        module().parse_execution_plan(canonical(material_documents()["plan"]), budgets=budgets())


def test_closed_root_keeps_full_nested_field_constraints(monkeypatch):
    from business_app.contracts import SCHEMAS

    schema = copy.deepcopy(SCHEMAS["urn:media-trace:api:0.1.0"])
    schema["$defs"]["ObjectRef"]["properties"]["version_id"] = {
        "anyOf": [{"const": "self-owned/fixed/1"}, {"const": "self-owned/alternate"}]
    }
    monkeypatch.setitem(SCHEMAS, "urn:media-trace:api:0.1.0", schema)
    assert bundle().node_inputs
    d = material_documents()
    d["input"]["asset"]["object_ref"]["version_id"] = "self-owned/unsupported"
    d["input"]["nodes"][0]["inputs"][1]["value"] = "self-owned/unsupported"
    with pytest.raises(ValueError, match="TASK_MATERIAL_BINDING_INVALID"):
        bundle(d)
