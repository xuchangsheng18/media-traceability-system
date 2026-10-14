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
