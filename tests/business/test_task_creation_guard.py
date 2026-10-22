"""Self-owned HTTP guard probes, never task acceptance or real-provider evidence.

The only handler returns a 200 component marker. No application, database,
adoption, identity account, task/run row or Accepted response is created here.
"""

import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier, Lock, get_ident
from uuid import UUID, uuid4

import pytest
from business_app.errors import BusinessError
from business_app.permissions.catalog import load_catalog
from business_app.permissions.context import RequestAuthorization, current_authorization
from business_app.permissions.guard import authorize_business_route
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import AuthorizationEvidence, RuleTarget
from business_app.permissions.task_creation_context import TaskCreationContext, current_task_creation_context
from business_app.permissions.types import Principal
from business_app.types import Actor
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

PATH = "/api/v1/analysis/tasks"
ROOT = Path(__file__).resolve().parents[2]


class CleanupObserver:
    """Observe the same ASGI task after the actual dependency has unwound."""

    def __init__(self, app, probe):
        self.app, self.probe = app, probe

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        try:
            await self.app(scope, receive, send)
        finally:
            self.probe.cleanup_observations.append((current_task_creation_context(), current_authorization()))


def request_body():
    return dict(
        case_id=str(uuid4()),
        asset_id=str(uuid4()),
        scene="accident_rumor",
        policy_version="self-owned/策略/1",
        modules=["INGEST", "RESOURCE"],
        priority="normal",
    )


class GuardProbe:
    """Explicit synthetic authorities only; no grant of actual business rights."""

    def __init__(self):
        self.principal = Principal(
            Actor(uuid4(), uuid4()), "https://self-owned.example.test", "self-owned-subject", int(time.time()) + 600
        )
        self.body = request_body()
        self.calls = []
        self.conditional_observations = []
        self.handler_observations: list[tuple[TaskCreationContext | None, RequestAuthorization | None, int]] = []
        self.cleanup_observations = []
        self.identities = {"self-owned-token": self.principal}
        self.authentication_error = None
        self.permission_error = None
        self.permission_result = None
        self.conditional_error = None
        self.conditional_hook = None
        self.evidence_transform = None
        self.handler_error = None
        self.handler_hook = None
        self.app = FastAPI()
        self.app.state.permission_catalog = load_catalog(ROOT)
        self.app.state.business_authority = self
        self.app.state.permission_authority = self
        self.app.state.conditional_permissions = self
        self.app.state.authorization_fence = None
        self.app.add_middleware(CleanupObserver, probe=self)

        @self.app.exception_handler(BusinessError)
        async def business_error(_request: Request, error: BusinessError):
            return JSONResponse({"code": error.code}, status_code=error.http_status)

        @self.app.post(PATH, operation_id="createTask", dependencies=[Depends(authorize_business_route)])
        def component_probe(_request: Request):
            context, authorization = current_task_creation_context(), current_authorization()
            self.handler_observations.append((context, authorization, get_ident()))
            if self.handler_hook is not None:
                self.handler_hook(context, authorization)
            if self.handler_error is not None:
                raise self.handler_error
            return {"component_probe": True}

    def authenticate_principal(self, token):
        self.calls.append(("authenticate", token))
        if self.authentication_error is not None:
            raise self.authentication_error
        if token not in self.identities:
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        return self.identities[token]

    def check(self, principal, permission):
        self.calls.append(("permission", principal, permission))
        if self.permission_error is not None:
            raise self.permission_error
        if principal not in self.identities.values() or permission != "task.create":
            raise BusinessError("PERMISSION_REQUIRED", 403)
        return self.permission_result

    def authorize_http(self, principal, operation_id, path, query, body):
        self.calls.append(
            ("conditional", principal, operation_id, copy.deepcopy(path), copy.deepcopy(query), copy.deepcopy(body))
        )
        self.conditional_observations.append((current_task_creation_context(), current_authorization(), get_ident()))
        if self.conditional_error is not None:
            raise self.conditional_error
        # The first RED fixture used the exact sent fixture here because the old
        # guard passed no body. After binding, test the actual guard-parsed body.
        target = RuleTarget(
            principal.actor.org_id,
            "asset",
            UUID(body["asset_id"]),
            1,
            UUID(body["case_id"]),
            "analysis",
            None,
            request_digest=digest(dict(path=path, query=query, body=body)),
        )
        evidence = AuthorizationEvidence(
            principal,
            operation_id,
            target,
            "a" * 64,
            "b" * 64,
            "self-owned/rule/1",
            "self-owned/recovery/1",
            time.time() + 60,
        )
        if self.conditional_hook is not None:
            self.conditional_hook(principal, operation_id, path, query, body)
        return self.evidence_transform(evidence) if self.evidence_transform is not None else evidence

    def headers(self):
        return {"Authorization": "Bearer self-owned-token", "Idempotency-Key": "self-owned-key"}


def test_create_task_first_conditional_thread_receives_parent_request_context():
    probe = GuardProbe()
    with TestClient(probe.app) as client:
        response = client.post(PATH, json=probe.body, headers=probe.headers())
    assert response.status_code == 200 and response.json() == {"component_probe": True}
    assert [call[0] for call in probe.calls] == ["authenticate", "permission", "conditional"]
    assert len(probe.conditional_observations) == 1
    context, authorization, _thread = probe.conditional_observations[0]
    assert context is not None, "Parent async task must bind createTask context before the first conditional worker"
    assert context.principal == probe.principal
    assert context.request.case_id == UUID(probe.body["case_id"])
    assert context.request.asset_id == UUID(probe.body["asset_id"])
    assert authorization is None, "Request context alone must not become an authorization"
    assert probe.calls[-1][3:] == ({}, {}, probe.body)
    assert len(probe.handler_observations) == 1
    handler_context, handler_authorization, _thread = probe.handler_observations[0]
    assert handler_context is not None and handler_authorization is not None
    assert isinstance(handler_authorization.evidence, AuthorizationEvidence)
    assert handler_context == context and handler_context is not context
    assert handler_authorization.evidence.principal == probe.principal
    assert handler_authorization.evidence.operation_id == "createTask" and handler_authorization.mutation is True
    assert handler_authorization.evidence.target.request_digest == context.authorization_request_digest
    assert probe.cleanup_observations == [(None, None)]
    assert current_task_creation_context() is None and current_authorization() is None


@pytest.mark.parametrize(
    "headers, expected_calls",
    [
        ([], []),
        ([("Authorization", "Basic self-owned")], []),
        ([("Authorization", "Bearer unknown-self-owned-token")], ["authenticate"]),
        ([("Authorization", "Bearer self-owned-token"), ("Authorization", "Bearer self-owned-token")], []),
    ],
)
def test_authentication_denial_precedes_ambiguous_raw_input(headers, expected_calls):
    probe = GuardProbe()
    with TestClient(probe.app) as client:
        response = client.post(PATH + "?unsupported=1", content=b"not-json", headers=headers)
    assert response.status_code == 401 and response.json() == {"code": "AUTHENTICATION_REQUIRED"}
    assert [call[0] for call in probe.calls] == expected_calls
    assert probe.conditional_observations == [] and probe.handler_observations == []
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize("kind", ["permission-denial", "permission-error", "permission-non-none", "identity-error"])
def test_identity_and_function_permission_failure_precede_body_query_and_key_parsing(kind):
    probe = GuardProbe()
    if kind == "permission-denial":
        probe.permission_error = BusinessError("PERMISSION_REQUIRED", 403)
    elif kind == "permission-error":
        probe.permission_error = RuntimeError("self-owned unavailable permission fixture")
    elif kind == "permission-non-none":
        probe.permission_result = True
    else:
        probe.authentication_error = RuntimeError("self-owned unavailable identity fixture")
    with TestClient(probe.app) as client:
        response = client.post(
            PATH + "?unsupported=1", content=b"not-json", headers={"Authorization": "Bearer self-owned-token"}
        )
    assert response.status_code == (403 if kind == "permission-denial" else 503)
    assert [call[0] for call in probe.calls] == (
        ["authenticate"] if kind == "identity-error" else ["authenticate", "permission"]
    )
    assert probe.conditional_observations == [] and probe.handler_observations == []
    assert probe.cleanup_observations == [(None, None)]


def malformed_body(name, value):
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
    if name in {"duplicate-same", "duplicate-other", "escaped-duplicate"}:
        key = '"case_id"' if name != "escaped-duplicate" else '"case_\\u0069d"'
        other = value["case_id"] if name == "duplicate-same" else str(uuid4())
        return raw[:-1] + b"," + key.encode() + b":" + json.dumps(other).encode() + b"}"
    if name in {"nan", "infinity", "negative-infinity", "overflow"}:
        literal = {"nan": b"NaN", "infinity": b"Infinity", "negative-infinity": b"-Infinity", "overflow": b"1e999"}[
            name
        ]
        return raw.replace(b'"priority":"normal"', b'"priority":' + literal)
    if name == "invalid-utf8":
        return raw.replace(b"self-owned/", b"\xff/")
    if name == "utf16":
        return raw.decode().encode("utf16")
    if name == "surrogate":
        value["policy_version"] = "self-owned/\ud800"
        return json.dumps(value).encode()
    return {"truncated": raw[:-1], "trailing": raw + b"{}", "array": b"[]", "null": b"null", "string": b'"self-owned"'}[
        name
    ]


@pytest.mark.parametrize(
    "name",
    [
        "duplicate-same",
        "duplicate-other",
        "escaped-duplicate",
        "nan",
        "infinity",
        "negative-infinity",
        "overflow",
        "invalid-utf8",
        "utf16",
        "surrogate",
        "truncated",
        "trailing",
        "array",
        "null",
        "string",
    ],
)
def test_raw_json_is_strictly_rejected_before_conditional(name):
    probe = GuardProbe()
    headers = probe.headers() | {"Content-Type": "application/json"}
    with TestClient(probe.app) as client:
        response = client.post(PATH, content=malformed_body(name, copy.deepcopy(probe.body)), headers=headers)
    assert response.status_code == 422
    assert [call[0] for call in probe.calls] == ["authenticate", "permission"]
    assert probe.conditional_observations == [] and probe.handler_observations == []
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize(
    "name",
    [
        "extra",
        "missing-case",
        "missing-asset",
        "zero-case",
        "zero-asset",
        "invalid-case",
        "invalid-asset",
        "scene",
        "policy-empty",
        "policy-long",
        "modules-empty",
        "modules-duplicate",
        "module-unknown",
        "priority",
        "bool-priority",
    ],
)
def test_task_create_schema_is_checked_before_conditional(name):
    probe = GuardProbe()
    value = copy.deepcopy(probe.body)
    if name == "extra":
        value["actor_id"] = str(probe.principal.actor.user_id)
    elif name.startswith("missing-"):
        del value[name.removeprefix("missing-") + "_id"]
    elif name.startswith("zero-"):
        value[name.removeprefix("zero-") + "_id"] = str(UUID(int=0))
    elif name.startswith("invalid-"):
        value[name.removeprefix("invalid-") + "_id"] = "self-owned-not-a-uuid"
    else:
        key, changed = {
            "scene": ("scene", "not-a-scene"),
            "policy-empty": ("policy_version", ""),
            "policy-long": ("policy_version", "x" * 129),
            "modules-empty": ("modules", []),
            "modules-duplicate": ("modules", ["INGEST", "INGEST"]),
            "module-unknown": ("modules", ["UNKNOWN"]),
            "priority": ("priority", "urgent"),
            "bool-priority": ("priority", True),
        }[name]
        value[key] = changed
    with TestClient(probe.app) as client:
        response = client.post(PATH, json=value, headers=probe.headers())
    assert response.status_code == 422
    assert [call[0] for call in probe.calls] == ["authenticate", "permission"]
    assert probe.conditional_observations == [] and probe.handler_observations == []
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize("suffix", ["?unknown=1", "?case_id=a&case_id=b", "?case_id=", "?limit=1", "?%61sset_id=x"])
def test_create_task_accepts_no_query_parameters(suffix):
    probe = GuardProbe()
    with TestClient(probe.app) as client:
        response = client.post(PATH + suffix, json=probe.body, headers=probe.headers())
    assert response.status_code == 422
    assert [call[0] for call in probe.calls] == ["authenticate", "permission"]
    assert probe.conditional_observations == [] and probe.handler_observations == []
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize("name", ["missing", "empty", "long", "duplicate-same", "duplicate-different"])
def test_exactly_one_contract_bounded_idempotency_key_precedes_conditional(name):
    probe = GuardProbe()
    headers = [("Authorization", "Bearer self-owned-token")]
    if name != "missing":
        headers.append(
            ("Idempotency-Key", "" if name == "empty" else "x" * 129 if name == "long" else "self-owned-key")
        )
    if name.startswith("duplicate-"):
        headers.append(("idempotency-key", "self-owned-key" if name == "duplicate-same" else "other-self-owned-key"))
    with TestClient(probe.app) as client:
        response = client.post(PATH, json=probe.body, headers=headers)
    assert response.status_code == 422
    assert [call[0] for call in probe.calls] == ["authenticate", "permission"]
    assert probe.conditional_observations == [] and probe.handler_observations == []
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize("key", ["a", "x" * 128, "one,literal-key", "literal key"])
def test_single_valid_key_does_not_invent_a_new_key_vocabulary(key):
    probe = GuardProbe()
    with TestClient(probe.app) as client:
        response = client.post(PATH, json=probe.body, headers=probe.headers() | {"Idempotency-Key": key})
    assert response.status_code == 200 and response.json() == {"component_probe": True}
    assert len(probe.conditional_observations) == len(probe.handler_observations) == 1
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize(
    "kind",
    [
        "principal",
        "operation",
        "org",
        "target-kind",
        "asset",
        "case",
        "purpose",
        "digest",
        "version-missing",
        "version-zero",
        "version-bool",
    ],
)
def test_mismatched_conditional_evidence_never_reaches_component_handler(kind):
    probe = GuardProbe()

    def transform(evidence):
        if kind == "principal":
            return replace(evidence, principal=replace(evidence.principal, subject="another-self-owned-subject"))
        if kind == "operation":
            return replace(evidence, operation_id="getAsset")
        key, value = {
            "org": ("org_id", uuid4()),
            "target-kind": ("kind", "task"),
            "asset": ("object_id", uuid4()),
            "case": ("case_id", uuid4()),
            "purpose": ("purpose", "read"),
            "digest": ("request_digest", "c" * 64),
            "version-missing": ("object_version", None),
            "version-zero": ("object_version", 0),
            "version-bool": ("object_version", True),
        }[kind]
        return replace(evidence, target=replace(evidence.target, **{key: value}))

    probe.evidence_transform = transform
    with TestClient(probe.app) as client:
        response = client.post(PATH, json=probe.body, headers=probe.headers())
    assert response.status_code == 503 and response.json() == {"code": "AUTHORITY_SCOPE_INVALID"}
    assert len(probe.conditional_observations) == 1 and probe.handler_observations == []
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize(
    "phase, business", [("conditional", True), ("conditional", False), ("handler", True), ("handler", False)]
)
def test_exception_paths_reset_both_request_bindings(phase, business):
    probe = GuardProbe()
    error = BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) if business else RuntimeError("self-owned failure")
    setattr(probe, phase + "_error", error)
    with TestClient(probe.app, raise_server_exceptions=False) as client:
        response = client.post(PATH, json=probe.body, headers=probe.headers())
    assert response.status_code == (500 if phase == "handler" and not business else 503)
    assert len(probe.conditional_observations) == 1
    assert len(probe.handler_observations) == (1 if phase == "handler" else 0)
    assert probe.cleanup_observations == [(None, None)]
    assert current_task_creation_context() is None and current_authorization() is None


def test_mutating_provider_body_does_not_change_the_parent_context():
    probe = GuardProbe()

    def mutate(_principal, _operation, _path, _query, body):
        body["modules"].reverse()
        body["priority"] = "high"
        observed = current_task_creation_context()
        assert observed is not None
        assert observed.request.modules == ("INGEST", "RESOURCE")
        assert observed.request.priority == "normal"

    probe.conditional_hook = mutate
    with TestClient(probe.app) as client:
        response = client.post(PATH, json=probe.body, headers=probe.headers())
    assert response.status_code == 200 and response.json() == {"component_probe": True}
    handler_context = probe.handler_observations[0][0]
    assert handler_context is not None
    assert handler_context.request.modules == ("INGEST", "RESOURCE")
    assert handler_context.request.priority == "normal"
    assert probe.cleanup_observations == [(None, None)]


@pytest.mark.parametrize("identity_mode", ["different-users", "same-user-different-cases"])
def test_overlapping_requests_do_not_share_threadpool_or_handler_context(identity_mode):
    probe = GuardProbe()
    second = replace(
        probe.principal, actor=Actor(uuid4(), probe.principal.actor.org_id), subject="second-self-owned-subject"
    )
    if identity_mode == "same-user-different-cases":
        second = probe.principal
    probe.identities["second-self-owned-token"] = second
    first_body, second_body = copy.deepcopy(probe.body), request_body()
    conditional_barrier, handler_barrier = Barrier(2, timeout=10), Barrier(2, timeout=10)
    lock, observed = Lock(), []

    def conditional(identity, _operation, _path, _query, body):
        before = current_task_creation_context()
        assert before is not None
        assert before.principal == identity
        assert before.request.case_id == UUID(body["case_id"]) and before.request.asset_id == UUID(body["asset_id"])
        assert current_authorization() is None
        conditional_barrier.wait()
        after = current_task_creation_context()
        assert after == before and after is not before
        with lock:
            observed.append((identity.actor.user_id, before.request.case_id, before.request.asset_id))

    def handler(context, authorization):
        assert authorization.evidence.principal == context.principal
        assert authorization.evidence.target.case_id == context.request.case_id
        assert authorization.evidence.target.object_id == context.request.asset_id
        handler_barrier.wait()
        assert current_task_creation_context() == context
        assert current_authorization() == authorization

    probe.conditional_hook, probe.handler_hook = conditional, handler
    with TestClient(probe.app) as client, ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(client.post, PATH, json=first_body, headers=probe.headers())
        second_result = executor.submit(
            client.post,
            PATH,
            json=second_body,
            headers=probe.headers() | {"Authorization": "Bearer second-self-owned-token"},
        )
        responses = [first.result(timeout=30), second_result.result(timeout=30)]
    assert [response.status_code for response in responses] == [200, 200]
    assert all(response.json() == {"component_probe": True} for response in responses)
    assert set(observed) == {
        (probe.principal.actor.user_id, UUID(first_body["case_id"]), UUID(first_body["asset_id"])),
        (second.actor.user_id, UUID(second_body["case_id"]), UUID(second_body["asset_id"])),
    }
    assert len(probe.conditional_observations) == len(probe.handler_observations) == 2
    assert probe.cleanup_observations == [(None, None), (None, None)]
    assert current_task_creation_context() is None and current_authorization() is None


def test_create_task_extra_query_is_rejected_before_conditional_facts():
    probe = GuardProbe()
    with TestClient(probe.app) as client:
        response = client.post(PATH + "?case_id=" + probe.body["case_id"], json=probe.body, headers=probe.headers())
    assert response.status_code == 422
    assert [call[0] for call in probe.calls] == ["authenticate", "permission"]
    assert probe.conditional_observations == [] and probe.handler_observations == []
    assert current_task_creation_context() is None and current_authorization() is None
