"""Real RLS and Chinese lexical queries on disposable PostgreSQL16, not production integration."""
import datetime
import hashlib
import json
import secrets
import subprocess
import time
import unicodedata
import uuid

import psycopg
from poc_control import ROOT, docker_env
from psycopg import sql


def chinese_tokens(value):
    normalized = unicodedata.normalize("NFKC", value).casefold()
    groups, current = [], ""
    for character in normalized:
        if "\u4e00" <= character <= "\u9fff":
            current += character
        else:
            if current:
                groups.append(current)
                current = ""
    if current:
        groups.append(current)
    return sorted({word[i:i+2] for word in groups for i in range(len(word)-1)} |
                  {word for word in groups if len(word) == 1})


def main():
    name = "mt-isolation-probe-" + uuid.uuid4().hex[:12]
    password, checks = secrets.token_hex(24), []
    env, created = docker_env(), False

    def docker(*args):
        return subprocess.run(["docker", *args], env=env, check=True, capture_output=True,
                              text=True, timeout=60).stdout

    def check(label, condition):
        assert condition, label
        checks.append({"name": label, "status": "PASS"})

    try:
        docker("run", "--pull", "never", "-d", "--name", name, "--memory", "512m", "--cpus", "1",
               "--pids-limit", "128", "-p", "127.0.0.1::5432", "--tmpfs", "/var/lib/postgresql/data:rw,size=256m",
               "-e", "POSTGRES_PASSWORD="+password,
               "postgres@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d")
        created = True
        port = int(json.loads(docker("inspect", name))[0]["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostPort"])
        settings = dict(host="127.0.0.1", port=port, dbname="postgres", password=password)
        for _ in range(30):
            try:
                admin = psycopg.connect(user="postgres", **settings)
                break
            except psycopg.OperationalError:
                time.sleep(1)
        else:
            raise RuntimeError("ISOLATED_DATABASE_NOT_READY")
        with admin:
            source = ROOT/"tests/sql/authorization-prototype.sql"
            admin.execute(source.read_text())
            admin.execute(sql.SQL("ALTER ROLE probe_app PASSWORD {}").format(sql.Literal(password)))
            subject, org_a, org_b, case_a, case_b, task = [uuid.uuid4() for _ in range(6)]
            admin.execute("INSERT INTO isolation_probe.grants VALUES(%s,%s,%s,true,false)", (subject, org_a, case_a))
            for org, case, version in [(org_a, case_a, 1), (org_a, case_a, 2), (org_a, case_b, 1), (org_b, case_a, 1)]:
                admin.execute("INSERT INTO isolation_probe.results VALUES(%s,%s,%s,%s,1,%s,'{}')",
                              (uuid.uuid4(), org, case, task, version))
            admin.commit()

            def context(app, org=org_a, case=case_a):
                for key, value in [("subject_id", subject), ("org_id", org), ("case_id", case)]:
                    app.execute("SELECT set_config(%s,%s,true)", ("mt."+key, str(value)))

            def denied(app, label, statement, parameters=()):
                blocked = False
                try:
                    with app.transaction():
                        app.execute(statement, parameters)
                except psycopg.errors.InsufficientPrivilege:
                    blocked = True
                check(label, blocked)

            with psycopg.connect(user="probe_app", autocommit=True, **settings) as app:
                check("missing_context_returns_no_rows", app.execute("SELECT count(*) FROM isolation_probe.results").fetchone()[0] == 0)
                with app.transaction():
                    context(app)
                    rows = app.execute("SELECT org_id,case_id,result_version FROM isolation_probe.results ORDER BY result_version").fetchall()
                    check("org_case_and_history_isolation", rows == [(org_a, case_a, 1), (org_a, case_a, 2)])
                    denied(app, "cross_case_insert_denied", "INSERT INTO isolation_probe.results VALUES(%s,%s,%s,%s,1,3,'{}')",
                           (uuid.uuid4(), org_a, case_b, task))
                    denied(app, "cross_org_insert_denied", "INSERT INTO isolation_probe.results VALUES(%s,%s,%s,%s,1,3,'{}')",
                           (uuid.uuid4(), org_b, case_a, task))
                    app.execute("INSERT INTO isolation_probe.results VALUES(%s,%s,%s,%s,1,3,'{}')",
                                (uuid.uuid4(), org_a, case_a, task))
                    check("authorized_new_version_append", app.execute("SELECT count(*) FROM isolation_probe.results").fetchone()[0] == 3)
                    denied(app, "history_update_denied", "UPDATE isolation_probe.results SET payload='{}'")
                    denied(app, "history_delete_denied", "DELETE FROM isolation_probe.results")
                    denied(app, "acl_write_denied", "UPDATE isolation_probe.grants SET revoked=false")
                check("pooled_connection_local_context_cleared", app.execute("SELECT count(*) FROM isolation_probe.results").fetchone()[0] == 0)
                with app.transaction():
                    context(app, case=case_b)
                    check("context_without_acl_cannot_read", app.execute("SELECT count(*) FROM isolation_probe.results").fetchone()[0] == 0)
                with app.transaction():
                    context(app)
                    admin.execute("UPDATE isolation_probe.grants SET revoked=true")
                    admin.commit()
                    check("revocation_visible_next_statement_read_committed", app.execute("SELECT count(*) FROM isolation_probe.results").fetchone()[0] == 0)
                    denied(app, "revoked_append_denied", "INSERT INTO isolation_probe.results VALUES(%s,%s,%s,%s,1,4,'{}')",
                           (uuid.uuid4(), org_a, case_a, task))
                flags = admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='probe_app'").fetchone()
                check("application_role_no_superuser_no_bypass", flags == (False, False))
                flags = admin.execute("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname='results'").fetchone()
                check("table_enable_and_force_rls", flags == (True, True))

            # A lexical prototype with explicit token semantics and an actual GIN index.
            admin.execute("CREATE TABLE isolation_probe.texts(id integer PRIMARY KEY, tokens text[] NOT NULL)")
            samples = {1: "视频证据溯源与案件复核", 2: "音频来源核验", 3: "天气预报", 4: "证据，溯源"}
            for number, title in samples.items():
                admin.execute("INSERT INTO isolation_probe.texts VALUES(%s,%s)", (number, chinese_tokens(title)))
            admin.execute("CREATE INDEX lexical_probe_gin ON isolation_probe.texts USING gin(tokens)")

            def query(value):
                tokens = chinese_tokens(value)
                if not tokens:
                    return []
                return [row[0] for row in admin.execute("SELECT id FROM isolation_probe.texts WHERE tokens @> %s ORDER BY id", (tokens,))]

            check("chinese_lexical_query_actual_sql", query("证据") == [1, 4])
            check("chinese_and_query_actual_sql", query("证据 溯源") == [1, 4])
            check("chinese_unseen_term_empty", query("秘密") == [])
            check("empty_tokens_do_not_match_everything", query("---") == [])
            check("punctuation_does_not_create_false_cross_boundary_token", "据溯" not in chinese_tokens("证据，溯源"))
            check("unicode_normalization_explicit", chinese_tokens("案件，复核") == chinese_tokens("案件,复核"))
            admin.execute("SET LOCAL enable_seqscan=off")
            plan = admin.execute("EXPLAIN (FORMAT JSON) SELECT id FROM isolation_probe.texts WHERE tokens @> %s", (["证据"],)).fetchone()[0]
            check("actual_gin_index_access_plan", "lexical_probe_gin" in json.dumps(plan))
        report = {"status": "PASS", "scope": "isolated_representative_RLS_append_history_and_4_document_Chinese_lexical_GIN",
                  "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "checks": checks,
                  "sql_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "temporary_database_removed": True,
                  "existing_database_changed": False, "formal_identity_integrated": False,
                  "business_62_table_RLS_deployed": False, "production_privileged_immutability_validated": False,
                  "chinese_semantic_search_validated": False, "large_index_or_performance_validated": False}
    finally:
        if created:
            docker("rm", "-f", name)
    (ROOT/"docs/00-project/validation/stage-two-isolation-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "checks": len(checks), "existing_database_changed": False}))


if __name__ == "__main__":
    main()
