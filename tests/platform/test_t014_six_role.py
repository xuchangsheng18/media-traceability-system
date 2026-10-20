"""Confirmed 246 cells are isolated rule inputs, never production role seeds."""

import hashlib
import importlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from business_app.errors import BusinessError
from business_app.permissions.types import Principal
from business_app.types import Actor

ROOT = Path(__file__).resolve().parents[2]
SOURCE = json.loads((ROOT / "docs/08-security/t014-six-role-rule-proposal.json").read_text(encoding="utf8"))
NOW = 2_000_000_000
CELLS = [
    (p["permission"], role, cell["condition_ref"]) for p in SOURCE["permissions"] for role, cell in p["cells"].items()
]


def module(name):
    assert (ROOT / f"backend/business_app/permissions/{name}.py").is_file(), f"T014 {name} is missing"
    return importlib.import_module("business_app.permissions." + name)


def rule_input_digest():
    value = {
        "revision": SOURCE["revision"],
        "roles": [r["code"] for r in SOURCE["roles"]],
        "conditions": SOURCE["conditions"],
        "cells": {
            p["permission"]: {role: c["condition_ref"] for role, c in p["cells"].items()} for p in SOURCE["permissions"]
        },
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")
    ).hexdigest()


def rules():
    policy = module("six_role")
    types = module("rule_types")
    snapshot = types.RuleSnapshot(SOURCE["revision"], rule_input_digest(), "synthetic-isolated-generation", NOW + 3600)
    return policy.SixRoleRules(snapshot, clock=lambda: float(NOW))


def facts(permission, roles, providers=None):
    types = module("rule_types")
    principal = Principal(Actor(uuid4(), uuid4()), "https://synthetic.example.test", "synthetic-subject", NOW + 600)
    active = tuple(types.ActiveRole(uuid4(), code, uuid4(), 1, 1, None) for code in roles)
    provided = roles if providers is None else providers
    ids = tuple(r.role_id for r in active if r.code in provided)
    return types.RoleFacts(principal, permission, bool(ids), active, ids, "1" * 64)


@pytest.mark.parametrize("permission,role,condition", CELLS)
def test_all_246_cells_match_confirmed_input(permission, role, condition):
    policy = rules()
    value = facts(permission, [role])
    if condition is None:
        with pytest.raises(BusinessError) as caught:
            policy.entry(value)
        assert caught.value.http_status == 403
    else:
        assert policy.entry(value) == (condition,)


def test_cell_totals_and_legacy_role_model_are_not_rewritten():
    assert len(CELLS) == 246
    assert sum(c is not None for _, _, c in CELLS) == 72
    assert sum(c is None for _, _, c in CELLS) == 174
    assert all(c["runtime_allow"] is False for p in SOURCE["permissions"] for c in p["cells"].values())
    for name, digest in SOURCE["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize(
    "writer", ["system_admin", "data_admin", "algorithm_admin", "business_reviewer", "case_investigator"]
)
def test_auditor_writer_combination_is_denied(writer):
    with pytest.raises(BusinessError) as caught:
        rules().entry(facts("audit.read", ["auditor", writer]))
    assert caught.value.http_status == 403


def test_nonmatching_role_still_triggers_conflict():
    with pytest.raises(BusinessError) as caught:
        rules().entry(facts("asset.upload", ["case_investigator", "system_admin"], ["case_investigator"]))
    assert caught.value.http_status == 403


@pytest.mark.parametrize(
    "roles", [["unknown"], ["system_admin", "algorithm_admin"], ["data_admin", "business_reviewer"]]
)
def test_unknown_or_unregistered_combination_is_denied(roles):
    with pytest.raises(BusinessError) as caught:
        rules().entry(facts("identity.read", roles))
    assert caught.value.http_status == 403


def test_registered_data_investigator_combination_preserves_condition_branch():
    assert rules().entry(facts("asset.upload", ["data_admin", "case_investigator"])) == ("INGEST",)
    assert rules().entry(facts("policy.manage", ["data_admin", "case_investigator"], ["data_admin"])) == (
        "POLICY_RETENTION",
    )


@pytest.mark.parametrize(
    "purpose,count",
    [
        ("review", 1),
        ("confirmation", 1),
        ("seal", 2),
        ("report_export", 2),
        ("training_feedback", 2),
        ("model_release", 2),
    ],
)
def test_approval_rules_have_exact_independent_people_and_1800_second_ttl(purpose, count):
    value = rules().approval_rule(purpose, SOURCE["revision"])
    assert (value.version, value.ttl_seconds, value.independent_approvers) == (SOURCE["revision"], 1800, count)


@pytest.mark.parametrize("purpose,version", [("audit_export", SOURCE["revision"]), ("review", "wrong-version")])
def test_unknown_approval_purpose_or_version_is_unavailable(purpose, version):
    with pytest.raises(BusinessError) as caught:
        rules().approval_rule(purpose, version)
    assert caught.value.http_status == 503


@pytest.mark.parametrize(
    "change",
    ["wrong_digest", "duplicate_role", "expired_role", "malformed_boolean", "unbound_provider", "expired_snapshot"],
)
def test_invalid_rule_facts_do_not_become_function_eligibility(change):
    policy = rules()
    value = facts("identity.read", ["case_investigator"])
    if change == "wrong_digest":
        value = replace(value, version_digest="not-a-sha256")
    elif change == "duplicate_role":
        value = replace(value, active_roles=value.active_roles * 2)
    elif change == "expired_role":
        value = replace(value, active_roles=(replace(value.active_roles[0], expires_at=float(NOW)),))
    elif change == "malformed_boolean":
        value = replace(value, eligible="true")
    elif change == "unbound_provider":
        value = replace(value, permission_role_ids=(uuid4(),))
    else:
        policy = module("six_role").SixRoleRules(replace(policy.snapshot, valid_until=NOW), clock=lambda: float(NOW))
    with pytest.raises(BusinessError) as caught:
        policy.entry(value)
    assert caught.value.http_status == 503


@pytest.mark.parametrize("change,status", [("digest", 503), ("principal", 503), ("revoked", 403)])
def test_entry_authority_rechecks_exact_facts_without_cross_request_allow_cache(change, status):
    policy = rules()
    value = facts("identity.read", ["case_investigator"])
    altered = replace(value, version_digest="2" * 64)
    if change == "principal":
        altered = replace(value, principal=replace(value.principal, subject="different"))
    elif change == "revoked":
        altered = replace(value, eligible=False, permission_role_ids=())
    responses = iter([value, altered])
    reader = SimpleNamespace(read_roles=lambda *a, **k: next(responses))
    authority = module("six_role").SixRoleEntryAuthority(reader, policy)
    with pytest.raises(BusinessError) as caught:
        authority.check(value.principal, value.permission)
    assert caught.value.http_status == status
