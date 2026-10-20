"""Explicit synthetic permissions and isolated HTTP error harnesses, never deployment defaults."""

import hashlib
import time
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

from business_app.errors import BusinessError
from business_app.permissions.context import Evidence, current_authorization, evidence_actor, request_authorization
from business_app.permissions.duties import DutyActors, IndependentDuties, VerifiedPerson
from business_app.permissions.object_facts import ObjectFactsReader
from business_app.permissions.rule_types import (
    AuthorizationEvidence,
    ExecutionSubject,
    RuleTarget,
    WorkAuthorizationEvidence,
)
from business_app.permissions.types import Principal
from business_app.permissions.work import WorkTrust, WorkTrustFacts
from business_app.permissions.work_subject import WORK_OPERATIONS
from business_app.types import Actor, Scope
from fastapi import FastAPI
from sqlalchemy import Connection, text


class FixturePermissions:
    def __init__(self, actors: frozenset[Actor], permissions: frozenset[str]) -> None:
        self.actors, self.permissions = actors, permissions

    def check(self, principal: Principal, permission: str) -> None:
        if principal.actor not in self.actors or permission not in self.permissions:
            raise BusinessError("PERMISSION_REQUIRED", 403)


class FixtureConditionals:
    """Explicit old-business harness, not a six-role rule or production adapter."""

    def __init__(self, actors: frozenset[Actor], database) -> None:
        self.actors, self.database = actors, database

    def authorize_http(
        self,
        principal: Principal,
        operation_id: str,
        path: Mapping[str, Any],
        query: Mapping[str, Any],
        body: Mapping[str, Any],
    ) -> AuthorizationEvidence:
        if principal.actor not in self.actors:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        target = ObjectFactsReader(self.database).resolve_http(principal, operation_id, path, query, body)
        sha = hashlib.sha256(b"explicit isolated old-business fixture, not formal policy").hexdigest()
        return AuthorizationEvidence(
            principal,
            operation_id,
            target,
            sha,
            sha,
            "explicit-synthetic-fixture",
            "explicit-synthetic-fixture",
            min(time.time() + 5, principal.expires_at),
        )

    def policy_kinds(self, principal: Principal) -> tuple[str, ...]:
        if principal.actor not in self.actors:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        return ("analysis", "retention", "review", "risk_taxonomy", "threshold")

    def authorize_collection_item(
        self, principal: Principal, operation_id: str, target: RuleTarget, *, connection: Connection
    ) -> AuthorizationEvidence:
        current = current_authorization()
        if (
            current is None
            or not isinstance(current.evidence, AuthorizationEvidence)
            or current.evidence.principal != principal
            or principal.actor not in self.actors
            or current.evidence.operation_id != operation_id
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        # Explicit synthetic legacy input only; real six-role tests use the
        # production authority and do not instantiate this adapter.
        return replace(current.evidence, target=target, valid_until=time.time() + 5)

    def review_ids(
        self, principal: Principal, operation_id: str, case_id: UUID, *, connection: Connection
    ) -> tuple[UUID, ...]:
        if principal.actor not in self.actors:
            raise BusinessError("PERMISSION_REQUIRED", 403)
        if operation_id not in {"listReviews", "listPendingReviews"}:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        # Preserve the explicit legacy business harness. Real six-role tests use
        # ConditionalPermissionAuthority and source/per-object SQL filtering.
        table, key = ("review_record", "review_id") if operation_id == "listReviews" else ("analysis_task", "task_id")
        values = (
            connection.execute(
                text(f"SELECT {key} FROM mt.{table} WHERE case_id=:case AND org_id=:org ORDER BY {key}"),
                dict(case=case_id, org=principal.actor.org_id),
            )
            .scalars()
            .all()
        )
        return tuple(values)


class FixtureFence:
    """Explicit old-HTTP harness only, not six-role/epoch/recovery proof."""

    def __init__(self, actors: frozenset[Actor]) -> None:
        self.actors = actors

    def hold(self, connection: Connection, evidence: Evidence) -> None:
        if evidence_actor(evidence) not in self.actors or evidence.policy_version != "explicit-synthetic-fixture":
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        binding = connection.execute(text("SELECT mt.actor_id(),mt.org_id()")).one()
        actor = evidence_actor(evidence)
        if tuple(binding) != (actor.user_id, actor.org_id):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)

    def finish(self, connection: Connection, evidence: Evidence) -> None:
        self.hold(connection, evidence)


@contextmanager
def synthetic_case_evidence(actor: Actor, case_id: UUID) -> Iterator[None]:
    """Explicit trusted test input for direct legacy DAO/RLS checks, never a default."""
    principal = Principal(actor, "https://identity.example.test", str(actor.user_id), int(time.time()) + 600)
    proof = AuthorizationEvidence(
        principal,
        "listSources",
        RuleTarget(actor.org_id, "case", case_id, None, case_id, None, None),
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-case-test",
        time.time() + 60,
    )
    with request_authorization(proof, FixtureFence(frozenset({actor})), mutation=True):
        yield


@contextmanager
def synthetic_upload_evidence(actor: Actor, case_id: UUID, upload_id: UUID) -> Iterator[None]:
    """Explicit resource-bound proof for a direct concurrent-upload test."""
    principal = Principal(actor, "https://identity.example.test", str(actor.user_id), int(time.time()) + 600)
    evidence = AuthorizationEvidence(
        principal,
        "putUploadPart",
        RuleTarget(actor.org_id, "upload", upload_id, None, case_id, "upload", None),
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-upload-test",
        time.time() + 60,
    )
    with request_authorization(evidence, FixtureFence(frozenset({actor})), mutation=True):
        yield


class FixtureWork:
    """Explicit legacy workflow harness; no claim of real delegation/service proof."""

    def __init__(self, actors: frozenset[Actor]) -> None:
        self.actors = actors

    @contextmanager
    def open(self, scope: Scope, kind: str, identifier: UUID, operation_id: str) -> Iterator[None]:
        if scope.actor not in self.actors:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        subject = ExecutionSubject(scope.actor, uuid4(), "synthetic-harness-only", kind, identifier)
        evidence = WorkAuthorizationEvidence(
            subject,
            operation_id,
            RuleTarget(
                scope.actor.org_id, WORK_OPERATIONS[operation_id][1], identifier, None, scope.case_id, None, None
            ),
            "a" * 64,
            "b" * 64,
            "explicit-synthetic-fixture",
            "synthetic-fixture",
            time.time() + 60,
        )
        with request_authorization(evidence, FixtureFence(self.actors), mutation=True):
            yield


class FixtureMetadataWorkTrust(WorkTrust):
    """Trusted synthetic input for isolated directory-fact tests only, not delegation proof."""

    def __init__(self):
        pass

    def read(self, subject: ExecutionSubject) -> WorkTrustFacts:
        return WorkTrustFacts(subject, "a" * 64, time.time() + 5)


def isolated_rule_fence(context, authority):
    """Actual epoch/fence against a newly activated, explicitly synthetic generation."""
    import psycopg
    from business_app.permissions.fence import AuthorizationFence, GenerationProof

    snapshot = authority.rules.snapshot
    with psycopg.connect(context["admin_dsn"]) as admin:
        row = admin.execute("SELECT datname,oid FROM pg_database WHERE datname=current_database()").fetchone()
        assert row is not None
        name, oid = row
        row = admin.execute("SELECT epoch FROM mt.authorization_epoch").fetchone()
        assert row is not None
        minimum = row[0]
        row = admin.execute(
            "SELECT mt.activate_authorization_generation(%s,%s,%s,%s)",
            (snapshot.version, snapshot.sha256, snapshot.recovery_generation, minimum),
        ).fetchone()
        assert row is not None
        epoch = row[0]

    class Generations:
        def read(self):
            now = time.time()
            return GenerationProof(
                snapshot.recovery_generation, snapshot.version, snapshot.sha256, name, oid, epoch, now - 1, now + 60
            )

    return AuthorizationFence(authority, Generations(), clock=time.time)


class FixtureDuties(IndependentDuties):
    """Explicit fake people/duties as inputs; uses the real independent-person checks."""

    def __init__(self, actors: frozenset[Actor], requester: Actor) -> None:
        deadline = int(time.time()) + 3600
        mappings = {a: VerifiedPerson(a, uuid4(), "explicit-synthetic-person-v1", deadline) for a in actors}

        class People:
            def resolve(self, actor: Actor) -> VerifiedPerson:
                return mappings[actor]

        class Assignments:
            def read(self, target: RuleTarget, *, connection: Connection | None) -> DutyActors:
                return DutyActors(
                    target,
                    frozenset({requester}),
                    frozenset({requester}),
                    frozenset(),
                    hashlib.sha256(b"explicit synthetic duty assignment; not an institutional authority").hexdigest(),
                    deadline,
                )

        super().__init__(People(), Assignments())


def isolated_http_harness(application: FastAPI) -> FastAPI:
    """Test actual error middleware/handlers without adding unknown production routes."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            application.state.business_database.close()

    harness = FastAPI(middleware=application.user_middleware, lifespan=lifespan)
    harness.exception_handlers = dict(application.exception_handlers)
    harness.state = application.state
    return harness
