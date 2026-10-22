"""Real isolated SQL/HTTP reads of explicit self-owned producer snapshots."""

import hashlib
import json
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.history.repository import CURRENT_SCHEMA, canonical

from tests.business.history_fixtures import snapshot
from tests.business.test_history import evidence, repository
from tests.business.test_history import history_context as _history_context
from tests.business.test_history_http import AUTH, OPERATIONS, history, route

history_context = _history_context


def seed_evidence(context, run=1, result=1, count=5, *, next_cursor=None, wrong_binding=False, duplicate=False):
    """Insert a synthetic producer transaction, never mutate an immutable result.

    Public append currently rejects references to evidence not yet persisted;
    this fixture prepares the result and its evidence together with admin-only
    isolated-test SQL. Production reads still use the unchanged real repository.
    """
    payload = snapshot(context, run, result)
    items = []
    for _ in range(count):
        item = evidence(context)
        item.update(run_version=run, result_version=result)
        items.append(item)
    if duplicate:
        items.append(dict(items[0]))
    payload["api_projections"][3]["response"] = {"items": items, "next_cursor": next_cursor}
    if wrong_binding:
        items[-1]["case_id"] = str(context["other_case_id"])
    repository(context).validate_snapshot(payload)
    key = payload["binding"]
    with psycopg.connect(context["admin_dsn"]) as connection:
        connection.execute(
            "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,"
            "policy_version,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT(case_id,task_id,run_version) DO NOTHING",
            (
                uuid4(),
                context["actor"].org_id,
                context["case_id"],
                context["task_id"],
                run,
                hashlib.sha256(canonical({"input_refs": payload["input_refs"]})).hexdigest(),
                key["dag_version"],
                key["policy_version"],
                context["actor"].user_id,
            ),
        )
        connection.execute(
            "INSERT INTO mt.task_result(result_id,org_id,case_id,task_id,run_version,result_version,sha256,"
            "policy_version,summary,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
            (
                uuid4(),
                context["actor"].org_id,
                context["case_id"],
                context["task_id"],
                run,
                result,
                hashlib.sha256(canonical(payload)).hexdigest(),
                key["policy_version"],
                json.dumps({"snapshot_schema_id": CURRENT_SCHEMA, "snapshot": payload}),
                context["actor"].user_id,
            ),
        )
        recorded = set()
        for item in items:
            if item["evidence_id"] in recorded:
                continue
            recorded.add(item["evidence_id"])
            connection.execute(
                "INSERT INTO mt.evidence_item(evidence_id,org_id,case_id,task_id,run_version,result_version,"
                "asset_id,type,object_id,sha256,captured_at,mapping_version,authorization_version,immutable_state) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,'synthetic-paging-only',%s,%s,now(),%s,%s,'RECORDED')",
                (
                    UUID(item["evidence_id"]),
                    context["actor"].org_id,
                    context["case_id"],
                    context["task_id"],
                    run,
                    result,
                    context["asset_id"],
                    context["input_ref"]["object_id"],
                    item["sha256"],
                    item["mapping_version"],
                    item["authorization_version"],
                ),
            )
    return payload["api_projections"][3]["response"]


def read(context, params=None, headers=AUTH):
    return context["http"].get(route(context, "getTaskEvidence"), params=params, headers=headers)


def test_real_multi_page_current_and_exact_history_keep_headers_and_order(history_context):
    ctx = history_context
    old = seed_evidence(ctx, 1)
    latest = seed_evidence(ctx, 2)
    for params, source, run in [({}, latest, "2"), (history(ctx, "getTaskEvidence"), old, "1")]:
        legacy = read(ctx, params)
        assert legacy.status_code == 200 and legacy.json() == source
        selected, cursor = [], None
        for expected_count in [2, 2, 1]:
            query = dict(params, limit=2)
            if cursor is not None:
                query["cursor"] = cursor
            response = read(ctx, query)
            assert response.status_code == 200, response.text
            assert response.headers["X-Task-Id"] == str(ctx["task_id"])
            assert response.headers["X-Run-Version"] == run and response.headers["X-Result-Version"] == "1"
            assert response.headers["Cache-Control"] == "no-store"
            body = response.json()
            assert len(body["items"]) == expected_count
            selected.extend(body["items"])
            cursor = body["next_cursor"]
        assert selected == source["items"] and cursor is None
    # Cursor-only requests use the declared default 20, not an invented required limit.
    assert read(ctx, {"limit": 20}).json() == latest


def test_cursor_only_uses_default_limit_and_pages_current_snapshot(history_context):
    ctx = history_context
    source = seed_evidence(ctx, count=21)
    first = read(ctx, {"limit": 20})
    assert first.status_code == 200 and len(first.json()["items"]) == 20
    second = read(ctx, {"cursor": first.json()["next_cursor"]})
    assert second.status_code == 200 and second.json() == {"items": source["items"][20:], "next_cursor": None}


def test_latest_advance_rejects_old_cursor_but_exact_old_history_still_works(history_context):
    ctx = history_context
    old = seed_evidence(ctx, 1)
    first = read(ctx, {"limit": 2})
    token = first.json()["next_cursor"]
    seed_evidence(ctx, 2)
    moved = read(ctx, {"limit": 2, "cursor": token})
    assert (moved.status_code, moved.json()["code"]) == (422, "PAGE_CURSOR_INVALID")
    exact = read(ctx, {**history(ctx, "getTaskEvidence"), "limit": 2, "cursor": token})
    assert exact.status_code == 200 and exact.json()["items"] == old["items"][2:4]
    missing = read(ctx, {**history(ctx, "getTaskEvidence", run=99), "limit": 2, "cursor": token})
    assert (missing.status_code, missing.json()["code"]) == (404, "TASK_RUN_NOT_FOUND")
    missing_result = read(
        ctx,
        {"history[run_version]": 1, "history[result_version]": 99, "limit": 2, "cursor": token},
    )
    assert (missing_result.status_code, missing_result.json()["code"]) == (404, "RESULT_NOT_FOUND")


def test_no_arguments_preserves_nonnull_legacy_producer_cursor_and_no_paged_fallback(history_context):
    ctx = history_context
    seed_evidence(ctx, 1)
    incomplete = seed_evidence(ctx, 2, next_cursor="producer-still-has-unpublished-evidence")
    legacy = read(ctx)
    assert legacy.status_code == 200 and legacy.json() == incomplete
    for params in [{"limit": 2}, {"cursor": "not-a-local-token"}]:
        response = read(ctx, params)
        assert (response.status_code, response.json()["code"]) == (503, "EVIDENCE_PAGING_SOURCE_INCOMPLETE")
        assert "items" not in response.json()
    old = read(ctx, {**history(ctx, "getTaskEvidence"), "limit": 2})
    assert old.status_code == 200 and len(old.json()["items"]) == 2


def test_empty_projection_is_valid_empty_page_not_missing_result(history_context):
    ctx = history_context
    source = seed_evidence(ctx, count=0)
    empty = read(ctx, {"limit": 1})
    assert empty.status_code == 200 and empty.json() == source == {"items": [], "next_cursor": None}


def test_query_bounds_duplicates_and_unsupported_filters_are_rejected(history_context):
    ctx = history_context
    seed_evidence(ctx)
    for params in [
        {"limit": 0},
        {"limit": 101},
        {"limit": "invalid"},
        {"cursor": ""},
        {"cursor": "x" * 129},
        [("limit", "1"), ("limit", "1")],
        [("cursor", "x"), ("cursor", "x")],
        {"limit": 1, "case_id": str(ctx["case_id"])},
        {"limit": 1, "unknown": "filter"},
    ]:
        denied = read(ctx, params)
        assert denied.status_code == 422 and "items" not in denied.json(), denied.text
    # Existing endpoints do not acquire evidence paging parameters as a side effect.
    for operation in set(OPERATIONS) - {"getTaskEvidence"}:
        for name, value in [("limit", 1), ("cursor", "x")]:
            denied = ctx["http"].get(route(ctx, operation), params={name: value}, headers=AUTH)
            assert (denied.status_code, denied.json()["code"]) == (422, "READ_PARAMETER_UNSUPPORTED")


def test_each_page_rechecks_authentication_permission_and_current_membership(history_context):
    ctx = history_context
    seed_evidence(ctx)
    first = read(ctx, {"limit": 2})
    query = {"limit": 2, "cursor": first.json()["next_cursor"]}
    for headers in [{}, {"Authorization": "Bearer invalid-synthetic-token"}]:
        denied = read(ctx, query, headers)
        assert denied.status_code == 401 and "items" not in denied.json()
    permissions = ctx["app"].state.permission_authority
    previous = permissions.permissions
    permissions.permissions = previous - {"evidence.read"}
    denied = read(ctx, query)
    assert (denied.status_code, denied.json()["code"]) == (403, "PERMISSION_REQUIRED")
    permissions.permissions = previous
    assert read(ctx, query).status_code == 200
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.case_membership SET revoked_at=now() WHERE case_id=%s", (ctx["case_id"],))
    denied = read(ctx, query)
    assert denied.status_code == 404 and "items" not in denied.json()


def test_each_page_rechecks_source_authorization(history_context):
    ctx = history_context
    seed_evidence(ctx)
    first = read(ctx, {"limit": 2})
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked',row_version=row_version+1 WHERE source_id=%s",
            (ctx["source_id"],),
        )
    denied = read(ctx, {"limit": 2, "cursor": first.json()["next_cursor"]})
    assert denied.status_code == 403 and "items" not in denied.json()


@pytest.mark.parametrize(
    "defect,expected",
    [("binding", (409, "SNAPSHOT_BINDING_INVALID")), ("duplicate", (503, "RESPONSE_CONTRACT_UNAVAILABLE"))],
)
def test_bad_projection_never_gets_a_paged_success(history_context, defect, expected):
    ctx = history_context
    seed_evidence(ctx, wrong_binding=defect == "binding", duplicate=defect == "duplicate")
    denied = read(ctx, {"limit": 1})
    assert (denied.status_code, denied.json()["code"]) == expected and "items" not in denied.json()


def test_strict_cursor_encoding_rejects_tampered_or_noncanonical_forms_over_http(history_context):
    ctx = history_context
    seed_evidence(ctx)
    first = read(ctx, {"limit": 2})
    token = first.json()["next_cursor"]
    for invalid in [token + "=", " " + token, token + "\n", token[:-1], "_" + token[1:], "中" + token[1:]]:
        denied = read(ctx, {"limit": 2, "cursor": invalid})
        assert (denied.status_code, denied.json()["code"]) == (422, "PAGE_CURSOR_INVALID")
        assert "items" not in denied.json()
