"""Architectural guard: business byte callers cannot bypass the scoped port."""

import ast
from pathlib import Path

from business_app.errors import BusinessError

ROOT = Path(__file__).resolve().parents[2]


def test_business_byte_callers_use_the_scoped_object_port():
    forbidden = []
    for path in sorted((ROOT / "backend/business_app").rglob("*.py")):
        if path.name in {"objects.py", "scoped_objects.py"}:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf8"))):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            if node.func.attr in {"read", "put_part"} and isinstance(owner, ast.Attribute) and owner.attr == "store":
                forbidden.append(f"{path.relative_to(ROOT).as_posix()}:{node.lineno}")
    assert not forbidden, f"BUSINESS_BYTE_SCOPE_BYPASS: {forbidden}"


def test_scoped_object_errors_preserve_the_registered_public_error_contract():
    path = ROOT / "backend/business_app/scoped_objects.py"
    invalid = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf8"))):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "BusinessError":
            continue
        code, status = [ast.literal_eval(argument) for argument in node.args]
        try:
            error = BusinessError(code, status)
            assert error.code == code and error.http_status == status
        except ValueError:
            invalid.append((code, status))
    assert not invalid, f"UNREGISTERED_PUBLIC_ERRORS: {invalid}"
