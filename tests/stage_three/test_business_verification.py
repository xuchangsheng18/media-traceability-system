import importlib.util
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "business_verification", Path(__file__).resolve().parents[2] / "scripts/verify_business_foundation.py"
)
assert spec is not None and spec.loader is not None
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


def test_verification_requires_isolated_target():
    with pytest.raises(RuntimeError, match="EXPLICIT"):
        tools.validate_target({})
    with pytest.raises(RuntimeError, match="POC"):
        tools.validate_target(
            {"MT_BUSINESS_TEST_ADMIN_DSN": "dbname=media_trace_poc", "MT_BUSINESS_TEST_BROKER_URL": "amqp://test"}
        )


def test_failed_business_check_returns_nonzero(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "_run_pytest", lambda *args, **kwargs: subprocess.CompletedProcess(args, 1, "", ""))
    report = tools.run_checks(tmp_path, {}, tmp_path / "report.xml")
    assert report["exit_code"] != 0 and report["status"] == "FAIL"
    assert report["test_count"] == 0
