"""Internal scope inputs never stand in for authentication or widen a request."""

import importlib
import importlib.util
import math
import re
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest
from business_app.errors import BusinessError
from business_app.permissions.rule_types import (
    AuthorizationEvidence,
    ExecutionSubject,
    RuleTarget,
    WorkAuthorizationEvidence,
)
from business_app.permissions.types import Principal
from business_app.types import Actor

ACTOR = Actor(UUID(int=1), UUID(int=2))
CASE = UUID(int=3)
TASK = UUID(int=4)
SOURCE = UUID(int=5)
ROOT = Path(__file__).resolve().parents[2]


def api():
    name = "business_app.data_scope"
    assert importlib.util.find_spec(name) is not None, "SERVER_BOUND_DATA_SCOPE_CAPABILITY_REQUIRED"
    catalog = "business_app.scope_catalog"
    assert importlib.util.find_spec(catalog) is not None, "FIXED_SCOPE_CATALOG_CAPABILITY_REQUIRED"
    return importlib.import_module(name), importlib.import_module(catalog)


def evidence():
    principal = Principal(ACTOR, "https://identity.example.test", "synthetic-user", 2000)
    target = RuleTarget(ACTOR.org_id, "task", TASK, 1, CASE, "analysis", None, (SOURCE,), "a" * 64)
    return AuthorizationEvidence(principal, "getTask", target, "b" * 64, "c" * 64, "policy-v1", "generation-v1", 1005.0)


def scope_args(module):
    return dict(
        actor=ACTOR,
        mode=module.AccessMode.CASE,
        operation_id="getTask",
        case_id=CASE,
        lookup=None,
        task_binding=None,
        evidence_binding="a" * 64,
    )


@pytest.mark.parametrize("bad", [None, UUID(int=0), "00000000-0000-0000-0000-000000000003"])
def test_case_requires_exact_nonzero_case_and_actor(bad):
    module, _ = api()
    with pytest.raises(BusinessError) as caught:
        module.DataScope(**(scope_args(module) | {"case_id": bad}))
    assert (caught.value.code, caught.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)


@pytest.mark.parametrize(
    "actor", [None, Actor(cast(Any, "fake-user"), ACTOR.org_id), Actor(ACTOR.user_id, UUID(int=0))]
)
def test_invalid_server_actor_is_not_coerced(actor):
    module, _ = api()
    with pytest.raises(BusinessError):
        module.DataScope(**(scope_args(module) | {"actor": actor}))


def test_valid_case_is_immutable_but_is_not_an_authorization_decision():
    module, _ = api()
    scope = module.DataScope(**scope_args(module))
    assert scope.actor == ACTOR and scope.case_id == CASE
    assert not hasattr(scope, "allowed") and not hasattr(scope, "bearer")
    with pytest.raises(FrozenInstanceError):
        scope.case_id = UUID(int=6)


@pytest.mark.parametrize("mode", ["ORGANIZATION", "LOOKUP"])
def test_org_and_lookup_cannot_carry_case_or_task(mode):
    module, _ = api()
    values = scope_args(module) | {"mode": getattr(module.AccessMode, mode)}
    if mode == "LOOKUP":
        values.update(lookup=module.LookupKey("task", TASK), evidence_binding=None)
    with pytest.raises(BusinessError):
        module.DataScope(**values)
    values.update(case_id=None, task_binding=module.TaskBinding(TASK))
    with pytest.raises(BusinessError):
        module.DataScope(**values)


def test_valid_lookup_has_exact_registered_kind_id_and_operation_without_evidence():
    module, catalog = api()
    key = module.LookupKey("task", TASK)
    scope = module.DataScope(ACTOR, module.AccessMode.LOOKUP, "getTask", None, key, None, None)
    assert scope.lookup.identifier == TASK and scope.case_id is None
    spec = catalog.lookup_spec(scope.lookup.kind)
    assert (spec.table, spec.key) == ("analysis_task", "task_id")
    assert "getTask" in spec.operation_ids
    assert not {"snapshot", "details", "artifact_ref", "claim_text", "credentials"} & set(spec.projection)
    with pytest.raises(BusinessError):
        replace(scope, operation_id="getPolicy")
    with pytest.raises(BusinessError):
        replace(scope, evidence_binding="a" * 64)


@pytest.mark.parametrize(
    "change",
    [
        dict(mode="CASE"),
        dict(mode="all"),
        dict(operation_id="arbitraryAllow"),
        dict(operation_id="devLogin"),
        dict(operation_id="getModelHealth"),
        dict(evidence_binding=None),
        dict(evidence_binding="a" * 63),
        dict(evidence_binding="A" * 64),
    ],
)
def test_unknown_mode_kind_operation_and_boolean_versions_are_rejected(change):
    module, _ = api()
    with pytest.raises(BusinessError):
        module.DataScope(**(scope_args(module) | change))


@pytest.mark.parametrize(
    "kind,identifier",
    [("analysis_task;DROP TABLE mt.users", TASK), ("unknown", TASK), ("task", UUID(int=0)), ("task", str(TASK))],
    ids=["sql-injection-kind", "unknown-kind", "zero-id", "string-id"],
)
def test_lookup_key_cannot_name_a_table_or_coerce_an_id(kind, identifier):
    module, _ = api()
    with pytest.raises(BusinessError):
        module.LookupKey(kind, identifier)


@pytest.mark.parametrize(
    "run,result", [(True, None), (0, None), (-1, None), (1.0, None), (None, 1), (1, True), (1, 0), (1, -1)]
)
def test_task_versions_must_be_exact_positive_integers_and_result_requires_run(run, result):
    module, _ = api()
    with pytest.raises(BusinessError):
        module.TaskBinding(TASK, run, result)


def test_task_and_part_bindings_preserve_real_pre_object_version_upload():
    module, _ = api()
    task = module.TaskBinding(TASK, 2, 3)
    assert (task.task_id, task.run_version, task.result_version) == (TASK, 2, 3)
    part = module.ResourceBinding("upload_part", UUID(int=7), part_no=1)
    assert part.part_no == 1 and part.row_version is None
    with pytest.raises(BusinessError):
        module.ResourceBinding("upload_part", UUID(int=7))
    with pytest.raises(BusinessError):
        module.ResourceBinding("task", TASK, row_version=True)
    with pytest.raises(BusinessError):
        module.ResourceBinding("task", TASK, part_no=1)


def test_evidence_renewal_preserves_binding_but_scope_change_does_not():
    module, _ = api()
    proof = evidence()
    original = module.from_evidence(proof, clock=lambda: 1000.0)
    refreshed = module.from_evidence(replace(proof, valid_until=1008.0), clock=lambda: 1001.0)
    assert original.evidence_binding == refreshed.evidence_binding
    for target in [
        replace(proof.target, case_id=UUID(int=6)),
        replace(proof.target, object_id=UUID(int=7)),
        replace(proof.target, object_version=2),
        replace(proof.target, source_ids=(UUID(int=8),)),
    ]:
        changed = module.from_evidence(replace(proof, target=target), clock=lambda: 1000.0)
        assert changed.evidence_binding != original.evidence_binding
    for changed in [
        replace(proof, operation_id="getForensics"),
        replace(proof, policy_version="policy-v2"),
        replace(proof, recovery_generation="generation-v2"),
        replace(proof, principal=replace(proof.principal, subject="different-user")),
        replace(proof, principal=replace(proof.principal, actor=Actor(UUID(int=9), ACTOR.org_id))),
    ]:
        assert module.from_evidence(changed, clock=lambda: 1000.0).evidence_binding != original.evidence_binding


@pytest.mark.parametrize("value", [1000.0, 999.0, math.nan, math.inf, True, "1005"])
def test_expired_or_malformed_evidence_cannot_create_a_live_scope(value):
    module, _ = api()
    with pytest.raises(BusinessError):
        module.from_evidence(replace(evidence(), valid_until=value), clock=lambda: 1000.0)


@pytest.mark.parametrize("value", [math.nan, math.inf, True, "1000"])
def test_invalid_clock_cannot_create_a_live_scope(value):
    module, _ = api()
    with pytest.raises(BusinessError):
        module.from_evidence(evidence(), clock=lambda: value)


def test_target_org_and_object_case_cannot_be_replaced_or_omitted():
    module, _ = api()
    proof = evidence()
    for target in [
        replace(proof.target, org_id=UUID(int=9)),
        replace(proof.target, case_id=None),
        replace(proof.target, kind="policy"),
        replace(proof.target, object_version=True),
    ]:
        with pytest.raises(BusinessError):
            module.from_evidence(replace(proof, target=target), clock=lambda: 1000.0)


def test_unit_policy_is_unit_scoped_and_does_not_invent_a_case():
    module, _ = api()
    proof = replace(
        evidence(),
        operation_id="getPolicy",
        target=RuleTarget(ACTOR.org_id, "policy", UUID(int=10), 1, None, None, "retention"),
    )
    result = module.from_evidence(proof, clock=lambda: 1000.0)
    assert result.mode is module.AccessMode.ORGANIZATION and result.case_id is None
    assert result.task_binding is None and result.lookup is None


def test_work_identity_and_mapping_are_bound_without_fabricating_a_jwt():
    module, _ = api()
    subject = ExecutionSubject(ACTOR, UUID(int=11), "map-v1", "upload_validation", UUID(int=12))
    target = RuleTarget(ACTOR.org_id, "upload", subject.work_id, 1, CASE, "upload", None)
    proof = WorkAuthorizationEvidence(
        subject, "validateUploadWork", target, "b" * 64, "c" * 64, "policy-v1", "generation-v1", 1005.0
    )
    result = module.from_evidence(proof, clock=lambda: 1000.0)
    assert result.actor == ACTOR and result.mode is module.AccessMode.CASE
    assert not hasattr(result, "issuer") and not hasattr(result, "expires_at")
    changed = replace(proof, subject=replace(subject, mapping_version="map-v2"))
    assert module.from_evidence(changed, clock=lambda: 1000.0).evidence_binding != result.evidence_binding
    with pytest.raises(BusinessError):
        module.from_evidence(replace(proof, target=replace(target, object_id=UUID(int=13))), clock=lambda: 1000.0)


@pytest.mark.parametrize("bad_target", [None, {"kind": "upload"}])
def test_malformed_work_target_is_an_opaque_refusal_not_an_attribute_error(bad_target):
    module, _ = api()
    subject = ExecutionSubject(ACTOR, UUID(int=11), "map-v1", "upload_validation", UUID(int=12))
    proof = WorkAuthorizationEvidence(
        subject, "validateUploadWork", bad_target, "b" * 64, "c" * 64, "policy-v1", "generation-v1", 1005.0
    )
    with pytest.raises(BusinessError) as caught:
        module.from_evidence(proof, clock=lambda: 1000.0)
    assert (caught.value.code, caught.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)


def test_same_source_set_has_stable_binding_independent_of_query_order():
    module, _ = api()
    proof = evidence()
    first = replace(proof, target=replace(proof.target, source_ids=(UUID(int=5), UUID(int=6))))
    second = replace(proof, target=replace(proof.target, source_ids=(UUID(int=6), UUID(int=5))))
    assert (
        module.from_evidence(first, clock=lambda: 1000.0).evidence_binding
        == module.from_evidence(second, clock=lambda: 1000.0).evidence_binding
    )


def test_catalog_classifies_every_source_table_without_claiming_crud_coverage():
    _, catalog = api()
    names = set()
    for file in (ROOT / "backend/business_migrations").glob("*.sql"):
        names.update(re.findall(r"CREATE TABLE mt\.(\w+)\s*\(", file.read_text(encoding="utf8")))
    assert len(names) == 64 and set(catalog.TABLE_SCOPES) == names
    for name in ("approval_request", "approval_decision", "operation_token", "audit_event"):
        assert catalog.TABLE_SCOPES[name].scope_class == "MIXED"
    assert catalog.TABLE_SCOPES["authorization_epoch"].runtime_select is False
    assert catalog.TABLE_SCOPES["user_identities"].runtime_select is False
    assert catalog.TABLE_SCOPES["case_membership"].scope_class == "DIRECTORY"
    assert catalog.TABLE_SCOPES["policy_registry"].scope_class == "ORG"
    assert catalog.TABLE_SCOPES["analysis_task"].scope_class == "CASE"
    with pytest.raises(TypeError):
        catalog.TABLE_SCOPES["analysis_task"] = catalog.TABLE_SCOPES["policy_registry"]
