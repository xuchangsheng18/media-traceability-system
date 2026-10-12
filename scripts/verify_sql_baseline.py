"""Run the proposed business DDL in a brand-new, networkless disposable database."""
import datetime
import hashlib
import json
import re
import subprocess
import time
import uuid

from poc_control import ROOT, docker_env


def main():
    name = "mt-poc-sql-"+uuid.uuid4().hex[:12]
    image = "postgres@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d"
    report = {"scope": "isolated_database_constraints_not_production", "container": name, "image": image,
              "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "checks": []}
    created = False

    def docker(*args, data=None):
        return subprocess.run(["docker", *args], env=docker_env(), input=data, text=True, capture_output=True, timeout=60)

    try:
        result = docker("run", "--pull", "never", "-d", "--name", name, "--network", "none", "--memory", "512m",
                        "--cpus", "2", "--pids-limit", "128", "--user", "999:999", "--cap-drop", "ALL",
                        "--security-opt", "no-new-privileges", "--tmpfs", "/var/lib/postgresql/data:rw,size=512m,uid=999,gid=999,mode=0700",
                        "--tmpfs", "/var/run/postgresql:rw,size=16m,uid=999,gid=999,mode=0770",
                        "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-e", "POSTGRES_DB=input_validation", image)
        assert result.returncode == 0, result.stderr
        created = True
        for _ in range(25):
            if docker("exec", name, "pg_isready", "-U", "postgres", "-d", "input_validation").returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("DATABASE_NOT_READY")

        def sql(statement):
            return docker("exec", "-i", name, "psql", "-X", "-U", "postgres", "-d", "input_validation",
                          "-v", "ON_ERROR_STOP=1", data="\\set VERBOSITY verbose\n"+statement)

        for path in ["docs/04-database/initial-schema.sql", "tests/sql/integrity-tests.sql", "tests/sql/ranking-fixtures.sql"]:
            body = (ROOT/path).read_text()
            result = sql(body)
            assert result.returncode == 0, result.stderr
            report["checks"].append({"name": path, "sha256": hashlib.sha256(body.encode()).hexdigest(), "status": "PASS"})
        for case in json.loads((ROOT/"tests/sql/first-source-cases.json").read_text())["cases"]:
            result = sql(case["sql"])
            expected = case["expected_sqlstate"]
            passed = result.returncode == 0 if expected is None else result.returncode != 0 and re.search(r"ERROR:\s+"+expected+r":", result.stderr)
            assert passed, case["name"]+":"+result.stderr[-1200:]
            report["checks"].append({"name": case["name"], "expected_sqlstate": expected, "status": "PASS"})
        report["status"] = "PASS"
    except Exception as exc:
        report.update(status="FAIL", error=str(exc))
    finally:
        if created:
            removed = docker("rm", "-f", name)
            report["cleanup_exit_code"] = removed.returncode
            if removed.returncode:
                report["status"] = "FAIL"
        report["ended_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (ROOT/"docs/00-project/validation/database-foundation-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": report["status"], "checks": len(report["checks"])}))
    return report["status"] != "PASS"


if __name__ == "__main__":
    raise SystemExit(main())
