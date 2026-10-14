import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "changed,dirty,metadata",
    [
        (b" M config/locks/runtime-archive.json\0", False, True),
        (b" M config/locks/runtime-archive.json\0 M config/mypy.ini\0", True, True),
        (b" M backend/business_app/main.py\0", True, False),
    ],
)
def test_source_identity_separates_generated_archive_metadata(monkeypatch, changed, dirty, metadata):
    module = load_types()
    monkeypatch.setattr(module.subprocess, "check_output", lambda *args, **kwargs: changed)
    state = module.source_tree_state(ROOT)
    assert state["source_code_dirty"] is dirty
    assert bool(state["build_metadata_changes"]) is metadata


def load_types():
    source = ROOT / "scripts/stage_three_types.py"
    assert source.is_file(), "independent Python type tool entry is not implemented"
    spec = importlib.util.spec_from_file_location("stage_three_types", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bad_artifact_digest_rejected(tmp_path):
    tools = load_types()
    wheel = tmp_path / "example-1.0-py3-none-any.whl"
    wheel.write_bytes(b"original")
    checksum = hashlib.sha256(b"original").hexdigest()
    lock = tmp_path / "requirements.lock"
    lock.write_text(f"example==1.0 --hash=sha256:{checksum}\n")
    artifacts = tmp_path / "artifacts.json"
    artifacts.write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "name": "example",
                        "version": "1.0",
                        "filename": wheel.name,
                        "sha256": checksum,
                        "local_path": str(wheel),
                    }
                ]
            }
        )
    )
    tools.verify_artifacts(lock, artifacts)
    wheel.write_bytes(b"corrupted")
    with pytest.raises(RuntimeError, match="ARTIFACT_DIGEST"):
        tools.verify_artifacts(lock, artifacts)


def test_runtime_target_inside_repo_rejected():
    tools = load_types()
    with pytest.raises(RuntimeError, match="OUTSIDE_SOURCE"):
        tools.setup_type_environment(ROOT / "bad-type-runtime", Path(sys.executable))
    assert not (ROOT / "bad-type-runtime").exists()


def test_runtime_symlink_rejected(tmp_path):
    tools = load_types()
    target = tmp_path / "private"
    target.mkdir()
    link = tmp_path / "linked-runtime"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(RuntimeError, match="SYMLINK"):
        tools.setup_type_environment(link, Path(sys.executable))


def type_python():
    tools = load_types()
    return tools.RUNTIME / "stage-three-type-tools/bin/python"


def test_type_error_returns_nonzero(tmp_path):
    tools = load_types()
    source = tmp_path / "wrong.py"
    source.write_text('value: int = "wrong"\n')
    assert hasattr(tools, "run_type_check"), "real Python type check is not implemented"
    result = tools.run_type_check(type_python(), tmp_path)
    assert result.returncode != 0
    assert "assignment" in result.stdout


def test_new_business_directory_included(tmp_path):
    tools = load_types()
    folder = tmp_path / "backend/business_app"
    folder.mkdir(parents=True)
    (folder / "handler.py").write_text('value: int = "wrong"\n')
    assert hasattr(tools, "run_type_check"), "new business directories have no type check"
    result = tools.run_type_check(type_python(), tmp_path)
    assert result.returncode != 0
    assert "backend/business_app/handler.py" in result.stdout


def test_valid_module_passes(tmp_path):
    tools = load_types()
    (tmp_path / "correct.py").write_text("value: int = 1\n")
    assert hasattr(tools, "run_type_check")
    assert tools.run_type_check(type_python(), tmp_path).returncode == 0


def test_type_failure_propagates_to_dev_command(monkeypatch, capfd):
    monkeypatch.setenv("MT_TYPE_REPORT_DISABLED", "1")
    spec = importlib.util.spec_from_file_location("type_dev_entry", ROOT / "scripts/dev.py")
    assert spec is not None and spec.loader is not None
    dev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev)
    monkeypatch.setattr(dev, "python", lambda: sys.executable)
    probe = ROOT / "backend/app/_controlled_type_failure_probe.py"
    assert not probe.exists()
    try:
        probe.write_text('value: int = "wrong"\n')
        assert dev.main(["type-check"]) != 0
        observed = capfd.readouterr()
        assert "_controlled_type_failure_probe.py" in observed.out
        assert "assignment" in observed.out
    finally:
        probe.unlink(missing_ok=True)


@pytest.mark.parametrize("linked_bin", [False, True])
def test_existing_nonvenv_python_never_installs(tmp_path, monkeypatch, linked_bin):
    tools = load_types()
    marker = tmp_path / "install-was-called"
    target = tmp_path / "stage-three-type-tools/bin"
    target.parent.mkdir(parents=True)
    if linked_bin:
        linked = tmp_path / "controlled-other-bin"
        linked.mkdir()
        target.symlink_to(linked, target_is_directory=True)
    else:
        target.mkdir()
    (target.parent / "pyvenv.cfg").write_text("include-system-site-packages = true\n")
    wrapper = target / "python"
    wrapper.write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "-m" ] && [ "$2" = "pip" ] && [ "$3" = "install" ]; then touch "{marker}"; exit 0; fi\n'
        f'exec "{sys.executable}" "$@"\n'
    )
    wrapper.chmod(0o700)
    cache = tmp_path / "stage-three-type-artifacts"
    cache.mkdir()
    wheel = cache / "example.whl"
    wheel.write_bytes(b"fixture")
    digest = hashlib.sha256(b"fixture").hexdigest()
    artifacts = tmp_path / "artifacts.json"
    artifacts.write_text(
        json.dumps({"artifacts": [{"name": "example", "version": "1.0", "filename": wheel.name, "sha256": digest}]})
    )
    lock = tmp_path / "requirements.lock"
    lock.write_text(f"example==1.0 --hash=sha256:{digest}\n")
    monkeypatch.setattr(tools, "ARTIFACTS", artifacts)
    monkeypatch.setattr(tools, "LOCK", lock)
    try:
        tools.setup_type_environment(tmp_path, Path(sys.executable))
    except (RuntimeError, subprocess.CalledProcessError):
        pass
    assert not marker.exists(), "non-venv executable reached pip installation"
