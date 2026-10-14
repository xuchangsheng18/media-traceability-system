"""Verify third-stage inputs and actually execute the bounded existing py310 profile."""

import argparse
import datetime
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "docs/03-development/stage-three/"
REPORTS = ROOT / "docs/00-project/validation"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def static_checks():
    checks = []
    inventory = read(PREFIX + "source-inventory.json")
    assert len(inventory["records"]) == 2 and inventory["steps"] == 16
    for source in inventory["records"]:
        assert digest(source["path"]) == source["sha256"]
        assert digest(source["converted_path"]) == source["converted_sha256"]
        assert source["byte_preserved"] and source["approval_asserted"] is False
    checks.append({"name": "two_unchanged_originals_and_reading_versions", "status": "PASS"})
    prior = read("docs/00-project/source-inventory.json")
    assert len(prior) == 10 and all(digest(item["path"]) == item["sha256"] for item in prior)
    history = read("docs/00-project/stage-one/materials-manifest.json")["records"]
    assert len(history) == 14 and all(digest(item["archived_path"]) == item["sha256"] for item in history)
    checks.append({"name": "prior_ten_originals_and_fourteen_history_files_preserved", "status": "PASS"})
    record = read(PREFIX + "deliverables.json")
    source = (ROOT / record["source_guide"]).read_text(encoding="utf-8")
    actual = re.findall(r"^## 步骤(\d+) ([^\n]+)", source, re.M)
    assert actual == [(str(item["step"]), item["title"]) for item in record["steps"]]
    assert digest(record["source_guide"]) == record["source_guide_sha256"]
    assert [item["step"] for item in record["steps"]] == list(range(1, 17))
    assert all(
        item["source_acceptance"] and item["operation"] and item["remaining"] and item["outputs"]
        for item in record["steps"]
    )
    assert all((ROOT / path).is_file() for item in record["steps"] for path in item["outputs"])
    assert sum(len(item["acceptance_review"]) for item in record["steps"]) == 57
    for item in record["steps"]:
        assert [review["criterion"] for review in item["acceptance_review"]] == item["source_acceptance"]
        assert item["development_status"] != "工程产物/实际证据分别核验；正式条件待落实"
        assert item["engineering_status"] in {"DOCUMENTED", "PARTIAL", "VERIFIED_SELECTED_SCOPE"}
        for review in item["acceptance_review"]:
            assert review["status"] in {
                "DOCUMENTED",
                "PARTIAL",
                "VERIFIED_SELECTED_SCOPE",
                "PENDING_EXTERNAL",
                "ADAPTED_EXISTING_REPOSITORY",
            }
            assert review["scope_note"] and review["evidence"]
            assert all((ROOT / path).is_file() for path in review["evidence"])
    checks.append({"name": "sixteen_source_steps_exact_titles_acceptance_and_real_outputs", "status": "PASS"})
    profile = read("config/stage-three-profile.json")
    versions = yaml.safe_load((ROOT / "config/versions.yaml").read_text(encoding="utf-8"))
    assert (ROOT / ".python-version").read_text().strip() == versions["python"]["version"] == "3.10.22"
    assert (ROOT / ".nvmrc").read_text().strip() == versions["frontend"]["node"] == "22.21.1"
    assert profile["python_executable"] == versions["python"]["executable"]
    assert versions["production_python_selection"]["production_approved"] is False
    checks.append({"name": "existing_py310_node_versions_preserved_production_not_approved", "status": "PASS"})
    fields = read(PREFIX + "external-inputs.json")
    assert fields["formal_frozen"] is False and fields["formal_approved"] is False
    assert record["formal_frozen"] is False and all(
        item["formal_completion_asserted"] is False and item["owner_name"] is None for item in record["steps"]
    )
    assert profile["formal_approval_refs"] == [] and profile["production_release_or_formal_data_access"] is False
    assert "NOT_FROZEN" in (ROOT / "docs/03-development/development-environment-baseline.md").read_text(
        encoding="utf-8"
    )
    foundation = read("docs/00-project/validation/stage-three-foundation-audit-report.json")
    assert foundation["formal_approved"] is False and foundation["formal_frozen"] is False
    assert len(foundation["interface_gaps"]) == 13 and all(
        item["business_implementation_asserted"] is False for item in foundation["interface_gaps"]
    )
    assert foundation["quality"]["formatter_remediation"]["old_scope_files_checked"] == 13
    assert all(item["AST_identical"] for item in foundation["quality"]["formatter_remediation"]["records"])
    assert foundation["torch"]["installed_payload_verification"]["files_checked"] == 12240
    assert not foundation["torch"]["installed_payload_verification"]["mismatches"]
    for platform in ["codex_windows", "codex_linux"]:
        assert foundation[platform]["full_root_AGENTS_loaded_into_prompt_input"]
        layers = foundation[platform]["effective_config_after"]["project_layer_metadata"]
        assert any(layer["name"]["type"] == "project" and not layer.get("disabledReason") for layer in layers)
    checks.append({"name": "no_invented_people_formal_approvals_freeze_or_release", "status": "PASS"})
    for path in [
        "frontend",
        "backend",
        "ai-services",
        "shared-contracts",
        "schemas",
        "docs",
        "tasks",
        "prompts",
        "config",
        "deploy",
        "scripts",
        "tests",
        "datasets",
        "data-pipeline",
        "tools",
    ]:
        assert (ROOT / path / "README.md").is_file(), path
    for path in [
        "AGENTS.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODEOWNERS",
        ".gitignore",
        ".editorconfig",
        ".env.example",
        ".pre-commit-config.yaml",
        "Makefile",
        "scripts/dev.ps1",
        ".codex/config.toml",
    ]:
        assert (ROOT / path).is_file(), path
    checks.append({"name": "fifteen_directory_readmes_and_governance_files_present", "status": "PASS"})
    tools = read("config/locks/stage-three-quality-artifacts.json")
    lock = (ROOT / profile["quality_lock"]).read_text()
    assert len(tools["packages"]) == 12 and tools["pre_commit"] == "4.6.2"
    for package in tools["packages"]:
        assert package["name"] + "==" + package["version"] + " --hash=sha256:" + package["sha256"] in lock
    assert tools["runtime_dependency_lock_changed"] is False
    checks.append({"name": "separate_quality_tool_closure_twelve_version_and_download_hashes", "status": "PASS"})
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text())
    assert config == {"project_doc_max_bytes": 32768}
    assert (ROOT / "AGENTS.md").stat().st_size < 32768
    owners = (ROOT / "CODEOWNERS").read_text()
    assert "* @xuchangsheng18" in owners
    precommit = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    assert precommit["repos"][0]["hooks"][0]["entry"] == "python scripts/dev.py pre-commit"
    checks.append({"name": "project_config_preserves_user_model_permissions_and_valid_local_hook", "status": "PASS"})
    from dev import COMMANDS, plan

    assert set(
        [
            "help",
            "setup",
            "dev",
            "stop",
            "lint",
            "format-check",
            "type-check",
            "test",
            "contract-test",
            "integration-test",
            "build",
            "security-scan",
            "clean",
        ]
    ) <= set(COMMANDS)
    assert plan("ci")[0][-1] == "all" and plan("stop")[0][-1] == "down"
    assert profile["clean_allowlist"] == [".pytest_cache", ".ruff_cache"]
    checks.append({"name": "portable_task_entry_retains_ci_and_restricted_clean_scope", "status": "PASS"})
    schema = read("schemas/development/mock-connectivity.response.schema.json")
    Draft202012Validator.check_schema(schema)
    good = {
        "schema_version": "development-connectivity-v1",
        "nonce": "00000000-0000-4000-8000-000000000001",
        "mock": True,
        "business_result": False,
        "model_name": "mock-connectivity",
        "model_version": "example-1",
        "request_id": "00000000-0000-4000-8000-000000000002",
    }
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(good)
    assert list(validator.iter_errors(dict(good, mock=False))) and list(
        validator.iter_errors(dict(good, business_result=True))
    )
    assert list(validator.iter_errors(dict(good, case_id=good["nonce"])))
    checks.append({"name": "demo_schema_rejects_business_results_and_foreign_case_fields", "status": "PASS"})
    return checks


def run_bounded(command, env):
    process = subprocess.Popen(command, cwd=ROOT, env=env, start_new_session=os.name == "posix")
    try:
        result = process.wait(timeout=300)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=5)
        raise
    if result:
        raise subprocess.CalledProcessError(result, command)


def run_profile():
    from dev import PROFILE, environment
    from poc_control import RUNTIME, compose

    assert sys.version_info[:2] == (3, 10)
    python = str(Path(sys.executable).resolve())
    env = environment()
    commands = [
        ("setup_existing_locks_and_separate_tools", [python, "scripts/dev.py", "setup", "--tools"]),
        ("lint_and_TS", [python, "scripts/dev.py", "lint"]),
        ("new_code_format_and_text", [python, "scripts/dev.py", "format-check"]),
        ("unit_and_frontend_tests", [python, "scripts/dev.py", "test"]),
        ("unique_contract_SQL_and_generated_types", [python, "scripts/dev.py", "contract-test"]),
        ("secret_and_dependency_scans", [python, "scripts/dev.py", "security-scan"]),
        (
            "actual_precommit_all_files_no_hooks_installed",
            [
                str(RUNTIME / PROFILE["quality_environment_directory"] / "bin/python"),
                "-m",
                "pre_commit",
                "run",
                "--all-files",
            ],
        ),
        ("actual_three_process_and_browser_fixture", [python, "scripts/verify_stage_three_demo.py"]),
        ("existing_stack_read_only_status", [python, "scripts/dev.py", "status"]),
        ("clean_preview_only", [python, "scripts/dev.py", "clean", "--dry-run"]),
        ("full_CI_entry_plan_only_actual_run_evidence_separate", [python, "scripts/dev.py", "ci", "--dry-run"]),
        ("original_runtime_lock_after_tool_layer", [python, "scripts/verify_runtime_lock.py"]),
    ]
    results = []
    prior_runtime = read("docs/00-project/validation/stage-three-runtime-report.json")
    previous_attempts = prior_runtime.get("previous_attempts", [])
    if prior_runtime.get("status") == "FAIL":
        previous_attempts.append(
            {
                "status": "FAIL",
                "observed_at": prior_runtime.get("observed_at"),
                "failed_checks": [item for item in prior_runtime.get("checks", []) if item["status"] == "FAIL"],
                "scope": "preserved_failed_attempt_before_retry_not_counted_as_current_pass",
            }
        )
    for name, command in commands:
        started = datetime.datetime.now(datetime.timezone.utc)
        try:
            run_bounded(command, env)
        except (OSError, subprocess.SubprocessError) as exc:
            results.append(
                {
                    "name": name,
                    "command": command,
                    "status": "FAIL",
                    "scope": "current_locked_CPU_development_only",
                    "error_type": type(exc).__name__,
                }
            )
            failure = {
                "status": "FAIL",
                "checks": results,
                "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "formal_frozen": False,
                "previous_attempts": previous_attempts,
            }
            (REPORTS / "stage-three-runtime-report.json").write_bytes((json.dumps(failure, indent=2) + "\n").encode())
            raise
        results.append(
            {
                "name": name,
                "command": command,
                "status": "PASS",
                "scope": "current_locked_CPU_development_only",
                "elapsed_seconds": (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds(),
            }
        )
    compose("config", "--quiet")
    results.append(
        {
            "name": "compose_syntax_without_dumping_secrets",
            "command": ["docker", "compose", "config", "--quiet"],
            "status": "PASS",
            "scope": "existing_named_development_stack_read_only",
        }
    )
    actual_node = subprocess.check_output(["node", "--version"], env=env, text=True).strip()
    assert actual_node == "v22.21.1"
    report = {
        "status": "PASS",
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checks": results,
        "python": sys.version,
        "python_executable": str(Path(sys.executable)),
        "node": actual_node,
        "provider": "github_actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "Linux_server",
        "source_commit": os.environ.get("GITHUB_SHA"),
        "actual_count": len(results),
        "existing_application_code_changed": False,
        "existing_Docker_stack_restarted": False,
        "full_build_or_recovery_repeated_by_this_report": False,
        "full_CI_evidence_ref": "docs/00-project/validation/github-actions-report.json",
        "Windows_native_install_GPU_or_formal_business_validation": False,
        "formal_frozen": False,
        "Git_hooks_installed_or_platform_settings_modified": False,
        "previous_attempts": previous_attempts,
    }
    (REPORTS / "stage-three-runtime-report.json").write_bytes((json.dumps(report, indent=2) + "\n").encode())
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", action="store_true")
    args = parser.parse_args()
    checks = static_checks()
    report = {
        "status": "PASS",
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checks": checks,
        "source_steps": 16,
        "source_acceptance_criteria_reviewed": 57,
        "originals_added": 2,
        "prior_originals_preserved": 10,
        "historical_files_preserved": 14,
        "formal_approved": False,
        "formal_frozen": False,
        "complete_business_implementation_asserted": False,
    }
    (REPORTS / "stage-three-validation-report.json").write_bytes((json.dumps(report, indent=2) + "\n").encode())
    if args.runtime:
        run_profile()
    print(
        json.dumps({"status": "PASS", "checks": len(checks), "runtime_executed": args.runtime, "formal_frozen": False})
    )


if __name__ == "__main__":
    main()
