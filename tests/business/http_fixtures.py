"""Explicit synthetic permissions and isolated HTTP error harnesses, never deployment defaults."""

import hashlib
import time
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from typing import Any
from uuid import UUID, uuid4

from business_app.errors import BusinessError
from business_app.permissions.context import Evidence, evidence_actor, request_authorization
from business_app.permissions.duties import DutyActors, IndependentDuties, VerifiedPerson
from business_app.permissions.rule_types import (
    AuthorizationEvidence,
    ExecutionSubject,
    RuleTarget,
    WorkAuthorizationEvidence,
)
from business_app.permissions.types import Principal
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

    def __init__(self, actors: frozenset[Actor]) -> None:
        self.actors = actors

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
        target = RuleTarget(principal.actor.org_id, "explicit-synthetic-http-fixture", None, None, None, None, None)
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
