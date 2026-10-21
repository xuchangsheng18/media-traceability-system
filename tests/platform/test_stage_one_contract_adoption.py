"""A historical semantic review permits only the confirmed two-query addition."""

import ast
import copy
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
API = "docs/03-api/openapi.yaml"
ADOPTION = "docs/08-security/catalog-read-contract-adoption.json"
PRIOR = "docs/08-security/history/t001-t123-catalog-predecessor-openapi.yaml"


def verifier(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = importlib.import_module("validate_stage_one_completion")
    method = getattr(module, "verify_semantic_source_binding", None)
    assert callable(method), "EXACT_CONFIRMED_SEMANTIC_SOURCE_TRANSITION_REQUIRED"
    return method


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def transition(tmp_path):
    old: dict[str, Any] = {
        "paths": {},
        "security": [{"bearerAuth": []}],
        "components": {"schemas": {"Asset": {"type": "object"}}},
    }
    for path, operation in [("/assets", "listAssets"), ("/analysis/tasks", "listTasks")]:
        old["paths"][path] = {
            "get": {
                "operationId": operation,
                "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}],
            }
        }
    current = copy.deepcopy(old)
    for path in old["paths"]:
        current["paths"][path]["get"]["parameters"].append(
            {"name": "case_id", "in": "query", "required": True, "schema": {"type": "string", "format": "uuid"}}
        )
    prior_raw = yaml.safe_dump(old, sort_keys=False).encode()
    current_raw = yaml.safe_dump(current, sort_keys=False).encode()
    adoption = {
        "status": "EXPLICIT_CONTRACT_CHANGE_AND_SOURCE_REGISTRATION_ONLY_NOT_POLICY_ADOPTION",
        "user_confirmation": "required_case_id_for_listAssets_and_listTasks_explicitly_confirmed_in_current_conversation",
        "scope": ["getAsset", "listAssets", "listTasks"],
        "role_cells_changed": False,
        "formal_allow": False,
        "shared_adopted": False,
        "current_bytes_hash_convention": "UTF8_text_normalized_to_LF_equal_to_staged_Git_blob_bytes",
        "source_bindings": {
            API: {"prior_sha256": sha(prior_raw), "current_sha256": sha(current_raw), "prior_copy": PRIOR}
        },
    }
    for relative, raw in [(API, current_raw), (PRIOR, prior_raw), (ADOPTION, json.dumps(adoption).encode())]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return dict(root=tmp_path, old=old, current=current, adoption=adoption, expected=sha(prior_raw))


def save_adoption(ctx):
    (ctx["root"] / ADOPTION).write_text(json.dumps(ctx["adoption"]), encoding="utf8")


def save_current_with_honest_new_hash(ctx):
    raw = yaml.safe_dump(ctx["current"], sort_keys=False).encode()
    (ctx["root"] / API).write_bytes(raw)
    ctx["adoption"]["source_bindings"][API]["current_sha256"] = sha(raw)
    save_adoption(ctx)


def test_exact_confirmed_two_case_parameters_preserve_historical_review(monkeypatch, transition):
    ctx = transition
    original = (ctx["root"] / PRIOR).read_bytes()
    assert verifier(monkeypatch)(API, ctx["expected"], root=ctx["root"]) == "CONFIRMED_CASE_QUERY_ADDITION"
    assert (ctx["root"] / PRIOR).read_bytes() == original


def test_confirmed_parameter_description_and_declared_lf_convention_are_supported(monkeypatch, transition):
    ctx = transition
    for path in ["/assets", "/analysis/tasks"]:
        ctx["current"]["paths"][path]["get"]["parameters"][-1]["description"] = (
            "Explicit case scope; authorization remains server-side."
        )
    save_current_with_honest_new_hash(ctx)
    current = ctx["root"] / API
    current.write_bytes(current.read_bytes().replace(b"\n", b"\r\n"))
    assert verifier(monkeypatch)(API, ctx["expected"], root=ctx["root"]) == "CONFIRMED_CASE_QUERY_ADDITION"


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "fake_old",
        "fake_new",
        "bad_prior",
        "unconfirmed",
        "scope",
        "role_cells_changed",
        "formal_allow",
        "shared_adopted",
    ],
)
def test_missing_or_unconfirmed_binding_does_not_accept_hash_drift(monkeypatch, transition, defect):
    ctx = transition
    if defect == "missing":
        (ctx["root"] / ADOPTION).unlink()
    else:
        if defect == "fake_old":
            ctx["adoption"]["source_bindings"][API]["prior_sha256"] = "0" * 64
        elif defect == "fake_new":
            ctx["adoption"]["source_bindings"][API]["current_sha256"] = "0" * 64
        elif defect == "bad_prior":
            (ctx["root"] / PRIOR).write_bytes(b"not the reviewed source")
        elif defect == "unconfirmed":
            ctx["adoption"]["user_confirmation"] = "pending"
        elif defect == "scope":
            ctx["adoption"]["scope"].append("createTask")
        else:
            ctx["adoption"][defect] = True
        save_adoption(ctx)
    with pytest.raises(AssertionError):
        verifier(monkeypatch)(API, ctx["expected"], root=ctx["root"])


@pytest.mark.parametrize(
    "defect",
    [
        "optional",
        "not_uuid",
        "body_parameter",
        "duplicate",
        "one_only",
        "other_schema",
        "security",
        "extra_route",
        "malformed_description",
    ],
)
def test_honest_adoption_hash_cannot_authorize_other_contract_edits(monkeypatch, transition, defect):
    ctx = transition
    parameter = ctx["current"]["paths"]["/assets"]["get"]["parameters"][-1]
    if defect == "optional":
        parameter["required"] = False
    elif defect == "not_uuid":
        parameter["schema"]["format"] = "hostname"
    elif defect == "body_parameter":
        parameter["in"] = "header"
    elif defect == "duplicate":
        ctx["current"]["paths"]["/assets"]["get"]["parameters"].append(copy.deepcopy(parameter))
    elif defect == "one_only":
        ctx["current"]["paths"]["/analysis/tasks"]["get"]["parameters"].pop()
    elif defect == "other_schema":
        ctx["current"]["components"]["schemas"]["Asset"]["type"] = "string"
    elif defect == "security":
        ctx["current"]["security"] = []
    elif defect == "malformed_description":
        parameter["description"] = None
    else:
        ctx["current"]["paths"]["/unapproved"] = {"get": {"operationId": "newOperation"}}
    save_current_with_honest_new_hash(ctx)
    with pytest.raises(AssertionError):
        verifier(monkeypatch)(API, ctx["expected"], root=ctx["root"])


def test_other_source_paths_still_require_exact_reviewed_bytes(monkeypatch, transition):
    ctx = transition
    name = "docs/08-security/other-source.json"
    path = ctx["root"] / name
    path.write_bytes(b'{"approved":false}')
    expected = sha(path.read_bytes())
    assert verifier(monkeypatch)(name, expected, root=ctx["root"]) == "UNCHANGED_SOURCE"
    path.write_bytes(b'{"approved":true}')
    ctx["adoption"]["source_bindings"][name] = dict(
        prior_sha256=expected, current_sha256=sha(path.read_bytes()), prior_copy=PRIOR
    )
    save_adoption(ctx)
    with pytest.raises(AssertionError):
        verifier(monkeypatch)(name, expected, root=ctx["root"])


def test_actual_repository_binding_does_not_rewrite_semantic_review(monkeypatch):
    path = ROOT / "docs/00-project/requirement-semantic-review.json"
    before = path.read_bytes()
    review = json.loads(before)
    method = verifier(monkeypatch)
    for name, expected in review["source_hashes"].items():
        method(name, expected, root=ROOT)
    assert path.read_bytes() == before


def test_existing_36_requirement_semantic_action_remains_enforced(monkeypatch):
    verifier(monkeypatch)
    module = importlib.import_module("validate_stage_one_completion")
    tree = ast.parse((ROOT / "scripts/validate_stage_one_completion.py").read_text("utf8"))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    semantic = next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == "semantic")
    namespace = dict(vars(module))
    exec(compile(ast.Module(body=[semantic], type_ignores=[]), "<existing-semantic-action>", "exec"), namespace)
    result = namespace["semantic"]()
    assert result == {
        "reviewed_requirements": 36,
        "specific_flow_corrections_checked": 5,
        "formal_business_approval": False,
    }
