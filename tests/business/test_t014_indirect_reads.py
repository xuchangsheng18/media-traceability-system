"""Positive real HTTP object/source relationships, with explicit synthetic rule inputs."""

from uuid import UUID, uuid4

import psycopg
import pytest

from tests.business.history_fixtures import prepare_history, snapshot
from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context


def another_history(ctx, *, new_source=False):
    from tests.business.scoped_history_fixtures import append_synthetic_snapshot

    changed = dict(ctx)
    if new_source:
        changed["source_id"] = uuid4()
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(
                "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) VALUES(%s,%s,%s,'synthetic-related','synthetic','synthetic-only',ARRAY['upload','analysis','import'],'verified','test-version-1')",
                (changed["source_id"], ctx["actor"].org_id, ctx["case_id"]),
            )
    result = prepare_history(changed)
    try:
        append_synthetic_snapshot(result, snapshot(result, 1))
    finally:
        result["http"].__exit__(None, None, None)
    return result


def add_review(admin, ctx, identifier):
    evidence = uuid4()
    admin.execute(
        "INSERT INTO mt.evidence_item(evidence_id,org_id,case_id,task_id,run_version,result_version,asset_id,type,object_id,sha256,captured_at,mapping_version,authorization_version,immutable_state) VALUES(%s,%s,%s,%s,1,1,%s,'synthetic-review-input',%s,%s,now(),'synthetic/1','test-version-1','RECORDED')",
        (
            evidence,
            ctx["actor"].org_id,
            ctx["case_id"],
            ctx["task_id"],
            ctx["asset_id"],
            ctx["input_ref"]["object_id"],
            ctx["input_ref"]["sha256"],
        ),
    )
    admin.execute(
        "INSERT INTO mt.review_record(review_id,org_id,case_id,task_id,run_version,result_version,reviewer_id,decision,comments,review_version,policy_version,created_by) VALUES(%s,%s,%s,%s,1,1,%s,'return_for_evidence','synthetic-only',1,'policy-dev-1',%s)",
        (identifier, ctx["actor"].org_id, ctx["case_id"], ctx["task_id"], ctx["actor"].user_id, ctx["actor"].user_id),
    )
    admin.execute(
        "INSERT INTO mt.review_evidence(link_id,org_id,case_id,review_id,evidence_id,created_by) VALUES(%s,%s,%s,%s,%s,%s)",
        (uuid4(), ctx["actor"].org_id, ctx["case_id"], identifier, evidence, ctx["actor"].user_id),
    )


@pytest.mark.parametrize("operation", ["getImport", "getReview", "getFirstSource", "getPropagation"])
def test_indirect_read_HTTP_checks_every_source(control_context, permission_context, operation):
    ctx = control_context
    related = another_history(ctx, new_source=True)
    identifier = uuid4()
    sources = [ctx["source_id"]]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET purpose=ARRAY['upload','analysis','import'] WHERE source_id=%s",
            (ctx["source_id"],),
        )
        if operation == "getImport":
            sources.append(related["source_id"])
            admin.execute(
                "INSERT INTO mt.import_job(import_id,org_id,case_id,state,requested_count,created_by) VALUES(%s,%s,%s,'COMPLETED',2,%s)",
                (identifier, ctx["actor"].org_id, ctx["case_id"], ctx["actor"].user_id),
            )
            for ordinal, item in enumerate([ctx, related]):
                admin.execute(
                    "INSERT INTO mt.import_item(item_id,org_id,case_id,import_id,ordinal,source_id,asset_id,state) VALUES(%s,%s,%s,%s,%s,%s,%s,'accepted')",
                    (
                        uuid4(),
                        ctx["actor"].org_id,
                        ctx["case_id"],
                        identifier,
                        ordinal,
                        item["source_id"],
                        item["asset_id"],
                    ),
                )
            path = f"/api/v1/imports/{identifier}"
        elif operation == "getReview":
            add_review(admin, ctx, identifier)
            path = f"/api/v1/reviews/{identifier}"
        else:
            identifier = ctx["cluster_id"]
            sources.append(related["source_id"])
            evidence = uuid4()
            admin.execute(
                "INSERT INTO mt.evidence_item(evidence_id,org_id,case_id,task_id,run_version,result_version,asset_id,type,object_id,sha256,captured_at,mapping_version,authorization_version,immutable_state) VALUES(%s,%s,%s,%s,1,1,%s,'synthetic-related-asset',%s,%s,now(),'synthetic/1','test-version-1','RECORDED')",
                (
                    evidence,
                    ctx["actor"].org_id,
                    ctx["case_id"],
                    related["task_id"],
                    related["asset_id"],
                    related["input_ref"]["object_id"],
                    related["input_ref"]["sha256"],
                ),
            )
            for item, evidence_id in [(ctx, ctx["evidence_id"]), (related, evidence)]:
                admin.execute(
                    "INSERT INTO mt.cluster_member(member_id,org_id,case_id,cluster_id,asset_id,relation,evidence_id) VALUES(%s,%s,%s,%s,%s,'full_copy',%s)",
                    (uuid4(), ctx["actor"].org_id, ctx["case_id"], identifier, item["asset_id"], evidence_id),
                )
            path = (
                f"/api/v1/clusters/{identifier}/first-source"
                if operation == "getFirstSource"
                else f"/api/v1/propagation/{identifier}"
            )
    candidate(ctx, permission_context, ["asset.import", "review.read", "origin.read", "propagation.read"])
    http = ctx["control_http"]
    positive = http.get(path, headers=AUTH)
    assert positive.status_code == 200, positive.json()
    for source in sources:
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(
                "UPDATE mt.source_registry SET authorization_status='revoked',row_version=row_version+1 WHERE source_id=%s",
                (source,),
            )
        denied = http.get(path, headers=AUTH)
        assert (denied.status_code, denied.json()["code"]) == (403, "PERMISSION_REQUIRED")
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(
                "UPDATE mt.source_registry SET authorization_status='verified',row_version=row_version+1 WHERE source_id=%s",
                (source,),
            )


@pytest.mark.parametrize("operation", ["listReviews", "listPendingReviews"])
def test_review_collections_filter_before_pagination_and_allow_empty(control_context, permission_context, operation):
    ctx = control_context
    contexts = [another_history(ctx, new_source=True), another_history(ctx), another_history(ctx)]
    review_ids = [UUID(int=i + 1) for i in range(3)]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        for item, identifier in zip(contexts, review_ids):
            add_review(admin, item, identifier)
            admin.execute("UPDATE mt.analysis_task SET state='WAIT_REVIEW' WHERE task_id=%s", (item["task_id"],))
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s",
            (contexts[0]["source_id"],),
        )
    _, _, _, facts = candidate(ctx, permission_context, ["review.read"])
    identifiers = review_ids if operation == "listReviews" else [item["task_id"] for item in contexts]
    facts.blocked = {identifiers[1]}
    path = "/api/v1/reviews" + ("/pending" if operation == "listPendingReviews" else "")
    http = ctx["control_http"]
    response = http.get(path, params={"case_id": str(ctx["case_id"]), "limit": 1}, headers=AUTH)
    assert response.status_code == 200, response.json()
    key = "review_id" if operation == "listReviews" else "task_id"
    assert [v[key] for v in response.json()["items"]] == [str(identifiers[2])]
    assert response.json()["next_cursor"] is None
    facts.blocked = set(identifiers)
    empty = http.get(path, params={"case_id": str(ctx["case_id"]), "limit": 1}, headers=AUTH)
    assert empty.status_code == 200, empty.json()
    assert empty.json() == {"items": [], "next_cursor": None}
    facts.blocked = set()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='verified' WHERE source_id=%s",
            (contexts[0]["source_id"],),
        )
    first = http.get(path, params={"case_id": str(ctx["case_id"]), "limit": 1}, headers=AUTH)
    assert first.status_code == 200 and first.json()["next_cursor"] is not None
    cursor = first.json()["next_cursor"]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s",
            (contexts[0]["source_id"],),
        )
    stale = http.get(path, params={"case_id": str(ctx["case_id"]), "limit": 1, "cursor": cursor}, headers=AUTH)
    assert (stale.status_code, stale.json()["code"]) == (422, "PAGE_CURSOR_INVALID")
