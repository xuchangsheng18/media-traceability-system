"""Pure catalog and object-fact logic; SQL enforcement is verified separately."""

from copy import deepcopy
from typing import Any, cast
from uuid import UUID

import pytest
from business_app.data_scope import ScopeMetadata
from business_app.errors import BusinessError
from business_app.permissions import object_facts
from business_app.permissions.conditional import REQUIREMENTS
from business_app.permissions.object_facts import ObjectFactsReader
from business_app.permissions.rule_types import ConditionFacts, RuleTarget
from business_app.permissions.types import Principal
from business_app.scope_catalog import lookup_spec, registered_operation
from business_app.types import Actor

ACTOR, ORG, CASE, APPROVAL, TASK, SOURCE = (UUID(int=value) for value in range(1, 7))
PRINCIPAL = Principal(Actor(ACTOR, ORG), "https://identity.example.test", "self-owned", 2000000000)
NOW = 1700000000.0


def envelopes():
    common = dict(org_id=str(ORG), case_id=str(CASE), row_version=2, created_by=str(ACTOR))
    approval = dict(
        record=dict(
            common,
            approval_id=str(APPROVAL),
            object_type="task",
            object_id=str(TASK),
            object_version=3,
            purpose="seal",
            requested_by=str(ACTOR),
            state="APPROVED",
            expires_at="2030-01-01T00:00:00+00:00",
            policy_version="self-owned-policy-1",
            run_version=2,
            result_version=4,
        ),
        memberships=[dict(expires_at=None)],
        related=[],
        sources=[],
        same_org=True,
    )
    task = dict(
        record=dict(
            common,
            row_version=3,
            task_id=str(TASK),
            asset_id=str(UUID(int=7)),
            run_version=2,
            result_version=4,
            state="SUCCEEDED",
            policy_version="self-owned-policy-1",
        ),
        memberships=[dict(expires_at=None)],
        related=[],
        sources=[
            dict(
                source_id=str(SOURCE),
                org_id=str(ORG),
                case_id=str(CASE),
                row_version=1,
                authorization_version="self-owned-source-1",
                authorization_status="verified",
                expires_at=None,
                purpose=["analysis"],
            )
        ],
        same_org=True,
    )
    return [approval, task]


def target():
    return RuleTarget(ORG, "approval", APPROVAL, 2, CASE, "seal", None, request_digest="a" * 64)


def test_issuance_is_a_fixed_approval_lookup_and_seal_remains_internal():
    assert object_facts.OPERATION_KINDS.get("issueOperationToken") == "approval"
    assert object_facts.BODY_SCHEMAS.get("issueOperationToken") == "OperationTokenRequest"
    assert "issueOperationToken" in lookup_spec("approval").operation_ids
    assert "issueOperationToken" in lookup_spec("task").operation_ids
    assert registered_operation("sealEvidence")
    assert "sealEvidence" in lookup_spec("task").operation_ids
    assert "sealEvidence" not in object_facts.SUPPORTED_OPERATIONS
    assert not registered_operation("arbitraryAction")


def test_case_confirmation_requires_complete_sql_and_classification_conditions():
    assert REQUIREMENTS.get("CONFIRM_CASE") == (
        "same_org",
        "case",
        "case_request_purpose",
        "confirmation_subject",
        "object_binding",
        "source",
        "analysis_purpose",
        "classification",
    )
    assert "CONFIRM_MODEL" not in REQUIREMENTS


@pytest.mark.parametrize("change", ["object_id", "object_version", "purpose"])
def test_http_claims_must_equal_authoritative_approval_metadata(monkeypatch, change):
    class Lookup:
        def __init__(self, *args, **kwargs):
            pass

        def read(self, principal, operation_id, key):
            assert operation_id == "issueOperationToken" and key.kind == "approval" and key.identifier == APPROVAL
            return ScopeMetadata(target(), envelopes()[0]["record"], {}, "c" * 64, NOW + 5)

    monkeypatch.setattr(object_facts, "SqlScopeLookup", Lookup)
    reader = ObjectFactsReader(cast(Any, object()), clock=lambda: NOW)
    body = dict(approval_id=str(APPROVAL), object_id=str(TASK), object_version=3, purpose="seal")
    body[change] = str(UUID(int=999)) if change == "object_id" else 99 if change == "object_version" else "review"
    with pytest.raises(BusinessError) as failure:
        reader.resolve_http(PRINCIPAL, "issueOperationToken", {}, {}, body)
    assert failure.value.code == "AUTHORIZATION_OBJECT_STALE"


def test_http_target_uses_server_case_and_approval_row_version(monkeypatch):
    class Lookup:
        def __init__(self, *args, **kwargs):
            pass

        def read(self, principal, operation_id, key):
            assert key.identifier == APPROVAL
            return ScopeMetadata(target(), envelopes()[0]["record"], {}, "c" * 64, NOW + 5)

    monkeypatch.setattr(object_facts, "SqlScopeLookup", Lookup)
    value = ObjectFactsReader(cast(Any, object()), clock=lambda: NOW).resolve_http(
        PRINCIPAL,
        "issueOperationToken",
        {},
        {},
        dict(approval_id=str(APPROVAL), object_id=str(TASK), object_version=3, purpose="seal"),
    )
    assert (value.kind, value.object_id, value.case_id, value.object_version, value.purpose) == (
        "approval",
        APPROVAL,
        CASE,
        2,
        "seal",
    )
    assert isinstance(value.request_digest, str) and len(value.request_digest) == 64


def test_http_uuid_claims_compare_canonical_identifiers(monkeypatch):
    task_id = UUID("abcdefab-cdef-4abc-8def-abcdefabcdef")

    class Lookup:
        def __init__(self, *args, **kwargs):
            pass

        def read(self, principal, operation_id, key):
            record = envelopes()[0]["record"]
            record["object_id"] = str(task_id)
            return ScopeMetadata(target(), record, {}, "c" * 64, NOW + 5)

    monkeypatch.setattr(object_facts, "SqlScopeLookup", Lookup)
    value = ObjectFactsReader(cast(Any, object()), clock=lambda: NOW).resolve_http(
        PRINCIPAL,
        "issueOperationToken",
        {},
        {},
        dict(approval_id=str(APPROVAL).upper(), object_id=str(task_id).upper(), object_version=3, purpose="seal"),
    )
    assert value.object_id == APPROVAL and value.case_id == CASE


def test_seal_consumer_target_validation_is_exact_without_http_registration():
    bound = RuleTarget(ORG, "task", TASK, 3, CASE, "seal", None)
    ObjectFactsReader._validate_target("sealEvidence", bound)
    assert "sealEvidence" not in object_facts.SUPPORTED_OPERATIONS
    for operation in ("arbitraryAction", "createReport"):
        with pytest.raises(BusinessError):
            ObjectFactsReader._validate_target(operation, bound)
    with pytest.raises(BusinessError):
        ObjectFactsReader._validate_target("sealEvidence", target())


def read_facts(monkeypatch, values, *, supplemental=None):
    class Lookup:
        def __init__(self, *args, **kwargs):
            pass

        def load(self, principal, operation_id, key, *, connection):
            assert operation_id == "issueOperationToken"
            return deepcopy(values[0 if key.kind == "approval" else 1])

    monkeypatch.setattr(object_facts, "SqlScopeLookup", Lookup)
    return ObjectFactsReader(cast(Any, object()), clock=lambda: NOW, supplemental=supplemental).read(
        PRINCIPAL,
        "issueOperationToken",
        target(),
        connection=cast(Any, object()),
    )


def test_confirmation_uses_linked_task_sources_and_exact_current_binding(monkeypatch):
    value = read_facts(monkeypatch, envelopes())
    assert all(
        value.checks[name] is True
        for name in (
            "case_request_purpose",
            "confirmation_subject",
            "object_binding",
            "source",
            "analysis_purpose",
        )
    )
    assert "classification" not in value.checks


@pytest.mark.parametrize(
    "change",
    ["object_version", "run_version", "result_version", "policy_version", "purpose", "state", "owner", "task_id"],
)
def test_changed_approval_or_task_never_produces_a_complete_confirmation(monkeypatch, change):
    values = envelopes()
    if change == "object_version":
        values[1]["record"]["row_version"] = 4
    elif change in {"run_version", "result_version", "policy_version"}:
        values[1]["record"][change] = "other-policy" if change == "policy_version" else 99
    elif change == "owner":
        values[0]["record"]["requested_by"] = str(UUID(int=999))
    elif change == "task_id":
        values[1]["record"]["task_id"] = str(UUID(int=999))
    else:
        values[0]["record"][change] = "review" if change == "purpose" else "REVOKED"
    value = read_facts(monkeypatch, values)
    assert any(
        value.checks[name] is False
        for name in (
            "case_request_purpose",
            "confirmation_subject",
            "object_binding",
        )
    )


@pytest.mark.parametrize("change", ["empty", "revoked", "purpose", "expired"])
def test_empty_or_invalid_linked_source_does_not_satisfy_confirmation(monkeypatch, change):
    values = envelopes()
    if change == "empty":
        values[1]["sources"] = []
    else:
        source = values[1]["sources"][0]
        source[{"revoked": "authorization_status", "purpose": "purpose", "expired": "expires_at"}[change]] = {
            "revoked": "revoked",
            "purpose": ["upload"],
            "expired": "2020-01-01T00:00:00+00:00",
        }[change]
    value = read_facts(monkeypatch, values)
    assert value.checks["source"] is False and value.checks["analysis_purpose"] is False


def test_confirmation_requires_the_linked_task_source_not_an_approval_source(monkeypatch):
    values = envelopes()
    values[0]["sources"] = values[1]["sources"]
    values[1]["sources"] = []
    value = read_facts(monkeypatch, values)
    assert value.checks["source"] is False and value.checks["analysis_purpose"] is False


def test_supplemental_adapter_cannot_override_confirmation_sql_binding(monkeypatch):
    class Override:
        def read(self, principal, operation_id, bound, *, connection):
            return ConditionFacts(principal, bound, {"object_binding": True}, "b" * 64, NOW + 60)

    with pytest.raises(BusinessError) as failure:
        read_facts(monkeypatch, envelopes(), supplemental=Override())
    assert failure.value.code == "CONDITIONAL_FACTS_UNAVAILABLE"
