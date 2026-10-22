"""Fixed SQL wrapper tests; self-owned observations never prove real adoption."""

import copy
import importlib
from contextlib import AbstractContextManager, contextmanager
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest
from business_app.data_scope import AccessMode, DataScope, LookupKey
from business_app.errors import BusinessError
from business_app.permissions.context import Evidence, current_authorization, request_authorization
from business_app.permissions.rule_types import AuthorizationEvidence, RuleTarget
from business_app.permissions.task_creation_context import TaskCreationContext, bind_task_creation_context
from business_app.scope_context import BoundTransaction, bind_scope_transaction
from business_app.task_creation_authority import freeze_plan_binding
from sqlalchemy import Connection

from tests.business.test_task_creation_authority import NOW, arranged, limits, sha
from tests.business.test_task_creation_materials import canonical, material_documents


def test_task_creation_sql_authority_component_exists():
    assert importlib.util.find_spec("business_app.task_creation_sql_authority") is not None
    module = importlib.import_module("business_app.task_creation_sql_authority")
    assert hasattr(module, "SqlTaskPlanAuthority"), (
        "Fixed task plan SQL wrapper is not implemented; structural component boundary only"
    )


def sql_fixture():
    documents = material_documents()
    context, proof, metadata, raw = arranged(documents)
    actor, request = context.principal.actor, context.request
    source_id, membership_id = str(uuid4()), str(uuid4())
    facts = dict(
        asset=dict(
            asset_id=str(request.asset_id),
            org_id=str(actor.org_id),
            case_id=str(request.case_id),
            content_id=str(uuid4()),
            source_id=source_id,
            kind="original",
            object_ref=copy.deepcopy(documents["input"]["asset"]["object_ref"]),
            mime="image/png",
            size_bytes=17,
            duration_ms=None,
            width=None,
            height=None,
            state="VALID",
            version=1,
            created_at="2026-10-22T12:00:00.000000Z",
            mapping_version="self-owned/asset/1",
            sha256=documents["input"]["asset"]["sha256"],
        ),
        source=dict(
            source_id=source_id,
            org_id=str(actor.org_id),
            case_id=str(request.case_id),
            authorization_status="verified",
            authorization_version=documents["input"]["asset"]["source_authorization_version"],
            purpose=["analysis"],
            expires_at=None,
            row_version=1,
        ),
        policy=dict(
            policy_id=str(metadata["policy_id"]),
            kind=metadata["policy_kind"],
            version=request.policy_version,
            status="APPROVED",
            row_version=1,
        ),
        case=dict(case_id=str(request.case_id), status="ACTIVE", row_version=1),
        memberships=[dict(membership_id=membership_id, row_version=1, expires_at=None)],
        actor=dict(user_id=str(actor.user_id), org_id=str(actor.org_id), enabled=True, row_version=1),
        organization=dict(org_id=str(actor.org_id), enabled=True, row_version=1),
        head=dict(revision_id=str(metadata["revision_id"]), state="ACTIVE", row_version=1),
        generation=dict(database_oid=7, epoch=1, policy_version=None, policy_sha256=None, recovery_generation=None),
    )
    row = dict(
        revision_id=metadata["revision_id"],
        mapping_id=metadata["mapping_id"],
        mapping_version=metadata["mapping_version"],
        authority_version=proof.authority_version,
        head_row_version=1,
        policy_id=metadata["policy_id"],
        policy_kind=metadata["policy_kind"],
        policy_version=request.policy_version,
        policy_sha256=proof.policy_sha256,
        plan_id=proof.plan_id,
        plan_version=proof.plan_version,
        plan_sha256=proof.plan_sha256,
        capability_id=proof.capability_id,
        capability_version=proof.capability_version,
        capability_sha256=proof.capability_sha256,
        valid_from=metadata["mapping_valid_from"],
        valid_until=metadata["mapping_valid_until"],
        recovery_generation=metadata["recovery_generation"],
        validation_receipt=dict(
            sha256=metadata["validation_receipt_sha256"],
            validator_id=None,
            validator_version=None,
            schema_id=None,
            schema_version=None,
        ),
        required_capability_refs=dict(
            capability_id=proof.capability_id,
            capability_version=proof.capability_version,
            capability_sha256=proof.capability_sha256,
            handlers=documents["capability"]["handlers"],
        ),
        current_state_facts=facts,
    )
    metadata["current_state_facts_bytes"] = canonical(facts)
    metadata["current_state_facts_sha256"] = sha(metadata["current_state_facts_bytes"])
    execution = dict(
        revision_id=metadata["revision_id"],
        head_row_version=1,
        policy_bytes=raw["policy"],
        plan_bytes=raw["plan"],
        capability_bytes=raw["capability"],
        validation_receipt_bytes=metadata["validation_receipt_bytes"],
        current_state_facts=copy.deepcopy(facts),
        valid_until=metadata["mapping_valid_until"],
        recovery_generation=metadata["recovery_generation"],
    )
    return context, proof, metadata, raw, row, execution


class Result:
    def __init__(self, rows=None, scalar=None):
        self.rows, self.scalar = rows, scalar

    def mappings(self):
        return self

    def fetchmany(self, size):
        assert size == 2
        return self.rows[:size]

    def scalar_one(self):
        return self.scalar


class ConnectionDouble:
    """No database: records the fixed statements against explicit self-owned rows."""

    def __init__(self, row, execution):
        self.rows, self.execution = [row], execution
        self.statements = []
        self.read_only = "on"
        self.transaction = object()

    def in_transaction(self):
        return self.transaction is not None

    def get_transaction(self):
        return self.transaction

    def execute(self, statement, parameters=None):
        self.statements.append((str(statement), copy.deepcopy(parameters)))
        if "transaction_read_only" in str(statement):
            return Result(scalar=self.read_only)
        if "task_create_execution_plan" in str(statement):
            return Result(rows=[copy.deepcopy(self.execution)])
        assert "task_create_plan_metadata" in str(statement)
        return Result(rows=copy.deepcopy(self.rows))


class NoInvocationFixtureFence:
    """Protocol-shaped marker; pure wrapper probes must not invoke a fence."""

    def hold(self, connection: Connection, evidence: Evidence) -> None:
        raise AssertionError("Pure wrapper fixture must not perform authorization fencing")

    def finish(self, connection: Connection, evidence: Evidence) -> None:
        raise AssertionError("Pure wrapper fixture must not perform authorization fencing")


@contextmanager
def scoped_fixture(context, database, connection, *, case=False):
    request, principal = context.request, context.principal
    with bind_task_creation_context(context, clock=NOW.timestamp):
        if not case:
            scope = DataScope(
                principal.actor, AccessMode.LOOKUP, "createTask", None, LookupKey("asset", request.asset_id), None, None
            )
            with bind_scope_transaction(BoundTransaction(database, connection, scope, None)):
                yield scope
        else:
            target = RuleTarget(
                principal.actor.org_id,
                "asset",
                request.asset_id,
                1,
                request.case_id,
                "analysis",
                None,
                request_digest=context.authorization_request_digest,
            )
            evidence = AuthorizationEvidence(
                principal,
                "createTask",
                target,
                "a" * 64,
                "b" * 64,
                "self-owned/rules",
                "self-owned/generation",
                principal.expires_at,
            )
            with request_authorization(evidence, NoInvocationFixtureFence(), mutation=True):
                scope = DataScope(principal.actor, AccessMode.CASE, "createTask", request.case_id, None, None, "c" * 64)
                with bind_scope_transaction(BoundTransaction(database, connection, scope, current_authorization())):
                    yield scope


def authority_fixture():
    context, proof, metadata, raw, row, execution = sql_fixture()
    database = object()
    connection = ConnectionDouble(row, execution)
    module = importlib.import_module("business_app.task_creation_sql_authority")
    authority = module.SqlTaskPlanAuthority(database, budgets=limits(), clock=lambda: NOW)
    return module, authority, database, connection, context, proof, metadata, raw


def test_lookup_returns_frozen_limited_observation_and_fixed_bound_sql_without_proof():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    with scoped_fixture(context, database, connection):
        result = authority.read_metadata(context, connection=connection)
    row = result.as_dict()
    assert set(row) == set(connection.rows[0]) and "validation_receipt_bytes" not in row
    assert result.request == context.request and result.request is not context.request
    assert result.request.actor.user_id is not context.request.actor.user_id
    assert result.authorization_request_digest == context.authorization_request_digest
    assert result.sha256 == sha(result.canonical_bytes)
    assert not hasattr(result, "proof") and not hasattr(result, "authorized")
    row["current_state_facts"]["actor"]["enabled"] = False
    assert result.as_dict()["current_state_facts"]["actor"]["enabled"] is True
    statements = [item for item in connection.statements if "task_create_plan_metadata" in item[0]]
    assert len(statements) == 1
    assert statements[0][1] == dict(
        asset=context.request.asset_id,
        case=context.request.case_id,
        scene=context.request.scene,
        policy=context.request.policy_version,
        modules=list(context.request.modules),
        priority=context.request.priority,
    )
    assert all("task_create_execution_plan" not in sql and "FOR SHARE" not in sql for sql, _ in connection.statements)


@pytest.mark.parametrize(
    "change", ["no-context", "wrong-connection", "wrong-database", "ended-transaction", "different-body"]
)
def test_unbound_or_mismatched_request_and_root_are_refused_before_sql(change):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    if change == "no-context":
        with pytest.raises(BusinessError):
            authority.read_metadata(context, connection=connection)
    else:
        with scoped_fixture(context, object() if change == "wrong-database" else database, connection):
            if change == "ended-transaction":
                connection.transaction = None
            supplied = (
                replace(context, authorization_request_digest="b" * 64) if change == "different-body" else context
            )
            actual = (
                ConnectionDouble(connection.rows[0], connection.execution)
                if change == "wrong-connection"
                else connection
            )
            with pytest.raises(BusinessError):
                authority.read_metadata(supplied, connection=actual)
            if change == "wrong-connection":
                assert actual.statements == []
    assert connection.statements == []


def test_lookup_independently_requires_actual_read_only_transaction():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    connection.read_only = "off"
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError) as error:
        authority.read_metadata(context, connection=connection)
    assert error.value.code == "AUTHORITY_SCOPE_INVALID"
    assert len(connection.statements) == 1 and "transaction_read_only" in connection.statements[0][0]


@pytest.mark.parametrize("count", [0, 2, 3])
def test_metadata_missing_or_ambiguous_rows_never_selects_first(count):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    connection.rows = [copy.deepcopy(connection.rows[0]) for _ in range(count)]
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError) as error:
        authority.read_metadata(context, connection=connection)
    assert (error.value.code, error.value.http_status) == ("CONDITIONAL_FACTS_UNAVAILABLE", 503)


@pytest.mark.parametrize(
    "defect",
    [
        "extra-column",
        "extra-receipt",
        "extra-fact",
        "missing-fact",
        "wrong-actor",
        "cross-case",
        "source-org",
        "wrong-policy",
        "wrong-head",
        "bool-head",
        "bool-size",
        "zero-object",
        "wrong-asset-sha",
        "bad-handler-hash",
        "extra-handler",
        "missing-membership",
        "negative-epoch",
        "bad-generation-hash",
        "bad-timestamp",
    ],
)
def test_limited_sql_shapes_and_cross_bindings_are_revalidated(defect):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    row = connection.rows[0]
    facts = row["current_state_facts"]
    if defect == "extra-column":
        row["raw_secret"] = "must-not-leak"
    elif defect == "extra-receipt":
        row["validation_receipt"]["validated"] = True
    elif defect == "extra-fact":
        facts["classification"] = True
    elif defect == "missing-fact":
        del facts["source"]
    elif defect == "wrong-actor":
        facts["actor"]["user_id"] = str(uuid4())
    elif defect == "cross-case":
        facts["asset"]["case_id"] = str(uuid4())
    elif defect == "source-org":
        facts["source"]["org_id"] = str(uuid4())
    elif defect == "wrong-policy":
        facts["policy"]["version"] = "different"
    elif defect == "wrong-head":
        facts["head"]["revision_id"] = str(uuid4())
    elif defect == "bool-head":
        facts["head"]["row_version"] = True
    elif defect == "bool-size":
        facts["asset"]["size_bytes"] = True
    elif defect == "zero-object":
        facts["asset"]["object_ref"]["object_id"] = "00000000-0000-0000-0000-000000000000"
    elif defect == "wrong-asset-sha":
        facts["asset"]["sha256"] = "b" * 64
    elif defect == "bad-handler-hash":
        row["required_capability_refs"]["handlers"][0]["package_sha256"] = "b" * 64
    elif defect == "extra-handler":
        row["required_capability_refs"]["handlers"].append(
            copy.deepcopy(row["required_capability_refs"]["handlers"][0])
        )
    elif defect == "missing-membership":
        facts["memberships"] = []
    elif defect == "negative-epoch":
        facts["generation"]["epoch"] = -1
    elif defect == "bad-generation-hash":
        facts["generation"]["policy_sha256"] = "wrong"
    else:
        facts["source"]["expires_at"] = "2026-10-22T12:00:00"
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError) as error:
        authority.read_metadata(context, connection=connection)
    assert (error.value.code, error.value.http_status) == ("CONDITIONAL_FACTS_UNAVAILABLE", 503)
    assert "must-not-leak" not in str(error.value)


@pytest.mark.parametrize("fraction", ["1", "12", "123", "1234", "12345", "123456"])
def test_pg16_fractional_utc_timestamp_is_losslessly_accepted(fraction):
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    value = "2026-10-22T12:01:00." + fraction + "Z"
    connection.rows[0]["current_state_facts"]["source"]["expires_at"] = value
    with scoped_fixture(context, database, connection):
        result = authority.read_metadata(context, connection=connection)
    assert result.as_dict()["current_state_facts"]["source"]["expires_at"] == value


def test_metadata_resamples_clock_and_cannot_return_an_expired_observation():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    ticks = iter((NOW, NOW + timedelta(seconds=301)))
    authority.clock = lambda: next(ticks)
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError) as error:
        authority.read_metadata(context, connection=connection)
    assert error.value.code == "AUTHORIZATION_CHANGED"


def test_case_execution_rechecks_all_identities_and_original_bytes_without_issuing_proof():
    module, authority, database, connection, context, proof, metadata, raw = authority_fixture()
    expected = freeze_plan_binding(context, proof, **metadata, budgets=limits(), clock=lambda: NOW)
    with scoped_fixture(context, database, connection, case=True):
        result = authority.read_execution(context, expected, raw["input"], connection=connection)
    assert result.binding == expected and result.binding is not expected
    assert result.materials.inputs.canonical_bytes == raw["input"]
    calls = [item for item in connection.statements if "task_create_execution_plan" in item[0]]
    assert len(calls) == 1
    assert calls[0][1]["revision"] == expected.revision_id and calls[0][1]["plan_sha"] == proof.plan_sha256
    assert not hasattr(authority, "resolve")


def test_execution_is_never_available_in_lookup_scope():
    module, authority, database, connection, context, proof, metadata, raw = authority_fixture()
    expected = freeze_plan_binding(context, proof, **metadata, budgets=limits(), clock=lambda: NOW)
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError):
        authority.read_execution(context, expected, raw["input"], connection=connection)
    assert all("task_create_execution_plan" not in sql for sql, _ in connection.statements)


@pytest.mark.parametrize(
    "change", ["revision", "head", "receipt", "facts", "source-version", "input-object", "receipt-projection"]
)
def test_case_execution_rejects_late_changed_binding_or_input_without_rebinding(change):
    module, authority, database, connection, context, proof, metadata, raw = authority_fixture()
    expected = freeze_plan_binding(context, proof, **metadata, budgets=limits(), clock=lambda: NOW)
    if change == "revision":
        connection.execution["revision_id"] = uuid4()
    elif change == "head":
        connection.execution["head_row_version"] = 2
    elif change == "receipt":
        connection.execution["validation_receipt_bytes"] = b'{"validated":true}'
    elif change == "facts":
        connection.execution["current_state_facts"]["asset"]["version"] = 2
    elif change == "source-version":
        connection.execution["current_state_facts"]["source"]["authorization_version"] = "other"
    elif change == "receipt-projection":
        connection.rows[0]["validation_receipt"]["validator_id"] = "invented-validator"
    else:
        value = importlib.import_module("json").loads(raw["input"])
        value["asset"]["object_ref"]["version_id"] = "other"
        value["nodes"][0]["inputs"][1]["value"] = "other"
        raw["input"] = canonical(value)
    with scoped_fixture(context, database, connection, case=True), pytest.raises(BusinessError):
        authority.read_execution(context, expected, raw["input"], connection=connection)


def test_lookup_transaction_probe_normalizes_driver_failures_without_raw_diagnostics():
    _, authority, database, connection, context, _, _, _ = authority_fixture()
    original = connection.execute

    def failed_probe(statement, parameters=None):
        if "transaction_read_only" in str(statement):
            raise RuntimeError("self-owned driver diagnostics must-not-escape")
        return original(statement, parameters)

    connection.execute = failed_probe
    with scoped_fixture(context, database, connection), pytest.raises(BusinessError) as error:
        authority.read_metadata(context, connection=connection)
    assert error.value.http_status == 503 and "must-not-escape" not in str(error.value)


def test_case_execution_rechecks_current_context_changed_during_material_read():
    module, authority, database, connection, context, proof, metadata, raw = authority_fixture()
    expected = freeze_plan_binding(context, proof, **metadata, budgets=limits(), clock=lambda: NOW)
    other = arranged()[0]
    entered: list[AbstractContextManager[TaskCreationContext]] = []

    def changing_clock():
        if not entered and any("task_create_execution_plan" in sql for sql, _ in connection.statements):
            manager = bind_task_creation_context(other, clock=NOW.timestamp)
            manager.__enter__()
            entered.append(manager)
        return NOW

    authority.clock = changing_clock
    with scoped_fixture(context, database, connection, case=True):
        try:
            with pytest.raises(BusinessError) as error:
                authority.read_execution(context, expected, raw["input"], connection=connection)
            assert error.value.code == "AUTHORITY_SCOPE_INVALID"
        finally:
            for manager in reversed(entered):
                manager.__exit__(None, None, None)
