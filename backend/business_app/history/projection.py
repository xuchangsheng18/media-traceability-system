import re
from typing import Any
from uuid import UUID

from ..contracts import validate_api
from ..errors import BusinessError

RESPONSES = {
    "getTask": "Task",
    "getRiskFindings": "Findings",
    "getForensics": "Findings",
    "getTaskEvidence": "EvidencePage",
    "getTimeline": "Timeline",
    "getFirstSource": "FirstSource",
    "getPropagation": "Graph",
}


def nested_dicts(value: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if isinstance(value, dict):
        result.append(value)
        for child in value.values():
            result.extend(nested_dicts(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(nested_dicts(child))
    return result


def resolve_pointer(snapshot: dict[str, Any], pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise BusinessError("SNAPSHOT_MAPPING_INVALID", 503)
    value: Any = snapshot
    try:
        for raw in pointer[1:].split("/"):
            token = raw.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                if not re.fullmatch(r"0|[1-9][0-9]*", token):
                    raise ValueError()
                value = value[int(token)]
            else:
                value = value[token]
        return value
    except (KeyError, IndexError, TypeError, ValueError):
        raise BusinessError("SNAPSHOT_MAPPING_INVALID", 503) from None


def project(
    snapshot: dict[str, Any], operation_id: str, resource_id: UUID, ranking_id: UUID | None = None
) -> dict[str, Any]:
    if operation_id not in RESPONSES:
        raise BusinessError("SNAPSHOT_OPERATION_UNSUPPORTED", 503)
    if "api_projections" not in snapshot:
        raise BusinessError("LEGACY_SNAPSHOT_MAPPING_UNAVAILABLE", 503)
    entries = [
        entry
        for entry in snapshot["api_projections"]
        if entry["operation_id"] == operation_id and UUID(entry["resource_id"]) == resource_id
    ]
    if len(entries) != 1:
        raise BusinessError("SNAPSHOT_PROJECTION_NOT_FOUND", 404)
    selected = entries[0]
    references = [
        ref
        for ref in snapshot["projection_refs"]
        if ref["operation_id"] == operation_id
        and ref["schema_id"] == "urn:media-trace:api:0.1.0#/$defs/" + RESPONSES[operation_id]
        and ref["mapping_version"] == "history-api-projection/1"
    ]
    if len(references) != 1 or resolve_pointer(snapshot, references[0]["json_pointer"]) != selected["response"]:
        raise BusinessError("SNAPSHOT_MAPPING_INVALID", 503)
    response = dict(selected["response"])
    validate_api(RESPONSES[operation_id], response)
    binding = snapshot["binding"]
    for body in nested_dicts(response):
        for field in ["task_id", "case_id", "run_version", "result_version", "policy_version"]:
            if field in body and body[field] != binding[field]:
                raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
    if operation_id == "getTimeline" and UUID(response["asset_id"]) != resource_id:
        raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
    if operation_id in {"getFirstSource", "getPropagation"} and UUID(response["cluster_id"]) != resource_id:
        raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
    if operation_id in {"getTask", "getRiskFindings", "getForensics", "getTaskEvidence"} and resource_id != UUID(
        binding["task_id"]
    ):
        raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
    if ranking_id is not None and response.get("ranking_id") != str(ranking_id):
        raise BusinessError("SNAPSHOT_PROJECTION_NOT_FOUND", 404)
    return response
