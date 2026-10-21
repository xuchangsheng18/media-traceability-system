"""Immutable engineering-candidate DAG snapshots, never execution authority."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from .contracts import REGISTRY, SCHEMAS


@dataclass(frozen=True)
class CandidateBinding:
    field_path: str
    source: str


@dataclass(frozen=True)
class CandidateNode:
    node_id: str
    kind: str
    dependencies: tuple[str, ...]
    required: bool
    model_id: str | None
    request_schema_id: str | None
    response_schema_id: str | None
    input_bindings: tuple[CandidateBinding, ...]
    outputs: tuple[str, ...]
    missing_policy: str
    active_entry_modes: tuple[str, ...]


@dataclass(frozen=True)
class CandidateEntry:
    operation_id: str
    mode: str
    request_structure_source: str | None
    internal_run_record_required: bool


@dataclass(frozen=True)
class CandidateDAG:
    dag_id: str
    dag_version: str
    status: str
    requirement_id: str
    source_task_ids: tuple[str, ...]
    external_inputs: tuple[str, ...]
    nodes: tuple[CandidateNode, ...]
    entries: tuple[CandidateEntry, ...]
    source_sha256: str
    content_sha256: str
    canonical_bytes: bytes

    def select(self, operation_id: str) -> "CandidateSelection":
        entry = next((entry for entry in self.entries if entry.operation_id == operation_id), None)
        if entry is None:
            raise ValueError("CANDIDATE_ENTRY_NOT_FOUND")
        selected = tuple(node for node in self.nodes if entry.mode in node.active_entry_modes)
        if entry.mode in {"READ_ONLY", "CONTROL_TRANSACTION"} and any(
            node.kind in {"media", "model", "publish"} for node in selected
        ):
            raise ValueError("CANDIDATE_DAG_INVALID")
        # A selected response may depend on the other, inactive entry branch.
        # Keep that structural distinction separate from persisted node states.
        inactive = tuple(node.node_id for node in self.nodes if entry.mode not in node.active_entry_modes)
        return CandidateSelection(self, entry, selected, inactive)


@dataclass(frozen=True)
class CandidateSelection:
    dag: CandidateDAG
    entry: CandidateEntry
    nodes: tuple[CandidateNode, ...]
    not_selected_node_ids: tuple[str, ...]


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("CANDIDATE_DAG_INVALID")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("CANDIDATE_DAG_INVALID")


def _ordered_nodes(value: dict[str, Any]) -> tuple[CandidateNode, ...]:
    nodes = {node["node_id"]: node for node in value["nodes"]}
    if len(nodes) != len(value["nodes"]):
        raise ValueError("CANDIDATE_DAG_INVALID")
    pending = dict(nodes)
    completed: set[str] = set()
    ordered = []
    while pending:
        ready = sorted(name for name, node in pending.items() if set(node["dependencies"]) <= completed)
        if not ready:
            raise ValueError("CANDIDATE_DAG_INVALID")
        for name in ready:
            node = pending.pop(name)
            if (node["missing_policy"] == "FAIL_REQUIRED") != node["required"]:
                raise ValueError("CANDIDATE_DAG_INVALID")
            if node["kind"] == "model":
                request_id = f"urn:media-trace:model:{node['model_id']}:request:0.1.0"
                response_id = f"urn:media-trace:model:{node['model_id']}:response:0.1.0"
                request = SCHEMAS.get(request_id)
                if (
                    request is None
                    or response_id not in SCHEMAS
                    or (node["request_schema_id"], node["response_schema_id"]) != (request_id, response_id)
                    or {binding["field_path"] for binding in node["input_bindings"]} != set(request["required"])
                    or len(node["input_bindings"]) != len(request["required"])
                ):
                    raise ValueError("CANDIDATE_DAG_INVALID")
            elif node["model_id"] is not None:
                raise ValueError("CANDIDATE_DAG_INVALID")
            ordered.append(
                CandidateNode(
                    node_id=name,
                    kind=node["kind"],
                    dependencies=tuple(node["dependencies"]),
                    required=node["required"],
                    model_id=node["model_id"],
                    request_schema_id=node["request_schema_id"],
                    response_schema_id=node["response_schema_id"],
                    input_bindings=tuple(CandidateBinding(**binding) for binding in node["input_bindings"]),
                    outputs=tuple(node["outputs"]),
                    missing_policy=node["missing_policy"],
                    active_entry_modes=tuple(node["active_entry_modes"]),
                )
            )
            completed.add(name)
    if sum(node.kind == "publish" for node in ordered) != 1 or ordered[-1].kind != "response":
        raise ValueError("CANDIDATE_DAG_INVALID")
    return tuple(ordered)


def parse_candidate_dag(raw: bytes, *, max_bytes: int, max_nodes: int) -> CandidateDAG:
    """Caller-owned resource budgets; no policy adoption, database writes or I/O."""
    if any(type(limit) is not int or limit <= 0 for limit in (max_bytes, max_nodes)):
        raise ValueError("CANDIDATE_PLAN_LIMIT_INVALID")
    if not isinstance(raw, bytes):
        raise ValueError("CANDIDATE_DAG_INVALID")
    if len(raw) > max_bytes:
        raise ValueError("CANDIDATE_DAG_BUDGET_EXCEEDED")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError("CANDIDATE_DAG_INVALID") from None
    if isinstance(value, dict) and isinstance(value.get("nodes"), list) and len(value["nodes"]) > max_nodes:
        raise ValueError("CANDIDATE_DAG_BUDGET_EXCEEDED")
    try:
        Draft202012Validator(
            SCHEMAS["urn:media-trace:stage-one:dag:0.1.0"], registry=REGISTRY, format_checker=FormatChecker()
        ).validate(value)
    except (ValidationError, RecursionError):
        raise ValueError("CANDIDATE_DAG_INVALID") from None
    ordered = _ordered_nodes(value)
    entries = tuple(CandidateEntry(**entry) for entry in value["entry_variants"])
    if len({entry.operation_id for entry in entries}) != len(entries):
        raise ValueError("CANDIDATE_DAG_INVALID")
    try:
        canonical = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    except UnicodeError:
        raise ValueError("CANDIDATE_DAG_INVALID") from None
    return CandidateDAG(
        dag_id=value["dag_id"],
        dag_version=value["dag_version"],
        status=value["status"],
        requirement_id=value["requirement_id"],
        source_task_ids=tuple(value["source_task_ids"]),
        external_inputs=tuple(value["external_inputs"]),
        nodes=ordered,
        entries=entries,
        source_sha256=hashlib.sha256(raw).hexdigest(),
        content_sha256=hashlib.sha256(canonical).hexdigest(),
        canonical_bytes=canonical,
    )
