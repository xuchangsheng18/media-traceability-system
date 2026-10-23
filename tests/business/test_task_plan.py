"""Candidate plan parsing never runs nodes or grants business authority."""

import copy
import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GRAPHS = sorted((ROOT / "docs/05-workflows/dags").glob("*.json"))


def parse(value, **limits):
    from business_app.task_plan import parse_candidate_dag

    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return parse_candidate_dag(
        raw, max_bytes=limits.get("max_bytes", 1_048_576), max_nodes=limits.get("max_nodes", 128)
    )


def document(name="FR-MEDIA-001"):
    return json.loads((ROOT / "docs/05-workflows/dags" / (name + ".json")).read_text())


@pytest.mark.parametrize("path", GRAPHS, ids=lambda path: path.stem)
def test_existing_dags_are_immutable_candidates_and_select_every_declared_entry(path):
    raw = path.read_bytes()
    value, dag = json.loads(raw), parse(raw)
    assert len(GRAPHS) == 36
    assert (dag.dag_id, dag.dag_version, dag.status) == (value["dag_id"], "candidate-1", "ENGINEERING_CANDIDATE")
    assert dag.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert dag.content_sha256 == hashlib.sha256(dag.canonical_bytes).hexdigest()
    assert json.loads(dag.canonical_bytes) == value
    seen: set[str] = set()
    for node in dag.nodes:
        assert set(node.dependencies) <= seen
        seen.add(node.node_id)
    assert dag.nodes[-1].kind == "response" and sum(n.kind == "publish" for n in dag.nodes) == 1
    for entry in value["entry_variants"]:
        selected = dag.select(entry["operation_id"])
        assert selected.dag is dag and selected.entry.operation_id == entry["operation_id"]
        assert selected.entry.mode == entry["mode"]
        expected = {n["node_id"] for n in value["nodes"] if entry["mode"] in n["active_entry_modes"]}
        assert {n.node_id for n in selected.nodes} == expected
        assert set(selected.not_selected_node_ids) == seen - expected
        if entry["mode"] in {"READ_ONLY", "CONTROL_TRANSACTION"}:
            assert not {"media", "model", "publish"} & {n.kind for n in selected.nodes}


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "unknown_dependency",
        "self_cycle",
        "cycle",
        "required_policy",
        "no_publish",
        "extra_publish",
        "response_not_last",
        "duplicate_entry",
        "extra_field",
        "unknown_mode",
    ],
)
def test_invalid_graph_semantics_are_refused(change):
    value = document()
    nodes = value["nodes"]
    if change == "duplicate":
        nodes.append(copy.deepcopy(nodes[0]))
    elif change == "unknown_dependency":
        nodes[1]["dependencies"] = ["missing-node"]
    elif change == "self_cycle":
        nodes[1]["dependencies"] = [nodes[1]["node_id"]]
    elif change == "cycle":
        nodes[0]["dependencies"] = [nodes[1]["node_id"]]
    elif change == "required_policy":
        nodes[0]["missing_policy"] = "SKIP_OPTIONAL_WITH_REASON"
    elif change == "no_publish":
        next(n for n in nodes if n["kind"] == "publish")["kind"] = "projection"
    elif change == "extra_publish":
        nodes[1]["kind"] = "publish"
    elif change == "response_not_last":
        nodes[-1]["kind"] = "control"
    elif change == "duplicate_entry":
        value["entry_variants"].append(copy.deepcopy(value["entry_variants"][0]))
    elif change == "extra_field":
        value["approved"] = True
    else:
        nodes[0]["active_entry_modes"] = ["UNCONFIRMED_EXECUTION"]
    with pytest.raises(ValueError, match="^CANDIDATE_DAG_INVALID$"):
        parse(value)


@pytest.mark.parametrize(
    "change", ["model_id", "request", "response", "missing_binding", "duplicate_binding", "extra_binding", "non_model"]
)
def test_model_schema_and_required_binding_identity_must_match(change):
    value = next(
        document(path.stem) for path in GRAPHS if any(n["kind"] == "model" for n in document(path.stem)["nodes"])
    )
    node = next(n for n in value["nodes"] if n["kind"] == "model")
    if change == "model_id":
        node["model_id"] = "M99"
    elif change in {"request", "response"}:
        node[change + "_schema_id"] = "urn:unconfirmed:schema"
    elif change == "missing_binding":
        node["input_bindings"].pop()
    elif change == "duplicate_binding":
        node["input_bindings"][1] = copy.deepcopy(node["input_bindings"][0])
    elif change == "extra_binding":
        node["input_bindings"].append(dict(field_path="extra-unconfirmed-input", source="untrusted"))
    else:
        value["nodes"][0]["model_id"] = node["model_id"]
    with pytest.raises(ValueError, match="^CANDIDATE_DAG_INVALID$"):
        parse(value)


@pytest.mark.parametrize("mode", ["READ_ONLY", "CONTROL_TRANSACTION"])
def test_read_and_control_entries_cannot_select_execution_nodes(mode):
    value = document("FR-INGEST-001")
    value["entry_variants"][0]["mode"] = mode
    value["nodes"][1]["active_entry_modes"].append(mode)
    dag = parse(value)
    with pytest.raises(ValueError, match="^CANDIDATE_DAG_INVALID$"):
        dag.select(value["entry_variants"][0]["operation_id"])


def test_inactive_branch_dependency_is_structural_not_a_persisted_node_state():
    dag = parse(document("FR-INGEST-001"))
    selected = dag.select("createSource")
    assert [n.node_id for n in selected.nodes] == ["control.authorize", "project.control", "response.emit"]
    assert "publish.snapshot" in selected.nodes[-1].dependencies
    assert "publish.snapshot" in selected.not_selected_node_ids
    assert not hasattr(selected.nodes[-1], "state")


@pytest.mark.parametrize("operation", ["", "unknown-operation", " createTask", None])
def test_unknown_entry_never_falls_back(operation):
    with pytest.raises(ValueError, match="^CANDIDATE_ENTRY_NOT_FOUND$"):
        parse(document()).select(operation)


def test_parsed_snapshot_does_not_retain_mutable_caller_structures():
    value = document()
    dag = parse(value)
    selected = dag.select("createTask")
    previous = (dag.canonical_bytes, dag.source_sha256, dag.nodes, selected.nodes)
    value["nodes"][0]["dependencies"].append("new-untrusted-input")
    value["nodes"][0]["input_bindings"][0]["source"] = "modified-after-parse"
    value["entry_variants"][0]["mode"] = "READ_ONLY"
    assert previous == (dag.canonical_bytes, dag.source_sha256, dag.nodes, selected.nodes)
    with pytest.raises(FrozenInstanceError):
        dag.dag_version = "changed"
    with pytest.raises(FrozenInstanceError):
        dag.nodes[0].required = False
    with pytest.raises(FrozenInstanceError):
        dag.nodes[0].input_bindings[0].source = "changed"
    with pytest.raises(FrozenInstanceError):
        selected.entry.mode = "changed"


def test_topology_and_canonical_digest_are_deterministic_without_erasing_source_bytes():
    value = document()
    a = parse(json.dumps(value, sort_keys=True).encode())
    b = parse(json.dumps(value, indent=3).encode())
    assert a.source_sha256 != b.source_sha256
    assert a.content_sha256 == b.content_sha256 and a.nodes == b.nodes
    reordered = copy.deepcopy(value)
    reordered["nodes"].reverse()
    assert parse(reordered).nodes == a.nodes
    assert parse(reordered).content_sha256 != a.content_sha256


@pytest.mark.parametrize(
    "raw", [b"{", b"[]", b"\xff", b'{"dag_id":"a","dag_id":"b"}', b'{"unexpected":NaN}', b'{"unexpected":Infinity}']
)
def test_malformed_or_duplicate_json_has_only_a_safe_error(raw):
    with pytest.raises(ValueError, match="^CANDIDATE_DAG_INVALID$"):
        parse(raw)


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
def test_unpaired_surrogate_in_json_is_refused_with_only_the_safe_error(surrogate):
    value = document()
    value["dag_id"] = "self-owned-invalid-unicode-" + surrogate
    with pytest.raises(ValueError, match="^CANDIDATE_DAG_INVALID$"):
        parse(value)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, None])
def test_input_limits_must_be_explicit_positive_integers(limit):
    with pytest.raises(ValueError, match="^CANDIDATE_PLAN_LIMIT_INVALID$"):
        parse(document(), max_bytes=limit)
    with pytest.raises(ValueError, match="^CANDIDATE_PLAN_LIMIT_INVALID$"):
        parse(document(), max_nodes=limit)


def test_input_bytes_and_node_count_are_bounded_before_plan_creation():
    value = document()
    raw = json.dumps(value).encode()
    assert parse(raw, max_bytes=len(raw), max_nodes=len(value["nodes"]))
    with pytest.raises(ValueError, match="^CANDIDATE_DAG_BUDGET_EXCEEDED$"):
        parse(raw, max_bytes=len(raw) - 1)
    with pytest.raises(ValueError, match="^CANDIDATE_DAG_BUDGET_EXCEEDED$"):
        parse(raw, max_nodes=len(value["nodes"]) - 1)
