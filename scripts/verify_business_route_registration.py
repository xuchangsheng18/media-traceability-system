"""Verify the exact report-read source registration without changing past evidence."""

import ast
import hashlib
import json
from pathlib import Path

from scripts.verify_resource_registry_registration import verify_resource_registry_registration

MATRIX = "docs/08-security/t014-interface-scope-matrix.json"
PRIOR = "docs/08-security/history/report-read-predecessor-scope-matrix.json"
REGISTRATION = "docs/08-security/report-read-route-registration.json"
PRIOR_SHA256 = "78681bf5dcb434eef9ec12fa12e79ee2d258c325016a6cbc6f324ac7596d03c1"


def _same(left: object, right: object) -> bool:
    # JSON booleans must not compare equal to Python's integer 0/1.
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def verify_business_route_registration(root: Path) -> Path:
    """Return the original catalog-adopted matrix only after validating its successor."""
    try:
        previous_path = root / PRIOR
        assert previous_path.resolve().is_relative_to(root.resolve())
        previous_raw = previous_path.read_bytes()
        current_raw = verify_resource_registry_registration(root).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(previous_raw).hexdigest() == PRIOR_SHA256
        record = json.loads((root / REGISTRATION).read_text("utf8"))
        expected_record = dict(
            status="SOURCE_ROUTE_REGISTRATION_ONLY_NOT_POLICY_ADOPTION",
            scope=["getReport"],
            source_bindings={
                MATRIX: dict(
                    prior_sha256=PRIOR_SHA256,
                    prior_copy=PRIOR,
                    current_sha256=hashlib.sha256(current_raw).hexdigest(),
                )
            },
            role_cells_changed=False,
            formal_allow=False,
            shared_adopted=False,
            current_bytes_hash_convention="UTF8_text_normalized_to_LF_equal_to_staged_Git_blob_bytes",
        )
        assert _same(record, expected_record)
        previous = json.loads(previous_raw)
        current = json.loads(current_raw)
        expected_increment = dict(
            status="SOURCE_ROUTE_REGISTRATION_ONLY_NOT_RUNTIME_ACCEPTANCE",
            previous_mounted_operations=46,
            previous_unmounted_operations=27,
            added_operations=["getReport"],
            mounted_operations=47,
            unmounted_operations=26,
            formal_approved=False,
            shared_services_adopted=False,
            registration_ref=REGISTRATION,
        )
        assert _same(current.pop("report_read_increment"), expected_increment)
        route_source = "backend/business_app/registry_router.py"
        tree = ast.parse((root / route_source).read_text("utf8"))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "get_report"]
        assert len(functions) == 1
        function = functions[0]
        assert len(function.decorator_list) == 1
        decorator = function.decorator_list[0]
        assert isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
        assert isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "router"
        assert decorator.func.attr == "get"
        assert [ast.literal_eval(argument) for argument in decorator.args] == ["/reports/{id}"]
        assert {item.arg: ast.literal_eval(item.value) for item in decorator.keywords} == {"operation_id": "getReport"}
        index = next(i for i, row in enumerate(previous["operations"]) if row["operation_id"] == "getReport")
        old = previous["operations"][index]
        assert old["runtime_route"] is None
        expected = dict(old)
        expected.update(
            runtime_route=dict(
                source=route_source,
                function="get_report",
                line=function.lineno,
                method="GET",
                path="/reports/{id}",
                guard_expressions=[
                    "authorize_business_route",
                    "Database request transaction with per-object conditions",
                ],
            ),
            runtime_state="MOUNTED_SOURCE_PENDING_ISOLATED_VALIDATION",
            resource_scope_resolution="Server resolves the report case and exact persisted report version; client scope claims cannot expand access.",
            current_guard_review="Unified authentication/function/object conditions, exact report/task/result binding, source/read purpose/classification, and transaction-end revalidation; runtime results recorded separately.",
        )
        assert _same(current["operations"][index], expected)
        current["operations"][index] = old
        assert _same(current, previous)
        assert len(previous["operations"]) == 73
        assert sum(row["runtime_route"] is not None for row in previous["operations"]) == 46
        return previous_path
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, SyntaxError, AssertionError):
        raise AssertionError("ROUTE_REGISTRATION_INVALID") from None


if __name__ == "__main__":
    verify_business_route_registration(Path(__file__).resolve().parents[1])
    print(json.dumps(dict(status="PASS_SCOPE_REGISTRATION_ONLY", added_operations=["getReport"], formal_allow=False)))
