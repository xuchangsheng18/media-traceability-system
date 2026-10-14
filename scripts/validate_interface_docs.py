"""Validate detailed interface lineage/coverage, without running business services."""
import ast
import datetime
import json

from generate_interface_docs import BASE, METHODS, MODULES, ROOT, digest, outputs, read


def routes(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    result = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr in METHODS:
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    result.add((decorator.func.attr.upper(), decorator.args[0].value))
    return result


def main():
    checks, errors = [], []

    def check(name, action):
        try:
            checks.append({"name": name, "status": "PASS", "detail": action()})
        except Exception as exc:
            checks.append({"name": name, "status": "FAIL"})
            errors.append({"name": name, "error": str(exc)})

    spec = read(BASE + "openapi.yaml")
    catalog = read(BASE + "interface-catalog.json")
    operations = {o["operationId"]: (method.upper(), "/api/v1" + path, o) for path, value in spec["paths"].items() for method, o in value.items() if method in METHODS}
    trace = read("docs/00-project/requirement-traceability.yaml")["requirements"]

    def operation_coverage():
        actual = {r["operation_id"]: r for r in catalog["operations"]}
        assert set(actual) == set(operations) and len(actual) == 55
        assert len(spec["components"]["schemas"]) == 85
        for oid, record in actual.items():
            method, path, op = operations[oid]
            assert (record["method"], record["path"], record["task_ids"], record["table_names"]) == (method, path, op["x-task-ids"], op["x-table-names"])
            assert (ROOT / record["detail_file"]).is_file() and record["formal_approved"] is False
        assert catalog["formal_frozen"] is False
        return {"business_operations": 55, "components": 85, "all_business_implemented": False}

    check("business_operation_and_schema_detail_coverage", operation_coverage)

    def source_drift():
        for path, expected in catalog["source_hashes"].items():
            assert digest(path) == expected, path
        expected = outputs()
        for path, content in expected.items():
            assert (ROOT / path).read_bytes() == content.encode("utf-8"), "DERIVED_INTERFACE_DOCUMENT_DRIFT:" + path
        return {"derived_files": len(expected), "source_hashes": len(catalog["source_hashes"]), "sources_or_types_rewritten_by_check": False}

    check("source_hashes_and_all_generated_docs_no_drift", source_drift)

    def module_coverage():
        assert {m["module"] for m in catalog["modules"]} == set(MODULES)
        for module in catalog["modules"]:
            reqs = [r for r in trace if r["requirement_id"].startswith("FR-" + module["module"] + "-")]
            assert len(reqs) == 3
            assert module["requirement_ids"] == [r["requirement_id"] for r in reqs]
            assert module["declared_business_operations"] == sorted({oid for r in reqs for oid in r["operation_ids"]})
            assert module["all_business_implemented"] is False
            assert (ROOT / module["doc_file"]).is_file()
        return {"modules": 12, "business_requirements": 36, "requirements_without_direct_API": sum(r["type"] == "functional" and not r["operation_ids"] for r in trace)}

    check("12_modules_and_exact_requirement_trace_not_invented", module_coverage)

    def inference_identity():
        op = read(BASE + "inference-openapi.yaml")["paths"]["/inference/{capability}"]["post"]
        models = read("docs/06-algorithms/model-catalog.yaml")["models"]
        assert len(models) == 34
        request = op["requestBody"]["content"]["application/json"]["schema"]["oneOf"]
        response = op["responses"]["200"]["content"]["application/json"]["schema"]["oneOf"]
        common = read("schemas/api/common.schema.json")

        def expand(value):
            if isinstance(value, list):
                return [expand(v) for v in value]
            if not isinstance(value, dict):
                return value
            if "$ref" in value:
                assert set(value) == {"$ref"}, "reference siblings need explicit intersection handling"
                document_id, pointer = value["$ref"].split("#", 1)
                assert document_id in {"", common["$id"]} and pointer.startswith("/$defs/"), "unexpected model reference source"
                target = common
                for part in pointer.lstrip("/").split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
                return expand(target)
            return {k: expand(v) for k, v in value.items()}

        for kind, branches in [("request", request), ("response", response)]:
            assert len(branches) == 34
            expected = [expand(read(f"schemas/model/{m['id']}.{kind}.schema.json")) for m in models]
            assert sorted(json.dumps(expand(b), sort_keys=True) for b in branches) == sorted(json.dumps(b, sort_keys=True) for b in expected), kind + " branch differs after resolving authoritative common references"
        return {"capabilities": 34, "resolved_independent_schema_branches": 68, "model_accuracy_or_all_backend_validation_asserted": False}

    check("34_inference_capabilities_and_68_schema_branches", inference_identity)

    def gaps():
        registry = read(BASE + "interface-gap-register.json")
        tasks = set(read("tasks/source-task-cards.json"))
        assert len(registry["items"]) == 13 and registry["formal_frozen"] is False
        assert len({r["id"] for r in registry["items"]}) == 13
        for item in registry["items"]:
            assert set(item["task_ids"]) <= tasks and set(item["existing_operation_ids"]) <= set(operations)
            assert item["owner_name"] is None and item["approved"] is False and item["candidate_routes_callable"] is (item["id"] == "IF-G01")
            assert item["evidence"] and item["proposed_detail"] and item["closure_criteria"]
            for route in item["candidate_routes_for_review"]:
                method, path = route.split(" ", 1)
                exists = (method, "/api/v1" + path) in {(v[0], v[1]) for v in operations.values()}
                assert exists is (item["id"] == "IF-G01"), (item["id"], method, path)
        return {"open_gaps": 13, "candidate_routes_added_to_API": ["GET /uploads/{id}", "GET /uploads/{id}/parts"], "task_dependencies_or_approvals_changed": False}

    check("13_explicit_gaps_and_non_callable_proposals", gaps)

    def implemented_boundary():
        backend = routes("backend/app/main.py")
        matching = {oid for oid, (method, path, _) in operations.items() if (method, path) in backend}
        assert matching == {"health"}
        business_routes = {(method, "/api/v1" + path) for method, path in routes("backend/business_app/uploads/router.py")}
        business_matching = {oid for oid, (method, path, _) in operations.items() if (method, path) in business_routes}
        assert business_matching == {"createUpload", "putUploadPart", "getUploadStatus", "listUploadParts"}
        matching |= business_matching
        annotations = read(BASE + "interface-annotations.json")["operations"]
        assert {oid for oid, a in annotations.items() if a["implementation_status"] == "DEV_PARTIAL"} == matching
        assert all(a["implementation_status"] == "CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API" for oid, a in annotations.items() if oid not in matching)
        assert ("POST", "/internal/v1/inference/retrieval.image_embedding") in routes("ai-services/inference/service.py")
        event = read("schemas/events/poc.analysis.requested.v1.schema.json")
        assert event["properties"]["event_type"]["const"] == "poc.analysis.requested.v1"
        return {"business_matching_development_partial_routes": 5, "all_business_API_implementation_asserted": False,
                "new_runtime_tests_executed": False, "one_PoC_event_not_cross_module_bus": True}

    check("source_code_PoC_boundary_not_business_acceptance", implemented_boundary)
    report = {"status": "FAIL" if errors else "PASS", "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "interface_document_lineage_coverage_and_open_gaps_not_runtime_or_business_acceptance",
              "checks": checks, "errors": errors, "formal_frozen": False, "business_contract_gap_count": 13,
              "contract_source_hashes": {p: digest(p) for p in [BASE + "openapi.yaml", BASE + "inference-openapi.yaml", "schemas/events/poc.analysis.requested.v1.schema.json"]}}
    (ROOT / "docs/00-project/validation/interface-documentation-report.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"status": report["status"], "checks": len(checks), "errors": errors}, ensure_ascii=False))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
