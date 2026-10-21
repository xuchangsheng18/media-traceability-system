"""Linux directory barriers with real files and deterministic I/O faults."""

import errno
import hashlib
import io
import json
import os
import stat
from pathlib import Path
from uuid import uuid4

import pytest
from business_app.objects import FileObjectStore
from business_app.types import Actor, Scope


def scope():
    return Scope(Actor(uuid4(), uuid4()), uuid4())


def directory_path(descriptor):
    return Path(os.readlink(f"/proc/self/fd/{descriptor}"))


def assert_closed(descriptors):
    for descriptor in descriptors:
        with pytest.raises(OSError) as raised:
            os.fstat(descriptor)
        assert raised.value.errno == errno.EBADF


def test_object_return_follows_file_object_directory_and_root_barriers(tmp_path, monkeypatch):
    store = FileObjectStore(tmp_path / "objects")
    original = os.fsync
    synchronized, directory_descriptors = [], []

    def trace(descriptor):
        synchronized.append(directory_path(descriptor))
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            directory_descriptors.append(descriptor)
        original(descriptor)

    monkeypatch.setattr(os, "fsync", trace)
    stored = store.put_part(scope(), uuid4(), 1, io.BytesIO(b"self-owned-bytes"))
    folder = store.root / str(stored.ref.object_id)
    assert synchronized == [folder / (stored.ref.version_id + ".bin"), folder, store.root]
    assert b"".join(store.read(stored.ref)) == b"self-owned-bytes"
    assert_closed(directory_descriptors)


@pytest.mark.parametrize("target", ["object_directory", "root"])
def test_directory_barrier_failure_never_returns_stored_object(tmp_path, monkeypatch, target):
    store = FileObjectStore(tmp_path / "objects")
    original = os.fsync
    descriptors = []

    def fail(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            descriptors.append(descriptor)
            selected = directory_path(descriptor)
            if (selected == store.root) == (target == "root"):
                raise OSError(errno.EIO, "synthetic-directory-sync-failure")
        original(descriptor)

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError, match="synthetic-directory-sync-failure"):
        store.put_part(scope(), uuid4(), 1, io.BytesIO(b"ABC"))
    blobs, receipts = list(store.root.rglob("*.bin")), list(store.root.rglob("*.orphan.json"))
    assert len(blobs) == len(receipts) == 1 and blobs[0].read_bytes() == b"ABC"
    record = json.loads(receipts[0].read_text())
    assert record["sha256"] == hashlib.sha256(b"ABC").hexdigest() and record["size_bytes"] == 3
    assert record["automatic_data_deletion"] is False
    assert_closed(descriptors)


def test_nested_root_creation_syncs_each_directory_before_creating_its_child(tmp_path, monkeypatch):
    root = tmp_path / "new" / "runtime" / "objects"
    original = os.fsync
    synchronized, descriptors = [], []

    def trace(descriptor):
        selected = directory_path(descriptor)
        synchronized.append(selected)
        descriptors.append(descriptor)
        if selected == tmp_path / "new" and synchronized.count(selected) == 1:
            assert not (selected / "runtime").exists()
        original(descriptor)

    monkeypatch.setattr(os, "fsync", trace)
    assert FileObjectStore(root).root == root
    assert synchronized == [
        tmp_path,
        tmp_path.parent,
        root.parents[1],
        tmp_path,
        root.parent,
        root.parents[1],
        root,
        root.parent,
    ]
    assert_closed(descriptors)


@pytest.mark.parametrize("target", ["new_directory", "parent_entry"])
def test_failed_root_initialization_is_refused_and_retry_resyncs_anchor(tmp_path, monkeypatch, target):
    root = tmp_path / "new" / "objects"
    original = os.fsync
    failed_once = False
    descriptors = []

    def fail_once(descriptor):
        nonlocal failed_once
        selected = directory_path(descriptor)
        descriptors.append(descriptor)
        selected_target = root.parent if target == "new_directory" else tmp_path
        if root.parent.is_dir() and selected == selected_target and not failed_once:
            failed_once = True
            raise OSError(errno.EIO, "synthetic-root-initialization-sync-failure")
        original(descriptor)

    monkeypatch.setattr(os, "fsync", fail_once)
    with pytest.raises(OSError, match="synthetic-root-initialization-sync-failure"):
        FileObjectStore(root)
    assert failed_once and root.parent.is_dir() and not root.exists()
    assert_closed(descriptors)
    assert FileObjectStore(root).root == root
    assert_closed(descriptors)


def test_directory_barriers_are_not_silently_skipped_on_unsupported_runtime(tmp_path, monkeypatch):
    with monkeypatch.context() as isolated:
        isolated.delattr(os, "O_DIRECTORY")
        with pytest.raises(RuntimeError, match="PRIVATE_OBJECT_DURABILITY_UNSUPPORTED"):
            FileObjectStore(tmp_path / "objects")
