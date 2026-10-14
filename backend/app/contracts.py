"""Runtime validators loaded from the existing authoritative Schema registry."""

import json

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from app.common import ROOT

SCHEMAS = {
    schema["$id"]: schema for schema in (json.loads(p.read_text()) for p in (ROOT / "schemas").rglob("*.schema.json"))
}
REGISTRY = Registry().with_resources((name, Resource.from_contents(schema)) for name, schema in SCHEMAS.items())


def validator(identifier):
    return Draft202012Validator(SCHEMAS[identifier], registry=REGISTRY, format_checker=FormatChecker())


EVENT = validator("urn:media-trace:event:poc.analysis.requested:1.0.0")
MODEL_RESPONSE = validator("urn:media-trace:model:M15:response:0.1.0")


def validate_model_result(request, result):
    MODEL_RESPONSE.validate(result)
    for field in [
        "request_id",
        "task_id",
        "run_version",
        "capability",
        "model_name",
        "model_version",
        "preprocessing_version",
        "mapping_version",
    ]:
        if result[field] != request[field]:
            raise ValueError("MODEL_RESPONSE_IDENTITY_MISMATCH")
    if result["mock"] or result["status"] != "SUCCEEDED":
        raise ValueError("MODEL_RESPONSE_NOT_REAL_SUCCESS")
