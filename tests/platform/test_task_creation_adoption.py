"""Offline Linux material preparation against self-owned documents; no database fixtures."""

import hashlib
import importlib
import json
import os
import socket
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def material_documents():
    """Private transport/build fixtures only; no valid adoption or real handler registration."""
    uri = "urn:media-trace:api:0.1.0#/$defs/ObjectRef"
    handler = dict(
        handler_id="self-owned/ref-copy",
        handler_version="1",
        release_id="60000000-0000-4000-8000-000000000001",
        code_sha256="c" * 64,
        package_sha256="d" * 64,
    )
    capability = dict(
        schema_id="urn:media-trace:task-capability-manifest:1.0.0",
        schema_version="1.0.0",
        capability_id="self-owned/capabilities",
        capability_version="1",
        handlers=[
            dict(
                **handler,
                input_schema_id=uri,
                output_schema_id=uri,
                license_ref="self-owned-fixture/license",
                status_protocol_version="self-owned/current-status/1",
                model_dependencies=[],
            )
        ],
    )
    bindings = [
        dict(field_path=field, source="asset", selector="asset.object_ref." + field)
        for field in ["object_id", "version_id", "sha256"]
    ]
    plan = dict(
        schema_id="urn:media-trace:task-execution-plan:1.0.0",
        schema_version="1.0.0",
        plan_id="self-owned/plan",
        plan_version="1",
        scene="accident_rumor",
        modules=["INGEST", "RESOURCE"],
        priority="normal",
        policy_version="self-owned/policy/1",
        capability=dict(
            capability_id=capability["capability_id"],
            capability_version=capability["capability_version"],
            capability_sha256=hashlib.sha256(canonical(capability)).hexdigest(),
        ),
        nodes=[
            dict(
                node_code="retain_ref",
                dependencies=[],
                required=True,
                missing_policy="FAIL_REQUIRED",
                handler=handler,
                model_dependencies=[],
                input_schema_id=uri,
                output_schema_id=uri,
                input_bindings=bindings,
                preprocessing_version="self-owned/identity/1",
                postprocessing_version="self-owned/identity/1",
                output_refs=["result"],
                dispatch_protocol_version="self-owned/task-dispatch/1",
            )
        ],
    )
    values = {"self_owned_fixture": True}
    digest = hashlib.sha256(canonical(values)).hexdigest()
    policy = dict(definition_ref="urn:sha256:" + digest, version=plan["policy_version"], sha256=digest, values=values)
    reference = dict(object_id="80000000-0000-4000-8000-000000000001", version_id="self-owned/fixed/1", sha256="a" * 64)
    inputs = dict(
        schema_id="urn:media-trace:task-input-manifest:1.0.0",
        schema_version="1.0.0",
        input_id="self-owned/input",
        input_version="1",
        plan_id=plan["plan_id"],
        plan_version=plan["plan_version"],
        plan_sha256=hashlib.sha256(canonical(plan)).hexdigest(),
        asset=dict(
            asset_id="70000000-0000-4000-8000-000000000001",
            sha256="a" * 64,
            object_ref=reference,
            source_authorization_version="self-owned/source-auth/1",
        ),
        nodes=[
            dict(
                node_code="retain_ref",
                inputs=[
                    dict(**binding, materialized=True, value=reference[binding["field_path"]]) for binding in bindings
                ],
            )
        ],
    )
    return dict(policy=policy, plan=plan, capability=capability, input=inputs)


def tool():
    return importlib.import_module("scripts.task_creation_adoption")


@pytest.fixture
def documents(tmp_path):
    directory = tmp_path / "inputs"
    directory.mkdir()
    paths = {}
    for name, value in material_documents().items():
        paths[name] = directory / (name + ".json")
        paths[name].write_bytes(json.dumps(value, indent=2).encode())
    return paths


@pytest.fixture
def limits():
    return dict(max_bytes=32768, max_nodes=4, max_capabilities=4)


def arguments(action, documents, limits, output=None):
    values = [action]
    for name, path in documents.items():
        values.extend(["--" + name, str(path)])
    for name, value in limits.items():
        values.extend(["--" + name.replace("_", "-"), str(value)])
    if output is not None:
        values.extend(["--output", str(output)])
    return values


def test_validate_real_materials_changes_no_files_or_authority(documents, limits, tmp_path, capsys):
    before = {path: path.read_bytes() for path in documents.values()}
    assert tool().main(arguments("validate", documents, limits)) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "VALIDATED_OFFLINE_NOT_ADOPTED" and result["artifact_count"] == 5
    assert not any(
        result[name]
        for name in [
            "output_written",
            "database_written",
            "network_accessed",
            "active_mapping_created",
            "task_created",
            "authority_or_license_verified",
        ]
    )
    assert set(tmp_path.iterdir()) == {tmp_path / "inputs"}
    assert before == {path: path.read_bytes() for path in documents.values()}


def test_prepare_writes_exclusive_private_canonical_materials_and_manifest(documents, limits, tmp_path):
    destination = tmp_path / "prepared"
    result = tool().run("prepare", documents, limits, destination)
    assert result["status"] == "PREPARED_OFFLINE_NOT_ADOPTED"
    manifest_bytes = (destination / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert hashlib.sha256(manifest_bytes).hexdigest() == result["manifest_sha256"]
    assert manifest_bytes == canonical(manifest)
    assert set(path.name for path in destination.iterdir()) == {row["filename"] for row in manifest["artifacts"]} | {
        "manifest.json"
    }
    assert len(manifest["artifacts"]) == result["artifact_count"] == 5
    for row in manifest["artifacts"]:
        path = destination / row["filename"]
        raw = path.read_bytes()
        assert len(raw) == row["size_bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
        assert raw == canonical(json.loads(raw))
        assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
    assert stat.S_IMODE(destination.stat().st_mode) & 0o077 == 0
    assert not any(
        manifest[name]
        for name in [
            "database_written",
            "network_accessed",
            "active_mapping_created",
            "task_created",
            "handlers_executed",
            "authority_or_license_verified",
        ]
    )


def test_prepare_is_deterministic_and_does_not_modify_inputs(documents, limits, tmp_path):
    before = {name: path.read_bytes() for name, path in documents.items()}
    first = tool().run("prepare", documents, limits, tmp_path / "one")
    second = tool().run("prepare", documents, limits, tmp_path / "two")
    assert first == second
    assert before == {name: path.read_bytes() for name, path in documents.items()}
    assert {p.name: p.read_bytes() for p in (tmp_path / "one").iterdir()} == {
        p.name: p.read_bytes() for p in (tmp_path / "two").iterdir()
    }


@pytest.mark.parametrize("kind", ["empty_directory", "existing_file", "populated_directory"])
def test_existing_output_is_never_overwritten(documents, limits, tmp_path, kind):
    destination = tmp_path / "existing"
    if kind == "existing_file":
        destination.write_text("self-owned-preserved")
    else:
        destination.mkdir()
        if kind == "populated_directory":
            (destination / "keep").write_text("self-owned-preserved")
    before = (
        destination.read_bytes() if destination.is_file() else {p.name: p.read_bytes() for p in destination.iterdir()}
    )
    with pytest.raises(tool().PreparationError, match="OUTPUT_ALREADY_EXISTS"):
        tool().run("prepare", documents, limits, destination)
    after = (
        destination.read_bytes() if destination.is_file() else {p.name: p.read_bytes() for p in destination.iterdir()}
    )
    assert before == after


@pytest.mark.parametrize("candidate", ["inside", "ancestor"])
def test_output_must_be_external_to_repository(documents, limits, candidate):
    module = tool()
    path = ROOT / "must-not-create-task-materials" if candidate == "inside" else ROOT.parent
    with pytest.raises(module.PreparationError, match="EXTERNAL_OUTPUT_REQUIRED"):
        module.run("prepare", documents, limits, path)
    assert not (ROOT / "must-not-create-task-materials").exists()


@pytest.mark.parametrize("kind", ["input", "output"])
def test_relative_paths_are_rejected(documents, limits, tmp_path, kind):
    module = tool()
    if kind == "input":
        documents["policy"] = Path("relative-policy.json")
    output = Path("relative-prepared") if kind == "output" else tmp_path / "prepared"
    with pytest.raises(module.PreparationError, match="ABSOLUTE_PATH_REQUIRED"):
        module.run("prepare", documents, limits, output)
    assert not (tmp_path / "prepared").exists()


@pytest.mark.parametrize("kind", ["leaf", "parent"])
def test_input_symlink_is_never_followed(documents, limits, tmp_path, kind):
    link = tmp_path / "input-link"
    link.symlink_to(
        documents["policy"] if kind == "leaf" else documents["policy"].parent, target_is_directory=kind == "parent"
    )
    documents["policy"] = link if kind == "leaf" else link / documents["policy"].name
    with pytest.raises(OSError):
        tool().run("prepare", documents, limits, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()


@pytest.mark.parametrize("kind", ["leaf", "parent"])
def test_output_symlink_is_never_followed(documents, limits, tmp_path, kind):
    target = tmp_path / "protected"
    target.mkdir()
    (target / "keep").write_text("self-owned-do-not-change")
    link = tmp_path / "output-link"
    link.symlink_to(target, target_is_directory=True)
    output = link if kind == "leaf" else link / "prepared"
    with pytest.raises((OSError, tool().PreparationError)):
        tool().run("prepare", documents, limits, output)
    assert {p.name: p.read_text() for p in target.iterdir()} == {"keep": "self-owned-do-not-change"}


def test_fifo_input_is_rejected_without_blocking(documents, limits, tmp_path):
    fifo = tmp_path / "not-a-regular-file"
    os.mkfifo(fifo)
    documents["policy"] = fifo
    with pytest.raises(tool().PreparationError, match="REGULAR_INPUT_REQUIRED"):
        tool().run("prepare", documents, limits, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()


def test_budget_is_checked_before_reading_oversized_input(documents, limits, tmp_path):
    documents["policy"].write_bytes(b"x" * 33)
    limits["max_bytes"] = 32
    with pytest.raises(tool().PreparationError, match="BUDGET_EXCEEDED"):
        tool().run("prepare", documents, limits, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()


@pytest.mark.parametrize("value", [True, 0, -1, 1.5])
def test_no_implicit_or_invalid_budget_is_accepted(documents, limits, tmp_path, value):
    limits["max_nodes"] = value
    with pytest.raises(tool().PreparationError, match="LIMIT_INVALID"):
        tool().run("prepare", documents, limits, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()


def test_invalid_material_does_not_leak_input_or_create_output(documents, limits, tmp_path, capsys):
    marker = "SELF_OWNED_DO_NOT_PUBLISH_INPUT_OR_PATH"
    documents["policy"].write_text('{"private": "' + marker)
    assert tool().main(arguments("prepare", documents, limits, tmp_path / "prepared")) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["status"] == "FAILED"
    assert marker not in captured.out + captured.err and str(tmp_path) not in captured.out + captured.err
    assert not (tmp_path / "prepared").exists()


@pytest.mark.parametrize("mode", ["missing-budget", "activation-command", "unexpected-argument"])
def test_cli_rejects_missing_budgets_and_any_activation_command(documents, limits, tmp_path, capsys, mode):
    args = arguments("prepare", documents, limits, tmp_path / "prepared")
    if mode == "missing-budget":
        index = args.index("--max-nodes")
        del args[index : index + 2]
    elif mode == "activation-command":
        args[0] = "activate"
    else:
        args.extend(["--database-dsn", "SELF_OWNED_NEVER_LOG_THIS_ARGUMENT"])
    with pytest.raises(SystemExit) as error:
        tool().main(args)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert "TASK_PREPARATION_ARGUMENT_INVALID" in captured.err
    assert "SELF_OWNED_NEVER_LOG_THIS_ARGUMENT" not in captured.out + captured.err
    assert not (tmp_path / "prepared").exists()


def test_partial_failure_removes_only_created_files_and_own_empty_directory(documents, limits, tmp_path, monkeypatch):
    module = tool()
    destination = tmp_path / "prepared"
    original = module._write_exclusive
    calls = 0

    def fail(directory, name, raw, created):
        nonlocal calls
        calls += 1
        original(directory, name, raw, created)
        if calls == 2:
            raise OSError("SELF_OWNED_INJECTED_WRITE_FAILURE")

    monkeypatch.setattr(module, "_write_exclusive", fail)
    with pytest.raises(OSError):
        module.run("prepare", documents, limits, destination)
    assert not destination.exists()
    assert set(tmp_path.iterdir()) == {tmp_path / "inputs"}


@pytest.mark.parametrize("kind", ["file", "symlink"])
def test_cleanup_preserves_unknown_files_and_never_follows_them(documents, limits, tmp_path, monkeypatch, kind):
    module = tool()
    destination = tmp_path / "prepared"
    keeper = tmp_path / "keep"
    keeper.write_text("self-owned-preserved")
    original = module._write_exclusive

    def fail(directory, name, raw, created):
        original(directory, name, raw, created)
        if kind == "file":
            (destination / "foreign").write_text("self-owned-unknown")
        else:
            (destination / "foreign").symlink_to(keeper)
        raise OSError("SELF_OWNED_INJECTED_WRITE_FAILURE")

    monkeypatch.setattr(module, "_write_exclusive", fail)
    with pytest.raises(OSError):
        module.run("prepare", documents, limits, destination)
    assert {path.name for path in destination.iterdir()} == {"foreign"}
    assert keeper.read_text() == "self-owned-preserved"
    assert (
        (destination / "foreign").is_symlink()
        if kind == "symlink"
        else (destination / "foreign").read_text() == "self-owned-unknown"
    )


def test_exclusive_file_creation_rejects_a_planted_link_without_touching_target(
    documents, limits, tmp_path, monkeypatch
):
    module = tool()
    destination = tmp_path / "prepared"
    keeper = tmp_path / "keep"
    keeper.write_text("self-owned-preserved")
    original = module._write_exclusive

    def planted(directory, name, raw, created):
        (destination / name).symlink_to(keeper)
        original(directory, name, raw, created)

    monkeypatch.setattr(module, "_write_exclusive", planted)
    with pytest.raises(FileExistsError):
        module.run("prepare", documents, limits, destination)
    assert keeper.read_text() == "self-owned-preserved"
    assert [p.name for p in destination.iterdir()] == ["policy.canonical.json"]
    assert (destination / "policy.canonical.json").is_symlink()


def test_parent_path_replacement_cannot_redirect_writes_or_cleanup(documents, limits, tmp_path, monkeypatch):
    module = tool()
    parent = tmp_path / "parent"
    parent.mkdir()
    moved = tmp_path / "moved"
    target = tmp_path / "target"
    target.mkdir()
    (target / "keep").write_text("self-owned-preserved")
    destination = parent / "prepared"
    original = module._write_exclusive
    replaced = False

    def replace(directory, name, raw, created):
        nonlocal replaced
        original(directory, name, raw, created)
        if not replaced:
            parent.rename(moved)
            parent.symlink_to(target, target_is_directory=True)
            replaced = True

    monkeypatch.setattr(module, "_write_exclusive", replace)
    with pytest.raises(OSError):
        module.run("prepare", documents, limits, destination)
    assert parent.is_symlink() and not (moved / "prepared").exists()
    assert {p.name: p.read_text() for p in target.iterdir()} == {"keep": "self-owned-preserved"}


def test_partial_os_writes_are_completed_before_success(documents, limits, tmp_path, monkeypatch):
    original = os.write
    monkeypatch.setattr(os, "write", lambda descriptor, raw: original(descriptor, raw[:7]))
    destination = tmp_path / "prepared"
    tool().run("prepare", documents, limits, destination)
    manifest = json.loads((destination / "manifest.json").read_bytes())
    assert all(
        hashlib.sha256((destination / row["filename"]).read_bytes()).hexdigest() == row["sha256"]
        for row in manifest["artifacts"]
    )


def test_zero_byte_write_is_a_failure_with_no_partial_result(documents, limits, tmp_path, monkeypatch):
    monkeypatch.setattr(os, "write", lambda descriptor, raw: 0)
    destination = tmp_path / "prepared"
    with pytest.raises(tool().PreparationError, match="WRITE_INCOMPLETE"):
        tool().run("prepare", documents, limits, destination)
    assert not destination.exists()


def test_two_processes_cannot_overwrite_the_same_preparation(documents, limits, tmp_path):
    destination = tmp_path / "prepared"
    command = [
        sys.executable,
        str(ROOT / "scripts/task_creation_adoption.py"),
        *arguments("prepare", documents, limits, destination),
    ]
    first = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        outputs = [process.communicate(timeout=30) for process in [first, second]]
    finally:
        for process in [first, second]:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
    assert sorted(process.returncode for process in [first, second]) == [0, 2]
    results = [json.loads(stdout) for stdout, _ in outputs]
    assert {result["status"] for result in results} == {"PREPARED_OFFLINE_NOT_ADOPTED", "FAILED"}
    manifest = json.loads((destination / "manifest.json").read_bytes())
    assert len(list(destination.iterdir())) == len(manifest["artifacts"]) + 1


def test_no_network_database_or_material_code_execution(documents, limits, tmp_path, monkeypatch):
    # Load fixed local modules before installing hostile-I/O sentinels.
    tool().run("validate", documents, limits)
    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append("FORBIDDEN_IO")
        raise AssertionError("OFFLINE_PREPARATION_MUST_NOT_CONNECT")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    for name, attribute in [("psycopg", "connect"), ("sqlalchemy", "create_engine")]:
        module = sys.modules.get(name)
        if module is not None:
            monkeypatch.setattr(module, attribute, forbidden)
    result = tool().run("prepare", documents, limits, tmp_path / "prepared")
    assert result["status"] == "PREPARED_OFFLINE_NOT_ADOPTED" and attempts == []


def test_missing_secure_descriptor_primitives_fail_closed(documents, limits, tmp_path, monkeypatch):
    module = tool()
    monkeypatch.setattr(module, "_DESCRIPTOR_IO", False)
    with pytest.raises(module.PreparationError, match="SECURE_LINUX_IO_REQUIRED"):
        module.run("prepare", documents, limits, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()


def configured_documents(tmp_path, values=None):
    values = material_documents() if values is None else values
    for handler in values["capability"]["handlers"]:
        handler["handler_id"] = "internal-rnd-original-integrity"
    for node in values["plan"]["nodes"]:
        node["handler"]["handler_id"] = "internal-rnd-original-integrity"
    rebind_configured_documents(values)
    directory = tmp_path / "configured-inputs"
    directory.mkdir(mode=0o700)
    paths = {}
    for name, value in values.items():
        paths[name] = directory / (name + ".json")
        paths[name].write_bytes(canonical(value))
    return paths


def rebind_configured_documents(values):
    values["plan"]["capability"]["capability_sha256"] = hashlib.sha256(canonical(values["capability"])).hexdigest()
    values["input"]["plan_sha256"] = hashlib.sha256(canonical(values["plan"])).hexdigest()


def development_configuration(**changes):
    values = dict(
        schema_version="1.0.0",
        environment="linux-py311-cpu-internal-rnd",
        revision="e04-v1",
        allowed_handler_ids=["internal-rnd-original-integrity"],
        max_material_bytes=262144,
        max_nodes=16,
        max_capabilities=64,
        max_bundle_bytes=1048576,
        max_snapshots_bytes=4194304,
        max_http_body_bytes=16384,
        proof_budget_seconds=30,
        control_ttl_seconds=86400,
        adoption_max_seconds=604800,
        generation_max_age_seconds=30,
        capability_lease_seconds=60,
        node_lease_seconds=60,
        max_object_bytes=1048576,
        handler_deadline_seconds=10,
        db_connect_timeout_seconds=2,
        db_pool_timeout_seconds=2,
        db_statement_timeout_ms=2000,
        db_lock_timeout_ms=1000,
        create_deadline_seconds=10,
        max_concurrent_handlers=1,
        prefetch_count=1,
        max_task_temp_bytes=8388608,
        max_incomplete_temp_tasks=2,
        min_free_space_bytes=5368709120,
    )
    values.update(changes)
    return {"task_creation_development": values}


def private_development_configuration(tmp_path, values=None, *, filename="development.json"):
    directory = tmp_path / "private-configuration"
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / filename
    path.write_bytes(canonical(development_configuration() if values is None else values))
    path.chmod(0o600)
    return path


def development_arguments(action, documents, configuration_path, output=None, *, profile="development"):
    result = [action, "--runtime-profile", profile, "--development-config", str(configuration_path)]
    for name, path in documents.items():
        result.extend(["--" + name, str(path)])
    if output is not None:
        result.extend(["--output", str(output)])
    return result


def expected_development_binding(documents, configuration, *, profile="development"):
    from business_app.task_creation_materials import MaterialBudgets, prepare_material_bundle

    values = configuration["task_creation_development"]
    raw = [documents[name].read_bytes() for name in ("policy", "plan", "capability", "input")]
    bundle = prepare_material_bundle(
        *raw,
        budgets=MaterialBudgets(values["max_material_bytes"], values["max_nodes"], values["max_capabilities"]),
    )
    return dict(
        runtime_profile=profile,
        environment=values["environment"],
        revision=values["revision"],
        canonicalization_version="task-creation-development-json-v1",
        sha256=hashlib.sha256(
            canonical(
                dict(
                    runtime_profile=profile,
                    canonicalization_version="task-creation-development-json-v1",
                    configuration=configuration,
                )
            )
        ).hexdigest(),
        aggregate_bytes=dict(
            source_documents=sum(map(len, raw)),
            canonical_documents=sum(
                len(material.canonical_bytes)
                for material in (bundle.policy, bundle.plan, bundle.capability, bundle.inputs)
            ),
            node_snapshots=sum(len(material.canonical_bytes) for material in bundle.node_inputs),
        ),
        enforced_limits={
            name: values[name]
            for name in (
                "max_material_bytes",
                "max_nodes",
                "max_capabilities",
                "max_bundle_bytes",
                "max_snapshots_bytes",
                "allowed_handler_ids",
            )
        },
    )


def test_configured_prepare_uses_explicit_private_configuration_and_actual_budgets(tmp_path, capsys):
    documents = configured_documents(tmp_path)
    configuration = development_configuration()
    configuration_path = private_development_configuration(tmp_path, configuration)
    destination = tmp_path / "configured-prepared"
    assert tool().main(development_arguments("prepare-development", documents, configuration_path, destination)) == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    manifest_bytes = (destination / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    expected = expected_development_binding(documents, configuration)
    assert result["status"] == "PREPARED_OFFLINE_NOT_ADOPTED"
    assert manifest["status"] == "OFFLINE_MATERIALS_ONLY_NOT_ADOPTED"
    assert result["development_configuration"] == manifest["development_configuration"] == expected
    assert hashlib.sha256(manifest_bytes).hexdigest() == result["manifest_sha256"]
    assert manifest_bytes == canonical(manifest)
    assert len(manifest["artifacts"]) == result["artifact_count"] == 5
    assert not any(
        manifest[name]
        for name in (
            "database_written",
            "network_accessed",
            "active_mapping_created",
            "task_created",
            "handlers_executed",
            "authority_or_license_verified",
        )
    )
    assert str(configuration_path) not in captured.out + captured.err
    assert str(documents["input"]) not in captured.out + captured.err
    for row in manifest["artifacts"]:
        path = destination / row["filename"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        assert len(path.read_bytes()) == row["size_bytes"]
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700


def bounded_development_configuration(documents, *, max_bundle_bytes=None, max_snapshots_bytes=None):
    binding = expected_development_binding(documents, development_configuration())
    largest = max(len(path.read_bytes()) for path in documents.values())
    # The complete base parser validates these real materials before the tighter
    # aggregate boundary is exercised. Each snapshot is independently bounded.
    from business_app.task_creation_materials import MaterialBudgets, prepare_material_bundle

    bundle = prepare_material_bundle(
        *(documents[name].read_bytes() for name in ("policy", "plan", "capability", "input")),
        budgets=MaterialBudgets(262144, 16, 64),
    )
    largest = max(
        largest,
        *(len(material.canonical_bytes) for material in (bundle.policy, bundle.plan, bundle.capability, bundle.inputs)),
        *(len(material.canonical_bytes) for material in bundle.node_inputs),
    )
    counts = binding["aggregate_bytes"]
    return development_configuration(
        max_material_bytes=largest,
        max_nodes=len(bundle.node_inputs),
        max_capabilities=1,
        max_http_body_bytes=min(largest, 16384),
        max_bundle_bytes=max(counts["source_documents"], counts["canonical_documents"])
        if max_bundle_bytes is None
        else max_bundle_bytes,
        max_snapshots_bytes=max(largest, counts["node_snapshots"])
        if max_snapshots_bytes is None
        else max_snapshots_bytes,
    )


def assert_no_configured_output_write(module, monkeypatch):
    calls = []

    def forbidden_save(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Aggregate or configuration rejection must precede output creation")

    monkeypatch.setattr(module, "_save_prepared", forbidden_save)
    return calls


@pytest.mark.parametrize("excess", [0, 1])
def test_configured_source_aggregate_boundary_uses_all_four_valid_documents(tmp_path, monkeypatch, excess):
    documents = configured_documents(tmp_path)
    # Make source bytes distinct from their smaller canonical representation.
    documents["policy"].write_bytes(documents["policy"].read_bytes() + b" " * 8)
    total = sum(len(path.read_bytes()) for path in documents.values())
    configuration = bounded_development_configuration(documents, max_bundle_bytes=total - excess)
    path = private_development_configuration(tmp_path, configuration)
    destination = tmp_path / "prepared"
    assert all(
        len(material.read_bytes()) <= configuration["task_creation_development"]["max_material_bytes"]
        for material in documents.values()
    )
    if excess:
        module = tool()
        writes = assert_no_configured_output_write(module, monkeypatch)
        with pytest.raises(module.PreparationError, match="^TASK_PREPARATION_BUNDLE_BUDGET_EXCEEDED$"):
            module.run_development(
                "prepare-development", documents, path, runtime_profile="development", output=destination
            )
        assert writes == []
        assert not destination.exists()
    else:
        result = tool().run_development(
            "prepare-development", documents, path, runtime_profile="development", output=destination
        )
        assert result["development_configuration"]["aggregate_bytes"]["source_documents"] == total
        assert destination.is_dir()


@pytest.mark.parametrize("excess", [0, 1])
def test_configured_canonical_aggregate_expansion_has_a_separate_equal_and_plus_one_boundary(
    tmp_path, monkeypatch, excess
):
    values = material_documents()
    values["policy"]["values"]["canonical_expansion"] = 100.0
    digest = hashlib.sha256(canonical(values["policy"]["values"])).hexdigest()
    values["policy"].update(sha256=digest, definition_ref="urn:sha256:" + digest)
    documents = configured_documents(tmp_path, values)
    policy = documents["policy"].read_bytes()
    assert policy.count(b'"canonical_expansion":100.0') == 1
    documents["policy"].write_bytes(policy.replace(b'"canonical_expansion":100.0', b'"canonical_expansion":1e2'))
    counts = expected_development_binding(documents, development_configuration())["aggregate_bytes"]
    assert counts["canonical_documents"] == counts["source_documents"] + 2
    configuration = bounded_development_configuration(
        documents, max_bundle_bytes=counts["canonical_documents"] - excess
    )
    path = private_development_configuration(tmp_path, configuration)
    destination = tmp_path / "prepared"
    assert counts["source_documents"] <= configuration["task_creation_development"]["max_bundle_bytes"]
    if excess:
        module = tool()
        writes = assert_no_configured_output_write(module, monkeypatch)
        with pytest.raises(module.PreparationError, match="^TASK_PREPARATION_BUNDLE_BUDGET_EXCEEDED$"):
            module.run_development(
                "prepare-development", documents, path, runtime_profile="development", output=destination
            )
        assert writes == []
        assert not destination.exists()
    else:
        result = tool().run_development(
            "prepare-development", documents, path, runtime_profile="development", output=destination
        )
        assert result["development_configuration"]["aggregate_bytes"] == counts
        assert destination.is_dir()


def amplified_snapshot_documents():
    values = material_documents()
    reference = values["input"]["asset"]["object_ref"]
    reference["version_id"] = "v" * 128
    values["input"]["asset"]["source_authorization_version"] = "s" * 128
    values["input"]["input_id"] = "i" * 128
    first_plan = values["plan"]["nodes"][0]
    first_inputs = values["input"]["nodes"][0]
    values["plan"]["nodes"] = []
    values["input"]["nodes"] = []
    for index in range(4):
        node = json.loads(canonical(first_plan))
        inputs = json.loads(canonical(first_inputs))
        node["node_code"] = inputs["node_code"] = f"retain_{index}"
        for item in inputs["inputs"]:
            item["value"] = reference[item["field_path"]]
        values["plan"]["nodes"].append(node)
        values["input"]["nodes"].append(inputs)
    return values


@pytest.mark.parametrize("excess", [0, 1])
def test_configured_snapshot_aggregate_counts_every_valid_node_copy(tmp_path, monkeypatch, excess):
    documents = configured_documents(tmp_path, amplified_snapshot_documents())
    counts = expected_development_binding(documents, development_configuration())["aggregate_bytes"]
    configuration = bounded_development_configuration(documents, max_snapshots_bytes=counts["node_snapshots"] - excess)
    values = configuration["task_creation_development"]
    assert values["max_nodes"] == 4
    assert values["max_material_bytes"] < counts["node_snapshots"] - 1
    path = private_development_configuration(tmp_path, configuration)
    destination = tmp_path / "prepared"
    if excess:
        module = tool()
        writes = assert_no_configured_output_write(module, monkeypatch)
        with pytest.raises(module.PreparationError, match="^TASK_PREPARATION_SNAPSHOT_BUDGET_EXCEEDED$"):
            module.run_development(
                "prepare-development", documents, path, runtime_profile="development", output=destination
            )
        assert writes == []
        assert not destination.exists()
    else:
        result = tool().run_development(
            "prepare-development", documents, path, runtime_profile="development", output=destination
        )
        manifest = json.loads((destination / "manifest.json").read_bytes())
        snapshots = [row for row in manifest["artifacts"] if row["kind"] == "node_input"]
        assert len(snapshots) == 4
        assert sum(row["size_bytes"] for row in snapshots) == counts["node_snapshots"]
        assert result["development_configuration"]["aggregate_bytes"] == counts


def test_configured_validate_writes_nothing_and_legacy_manifest_bytes_keep_their_shape(tmp_path):
    documents = configured_documents(tmp_path)
    configuration = development_configuration()
    path = private_development_configuration(tmp_path, configuration)
    before = {material: material.read_bytes() for material in documents.values()}
    result = tool().run_development("validate-development", documents, path, runtime_profile="development")
    assert result["status"] == "VALIDATED_OFFLINE_NOT_ADOPTED" and not result["output_written"]
    assert set(tmp_path.iterdir()) == {tmp_path / "configured-inputs", tmp_path / "private-configuration"}
    legacy = tmp_path / "legacy"
    configured = tmp_path / "configured"
    tool().run("prepare", documents, dict(max_bytes=262144, max_nodes=16, max_capabilities=64), legacy)
    tool().run_development("prepare-development", documents, path, runtime_profile="development", output=configured)
    legacy_bytes = (legacy / "manifest.json").read_bytes()
    old_manifest = json.loads(legacy_bytes)
    new_manifest = json.loads((configured / "manifest.json").read_bytes())
    assert "development_configuration" not in old_manifest
    del new_manifest["development_configuration"]
    assert canonical(new_manifest) == legacy_bytes
    assert before == {material: material.read_bytes() for material in documents.values()}
    assert {p.name: p.read_bytes() for p in legacy.iterdir() if p.name != "manifest.json"} == {
        p.name: p.read_bytes() for p in configured.iterdir() if p.name != "manifest.json"
    }


@pytest.mark.parametrize("change", ["format", "profile", "revision", "unused_limit"])
def test_configured_manifest_binds_profile_and_complete_frozen_configuration(tmp_path, change):
    documents = configured_documents(tmp_path)
    original = development_configuration()
    path = private_development_configuration(tmp_path, original)
    first_output = tmp_path / "one"
    second_output = tmp_path / "two"
    first = tool().run_development(
        "prepare-development", documents, path, runtime_profile="development", output=first_output
    )
    changed = development_configuration()
    profile = "development"
    if change == "format":
        path.write_bytes(json.dumps(changed, indent=4).encode())
    elif change == "profile":
        profile = "test"
    elif change == "revision":
        changed["task_creation_development"]["revision"] = "e04-v2"
        path.write_bytes(canonical(changed))
    else:
        changed["task_creation_development"]["control_ttl_seconds"] -= 1
        path.write_bytes(canonical(changed))
    second = tool().run_development(
        "prepare-development", documents, path, runtime_profile=profile, output=second_output
    )
    assert second["development_configuration"] == expected_development_binding(documents, changed, profile=profile)
    if change == "format":
        assert first == second
        assert (first_output / "manifest.json").read_bytes() == (second_output / "manifest.json").read_bytes()
    else:
        assert first["development_configuration"]["sha256"] != second["development_configuration"]["sha256"]
    assert [row["sha256"] for row in json.loads((first_output / "manifest.json").read_bytes())["artifacts"]] == [
        row["sha256"] for row in json.loads((second_output / "manifest.json").read_bytes())["artifacts"]
    ]


def test_configured_action_loads_configuration_once_and_never_rereads_material_paths(tmp_path, monkeypatch):
    from business_app import task_creation_development

    documents = configured_documents(tmp_path)
    original = development_configuration()
    path = private_development_configuration(tmp_path, original)
    expected = expected_development_binding(documents, original)
    loads, reads = [], []
    loader = task_creation_development.load_task_creation_development
    reader = tool()._read_material

    def counted_loader(*args, **kwargs):
        loads.append(True)
        return loader(*args, **kwargs)

    def changing_reader(material, maximum):
        reads.append(material)
        result = reader(material, maximum)
        if len(reads) == 1:
            path.write_bytes(canonical(development_configuration(revision="e04-after-freeze")))
        return result

    monkeypatch.setattr(task_creation_development, "load_task_creation_development", counted_loader)
    monkeypatch.setattr(tool(), "_read_material", changing_reader)
    result = tool().run_development("validate-development", documents, path, runtime_profile="development")
    assert result["development_configuration"] == expected
    assert loads == [True]
    assert reads == [documents[name] for name in ("policy", "plan", "capability", "input")]


@pytest.mark.parametrize(
    "defect,expected",
    [
        ("invalid_json", "TASK_CREATION_DEVELOPMENT_CONFIG_INVALID"),
        ("profile_override", "TASK_CREATION_DEVELOPMENT_CONFIG_INVALID"),
        ("public_file", "TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED"),
        ("public_parent", "TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED"),
        ("symlink", "TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED"),
        ("missing", "TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED"),
    ],
)
def test_configured_cli_refuses_bad_configuration_before_material_io_or_output(
    tmp_path, monkeypatch, capsys, defect, expected
):
    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    if defect == "invalid_json":
        path.write_text('{"self_owned_private_marker":')
    elif defect == "profile_override":
        values = development_configuration()
        values["runtime_profile"] = "production"
        path.write_bytes(canonical(values))
    elif defect == "public_file":
        path.chmod(0o644)
    elif defect == "public_parent":
        path.parent.chmod(0o755)
    elif defect == "symlink":
        link = path.with_name("link.json")
        link.symlink_to(path)
        path = link
    else:
        path = path.with_name("missing.json")
    module = tool()
    writes = assert_no_configured_output_write(module, monkeypatch)
    reads = []

    def forbidden_read(*args, **kwargs):
        reads.append(True)
        raise AssertionError("Invalid development configuration must precede material I/O")

    monkeypatch.setattr(module, "_read_material", forbidden_read)
    destination = tmp_path / "prepared"
    assert module.main(development_arguments("prepare-development", documents, path, destination)) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["code"] == expected
    assert str(path) not in captured.out + captured.err
    assert "self_owned_private_marker" not in captured.out + captured.err
    assert reads == writes == []
    assert not destination.exists()


@pytest.mark.parametrize(
    "defect", ["missing_profile", "missing_configuration", "production", "max_bytes", "max_nodes", "max_capabilities"]
)
def test_configured_cli_has_one_explicit_configuration_source_and_no_numeric_overrides(tmp_path, capsys, defect):
    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    arguments = development_arguments("prepare-development", documents, path, destination)
    if defect in {"missing_profile", "missing_configuration"}:
        option = "--runtime-profile" if defect == "missing_profile" else "--development-config"
        index = arguments.index(option)
        del arguments[index : index + 2]
    elif defect == "production":
        arguments[arguments.index("--runtime-profile") + 1] = "production"
    else:
        arguments.extend(["--" + defect.replace("_", "-"), "16"])
    with pytest.raises(SystemExit) as error:
        tool().main(arguments)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert "TASK_PREPARATION_ARGUMENT_INVALID" in captured.err
    assert str(path) not in captured.out + captured.err
    assert not destination.exists()


def test_configured_direct_production_profile_is_refused_before_material_io(tmp_path, monkeypatch):
    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    module = tool()
    reads = []

    def forbidden_read(*args, **kwargs):
        reads.append(True)
        raise AssertionError("Production profile must fail before material I/O")

    monkeypatch.setattr(module, "_read_material", forbidden_read)
    with pytest.raises(ValueError, match="^TASK_CREATION_DEVELOPMENT_PROFILE_NOT_APPROVED$"):
        module.run_development("validate-development", documents, path, runtime_profile="production")
    assert reads == []


@pytest.mark.parametrize(
    "handler_id", ["self-owned/ref-copy", "business_app.handlers.original_integrity", "subprocess.Popen"]
)
def test_configured_material_handler_ids_remain_data_and_must_match_allowlist(tmp_path, monkeypatch, handler_id):
    import builtins

    documents = configured_documents(tmp_path)
    values = {name: json.loads(path.read_bytes()) for name, path in documents.items()}
    values["capability"]["handlers"][0]["handler_id"] = handler_id
    values["plan"]["nodes"][0]["handler"]["handler_id"] = handler_id
    rebind_configured_documents(values)
    for name, value in values.items():
        documents[name].write_bytes(canonical(value))
    # Independently confirm all cross-material bindings before the allowlist refusal.
    expected_development_binding(documents, development_configuration())
    path = private_development_configuration(tmp_path)
    module = tool()
    imports = []
    original_import = builtins.__import__
    original_import_module = importlib.import_module

    def forbidden_import(name, *args, **kwargs):
        if name == handler_id:
            imports.append(name)
            raise AssertionError("Material-supplied handler ID must not be imported")
        return original_import(name, *args, **kwargs)

    def forbidden_import_module(name, *args, **kwargs):
        if name == handler_id:
            imports.append(name)
            raise AssertionError("Material-supplied handler ID must not be imported")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    monkeypatch.setattr(importlib, "import_module", forbidden_import_module)
    writes = assert_no_configured_output_write(module, monkeypatch)
    destination = tmp_path / "prepared"
    with pytest.raises(module.PreparationError, match="^TASK_PREPARATION_HANDLER_NOT_ALLOWED$"):
        module.run_development(
            "prepare-development", documents, path, runtime_profile="development", output=destination
        )
    assert imports == writes == []
    assert not destination.exists()


@pytest.mark.parametrize(
    "test_name,extra",
    [
        ("test_prepare_writes_exclusive_private_canonical_materials_and_manifest", {}),
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
def test_configured_output_reuses_the_unchanged_existing_safety_assertions(tmp_path, monkeypatch, test_name, extra):
    import inspect

    scenario = tmp_path / "scenario"
    scenario.mkdir(mode=0o700)
    documents = configured_documents(scenario)
    (scenario / "configured-inputs").rename(scenario / "inputs")
    documents = {name: scenario / "inputs" / path.name for name, path in documents.items()}
    configuration_path = private_development_configuration(tmp_path)
    module = tool()

    def configured_run(action, paths, limits, output=None):
        # Existing assertions execute the real configured call chain; limits are
        # legacy-test inputs only and never override the private configuration.
        return module.run_development(
            action + "-development", paths, configuration_path, runtime_profile="development", output=output
        )

    monkeypatch.setattr(module, "run", configured_run)
    target = globals()[test_name]
    available = dict(
        documents=documents,
        limits=dict(max_bytes=262144, max_nodes=16, max_capabilities=64),
        tmp_path=scenario,
        monkeypatch=monkeypatch,
        **extra,
    )
    target(**{name: available[name] for name in inspect.signature(target).parameters})


def test_configured_two_processes_cannot_overwrite_the_same_preparation(tmp_path):
    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    command = [
        sys.executable,
        str(ROOT / "scripts/task_creation_adoption.py"),
        *development_arguments("prepare-development", documents, path, destination),
    ]
    first = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
    assert len(list(destination.iterdir())) == len(manifest["artifacts"]) + 1
    assert manifest["development_configuration"] == expected_development_binding(documents, development_configuration())
    assert all(str(path).encode() not in stdout + stderr for stdout, stderr in outputs)


def test_configured_invalid_material_safe_error_never_writes_output_or_echoes_input(tmp_path, capsys):
    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    marker = "SELF_OWNED_CONFIGURED_INPUT_DO_NOT_ECHO"
    documents["policy"].write_text('{"private": "' + marker)
    destination = tmp_path / "prepared"
    assert tool().main(development_arguments("prepare-development", documents, path, destination)) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["status"] == "FAILED"
    assert marker not in captured.out + captured.err
    assert str(tmp_path) not in captured.out + captured.err
    assert not destination.exists()


def test_configured_aggregate_refusal_preserves_an_existing_destination(tmp_path, monkeypatch):
    documents = configured_documents(tmp_path)
    total = sum(len(path.read_bytes()) for path in documents.values())
    configuration = bounded_development_configuration(documents, max_bundle_bytes=total - 1)
    path = private_development_configuration(tmp_path, configuration)
    destination = tmp_path / "protected"
    destination.mkdir(mode=0o700)
    (destination / "keep").write_text("self-owned-preserved")
    module = tool()
    writes = assert_no_configured_output_write(module, monkeypatch)
    with pytest.raises(module.PreparationError, match="^TASK_PREPARATION_BUNDLE_BUDGET_EXCEEDED$"):
        module.run_development(
            "prepare-development", documents, path, runtime_profile="development", output=destination
        )
    assert writes == []
    assert {p.name: p.read_text() for p in destination.iterdir()} == {"keep": "self-owned-preserved"}


def test_configured_allowed_handler_does_not_import_or_execute_a_reserved_handler(tmp_path, monkeypatch):
    import builtins

    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    expected_development_binding(documents, development_configuration())
    module = tool()
    attempts = []
    original_import = builtins.__import__
    original_import_module = importlib.import_module

    def forbidden_import(name, *args, **kwargs):
        if "original_integrity" in name or name == "internal-rnd-original-integrity":
            attempts.append(name)
            raise AssertionError("Offline preparation must not import or execute a reserved handler")
        return original_import(name, *args, **kwargs)

    def forbidden_import_module(name, *args, **kwargs):
        if "original_integrity" in name or name == "internal-rnd-original-integrity":
            attempts.append(name)
            raise AssertionError("Offline preparation must not import or execute a reserved handler")
        return original_import_module(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    monkeypatch.setattr(importlib, "import_module", forbidden_import_module)
    destination = tmp_path / "prepared"
    result = module.run_development(
        "prepare-development", documents, path, runtime_profile="development", output=destination
    )
    manifest = json.loads((destination / "manifest.json").read_bytes())
    assert result["status"] == "PREPARED_OFFLINE_NOT_ADOPTED"
    assert attempts == []
    assert not manifest["handlers_executed"] and not manifest["authority_or_license_verified"]


@pytest.mark.parametrize(
    "defect", ["action", "missing_kind", "extra_kind", "non_path", "missing_output", "unexpected_output"]
)
def test_configured_direct_arguments_have_no_implicit_action_paths_or_output(tmp_path, defect):
    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    action = "prepare-development"
    output = tmp_path / "prepared"
    if defect == "action":
        action = "activate"
    elif defect == "missing_kind":
        del documents["input"]
    elif defect == "extra_kind":
        documents["unexpected"] = documents["input"]
    elif defect == "non_path":
        documents["input"] = str(documents["input"])
    elif defect == "missing_output":
        output = None
    else:
        action = "validate-development"
    with pytest.raises(tool().PreparationError, match="^TASK_PREPARATION_ARGUMENT_INVALID$"):
        tool().run_development(action, documents, path, runtime_profile="development", output=output)
    assert not (tmp_path / "prepared").exists()


def test_configured_cli_safely_redacts_an_output_fault_and_removes_its_partial_output(tmp_path, monkeypatch, capsys):
    documents = configured_documents(tmp_path)
    path = private_development_configuration(tmp_path)
    destination = tmp_path / "prepared"
    module = tool()
    original = module._write_exclusive
    marker = "SELF_OWNED_CONFIGURED_WRITE_FAULT_DO_NOT_ECHO"

    def fail_after_actual_write(directory, name, raw, created):
        original(directory, name, raw, created)
        raise OSError(marker)

    monkeypatch.setattr(module, "_write_exclusive", fail_after_actual_write)
    assert module.main(development_arguments("prepare-development", documents, path, destination)) == 2
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result == dict(status="FAILED", code="TASK_PREPARATION_LOCAL_OR_MATERIAL_INVALID", output_complete=False)
    assert marker not in captured.out + captured.err
    assert str(tmp_path) not in captured.out + captured.err
    assert not destination.exists()
