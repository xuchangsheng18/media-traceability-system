"""Regenerate types in scratch space and fail when committed types have drifted."""
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from poc_control import ROOT


def main():
    checks = []
    cli = ROOT/"frontend/node_modules/.bin/openapi-typescript"
    with tempfile.TemporaryDirectory(prefix="mt-contracts-") as folder:
        schema = json.loads((ROOT/"schemas/events/poc.analysis.requested.v1.schema.json").read_text())
        schema.pop("$id")
        schema.pop("$schema")
        event_source = os.path.join(folder, "event-openapi.json")
        with open(event_source, "w") as stream:
            json.dump({"openapi": "3.1.0", "info": {"title": "Generated development event wrapper", "version": "1.0.0"},
                       "paths": {}, "components": {"schemas": {"PocAnalysisRequestedEvent": schema}}}, stream)
        for source, target in [("docs/03-api/openapi.yaml", "business-api.d.ts"),
                               ("docs/03-api/inference-openapi.yaml", "inference-api.d.ts"),
                               (event_source, "poc-event.d.ts")]:
            output = os.path.join(folder, target)
            subprocess.run([str(cli), str(ROOT/source), "-o", output], check=True, cwd=ROOT)
            expected = (ROOT/"shared-contracts/generated"/target).read_bytes()
            with open(output, "rb") as stream:
                assert stream.read() == expected, "GENERATED_CONTRACT_DRIFT:"+target
            checks.append({"source": "schemas/events/poc.analysis.requested.v1.schema.json" if target == "poc-event.d.ts" else source, "generated": target, "status": "PASS",
                           "sha256": hashlib.sha256(expected).hexdigest()})
    from generate_workflow_types import generate

    with tempfile.TemporaryDirectory(prefix="mt-workflow-drift-") as workflow_folder:
        output = Path(workflow_folder) / "workflow.d.ts"
        generate(output)
        expected = (ROOT / "shared-contracts/generated/workflow.d.ts").read_bytes()
        assert output.read_bytes() == expected, "GENERATED_WORKFLOW_CONTRACT_DRIFT"
        checks.append({"source": "schemas/workflow and schemas/events/workflow.domain.v1.schema.json and schemas/controls", "generated": "workflow.d.ts",
                       "status": "PASS", "sha256": hashlib.sha256(expected).hexdigest()})
    (ROOT/"docs/00-project/validation/generated-contract-report.json").write_text(json.dumps({"status": "PASS", "checks": checks}, indent=2)+"\n")


if __name__ == "__main__":
    main()
