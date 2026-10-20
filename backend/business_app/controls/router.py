import hashlib
import json
from datetime import datetime
from typing import Annotated, Any, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import Connection, text

from ..auth import authorize_request
from ..contracts import validate_api, validate_response
from ..db import Database
from ..errors import BusinessError
from ..permissions.conditional import ConditionalPort
from ..permissions.guard import current_principal
from ..scope_collections import CollectionScope
from ..settings import BusinessSettings
from ..types import Actor, Scope
from ..uploads.repository import UploadRepository
from .approvals import Approvals
from .common import actor_for, audit, canonical, match, now, page, reply, resource_scope, row
from .execution import Execution
from .exports import Exports, audit_wire
from .imports import Imports
from .operation_tokens import OperationTokens
from .providers import DefinitionProvider, DeploymentOperations, IdentityDirectory, SourceSynchronization
from .reviews import Reviews

router = APIRouter(prefix="/api/v1")
Key = Annotated[str, Header(min_length=1, max_length=128)]
Limit = Annotated[int, Query(ge=1, le=100)]
Cursor = Annotated[str | None, Query(min_length=1, max_length=128)]


def db(request: Request) -> Database:
    return cast(Database, request.app.state.business_database)


def settings(request: Request) -> BusinessSettings:
    return cast(BusinessSettings, request.app.state.business_settings)


def collection_scope(request: Request) -> CollectionScope:
    return CollectionScope(cast(ConditionalPort, request.app.state.conditional_permissions))


def approvals(request: Request) -> Approvals:
    return cast(Approvals, request.app.state.approvals)


@router.post("/operation-tokens", operation_id="issueOperationToken")
def issue_operation_token(request: Request, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("OperationTokenRequest", body)
    scope = resource_scope(request, "approval", UUID(body["approval_id"]), "operation.confirm")
    service = cast(OperationTokens, request.app.state.operation_tokens)
    response = reply("OperationToken", service.issue(scope, body, request, idempotency_key))
    response.headers["Cache-Control"] = "no-store"
    return response


def reviews(request: Request) -> Reviews:
    return cast(Reviews, request.app.state.reviews)


def exports(request: Request) -> Exports:
    return cast(Exports, request.app.state.exports)


def review_scope(request: Request, scope: Scope, connection: Connection, operation_id: str) -> tuple[UUID, ...]:
    conditional = cast(ConditionalPort, request.app.state.conditional_permissions)
    try:
        identifiers = conditional.review_ids(
            current_principal(request), operation_id, scope.case_id, connection=connection
        )
    except BusinessError:
        raise
    except Exception:
        raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
    if (
        type(identifiers) is not tuple
        or any(not isinstance(v, UUID) for v in identifiers)
        or len(set(identifiers)) != len(identifiers)
    ):
        raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
    return identifiers


@router.get("/approvals", operation_id="listApprovals")
def list_approvals(request: Request, case_id: UUID, cursor: Cursor = None, limit: Limit = 20) -> JSONResponse:
    scope = authorize_request(request, case_id, "approval.read")
    with db(request).transaction(scope) as connection:
        rows, following = page(
            connection,
            "approval_request",
            "approval_id",
            scope,
            settings(request).cursor_secret,
            cursor,
            limit,
            collection=collection_scope(request),
        )
        items = [approvals(request).detail(connection, scope, item["approval_id"]) for item in rows]
    return reply("ApprovalPage", dict(items=items, next_cursor=following))


@router.get("/approvals/{id}", operation_id="getApproval")
def get_approval(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "approval", id, "approval.read")
    with db(request).transaction(scope) as connection:
        value = approvals(request).detail(connection, scope, id)
    return reply("ApprovalDetail", value)


@router.post("/approvals", status_code=201, operation_id="requestApproval")
def request_approval(request: Request, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("ApprovalCreate", body)
    if body["case_id"] is None:
        actor_for(request)
        raise BusinessError("ORGANIZATION_APPROVAL_ADAPTER_UNAVAILABLE", 503)
    scope = authorize_request(request, UUID(body["case_id"]), "approval.request")
    value = approvals(request).create(scope, body, request, idempotency_key)
    return reply("Approval", value["approval"], 201, value)


@router.post("/approvals/{id}/decisions", status_code=201, operation_id="decideApproval")
def decide_approval(request: Request, id: UUID, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("ApprovalDecision", body)
    scope = resource_scope(request, "approval", id, "approval.decide")
    value = approvals(request).decide(scope, id, body, request, idempotency_key)
    return reply("Approval", value["approval"], 201, value)


@router.post("/approvals/{id}/revoke", operation_id="revokeApproval")
def revoke_approval(request: Request, id: UUID, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("ApprovalRevoke", body)
    scope = resource_scope(request, "approval", id, "approval.revoke")
    value = approvals(request).decide(scope, id, body, request, idempotency_key, revoke=True)
    return reply("Approval", value["approval"], version=value)


@router.get("/reviews", operation_id="listReviews")
def list_reviews(
    request: Request, case_id: UUID, cursor: Cursor = None, limit: Limit = 20, task_id: UUID | None = None
) -> JSONResponse:
    scope = authorize_request(request, case_id, "review.read")
    with db(request).transaction(scope) as connection:
        predicate = "case_id=:case AND org_id=:org" + (" AND task_id=:task" if task_id is not None else "")
        rows, following = page(
            connection,
            "review_record",
            "review_id",
            scope,
            settings(request).cursor_secret,
            cursor,
            limit,
            where=predicate,
            filters=dict(task=task_id) if task_id else None,
            bind_visibility=True,
            collection=collection_scope(request),
        )
        items = [reviews(request).wire(connection, item["review_id"]) for item in rows]
    return reply("ReviewPage", dict(items=items, next_cursor=following))


@router.get("/reviews/pending", operation_id="listPendingReviews")
def pending_reviews(request: Request, case_id: UUID, cursor: Cursor = None, limit: Limit = 20) -> JSONResponse:
    scope = authorize_request(request, case_id, "review.read")
    revision = """row_version::text||':'||coalesce((SELECT r.sha256 FROM mt.task_result r WHERE r.case_id=analysis_task.case_id AND r.task_id=analysis_task.task_id ORDER BY r.run_version DESC,r.result_version DESC LIMIT 1),'')||':'||coalesce((SELECT max(v.review_version)::text FROM mt.review_record v WHERE v.case_id=analysis_task.case_id AND v.task_id=analysis_task.task_id),'0')"""
    with db(request).transaction(scope) as connection:
        rows, following = page(
            connection,
            "analysis_task",
            "task_id",
            scope,
            settings(request).cursor_secret,
            cursor,
            limit,
            where="case_id=:case AND org_id=:org AND state IN ('WAIT_REVIEW','REVIEWING','RETURNED')",
            version_expression=revision,
            bind_visibility=True,
            collection=collection_scope(request),
        )
        items = []
        for item in rows:
            context = None
            availability = "RESULT_UNAVAILABLE"
            try:
                context = reviews(request).context(connection, scope, item["task_id"])
                availability = "READY"
            except BusinessError as error:
                if error.http_status != 404:
                    raise
            items.append(
                dict(
                    task_id=str(item["task_id"]),
                    case_id=str(case_id),
                    task_state=item["state"],
                    availability=availability,
                    context=context,
                )
            )
        source_ids = {
            str(item["task_id"]): connection.execute(
                text("SELECT source_id FROM mt.media_asset WHERE case_id=:case AND asset_id=:asset"),
                dict(case=case_id, asset=item["asset_id"]),
            ).scalar_one_or_none()
            for item in rows
        }
    for item in items:
        source = source_ids[item["task_id"]]
        if item["context"] is not None:
            try:
                if source is None:
                    raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)
                request.app.state.business_authority.authorize_source(scope, source, "analysis")
            except BusinessError as error:
                if error.http_status != 403:
                    raise
                item["availability"], item["context"] = "SOURCE_BLOCKED", None
    return reply("PendingReviewPage", dict(items=items, next_cursor=following))


@router.get("/reviews/{id}", operation_id="getReview")
def get_review(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "review", id, "review.read")
    with db(request).transaction(scope) as connection:
        value = reviews(request).wire(connection, id)
    return reply("Review", value)


@router.get("/analysis/tasks/{id}/review-context", operation_id="getReviewContext")
def get_review_context(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "task", id, "review.read")
    with db(request).transaction(scope) as connection:
        value = reviews(request).context(connection, scope, id)
    return reply("ReviewContext", value)


@router.post("/reviews", status_code=201, operation_id="createReview")
def create_review(request: Request, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("ReviewCreate", body)
    scope = resource_scope(request, "task", UUID(body["task_id"]), "review.perform")
    return reply("Review", reviews(request).create(scope, body, request, idempotency_key), 201)


@router.get("/audit/events", operation_id="listAuditEvents")
def list_audit(request: Request, case_id: UUID, cursor: Cursor = None, limit: Limit = 20) -> JSONResponse:
    scope = authorize_request(request, case_id, "audit.read")
    with db(request).transaction(scope) as connection:
        rows, following = page(
            connection,
            "audit_event",
            "event_id",
            scope,
            settings(request).cursor_secret,
            cursor,
            limit,
            collection=collection_scope(request),
        )
    return reply("AuditEventPage", dict(items=[audit_wire(item) for item in rows], next_cursor=following))


@router.post("/audit/exports", status_code=202, operation_id="exportAudit")
def export_audit(request: Request, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("AuditExport", body)
    if body["case_id"] is None:
        actor_for(request)
        raise BusinessError("ORGANIZATION_AUDIT_EXPORT_UNAVAILABLE", 503)
    scope = authorize_request(request, UUID(body["case_id"]), "audit.export")
    return reply("ActionAck", exports(request).create(scope, body, request, idempotency_key), 202)


@router.get("/audit/exports/{id}", operation_id="getAuditExport")
def get_export(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "export", id, "audit.export")
    return reply("AuditExportStatus", exports(request).status(scope, id))


@router.get("/audit/exports/{id}/content", operation_id="downloadAuditExport")
def download_export(request: Request, id: UUID) -> Response:
    scope = resource_scope(request, "export", id, "audit.export")
    return exports(request).content(scope, id, request)


@router.get("/feedback/samples/{id}", operation_id="getFeedback")
def get_feedback(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "feedback", id, "feedback.read")
    with db(request).transaction(scope) as connection:
        item = row(connection, "feedback_request", "feedback_id", id)
        finding = row(connection, "risk_finding", "finding_id", item["finding_id"])
        approval = approvals(request).detail(connection, scope, item["approval_id"])
        if item["state"] == "APPLIED":
            raise BusinessError("FEEDBACK_DATASET_PROVENANCE_UNAVAILABLE", 503)
        if approval["approval"]["purpose"] != "training_feedback":
            raise BusinessError("FEEDBACK_APPROVAL_BINDING_INVALID", 503)
        binding = approval["binding"]
        task_binding = (
            binding["object_type"] == "task"
            and binding["object_id"] == str(finding["task_id"])
            and (approval["approval"]["run_version"], approval["approval"]["result_version"])
            == (finding["run_version"], finding["result_version"])
        )
        if not task_binding and not (binding["object_type"] == "feedback" and binding["object_id"] == str(id)):
            raise BusinessError("FEEDBACK_APPROVAL_BINDING_INVALID", 503)
        if item["state"] == "APPROVED" and approval["approval"]["state"] not in {
            "APPROVED",
            "REVOKED",
            "EXPIRED",
            "INVALIDATED",
        }:
            raise BusinessError("FEEDBACK_APPROVAL_STATE_CONFLICT", 503)
        state = item["state"]
        if approval["approval"]["state"] in {"REVOKED", "EXPIRED", "INVALIDATED"}:
            state = "REVOKED"
        return reply(
            "FeedbackRecord",
            dict(
                feedback_id=str(id), approval_id=str(item["approval_id"]), state=state, version=int(item["row_version"])
            ),
        )


@router.get("/auth/me", operation_id="getCurrentUser")
def current_user(request: Request) -> JSONResponse:
    actor = actor_for(request)
    provider = cast(IdentityDirectory | None, request.app.state.identity_directory)
    if provider is None:
        raise BusinessError("IDENTITY_DIRECTORY_UNAVAILABLE", 503)
    value = provider.current(actor)
    validate_response("CurrentUser", value)
    if (value["user_id"], value["org_id"]) != (str(actor.user_id), str(actor.org_id)):
        raise BusinessError("IDENTITY_DIRECTORY_BINDING_INVALID", 503)
    with db(request).identity_transaction(actor) as connection:
        if not connection.execute(text("SELECT mt.actor_in_org()")).scalar_one():
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        permitted = {
            str(v) for v in connection.execute(text("SELECT case_id FROM mt.current_actor_case_ids()")).scalars()
        }
    value = dict(value, case_ids=sorted(set(value["case_ids"]) & permitted))
    for identifier in value["case_ids"]:
        authorize_request(request, UUID(identifier), "case.read")
    return reply("CurrentUser", value)


def source_wire(item: dict[str, Any]) -> dict[str, Any]:
    state = item["authorization_status"]
    if state == "verified" and item["expires_at"] is not None and item["expires_at"] <= now():
        state = "expired"
    return dict(
        source_id=str(item["source_id"]),
        case_id=str(item["case_id"]),
        name=item["name"],
        source_type=item["source_type"],
        authorization_ref=item["authorization_ref"],
        purpose=item["purpose"],
        expires_at=item["expires_at"].isoformat() if item["expires_at"] else None,
        authorization_status=state,
        version=int(item["row_version"]),
    )


@router.get("/sources", operation_id="listSources")
def list_sources(request: Request, case_id: UUID, cursor: Cursor = None, limit: Limit = 20) -> JSONResponse:
    scope = authorize_request(request, case_id, "source.read")
    with db(request).transaction(scope) as connection:
        rows, following = page(
            connection,
            "source_registry",
            "source_id",
            scope,
            settings(request).cursor_secret,
            cursor,
            limit,
            collection=collection_scope(request),
        )
    return reply("SourcePage", dict(items=[source_wire(item) for item in rows], next_cursor=following))


@router.get("/sources/{id}", operation_id="getSource")
def get_source(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "source", id, "source.read")
    with db(request).transaction(scope) as connection:
        value = source_wire(row(connection, "source_registry", "source_id", id))
    return reply("Source", value)


@router.post("/sources/{id}/authorization/sync", operation_id="syncSourceAuthorization")
def sync_source(request: Request, id: UUID, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("SourceSyncRequest", body)
    scope = resource_scope(request, "source", id, "source.manage")
    provider = cast(SourceSynchronization | None, request.app.state.source_synchronization)
    if provider is None:
        raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)
    authoritative = provider.current(scope, id)
    validate_response("SourceAuthorizationUpdate", authoritative)
    if authoritative["source_id"] != str(id) or authoritative["case_id"] != str(scope.case_id):
        raise BusinessError("SOURCE_AUTHORITY_BINDING_INVALID", 503)
    receipts = cast(UploadRepository, request.app.state.control_receipts)
    digest = hashlib.sha256(canonical([str(id), body])).hexdigest()
    with db(request).transaction(scope) as connection:
        item = row(connection, "source_registry", "source_id", id, lock=True)
        old = receipts.replay(connection, scope, "syncSourceAuthorization", idempotency_key, digest)
        if old is not None:
            return reply("Source", old)
        match(request, source_wire(item))
        if body["expected_version"] != item["row_version"]:
            raise BusinessError("SOURCE_VERSION_CONFLICT", 409)
        params = dict(
            authoritative,
            id=id,
            case=scope.case_id,
            expires=datetime.fromisoformat(authoritative["expires_at"].replace("Z", "+00:00"))
            if authoritative["expires_at"]
            else None,
        )
        if item["authorization_version"] == authoritative["authorization_version"]:
            if (
                any(item[k] != params[k] for k in ["authorization_status", "authorization_ref", "purpose"])
                or item["expires_at"] != params["expires"]
            ):
                raise BusinessError("SOURCE_AUTHORITY_VERSION_CONFLICT", 503)
        else:
            connection.execute(
                text(
                    "UPDATE mt.source_registry SET authorization_ref=:authorization_ref,purpose=:purpose,authorization_status=:authorization_status,authorization_version=:authorization_version,expires_at=:expires,row_version=row_version+1,updated_at=now() WHERE case_id=:case AND source_id=:id"
                ),
                params,
            )
        value = source_wire(row(connection, "source_registry", "source_id", id))
        receipts.remember(connection, scope, "syncSourceAuthorization", idempotency_key, digest, value)
        audit(connection, scope, "source.authorization.sync", "source", id, value["version"], request)
    return reply("Source", value)


@router.get("/imports/{id}", operation_id="getImport")
def get_import(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "import", id, "asset.import")
    with db(request).transaction(scope) as connection:
        item = row(connection, "import_job", "import_id", id)
        items = (
            connection.execute(
                text(
                    "SELECT ordinal,asset_id,state,error_code,source_id FROM mt.import_item WHERE case_id=:case AND import_id=:id ORDER BY ordinal"
                ),
                dict(case=scope.case_id, id=id),
            )
            .mappings()
            .all()
        )
        if len(items) != item["requested_count"] or [v["ordinal"] for v in items] != list(range(len(items))):
            raise BusinessError("IMPORT_ITEM_LEDGER_INCOMPLETE", 503)
        for value in items:
            authority = request.app.state.business_authority
            authority.authorize_source(scope, value["source_id"], "analysis")
            if value["state"] == "accepted":
                asset = connection.execute(
                    text("SELECT source_id,state FROM mt.media_asset WHERE case_id=:case AND asset_id=:asset"),
                    dict(case=scope.case_id, asset=value["asset_id"]),
                ).one_or_none()
                if asset is None or tuple(asset) != (value["source_id"], "VALID"):
                    raise BusinessError("IMPORT_ASSET_BINDING_INVALID", 503)
        result = dict(
            import_id=str(id),
            state=item["state"],
            items=[
                dict(
                    ordinal=int(v["ordinal"]),
                    asset_id=str(v["asset_id"]) if v["asset_id"] else None,
                    state=v["state"],
                    error_code=v["error_code"],
                )
                for v in items
            ],
        )
    return reply("ImportStatus", result)


@router.post("/imports", status_code=202, operation_id="createImport")
def create_import(request: Request, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("ImportRequest", body)
    scope = authorize_request(request, UUID(body["case_id"]), "asset.import")
    service = cast(Imports, request.app.state.imports)
    return reply("ImportStatus", service.create(scope, body, request, idempotency_key), 202)


@router.get("/model-operations/{id}", operation_id="getModelOperation")
def model_operation(request: Request, id: UUID) -> JSONResponse:
    actor = policy_actor(request, "model.read")
    provider = cast(DeploymentOperations | None, request.app.state.deployment_operations)
    if provider is None:
        raise BusinessError("DEPLOYMENT_OPERATION_ADAPTER_UNAVAILABLE", 503)
    value = provider.get(actor, id)
    validate_response("ModelOperation", value)
    if value["operation_id"] != str(id) or value["org_id"] != str(actor.org_id):
        raise BusinessError("DEPLOYMENT_OPERATION_BINDING_INVALID", 503)
    with db(request).identity_transaction(actor) as connection:
        release = connection.execute(
            text(
                "SELECT r.model_id,r.state,m.version FROM mt.model_release r JOIN mt.model_registry m ON m.org_id=r.org_id AND m.model_id=r.model_id WHERE r.org_id=:org AND r.release_id=:id"
            ),
            dict(org=actor.org_id, id=UUID(value["release_bundle_id"])),
        ).one_or_none()
        if release is None or str(release[0]) != value["model_id"] or release[2] != value["model_version"]:
            raise BusinessError("DEPLOYMENT_RELEASE_BINDING_INVALID", 503)
        if value["state"] == "SUCCEEDED" and (
            value["progress"] != 1
            or value["error_code"] is not None
            or (value["mode"] in {"activate", "rollback"} and release[1] != "ACTIVE")
        ):
            raise BusinessError("DEPLOYMENT_TERMINAL_STATE_INVALID", 503)
        if value["state"] == "FAILED" and value["error_code"] is None:
            raise BusinessError("DEPLOYMENT_TERMINAL_STATE_INVALID", 503)
    return reply("ModelOperation", value)


def policy_wire(item: dict[str, Any]) -> dict[str, Any]:
    return {key: str(item[key]) if item[key] is not None else None for key in ["policy_id", "approval_id"]} | {
        key: item[key] for key in ["kind", "version", "definition_ref", "status", "row_version"]
    }


@router.post("/policies", status_code=201, operation_id="createPolicy")
def create_policy(request: Request, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("PolicyCreate", body)
    actor = policy_actor(request, "policy.manage")
    if body["status"] != "DRAFT" or body["approval_id"] is not None:
        raise BusinessError("POLICY_ACTIVATION_RULE_UNAVAILABLE", 503)
    ttl = settings(request).control_ttl_seconds
    if ttl is None:
        raise BusinessError("CONTROL_RECEIPT_TTL_UNCONFIRMED", 503)
    # Organisation policies never require an invented case membership.
    digest = hashlib.sha256(canonical(body)).hexdigest()
    with db(request).identity_transaction(actor) as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            dict(key=f"policy-request/{actor.org_id}/{actor.user_id}/{idempotency_key}"),
        )
        # Audit details are an immutable receipt for this organisation-scoped operation.
        receipt = connection.execute(
            text(
                "SELECT details FROM mt.audit_event WHERE case_id IS NULL AND org_id=:org AND actor_id=:actor AND action='policy.create' AND details->>'key_sha256'=:key ORDER BY created_at LIMIT 1"
            ),
            dict(org=actor.org_id, actor=actor.user_id, key=hashlib.sha256(idempotency_key.encode()).hexdigest()),
        ).scalar_one_or_none()
        if receipt is not None:
            if receipt["request_sha256"] != digest or datetime.fromisoformat(receipt["expires_at"]) <= now():
                raise BusinessError("IDEMPOTENCY_CONFLICT", 409)
            return reply("Policy", dict(receipt["response"]), 201)
        connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            dict(key=f"policy/{actor.org_id}/{body['kind']}/{body['version']}"),
        )
        existing = (
            connection.execute(
                text("SELECT * FROM mt.policy_registry WHERE org_id=:org AND kind=:kind AND version=:version"),
                dict(body, org=actor.org_id),
            )
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            value = policy_wire(dict(existing))
            if any(value[k] != body[k] for k in body):
                raise BusinessError("POLICY_VERSION_EXISTS", 409)
            identifier = UUID(value["policy_id"])
        else:
            identifier = uuid4()
            created = (
                connection.execute(
                    text(
                        "INSERT INTO mt.policy_registry(policy_id,org_id,kind,version,definition_ref,status,approval_id,created_by) VALUES(:id,:org,:kind,:version,:definition_ref,'DRAFT',NULL,:actor) RETURNING *"
                    ),
                    dict(body, id=identifier, org=actor.org_id, actor=actor.user_id),
                )
                .mappings()
                .one()
            )
            value = policy_wire(dict(created))
        from datetime import timedelta

        connection.execute(
            text(
                "INSERT INTO mt.audit_event(event_id,org_id,actor_id,action,object_type,object_id,object_version,outcome,request_id,occurred_at,details,created_by) VALUES(:id,:org,:actor,'policy.create','policy',:policy,1,'allowed',:request,now(),CAST(:details AS jsonb),:actor)"
            ),
            dict(
                id=uuid4(),
                org=actor.org_id,
                actor=actor.user_id,
                policy=identifier,
                request=uuid4(),
                details=json.dumps(
                    dict(
                        key_sha256=hashlib.sha256(idempotency_key.encode()).hexdigest(),
                        request_sha256=digest,
                        response=value,
                        expires_at=(now() + timedelta(seconds=ttl)).isoformat(),
                    )
                ),
            ),
        )
    return reply("Policy", value, 201)


@router.get("/policies", operation_id="listPolicies")
def list_policies(request: Request, cursor: Cursor = None, limit: Limit = 20) -> JSONResponse:
    actor = policy_actor(request)
    conditional = cast(ConditionalPort, request.app.state.conditional_permissions)
    allowed_kinds = conditional.policy_kinds(current_principal(request))
    with db(request).identity_transaction(actor) as connection:
        rows, following = page(
            connection,
            "policy_registry",
            "policy_id",
            Scope(actor, UUID(int=0)),
            settings(request).cursor_secret,
            cursor,
            limit,
            where="org_id=:org AND kind=ANY(:allowed_kinds)",
            filters=dict(allowed_kinds=list(allowed_kinds)),
            collection=collection_scope(request),
        )
    return reply("PolicyPage", dict(items=[policy_wire(v) for v in rows], next_cursor=following))


def policy_actor(request: Request, permission: str = "policy.read") -> Actor:
    actor = actor_for(request)
    provider = cast(IdentityDirectory | None, request.app.state.identity_directory)
    if provider is None:
        raise BusinessError("IDENTITY_DIRECTORY_UNAVAILABLE", 503)
    claims = provider.current(actor)
    validate_response("CurrentUser", claims)
    if (claims["user_id"], claims["org_id"]) != (str(actor.user_id), str(actor.org_id)):
        raise BusinessError("IDENTITY_DIRECTORY_BINDING_INVALID", 503)
    if permission not in claims["permissions"]:
        raise BusinessError("POLICY_PERMISSION_REQUIRED", 403)
    with db(request).identity_transaction(actor) as connection:
        if not connection.execute(text("SELECT mt.actor_in_org()")).scalar_one():
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
    return actor


@router.get("/policies/{id}", operation_id="getPolicy")
def get_policy(request: Request, id: UUID) -> JSONResponse:
    actor = policy_actor(request)
    with db(request).identity_transaction(actor) as connection:
        value = policy_wire(row(connection, "policy_registry", "policy_id", id))
    return reply("Policy", value)


@router.get("/policies/{id}/definition", operation_id="getPolicyDefinition")
def get_policy_definition(request: Request, id: UUID) -> JSONResponse:
    actor = policy_actor(request)
    provider = cast(DefinitionProvider | None, request.app.state.definition_provider)
    if provider is None:
        raise BusinessError("POLICY_DEFINITION_UNAVAILABLE", 503)
    with db(request).identity_transaction(actor) as connection:
        item = row(connection, "policy_registry", "policy_id", id)
        definition = provider.resolve(actor, item["definition_ref"], item["version"])
        validate_response("PolicyDefinition", definition)
        if (
            definition["definition_ref"] != item["definition_ref"]
            or definition["version"] != item["version"]
            or definition["sha256"] != hashlib.sha256(canonical(definition["values"])).hexdigest()
            or item["definition_ref"] != "urn:sha256:" + definition["sha256"]
        ):
            raise BusinessError("POLICY_DEFINITION_BINDING_INVALID", 503)
        return reply("PolicyDefinition", definition)


@router.get("/analysis/tasks/{id}/nodes", operation_id="listTaskNodes")
def list_nodes(request: Request, id: UUID, run_version: Annotated[int, Query(ge=1)]) -> JSONResponse:
    scope = resource_scope(request, "task", id, "task.read")
    execution = cast(Execution, request.app.state.execution)
    return reply("NodePage", execution.nodes(scope, id, run_version))


@router.get("/analysis/tasks/{id}/execution", operation_id="getTaskExecution")
def task_execution(request: Request, id: UUID) -> JSONResponse:
    scope = resource_scope(request, "task", id, "task.read")
    execution = cast(Execution, request.app.state.execution)
    with db(request).transaction(scope) as connection:
        value = execution.status(connection, scope, id)
    return reply("TaskExecutionStatus", value)


@router.post("/analysis/tasks/{id}/cancel", status_code=202, operation_id="cancelTask")
def cancel_task(request: Request, id: UUID, body: dict[str, Any], idempotency_key: Key) -> JSONResponse:
    validate_api("TaskAction", body)
    scope = resource_scope(request, "task", id, "task.cancel")
    rules = approvals(request).rules
    if rules is None:
        raise BusinessError("CANCELLATION_RULE_UNAVAILABLE", 503)
    rules.cancellation(scope, UUID(body["approval_id"]) if body["approval_id"] else None)
    execution = cast(Execution, request.app.state.execution)
    receipts = cast(UploadRepository, request.app.state.control_receipts)
    digest = hashlib.sha256(canonical([str(id), body])).hexdigest()
    with db(request).transaction(scope) as connection:
        value = execution.status(connection, scope, id, lock=True)
        old = receipts.replay(connection, scope, "cancelTask", idempotency_key, digest)
        if old is not None:
            return reply("Accepted", old, 202)
        match(request, value)
        if (body["expected_version"], body["expected_run_version"]) != (value["version"], value["run_version"]):
            raise BusinessError("TASK_CONTROL_VERSION_CONFLICT", 409)
        if value["state"] not in {"CREATED", "QUEUED", "RUNNING", "WAIT_REVIEW", "REVIEWING", "RETURNED"}:
            raise BusinessError("TASK_CONTROL_STATE_CONFLICT", 409)
        if body["approval_id"] is not None:
            approval = approvals(request).detail(connection, scope, UUID(body["approval_id"]))
            if (
                approval["approval"]["state"] != "APPROVED"
                or approval["approval"]["purpose"] != "confirmation"
                or approval["binding"]["object_id"] != str(id)
                or approval["binding"]["object_type"] != "task"
            ):
                raise BusinessError("CANCELLATION_CONFIRMATION_INVALID", 403)
        connection.execute(
            text(
                "UPDATE mt.analysis_task SET state='CANCEL_REQUESTED',row_version=row_version+1,updated_at=now() WHERE case_id=:case AND task_id=:id"
            ),
            dict(case=scope.case_id, id=id),
        )
        execution.transition(
            connection,
            scope,
            id,
            value["version"] + 1,
            value["state"],
            "CANCEL_REQUESTED",
            request.state.request_id,
            body["reason"],
        )
        result = dict(task_id=str(id), state="CANCEL_REQUESTED", status_url=f"/api/v1/analysis/tasks/{id}/execution")
        receipts.remember(connection, scope, "cancelTask", idempotency_key, digest, result)
        audit(connection, scope, "task.cancel.request", "task", id, value["version"] + 1, request)
    return reply("Accepted", result, 202)


@router.get("/analysis/tasks/{id}/events", operation_id="listTaskEvents")
def list_events(
    request: Request, id: UUID, run_version: Annotated[int, Query(ge=1)], cursor: Cursor = None, limit: Limit = 20
) -> JSONResponse:
    scope = resource_scope(request, "task", id, "task.read")
    with db(request).transaction(scope) as connection:
        if (
            connection.execute(
                text("SELECT 1 FROM mt.task_run WHERE case_id=:case AND task_id=:task AND run_version=:run"),
                dict(case=scope.case_id, task=id, run=run_version),
            ).scalar_one_or_none()
            is None
        ):
            raise BusinessError("TASK_RUN_NOT_FOUND", 404)
        rows, following = page(
            connection,
            "task_event",
            "event_id",
            scope,
            settings(request).cursor_secret,
            cursor,
            limit,
            where="case_id=:case AND task_id=:task AND run_version=:run",
            filters=dict(task=id, run=run_version),
        )
        items = [
            dict(
                event_id=str(v["event_id"]),
                task_id=str(v["task_id"]),
                run_version=int(v["run_version"]),
                from_state=v["from_state"],
                to_state=v["to_state"],
                reason=v["reason"],
                request_id=str(v["request_id"]),
                created_at=v["created_at"].isoformat(),
            )
            for v in rows
        ]
    return reply("TaskEventPage", dict(items=items, next_cursor=following))
