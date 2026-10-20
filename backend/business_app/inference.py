"""Validate independent model contracts before calling explicitly registered backends."""

import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, cast
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from sqlalchemy import text

from .auth import AuthorityProvider
from .contracts import REGISTRY, SCHEMAS
from .controls.common import now
from .db import Database
from .errors import BusinessError
from .objects import FileObjectStore
from .permissions.context import WorkPort, protected_work
from .types import ObjectRef, Scope

router = APIRouter(prefix="/internal/v1")


class ServiceAuthority(Protocol):
    def authorize(self, bearer: str, payload: dict[str, Any]) -> Scope: ...


class ModelBackend(Protocol):
    def execute(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class ResponseSemantics(Protocol):
    def validate(self, scope: Scope, request: dict[str, Any], response: dict[str, Any]) -> None: ...


@dataclass(frozen=True)
class BackendRegistration:
    capability: str
    model_name: str
    model_version: str
    preprocessing_version: str
    mapping_version: str
    backend: ModelBackend
    release_bundle_id: UUID | None = None
    semantics: ResponseSemantics | None = None


MODELS = {
    schema["properties"]["capability"]["const"]: (identifier, schema)
    for identifier, schema in SCHEMAS.items()
    if identifier.startswith("urn:media-trace:model:") and ":request:" in identifier
}


def validate_model(identifier: str, payload: dict[str, Any]) -> None:
    try:
        Draft202012Validator(SCHEMAS[identifier], registry=REGISTRY, format_checker=FormatChecker()).validate(payload)
    except ValidationError:
        raise BusinessError("MODEL_CONTRACT_INVALID", 422) from None


class InferenceGateway:
    def __init__(
        self,
        database: Database,
        store: FileObjectStore,
        authority: AuthorityProvider | None,
        service_authority: ServiceAuthority | None,
        backends: dict[str, BackendRegistration] | None = None,
        *,
        work_authorization: WorkPort | None = None,
    ) -> None:
        self.database, self.store, self.authority, self.service_authority = (
            database,
            store,
            authority,
            service_authority,
        )
        self.backends = dict(backends or {})
        self.work_authorization = work_authorization
        if any(key != registration.capability or key not in MODELS for key, registration in self.backends.items()):
            raise ValueError("CAPABILITY_REGISTRATION_INVALID")

    def check_inputs(self, scope: Scope, payload: dict[str, Any]) -> None:
        if self.authority is None or self.authority.authorize_case(scope.actor, scope.case_id, "task.execute") != scope:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        references: set[tuple[str, str, str]] = set()
        with self.database.transaction(scope) as connection:
            task = (
                connection.execute(
                    text(
                        "SELECT asset_id,state,run_version FROM mt.analysis_task WHERE case_id=:case AND task_id=:task"
                    ),
                    dict(case=scope.case_id, task=UUID(payload["task_id"])),
                )
                .mappings()
                .one_or_none()
            )
            if task is None:
                raise BusinessError("TASK_NOT_FOUND", 404)
            if task["state"] != "RUNNING" or task["run_version"] != payload["run_version"]:
                raise BusinessError("TASK_EXECUTION_STATE_CONFLICT", 409)
            if (
                connection.execute(
                    text("SELECT 1 FROM mt.task_run WHERE case_id=:case AND task_id=:task AND run_version=:run"),
                    dict(case=scope.case_id, task=UUID(payload["task_id"]), run=payload["run_version"]),
                ).scalar_one_or_none()
                is None
            ):
                raise BusinessError("TASK_RUN_NOT_FOUND", 404)
            if payload["source_segment_ids"]:
                raise BusinessError("SEGMENT_MAPPING_ADAPTER_UNAVAILABLE", 503)
            for asset_id in payload["asset_ids"]:
                item = (
                    connection.execute(
                        text(
                            "SELECT a.*,o.version_id,o.sha256 AS object_sha,s.authorization_version FROM mt.media_asset a JOIN mt.object_version o ON o.case_id=a.case_id AND o.object_id=a.object_id JOIN mt.source_registry s ON s.case_id=a.case_id AND s.source_id=a.source_id WHERE a.case_id=:case AND a.asset_id=:asset"
                        ),
                        dict(case=scope.case_id, asset=UUID(asset_id)),
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    item is None
                    or item["state"] != "VALID"
                    or (item["asset_id"] != task["asset_id"] and item["parent_asset_id"] != task["asset_id"])
                ):
                    raise BusinessError("MODEL_ASSET_BINDING_INVALID", 422)
                if payload["input_kind"] == "analysis_copy" and (
                    item["kind"] != "derived" or item["mapping_version"] != payload["mapping_version"]
                ):
                    raise BusinessError("ANALYSIS_COPY_REQUIRED", 422)
                if payload["input_kind"] == "original_bytes" and item["kind"] != "original":
                    raise BusinessError("ORIGINAL_BYTES_REQUIRED", 422)
                if payload["input_kind"] == "decoded_original" and (
                    item["kind"] != "original"
                    or item["parent_asset_id"] is not None
                    or item["asset_id"] != task["asset_id"]
                    or item["mapping_version"] != payload["mapping_version"]
                ):
                    raise BusinessError("DECODED_ORIGINAL_BINDING_INVALID", 422)
                if item["authorization_version"] != payload["authorization_version"]:
                    raise BusinessError("MODEL_AUTHORIZATION_VERSION_STALE", 409)
                self.authority.authorize_source(scope, item["source_id"], "analysis")
                references.add((str(item["object_id"]), item["version_id"], item["object_sha"]))
        supplied = {(ref["object_id"], ref["version_id"], ref["sha256"]) for ref in payload["object_refs"]}
        if supplied != references or len(supplied) != len(payload["object_refs"]):
            raise BusinessError("MODEL_OBJECT_BINDING_INVALID", 422)
        for identifier, version, digest in references:
            try:
                for _ in self.store.read(ObjectRef(UUID(identifier), version, digest)):
                    pass
            except (OSError, ValueError, RuntimeError):
                raise BusinessError("MODEL_INPUT_OBJECT_UNAVAILABLE", 503) from None

    def execute(self, capability: str, payload: dict[str, Any], bearer: str, request_id: str | None) -> dict[str, Any]:
        if capability not in MODELS:
            raise BusinessError("CAPABILITY_NOT_SUPPORTED", 503)
        identifier, _ = MODELS[capability]
        validate_model(identifier, payload)
        if payload["capability"] != capability or (request_id is not None and request_id != payload["request_id"]):
            raise BusinessError("MODEL_REQUEST_BINDING_INVALID", 422)
        deadline = datetime.fromisoformat(payload["deadline_at"].replace("Z", "+00:00"))
        if deadline <= now():
            raise BusinessError("MODEL_DEADLINE_EXCEEDED", 504)
        if self.service_authority is None:
            raise BusinessError("SERVICE_AUTHORITY_UNAVAILABLE", 503)
        scope = self.service_authority.authorize(bearer, payload)
        if scope.case_id != UUID(payload["case_id"]):
            raise BusinessError("SERVICE_AUTHORITY_BINDING_INVALID", 503)
        backend = self.backends.get(capability)
        if backend is None:
            raise BusinessError("CAPABILITY_BACKEND_UNAVAILABLE", 503)
        if any(
            getattr(backend, name) != payload[name]
            for name in ["capability", "model_name", "model_version", "preprocessing_version", "mapping_version"]
        ):
            raise BusinessError("MODEL_VERSION_UNAVAILABLE", 503)
        task_id = UUID(payload["task_id"])
        with protected_work(self.work_authorization, scope, "task_execution", task_id, "startTaskNodeWork"):
            self.check_inputs(scope, payload)
        value = backend.backend.execute(copy.deepcopy(payload))
        # The backend can outlive the first fact interval. Obtain current work
        # evidence again; do not carry an expired ALLOW or database lock over it.
        with protected_work(self.work_authorization, scope, "task_execution", task_id, "finishTaskNodeWork"):
            return self._finish_response(scope, identifier, payload, backend, value, deadline)

    def _finish_response(
        self,
        scope: Scope,
        identifier: str,
        payload: dict[str, Any],
        backend: BackendRegistration,
        value: dict[str, Any],
        deadline: datetime,
    ) -> dict[str, Any]:
        capability = payload["capability"]
        try:
            validate_model(identifier.replace(":request:", ":response:"), value)
        except BusinessError:
            raise BusinessError("MODEL_RESPONSE_CONTRACT_INVALID", 503) from None
        if any(
            value[name] != payload[name]
            for name in [
                "request_id",
                "task_id",
                "run_version",
                "capability",
                "model_name",
                "model_version",
                "preprocessing_version",
                "mapping_version",
            ]
        ):
            raise BusinessError("MODEL_RESPONSE_BINDING_INVALID", 503)
        if value["status"] != "SUCCEEDED" and (value["findings"] or value["artifacts"]):
            raise BusinessError("FAILED_MODEL_MUST_NOT_RETURN_RESULTS", 503)
        if value["status"] == "SUCCEEDED":
            if value["mock"] or backend.release_bundle_id is None or backend.semantics is None:
                raise BusinessError("VERIFIED_MODEL_PUBLICATION_REQUIRED", 503)
            with self.database.identity_transaction(scope.actor) as connection:
                released = connection.execute(
                    text(
                        "SELECT 1 FROM mt.model_release r JOIN mt.model_registry m ON m.org_id=r.org_id AND m.model_id=r.model_id WHERE r.org_id=:org AND r.release_id=:id AND r.state='ACTIVE' AND m.name=:name AND m.version=:version AND m.capability=:capability AND m.status IN ('APPROVED','ACTIVE') AND m.license_record_ref<>''"
                    ),
                    dict(
                        org=scope.actor.org_id,
                        id=backend.release_bundle_id,
                        name=backend.model_name,
                        version=backend.model_version,
                        capability=capability,
                    ),
                ).scalar_one_or_none()
            if released is None:
                raise BusinessError("VERIFIED_MODEL_PUBLICATION_REQUIRED", 503)
            backend.semantics.validate(scope, payload, value)
        if deadline <= now():
            raise BusinessError("MODEL_DEADLINE_EXCEEDED", 504)
        self.check_inputs(scope, payload)  # Cancellation and source revocation can occur while the backend runs.
        with self.database.transaction(scope) as connection:
            for ref in value["artifacts"]:
                exists = connection.execute(
                    text(
                        "SELECT 1 FROM mt.object_version WHERE case_id=:case AND object_id=:id AND version_id=:version AND sha256=:sha"
                    ),
                    dict(case=scope.case_id, id=UUID(ref["object_id"]), version=ref["version_id"], sha=ref["sha256"]),
                ).scalar_one_or_none()
                if exists is None:
                    raise BusinessError("MODEL_ARTIFACT_BINDING_INVALID", 503)
                try:
                    for _ in self.store.read(ObjectRef(UUID(ref["object_id"]), ref["version_id"], ref["sha256"])):
                        pass
                except (OSError, ValueError, RuntimeError):
                    raise BusinessError("MODEL_ARTIFACT_UNAVAILABLE", 503) from None
        return value


@router.post("/inference/{capability}", operation_id="internalInference")
def inference(request: Request, capability: str, body: dict[str, Any]) -> JSONResponse:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer ") or not authorization[7:]:
        raise BusinessError("SERVICE_AUTHENTICATION_REQUIRED", 401)
    gateway = cast(InferenceGateway, request.app.state.inference_gateway)
    header_id = request.headers.get("X-Request-Id") if request.state.client_request_id_provided else None
    try:
        request.state.request_id = UUID(body["request_id"])
    except (KeyError, ValueError, TypeError):
        raise BusinessError("MODEL_REQUEST_BINDING_INVALID", 422) from None
    return JSONResponse(gateway.execute(capability, body, authorization[7:], header_id))
