"""T014 strict permission catalog and real business-route boundaries."""

import importlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def catalog_module():
    assert importlib.util.find_spec("business_app.permissions") is not None, "T014 permission package is missing"
    return importlib.import_module("business_app.permissions.catalog")


def test_catalog_matches_all_73_operations_and_41_permissions():
    catalog = catalog_module().load_catalog(ROOT)
    assert len(catalog) == 73
    assert len({item.permission for item in catalog.values()}) == 41
    assert [item.operation_id for item in catalog.values() if item.public] == ["devLogin"]
    assert catalog["getCurrentUser"].permission == "identity.read"
    assert catalog["getCurrentUser"].path == "/api/v1/auth/me"
    assert catalog["health"].public is False


@pytest.mark.parametrize("change", ["missing_permission", "duplicate_operation", "unknown_permission", "wrong_method"])
def test_catalog_rejects_missing_duplicate_or_unbound_permissions(tmp_path, change):
    module = catalog_module()
    document = yaml.safe_load((ROOT / "docs/03-api/openapi.yaml").read_text(encoding="utf8"))
    operation = document["paths"]["/auth/me"]["get"]
    if change == "missing_permission":
        operation.pop("x-required-permission")
    elif change == "duplicate_operation":
        operation["operationId"] = "health"
    elif change == "unknown_permission":
        operation["x-required-permission"] = "undeclared.permission"
    else:
        document["paths"]["/auth/me"]["post"] = document["paths"]["/auth/me"].pop("get")
    for folder in ["docs/03-api", "docs/08-security"]:
        (tmp_path / folder).mkdir(parents=True)
    (tmp_path / "docs/03-api/openapi.yaml").write_text(yaml.safe_dump(document), encoding="utf8")
    model = json.loads((ROOT / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))
    (tmp_path / "docs/08-security/access-control-model.json").write_text(json.dumps(model), encoding="utf8")
    with pytest.raises(ValueError, match="PERMISSION_CATALOG_INVALID"):
        module.load_catalog(tmp_path)


def test_catalog_rejects_new_public_exception(tmp_path):
    module = catalog_module()
    document = yaml.safe_load((ROOT / "docs/03-api/openapi.yaml").read_text(encoding="utf8"))
    document["paths"]["/auth/me"]["get"]["security"] = []
    for folder in ["docs/03-api", "docs/08-security"]:
        (tmp_path / folder).mkdir(parents=True)
    (tmp_path / "docs/03-api/openapi.yaml").write_text(yaml.safe_dump(document), encoding="utf8")
    (tmp_path / "docs/08-security/access-control-model.json").write_bytes(
        (ROOT / "docs/08-security/access-control-model.json").read_bytes()
    )
    with pytest.raises(ValueError, match="PERMISSION_CATALOG_INVALID"):
        module.load_catalog(tmp_path)
