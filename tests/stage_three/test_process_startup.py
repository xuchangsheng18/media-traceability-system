"""Exercise actual process entrypoints using self-owned unreachable configuration."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("profile", ["production", "invalid-profile"])
@pytest.mark.parametrize("entry", ["worker", "inference"])
def test_process_rejects_profile_before_broker_or_model_start(profile, entry, tmp_path):
    env = dict(os.environ, MT_RUNTIME_PROFILE=profile, PYTHONPATH=str(ROOT / "backend"))
    env.update(
        {
            "DATABASE_URL": "postgresql+psycopg://unused:synthetic-only@127.0.0.1:1/unused",
            "BROKER_URL": "amqp://unused:synthetic-only@127.0.0.1:1/unused",
            "S3_ENDPOINT": "http://127.0.0.1:1",
            "INFERENCE_URL": "http://127.0.0.1:1",
            "S3_ACCESS_KEY": "self-owned-key-" * 4,
            "S3_SECRET_KEY": "self-owned-secret-" * 4,
            "POC_API_TOKEN": "self-owned-api-" * 4,
            "INTERNAL_TOKEN": "self-owned-internal-" * 4,
            "MODEL_DIR": str(tmp_path),
        }
    )
    if entry == "worker":
        code = "import app.worker; raise RuntimeError('WORKER_IMPORT_WRONGLY_ALLOWED')"
    else:
        code = "\n".join(
            [
                "import sys",
                f"sys.path.insert(0, {str(ROOT / 'ai-services/inference')!r})",
                "import service",
                "from fastapi.testclient import TestClient",
                "def reject_model_initialization(): raise RuntimeError('MODEL_INITIALIZATION_WRONGLY_ALLOWED')",
                "service.initialize_model = reject_model_initialization",
                "with TestClient(service.app): pass",
            ]
        )
    run = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    expected = "PRODUCTION_PROFILE_NOT_APPROVED" if profile == "production" else "CONFIGURATION_INVALID"
    assert run.returncode != 0 and expected in run.stderr
    assert "WRONGLY_ALLOWED" not in run.stderr
    assert list(tmp_path.iterdir()) == []
