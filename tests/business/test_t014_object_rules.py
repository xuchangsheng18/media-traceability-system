"""Actual RLS/object facts and isolated six-role rules; missing facts never imply ALLOW."""

import hashlib
import time
from uuid import uuid4

import psycopg
import pytest
from business_app.errors import BusinessError
from fastapi.testclient import TestClient

from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t014_permissions import permission_module
from tests.platform.test_t014_six_role import SOURCE, rule_input_digest


def configure(ctx, role):
    new_role, binding = uuid4(), uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.user_roles SET revoked_at=statement_timestamp() WHERE user_role_id=%s", (ctx["binding"],)
        )
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,%s,'synthetic-only',true)",
            (new_role, role),
        )
        admin.execute(
            "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
            (binding, ctx["actor"].user_id, new_role),
        )
        for code in ["policy.manage", "policy.read", "asset.upload", "approval.request", "source.read"]:
            permission = uuid4()
            admin.execute(
                "INSERT INTO mt.permissions(permission_id,code,description,enabled) VALUES(%s,%s,'synthetic-only',true)",
                (permission, code),
            )
            admin.execute(
                "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s)",
                (uuid4(), new_role, permission),
            )
    roles = permission_module("role_facts").RoleDirectory(ctx["lookup"], clock=time.time)
    types = permission_module("rule_types")
    rules = permission_module("six_role").SixRoleRules(
        types.RuleSnapshot(
            SOURCE["revision"], rule_input_digest(), "synthetic-isolated-generation", int(time.time()) + 1800
        ),
        clock=time.time,
    )
    objects = permission_module("object_facts").ObjectFactsReader(ctx["database"], clock=time.time)
    authority = permission_module("conditional").ConditionalPermissionAuthority(roles, rules, objects, clock=time.time)
    return types, roles, rules, objects, authority


def side_effect_counts(admin):
    counts = []
    for name in ["upload_session", "object_version", "outbox_event", "idempotency_record"]:
        value = admin.execute("SELECT count(*) FROM mt." + name).fetchone()
        assert value is not None
        counts.append(value[0])
    return counts


@pytest.mark.parametrize(
    "role,kind,allowed",
    [
        ("data_admin", "retention", True),
        ("data_admin", "threshold", False),
        ("data_admin", "analysis", False),
        ("data_admin", "risk_taxonomy", False),
        ("data_admin", "review", False),
        ("algorithm_admin", "retention", False),
        ("algorithm_admin", "threshold", True),
        ("algorithm_admin", "analysis", True),
        ("algorithm_admin", "risk_taxonomy", False),
        ("algorithm_admin", "review", False),
        ("business_reviewer", "retention", False),
        ("business_reviewer", "threshold", False),
        ("business_reviewer", "analysis", False),
        ("business_reviewer", "risk_taxonomy", True),
        ("business_reviewer", "review", True),
    ],
)
def test_policy_manage_is_bound_to_exact_kind(permission_context, role, kind, allowed):
    ctx = permission_context
    types, _, _, _, authority = configure(ctx, role)
    target = types.RuleTarget(ctx["actor"].org_id, "policy_collection", None, None, None, None, kind)
    if allowed:
        value = authority.authorize(ctx["principal"], "createPolicy", target)
        assert value.principal == ctx["principal"]
        assert value.operation_id == "createPolicy"
        assert value.target == target
    else:
        with pytest.raises(BusinessError) as caught:
            authority.authorize(ctx["principal"], "createPolicy", target)
        assert caught.value.http_status == 403


def test_object_case_cannot_be_replaced_by_request_case(permission_context):
    ctx = permission_context
    types, _, _, _, authority = configure(ctx, "case_investigator")
    target = types.RuleTarget(ctx["actor"].org_id, "source", ctx["source_id"], None, ctx["other_case_id"], None, None)
    with pytest.raises(BusinessError) as caught:
        authority.authorize(ctx["principal"], "getSource", target)
    assert caught.value.http_status == 404


def test_propagation_resolver_uses_canonical_cluster_path(permission_context):
    ctx = permission_context
    _, _, _, objects, _ = configure(ctx, "case_investigator")
    cluster = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.content_cluster(cluster_id,org_id,case_id,scope,policy_version,status,created_by) VALUES(%s,%s,%s,'synthetic-only','synthetic-policy','candidate',%s)",
            (cluster, ctx["actor"].org_id, ctx["case_id"], ctx["actor"].user_id),
        )
    target = objects.resolve_http(ctx["principal"], "getPropagation", {"cluster_id": str(cluster)}, {}, {})
    assert (target.kind, target.object_id, target.case_id, target.object_version) == (
        "cluster",
        cluster,
        ctx["case_id"],
        1,
    )


@pytest.mark.parametrize("operation", ["cancelTask", "getApproval"])
def test_exact_trusted_delegation_can_authorize_nonowner(control_context, permission_context, operation):
    from tests.business.t014_positive_fixtures import candidate
    from tests.business.test_controls import request_approval

    ctx = control_context
    approval = request_approval(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.analysis_task SET created_by=%s WHERE task_id=%s", (ctx["reviewers"][0].user_id, ctx["task_id"])
        )
        admin.execute(
            "UPDATE mt.approval_request SET requested_by=%s WHERE approval_id=%s",
            (ctx["reviewers"][0].user_id, approval),
        )
    current, objects, authority, facts = candidate(ctx, permission_context, ["task.cancel", "approval.read"])
    identifier = ctx["task_id"] if operation == "cancelTask" else approval
    target = objects.resolve_http(
        current["principal"],
        operation,
        {"id": str(identifier)},
        {},
        {"reason": "synthetic delegation", "expected_run_version": 1, "expected_version": 1, "approval_id": None}
        if operation == "cancelTask"
        else {},
    )
    facts.delegation = True
    evidence = authority.authorize(current["principal"], operation, target)
    assert evidence.operation_id == operation and evidence.target == target
    facts.delegation = False
    with pytest.raises(BusinessError) as denied:
        authority.authorize(current["principal"], operation, target)
    assert (denied.value.http_status, denied.value.code) == (403, "PERMISSION_REQUIRED")
    facts.delegation = None
    with pytest.raises(BusinessError) as missing:
        authority.authorize(current["principal"], operation, target)
    assert (missing.value.http_status, missing.value.code) == (503, "CONDITIONAL_FACTS_UNAVAILABLE")


def test_missing_classification_or_authoritative_purpose_is_unavailable(permission_context):
    from business_app.main import create_app

    ctx = permission_context
    _, roles, rules, _, authority = configure(ctx, "case_investigator")
    delegate = ctx["authority"]

    class Identity:
        def authenticate_principal(self, bearer):
            assert delegate.authenticate(bearer) == ctx["principal"].actor
            return ctx["principal"]

        def authenticate(self, bearer):
            return delegate.authenticate(bearer)

        def authorize_case(self, *args):
            return delegate.authorize_case(*args)

        def authorize_source(self, *args):
            return delegate.authorize_source(*args)

    app = create_app(
        ctx["settings"],
        Identity(),
        permission_authority=permission_module("six_role").SixRoleEntryAuthority(roles, rules),
        conditional_permissions=authority,
    )
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        before = side_effect_counts(admin)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/uploads",
            headers={"Authorization": "Bearer test-only-valid-token", "Idempotency-Key": "synthetic-no-classification"},
            json={
                "case_id": str(ctx["case_id"]),
                "source_id": str(ctx["source_id"]),
                "filename": "synthetic.bin",
                "size_bytes": 6,
                "mime": "image/png",
                "sha256": hashlib.sha256(b"ABCDEF").hexdigest(),
            },
        )
    assert response.status_code == 503
    assert response.json()["code"] == "CONDITIONAL_FACTS_UNAVAILABLE"
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        after = side_effect_counts(admin)
    assert after == before
    assert not list(ctx["settings"].object_root.rglob("*.part"))


def test_model_release_remains_org_scoped_and_unavailable_without_adapter(permission_context):
    ctx = permission_context
    types, _, _, _, authority = configure(ctx, "algorithm_admin")
    target = types.RuleTarget(ctx["actor"].org_id, "model_release", uuid4(), 1, None, "model_release", None)
    with pytest.raises(BusinessError) as caught:
        authority.authorize(ctx["principal"], "requestApproval", target)
    assert caught.value.http_status == 503
    assert caught.value.code == "ORGANIZATION_APPROVAL_ADAPTER_UNAVAILABLE"


def test_no_new_unmounted_operation_is_claimed(permission_context):
    ctx = permission_context
    _, _, _, objects, _ = configure(ctx, "case_investigator")
    expected = {
        o["operation_id"]
        for p in SOURCE["permissions"]
        for o in p["operations"]
        if o["runtime_state"] == "MOUNTED_DEVELOPMENT_PERMISSION_GATE_VERIFIED"
    }
    unmounted = {o["operation_id"] for p in SOURCE["permissions"] for o in p["operations"]} - expected
    assert len(expected) == 42 and len(unmounted) == 31
    assert objects.supported_operation_ids == frozenset(expected)
    assert not objects.supported_operation_ids & unmounted


def test_conditional_dependency_is_required_when_function_gate_allows(business_context):
    from business_app.main import create_app

    ctx = business_context
    app = create_app(ctx["settings"], ctx["authority"], permission_authority=ctx["permission_authority"])
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test-only-valid-token"})
    assert response.status_code == 503
    assert response.json()["code"] == "CONDITIONAL_POLICY_UNCONFIGURED"


def test_wrong_target_kind_cannot_use_policy_kind_as_an_allow(permission_context):
    ctx = permission_context
    types, _, _, _, authority = configure(ctx, "data_admin")
    target = types.RuleTarget(ctx["actor"].org_id, "user", ctx["actor"].user_id, None, None, None, "retention")
    with pytest.raises(BusinessError) as caught:
        authority.authorize(ctx["principal"], "createPolicy", target)
    assert caught.value.http_status == 503


def test_same_transaction_actor_must_match_bound_principal(permission_context):
    ctx = permission_context
    types, _, _, objects, _ = configure(ctx, "data_admin")
    target = types.RuleTarget(ctx["actor"].org_id, "policy_collection", None, None, None, None, "retention")
    with ctx["database"].identity_transaction(ctx["other_actor"]) as connection:
        with pytest.raises(BusinessError) as caught:
            objects.read(ctx["principal"], "createPolicy", target, connection=connection)
    assert (caught.value.code, caught.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)


@pytest.mark.parametrize("defect", ["digest", "nan", "infinite", "bool_expiry", "sql_override"])
def test_supplemental_facts_validate_provenance_and_never_override_SQL(permission_context, defect):
    from dataclasses import replace

    ctx = permission_context
    types, roles, rules, _, _ = configure(ctx, "data_admin")
    target = types.RuleTarget(ctx["actor"].org_id, "policy_collection", None, None, None, None, "retention")

    class BadFacts:
        def read(self, principal, operation_id, target, *, connection):
            fact = types.ConditionFacts(principal, target, {}, "a" * 64, time.time() + 60)
            return {
                "digest": replace(fact, version_digest="unverified"),
                "nan": replace(fact, valid_until=float("nan")),
                "infinite": replace(fact, valid_until=float("inf")),
                "bool_expiry": replace(fact, valid_until=True),
                "sql_override": replace(fact, checks={"same_org": True}),
            }[defect]

    objects = permission_module("object_facts").ObjectFactsReader(ctx["database"], supplemental=BadFacts())
    authority = permission_module("conditional").ConditionalPermissionAuthority(roles, rules, objects)
    with pytest.raises(BusinessError) as caught:
        authority.authorize(ctx["principal"], "createPolicy", target)
    assert (caught.value.code, caught.value.http_status) == ("CONDITIONAL_FACTS_UNAVAILABLE", 503)


def test_policy_list_SQL_scope_and_cursor_follow_current_role_kind(permission_context):
    from business_app.main import create_app

    ctx = permission_context
    _, roles, rules, _, authority = configure(ctx, "data_admin")
    delegate = ctx["authority"]

    class Identity:
        def authenticate_principal(self, token):
            assert delegate.authenticate(token) == ctx["actor"]
            return ctx["principal"]

        authenticate = delegate.authenticate
        authorize_case = delegate.authorize_case
        authorize_source = delegate.authorize_source

    class Directory:
        def current(self, actor):
            return dict(
                user_id=str(actor.user_id),
                org_id=str(actor.org_id),
                roles=["synthetic"],
                permissions=["policy.read"],
                case_ids=[],
            )

    ids = {}
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        for kind, version in [("retention", "a"), ("retention", "b"), ("analysis", "c"), ("review", "d")]:
            identifier = uuid4()
            ids[kind] = identifier
            admin.execute(
                "INSERT INTO mt.policy_registry(policy_id,org_id,kind,version,definition_ref,status,approval_id) VALUES(%s,%s,%s,%s,'urn:synthetic-only','DRAFT',NULL)",
                (identifier, ctx["actor"].org_id, kind, version),
            )
    app = create_app(
        ctx["settings"],
        Identity(),
        identity_directory=Directory(),
        permission_authority=permission_module("six_role").SixRoleEntryAuthority(roles, rules),
        conditional_permissions=authority,
    )
    headers = {"Authorization": "Bearer test-only-valid-token"}
    with TestClient(app) as client:
        first = client.get("/api/v1/policies", params={"limit": 1}, headers=headers)
        assert first.status_code == 200, first.json()
        assert [v["kind"] for v in first.json()["items"]] == ["retention"]
        cursor = first.json()["next_cursor"]
        assert cursor is not None
        second = client.get("/api/v1/policies", params={"limit": 1, "cursor": cursor}, headers=headers)
        assert second.status_code == 200
        assert [v["kind"] for v in second.json()["items"]] == ["retention"]
        assert second.json()["next_cursor"] is None
        blocked = client.get("/api/v1/policies/" + str(ids["analysis"]), headers=headers)
        assert blocked.status_code == 403
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            # Role codes are immutable. Revoke/rebind instead of renaming a role.
            admin.execute(
                "UPDATE mt.user_roles SET revoked_at=now() WHERE user_id=%s AND role_id IN (SELECT role_id FROM mt.roles WHERE code='data_admin')",
                (ctx["actor"].user_id,),
            )
            role = uuid4()
            admin.execute(
                "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'algorithm_admin','synthetic-only',true)",
                (role,),
            )
            admin.execute(
                "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
                (uuid4(), ctx["actor"].user_id, role),
            )
            for (permission,) in admin.execute(
                "SELECT permission_id FROM mt.permissions WHERE code IN ('policy.read','policy.manage')"
            ).fetchall():
                admin.execute(
                    "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s)",
                    (uuid4(), role, permission),
                )
        changed = client.get("/api/v1/policies", params={"limit": 1, "cursor": cursor}, headers=headers)
        assert changed.status_code == 422
        assert changed.json()["code"] == "PAGE_CURSOR_INVALID"
        fresh = client.get("/api/v1/policies", params={"limit": 1}, headers=headers)
        assert fresh.status_code == 200
        assert [v["kind"] for v in fresh.json()["items"]] == ["analysis"]
