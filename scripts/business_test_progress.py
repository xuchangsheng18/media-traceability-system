"""Private bounded pytest progress for the full business verifier only."""

import json
import os
import re
from pathlib import Path

import pytest


def _record(nodeid: str, phase: str) -> None:
    path_value = os.environ.get("MT_BUSINESS_TEST_PROGRESS_FILE")
    nonce = os.environ.get("MT_BUSINESS_TEST_PROGRESS_NONCE", "")
    if not path_value or re.fullmatch(r"[a-f0-9]{32}", nonce) is None:
        return
    # Do not write parameter IDs, captured output or fixture values, even privately.
    parts = nodeid.split("[", 1)[0].split("::")
    if len(parts) not in {2, 3} or re.fullmatch(r"tests/business/test_[A-Za-z0-9_]+\.py", parts[0]) is None:
        return
    if re.fullmatch(r"test_[A-Za-z0-9_]+", parts[-1]) is None:
        return
    if len(parts) == 3 and re.fullmatch(r"Test[A-Za-z0-9_]+", parts[1]) is None:
        return
    module = parts[0][:-3].replace("/", ".")
    value = dict(
        classname=module + ("." + parts[1] if len(parts) == 3 else ""), name=parts[-1], phase=phase, nonce=nonce
    )
    path = Path(path_value)
    pending = path.with_suffix(".pending")
    try:
        if path.is_symlink() or pending.is_symlink():
            return
        pending.write_text(json.dumps(value), encoding="utf8")
        pending.replace(path)
    except OSError:
        # Losing a diagnostic must not change the tested operation or its outcome.
        return


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    _record(item.nodeid, "setup")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item: pytest.Item) -> None:
    _record(item.nodeid, "call")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item: pytest.Item) -> None:
    _record(item.nodeid, "teardown")


def pytest_runtest_logfinish(nodeid: str) -> None:
    _record(nodeid, "finished")
