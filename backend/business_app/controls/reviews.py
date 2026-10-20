import hashlib
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import Connection, text

from ..db import Database
from ..errors import BusinessError
from ..history.repository import ResultRepository
from ..permissions.duties import IndependentDuties
from ..types import ObjectRef, ResultKey, Scope
from ..uploads.repository import UploadRepository
from .common import audit, canonical, match, row
from .providers import RuleProvider


class Reviews:
    def __init__(
        self,
        database: Database,
        receipts: UploadRepository,
        results: ResultRepository,
        rules: RuleProvider | None,
        duties: IndependentDuties | None = None,
    ) -> None:
        self.database, self.receipts, self.results, self.rules = database, receipts, results, rules
        self.duties = duties

    def context(self, connection: Connection, scope: Scope, task_id: UUID, *, lock: bool = False) -> dict[str, Any]:
        task = row(connection, "analysis_task", "task_id", task_id, lock)
        latest = (
            connection.execute(
                text(
                    "SELECT run_version,result_version,policy_version,sha256 FROM mt.task_result WHERE case_id=:case AND task_id=:task ORDER BY run_version DESC,result_version DESC LIMIT 1"
                ),
                dict(case=scope.case_id, task=task_id),
            )
            .mappings()
            .one_or_none()
        )
        if latest is None:
            raise BusinessError("RESULT_NOT_FOUND", 404)
        version = connection.execute(
            text("SELECT coalesce(max(review_version),0) FROM mt.review_record WHERE case_id=:case AND task_id=:task"),
            dict(case=scope.case_id, task=task_id),
        ).scalar_one()
        return dict(
            task_id=str(task_id),
            run_version=int(latest["run_version"]),
            result_version=int(latest["result_version"]),
            policy_version=latest["policy_version"],
            snapshot_sha256=latest["sha256"],
            object_version=int(task["row_version"]),
            review_version=int(version),
        )

    def wire(self, connection: Connection, identifier: UUID) -> dict[str, Any]:
        item = row(connection, "review_record", "review_id", identifier)
        ids = (
            connection.execute(
                text(
                    "SELECT evidence_id FROM mt.review_evidence WHERE case_id=:case AND review_id=:id ORDER BY evidence_id"
                ),
                dict(case=item["case_id"], id=identifier),
            )
            .scalars()
            .all()
        )
        return dict(
            review_id=str(identifier),
            reviewer_id=str(item["reviewer_id"]),
            task_id=str(item["task_id"]),
            run_version=int(item["run_version"]),
            result_version=int(item["result_version"]),
            expected_review_version=int(item["review_version"]) - 1,
            decision=item["decision"],
            reason=item["comments"],
            evidence_ids=[str(i) for i in ids],
            policy_version=item["policy_version"],
            review_version=int(item["review_version"]),
            created_at=item["created_at"].isoformat(),
        )

    def create(self, scope: Scope, body: dict[str, Any], request: Request, key: str) -> dict[str, Any]:
        if self.rules is None:
            raise BusinessError("REVIEW_RULE_UNAVAILABLE", 503)
        self.rules.review(scope, body["policy_version"], body["decision"])
        result_key = ResultKey(UUID(body["task_id"]), body["run_version"], body["result_version"])
        self.results.load_exact(scope, result_key)  # Recheck current sources and immutable input references.
        digest = hashlib.sha256(canonical(body)).hexdigest()
        with self.database.transaction(scope) as connection:
            context = self.context(connection, scope, result_key.task_id, lock=True)
            if self.duties is None:
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            task = row(connection, "analysis_task", "task_id", result_key.task_id)
            self.duties.review(scope, task, context, connection=connection)
            replay = self.receipts.replay(connection, scope, "createReview", key, digest)
            if replay is not None:
                return replay
            match(request, context)
            if (
                any(body[name] != context[name] for name in ["run_version", "result_version", "policy_version"])
                or body["expected_review_version"] != context["review_version"]
            ):
                raise BusinessError("REVIEW_VERSION_CONFLICT", 409)
            evidence_ids = sorted(UUID(v) for v in body["evidence_ids"])
            for identifier in evidence_ids:
                evidence = row(connection, "evidence_item", "evidence_id", identifier)
                if (evidence["case_id"], evidence["task_id"], evidence["run_version"], evidence["result_version"]) != (
                    scope.case_id,
                    result_key.task_id,
                    result_key.run_version,
                    result_key.result_version,
                ):
                    raise BusinessError("REVIEW_EVIDENCE_BINDING_INVALID", 422)
                asset = row(connection, "media_asset", "asset_id", evidence["asset_id"])
                if self.results.authority is None:
                    raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
                self.results.authority.authorize_source(scope, asset["source_id"], "analysis")
                source = row(connection, "source_registry", "source_id", asset["source_id"])
                if evidence["authorization_version"] != source["authorization_version"]:
                    raise BusinessError("REVIEW_EVIDENCE_AUTHORIZATION_STALE", 409)
                if evidence["object_id"] is not None:
                    fixed = row(connection, "object_version", "object_id", evidence["object_id"])
                    if fixed["sha256"] != evidence["sha256"]:
                        raise BusinessError("REVIEW_EVIDENCE_OBJECT_BINDING_INVALID", 409)
                    try:
                        for _ in self.results.store.read(
                            ObjectRef(fixed["object_id"], fixed["version_id"], fixed["sha256"])
                        ):
                            pass
                    except (OSError, ValueError, RuntimeError):
                        raise BusinessError("REVIEW_EVIDENCE_INTEGRITY_FAILED", 503) from None
            identifier, version = uuid4(), context["review_version"] + 1
            self.duties.review(scope, task, context, connection=connection)
            connection.execute(
                text("""INSERT INTO mt.review_record(review_id,org_id,case_id,task_id,run_version,result_version,reviewer_id,decision,comments,review_version,policy_version,created_by)
                VALUES(:id,:org,:case,:task_id,:run_version,:result_version,:actor,:decision,:reason,:version,:policy_version,:actor)"""),
                dict(
                    body,
                    id=identifier,
                    org=scope.actor.org_id,
                    case=scope.case_id,
                    actor=scope.actor.user_id,
                    version=version,
                ),
            )
            for evidence_id in evidence_ids:
                connection.execute(
                    text(
                        "INSERT INTO mt.review_evidence(link_id,org_id,case_id,review_id,evidence_id,created_by) VALUES(:id,:org,:case,:review,:evidence,:actor)"
                    ),
                    dict(
                        id=uuid4(),
                        org=scope.actor.org_id,
                        case=scope.case_id,
                        review=identifier,
                        evidence=evidence_id,
                        actor=scope.actor.user_id,
                    ),
                )
            value = self.wire(connection, identifier)
            self.receipts.remember(connection, scope, "createReview", key, digest, value)
            audit(connection, scope, "review.perform", "review", identifier, version, request)
            return value
