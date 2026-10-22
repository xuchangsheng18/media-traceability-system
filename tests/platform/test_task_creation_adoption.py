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
