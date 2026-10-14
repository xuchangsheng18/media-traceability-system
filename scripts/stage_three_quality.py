"""Explicit development quality checks and a separate pre-commit tool environment."""

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import venv
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "docs/00-project/validation"
RUNTIME = Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
PROFILE = json.loads((ROOT / "config/stage-three-profile.json").read_text(encoding="utf-8"))
EXCLUDED = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "test-results",
    "playwright-report",
}


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True
    )
    return sorted({name for name in result.stdout.decode("utf-8").split("\0") if name and (ROOT / name).is_file()})


def text_check():
    paths = PROFILE["format_scope"] + [
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODEOWNERS",
        ".editorconfig",
        ".env.example",
        ".python-version",
        ".nvmrc",
        ".pre-commit-config.yaml",
        ".codex/config.toml",
        "Makefile",
        "scripts/dev.ps1",
        "config/stage-three-profile.json",
    ]
    for name in paths:
        raw = (ROOT / name).read_bytes()
        raw.decode("utf-8")
        assert b"\r\n" not in raw and raw.endswith(b"\n"), name
    print(
        json.dumps({"status": "PASS", "scope": "selected_development_python_and_governance_text", "files": len(paths)})
    )
    return 0


def secret_check():
    private = RUNTIME / "credentials.json"
    values = [value.encode() for value in json.loads(private.read_text()).values()] if private.exists() else []
    patterns = [
        re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(rb"ghp_[A-Za-z0-9]{36,}"),
        re.compile(rb"github_pat_[A-Za-z0-9_]{70,}"),
        re.compile(rb"AKIA[0-9A-Z]{16}"),
    ]
    errors = []
    files = tracked_files()
    for name in files:
        raw = (ROOT / name).read_bytes()
        if (
            Path(name).name in {"credentials.json", "poc.env", "postgres.env", "rabbitmq.env", "s3.json"}
            or any(value in raw for value in values)
            or any(pattern.search(raw) for pattern in patterns)
        ):
            errors.append(name)
    summary = {
        "status": "FAIL" if errors else "PASS",
        "files_checked": len(files),
        "errors": errors,
        "exact_runtime_values_available": bool(values),
        "scope": "tracked_and_unignored_files_known_private_values_and_basic_key_patterns",
        "comprehensive_DLP_or_history_scan": False,
        "secret_values_printed": False,
    }
    (VALIDATION / "stage-three-secrets-report.json").write_bytes((json.dumps(summary, indent=2) + "\n").encode())
    print(json.dumps({key: value for key, value in summary.items() if key != "errors"}))
    return int(bool(errors))


def setup_tools():
    base = RUNTIME.resolve()
    if base.is_relative_to(ROOT.resolve()) or RUNTIME.is_symlink():
        raise RuntimeError("QUALITY_ENVIRONMENT_MUST_BE_OUTSIDE_SOURCE")
    target = base / PROFILE["quality_environment_directory"]
    if target.is_symlink():
        raise RuntimeError("QUALITY_ENVIRONMENT_SYMLINK_REJECTED")
    target.mkdir(parents=True, exist_ok=True)
    py = target / "bin/python"
    if not py.exists():
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(target)
    install_command = [
        str(py),
        "-m",
        "pip",
        "install",
        "--require-hashes",
        "--no-deps",
        "-r",
        str(ROOT / PROFILE["quality_lock"]),
    ]
    wheelhouse = Path(os.environ.get("MT_QUALITY_WHEELHOUSE", str(RUNTIME / "stage-three-quality-wheelhouse")))
    if wheelhouse.is_dir():
        install_command.extend(["--no-index", "--find-links", str(wheelhouse)])
    subprocess.run(install_command, check=True)
    subprocess.run([str(py), "-m", "pre_commit", "validate-config", str(ROOT / ".pre-commit-config.yaml")], check=True)
    print(
        json.dumps(
            {
                "status": "PASS",
                "quality_python": str(py),
                "project_py310_or_100_package_lock_changed": False,
                "git_hooks_installed": False,
            }
        )
    )
    return 0


def normalize_npm_report(raw):
    # Registry failures may include cookies/headers; never publish that response.
    if isinstance(raw, dict):
        metadata = raw.get("metadata")
        if isinstance(metadata, dict):
            counts, dependencies = metadata.get("vulnerabilities"), metadata.get("dependencies")
            levels = {"info", "low", "moderate", "high", "critical", "total"}
            if (
                not raw.get("error")
                and raw.get("auditReportVersion") == 2
                and isinstance(raw.get("vulnerabilities"), dict)
                and isinstance(counts, dict)
                and levels <= counts.keys()
                and all(type(counts[key]) is int and counts[key] >= 0 for key in levels)
                and counts["total"] == sum(counts[key] for key in levels - {"total"})
                and isinstance(dependencies, dict)
                and type(dependencies.get("total")) is int
                and dependencies["total"] > 0
            ):
                return {key: raw[key] for key in ("auditReportVersion", "vulnerabilities", "metadata")}, False
    return {
        "error": "NPM_AUDIT_EXECUTION_ERROR_OR_INCOMPLETE_REPORT",
        "external_response_headers_or_cookies_published": False,
    }, True


def dependency_check():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    python_path = VALIDATION / "stage-three-python-dependency-report.json"
    node_path = VALIDATION / "stage-three-npm-dependency-report.json"
    quality_path = VALIDATION / "stage-three-quality-dependency-report.json"
    audit = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            "config/locks/requirements-py310.lock",
            "--no-deps",
            "--disable-pip",
            "--progress-spinner",
            "off",
            "--format",
            "json",
            "--output",
            str(python_path),
        ],
        cwd=ROOT,
        check=False,
    )
    quality_audit = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            PROFILE["quality_lock"],
            "--no-deps",
            "--disable-pip",
            "--progress-spinner",
            "off",
            "--format",
            "json",
            "--output",
            str(quality_path),
        ],
        cwd=ROOT,
        check=False,
    )
    npm = subprocess.run(
        ["npm", "--prefix", "frontend", "audit", "--json", "--audit-level=high"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        node_data, node_error = normalize_npm_report(json.loads(npm.stdout))
    except json.JSONDecodeError:
        node_data, node_error = normalize_npm_report(None)
    node_path.write_bytes((json.dumps(node_data, indent=2) + "\n").encode())
    python_data: dict[str, Any] = (
        json.loads(python_path.read_text()) if python_path.exists() else {"error": "PYTHON_AUDIT_NO_REPORT"}
    )
    dependencies = python_data.get("dependencies", [])
    quality_data: dict[str, Any] = (
        json.loads(quality_path.read_text()) if quality_path.exists() else {"error": "QUALITY_AUDIT_NO_REPORT"}
    )
    quality_dependencies = quality_data.get("dependencies", [])
    quality_findings = sum(len(item.get("vulns", [])) for item in quality_dependencies)
    quality_skips = [
        {"name": item["name"], "reason": item.get("skip_reason")}
        for item in quality_dependencies
        if item.get("skip_reason")
    ]
    skips = [
        {"name": item["name"], "reason": item.get("skip_reason")} for item in dependencies if item.get("skip_reason")
    ]
    findings = sum(len(item.get("vulns", [])) for item in dependencies)
    node_counts = node_data.get("metadata", {}).get("vulnerabilities", {})
    execution_error = bool(
        python_data.get("error")
        or node_error
        or quality_data.get("error")
        or quality_audit.returncode not in {0, 1}
        or node_data.get("error")
        or audit.returncode not in {0, 1}
        or npm.returncode not in {0, 1}
    )
    blocking = (
        execution_error
        or findings > 0
        or quality_findings > 0
        or node_counts.get("high", 0) > 0
        or node_counts.get("critical", 0) > 0
    )
    summary = {
        "status": "FAIL_OR_SCAN_ERROR" if blocking else "NO_REPORTED_BLOCKING_FINDINGS_WITH_COVERAGE_LIMITS",
        "started_at": started,
        "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python_dependencies_listed": len(dependencies),
        "python_findings": findings,
        "quality_tool_dependencies_listed": len(quality_dependencies),
        "quality_tool_findings": quality_findings,
        "quality_tool_skips": quality_skips,
        "raw_quality_tool_report": quality_path.relative_to(ROOT).as_posix(),
        "python_skips": skips,
        "npm_findings_by_severity": node_counts,
        "raw_python_report": python_path.relative_to(ROOT).as_posix(),
        "raw_npm_report": node_path.relative_to(ROOT).as_posix(),
        "python_lock_sha256": hashlib.sha256((ROOT / "config/locks/requirements-py310.lock").read_bytes()).hexdigest(),
        "runtime_Python_OS_model_and_full_DLP_acceptance": False,
        "skip_does_not_mean_safe": True,
        "npm_development_gate_severity": "high_and_critical_block_low_and_moderate_recorded_not_formally_accepted",
    }
    (VALIDATION / "stage-three-dependency-scan-report.json").write_bytes(
        (json.dumps(summary, indent=2) + "\n").encode()
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "python_findings": findings,
                "python_skipped": len(skips),
                "npm_findings": node_counts,
            }
        )
    )
    return int(blocking)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["text", "secrets", "setup-tools", "dependencies"])
    args = parser.parse_args()
    return {"text": text_check, "secrets": secret_check, "setup-tools": setup_tools, "dependencies": dependency_check}[
        args.action
    ]()


if __name__ == "__main__":
    raise SystemExit(main())
