"""Default protection for the exact canonical business operations."""

import hashlib
import hmac
import re
import time
from collections.abc import Callable, Mapping
from typing import cast

from fastapi import FastAPI, Request
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, iter_route_contexts

from ..errors import BusinessError
from .catalog import OperationPermission
from .policy import validate_principal
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


def authorize_business_route(request: Request) -> None:
    route = request.scope.get("route")
    catalog = cast(Mapping[str, OperationPermission], request.app.state.permission_catalog)
    operation = catalog.get(getattr(route, "operation_id", ""))
    if operation is None or operation.path != getattr(route, "path_format", None) or operation.method != request.method:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    if not operation.public:
        require_permission(operation.permission)(request)


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
