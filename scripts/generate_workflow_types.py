"""Generate workflow/shared model types from local authoritative JSON Schemas."""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from generate_interface_docs import ROOT, read

SOURCES = {"WorkflowDag": "schemas/workflow/dag.schema.json", "RunResultSnapshot": "schemas/workflow/run-result.schema.json",
           "WorkflowDomainEvent": "schemas/events/workflow.domain.v1.schema.json", "BusinessParameters": "schemas/controls/business-parameters.schema.json"}


def document():
    common = read("schemas/api/common.schema.json")
    components = dict(common["$defs"])
    id_names = {common["$id"]: None}
    for name, path in SOURCES.items():
        schema = read(path)
        components[name] = schema
        id_names[schema["$id"]] = name
    for i in range(1, 35):
        model_id = f"M{i:02}"
        name = model_id + "Response"
        schema = read(f"schemas/model/{model_id}.response.schema.json")
        components[name] = schema
        id_names[schema["$id"]] = name

    def convert(value):
        if isinstance(value, list):
            return [convert(v) for v in value]
        if not isinstance(value, dict):
            return value
        converted = {k: convert(v) for k, v in value.items() if k not in {"$schema", "$id"}}
        if converted.get("$ref", "").startswith("#/$defs/"):
            converted["$ref"] = "#/components/schemas/" + converted["$ref"].removeprefix("#/$defs/")
        if "$ref" in converted and converted["$ref"].startswith("urn:"):
            identifier, _, pointer = converted["$ref"].partition("#")
            assert identifier in id_names, "Unknown workflow type source:" + identifier
            if identifier == common["$id"]:
                assert pointer.startswith("/$defs/")
                converted["$ref"] = "#/components/schemas/" + pointer.removeprefix("/$defs/")
            else:
                assert not pointer
                converted["$ref"] = "#/components/schemas/" + id_names[identifier]
        return converted

    return {"openapi": "3.1.0", "info": {"title": "Locally generated workflow and capability wrapper", "version": "0.1.0"},
            "paths": {}, "components": {"schemas": convert(components)}}


def generate(output):
    with tempfile.TemporaryDirectory(prefix="mt-workflow-types-") as folder:
        source = Path(folder) / "workflow-openapi.json"
        source.write_text(json.dumps(document()), encoding="utf-8")
        node = shutil.which("node")
        assert node, "Node runtime not available in PATH"
        subprocess.run([node, str(ROOT / "frontend/node_modules/openapi-typescript/bin/cli.js"), str(source), "-o", str(output)],
                       check=True, cwd=ROOT, env=dict(os.environ))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "shared-contracts/generated/workflow.d.ts"
    if args.check:
        with tempfile.TemporaryDirectory(prefix="mt-workflow-compare-") as folder:
            output = Path(folder) / "workflow.d.ts"
            generate(output)
            assert output.read_bytes() == target.read_bytes(), "WORKFLOW_GENERATED_TYPE_DRIFT"
    else:
        generate(target)


if __name__ == "__main__":
    main()
