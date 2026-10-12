"""Regenerate types in scratch space and fail when committed types have drifted."""
import hashlib
import json
import os
import subprocess
import tempfile

from poc_control import ROOT


def main():
    checks = []
    cli = ROOT/"frontend/node_modules/.bin/openapi-typescript"
    with tempfile.TemporaryDirectory(prefix="mt-contracts-") as folder:
        for source, target in [("docs/03-api/openapi.yaml", "business-api.d.ts"),
                               ("docs/03-api/inference-openapi.yaml", "inference-api.d.ts")]:
            output = os.path.join(folder, target)
            subprocess.run([str(cli), str(ROOT/source), "-o", output], check=True, cwd=ROOT)
            expected = (ROOT/"shared-contracts/generated"/target).read_bytes()
            with open(output, "rb") as stream:
                assert stream.read() == expected, "GENERATED_CONTRACT_DRIFT:"+target
            checks.append({"source": source, "generated": target, "status": "PASS",
                           "sha256": hashlib.sha256(expected).hexdigest()})
    (ROOT/"docs/00-project/validation/generated-contract-report.json").write_text(json.dumps({"status": "PASS", "checks": checks}, indent=2)+"\n")


if __name__ == "__main__":
    main()
