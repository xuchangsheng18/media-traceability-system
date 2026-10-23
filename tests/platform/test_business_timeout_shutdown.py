"""Real child-pytest shutdown; no database or runtime timeout override."""

import json
import os
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts import verify_business_foundation as verifier

SECRET = "SYNTHETIC_UNPUBLISHED_SHUTDOWN_SECRET"
SHORT_CLEANUP = 0.3
SHORT_TERMINATION = 0.2
SHORT_DRAIN = 1
ZERO_TOTALS = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
SHUTDOWN_FIELDS = {
    "strategy",
    "cleanup_grace_seconds",
    "termination_grace_seconds",
    "final_drain_seconds",
    "interrupt_attempted",
    "terminate_attempted",
    "kill_attempted",
    "signal_failure_count",
    "direct_child_reaped",
    "output_drain_completed",
    "process_group_cleanup_verified",
    "database_cleanup_verified",
}


def child_environment():
    env = dict(os.environ)
    repo = str(Path(verifier.__file__).resolve().parents[1])
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [repo, env.get("PYTHONPATH", "")]))
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("MT_BUSINESS_TEST_PROGRESS_FILE", None)
    env.pop("MT_BUSINESS_TEST_PROGRESS_NONCE", None)
    return env


def short_limits(monkeypatch):
    monkeypatch.setattr(verifier, "BUSINESS_TEST_TIMEOUT_SECONDS", 2)
    monkeypatch.setattr(verifier, "BUSINESS_TEST_CLEANUP_GRACE_SECONDS", SHORT_CLEANUP)
    monkeypatch.setattr(verifier, "BUSINESS_TEST_TERMINATION_GRACE_SECONDS", SHORT_TERMINATION)
    monkeypatch.setattr(verifier, "BUSINESS_TEST_FINAL_DRAIN_SECONDS", SHORT_DRAIN)


def assert_shutdown(value):
    assert set(value) == SHUTDOWN_FIELDS
    assert value["strategy"] == ("linux_owned_process_group" if sys.platform == "linux" else "direct_child_fallback")
    assert value["cleanup_grace_seconds"] == SHORT_CLEANUP
    assert value["termination_grace_seconds"] == SHORT_TERMINATION
    assert value["final_drain_seconds"] == SHORT_DRAIN
    assert value["direct_child_reaped"] is True
    assert value["process_group_cleanup_verified"] is False
    assert value["database_cleanup_verified"] is False
    assert SECRET not in json.dumps(value)


def assert_timeout(value):
    assert value["status"] == "TIMEOUT" and value["exit_code"] == 2
    assert value["complete"] is False and value["timeout_seconds"] == 2
    assert value["test_count"] == 0 and value["totals"] == ZERO_TOTALS
    assert value["raw_logs_published"] is False
    assert SECRET not in json.dumps(value, ensure_ascii=False)
    assert_shutdown(value["timeout_shutdown"])


def finalizing_child(root, phase):
    tests = root / "tests/business"
    tests.mkdir(parents=True)
    cleanup = root / "finalized.txt"
    unexpected = root / "next-test-started.txt"
    (tests / "test_shutdown_fixture.py").write_text(
        "import sys\n"
        "import time\n"
        "from pathlib import Path\n"
        "import pytest\n"
        f"SECRET = {SECRET!r}\n"
        f"PHASE = {phase!r}\n"
        "@pytest.fixture\n"
        "def cleanup_fixture():\n"
        "    try:\n"
        "        if PHASE == 'setup':\n"
        "            time.sleep(30)\n"
        "        yield\n"
        "        if PHASE == 'teardown':\n"
        "            time.sleep(30)\n"
        "    finally:\n"
        f"        Path({str(cleanup)!r}).write_text('finalized', encoding='utf8')\n"
        "@pytest.mark.parametrize('label', [SECRET])\n"
        "def test_a_timeout_call(cleanup_fixture, label):\n"
        "    print(label, flush=True)\n"
        "    print(label, file=sys.stderr, flush=True)\n"
        "    if PHASE == 'call':\n"
        "        time.sleep(30)\n"
        "def test_z_must_not_start():\n"
        f"    Path({str(unexpected)!r}).write_text('not allowed', encoding='utf8')\n",
        encoding="utf8",
    )
    return cleanup, unexpected


def assert_finalized_if_supported(cleanup, unexpected, value):
    if sys.platform == "linux":
        assert cleanup.is_file(), (
            "Timed-out child pytest must receive a bounded opportunity to run its existing finalizer"
        )
        assert cleanup.read_text("utf8") == "finalized"
        assert value["timeout_shutdown"]["interrupt_attempted"] is True
    else:
        # The fallback is checked, not presented as Linux group/finalizer
        # evidence. It must never claim either group or database cleanup.
        assert value["timeout_shutdown"]["strategy"] == "direct_child_fallback"
        assert value["timeout_shutdown"]["process_group_cleanup_verified"] is False
    assert not unexpected.exists(), "The shutdown interval must not be used to start the next test"


def test_real_call_timeout_runs_finalizer_without_starting_the_next_test(tmp_path, monkeypatch):
    cleanup, unexpected = finalizing_child(tmp_path, "call")
    short_limits(monkeypatch)
    value = verifier.run_checks(tmp_path, child_environment(), tmp_path / "results.xml")
    assert_timeout(value)
    assert value["last_test_progress"] == {
        "nodeid": "tests/business/test_shutdown_fixture.py::test_a_timeout_call",
        "phase": "call",
    }
    assert_finalized_if_supported(cleanup, unexpected, value)


@pytest.mark.parametrize("phase", ["setup", "teardown"])
def test_real_setup_and_teardown_timeouts_run_finally_and_keep_deadline_checkpoint(tmp_path, monkeypatch, phase):
    cleanup, unexpected = finalizing_child(tmp_path, phase)
    short_limits(monkeypatch)
    value = verifier.run_checks(tmp_path, child_environment(), tmp_path / "results.xml")
    assert_timeout(value)
    assert value["last_test_progress"] == {
        "nodeid": "tests/business/test_shutdown_fixture.py::test_a_timeout_call",
        "phase": phase,
    }
    assert_finalized_if_supported(cleanup, unexpected, value)


def test_real_interrupted_junit_is_separate_from_canonical_suite_totals(tmp_path, monkeypatch):
    tests = tmp_path / "tests/business"
    tests.mkdir(parents=True)
    (tests / "test_partial_fixture.py").write_text(
        "import time\n"
        "def test_a_finished():\n"
        "    assert 1 == 1\n"
        "def test_b_timeout():\n"
        f"    print({SECRET!r}, flush=True)\n"
        "    time.sleep(30)\n"
        "def test_z_not_executed():\n"
        "    raise AssertionError('must not start after timeout')\n",
        encoding="utf8",
    )
    short_limits(monkeypatch)
    junit = tmp_path / "results.xml"
    value = verifier.run_checks(tmp_path, child_environment(), junit)
    assert_timeout(value)
    assert value["last_test_progress"] == {
        "nodeid": "tests/business/test_partial_fixture.py::test_b_timeout",
        "phase": "call",
    }
    if sys.platform == "linux":
        assert junit.is_file()
        assert value["interrupted_junit_observed"] is True
        assert value["partial_totals"] == verifier.test_totals(junit)
        assert value["partial_totals"]["tests"] >= 1
    else:
        assert value["interrupted_junit_observed"] is False
        assert value["partial_totals"] is None


@pytest.mark.parametrize("artifact", ["passing", "malformed", "missing"])
def test_sessionfinish_artifact_never_turns_timeout_into_complete_or_pass(tmp_path, monkeypatch, artifact):
    tests = tmp_path / "tests/business"
    tests.mkdir(parents=True)
    (tests / "test_finished_fixture.py").write_text("def test_finished():\n    assert True\n", encoding="utf8")
    junit = tmp_path / "results.xml"
    passing_xml = '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>'
    action = {
        "passing": f"path.write_text({passing_xml!r}, encoding='utf8')",
        "malformed": f"path.write_text({('malformed ' + SECRET)!r}, encoding='utf8')",
        "missing": "path.unlink(missing_ok=True)",
    }[artifact]
    (tmp_path / "conftest.py").write_text(
        "import time\nfrom pathlib import Path\nimport pytest\n"
        "@pytest.hookimpl(trylast=True)\n"
        "def pytest_sessionfinish(session):\n"
        f"    path = Path({str(junit)!r})\n"
        f"    {action}\n"
        f"    print({SECRET!r}, flush=True)\n"
        "    time.sleep(30)\n",
        encoding="utf8",
    )
    short_limits(monkeypatch)
    value = verifier.run_checks(tmp_path, child_environment(), junit)
    assert_timeout(value)
    assert value["last_test_progress"] == {
        "nodeid": "tests/business/test_finished_fixture.py::test_finished",
        "phase": "finished",
    }
    assert value["interrupted_junit_observed"] is (artifact == "passing")
    assert value["partial_totals"] == (
        {"tests": 1, "failures": 0, "errors": 0, "skipped": 0} if artifact == "passing" else None
    )


def test_normal_success_never_sends_shutdown_signals_or_invents_interrupted_junit(tmp_path, monkeypatch):
    tests = tmp_path / "tests/business"
    tests.mkdir(parents=True)
    (tests / "test_success_fixture.py").write_text(
        f"def test_finished():\n    print({SECRET!r})\n    assert True\n", encoding="utf8"
    )
    calls: list[bool] = []

    def forbidden_signal(*args):
        calls.append(True)
        raise AssertionError("A normal successful child must not receive shutdown signals")

    monkeypatch.setattr(verifier.os, "killpg", forbidden_signal, raising=False)
    value = verifier.run_checks(tmp_path, child_environment(), tmp_path / "results.xml")
    assert value["status"] == "PASS" and value["exit_code"] == 0 and value["complete"] is True
    assert value["totals"] == {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}
    assert value["timeout_shutdown"] is None
    assert value["interrupted_junit_observed"] is False and value["partial_totals"] is None
    assert calls == [] and value["raw_logs_published"] is False
    assert SECRET not in json.dumps(value)


def test_timeout_callback_failure_does_not_prevent_bounded_child_cleanup(tmp_path, monkeypatch):
    short_limits(monkeypatch)
    cleanup = tmp_path / "callback-finalized.txt"
    body = (
        "import time\nfrom pathlib import Path\ntry:\n    time.sleep(30)\nfinally:\n"
        f"    Path({str(cleanup)!r}).write_text('finalized', encoding='utf8')\n"
    )
    callbacks: list[bool] = []

    def fail_observation():
        callbacks.append(True)
        raise ValueError(SECRET)

    with pytest.raises(verifier._PytestTimeout) as error:
        verifier._run_pytest(
            [sys.executable, "-c", body],
            cwd=tmp_path,
            env=child_environment(),
            capture_output=True,
            text=True,
            timeout=2,
            on_timeout=fail_observation,
        )
    assert callbacks == [True]
    assert_shutdown(error.value.shutdown)
    assert error.value.shutdown["output_drain_completed"] is True
    if sys.platform == "linux":
        assert cleanup.read_text("utf8") == "finalized"


def test_signal_oserror_does_not_publish_error_text_or_skip_remaining_cleanup(tmp_path, monkeypatch):
    short_limits(monkeypatch)
    if sys.platform != "linux":
        # The non-Linux fallback is independently exercised by a real child;
        # Linux-only killpg fault injection cannot be claimed on this platform.
        with pytest.raises(verifier._PytestTimeout) as error:
            verifier._run_pytest(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                cwd=tmp_path,
                env=child_environment(),
                timeout=2,
            )
        assert_shutdown(error.value.shutdown)
        return
    actual = verifier.os.killpg
    calls: list[signal.Signals] = []

    def failed_interrupt(pgid, signum):
        calls.append(signum)
        if signum == signal.SIGINT:
            raise OSError(SECRET)
        return actual(pgid, signum)

    monkeypatch.setattr(verifier.os, "killpg", failed_interrupt)
    with pytest.raises(verifier._PytestTimeout) as error:
        verifier._run_pytest(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=tmp_path,
            env=child_environment(),
            timeout=2,
        )
    assert_shutdown(error.value.shutdown)
    assert signal.SIGTERM in calls and signal.SIGKILL in calls
    assert error.value.shutdown["signal_failure_count"] == 1


def process_tree_probe(root, *, parent_cooperates, escape):
    """A separate test-only subreaper owns orphans; the main pytest is unchanged."""
    child_ready = root / "descendant.json"
    parent_ready = root / "parent.json"
    child = textwrap.dedent(
        f"""
        import json, os, signal, time
        from pathlib import Path
        if {escape!r}:
            os.setsid()
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        Path({str(child_ready)!r}).write_text(json.dumps(dict(pid=os.getpid(),pgid=os.getpgrp())),encoding='utf8')
        while True:
            time.sleep(30)
        """
    )
    parent = textwrap.dedent(
        f"""
        import json, os, signal, subprocess, sys, time
        from pathlib import Path
        if not {parent_cooperates!r}:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        subprocess.Popen([sys.executable,'-c',{child!r}])
        Path({str(parent_ready)!r}).write_text(json.dumps(dict(pid=os.getpid(),pgid=os.getpgrp())),encoding='utf8')
        print({SECRET!r},flush=True)
        time.sleep(30)
        """
    )
    wrapper = textwrap.dedent(
        f"""
        import ctypes, json, os, signal, sys, time
        from pathlib import Path
        from scripts import verify_business_foundation as verifier
        libc=ctypes.CDLL(None,use_errno=True)
        if libc.prctl(36,1,0,0,0)!=0:
            raise RuntimeError('TEST_ONLY_SUBREAPER_SETUP_FAILED')
        verifier.BUSINESS_TEST_CLEANUP_GRACE_SECONDS={SHORT_CLEANUP!r}
        verifier.BUSINESS_TEST_TERMINATION_GRACE_SECONDS={SHORT_TERMINATION!r}
        verifier.BUSINESS_TEST_FINAL_DRAIN_SECONDS={SHORT_DRAIN!r}
        result={{}}
        known=[]
        try:
            try:
                verifier._run_pytest([sys.executable,'-c',{parent!r}],cwd=Path({str(root)!r}),env=dict(os.environ),timeout=2)
            except verifier._PytestTimeout as error:
                result['timeout']=True
                result['shutdown']=error.shutdown
            else:
                result['timeout']=False
            parent=json.loads(Path({str(parent_ready)!r}).read_text('utf8'))
            child=json.loads(Path({str(child_ready)!r}).read_text('utf8'))
            known=[parent['pid'],child['pid']]
            result['owned_session']=parent['pid']==parent['pgid']
            result['descendant_same_group']=child['pgid']==parent['pgid']
            try:
                waited,_=os.waitpid(child['pid'],os.WNOHANG)
            except ChildProcessError:
                waited=child['pid']
            result['descendant_running_after_shutdown']=waited==0
        finally:
            # Only children adopted by this separate reaper are signalled.
            # Record pre-cleanup state above so this safety net cannot make a
            # leaked descendant look like successful product cleanup.
            for marker in ({str(parent_ready)!r},{str(child_ready)!r}):
                try:
                    value=json.loads(Path(marker).read_text('utf8'))
                except (OSError,ValueError):
                    continue
                if type(value.get('pid')) is int and value['pid']>0 and value['pid'] not in known:
                    known.append(value['pid'])
            deadline=time.monotonic()+3
            while True:
                for pid in known:
                    try:
                        waited,_=os.waitpid(pid,os.WNOHANG)
                    except ChildProcessError:
                        continue
                    if waited==0:
                        try:
                            os.kill(pid,signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                try:
                    waited,_=os.waitpid(-1,os.WNOHANG)
                except ChildProcessError:
                    result['test_owned_orphans_reaped']=True
                    break
                if waited==0:
                    if time.monotonic()>=deadline:
                        result['test_owned_orphans_reaped']=False
                        break
                    time.sleep(0.01)
            print(json.dumps(result,sort_keys=True))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", wrapper],
        cwd=root,
        env=child_environment(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, "The separate test-owned descendant reaper must finish successfully"
    value = json.loads(result.stdout)
    assert SECRET not in json.dumps(value)
    return value


@pytest.mark.parametrize("parent_cooperates", [True, False])
def test_noncooperating_same_group_descendant_is_killed_even_after_parent_exit(
    tmp_path, monkeypatch, parent_cooperates
):
    short_limits(monkeypatch)
    if sys.platform != "linux":
        with pytest.raises(verifier._PytestTimeout) as error:
            verifier._run_pytest(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                cwd=tmp_path,
                env=child_environment(),
                timeout=2,
            )
        assert_shutdown(error.value.shutdown)
        return
    value = process_tree_probe(tmp_path, parent_cooperates=parent_cooperates, escape=False)
    assert value["timeout"] is True and value["owned_session"] is True
    assert value["descendant_same_group"] is True
    assert value["descendant_running_after_shutdown"] is False
    assert value["test_owned_orphans_reaped"] is True
    assert_shutdown(value["shutdown"])
    assert value["shutdown"]["kill_attempted"] is True
    assert value["shutdown"]["output_drain_completed"] is True


def test_escaped_session_with_open_pipe_is_bounded_and_never_claimed_cleaned(tmp_path, monkeypatch):
    short_limits(monkeypatch)
    if sys.platform != "linux":
        with pytest.raises(verifier._PytestTimeout) as error:
            verifier._run_pytest(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                cwd=tmp_path,
                env=child_environment(),
                timeout=2,
            )
        assert_shutdown(error.value.shutdown)
        return
    value = process_tree_probe(tmp_path, parent_cooperates=False, escape=True)
    assert value["timeout"] is True and value["owned_session"] is True
    assert value["descendant_same_group"] is False
    assert value["descendant_running_after_shutdown"] is True
    assert value["test_owned_orphans_reaped"] is True
    assert_shutdown(value["shutdown"])
    assert value["shutdown"]["output_drain_completed"] is False
