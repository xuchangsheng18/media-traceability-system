"""Real SQL confirmation facts; synthetic approvals here do not prove approval duty."""

from dataclasses import replace
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.errors import BusinessError
from business_app.permissions.context import request_authorization
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import ConditionFacts
from business_app.types import Scope
from sqlalchemy import text

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context


@pytest.fixture
def confirmation_context(control_context, permission_context):
    ctx = control_context
    current, objects, authority, facts = candidate(ctx, permission_context, ["operation.confirm"])
    identifier = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        task = admin.execute(
            "SELECT row_version,run_version,result_version,policy_version FROM mt.analysis_task WHERE task_id=%s",
            (ctx["task_id"],),
        ).fetchone()
        assert task is not None
        admin.execute(
            """INSERT INTO mt.approval_request(approval_id,org_id,case_id,object_type,object_id,
            object_version,purpose,policy_version,requested_by,state,expires_at,reason,run_version,result_version,created_by)
            VALUES(%s,%s,%s,'task',%s,%s,'seal',%s,%s,'APPROVED',now()+interval '10 minutes',
            'self-owned SQL facts only; not independent duty validation',%s,%s,%s)""",
            (
                identifier,
                ctx["actor"].org_id,
                ctx["case_id"],
                ctx["task_id"],
                task[0],
                task[3],
                ctx["actor"].user_id,
                task[1],
                task[2],
                ctx["actor"].user_id,
            ),
        )
    body = dict(approval_id=str(identifier), object_id=str(ctx["task_id"]), object_version=task[0], purpose="seal")
    target = objects.resolve_http(current["principal"], "issueOperationToken", {}, {}, body)
    return dict(
        ctx,
        current=current,
        objects=objects,
        conditional=authority,
        facts=facts,
        operation_approval=identifier,
        operation_body=body,
        operation_target=target,
    )


def test_real_sql_case_confirmation_rechecks_linked_task_and_source_in_same_root(confirmation_context):
    ctx = confirmation_context
    principal, authority = ctx["current"]["principal"], ctx["conditional"]
    evidence = authority.authorize(principal, "issueOperationToken", ctx["operation_target"])
    with (
        request_authorization(evidence, ctx["control_app"].state.authorization_fence, mutation=True),
        ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        facts = ctx["objects"].read(principal, "issueOperationToken", ctx["operation_target"], connection=connection)
        assert all(
            facts.checks[name] is True
            for name in (
                "same_org",
                "case",
                "confirmation_subject",
                "object_binding",
                "source",
                "analysis_purpose",
            )
        )
    assert evidence.target.case_id == ctx["case_id"] and evidence.target.object_id == ctx["operation_approval"]


@pytest.mark.parametrize(
    "change", ["row_version", "run_version", "result_version", "policy_version", "owner", "state", "expires_at"]
)
def test_real_sql_stale_task_or_invalid_approval_cannot_confirm(confirmation_context, change):
    ctx = confirmation_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if change in {"row_version", "run_version", "result_version", "policy_version"}:
            column = {
                "row_version": "row_version",
                "run_version": "run_version",
                "result_version": "result_version",
                "policy_version": "policy_version",
            }[change]
            value = "other-self-owned-policy" if change == "policy_version" else 999
            admin.execute(f"UPDATE mt.analysis_task SET {column}=%s WHERE task_id=%s", (value, ctx["task_id"]))
        elif change == "owner":
            admin.execute(
                "UPDATE mt.approval_request SET requested_by=%s WHERE approval_id=%s",
                (ctx["reviewers"][0].user_id, ctx["operation_approval"]),
            )
        elif change == "state":
            admin.execute(
                "UPDATE mt.approval_request SET state='REVOKED' WHERE approval_id=%s", (ctx["operation_approval"],)
            )
        else:
            admin.execute(
                "UPDATE mt.approval_request SET expires_at=now()-interval '1 second' WHERE approval_id=%s",
                (ctx["operation_approval"],),
            )
    target = ctx["objects"].resolve_http(
        ctx["current"]["principal"], "issueOperationToken", {}, {}, ctx["operation_body"]
    )
    with pytest.raises(BusinessError) as failure:
        ctx["conditional"].authorize(ctx["current"]["principal"], "issueOperationToken", target)
    assert (failure.value.code, failure.value.http_status) == (
        ("CONDITIONAL_FACTS_UNAVAILABLE", 503) if change == "expires_at" else ("PERMISSION_REQUIRED", 403)
    )


@pytest.mark.parametrize("change", ["revoked", "purpose", "expired"])
def test_real_sql_linked_source_authorization_is_required(confirmation_context, change):
    ctx = confirmation_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if change == "revoked":
            admin.execute(
                "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s", (ctx["source_id"],)
            )
        elif change == "purpose":
            admin.execute(
                "UPDATE mt.source_registry SET purpose=ARRAY['upload'] WHERE source_id=%s", (ctx["source_id"],)
            )
        else:
            admin.execute(
                "UPDATE mt.source_registry SET expires_at=now()-interval '1 second' WHERE source_id=%s",
                (ctx["source_id"],),
            )
    with pytest.raises(BusinessError) as failure:
        ctx["conditional"].authorize(ctx["current"]["principal"], "issueOperationToken", ctx["operation_target"])
    assert (failure.value.code, failure.value.http_status) == (
        ("CONDITIONAL_FACTS_UNAVAILABLE", 503) if change == "expired" else ("PERMISSION_REQUIRED", 403)
    )


def test_real_sql_confirmation_does_not_infer_classification_or_accept_override(confirmation_context):
    ctx = confirmation_context
    ctx["objects"].supplemental = None
    with pytest.raises(BusinessError) as missing:
        ctx["conditional"].authorize(ctx["current"]["principal"], "issueOperationToken", ctx["operation_target"])
    assert missing.value.code == "CONDITIONAL_FACTS_UNAVAILABLE"

    class Override:
        def read(self, principal, operation_id, target, *, connection):
            return ConditionFacts(
                principal,
                target,
                {"object_binding": True, "classification": True},
                digest([operation_id, target]),
                principal.expires_at,
            )

    ctx["objects"].supplemental = Override()
    with pytest.raises(BusinessError) as override:
        ctx["conditional"].authorize(ctx["current"]["principal"], "issueOperationToken", ctx["operation_target"])
    assert override.value.code == "CONDITIONAL_FACTS_UNAVAILABLE"


def test_real_sql_two_case_member_cannot_replace_approval_case(confirmation_context):
    ctx = confirmation_context
    case_b = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
            (case_b, ctx["actor"].org_id, str(case_b)),
        )
        admin.execute(
            "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
            (uuid4(), case_b, ctx["actor"].org_id, ctx["actor"].user_id),
        )
    wrong = replace(ctx["operation_target"], case_id=case_b)
    assert wrong.case_id != ctx["operation_target"].case_id
    with pytest.raises(BusinessError) as failure:
        ctx["conditional"].authorize(ctx["current"]["principal"], "issueOperationToken", wrong)
    assert failure.value.http_status == 404


@pytest.mark.parametrize("change", ["task_policy", "source_purpose"])
def test_real_sql_commit_fence_rechecks_confirmation_binding_and_rolls_back(confirmation_context, change):
    ctx = confirmation_context
    principal, authority = ctx["current"]["principal"], ctx["conditional"]
    evidence = authority.authorize(principal, "issueOperationToken", ctx["operation_target"])
    with pytest.raises(BusinessError) as failure:
        with (
            request_authorization(evidence, ctx["control_app"].state.authorization_fence, mutation=True),
            ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
        ):
            if change == "task_policy":
                connection.execute(
                    text(
                        "UPDATE mt.analysis_task SET policy_version='self-owned-invalidated-policy' WHERE task_id=:id"
                    ),
                    dict(id=ctx["task_id"]),
                )
            else:
                connection.execute(
                    text("UPDATE mt.source_registry SET purpose=ARRAY['upload'] WHERE source_id=:id"),
                    dict(id=ctx["source_id"]),
                )
    assert failure.value.code == "PERMISSION_REQUIRED"
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT policy_version FROM mt.analysis_task WHERE task_id=%s", (ctx["task_id"],)
        ).fetchone() == ("policy-dev-1",)
        source = admin.execute(
            "SELECT purpose FROM mt.source_registry WHERE source_id=%s", (ctx["source_id"],)
        ).fetchone()
        assert source is not None and "analysis" in source[0]


@pytest.mark.parametrize("claim", ["object_id", "object_version", "purpose"])
def test_real_sql_http_object_claims_are_compared_with_approval(confirmation_context, claim):
    ctx = confirmation_context
    body = dict(ctx["operation_body"])
    body[claim] = str(UUID(int=999)) if claim == "object_id" else 999 if claim == "object_version" else "review"
    with pytest.raises(BusinessError) as failure:
        ctx["objects"].resolve_http(ctx["current"]["principal"], "issueOperationToken", {}, {}, body)
    assert failure.value.code == "AUTHORIZATION_OBJECT_STALE" and failure.value.http_status == 409
