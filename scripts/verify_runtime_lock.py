"""Detect third-party dependency drift in the explicitly selected Miniforge runtime."""
import hashlib
import importlib.metadata
import json
import platform
from typing import TYPE_CHECKING

from packaging.utils import canonicalize_name
if TYPE_CHECKING:
    from scripts.poc_control import ROOT
else:
    from poc_control import ROOT


def main():
    path = ROOT/"config/locks/requirements-py310.lock"
    expected = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith(("#", "--")):
            continue
        name, version = line.split("==", 1)
        expected[canonicalize_name(name)] = version
    installed = {canonicalize_name(d.metadata["Name"]): d.version for d in importlib.metadata.distributions()
                 if canonicalize_name(d.metadata["Name"]) != "media-trace-poc"}
    assert platform.python_version() == "3.10.22", "PYTHON_PATCH_VERSION_DRIFT"
    differences = [{"name": name, "expected": expected.get(name), "installed": installed.get(name)}
                   for name in sorted(set(expected)|set(installed)) if expected.get(name) != installed.get(name)]
    report = {"status": "FAIL" if differences else "PASS", "python": platform.python_version(),
              "third_party_packages": len(expected), "lock_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "differences": differences}
    (ROOT/"docs/00-project/validation/runtime-lock-report.json").write_text(json.dumps(report, indent=2)+"\n")
    assert not differences, "DEPENDENCY_LOCK_DRIFT"
    return report


if __name__ == "__main__":
    print(json.dumps(main()))
