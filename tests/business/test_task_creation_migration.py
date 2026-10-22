"""I01 adds private immutable plan materials, never an adopted business mapping."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from tests.business.test_migrations import MIGRATIONS, migrate

PRIVATE_TABLES = {
    "task_policy_artifact",
    "task_plan_artifact",
    "task_capability_manifest",
    "task_plan_mapping_revision",
    "task_plan_mapping_head",
}
NEW_TABLES = PRIVATE_TABLES | {"task_run_plan"}
CANONICALIZATION = "task-material-json-utf8-sortkeys-v1"
COLUMNS = {
    "task_policy_artifact": 11,
    "task_plan_artifact": 10,
    "task_capability_manifest": 10,
    "task_plan_mapping_revision": 27,
    "task_plan_mapping_head": 12,
    "task_run_plan": 36,
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def insert(connection, table, value):
    keys = tuple(value)
    connection.execute(
        sql.SQL("INSERT INTO mt.{} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(",").join(map(sql.Identifier, keys)),
            sql.SQL(",").join(sql.Placeholder() for _ in keys),
        ),
        tuple(value[key] for key in keys),
    )


def legacy_rows(connection):
    org, other_org, user, other_user, case, other_case, policy, obj, source, content, asset, task = [
        uuid4() for _ in range(12)
    ]
    for org_id, user_id, case_id in [(org, user, case), (other_org, other_user, other_case)]:
        connection.execute("INSERT INTO mt.organizations(org_id,name) VALUES(%s,'synthetic-I01-only')", (org_id,))
        connection.execute(
            "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)",
            (user_id, org_id, str(user_id)),
        )
        connection.execute(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
            (case_id, org_id, str(case_id)),
        )
        connection.execute(
            "INSERT INTO mt.case_membership(membership_id,org_id,case_id,user_id) VALUES(%s,%s,%s,%s)",
            (uuid4(), org_id, case_id, user_id),
        )
    connection.execute(
        "INSERT INTO mt.policy_registry(policy_id,org_id,kind,version,definition_ref,status,created_by) "
        "VALUES(%s,%s,'synthetic-policy','fixture-policy/1','fixture-only-not-adopted','DRAFT',%s)",
        (policy, org, user),
    )
    connection.execute(
        "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) "
        "VALUES(%s,%s,%s,'fixture','synthetic','not-formal-authority',ARRAY['analysis'],'pending','fixture-source/1')",
        (source, org, case),
    )
    connection.execute(
        "INSERT INTO mt.content_item(content_id,org_id,case_id,source_id,discovered_at,status) "
        "VALUES(%s,%s,%s,%s,now(),'fixture')",
        (content, org, case, source),
    )
    connection.execute(
        "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,size_bytes) "
        "VALUES(%s,%s,%s,'fixture','fixture','fixture-object/1',%s,1)",
        (obj, org, case, "a" * 64),
    )
    connection.execute(
        "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,kind,mapping_version,state) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,'application/octet-stream',1,'original','fixture-only','VALIDATING')",
        (asset, org, case, content, source, obj, "a" * 64),
    )
    connection.execute(
        "INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility) "
        "VALUES(%s,%s,%s,%s,'accident_rumor','normal','CREATED','fixture-policy/1',ARRAY['MEDIA','RESOURCE'],'draft_only')",
        (task, org, case, asset),
    )
    # These bytes exercise SQL byte/FK invariants only, not material Schema,
    # authoritative adoption, executable handlers or a successful task result.
    input_bytes = canonical({"synthetic_sql_input": str(asset), "formal_authorization": False})
    connection.execute(
        "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,policy_version) "
        "VALUES(%s,%s,%s,%s,1,%s,'fixture-plan/1','fixture-policy/1')",
        (uuid4(), org, case, task, sha(input_bytes)),
    )
    return dict(
        org=org,
        other_org=other_org,
        user=user,
        other_user=other_user,
        case=case,
        other_case=other_case,
        policy=policy,
        asset=asset,
        task=task,
        input_bytes=input_bytes,
    )


def material_rows(connection, values):
    org, user, case, policy = [values[key] for key in ("org", "user", "case", "policy")]
    common = dict(
        org_id=org,
        canonicalization_version=CANONICALIZATION,
        provenance_ref="fixture-only-no-adoption",
        created_by=user,
    )
    policy_bytes = canonical({"synthetic_sql_policy": "no-adoption"})
    plan_bytes = canonical({"synthetic_sql_plan": "no-handler-execution"})
    capability_bytes = canonical({"synthetic_sql_capability": "no-dynamic-provider"})
    receipt_bytes = canonical({"synthetic_sql_receipt": True, "authority_adopted": False})
    insert(
        connection,
        "task_policy_artifact",
        dict(
            common,
            policy_id=policy,
            policy_kind="synthetic-policy",
            policy_version="fixture-policy/1",
            canonical_bytes=policy_bytes,
            policy_sha256=sha(policy_bytes),
            schema_version="urn:media-trace:api:0.1.0#/$defs/PolicyDefinition",
        ),
    )
    insert(
        connection,
        "task_plan_artifact",
        dict(
            common,
            plan_id="fixture-plan",
            plan_version="fixture-plan/1",
            canonical_bytes=plan_bytes,
            plan_sha256=sha(plan_bytes),
            schema_version="urn:media-trace:task-execution-plan:1.0.0",
        ),
    )
    insert(
        connection,
        "task_capability_manifest",
        dict(
            common,
            capability_id="fixture-capabilities",
            capability_version="fixture-capabilities/1",
            canonical_bytes=capability_bytes,
            capability_sha256=sha(capability_bytes),
            schema_version="urn:media-trace:task-capability-manifest:1.0.0",
        ),
    )
    observed = datetime.now(timezone.utc)
    revision = dict(
        revision_id=uuid4(),
        org_id=org,
        case_id=case,
        mapping_id="fixture-mapping",
        mapping_version="fixture-mapping/1",
        authority_version="fixture-authority/1",
        scene="accident_rumor",
        modules=["MEDIA", "RESOURCE"],
        priority="normal",
        policy_id=policy,
        policy_kind="synthetic-policy",
        policy_version="fixture-policy/1",
        policy_sha256=sha(policy_bytes),
        plan_id="fixture-plan",
        plan_version="fixture-plan/1",
        plan_sha256=sha(plan_bytes),
        capability_id="fixture-capabilities",
        capability_version="fixture-capabilities/1",
        capability_sha256=sha(capability_bytes),
        valid_from=observed - timedelta(minutes=1),
        valid_until=observed + timedelta(minutes=30),
        adoption_basis_ref="fixture-only-not-a-real-adoption",
        recovery_generation="fixture-recovery/1",
        validation_receipt_bytes=receipt_bytes,
        validation_receipt_sha256=sha(receipt_bytes),
        created_by=user,
    )
    insert(connection, "task_plan_mapping_revision", revision)
    head = {
        key: revision[key]
        for key in ["org_id", "case_id", "scene", "policy_id", "policy_version", "modules", "priority", "revision_id"]
    }
    head.update(state="INACTIVE", changed_by=user)
    insert(connection, "task_plan_mapping_head", head)
    request = canonical(
        dict(
            case_id=str(case),
            asset_id=str(values["asset"]),
            scene="accident_rumor",
            policy_version="fixture-policy/1",
            modules=["MEDIA", "RESOURCE"],
            priority="normal",
        )
    )
    run = {
        key: revision[key]
        for key in [
            "org_id",
            "case_id",
            "revision_id",
            "mapping_id",
            "mapping_version",
            "authority_version",
            "policy_id",
            "policy_kind",
            "policy_version",
            "policy_sha256",
            "plan_id",
            "plan_version",
            "plan_sha256",
            "capability_id",
            "capability_version",
            "capability_sha256",
            "validation_receipt_bytes",
            "validation_receipt_sha256",
            "recovery_generation",
            "created_by",
        ]
    }
    run.update(
        task_id=values["task"],
        run_version=1,
        request_body_bytes=request,
        request_body_sha256=sha(request),
        authorization_request_digest=sha(b"synthetic-path-query-body-envelope"),
        head_row_version=1,
        policy_bytes=policy_bytes,
        plan_bytes=plan_bytes,
        capability_bytes=capability_bytes,
        input_manifest_bytes=values["input_bytes"],
        input_sha256=sha(values["input_bytes"]),
        mapping_valid_from=revision["valid_from"],
        mapping_valid_until=revision["valid_until"],
        proof_observed_at=observed,
        proof_valid_until=observed + timedelta(minutes=1),
    )
    return dict(values, common=common, revision=revision, head=head, run=run)


I01_UNREGISTERED_HISTORY_TESTS = {
    "test_i01_runtime_cannot_read_private_tables_or_use_unregistered_create_scope",
    "test_i01_private_roles_do_not_enable_material_access_without_i02_scope",
}


@pytest.fixture
def i01_context(database_dsn, request, tmp_path):
    if request.node.originalname in I01_UNREGISTERED_HISTORY_TESTS:
        # The parent-owned conftest routes only these cases to a new template0
        # database. Preserve the original I01 assertions against real0016,
        # never remove0017 from an already-upgraded database or relax a check.
        with psycopg.connect(database_dsn) as connection:
            assert connection.execute("SELECT to_regclass('mt_meta.schema_migrations')").fetchone() == (None,)
        history = tmp_path / "through0016"
        history.mkdir()
        files = [path for path in sorted(MIGRATIONS.glob("*.sql")) if path.name[:4] <= "0016"]
        assert len(files) == 16
        for path in files:
            (history / path.name).write_bytes(path.read_bytes())
        assert migrate(database_dsn, history) == [f"{version:04d}" for version in range(1, 17)]
        with psycopg.connect(database_dsn) as connection:
            assert connection.execute("SELECT max(version),count(*) FROM mt_meta.schema_migrations").fetchone() == (
                "0016",
                16,
            )
    else:
        migrate(database_dsn)
    with psycopg.connect(database_dsn) as connection:
        return material_rows(connection, legacy_rows(connection))


def test_i01_empty_upgrade_registers_six_private_tables(database_dsn):
    migrate(database_dsn)
    with psycopg.connect(database_dsn) as connection:
        present = {
            row[0]
            for row in connection.execute(
                "SELECT relname FROM pg_class WHERE relnamespace='mt'::regnamespace AND relkind='r' "
                "AND relname=ANY(%s::text[])",
                (sorted(NEW_TABLES),),
            ).fetchall()
        }
        assert present == NEW_TABLES


def test_i01_migration_is_append_only_to_history_and_replay_noops(database_dsn, tmp_path):
    previous = sorted(file for file in MIGRATIONS.glob("*.sql") if file.name[:4] <= "0015")
    for file in previous:
        (tmp_path / file.name).write_bytes(file.read_bytes())
    assert migrate(database_dsn, tmp_path) == [f"{number:04d}" for number in range(1, 16)]
    with psycopg.connect(database_dsn) as connection:
        legacy_rows(connection)
        columns = connection.execute(
            "SELECT table_name,column_name,data_type,column_default,is_nullable FROM information_schema.columns "
            "WHERE table_schema='mt' ORDER BY table_name,ordinal_position"
        ).fetchall()
        data = {
            name: connection.execute(sql.SQL("SELECT * FROM mt.{} ORDER BY 1").format(sql.Identifier(name))).fetchall()
            for name in ["policy_registry", "analysis_task", "task_run"]
        }
    upgrade = MIGRATIONS / "0016_task_creation_plan_bindings.sql"
    (tmp_path / upgrade.name).write_bytes(upgrade.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0016"]
    assert migrate(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as connection:
        old_columns = connection.execute(
            "SELECT table_name,column_name,data_type,column_default,is_nullable FROM information_schema.columns "
            "WHERE table_schema='mt' AND NOT table_name=ANY(%s::text[]) ORDER BY table_name,ordinal_position",
            (sorted(NEW_TABLES),),
        ).fetchall()
        assert old_columns == columns
        for name, rows in data.items():
            assert (
                connection.execute(sql.SQL("SELECT * FROM mt.{} ORDER BY 1").format(sql.Identifier(name))).fetchall()
                == rows
            )
        for name in NEW_TABLES:
            assert connection.execute(
                sql.SQL("SELECT count(*) FROM mt.{}").format(sql.Identifier(name))
            ).fetchone() == (0,)
        assert connection.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0015' ORDER BY version"
        ).fetchall() == [(file.name[:4], sha(file.read_bytes())) for file in previous]


def test_i01_failed_upgrade_rolls_back_new_objects_and_ledger(database_dsn, tmp_path):
    for file in sorted(MIGRATIONS.glob("*.sql")):
        if file.name[:4] <= "0015":
            (tmp_path / file.name).write_bytes(file.read_bytes())
    migrate(database_dsn, tmp_path)
    with psycopg.connect(database_dsn) as connection:
        before = connection.execute(
            "SELECT conname,conrelid::regclass::text,pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE connamespace='mt'::regnamespace ORDER BY conrelid,conname"
        ).fetchall()
    migration = MIGRATIONS / "0016_task_creation_plan_bindings.sql"
    (tmp_path / migration.name).write_bytes(
        migration.read_bytes() + b"\nSELECT injected_missing_i01_upgrade_function();\n"
    )
    with pytest.raises(psycopg.errors.UndefinedFunction):
        migrate(database_dsn, tmp_path)
    with psycopg.connect(database_dsn) as connection:
        assert connection.execute(
            "SELECT count(*) FROM pg_class WHERE relnamespace='mt'::regnamespace AND relname=ANY(%s::text[])",
            (sorted(NEW_TABLES),),
        ).fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM mt_meta.schema_migrations WHERE version='0016'").fetchone() == (
            0,
        )
        assert (
            connection.execute(
                "SELECT conname,conrelid::regclass::text,pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE connamespace='mt'::regnamespace ORDER BY conrelid,conname"
            ).fetchall()
            == before
        )


def test_i01_six_tables_have_exact_columns_force_rls_and_no_active_seeds(database_dsn):
    migrate(database_dsn)
    with psycopg.connect(database_dsn) as connection:
        assert (
            dict(
                connection.execute(
                    "SELECT table_name,count(*) FROM information_schema.columns WHERE table_schema='mt' "
                    "AND table_name=ANY(%s::text[]) GROUP BY table_name",
                    (sorted(NEW_TABLES),),
                ).fetchall()
            )
            == COLUMNS
        )
        assert connection.execute(
            "SELECT bool_and(relrowsecurity AND relforcerowsecurity) FROM pg_class "
            "WHERE relnamespace='mt'::regnamespace AND relname=ANY(%s::text[])",
            (sorted(NEW_TABLES),),
        ).fetchone() == (True,)
        scope_expression = "((org_id = mt.org_id()) AND mt.scope_allows_case(case_id))"
        assert connection.execute(
            "SELECT permissive,roles,cmd,qual,with_check FROM pg_policies WHERE schemaname='mt' "
            "AND tablename='task_run_plan' AND policyname='request_data_scope'"
        ).fetchone() == ("RESTRICTIVE", ["mt_runtime"], "ALL", scope_expression, scope_expression)
        assert connection.execute(
            "SELECT column_default FROM information_schema.columns WHERE table_schema='mt' "
            "AND table_name='task_plan_mapping_head' AND column_name='state'"
        ).fetchone() == (None,)
        assert connection.execute("SELECT count(*) FROM mt.task_plan_mapping_head").fetchone() == (0,)
        assert connection.execute("SELECT mt.scope_operation()").fetchone() == (None,)


def test_i01_role_acl_is_private_minimal_and_never_a_runtime_membership(database_dsn):
    migrate(database_dsn)
    with psycopg.connect(database_dsn) as connection:
        flags = connection.execute(
            "SELECT rolname,rolcanlogin,rolinherit,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication "
            "FROM pg_roles WHERE rolname=ANY(%s::text[]) ORDER BY rolname",
            (["mt_task_plan_lookup", "mt_task_plan_manager"],),
        ).fetchall()
        assert len(flags) == 2 and all(not any(row[1:]) for row in flags)
        for role in ["mt_task_plan_lookup", "mt_task_plan_manager"]:
            assert connection.execute(
                "SELECT pg_has_role('mt_runtime',%s,'MEMBER'),pg_has_role(%s,'mt_runtime','MEMBER')", (role, role)
            ).fetchone() == (False, False)
        for name in NEW_TABLES:
            for role in ["mt_runtime", "mt_task_plan_lookup", "mt_task_plan_manager"]:
                for privilege in ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"]:
                    expected = privilege in (
                        {"SELECT", "INSERT"}
                        if role == "mt_runtime" and name == "task_run_plan"
                        else {"SELECT"}
                        if role == "mt_task_plan_lookup" and name in PRIVATE_TABLES
                        else {"SELECT", "INSERT", "UPDATE"}
                        if role == "mt_task_plan_manager" and name == "task_plan_mapping_head"
                        else {"SELECT", "INSERT"}
                        if role == "mt_task_plan_manager" and name in PRIVATE_TABLES
                        else set()
                    )
                    assert connection.execute(
                        "SELECT has_table_privilege(%s,%s,%s)", (role, "mt." + name, privilege)
                    ).fetchone() == (expected,)


def test_i01_exact_run_bytes_accept_different_a_b_and_survive_head_revocation(database_dsn, i01_context):
    values = i01_context
    assert values["run"]["request_body_sha256"] != values["run"]["authorization_request_digest"]
    with psycopg.connect(database_dsn) as connection:
        insert(connection, "task_run_plan", values["run"])
        connection.execute("UPDATE mt.task_plan_mapping_head SET state='REVOKED',row_version=row_version+1")
        assert connection.execute(
            "SELECT request_body_sha256,authorization_request_digest,input_sha256 FROM mt.task_run_plan"
        ).fetchone() == (
            values["run"]["request_body_sha256"],
            values["run"]["authorization_request_digest"],
            values["run"]["input_sha256"],
        )
        assert connection.execute("SELECT state,row_version FROM mt.task_plan_mapping_head").fetchone() == (
            "REVOKED",
            2,
        )


@pytest.mark.parametrize(
    "field",
    [
        "request_body_bytes",
        "policy_bytes",
        "plan_bytes",
        "capability_bytes",
        "input_manifest_bytes",
        "validation_receipt_bytes",
    ],
)
def test_i01_run_cannot_substitute_bytes_without_exact_digest(database_dsn, i01_context, field):
    with psycopg.connect(database_dsn) as connection, pytest.raises(psycopg.errors.CheckViolation):
        insert(connection, "task_run_plan", dict(i01_context["run"], **{field: b"synthetic-different-byte-sequence"}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("mapping_id", "other-mapping"),
        ("mapping_version", "other-version"),
        ("authority_version", "other-authority"),
        ("policy_kind", "other-kind"),
        ("policy_version", "other-policy-version"),
        ("plan_id", "other-plan"),
        ("plan_version", "other-plan-version"),
        ("capability_id", "other-capability"),
        ("capability_version", "other-capability-version"),
        ("recovery_generation", "other-recovery"),
        ("run_version", 99),
    ],
)
def test_i01_run_full_material_and_run_identities_are_foreign_key_bound(database_dsn, i01_context, field, value):
    with psycopg.connect(database_dsn) as connection, pytest.raises(psycopg.errors.ForeignKeyViolation):
        insert(connection, "task_run_plan", dict(i01_context["run"], **{field: value}))


@pytest.mark.parametrize("field", ["case_id", "org_id", "created_by", "revision_id", "task_id", "policy_id"])
def test_i01_run_cannot_cross_case_org_creator_or_revision(database_dsn, i01_context, field):
    substitute = i01_context.get(
        {"case_id": "other_case", "org_id": "other_org", "created_by": "other_user"}.get(field, ""), uuid4()
    )
    with psycopg.connect(database_dsn) as connection, pytest.raises(psycopg.errors.ForeignKeyViolation):
        insert(connection, "task_run_plan", dict(i01_context["run"], **{field: substitute}))


@pytest.mark.parametrize(
    "field",
    [
        "request_body_sha256",
        "authorization_request_digest",
        "policy_sha256",
        "plan_sha256",
        "capability_sha256",
        "input_sha256",
        "validation_receipt_sha256",
    ],
)
def test_i01_run_digest_fields_reject_non_lowercase_sha256(database_dsn, i01_context, field):
    with psycopg.connect(database_dsn) as connection, pytest.raises(psycopg.errors.CheckViolation):
        insert(connection, "task_run_plan", dict(i01_context["run"], **{field: "A" * 64}))


@pytest.mark.parametrize("field", ["proof_observed_at", "proof_valid_until", "mapping_valid_until"])
def test_i01_proof_deadlines_are_inside_the_fixed_mapping_window(database_dsn, i01_context, field):
    run = i01_context["run"]
    value = (
        run["mapping_valid_from"] - timedelta(seconds=1)
        if field == "proof_observed_at"
        else run["mapping_valid_until"] + timedelta(seconds=1)
        if field == "proof_valid_until"
        else run["mapping_valid_from"]
    )
    with psycopg.connect(database_dsn) as connection, pytest.raises(psycopg.errors.CheckViolation):
        insert(connection, "task_run_plan", dict(run, **{field: value}))


@pytest.mark.parametrize("modules", [[], ["MEDIA", "MEDIA"], ["UNKNOWN"], [None], [["MEDIA"]]])
def test_i01_revision_modules_are_nonempty_distinct_known_and_one_dimensional(database_dsn, i01_context, modules):
    revision = dict(i01_context["revision"], revision_id=uuid4(), mapping_version="fixture-mapping/2", modules=modules)
    with psycopg.connect(database_dsn) as connection, pytest.raises(psycopg.errors.CheckViolation):
        insert(connection, "task_plan_mapping_revision", revision)


def test_i01_head_cannot_reorder_modules_or_reference_another_revision_tuple(database_dsn, i01_context):
    with psycopg.connect(database_dsn) as connection:
        for field, value in [("modules", ["RESOURCE", "MEDIA"]), ("scene", "harmful_content"), ("priority", "high")]:
            with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
                insert(connection, "task_plan_mapping_head", dict(i01_context["head"], **{field: value}))
        with pytest.raises(psycopg.errors.NotNullViolation), connection.transaction():
            row = dict(i01_context["head"])
            del row["state"]
            insert(connection, "task_plan_mapping_head", row)
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState), connection.transaction():
            connection.execute("UPDATE mt.task_plan_mapping_head SET state='REVOKED'")
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState), connection.transaction():
            connection.execute("UPDATE mt.task_plan_mapping_head SET priority='high',row_version=row_version+1")


@pytest.mark.parametrize("table", sorted(NEW_TABLES - {"task_plan_mapping_head"}))
@pytest.mark.parametrize("action", ["UPDATE", "DELETE", "TRUNCATE"])
def test_i01_materials_revisions_and_run_plans_are_append_only_even_for_admin(database_dsn, i01_context, table, action):
    with psycopg.connect(database_dsn) as connection:
        insert(connection, "task_run_plan", i01_context["run"])
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState), connection.transaction():
            statement = {
                "UPDATE": "UPDATE mt.{} SET created_at=created_at",
                "DELETE": "DELETE FROM mt.{}",
                "TRUNCATE": "TRUNCATE mt.{} CASCADE",
            }[action]
            connection.execute(sql.SQL(statement).format(sql.Identifier(table)))


@pytest.mark.parametrize(
    "mode,operation",
    [("CASE", "getTask"), ("CASE", "createTask"), ("LOOKUP", "getAsset"), ("ORGANIZATION", "getCurrentUser")],
)
def test_i01_runtime_cannot_read_private_tables_or_use_unregistered_create_scope(
    database_dsn, i01_context, mode, operation
):
    with psycopg.connect(database_dsn) as connection:
        insert(connection, "task_run_plan", i01_context["run"])
        for name, value in [
            ("app.actor_id", str(i01_context["user"])),
            ("app.org_id", str(i01_context["org"])),
            ("app.case_id", str(i01_context["case"])),
            ("app.scope_mode", mode),
            ("app.operation_id", operation),
        ]:
            connection.execute("SELECT set_config(%s,%s,true)", (name, value))
        connection.execute("SET LOCAL ROLE mt_runtime")
        for name in PRIVATE_TABLES:
            with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
                connection.execute(sql.SQL("SELECT * FROM mt.{}").format(sql.Identifier(name)))
        assert connection.execute("SELECT count(*) FROM mt.task_run_plan").fetchone() == (0,)
        with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
            insert(connection, "task_run_plan", i01_context["run"])


def test_i01_private_scope_catalog_and_inherited_role_guards_are_explicit(database_dsn):
    from business_app.db import Database
    from business_app.scope_catalog import TABLE_SCOPES

    migrate(database_dsn)
    assert all(
        TABLE_SCOPES[name].scope_class == "ORG" and TABLE_SCOPES[name].runtime_select is False
        for name in PRIVATE_TABLES
    )
    assert TABLE_SCOPES["task_run_plan"].scope_class == "CASE"
    database = Database(database_dsn)
    role = "mt_i01_guard_" + uuid4().hex
    try:
        with database.engine.begin() as connection:
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOSUPERUSER NOBYPASSRLS")
            connection.exec_driver_sql(f"GRANT mt_runtime TO {role}")
            try:
                for protected in ["mt_task_plan_lookup", "mt_task_plan_manager"]:
                    connection.exec_driver_sql(f"SET LOCAL ROLE {role}")
                    Database._unprivileged(connection)
                    connection.exec_driver_sql("RESET ROLE")
                    connection.exec_driver_sql(f"GRANT {protected} TO {role}")
                    connection.exec_driver_sql(f"SET LOCAL ROLE {role}")
                    with pytest.raises(RuntimeError, match="PRIVILEGED_BUSINESS_CONNECTION_FORBIDDEN"):
                        Database._unprivileged(connection)
                    connection.exec_driver_sql("RESET ROLE")
                    connection.exec_driver_sql(f"REVOKE {protected} FROM {role}")
            finally:
                connection.exec_driver_sql("RESET ROLE")
                connection.exec_driver_sql(f"DROP ROLE {role}")
    finally:
        database.close()


@pytest.mark.parametrize("role", ["mt_task_plan_lookup", "mt_task_plan_manager"])
@pytest.mark.parametrize("scope", ["empty", "same-org-case", "other-org", "other-case", "lookup"])
def test_i01_private_roles_do_not_enable_material_access_without_i02_scope(database_dsn, i01_context, role, scope):
    values = i01_context
    with psycopg.connect(database_dsn) as connection:
        for name, value in [
            ("app.actor_id", str(values["user"])),
            ("app.org_id", str(values["other_org"] if scope == "other-org" else values["org"])),
            ("app.case_id", str(values["other_case"] if scope == "other-case" else values["case"])),
            ("app.scope_mode", "" if scope == "empty" else "LOOKUP" if scope == "lookup" else "CASE"),
            ("app.operation_id", "" if scope == "empty" else "createTask"),
        ]:
            connection.execute("SELECT set_config(%s,%s,true)", (name, value))
        connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
        for table in sorted(PRIVATE_TABLES):
            assert connection.execute(
                sql.SQL("SELECT count(*) FROM mt.{}").format(sql.Identifier(table))
            ).fetchone() == (0,)
        plan_bytes = canonical({"synthetic_sql_plan": "new-insert-must-not-be-permitted"})
        with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
            insert(
                connection,
                "task_plan_artifact",
                dict(
                    values["common"],
                    plan_id="denied-new-plan",
                    plan_version="denied/1",
                    canonical_bytes=plan_bytes,
                    plan_sha256=sha(plan_bytes),
                    schema_version="urn:media-trace:task-execution-plan:1.0.0",
                ),
            )
        if role == "mt_task_plan_manager":
            assert (
                connection.execute(
                    "UPDATE mt.task_plan_mapping_head SET state='REVOKED',row_version=row_version+1"
                ).rowcount
                == 0
            )
        connection.execute("RESET ROLE")
        assert connection.execute("SELECT state,row_version FROM mt.task_plan_mapping_head").fetchone() == (
            "INACTIVE",
            1,
        )
