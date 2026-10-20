import copy
import hashlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from business_app.controls.common import canonical
from business_app.errors import BusinessError
from business_app.inference import MODELS, SCHEMAS, BackendRegistration
from business_app.main import create_app
from business_app.types import Scope
from fastapi.testclient import TestClient

from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context


def test_import_registered_fixed_objects_and_current_source(control_context):
    c = control_context
    http = c["control_http"]
    c["control_app"].state.imports.settings = replace(c["control_settings"], max_import_entries=10)
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.source_registry SET purpose=array_append(purpose,'import') WHERE source_id=%s", (c["source_id"],)
        )
    body: dict[str, Any] = dict(
        case_id=str(c["case_id"]),
        entries=[
            dict(source_id=str(c["source_id"]), object_ref=c["input_ref"], filename="self-owned.png", mime="image/png")
        ],
    )
    headers = dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    created = http.post("/api/v1/imports", json=body, headers=headers)
    assert created.status_code == 202, created.json()
    assert created.json()["state"] == "COMPLETED" and created.json()["items"][0]["asset_id"] == c["asset_id"]
    assert http.post("/api/v1/imports", json=body, headers=headers).json() == created.json()
    assert http.get(f"/api/v1/imports/{created.json()['import_id']}", headers=AUTH).json() == created.json()
    conflicting = copy.deepcopy(body)
    conflicting["entries"][0]["filename"] = "different.png"
    assert http.post("/api/v1/imports", json=conflicting, headers=headers).status_code == 409
    invalid = copy.deepcopy(body)
    invalid["entries"][0]["object_ref"]["object_id"] = str(uuid4())
    assert (
        http.post("/api/v1/imports", json=invalid, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})).status_code
        == 503
    )
    with psycopg.connect(c["admin_dsn"]) as connection:
        assert required_scalar(connection.execute("SELECT count(*) FROM mt.import_job")) == 1
        connection.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s", (c["source_id"],)
        )
    assert http.get(f"/api/v1/imports/{created.json()['import_id']}", headers=AUTH).status_code == 403


def test_source_authority_sync_rejects_forgery_and_invalidates_upload(control_context):
    c = control_context
    http = c["control_http"]

    class SourceAuthority:
        def current(self, scope, source_id):
            return dict(
                source_id=str(source_id),
                case_id=str(scope.case_id),
                authorization_ref="self-owned-authority-fixture",
                authorization_version="test-version-2",
                purpose=["upload", "analysis"],
                authorization_status="revoked",
                expires_at=None,
            )

    c["control_app"].state.source_synchronization = SourceAuthority()
    path = f"/api/v1/sources/{c['source_id']}"
    previous = http.get(path, headers=AUTH)
    headers = dict(AUTH, **{"If-Match": previous.headers["ETag"], "Idempotency-Key": uuid4().hex})
    updated = http.post(path + "/authorization/sync", json=dict(expected_version=1), headers=headers)
    assert updated.status_code == 200 and updated.json()["authorization_status"] == "revoked"
    assert updated.json()["version"] == 2
    assert (
        http.post(path + "/authorization/sync", json=dict(expected_version=1), headers=headers).json() == updated.json()
    )
    assert (
        http.post(
            path + "/authorization/sync",
            json=dict(expected_version=1),
            headers=dict(headers, **{"Idempotency-Key": uuid4().hex}),
        ).status_code
        == 412
    )
    assert (
        http.post(
            path + "/authorization/sync",
            json=dict(expected_version=2, authorization_status="verified"),
            headers=headers,
        ).status_code
        == 422
    )
    with psycopg.connect(c["admin_dsn"]) as connection:
        assert (
            required_scalar(
                connection.execute(
                    "SELECT authorization_version FROM mt.source_registry WHERE source_id=%s", (c["source_id"],)
                )
            )
            == "test-version-2"
        )


def test_policy_definition_digest_and_identity_binding(control_context):
    c = control_context
    http = c["control_http"]
    values = dict(purpose="self-owned-fixture-only", threshold=None)
    body = dict(
        kind="review",
        version="self-owned-policy-1",
        definition_ref="urn:sha256:" + hashlib.sha256(canonical(values)).hexdigest(),
        approval_id=None,
        status="DRAFT",
    )
    created = http.post("/api/v1/policies", json=body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex}))
    assert created.status_code == 201

    class Definitions:
        def resolve(self, actor, reference, version):
            values = dict(purpose="self-owned-fixture-only", threshold=None)
            return dict(
                definition_ref=reference,
                version=body["version"],
                sha256=hashlib.sha256(canonical(values)).hexdigest(),
                values=values,
            )

    c["control_app"].state.definition_provider = Definitions()
    path = f"/api/v1/policies/{created.json()['policy_id']}/definition"
    assert http.get(path, headers=AUTH).status_code == 200

    class BadDefinitions(Definitions):
        def resolve(self, actor, reference, version):
            value = super().resolve(actor, reference, version)
            value["sha256"] = "0" * 64
            return value

    c["control_app"].state.definition_provider = BadDefinitions()
    assert http.get(path, headers=AUTH).status_code == 503

    class BadIdentity:
        def current(self, actor):
            value = c["directory"].current(actor)
            value["user_id"] = str(uuid4())
            return value

    c["control_app"].state.identity_directory = BadIdentity()
    assert http.get("/api/v1/auth/me", headers=AUTH).status_code == 503
    assert (
        http.post(
            "/api/v1/policies",
            json=dict(body, version="another"),
            headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex}),
        ).status_code
        == 503
    )


def prepare_node(context):
    identifier = uuid4()
    with psycopg.connect(context["admin_dsn"]) as connection:
        connection.execute(
            "INSERT INTO mt.task_node_run(run_id,org_id,case_id,task_id,run_version,node_code,attempt,input_hash,state,required,fencing_epoch) VALUES(%s,%s,%s,%s,1,'self-owned-no-algorithm',1,%s,'READY',true,1)",
            (identifier, context["actor"].org_id, context["case_id"], context["task_id"], "0" * 64),
        )
    return identifier


def test_actual_node_lease_reclaim_fences_old_worker(control_context):
    c = control_context
    node = prepare_node(c)
    execution = c["control_app"].state.execution
    scope = Scope(c["actor"], c["case_id"])
    old = execution.claim(scope, node, task_id=c["task_id"])
    with pytest.raises(BusinessError) as error:
        execution.claim(scope, node, task_id=c["task_id"])
    assert error.value.code == "NODE_NOT_CLAIMABLE"
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.task_node_run SET started_at=now()-interval '31 seconds' WHERE run_id=%s", (node,)
        )
    current = execution.claim(scope, node, task_id=c["task_id"])
    assert current.epoch > old.epoch and current.token != old.token
    with pytest.raises(BusinessError) as error:
        execution.finish_without_result(scope, old, "FAILED", "old worker")
    assert error.value.code == "NODE_LEASE_STALE"
    execution.finish_without_result(scope, current, "NOT_SUPPORTED", "No algorithm installed; self-owned lease test")
    response = c["control_http"].get(
        f"/api/v1/analysis/tasks/{c['task_id']}/nodes", params=dict(run_version=1), headers=AUTH
    )
    assert response.status_code == 200 and response.json()["items"][0]["state"] == "NOT_SUPPORTED"
    assert "lease_token" not in response.text
    with pytest.raises(BusinessError):
        execution.finish_without_result(scope, current, "SUCCEEDED", "unsupported fake completion")


def test_nodes_and_events_bind_run_and_do_not_expose_other_case(control_context):
    c = control_context
    prepare_node(c)
    http = c["control_http"]
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "INSERT INTO mt.task_event(event_id,org_id,case_id,task_id,run_version,from_state,to_state,reason,request_id) VALUES(%s,%s,%s,%s,1,'CREATED','QUEUED','self-owned-event',%s)",
            (uuid4(), c["actor"].org_id, c["case_id"], c["task_id"], uuid4()),
        )
    for suffix in ["nodes", "events"]:
        path = f"/api/v1/analysis/tasks/{c['task_id']}/{suffix}"
        assert http.get(path, params=dict(run_version=1), headers=AUTH).status_code == 200
        assert http.get(path, params=dict(run_version=2), headers=AUTH).status_code == 404
        assert http.get(path, params=dict(run_version=1)).status_code == 401
    assert (
        http.get(f"/api/v1/analysis/tasks/{uuid4()}/nodes", params=dict(run_version=1), headers=AUTH).status_code == 404
    )


def model_request(context):
    return dict(
        request_id=str(uuid4()),
        case_id=str(context["case_id"]),
        task_id=str(context["task_id"]),
        run_version=1,
        capability="forensic.image_localization",
        model_name="self-owned-nonexecuting-protocol-fixture",
        model_version="test/1",
        input_kind="original_bytes",
        asset_ids=[context["asset_id"]],
        object_refs=[context["input_ref"]],
        source_segment_ids=[],
        preprocessing_version="test-preprocessing/1",
        mapping_version="test-mapping/1",
        missing_modalities=[],
        deadline_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
        authorization_version="test-version-1",
    )


def model_response(payload):
    identifier, _ = MODELS[payload["capability"]]
    schema = SCHEMAS[identifier.replace(":request:", ":response:")]
    return {
        k: payload[k]
        for k in [
            "request_id",
            "task_id",
            "run_version",
            "capability",
            "model_name",
            "model_version",
            "preprocessing_version",
            "mapping_version",
        ]
    } | dict(
        status="NOT_SUPPORTED",
        output_kind=schema["properties"]["output_kind"]["const"],
        findings=[],
        artifacts=[],
        missing_modalities=[],
        warnings=["Self-owned gateway test; no algorithm executed"],
        reason="Algorithm intentionally unavailable",
        latency_ms=0,
        mock=True,
        payload=None,
    )


def inference_app(context, backend):
    class Services:
        def authorize(self, bearer, payload):
            if bearer != "self-owned-service-token":
                raise BusinessError("SERVICE_AUTHENTICATION_REQUIRED", 401)
            return Scope(context["actor"], context["case_id"])

    payload = model_request(context)
    registration = BackendRegistration(
        payload["capability"],
        payload["model_name"],
        payload["model_version"],
        payload["preprocessing_version"],
        payload["mapping_version"],
        backend,
    )
    with psycopg.connect(context["admin_dsn"]) as connection:
        connection.execute("UPDATE mt.analysis_task SET state='RUNNING' WHERE task_id=%s", (context["task_id"],))
    return create_app(
        context["control_settings"],
        context["control_authority"],
        service_authority=Services(),
        inference_backends={registration.capability: registration},
        work_authorization=context["work_authorization"],
    ), payload


def test_gateway_checks_identity_capability_input_and_response(control_context):
    c = control_context

    class Backend:
        def execute(self, payload):
            return model_response(payload)

    app, payload = inference_app(c, Backend())
    path = "/internal/v1/inference/" + payload["capability"]
    headers = {"Authorization": "Bearer self-owned-service-token"}
    with TestClient(app) as http:
        result = http.post(path, json=payload, headers=headers)
        assert result.status_code == 200, result.json()
        assert result.json()["status"] == "NOT_SUPPORTED" and result.json()["payload"] is None
        assert http.post(path, json=payload, headers=AUTH).status_code == 401
        assert (
            http.post("/internal/v1/inference/retrieval.image_embedding", json=payload, headers=headers).status_code
            == 422
        )
        bad = copy.deepcopy(payload)
        bad["object_refs"][0]["sha256"] = "0" * 64
        assert http.post(path, json=bad, headers=headers).status_code == 422
        assert http.post(path, json=payload, headers=dict(headers, **{"X-Request-Id": str(uuid4())})).status_code == 422
        assert (
            http.post(
                path,
                json=dict(payload, deadline_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()),
                headers=headers,
            ).status_code
            == 504
        )


def test_gateway_rechecks_revocation_after_backend_returns(control_context):
    c = control_context

    class Backend:
        def execute(self, payload):
            with psycopg.connect(c["admin_dsn"]) as connection:
                connection.execute(
                    "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s", (c["source_id"],)
                )
            return model_response(payload)

    app, payload = inference_app(c, Backend())
    with TestClient(app) as http:
        response = http.post(
            "/internal/v1/inference/" + payload["capability"],
            json=payload,
            headers={"Authorization": "Bearer self-owned-service-token"},
        )
    assert response.status_code == 403


def test_gateway_rejects_wrong_response_identity(control_context):
    class Backend:
        def execute(self, payload):
            return dict(model_response(payload), task_id=str(uuid4()))

    app, payload = inference_app(control_context, Backend())
    with TestClient(app) as http:
        response = http.post(
            "/internal/v1/inference/" + payload["capability"],
            json=payload,
            headers={"Authorization": "Bearer self-owned-service-token"},
        )
    assert response.status_code == 503


def test_all_34_capabilities_have_distinct_request_and_response_contracts(control_context):
    assert len(MODELS) == 34
    for capability, (identifier, schema) in MODELS.items():
        assert schema["properties"]["capability"]["const"] == capability
        assert SCHEMAS[identifier.replace(":request:", ":response:")]["properties"]["capability"]["const"] == capability
    app = create_app(control_context["control_settings"], control_context["control_authority"])
    with TestClient(app) as http:
        payload = model_request(control_context)
        response = http.post(
            "/internal/v1/inference/" + payload["capability"],
            json=payload,
            headers={"Authorization": "Bearer self-owned-service-token"},
        )
        assert response.status_code == 503 and response.json()["code"] == "SERVICE_AUTHORITY_UNAVAILABLE"


def required_scalar(cursor):
    value = cursor.fetchone()
    assert value is not None
    return value[0]


@pytest.mark.parametrize("invalid", ["derived_asset", "wrong_mapping", None])
def test_decoded_original_preserves_original_asset_and_mapping(control_context, invalid):
    from tests.business.http_fixtures import FixtureWork

    c = control_context
    app, payload = inference_app(c, None)
    with psycopg.connect(c["admin_dsn"]) as connection:
        mapping = required_scalar(
            connection.execute("SELECT mapping_version FROM mt.media_asset WHERE asset_id=%s", (c["asset_id"],))
        )
        if invalid == "derived_asset":
            child = uuid4()
            connection.execute(
                "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,kind,parent_asset_id,mapping_version,state) SELECT %s,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,'derived',asset_id,mapping_version,state FROM mt.media_asset WHERE asset_id=%s",
                (child, c["asset_id"]),
            )
            payload["asset_ids"] = [str(child)]
    payload.update(
        capability="forensic.video_spatial",
        input_kind="decoded_original",
        mapping_version="incorrect-mapping" if invalid == "wrong_mapping" else mapping,
    )
    gateway = app.state.inference_gateway
    scope = Scope(c["actor"], c["case_id"])
    if invalid:
        with (
            pytest.raises(BusinessError) as error,
            FixtureWork(frozenset({scope.actor})).open(scope, "task_execution", c["task_id"], "startTaskNodeWork"),
        ):
            gateway.check_inputs(scope, payload)
        assert error.value.code == "DECODED_ORIGINAL_BINDING_INVALID"
    else:
        with FixtureWork(frozenset({scope.actor})).open(scope, "task_execution", c["task_id"], "startTaskNodeWork"):
            gateway.check_inputs(scope, payload)
