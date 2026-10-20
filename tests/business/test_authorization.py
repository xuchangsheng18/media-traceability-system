from uuid import UUID

import psycopg
import pytest
from fastapi import Depends, Request
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.business.http_fixtures import isolated_http_harness


def client(context, configured=True):
    from business_app.auth import authorize_request
    from business_app.main import create_app
    from business_app.permissions.guard import require_permission

    app = isolated_http_harness(
        create_app(
            context["settings"],
            context["authority"] if configured else None,
            permission_authority=context["permission_authority"],
            conditional_permissions=context["conditional_permissions"],
            authorization_fence=context["authorization_fence"],
        )
    )

    @app.get("/_test/authorization/{case_id}", dependencies=[Depends(require_permission("asset.read"))])
    def inspect_authorization(case_id: UUID, request: Request):
        scope = authorize_request(request, case_id, "result:read")
        with app.state.business_database.transaction(scope) as connection:
            row = connection.execute(text("SELECT case_id FROM mt.cases WHERE case_id=:case"), {"case": case_id}).one()
        return {"case_id": str(row.case_id)}

    return TestClient(app)


def test_no_authority_returns_503(business_context):
    assert business_context is not None, "business app/authentication missing"
    with client(business_context, configured=False) as http:
        response = http.get(
            f"/_test/authorization/{business_context['case_id']}",
            headers={"Authorization": "Bearer test-only-valid-token"},
        )
        assert response.status_code == 503
        assert "test-only-valid-token" not in response.text


def test_invalid_token_returns_401(business_context):
    assert business_context is not None, "business app/authentication missing"
    with client(business_context) as http:
        response = http.get(
            f"/_test/authorization/{business_context['case_id']}", headers={"Authorization": "Bearer wrong"}
        )
        assert response.status_code == 401
        assert "wrong" not in response.text


def test_revoked_case_returns_404(business_context):
    assert business_context is not None, "business app/authentication missing"
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.case_membership SET revoked_at=now() WHERE case_id=%s", (business_context["case_id"],)
        )
    with client(business_context) as http:
        response = http.get(
            f"/_test/authorization/{business_context['case_id']}",
            headers={"Authorization": "Bearer test-only-valid-token"},
        )
        assert response.status_code == 404


def test_RLS_context_does_not_leak_across_pool_reuse(business_context):
    assert business_context is not None, "business app/authentication missing"
    from business_app.types import Scope

    database = business_context["database"]
    first = Scope(actor=business_context["actor"], case_id=business_context["case_id"])
    second = Scope(actor=business_context["other_actor"], case_id=business_context["other_case_id"])
    with database.transaction(first) as connection:
        assert connection.execute(text("SELECT case_id FROM mt.cases")).scalars().all() == [first.case_id]
    with database.transaction(second) as connection:
        assert connection.execute(text("SELECT case_id FROM mt.cases")).scalars().all() == [second.case_id]
    with database.engine.connect() as connection:
        assert connection.execute(text("SELECT mt.actor_id()")).scalar_one() is None


def test_superuser_database_connection_rejected(business_context):
    assert business_context is not None, "business app/authentication missing"
    from business_app.db import Database
    from business_app.types import Scope

    database = Database(business_context["admin_dsn"])
    try:
        with pytest.raises(RuntimeError, match="PRIVILEGED"):
            with database.transaction(Scope(actor=business_context["actor"], case_id=business_context["case_id"])):
                pytest.fail("privileged connection was accepted")
    finally:
        database.close()
