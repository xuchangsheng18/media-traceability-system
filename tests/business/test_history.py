import copy
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def history_context(business_context):
    if not (ROOT / "backend/business_app/history/repository.py").is_file():
        yield None
        return
    from tests.business.history_fixtures import prepare_history

    context = prepare_history(business_context)
    try:
        yield context
    finally:
        context["http"].__exit__(None, None, None)


def repository(context):
    from business_app.history.repository import ResultRepository

    return ResultRepository(
        context["app"].state.business_database, context["app"].state.upload_service.store, context["authority"]
    )


def scope(context):
    from business_app.types import Scope

    return Scope(context["actor"], context["case_id"])


def test_two_runs_return_exact_old_snapshot(history_context):
    assert history_context is not None, "actual immutable snapshot persistence is not implemented"
    from tests.business.history_fixtures import snapshot

    first, second = snapshot(history_context, 1), snapshot(history_context, 2)
    repo = repository(history_context)
    key1 = repo.append_snapshot(scope(history_context), first)
    repo.append_snapshot(scope(history_context), second)
    assert repo.load_exact(scope(history_context), key1) == first
    assert repo.load_latest(scope(history_context), "getTask", history_context["task_id"])[0].run_version == 2


def test_result_mutation_rejected_by_DB(history_context):
    assert history_context is not None
    from tests.business.history_fixtures import snapshot

    repository(history_context).append_snapshot(scope(history_context), snapshot(history_context, 1))
    for query in [
        "UPDATE mt.task_result SET policy_version='changed'",
        "DELETE FROM mt.task_result",
        "TRUNCATE mt.task_result CASCADE",
    ]:
        with pytest.raises(psycopg.Error):
            with psycopg.connect(history_context["admin_dsn"]) as connection:
                connection.execute(query)


def test_missing_exact_version_is_404(history_context):
    assert history_context is not None
    from business_app.errors import BusinessError
    from business_app.types import ResultKey

    with pytest.raises(BusinessError) as failure:
        repository(history_context).load_exact(scope(history_context), ResultKey(history_context["task_id"], 99, 1))
    assert failure.value.http_status == 404


def test_invalid_projection_or_binding_rejected(history_context):
    assert history_context is not None
    from business_app.errors import BusinessError

    from tests.business.history_fixtures import snapshot

    repo = repository(history_context)
    valid = snapshot(history_context, 1)
    bad = copy.deepcopy(valid)
    bad["api_projections"][0]["response"]["task_id"] = str(history_context["cluster_id"])
    with pytest.raises(BusinessError):
        repo.append_snapshot(scope(history_context), bad)
    bad = copy.deepcopy(valid)
    bad["projection_refs"][0]["json_pointer"] = "/api_projections/99/response"
    with pytest.raises(BusinessError):
        repo.append_snapshot(scope(history_context), bad)


def test_run_cannot_change_input_digest(history_context):
    from business_app.errors import BusinessError

    from tests.business.history_fixtures import snapshot

    original = snapshot(history_context, 1)
    repository(history_context).append_snapshot(scope(history_context), original)
    changed = snapshot(history_context, 1, 2)
    from tests.business.history_fixtures import prepare_history

    other = prepare_history(history_context)
    changed["input_refs"].append(other["input_ref"])
    with pytest.raises(BusinessError):
        repository(history_context).append_snapshot(scope(history_context), changed)
    other["http"].__exit__(None, None, None)


def test_primary_task_object_must_be_in_inputs(history_context):
    from business_app.errors import BusinessError

    from tests.business.history_fixtures import prepare_history, snapshot

    other = prepare_history(history_context)
    changed = snapshot(history_context, 1)
    changed["input_refs"] = [other["input_ref"]]
    with pytest.raises(BusinessError):
        repository(history_context).append_snapshot(scope(history_context), changed)
    other["http"].__exit__(None, None, None)


def evidence(context):
    from datetime import datetime, timezone
    from uuid import uuid4

    return {
        "evidence_id": str(uuid4()),
        "case_id": str(context["case_id"]),
        "task_id": str(context["task_id"]),
        "run_version": 1,
        "result_version": 1,
        "kind": "original",
        "asset_id": context["asset_id"],
        "object_ref": copy.deepcopy(context["input_ref"]),
        "time_range": None,
        "bbox": None,
        "mapping_version": "test-only/1",
        "model_name": None,
        "model_version": None,
        "authorization_version": "test-version-1",
        "sha256": context["input_ref"]["sha256"],
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def test_nested_evidence_versions_cannot_contradict_headers(history_context):
    from business_app.errors import BusinessError

    from tests.business.history_fixtures import snapshot

    changed = snapshot(history_context, 1)
    item = evidence(history_context)
    item["run_version"] = 2
    changed["api_projections"][3]["response"]["items"] = [item]
    with pytest.raises(BusinessError):
        repository(history_context).append_snapshot(scope(history_context), changed)


def test_nested_object_version_is_actually_verified(history_context):
    from business_app.errors import BusinessError

    from tests.business.history_fixtures import snapshot

    changed = snapshot(history_context, 1)
    item = evidence(history_context)
    item["object_ref"]["version_id"] = "fs-v1-" + "0" * 32
    changed["api_projections"][3]["response"]["items"] = [item]
    repo = repository(history_context)
    repo.validate_snapshot(changed)
    with pytest.raises(BusinessError):
        with repo.database.transaction(scope(history_context)) as connection:
            repo.verify_current_inputs(connection, scope(history_context), changed)


def test_ranking_identity_cannot_be_rebound(history_context):
    from business_app.errors import BusinessError

    from tests.business.history_fixtures import snapshot

    one = snapshot(history_context, 1)
    two = snapshot(history_context, 2)
    two["api_projections"][5]["response"]["ranking_id"] = one["api_projections"][5]["response"]["ranking_id"]
    repository(history_context).append_snapshot(scope(history_context), one)
    with pytest.raises(BusinessError):
        repository(history_context).append_snapshot(scope(history_context), two)


@pytest.mark.parametrize("operation", ["getTimeline", "getFirstSource", "getPropagation"])
def test_latest_across_tasks_uses_newest_snapshot(history_context, operation):
    from uuid import uuid4

    from tests.business.history_fixtures import snapshot

    context = history_context
    repository(context).append_snapshot(scope(context), snapshot(context, 10))
    next_task = uuid4()
    with psycopg.connect(context["admin_dsn"]) as connection:
        connection.execute(
            """INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility)
        VALUES(%s,%s,%s,%s,'test-only','normal','CREATED','policy-dev-1',ARRAY[]::text[],'draft_only')""",
            (next_task, context["actor"].org_id, context["case_id"], context["asset_id"]),
        )
    fresh = snapshot(dict(context, task_id=next_task), 1)
    repository(context).append_snapshot(scope(context), fresh)
    resource = context["asset_id"] if operation == "getTimeline" else context["cluster_id"]
    from uuid import UUID

    key, _ = repository(context).load_latest(scope(context), operation, UUID(str(resource)))
    assert key.task_id == next_task
