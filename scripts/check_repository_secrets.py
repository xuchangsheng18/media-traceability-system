"""Check this repository for exact private development credentials without printing them."""
import json

from poc_control import ROOT, RUNTIME


def main():
    excluded = {".git", "node_modules", "dist", "build", "__pycache__", ".pytest_cache", ".ruff_cache", "test-results"}
    values = [v.encode() for v in json.loads((RUNTIME/"credentials.json").read_text()).values()]
    errors, total = [], 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(p in excluded for p in path.relative_to(ROOT).parts):
            continue
        total += 1
        data = path.read_bytes()
        if any(value in data for value in values) or path.name in {"credentials.json", "poc.env", "postgres.env", "rabbitmq.env", "s3.json"}:
            errors.append(path.relative_to(ROOT).as_posix())
    report = {"status": "FAIL" if errors else "PASS", "scope": "exact_runtime_values_and_known_secret_filenames_not_comprehensive_dlp",
              "files_checked": total, "errors": errors, "credential_values_printed": False}
    (ROOT/"docs/00-project/validation/repository-secrets-report.json").write_text(json.dumps(report, indent=2)+"\n")
    assert not errors, "PRIVATE_CREDENTIALS_FOUND"
    print(json.dumps({"status": "PASS", "files_checked": total}))


if __name__ == "__main__":
    main()
