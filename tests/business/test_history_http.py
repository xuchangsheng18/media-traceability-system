from uuid import uuid4

import psycopg
import pytest

from tests.business.test_history import history_context as history_context
from tests.business.test_history import repository, scope

AUTH = {"Authorization": "Bearer test-only-valid-token"}
OPERATIONS = [
    "getTask",
    "getRiskFindings",
    "getForensics",
    "getTaskEvidence",
    "getTimeline",
    "getFirstSource",
    "getPropagation",
]


def route(context, operation):
    task = str(context["task_id"])
    asset = context["asset_id"]
    cluster = str(context["cluster_id"])
    return {
        "getTask": f"/api/v1/analysis/tasks/{task}",
        "getRiskFindings": f"/api/v1/analysis/tasks/{task}/risk-findings",
        "getForensics": f"/api/v1/analysis/tasks/{task}/forensics",
        "getTaskEvidence": f"/api/v1/analysis/tasks/{task}/evidence",
        "getTimeline": f"/api/v1/assets/{asset}/timeline",
        "getFirstSource": f"/api/v1/clusters/{cluster}/first-source",
        "getPropagation": f"/api/v1/propagation/{cluster}",
    }[operation]


def history(context, operation, run=1):
    params = {"history[run_version]": str(run), "history[result_version]": "1"}
    if operation in {"getTimeline", "getFirstSource", "getPropagation"}:
        params["history[task_id]"] = str(context["task_id"])
    return params


def seed(context):
    from tests.business.history_fixtures import snapshot

    one, two = snapshot(context, 1), snapshot(context, 2)
    repository(context).append_snapshot(scope(context), one)
    repository(context).append_snapshot(scope(context), two)
    return one, two


@pytest.mark.parametrize("operation", OPERATIONS)
def test_history_headers_match_snapshot(history_context, operation):
    assert history_context is not None
    one, _ = seed(history_context)
    response = history_context["http"].get(
        route(history_context, operation), params=history(history_context, operation), headers=AUTH
    )
    assert response.status_code == 200, response.text
    assert response.headers["X-Task-Id"] == str(history_context["task_id"])
    assert response.headers["X-Run-Version"] == "1" and response.headers["X-Result-Version"] == "1"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == next(x["response"] for x in one["api_projections"] if x["operation_id"] == operation)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_history_group_must_be_complete(history_context, operation):
    assert history_context is not None
    seed(history_context)
    url = route(history_context, operation)
    for params in [
        {"history[run_version]": "1"},
        {**history(history_context, operation), "history[unknown]": "1"},
        list(history(history_context, operation).items()) + [("history[run_version]", "2")],
    ]:
        assert history_context["http"].get(url, params=params, headers=AUTH).status_code == 422


@pytest.mark.parametrize("operation", OPERATIONS)
def test_omitted_history_preserves_latest_selection(history_context, operation):
    assert history_context is not None
    _, two = seed(history_context)
    response = history_context["http"].get(route(history_context, operation), headers=AUTH)
    assert response.status_code == 200
    assert response.headers["X-Run-Version"] == "2"
    assert response.json() == next(x["response"] for x in two["api_projections"] if x["operation_id"] == operation)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_no_snapshot_does_not_return_empty_success(history_context, operation):
    assert history_context is not None
    response = history_context["http"].get(
        route(history_context, operation), params=history(history_context, operation), headers=AUTH
    )
    assert response.status_code == 404


def test_current_access_revoked_denies_old_result(history_context):
    assert history_context is not None
    seed(history_context)
    with psycopg.connect(history_context["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.case_membership SET revoked_at=now() WHERE case_id=%s", (history_context["case_id"],)
        )
    assert (
        history_context["http"]
        .get(route(history_context, "getTask"), params=history(history_context, "getTask"), headers=AUTH)
        .status_code
        == 404
    )


def test_path_and_ranking_must_match_result(history_context):
    assert history_context is not None
    seed(history_context)
    params = {**history(history_context, "getFirstSource"), "ranking_id": str(uuid4())}
    assert (
        history_context["http"].get(route(history_context, "getFirstSource"), params=params, headers=AUTH).status_code
        == 404
    )
    params = {**history(history_context, "getFirstSource"), "history[task_id]": str(uuid4())}
    assert (
        history_context["http"].get(route(history_context, "getFirstSource"), params=params, headers=AUTH).status_code
        == 404
    )
