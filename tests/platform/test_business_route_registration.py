"""A new metadata route cannot rewrite the prior permission adoption evidence."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MATRIX = "docs/08-security/t014-interface-scope-matrix.json"
PRIOR = "docs/08-security/history/report-read-predecessor-scope-matrix.json"
REGISTRATION = "docs/08-security/report-read-route-registration.json"


def verifier(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    assert (ROOT / "scripts/verify_business_route_registration.py").is_file(), "STRICT_ROUTE_DELTA_REQUIRED"
    return importlib.import_module("verify_business_route_registration").verify_business_route_registration


@pytest.fixture
def registered(tmp_path):
    for relative in [
        MATRIX,
        PRIOR,
        REGISTRATION,
        "backend/business_app/registry_router.py",
        "docs/08-security/history/resource-registry-predecessor-scope-matrix.json",
        "docs/08-security/resource-registry-route-registration.json",
        "backend/business_app/asset_download_router.py",
        "backend/business_app/source_registration_router.py",
        "backend/business_app/model_catalog_router.py",
        "backend/business_app/task_creation_router.py",
        "docs/08-security/history/task-creation-predecessor-scope-matrix.json",
        "docs/08-security/task-creation-route-registration.json",
    ]:
        source = ROOT / relative
        assert source.is_file(), "REGISTRATION_FIXTURE_REQUIRED"
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    return tmp_path


def change_matrix(root, change):
    matrix = json.loads((root / MATRIX).read_text("utf8"))
    change(matrix)
    body = (json.dumps(matrix, ensure_ascii=False, indent=2) + "\n").encode("utf8")
    (root / MATRIX).write_bytes(body)
    record = json.loads((root / REGISTRATION).read_text("utf8"))
    record["source_bindings"][MATRIX]["current_sha256"] = hashlib.sha256(body).hexdigest()
    (root / REGISTRATION).write_text(json.dumps(record), encoding="utf8")


def test_registered_report_route_keeps_the_exact_historical_matrix(monkeypatch, registered):
    assert verifier(monkeypatch)(registered) == registered / PRIOR
    old = json.loads((registered / PRIOR).read_text("utf8"))
    current = json.loads((registered / MATRIX).read_text("utf8"))
    assert sum(row["runtime_route"] is not None for row in old["operations"]) == 46
    assert sum(row["runtime_route"] is not None for row in current["operations"]) == 52


@pytest.mark.parametrize(
    "change",
    [
        "roles",
        "default_effect",
        "formal_approved",
        "integer_flag",
        "another_operation",
        "extra_route",
        "task_formal_allow",
        "task_authentication",
    ],
)
def test_latest_registration_rehash_cannot_expand_the_semantic_delta(registered, change):
    from scripts.verify_task_creation_registration import verify_task_creation_registration

    current = json.loads((registered / MATRIX).read_text("utf8"))
    if change in {"roles", "default_effect", "formal_approved", "integer_flag"}:
        field, value = {
            "roles": ("roles", []),
            "default_effect": ("default_effect", "ALLOW"),
            "formal_approved": ("formal_approved", True),
            "integer_flag": ("formal_approved", 0),
        }[change]
        current[field] = value
    elif change == "another_operation":
        current["operations"][0]["current_guard_review"] = "untrusted expansion"
    elif change == "extra_route":
        current["task_creation_increment"]["mounted_operations"] = 53
    else:
        row = next(item for item in current["operations"] if item["operation_id"] == "createTask")
        row["formal_allow" if change == "task_formal_allow" else "authentication"] = True
    raw = (json.dumps(current, ensure_ascii=False, indent=2) + "\n").encode()
    (registered / MATRIX).write_bytes(raw)
    path = registered / "docs/08-security/task-creation-route-registration.json"
    record = json.loads(path.read_text("utf8"))
    record["current_sha256"] = hashlib.sha256(raw).hexdigest()
    path.write_text(json.dumps(record), encoding="utf8")
    with pytest.raises(AssertionError):
        verify_task_creation_registration(registered)


@pytest.mark.parametrize(
    "field,value",
    [("roles", []), ("default_effect", "ALLOW"), ("formal_approved", True), ("formal_approved", 0)],
)
def test_rehashed_registration_cannot_rewrite_roles_or_global_policy(monkeypatch, registered, field, value):
    change_matrix(registered, lambda value_dict: value_dict.__setitem__(field, value))
    with pytest.raises(AssertionError, match="ROUTE_REGISTRATION_INVALID"):
        verifier(monkeypatch)(registered)


@pytest.mark.parametrize("field", ["case_rule", "unit_rule", "permission", "authentication", "formal_allow"])
def test_rehashed_registration_cannot_rewrite_report_authorization(monkeypatch, registered, field):
    def change(value):
        row = next(item for item in value["operations"] if item["operation_id"] == "getReport")
        row[field] = True if field == "formal_allow" else "untrusted expansion"

    change_matrix(registered, change)
    with pytest.raises(AssertionError, match="ROUTE_REGISTRATION_INVALID"):
        verifier(monkeypatch)(registered)


def test_rehashed_registration_cannot_change_another_operation(monkeypatch, registered):
    change_matrix(registered, lambda value: value["operations"][0].__setitem__("current_guard_review", "changed"))
    with pytest.raises(AssertionError, match="ROUTE_REGISTRATION_INVALID"):
        verifier(monkeypatch)(registered)


@pytest.mark.parametrize(
    "defect", ["current_hash", "prior_hash", "prior_copy", "extra_scope", "formal_flag", "integer_flag"]
)
def test_registration_rejects_hash_path_and_claim_drift(monkeypatch, registered, defect):
    record = json.loads((registered / REGISTRATION).read_text("utf8"))
    binding = record["source_bindings"][MATRIX]
    if defect in {"current_hash", "prior_hash"}:
        binding["current_sha256" if defect == "current_hash" else "prior_sha256"] = "0" * 64
    elif defect == "prior_copy":
        binding["prior_copy"] = MATRIX
    elif defect == "extra_scope":
        record["scope"].append("downloadAsset")
    elif defect == "formal_flag":
        record["formal_allow"] = True
    else:
        record["formal_allow"] = 0
    (registered / REGISTRATION).write_text(json.dumps(record), encoding="utf8")
    with pytest.raises(AssertionError, match="ROUTE_REGISTRATION_INVALID"):
        verifier(monkeypatch)(registered)


def test_historical_copy_bytes_cannot_be_replaced(monkeypatch, registered):
    path = registered / PRIOR
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(AssertionError, match="ROUTE_REGISTRATION_INVALID"):
        verifier(monkeypatch)(registered)


def test_new_increment_cannot_claim_runtime_or_formal_acceptance(monkeypatch, registered):
    change_matrix(registered, lambda value: value["report_read_increment"].__setitem__("formal_approved", True))
    with pytest.raises(AssertionError, match="ROUTE_REGISTRATION_INVALID"):
        verifier(monkeypatch)(registered)


@pytest.mark.parametrize("defect", ["scope", "hash", "prior", "allow", "integer_allow", "shared"])
def test_resource_successor_rejects_unapproved_scope_or_adoption(monkeypatch, registered, defect):
    path = registered / "docs/08-security/resource-registry-route-registration.json"
    record = json.loads(path.read_text("utf8"))
    if defect == "scope":
        record["scope"].append("health")
    elif defect == "hash":
        record["source_bindings"][MATRIX]["current_sha256"] = "0" * 64
    elif defect == "prior":
        record["source_bindings"][MATRIX]["prior_copy"] = MATRIX
    elif defect == "shared":
        record["shared_adopted"] = True
    else:
        record["formal_allow"] = True if defect == "allow" else 0
    path.write_text(json.dumps(record), encoding="utf8")
    with pytest.raises(AssertionError, match="ROUTE_REGISTRATION_INVALID"):
        verifier(monkeypatch)(registered)
