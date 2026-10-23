"""Read the canonical API permission mapping, rejecting ambiguous registrations."""

import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import yaml

METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options", "trace"})


@dataclass(frozen=True)
class OperationPermission:
    operation_id: str
    method: str
    path: str
    permission: str
    public: bool


# Only validated, immutable API metadata is shared. Every call reads both source
# files again; neither timestamps nor caller-owned dictionaries are trusted.
_CATALOG_CACHE: OrderedDict[tuple[Path, Path, bytes, bytes], tuple[tuple[str, OperationPermission], ...]] = (
    OrderedDict()
)
_CATALOG_LOCK = Lock()


def load_catalog(root: Path) -> dict[str, OperationPermission]:
    try:
        document_path = (root / "docs/03-api/openapi.yaml").resolve()
        model_path = (root / "docs/08-security/access-control-model.json").resolve()
        document_bytes = document_path.read_bytes()
        model_bytes = model_path.read_bytes()
        key = (document_path, model_path, hashlib.sha256(document_bytes).digest(), hashlib.sha256(model_bytes).digest())
        with _CATALOG_LOCK:
            entries = _CATALOG_CACHE.get(key)
            if entries is None:
                entries = tuple(_parse_catalog(document_bytes.decode("utf8"), model_bytes.decode("utf8")).items())
                _CATALOG_CACHE[key] = entries
                if len(_CATALOG_CACHE) > 8:
                    _CATALOG_CACHE.popitem(last=False)
            _CATALOG_CACHE.move_to_end(key)
        return dict(entries)
    except (OSError, ValueError):
        raise ValueError("PERMISSION_CATALOG_INVALID") from None


def _parse_catalog(document_text: str, model_text: str) -> dict[str, OperationPermission]:
    try:
        document = yaml.safe_load(document_text)
        model = json.loads(model_text)
        permissions = model["permissions"]
        if not isinstance(permissions, list) or len(permissions) != len(set(permissions)):
            raise ValueError()
        if document["servers"][0]["url"] != "/api/v1" or document["security"] != [{"bearerAuth": []}]:
            raise ValueError()
        catalog = {}
        bindings = []
        for path, methods in document["paths"].items():
            if not isinstance(path, str) or not path.startswith("/"):
                raise ValueError()
            for method, operation in methods.items():
                if method not in METHODS:
                    continue
                identifier = operation["operationId"]
                permission = operation["x-required-permission"]
                if (
                    not isinstance(identifier, str)
                    or not identifier
                    or identifier in catalog
                    or permission not in permissions
                ):
                    raise ValueError()
                security = operation.get("security", document["security"])
                public = security == []
                if security != [{"bearerAuth": []}] and not (
                    public
                    and identifier == "devLogin"
                    and method == "post"
                    and path == "/auth/login"
                    and permission == "development.login"
                    and operation.get("x-development-only") is True
                ):
                    raise ValueError()
                catalog[identifier] = OperationPermission(
                    identifier, method.upper(), "/api/v1" + path, permission, public
                )
                bindings.append(
                    dict(
                        operation_id=identifier,
                        method=method.upper(),
                        path=path,
                        permission=permission,
                    )
                )
        if sorted(bindings, key=lambda row: row["operation_id"]) != model["operations"]:
            raise ValueError()
        if {entry.permission for entry in catalog.values()} != set(permissions):
            raise ValueError()
        return dict(sorted(catalog.items()))
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        yaml.YAMLError,
    ):
        raise ValueError("PERMISSION_CATALOG_INVALID") from None
