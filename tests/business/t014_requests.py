"""Valid contract requests and actual self-owned resources for the 42-operation denial matrix."""

import hashlib
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import psycopg
import yaml
from business_app.contracts import validate_api
from business_app.controls.definitions import FileDefinitions
from business_app.permissions.catalog import load_catalog
from business_app.types import Scope
from fastapi.routing import APIRoute, iter_route_contexts
from PIL import Image
from psycopg import sql

from tests.business.test_controls import AUTH, approve, export_fixture, request_approval, review_body
from tests.business.test_upload_validation import prepared_upload

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class PreparedRequests:
    requests: dict[str, dict[str, Any]] = field(default_factory=dict)
    extra_clients: list[Any] = field(default_factory=list)

    def close(self) -> None:
        for client in self.extra_clients:
            client.__exit__(None, None, None)


def send(http, request, *, authenticated=True):
    headers = dict(request["headers"])
    if authenticated:
        headers.setdefault("Authorization", AUTH["Authorization"])
    else:
        headers.pop("Authorization", None)
    options: dict[str, Any] = dict(headers=headers, params=request["params"])
    if request.get("content") is not None:
        options["content"] = request["content"]
    elif request.get("json") is not None:
        options["json"] = request["json"]
    return http.request(request["method"], request["path"], **options)


def business_state(context):
    """Compare all business rows, including audit/outbox/receipts, and object bytes."""
    records = {}
    with psycopg.connect(context["admin_dsn"]) as admin:
        names = admin.execute("SELECT tablename FROM pg_tables WHERE schemaname='mt' ORDER BY tablename").fetchall()
        for (name,) in names:
            row = admin.execute(
                sql.SQL(
                    "SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text)::text,'[]') FROM mt.{} t"
                ).format(sql.Identifier(name))
            ).fetchone()
            assert row is not None and isinstance(row[0], str)
            raw = row[0]
            records[name] = hashlib.sha256(raw.encode()).hexdigest()
    root = context["settings"].object_root
    objects = {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }
    return dict(tables=records, objects=objects)


def prepare_requests(c):
    resources = PreparedRequests()
    try:
        _populate(c, resources)
        return resources
    except Exception:
        resources.close()
        raise


def _populate(c, resources):
    app, http = c["control_app"], c["control_http"]
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format="PNG")
    image = buffer.getvalue()
    _, upload_http, complete_id, descriptor = prepared_upload(c, image)
    resources.extra_clients.append(upload_http)
    assert descriptor["sha256"] == hashlib.sha256(image).hexdigest()
    upload_body = dict(
        case_id=str(c["case_id"]),
        source_id=str(c["source_id"]),
        filename="self-owned.png",
        size_bytes=len(image),
        mime="image/png",
        sha256=descriptor["sha256"],
    )
    pending = http.post("/api/v1/uploads", json=upload_body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex}))
    assert pending.status_code == 201, pending.json()
    part_id = pending.json()["upload_id"]

    approval = request_approval(c)
    approval_detail = http.get(f"/api/v1/approvals/{approval}", headers=AUTH)
    assert approval_detail.status_code == 200
    revoke_target = request_approval(c)
    approve(c, revoke_target)
    revoke_detail = http.get(f"/api/v1/approvals/{revoke_target}", headers=AUTH)
    assert revoke_detail.status_code == 200
    review_context = http.get(f"/api/v1/analysis/tasks/{c['task_id']}/review-context", headers=AUTH)
    assert review_context.status_code == 200
    created_review = http.post(
        "/api/v1/reviews",
        json=review_body(c),
        headers=dict(AUTH, **{"If-Match": review_context.headers["ETag"], "Idempotency-Key": uuid4().hex}),
    )
    assert created_review.status_code == 201, created_review.json()
    review_id = created_review.json()["review_id"]
    next_review = http.get(f"/api/v1/analysis/tasks/{c['task_id']}/review-context", headers=AUTH)
    assert next_review.status_code == 200
    new_review_body = dict(review_body(c), expected_review_version=next_review.json()["review_version"])

    export_id, _ = export_fixture(c)
    app.state.exports.process(Scope(c["actor"], c["case_id"]), UUID(export_id))
    assert http.get(f"/api/v1/audit/exports/{export_id}/content", headers=AUTH).status_code == 200
    export_approval = request_approval(c, purpose="report_export", kind="operation")
    approve(c, export_approval)

    definitions = FileDefinitions(c["settings"].object_root / "fixture-policy-definitions")
    app.state.definition_provider = definitions
    reference = definitions.publish(
        c["actor"], "fixture/1", dict(scope="self-owned-permission-fixture", threshold=None)
    )
    policy_body = dict(kind="review", version="fixture/1", definition_ref=reference, approval_id=None, status="DRAFT")
    policy_response = http.post(
        "/api/v1/policies", json=policy_body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    )
    assert policy_response.status_code == 201, policy_response.json()
    policy_id = policy_response.json()["policy_id"]
    next_reference = definitions.publish(
        c["actor"], "fixture/2", dict(scope="self-owned-permission-fixture", threshold=None)
    )
    new_policy_body = dict(policy_body, version="fixture/2", definition_ref=next_reference)

    finding, feedback_approval, feedback, model, release, model_operation = [uuid4() for _ in range(6)]
    with psycopg.connect(c["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET purpose=array_append(array_append(purpose,'training'),'import') WHERE source_id=%s",
            (c["source_id"],),
        )
        admin.execute(
            "INSERT INTO mt.risk_finding(finding_id,org_id,case_id,task_id,run_version,result_version,category,model_name,model_version,status) VALUES(%s,%s,%s,%s,1,1,'self-owned-fixture','no-model-executed','fixture/1','insufficient')",
            (finding, c["actor"].org_id, c["case_id"], c["task_id"]),
        )
        admin.execute(
            "INSERT INTO mt.approval_request(approval_id,org_id,case_id,object_type,object_id,object_version,purpose,policy_version,requested_by,state,expires_at,reason,run_version,result_version) VALUES(%s,%s,%s,'task',%s,1,'training_feedback','policy-dev-1',%s,'REQUESTED',now()+interval '1 hour','self-owned fixture',1,1)",
            (feedback_approval, c["actor"].org_id, c["case_id"], c["task_id"], c["actor"].user_id),
        )
        admin.execute(
            "INSERT INTO mt.feedback_request(feedback_id,org_id,case_id,finding_id,approval_id,label_version,label,purpose,source_authorization_ref,state) VALUES(%s,%s,%s,%s,%s,'fixture/1','not-formal-taxonomy','training','not-formal-authorization','REQUESTED')",
            (feedback, c["actor"].org_id, c["case_id"], finding, feedback_approval),
        )
        admin.execute(
            "INSERT INTO mt.model_registry(model_id,org_id,name,version,capability,digest,dataset_version,model_card_ref,license_record_ref,backend,environment_ref,status) VALUES(%s,%s,'metadata-only-fixture','fixture/1','forensic.image_localization',%s,'no-training-data','fixture-card','not-production-admission','not-executing','fixture','REGISTERED')",
            (model, c["actor"].org_id, "0" * 64),
        )
        admin.execute(
            "INSERT INTO mt.model_release(release_id,org_id,model_id,bundle_sha256,backend,state,environment_ref) VALUES(%s,%s,%s,%s,'not-executing','CANDIDATE','fixture')",
            (release, c["actor"].org_id, model, "0" * 64),
        )

    class Operations:
        def get(self, actor, identifier):
            assert identifier == model_operation
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

    class SourceSynchronization:
        def current(self, scope, identifier):
            assert identifier == c["source_id"]
            return dict(
                source_id=str(identifier),
                case_id=str(scope.case_id),
                authorization_ref="self-owned-fixture",
                authorization_version="fixture-auth/2",
                purpose=["upload", "analysis", "import", "training"],
                authorization_status="verified",
                expires_at=None,
            )

    app.state.deployment_operations = Operations()
    app.state.source_synchronization = SourceSynchronization()
    from dataclasses import replace

    app.state.imports.settings = replace(c["control_settings"], max_import_entries=10)
    import_body = dict(
        case_id=str(c["case_id"]),
        entries=[
            dict(source_id=str(c["source_id"]), object_ref=c["input_ref"], filename="self-owned.png", mime="image/png")
        ],
    )
    imported = http.post("/api/v1/imports", json=import_body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex}))
    assert imported.status_code == 202, imported.json()
    import_id = imported.json()["import_id"]
    execution = http.get(f"/api/v1/analysis/tasks/{c['task_id']}/execution", headers=AUTH)
    assert execution.status_code == 200, execution.json()
    source = http.get(f"/api/v1/sources/{c['source_id']}", headers=AUTH)
    assert source.status_code == 200
    now = datetime.now(timezone.utc)

    bodies = dict(
        createUpload=upload_body,
        completeUpload=dict(parts=[descriptor]),
        requestApproval=dict(
            case_id=str(c["case_id"]),
            object_type="task",
            object_id=str(c["task_id"]),
            object_version=1,
            purpose="review",
            policy_version="policy-dev-1",
            reason="self-owned permission fixture",
            run_version=1,
            result_version=1,
        ),
        decideApproval=dict(
            expected_version=approval_detail.json()["approval"]["version"],
            decision="reject",
            reason="self-owned permission fixture",
            evidence_ids=[],
        ),
        revokeApproval=dict(
            expected_version=revoke_detail.json()["approval"]["version"], reason="self-owned permission fixture"
        ),
        createReview=new_review_body,
        exportAudit=dict(
            case_id=str(c["case_id"]),
            start_at=(now - timedelta(hours=1)).isoformat(),
            end_at=(now + timedelta(minutes=1)).isoformat(),
            purpose="self-owned-test-audit",
            approval_id=export_approval,
        ),
        syncSourceAuthorization=dict(expected_version=source.json()["version"]),
        createImport=import_body,
        createPolicy=new_policy_body,
        cancelTask=dict(
            expected_version=execution.json()["version"],
            expected_run_version=execution.json()["run_version"],
            approval_id=None,
            reason="self-owned permission fixture",
        ),
    )
    ids = dict(
        getUploadStatus=complete_id,
        listUploadParts=complete_id,
        putUploadPart=part_id,
        completeUpload=complete_id,
        getApproval=approval,
        decideApproval=approval,
        revokeApproval=revoke_target,
        getReview=review_id,
        getAuditExport=export_id,
        downloadAuditExport=export_id,
        getFeedback=str(feedback),
        getImport=import_id,
        getModelOperation=str(model_operation),
        getPolicy=policy_id,
        getPolicyDefinition=policy_id,
        getSource=str(c["source_id"]),
        syncSourceAuthorization=str(c["source_id"]),
    )
    etags = dict(
        decideApproval=approval_detail.headers["ETag"],
        revokeApproval=revoke_detail.headers["ETag"],
        createReview=next_review.headers["ETag"],
        syncSourceAuthorization=source.headers["ETag"],
        cancelTask=execution.headers["ETag"],
    )
    catalog = load_catalog(ROOT)
    specification = yaml.safe_load((ROOT / "docs/03-api/openapi.yaml").read_text(encoding="utf8"))
    mounted: set[str] = set()
    for context in iter_route_contexts(app.routes):
        if isinstance(context.original_route, APIRoute) and (context.path or "").startswith("/api/v1/"):
            identifier = getattr(context, "operation_id", None)
            assert isinstance(identifier, str)
            mounted.add(identifier)
    for identifier in sorted(mounted):
        operation = catalog[identifier]
        path = operation.path
        if "{id}" in path:
            if identifier in ids:
                value = ids[identifier]
            elif path.startswith("/api/v1/analysis/tasks/"):
                value = str(c["task_id"])
            elif path.startswith("/api/v1/assets/"):
                value = str(c["asset_id"])
            elif path.startswith("/api/v1/clusters/"):
                value = str(c["cluster_id"])
            else:
                raise AssertionError("Actual resource fixture is missing for " + identifier)
            path = path.replace("{id}", str(value))
        path = path.replace("{cluster_id}", str(c["cluster_id"])).replace("{part_no}", "1")
        assert "{" not in path
        params = {}
        if identifier in {"listApprovals", "listReviews", "listPendingReviews", "listAuditEvents", "listSources"}:
            params["case_id"] = str(c["case_id"])
        if identifier in {"listTaskNodes", "listTaskEvents"}:
            params["run_version"] = "1"
        headers = {"Idempotency-Key": uuid4().hex}
        if identifier in etags:
            headers["If-Match"] = etags[identifier]
        if identifier == "decideApproval":
            headers["Authorization"] = "Bearer test-only-reviewer-1"
        request: dict[str, Any] = dict(
            method=operation.method,
            path=path,
            headers=headers,
            params=params,
            json=bodies.get(identifier),
            content=None,
        )
        if identifier == "putUploadPart":
            request.update(content=image, json=None)
            headers.update(
                {
                    "Content-Length": str(len(image)),
                    "X-Part-Sha256": descriptor["sha256"],
                    "Content-Type": "application/octet-stream",
                }
            )
        elif identifier == "downloadAuditExport":
            headers["Range"] = "bytes=0-9"
        definition = specification["paths"][operation.path.removeprefix("/api/v1")][operation.method.lower()]
        body = definition.get("requestBody", {}).get("content", {}).get("application/json")
        if body:
            assert isinstance(request["json"], dict)
            validate_api(body["schema"]["$ref"].rsplit("/", 1)[-1], request["json"])
        resources.requests[identifier] = request
    assert len(resources.requests) == 42
