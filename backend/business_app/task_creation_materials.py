"""Strict immutable internal materials; never adoption, permission or execution.

All budgets are caller-owned. Schema validation checks declared references only:
it neither imports handlers nor proves current release, licence or source facts.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from jsonschema import Draft202012Validator, FormatChecker

from .contracts import REGISTRY, SCHEMAS

CANONICALIZATION_VERSION = "task-material-json-utf8-sortkeys-v1"
PLAN_SCHEMA_ID = "urn:media-trace:task-execution-plan:1.0.0"
CAPABILITY_SCHEMA_ID = "urn:media-trace:task-capability-manifest:1.0.0"
INPUT_SCHEMA_ID = "urn:media-trace:task-input-manifest:1.0.0"
POLICY_SCHEMA_ID = "urn:media-trace:api:0.1.0#/$defs/PolicyDefinition"
ASSET_SELECTORS = frozenset(
    {
        "asset.asset_id",
        "asset.sha256",
        "asset.object_ref.object_id",
        "asset.object_ref.version_id",
        "asset.object_ref.sha256",
        "asset.source_authorization_version",
    }
)


@dataclass(frozen=True)
class MaterialBudgets:
    max_bytes: int
    max_nodes: int
    max_capabilities: int

    def __post_init__(self) -> None:
        _limits(self)


@dataclass(frozen=True)
class CanonicalMaterial:
    schema_id: str
    document_id: str
    version: str
    canonicalization_version: str
    canonical_bytes: bytes
    sha256: str
    source_sha256: str

    def as_dict(self) -> dict[str, Any]:
        # Returning a detached projection cannot mutate the frozen byte snapshot.
        value = json.loads(self.canonical_bytes)
        if not isinstance(value, dict):
            raise ValueError("TASK_MATERIAL_INVALID")
        return value


@dataclass(frozen=True)
class MaterialBundle:
    policy: CanonicalMaterial
    plan: CanonicalMaterial
    capability: CanonicalMaterial
    inputs: CanonicalMaterial
    node_inputs: tuple[CanonicalMaterial, ...]


def _limits(budgets: MaterialBudgets) -> None:
    if type(budgets) is not MaterialBudgets or any(
        type(value) is not int or value <= 0
        for value in (budgets.max_bytes, budgets.max_nodes, budgets.max_capabilities)
    ):
        raise ValueError("TASK_MATERIAL_LIMIT_INVALID")


def _invalid() -> ValueError:
    return ValueError("TASK_MATERIAL_INVALID")


def _binding() -> ValueError:
    return ValueError("TASK_MATERIAL_BINDING_INVALID")


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for name, item in pairs:
        if name in value:
            raise _invalid()
        value[name] = item
    return value


def _constant(_: str) -> None:
    raise _invalid()


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
            "utf8"
        )
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise _invalid() from None


def _load(raw: bytes, budgets: MaterialBudgets) -> dict[str, Any]:
    _limits(budgets)
    if type(raw) is not bytes:
        raise _invalid()
    if len(raw) > budgets.max_bytes:
        raise ValueError("TASK_MATERIAL_BUDGET_EXCEEDED")
    try:
        value = json.loads(raw.decode("utf8"), object_pairs_hook=_unique, parse_constant=_constant)
        if not isinstance(value, dict):
            raise _invalid()
        # Also catches overflowing finite-looking literals and lone surrogates.
        _canonical(value)
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise _invalid() from None


def _schema_document(identifier: str) -> dict[str, Any]:
    try:
        base, separator, fragment = identifier.partition("#")
        value = SCHEMAS[base]
        if separator:
            if not fragment.startswith("/"):
                raise _invalid()
            for part in fragment[1:].split("/"):
                value = value[part.replace("~1", "/").replace("~0", "~")]
        if not isinstance(value, dict):
            raise _invalid()
        return value
    except (KeyError, TypeError, AttributeError, ValueError):
        raise _invalid() from None


def _validate(identifier: str, value: Any) -> None:
    # Only this already loaded local registry is used. No retriever or URL I/O.
    _schema_document(identifier)
    try:
        Draft202012Validator({"$ref": identifier}, registry=REGISTRY, format_checker=FormatChecker()).validate(value)
    except Exception:
        raise _invalid() from None


def _freeze(
    identifier: str, document_id: str, version: str, value: dict[str, Any], raw: bytes, budgets: MaterialBudgets
) -> CanonicalMaterial:
    canonical = _canonical(value)
    if len(canonical) > budgets.max_bytes:
        raise ValueError("TASK_MATERIAL_BUDGET_EXCEEDED")
    return CanonicalMaterial(
        identifier,
        document_id,
        version,
        CANONICALIZATION_VERSION,
        canonical,
        hashlib.sha256(canonical).hexdigest(),
        hashlib.sha256(raw).hexdigest(),
    )


def _properties(identifier: str) -> tuple[dict[str, Any], set[str]]:
    value = _schema_document(identifier)
    properties, required = value.get("properties"), value.get("required", [])
    # This mapper supports a closed, statically named object at the root only.
    # Field subschemas are still validated in full by jsonschema below; root
    # combinations/conditionals/dynamic keys must never become a field-only
    # projection that silently discards their cross-field requirements.
    supported = {
        "$schema",
        "$id",
        "$comment",
        "title",
        "description",
        "type",
        "properties",
        "required",
        "additionalProperties",
    }
    if (
        set(value) - supported
        or value.get("type") != "object"
        or value.get("additionalProperties") is not False
        or not isinstance(properties, dict)
        or not isinstance(required, list)
        or any(not isinstance(field, str) or field not in properties for field in required)
    ):
        # Complex/unknown request shapes require an explicitly supported mapping,
        # not an unchecked path or arbitrary schema download.
        raise _binding()
    return properties, set(required)


def _model_identity(value: dict[str, Any]) -> tuple[str, ...]:
    # Identity equality uses UUID values without rewriting canonical source bytes.
    return (
        str(UUID(value["model_id"])),
        value["model_version"],
        value["model_task_version"],
        str(UUID(value["release_id"])),
    )


def _models(items: list[dict[str, Any]]) -> None:
    if len({_model_identity(item) for item in items}) != len(items):
        raise _binding()


def _handler_identity(value: dict[str, Any]) -> tuple[str, str]:
    return value["handler_id"], value["handler_version"]


def _graph(value: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    nodes = {node["node_code"]: node for node in value["nodes"]}
    if len(nodes) != len(value["nodes"]):
        raise _binding()
    for node in nodes.values():
        if not set(node["dependencies"]) <= nodes.keys():
            raise _binding()
        if (node["missing_policy"] == "FAIL_REQUIRED") != node["required"]:
            raise _binding()
        _models(node["model_dependencies"])
        properties, required = _properties(node["input_schema_id"])
        _properties(node["output_schema_id"])
        fields = [binding["field_path"] for binding in node["input_bindings"]]
        if len(set(fields)) != len(fields) or not required <= set(fields) <= properties.keys():
            raise _binding()
        for binding in node["input_bindings"]:
            if binding["source"] == "asset":
                if binding["selector"] not in ASSET_SELECTORS:
                    raise _binding()
            else:
                source = nodes.get(binding["node_code"])
                if (
                    source is None
                    or source["node_code"] not in node["dependencies"]
                    or binding["output_ref"] not in source["output_refs"]
                ):
                    raise _binding()
                outputs, _ = _properties(source["output_schema_id"])
                field = binding["selector"]
                if field not in outputs or _canonical(outputs[field]) != _canonical(properties[binding["field_path"]]):
                    raise _binding()
    pending = dict(nodes)
    finished: set[str] = set()
    ordered: list[dict[str, Any]] = []
    while pending:
        ready = [name for name, node in pending.items() if set(node["dependencies"]) <= finished]
        if not ready:
            raise _binding()
        for name in ready:
            ordered.append(pending.pop(name))
            finished.add(name)
    return tuple(ordered)


def parse_execution_plan(raw: bytes, *, budgets: MaterialBudgets) -> CanonicalMaterial:
    value = _load(raw, budgets)
    if isinstance(value.get("nodes"), list) and len(value["nodes"]) > budgets.max_nodes:
        raise ValueError("TASK_MATERIAL_BUDGET_EXCEEDED")
    _validate(PLAN_SCHEMA_ID, value)
    if sum(len(node["model_dependencies"]) for node in value["nodes"]) > budgets.max_capabilities:
        raise ValueError("TASK_MATERIAL_BUDGET_EXCEEDED")
    _graph(value)
    return _freeze(PLAN_SCHEMA_ID, value["plan_id"], value["plan_version"], value, raw, budgets)


def parse_capability_manifest(raw: bytes, *, budgets: MaterialBudgets) -> CanonicalMaterial:
    value = _load(raw, budgets)
    if isinstance(value.get("handlers"), list) and len(value["handlers"]) > budgets.max_capabilities:
        raise ValueError("TASK_MATERIAL_BUDGET_EXCEEDED")
    _validate(CAPABILITY_SCHEMA_ID, value)
    handlers = value["handlers"]
    if len({_handler_identity(handler) for handler in handlers}) != len(handlers):
        raise _binding()
    if sum(1 + len(handler["model_dependencies"]) for handler in handlers) > budgets.max_capabilities:
        raise ValueError("TASK_MATERIAL_BUDGET_EXCEEDED")
    for handler in handlers:
        _properties(handler["input_schema_id"])
        _properties(handler["output_schema_id"])
        _models(handler["model_dependencies"])
    return _freeze(CAPABILITY_SCHEMA_ID, value["capability_id"], value["capability_version"], value, raw, budgets)


def parse_input_manifest(raw: bytes, *, budgets: MaterialBudgets) -> CanonicalMaterial:
    value = _load(raw, budgets)
    if isinstance(value.get("nodes"), list) and len(value["nodes"]) > budgets.max_nodes:
        raise ValueError("TASK_MATERIAL_BUDGET_EXCEEDED")
    _validate(INPUT_SCHEMA_ID, value)
    asset = value["asset"]
    if (
        UUID(asset["object_ref"]["object_id"]).int == 0
        or asset["sha256"] != asset["object_ref"]["sha256"]
        or len({node["node_code"] for node in value["nodes"]}) != len(value["nodes"])
    ):
        raise _binding()
    for node in value["nodes"]:
        fields = [item["field_path"] for item in node["inputs"]]
        if len(fields) != len(set(fields)):
            raise _binding()
    return _freeze(INPUT_SCHEMA_ID, value["input_id"], value["input_version"], value, raw, budgets)


def parse_policy_artifact(raw: bytes, *, budgets: MaterialBudgets) -> CanonicalMaterial:
    value = _load(raw, budgets)
    _validate(POLICY_SCHEMA_ID, value)
    digest = hashlib.sha256(_canonical(value["values"])).hexdigest()
    if value["sha256"] != digest or value["definition_ref"] != "urn:sha256:" + digest:
        raise _binding()
    return _freeze(POLICY_SCHEMA_ID, value["definition_ref"], value["version"], value, raw, budgets)


def _asset_value(asset: dict[str, Any], selector: str) -> Any:
    if selector not in ASSET_SELECTORS:
        raise _binding()
    value: Any = asset
    for field in selector.split(".")[1:]:
        value = value[field]
    return value


def prepare_material_bundle(
    policy_raw: bytes,
    plan_raw: bytes,
    capability_raw: bytes,
    input_raw: bytes,
    *,
    budgets: MaterialBudgets,
) -> MaterialBundle:
    """Check exact material relationships; no current-facts/authority decision."""
    policy = parse_policy_artifact(policy_raw, budgets=budgets)
    plan = parse_execution_plan(plan_raw, budgets=budgets)
    capability = parse_capability_manifest(capability_raw, budgets=budgets)
    inputs = parse_input_manifest(input_raw, budgets=budgets)
    p, c, i = plan.as_dict(), capability.as_dict(), inputs.as_dict()
    if (
        p["policy_version"] != policy.version
        or p["capability"]
        != dict(
            capability_id=capability.document_id,
            capability_version=capability.version,
            capability_sha256=capability.sha256,
        )
        or (i["plan_id"], i["plan_version"], i["plan_sha256"]) != (plan.document_id, plan.version, plan.sha256)
        or [node["node_code"] for node in p["nodes"]] != [node["node_code"] for node in i["nodes"]]
    ):
        raise _binding()
    handlers = {_handler_identity(handler): handler for handler in c["handlers"]}
    if set(handlers) != {_handler_identity(node["handler"]) for node in p["nodes"]}:
        raise _binding()
    input_nodes = {node["node_code"]: node for node in i["nodes"]}
    snapshots = []
    for node in _graph(p):
        handler = handlers[_handler_identity(node["handler"])]
        if any(handler[field] != item for field, item in node["handler"].items()) or any(
            handler[field] != node[field] for field in ("model_dependencies", "input_schema_id", "output_schema_id")
        ):
            raise _binding()
        actual = input_nodes[node["node_code"]]
        properties, _ = _properties(node["input_schema_id"])
        expected = []
        for binding in node["input_bindings"]:
            if binding["source"] == "asset":
                item = _asset_value(i["asset"], binding["selector"])
                try:
                    Draft202012Validator(
                        properties[binding["field_path"]], registry=REGISTRY, format_checker=FormatChecker()
                    ).validate(item)
                except Exception:
                    raise _binding() from None
                expected.append(dict(binding, materialized=True, value=item))
            else:
                # Explicit selector only. Actual upstream bytes must be frozen by
                # the later authorized dispatcher after dependency completion.
                expected.append(dict(binding, materialized=False))
        if _canonical(actual["inputs"]) != _canonical(expected):
            raise _binding()
        snapshot_id = INPUT_SCHEMA_ID + "#/$defs/NodeSnapshot"
        snapshot = dict(
            schema_id=snapshot_id,
            schema_version="1.0.0",
            input_id=inputs.document_id,
            input_version=inputs.version,
            plan_sha256=plan.sha256,
            asset=i["asset"],
            node=actual,
        )
        _validate(snapshot_id, snapshot)
        raw = _canonical(snapshot)
        snapshots.append(_freeze(snapshot_id, node["node_code"], inputs.version, snapshot, raw, budgets))
    return MaterialBundle(policy, plan, capability, inputs, tuple(snapshots))
