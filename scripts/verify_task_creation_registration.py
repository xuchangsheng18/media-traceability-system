"""Strict one-route successor: source registration is not adoption or acceptance."""

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

MATRIX = "docs/08-security/t014-interface-scope-matrix.json"
PRIOR = "docs/08-security/history/task-creation-predecessor-scope-matrix.json"
REGISTRATION = "docs/08-security/task-creation-route-registration.json"


def registered_row(root: Path, old: dict[str, Any]) -> dict[str, Any]:
    source = "backend/business_app/task_creation_router.py"
    tree = ast.parse((root / source).read_text("utf8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "create_task"]
    assert len(functions) == 1
    function = functions[0]
    assert len(function.decorator_list) == 1
    decorator = function.decorator_list[0]
    assert isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
    assert isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "router"
    assert decorator.func.attr == "post"
    assert [ast.literal_eval(item) for item in decorator.args] == ["/analysis/tasks"]
    assert {item.arg: ast.literal_eval(item.value) for item in decorator.keywords} == dict(
        status_code=202, operation_id="createTask"
    )
    assert old["runtime_route"] is None
    return dict(
        old,
        runtime_route=dict(
            source=source,
            function="create_task",
            line=function.lineno,
            method="POST",
            path="/analysis/tasks",
            guard_expressions=["authorize_business_route", "Database request transaction with per-object conditions"],
        ),
        runtime_state="MOUNTED_SOURCE_PENDING_ISOLATED_VALIDATION",
        resource_scope_resolution="Exact authenticated actor/organization/case/asset and frozen request; explicit current facts and materials only.",
        current_guard_review="Unified function and object guard plus atomic createTask service and commit fence; missing providers or budgets never allow acceptance.",
    )


def increment() -> dict[str, Any]:
    return dict(
        status="SOURCE_ROUTE_REGISTRATION_ONLY_NOT_RUNTIME_ACCEPTANCE",
        previous_mounted_operations=51,
        previous_unmounted_operations=22,
        added_operations=["createTask"],
        mounted_operations=52,
        unmounted_operations=21,
        formal_approved=False,
        shared_services_adopted=False,
        registration_ref=REGISTRATION,
    )


def verify_task_creation_registration(root: Path) -> Path:
    # This exact predecessor is separately bound by the earlier registry delta.
    previous_raw = (root / PRIOR).read_bytes().replace(b"\r\n", b"\n")
    current_raw = (root / MATRIX).read_bytes().replace(b"\r\n", b"\n")
    previous, current = json.loads(previous_raw), json.loads(current_raw)
    expected = dict(
        status="SOURCE_ROUTE_REGISTRATION_ONLY_NOT_POLICY_ADOPTION",
        scope=["createTask"],
        prior_copy=PRIOR,
        prior_sha256=hashlib.sha256(previous_raw).hexdigest(),
        current_sha256=hashlib.sha256(current_raw).hexdigest(),
        role_cells_changed=False,
        formal_allow=False,
        shared_adopted=False,
    )
    assert json.dumps(json.loads((root / REGISTRATION).read_text("utf8")), sort_keys=True) == json.dumps(
        expected, sort_keys=True
    )
    assert json.dumps(current.pop("task_creation_increment"), sort_keys=True) == json.dumps(increment(), sort_keys=True)
    for index, old in enumerate(previous["operations"]):
        if old["operation_id"] == "createTask":
            assert json.dumps(current["operations"][index], sort_keys=True) == json.dumps(
                registered_row(root, old), sort_keys=True
            )
            current["operations"][index] = old
    assert json.dumps(current, sort_keys=True) == json.dumps(previous, sort_keys=True)
    assert len(previous["operations"]) == 73
    assert sum(row["runtime_route"] is not None for row in previous["operations"]) == 51
    return root / PRIOR
