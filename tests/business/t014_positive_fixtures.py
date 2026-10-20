"""Explicit synthetic facts with real role lookup, RLS, resolver and condition authority."""

import time
from uuid import UUID, uuid4

import psycopg

from tests.business.http_fixtures import isolated_rule_fence
from tests.business.test_t014_object_rules import configure
from tests.business.test_t014_permissions import permission_module


def candidate(ctx, permission_context, permissions):
    current = dict(ctx)
    for key in ["lookup", "principal", "identity", "binding", "role", "permission", "relation", "login"]:
        current[key] = permission_context[key]
    types, roles, rules, objects, authority = configure(current, "case_investigator")
    with psycopg.connect(current["admin_dsn"]) as admin:
        found_role = admin.execute("SELECT role_id FROM mt.roles WHERE code='case_investigator'").fetchone()
        assert found_role is not None
        role = found_role[0]
        for code in permissions:
            found = admin.execute("SELECT permission_id FROM mt.permissions WHERE code=%s", (code,)).fetchone()
            identifier = found[0] if found else uuid4()
            if not found:
                admin.execute(
                    "INSERT INTO mt.permissions(permission_id,code,description,enabled) VALUES(%s,%s,'synthetic-only',true)",
                    (identifier, code),
                )
            admin.execute(
                "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s) ON CONFLICT(role_id,permission_id) DO NOTHING",
                (uuid4(), role, identifier),
            )

    class InstitutionalFacts:
        blocked: set[UUID] = set()
        delegation: bool | None = None

        def read(self, principal, operation_id, target, *, connection):
            assert principal == current["principal"] and target.org_id == current["actor"].org_id
            assert target.case_id == current["case_id"]
            checks = dict(
                classification=target.object_id not in self.blocked,
                read_purpose=True,
                purpose_basis=True,
                metadata_scope=True,
            )
            if operation_id in {"cancelTask", "getApproval"} and self.delegation is not None:
                checks["control_authorized" if operation_id == "cancelTask" else "own_or_delegated_request"] = (
                    self.delegation
                )
            return types.ConditionFacts(
                principal,
                target,
                checks,
                permission_module("object_facts").digest([operation_id, target, checks]),
                time.time() + 60,
            )

    facts = InstitutionalFacts()
    objects.supplemental = facts
    original = ctx["control_authority"]

    class Identity:
        def authenticate_principal(self, token):
            assert original.authenticate(token) == current["actor"]
            return current["principal"]

        authenticate = original.authenticate
        authorize_case = original.authorize_case
        authorize_source = original.authorize_source

    app = ctx["control_app"]
    app.state.business_authority = Identity()
    app.state.permission_authority = permission_module("six_role").SixRoleEntryAuthority(roles, rules)
    app.state.conditional_permissions = authority
    app.state.authorization_fence = isolated_rule_fence(current, authority)
    return current, objects, authority, facts
