"""Real database race and migration checks in a new, isolated development database."""
import concurrent.futures
import datetime
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import psycopg
from poc_control import ROOT, docker_env
from sqlalchemy import create_engine


def main():
    suffix = uuid.uuid4().hex[:12]
    name, network = "mt-fence-test-"+suffix, "mt-fence-net-"+suffix
    password = secrets.token_hex(24)
    env = docker_env()
    checks = []
    created = False

    def docker(*args, data=None):
        return subprocess.run(["docker", *args], env=env, input=data, text=True, capture_output=True, check=True, timeout=60).stdout

    def check(label, condition):
        assert condition, label
        checks.append({"name": label, "status": "PASS"})

    docker("network", "create", network)
    try:
        docker("run", "--pull", "never", "-d", "--name", name, "--network", network, "--memory", "512m", "--cpus", "1",
               "--pids-limit", "128", "-p", "127.0.0.1::5432", "--tmpfs", "/var/lib/postgresql/data:rw,size=512m",
               "-e", "POSTGRES_DB=media_trace_poc", "-e", "POSTGRES_PASSWORD="+password,
               "postgres@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d")
        created = True
        inspected = json.loads(docker("inspect", name))[0]
        port = int(inspected["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostPort"])
        for _ in range(30):
            try:
                admin = psycopg.connect(host="127.0.0.1", port=port, user="postgres", password=password, dbname="media_trace_poc")
                break
            except psycopg.OperationalError:
                time.sleep(1)
        else:
            raise RuntimeError("TEST_DATABASE_NOT_READY")
        sys.path.insert(0, str(ROOT/"backend"))
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://postgres:{password}@127.0.0.1:{port}/media_trace_poc"
        from app import leases
        from app.common import CASE_ID
        from app.contracts import EVENT
        from app.migrations import configure_application_grants, run_migrations

        with admin:
            # Start with an existing 1.0 schema, as on the development host.
            admin.execute((ROOT/"backend/migrations/0001_poc.sql").read_text())
            admin.commit()
            changed = run_migrations(admin)
            check("legacy_schema_incremental_upgrade", changed == ["0001_poc.sql", "0002_event_leases_audit.sql"])
            check("repeat_migration_no_effect", run_migrations(admin) == [])
            with tempfile.TemporaryDirectory(prefix="mt-migration-copy-") as directory:
                for p in (ROOT/"backend/migrations").glob("*.sql"):
                    shutil.copyfile(p, Path(directory)/p.name)
                changed_path = Path(directory)/"0001_poc.sql"
                changed_path.write_text(changed_path.read_text()+"\n-- intentional checksum probe\n")
                rejected = False
                try:
                    run_migrations(admin, Path(directory))
                except RuntimeError as error:
                    rejected = str(error) == "APPLIED_MIGRATION_CHECKSUM_CHANGED"
                check("changed_applied_migration_rejected", rejected)
            from psycopg import sql
            admin.execute(sql.SQL("CREATE ROLE poc_app LOGIN PASSWORD {}").format(sql.Literal(password)))
            configure_application_grants(admin)
            asset, job, request_id = [str(uuid.uuid4()) for _ in range(3)]
            ref = {"object_id": str(uuid.uuid4()), "version_id": "synthetic", "sha256": "a"*64}
            admin.execute("INSERT INTO poc.assets(asset_id,case_id,filename,object_ref,analysis_ref,size_bytes) VALUES(%s,%s,%s,%s,%s,1)",
                          (asset, CASE_ID, "synthetic.png", json.dumps(ref), json.dumps(ref)))
            admin.execute("INSERT INTO poc.jobs(job_id,case_id,asset_id,idempotency_key,state,request_id,trace_origin) VALUES(%s,%s,%s,%s,'QUEUED',%s,'api')",
                          (job, CASE_ID, asset, "race-"+job, request_id))
            admin.commit()
            engine = create_engine(f"postgresql+psycopg://poc_app:{password}@127.0.0.1:{port}/media_trace_poc", pool_size=8)
            leases.engine = engine
            event = {"schema_version": "1.0.0", "event_type": "poc.analysis.requested.v1", "event_id": str(uuid.uuid4()),
                     "occurred_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "request_id": request_id,
                     "case_id": CASE_ID, "producer": "backend.poc", "trace_origin": "api", "payload": {"job_id": job, "asset_id": asset}}
            EVENT.validate(event)
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                claims = list(pool.map(leases.claim_job, [event]*8))
            claims = [c for c in claims if c is not None]
            check("eight_contenders_one_atomic_claim", len(claims) == 1)
            old = claims[0]
            admin.execute("UPDATE poc.jobs SET lease_until=now()-interval '1 second' WHERE job_id=%s", (job,))
            admin.commit()
            check("expired_lease_write_rejected", leases.finish_job(old, result={"old": True}) is False)
            new = leases.claim_job(event)
            check("new_claim_changes_token_and_version", new["lease_token"] != old["lease_token"] and new["run_version"] == 2)
            check("old_token_cannot_overwrite_new_claim", leases.finish_job(old, result={"old": True}) is False)
            check("old_failure_cannot_reset_new_claim", leases.finish_job(old, error_code="OLD_FAILURE", retry=True) is False)
            check("current_token_result_accepted", leases.finish_job(new, result={"current": True}) is True)
            row = admin.execute("SELECT state,result,attempts FROM poc.jobs WHERE job_id=%s", (job,)).fetchone()
            check("result_and_attempts_preserved", row == ("SUCCEEDED", {"current": True}, 2))
            with psycopg.connect(host="127.0.0.1", port=port, user="poc_app", password=password, dbname="media_trace_poc") as app:
                for label, statement in [("audit_update_denied", "UPDATE poc.job_events SET details='{}'"),
                                          ("audit_delete_denied", "DELETE FROM poc.job_events"),
                                          ("original_reference_update_denied", "UPDATE poc.assets SET object_ref='{}'"),
                                          ("migration_history_update_denied", "UPDATE poc.schema_migrations SET sha256='0'")]:
                    denied = False
                    try:
                        with app.transaction():
                            app.execute(statement)
                    except psycopg.errors.InsufficientPrivilege:
                        denied = True
                    check(label, denied)
            engine.dispose()
            versions = admin.execute("SELECT version,sha256 FROM poc.schema_migrations ORDER BY version").fetchall()
            check("migration_hashes_match_sources", all(hashlib.sha256((ROOT/"backend/migrations"/v).read_bytes()).hexdigest() == d for v, d in versions))
        status = "PASS"
    finally:
        if created:
            docker("rm", "-f", name)
        docker("network", "rm", network)
    report = {"status": status, "scope": "isolated_development_migration_and_database_claim_races", "checks": checks,
              "contenders": 8, "temporary_resources_removed": True, "production_policy_validated": False}
    (ROOT/"docs/00-project/validation/migration-fencing-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": status, "checks": len(checks)}))


if __name__ == "__main__":
    main()
