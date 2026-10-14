"""Validate actual HTTP payloads against the existing shared schema registry."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from .errors import BusinessError

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = {
    value["$id"]: value
    for value in (json.loads(path.read_text()) for path in (ROOT / "schemas").rglob("*.schema.json"))
}
REGISTRY = Registry().with_resources((name, Resource.from_contents(schema)) for name, schema in SCHEMAS.items())


def validate_api(name: str, payload: dict[str, Any]) -> None:
    validator = Draft202012Validator(
        {"$ref": "urn:media-trace:api:0.1.0#/$defs/" + name}, registry=REGISTRY, format_checker=FormatChecker()
    )
    try:
        validator.validate(payload)
    except ValidationError:
        raise BusinessError("INPUT_INVALID", 422) from None
