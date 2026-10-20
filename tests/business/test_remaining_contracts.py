from uuid import uuid4

import psycopg
import pytest
from business_app.controls.definitions import FileDefinitions
from business_app.errors import BusinessError

from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context


def test_feedback_reads_real_request_and_refuses_unproven_applied_state(control_context):
    c = control_context
    finding, approval, feedback = [uuid4() for _ in range(3)]
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.source_registry SET purpose=array_append(purpose,'training') WHERE source_id=%s",
            (c["source_id"],),
        )
        connection.execute(
            "INSERT INTO mt.risk_finding(finding_id,org_id,case_id,task_id,run_version,result_version,category,model_name,model_version,status) VALUES(%s,%s,%s,%s,1,1,'self-owned-insufficient-fixture','no-model-executed','fixture/1','insufficient')",
            (finding, c["actor"].org_id, c["case_id"], c["task_id"]),
        )
        connection.execute(
            "INSERT INTO mt.approval_request(approval_id,org_id,case_id,object_type,object_id,object_version,purpose,policy_version,requested_by,state,expires_at,reason,run_version,result_version) VALUES(%s,%s,%s,'task',%s,1,'training_feedback','policy-dev-1',%s,'REQUESTED',now()+interval '30 minutes','self-owned fixture',1,1)",
            (approval, c["actor"].org_id, c["case_id"], c["task_id"], c["actor"].user_id),
        )
        connection.execute(
            "INSERT INTO mt.feedback_request(feedback_id,org_id,case_id,finding_id,approval_id,label_version,label,purpose,source_authorization_ref,state) VALUES(%s,%s,%s,%s,%s,'fixture-label/1','fixture-not-formal-taxonomy','training','fixture-not-formal-authority','REQUESTED')",
            (feedback, c["actor"].org_id, c["case_id"], finding, approval),
        )
    path = f"/api/v1/feedback/samples/{feedback}"
    read = c["control_http"].get(path, headers=AUTH)
    assert read.status_code == 200 and read.json()["state"] == "REQUESTED"
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute("UPDATE mt.feedback_request SET state='APPLIED' WHERE feedback_id=%s", (feedback,))
    rejected = c["control_http"].get(path, headers=AUTH)
    assert rejected.status_code == 503 and rejected.json()["code"] == "FEEDBACK_DATASET_PROVENANCE_UNAVAILABLE"


def test_deployment_operation_matches_organization_and_registered_release(control_context):
    c = control_context
    model, release, operation = [uuid4() for _ in range(3)]
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "INSERT INTO mt.model_registry(model_id,org_id,name,version,capability,digest,dataset_version,model_card_ref,license_record_ref,backend,environment_ref,status) VALUES(%s,%s,'self-owned-metadata-only','fixture/1','forensic.image_localization',%s,'fixture-no-data','fixture-card','not-a-production-license','fixture-not-executing','fixture-environment','REGISTERED')",
            (model, c["actor"].org_id, "0" * 64),
        )
        connection.execute(
            "INSERT INTO mt.model_release(release_id,org_id,model_id,bundle_sha256,backend,state,environment_ref) VALUES(%s,%s,%s,%s,'fixture-not-executing','CANDIDATE','fixture-environment')",
            (release, c["actor"].org_id, model, "0" * 64),
        )

    class Operations:
        def get(self, actor, identifier):
            return dict(
                operation_id=str(identifier),
                org_id=str(actor.org_id),
                release_bundle_id=str(release),
                model_id=str(model),
                mode="activate",
                state="REQUESTED",
                version=1,
                progress=0,
                model_version="fixture/1",
                index_version=None,
                error_code=None,
            )

    c["control_app"].state.deployment_operations = Operations()
    assert c["control_http"].get(f"/api/v1/model-operations/{operation}", headers=AUTH).status_code == 200

    class FalseSuccess(Operations):
        def get(self, actor, identifier):
            return dict(super().get(actor, identifier), state="SUCCEEDED", progress=1)

    c["control_app"].state.deployment_operations = FalseSuccess()
    assert c["control_http"].get(f"/api/v1/model-operations/{operation}", headers=AUTH).status_code == 503


def test_runtime_openapi_is_authoritative_and_only_publishes_mounted_operations(control_context):
    c = control_context
    spec = c["control_http"].get("/openapi.json").json()
    operations = {op["operationId"] for methods in spec["paths"].values() for op in methods.values()}
    assert len(operations) == 43 and "getApproval" in operations and "internalInference" in operations
    assert "devLogin" not in operations and "rolloutModel" not in operations and "requestFeedback" not in operations
    assert len(spec["components"]["schemas"]) == 102
    assert (
        spec["paths"]["/api/v1/approvals"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ApprovalCreate"
    )
    assert spec["paths"]["/internal/v1/inference/{capability}"]["post"]["security"] == [{"serviceAuth": []}]
    trace = str(uuid4())
    response = c["control_http"].get("/api/v1/auth/me", headers=dict(AUTH, **{"X-Request-Id": trace}))
    assert response.headers["X-Request-Id"] == trace
    assert (
        c["control_http"].get("/api/v1/auth/me", headers=dict(AUTH, **{"X-Request-Id": "invalid"})).status_code == 422
    )


def test_pending_workbench_includes_unreviewed_task_and_rechecks_source(control_context):
    c = control_context
    http = c["control_http"]
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.analysis_task SET state='WAIT_REVIEW',row_version=row_version+1 WHERE task_id=%s",
            (c["task_id"],),
        )
    assert http.get("/api/v1/reviews", params=dict(case_id=str(c["case_id"])), headers=AUTH).json()["items"] == []
    path = "/api/v1/reviews/pending"
    ready = http.get(path, params=dict(case_id=str(c["case_id"])), headers=AUTH)
    assert ready.status_code == 200 and len(ready.json()["items"]) == 1
    item = ready.json()["items"][0]
    assert item["availability"] == "READY" and item["context"]["review_version"] == 0
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s", (c["source_id"],)
        )
    blocked = http.get(path, params=dict(case_id=str(c["case_id"])), headers=AUTH).json()["items"][0]
    assert blocked["availability"] == "SOURCE_BLOCKED" and blocked["context"] is None


def test_real_parameter_definition_storage_digest_version_and_organization(control_context, tmp_path):
    c = control_context
    provider = FileDefinitions(tmp_path / "private-parameter-definitions")
    values = dict(review_threshold=None, scope="self-owned-planning-fixture")
    reference = provider.publish(c["actor"], "fixture/1", values)
    assert provider.publish(c["actor"], "fixture/1", values) == reference
    assert provider.resolve(c["actor"], reference, "fixture/1")["values"] == values
    with pytest.raises(BusinessError):
        provider.resolve(c["other_actor"], reference, "fixture/1")
    c["control_app"].state.definition_provider = provider
    body = dict(kind="review", version="fixture/1", definition_ref=reference, approval_id=None, status="DRAFT")
    created = c["control_http"].post(
        "/api/v1/policies", json=body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    )
    assert created.status_code == 201
    path = f"/api/v1/policies/{created.json()['policy_id']}/definition"
    assert c["control_http"].get(path, headers=AUTH).json()["values"] == values
    provider.path(c["actor"], reference, "fixture/1").write_text('{"version":"fixture/1","values":{"tampered":true}}')
    assert c["control_http"].get(path, headers=AUTH).status_code == 503
