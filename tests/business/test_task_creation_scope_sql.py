"""Real isolated SQL for fixed plan reads; fixtures never confer business authority."""

import copy
import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from tests.business.conftest import PrivateTestDSN
from tests.business.test_migrations import migrate
from tests.business.test_task_creation_materials import material_documents, rebind
from tests.business.test_task_creation_migration import canonical, insert, legacy_rows

CASE_READER = "mt_task_plan_case_reader"
LOCKED_TABLES = (
    "media_asset",
    "source_registry",
    "policy_registry",
    "task_plan_mapping_head",
)
METADATA = "SELECT * FROM mt.task_create_plan_metadata(%s,%s,%s,%s,%s::text[],%s)"
EXECUTION = "SELECT * FROM mt.task_create_execution_plan(%s,%s,%s,%s,%s::text[],%s,%s,%s,%s,%s)"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def rows(connection, query, arguments):
    cursor = connection.execute(query, arguments)
    names = [field.name for field in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def bind(
    connection,
    context,
    *,
    mode="CASE",
    operation="createTask",
    case=None,
    lookup=None,
    actor=None,
    org=None,
):
    for name, value in {
        "app.actor_id": str(actor or context["user"]),
        "app.org_id": str(org or context["org"]),
        "app.case_id": "" if mode == "LOOKUP" else str(case or context["case"]),
        "app.scope_mode": mode,
        "app.operation_id": operation,
        "app.lookup_kind": "asset" if mode == "LOOKUP" else "",
        "app.lookup_id": str(lookup or context["asset"]) if mode == "LOOKUP" else "",
    }.items():
        connection.execute("SELECT set_config(%s,%s,true)", (name, value))


def arguments(context):
    revision = context["revision"]
    return (
        context["asset"],
        context["case"],
        revision["scene"],
        revision["policy_version"],
        revision["modules"],
        revision["priority"],
    )


def execution_arguments(context):
    revision = context["revision"]
    return arguments(context) + tuple(
        revision[key] for key in ("revision_id", "policy_sha256", "plan_sha256", "capability_sha256")
    )


@pytest.fixture
def sql_context(database_dsn):
    migrate(database_dsn)
    documents = material_documents()
    documents["policy"]["version"] = "fixture-policy/1"
    documents["plan"]["policy_version"] = "fixture-policy/1"
    rebind(documents)
    raw = {name: canonical(documents[name]) for name in ("policy", "plan", "capability")}
    receipt = canonical({"validated": True, "private_extra": "must-not-be-returned", "validator_id": 7})
    role, password = "mt_plan_runtime_" + uuid4().hex, uuid4().hex + uuid4().hex
    with psycopg.connect(database_dsn) as connection:
        context = legacy_rows(connection)
        source_object = connection.execute(
            "SELECT source_id,object_id FROM mt.media_asset WHERE asset_id=%s",
            (context["asset"],),
        ).fetchone()
        assert source_object is not None
        source, obj = source_object
        context.update(source=source, object=obj)
        connection.execute(
            "UPDATE mt.media_asset SET state='VALID' WHERE asset_id=%s",
            (context["asset"],),
        )
        connection.execute(
            "UPDATE mt.source_registry SET authorization_status='verified' WHERE source_id=%s",
            (source,),
        )
        common = dict(
            org_id=context["org"],
            canonicalization_version="task-material-json-utf8-sortkeys-v1",
            provenance_ref="self-owned-SQL-fixture-not-formal-adoption",
            created_by=context["user"],
        )
        insert(
            connection,
            "task_policy_artifact",
            dict(
                common,
                policy_id=context["policy"],
                policy_kind="synthetic-policy",
                policy_version="fixture-policy/1",
                canonical_bytes=raw["policy"],
                policy_sha256=digest(raw["policy"]),
                schema_version="urn:media-trace:api:0.1.0#/$defs/PolicyDefinition",
            ),
        )
        for kind, table, identifier in (
            ("plan", "task_plan_artifact", "plan"),
            ("capability", "task_capability_manifest", "capability"),
        ):
            insert(
                connection,
                table,
                dict(
                    common,
                    **{
                        identifier + "_id": documents[kind][identifier + "_id"],
                        identifier + "_version": documents[kind][identifier + "_version"],
                        "canonical_bytes": raw[kind],
                        identifier + "_sha256": digest(raw[kind]),
                        "schema_version": documents[kind]["schema_id"],
                    },
                ),
            )
        now = datetime.now(timezone.utc)
        revision = dict(
            revision_id=uuid4(),
            org_id=context["org"],
            case_id=context["case"],
            mapping_id="fixture-SQL-mapping",
            mapping_version="1",
            authority_version="self-owned-only/1",
            scene=documents["plan"]["scene"],
            modules=documents["plan"]["modules"],
            priority=documents["plan"]["priority"],
            policy_id=context["policy"],
            policy_kind="synthetic-policy",
            policy_version="fixture-policy/1",
            policy_sha256=digest(raw["policy"]),
            plan_id=documents["plan"]["plan_id"],
            plan_version=documents["plan"]["plan_version"],
            plan_sha256=digest(raw["plan"]),
            capability_id=documents["capability"]["capability_id"],
            capability_version=documents["capability"]["capability_version"],
            capability_sha256=digest(raw["capability"]),
            valid_from=now - timedelta(minutes=1),
            valid_until=now + timedelta(minutes=30),
            adoption_basis_ref="self-owned-fixture-not-a-real-decision",
            recovery_generation="self-owned-recovery/1",
            validation_receipt_bytes=receipt,
            validation_receipt_sha256=digest(receipt),
            created_by=context["user"],
        )
        insert(connection, "task_plan_mapping_revision", revision)
        head = {
            key: revision[key]
            for key in (
                "org_id",
                "case_id",
                "scene",
                "policy_id",
                "policy_version",
                "modules",
                "priority",
                "revision_id",
            )
        }
        head.update(state="ACTIVE", changed_by=context["user"])
        insert(connection, "task_plan_mapping_head", head)
        # Test-only local generation, not an independent RecoveryGenerationReader.
        connection.execute(
            "UPDATE mt.authorization_epoch SET policy_version='self-owned-fence/1',policy_sha256=%s,recovery_generation=%s",
            ("f" * 64, revision["recovery_generation"]),
        )
        connection.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )
        connection.execute(sql.SQL("GRANT mt_runtime TO {}").format(sql.Identifier(role)))
    context.update(
        admin_dsn=database_dsn,
        runtime_dsn=PrivateTestDSN(make_conninfo(database_dsn, user=role, password=password)),
        runtime_role=role,
        revision=revision,
        head=head,
        documents=documents,
        raw=raw,
        receipt=receipt,
    )
    try:
        yield context
    finally:
        with psycopg.connect(database_dsn) as connection:
            connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_two_fixed_plan_functions_are_installed(database_dsn):
    migrate(database_dsn)
    with psycopg.connect(database_dsn) as connection:
        rows = connection.execute(
            "SELECT p.proname,p.prosecdef FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid=p.pronamespace "
            "WHERE n.nspname='mt' AND p.proname IN "
            "('task_create_plan_metadata','task_create_execution_plan') ORDER BY p.proname"
        ).fetchall()
    assert rows == [
        ("task_create_execution_plan", True),
        ("task_create_plan_metadata", True),
    ]


def test_real_runtime_lookup_is_readonly_exact_and_body_free(sql_context):
    context = sql_context
    with psycopg.connect(context["runtime_dsn"]) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        bind(connection, context, mode="LOOKUP")
        result = rows(connection, METADATA, arguments(context))
        assert len(result) == 1
        metadata = result[0]
        assert set(metadata["validation_receipt"]) == {
            "sha256",
            "validator_id",
            "validator_version",
            "schema_id",
            "schema_version",
        }
        assert metadata["validation_receipt"] == dict(
            sha256=digest(context["receipt"]),
            validator_id=None,
            validator_version=None,
            schema_id=None,
            schema_version=None,
        )
        assert metadata["required_capability_refs"] == dict(
            capability_id=context["revision"]["capability_id"],
            capability_version=context["revision"]["capability_version"],
            capability_sha256=context["revision"]["capability_sha256"],
            handlers=context["documents"]["capability"]["handlers"],
        )
        assert not any("bytes" in key for key in metadata)
        facts = metadata["current_state_facts"]
        assert set(facts) == {
            "asset",
            "source",
            "policy",
            "case",
            "memberships",
            "actor",
            "organization",
            "head",
            "generation",
        }
        assert facts["asset"]["object_ref"] == dict(
            object_id=str(context["object"]),
            version_id="fixture-object/1",
            sha256="a" * 64,
        )
        assert facts["asset"]["content_id"] is not None and facts["asset"]["mapping_version"] == "fixture-only"
        assert facts["asset"]["created_at"].endswith("Z")
        assert rows(connection, EXECUTION, execution_arguments(context)) == []
        assert connection.execute(
            "SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND mode='RowShareLock'"
        ).fetchone() == (0,)
        for table in (
            "task_policy_artifact",
            "task_plan_artifact",
            "task_capability_manifest",
        ):
            with (
                pytest.raises(psycopg.errors.InsufficientPrivilege),
                connection.transaction(),
            ):
                connection.execute(sql.SQL("SELECT canonical_bytes FROM mt.{}").format(sql.Identifier(table)))


def test_case_body_and_metadata_are_same_observation_with_actual_nonowner_locks(
    sql_context,
):
    context = sql_context
    with psycopg.connect(context["runtime_dsn"]) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        bind(connection, context, mode="LOOKUP")
        before = rows(connection, METADATA, arguments(context))[0]
    with psycopg.connect(context["runtime_dsn"]) as connection:
        bind(connection, context)
        body = rows(connection, EXECUTION, execution_arguments(context))
        assert len(body) == 1
        assert body[0]["policy_bytes"] == context["raw"]["policy"]
        assert body[0]["plan_bytes"] == context["raw"]["plan"]
        assert body[0]["capability_bytes"] == context["raw"]["capability"]
        assert body[0]["validation_receipt_bytes"] == context["receipt"]
        after = rows(connection, METADATA, arguments(context))[0]
        assert after == before
        assert body[0]["current_state_facts"] == before["current_state_facts"]
        locked = {
            row[0]
            for row in connection.execute(
                "SELECT c.relname FROM pg_locks l JOIN pg_class c ON c.oid=l.relation "
                "WHERE l.pid=pg_backend_pid() AND l.mode='RowShareLock'"
            ).fetchall()
        }
        assert set(LOCKED_TABLES) <= locked
        assert connection.execute("SELECT current_user").fetchone() == (context["runtime_role"],)


def test_fixed_owners_are_restricted_not_tableowners_and_runtime_cannot_inherit(
    sql_context,
):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        result = connection.execute(
            "SELECT p.proname,r.rolname,r.rolcanlogin,r.rolinherit,r.rolsuper,r.rolbypassrls "
            "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_roles r ON r.oid=p.proowner "
            "WHERE n.nspname='mt' AND p.proname IN ('task_create_plan_metadata','task_create_execution_plan') ORDER BY p.proname"
        ).fetchall()
        assert result == [
            ("task_create_execution_plan", CASE_READER, False, False, False, False),
            (
                "task_create_plan_metadata",
                "mt_task_plan_lookup",
                False,
                False,
                False,
                False,
            ),
        ]
        assert connection.execute(
            "SELECT count(*) FROM pg_class WHERE relnamespace='mt'::regnamespace "
            "AND relowner IN ('mt_task_plan_lookup'::regrole,'mt_task_plan_case_reader'::regrole)"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT count(*) FROM pg_auth_members WHERE roleid='mt_task_plan_case_reader'::regrole "
            "OR member='mt_task_plan_case_reader'::regrole"
        ).fetchone() == (0,)
        for table in LOCKED_TABLES:
            assert connection.execute(
                "SELECT has_any_column_privilege(%s,%s,'UPDATE')",
                ("mt_task_plan_lookup", "mt." + table),
            ).fetchone() == (False,)
            assert connection.execute(
                "SELECT has_table_privilege(%s,%s,'UPDATE'),has_column_privilege(%s,%s,'row_version','UPDATE')",
                (CASE_READER, "mt." + table, CASE_READER, "mt." + table),
            ).fetchone() == (False, True)
        assert connection.execute("SELECT has_schema_privilege(%s,'mt','CREATE')", (CASE_READER,)).fetchone() == (
            False,
        )
    with psycopg.connect(context["runtime_dsn"]) as connection:
        for role in ("mt_task_plan_lookup", CASE_READER, "mt_task_plan_manager"):
            with (
                pytest.raises(psycopg.errors.InsufficientPrivilege),
                connection.transaction(),
            ):
                connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))


@pytest.mark.parametrize("change", ["operation", "mode", "lookup", "actor", "org", "case", "readonly-case"])
def test_scope_cannot_be_replaced_even_for_real_directory_rows(sql_context, change):
    context = sql_context
    with psycopg.connect(context["runtime_dsn"]) as connection:
        if change in {"lookup", "readonly-case"}:
            connection.execute("SET TRANSACTION READ ONLY")
        kwargs = {}
        if change == "operation":
            kwargs["operation"] = "getAsset"
        if change == "mode":
            kwargs["mode"] = "ORGANIZATION"
        if change == "lookup":
            kwargs.update(mode="LOOKUP", lookup=str(uuid4()))
        if change == "actor":
            kwargs["actor"] = context["other_user"]
        if change == "org":
            kwargs["org"] = context["other_org"]
        if change == "case":
            kwargs["case"] = context["other_case"]
        bind(connection, context, **kwargs)
        assert rows(connection, METADATA, arguments(context)) == []
        assert rows(connection, EXECUTION, execution_arguments(context)) == []


@pytest.mark.parametrize(
    "index,value",
    [
        (0, None),
        (1, None),
        (2, "unknown"),
        (3, "wrong-version"),
        (4, []),
        (4, ["RESOURCE", "INGEST"]),
        (5, "urgent"),
    ],
)
def test_exact_request_tuple_never_uses_a_nearby_default(sql_context, index, value):
    context = sql_context
    args = list(arguments(context))
    args[index] = value
    with psycopg.connect(context["runtime_dsn"]) as connection:
        bind(connection, context)
        assert rows(connection, METADATA, args) == []


@pytest.mark.parametrize(
    "index,value",
    [
        (6, None),
        (6, uuid4()),
        (7, "A" * 64),
        (7, "b" * 64),
        (8, "b" * 64),
        (9, "b" * 64),
    ],
)
def test_execution_requires_exact_revision_and_all_three_raw_material_hashes(sql_context, index, value):
    context = sql_context
    args = list(execution_arguments(context))
    args[index] = value
    with psycopg.connect(context["runtime_dsn"]) as connection:
        bind(connection, context)
        assert rows(connection, EXECUTION, args) == []


@pytest.mark.parametrize("table", LOCKED_TABLES)
@pytest.mark.parametrize("statement", ["UPDATE", "INSERT", "DELETE", "TRUNCATE"])
def test_case_lock_column_acl_never_permits_actual_dml(sql_context, table, statement):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        bind(connection, context)
        connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(CASE_READER)))
        assert connection.execute("SELECT current_user").fetchone() == (CASE_READER,)
        count = connection.execute(sql.SQL("SELECT count(*) FROM mt.{}").format(sql.Identifier(table))).fetchone()
        assert count is not None and count[0] > 0
        query = {
            "UPDATE": sql.SQL("UPDATE mt.{} SET row_version=row_version+1"),
            "INSERT": sql.SQL("INSERT INTO mt.{} DEFAULT VALUES"),
            "DELETE": sql.SQL("DELETE FROM mt.{}"),
            "TRUNCATE": sql.SQL("TRUNCATE mt.{}"),
        }[statement].format(sql.Identifier(table))
        with (
            pytest.raises(psycopg.errors.InsufficientPrivilege),
            connection.transaction(),
        ):
            connection.execute(query)


def test_dml_guard_is_invoker_and_orders_before_any_epoch_trigger(sql_context):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        assert connection.execute(
            "SELECT prosecdef FROM pg_proc WHERE oid='mt.reject_task_plan_case_reader_dml()'::regprocedure"
        ).fetchone() == (False,)
        assert connection.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_proc p,LATERAL aclexplode(p.proacl) a "
            "WHERE p.oid='mt.reject_task_plan_case_reader_dml()'::regprocedure "
            "AND a.grantee=0 AND a.privilege_type='EXECUTE')"
        ).fetchone() == (False,)
        assert connection.execute(
            "SELECT has_function_privilege(%s,'mt.reject_task_plan_case_reader_dml()','EXECUTE')",
            (context["runtime_role"],),
        ).fetchone() == (False,)
        for table in LOCKED_TABLES:
            triggers = connection.execute(
                "SELECT tgname,tgtype,pg_get_triggerdef(oid) FROM pg_trigger "
                "WHERE tgrelid=%s::regclass AND NOT tgisinternal ORDER BY tgname",
                ("mt." + table,),
            ).fetchall()
            guards = [row for row in triggers if row[0] == "aaa_task_plan_case_reader_no_dml"]
            assert len(guards) == 1 and guards[0][1] == 62
            assert "reject_task_plan_case_reader_dml" in guards[0][2]
            assert all(guards[0][0] < row[0] for row in triggers if "epoch" in row[0])


@pytest.mark.parametrize("table", LOCKED_TABLES)
def test_case_reader_zero_row_statements_cannot_advance_epoch(sql_context, table):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        before_row = connection.execute("SELECT epoch FROM mt.authorization_epoch WHERE singleton").fetchone()
        assert before_row is not None
        before = before_row[0]
        bind(connection, context)
        connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(CASE_READER)))
        assert connection.execute("SELECT current_user").fetchone() == (CASE_READER,)
        denied = False
        try:
            with connection.transaction():
                result = connection.execute(
                    sql.SQL("UPDATE mt.{} SET row_version=row_version WHERE false").format(sql.Identifier(table))
                )
                assert result.rowcount == 0
        except psycopg.errors.InsufficientPrivilege:
            denied = True
        connection.execute("RESET ROLE")
    # Commit the zero-row statement if it was accepted, then inspect from an
    # independent transaction. A statement-level epoch trigger is observable
    # even when no row reached an RLS WITH CHECK expression.
    with psycopg.connect(context["admin_dsn"]) as connection:
        after_row = connection.execute("SELECT epoch FROM mt.authorization_epoch WHERE singleton").fetchone()
        assert after_row is not None
        after = after_row[0]
    assert after == before, "ZERO_ROW_STATEMENT_ADVANCED_AUTHORIZATION_EPOCH"
    assert denied is True, "CASE_READER_ZERO_ROW_DML_NOT_REJECTED"


@pytest.mark.parametrize(
    "flaw", ["other-member", "inherit", "admin", "cannot-set", "runtime-member", "private-inherits"]
)
def test_installation_precheck_rejects_every_nonexact_temporary_membership(sql_context, flaw):
    from tests.business.test_migrations import MIGRATIONS

    migration = (MIGRATIONS / "0017_task_creation_scope_reads.sql").read_text("utf8")
    precheck = migration.split("REVOKE ALL ON ALL TABLES", 1)[0]
    context = sql_context
    installer = "mt_plan_installer_" + uuid4().hex
    with psycopg.connect(context["admin_dsn"]) as connection:
        try:
            connection.execute(
                sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB").format(
                    sql.Identifier(installer)
                )
            )
            connection.execute(sql.SQL("ALTER SCHEMA mt OWNER TO {}").format(sql.Identifier(installer)))
            connection.execute(
                sql.SQL("GRANT mt_task_plan_lookup TO {} WITH INHERIT FALSE, SET TRUE, ADMIN FALSE").format(
                    sql.Identifier(installer)
                )
            )
            inherit = "TRUE" if flaw == "inherit" else "FALSE"
            can_set = "FALSE" if flaw == "cannot-set" else "TRUE"
            admin = "TRUE" if flaw == "admin" else "FALSE"
            recipient = context["runtime_role"] if flaw == "other-member" else installer
            connection.execute(
                sql.SQL("GRANT mt_task_plan_case_reader TO {} WITH INHERIT {}, SET {}, ADMIN {}").format(
                    sql.Identifier(recipient), sql.SQL(inherit), sql.SQL(can_set), sql.SQL(admin)
                )
            )
            if flaw == "runtime-member":
                connection.execute(sql.SQL("GRANT mt_runtime TO {}").format(sql.Identifier(installer)))
            if flaw == "private-inherits":
                connection.execute("GRANT mt_runtime TO mt_task_plan_case_reader WITH INHERIT FALSE, SET TRUE")
            connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(installer)))
            with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState), connection.transaction():
                connection.execute(precheck)
        finally:
            # Role edges and schema ownership are global/catalog changes. No
            # successful or failed test may leak even a temporary installer.
            connection.rollback()


def test_restrictive_check_still_rejects_update_after_another_permissive_policy(
    sql_context,
):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        connection.execute(
            "CREATE POLICY synthetic_extra_allow ON mt.media_asset FOR UPDATE TO mt_task_plan_case_reader USING(true) WITH CHECK(true)"
        )
        bind(connection, context)
        connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(CASE_READER)))
        with (
            pytest.raises(psycopg.errors.InsufficientPrivilege),
            connection.transaction(),
        ):
            connection.execute(
                "UPDATE mt.media_asset SET row_version=row_version+1 WHERE asset_id=%s",
                (context["asset"],),
            )


@pytest.mark.parametrize(
    "field,value",
    [
        ("authorization_status", "pending"),
        ("purpose", ["upload"]),
        ("expires_at", datetime(2020, 1, 1, tzinfo=timezone.utc)),
    ],
)
def test_case_body_refuses_current_source_revocation_purpose_and_expiry(sql_context, field, value):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        connection.execute(
            sql.SQL("UPDATE mt.source_registry SET {}=%s,row_version=row_version+1 WHERE source_id=%s").format(
                sql.Identifier(field)
            ),
            (value, context["source"]),
        )
    with psycopg.connect(context["runtime_dsn"]) as connection:
        bind(connection, context)
        assert rows(connection, EXECUTION, execution_arguments(context)) == []


@pytest.mark.parametrize("state", ["INACTIVE", "REVOKED"])
def test_no_current_active_head_does_not_replay_an_immutable_old_revision(sql_context, state):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.task_plan_mapping_head SET state=%s,row_version=row_version+1",
            (state,),
        )
    with psycopg.connect(context["runtime_dsn"]) as connection:
        bind(connection, context)
        assert rows(connection, METADATA, arguments(context)) == []
        assert rows(connection, EXECUTION, execution_arguments(context)) == []


def ambiguous_head(connection, context):
    revision = copy.deepcopy(context["revision"])
    policy = uuid4()
    connection.execute(
        "INSERT INTO mt.policy_registry(policy_id,org_id,kind,version,definition_ref,status,created_by) VALUES(%s,%s,'another-kind','fixture-policy/1','self-owned-only','DRAFT',%s)",
        (policy, context["org"], context["user"]),
    )
    insert(
        connection,
        "task_policy_artifact",
        dict(
            org_id=context["org"],
            policy_id=policy,
            policy_kind="another-kind",
            policy_version="fixture-policy/1",
            canonical_bytes=context["raw"]["policy"],
            policy_sha256=revision["policy_sha256"],
            schema_version="urn:media-trace:api:0.1.0#/$defs/PolicyDefinition",
            canonicalization_version="task-material-json-utf8-sortkeys-v1",
            provenance_ref="ambiguous-fixture-only",
            created_by=context["user"],
        ),
    )
    revision.update(
        revision_id=uuid4(),
        mapping_id="ambiguous-mapping",
        policy_id=policy,
        policy_kind="another-kind",
    )
    insert(connection, "task_plan_mapping_revision", revision)
    head = dict(context["head"], policy_id=policy, revision_id=revision["revision_id"])
    return head


def test_two_policy_kinds_with_same_request_version_are_ambiguous_not_limit_one(
    sql_context,
):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as connection:
        insert(connection, "task_plan_mapping_head", ambiguous_head(connection, context))
    with psycopg.connect(context["runtime_dsn"]) as connection:
        bind(connection, context)
        assert rows(connection, METADATA, arguments(context)) == []
        # Supplying the first revision must not hide the other valid candidate.
        assert rows(connection, EXECUTION, execution_arguments(context)) == []


@pytest.mark.parametrize("table", LOCKED_TABLES)
def test_actual_case_read_holds_locks_until_the_callers_transaction_ends(sql_context, table):
    context = sql_context
    with psycopg.connect(context["runtime_dsn"]) as runtime:
        bind(runtime, context)
        assert len(rows(runtime, EXECUTION, execution_arguments(context))) == 1
        with psycopg.connect(context["admin_dsn"]) as writer:
            writer.execute("SET LOCAL lock_timeout='150ms'")
            with pytest.raises(psycopg.errors.LockNotAvailable), writer.transaction():
                writer.execute(sql.SQL("UPDATE mt.{} SET row_version=row_version+1").format(sql.Identifier(table)))
    with psycopg.connect(context["admin_dsn"]) as writer:
        assert (
            writer.execute(sql.SQL("UPDATE mt.{} SET row_version=row_version+1").format(sql.Identifier(table))).rowcount
            > 0
        )


def test_epoch_lock_also_blocks_a_new_ambiguous_head_phantom(sql_context):
    context = sql_context
    with psycopg.connect(context["admin_dsn"]) as writer:
        # Prepare immutable rows before the reader holds epoch; only insertion
        # of the second adopted head is the concurrent change being exercised.
        second = ambiguous_head(writer, context)
    with psycopg.connect(context["runtime_dsn"]) as runtime:
        bind(runtime, context)
        assert len(rows(runtime, EXECUTION, execution_arguments(context))) == 1
        with psycopg.connect(context["admin_dsn"]) as writer:
            writer.execute("SET LOCAL lock_timeout='150ms'")
            with pytest.raises(psycopg.errors.LockNotAvailable), writer.transaction():
                insert(writer, "task_plan_mapping_head", second)
    with psycopg.connect(context["admin_dsn"]) as writer:
        insert(writer, "task_plan_mapping_head", second)
    with psycopg.connect(context["runtime_dsn"]) as runtime:
        bind(runtime, context)
        assert rows(runtime, METADATA, arguments(context)) == []


def test_temporary_shadow_and_session_timezone_cannot_replace_fixed_projection(
    sql_context,
):
    context = sql_context
    with psycopg.connect(context["runtime_dsn"]) as connection:
        connection.execute("CREATE TEMP TABLE task_plan_mapping_head(fake text)")
        connection.commit()
        connection.execute("SET TRANSACTION READ ONLY")
        connection.execute("SET LOCAL search_path=pg_temp,public,mt")
        connection.execute("SET LOCAL TimeZone='Pacific/Honolulu'")
        bind(connection, context, mode="LOOKUP")
        first = rows(connection, METADATA, arguments(context))
        connection.execute("SET LOCAL TimeZone='Asia/Shanghai'")
        assert rows(connection, METADATA, arguments(context)) == first
