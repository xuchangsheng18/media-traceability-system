"""Read the canonical API permission mapping, rejecting ambiguous registrations."""

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options", "trace"})


@dataclass(frozen=True)
class OperationPermission:
    operation_id: str
    method: str
    path: str
    permission: str
    public: bool


def load_catalog(root: Path) -> dict[str, OperationPermission]:
    try:
        document = yaml.safe_load((root / "docs/03-api/openapi.yaml").read_text(encoding="utf8"))
        model = json.loads((root / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))
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
