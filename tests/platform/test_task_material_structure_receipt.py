"""Offline structure receipts never establish adoption or live authority."""

import hashlib
import importlib
import json
import os
import socket
import stat
import subprocess
import sys
from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from tests.platform import test_task_creation_adoption as adoption
from tests.platform.test_task_creation_adoption import (
    canonical,
    configured_documents,
    development_arguments,
    private_development_configuration,
    tool,
)


def test_configured_prepare_writes_a_real_structure_receipt_that_verifies_against_the_same_inputs(tmp_path, capsys):
    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    arguments = development_arguments("prepare-development", documents, configuration_path, destination)
    assert tool().main([*arguments, "--structure-receipt"]) == 0
    prepared = json.loads(capsys.readouterr().out)
    receipt_path = destination / "material-structure-receipt.json"
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    assert receipt_raw == canonical(receipt)
    assert receipt["schema_id"] == "urn:media-trace:task-material-structure-receipt:1.0.0"
    assert receipt["status"] == "MATERIAL_STRUCTURE_VALIDATED_NOT_ADOPTED"
    manifest = json.loads((destination / "manifest.json").read_bytes())
    expected = dict(
        file_name="material-structure-receipt.json",
        sha256=hashlib.sha256(receipt_raw).hexdigest(),
        size_bytes=len(receipt_raw),
        status="MATERIAL_STRUCTURE_VALIDATED_NOT_ADOPTED",
    )
    assert prepared["structure_receipt"] == manifest["structure_receipt"] == expected
    assert prepared["artifact_count"] == 6
    verify_arguments = development_arguments("verify-development-receipt", documents, configuration_path)
    assert tool().main([*verify_arguments, "--receipt", str(receipt_path)]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["status"] == "STRUCTURE_RECEIPT_VERIFIED_NOT_ADOPTED"
    assert verified["receipt_sha256"] == verified["receipt_source_sha256"] == expected["sha256"]
    assert verified["development_configuration"] == prepared["development_configuration"]


def receipt_module():
    return importlib.import_module("business_app.task_creation_receipt")


def prepared_receipt(tmp_path):
    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    result = tool().run_development(
        "prepare-development",
        documents,
        configuration_path,
        runtime_profile="development",
        output=destination,
        structure_receipt=True,
    )
    receipt_path = destination / "material-structure-receipt.json"
    return documents, configuration_path, destination, receipt_path, result


def verify_arguments(documents, configuration_path, receipt_path, *, profile="development"):
    return [
        *development_arguments("verify-development-receipt", documents, configuration_path, profile=profile),
        "--receipt",
        str(receipt_path),
    ]


def assert_fixed_receipt_refusal(capsys, documents, configuration_path, receipt_path, *, expected=None):
    assert tool().main(verify_arguments(documents, configuration_path, receipt_path)) == 2
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["status"] == "FAILED" and result["output_complete"] is False
    allowed = (
        {"TASK_STRUCTURE_RECEIPT_INVALID", "TASK_STRUCTURE_RECEIPT_BINDING_INVALID"} if expected is None else {expected}
    )
    assert result["code"] in allowed
    assert str(receipt_path) not in captured.out + captured.err
    assert str(configuration_path) not in captured.out + captured.err
    return result


def test_structure_receipt_records_actual_material_snapshots_registry_and_observed_local_source(tmp_path):
    from business_app.contracts import SCHEMAS
    from business_app.task_creation_development import load_task_creation_development
    from business_app.task_creation_materials import CANONICALIZATION_VERSION, prepare_material_bundle

    documents, configuration_path, destination, receipt_path, result = prepared_receipt(tmp_path)
    settings = load_task_creation_development(configuration_path, runtime_profile="development")
    raw = tuple(documents[name].read_bytes() for name in ("policy", "plan", "capability", "input"))
    bundle = prepare_material_bundle(*raw, budgets=settings.material_budgets())
    receipt = json.loads(receipt_path.read_bytes())
    assert set(receipt) == {
        "schema_id",
        "schema_version",
        "canonicalization_version",
        "material_canonicalization_version",
        "status",
        "validator_protocol",
        "development_configuration",
        "materials",
        "node_inputs",
        "schema_registry",
        "observed_source_inventory",
        "limitations",
    }
    assert receipt["schema_version"] == "1.0.0"
    assert receipt["canonicalization_version"] == "task-structure-receipt-json-utf8-sortkeys-v1"
    assert receipt["material_canonicalization_version"] == CANONICALIZATION_VERSION
    assert receipt["validator_protocol"] == "offline-task-material-structure-validation-v1"
    assert receipt["development_configuration"] == result["development_configuration"]
    materials = (bundle.policy, bundle.plan, bundle.capability, bundle.inputs)
    expected_materials = [
        dict(
            kind=kind,
            schema_id=material.schema_id,
            document_id=material.document_id,
            document_version=material.version,
            canonicalization_version=material.canonicalization_version,
            source_sha256=hashlib.sha256(source).hexdigest(),
            source_size_bytes=len(source),
            canonical_sha256=hashlib.sha256(material.canonical_bytes).hexdigest(),
            canonical_size_bytes=len(material.canonical_bytes),
        )
        for kind, material, source in zip(("policy", "plan", "capability", "input"), materials, raw, strict=True)
    ]
    assert receipt["materials"] == expected_materials
    assert receipt["node_inputs"] == [
        dict(
            node_code=material.document_id,
            schema_id=material.schema_id,
            input_version=material.version,
            canonical_sha256=hashlib.sha256(material.canonical_bytes).hexdigest(),
            canonical_size_bytes=len(material.canonical_bytes),
        )
        for material in bundle.node_inputs
    ]
    assert receipt["schema_registry"] == dict(
        canonicalization_version="local-schema-registry-json-v1",
        sha256=hashlib.sha256(canonical(SCHEMAS)).hexdigest(),
        schema_count=len(SCHEMAS),
    )
    paths = sorted(
        [
            "backend/business_app/task_creation_receipt.py",
            "backend/business_app/task_creation_materials.py",
            "backend/business_app/task_creation_development.py",
            "backend/business_app/contracts.py",
            "scripts/task_creation_adoption.py",
        ]
    )
    assert receipt["observed_source_inventory"] == dict(
        semantics="LOCAL_SOURCE_BYTES_OBSERVED_NOT_EXECUTED_CODE_OR_RELEASE_ATTESTATION",
        files=[
            dict(
                path=path,
                sha256=hashlib.sha256((adoption.ROOT / path).read_bytes()).hexdigest(),
                size_bytes=(adoption.ROOT / path).stat().st_size,
            )
            for path in paths
        ],
    )
    assert receipt["limitations"] == {
        "adopted": False,
        "authority_verified": False,
        "licence_verified": False,
        "current_facts_verified": False,
        "handlers_executed": False,
        "database_written": False,
        "network_accessed": False,
        "task_created": False,
        "active_mapping_created": False,
    }
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700


def test_structure_receipt_pure_value_is_frozen_detached_and_bound_to_canonical_bytes(tmp_path):
    from business_app.task_creation_development import load_task_creation_development

    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    settings = load_task_creation_development(configuration_path, runtime_profile="development")
    raw = tuple(documents[name].read_bytes() for name in ("policy", "plan", "capability", "input"))
    value = receipt_module().create_structure_receipt(raw, settings)
    assert value.canonical_bytes == canonical(value.as_dict())
    assert value.sha256 == hashlib.sha256(value.canonical_bytes).hexdigest()
    assert receipt_module().verify_structure_receipt(value.canonical_bytes, raw, settings) == value
    exported = value.as_dict()
    exported["limitations"]["adopted"] = True
    exported["materials"].clear()
    assert value.as_dict()["limitations"]["adopted"] is False
    assert len(value.as_dict()["materials"]) == 4
    with pytest.raises(FrozenInstanceError):
        value.canonical_bytes = b"{}"


def test_receipt_flag_is_opt_in_and_unflagged_configured_output_remains_exactly_compatible(tmp_path):
    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    first, second = tmp_path / "one", tmp_path / "two"
    implicit = tool().run_development(
        "prepare-development", documents, configuration_path, runtime_profile="development", output=first
    )
    explicit = tool().run_development(
        "prepare-development",
        documents,
        configuration_path,
        runtime_profile="development",
        output=second,
        structure_receipt=False,
    )
    assert implicit == explicit
    assert implicit["artifact_count"] == 5 and "structure_receipt" not in implicit
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    assert not (first / "material-structure-receipt.json").exists()
    assert "structure_receipt" not in json.loads((first / "manifest.json").read_bytes())


def test_receipt_verification_never_writes_or_changes_materials_configuration_or_prepared_output(tmp_path, capsys):
    documents, configuration_path, destination, receipt_path, _ = prepared_receipt(tmp_path)
    paths = [*documents.values(), configuration_path, *destination.iterdir()]
    before = {path: path.read_bytes() for path in paths}
    entries = set(tmp_path.rglob("*"))
    assert tool().main(verify_arguments(documents, configuration_path, receipt_path)) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "STRUCTURE_RECEIPT_VERIFIED_NOT_ADOPTED"
    for name in (
        "output_written",
        "database_written",
        "network_accessed",
        "active_mapping_created",
        "task_created",
        "authority_or_license_verified",
    ):
        assert result[name] is False
    assert result.get("handlers_executed", False) is False
    assert before == {path: path.read_bytes() for path in paths}
    assert entries == set(tmp_path.rglob("*"))


@pytest.mark.parametrize("profile", ["development", "test"])
def test_receipt_profile_is_explicit_and_verified_with_the_same_configuration(tmp_path, capsys, profile):
    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    result = tool().run_development(
        "prepare-development",
        documents,
        configuration_path,
        runtime_profile=profile,
        output=destination,
        structure_receipt=True,
    )
    receipt_path = destination / "material-structure-receipt.json"
    assert tool().main(verify_arguments(documents, configuration_path, receipt_path, profile=profile)) == 0
    assert json.loads(capsys.readouterr().out)["development_configuration"] == result["development_configuration"]
    other = "test" if profile == "development" else "development"
    assert tool().main(verify_arguments(documents, configuration_path, receipt_path, profile=other)) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "TASK_STRUCTURE_RECEIPT_BINDING_INVALID"


@pytest.mark.parametrize("kind", ["policy", "plan", "capability", "input"])
def test_receipt_binds_actual_source_bytes_even_when_material_formatting_alone_changes(tmp_path, capsys, kind):
    documents, configuration_path, _, receipt_path, _ = prepared_receipt(tmp_path)
    original = documents[kind].read_bytes()
    documents[kind].write_bytes(original + b" ")
    assert canonical(json.loads(original)) == canonical(json.loads(documents[kind].read_bytes()))
    assert_fixed_receipt_refusal(
        capsys, documents, configuration_path, receipt_path, expected="TASK_STRUCTURE_RECEIPT_BINDING_INVALID"
    )


@pytest.mark.parametrize("change", ["revision", "unused_limit", "material_identity"])
def test_receipt_rejects_a_new_valid_configuration_or_material_identity(tmp_path, capsys, change):
    documents, configuration_path, _, receipt_path, _ = prepared_receipt(tmp_path)
    if change in {"revision", "unused_limit"}:
        configuration = json.loads(configuration_path.read_bytes())
        if change == "revision":
            configuration["task_creation_development"]["revision"] = "e04-other"
        else:
            configuration["task_creation_development"]["control_ttl_seconds"] -= 1
        configuration_path.write_bytes(canonical(configuration))
    else:
        value = json.loads(documents["input"].read_bytes())
        value["input_id"] = "self-owned/a-different-valid-input"
        documents["input"].write_bytes(canonical(value))
    assert_fixed_receipt_refusal(
        capsys, documents, configuration_path, receipt_path, expected="TASK_STRUCTURE_RECEIPT_BINDING_INVALID"
    )


@pytest.mark.parametrize(
    "change",
    [
        "validator",
        "schema_id",
        "schema_version",
        "canonicalization",
        "material_canonicalization",
        "status",
        "material_id",
        "material_version",
        "source_digest",
        "source_size",
        "canonical_digest",
        "canonical_size",
        "materials_order",
        "node_digest",
        "node_count",
        "registry_digest",
        "registry_count",
        "inventory_digest",
        "inventory_order",
        "counter",
        "enforced_limit",
        "configuration_digest",
    ],
)
def test_receipt_rejects_changed_identity_order_counters_validator_registry_or_inventory(tmp_path, capsys, change):
    documents, configuration_path, _, receipt_path, _ = prepared_receipt(tmp_path)
    value = json.loads(receipt_path.read_bytes())
    if change == "validator":
        value["validator_protocol"] = "self-owned-a-different-validator"
    elif change == "schema_id":
        value["schema_id"] = "urn:self-owned:different-schema"
    elif change == "schema_version":
        value["schema_version"] = "2.0.0"
    elif change == "canonicalization":
        value["canonicalization_version"] += "-other"
    elif change == "material_canonicalization":
        value["material_canonicalization_version"] += "-other"
    elif change == "status":
        value["status"] = "ADOPTED"
    elif change == "material_id":
        value["materials"][0]["document_id"] = "self-owned-other-material"
    elif change == "material_version":
        value["materials"][0]["document_version"] += "-other"
    elif change in {"source_digest", "canonical_digest"}:
        key = "source_sha256" if change == "source_digest" else "canonical_sha256"
        value["materials"][0][key] = "0" * 64
    elif change in {"source_size", "canonical_size"}:
        key = "source_size_bytes" if change == "source_size" else "canonical_size_bytes"
        value["materials"][0][key] += 1
    elif change == "materials_order":
        value["materials"][0], value["materials"][1] = value["materials"][1], value["materials"][0]
    elif change == "node_digest":
        value["node_inputs"][0]["canonical_sha256"] = "0" * 64
    elif change == "node_count":
        value["node_inputs"].append(dict(value["node_inputs"][0]))
    elif change == "registry_digest":
        value["schema_registry"]["sha256"] = "0" * 64
    elif change == "registry_count":
        value["schema_registry"]["schema_count"] += 1
    elif change == "inventory_digest":
        value["observed_source_inventory"]["files"][0]["sha256"] = "0" * 64
    elif change == "inventory_order":
        value["observed_source_inventory"]["files"].reverse()
    elif change == "counter":
        value["development_configuration"]["aggregate_bytes"]["node_snapshots"] += 1
    elif change == "enforced_limit":
        value["development_configuration"]["enforced_limits"]["max_nodes"] -= 1
    else:
        value["development_configuration"]["sha256"] = "0" * 64
    receipt_path.write_bytes(canonical(value))
    assert_fixed_receipt_refusal(capsys, documents, configuration_path, receipt_path)


def test_receipt_preserves_the_generated_node_snapshot_order(tmp_path, capsys):
    documents = configured_documents(tmp_path, adoption.amplified_snapshot_documents())
    configuration_path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    tool().run_development(
        "prepare-development",
        documents,
        configuration_path,
        runtime_profile="development",
        output=destination,
        structure_receipt=True,
    )
    receipt_path = destination / "material-structure-receipt.json"
    value = json.loads(receipt_path.read_bytes())
    assert len(value["node_inputs"]) == 4
    value["node_inputs"].reverse()
    receipt_path.write_bytes(canonical(value))
    assert_fixed_receipt_refusal(
        capsys, documents, configuration_path, receipt_path, expected="TASK_STRUCTURE_RECEIPT_BINDING_INVALID"
    )


@pytest.mark.parametrize(
    "location", ["root", "material", "node", "configuration", "registry", "inventory", "source_entry", "limitations"]
)
def test_receipt_rejects_unknown_fields_at_every_record_boundary(tmp_path, capsys, location):
    documents, configuration_path, _, receipt_path, _ = prepared_receipt(tmp_path)
    value = json.loads(receipt_path.read_bytes())
    targets = {
        "root": value,
        "material": value["materials"][0],
        "node": value["node_inputs"][0],
        "configuration": value["development_configuration"],
        "registry": value["schema_registry"],
        "inventory": value["observed_source_inventory"],
        "source_entry": value["observed_source_inventory"]["files"][0],
        "limitations": value["limitations"],
    }
    targets[location]["self_reported_authorized"] = True
    receipt_path.write_bytes(canonical(value))
    assert_fixed_receipt_refusal(capsys, documents, configuration_path, receipt_path)


@pytest.mark.parametrize(
    "field",
    [
        "adopted",
        "authority_verified",
        "licence_verified",
        "current_facts_verified",
        "handlers_executed",
        "database_written",
        "network_accessed",
        "task_created",
        "active_mapping_created",
    ],
)
@pytest.mark.parametrize("bad", [True, 0, 1, "false", None])
def test_receipt_never_accepts_self_reported_authority_or_coerced_false_flags(tmp_path, capsys, field, bad):
    documents, configuration_path, _, receipt_path, _ = prepared_receipt(tmp_path)
    value = json.loads(receipt_path.read_bytes())
    value["limitations"][field] = bad
    receipt_path.write_bytes(canonical(value))
    assert_fixed_receipt_refusal(capsys, documents, configuration_path, receipt_path)


@pytest.mark.parametrize(
    "defect",
    [
        "whitespace",
        "pretty",
        "root_duplicate",
        "nested_duplicate",
        "nan",
        "infinity",
        "invalid_utf8",
        "empty",
        "array",
        "null",
        "surrogate",
    ],
)
def test_receipt_requires_unique_strict_json_and_exact_canonical_source_bytes(tmp_path, capsys, defect):
    documents, configuration_path, _, receipt_path, _ = prepared_receipt(tmp_path)
    raw = receipt_path.read_bytes()
    if defect == "whitespace":
        raw += b"\n"
    elif defect == "pretty":
        raw = json.dumps(json.loads(raw), indent=2).encode()
    elif defect == "root_duplicate":
        raw = b'{"status":"MATERIAL_STRUCTURE_VALIDATED_NOT_ADOPTED",' + raw[1:]
    elif defect == "nested_duplicate":
        raw = raw.replace(b'"adopted":false', b'"adopted":false,"adopted":false', 1)
    elif defect == "nan":
        raw = raw.replace(b'"schema_count":', b'"self_owned":NaN,"schema_count":', 1)
    elif defect == "infinity":
        raw = raw.replace(b'"schema_count":', b'"self_owned":Infinity,"schema_count":', 1)
    elif defect == "invalid_utf8":
        raw = b"\xff"
    elif defect == "empty":
        raw = b""
    elif defect == "array":
        raw = b"[]"
    elif defect == "null":
        raw = b"null"
    else:
        raw = b'{"self_owned":"\\ud800"}'
    receipt_path.write_bytes(raw)
    assert_fixed_receipt_refusal(
        capsys, documents, configuration_path, receipt_path, expected="TASK_STRUCTURE_RECEIPT_INVALID"
    )


def test_receipt_oversize_is_refused_by_its_own_budget_without_echoing_bytes(tmp_path, capsys):
    documents, configuration_path, _, receipt_path, _ = prepared_receipt(tmp_path)
    receipt_path.write_bytes(b"x" * 262145)
    assert_fixed_receipt_refusal(
        capsys, documents, configuration_path, receipt_path, expected="TASK_STRUCTURE_RECEIPT_BUDGET_EXCEEDED"
    )


def test_source_inventory_closes_all_opened_descriptors_when_close_reports_failure(monkeypatch):
    module = receipt_module()
    original_open, original_close, original_fstat = os.open, os.close, os.fstat
    opened, closed = [], []
    private_marker = "SELF_OWNED_SOURCE_CLOSE_FAULT_DO_NOT_ECHO"

    def tracked_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def close_then_report_failure(descriptor):
        closed.append(descriptor)
        original_close(descriptor)
        if len(closed) == 1:
            raise OSError(private_marker)

    with monkeypatch.context() as context:
        context.setattr(module.os, "open", tracked_open)
        context.setattr(module.os, "close", close_then_report_failure)
        try:
            with pytest.raises(ValueError, match="^TASK_STRUCTURE_RECEIPT_INVENTORY_UNAVAILABLE$") as error:
                module._source_observation(module.SOURCE_PATHS[0])
            assert private_marker not in str(error.value)
            assert len(opened) > 1
            assert closed == list(reversed(opened))
            for descriptor in opened:
                with pytest.raises(OSError):
                    original_fstat(descriptor)
        finally:
            # The pre-fix implementation leaks its newly opened child when the
            # preceding close fails. Do not leave that descriptor in the suite.
            for descriptor in reversed(opened):
                try:
                    original_fstat(descriptor)
                except OSError:
                    continue
                original_close(descriptor)


@pytest.mark.parametrize("action", ["prepare-development", "verify-development-receipt"])
def test_receipt_config_and_material_paths_are_read_once_from_a_single_frozen_configuration(
    tmp_path, monkeypatch, action
):
    from business_app import task_creation_development

    documents, configuration_path, destination, receipt_path, initial = prepared_receipt(tmp_path)
    originals = {path: path.read_bytes() for path in documents.values()}
    original_configuration = json.loads(configuration_path.read_bytes())
    expected_sha = initial["development_configuration"]["sha256"]
    loader = task_creation_development.load_task_creation_development
    reader = tool()._read_material
    loads, reads = [], []

    def counted_loader(*args, **kwargs):
        loads.append(True)
        return loader(*args, **kwargs)

    def changing_reader(path, maximum):
        reads.append(path)
        result = reader(path, maximum)
        if path == documents["policy"]:
            configuration = json.loads(canonical(original_configuration))
            configuration["task_creation_development"]["revision"] = "e04-after-freeze"
            configuration_path.write_bytes(canonical(configuration))
            if action == "prepare-development":
                path.write_bytes(result + b" ")
        return result

    monkeypatch.setattr(task_creation_development, "load_task_creation_development", counted_loader)
    monkeypatch.setattr(tool(), "_read_material", changing_reader)
    if action == "prepare-development":
        output = destination.with_name("second-prepared")
        result = tool().run_development(
            action, documents, configuration_path, runtime_profile="development", output=output, structure_receipt=True
        )
        receipt = json.loads((output / "material-structure-receipt.json").read_bytes())
        assert receipt["materials"][0]["source_sha256"] == hashlib.sha256(originals[documents["policy"]]).hexdigest()
    else:
        result = tool().run_development(
            action, documents, configuration_path, runtime_profile="development", receipt_path=receipt_path
        )
        assert reads.count(receipt_path) == 1
    assert result["development_configuration"]["sha256"] == expected_sha
    assert loads == [True]
    assert all(reads.count(path) == 1 for path in documents.values())
    assert len(reads) == (4 if action == "prepare-development" else 5)


@pytest.mark.parametrize(
    "defect",
    [
        "missing_receipt",
        "output",
        "flag",
        "max_bytes",
        "max_nodes",
        "max_capabilities",
        "production",
        "legacy_flag",
        "validate_flag",
    ],
)
def test_receipt_cli_refuses_invalid_argument_mixtures_before_configuration_or_material_io(
    tmp_path, monkeypatch, capsys, defect
):
    from business_app import task_creation_development

    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    receipt_path = tmp_path / "not-read.json"
    arguments = verify_arguments(documents, configuration_path, receipt_path)
    if defect == "missing_receipt":
        index = arguments.index("--receipt")
        del arguments[index : index + 2]
    elif defect == "output":
        arguments.extend(["--output", str(tmp_path / "not-created")])
    elif defect == "flag":
        arguments.append("--structure-receipt")
    elif defect in {"max_bytes", "max_nodes", "max_capabilities"}:
        arguments.extend(["--" + defect.replace("_", "-"), "4"])
    elif defect == "production":
        arguments[arguments.index("--runtime-profile") + 1] = "production"
    elif defect == "legacy_flag":
        arguments = adoption.arguments(
            "prepare", documents, dict(max_bytes=262144, max_nodes=16, max_capabilities=64), tmp_path / "not-created"
        )
        arguments.append("--structure-receipt")
    else:
        arguments = [
            *development_arguments("validate-development", documents, configuration_path),
            "--structure-receipt",
        ]
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Invalid argument mixtures must fail before configuration or material reads")

    monkeypatch.setattr(task_creation_development, "load_task_creation_development", forbidden)
    monkeypatch.setattr(tool(), "_read_material", forbidden)
    with pytest.raises(SystemExit) as error:
        tool().main(arguments)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert "TASK_PREPARATION_ARGUMENT_INVALID" in captured.err
    assert str(configuration_path) not in captured.out + captured.err
    assert str(receipt_path) not in captured.out + captured.err
    assert calls == []
    assert not (tmp_path / "not-created").exists()


@pytest.mark.parametrize(
    "defect",
    [
        "validate_flag",
        "verify_flag",
        "prepare_receipt",
        "verify_missing_receipt",
        "verify_output",
        "integer_flag",
        "string_receipt",
    ],
)
def test_receipt_direct_api_refuses_invalid_action_flag_receipt_and_output_combinations(tmp_path, monkeypatch, defect):
    from business_app import task_creation_development

    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    action, kwargs = "prepare-development", dict(output=tmp_path / "not-created", structure_receipt=True)
    if defect == "validate_flag":
        action, kwargs = "validate-development", dict(structure_receipt=True)
    elif defect == "verify_flag":
        action, kwargs = (
            "verify-development-receipt",
            dict(receipt_path=tmp_path / "not-read.json", structure_receipt=True),
        )
    elif defect == "prepare_receipt":
        kwargs["receipt_path"] = tmp_path / "not-read.json"
    elif defect == "verify_missing_receipt":
        action, kwargs = "verify-development-receipt", {}
    elif defect == "verify_output":
        action = "verify-development-receipt"
        kwargs.update(receipt_path=tmp_path / "not-read.json", structure_receipt=False)
    elif defect == "integer_flag":
        kwargs["structure_receipt"] = 1
    else:
        action, kwargs = "verify-development-receipt", dict(receipt_path="not-a-Path")
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Invalid direct arguments must fail before reads or output")

    monkeypatch.setattr(task_creation_development, "load_task_creation_development", forbidden)
    monkeypatch.setattr(tool(), "_read_material", forbidden)
    with pytest.raises(tool().PreparationError, match="^TASK_PREPARATION_ARGUMENT_INVALID$"):
        tool().run_development(action, documents, configuration_path, runtime_profile="development", **kwargs)
    assert calls == []
    assert not (tmp_path / "not-created").exists()


def test_structure_receipt_must_fit_its_own_limit_before_any_output_is_created(tmp_path, monkeypatch, capsys):
    documents = configured_documents(tmp_path)
    configuration = adoption.bounded_development_configuration(documents)
    configuration_path = private_development_configuration(tmp_path, configuration)
    assert (
        tool().run_development("validate-development", documents, configuration_path, runtime_profile="development")[
            "status"
        ]
        == "VALIDATED_OFFLINE_NOT_ADOPTED"
    )
    writes = adoption.assert_no_configured_output_write(tool(), monkeypatch)
    destination = tmp_path / "not-created"
    assert (
        tool().main(
            [
                *development_arguments("prepare-development", documents, configuration_path, destination),
                "--structure-receipt",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert json.loads(captured.out)["code"] == "TASK_STRUCTURE_RECEIPT_BUDGET_EXCEEDED"
    assert writes == []
    assert not destination.exists()


def test_structure_receipt_own_byte_limit_accepts_equality_and_refuses_one_byte_more(tmp_path):
    from business_app.task_creation_development import parse_task_creation_development

    documents = configured_documents(tmp_path)
    raw = tuple(documents[name].read_bytes() for name in ("policy", "plan", "capability", "input"))
    limit = 16000
    for _ in range(6):
        configuration = adoption.development_configuration(
            max_material_bytes=limit,
            max_nodes=1,
            max_capabilities=1,
            max_bundle_bytes=limit,
            max_snapshots_bytes=limit,
            max_http_body_bytes=min(limit, 16384),
        )
        settings = parse_task_creation_development(canonical(configuration), runtime_profile="development")
        receipt = receipt_module().create_structure_receipt(raw, settings)
        size = len(receipt.canonical_bytes)
        if size == limit:
            break
        limit = size
    assert len(receipt.canonical_bytes) == settings.max_material_bytes
    configuration["task_creation_development"].update(
        max_material_bytes=limit - 1,
        max_bundle_bytes=limit - 1,
        max_snapshots_bytes=limit - 1,
        max_http_body_bytes=min(limit - 1, 16384),
    )
    smaller = parse_task_creation_development(canonical(configuration), runtime_profile="development")
    with pytest.raises(ValueError, match="^TASK_STRUCTURE_RECEIPT_BUDGET_EXCEEDED$"):
        receipt_module().create_structure_receipt(raw, smaller)


@pytest.mark.parametrize("action", ["prepare-development", "verify-development-receipt"])
def test_unavailable_fixed_source_inventory_fails_closed_and_does_not_echo_the_os_error(
    tmp_path, monkeypatch, capsys, action
):
    documents, configuration_path, destination, receipt_path, _ = prepared_receipt(tmp_path)
    module = receipt_module()
    original_open = module.os.open
    marker = "SELF_OWNED_SOURCE_INVENTORY_FAULT_DO_NOT_ECHO"

    def missing_fixed_source(path, flags, *args, **kwargs):
        if path == "task_creation_receipt.py":
            raise OSError(marker)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", missing_fixed_source)
    output = destination.with_name("not-created")
    arguments = (
        [*development_arguments(action, documents, configuration_path, output), "--structure-receipt"]
        if action == "prepare-development"
        else verify_arguments(documents, configuration_path, receipt_path)
    )
    assert tool().main(arguments) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["code"] == "TASK_STRUCTURE_RECEIPT_INVENTORY_UNAVAILABLE"
    assert marker not in captured.out + captured.err
    assert str(output) not in captured.out + captured.err
    assert not output.exists()


def test_structure_receipt_preparation_and_verification_do_not_connect_or_import_handlers(tmp_path, monkeypatch):
    import builtins

    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    receipt_module()
    attempts = []
    original_import = builtins.__import__

    def forbidden(*args, **kwargs):
        attempts.append("FORBIDDEN_IO")
        raise AssertionError("Structure receipt is offline and must not execute a handler")

    def no_handler_import(name, *args, **kwargs):
        if "original_integrity" in name or name == "internal-rnd-original-integrity":
            return forbidden()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(builtins, "__import__", no_handler_import)
    for name, attribute in (("psycopg", "connect"), ("sqlalchemy", "create_engine")):
        module = sys.modules.get(name)
        if module is not None:
            monkeypatch.setattr(module, attribute, forbidden)
    destination = tmp_path / "prepared"
    prepared = tool().run_development(
        "prepare-development",
        documents,
        configuration_path,
        runtime_profile="development",
        output=destination,
        structure_receipt=True,
    )
    verified = tool().run_development(
        "verify-development-receipt",
        documents,
        configuration_path,
        runtime_profile="development",
        receipt_path=destination / "material-structure-receipt.json",
    )
    assert prepared["status"] == "PREPARED_OFFLINE_NOT_ADOPTED"
    assert verified["status"] == "STRUCTURE_RECEIPT_VERIFIED_NOT_ADOPTED"
    assert attempts == []


@pytest.mark.parametrize(
    "test_name,extra",
    [
        ("test_prepare_is_deterministic_and_does_not_modify_inputs", {}),
        ("test_existing_output_is_never_overwritten", {"kind": "empty_directory"}),
        ("test_existing_output_is_never_overwritten", {"kind": "existing_file"}),
        ("test_existing_output_is_never_overwritten", {"kind": "populated_directory"}),
        ("test_output_must_be_external_to_repository", {"candidate": "inside"}),
        ("test_output_must_be_external_to_repository", {"candidate": "ancestor"}),
        ("test_relative_paths_are_rejected", {"kind": "input"}),
        ("test_relative_paths_are_rejected", {"kind": "output"}),
        ("test_input_symlink_is_never_followed", {"kind": "leaf"}),
        ("test_input_symlink_is_never_followed", {"kind": "parent"}),
        ("test_output_symlink_is_never_followed", {"kind": "leaf"}),
        ("test_output_symlink_is_never_followed", {"kind": "parent"}),
        ("test_fifo_input_is_rejected_without_blocking", {}),
        ("test_partial_failure_removes_only_created_files_and_own_empty_directory", {}),
        ("test_cleanup_preserves_unknown_files_and_never_follows_them", {"kind": "file"}),
        ("test_cleanup_preserves_unknown_files_and_never_follows_them", {"kind": "symlink"}),
        ("test_exclusive_file_creation_rejects_a_planted_link_without_touching_target", {}),
        ("test_parent_path_replacement_cannot_redirect_writes_or_cleanup", {}),
        ("test_partial_os_writes_are_completed_before_success", {}),
        ("test_zero_byte_write_is_a_failure_with_no_partial_result", {}),
        ("test_no_network_database_or_material_code_execution", {}),
        ("test_missing_secure_descriptor_primitives_fail_closed", {}),
    ],
)
def test_structure_receipt_output_reuses_existing_safety_assertions_without_changing_them(
    tmp_path, monkeypatch, test_name, extra
):
    original_run_development = tool().run_development

    def with_structure_receipt(action, *args, **kwargs):
        kwargs["structure_receipt"] = action == "prepare-development"
        return original_run_development(action, *args, **kwargs)

    monkeypatch.setattr(tool(), "run_development", with_structure_receipt)
    adoption.test_configured_output_reuses_the_unchanged_existing_safety_assertions(
        tmp_path, monkeypatch, test_name, extra
    )


def test_structure_receipt_two_processes_cannot_overwrite_the_same_complete_output(tmp_path):
    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    command = [
        sys.executable,
        str(adoption.ROOT / "scripts/task_creation_adoption.py"),
        *development_arguments("prepare-development", documents, configuration_path, destination),
        "--structure-receipt",
    ]
    first = subprocess.Popen(command, cwd=adoption.ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = subprocess.Popen(command, cwd=adoption.ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        outputs = [process.communicate(timeout=30) for process in (first, second)]
    finally:
        for process in (first, second):
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
    assert sorted(process.returncode for process in (first, second)) == [0, 2]
    results = [json.loads(stdout) for stdout, _ in outputs]
    assert {result["status"] for result in results} == {"PREPARED_OFFLINE_NOT_ADOPTED", "FAILED"}
    manifest = json.loads((destination / "manifest.json").read_bytes())
    assert {path.name for path in destination.iterdir()} == {row["filename"] for row in manifest["artifacts"]} | {
        "manifest.json",
        "material-structure-receipt.json",
    }
    receipt_raw = (destination / "material-structure-receipt.json").read_bytes()
    assert hashlib.sha256(receipt_raw).hexdigest() == manifest["structure_receipt"]["sha256"]
    assert all(str(configuration_path).encode() not in stdout + stderr for stdout, stderr in outputs)


def test_structure_receipt_output_write_failure_is_redacted_and_cleans_only_its_partial_output(
    tmp_path, monkeypatch, capsys
):
    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    destination = tmp_path / "not-created"
    original_write = tool()._write_exclusive
    marker = "SELF_OWNED_RECEIPT_WRITE_FAULT_DO_NOT_ECHO"

    def fail_after_receipt_write(directory, name, raw, created):
        original_write(directory, name, raw, created)
        if name == "material-structure-receipt.json":
            raise OSError(marker)

    monkeypatch.setattr(tool(), "_write_exclusive", fail_after_receipt_write)
    arguments = [
        *development_arguments("prepare-development", documents, configuration_path, destination),
        "--structure-receipt",
    ]
    assert tool().main(arguments) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out) == dict(
        status="FAILED", code="TASK_PREPARATION_LOCAL_OR_MATERIAL_INVALID", output_complete=False
    )
    assert marker not in captured.out + captured.err
    assert str(destination) not in captured.out + captured.err
    assert not destination.exists()


@pytest.mark.parametrize("kind", ["leaf", "parent"])
def test_receipt_verification_refuses_symlink_input_without_changing_the_target(tmp_path, capsys, kind):
    documents, configuration_path, destination, receipt_path, _ = prepared_receipt(tmp_path)
    before = receipt_path.read_bytes()
    link = tmp_path / "receipt-link"
    link.symlink_to(receipt_path if kind == "leaf" else destination, target_is_directory=kind == "parent")
    selected = link if kind == "leaf" else link / receipt_path.name
    assert tool().main(verify_arguments(documents, configuration_path, selected)) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["status"] == "FAILED"
    assert str(selected) not in captured.out + captured.err
    assert receipt_path.read_bytes() == before


def test_source_inventory_refuses_non_linux_before_opening_source(monkeypatch):
    module = receipt_module()
    calls = []

    def forbidden_open(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Non-Linux inventory must fail before opening a descriptor")

    with monkeypatch.context() as context:
        context.setattr(module.sys, "platform", "darwin")
        context.setattr(module.os, "open", forbidden_open)
        with pytest.raises(ValueError, match="^TASK_STRUCTURE_RECEIPT_INVENTORY_UNAVAILABLE$"):
            module._source_observation(module.SOURCE_PATHS[0])
    assert calls == []


@pytest.mark.parametrize(
    "relative", ["../outside.py", "/self-owned/absolute.py", "backend/business_app/../contracts.py"]
)
def test_source_inventory_never_reads_a_caller_supplied_alias_outside_the_fixed_list(monkeypatch, relative):
    module = receipt_module()
    calls = []

    def forbidden_open(*args, **kwargs):
        calls.append(True)
        raise AssertionError("An inventory alias must be refused before opening a descriptor")

    monkeypatch.setattr(module.os, "open", forbidden_open)
    with pytest.raises(ValueError, match="^TASK_STRUCTURE_RECEIPT_INVENTORY_UNAVAILABLE$"):
        module._source_observation(relative)
    assert calls == []


@pytest.mark.parametrize(
    "defect", ["leaf_symlink", "parent_symlink", "fifo", "empty", "oversize", "changed_during_read"]
)
def test_fixed_source_inventory_rejects_actual_unsafe_self_owned_files(tmp_path, monkeypatch, defect):
    module = receipt_module()
    root = tmp_path / "source-root"
    source = root / module.SOURCE_PATHS[0]
    source.parent.mkdir(parents=True)
    source.write_bytes(b"# Self-owned source observation fixture only.\n")
    monkeypatch.setattr(module, "ROOT", root)
    if defect == "leaf_symlink":
        moved = source.with_name("self-owned-target.py")
        source.rename(moved)
        source.symlink_to(moved)
    elif defect == "parent_symlink":
        parent = source.parent
        moved = parent.with_name("moved-source")
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
    elif defect == "fifo":
        source.unlink()
        os.mkfifo(source)
    elif defect == "empty":
        source.write_bytes(b"")
    elif defect == "oversize":
        source.write_bytes(b"x" * 1048577)
    else:
        original_read = os.read
        changed = False

        def changed_read(descriptor, size):
            nonlocal changed
            block = original_read(descriptor, size)
            if not changed:
                changed = True
                with source.open("ab") as stream:
                    stream.write(b"# changed\n")
            return block

        monkeypatch.setattr(module.os, "read", changed_read)
    with pytest.raises(ValueError, match="^TASK_STRUCTURE_RECEIPT_INVENTORY_UNAVAILABLE$"):
        module._source_observation(module.SOURCE_PATHS[0])


@pytest.mark.parametrize("defect", ["list", "missing", "extra", "text", "mutable_bytes"])
def test_receipt_creation_requires_four_actual_immutable_raw_byte_inputs(tmp_path, defect):
    from business_app.task_creation_development import load_task_creation_development

    documents = configured_documents(tmp_path)
    configuration_path = private_development_configuration(tmp_path)
    settings = load_task_creation_development(configuration_path, runtime_profile="development")
    # Deliberately replace the valid tuple with inputs of invalid runtime types.
    raw: Any = tuple(documents[name].read_bytes() for name in ("policy", "plan", "capability", "input"))
    if defect == "list":
        raw = list(raw)
    elif defect == "missing":
        raw = raw[:-1]
    elif defect == "extra":
        raw += (raw[0],)
    elif defect == "text":
        raw = (raw[0].decode(), *raw[1:])
    else:
        raw = (bytearray(raw[0]), *raw[1:])
    with pytest.raises(ValueError, match="^TASK_STRUCTURE_RECEIPT_INVALID$"):
        receipt_module().create_structure_receipt(raw, settings)
