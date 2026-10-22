"""Real child pytest timeout diagnostics; no database or runtime timeout override."""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from scripts import verify_business_foundation as verifier

MARKER = "SYNTHETIC_UNPUBLISHED_TIMEOUT_SECRET"
SELECTOR = "tests/business/test_fixture.py::test_public_case"
NONCE = "a" * 32


def child_environment():
    env = dict(os.environ)
    repo = str(Path(verifier.__file__).resolve().parents[1])
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [repo, env.get("PYTHONPATH", "")]))
    # The diagnostic plugin is explicitly loaded by the verifier. Unrelated
    # installed plugins must not consume this deliberately short test budget.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("MT_BUSINESS_TEST_PROGRESS_FILE", None)
    env.pop("MT_BUSINESS_TEST_PROGRESS_NONCE", None)
    return env


def source(root, body):
    path = root / "tests/business/test_fixture.py"
    path.parent.mkdir(parents=True)
    path.write_text(body, encoding="utf8")
    return path


def readable_source(root):
    return source(root, "def test_public_case():\n    assert True\n")


def assert_no_private_output(value):
    assert MARKER not in json.dumps(value, ensure_ascii=False)
    assert value["raw_logs_published"] is False


def test_production_timeout_remains_exactly_1800_seconds():
    assert verifier.BUSINESS_TEST_TIMEOUT_SECONDS == 1800


@pytest.mark.parametrize("phase", ["setup", "call", "teardown"])
def test_real_child_timeout_retains_safe_current_stage_without_fabricated_totals(tmp_path, monkeypatch, phase):
    source(
        tmp_path,
        "import sys\n"
        "import time\n"
        "import pytest\n"
        f"MARKER = {MARKER!r}\n"
        f"SLOW_PHASE = {phase!r}\n"
        "@pytest.fixture\n"
        "def slow_fixture():\n"
        "    print(MARKER, flush=True)\n"
        "    if SLOW_PHASE == 'setup':\n"
        "        time.sleep(30)\n"
        "    yield\n"
        "    print(MARKER, file=sys.stderr, flush=True)\n"
        "    if SLOW_PHASE == 'teardown':\n"
        "        time.sleep(30)\n"
        "@pytest.mark.parametrize('label', [MARKER])\n"
        "def test_public_case(slow_fixture, label):\n"
        "    print(label, flush=True)\n"
        "    if SLOW_PHASE == 'call':\n"
        "        time.sleep(30)\n"
        "    assert label == MARKER\n",
    )
    monkeypatch.setattr(verifier, "BUSINESS_TEST_TIMEOUT_SECONDS", 2)
    junit = tmp_path / "results.xml"
    value = verifier.run_checks(tmp_path, child_environment(), junit)
    assert value["status"] == "TIMEOUT"
    assert value["exit_code"] == 2
    assert value["complete"] is False
    assert value["timeout_seconds"] == 2
    assert value["test_count"] == 0
    assert value["last_test_progress"] == {"nodeid": SELECTOR, "phase": phase}
    assert_no_private_output(value)


@pytest.mark.parametrize("outcome", ["pass", "failure", "skip"])
def test_real_child_terminal_results_preserve_existing_gate_and_complete_junit(tmp_path, outcome):
    statement = {
        "pass": "assert 2 + 2 == 4",
        "failure": "raise RuntimeError(MARKER)",
        "skip": "pytest.skip(MARKER)",
    }[outcome]
    source(
        tmp_path,
        "import sys\n"
        "import pytest\n"
        f"MARKER = {MARKER!r}\n"
        "@pytest.mark.parametrize('label', [MARKER])\n"
        "def test_public_case(label):\n"
        "    print(label, flush=True)\n"
        "    print(label, file=sys.stderr, flush=True)\n"
        f"    {statement}\n",
    )
    value = verifier.run_checks(tmp_path, child_environment(), tmp_path / "results.xml")
    assert value["status"] == ("PASS" if outcome == "pass" else "FAIL")
    assert value["exit_code"] == (0 if outcome == "pass" else 1)
    assert value["complete"] is True
    assert value["test_count"] == 1
    assert value["totals"] == {
        "tests": 1,
        "failures": int(outcome == "failure"),
        "errors": 0,
        "skipped": int(outcome == "skip"),
    }
    assert value["failure_diagnostics"]["items"] == (
        [{"nodeid": SELECTOR, "kind": "failure", "testcase_index": 0}] if outcome == "failure" else []
    )
    assert_no_private_output(value)


def test_normal_child_without_junit_cannot_claim_complete_or_pass(tmp_path, monkeypatch):
    readable_source(tmp_path)
    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, MARKER, MARKER),
    )
    value = verifier.run_checks(tmp_path, child_environment(), tmp_path / "missing.xml")
    assert value["status"] == "FAIL"
    assert value["exit_code"] != 0
    assert value["complete"] is False
    assert value["test_count"] == 0
    assert_no_private_output(value)


def test_timeout_after_last_test_finished_does_not_claim_completed_suite(tmp_path, monkeypatch):
    readable_source(tmp_path)
    (tmp_path / "conftest.py").write_text(
        "import time\ndef pytest_sessionfinish(session):\n    time.sleep(30)\n", encoding="utf8"
    )
    monkeypatch.setattr(verifier, "BUSINESS_TEST_TIMEOUT_SECONDS", 2)
    value = verifier.run_checks(tmp_path, child_environment(), tmp_path / "results.xml")
    assert value["status"] == "TIMEOUT" and value["exit_code"] == 2
    assert value["complete"] is False
    assert value["last_test_progress"] == {"nodeid": SELECTOR, "phase": "finished"}


@pytest.mark.parametrize("junit_kind", ["missing", "malformed", "valid"])
def test_timeout_never_publishes_exception_output_or_passes_from_junit(tmp_path, monkeypatch, junit_kind):
    readable_source(tmp_path)
    junit = tmp_path / "results.xml"

    def expired_child(command, **kwargs):
        if junit_kind != "missing":
            junit.write_text(
                "not XML " + MARKER
                if junit_kind == "malformed"
                else '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>',
                encoding="utf8",
            )
        raise subprocess.TimeoutExpired(MARKER, kwargs["timeout"], output=MARKER, stderr=MARKER)

    monkeypatch.setattr(verifier.subprocess, "run", expired_child)
    value = verifier.run_checks(tmp_path, child_environment(), junit)
    assert value["status"] == "TIMEOUT" and value["exit_code"] == 2
    assert value["complete"] is False and value["last_test_progress"] is None
    assert value["timeout_seconds"] == 1800
    assert_no_private_output(value)


def test_each_run_owns_a_new_progress_nonce_instead_of_reusing_caller_values(tmp_path, monkeypatch):
    readable_source(tmp_path)
    seen = []

    def completed_child(command, **kwargs):
        env = kwargs["env"]
        nonce = env["MT_BUSINESS_TEST_PROGRESS_NONCE"]
        assert re.fullmatch(r"[a-f0-9]{32}", nonce)
        assert nonce != NONCE
        assert nonce not in seen
        seen.append(nonce)
        progress = Path(env["MT_BUSINESS_TEST_PROGRESS_FILE"])
        progress.write_text(
            json.dumps(
                {
                    "classname": "tests.business.test_fixture",
                    "name": "test_public_case",
                    "phase": "finished",
                    "nonce": nonce,
                }
            ),
            encoding="utf8",
        )
        junit = Path(command[command.index("--junitxml") + 1])
        junit.write_text(
            '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0">'
            '<testcase classname="tests.business.test_fixture" name="test_public_case"/>'
            "</testsuite></testsuites>",
            encoding="utf8",
        )
        return subprocess.CompletedProcess(command, 0, MARKER, MARKER)

    monkeypatch.setattr(verifier.subprocess, "run", completed_child)
    env = dict(child_environment(), MT_BUSINESS_TEST_PROGRESS_NONCE=NONCE)
    for index in range(2):
        value = verifier.run_checks(tmp_path, env, tmp_path / f"complete-{index}.xml")
        assert value["status"] == "PASS"
        assert value["complete"] is True
        assert_no_private_output(value)
    assert len(seen) == 2
    assert env["MT_BUSINESS_TEST_PROGRESS_NONCE"] == NONCE


@pytest.mark.parametrize("phase", ["setup", "call", "teardown", "finished"])
def test_progress_reader_accepts_only_existing_source_selector_and_phase(tmp_path, phase):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    path.write_text(
        json.dumps(
            {"classname": "tests.business.test_fixture", "name": "test_public_case", "phase": phase, "nonce": NONCE}
        ),
        encoding="utf8",
    )
    assert verifier.last_test_progress(tmp_path, path, NONCE) == {"nodeid": SELECTOR, "phase": phase}


def test_progress_reader_missing_file_does_not_invent_current_test(tmp_path):
    readable_source(tmp_path)
    assert verifier.last_test_progress(tmp_path, tmp_path / "absent.json", NONCE) is None


@pytest.mark.parametrize(
    "raw",
    [
        b"not-json",
        b"\xff",
        b"null",
        b"[]",
        b"{}",
        b'{"classname":"tests.business.test_fixture","name":"test_unknown","phase":"call"}',
        b'{"classname":"tests.business.test_missing","name":"test_public_case","phase":"call"}',
        b'{"classname":"outside.test_fixture","name":"test_public_case","phase":"call"}',
        b'{"classname":"../../outside","name":"test_public_case","phase":"call"}',
        b'{"classname":"tests.business.test_fixture","name":"test_public_case","phase":"unknown"}',
        b'{"classname":7,"name":"test_public_case","phase":"call"}',
        b'{"classname":"tests.business.test_fixture","name":false,"phase":"call"}',
        b'{"classname":"tests.business.test_fixture","name":"test_public_case","phase":null}',
    ],
)
def test_progress_reader_rejects_missing_malformed_or_unknown_checkpoint(tmp_path, raw):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        pass
    else:
        if isinstance(value, dict):
            value["nonce"] = NONCE
            raw = json.dumps(value).encode("utf8")
    path.write_bytes(raw)
    assert verifier.last_test_progress(tmp_path, path, NONCE) is None


def test_reader_never_publishes_parameters_even_if_checkpoint_is_tampered(tmp_path):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    path.write_text(
        json.dumps(
            {
                "classname": "tests.business.test_fixture",
                "name": "test_public_case[" + MARKER + "]",
                "phase": "call",
                "nonce": NONCE,
            }
        ),
        encoding="utf8",
    )
    value = verifier.last_test_progress(tmp_path, path, NONCE)
    # Rejecting the malformed checkpoint or rechecking its parameter-free
    # source identity are both safe. Never publish its raw name or parameters.
    assert value is None or value == {"nodeid": SELECTOR, "phase": "call"}
    assert MARKER not in json.dumps(value)


@pytest.mark.parametrize("nonce", [None, False, 7, "", "a" * 31, "A" * 32, "g" * 32, "b" * 32])
def test_reader_refuses_absent_malformed_or_another_invocation_nonce(tmp_path, nonce):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    value = {"classname": "tests.business.test_fixture", "name": "test_public_case", "phase": "call"}
    if nonce is not None:
        value["nonce"] = nonce
    path.write_text(json.dumps(value), encoding="utf8")
    assert verifier.last_test_progress(tmp_path, path, NONCE) is None


@pytest.mark.parametrize("expected_nonce", [None, False, 7, "", "a" * 31, "A" * 32, "g" * 32])
def test_reader_requires_a_valid_expected_nonce(tmp_path, expected_nonce):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    path.write_text(
        json.dumps(
            {"classname": "tests.business.test_fixture", "name": "test_public_case", "phase": "call", "nonce": NONCE}
        ),
        encoding="utf8",
    )
    assert verifier.last_test_progress(tmp_path, path, expected_nonce) is None


def test_reader_refuses_additional_fields_in_an_otherwise_valid_checkpoint(tmp_path):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    path.write_text(
        json.dumps(
            {
                "classname": "tests.business.test_fixture",
                "name": "test_public_case",
                "phase": "call",
                "nonce": NONCE,
                "raw_output": MARKER,
            }
        ),
        encoding="utf8",
    )
    assert verifier.last_test_progress(tmp_path, path, NONCE) is None


def test_reader_refuses_over_budget_semantically_valid_checkpoint(tmp_path):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    path.write_text(
        " " * 4097
        + json.dumps(
            {"classname": "tests.business.test_fixture", "name": "test_public_case", "phase": "call", "nonce": NONCE}
        ),
        encoding="utf8",
    )
    assert verifier.last_test_progress(tmp_path, path, NONCE) is None


def test_reader_refuses_deeply_nested_json_within_byte_budget(tmp_path):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    raw = b"[" * 1100 + b"0" + b"]" * 1100
    assert len(raw) < 4096
    path.write_bytes(raw)
    assert verifier.last_test_progress(tmp_path, path, NONCE) is None


def test_reader_refuses_checkpoint_reported_as_symlink_without_reading_it(tmp_path, monkeypatch):
    readable_source(tmp_path)
    path = tmp_path / "latest.json"
    path.write_text(
        json.dumps(
            {"classname": "tests.business.test_fixture", "name": "test_public_case", "phase": "call", "nonce": NONCE}
        ),
        encoding="utf8",
    )
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda current: current == path or original(current))
    assert verifier.last_test_progress(tmp_path, path, NONCE) is None
