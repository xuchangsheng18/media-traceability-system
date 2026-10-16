"""T011 candidate policy review; never tests a production identity provider."""

import importlib.util
import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 16, tzinfo=timezone.utc)


def review_module():
    name = "t011_access_review"
    if name not in sys.modules:
        path = ROOT / "tools/access_control_review.py"
        assert path.is_file(), "T011 review evaluator is not implemented"
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def review_values():
    module = review_module()
    model = json.loads((ROOT / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))
    request = module.ReviewRequest(
        subject_id="fixture-user-a",
        subject_org_id="fixture-org-a",
        roles=("case_investigator",),
        resource_org_id="fixture-org-a",
        case_id="fixture-case-a",
        object_id="fixture-object-a",
        permission="asset.read",
        purpose="fixture-case-review",
        labels=("fixture-label-a",),
        policy_revision="fixture-policy-v1",
        identity_verified=True,
        account_enabled=True,
        membership_org_id="fixture-org-a",
        membership_case_id="fixture-case-a",
        membership_expires_at=NOW + timedelta(days=1),
        membership_revoked=False,
        role_expires_at=NOW + timedelta(days=1),
        role_revoked=False,
    )
    grant = module.ReviewGrant(
        subject_id="fixture-user-a",
        role="case_investigator",
        permission="asset.read",
        org_id="fixture-org-a",
        case_id="fixture-case-a",
        object_id="fixture-object-a",
        purposes=("fixture-case-review",),
        labels=("fixture-label-a",),
        policy_revision="fixture-policy-v1",
        valid_from=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(hours=1),
        revoked=False,
    )
    return module, model, request, grant


@pytest.fixture
def review():
    return review_values()


def test_no_explicit_grant_is_denied_even_for_source_responsibility():
    module, model, request, _ = review_values()
    request = replace(request, permission="task.create")
    result = module.evaluate_review(model, request, (), now=NOW)
    assert (result.effect, result.reason, result.runtime_authorization) == ("DENY", "NO_MATCHING_EXPLICIT_GRANT", False)


def test_matching_fixture_grant_allows_only_candidate_review(review):
    module, model, request, grant = review
    result = module.evaluate_review(model, request, (grant,), now=NOW)
    assert (result.effect, result.reason, result.runtime_authorization) == ("CANDIDATE_ALLOW", "REVIEW_MATCH", False)


@pytest.mark.parametrize("role", ["system_admin", "data_admin", "algorithm_admin", "business_reviewer", "auditor"])
def test_role_names_never_supply_implicit_permissions(review, role):
    module, model, request, _ = review
    result = module.evaluate_review(model, replace(request, roles=(role,)), (), now=NOW)
    assert result.effect == "DENY" and not result.runtime_authorization


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"identity_verified": False}, "IDENTITY_NOT_VERIFIED"),
        ({"account_enabled": False}, "ACCOUNT_DISABLED"),
        ({"roles": ()}, "ROLE_MISSING_OR_UNKNOWN"),
        ({"roles": ("unknown-role",)}, "ROLE_MISSING_OR_UNKNOWN"),
        ({"role_revoked": True}, "ROLE_BINDING_INACTIVE"),
        ({"role_expires_at": NOW}, "ROLE_BINDING_INACTIVE"),
        ({"resource_org_id": "fixture-org-b"}, "ORGANIZATION_MISMATCH"),
        ({"membership_org_id": "fixture-org-b"}, "ORGANIZATION_MISMATCH"),
        ({"case_id": "fixture-case-b"}, "CASE_MEMBERSHIP_INACTIVE"),
        ({"membership_case_id": "fixture-case-b"}, "CASE_MEMBERSHIP_INACTIVE"),
        ({"membership_revoked": True}, "CASE_MEMBERSHIP_INACTIVE"),
        ({"membership_expires_at": NOW}, "CASE_MEMBERSHIP_INACTIVE"),
        ({"case_id": ""}, "CASE_MEMBERSHIP_INACTIVE"),
        ({"subject_id": ""}, "SUBJECT_MISSING"),
        ({"object_id": ""}, "OBJECT_MISSING"),
        ({"permission": "asset.unknown"}, "PERMISSION_UNKNOWN"),
        ({"permission": "policy.manage"}, "REVIEW_SCOPE_UNSUPPORTED"),
        ({"purpose": ""}, "PURPOSE_OR_CLASSIFICATION_UNCONFIRMED"),
        ({"labels": ()}, "PURPOSE_OR_CLASSIFICATION_UNCONFIRMED"),
        ({"policy_revision": ""}, "PURPOSE_OR_CLASSIFICATION_UNCONFIRMED"),
        ({"labels": ("fixture-label-b",)}, "NO_MATCHING_EXPLICIT_GRANT"),
        ({"purpose": "fixture-training"}, "NO_MATCHING_EXPLICIT_GRANT"),
        ({"policy_revision": "fixture-policy-v2"}, "NO_MATCHING_EXPLICIT_GRANT"),
        ({"object_id": "fixture-object-b"}, "NO_MATCHING_EXPLICIT_GRANT"),
    ],
)
def test_scope_and_freshness_fail_closed(review, changes, reason):
    module, model, request, grant = review
    result = module.evaluate_review(model, replace(request, **changes), (grant,), now=NOW)
    assert (result.effect, result.reason, result.runtime_authorization) == ("DENY", reason, False)


@pytest.mark.parametrize(
    "changes",
    [
        {"revoked": True},
        {"expires_at": NOW},
        {"valid_from": NOW + timedelta(seconds=1)},
        {"subject_id": "fixture-user-b"},
        {"role": "system_admin"},
        {"permission": "asset.download"},
        {"org_id": "fixture-org-b"},
        {"case_id": "fixture-case-b"},
        {"object_id": "fixture-object-b"},
        {"policy_revision": "fixture-policy-old"},
        {"purposes": ()},
        {"labels": ()},
        {"expires_at": NOW.replace(tzinfo=None)},
    ],
)
def test_grant_cannot_be_reused_for_another_scope_or_lifetime(review, changes):
    module, model, request, grant = review
    result = module.evaluate_review(model, request, (replace(grant, **changes),), now=NOW)
    assert result.effect == "DENY" and not result.runtime_authorization


def test_source_restriction_cannot_be_overridden_by_fixture_grant(review):
    module, model, request, grant = review
    request = replace(request, roles=("auditor",), permission="review.perform")
    grant = replace(grant, role="auditor", permission="review.perform")
    result = module.evaluate_review(model, request, (grant,), now=NOW)
    assert (result.effect, result.reason) == ("DENY", "SOURCE_ROLE_RESTRICTION")


def test_unknown_classification_is_not_an_ordered_clearance(review):
    module, model, request, grant = review
    request = replace(request, labels=("fixture-label-a", "fixture-label-unknown"))
    assert module.evaluate_review(model, request, (grant,), now=NOW).effect == "DENY"


@pytest.mark.parametrize("mode", ["production", "development", "unrecognized"])
def test_review_tool_never_becomes_runtime_authority(review, mode):
    module, model, request, grant = review
    result = module.evaluate_review(model, request, (grant,), now=NOW, mode=mode)
    assert (result.effect, result.reason, result.runtime_authorization) == ("DENY", "REVIEW_ONLY", False)


def test_naive_clock_is_rejected(review):
    module, model, request, grant = review
    result = module.evaluate_review(model, request, (grant,), now=NOW.replace(tzinfo=None))
    assert (result.effect, result.reason) == ("DENY", "CLOCK_INVALID")


@pytest.mark.parametrize(
    "request_changes,grant_changes",
    [
        ({"purpose": " "}, {"purposes": (" ",)}),
        ({"labels": ("",)}, {"labels": ("",)}),
        ({"policy_revision": " "}, {"policy_revision": " "}),
    ],
)
def test_blank_policy_attributes_cannot_be_approved_by_matching_blank_grants(review, request_changes, grant_changes):
    module, model, request, grant = review
    result = module.evaluate_review(
        model, replace(request, **request_changes), (replace(grant, **grant_changes),), now=NOW
    )
    assert (result.effect, result.reason) == ("DENY", "PURPOSE_OR_CLASSIFICATION_UNCONFIRMED")


def test_model_cannot_enable_production_use(review):
    module, model, request, grant = review
    model["production_enabled"] = True
    result = module.evaluate_review(model, request, (grant,), now=NOW)
    assert (result.effect, result.reason, result.runtime_authorization) == ("DENY", "REVIEW_ONLY", False)


def test_policy_catalog_rejects_missing_operation_and_unknown_grant():
    review_module()
    spec = importlib.util.spec_from_file_location("t011_validator", ROOT / "scripts/validate_access_control_model.py")
    assert spec is not None and spec.loader is not None
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    model = json.loads((ROOT / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))
    validator.validate_model(model, ROOT)
    incomplete = json.loads(json.dumps(model))
    incomplete["operations"].pop()
    with pytest.raises(ValueError, match="OPERATION_CATALOG_DRIFT"):
        validator.validate_model(incomplete, ROOT)
    unexpected = json.loads(json.dumps(model))
    unexpected["roles"][0]["permission_review"]["asset.read"] = "ALLOW"
    with pytest.raises(ValueError, match="MODEL_SCHEMA_INVALID"):
        validator.validate_model(unexpected, ROOT)
    complete_entities = json.loads(json.dumps(model))
    if "user_identities" not in complete_entities["entities"]:
        complete_entities["entities"].append("user_identities")
    validator.validate_model(complete_entities, ROOT)
    complete_entities["entities"].remove("user_identities")
    with pytest.raises(ValueError, match="MODEL_SCHEMA_INVALID"):
        validator.validate_model(complete_entities, ROOT)


def test_task_progress_grows_with_evidence_and_rejects_false_classification(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "t011_progress_check", ROOT / "scripts/validate_stage_one_completion.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    classify = getattr(module, "partial_task_ids", None)
    assert callable(classify), "task evidence classifier is missing"
    rows = [
        {"task_id": "T001", "status": "PARTIAL_VERIFIED_SCOPE", "completed_steps": [{"evidence": ["fixture-a"]}]},
        {"task_id": "T002", "status": "NO_FULL_TASK_VERIFICATION_EVIDENCE", "completed_steps": []},
    ]
    assert classify({"tasks": rows}) == {"T001"}
    rows[1] = {"task_id": "T002", "status": "PARTIAL_VERIFIED_SCOPE", "completed_steps": [{"evidence": ["fixture-b"]}]}
    assert classify({"tasks": rows}) == {"T001", "T002"}
    inconsistent = json.loads(json.dumps(rows))
    inconsistent[1]["completed_steps"] = []
    with pytest.raises(AssertionError):
        classify({"tasks": inconsistent})
    unsupported = json.loads(json.dumps(rows))
    unsupported[1]["completed_steps"] = [{"evidence": []}]
    with pytest.raises(AssertionError):
        classify({"tasks": unsupported})
    hidden = json.loads(json.dumps(rows))
    hidden[1]["status"] = "NO_FULL_TASK_VERIFICATION_EVIDENCE"
    with pytest.raises(AssertionError):
        classify({"tasks": hidden})
    with pytest.raises(AssertionError):
        classify({"tasks": [rows[0], rows[0]]})
