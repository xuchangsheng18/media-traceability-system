"""Real private files with deterministic I/O faults, never a storage-success mock."""

import hashlib
import io
import json
from pathlib import Path
from uuid import uuid4

import pytest
from business_app.objects import FileObjectStore
from business_app.types import Actor, Scope


def test_partial_system_write_orphan_hash_describes_actual_surviving_bytes(tmp_path, monkeypatch):
    store = FileObjectStore(tmp_path / "objects")
    original = Path.open

    class InterruptedWrite:
        def __init__(self, path, *args, **kwargs):
            self.output = original(path, *args, **kwargs)

        def __enter__(self):
            return self

        def write(self, block):
            self.output.write(block[:1])
            self.output.flush()
            raise OSError("synthetic-write-failed-after-one-real-byte")

        def __exit__(self, *args):
            self.output.close()

    def faulty_open(path, *args, **kwargs):
        if path.suffix == ".bin" and args == ("xb",):
            return InterruptedWrite(path, *args, **kwargs)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", faulty_open)
    with pytest.raises(OSError, match="one-real-byte"):
        store.put_part(Scope(Actor(uuid4(), uuid4()), uuid4()), uuid4(), 1, io.BytesIO(b"ABC"))
    blobs = list(store.root.rglob("*.bin"))
    orphans = list(store.root.rglob("*.orphan.json"))
    assert len(blobs) == len(orphans) == 1
    assert blobs[0].read_bytes() == b"A"
    record = json.loads(orphans[0].read_text())
    assert record["size_bytes"] == 1
    assert record["sha256"] == hashlib.sha256(b"A").hexdigest()
    assert record["reason"] == "OBJECT_WRITE_INCOMPLETE"
