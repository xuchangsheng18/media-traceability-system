"""Mounted real atomic service with self-owned trust, never a deployable issuer."""

import time
from contextlib import contextmanager
from uuid import UUID, uuid4

import pytest
from business_app.controls.common import etag
from business_app.errors import BusinessError
from business_app.main import create_app
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import AuthorizationEvidence, RuleTarget
from business_app.types import Scope
from fastapi.testclient import TestClient

from tests.business.http_fixtures import FixtureConditionals, FixturePermissions
from tests.business.test_task_creation_transaction import counts, creation_environment, sql_context

creation_environment = creation_environment
sql_context = sql_context
PATH = "/api/v1/analysis/tasks"
AUTH = {"Authorization": "Bearer explicit-http-fixture"}


def test_task_creation_is_mounted_and_refuses_unauthenticated_requests(business_context):
    with TestClient(create_app(business_context["settings"])) as http:
        response = http.post(PATH, json={})
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
        assert response.headers["Cache-Control"] == "no-store"
        assert http.get("/openapi.json").json()["paths"][PATH]["post"]["operationId"] == "createTask"


@contextmanager
def client(e, *, configured=True, permissions=True):
    class Identity:
        def authenticate_principal(self, token):
            if token != "explicit-http-fixture":
                raise BusinessError("AUTHENTICATION_REQUIRED", 401)
            return e["principal"]

        def authenticate(self, token):
            return self.authenticate_principal(token).actor

        def authorize_source(self, scope, source_id, purpose) -> None:
            raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)

        def authorize_case(self, actor, case_id, action):
            if actor != e["actor"] or case_id != e["case"] or action != "task.create":
                raise BusinessError("CASE_NOT_FOUND", 404)
            return Scope(actor, case_id)

    class Conditions(FixtureConditionals):
        def authorize_http(self, principal, operation_id, path, query, body):
            assert operation_id == "createTask"
            return AuthorizationEvidence(
                principal,
                operation_id,
                RuleTarget(
                    principal.actor.org_id,
                    "asset",
                    UUID(body["asset_id"]),
                    1,
                    UUID(body["case_id"]),
                    "analysis",
                    None,
                    (e["source"],),
                    digest(dict(path=path, query=query, body=body)),
                ),
                "e" * 64,
                "f" * 64,
                "explicit-synthetic-fixture",
                e["revision"]["recovery_generation"],
                time.time() + 600,
            )

    options = dict(task_creation_materials=e["reader"], task_creation_budgets=e["budgets"]) if configured else {}
    app = create_app(
        e["settings"],
        Identity(),
        permission_authority=FixturePermissions(
            frozenset({e["actor"]}), frozenset({"task.create"}) if permissions else frozenset()
        ),
        conditional_permissions=Conditions(frozenset({e["actor"]}), e["database"]),
        authorization_fence=e["fence"],
        **options,
    )
    original_database = e["database"]
    e["database"] = app.state.business_database
    try:
        with TestClient(app) as http:
            yield http
    finally:
        e["database"] = original_database


def test_http_acceptance_replays_exact_response_and_writes_one_run(creation_environment):
    e = creation_environment
    with client(e) as http:
        headers = {**AUTH, "Idempotency-Key": uuid4().hex, "X-Request-Id": str(uuid4())}
        response = http.post(PATH, json=e["body"], headers=headers)
        assert response.status_code == 202, response.text
        accepted = response.json()
        assert set(accepted) == {"task_id", "state", "status_url"}
        assert accepted["state"] == "QUEUED"
        assert accepted["status_url"] == f"/api/v1/analysis/tasks/{accepted['task_id']}/execution"
        assert response.headers["ETag"] == etag(accepted)
        assert response.headers["Cache-Control"] == "no-store"
        saved = counts(e)
        assert saved["analysis_task"] == e["initial_counts"]["analysis_task"] + 1
        assert saved["task_result"] == e["initial_counts"]["task_result"]
        replay = http.post(PATH, json=e["body"], headers=headers)
        assert replay.status_code == 202 and replay.json() == accepted
        assert replay.headers["ETag"] == response.headers["ETag"]
        assert counts(e) == saved


@pytest.mark.parametrize("fault", ["provider", "permission", "query", "duplicate_key", "duplicate_json"])
def test_http_refusals_create_no_partial_task(creation_environment, fault):
    e = creation_environment
    with client(e, configured=fault != "provider", permissions=fault != "permission") as http:
        headers = [*AUTH.items(), ("Idempotency-Key", "self-owned-key"), ("Content-Type", "application/json")]
        path = PATH + ("?case_id=" + str(e["case"]) if fault == "query" else "")
        if fault == "duplicate_key":
            headers.append(("Idempotency-Key", "another-key"))
        if fault == "duplicate_json":
            import json

            body = json.dumps(e["body"])[:-1] + ',"priority":"normal"}'
            response = http.post(path, content=body, headers=headers)
        else:
            response = http.post(path, json=e["body"], headers=headers)
        assert response.status_code == (503 if fault == "provider" else 403 if fault == "permission" else 422), (
            response.text
        )
        assert response.headers["Cache-Control"] == "no-store"
        assert counts(e) == e["initial_counts"]
