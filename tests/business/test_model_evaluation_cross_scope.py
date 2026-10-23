"""Real foreign-unit records must stay outside runtime model metadata reads."""

import hashlib
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from business_app.contracts import validate_response
from business_app.data_scope import AccessMode
from business_app.scope_context import current_data_scope
from sqlalchemy import event, text

from tests.business.test_controls import control_context as control_context
from tests.business.test_model_catalog import get, insert_evaluation, insert_model
from tests.business.test_model_catalog import model_catalog_context as model_catalog_context
from tests.business.test_t014_permissions import permission_context as permission_context


@pytest.fixture
def foreign_evaluation_context(model_catalog_context) -> dict[str, Any]:
    ctx = model_catalog_context
    actor = ctx["other_actor"]
    assert actor.org_id != ctx["actor"].org_id
    foreign_model = insert_model(ctx, uuid4(), actor=actor)
    object_id = uuid4()
    synthetic_report = b"self-owned synthetic foreign-unit evaluation report fixture"
    reference = dict(
        object_id=str(object_id),
        version_id="synthetic-report-version/1",
        sha256=hashlib.sha256(synthetic_report).hexdigest(),
    )
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,"
            "sha256,size_bytes,created_by) VALUES(%s,%s,%s,'synthetic-cross-scope',%s,%s,%s,%s,%s)",
            (
                object_id,
                actor.org_id,
                ctx["other_case_id"],
                "synthetic-report/" + str(object_id),
                reference["version_id"],
                reference["sha256"],
                len(synthetic_report),
                actor.user_id,
            ),
        )
    foreign_evaluation = insert_evaluation(dict(ctx, actor=actor), foreign_model, uuid4(), artifact=reference)
    # Establish that the target and exact registered report really exist together.
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT e.org_id,m.org_id,o.org_id,o.object_id,o.version_id,o.sha256 "
            "FROM mt.model_evaluation e JOIN mt.model_registry m "
            "ON m.org_id=e.org_id AND m.model_id=e.model_id "
            "JOIN mt.object_version o ON o.org_id=e.org_id "
            "AND o.object_id::text=e.artifact_ref->>'object_id' "
            "AND o.version_id=e.artifact_ref->>'version_id' "
            "AND o.sha256=e.artifact_ref->>'sha256' WHERE e.evaluation_id=%s",
            (foreign_evaluation,),
        ).fetchone() == (
            actor.org_id,
            actor.org_id,
            actor.org_id,
            object_id,
            reference["version_id"],
            reference["sha256"],
        )
    return dict(
        ctx,
        foreign_model=foreign_model,
        foreign_evaluation=foreign_evaluation,
        foreign_reference=reference,
    )


def test_real_foreign_evaluation_is_absent_from_list_candidates(foreign_evaluation_context):
    ctx = foreign_evaluation_context
    engine = ctx["control_app"].state.business_database.engine
    inspected = False
    foreign_candidate: list[Any] = []

    def inspect_runtime_scope(connection, cursor, statement, parameters, context, executemany):
        nonlocal inspected
        if inspected or "SELECT evaluation_id,row_version FROM mt.model_evaluation" not in statement:
            return
        inspected = True
        scope = current_data_scope()
        assert scope is not None and scope.mode is AccessMode.ORGANIZATION
        assert scope.operation_id == "listEvaluations" and scope.actor == ctx["actor"]
        foreign_candidate.append(
            connection.execute(
                text("SELECT evaluation_id FROM mt.model_evaluation WHERE evaluation_id=:id"),
                {"id": ctx["foreign_evaluation"]},
            ).scalar_one_or_none()
        )

    event.listen(engine, "after_cursor_execute", inspect_runtime_scope)
    try:
        response = get(ctx, "/api/v1/model-evaluations")
    finally:
        event.remove(engine, "after_cursor_execute", inspect_runtime_scope)
    assert inspected and foreign_candidate == [None]
    assert response.status_code == 200, response.json()
    validate_response("EvaluationPage", response.json())
    assert [row["evaluation_id"] for row in response.json()["items"]] == [str(ctx["evaluation"])]
    assert response.json()["next_cursor"] is None


def test_artifact_definer_returns_null_for_real_foreign_evaluation_and_registered_report(foreign_evaluation_context):
    ctx = foreign_evaluation_context
    engine = ctx["control_app"].state.business_database.engine
    inspected = False
    foreign_artifact: list[Any] = []

    def inspect_artifact_scope(connection, cursor, statement, parameters, context, executemany):
        nonlocal inspected
        if inspected or "SELECT mt.model_evaluation_artifact_metadata(" not in statement:
            return
        inspected = True
        scope = current_data_scope()
        assert scope is not None and scope.mode is AccessMode.ORGANIZATION
        assert scope.operation_id == "listEvaluations" and scope.actor == ctx["actor"]
        foreign_artifact.append(
            connection.execute(
                text("SELECT mt.model_evaluation_artifact_metadata(:id)"),
                {"id": ctx["foreign_evaluation"]},
            ).scalar_one()
        )

    event.listen(engine, "after_cursor_execute", inspect_artifact_scope)
    try:
        response = get(ctx, "/api/v1/model-evaluations")
    finally:
        event.remove(engine, "after_cursor_execute", inspect_artifact_scope)
    assert inspected and foreign_artifact == [None]
    assert response.status_code == 200, response.json()
    assert [row["evaluation_id"] for row in response.json()["items"]] == [str(ctx["evaluation"])]
    assert response.json()["items"][0]["artifact_ref"] == ctx["input_ref"]
