"""Restart readiness requires readable object bytes, not just a bucket listing."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
readiness = importlib.import_module("storage_readiness")


class StorageError(Exception):
    def __init__(self, status):
        self.response = {"ResponseMetadata": {"HTTPStatusCode": status}}


class Storage:
    def __init__(self, failures, status=500):
        self.failures = failures
        self.status = status
        self.calls = []

    def get_object(self, **kwargs):
        import io

        self.calls.append(kwargs)
        if len(self.calls) <= self.failures:
            raise StorageError(self.status)
        return {"Body": io.BytesIO(b"exact-version-bytes")}


def test_transient_object_unavailability_retries_exact_version(monkeypatch):
    pauses = []
    monkeypatch.setattr(readiness.time, "sleep", pauses.append)
    storage = Storage(2)
    result = readiness.read_version_after_restart(storage, "bucket", "vector", "version-1", attempts=3)
    assert result == b"exact-version-bytes"
    assert storage.calls == [{"Bucket": "bucket", "Key": "vector", "VersionId": "version-1"}] * 3
    assert pauses == [1, 1]


@pytest.mark.parametrize("status", [403, 404])
def test_permission_and_missing_version_errors_are_not_retried(monkeypatch, status):
    monkeypatch.setattr(readiness.time, "sleep", lambda _: pytest.fail("must not retry"))
    storage = Storage(10, status)
    with pytest.raises(StorageError):
        readiness.read_version_after_restart(storage, "bucket", "vector", "version-1", attempts=3)
    assert len(storage.calls) == 1


def test_persistent_storage_error_fails_at_bound(monkeypatch):
    monkeypatch.setattr(readiness.time, "sleep", lambda _: None)
    storage = Storage(10)
    with pytest.raises(StorageError):
        readiness.read_version_after_restart(storage, "bucket", "vector", "version-1", attempts=3)
    assert len(storage.calls) == 3


def test_zero_attempts_is_rejected():
    with pytest.raises(ValueError):
        readiness.read_version_after_restart(Storage(0), "bucket", "vector", "version-1", attempts=0)
