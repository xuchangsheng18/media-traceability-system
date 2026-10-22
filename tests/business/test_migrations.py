import hashlib
import importlib.util
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "backend/business_migrations"


def migrate(dsn, directory=MIGRATIONS):
    source = MIGRATIONS / "runner.py"
    assert source.is_file(), "independent versioned business migrations are not implemented"
    spec = importlib.util.spec_from_file_location("business_migration_runner", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply_migrations(dsn, directory)


def scalar(connection, query):
    row = connection.execute(query).fetchone()
    assert row is not None
    return row[0]


@pytest.mark.parametrize("history", ["valid", "orphan_run", "unknown_from", "unknown_to", "injected_failure"])
def test_0015_event_upgrade_validates_history_and_rolls_back_atomically(database_dsn, tmp_path, history):
    from uuid import uuid4

    from tests.business.test_report_migration import schema_snapshot

    previous = [file for file in sorted(MIGRATIONS.glob("*.sql")) if file.name[:4] <= "0014"]
    for file in previous:
        (tmp_path / file.name).write_bytes(file.read_bytes())
    assert migrate(database_dsn, tmp_path) == [f"{version:04d}" for version in range(1, 15)]
    org, case, source, content, obj, asset, task, run, event = [uuid4() for _ in range(9)]
    with psycopg.connect(database_dsn) as connection:
        connection.execute("INSERT INTO mt.organizations(org_id,name) VALUES(%s,'synthetic-upgrade-unit')", (org,))
        connection.execute(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,'fixture','ACTIVE')", (case, org)
        )
        connection.execute(
            "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) "
            "VALUES(%s,%s,%s,'fixture','synthetic','not-formal-authority',ARRAY['analysis'],'pending','fixture-v1')",
            (source, org, case),
        )
        connection.execute(
            "INSERT INTO mt.content_item(content_id,org_id,case_id,source_id,discovered_at,status) VALUES(%s,%s,%s,%s,now(),'fixture')",
            (content, org, case, source),
        )
        connection.execute(
            "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,size_bytes) "
            "VALUES(%s,%s,%s,'fixture','fixture','1',%s,1)",
            (obj, org, case, "a" * 64),
        )
        connection.execute(
            "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,kind,mapping_version,state) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,'application/octet-stream',1,'original','fixture','VALIDATING')",
            (asset, org, case, content, source, obj, "a" * 64),
        )
        connection.execute(
            "INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility) "
            "VALUES(%s,%s,%s,%s,'accident_rumor','normal','CREATED','fixture',ARRAY['MEDIA'],'draft_only')",
            (task, org, case, asset),
        )
        connection.execute(
            "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,policy_version) "
            "VALUES(%s,%s,%s,%s,1,%s,'fixture','fixture')",
            (run, org, case, task, "a" * 64),
        )
        connection.execute(
            "INSERT INTO mt.task_event(event_id,org_id,case_id,task_id,run_version,from_state,to_state,reason,request_id) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,'synthetic legacy record',%s)",
            (
                event,
                org,
                case,
                task,
                99 if history == "orphan_run" else 1,
                "UNKNOWN" if history == "unknown_from" else None,
                "UNKNOWN" if history == "unknown_to" else "CREATED",
                uuid4(),
            ),
        )
        before = schema_snapshot(connection)
        records = {
            name: connection.execute(f"SELECT * FROM mt.{name} ORDER BY 1").fetchall()
            for name in ("analysis_task", "task_run", "task_event")
        }
        ledger = connection.execute("SELECT * FROM mt_meta.schema_migrations ORDER BY version").fetchall()
    upgrades = list(MIGRATIONS.glob("0015_*.sql"))
    assert len(upgrades) == 1, "fixed-run event migration is missing"
    upgrade = upgrades[0]
    (tmp_path / upgrade.name).write_bytes(
        upgrade.read_bytes()
        + (b"\nSELECT missing_event_upgrade_function();\n" if history == "injected_failure" else b"")
    )
    if history == "valid":
        assert migrate(database_dsn, tmp_path) == ["0015"]
        assert migrate(database_dsn, tmp_path) == []
    else:
        expected = (
            psycopg.errors.ForeignKeyViolation
            if history == "orphan_run"
            else psycopg.errors.UndefinedFunction
            if history == "injected_failure"
            else psycopg.errors.CheckViolation
        )
        with pytest.raises(expected):
            migrate(database_dsn, tmp_path)
    with psycopg.connect(database_dsn) as connection:
        after = schema_snapshot(connection)
        for key in before:
            if key != "constraints" or history != "valid":
                assert after[key] == before[key]
        for name, rows in records.items():
            assert connection.execute(f"SELECT * FROM mt.{name} ORDER BY 1").fetchall() == rows
        assert (
            connection.execute(
                "SELECT * FROM mt_meta.schema_migrations WHERE version<='0014' ORDER BY version"
            ).fetchall()
            == ledger
        )
        assert scalar(connection, "SELECT count(*) FROM mt_meta.schema_migrations WHERE version='0015'") == (
            1 if history == "valid" else 0
        )
        if history == "valid":
            additions = {row[0] for row in after["constraints"]} - {row[0] for row in before["constraints"]}
            assert additions == {
                "task_event_run_identity_fk",
                "task_event_from_state_check",
                "task_event_to_state_check",
            }
            assert (
                scalar(
                    connection,
                    "SELECT bool_and(convalidated) FROM pg_constraint WHERE conname IN ('task_event_run_identity_fk','task_event_from_state_check','task_event_to_state_check')",
                )
                is True
            )


def test_empty_database_migrates_and_replay_noops(database_dsn):
    assert migrate(database_dsn) == [
        "0001",
        "0002",
        "0003",
        "0004",
        "0005",
        "0006",
        "0007",
        "0008",
        "0009",
        "0010",
        "0011",
        "0012",
        "0013",
        "0014",
        "0015",
        "0016",
        "0017",
        "0018",
    ]
    assert migrate(database_dsn) == []
    with psycopg.connect(database_dsn) as connection:
        assert (
            scalar(
                connection,
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='mt' AND table_type='BASE TABLE'",
            )
            == 70
        )
        assert scalar(connection, "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt'") == 967
        assert (
            scalar(
                connection,
                """SELECT count(*) FROM information_schema.columns WHERE table_schema='mt'
            AND table_name NOT IN ('task_policy_artifact','task_plan_artifact','task_capability_manifest',
            'task_plan_mapping_revision','task_plan_mapping_head','task_run_plan')""",
            )
            == 861
        )
        assert scalar(connection, "SELECT rolbypassrls OR rolsuper FROM pg_roles WHERE rolname='mt_runtime'") is False


def test_changed_migration_digest_rejected(database_dsn, tmp_path):
    migrate(database_dsn)
    for original in MIGRATIONS.glob("*.sql"):
        (tmp_path / original.name).write_bytes(original.read_bytes() + b"\n-- modified\n")
    with pytest.raises(RuntimeError, match="DIGEST"):
        migrate(database_dsn, tmp_path)


def test_0012_catalog_reads_upgrade_preserves_existing_registries_and_tables(database_dsn, tmp_path):
    previous = [file for file in sorted(MIGRATIONS.glob("*.sql")) if file.name[:4] <= "0011"]
    for file in previous:
        (tmp_path / file.name).write_bytes(file.read_bytes())
    assert migrate(database_dsn, tmp_path) == [f"{version:04d}" for version in range(1, 12)]
    with psycopg.connect(database_dsn) as connection:
        before = connection.execute(
            "SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='mt' ORDER BY table_name,ordinal_position"
        ).fetchall()
    (tmp_path / "0012_catalog_reads.sql").write_bytes((MIGRATIONS / "0012_catalog_reads.sql").read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0012"]
    assert migrate(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as connection:
        assert (
            connection.execute(
                "SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='mt' ORDER BY table_name,ordinal_position"
            ).fetchall()
            == before
        )
        assert connection.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0011' ORDER BY version"
        ).fetchall() == [(file.name[:4], hashlib.sha256(file.read_bytes()).hexdigest()) for file in previous]
        for operation in ["getAsset", "listAssets", "listTasks", "issueOperationToken", "sealEvidence"]:
            connection.execute("SELECT set_config('app.operation_id',%s,true)", (operation,))
            assert connection.execute("SELECT mt.scope_operation()").fetchone() == (operation,)
        for kind, operation in [
            ("asset", "getAsset"),
            ("asset", "listAssets"),
            ("task", "listTasks"),
            ("approval", "issueOperationToken"),
            ("task", "sealEvidence"),
        ]:
            assert connection.execute("SELECT mt.scope_lookup_kind_allowed(%s,%s)", (kind, operation)).fetchone() == (
                True,
            )


def test_untracked_existing_mt_schema_rejected(database_dsn):
    with psycopg.connect(database_dsn) as connection:
        connection.execute("CREATE SCHEMA mt")
    with pytest.raises(RuntimeError, match="UNTRACKED"):
        migrate(database_dsn)


def test_mid_migration_failure_is_atomic(database_dsn, tmp_path):
    (tmp_path / "0001_marker.sql").write_text("CREATE SCHEMA mt; CREATE TABLE mt.marker(id integer);")
    (tmp_path / "0002_failure.sql").write_text("CREATE TABLE mt.partial(id integer); SELECT no_such_function();")
    with pytest.raises(psycopg.Error):
        migrate(database_dsn, tmp_path)
    with psycopg.connect(database_dsn) as connection:
        assert scalar(connection, "SELECT to_regnamespace('mt')") is None
        assert scalar(connection, "SELECT to_regclass('mt_meta.schema_migrations')") is None


@pytest.mark.parametrize("cross_unit", [False, True])
def test_identity_upgrade_preserves_legacy_rows_or_rejects_cross_unit_members(database_dsn, tmp_path, cross_unit):
    from uuid import uuid4

    for original in sorted(MIGRATIONS.glob("*.sql"))[:3]:
        (tmp_path / original.name).write_bytes(original.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0001", "0002", "0003"]
    org, other_org, user, case, membership = [uuid4() for _ in range(5)]
    with psycopg.connect(database_dsn) as connection:
        connection.execute(
            "INSERT INTO mt.organizations(org_id,name) VALUES(%s,'legacy-unit'),(%s,'other-unit')", (org, other_org)
        )
        connection.execute(
            "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,'legacy-internal-label',true)",
            (user, org),
        )
        connection.execute(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,'legacy-case','ACTIVE')",
            (case, other_org if cross_unit else org),
        )
        connection.execute(
            "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
            (membership, case, other_org if cross_unit else org, user),
        )
    if cross_unit:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt_meta.schema_migrations") == 3
            assert scalar(connection, "SELECT to_regclass('mt.user_identities')") is None
            assert scalar(connection, "SELECT count(*) FROM mt.case_membership") == 1
    else:
        assert migrate(database_dsn) == [
            "0004",
            "0005",
            "0006",
            "0007",
            "0008",
            "0009",
            "0010",
            "0011",
            "0012",
            "0013",
            "0014",
            "0015",
            "0016",
            "0017",
            "0018",
        ]
        assert migrate(database_dsn) == []
        with psycopg.connect(database_dsn) as connection:
            assert connection.execute(
                "SELECT org_id,subject,enabled FROM mt.users WHERE user_id=%s", (user,)
            ).fetchone() == (org, "legacy-internal-label", True)
            assert scalar(connection, "SELECT count(*) FROM mt.user_identities") == 0
            assert scalar(connection, "SELECT count(*) FROM mt.case_membership") == 1


def test_identity_lookup_works_when_migration_owner_cannot_bypass_rls(database_dsn, tmp_path):
    from uuid import uuid4

    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    role = "mt_schema_owner_" + uuid4().hex
    settings = conninfo_to_dict(database_dsn)
    with psycopg.connect(database_dsn) as admin:
        admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS CREATEROLE").format(sql.Identifier(role)))
        admin.execute(
            sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
                sql.Identifier(str(settings["dbname"])), sql.Identifier(role)
            )
        )

    def revoke_installation_memberships():
        with psycopg.connect(database_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("REVOKE mt_task_plan_lookup,mt_task_plan_case_reader FROM {}").format(sql.Identifier(role))
            )
            assert admin.execute(
                "SELECT count(*) FROM pg_auth_members WHERE member=%s::regrole AND roleid IN "
                "('mt_task_plan_lookup'::regrole,'mt_task_plan_case_reader'::regrole)",
                (role,),
            ).fetchone() == (0,)

    try:
        owner_dsn = make_conninfo(database_dsn, options="-crole=" + role)
        history = tmp_path / "identity_owner_through0016"
        history.mkdir()
        previous = [path for path in sorted(MIGRATIONS.glob("*.sql")) if path.name[:4] <= "0016"]
        assert [path.name[:4] for path in previous] == [f"{version:04d}" for version in range(1, 17)]
        for path in previous:
            (history / path.name).write_bytes(path.read_bytes())
        applied = migrate(owner_dsn, history)
        assert applied == [f"{version:04d}" for version in range(1, 17)]
        # The test administrator supplies the documented installation prerequisite.
        # Migration execution remains the same non-super, non-BYPASSRLS owner.
        with psycopg.connect(database_dsn, autocommit=True) as admin:
            assert admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s", (role,)).fetchone() == (
                False,
                False,
            )
            admin.execute(
                sql.SQL(
                    "GRANT mt_task_plan_lookup,mt_task_plan_case_reader TO {} WITH INHERIT FALSE, SET TRUE, ADMIN FALSE"
                ).format(sql.Identifier(role))
            )
            assert admin.execute(
                "SELECT r.rolname,m.inherit_option,m.set_option,m.admin_option "
                "FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid "
                "WHERE m.member=%s::regrole AND r.rolname IN "
                "('mt_task_plan_lookup','mt_task_plan_case_reader') ORDER BY r.rolname",
                (role,),
            ).fetchall() == [
                ("mt_task_plan_case_reader", False, True, False),
                ("mt_task_plan_lookup", False, True, False),
            ]
        try:
            remaining = migrate(owner_dsn)
            assert remaining == ["0017", "0018"]
            applied += remaining
        finally:
            revoke_installation_memberships()
        assert applied == [
            "0001",
            "0002",
            "0003",
            "0004",
            "0005",
            "0006",
            "0007",
            "0008",
            "0009",
            "0010",
            "0011",
            "0012",
            "0013",
            "0014",
            "0015",
            "0016",
            "0017",
            "0018",
        ]
        assert migrate(owner_dsn) == []
        org, user = uuid4(), uuid4()
        with psycopg.connect(database_dsn) as admin:
            admin.execute("INSERT INTO mt.organizations(org_id,name) VALUES(%s,'owner-test')", (org,))
            admin.execute(
                "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)", (user, org, str(user))
            )
            admin.execute(
                "INSERT INTO mt.user_identities(identity_id,user_id,org_id,issuer,subject,enabled,mapping_version) VALUES(%s,%s,%s,'owner-provider','owner-subject',true,'v1')",
                (uuid4(), user, org),
            )
            row = admin.execute("SELECT user_id FROM mt.resolve_identity('owner-provider','owner-subject')").fetchone()
            assert row == (user,)
    finally:
        revoke_installation_memberships()
        with psycopg.connect(database_dsn) as admin:
            admin.execute(sql.SQL("REASSIGN OWNED BY {} TO CURRENT_USER").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@pytest.mark.parametrize(
    "collision", ["runtime_manager", "runtime_lookup", "lookup_manager", "indirect_runtime_manager"]
)
def test_unsafe_identity_role_inheritance_aborts_migration(database_dsn, collision):
    from uuid import uuid4

    from psycopg import sql

    middle = "mt_collision_" + uuid4().hex
    grants = {
        "runtime_manager": [("mt_directory_manager", "mt_runtime")],
        "runtime_lookup": [("mt_identity_lookup", "mt_runtime")],
        "lookup_manager": [("mt_directory_manager", "mt_identity_lookup")],
        "indirect_runtime_manager": [("mt_directory_manager", middle), (middle, "mt_runtime")],
    }[collision]
    # These group roles already exist in the dedicated isolated test instance.
    with psycopg.connect(database_dsn) as admin:
        assert not scalar(
            admin,
            "SELECT pg_has_role('mt_runtime','mt_directory_manager','MEMBER') OR pg_has_role('mt_runtime','mt_identity_lookup','MEMBER') OR pg_has_role('mt_identity_lookup','mt_directory_manager','MEMBER')",
        )
        if collision.startswith("indirect"):
            admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(middle)))
        for granted, member in grants:
            admin.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(granted), sql.Identifier(member)))
    try:
        with pytest.raises(psycopg.Error, match="UNSAFE_IDENTITY_ROLE_INHERITANCE"):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as admin:
            assert scalar(admin, "SELECT to_regnamespace('mt')") is None
    finally:
        with psycopg.connect(database_dsn) as admin:
            for granted, member in reversed(grants):
                admin.execute(sql.SQL("REVOKE {} FROM {}").format(sql.Identifier(granted), sql.Identifier(member)))
            if collision.startswith("indirect"):
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(middle)))


@pytest.mark.parametrize("invalid_legacy", [False, True])
def test_role_catalog_upgrade_preserves_legacy_or_rolls_back_atomically(database_dsn, tmp_path, invalid_legacy):
    from uuid import uuid4

    for original in sorted(MIGRATIONS.glob("*.sql"))[:4]:
        (tmp_path / original.name).write_bytes(original.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0001", "0002", "0003", "0004"]
    role, permission, relation = [uuid4() for _ in range(3)]
    with psycopg.connect(database_dsn) as connection:
        connection.execute(
            "INSERT INTO mt.roles(role_id,code,description) VALUES(%s,%s,'legacy')",
            (role, " bad legacy" if invalid_legacy else "legacy.role"),
        )
        connection.execute(
            "INSERT INTO mt.permissions(permission_id,code,description) VALUES(%s,'legacy.permission','legacy')",
            (permission,),
        )
        connection.execute(
            "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s)",
            (relation, role, permission),
        )
    if invalid_legacy:
        with pytest.raises(psycopg.errors.CheckViolation):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt_meta.schema_migrations") == 4
            assert (
                scalar(
                    connection,
                    "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt' AND table_name='roles' AND column_name='enabled'",
                )
                == 0
            )
            assert connection.execute("SELECT code FROM mt.roles WHERE role_id=%s", (role,)).fetchone() == (
                " bad legacy",
            )
    else:
        assert migrate(database_dsn) == [
            "0005",
            "0006",
            "0007",
            "0008",
            "0009",
            "0010",
            "0011",
            "0012",
            "0013",
            "0014",
            "0015",
            "0016",
            "0017",
            "0018",
        ]
        assert migrate(database_dsn) == []
        with psycopg.connect(database_dsn) as connection:
            assert connection.execute(
                "SELECT enabled,code,row_version FROM mt.roles WHERE role_id=%s", (role,)
            ).fetchone() == (True, "legacy.role", 1)
            assert connection.execute(
                "SELECT enabled,code,row_version FROM mt.permissions WHERE permission_id=%s", (permission,)
            ).fetchone() == (True, "legacy.permission", 1)
            assert connection.execute(
                "SELECT role_id,permission_id,revoked_at,row_version FROM mt.role_permissions WHERE role_permission_id=%s",
                (relation,),
            ).fetchone() == (role, permission, None, 1)
            new_role = uuid4()
            connection.execute(
                "INSERT INTO mt.roles(role_id,code,description) VALUES(%s,'new.role','new')", (new_role,)
            )
            assert connection.execute("SELECT enabled FROM mt.roles WHERE role_id=%s", (new_role,)).fetchone() == (
                False,
            )


def test_new_catalog_migration_rechecks_unsafe_existing_role_inheritance(database_dsn, tmp_path):
    for original in sorted(MIGRATIONS.glob("*.sql"))[:4]:
        (tmp_path / original.name).write_bytes(original.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0001", "0002", "0003", "0004"]
    with psycopg.connect(database_dsn) as admin:
        admin.execute("GRANT mt_directory_manager TO mt_runtime")
    try:
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState, match="UNSAFE_ROLE_CATALOG_MANAGEMENT"):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt_meta.schema_migrations") == 4
            assert (
                scalar(
                    connection,
                    "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt' AND table_name='permissions' AND column_name='enabled'",
                )
                == 0
            )
    finally:
        with psycopg.connect(database_dsn) as admin:
            admin.execute("REVOKE mt_directory_manager FROM mt_runtime")


@pytest.mark.parametrize("fail_after_function", [False, True])
def test_permission_upgrade_preserves_catalog_and_failure_rolls_back(database_dsn, tmp_path, fail_after_function):
    import hashlib
    from uuid import uuid4

    previous = sorted(MIGRATIONS.glob("*.sql"))[:5]
    for original in previous:
        (tmp_path / original.name).write_bytes(original.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0001", "0002", "0003", "0004", "0005"]
    role = uuid4()
    with psycopg.connect(database_dsn) as admin:
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'upgrade-preserved','fixture',false)",
            (role,),
        )
        before = admin.execute("SELECT * FROM mt.roles WHERE role_id=%s", (role,)).fetchone()
    new = MIGRATIONS / "0006_permission_lookup.sql"
    assert new.is_file(), "T014 additive permission migration is missing"
    target = tmp_path / new.name
    target.write_bytes(
        new.read_bytes() + (b"\nSELECT no_such_permission_function();\n" if fail_after_function else b"")
    )
    if fail_after_function:
        with pytest.raises(psycopg.Error):
            migrate(database_dsn, tmp_path)
    else:
        assert migrate(database_dsn, tmp_path) == ["0006"]
        assert migrate(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as admin:
        assert admin.execute("SELECT * FROM mt.roles WHERE role_id=%s", (role,)).fetchone() == before
        expected = [(p.name[:4], hashlib.sha256(p.read_bytes()).hexdigest()) for p in previous]
        assert (
            admin.execute(
                "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0005' ORDER BY version"
            ).fetchall()
            == expected
        )
        assert admin.execute(
            "SELECT to_regprocedure('mt.lookup_permission(text,text,uuid,uuid,text)') IS NOT NULL"
        ).fetchone() == (not fail_after_function,)


@pytest.mark.parametrize("fail_after_function", [False, True])
def test_role_facts_upgrade_is_atomic_and_preserves_previous_rows(database_dsn, tmp_path, fail_after_function):
    import hashlib
    from uuid import uuid4

    from business_migrations.runner import apply_migrations

    migrations = Path(__file__).resolve().parents[2] / "backend/business_migrations"
    for old in sorted(migrations.glob("*.sql"))[:6]:
        (tmp_path / old.name).write_bytes(old.read_bytes())
    assert apply_migrations(database_dsn, tmp_path) == [f"{i:04}" for i in range(1, 7)]
    role_id = uuid4()
    with psycopg.connect(database_dsn) as admin:
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'preserved.role','synthetic',false)",
            (role_id,),
        )
        before = admin.execute("SELECT * FROM mt.roles WHERE role_id=%s", (role_id,)).fetchone()
    new = migrations / "0007_role_facts.sql"
    assert new.is_file(), "additive role-facts migration is missing"
    (tmp_path / new.name).write_bytes(
        new.read_bytes() + (b"\nSELECT missing_role_fact_marker();" if fail_after_function else b"")
    )
    if fail_after_function:
        with pytest.raises(psycopg.Error):
            apply_migrations(database_dsn, tmp_path)
    else:
        assert apply_migrations(database_dsn, tmp_path) == ["0007"]
        assert apply_migrations(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as admin:
        assert admin.execute("SELECT * FROM mt.roles WHERE role_id=%s", (role_id,)).fetchone() == before
        assert admin.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0006' ORDER BY version"
        ).fetchall() == [
            (p.name[:4], hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(migrations.glob("*.sql"))[:6]
        ]
        assert admin.execute(
            "SELECT to_regprocedure('mt.lookup_role_facts(text,text,uuid,uuid,text)') IS NOT NULL"
        ).fetchone() == (not fail_after_function,)


@pytest.mark.parametrize("fail_after_triggers", [False, True])
def test_authorization_fence_upgrade_preserves_catalog_and_rolls_back_atomically(
    database_dsn, tmp_path, fail_after_triggers
):
    import hashlib
    from uuid import uuid4

    previous = sorted(MIGRATIONS.glob("*.sql"))[:7]
    for p in previous:
        (tmp_path / p.name).write_bytes(p.read_bytes())
    assert migrate(database_dsn, tmp_path) == [f"{n:04}" for n in range(1, 8)]
    role = uuid4()
    with psycopg.connect(database_dsn) as admin:
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'preserved.before.fence','synthetic only',false)",
            (role,),
        )
        before = admin.execute("SELECT * FROM mt.roles WHERE role_id=%s", (role,)).fetchone()
    new = MIGRATIONS / "0008_authorization_fence.sql"
    (tmp_path / new.name).write_bytes(
        new.read_bytes() + (b"\nSELECT missing_fence_migration_marker();" if fail_after_triggers else b"")
    )
    if fail_after_triggers:
        with pytest.raises(psycopg.Error):
            migrate(database_dsn, tmp_path)
    else:
        assert migrate(database_dsn, tmp_path) == ["0008"]
        assert migrate(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as admin:
        assert admin.execute("SELECT * FROM mt.roles WHERE role_id=%s", (role,)).fetchone() == before
        assert admin.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0007' ORDER BY version"
        ).fetchall() == [(p.name[:4], hashlib.sha256(p.read_bytes()).hexdigest()) for p in previous]
        assert admin.execute("SELECT to_regclass('mt.authorization_epoch') IS NOT NULL").fetchone() == (
            not fail_after_triggers,
        )
        if not fail_after_triggers:
            assert admin.execute(
                "SELECT policy_version,policy_sha256,recovery_generation FROM mt.authorization_epoch"
            ).fetchone() == (None, None, None)


@pytest.mark.parametrize("fail_after_function", [False, True])
def test_work_role_facts_upgrade_is_atomic_and_function_only(database_dsn, tmp_path, fail_after_function):
    import hashlib

    previous = sorted(MIGRATIONS.glob("*.sql"))[:8]
    for p in previous:
        (tmp_path / p.name).write_bytes(p.read_bytes())
    assert migrate(database_dsn, tmp_path) == [f"{n:04}" for n in range(1, 9)]
    new = MIGRATIONS / "0009_work_role_facts.sql"
    (tmp_path / new.name).write_bytes(
        new.read_bytes() + (b"\nSELECT missing_work_migration_marker();" if fail_after_function else b"")
    )
    if fail_after_function:
        with pytest.raises(psycopg.Error):
            migrate(database_dsn, tmp_path)
    else:
        assert migrate(database_dsn, tmp_path) == ["0009"]
        assert migrate(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as admin:
        assert admin.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0008' ORDER BY version"
        ).fetchall() == [(p.name[:4], hashlib.sha256(p.read_bytes()).hexdigest()) for p in previous]
        assert admin.execute(
            "SELECT to_regprocedure('mt.lookup_actor_work_role_facts(uuid,text,text)') IS NOT NULL"
        ).fetchone() == (not fail_after_function,)
        if not fail_after_function:
            assert admin.execute(
                "SELECT has_function_privilege('mt_runtime','mt.lookup_actor_work_role_facts(uuid,text,text)','EXECUTE'),has_function_privilege('mt_permission_lookup','mt.lookup_actor_work_role_facts(uuid,text,text)','EXECUTE')"
            ).fetchone() == (True, False)
            assert admin.execute(
                "SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.oid='mt.lookup_actor_work_role_facts(uuid,text,text)'::regprocedure AND a.grantee=0"
            ).fetchone() == (0,)
            assert scalar(admin, "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt'") == 849
