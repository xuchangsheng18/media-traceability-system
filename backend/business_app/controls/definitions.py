"""Immutable, organisation-scoped parameter definitions outside the source repository."""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from ..errors import BusinessError
from ..types import Actor
from .common import canonical


class FileDefinitions:
    def __init__(self, root: Path) -> None:
        if any(path.is_symlink() for path in [root, *root.parents]):
            raise ValueError("DEFINITION_DIRECTORY_SYMLINK_REJECTED")
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def path(self, actor: Actor, reference: str, version: str) -> Path:
        folder = self.root / str(actor.org_id)
        if any(path.is_symlink() for path in [folder, *folder.parents]):
            raise BusinessError("DEFINITION_DIRECTORY_UNAVAILABLE", 503)
        name = hashlib.sha256(canonical([reference, version])).hexdigest() + ".json"
        target = folder / name
        if target.is_symlink():
            raise BusinessError("DEFINITION_OBJECT_UNAVAILABLE", 503)
        return target

    def publish(self, actor: Actor, version: str, values: dict[str, Any]) -> str:
        """Trusted bootstrap/admin boundary; never an unauthenticated HTTP writer."""
        if not version or len(version) > 128:
            raise ValueError("DEFINITION_VERSION_REQUIRED")
        reference = "urn:sha256:" + hashlib.sha256(canonical(values)).hexdigest()
        target = self.path(actor, reference, version)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        content = canonical(dict(version=version, values=values))
        if len(content) > 1024 * 1024:
            raise ValueError("DEFINITION_READ_LIMIT")
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".pending-", delete=False) as output:
                temporary = Path(output.name)
                os.chmod(temporary, 0o600)
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if target.read_bytes() != content:
                    raise BusinessError("DEFINITION_IMMUTABLE_CONFLICT", 409) from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return reference

    def resolve(self, actor: Actor, reference: str, version: str) -> dict[str, Any]:
        target = self.path(actor, reference, version)
        try:
            with target.open("rb") as source:
                raw = source.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("DEFINITION_READ_LIMIT")
            document = json.loads(raw)
            if (
                set(document) != {"version", "values"}
                or document["version"] != version
                or not isinstance(document["values"], dict)
            ):
                raise ValueError("DEFINITION_BINDING_INVALID")
            digest = hashlib.sha256(canonical(document["values"])).hexdigest()
            if reference != "urn:sha256:" + digest:
                raise ValueError("DEFINITION_DIGEST_INVALID")
            return dict(definition_ref=reference, version=version, sha256=digest, values=document["values"])
        except (OSError, ValueError, TypeError):
            raise BusinessError("POLICY_DEFINITION_UNAVAILABLE", 503) from None
