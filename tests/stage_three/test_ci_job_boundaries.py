"""Keep every existing CI gate while isolating bounded execution jobs."""

import hashlib
import itertools
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
DEPENDENCIES = ("identity-verification", "foundation-verification", "engineering-execution")


def jobs():
    return yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))["jobs"]


def final_gate():
    workflow = jobs()
    assert set(DEPENDENCIES) <= set(workflow), "independent verification jobs are required"
    return next(step for step in workflow["engineering"]["steps"] if "run" in step)


def test_all_required_verification_jobs_gate_the_unchanged_engineering_check():
    workflow = jobs()
    assert set(DEPENDENCIES) <= set(workflow), "independent verification jobs are required"
    gate = workflow["engineering"]
    assert set(gate["needs"]) == set(DEPENDENCIES)
    assert gate["if"] == "${{ always() }}"
    assert "continue-on-error" not in gate
    assert gate.get("name", "engineering") == "engineering"
    expected = {
        "IDENTITY_RESULT": DEPENDENCIES[0],
        "FOUNDATION_RESULT": DEPENDENCIES[1],
        "EXECUTION_RESULT": DEPENDENCIES[2],
    }
    assert final_gate()["env"] == {name: "${{ needs." + job + ".result }}" for name, job in expected.items()}
    assert "continue-on-error" not in final_gate()


@pytest.mark.parametrize("results", itertools.product(("success", "failure", "cancelled", "skipped"), repeat=3))
def test_real_shell_gate_rejects_every_non_success_dependency_combination(results):
    script = final_gate()["run"]
    env = dict(os.environ, IDENTITY_RESULT=results[0], FOUNDATION_RESULT=results[1], EXECUTION_RESULT=results[2])
    result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, timeout=5)
    assert (result.returncode == 0) is (results == ("success", "success", "success"))


def test_all_original_gates_and_execution_time_limits_are_retained():
    workflow = jobs()
    assert set(DEPENDENCIES) <= set(workflow), "independent verification jobs are required"
    for name in DEPENDENCIES[1:]:
        job = workflow[name]
        assert job["needs"] == "identity-verification"
        assert job["runs-on"] == "ubuntu-24.04" and job["timeout-minutes"] == 90
        assert "continue-on-error" not in job
        assert set(job["services"]) == {"business-postgres", "business-rabbit"}
        assert job["env"]["MT_DOCKER_CONTEXT"] == "default"
        assert "DOCKER_HOST" not in job["env"]
        assert all("continue-on-error" not in step for step in job["steps"])
    foundation = "\n".join(step.get("run", "") for step in workflow[DEPENDENCIES[1]]["steps"])
    execution = "\n".join(step.get("run", "") for step in workflow[DEPENDENCIES[2]]["steps"])
    for command in (
        '"$PYTHON" scripts/stage_three_types.py check',
        '"$PYTHON" scripts/stage_three_types.py failure-probe',
        '"$PYTHON" -m pytest tests/native -q --tb=short',
        '"$PYTHON" scripts/validate_access_control_model.py --run-tests',
        '"$PYTHON" scripts/verify_business_foundation.py run',
        '"$PYTHON" scripts/verify_business_foundation.py failure-probe',
        '"$PYTHON" scripts/verify_t014_permissions.py run',
        '"$PYTHON" scripts/verify_t014_permissions.py failure-probe',
    ):
        assert command in foundation
    for command in (
        '"$PYTHON" scripts/dev.py ci --allow-stack-changes',
        '"$PYTHON" scripts/verify_ci_failure_gate.py',
        '"$PYTHON" scripts/check_repository_secrets.py',
        '"$PYTHON" scripts/validate_stage_three.py --runtime',
        '"$PYTHON" scripts/verify_t015_scope.py failure-probe',
        '"$PYTHON" scripts/verify_development_limits.py',
    ):
        assert command in execution
    assert '"$PYTHON" scripts/validate_stage_three.py --runtime' not in foundation


def test_artifact_names_separate_job_run_and_attempt():
    workflow = jobs()
    assert set(DEPENDENCIES) <= set(workflow), "independent verification jobs are required"
    names = []
    for job_name in DEPENDENCIES[1:]:
        artifacts = [
            step
            for step in workflow[job_name]["steps"]
            if str(step.get("uses", "")).startswith("actions/upload-artifact@")
        ]
        assert len(artifacts) == 1 and artifacts[0]["if"] == "always()"
        name = artifacts[0]["with"]["name"]
        assert "${{ github.run_id }}" in name and "${{ github.run_attempt }}" in name
        names.append(name)
    assert len(set(names)) == 2


def test_report_ownership_manifest_is_in_each_actual_uploaded_artifact():
    for job_name in DEPENDENCIES[1:]:
        artifact = next(
            step
            for step in jobs()[job_name]["steps"]
            if str(step.get("uses", "")).startswith("actions/upload-artifact@")
        )
        assert "docs/00-project/validation/ci-job-evidence.json" in artifact["with"]["path"].splitlines()


@pytest.mark.parametrize("job_name", DEPENDENCIES[1:])
@pytest.mark.parametrize("case", ("valid", "old_source", "old_time", "future_time", "missing_time", "invalid_json"))
def test_actual_report_binding_rejects_stale_invalid_and_future_evidence(tmp_path, job_name, case):
    step = next(step for step in jobs()[job_name]["steps"] if "OWNED_REPORTS" in step.get("env", {}))
    owned = json.loads(step["env"]["OWNED_REPORTS"])
    root, temporary = tmp_path / "source", tmp_path / "temporary"
    directory = root / "docs/00-project/validation"
    directory.mkdir(parents=True)
    temporary.mkdir()
    (temporary / "verification-started-at").write_text("2020-01-01T00:00:00Z", encoding="utf-8")
    value = {
        "status": "PASS",
        "source_commit": "a" * 40,
        "observed_at": "2020-01-01T00:00:01Z",
        "unrelated_private_field": "self-owned-sentinel",
    }
    if case == "old_source":
        value["source_commit"] = "b" * 40
    elif case == "old_time":
        value["observed_at"] = "2019-01-01T00:00:00Z"
    elif case == "future_time":
        value["observed_at"] = "2099-01-01T00:00:00Z"
    elif case == "missing_time":
        del value["observed_at"]
    raw = json.dumps(value).encode() if case != "invalid_json" else b"self-owned-invalid-json"
    (directory / owned[0]).write_bytes(raw)
    env = dict(
        os.environ,
        **step["env"],
        GITHUB_WORKSPACE=str(root),
        RUNNER_TEMP=str(temporary),
        GITHUB_JOB=job_name,
        GITHUB_SHA="a" * 40,
        GITHUB_RUN_ID="17",
        GITHUB_RUN_ATTEMPT="2",
    )
    result = subprocess.run(["bash", "-c", step["run"]], env=env, capture_output=True, timeout=5)
    assert result.returncode == 0
    output = (directory / "ci-job-evidence.json").read_text(encoding="utf-8")
    manifest = json.loads(output)
    assert manifest["job"] == job_name and manifest["run_id"] == "17" and manifest["run_attempt"] == "2"
    assert manifest["source_commit"] == "a" * 40 and manifest["overall_job_success_not_inferred"] is True
    row = manifest["reports"][0]
    assert row["fresh_exact_source_PASS"] is (case == "valid")
    assert row["sha256"] == hashlib.sha256(raw).hexdigest()
    assert all(not item["fresh_exact_source_PASS"] for item in manifest["reports"][1:])
    assert "self-owned-sentinel" not in output and "self-owned-invalid-json" not in output
