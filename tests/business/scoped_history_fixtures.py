"""Explicit synthetic producer/read inputs around real immutable-history methods."""

from uuid import UUID

from business_app.history.repository import ResultRepository

from tests.business.http_fixtures import FixtureWork, synthetic_case_evidence


class FixtureResultRepository(ResultRepository):
    def append_snapshot(self, scope, snapshot):
        self.validate_snapshot(snapshot)
        task = UUID(snapshot["binding"]["task_id"])
        with FixtureWork(frozenset({scope.actor})).open(scope, "task_execution", task, "finishTaskNodeWork"):
            return super().append_snapshot(scope, snapshot)

    def load_exact(self, scope, key):
        with synthetic_case_evidence(scope.actor, scope.case_id):
            return super().load_exact(scope, key)

    def load_latest(self, scope, operation_id, resource_id, ranking_id=None):
        with synthetic_case_evidence(scope.actor, scope.case_id):
            return super().load_latest(scope, operation_id, resource_id, ranking_id)


def append_synthetic_snapshot(context, snapshot):
    from business_app.types import Scope

    scope = Scope(context["actor"], context["case_id"])
    repository = context["app"].state.result_repository
    task = UUID(snapshot["binding"]["task_id"])
    with FixtureWork(frozenset({scope.actor})).open(scope, "task_execution", task, "finishTaskNodeWork"):
        return repository.append_snapshot(scope, snapshot)
