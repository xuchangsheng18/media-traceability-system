"""Explicit internal-development configuration; never authority or live adoption."""

import copy
import hashlib
import importlib
import importlib.util
import json
import os
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

CONFIG_INVALID = "TASK_CREATION_DEVELOPMENT_CONFIG_INVALID"
PROFILE_INVALID = "TASK_CREATION_DEVELOPMENT_PROFILE_NOT_APPROVED"
PRIVATE_REQUIRED = "TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED"
LIMITS = {
    "max_material_bytes": 262144,
    "max_nodes": 16,
    "max_capabilities": 64,
    "max_bundle_bytes": 1048576,
    "max_snapshots_bytes": 4194304,
    "max_http_body_bytes": 16384,
    "proof_budget_seconds": 30,
    "control_ttl_seconds": 86400,
    "adoption_max_seconds": 604800,
    "generation_max_age_seconds": 30,
    "capability_lease_seconds": 60,
    "node_lease_seconds": 60,
    "max_object_bytes": 1048576,
    "handler_deadline_seconds": 10,
    "db_connect_timeout_seconds": 2,
    "db_pool_timeout_seconds": 2,
    "db_statement_timeout_ms": 2000,
    "db_lock_timeout_ms": 1000,
    "create_deadline_seconds": 10,
    "max_concurrent_handlers": 1,
    "prefetch_count": 1,
    "max_task_temp_bytes": 8388608,
    "max_incomplete_temp_tasks": 2,
    "min_free_space_bytes": 5368709120,
}


def configuration():
    return {
        "task_creation_development": {
            "schema_version": "1.0.0",
            "environment": "linux-py311-cpu-internal-rnd",
            "revision": "e04-v1",
            "allowed_handler_ids": ["internal-rnd-original-integrity"],
            **LIMITS,
        }
    }


def raw_configuration(document=None):
    return json.dumps(configuration() if document is None else document, ensure_ascii=False, allow_nan=False).encode(
        "utf8"
    )


def parse(document=None, *, profile="development"):
    return module().parse_task_creation_development(raw_configuration(document), runtime_profile=profile)


def private_config(tmp_path, *, raw=None):
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    path = folder / "task-creation.json"
    path.write_bytes(raw_configuration() if raw is None else raw)
    path.chmod(0o600)
    return path


def assert_config_invalid(document):
    with pytest.raises(ValueError, match=f"^{CONFIG_INVALID}$"):
        module().parse_task_creation_development(
            json.dumps(document, ensure_ascii=False, allow_nan=False).encode("utf8"), runtime_profile="development"
        )


def module():
    assert importlib.util.find_spec("business_app.task_creation_development") is not None, (
        "Task creation development configuration boundary is not implemented"
    )
    return importlib.import_module("business_app.task_creation_development")


def test_development_configuration_component_is_available_without_default_authority():
    value = module()
    assert callable(value.parse_task_creation_development)
    assert callable(value.load_task_creation_development)


@pytest.mark.parametrize("profile", ["development", "test"])
def test_explicit_approved_profile_carries_exact_e04_values_without_authority(profile):
    value = parse(profile=profile)
    assert type(value) is module().TaskCreationDevelopmentSettings
    assert value.runtime_profile == profile
    for name, expected in LIMITS.items():
        assert type(getattr(value, name)) is int
        assert getattr(value, name) == expected
    assert value.schema_version == "1.0.0"
    assert value.environment == "linux-py311-cpu-internal-rnd"
    assert value.revision == "e04-v1"
    assert value.allowed_handler_ids == ("internal-rnd-original-integrity",)
    assert not any(hasattr(value, name) for name in ("authorized", "active", "adopted", "executable", "authority"))
    from business_app.task_creation_materials import MaterialBudgets

    budgets = value.material_budgets()
    assert type(budgets) is MaterialBudgets
    assert (budgets.max_bytes, budgets.max_nodes, budgets.max_capabilities) == (262144, 16, 64)


def test_configuration_has_no_implicit_profile_or_default_constructor():
    with pytest.raises(TypeError):
        module().parse_task_creation_development(raw_configuration())
    with pytest.raises(TypeError):
        module().TaskCreationDevelopmentSettings()


@pytest.mark.parametrize("profile", ["production", "Production", "development ", "", None, True, 1, [], {}])
def test_unapproved_profile_is_refused_without_falling_back(profile):
    with pytest.raises(ValueError, match=f"^{PROFILE_INVALID}$"):
        parse(profile=profile)


@pytest.mark.parametrize("field", tuple(LIMITS))
@pytest.mark.parametrize("bad", [None, True, False, 0, -1, 1.5, "1"])
def test_each_limit_requires_an_explicit_positive_exact_integer(field, bad):
    document = configuration()
    document["task_creation_development"][field] = bad
    assert_config_invalid(document)


@pytest.mark.parametrize("field", tuple(name for name in LIMITS if name != "min_free_space_bytes"))
def test_each_engineering_ceiling_rejects_an_increased_budget(field):
    document = configuration()
    document["task_creation_development"][field] += 1
    assert_config_invalid(document)


@pytest.mark.parametrize("bad", [5368709119, 2**63])
def test_free_space_is_a_minimum_safety_reserve_with_a_bounded_integer(bad):
    document = configuration()
    document["task_creation_development"]["min_free_space_bytes"] = bad
    assert_config_invalid(document)


def test_free_space_may_be_made_more_conservative_and_has_a_stable_digest():
    document = configuration()
    document["task_creation_development"]["min_free_space_bytes"] = 2**63 - 1
    value = parse(document)
    assert value.min_free_space_bytes == 2**63 - 1
    assert value.sha256 != parse().sha256


@pytest.mark.parametrize("field", tuple(configuration()["task_creation_development"]))
def test_every_configuration_field_is_required_and_never_defaulted(field):
    document = configuration()
    del document["task_creation_development"][field]
    assert_config_invalid(document)


@pytest.mark.parametrize("location", ["root", "settings"])
@pytest.mark.parametrize("name", ["runtime_profile", "authorized", "active", "unknown"])
def test_unknown_fields_and_json_authority_or_profile_overrides_are_rejected(location, name):
    document = configuration()
    target = document if location == "root" else document["task_creation_development"]
    target[name] = "production" if name == "runtime_profile" else True
    assert_config_invalid(document)


@pytest.mark.parametrize("bad", [None, False, [], "task_creation_development", {}])
def test_envelope_requires_the_unique_configuration_object(bad):
    assert_config_invalid(bad)


@pytest.mark.parametrize("bad", [None, True, [], "configuration", 1])
def test_configuration_member_must_be_an_object(bad):
    assert_config_invalid({"task_creation_development": bad})


@pytest.mark.parametrize("field", ["schema_version", "environment"])
@pytest.mark.parametrize("bad", [None, True, 1, "", "unexpected"])
def test_schema_and_environment_cannot_select_another_execution_boundary(field, bad):
    document = configuration()
    document["task_creation_development"][field] = bad
    assert_config_invalid(document)


@pytest.mark.parametrize(
    "bad", [None, True, 1, "", " ", " e04-v1", "e04 v1", "研发-v1", "x" * 65, ".revision", "_revision", "-revision"]
)
def test_revision_requires_an_explicit_bounded_ascii_identifier(bad):
    document = configuration()
    document["task_creation_development"]["revision"] = bad
    assert_config_invalid(document)


@pytest.mark.parametrize("revision", ["a", "x" * 64, "e04-v2"])
def test_distinct_valid_revisions_remain_part_of_the_fixed_configuration_snapshot(revision):
    document = configuration()
    document["task_creation_development"]["revision"] = revision
    value = parse(document)
    assert value.revision == revision
    assert value.sha256 != parse().sha256


@pytest.mark.parametrize(
    "bad",
    [None, True, "internal-rnd-original-integrity", [], ["internal-rnd-original-integrity"] * 2, ["unknown"], [1]],
)
def test_reserved_handler_allowlist_is_nonempty_explicit_and_does_not_admit_import_paths(bad):
    document = configuration()
    document["task_creation_development"]["allowed_handler_ids"] = bad
    assert_config_invalid(document)


def test_parsing_reserved_handler_metadata_does_not_import_or_instantiate_handlers(monkeypatch):
    import builtins

    target = module()
    original_import = builtins.__import__
    attempted = []

    def observed_import(name, *args, **kwargs):
        if "handlers" in name or "original_integrity" in name or "internal-rnd-original-integrity" in name:
            attempted.append(name)
            raise AssertionError("Configuration must not import a handler")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", observed_import)
    value = target.parse_task_creation_development(raw_configuration(), runtime_profile="test")
    assert value.allowed_handler_ids == ("internal-rnd-original-integrity",)
    assert attempted == []


@pytest.mark.parametrize(
    "changes",
    [
        {"max_bundle_bytes": 262143},
        {"max_material_bytes": 65535},
        {"max_snapshots_bytes": 262143},
        {"max_nodes": 15},
        {"max_material_bytes": 16383, "max_bundle_bytes": 65532, "max_snapshots_bytes": 262128},
        {"max_task_temp_bytes": 6291455},
        {"proof_budget_seconds": 9},
        {"node_lease_seconds": 9, "proof_budget_seconds": 9, "create_deadline_seconds": 9},
        {"create_deadline_seconds": 1, "proof_budget_seconds": 1, "db_statement_timeout_ms": 1000},
        {"db_statement_timeout_ms": 999},
    ],
)
def test_cross_field_limits_cannot_form_a_larger_or_incoherent_effective_budget(changes):
    document = configuration()
    document["task_creation_development"].update(changes)
    assert_config_invalid(document)


def test_smaller_coherent_engineering_configuration_is_accepted_without_increasing_any_ceiling():
    document = configuration()
    document["task_creation_development"].update(
        max_material_bytes=4096,
        max_nodes=1,
        max_capabilities=1,
        max_bundle_bytes=16384,
        max_snapshots_bytes=4096,
        max_http_body_bytes=2048,
        proof_budget_seconds=5,
        control_ttl_seconds=30,
        adoption_max_seconds=60,
        generation_max_age_seconds=5,
        capability_lease_seconds=5,
        node_lease_seconds=10,
        max_object_bytes=4096,
        handler_deadline_seconds=5,
        db_connect_timeout_seconds=1,
        db_pool_timeout_seconds=1,
        db_statement_timeout_ms=1000,
        db_lock_timeout_ms=500,
        create_deadline_seconds=2,
        max_task_temp_bytes=24576,
        max_incomplete_temp_tasks=1,
    )
    value = parse(document)
    assert value.max_nodes == 1
    assert value.max_task_temp_bytes == 24576


def test_independent_short_retry_and_evidence_windows_are_not_treated_as_an_authorization_chain():
    document = configuration()
    document["task_creation_development"].update(
        control_ttl_seconds=1,
        adoption_max_seconds=1,
        capability_lease_seconds=1,
        node_lease_seconds=10,
    )
    value = parse(document)
    assert value.proof_budget_seconds == 30
    assert value.control_ttl_seconds == 1
    assert value.adoption_max_seconds == 1
    assert value.capability_lease_seconds == 1
    assert value.node_lease_seconds == 10
    assert not hasattr(value, "authorized")


def test_configuration_is_frozen_detached_and_canonically_bound_to_profile_and_revision():
    document = configuration()
    original = copy.deepcopy(document)
    value = parse(document)
    expected = json.dumps(
        {
            "runtime_profile": "development",
            "canonicalization_version": "task-creation-development-json-v1",
            "configuration": original,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf8")
    assert value.canonical_bytes == expected
    assert value.sha256 == hashlib.sha256(expected).hexdigest()
    assert value.sha256 != parse(profile="test").sha256
    document["task_creation_development"]["allowed_handler_ids"].clear()
    exported = value.as_dict()
    exported["task_creation_development"]["allowed_handler_ids"].clear()
    exported["task_creation_development"]["proof_budget_seconds"] = 1
    assert value.as_dict() == original
    assert value.canonical_bytes == expected
    with pytest.raises(FrozenInstanceError):
        value.revision = "different"
    with pytest.raises(FrozenInstanceError):
        value.allowed_handler_ids += ("unknown",)


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"proof_budget_seconds": True}, CONFIG_INVALID),
        ({"max_nodes": 0}, CONFIG_INVALID),
        ({"max_material_bytes": 1}, CONFIG_INVALID),
        ({"allowed_handler_ids": ["internal-rnd-original-integrity"]}, CONFIG_INVALID),
        ({"allowed_handler_ids": ("unknown",)}, CONFIG_INVALID),
        ({"runtime_profile": "production"}, PROFILE_INVALID),
    ],
)
def test_direct_dataclass_replacement_cannot_bypass_parser_validation(changes, expected):
    with pytest.raises(ValueError, match=f"^{expected}$"):
        replace(parse(), **changes)


def test_direct_construction_carries_the_same_explicit_validated_snapshot():
    document = configuration()["task_creation_development"]
    document["allowed_handler_ids"] = tuple(document["allowed_handler_ids"])
    value = module().TaskCreationDevelopmentSettings(runtime_profile="development", **document)
    assert value.canonical_bytes == parse().canonical_bytes
    document["max_nodes"] = False
    with pytest.raises(ValueError, match=f"^{CONFIG_INVALID}$"):
        module().TaskCreationDevelopmentSettings(runtime_profile="development", **document)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"null",
        b"[]",
        b"false",
        b"\xff",
        b'{"task_creation_development":{},"task_creation_development":{}}',
        b'{"task_creation_development":{"max_nodes":1,"max_nodes":2}}',
        b'{"task_creation_development":{"max_nodes":NaN}}',
        b'{"task_creation_development":{"max_nodes":Infinity}}',
        b'{"task_creation_development":{"max_nodes":-Infinity}}',
        b'{"task_creation_development":{"max_nodes":1e999}}',
        b'{"task_creation_development":{"revision":"\\ud800"}}',
        b"[" * 2000 + b"]" * 2000,
    ],
)
def test_ambiguous_nonfinite_or_malformed_json_never_reaches_configuration(raw):
    with pytest.raises(ValueError, match=f"^{CONFIG_INVALID}$"):
        module().parse_task_creation_development(raw, runtime_profile="development")


@pytest.mark.parametrize("raw", [None, "{}", bytearray(b"{}"), memoryview(b"{}")])
def test_parser_requires_raw_bytes_not_a_coerced_value(raw):
    with pytest.raises(ValueError, match=f"^{CONFIG_INVALID}$"):
        module().parse_task_creation_development(raw, runtime_profile="development")


def test_raw_configuration_has_a_bound_before_json_decoding():
    raw = raw_configuration() + b" " * 16384
    with pytest.raises(ValueError, match=f"^{CONFIG_INVALID}$"):
        module().parse_task_creation_development(raw, runtime_profile="development")


def test_raw_configuration_accepts_the_exact_format_byte_ceiling():
    raw = raw_configuration()
    padded = raw + b" " * (16384 - len(raw))
    assert module().parse_task_creation_development(padded, runtime_profile="development").sha256 == parse().sha256


@pytest.mark.parametrize("mode", [0o400, 0o600])
def test_private_loader_reads_exact_bytes_without_environment_fallback(tmp_path, monkeypatch, mode):
    path = private_config(tmp_path)
    path.chmod(mode)
    monkeypatch.setenv("MT_RUNTIME_PROFILE", "production")
    monkeypatch.setenv("MT_TASK_CREATION_PROOF_BUDGET_SECONDS", "999")
    value = module().load_task_creation_development(path, runtime_profile="test")
    assert value.runtime_profile == "test"
    assert value.as_dict() == configuration()
    assert value.sha256 == parse(profile="test").sha256


@pytest.mark.parametrize("mode", [0o500, 0o700])
def test_private_loader_accepts_owner_only_parent_directory(tmp_path, mode):
    path = private_config(tmp_path)
    path.parent.chmod(mode)
    try:
        assert module().load_task_creation_development(path, runtime_profile="development").as_dict() == configuration()
    finally:
        path.parent.chmod(0o700)


@pytest.mark.parametrize("mode", [0o750, 0o755, 0o770, 0o777])
def test_private_loader_rejects_accessible_parent_directory(tmp_path, mode):
    path = private_config(tmp_path)
    path.parent.chmod(mode)
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
        module().load_task_creation_development(path, runtime_profile="development")


@pytest.mark.parametrize("mode", [0o000, 0o200, 0o444, 0o640, 0o644, 0o660, 0o700, 0o777])
def test_private_loader_requires_an_exact_owner_only_readable_regular_file(tmp_path, mode):
    path = private_config(tmp_path)
    path.chmod(mode)
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
        module().load_task_creation_development(path, runtime_profile="development")


@pytest.mark.parametrize("defect", ["relative", "missing", "directory", "leaf_symlink", "parent_symlink", "hardlink"])
def test_private_loader_refuses_ambiguous_paths_and_linked_files(tmp_path, monkeypatch, defect):
    path = private_config(tmp_path)
    if defect == "relative":
        monkeypatch.chdir(tmp_path)
        path = Path("private/task-creation.json")
    elif defect == "missing":
        path = path.with_name("absent.json")
    elif defect == "directory":
        path = path.parent
    elif defect == "leaf_symlink":
        link = path.with_name("alias.json")
        link.symlink_to(path)
        path = link
    elif defect == "parent_symlink":
        link = tmp_path / "alias"
        link.symlink_to(path.parent, target_is_directory=True)
        path = link / path.name
    elif defect == "hardlink":
        path.with_name("second-name.json").hardlink_to(path)
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
        module().load_task_creation_development(path, runtime_profile="development")


def test_private_loader_rejects_repository_paths(tmp_path):
    # Existing repository source is never an approved private configuration.
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
        module().load_task_creation_development(Path(__file__).resolve(), runtime_profile="development")


def test_private_loader_rejects_an_otherwise_valid_file_inside_the_repository_boundary(tmp_path, monkeypatch):
    path = private_config(tmp_path)
    target = module()
    monkeypatch.setattr(target, "ROOT", tmp_path)
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
        target.load_task_creation_development(path, runtime_profile="development")


@pytest.mark.parametrize("raw", [b"", b"x" * 16385])
def test_private_loader_bounds_the_actual_file_before_parsing(tmp_path, raw):
    path = private_config(tmp_path, raw=raw)
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
        module().load_task_creation_development(path, runtime_profile="development")


def test_private_loader_rejects_production_even_with_a_valid_private_file(tmp_path):
    path = private_config(tmp_path)
    with pytest.raises(ValueError, match=f"^{PROFILE_INVALID}$"):
        module().load_task_creation_development(path, runtime_profile="production")


def test_loader_validation_errors_do_not_echo_private_path_or_configuration(tmp_path):
    sensitive_marker = "self-owned-never-echo-this-configuration"
    path = private_config(tmp_path, raw=json.dumps({"private": sensitive_marker}).encode())
    with pytest.raises(ValueError, match=f"^{CONFIG_INVALID}$") as error:
        module().load_task_creation_development(path, runtime_profile="development")
    assert str(path) not in str(error.value)
    assert sensitive_marker not in str(error.value)


@pytest.mark.parametrize(
    "defect",
    ["append", "rewrite", "file_mode", "hardlink", "replace_file", "parent_mode", "parent_entry", "replace_parent"],
)
def test_private_loader_rejects_actual_file_or_parent_changes_during_read(tmp_path, monkeypatch, defect):
    path = private_config(tmp_path)
    target = module()
    original_read = os.read
    changed = False

    def changing_read(descriptor, size):
        nonlocal changed
        block = original_read(descriptor, size)
        if changed:
            return block
        changed = True
        if defect == "append":
            with path.open("ab") as stream:
                stream.write(b" ")
        elif defect == "rewrite":
            before = path.stat()
            data = path.read_bytes().replace(b"e04-v1", b"e04-v2")
            assert len(data) == before.st_size
            path.write_bytes(data)
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000000))
        elif defect == "file_mode":
            path.chmod(0o400)
        elif defect == "hardlink":
            path.with_name("concurrent-name.json").hardlink_to(path)
        elif defect == "replace_file":
            other = path.with_name("replacement.json")
            other.write_bytes(raw_configuration())
            other.chmod(0o600)
            other.replace(path)
        elif defect == "parent_mode":
            path.parent.chmod(0o500)
        elif defect == "parent_entry":
            before = path.parent.stat()
            path.with_name("unrelated-sibling").write_text("self-owned parent mutation")
            os.utime(path.parent, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000000))
        elif defect == "replace_parent":
            before = path.parent.stat()
            moved = path.parent.with_name("old-private")
            path.parent.rename(moved)
            os.utime(moved, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000000))
            path.parent.mkdir(mode=0o700)
            path.write_bytes(raw_configuration())
            path.chmod(0o600)
        return block

    monkeypatch.setattr(target.os, "read", changing_read)
    try:
        with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$") as error:
            target.load_task_creation_development(path, runtime_profile="development")
        assert changed
        assert str(path) not in str(error.value)
    finally:
        path.parent.chmod(0o700)


@pytest.mark.parametrize("outcome", ["valid", "invalid_json", "public_file", "missing_file"])
def test_private_loader_closes_every_open_descriptor_on_success_and_each_failure(tmp_path, monkeypatch, outcome):
    path = private_config(tmp_path, raw=b"{" if outcome == "invalid_json" else None)
    if outcome == "public_file":
        path.chmod(0o644)
    elif outcome == "missing_file":
        path = path.with_name("absent.json")
    target = module()
    original_open = os.open
    original_close = os.close
    opened, closed = [], []

    def tracked_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def tracked_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    monkeypatch.setattr(target.os, "open", tracked_open)
    monkeypatch.setattr(target.os, "close", tracked_close)
    if outcome == "valid":
        assert target.load_task_creation_development(path, runtime_profile="development").as_dict() == configuration()
    else:
        expected = CONFIG_INVALID if outcome == "invalid_json" else PRIVATE_REQUIRED
        with pytest.raises(ValueError, match=f"^{expected}$"):
            target.load_task_creation_development(path, runtime_profile="development")
    assert opened
    assert closed == list(reversed(opened))
    for descriptor in opened:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_private_loader_refuses_a_leaf_owned_by_another_uid_without_changing_real_ownership(tmp_path, monkeypatch):
    path = private_config(tmp_path)
    leaf = path.stat()
    target = module()
    original_fstat = os.fstat
    injected = []

    def other_owner_fstat(descriptor):
        result = original_fstat(descriptor)
        if (result.st_dev, result.st_ino) == (leaf.st_dev, leaf.st_ino):
            attributes = list(result)
            attributes[4] = result.st_uid + 1
            injected.append(descriptor)
            return os.stat_result(attributes)
        return result

    monkeypatch.setattr(target.os, "fstat", other_owner_fstat)
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
        target.load_task_creation_development(path, runtime_profile="development")
    assert injected
    assert path.stat().st_uid == leaf.st_uid


def test_private_loader_refuses_a_non_linux_host_even_with_a_valid_private_file(tmp_path, monkeypatch):
    path = private_config(tmp_path)
    target = module()
    with monkeypatch.context() as context:
        context.setattr(target.sys, "platform", "darwin")
        with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$"):
            target.load_task_creation_development(path, runtime_profile="development")


def test_private_loader_attempts_all_closes_and_redacts_a_close_failure(tmp_path, monkeypatch):
    path = private_config(tmp_path)
    target = module()
    original_open = os.open
    original_close = os.close
    opened, closed = [], []
    private_marker = "self-owned-never-echo-close-fault"

    def tracked_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def close_then_report_failure(descriptor):
        closed.append(descriptor)
        original_close(descriptor)
        if len(closed) == 1:
            raise OSError(private_marker)

    monkeypatch.setattr(target.os, "open", tracked_open)
    monkeypatch.setattr(target.os, "close", close_then_report_failure)
    with pytest.raises(ValueError, match=f"^{PRIVATE_REQUIRED}$") as error:
        target.load_task_creation_development(path, runtime_profile="development")
    assert len(opened) > 1
    assert closed == list(reversed(opened))
    assert str(path) not in str(error.value)
    assert private_marker not in str(error.value)
    for descriptor in opened:
        with pytest.raises(OSError):
            os.fstat(descriptor)
