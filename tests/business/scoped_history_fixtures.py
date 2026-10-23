"""Explicit synthetic producer/read inputs around real immutable-history methods."""

import time
from contextlib import contextmanager
from uuid import UUID

from business_app.history.repository import ResultRepository
from business_app.permissions.context import current_authorization, request_authorization
from business_app.permissions.rule_types import AuthorizationEvidence, RuleTarget
from business_app.permissions.types import Principal

from tests.business.http_fixtures import FixtureFence, FixtureWork


@contextmanager
def history_read_evidence(scope, operation, kind, identifier):
    if current_authorization() is not None:
        yield
        return
    principal = Principal(
        scope.actor, "https://identity.example.test", str(scope.actor.user_id), int(time.time()) + 600
    )
    proof = AuthorizationEvidence(
        principal,
        operation,
        RuleTarget(scope.actor.org_id, kind, identifier, None, scope.case_id, None, None),
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-case-test",
        time.time() + 60,
    )
    with request_authorization(proof, FixtureFence(frozenset({scope.actor})), mutation=False):
        yield


class FixtureResultRepository(ResultRepository):
    def append_snapshot(self, scope, snapshot):
        self.validate_snapshot(snapshot)
        task = UUID(snapshot["binding"]["task_id"])
        with FixtureWork(frozenset({scope.actor})).open(scope, "task_execution", task, "finishTaskNodeWork"):
            return super().append_snapshot(scope, snapshot)

    def load_exact(self, scope, key):
        with history_read_evidence(scope, "getTask", "task", key.task_id):
            return super().load_exact(scope, key)

    def load_latest(self, scope, operation_id, resource_id, ranking_id=None):
        kind = (
            "task"
            if operation_id in {"getTask", "getRiskFindings", "getForensics", "getTaskEvidence"}
            else "asset"
            if operation_id == "getTimeline"
            else "cluster"
        )
        with history_read_evidence(scope, operation_id, kind, resource_id):
            return super().load_latest(scope, operation_id, resource_id, ranking_id)


def append_synthetic_snapshot(context, snapshot):
    from business_app.types import Scope

    scope = Scope(context["actor"], context["case_id"])
    repository = context["app"].state.result_repository
    task = UUID(snapshot["binding"]["task_id"])
    with FixtureWork(frozenset({scope.actor})).open(scope, "task_execution", task, "finishTaskNodeWork"):
        return repository.append_snapshot(scope, snapshot)
