"""Private immutable file versions for isolated development; S3 deployment is separate."""

import hashlib
import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import UUID, uuid4

from .types import ObjectRef, Scope


@dataclass(frozen=True)
class StoredObject:
    ref: ObjectRef
    size_bytes: int


class ObjectStore(Protocol):
    def put_part(self, scope: Scope, upload_id: UUID, part_no: int, body: BinaryIO) -> StoredObject: ...

    def read(self, ref: ObjectRef) -> Iterator[bytes]: ...


class FileObjectStore:
    def __init__(self, root: Path) -> None:
        if any(path.is_symlink() for path in [root, *root.parents]):
            raise RuntimeError("PRIVATE_OBJECT_DIRECTORY_SYMLINK_REJECTED")
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def put_part(self, scope: Scope, upload_id: UUID, part_no: int, body: BinaryIO) -> StoredObject:
        object_id, version = uuid4(), "fs-v1-" + uuid4().hex
        folder = self.root / str(object_id)
        folder.mkdir(mode=0o700)
        file = folder / (version + ".bin")
        digest = hashlib.sha256()
        count = 0
        try:
            with file.open("xb") as output:
                os.chmod(file, 0o600)
                for block in iter(lambda: body.read(1024 * 1024), b""):
                    written = output.write(block)
                    digest.update(block[:written])
                    count += written
                    if written != len(block):
                        raise OSError("OBJECT_WRITE_INCOMPLETE")
                output.flush()
                os.fsync(output.fileno())
        except Exception:
            if file.is_file():
                self.record_orphan(
                    StoredObject(ObjectRef(object_id, version, digest.hexdigest()), count),
                    scope,
                    upload_id,
                    "OBJECT_WRITE_INCOMPLETE",
                )
            raise
        return StoredObject(ObjectRef(object_id, version, digest.hexdigest()), count)

    def record_orphan(
        self,
        stored: StoredObject,
        scope: Scope | None = None,
        upload_id: UUID | None = None,
        reason: str = "DATABASE_RECEIPT_NOT_COMMITTED",
    ) -> None:
        path = self.root / str(stored.ref.object_id) / (stored.ref.version_id + ".orphan.json")
        with path.open("x") as output:
            os.chmod(path, 0o600)
            json.dump(
                {
                    "object_id": str(stored.ref.object_id),
                    "version_id": stored.ref.version_id,
                    "sha256": stored.ref.sha256,
                    "size_bytes": stored.size_bytes,
                    "reason": reason,
                    "case_id": str(scope.case_id) if scope else None,
                    "upload_id": str(upload_id) if upload_id else None,
                    "automatic_data_deletion": False,
                },
                output,
            )

    def read(self, ref: ObjectRef) -> Iterator[bytes]:
        if not ref.version_id.startswith("fs-v1-") or len(ref.version_id) != 38:
            raise RuntimeError("OBJECT_VERSION_UNSUPPORTED")
        UUID(hex=ref.version_id[6:])
        file = self.root / str(ref.object_id) / (ref.version_id + ".bin")
        if file.is_symlink() or file.parent.is_symlink():
            raise RuntimeError("OBJECT_VERSION_SYMLINK_REJECTED")
        digest = hashlib.sha256()
        with file.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
                yield block
        if digest.hexdigest() != ref.sha256:
            raise RuntimeError("OBJECT_INTEGRITY_FAILED")
