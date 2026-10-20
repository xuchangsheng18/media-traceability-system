import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import Connection, text

from ..auth import authenticated_actor, authorize_request
from ..contracts import validate_response
from ..cursor_encoding import decode_cursor
from ..data_scope import ResourceBinding, TaskBinding
from ..db import Database
from ..errors import BusinessError
from ..scope_collections import COLLECTION_TABLES, CollectionScope, bind_task_scope, require_resource, require_root
from ..scope_context import current_data_scope
from ..types import Actor, Scope


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def etag(value: Any) -> str:
    return '"' + hashlib.sha256(canonical(value)).hexdigest() + '"'


def match(request: Request, value: Any) -> None:
    condition = request.headers.get("If-Match")
    if not condition:
        raise BusinessError("PRECONDITION_REQUIRED", 428)
    if condition != etag(value):
        raise BusinessError("PRECONDITION_FAILED", 412)


def reply(name: str, value: dict[str, Any], status: int = 200, version: Any = None) -> JSONResponse:
    validate_response(name, value)
    return JSONResponse(value, status_code=status, headers={"ETag": etag(value if version is None else version)})


def actor_for(request: Request) -> Actor:
    return authenticated_actor(request)


RESOURCE_TABLES = {
    "approval": ("approval_request", "approval_id"),
    "review": ("review_record", "review_id"),
    "export": ("audit_export", "export_id"),
    "feedback": ("feedback_request", "feedback_id"),
    "source": ("source_registry", "source_id"),
    "import": ("import_job", "import_id"),
    "task": ("analysis_task", "task_id"),
}


def resource_scope(request: Request, kind: str, resource_id: UUID, action: str) -> Scope:
    actor = actor_for(request)
    database = cast(Database, request.app.state.business_database)
    table, key = RESOURCE_TABLES[kind]
    with database.identity_transaction(actor) as connection:
        case_id = connection.execute(
            text(f"SELECT case_id FROM mt.{table} WHERE {key}=:id"), {"id": resource_id}
        ).scalar_one_or_none()
    if case_id is None:
        raise BusinessError("RESOURCE_NOT_FOUND", 404)
    scope = authorize_request(request, case_id, action)
    if scope.actor != actor:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    return scope


def row(
    connection: Connection, table: str, key: str, identifier: UUID, lock: bool = False, *, shared: bool = False
) -> dict[str, Any]:
    root_scope = current_data_scope()
    kind = next((kind for kind, pair in RESOURCE_TABLES.items() if pair == (table, key)), None)
    if kind is not None:
        require_resource(connection, root_scope, kind, identifier)
    else:
        require_root(connection, root_scope)
    result = (
        connection.execute(
            text(
                f"SELECT * FROM mt.{table} WHERE {key}=:id"
                + (" FOR SHARE" if shared else " FOR UPDATE" if lock else "")
            ),
            {"id": identifier},
        )
        .mappings()
        .one_or_none()
    )
    if result is None:
        raise BusinessError("RESOURCE_NOT_FOUND", 404)
    return dict(result)


def audit(
    connection: Connection, scope: Scope, action: str, kind: str, identifier: UUID, version: int, request: Request
) -> None:
    try:
        request_id = UUID(request.headers.get("X-Request-Id", ""))
    except ValueError:
        request_id = uuid4()
    connection.execute(
        text("""INSERT INTO mt.audit_event(event_id,org_id,case_id,actor_id,action,object_type,object_id,object_version,outcome,request_id,occurred_at,created_by)
        VALUES(:id,:org,:case,:actor,:action,:kind,:object,:version,'allowed',:request,now(),:actor)"""),
        dict(
            id=uuid4(),
            org=scope.actor.org_id,
            case=scope.case_id,
            actor=scope.actor.user_id,
            action=action,
            kind=kind,
            object=identifier,
            version=version,
            request=request_id,
        ),
    )


def page(
    connection: Connection,
    table: str,
    key: str,
    scope: Scope,
    secret: str,
    cursor: str | None,
    limit: int,
    *,
    where: str = "case_id=:case",
    filters: dict[str, Any] | None = None,
    version_expression: str = "row_version::text",
    collection: CollectionScope | None = None,
    bind_visibility: bool = False,
) -> tuple[list[dict[str, Any]], str | None]:
    # Identifiers and predicates are exclusively internal constants, never client SQL.
    params: dict[str, Any] = dict(case=scope.case_id, org=scope.actor.org_id, **(filters or {}))
    if table == "task_event":
        if filters is None or not isinstance(filters.get("task"), UUID) or type(filters.get("run")) is not int:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        bind_task_scope(connection, current_data_scope(), TaskBinding(filters["task"], filters["run"]))
    candidates: tuple[ResourceBinding, ...] = ()
    visibility: tuple[UUID, ...] = ()
    cursor_filters = dict(filters or {})
    fingerprint = None
    kind = next((name for name, pair in COLLECTION_TABLES.items() if pair == (table, key)), None)
    if kind is not None:
        if collection is None:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        columns = key + ",row_version" + (",task_id,run_version,result_version" if kind == "review" else "")
        candidate_rows = (
            connection.execute(text(f"SELECT {columns} FROM mt.{table} WHERE {where} ORDER BY {key}"), params)
            .mappings()
            .all()
        )
        candidates = tuple(
            ResourceBinding(
                kind,
                item[key],
                int(item["row_version"]),
                TaskBinding(item["task_id"], int(item["run_version"]), int(item["result_version"]))
                if kind == "review"
                else None,
            )
            for item in candidate_rows
        )
        visibility = collection.allowed_ids(connection, current_data_scope(), candidates)
        fingerprint = collection.fingerprint
        filters = dict(filters or {}, scope_allowed=list(visibility), scope_visibility=fingerprint)
        params.update(filters)
        where = f"({where}) AND {key}=ANY(CAST(:scope_allowed AS uuid[]))"
    signature = connection.execute(
        text(
            f"SELECT encode(sha256(convert_to(coalesce(string_agg({key}::text||':'||({version_expression}),',' ORDER BY {key}),''),'UTF8')),'hex') FROM mt.{table} WHERE {where}"
        ),
        params,
    ).scalar_one()
    if collection is not None:
        signature = hashlib.sha256(canonical([signature, fingerprint])).hexdigest()
    binding = canonical(
        [
            table,
            str(scope.actor.user_id),
            str(scope.actor.org_id),
            str(scope.case_id),
            where,
            version_expression,
            {k: str(v) for k, v in cursor_filters.items()},
            limit,
            *([fingerprint] if bind_visibility else []),
        ]
    )
    after: UUID | None = None
    if cursor:
        try:
            raw = decode_cursor(cursor, padded=False)
            if len(raw) != 80 or not hmac.compare_digest(
                raw[48:], hmac.new(secret.encode(), binding + raw[:48], hashlib.sha256).digest()
            ):
                raise ValueError()
            if raw[16:48].hex() != signature:
                raise BusinessError("PAGE_CURSOR_STALE", 409)
            after = UUID(bytes=raw[:16])
        except (ValueError, TypeError):
            raise BusinessError("PAGE_CURSOR_INVALID", 422) from None
    params.update(after=after, limit=limit + 1)
    rows = (
        connection.execute(
            text(
                f"SELECT * FROM mt.{table} WHERE {where} AND (CAST(:after AS uuid) IS NULL OR {key}>CAST(:after AS uuid)) ORDER BY {key} LIMIT :limit"
            ),
            params,
        )
        .mappings()
        .all()
    )
    checked = connection.execute(
        text(
            f"SELECT encode(sha256(convert_to(coalesce(string_agg({key}::text||':'||({version_expression}),',' ORDER BY {key}),''),'UTF8')),'hex') FROM mt.{table} WHERE {where}"
        ),
        params,
    ).scalar_one()
    if collection is not None:
        checked = hashlib.sha256(canonical([checked, fingerprint])).hexdigest()
    if checked != signature:
        raise BusinessError("PAGE_CURSOR_STALE", 409)
    if collection is not None and kind is not None:
        refreshed = collection.allowed_ids(connection, current_data_scope(), candidates)
        if refreshed != visibility or collection.fingerprint != fingerprint:
            raise BusinessError("AUTHORIZATION_CHANGED", 503)
    items = [dict(item) for item in rows[:limit]]
    following = None
    if len(rows) > limit:
        raw = UUID(str(items[-1][key])).bytes + bytes.fromhex(signature)
        following = (
            base64.urlsafe_b64encode(raw + hmac.new(secret.encode(), binding + raw, hashlib.sha256).digest())
            .decode()
            .rstrip("=")
        )
    return items, following


def now() -> datetime:
    return datetime.now(timezone.utc)
