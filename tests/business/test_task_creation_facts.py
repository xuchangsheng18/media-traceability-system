"""Dedicated task facts remain unknown without real institutional providers."""

import importlib
import importlib.util
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest
from business_app.errors import BusinessError
from business_app.permissions.rule_types import RuleTarget

from tests.business.test_task_creation_authority import NOW
from tests.business.test_task_creation_materials import canonical
from tests.business.test_task_creation_sql_authority import authority_fixture, scoped_fixture


def test_task_creation_facts_component_exists():
    assert importlib.util.find_spec("business_app.permissions.task_creation_facts") is not None, (
        "Dedicated task facts component is not implemented; not an old authorization bypass"
    )


def module():
    return importlib.import_module("business_app.permissions.task_creation_facts")


def target_for(context):
    request = context.request
    return RuleTarget(
        request.actor.org_id,
        "asset",
        request.asset_id,
        1,
        request.case_id,
        "analysis",
        None,
        request_digest=context.authorization_request_digest,
    )


class SelfOwnedCapabilityFixture:
    """Protocol fixture only: no actual provider, release, licence or DB locks."""

    def __init__(self):
        self.mutate = lambda state, connection: state
        self.version = "self-owned/status/1"
        self.deadline = NOW + timedelta(seconds=60)
        self.value = True
        self.calls = 0
        self.input_mutation = lambda context, observation: None
        self.evidence_ref = "self-owned/release-license-basis"

    def read(self, context, observation, *, connection):
        from business_app.data_scope import AccessMode
        from business_app.scope_context import current_data_scope

        self.calls += 1
        m = module()
        refs = set()
        for handler in observation.as_dict()["required_capability_refs"]["handlers"]:
            refs.add(canonical(dict(kind="handler", reference=handler)))
            for model in handler["model_dependencies"]:
                refs.add(canonical(dict(kind="model", reference=model)))
        scope = current_data_scope()
        assert scope is not None
        mode = "LOOKUP_READ_ONLY" if scope.mode is AccessMode.LOOKUP else "CASE_SHARE_LOCKED"
        items = tuple(
            m.CurrentCapabilityItem(
                ref,
                True,
                self.value,
                True,
                "self-owned/source",
                self.version,
                self.evidence_ref,
                self.deadline,
            )
            for ref in sorted(refs)
        )
        state = m.CurrentCapabilityState(connection, connection.get_transaction(), mode, items)
        self.input_mutation(context, observation)
        return self.mutate(state, connection)


def test_missing_capability_and_receipt_semantics_return_only_two_unknown_core_facts():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    reader = module().TaskCreationFactsReader(authority, clock=lambda: NOW)
    target = target_for(context)
    with scoped_fixture(context, database, connection):
        facts = reader.read(context.principal, "createTask", target, connection=connection)
    assert facts.principal == context.principal and facts.target == target
    assert dict(facts.checks) == {"model_task_version": None, "capability": None}
    assert facts.valid_until == (NOW + timedelta(minutes=5)).timestamp()
    assert "classification" not in facts.checks
    with pytest.raises(TypeError):
        facts.checks["model_task_version"] = True


@pytest.mark.parametrize("case", [False, True])
def test_explicit_fixture_protocol_binds_every_reference_but_does_not_invent_adoption(case):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    fixture = SelfOwnedCapabilityFixture()
    reader = module().TaskCreationFactsReader(authority, capability_reader=fixture, clock=lambda: NOW)
    with scoped_fixture(context, database, connection, case=case):
        facts = reader.read(context.principal, "createTask", target_for(context), connection=connection)
    assert fixture.calls == 1
    assert dict(facts.checks) == {"model_task_version": None, "capability": True}
    assert facts.valid_until == fixture.deadline.timestamp()


def test_stable_digest_excludes_sampling_clock_and_renewable_capability_deadline():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    fixture = SelfOwnedCapabilityFixture()
    now = [NOW]
    authority.clock = lambda: now[0]
    reader = module().TaskCreationFactsReader(authority, capability_reader=fixture, clock=lambda: now[0])
    with scoped_fixture(context, database, connection):
        first = reader.read(context.principal, "createTask", target_for(context), connection=connection)
        now[0] += timedelta(seconds=1)
        fixture.deadline += timedelta(seconds=30)
        second = reader.read(context.principal, "createTask", target_for(context), connection=connection)
        fixture.version += "/changed"
        changed = reader.read(context.principal, "createTask", target_for(context), connection=connection)
    assert first.version_digest == second.version_digest
    assert first.valid_until < second.valid_until
    assert changed.version_digest != second.version_digest


def test_changed_release_or_license_evidence_ref_invalidates_stable_facts():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    fixture = SelfOwnedCapabilityFixture()
    reader = module().TaskCreationFactsReader(authority, capability_reader=fixture, clock=lambda: NOW)
    with scoped_fixture(context, database, connection):
        first = reader.read(context.principal, "createTask", target_for(context), connection=connection)
        fixture.evidence_ref += "/changed"
        current = reader.read(context.principal, "createTask", target_for(context), connection=connection)
    assert current.version_digest != first.version_digest


@pytest.mark.parametrize("value", [None, False])
def test_explicit_unknown_and_known_denial_are_not_promoted_to_true(value):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    fixture = SelfOwnedCapabilityFixture()
    fixture.value = value
    reader = module().TaskCreationFactsReader(authority, capability_reader=fixture, clock=lambda: NOW)
    with scoped_fixture(context, database, connection):
        facts = reader.read(context.principal, "createTask", target_for(context), connection=connection)
    assert facts.checks["capability"] is value and facts.checks["model_task_version"] is None


@pytest.mark.parametrize(
    "defect",
    [
        "dictionary",
        "wrong-connection",
        "wrong-transaction",
        "wrong-mode",
        "missing-item",
        "extra-item",
        "wrong-reference",
        "noncanonical-reference",
        "missing-source",
        "missing-version",
        "missing-evidence",
        "expired",
        "naive-deadline",
        "integer-boolean",
        "list-items",
        "transaction-switched",
    ],
)
def test_malformed_or_unbound_current_provider_results_are_unavailable(defect):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    fixture = SelfOwnedCapabilityFixture()

    def alter(state, current):
        item = state.items[0]
        if defect == "dictionary":
            return dict(capability=True)
        if defect == "wrong-connection":
            return replace(state, connection=object())
        if defect == "wrong-transaction":
            return replace(state, transaction=object())
        if defect == "wrong-mode":
            return replace(state, mode="CASE_SHARE_LOCKED")
        if defect == "missing-item":
            return replace(state, items=())
        if defect == "extra-item":
            return replace(state, items=state.items + state.items)
        if defect == "list-items":
            return replace(state, items=list(state.items))
        if defect == "transaction-switched":
            current.transaction = object()
            return replace(state, transaction=current.transaction)
        if defect == "wrong-reference":
            item = replace(item, reference_bytes=b'{"kind":"handler","reference":{}}')
        elif defect == "noncanonical-reference":
            item = replace(item, reference_bytes=b" " + item.reference_bytes)
        elif defect == "missing-source":
            item = replace(item, source_identity="")
        elif defect == "missing-version":
            item = replace(item, source_version="")
        elif defect == "missing-evidence":
            item = replace(item, evidence_ref="")
        elif defect == "expired":
            item = replace(item, valid_until=NOW)
        elif defect == "naive-deadline":
            item = replace(item, valid_until=NOW.replace(tzinfo=None))
        else:
            item = replace(item, available=1)
        return replace(state, items=(item,))

    fixture.mutate = alter
    reader = module().TaskCreationFactsReader(authority, capability_reader=fixture, clock=lambda: NOW)
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError) as error:
        reader.read(context.principal, "createTask", target_for(context), connection=connection)
    assert (error.value.code, error.value.http_status) == ("CONDITIONAL_FACTS_UNAVAILABLE", 503)


@pytest.mark.parametrize("field", ["actor", "operation", "case", "asset", "B", "purpose"])
def test_actual_principal_target_and_B_are_bound_before_any_sql(field):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    reader = module().TaskCreationFactsReader(authority, clock=lambda: NOW)
    principal, target, operation = context.principal, target_for(context), "createTask"
    if field == "actor":
        principal = replace(principal, subject="different-subject")
    elif field == "operation":
        operation = "getAsset"
    elif field == "case":
        target = replace(target, case_id=uuid4())
    elif field == "asset":
        target = replace(target, object_id=uuid4())
    elif field == "B":
        target = replace(target, request_digest="b" * 64)
    else:
        target = replace(target, purpose="download")
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError):
        reader.read(principal, operation, target, connection=connection)
    assert connection.statements == []


def test_existing_case_root_requires_connection_and_never_opens_a_recursive_transaction():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    reader = module().TaskCreationFactsReader(authority, clock=lambda: NOW)
    with scoped_fixture(context, database, connection, case=True), pytest.raises(BusinessError):
        reader.read(context.principal, "createTask", target_for(context))
    assert connection.statements == []


def test_provider_receives_detached_context_and_metadata_not_the_core_snapshots():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    fixture = SelfOwnedCapabilityFixture()

    def mutate_input(supplied_context, observation):
        object.__setattr__(supplied_context.principal.actor.user_id, "int", 0)
        object.__setattr__(observation, "canonical_bytes", b'{"capability":true}')

    fixture.input_mutation = mutate_input
    reader = module().TaskCreationFactsReader(authority, capability_reader=fixture, clock=lambda: NOW)
    with scoped_fixture(context, database, connection):
        facts = reader.read(context.principal, "createTask", target_for(context), connection=connection)
    assert context.principal.actor.user_id.int != 0
    assert facts.principal.actor.user_id == context.principal.actor.user_id
    assert dict(facts.checks) == {"model_task_version": None, "capability": True}
