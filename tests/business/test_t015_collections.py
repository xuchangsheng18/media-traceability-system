"""Actual task/version and per-item SQL/HTTP boundaries with synthetic facts only."""

import importlib
import importlib.util
import time
from contextlib import contextmanager
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.data_scope import ResourceBinding, TaskBinding
from business_app.errors import BusinessError
from business_app.permissions.context import request_authorization
from business_app.permissions.object_facts import ObjectFactsReader, digest
from business_app.permissions.rule_types import AuthorizationEvidence, ConditionFacts, RuleTarget
from business_app.permissions.types import Principal
from business_app.scope_context import bind_data_scope, current_data_scope
from business_app.types import ResultKey, Scope
from sqlalchemy import event, text

from tests.business.history_fixtures import snapshot
from tests.business.http_fixtures import FixtureFence
from tests.business.scoped_history_fixtures import append_synthetic_snapshot
from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH, request_approval
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_indirect_reads import add_review, another_history
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t015_scope_sql import principal, two_cases


def collections_module():
    name = "business_app.scope_collections"
    assert importlib.util.find_spec(name) is not None, "TRUSTED_TASK_AND_COLLECTION_SCOPE_REQUIRED"
    return importlib.import_module(name)


def test_single_target_metadata_and_supplement_use_the_same_readonly_root(business_context):
    ctx = business_context
    first, _ = two_cases(ctx)
    metadata_connections, supplemental_connections = [], []

    class Supplemental:
        def read(self, current, operation_id, target, *, connection):
            supplemental_connections.append(connection)
            assert connection.exec_driver_sql("SHOW transaction_read_only").scalar_one() == "on"
            return ConditionFacts(
                current, target, {"classification": True, "read_purpose": True}, "c" * 64, time.time() + 60
            )

    def observe(connection, cursor, statement, parameters, context, executemany):
        if "SELECT mt.lookup_scope_metadata" in statement:
            metadata_connections.append(connection)

    engine = ctx["database"].engine
    event.listen(engine, "before_cursor_execute", observe)
    try:
        reader = ObjectFactsReader(ctx["database"], supplemental=Supplemental())
        target = RuleTarget(ctx["actor"].org_id, "task", first["task"], 1, first["case"], None, None)
        facts = reader.read(principal(ctx), "getTask", target)
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    assert facts.checks["classification"] is True
    assert metadata_connections and supplemental_connections
    assert metadata_connections == supplemental_connections, "ONE_TARGET_MUST_NOT_SPLIT_SQL_AND_SUPPLEMENTAL_ROOTS"


@contextmanager
def synthetic_target(ctx, operation, target):
    actor = ctx["actor"]
    principal = Principal(actor, "https://identity.example.test", str(actor.user_id), int(time.time()) + 600)
    evidence = AuthorizationEvidence(
        principal,
        operation,
        target,
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-collection-only",
        time.time() + 60,
    )
    with request_authorization(evidence, FixtureFence(frozenset({actor})), mutation=False):
        yield evidence


def test_same_case_task_and_history_version_swap_is_denied(control_context):
    ctx = control_context
    other = another_history(ctx)
    repository = ctx["app"].state.result_repository
    scope = Scope(ctx["actor"], ctx["case_id"])
    target = RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], None, None)
    with synthetic_target(ctx, "getTask", target):
        with pytest.raises(BusinessError) as denied:
            repository.load_exact(scope, ResultKey(other["task_id"], 1, 1))
        assert denied.value.http_status in {403, 404, 409, 503}
    append_synthetic_snapshot(ctx, snapshot(ctx, 2))
    module = collections_module()
    with synthetic_target(ctx, "getTask", target), repository.database.transaction(scope) as connection:
        root = current_data_scope()
        fixed = module.bind_task_scope(connection, root, TaskBinding(ctx["task_id"], 1, 1))
        with bind_data_scope(fixed):
            assert repository.load_exact(scope, ResultKey(ctx["task_id"], 1, 1))["binding"]["run_version"] == 1
            with pytest.raises(BusinessError):
                repository.load_exact(scope, ResultKey(ctx["task_id"], 2, 1))
    assert current_data_scope() is None


@pytest.mark.parametrize("defect", ["task", "run", "result"])
def test_related_join_requires_org_case_task_and_result_version(control_context, defect):
    ctx = control_context
    other = another_history(ctx) if defect == "task" else ctx
    run, result = (2, 1) if defect == "run" else (1, 2) if defect == "result" else (1, 1)
    if defect != "task":
        append_synthetic_snapshot(ctx, snapshot(ctx, run, result))
    review, evidence = uuid4(), uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        add_review(admin, ctx, review)
        admin.execute(
            "INSERT INTO mt.evidence_item(evidence_id,org_id,case_id,task_id,run_version,result_version,asset_id,type,object_id,sha256,captured_at,mapping_version,authorization_version,immutable_state) VALUES(%s,%s,%s,%s,%s,%s,%s,'synthetic-wrong-review-binding',%s,%s,now(),'synthetic/1','test-version-1','RECORDED')",
            (
                evidence,
                ctx["actor"].org_id,
                ctx["case_id"],
                other["task_id"],
                run,
                result,
                other["asset_id"],
                other["input_ref"]["object_id"],
                other["input_ref"]["sha256"],
            ),
        )
    # Existing composite FKs alone permit this link, but 0003 already rejects its
    # task/result semantics. Preserve that real database defense, never disable it.
    with (
        pytest.raises(psycopg.errors.CheckViolation, match="review evidence result binding mismatch"),
        psycopg.connect(ctx["admin_dsn"]) as admin,
    ):
        admin.execute(
            "INSERT INTO mt.review_evidence(link_id,org_id,case_id,review_id,evidence_id) VALUES(%s,%s,%s,%s,%s)",
            (uuid4(), ctx["actor"].org_id, ctx["case_id"], review, evidence),
        )
    target = RuleTarget(ctx["actor"].org_id, "review", review, 1, ctx["case_id"], None, None)
    app = ctx["control_app"]
    with (
        synthetic_target(ctx, "getReview", target),
        app.state.business_database.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        value = app.state.reviews.wire(connection, review)
        assert value["task_id"] == str(ctx["task_id"])
        assert (value["run_version"], value["result_version"]) == (1, 1)
        assert evidence not in {UUID(identifier) for identifier in value["evidence_ids"]}
        assert len(value["evidence_ids"]) == 1


def approval_collection(ctx, permission_context):
    identifiers = tuple(sorted((UUID(request_approval(ctx)) for _ in range(3)), key=str))
    configured, objects, authority, _ = candidate(ctx, permission_context, ["approval.read"])

    class InstitutionalCollectionFacts:
        blocked: set[UUID] = set()
        unknown: set[UUID] = set()
        missing: set[UUID] = set()
        calls: list[tuple[str, str, UUID | None]] = []

        def read(self, principal, operation_id, target, *, connection):
            assert principal == configured["principal"] and target.case_id == ctx["case_id"]
            self.calls.append((operation_id, target.kind, target.object_id))
            if target.object_id in self.missing:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            checks = {
                "metadata_scope": None if target.object_id in self.unknown else target.object_id not in self.blocked
            }
            if target.kind == "case":
                # Explicit synthetic case-wide delegation for the collection header.
                checks["own_or_delegated_request"] = True
            return ConditionFacts(principal, target, checks, digest([operation_id, target, checks]), time.time() + 60)

    facts = InstitutionalCollectionFacts()
    objects.supplemental = facts
    return identifiers, configured, authority, facts


def test_item_filter_precedes_limit_count_and_cursor(control_context, permission_context):
    ctx = control_context
    identifiers, configured, authority, facts = approval_collection(ctx, permission_context)
    facts.blocked = {identifiers[0]}
    http = ctx["control_http"]
    query = {"case_id": str(ctx["case_id"]), "limit": 1}
    first = http.get("/api/v1/approvals", params=query, headers=AUTH)
    assert first.status_code == 200, first.json()
    assert [row["approval"]["approval_id"] for row in first.json()["items"]] == [str(identifiers[1])]
    assert first.json()["next_cursor"] is not None
    second = http.get("/api/v1/approvals", params=dict(query, cursor=first.json()["next_cursor"]), headers=AUTH)
    assert second.status_code == 200, second.json()
    assert [row["approval"]["approval_id"] for row in second.json()["items"]] == [str(identifiers[2])]
    assert second.json()["next_cursor"] is None
    module = collections_module()
    evidence = authority.authorize_http(configured["principal"], "listApprovals", {}, query, {})
    app = ctx["control_app"]
    with (
        request_authorization(evidence, app.state.authorization_fence, mutation=False),
        app.state.business_database.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        allowed = module.CollectionScope(authority).allowed_ids(
            connection,
            current_data_scope(),
            tuple(ResourceBinding("approval", identifier, 1) for identifier in identifiers),
        )
        assert allowed == identifiers[1:]
        assert (
            connection.execute(
                text("SELECT count(*) FROM mt.approval_request WHERE approval_id=ANY(CAST(:ids AS uuid[]))"),
                {"ids": list(allowed)},
            ).scalar_one()
            == 2
        )
    assert all(operation == "listApprovals" for operation, _, _ in facts.calls)


@pytest.mark.parametrize("reason", ["denied", "missing", "unknown"])
def test_explicitly_denied_items_are_excluded_unknown_facts_fail_request(control_context, permission_context, reason):
    ctx = control_context
    identifiers, _, _, facts = approval_collection(ctx, permission_context)
    setattr(facts, {"denied": "blocked", "missing": "missing", "unknown": "unknown"}[reason], {identifiers[0]})
    response = ctx["control_http"].get(
        "/api/v1/approvals", params={"case_id": str(ctx["case_id"]), "limit": 1}, headers=AUTH
    )
    if reason == "unknown":
        assert response.status_code == 503, response.json()
        assert not {"items", "next_cursor", "total"} & set(response.json())
    else:
        assert response.status_code == 200, response.json()
        assert [row["approval"]["approval_id"] for row in response.json()["items"]] == [str(identifiers[1])]


def test_empty_allowed_collection_is_valid(control_context, permission_context):
    ctx = control_context
    identifiers, _, _, facts = approval_collection(ctx, permission_context)
    facts.blocked = set(identifiers)
    response = ctx["control_http"].get(
        "/api/v1/approvals", params={"case_id": str(ctx["case_id"]), "limit": 1}, headers=AUTH
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"items": [], "next_cursor": None}


def test_cursor_after_source_revocation_does_not_leak_count(control_context, permission_context):
    ctx = control_context
    related = another_history(ctx, new_source=True)
    identifiers = [UUID(int=1), UUID(int=2)]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        add_review(admin, related, identifiers[0])
        add_review(admin, ctx, identifiers[1])
    candidate(ctx, permission_context, ["review.read"])
    query = {"case_id": str(ctx["case_id"]), "limit": 1}
    first = ctx["control_http"].get("/api/v1/reviews", params=query, headers=AUTH)
    assert first.status_code == 200 and first.json()["next_cursor"] is not None
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked',row_version=row_version+1 WHERE source_id=%s",
            (related["source_id"],),
        )
    stale = ctx["control_http"].get(
        "/api/v1/reviews", params=dict(query, cursor=first.json()["next_cursor"]), headers=AUTH
    )
    assert stale.status_code in {409, 422, 503}
    assert not {"items", "next_cursor", "total"} & set(stale.json())
    fresh = ctx["control_http"].get("/api/v1/reviews", params=query, headers=AUTH)
    assert fresh.status_code == 200 and [row["review_id"] for row in fresh.json()["items"]] == [str(identifiers[1])]


def test_org_policy_cursor_placeholder_never_sets_case_context(control_context):
    ctx = control_context
    observed = []
    engine = ctx["control_app"].state.business_database.engine

    def inspect(connection, cursor, statement, parameters, context, executemany):
        if "FROM mt.policy_registry" in statement:
            observed.append(
                tuple(
                    connection.exec_driver_sql(
                        "SELECT current_setting('app.scope_mode',true),NULLIF(current_setting('app.case_id',true),'')"
                    ).one()
                )
            )

    event.listen(engine, "before_cursor_execute", inspect)
    try:
        response = ctx["control_http"].get("/api/v1/policies", params={"limit": 1}, headers=AUTH)
    finally:
        event.remove(engine, "before_cursor_execute", inspect)
    assert response.status_code == 200, response.json()
    assert observed and set(observed) == {("ORGANIZATION", None)}


def test_admin_without_explicit_case_membership_is_denied(business_context):
    ctx = business_context
    _, second = two_cases(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        role = uuid4()
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'system_admin','synthetic-only',true)",
            (role,),
        )
        admin.execute(
            "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
            (uuid4(), ctx["actor"].user_id, role),
        )
        admin.execute(
            "UPDATE mt.case_membership SET revoked_at=now() WHERE case_id=%s AND user_id=%s",
            (second["case"], ctx["actor"].user_id),
        )
    target = RuleTarget(ctx["actor"].org_id, "case", second["case"], None, second["case"], None, None)
    with synthetic_target(ctx, "listSources", target):
        with pytest.raises(BusinessError) as denied, ctx["database"].transaction(Scope(ctx["actor"], second["case"])):
            pytest.fail("ADMIN_ROLE_MUST_NOT_REPLACE_EXPLICIT_CASE_MEMBERSHIP")
        assert denied.value.http_status == 404


@pytest.mark.parametrize("defect", ["task", "run", "event"])
def test_task_version_binding_rejects_same_case_node_and_event_swaps(control_context, defect):
    from business_app.controls.common import page

    ctx = control_context
    other = another_history(ctx) if defect in {"task", "event"} else ctx
    run = 2 if defect == "run" else 1
    if defect == "run":
        append_synthetic_snapshot(ctx, snapshot(ctx, 2))
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if defect == "event":
            admin.execute(
                "INSERT INTO mt.task_event(event_id,org_id,case_id,task_id,run_version,from_state,to_state,reason,request_id) VALUES(%s,%s,%s,%s,1,'CREATED','QUEUED','synthetic-scope-only',%s)",
                (uuid4(), ctx["actor"].org_id, ctx["case_id"], other["task_id"], uuid4()),
            )
        else:
            admin.execute(
                "INSERT INTO mt.task_node_run(run_id,org_id,case_id,task_id,run_version,node_code,attempt,input_hash,state,required,fencing_epoch) VALUES(%s,%s,%s,%s,%s,'synthetic-no-model',1,%s,'READY',true,1)",
                (uuid4(), ctx["actor"].org_id, ctx["case_id"], other["task_id"], run, "a" * 64),
            )
    operation = "listTaskEvents" if defect == "event" else "listTaskNodes"
    target = RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], None, None)
    app, scope = ctx["control_app"], Scope(ctx["actor"], ctx["case_id"])
    with synthetic_target(ctx, operation, target), app.state.business_database.transaction(scope) as connection:
        module = collections_module()
        fixed = module.bind_task_scope(connection, current_data_scope(), TaskBinding(ctx["task_id"], 1))
        with bind_data_scope(fixed):
            with pytest.raises(BusinessError) as denied:
                if defect == "event":
                    page(
                        connection,
                        "task_event",
                        "event_id",
                        scope,
                        ctx["settings"].cursor_secret,
                        None,
                        20,
                        where="org_id=:org AND case_id=:case AND task_id=:task AND run_version=:run",
                        filters=dict(task=other["task_id"], run=1),
                    )
                else:
                    app.state.execution.nodes(scope, other["task_id"], run)
            assert denied.value.http_status in {403, 404, 409, 503}


def test_upload_scope_cannot_be_reused_for_another_session(business_context):
    from tests.business.test_upload_validation import prepared_upload

    ctx = business_context
    app, first_http, first, _ = prepared_upload(ctx)
    _, second_http, second, _ = prepared_upload(ctx)
    scope = Scope(ctx["actor"], ctx["case_id"])
    target = RuleTarget(ctx["actor"].org_id, "upload", UUID(first), None, ctx["case_id"], "upload", None)
    try:
        with synthetic_target(ctx, "getUploadStatus", target):
            assert app.state.upload_service.repository.status(scope, UUID(first))["session"]["upload_id"] == first
            with pytest.raises(BusinessError) as denied:
                app.state.upload_service.repository.status(scope, UUID(second))
            assert denied.value.http_status in {403, 404, 409, 503}
    finally:
        first_http.__exit__(None, None, None)
        second_http.__exit__(None, None, None)


def test_one_item_evidence_cannot_be_reused_as_a_collection_header(control_context, permission_context):
    ctx = control_context
    identifiers, configured, authority, _ = approval_collection(ctx, permission_context)
    app = ctx["control_app"]
    evidence = authority.authorize_http(
        configured["principal"], "listApprovals", {}, {"case_id": str(ctx["case_id"])}, {}
    )
    scope = Scope(ctx["actor"], ctx["case_id"])
    with (
        request_authorization(evidence, app.state.authorization_fence, mutation=False),
        app.state.business_database.transaction(scope) as connection,
    ):
        target = RuleTarget(ctx["actor"].org_id, "approval", identifiers[0], 1, ctx["case_id"], "review", None)
        item_evidence = authority.authorize_collection_item(
            configured["principal"], "listApprovals", target, connection=connection
        )
    with (
        request_authorization(item_evidence, app.state.authorization_fence, mutation=False),
        app.state.business_database.transaction(scope) as connection,
    ):
        with pytest.raises(BusinessError) as denied:
            collections_module().CollectionScope(authority).allowed_ids(
                connection, current_data_scope(), (ResourceBinding("approval", identifiers[1], 1),)
            )
        assert denied.value.http_status == 503


def test_source_collection_keeps_array_purposes_as_source_facts(control_context, permission_context):
    ctx = control_context
    candidate(ctx, permission_context, ["source.read"])
    response = ctx["control_http"].get("/api/v1/sources", params={"case_id": str(ctx["case_id"])}, headers=AUTH)
    assert response.status_code == 200, response.json()
    assert [row["source_id"] for row in response.json()["items"]] == [str(ctx["source_id"])]
    assert "upload" in response.json()["items"][0]["purpose"]


def test_policy_collection_checks_the_actual_kind_under_organization_scope(control_context, permission_context):
    ctx = control_context
    wanted, forbidden = uuid4(), uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        for identifier, kind in ((wanted, "threshold"), (forbidden, "retention")):
            admin.execute(
                "INSERT INTO mt.policy_registry(policy_id,org_id,kind,version,definition_ref,status) VALUES(%s,%s,%s,%s,'urn:synthetic:policy','DRAFT')",
                (identifier, ctx["actor"].org_id, kind, str(identifier)),
            )
    configured, objects, authority, _ = candidate(ctx, permission_context, ["policy.read"], role_code="algorithm_admin")
    objects.supplemental = None
    response = ctx["control_http"].get("/api/v1/policies", headers=AUTH)
    assert response.status_code == 200, response.json()
    assert [row["policy_id"] for row in response.json()["items"]] == [str(wanted)]
    evidence = authority.authorize_http(configured["principal"], "listPolicies", {}, {}, {})
    app = ctx["control_app"]
    with (
        request_authorization(evidence, app.state.authorization_fence, mutation=False),
        app.state.business_database.identity_transaction(ctx["actor"]) as connection,
    ):
        actual = (
            collections_module()
            .CollectionScope(authority)
            .allowed_ids(
                connection,
                current_data_scope(),
                (ResourceBinding("policy", wanted, 1), ResourceBinding("policy", forbidden, 1)),
            )
        )
    assert actual == (wanted,)


def test_audit_collection_applies_exact_event_metadata_scope(control_context, permission_context):
    ctx = control_context
    allowed, denied = uuid4(), uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        for identifier in (allowed, denied):
            admin.execute(
                "INSERT INTO mt.audit_event(event_id,org_id,case_id,actor_id,action,object_type,object_id,object_version,outcome,request_id,occurred_at,created_by) VALUES(%s,%s,%s,%s,'synthetic.scope','task',%s,1,'allowed',%s,now(),%s)",
                (
                    identifier,
                    ctx["actor"].org_id,
                    ctx["case_id"],
                    ctx["actor"].user_id,
                    ctx["task_id"],
                    uuid4(),
                    ctx["actor"].user_id,
                ),
            )
    configured, objects, _, _ = candidate(ctx, permission_context, ["audit.read"], role_code="auditor")

    class AuditFacts:
        def read(self, principal, operation_id, target, *, connection):
            assert principal == configured["principal"] and operation_id == "listAuditEvents"
            checks = {"audit_delegation": True, "audit_metadata_scope": target.object_id != denied}
            return ConditionFacts(principal, target, checks, digest([target, checks]), time.time() + 60)

    objects.supplemental = AuditFacts()
    response = ctx["control_http"].get(
        "/api/v1/audit/events", params={"case_id": str(ctx["case_id"]), "limit": 100}, headers=AUTH
    )
    assert response.status_code == 200, response.json()
    identifiers = {row["event_id"] for row in response.json()["items"]}
    assert str(allowed) in identifiers and str(denied) not in identifiers
    assert all("details" not in row for row in response.json()["items"])
