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
    for relative in [MATRIX, PRIOR, REGISTRATION, "backend/business_app/registry_router.py"]:
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
    assert sum(row["runtime_route"] is not None for row in current["operations"]) == 47


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
