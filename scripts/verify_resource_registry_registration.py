"""A bounded four-route successor; past role and report evidence stays immutable."""

import ast
import hashlib
import json
from pathlib import Path

MATRIX = "docs/08-security/t014-interface-scope-matrix.json"
PRIOR = "docs/08-security/history/resource-registry-predecessor-scope-matrix.json"
REGISTRATION = "docs/08-security/resource-registry-route-registration.json"
PRIOR_SHA256 = "26e01f9de0417ec0b41371fea860729b5a0bf7c06d161099e025a7253d1798f0"
OPERATIONS = {
    "downloadAsset": ("asset_download_router.py", "download_asset", "get", "/assets/{id}/content"),
    "createSource": ("source_registration_router.py", "create_source", "post", "/sources"),
    "listModels": ("model_catalog_router.py", "list_models", "get", "/models"),
    "listEvaluations": ("model_catalog_router.py", "list_evaluations", "get", "/model-evaluations"),
}


def same(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def registered_row(root: Path, operation: str, old: dict) -> dict:
    file, name, method, path = OPERATIONS[operation]
    source = "backend/business_app/" + file
    tree = ast.parse((root / source).read_text("utf8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(functions) == 1
    function = functions[0]
    assert len(function.decorator_list) == 1
    decorator = function.decorator_list[0]
    assert isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
    assert isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "router"
    assert decorator.func.attr == method
    assert [ast.literal_eval(value) for value in decorator.args] == [path]
    keywords = {item.arg: ast.literal_eval(item.value) for item in decorator.keywords}
    assert keywords == dict(operation_id=operation, **({"status_code": 201} if operation == "createSource" else {}))
    assert old["runtime_route"] is None
    return dict(
        old,
        runtime_route=dict(
            source=source,
            function=name,
            line=function.lineno,
            method=method.upper(),
            path=path,
            guard_expressions=["authorize_business_route", "Database request transaction with per-object conditions"],
        ),
        runtime_state="MOUNTED_SOURCE_PENDING_ISOLATED_VALIDATION",
        resource_scope_resolution="Authenticated organization and exact server-resolved case/object or organization metadata collection; client claims cannot expand scope.",
        current_guard_review="Function eligibility, exact bound institutional facts and transaction-end revalidation; absent authority remains denied. Actual isolated results are recorded separately.",
    )


def increment() -> dict:
    return dict(
        status="SOURCE_ROUTE_REGISTRATION_ONLY_NOT_RUNTIME_ACCEPTANCE",
        previous_mounted_operations=47,
        previous_unmounted_operations=26,
        added_operations=list(OPERATIONS),
        mounted_operations=51,
        unmounted_operations=22,
        formal_approved=False,
        shared_services_adopted=False,
        registration_ref=REGISTRATION,
    )


def registration(current_raw: bytes) -> dict:
    return dict(
        status="SOURCE_ROUTE_REGISTRATION_ONLY_NOT_POLICY_ADOPTION",
        scope=list(OPERATIONS),
        source_bindings={
            MATRIX: dict(
                prior_sha256=PRIOR_SHA256, prior_copy=PRIOR, current_sha256=hashlib.sha256(current_raw).hexdigest()
            )
        },
        role_cells_changed=False,
        formal_allow=False,
        shared_adopted=False,
        current_bytes_hash_convention="UTF8_text_normalized_to_LF_equal_to_staged_Git_blob_bytes",
    )


def verify_resource_registry_registration(root: Path) -> Path:
    previous_path = root / PRIOR
    previous_raw = previous_path.read_bytes()
    assert hashlib.sha256(previous_raw).hexdigest() == PRIOR_SHA256
    current_raw = (root / MATRIX).read_bytes().replace(b"\r\n", b"\n")
    assert same(json.loads((root / REGISTRATION).read_text("utf8")), registration(current_raw))
    previous, current = json.loads(previous_raw), json.loads(current_raw)
    assert same(current.pop("resource_registry_increment"), increment())
    for index, old in enumerate(previous["operations"]):
        operation = old["operation_id"]
        if operation in OPERATIONS:
            assert same(current["operations"][index], registered_row(root, operation, old))
            current["operations"][index] = old
    assert same(current, previous)
    assert len(previous["operations"]) == 73
    assert sum(row["runtime_route"] is not None for row in previous["operations"]) == 47
    return previous_path
