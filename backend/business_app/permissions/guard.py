"""Default protection for the exact canonical business operations."""

import hashlib
import hmac
import json
import re
import time
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import nullcontext
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, iter_route_contexts
from starlette.concurrency import run_in_threadpool

from ..errors import BusinessError
from .catalog import OperationPermission
from .conditional import ConditionalPort
from .context import FencePort, request_authorization
from .object_facts import BODY_SCHEMAS
from .policy import validate_principal
from .rule_types import AuthorizationEvidence, RuleTarget
from .task_creation_context import bind_task_creation_context, freeze_task_creation_context
from .types import PermissionAuthority, Principal


def authorization(request: Request) -> tuple[str, str]:
    values = request.headers.getlist("Authorization")
    match = re.fullmatch(r"(?i:Bearer) +([A-Za-z0-9._~+/-]+=*)", values[0]) if len(values) == 1 else None
    if match is None:
        raise BusinessError("AUTHENTICATION_REQUIRED", 401)
    return values[0], match[1]


def current_principal(request: Request) -> Principal:
    header, _ = authorization(request)
    principal = getattr(request.state, "business_principal", None)
    binding = getattr(request.state, "business_authorization_binding", None)
    if not isinstance(principal, Principal) or not isinstance(binding, bytes):
        raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
    if not hmac.compare_digest(binding, hashlib.sha256(header.encode("utf8")).digest()):
        raise BusinessError("AUTHENTICATION_REQUIRED", 401)
    validate_principal(principal, time.time)
    return principal


def authenticate_principal(request: Request) -> Principal:
    header, token = authorization(request)
    if getattr(request.state, "business_principal", None) is not None:
        return current_principal(request)
    authority = getattr(request.app.state, "business_authority", None)
    method = getattr(authority, "authenticate_principal", None)
    if not callable(method):
        raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
    try:
        principal = method(token)
    except BusinessError:
        raise
    except Exception:
        raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
    validate_principal(principal, time.time)
    request.state.business_principal = principal
    request.state.business_authorization_binding = hashlib.sha256(header.encode("utf8")).digest()
    return cast(Principal, principal)


def require_permission(permission_code: str) -> Callable[[Request], None]:
    def required(request: Request) -> None:
        catalog = cast(Mapping[str, OperationPermission], request.app.state.permission_catalog)
        if permission_code not in {operation.permission for operation in catalog.values()}:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        principal = authenticate_principal(request)
        authority = cast(PermissionAuthority | None, request.app.state.permission_authority)
        if authority is None:
            raise BusinessError("FORMAL_POLICY_UNCONFIGURED", 503)
        try:
            check = cast(Callable[[Principal, str], object], authority.check)
            result = check(principal, permission_code)
        except BusinessError:
            raise
        except Exception:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        validate_principal(principal, time.time)
        if result is not None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)

    return required


def _unique_task_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("INPUT_INVALID")
        result[name] = value
    return result


def _invalid_task_constant(_value: str) -> None:
    raise ValueError("INPUT_INVALID")


async def _task_body(request: Request) -> dict[str, Any]:
    # Read multiplicity before flattening; no new key grammar or budget is
    # invented here. TaskCreate still supplies exactly its original six fields.
    keys = request.headers.getlist("Idempotency-Key")
    if request.scope.get("query_string") or len(keys) != 1 or not 1 <= len(keys[0]) <= 128:
        raise BusinessError("INPUT_INVALID", 422)
    try:
        value = json.loads(
            (await request.body()).decode("utf8"),
            object_pairs_hook=_unique_task_fields,
            parse_constant=_invalid_task_constant,
        )
        if type(value) is not dict:
            raise ValueError()
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise BusinessError("INPUT_INVALID", 422) from None


async def authorize_business_route(request: Request) -> AsyncIterator[None]:
    route = request.scope.get("route")
    catalog = cast(Mapping[str, OperationPermission], request.app.state.permission_catalog)
    operation = catalog.get(getattr(route, "operation_id", ""))
    if operation is None or operation.path != getattr(route, "path_format", None) or operation.method != request.method:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    if not operation.public:
        await run_in_threadpool(require_permission(operation.permission), request)
        if operation.operation_id in {
            "getAsset",
            "getReport",
            "downloadAsset",
            "createSource",
            "listAssets",
            "listTasks",
            "listModels",
            "listEvaluations",
        }:
            # Never flatten ambiguous catalog scope into a different case before
            # authorization. Function/identity denials still precede parsing.
            allowed = (
                {"case_id", "limit", "cursor"}
                if operation.operation_id in {"listAssets", "listTasks"}
                else {"limit", "cursor"}
                if operation.operation_id in {"listModels", "listEvaluations"}
                else set()
            )
            values = request.query_params
            if set(values) - allowed or any(len(values.getlist(key)) != 1 for key in values):
                raise BusinessError("READ_PARAMETER_UNSUPPORTED", 422)
        conditional = cast(ConditionalPort | None, getattr(request.app.state, "conditional_permissions", None))
        if conditional is None:
            raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
        principal = current_principal(request)
        body = {}
        if operation.operation_id == "createTask":
            body = await _task_body(request)
        elif operation.operation_id in BODY_SCHEMAS:
            try:
                body = await request.json()
            except (ValueError, UnicodeError):
                raise BusinessError("INPUT_INVALID", 422) from None
            if not isinstance(body, dict):
                raise BusinessError("INPUT_INVALID", 422)
        context = freeze_task_creation_context(principal, body) if operation.operation_id == "createTask" else None
        # Bind in the parent async task. Conditional threadpool readers and the
        # eventual sync handler/fence inherit it; all exits restore its token.
        with bind_task_creation_context(context) if context is not None else nullcontext():
            try:
                evidence = await run_in_threadpool(
                    conditional.authorize_http,
                    principal,
                    operation.operation_id,
                    dict(request.path_params),
                    dict(request.query_params),
                    body,
                )
            except BusinessError:
                raise
            except Exception:
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503) from None
            if (
                not isinstance(evidence, AuthorizationEvidence)
                or evidence.principal != principal
                or evidence.operation_id != operation.operation_id
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            if context is not None:
                target = evidence.target
                if (
                    type(target) is not RuleTarget
                    or target.org_id != context.principal.actor.org_id
                    or target.kind != "asset"
                    or target.object_id != context.request.asset_id
                    or target.case_id != context.request.case_id
                    or target.purpose != "analysis"
                    or type(target.object_version) is not int
                    or target.object_version < 1
                    or target.request_digest != context.authorization_request_digest
                ):
                    raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            current_principal(request)
            request.state.business_authorization_evidence = evidence
            fence = cast(FencePort | None, getattr(request.app.state, "authorization_fence", None))
            with request_authorization(evidence, fence, mutation=request.method != "GET"):
                yield
    else:
        yield


def audit_protected_routes(app: FastAPI) -> None:
    """Use FastAPI's effective contexts, including inherited router dependencies."""
    catalog = cast(Mapping[str, OperationPermission], app.state.permission_catalog)
    framework = cast(frozenset[int], app.state.permission_framework_routes)
    seen: set[str] = set()
    seen_framework: set[int] = set()
    internal_count = 0
    invalid = "PERMISSION_ROUTE_COVERAGE_INVALID"
    if authorize_business_route in app.dependency_overrides:
        raise RuntimeError(invalid)
    for context in iter_route_contexts(app.routes):
        original = context.original_route
        path = context.path_format or context.path
        if id(original) in framework:
            if id(original) in seen_framework or path != getattr(original, "path", None):
                raise RuntimeError(invalid)
            seen_framework.add(id(original))
            continue
        if not isinstance(original, APIRoute):
            raise RuntimeError(invalid)
        identifier = getattr(context, "operation_id", None)
        methods = context.methods or set()
        if path == "/internal/v1/inference/{capability}" and identifier == "internalInference" and methods == {"POST"}:
            internal_count += 1
            if internal_count > 1:
                raise RuntimeError(invalid)
            continue
        operation = catalog.get(identifier) if isinstance(identifier, str) else None
        if (
            operation is None
            or operation.operation_id in seen
            or operation.path != path
            or methods != {operation.method}
        ):
            raise RuntimeError(invalid)
        seen.add(operation.operation_id)
        if operation.public:
            if app.state.business_settings.runtime_profile != "development":
                raise RuntimeError(invalid)
            continue
        dependant = getattr(context, "dependant", None)
        if not isinstance(dependant, Dependant) or not any(
            item.call is authorize_business_route for item in dependant.dependencies
        ):
            raise RuntimeError(invalid)
    if seen_framework != set(framework) or internal_count != 1:
        raise RuntimeError(invalid)
