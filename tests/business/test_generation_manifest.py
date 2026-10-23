"""Private independent generation evidence, never a database self-attestation."""

import importlib
import importlib.util
import json
import os
from dataclasses import asdict, replace
from types import SimpleNamespace
from typing import Any

import pytest
from business_app.errors import BusinessError
from business_app.permissions.fence import AuthorizationFence, GenerationProof


def module():
    assert importlib.util.find_spec("business_app.permissions.generation_manifest") is not None, (
        "Independent generation manifest reader is not implemented"
    )
    return importlib.import_module("business_app.permissions.generation_manifest")


def identity():
    return module().GenerationIdentity("test-database", 12345, "test-policy-v1", "a" * 64, "test-generation", 7)


def document():
    return {"schema_version": "1.0.0", **asdict(identity()), "confirmed_at": 1000, "valid_until": 1030}


def parse(value=None, *, now=1001):
    return module().parse_generation_manifest(
        json.dumps(document() if value is None else value).encode(), expected=identity(), max_age_seconds=30, now=now
    )


def private_file(tmp_path):
    folder = tmp_path / "custody"
    folder.mkdir(mode=0o700)
    path = folder / "generation.json"
    path.write_text(json.dumps(document()))
    path.chmod(0o600)
    return path


def reader(path, *, clock=lambda: 1001):
    return module().PrivateGenerationReader(path, expected=identity(), max_age_seconds=30, clock=clock)


def denied(call):
    with pytest.raises(BusinessError) as error:
        call()
    assert error.value.code == "CONDITIONAL_FACTS_UNAVAILABLE"
    assert error.value.http_status == 503
    assert "generation.json" not in str(error.value)


def test_independent_reader_exists_and_returns_existing_fence_protocol():
    result = parse()
    assert type(result) is GenerationProof
    assert result == GenerationProof(
        "test-generation", "test-policy-v1", "a" * 64, "test-database", 12345, 7, 1000, 1030
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "2.0.0"),
        ("database_name", "other"),
        ("database_oid", 12346),
        ("database_oid", True),
        ("policy_version", "other"),
        ("policy_sha256", "b" * 64),
        ("recovery_generation", "old"),
        ("minimum_epoch", 6),
        ("minimum_epoch", True),
        ("confirmed_at", 1002),
        ("confirmed_at", True),
        ("confirmed_at", float("nan")),
        ("valid_until", 1001),
        ("valid_until", 1031),
        ("valid_until", float("inf")),
    ],
)
def test_changed_binding_unknown_fields_invalid_types_and_deadlines_refuse(field, value):
    data = document()
    data[field] = value
    denied(lambda: parse(data))


@pytest.mark.parametrize("change", ["missing", "extra", "nested"])
def test_manifest_has_a_closed_flat_shape(change):
    data = document()
    if change == "missing":
        del data["policy_sha256"]
    elif change == "extra":
        data["approved"] = True
    else:
        data["database_name"] = {"name": "test-database"}
    denied(lambda: parse(data))


@pytest.mark.parametrize(
    "raw",
    [b"", b"{}", b"[]", b"\xff", b" " * 16385, b'{"schema_version":"1.0.0","schema_version":"1.0.0"}', b'{"x":NaN}'],
)
def test_invalid_duplicate_unbounded_or_nonfinite_bytes_refuse(raw):
    denied(lambda: module().parse_generation_manifest(raw, expected=identity(), max_age_seconds=30, now=1001))


@pytest.mark.parametrize("now", [999, 1030, 1040, True, float("nan"), float("inf")])
def test_evidence_never_renews_itself_or_accepts_invalid_clocks(now):
    denied(lambda: parse(now=now))


@pytest.mark.parametrize("budget", [0, -1, True, 30.0, 31, None])
def test_explicit_freshness_budget_is_required_and_bounded(budget):
    denied(
        lambda: module().parse_generation_manifest(
            json.dumps(document()).encode(), expected=identity(), max_age_seconds=budget, now=1001
        )
    )


def test_private_file_reloads_every_read_and_missing_file_revokes(tmp_path):
    path = private_file(tmp_path)
    current = reader(path)
    assert current.read() == parse()
    data = document()
    data["recovery_generation"] = "changed-after-recovery"
    path.write_text(json.dumps(data))
    denied(current.read)
    path.unlink()
    denied(current.read)


@pytest.mark.parametrize(
    "kind", ["file_mode", "parent_mode", "symlink", "parent_symlink", "hardlink", "fifo", "missing", "directory"]
)
def test_unprotected_or_aliased_files_are_rejected(tmp_path, kind):
    path = private_file(tmp_path)
    if kind == "file_mode":
        path.chmod(0o644)
    elif kind == "parent_mode":
        path.parent.chmod(0o755)
    elif kind == "symlink":
        alias = path.with_name("alias.json")
        alias.symlink_to(path)
        path = alias
    elif kind == "parent_symlink":
        alias = tmp_path / "alias"
        alias.symlink_to(path.parent, target_is_directory=True)
        path = alias / path.name
    elif kind == "hardlink":
        os.link(path, path.with_name("alias.json"))
    elif kind == "fifo":
        path.unlink()
        os.mkfifo(path, 0o600)
    elif kind == "missing":
        path.unlink()
    else:
        path.unlink()
        path.mkdir(mode=0o700)
    denied(reader(path).read)


def test_reader_rejects_clock_and_evidence_rollback(tmp_path):
    path = private_file(tmp_path)
    now: list[float] = [1001]
    current = reader(path, clock=lambda: now[0])
    current.read()
    now[0] = 1000.5
    denied(current.read)
    now[0] = 1002
    data = document()
    data.update(confirmed_at=1001, valid_until=1031, minimum_epoch=8)
    path.write_text(json.dumps(data))
    assert current.read().minimum_epoch == 8
    path.write_text(json.dumps(document()))
    denied(current.read)


def test_fence_consumes_reader_and_rejects_restored_database_identity(tmp_path):
    path = private_file(tmp_path)
    authority: Any = SimpleNamespace(
        rules=SimpleNamespace(
            snapshot=SimpleNamespace(version="test-policy-v1", sha256="a" * 64, recovery_generation="test-generation"),
            validate_snapshot=lambda: None,
        )
    )
    fence = AuthorizationFence(authority, reader(path), clock=lambda: 1001)
    stamp = {**asdict(identity()), "epoch": 7}
    assert fence._generation(stamp, 1001) == parse()
    with pytest.raises(BusinessError, match="AUTHORIZATION_CHANGED"):
        fence._generation({**stamp, "database_oid": 999}, 1001)


def test_identity_configuration_cannot_be_changed_into_a_manifest_assertion():
    expected = identity()
    denied(
        lambda: module().parse_generation_manifest(
            json.dumps(document()).encode(), expected=replace(expected, minimum_epoch=8), max_age_seconds=30, now=1001
        )
    )


def test_read_cannot_publish_evidence_expiring_during_io(tmp_path):
    path = private_file(tmp_path)
    ticks = iter([1001, 1030])
    denied(reader(path, clock=lambda: next(ticks)).read)


def test_read_checks_replacement_and_mutation_during_io(tmp_path, monkeypatch):
    path = private_file(tmp_path)
    original_read = os.read
    mutated = [False]

    def changed(descriptor, size):
        raw = original_read(descriptor, size)
        if raw and not mutated[0]:
            mutated[0] = True
            replacement = path.with_name("replacement.json")
            replacement.write_bytes(raw)
            replacement.chmod(0o600)
            replacement.replace(path)
        return raw

    monkeypatch.setattr(module().os, "read", changed)
    denied(reader(path).read)


def test_parent_custody_owner_must_match_current_process(tmp_path, monkeypatch):
    path = private_file(tmp_path)
    actual_uid = os.getuid()
    monkeypatch.setattr(module().os, "getuid", lambda: actual_uid + 1)
    denied(reader(path).read)


def test_reader_cannot_read_from_repository_even_when_private(tmp_path, monkeypatch):
    path = private_file(tmp_path)
    monkeypatch.setattr(module(), "ROOT", tmp_path)
    denied(reader(path).read)


def test_freshness_renewal_returns_actual_new_deadline_without_moving_epoch(tmp_path):
    path = private_file(tmp_path)
    current = reader(path, clock=lambda: 1002)
    old = current.read()
    data = document()
    data.update(confirmed_at=1001, valid_until=1031)
    path.write_text(json.dumps(data))
    assert current.read() == replace(old, confirmed_at=1001, valid_until=1031)


def test_read_refuses_a_detached_ancestor_namespace(tmp_path, monkeypatch):
    namespace = tmp_path / "namespace"
    namespace.mkdir(mode=0o700)
    path = private_file(namespace)
    original_read = os.read
    moved = [False]

    def detach(descriptor, size):
        raw = original_read(descriptor, size)
        if raw and not moved[0]:
            moved[0] = True
            namespace.rename(tmp_path / "detached")
            namespace.mkdir(mode=0o700)
        return raw

    monkeypatch.setattr(module().os, "read", detach)
    denied(reader(path).read)


def test_read_refuses_a_writable_ancestor_even_with_private_custody_parent(tmp_path):
    namespace = tmp_path / "namespace"
    namespace.mkdir(mode=0o700)
    path = private_file(namespace)
    namespace.chmod(0o777)
    denied(reader(path).read)


def test_expired_observation_cannot_be_resurrected_by_clock_rollback(tmp_path):
    now = [1001]
    current = reader(private_file(tmp_path), clock=lambda: now[0])
    current.read()
    now[0] = 1030
    denied(current.read)
    now[0] = 1002
    denied(current.read)
