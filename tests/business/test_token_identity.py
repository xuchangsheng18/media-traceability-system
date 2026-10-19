"""Synthetic introspection plus real least-privilege PostgreSQL identity lookup."""

from typing import Any
from uuid import uuid4

import httpx
import psycopg
import pytest
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.identity.tokens import IntrospectionSettings, IntrospectionVerifier, MappedTokenAuthority
from business_app.types import Scope
from psycopg import sql
from psycopg.conninfo import make_conninfo


@pytest.fixture
def token_context(business_context):
    ctx = business_context
    role = "mt_token_lookup_" + uuid4().hex
    secret = uuid4().hex + uuid4().hex
    identity = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(secret)
            )
        )
        admin.execute(sql.SQL("GRANT mt_identity_lookup TO {}").format(sql.Identifier(role)))
        admin.execute(
            "INSERT INTO mt.user_identities(identity_id,user_id,org_id,issuer,subject,mapping_version,enabled) VALUES(%s,%s,%s,%s,%s,'synthetic-v1',true)",
            (identity, ctx["actor"].user_id, ctx["actor"].org_id, "https://identity.example.test", "synthetic-subject"),
        )
    lookup = Database(make_conninfo(ctx["admin_dsn"], user=role, password=secret))
    state: dict[str, Any] = dict(
        active=True,
        iss="https://identity.example.test",
        sub="synthetic-subject",
        aud="synthetic-api",
        exp=200,
        token_type="Bearer",
    )
    clock = [100]
    settings = IntrospectionSettings(
        endpoint="https://identity.example.test/introspect",
        issuer=state["iss"],
        audience=state["aud"],
        client_id="synthetic-client",
        client_secret=uuid4().hex,
        timeout_seconds=2,
        max_response_bytes=2048,
        max_token_bytes=128,
    )
    verifier = IntrospectionVerifier(
        settings, clock=lambda: clock[0], transport=httpx.MockTransport(lambda request: httpx.Response(200, json=state))
    )
    authority = MappedTokenAuthority(verifier, lookup)
    try:
        yield ctx, authority, state, identity, clock, role
    finally:
        verifier.close()
        lookup.close()
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_active_token_maps_exact_identity_without_granting_case_or_source(token_context):
    ctx, authority, _, _, _, _ = token_context
    actor = authority.authenticate("synthetic-token")
    assert actor == ctx["actor"]
    with pytest.raises(BusinessError, match="FORMAL_POLICY_UNCONFIGURED"):
        authority.authorize_case(actor, ctx["case_id"], "result.read")
    with pytest.raises(BusinessError, match="FORMAL_POLICY_UNCONFIGURED"):
        authority.authorize_source(Scope(actor, ctx["case_id"]), ctx["source_id"], "analysis")


def test_authenticate_principal_preserves_exact_issuer_subject_mapping(token_context):
    ctx, authority, state, _, _, _ = token_context
    method = getattr(authority, "authenticate_principal", None)
    assert callable(method), "T014 verified principal method is missing"
    principal = method("synthetic-token")
    assert principal.actor == ctx["actor"]
    assert principal.issuer == state["iss"]
    assert principal.subject == state["sub"]
    assert principal.expires_at == state["exp"]
    assert authority.authenticate("synthetic-token") == principal.actor


def test_principal_expired_after_database_lookup_is_rejected(token_context, monkeypatch):
    _, authority, _, _, clock, _ = token_context
    method = getattr(authority, "authenticate_principal", None)
    assert callable(method), "T014 verified principal method is missing"
    from business_app.identity.directory import IdentityDirectory

    original = IdentityDirectory.resolve

    def resolve_then_expire(self, issuer, subject):
        result = original(self, issuer, subject)
        clock[0] = 200
        return result

    monkeypatch.setattr(IdentityDirectory, "resolve", resolve_then_expire)
    with pytest.raises(BusinessError, match="AUTHENTICATION_REQUIRED") as error:
        method("synthetic-token")
    assert error.value.http_status == 401


@pytest.mark.parametrize(
    "change",
    [
        "disabled_user",
        "disabled_org",
        "revoked_mapping",
        "expired_mapping",
        "disabled_mapping",
        "unmapped",
        "issuer",
        "forged",
        "expired_token",
    ],
)
def test_identity_and_session_changes_are_seen_on_next_authentication(token_context, change):
    ctx, authority, state, identity, clock, _ = token_context
    assert authority.authenticate("synthetic-token") == ctx["actor"]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if change == "disabled_user":
            admin.execute("UPDATE mt.users SET enabled=false WHERE user_id=%s", (ctx["actor"].user_id,))
        elif change == "disabled_org":
            admin.execute("UPDATE mt.organizations SET enabled=false WHERE org_id=%s", (ctx["actor"].org_id,))
        elif change in {"revoked_mapping", "expired_mapping", "disabled_mapping"}:
            assignment = {
                "revoked_mapping": "enabled=false,revoked_at=now(),updated_at=now(),row_version=row_version+1",
                "expired_mapping": "expires_at=now()-interval '1 second'",
                "disabled_mapping": "enabled=false",
            }[change]
            admin.execute(
                sql.SQL("UPDATE mt.user_identities SET {} WHERE identity_id=%s").format(sql.SQL(assignment)),
                (identity,),
            )
    if change == "unmapped":
        state["sub"] = "unmapped-subject"
    elif change == "issuer":
        state["iss"] = "https://other.example.test"
    elif change == "forged":
        state["active"] = False  # The remote authority is the verifier; no local JWT decoding.
    elif change == "expired_token":
        clock[0] = 200
    with pytest.raises(BusinessError, match="AUTHENTICATION_REQUIRED"):
        authority.authenticate("synthetic-token")


def test_directory_manager_connection_rejected_for_authentication(token_context):
    ctx, authority, _, _, _, role = token_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(sql.SQL("GRANT mt_directory_manager TO {}").format(sql.Identifier(role)))
    with pytest.raises(BusinessError, match="IDENTITY_AUTHORITY_UNAVAILABLE"):
        authority.authenticate("synthetic-token")


def test_missing_lookup_privilege_fails_closed(token_context):
    ctx, authority, _, _, _, role = token_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(sql.SQL("REVOKE mt_identity_lookup FROM {}").format(sql.Identifier(role)))
    with pytest.raises(BusinessError, match="IDENTITY_AUTHORITY_UNAVAILABLE"):
        authority.authenticate("synthetic-token")


def test_token_expiring_during_lookup_is_rejected(token_context):
    _, authority, _, _, _, _ = token_context
    times = iter([100, 200])
    authority.verifier.clock = lambda: next(times)
    with pytest.raises(BusinessError, match="AUTHENTICATION_REQUIRED"):
        authority.authenticate("synthetic-token")
