"""Real SQL/HTTP catalog tests; institutional scope inputs are synthetic fixtures."""

import time
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.contracts import validate_response
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import ConditionFacts
from psycopg.types.json import Jsonb
from sqlalchemy import event, text

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context


@pytest.fixture
def model_catalog_context(control_context, permission_context):
    ctx = control_context
    configured, objects, authority, _ = candidate(ctx, permission_context, ["model.read"], role_code="algorithm_admin")

    class ModelMetadataFacts:
        blocked: set[UUID] = set()
        unknown: set[UUID] = set()

        def read(self, principal, operation_id, target, *, connection):
            assert principal == configured["principal"]
            assert operation_id in {"listModels", "listEvaluations"}
            assert target.org_id == ctx["actor"].org_id and target.case_id is None
            checks = dict(
                model_metadata_scope=None if target.object_id in self.unknown else target.object_id not in self.blocked
            )
            return ConditionFacts(principal, target, checks, digest([operation_id, target, checks]), time.time() + 60)

    facts = ModelMetadataFacts()
    objects.supplemental = facts
    model = insert_model(ctx, UUID(int=1))
    evaluation = insert_evaluation(ctx, model, UUID(int=11))
    return dict(
        ctx,
        configured=configured,
        object_facts=objects,
        conditions=authority,
        facts=facts,
        model=model,
        evaluation=evaluation,
    )


def insert_model(ctx, identifier, *, actor=None):
    actor = actor or ctx["actor"]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.model_registry(model_id,org_id,name,version,capability,digest,dataset_version,model_card_ref,license_record_ref,backend,environment_ref,status,created_by) VALUES(%s,%s,%s,'synthetic-v1','media.ocr',%s,'synthetic-data-v1','synthetic-card','synthetic-license','onnxruntime','synthetic-environment','REGISTERED',%s)",
            (identifier, actor.org_id, "synthetic-" + str(identifier), "a" * 64, actor.user_id),
        )
    return identifier


def insert_evaluation(ctx, model, identifier, *, artifact=None):
    artifact = artifact or ctx["input_ref"]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.model_evaluation(evaluation_id,org_id,model_id,dataset_id,dataset_version,protocol_id,split,sample_count,failure_count,metrics,artifact_ref,created_by) VALUES(%s,%s,%s,'synthetic-data','synthetic-data-v1','synthetic-protocol','validation',3,1,%s,%s,%s)",
            (
                identifier,
                ctx["actor"].org_id,
                model,
                Jsonb(dict(macro_f1=None, recall=0.5, iou=None, recall_at_k=None, ece=None, boundary_mae_ms=None)),
                Jsonb(artifact),
                ctx["actor"].user_id,
            ),
        )
    return identifier


def get(ctx, path, **query):
    return ctx["control_http"].get(path, params=query, headers=AUTH)


@pytest.mark.parametrize(
    "path,schema,key,fixture",
    [
        ("/api/v1/models", "ModelPage", "model_id", "model"),
        ("/api/v1/model-evaluations", "EvaluationPage", "evaluation_id", "evaluation"),
    ],
)
def test_catalog_returns_actual_org_bound_rows(model_catalog_context, path, schema, key, fixture):
    ctx = model_catalog_context
    response = get(ctx, path)
    assert response.status_code == 200, response.json()
    value = response.json()
    validate_response(schema, value)
    assert [row[key] for row in value["items"]] == [str(ctx[fixture])]
    assert value["next_cursor"] is None
    assert response.headers["ETag"] and response.headers["Cache-Control"] == "no-store"
    if fixture == "model":
        assert value["items"][0]["status"] == "REGISTERED"
        assert not {"health", "healthy", "latency_ms", "metric_json", "org_id"} & value["items"][0].keys()
    else:
        assert value["items"][0]["artifact_ref"] == ctx["input_ref"]
        assert value["items"][0]["metrics"]["recall"] == 0.5


@pytest.mark.parametrize("path", ["/api/v1/models", "/api/v1/model-evaluations"])
@pytest.mark.parametrize(
    "query",
    [
        [("case_id", str(uuid4()))],
        [("org_id", str(uuid4()))],
        [("model_id", str(uuid4()))],
        [("limit", "1"), ("limit", "2")],
        [("cursor", "x"), ("cursor", "y")],
    ],
)
def test_catalog_rejects_unsupported_or_ambiguous_query(model_catalog_context, path, query):
    response = model_catalog_context["control_http"].get(path, params=query, headers=AUTH)
    assert response.status_code == 422 and "items" not in response.json()


def test_per_row_visibility_precedes_model_pagination(model_catalog_context):
    ctx = model_catalog_context
    insert_model(ctx, UUID(int=2))
    insert_model(ctx, UUID(int=3))
    ctx["facts"].blocked.add(ctx["model"])
    first = get(ctx, "/api/v1/models", limit=1)
    assert first.status_code == 200, first.json()
    assert [row["model_id"] for row in first.json()["items"]] == [str(UUID(int=2))]
    cursor = first.json()["next_cursor"]
    assert cursor is not None
    second = get(ctx, "/api/v1/models", limit=1, cursor=cursor)
    assert second.status_code == 200, second.json()
    assert [row["model_id"] for row in second.json()["items"]] == [str(UUID(int=3))]
    assert second.json()["next_cursor"] is None


def test_per_row_evaluation_scope_precedes_pagination(model_catalog_context):
    ctx = model_catalog_context
    insert_evaluation(ctx, ctx["model"], UUID(int=12))
    insert_evaluation(ctx, ctx["model"], UUID(int=13))
    ctx["facts"].blocked.add(ctx["evaluation"])
    first = get(ctx, "/api/v1/model-evaluations", limit=1)
    assert first.status_code == 200, first.json()
    assert [row["evaluation_id"] for row in first.json()["items"]] == [str(UUID(int=12))]
    second = get(ctx, "/api/v1/model-evaluations", limit=1, cursor=first.json()["next_cursor"])
    assert second.status_code == 200, second.json()
    assert [row["evaluation_id"] for row in second.json()["items"]] == [str(UUID(int=13))]
    assert second.json()["next_cursor"] is None


@pytest.mark.parametrize("path,key", [("/api/v1/models", "model"), ("/api/v1/model-evaluations", "evaluation")])
def test_known_denied_items_produce_authorized_empty_page(model_catalog_context, path, key):
    ctx = model_catalog_context
    ctx["facts"].blocked.add(ctx[key])
    response = get(ctx, path)
    assert response.status_code == 200, response.json()
    assert response.json() == {"items": [], "next_cursor": None}


def test_model_cursor_rejects_a_changed_visible_record_with_existing_catalog_semantics(model_catalog_context):
    ctx = model_catalog_context
    insert_model(ctx, UUID(int=2))
    first = get(ctx, "/api/v1/models", limit=1)
    assert first.status_code == 200 and first.json()["next_cursor"]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.model_registry SET status='RETIRED',row_version=row_version+1 WHERE model_id=%s", (ctx["model"],)
        )
    response = get(ctx, "/api/v1/models", limit=1, cursor=first.json()["next_cursor"])
    assert response.status_code == 422 and response.json()["code"] == "PAGE_CURSOR_INVALID"
    assert "items" not in response.json()


def test_model_page_rejects_version_change_between_signature_and_recheck(model_catalog_context):
    ctx = model_catalog_context
    engine = ctx["control_app"].state.business_database.engine
    changed = False

    def change_visible_row(connection, cursor, statement, parameters, context, executemany):
        nonlocal changed
        if not changed and "string_agg(model_id::text" in statement and "FROM mt.model_registry" in statement:
            # Use the existing root transaction: another connection would block on its shared row locks.
            changed = True
            connection.execute(
                text("UPDATE mt.model_registry SET status='RETIRED',row_version=row_version+1 WHERE model_id=:id"),
                {"id": ctx["model"]},
            )

    event.listen(engine, "after_cursor_execute", change_visible_row)
    try:
        response = get(ctx, "/api/v1/models", limit=1)
    finally:
        event.remove(engine, "after_cursor_execute", change_visible_row)
    assert changed, "the initial page signature must have been read before injecting a version change"
    assert response.status_code == 409 and response.json()["code"] == "PAGE_CURSOR_STALE"
    assert "items" not in response.json()


@pytest.mark.parametrize("defect", ["signature", "padding", "operation", "limit"])
def test_model_cursor_cannot_replay_with_a_different_binding(model_catalog_context, defect):
    ctx = model_catalog_context
    insert_model(ctx, UUID(int=2))
    first = get(ctx, "/api/v1/models", limit=1)
    assert first.status_code == 200 and first.json()["next_cursor"]
    cursor, path, limit = first.json()["next_cursor"], "/api/v1/models", 1
    if defect == "signature":
        cursor = ("A" if cursor[0] != "A" else "B") + cursor[1:]
    elif defect == "padding":
        cursor += "="
    elif defect == "operation":
        path = "/api/v1/model-evaluations"
    else:
        limit = 2
    response = get(ctx, path, limit=limit, cursor=cursor)
    assert response.status_code == 422 and "items" not in response.json()


@pytest.mark.parametrize("kind", ["model", "evaluation"])
def test_unknown_item_scope_fails_whole_page(model_catalog_context, kind):
    ctx = model_catalog_context
    ctx["facts"].unknown.add(ctx[kind])
    path = "/api/v1/models" if kind == "model" else "/api/v1/model-evaluations"
    response = get(ctx, path)
    assert response.status_code == 503 and "items" not in response.json()


@pytest.mark.parametrize("path", ["/api/v1/models", "/api/v1/model-evaluations"])
def test_absent_authentication_and_trusted_metadata_scope_fail_closed(model_catalog_context, path):
    ctx = model_catalog_context
    assert ctx["control_http"].get(path).status_code == 401
    ctx["object_facts"].supplemental = None
    response = get(ctx, path)
    assert response.status_code == 503 and "items" not in response.json()


def test_other_organization_model_is_not_a_candidate(model_catalog_context):
    ctx = model_catalog_context
    foreign = insert_model(ctx, uuid4(), actor=ctx["other_actor"])
    response = get(ctx, "/api/v1/models")
    assert response.status_code == 200, response.json()
    assert foreign not in {UUID(row["model_id"]) for row in response.json()["items"]}


def test_evaluation_with_non_uuid_storage_version_is_readable(model_catalog_context):
    ctx = model_catalog_context
    assert ctx["input_ref"]["version_id"].startswith("fs-v1-")
    response = get(ctx, "/api/v1/model-evaluations")
    assert response.status_code == 200, response.json()
    evaluation = next(row for row in response.json()["items"] if row["evaluation_id"] == str(ctx["evaluation"]))
    assert evaluation["artifact_ref"]["version_id"] == ctx["input_ref"]["version_id"]


def test_evaluation_accepts_uppercase_uuid_for_its_registered_report(model_catalog_context):
    ctx = model_catalog_context
    reference = dict(ctx["input_ref"], object_id=ctx["input_ref"]["object_id"].upper())
    identifier = insert_evaluation(ctx, ctx["model"], uuid4(), artifact=reference)
    response = get(ctx, "/api/v1/model-evaluations")
    assert response.status_code == 200, response.json()
    evaluation = next(row for row in response.json()["items"] if row["evaluation_id"] == str(identifier))
    assert evaluation["artifact_ref"] == reference


@pytest.mark.parametrize(
    "field,value",
    [
        ("object_id", "ffffffff-ffff-ffff-ffff-ffffffffffff"),
        ("version_id", "different-immutable-version"),
        ("sha256", "c" * 64),
    ],
)
def test_mismatched_evaluation_artifact_fails_without_returning_page(model_catalog_context, field, value):
    ctx = model_catalog_context
    insert_evaluation(ctx, ctx["model"], uuid4(), artifact=dict(ctx["input_ref"], **{field: value}))
    response = get(ctx, "/api/v1/model-evaluations")
    assert response.status_code == 503 and "items" not in response.json()


@pytest.mark.parametrize("path", ["/api/v1/models", "/api/v1/model-evaluations"])
def test_role_revocation_refuses_catalog(model_catalog_context, path):
    ctx = model_catalog_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.user_roles SET revoked_at=now(),row_version=row_version+1 WHERE user_id=%s AND revoked_at IS NULL",
            (ctx["actor"].user_id,),
        )
    response = get(ctx, path)
    assert response.status_code == 403 and "items" not in response.json()


def test_scope_revocation_after_projection_refuses_page_before_commit(model_catalog_context):
    ctx = model_catalog_context
    engine = ctx["control_app"].state.business_database.engine

    def revoke(connection, cursor, statement, parameters, context, executemany):
        if "model_catalog_projection" in statement:
            ctx["facts"].blocked.add(ctx["model"])

    event.listen(engine, "after_cursor_execute", revoke)
    try:
        response = get(ctx, "/api/v1/models")
    finally:
        event.remove(engine, "after_cursor_execute", revoke)
    assert response.status_code == 503 and "items" not in response.json()
