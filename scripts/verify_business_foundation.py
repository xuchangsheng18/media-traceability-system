"""Run the selected business checks against explicit isolated test targets only."""

import argparse
import ast
import datetime
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from psycopg.conninfo import conninfo_to_dict

ROOT = Path(__file__).resolve().parents[1]
BUSINESS_TEST_TIMEOUT_SECONDS = 1800
BUSINESS_TEST_CLEANUP_GRACE_SECONDS = 5
BUSINESS_TEST_TERMINATION_GRACE_SECONDS = 2
BUSINESS_TEST_FINAL_DRAIN_SECONDS = 2


class _PytestTimeout(subprocess.TimeoutExpired):
    """Only a fixed shutdown observation, never a child command or output."""

    def __init__(self, timeout: float, shutdown: dict[str, Any]) -> None:
        super().__init__("isolated-business-pytest", timeout)
        self.shutdown = dict(shutdown)


def _run_pytest(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    capture_output: bool = True,
    text: bool = True,
    timeout: float,
    on_timeout: Callable[[], None] | None = None,
) -> subprocess.CompletedProcess[Any]:
    """Keep the execution budget; allow bounded best-effort teardown afterwards.

    The Linux leader is not polled or reaped between timeout and the final
    group signal, so its PID cannot be reused as an unrelated process group.
    Escaped grandchildren and database resources are never claimed cleaned.
    """
    owned_group = sys.platform == "linux"
    # Fallback intentionally discards unused raw output. Windows communicate
    # otherwise uses reader threads whose buffered close can block on an
    # escaped descendant's inherited pipe. This is not native Windows
    # acceptance or proof of descendant/database cleanup.
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=(subprocess.PIPE if capture_output else None) if owned_group else subprocess.DEVNULL,
        stderr=(subprocess.PIPE if capture_output else None) if owned_group else subprocess.DEVNULL,
        text=text,
        start_new_session=owned_group,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        shutdown: dict[str, Any] = dict(
            strategy="linux_owned_process_group" if owned_group else "direct_child_fallback",
            cleanup_grace_seconds=BUSINESS_TEST_CLEANUP_GRACE_SECONDS,
            termination_grace_seconds=BUSINESS_TEST_TERMINATION_GRACE_SECONDS,
            final_drain_seconds=BUSINESS_TEST_FINAL_DRAIN_SECONDS,
            interrupt_attempted=False,
            terminate_attempted=False,
            kill_attempted=False,
            signal_failure_count=0,
            direct_child_reaped=False,
            output_drain_completed=False,
            process_group_cleanup_verified=False,
            database_cleanup_verified=False,
        )
        # Observation failures must not prevent the owned child's termination.
        try:
            if on_timeout is not None:
                on_timeout()
        except BaseException:
            pass

        def send(kind: str) -> None:
            shutdown[kind + "_attempted"] = True
            try:
                if owned_group:
                    # No poll/wait here. Retain the unreaped leader throughout
                    # every group signal, including when SIGINT made it exit.
                    os.killpg(
                        process.pid,
                        {"interrupt": signal.SIGINT, "terminate": signal.SIGTERM, "kill": signal.SIGKILL}[kind],
                    )
                elif kind == "terminate":
                    process.terminate()
                elif kind == "kill":
                    process.kill()
            except ProcessLookupError:
                # A missing group/child is an observation, not proof about DBs.
                pass
            except BaseException:
                shutdown["signal_failure_count"] += 1

        def pause(seconds: float) -> None:
            try:
                time.sleep(seconds)
            except BaseException:
                # Cancellation or an unexpected wait error must still reach
                # the later kill and bounded reaping attempts.
                pass

        if owned_group:
            send("interrupt")
            pause(BUSINESS_TEST_CLEANUP_GRACE_SECONDS)
        send("terminate")
        pause(BUSINESS_TEST_TERMINATION_GRACE_SECONDS)
        send("kill")
        deadline = time.monotonic() + BUSINESS_TEST_FINAL_DRAIN_SECONDS
        try:
            process.communicate(timeout=max(0.0, deadline - time.monotonic()))
            shutdown["output_drain_completed"] = True
        except BaseException:
            # A grandchild that escaped the group can keep inherited pipes
            # open. Close only our endpoints; do not wait for it indefinitely.
            pass
        finally:
            for handle in (process.stdin, process.stdout, process.stderr):
                if handle is not None:
                    try:
                        handle.close()
                    except BaseException:
                        pass
            try:
                process.wait(timeout=max(0.0, deadline - time.monotonic()))
                shutdown["direct_child_reaped"] = True
            except BaseException:
                pass
        raise _PytestTimeout(timeout, shutdown) from None
    except BaseException:
        # Preserve subprocess.run's exceptional-path cleanup, without a Popen
        # context manager whose __exit__ could wait without a deadline.
        try:
            if owned_group and process.returncode is None:
                os.killpg(process.pid, signal.SIGKILL)
            elif not owned_group:
                process.kill()
        except BaseException:
            pass
        finally:
            for handle in (process.stdin, process.stdout, process.stderr):
                if handle is not None:
                    try:
                        handle.close()
                    except BaseException:
                        pass
            try:
                process.wait(timeout=BUSINESS_TEST_FINAL_DRAIN_SECONDS)
            except BaseException:
                pass
        raise
    returncode = process.returncode
    if returncode is None:
        raise RuntimeError("BUSINESS_CHILD_STATUS_UNAVAILABLE")
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def validate_target(env: dict[str, str]) -> None:
    dsn = env.get("MT_BUSINESS_TEST_ADMIN_DSN")
    if not dsn or not env.get("MT_BUSINESS_TEST_BROKER_URL"):
        raise RuntimeError("EXPLICIT_ISOLATED_BUSINESS_TEST_TARGETS_REQUIRED")
    values = conninfo_to_dict(dsn)
    if values.get("dbname") == "media_trace_poc" or values.get("user") == "media_trace_poc":
        raise RuntimeError("POC_TARGET_FORBIDDEN")
    if values.get("host") not in {"127.0.0.1", "localhost", "::1"} or not values.get("port"):
        raise RuntimeError("EXPLICIT_LOOPBACK_TEST_INSTANCE_REQUIRED")


def test_totals(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return {key: sum(int(s.get(key, "0")) for s in suites) for key in ["tests", "failures", "errors", "skipped"]}


def _source_test_selector(root: Path, case: ET.Element) -> str | None:
    module = re.fullmatch(
        r"(?:tests\.business\.)?(test_[A-Za-z0-9_]+)(?:\.(Test[A-Za-z0-9_]+))?", case.get("classname", "")
    )
    name = case.get("name", "").split("[", 1)[0]
    if module is None or re.fullmatch(r"test_[A-Za-z0-9_]+", name) is None:
        return None
    path = root / "tests" / "business" / (module[1] + ".py")
    if path.is_symlink():
        return None
    try:
        body = ast.parse(path.read_text("utf8")).body
    except (OSError, SyntaxError, UnicodeError):
        return None
    if module[2] is not None:
        body = [
            child for item in body if isinstance(item, ast.ClassDef) and item.name == module[2] for child in item.body
        ]
    if not any(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name for item in body):
        return None
    parts = [path.relative_to(root).as_posix(), *([module[2]] if module[2] else []), name]
    return "::".join(parts)


def failure_diagnostics(root: Path, path: Path) -> dict[str, Any]:
    """Publish only existing source selectors; JUnit messages and parameters remain private."""
    items: list[dict[str, Any]] = []
    omitted = 0
    if path.is_file():
        for index, case in enumerate(ET.parse(path).getroot().iter("testcase")):
            for child in case:
                if child.tag not in {"failure", "error"}:
                    continue
                nodeid = _source_test_selector(root, case) if len(items) < 20 else None
                if nodeid is None:
                    omitted += 1
                else:
                    items.append(dict(nodeid=nodeid, kind=child.tag, testcase_index=index))
    return dict(items=items, omitted=omitted, parameters_and_failure_text_published=False)


def last_test_progress(root: Path, path: Path, nonce: str) -> dict[str, str] | None:
    """A bounded source-checked observation, never a diagnosis of which test hung."""
    if not isinstance(nonce, str) or re.fullmatch(r"[a-f0-9]{32}", nonce) is None:
        return None
    try:
        if path.is_symlink():
            return None
        with path.open("rb") as handle:
            raw = handle.read(4097)
        if len(raw) > 4096:
            return None
        value = json.loads(raw)
    except (OSError, ValueError, UnicodeError, RecursionError):
        return None
    if not isinstance(value, dict) or set(value) != {"classname", "name", "phase", "nonce"}:
        return None
    if not all(isinstance(item, str) for item in value.values()) or value["nonce"] != nonce:
        return None
    if value["phase"] not in {"setup", "call", "teardown", "finished"}:
        return None
    case = ET.Element("testcase", classname=value["classname"], name=value["name"])
    selector = _source_test_selector(root, case)
    return dict(nodeid=selector, phase=value["phase"]) if selector is not None else None


def run_checks(root: Path, env: dict[str, str], junit: Path) -> dict[str, Any]:
    # This private side channel survives a killed child without publishing its output.
    # Each invocation owns its nonce and path; caller-provided checkpoints are ignored.
    with tempfile.TemporaryDirectory(prefix="media-trace-business-progress-") as temp:
        progress = Path(temp) / "latest.json"
        nonce = uuid4().hex
        child_env = dict(
            env,
            MT_BUSINESS_TEST_PROGRESS_FILE=str(progress),
            MT_BUSINESS_TEST_PROGRESS_NONCE=nonce,
            PYTHONPATH=os.pathsep.join(filter(None, [str(ROOT / "scripts"), env.get("PYTHONPATH", "")])),
        )
        timed_out = False
        checkpoint_frozen = False
        observation: dict[str, str] | None = None
        shutdown: dict[str, Any] | None = None

        def freeze_timeout_progress() -> None:
            nonlocal checkpoint_frozen, observation
            if not checkpoint_frozen:
                checkpoint_frozen = True
                observation = last_test_progress(root, progress, nonce)

        try:
            result = _run_pytest(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/business",
                    "-q",
                    "--tb=short",
                    "-p",
                    "business_test_progress",
                    "--junitxml",
                    str(junit),
                ],
                cwd=root,
                env=child_env,
                capture_output=True,
                text=True,
                timeout=BUSINESS_TEST_TIMEOUT_SECONDS,
                on_timeout=freeze_timeout_progress,
            )
            returncode = result.returncode
        except subprocess.TimeoutExpired as error:
            timed_out = True
            returncode = 2
            if type(error) is _PytestTimeout:
                shutdown = dict(error.shutdown)
            if not checkpoint_frozen:
                freeze_timeout_progress()
        if not timed_out:
            observation = last_test_progress(root, progress, nonce)
    junit_available = junit.is_file()
    try:
        totals = test_totals(junit)
    except (ET.ParseError, OSError, ValueError):
        junit_available = False
        totals = {key: 0 for key in ["tests", "failures", "errors", "skipped"]}
    partial_totals = None
    if timed_out:
        if junit_available and all(type(value) is int and 0 <= value <= 2**63 - 1 for value in totals.values()):
            partial_totals = dict(totals)
        # An interrupted JUnit file observes partial execution only. Preserve
        # the existing completed-suite counters and never convert it to PASS.
        totals = {key: 0 for key in ["tests", "failures", "errors", "skipped"]}
    success = (
        not timed_out
        and returncode == 0
        and totals["tests"] > 0
        and not any(totals[k] for k in ["failures", "errors", "skipped"])
    )
    # Raw tracebacks can include isolated credentials. Publish counts and safe identifiers only.
    return {
        "status": "TIMEOUT" if timed_out else "PASS" if success else "FAIL",
        "exit_code": 2 if timed_out else 0 if success else returncode or 1,
        "complete": not timed_out and junit_available,
        "timeout_seconds": BUSINESS_TEST_TIMEOUT_SECONDS,
        "last_test_progress": observation,
        "timeout_shutdown": shutdown,
        "interrupted_junit_observed": partial_totals is not None,
        "partial_totals": partial_totals,
        "test_count": totals["tests"],
        "totals": totals,
        "failure_diagnostics": failure_diagnostics(root, junit)
        if junit_available
        else {
            "items": [],
            "omitted": 0,
            "parameters_and_failure_text_published": False,
        },
        "raw_logs_published": False,
    }


def configured_environment() -> dict[str, str]:
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "backend"), str(ROOT)]))
    runtime = Path(env.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
    for key, file, value in [
        ("MT_BUSINESS_TEST_ADMIN_DSN", "business-test-postgres-private.json", "admin_dsn"),
        ("MT_BUSINESS_TEST_BROKER_URL", "business-test-broker-private.json", "url"),
    ]:
        if not env.get(key) and (runtime / file).is_file():
            env[key] = json.loads((runtime / file).read_text())[value]
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "failure-probe"], nargs="?", default="run")
    args = parser.parse_args()
    env = configured_environment()
    report: dict[str, Any] = {
        "scope": "isolated_development_upload_history_controls_adapters_execution_inference_boundaries",
        "formal_accepted": False,
        "all_13_gaps_closed": False,
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    try:
        validate_target(env)
        with tempfile.TemporaryDirectory(prefix="media-trace-business-verification-") as temp:
            if args.action == "failure-probe":
                path = Path(temp) / "test_controlled_failure.py"
                path.write_text("def test_controlled_failure():\n    assert 1 == 2\n")
                junit = Path(temp) / "failure.xml"
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(path), "-q", "--junitxml", str(junit)],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    timeout=60,
                )
                totals = test_totals(junit)
                expected = result.returncode == 1 and totals == {"tests": 1, "failures": 1, "errors": 0, "skipped": 0}
                print(json.dumps({"expected_assertion_failure_verified": expected, "exit_code": result.returncode}))
                return 1 if expected else 2
            report.update(run_checks(ROOT, env, Path(temp) / "business.xml"))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        report.update(status="BLOCKED_OR_FAIL", exit_code=2, test_count=0)
    report["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if TYPE_CHECKING:
        from scripts.stage_three_types import source_tree_state
    else:
        from stage_three_types import source_tree_state

    report.update(source_tree_state(ROOT))
    report["workflow_run_id"] = os.environ.get("GITHUB_RUN_ID")
    (ROOT / "docs/00-project/validation/business-foundation-report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "test_count": report["test_count"],
                "scope": report["scope"],
                "failure_diagnostics": report.get("failure_diagnostics"),
                "complete": report.get("complete", False),
                "timeout_seconds": report.get("timeout_seconds"),
                "last_test_progress": report.get("last_test_progress"),
                "timeout_shutdown": report.get("timeout_shutdown"),
                "interrupted_junit_observed": report.get("interrupted_junit_observed", False),
                "partial_totals": report.get("partial_totals"),
            }
        )
    )
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
