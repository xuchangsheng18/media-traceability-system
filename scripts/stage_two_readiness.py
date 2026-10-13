"""Fail-closed capacity and offline artifact digest checks. No cleanup, allocation or credentials."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def storage_state(volume, policy):
    total, available = volume["total_bytes"], volume["available_bytes"]
    used = volume["used_bytes"]
    if total <= 0 or min(available, used) < 0 or available+used > total:
        raise ValueError("INVALID_STORAGE_SNAPSHOT")
    if not 0 < policy["warning_used_percent"] < policy["critical_used_percent"] < 100:
        raise ValueError("INVALID_THRESHOLDS")
    percent = used/total*100
    critical = percent >= policy["critical_used_percent"] or available < policy["minimum_free_bytes"]
    return "CRITICAL" if critical else "WARNING" if percent >= policy["warning_used_percent"] else "OK"


def verify_artifacts(directory, records):
    root = Path(directory).resolve()
    if not records:
        raise ValueError("EMPTY_DELIVERY_MANIFEST")
    names = set()
    for record in records:
        name = record["path"]
        if name in names or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("UNSAFE_OR_DUPLICATE_ARTIFACT")
        names.add(name)
        path = (root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("ARTIFACT_MISSING_OR_OUTSIDE_ROOT")
        with path.open("rb") as stream:
            digest = hashlib.sha256()
            while block := stream.read(1024*1024):
                digest.update(block)
        if path.stat().st_size != record["size_bytes"] or digest.hexdigest() != record["sha256"]:
            raise ValueError("ARTIFACT_DIGEST_MISMATCH")
    return len(names)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-manifest", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--require-capacity", action="store_true", help="Exit nonzero when the observed development capacity is critical")
    args = parser.parse_args()
    if args.offline_manifest:
        if not args.artifact_root:
            parser.error("--artifact-root required")
        manifest = json.loads(args.offline_manifest.read_text())
        count = verify_artifacts(args.artifact_root, manifest["artifacts"])
        print(json.dumps({"status": "PASS", "verified_artifacts": count, "production_release_approved": False}))
        return 0
    source = ROOT/"docs/00-project/validation/resource-readiness-snapshot.json"
    snapshot = json.loads(source.read_text())
    policy = json.loads((ROOT/"config/stage-two-operations.candidate.json").read_text())["storage"]
    state = storage_state(snapshot["development_postgres_volume_filesystem"], policy)
    report = {"status": "OBSERVED_ACTION_REQUIRED" if state != "OK" else "OBSERVED", "storage_state": state,
              "scope": "development_volume_snapshot_candidate_thresholds_not_live_continuous_monitor",
              "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "snapshot_at": snapshot["observed_at"],
              "source_snapshot_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "candidate_thresholds": policy,
              "resource_readiness": "NOT_READY" if state == "CRITICAL" else "QUOTAS_UNCONFIRMED",
              "resources_allocated_or_cleaned": False, "formal_RPO_RTO_or_storage_quota_approved": False}
    (ROOT/"docs/00-project/validation/stage-two-resource-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"storage_state": state, "resource_readiness": report["resource_readiness"]}))
    return int(args.require_capacity and state == "CRITICAL")


if __name__ == "__main__":
    raise SystemExit(main())
