"""Run scoped identity checks and publish counts, never raw token-bearing logs."""

import argparse
import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GROUPS = {
    "identity-live.xml": ["tests/identity"],
    "identity-adapters.xml": [
        "tests/platform/test_t013_tokens.py",
        "tests/platform/test_t013_identity_config.py",
        "tests/platform/test_t013_identity_operations.py",
        "tests/platform/test_t013_identity_deploy.py",
        "tests/platform/test_t013_identity_checks.py",
        "tests/platform/test_t013_recovery_guard.py",
        "tests/platform/test_t013_privacy_audit.py",
        "tests/platform/test_t013_handover.py",
        "tests/platform/test_t013_management.py",
    ],
    "identity-mapping.xml": [
        "tests/business/test_token_identity.py",
        "tests/business/test_identity_directory.py",
        "tests/business/test_role_directory.py",
    ],
}
FIELDS = ("tests", "failures", "errors", "skipped")
GROUP_TIMEOUTS = {"identity-live.xml": 1800, "identity-adapters.xml": 900, "identity-mapping.xml": 900}
READINESS_CASE = ("tests.identity.test_recovery_live", "test_restart_and_database_dependency_readiness")
READINESS_MISSING_ERROR = "RECOVERY_LAB_READINESS_BUSINESS_ERROR_NOT_RAISED"


def readiness_diagnostic_codes() -> set[str]:
    """Load only the target assertions and the existing dependency timeout raise."""
    tree = ast.parse((ROOT / "tests/identity/test_recovery_live.py").read_text(encoding="utf-8"))
    codes = {
        node.msg.value
        for function in tree.body
        if isinstance(function, ast.FunctionDef) and function.name == READINESS_CASE[1]
        for node in ast.walk(function)
        if isinstance(node, ast.Assert)
        and isinstance(node.msg, ast.Constant)
        and isinstance(node.msg.value, str)
        and re.fullmatch(r"RECOVERY_LAB_READINESS_[A-Z][A-Z0-9_]*[A-Z0-9]", node.msg.value)
    }
    lab = ast.parse((ROOT / "tests/identity/recovery_lab.py").read_text(encoding="utf-8"))
    codes.update(
        node.exc.args[0].value
        for definition in lab.body
        if isinstance(definition, ast.ClassDef) and definition.name == "RecoveryLab"
        for method in definition.body
        if isinstance(method, ast.FunctionDef) and method.name == "wait_dependency_down"
        for node in ast.walk(method)
        if isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id == "AssertionError"
        and len(node.exc.args) == 1
        and isinstance(node.exc.args[0], ast.Constant)
        and node.exc.args[0].value == "KEYCLOAK_READINESS_DID_NOT_DETECT_DATABASE_FAILURE"
    )
    return codes


def readiness_failure_code(problem: ET.Element | None, codes: set[str]) -> str | None:
    """Recognize observed pytest call-failure shapes, never arbitrary payload words."""
    if problem is None or problem.tag != "failure" or "type" in problem.attrib:
        return None
    first = problem.get("message", "").split("\n", 1)[0]
    if first == "Failed: DID NOT RAISE BusinessError":
        return READINESS_MISSING_ERROR
    prefix = "AssertionError: "
    if first.startswith(prefix) and first[len(prefix) :] in codes:
        return first[len(prefix) :]
    return None


def private_root(path: Path) -> Path:
    path = path.absolute()
    if any(p.is_symlink() for p in [path, *path.parents]) or path.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("IDENTITY_PRIVATE_TEST_ROOT_REQUIRED")
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.stat().st_mode & 0o077 or path.stat().st_uid != os.geteuid():
        raise RuntimeError("IDENTITY_PRIVATE_TEST_ROOT_REQUIRED")
    return path


def junit_counts(path: Path) -> dict[str, int]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32 * 1024**2:
        raise ValueError("MISSING_OR_INVALID_JUNIT")
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise ValueError("MISSING_OR_INVALID_JUNIT")
    root = ET.fromstring(raw)
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    if not suites:
        raise ValueError("MISSING_OR_INVALID_JUNIT")
    totals = dict.fromkeys(FIELDS, 0)
    for suite in suites:
        counts = {k: int(suite.attrib[k]) for k in FIELDS}
        cases = suite.findall("testcase")
        actual = {
            "tests": len(cases),
            **{k: sum(c.find(k[:-1] if k != "skipped" else k) is not None for c in cases) for k in FIELDS[1:]},
        }
        if any(n < 0 for n in counts.values()) or counts != actual:
            raise ValueError("INCONSISTENT_JUNIT")
        for key in FIELDS:
            totals[key] += counts[key]
    return totals


def source_hashes() -> dict[str, str]:
    paths = [
        p
        for folder in ["backend/business_app/identity", "scripts/identity", "tests/identity"]
        for p in (ROOT / folder).glob("*.py")
    ]
    paths += [
        ROOT / p
        for p in [
            "tests/platform/test_t013_identity_checks.py",
            "tests/platform/test_t013_identity_operations.py",
            "tests/platform/test_t013_recovery_guard.py",
            "tests/platform/test_t013_privacy_audit.py",
            "tests/platform/test_t013_handover.py",
            "tests/platform/test_t013_management.py",
            "deploy/identity/Dockerfile.keycloak",
            "deploy/identity/compose.yaml",
            "deploy/identity/nginx.conf",
            "scripts/__init__.py",
            "scripts/stage_three_types.py",
            "tools/identity_oidc_probe.py",
            "tools/identity_oidc_browser.mjs",
            "tools/identity_admin_tokens.mjs",
            "config/identity/versions.json",
            ".github/workflows/identity.yml",
            ".github/workflows/ci.yml",
            "config/stage-three-profile.json",
        ]
        if (ROOT / p).is_file()
    ]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def safe_failed_cases(path: Path) -> list[dict[str, Any]]:
    """Allow static diagnostics and phases; never emit raw messages, values or traces."""
    known = {
        (".".join(p.relative_to(ROOT).with_suffix("").parts), node.name)
        for p in (ROOT / "tests").rglob("test_*.py")
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }
    sources = [
        p for folder in ["scripts/identity", "backend/business_app/identity"] for p in (ROOT / folder).glob("*.py")
    ] + [ROOT / "tools/identity_oidc_probe.py", ROOT / "tests/identity/recovery_lab.py"]
    readiness_codes = readiness_diagnostic_codes()
    codes = {
        node.value
        for p in sources
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and re.fullmatch(r"(?:IDENTITY|RECOVERY_LAB)_[A-Z][A-Z0-9_]*[A-Z0-9]", node.value)
        and node.value not in readiness_codes | {READINESS_MISSING_ERROR}
    }
    exception_types = {
        "RuntimeError",
        "AssertionError",
        "ReadTimeout",
        "ConnectTimeout",
        "ConnectError",
        "SSLError",
        "PermissionError",
    }
    result = []
    for case in ET.fromstring(path.read_bytes()).iter("testcase"):
        kind = "failure" if case.find("failure") is not None else "error" if case.find("error") is not None else None
        if kind:
            module, name = case.get("classname", ""), case.get("name", "").split("[", 1)[0]
            label = module + "." + name if (module, name) in known else "UNRECOGNIZED_TEST_CASE"
            item: dict[str, Any] = {"case": label, "kind": kind}
            problem = case.find(kind)
            message = problem.get("message", "") if problem is not None else ""
            words = set(re.findall(r"\b[A-Za-z][A-Za-z0-9_]*\b", message))
            if codes.intersection(words):
                item["diagnostic_codes"] = sorted(codes.intersection(words))
            if (module, name) == READINESS_CASE:
                reason = readiness_failure_code(problem, readiness_codes)
                if reason is not None:
                    item["diagnostic_codes"] = sorted({*item.get("diagnostic_codes", []), reason})
            if exception_types.intersection(words):
                item["exception_types"] = sorted(exception_types.intersection(words))
            for phase in ("setup", "teardown", "call"):
                if message.lower().startswith("failed on " + phase + " "):
                    item["phase"] = phase
            result.append(item)
    return result


def collect(path: Path) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    for name in GROUPS:
        target = path / name
        try:
            counts = junit_counts(target)
            passed = counts["tests"] > 0 and not any(counts[k] for k in FIELDS[1:])
            groups.append(
                {
                    "report": name,
                    "status": "PASS" if passed else "FAIL",
                    "totals": counts,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    "failed_cases": safe_failed_cases(target) if not passed else [],
                }
            )
        except (ValueError, KeyError, OSError, ET.ParseError):
            groups.append(
                {
                    "report": name,
                    "status": "FAIL",
                    "totals": dict.fromkeys(FIELDS, 0),
                    "error": "MISSING_OR_INVALID_JUNIT",
                }
            )
    report = {
        "status": "PASS" if all(g["status"] == "PASS" for g in groups) else "FAIL",
        "scope": "T013_isolated_identity_rotation_fault_mapping_restart_restore_tests_not_whole_acceptance",
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": source_hashes(),
        "python": sys.version.split()[0],
        "groups": groups,
        "totals": {k: sum(g["totals"][k] for g in groups) for k in FIELDS},
        "formal_accepted": False,
        "raw_logs_published": False,
        "Python_candidates_created": False,
    }
    report["source_code_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    return report


def run_groups(path: Path) -> list[int]:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "backend") + os.pathsep + str(ROOT), PYTHONDONTWRITEBYTECODE="1")
    exits = []
    for name, targets in GROUPS.items():
        junit = path / name
        if junit.exists():
            raise RuntimeError("IDENTITY_FRESH_TEST_REPORT_DIRECTORY_REQUIRED")
        command = [sys.executable, "-m", "pytest", *targets, "-q", "--tb=short", "--junitxml", str(junit)]
        log = path / (name + ".private.log")
        with log.open("xb") as output:
            os.chmod(log, 0o600)
            try:
                result = subprocess.run(
                    command, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=GROUP_TIMEOUTS[name]
                )
                exits.append(result.returncode)
            except subprocess.TimeoutExpired:
                exits.append(124)
        if junit.is_file():
            junit.chmod(0o600)
    return exits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "collect"])
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        path = private_root(args.private_root)
        exits = run_groups(path) if args.action == "run" else []
        report = collect(path)
        if any(exits):
            report["status"] = "FAIL"
        report["process_exit_codes"] = exits
        if args.output.is_symlink() or args.output.absolute() in {path / name for name in GROUPS}:
            raise RuntimeError("IDENTITY_REPORT_PATH_INVALID")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "totals": report["totals"], "raw_logs_published": False}))
        return 0 if report["status"] == "PASS" else 1
    except (RuntimeError, OSError):
        print('{"status":"FAIL","error":"IDENTITY_TEST_REPORT_FAILED","raw_logs_published":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
