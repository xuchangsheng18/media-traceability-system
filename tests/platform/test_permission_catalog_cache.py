"""Catalog reuse must preserve fresh-file validation and caller isolation."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path
from threading import Barrier

import pytest
from business_app.permissions import catalog

OPENAPI = "docs/03-api/openapi.yaml"
MODEL = "docs/08-security/access-control-model.json"


def write_catalog(root: Path, permission: str = "identity.read") -> None:
    document = (
        "servers: [{url: /api/v1}]\n"
        "security: [{bearerAuth: []}]\n"
        "paths:\n"
        "  /auth/me:\n"
        "    get:\n"
        "      operationId: getCurrentUser\n"
        f"      x-required-permission: {permission}\n"
    )
    model = dict(
        permissions=[permission],
        operations=[dict(operation_id="getCurrentUser", method="GET", path="/auth/me", permission=permission)],
    )
    for relative, text in [(OPENAPI, document), (MODEL, json.dumps(model))]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf8")


def count_parses(monkeypatch):
    original = catalog.yaml.safe_load
    calls = []

    def parse(document):
        calls.append(document)
        return original(document)

    monkeypatch.setattr(catalog.yaml, "safe_load", parse)
    return calls


def assert_identity_read(result):
    assert list(result) == ["getCurrentUser"]
    value = result["getCurrentUser"]
    assert (value.operation_id, value.method, value.path, value.permission, value.public) == (
        "getCurrentUser",
        "GET",
        "/api/v1/auth/me",
        "identity.read",
        False,
    )


def test_unchanged_files_reuse_validated_parse_with_independent_results(tmp_path, monkeypatch):
    write_catalog(tmp_path)
    calls = count_parses(monkeypatch)
    first = catalog.load_catalog(tmp_path)
    second = catalog.load_catalog(tmp_path)
    assert_identity_read(first)
    assert_identity_read(second)
    assert first is not second
    assert len(calls) == 1


def test_concurrent_cold_loads_parse_once_and_return_independent_results(tmp_path, monkeypatch):
    write_catalog(tmp_path)
    calls = count_parses(monkeypatch)
    ready = Barrier(8)

    def load(_):
        ready.wait(timeout=10)
        return catalog.load_catalog(tmp_path)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(load, range(8)))
    for result in results:
        assert_identity_read(result)
    assert len({id(result) for result in results}) == 8
    assert len(calls) == 1


def test_canonical_root_alias_reuses_the_same_validated_content(tmp_path, monkeypatch):
    write_catalog(tmp_path)
    (tmp_path / "alias").mkdir()
    calls = count_parses(monkeypatch)
    catalog.load_catalog(tmp_path)
    assert_identity_read(catalog.load_catalog(tmp_path / "alias" / ".."))
    assert len(calls) == 1


def test_changed_content_with_unchanged_size_and_mtime_is_revalidated(tmp_path, monkeypatch):
    write_catalog(tmp_path)
    calls = count_parses(monkeypatch)
    catalog.load_catalog(tmp_path)
    before = {relative: (tmp_path / relative).stat() for relative in [OPENAPI, MODEL]}
    write_catalog(tmp_path, "identity.edit")
    for relative, previous in before.items():
        path = tmp_path / relative
        assert path.stat().st_size == previous.st_size
        os.utime(path, ns=(previous.st_atime_ns, previous.st_mtime_ns))
    assert catalog.load_catalog(tmp_path)["getCurrentUser"].permission == "identity.edit"
    assert len(calls) == 2


@pytest.mark.parametrize("relative", [OPENAPI, MODEL])
def test_deleted_file_never_uses_a_warm_catalog(tmp_path, relative):
    write_catalog(tmp_path)
    catalog.load_catalog(tmp_path)
    (tmp_path / relative).unlink()
    with pytest.raises(ValueError, match="^PERMISSION_CATALOG_INVALID$"):
        catalog.load_catalog(tmp_path)


@pytest.mark.parametrize("relative", [OPENAPI, MODEL])
def test_changed_single_file_binding_never_uses_a_warm_catalog(tmp_path, relative):
    write_catalog(tmp_path)
    catalog.load_catalog(tmp_path)
    path = tmp_path / relative
    previous = path.stat()
    path.write_text(path.read_text(encoding="utf8").replace("identity.read", "identity.edit"), encoding="utf8")
    os.utime(path, ns=(previous.st_atime_ns, previous.st_mtime_ns))
    with pytest.raises(ValueError, match="^PERMISSION_CATALOG_INVALID$"):
        catalog.load_catalog(tmp_path)


@pytest.mark.parametrize("relative,invalid", [(OPENAPI, "paths: ["), (MODEL, "{")])
def test_malformed_warm_file_is_rejected_and_repaired_content_recovers(tmp_path, relative, invalid):
    write_catalog(tmp_path)
    catalog.load_catalog(tmp_path)
    (tmp_path / relative).write_text(invalid, encoding="utf8")
    with pytest.raises(ValueError, match="^PERMISSION_CATALOG_INVALID$"):
        catalog.load_catalog(tmp_path)
    write_catalog(tmp_path, "identity.edit")
    assert catalog.load_catalog(tmp_path)["getCurrentUser"].permission == "identity.edit"


def test_distinct_roots_are_validated_even_when_bytes_match(tmp_path, monkeypatch):
    first, second = tmp_path / "first", tmp_path / "second"
    write_catalog(first)
    write_catalog(second)
    calls = count_parses(monkeypatch)
    assert_identity_read(catalog.load_catalog(first))
    assert_identity_read(catalog.load_catalog(second))
    assert len(calls) == 2
    (second / MODEL).unlink()
    with pytest.raises(ValueError, match="^PERMISSION_CATALOG_INVALID$"):
        catalog.load_catalog(second)
    assert_identity_read(catalog.load_catalog(first))


def test_returned_dictionary_mutation_cannot_change_cached_permissions(tmp_path):
    write_catalog(tmp_path)
    result = catalog.load_catalog(tmp_path)
    entry = result.pop("getCurrentUser")
    result["injected"] = catalog.OperationPermission("injected", "GET", "/api/v1/injected", "identity.edit", True)
    with pytest.raises(FrozenInstanceError):
        setattr(entry, "permission", "identity.edit")
    assert_identity_read(catalog.load_catalog(tmp_path))


def test_evicted_catalog_is_revalidated_on_next_load(tmp_path, monkeypatch):
    calls = count_parses(monkeypatch)
    for index in range(17):
        root = tmp_path / str(index)
        write_catalog(root)
        assert_identity_read(catalog.load_catalog(root))
    before = len(calls)
    assert_identity_read(catalog.load_catalog(tmp_path / "0"))
    assert len(calls) == before + 1
