"""Isolated task-creation transactions; synthetic adapters are not real adoption."""

import copy
import hashlib
import importlib
import importlib.util
import json
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.contracts import REGISTRY, SCHEMAS, validate_response
from business_app.controls.common import etag
from business_app.data_scope import AccessMode, DataScope, LookupKey
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.permissions.context import request_authorization
from business_app.permissions.rule_types import AuthorizationEvidence, RuleTarget
from business_app.permissions.task_creation_context import bind_task_creation_context, freeze_task_creation_context
from business_app.permissions.types import Principal
from business_app.settings import BusinessSettings
from business_app.task_creation import TaskPlanProof
from business_app.task_creation_authority import ExecutionMaterials, freeze_plan_binding
from business_app.task_creation_materials import MaterialBudgets
from business_app.task_creation_sql_authority import SqlTaskPlanAuthority
from business_app.types import Actor, Scope
from jsonschema import Draft202012Validator, FormatChecker
from psycopg.rows import dict_row
from sqlalchemy import event, text

from tests.business import test_task_creation_scope_sql as scope_fixtures
from tests.business.http_fixtures import FixtureFence
from tests.business.test_task_creation_materials import canonical, rebind
from tests.business.test_task_creation_migration import insert

sql_context = scope_fixtures.sql_context

TABLES = (
    "analysis_task",
    "task_run",
    "task_run_plan",
    "task_node_run",
    "task_event",
    "outbox_event",
    "audit_event",
    "idempotency_record",
    "task_result",
)


def module():
    assert importlib.util.find_spec("business_app.task_creation_service") is not None, (
        "Task creation service is not implemented; structural component boundary only, "
        "not a previously accepted business creation or authorization bypass"
    )
    return importlib.import_module("business_app.task_creation_service")


def test_task_creation_service_component_exists():
    assert hasattr(module(), "TaskCreationService"), "The task creation service class is not implemented"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def counts(context):
    with psycopg.connect(context["admin_dsn"]) as connection:
        values = {}
        for table in TABLES:
            row = connection.execute("SELECT count(*) FROM mt." + table).fetchone()
            assert row is not None
            values[table] = row[0]
        return values


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class SyntheticTransactionFence(FixtureFence):
    """Explicit test trust only; no real generation, role or adoption assertion."""

    def __init__(self, actor, clock):
        super().__init__(frozenset({actor}))
        self.clock = lambda: clock().timestamp()
        self.holds = 0
        self.finishes = 0
        self.fail_finish = False

    def hold(self, connection, evidence):
        super().hold(connection, evidence)
        self.holds += 1

    def finish(self, connection, evidence):
        super().finish(connection, evidence)
        self.finishes += 1
        if self.fail_finish:
            raise BusinessError("AUTHORIZATION_CHANGED", 503)


class SyntheticMaterialsReader:
    """Self-owned Proof fixture plus actual fixed SQL reads, never a deployable issuer."""

    def __init__(self, environment):
        self.environment = environment
        self.calls = 0
        self.on_read = lambda value, index: value
        self.observations: list[ExecutionMaterials] = []

    def read(self, context, *, connection):
        environment = self.environment
        self.calls += 1
        authority = SqlTaskPlanAuthority(
            environment["database"], budgets=environment["budgets"], clock=environment["clock"]
        )
        row = authority.read_metadata(context, connection=connection).as_dict()
        proof = TaskPlanProof(
            context.request,
            row["authority_version"],
            row["policy_sha256"],
            row["plan_id"],
            row["plan_version"],
            row["plan_sha256"],
            row["capability_id"],
            row["capability_version"],
            row["capability_sha256"],
            True,
            environment["proof_deadline"],
        )
        facts = canonical(row["current_state_facts"])
        binding = freeze_plan_binding(
            context,
            proof,
            revision_id=UUID(row["revision_id"]),
            head_row_version=row["head_row_version"],
            mapping_id=row["mapping_id"],
            mapping_version=row["mapping_version"],
            policy_id=UUID(row["policy_id"]),
            policy_kind=row["policy_kind"],
            policy_version=row["policy_version"],
            mapping_valid_from=stamp(row["valid_from"]),
            mapping_valid_until=stamp(row["valid_until"]),
            validation_receipt_bytes=environment["receipt"],
            validation_receipt_sha256=sha(environment["receipt"]),
            recovery_generation=row["recovery_generation"],
            current_state_facts_bytes=facts,
            current_state_facts_sha256=sha(facts),
            budgets=environment["budgets"],
            clock=environment["clock"],
        )
        value = authority.read_execution(context, binding, environment["input_raw"], connection=connection)
        self.observations.append(value)
        return self.on_read(value, self.calls)


@pytest.fixture
def creation_environment(sql_context, tmp_path):
    context = sql_context
    current = [datetime.now(timezone.utc)]
    actor = Actor(context["user"], context["org"])
    database = Database(context["runtime_dsn"])
    plan = context["documents"]["plan"]
    body = dict(
        case_id=str(context["case"]),
        asset_id=str(context["asset"]),
        scene=plan["scene"],
        policy_version=plan["policy_version"],
        modules=copy.deepcopy(plan["modules"]),
        priority=plan["priority"],
    )
    inputs = copy.deepcopy(context["documents"]["input"])
    inputs["asset"].update(
        asset_id=str(context["asset"]),
        sha256="a" * 64,
        object_ref=dict(object_id=str(context["object"]), version_id="fixture-object/1", sha256="a" * 64),
        source_authorization_version="fixture-source/1",
    )
    for item in inputs["nodes"][0]["inputs"]:
        item["value"] = inputs["asset"]["object_ref"][item["field_path"]]
    settings = BusinessSettings(
        database_dsn=context["runtime_dsn"],
        object_root=tmp_path / "self-owned-objects",
        max_upload_bytes=1_048_576,
        part_size_bytes=256_000,
        upload_ttl_seconds=3600,
        cursor_secret=uuid4().hex,
        control_ttl_seconds=3600,
        runtime_profile="test",
    )
    environment = dict(
        context,
        database=database,
        settings=settings,
        actor=actor,
        scope=Scope(actor, context["case"]),
        principal=Principal(
            actor, "https://self-owned-transaction.example.test", str(actor.user_id), int(current[0].timestamp()) + 3600
        ),
        body=body,
        clock=lambda: current[0],
        clock_state=current,
        proof_deadline=current[0] + timedelta(minutes=5),
        budgets=MaterialBudgets(max_bytes=200_000, max_nodes=20, max_capabilities=20),
        input_raw=canonical(inputs),
        input_document=inputs,
    )
    environment["fence"] = SyntheticTransactionFence(actor, environment["clock"])
    environment["reader"] = SyntheticMaterialsReader(environment)
    environment["initial_counts"] = counts(environment)
    try:
        yield environment
    finally:
        database.close()


@contextmanager
def authorized(environment, *, body=None, context=True, evidence_changes=None, fence=True):
    body = environment["body"] if body is None else body
    now = environment["clock"]
    identity = freeze_task_creation_context(environment["principal"], body, clock=lambda: now().timestamp())
    target = RuleTarget(
        environment["actor"].org_id,
        "asset",
        identity.request.asset_id,
        1,
        identity.request.case_id,
        "analysis",
        None,
        (environment["source"],),
        identity.authorization_request_digest,
    )
    evidence = AuthorizationEvidence(
        identity.principal,
        "createTask",
        target,
        "e" * 64,
        "f" * 64,
        "explicit-synthetic-fixture",
        environment["revision"]["recovery_generation"],
        now().timestamp() + 600,
    )
    if evidence_changes:
        evidence = replace(evidence, **evidence_changes)
    with request_authorization(evidence, environment["fence"] if fence else None, mutation=True):
        if context:
            with bind_task_creation_context(identity, clock=lambda: now().timestamp()):
                yield identity
        else:
            yield identity


@pytest.mark.parametrize("mode", ["case", "lookup"])
def test_real_sql_generation_oid_is_a_json_integer(creation_environment, mode):
    """Real fixed projections must satisfy the existing strict reader's integer contract."""
    environment = creation_environment

    def check(connection, identity):
        request = identity.request
        observed = (
            connection.execute(
                text("SELECT * FROM mt.task_create_plan_metadata(:asset,:case,:scene,:policy,:modules,:priority)"),
                dict(
                    asset=request.asset_id,
                    case=request.case_id,
                    scene=request.scene,
                    policy=request.policy_version,
                    modules=list(request.modules),
                    priority=request.priority,
                ),
            )
            .mappings()
            .fetchmany(2)
        )
        assert len(observed) == 1
        generation = observed[0]["current_state_facts"]["generation"]
        assert type(generation["database_oid"]) is int, (
            "The fixed SQL projection must encode database_oid as an integer"
        )
        assert generation["database_oid"] > 0
        assert type(generation["epoch"]) is int
        assert generation["epoch"] > 0
        actual_oid = connection.execute(
            text("SELECT oid::bigint FROM pg_catalog.pg_database WHERE datname=current_database()")
        ).scalar_one()
        assert generation["database_oid"] == actual_oid
        authority = SqlTaskPlanAuthority(
            environment["database"], budgets=environment["budgets"], clock=environment["clock"]
        )
        metadata = authority.read_metadata(identity, connection=connection).as_dict()
        assert metadata["current_state_facts"]["generation"] == generation
        assert metadata["revision_id"] == str(environment["revision"]["revision_id"])

    if mode == "case":
        with (
            authorized(environment) as identity,
            environment["database"].transaction(environment["scope"]) as connection,
        ):
            check(connection, identity)
    else:
        identity = freeze_task_creation_context(
            environment["principal"], environment["body"], clock=lambda: environment["clock"]().timestamp()
        )
        scope = DataScope(
            environment["actor"],
            AccessMode.LOOKUP,
            "createTask",
            None,
            LookupKey("asset", identity.request.asset_id),
            None,
            None,
        )
        with (
            bind_task_creation_context(identity, clock=lambda: environment["clock"]().timestamp()),
            environment["database"].scoped_transaction(scope) as connection,
        ):
            check(connection, identity)


def service(environment, *, reader=True, settings=None):
    return module().TaskCreationService(
        environment["database"],
        environment["settings"] if settings is None else settings,
        materials_reader=environment["reader"] if reader else None,
        budgets=environment["budgets"],
        clock=environment["clock"],
    )


def create(environment, *, key="self-owned-creation-key", body=None, request_id=None, instance=None):
    return (service(environment) if instance is None else instance).create(
        environment["scope"],
        environment["body"] if body is None else body,
        idempotency_key=key,
        request_id=uuid4() if request_id is None else request_id,
    )


def task_rows(environment, task_id):
    with psycopg.connect(environment["admin_dsn"], row_factory=dict_row) as connection:
        result = {
            table: connection.execute("SELECT * FROM mt." + table + " WHERE task_id=%s", (task_id,)).fetchall()
            for table in ("analysis_task", "task_run", "task_run_plan", "task_node_run", "task_event", "task_result")
        }
        result["outbox_event"] = connection.execute(
            "SELECT * FROM mt.outbox_event WHERE aggregate_id=%s", (task_id,)
        ).fetchall()
        result["audit_event"] = connection.execute(
            "SELECT * FROM mt.audit_event WHERE object_id=%s", (task_id,)
        ).fetchall()
        result["idempotency_record"] = connection.execute(
            "SELECT * FROM mt.idempotency_record WHERE operation='createTask' AND case_id=%s AND actor_id=%s",
            (environment["case"], environment["user"]),
        ).fetchall()
        return result


def test_fresh_creation_writes_the_complete_fixed_run_without_results(creation_environment):
    environment = creation_environment
    request_id = uuid4()
    with authorized(environment) as context:
        accepted = create(environment, request_id=request_id)
    validate_response("Accepted", accepted)
    task_id = UUID(accepted["task_id"])
    assert accepted == dict(
        task_id=str(task_id), state="QUEUED", status_url=f"/api/v1/analysis/tasks/{task_id}/execution"
    )
    actual = task_rows(environment, task_id)
    assert {table: len(rows) for table, rows in actual.items()} == {
        table: 0 if table == "task_result" else 1 for table in TABLES
    }
    assert counts(environment) == {
        table: count + (0 if table == "task_result" else 1) for table, count in environment["initial_counts"].items()
    }
    for stored_rows in actual.values():
        for item in stored_rows:
            assert (item["org_id"], item["case_id"], item["created_by"]) == (
                environment["org"],
                environment["case"],
                environment["user"],
            )
    task, run, saved = [actual[table][0] for table in ("analysis_task", "task_run", "task_run_plan")]
    material = environment["reader"].observations[0]
    assert (task["state"], task["progress"], task["run_version"], task["result_version"], task["row_version"]) == (
        "QUEUED",
        0,
        1,
        1,
        2,
    )
    assert task["report_eligibility"] == "draft_only" and task["missing_modalities"] == []
    assert (run["run_version"], run["input_sha256"], run["dag_version"], run["policy_version"]) == (
        1,
        sha(environment["input_raw"]),
        material.materials.plan.version,
        context.request.policy_version,
    )
    assert bytes(saved["request_body_bytes"]) == context.request.canonical_body
    assert saved["request_body_sha256"] == context.request.request_sha256
    assert saved["authorization_request_digest"] == context.authorization_request_digest
    assert saved["request_body_sha256"] != saved["authorization_request_digest"]
    assert (saved["revision_id"], saved["head_row_version"], saved["recovery_generation"]) == (
        material.binding.revision_id,
        material.binding.head_row_version,
        material.binding.recovery_generation,
    )
    for kind in ("policy", "plan", "capability"):
        item = getattr(material.materials, kind)
        assert bytes(saved[kind + "_bytes"]) == item.canonical_bytes
        assert saved[kind + "_sha256"] == item.sha256
    assert bytes(saved["input_manifest_bytes"]) == environment["input_raw"]
    assert bytes(saved["validation_receipt_bytes"]) == environment["receipt"]
    assert saved["validation_receipt_sha256"] == sha(environment["receipt"])
    assert (
        saved["mapping_valid_from"]
        <= saved["proof_observed_at"]
        < saved["proof_valid_until"]
        <= saved["mapping_valid_until"]
    )
    node = actual["task_node_run"][0]
    assert (node["node_code"], node["attempt"], node["state"], node["required"], node["input_hash"]) == (
        "retain_ref",
        1,
        "READY",
        True,
        material.materials.node_inputs[0].sha256,
    )
    assert all(node[field] is None for field in ("started_at", "ended_at", "lease_token", "model_version"))
    assert node["fencing_epoch"] == run["fencing_epoch"] == 1
    event_row, outbox = actual["task_event"][0], actual["outbox_event"][0]
    event_payload = outbox["payload"]
    assert event_row["event_id"] == outbox["event_id"] == UUID(event_payload["event_id"])
    assert event_row["request_id"] == request_id and event_payload["request_id"] == str(request_id)
    assert (event_row["from_state"], event_row["to_state"]) == ("CREATED", "QUEUED")
    assert outbox["published_at"] is None and outbox["topic"] == "workflow.run.accepted.v1"
    assert event_payload["producer_role"] == "scheduler" and event_payload["state"] == "QUEUED"
    assert event_payload["binding"]["result_version"] is None and event_payload["result_snapshot_ref"] is None
    assert event_payload["binding"]["task_id"] == str(task_id) and event_payload["binding"]["run_version"] == 1
    assert (event_payload["binding"]["policy_version"], event_payload["binding"]["dag_version"]) == (
        context.request.policy_version,
        material.materials.plan.version,
    )
    assert outbox["aggregate_version"] == task["row_version"]
    Draft202012Validator(
        SCHEMAS["urn:media-trace:stage-one:domain-event:0.1.0"], registry=REGISTRY, format_checker=FormatChecker()
    ).validate(event_payload)
    audit = actual["audit_event"][0]
    assert audit["actor_id"] == environment["user"] and audit["request_id"] == request_id
    receipt = actual["idempotency_record"][0]
    assert receipt["request_sha256"] == context.request.request_sha256
    assert receipt["response_ref"]["schema_version"] == "task-create-control-receipt-v1"
    assert receipt["response_ref"]["accepted"] == accepted and receipt["response_ref"]["etag"] == etag(accepted)
    assert environment["reader"].calls >= 2 and environment["fence"].finishes >= 1


def test_dependency_nodes_keep_pending_selectors_without_fabricated_outputs(creation_environment):
    environment = creation_environment
    documents = copy.deepcopy(environment["documents"])
    documents["input"] = copy.deepcopy(environment["input_document"])
    plan, inputs = documents["plan"], documents["input"]
    plan["plan_version"] += "/two-nodes"
    inputs["plan_version"] = plan["plan_version"]
    child = copy.deepcopy(plan["nodes"][0])
    child["node_code"] = "after_ref"
    child["dependencies"] = ["retain_ref"]
    child["input_bindings"] = [
        dict(field_path=key, source="node_output", node_code="retain_ref", output_ref="result", selector=key)
        for key in ("object_id", "version_id", "sha256")
    ]
    plan["nodes"].append(child)
    inputs["nodes"].append(
        dict(node_code="after_ref", inputs=[dict(binding, materialized=False) for binding in child["input_bindings"]])
    )
    rebind(documents)
    raw = canonical(plan)
    revision = dict(
        environment["revision"],
        revision_id=uuid4(),
        mapping_version="self-owned-two-nodes",
        plan_version=plan["plan_version"],
        plan_sha256=sha(raw),
    )
    with psycopg.connect(environment["admin_dsn"]) as admin:
        insert(
            admin,
            "task_plan_artifact",
            dict(
                org_id=environment["org"],
                plan_id=plan["plan_id"],
                plan_version=plan["plan_version"],
                canonical_bytes=raw,
                plan_sha256=sha(raw),
                schema_version=plan["schema_id"],
                canonicalization_version="task-material-json-utf8-sortkeys-v1",
                provenance_ref="self-owned-two-node-test-not-adoption",
                created_by=environment["user"],
            ),
        )
        insert(admin, "task_plan_mapping_revision", revision)
        admin.execute(
            "UPDATE mt.task_plan_mapping_head SET revision_id=%s,row_version=row_version+1 WHERE org_id=%s AND case_id=%s",
            (revision["revision_id"], environment["org"], environment["case"]),
        )
    environment["input_raw"] = canonical(inputs)
    environment["input_document"] = inputs
    environment["revision"] = revision
    with authorized(environment):
        accepted = create(environment)
    actual = task_rows(environment, UUID(accepted["task_id"]))
    assert {(node["node_code"], node["state"], node["attempt"]) for node in actual["task_node_run"]} == {
        ("retain_ref", "READY", 1),
        ("after_ref", "PENDING", 1),
    }
    material = environment["reader"].observations[0]
    expected_inputs = {item.document_id: item for item in material.materials.node_inputs}
    assert {node["node_code"]: node["input_hash"] for node in actual["task_node_run"]} == {
        code: item.sha256 for code, item in expected_inputs.items()
    }
    assert all(
        node["started_at"] is None and node["ended_at"] is None and node["lease_token"] is None
        for node in actual["task_node_run"]
    )
    pending = expected_inputs["after_ref"].as_dict()["node"]["inputs"]
    assert all(item["materialized"] is False and "value" not in item for item in pending)
    receipt_nodes = actual["idempotency_record"][0]["response_ref"]["nodes"]
    assert {node["node_code"]: node["snapshot"] for node in receipt_nodes} == {
        code: item.as_dict() for code, item in expected_inputs.items()
    }
    assert actual["task_result"] == [] and actual["analysis_task"][0]["report_eligibility"] == "draft_only"


def test_same_key_replays_original_accepted_etag_without_duplicate_writes(creation_environment):
    environment = creation_environment
    with authorized(environment):
        accepted = create(environment)
    task_id = UUID(accepted["task_id"])
    original = task_rows(environment, task_id)["idempotency_record"][0]
    before = counts(environment)
    with authorized(environment):
        replayed = create(environment, request_id=uuid4())
    assert replayed == accepted
    assert counts(environment) == before
    record = task_rows(environment, task_id)["idempotency_record"][0]
    assert record == original
    assert record["response_ref"]["accepted"] == accepted
    assert record["response_ref"]["etag"] == etag(accepted)


def test_exact_material_read_precedes_the_idempotency_transaction_lock(creation_environment):
    environment = creation_environment
    steps: list[str] = []

    def material_observed(value, index):
        steps.append("materials")
        return value

    def statement_observed(connection, cursor, statement, parameters, execution_context, many):
        if "pg_advisory_xact_lock" in statement.lower():
            steps.append("idempotency-lock")

    environment["reader"].on_read = material_observed
    event.listen(environment["database"].engine, "before_cursor_execute", statement_observed)
    try:
        with authorized(environment):
            create(environment)
    finally:
        event.remove(environment["database"].engine, "before_cursor_execute", statement_observed)
    # The callback occurs after the real fixed SQL reader has taken the
    # approved asset/source/policy/head locks. A failure-only A/expiry SELECT
    # may precede it, but the first advisory lock must not.
    assert "materials" in steps and "idempotency-lock" in steps
    assert steps.index("materials") < steps.index("idempotency-lock")


def test_proof_expiring_during_advisory_wait_refuses_before_the_first_insert(creation_environment, monkeypatch):
    environment = creation_environment
    instance = service(environment)
    original = instance.receipts.replay
    observed: list[str] = []
    inserted: list[str] = []

    def waited(*args, **kwargs):
        result = original(*args, **kwargs)
        observed.append("advisory-lock-returned")
        environment["clock_state"][0] = environment["proof_deadline"] + timedelta(seconds=1)
        return result

    def record_insert(connection, cursor, statement, parameters, execution_context, many):
        if statement.lstrip().upper().startswith("INSERT INTO MT."):
            inserted.append("new-row-insert-attempted")

    monkeypatch.setattr(instance.receipts, "replay", waited)
    event.listen(environment["database"].engine, "before_cursor_execute", record_insert)
    try:
        with authorized(environment), pytest.raises(BusinessError) as error:
            create(environment, instance=instance)
    finally:
        event.remove(environment["database"].engine, "before_cursor_execute", record_insert)
    assert observed == ["advisory-lock-returned"]
    assert (error.value.code, error.value.http_status) == ("CONDITIONAL_FACTS_UNAVAILABLE", 503)
    assert environment["reader"].calls == 1
    assert inserted == []
    assert counts(environment) == environment["initial_counts"]


def test_replay_after_task_progress_keeps_the_original_acceptance(creation_environment):
    environment = creation_environment
    with authorized(environment):
        accepted = create(environment)
    task_id = UUID(accepted["task_id"])
    with psycopg.connect(environment["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.analysis_task SET state='RUNNING',progress=0.25,row_version=row_version+1 WHERE task_id=%s",
            (task_id,),
        )
        admin.execute(
            "UPDATE mt.task_node_run SET state='RUNNING',started_at=now(),lease_token='self-owned-lease',"
            "fencing_epoch=fencing_epoch+1,row_version=row_version+1 WHERE task_id=%s",
            (task_id,),
        )
    before = counts(environment)
    with authorized(environment):
        replayed = create(environment)
    assert replayed == accepted and replayed["state"] == "QUEUED"
    actual = task_rows(environment, task_id)
    assert (actual["analysis_task"][0]["state"], actual["analysis_task"][0]["progress"]) == ("RUNNING", 0.25)
    assert actual["task_node_run"][0]["state"] == "RUNNING"
    assert actual["idempotency_record"][0]["response_ref"]["etag"] == etag(accepted)
    assert counts(environment) == before


@pytest.mark.parametrize("field", ["asset_id", "case_id"])
def test_same_key_different_request_literal_is_a_conflict(creation_environment, field):
    environment = creation_environment
    with authorized(environment):
        create(environment)
    changed = copy.deepcopy(environment["body"])
    changed[field] = changed[field].upper()
    assert changed != environment["body"]
    before = counts(environment)
    with authorized(environment, body=changed), pytest.raises(BusinessError) as error:
        create(environment, body=changed)
    assert (error.value.code, error.value.http_status) == ("IDEMPOTENCY_CONFLICT", 409)
    assert counts(environment) == before


def test_different_keys_do_not_introduce_undocumented_business_deduplication(creation_environment):
    environment = creation_environment
    with authorized(environment):
        first = create(environment, key="self-owned-first-key")
    with authorized(environment):
        second = create(environment, key="self-owned-second-key")
    assert first["task_id"] != second["task_id"]
    assert counts(environment) == {
        table: count + (0 if table == "task_result" else 2) for table, count in environment["initial_counts"].items()
    }


@pytest.mark.parametrize("problem", ["expired", "unknown-field", "accepted-task", "etag", "revision"])
def test_invalid_old_receipt_never_rebuilds_or_rebinds_a_task(creation_environment, problem):
    environment = creation_environment
    with authorized(environment):
        accepted = create(environment)
    task_id = UUID(accepted["task_id"])
    with psycopg.connect(environment["admin_dsn"]) as admin:
        record = task_rows(environment, task_id)["idempotency_record"][0]
        value = copy.deepcopy(record["response_ref"])
        if problem == "expired":
            admin.execute(
                "UPDATE mt.idempotency_record SET expires_at=now()-interval '1 second' WHERE idempotency_id=%s",
                (record["idempotency_id"],),
            )
        else:
            if problem == "unknown-field":
                value["untrusted_extra"] = True
            elif problem == "accepted-task":
                value["accepted"]["task_id"] = str(uuid4())
            elif problem == "etag":
                value["etag"] = '"' + "0" * 64 + '"'
            else:
                value["binding"]["revision_id"] = str(uuid4())
            admin.execute(
                "UPDATE mt.idempotency_record SET response_ref=%s::jsonb WHERE idempotency_id=%s",
                (json.dumps(value), record["idempotency_id"]),
            )
    before = counts(environment)
    with authorized(environment), pytest.raises(BusinessError) as error:
        create(environment)
    assert (error.value.code, error.value.http_status) == ("IDEMPOTENCY_CONFLICT", 409)
    assert counts(environment) == before


def test_complete_receipts_cannot_be_copied_between_different_keys(creation_environment):
    environment = creation_environment
    with authorized(environment):
        first = create(environment, key="self-owned-copy-source")
    with authorized(environment):
        second = create(environment, key="self-owned-copy-target")
    assert first["task_id"] != second["task_id"]
    records = task_rows(environment, UUID(first["task_id"]))["idempotency_record"]
    by_key = {record["idempotency_key"]: record for record in records}
    with psycopg.connect(environment["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.idempotency_record SET response_ref=%s::jsonb WHERE idempotency_id=%s",
            (
                json.dumps(by_key["self-owned-copy-source"]["response_ref"]),
                by_key["self-owned-copy-target"]["idempotency_id"],
            ),
        )
    before = counts(environment)
    with authorized(environment), pytest.raises(BusinessError) as error:
        create(environment, key="self-owned-copy-target")
    assert (error.value.code, error.value.http_status) == ("IDEMPOTENCY_CONFLICT", 409)
    assert counts(environment) == before


@pytest.mark.parametrize("state", ["INACTIVE", "REVOKED"])
def test_old_head_no_longer_active_cannot_replay_immutable_history(creation_environment, state):
    environment = creation_environment
    with authorized(environment):
        create(environment)
    with psycopg.connect(environment["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.task_plan_mapping_head SET state=%s,row_version=row_version+1 WHERE org_id=%s AND case_id=%s",
            (state, environment["org"], environment["case"]),
        )
    before = counts(environment)
    with authorized(environment), pytest.raises(BusinessError) as error:
        create(environment)
    assert error.value.http_status in {409, 503}
    assert counts(environment) == before


@pytest.mark.parametrize("missing", ["reader", "ttl", "context", "fence", "authorization", "foreign-root"])
def test_missing_explicit_trust_or_wrong_root_refuses_before_writes(creation_environment, missing):
    environment = creation_environment
    instance = service(
        environment,
        reader=missing != "reader",
        settings=replace(environment["settings"], control_ttl_seconds=None) if missing == "ttl" else None,
    )
    if missing == "authorization":
        context = freeze_task_creation_context(
            environment["principal"], environment["body"], clock=lambda: environment["clock"]().timestamp()
        )
        with bind_task_creation_context(context, clock=lambda: environment["clock"]().timestamp()):
            with pytest.raises(BusinessError) as error:
                create(environment, instance=instance)
    elif missing == "foreign-root":
        other = Database(environment["runtime_dsn"])
        try:
            instance = module().TaskCreationService(
                other,
                environment["settings"],
                materials_reader=environment["reader"],
                budgets=environment["budgets"],
                clock=environment["clock"],
            )
            with authorized(environment), environment["database"].transaction(environment["scope"]):
                with pytest.raises(BusinessError) as error:
                    create(environment, instance=instance)
        finally:
            other.close()
    else:
        with authorized(environment, context=missing != "context", fence=missing != "fence"):
            with pytest.raises(BusinessError) as error:
                create(environment, instance=instance)
    assert error.value.http_status == 503
    if missing == "ttl":
        assert error.value.code == "CONTROL_RECEIPT_TTL_UNCONFIRMED"
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("wrong", ["asset", "case", "digest", "purpose", "operation", "principal"])
def test_scope_request_and_authorization_must_share_the_exact_target(creation_environment, wrong):
    environment = creation_environment
    with authorized(environment) as context:
        from business_app.permissions.context import current_authorization

        original = current_authorization()
        assert original is not None
        evidence = original.evidence
        if wrong == "operation":
            evidence = replace(evidence, operation_id="downloadAsset")
        elif wrong == "principal":
            evidence = replace(evidence, principal=replace(context.principal, subject="different-self-owned-subject"))
        else:
            changes = {
                "asset": dict(object_id=uuid4()),
                "case": dict(case_id=environment["other_case"]),
                "digest": dict(request_digest="0" * 64),
                "purpose": dict(purpose="download"),
            }
            evidence = replace(evidence, target=replace(evidence.target, **changes[wrong]))
        with request_authorization(evidence, environment["fence"], mutation=True), pytest.raises(BusinessError):
            create(environment)
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("key", [None, True, 7, "", "k" * 129])
def test_invalid_idempotency_key_is_rejected_without_creating_a_shell(creation_environment, key):
    environment = creation_environment
    with authorized(environment), pytest.raises(BusinessError):
        create(environment, key=key)
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("request_id", [None, UUID(int=0), "self-owned-request", True])
def test_request_id_is_an_explicit_nonzero_uuid(creation_environment, request_id):
    environment = creation_environment
    with authorized(environment), pytest.raises(BusinessError):
        service(environment).create(
            environment["scope"], environment["body"], idempotency_key="self-owned-key", request_id=request_id
        )
    assert counts(environment) == environment["initial_counts"]


WRITE_POINTS = (
    ("INSERT", "analysis_task"),
    ("INSERT", "task_run"),
    ("INSERT", "task_run_plan"),
    ("INSERT", "task_node_run"),
    ("UPDATE", "analysis_task"),
    ("INSERT", "task_event"),
    ("INSERT", "outbox_event"),
    ("INSERT", "audit_event"),
    ("INSERT", "idempotency_record"),
)


@contextmanager
def fail_write(database, verb, table):
    import re

    seen: list[bool] = []

    def fail(connection, cursor, statement, parameters, execution_context, many):
        if re.match(r"\s*" + verb + r"\s+(?:INTO\s+)?mt\." + table + r"\b", statement, re.IGNORECASE):
            seen.append(True)
            raise BusinessError("DATABASE_UNAVAILABLE", 503)

    event.listen(database.engine, "before_cursor_execute", fail)
    try:
        yield seen
    finally:
        event.remove(database.engine, "before_cursor_execute", fail)


@pytest.mark.parametrize("verb,table", WRITE_POINTS, ids=[verb.lower() + "-" + table for verb, table in WRITE_POINTS])
def test_each_write_failure_rolls_back_the_entire_new_collection(creation_environment, verb, table):
    environment = creation_environment
    with fail_write(environment["database"], verb, table) as hits:
        with authorized(environment), pytest.raises(BusinessError):
            create(environment)
    assert hits, "The actual write injection point was not reached"
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("table", ["task_run_plan", "outbox_event", "idempotency_record"])
def test_caller_catching_failure_cannot_commit_a_partial_creation(creation_environment, table):
    environment = creation_environment
    with authorized(environment), environment["database"].transaction(environment["scope"]) as connection:
        with fail_write(environment["database"], "INSERT", table) as hits, pytest.raises(BusinessError):
            create(environment)
        assert hits
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
        assert connection.execute(text("SELECT count(*) FROM mt.task_run_plan")).scalar_one() == 0
        # The outer transaction intentionally commits after the caught error.
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("append_first", [False, True])
def test_before_commit_registration_failure_rolls_back_even_when_caller_catches(
    creation_environment, monkeypatch, append_first
):
    from business_app.scope_context import current_scope_transaction

    environment = creation_environment
    original = environment["database"].before_commit
    reached: list[bool] = []

    def refuse(connection, check):
        reached.append(True)
        if append_first:
            original(connection, check)
        raise BusinessError("DATABASE_UNAVAILABLE", 503)

    monkeypatch.setattr(environment["database"], "before_commit", refuse)
    with authorized(environment), environment["database"].transaction(environment["scope"]):
        with pytest.raises(BusinessError) as error:
            create(environment)
        assert error.value.code == "DATABASE_UNAVAILABLE" and reached
        root = current_scope_transaction()
        assert root is not None and root.commit_checks == []
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("boundary", ["event-schema", "accepted-schema"])
def test_contract_validation_failure_rolls_back_the_creation(creation_environment, monkeypatch, boundary):
    environment = creation_environment
    component = module()
    reached: list[bool] = []

    def refuse(*args, **kwargs):
        reached.append(True)
        raise BusinessError("RESPONSE_CONTRACT_UNAVAILABLE", 503)

    monkeypatch.setattr(component, "_event" if boundary == "event-schema" else "validate_response", refuse)
    with authorized(environment), pytest.raises(BusinessError) as error:
        create(environment)
    assert error.value.code == "RESPONSE_CONTRACT_UNAVAILABLE" and reached
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("stage", ["provider-final", "proof-expiry", "fence-final", "commit"])
def test_final_failures_never_leave_accepted_rows(creation_environment, stage):
    environment = creation_environment
    reached: list[str] = []

    def changed(value, index):
        if index >= 2:
            reached.append(stage)
            if stage == "provider-final":
                raise BusinessError("AUTHORIZATION_CHANGED", 503)
            if stage == "proof-expiry":
                environment["clock_state"][0] = environment["proof_deadline"] + timedelta(seconds=1)
        return value

    def fail_commit(connection):
        reached.append(stage)
        raise BusinessError("DATABASE_UNAVAILABLE", 503)

    environment["reader"].on_read = changed
    if stage == "fence-final":
        environment["fence"].fail_finish = True
    if stage == "commit":
        event.listen(environment["database"].engine, "commit", fail_commit)
    try:
        with authorized(environment), pytest.raises(BusinessError):
            create(environment)
    finally:
        if stage == "commit":
            event.remove(environment["database"].engine, "commit", fail_commit)
    if stage == "fence-final":
        assert environment["fence"].finishes >= 1
    else:
        assert reached
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize("change", ["revision", "head-version", "fact-fingerprint", "input-bytes"])
def test_final_material_changes_do_not_replace_the_first_observation(creation_environment, change):
    environment = creation_environment

    def changed(value, index):
        if index < 2:
            return value
        binding = value.binding
        if change == "revision":
            binding = replace(binding, revision_id=uuid4())
        elif change == "head-version":
            binding = replace(binding, head_row_version=binding.head_row_version + 1)
        elif change == "fact-fingerprint":
            raw = canonical(dict(self_owned_changed_fingerprint=True))
            binding = replace(binding, current_state_facts_bytes=raw, current_state_facts_sha256=sha(raw))
        else:
            inputs = value.materials.inputs
            return replace(value, materials=replace(value.materials, inputs=replace(inputs, sha256="0" * 64)))
        return replace(value, binding=binding)

    environment["reader"].on_read = changed
    with authorized(environment), pytest.raises(BusinessError) as error:
        create(environment)
    assert error.value.http_status == 503
    assert environment["reader"].calls >= 2
    assert counts(environment) == environment["initial_counts"]


@pytest.mark.parametrize(
    "failure", ["asset-state", "source-pending", "source-purpose", "source-expired", "wrong-input"]
)
def test_actual_asset_source_and_input_changes_refuse_without_shell_rows(creation_environment, failure):
    environment = creation_environment
    with psycopg.connect(environment["admin_dsn"]) as admin:
        if failure == "asset-state":
            admin.execute("UPDATE mt.media_asset SET state='VALIDATING' WHERE asset_id=%s", (environment["asset"],))
        elif failure == "source-pending":
            admin.execute(
                "UPDATE mt.source_registry SET authorization_status='pending' WHERE source_id=%s",
                (environment["source"],),
            )
        elif failure == "source-purpose":
            admin.execute(
                "UPDATE mt.source_registry SET purpose=ARRAY['upload'] WHERE source_id=%s", (environment["source"],)
            )
        elif failure == "source-expired":
            admin.execute(
                "UPDATE mt.source_registry SET expires_at=now()-interval '1 second' WHERE source_id=%s",
                (environment["source"],),
            )
        else:
            inputs = copy.deepcopy(environment["input_document"])
            inputs["asset"]["asset_id"] = str(uuid4())
            environment["input_raw"] = canonical(inputs)
    with authorized(environment), pytest.raises(BusinessError):
        create(environment)
    assert counts(environment) == environment["initial_counts"]


def test_provider_failure_after_committed_acceptance_does_not_replay_unchecked_success(creation_environment):
    environment = creation_environment
    with authorized(environment):
        create(environment)
    before = counts(environment)

    def unavailable(value, index):
        raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)

    environment["reader"].on_read = unavailable
    with authorized(environment), pytest.raises(BusinessError) as error:
        create(environment)
    assert (error.value.code, error.value.http_status) == ("CONDITIONAL_FACTS_UNAVAILABLE", 503)
    assert counts(environment) == before


def test_run_plan_is_immutable_after_acceptance(creation_environment):
    environment = creation_environment
    with authorized(environment):
        accepted = create(environment)
    task_id = UUID(accepted["task_id"])
    before = task_rows(environment, task_id)["task_run_plan"]
    with psycopg.connect(environment["admin_dsn"]) as admin:
        with pytest.raises(psycopg.Error), admin.transaction():
            admin.execute(
                "UPDATE mt.task_run_plan SET head_row_version=head_row_version+1 WHERE task_id=%s", (task_id,)
            )
        with pytest.raises(psycopg.Error), admin.transaction():
            admin.execute("DELETE FROM mt.task_run_plan WHERE task_id=%s", (task_id,))
    assert task_rows(environment, task_id)["task_run_plan"] == before
