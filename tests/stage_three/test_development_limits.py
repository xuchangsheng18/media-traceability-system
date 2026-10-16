"""Checks of actual cgroup limits must reject drift, unlimited and missing values."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def verifier():
    path = ROOT / "scripts/verify_development_limits.py"
    assert path.is_file(), "read-only cgroup verification is missing"
    spec = importlib.util.spec_from_file_location("development_limits", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("cpus", [1, 0.5])
def test_real_kernel_limits_match_declared_limits(cpus):
    module = verifier()
    host = {"memory": 268435456, "nano_cpus": int(cpus * 1e9), "pids": 64}
    kernel = f"268435456\n{int(cpus * 100000)} 100000\n64\n"
    assert module.check_limits({"mem_limit": "256m", "cpus": cpus, "pids_limit": 64}, host, kernel)


@pytest.mark.parametrize(
    "kernel",
    [
        "max\n100000 100000\n64\n",
        "268435456\nmax 100000\n64\n",
        "268435456\n100000 100000\nmax\n",
        "134217728\n100000 100000\n64\n",
        "268435456\n50000 100000\n64\n",
        "268435456\n100000 100000\n32\n",
        "268435456\n100000 0\n64\n",
        "",
        "not kernel data",
    ],
)
def test_unlimited_drift_or_unreadable_kernel_limits_are_rejected(kernel):
    module = verifier()
    assert not module.check_limits(
        {"mem_limit": "256m", "cpus": 1, "pids_limit": 64},
        {"memory": 268435456, "nano_cpus": 1000000000, "pids": 64},
        kernel,
    )


@pytest.mark.parametrize("field", ["memory", "nano_cpus", "pids"])
def test_inspect_configuration_alone_is_insufficient(field):
    module = verifier()
    host = {"memory": 268435456, "nano_cpus": 1000000000, "pids": 64}
    host[field] = 0
    assert not module.check_limits(
        {"mem_limit": "256m", "cpus": 1, "pids_limit": 64},
        host,
        "268435456\n100000 100000\n64\n",
    )
