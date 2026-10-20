import hashlib
import json
from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import Connection, text

from ..auth import AuthorityProvider
from ..db import Database
from ..errors import BusinessError
from ..permissions.duties import IndependentDuties
from ..types import Scope
from ..uploads.repository import UploadRepository
from .common import audit, canonical, match, row
from .providers import RuleProvider


class Approvals:
    def __init__(
        self,
        database: Database,
        receipts: UploadRepository,
        rules: RuleProvider | None,
        authority: AuthorityProvider | None,
        duties: IndependentDuties | None = None,
    ) -> None:
        self.database, self.receipts, self.rules, self.authority = database, receipts, rules, authority
        self.duties = duties

    def require_duties(self) -> IndependentDuties:
        if self.duties is None:
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        return self.duties

    def bind(self, connection: Connection, scope: Scope, item: dict[str, Any]) -> None:
        targets = {
            "task": ("analysis_task", "task_id"),
            "report": ("report", "report_id"),
            "evidence_package": ("evidence_package", "package_id"),
            "feedback": ("feedback_request", "feedback_id"),
            "operation": ("cases", "case_id"),
        }
        if item["object_type"] not in targets:
            raise BusinessError("APPROVAL_OBJECT_ADAPTER_UNAVAILABLE", 503)
        if item["object_type"] == "operation" and (
            UUID(str(item["object_id"])) != scope.case_id or item["purpose"] != "report_export"
        ):
            raise BusinessError("APPROVAL_OBJECT_BINDING_INVALID", 422)
        table, key = targets[item["object_type"]]
        target = row(
            connection, table, key, UUID(str(item["object_id"])), lock=table in {"analysis_task", "cases", "report"}
        )
        if target["case_id"] != scope.case_id or int(target["row_version"]) != item["object_version"]:
            raise BusinessError("APPROVAL_OBJECT_STALE", 409)
        if item["object_type"] == "task":
            if self.authority is None:
                raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
            source_id = connection.execute(
                text("SELECT source_id FROM mt.media_asset WHERE case_id=:case AND asset_id=:asset"),
                dict(case=scope.case_id, asset=target["asset_id"]),
            ).scalar_one_or_none()
            if source_id is None:
                raise BusinessError("APPROVAL_SOURCE_INVALID", 409)
            try:
                self.authority.authorize_source(
                    scope, source_id, "training" if item["purpose"] == "training_feedback" else "analysis"
                )
            except BusinessError as error:
                if error.http_status != 403:
                    raise
                raise BusinessError("APPROVAL_SOURCE_INVALID", 409) from None
            exists = connection.execute(
                text(
                    "SELECT 1 FROM mt.task_result WHERE case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result AND policy_version=:policy"
                ),
                dict(
                    case=scope.case_id,
                    task=target["task_id"],
                    run=item["run_version"],
                    result=item["result_version"],
                    policy=item["policy_version"],
                ),
            ).scalar_one_or_none()
            latest = connection.execute(
                text(
                    "SELECT run_version,result_version FROM mt.task_result WHERE case_id=:case AND task_id=:task ORDER BY run_version DESC,result_version DESC LIMIT 1"
                ),
                dict(case=scope.case_id, task=target["task_id"]),
            ).one_or_none()
            if exists is None or latest is None or tuple(latest) != (item["run_version"], item["result_version"]):
                raise BusinessError("APPROVAL_RESULT_STALE", 409)

    def detail(self, connection: Connection, scope: Scope, identifier: UUID, *, lock: bool = False) -> dict[str, Any]:
        item = row(connection, "approval_request", "approval_id", identifier, lock)
        if item["case_id"] != scope.case_id:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        decisions = [
            dict(record)
            for record in (
                connection.execute(
                    text(
                        "SELECT * FROM mt.approval_decision WHERE case_id=:case AND approval_id=:id ORDER BY created_at,decision_id"
                    ),
                    dict(case=scope.case_id, id=identifier),
                )
                .mappings()
                .all()
            )
        ]
        state = item["state"]
        duties = self.require_duties()
        facts = duties.collect(scope, item, decisions, connection=connection)
        if self.rules is None:
            raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)
        current_rule = self.rules.approval(scope, item["purpose"], item["policy_version"])
        duties._rule(current_rule)
        if current_rule.version != item["policy_version"]:
            raise BusinessError("APPROVAL_RULE_VERSION_INVALID", 503)
        try:
            duties.validate_records(facts, decisions)
        except BusinessError as error:
            if error.http_status != 403:
                raise
            state = "INVALIDATED"
        if state == "APPROVED":
            if self.rules is None:
                raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)
            rule = self.rules.approval(scope, item["purpose"], item["policy_version"])
            actors = {
                d["decision_actor_id"]
                for d in decisions
                if d["decision"] == "approve" and d["decision_actor_id"] != item["requested_by"]
            }
            if (
                rule.version != item["policy_version"]
                or len(actors) < rule.independent_approvers
                or any(d["decision"] in {"reject", "return", "revoke", "invalidate"} for d in decisions)
            ):
                state = "INVALIDATED"
            if state == "APPROVED":
                try:
                    duties.validate_approval(facts, rule)
                except BusinessError as error:
                    if error.http_status != 403:
                        raise
                    state = "INVALIDATED"
        if state in {"REQUESTED", "APPROVED"}:
            if not duties.approval_live(item["created_at"], item["expires_at"], current_rule):
                state = "EXPIRED"
            else:
                try:
                    self.bind(connection, scope, item)
                except BusinessError as error:
                    if error.http_status not in {404, 409}:
                        raise
                    state = "INVALIDATED"
        value = dict(
            approval_id=str(identifier),
            state=state,
            version=int(item["row_version"]),
            object_version=int(item["object_version"]),
            purpose=item["purpose"],
            policy_version=item["policy_version"],
            expires_at=item["expires_at"].isoformat() if item["expires_at"] else None,
            decision_actor_id=str(decisions[-1]["decision_actor_id"]) if decisions else None,
            run_version=item["run_version"],
            result_version=item["result_version"],
        )
        return dict(
            approval=value,
            binding=dict(
                case_id=str(scope.case_id),
                object_type=item["object_type"],
                object_id=str(item["object_id"]),
                requested_by=str(item["requested_by"]),
            ),
            decisions=[
                dict(
                    decision_id=str(d["decision_id"]),
                    decision=d["decision"],
                    actor_id=str(d["decision_actor_id"]),
                    reason=d["reason"],
                    evidence_ids=d["evidence_refs"].get("evidence_ids", []),
                    created_at=d["created_at"].isoformat(),
                )
                for d in decisions
            ],
        )

    def create(self, scope: Scope, body: dict[str, Any], request: Request, key: str) -> dict[str, Any]:
        if self.rules is None:
            raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)
        rule = self.rules.approval(scope, body["purpose"], body["policy_version"])
        if rule.version != body["policy_version"]:
            raise BusinessError("APPROVAL_RULE_VERSION_INVALID", 503)
        duties = self.require_duties()
        duties._rule(rule)
        digest = hashlib.sha256(canonical(body)).hexdigest()
        with self.database.transaction(scope) as connection:
            duties.collect(scope, dict(body, requested_by=scope.actor.user_id), [], connection=connection)
            self.bind(connection, scope, body)
            old = self.receipts.replay(connection, scope, "requestApproval", key, digest)
            if old is not None:
                return old
            identifier = uuid4()
            connection.execute(
                text("""INSERT INTO mt.approval_request(approval_id,org_id,case_id,object_type,object_id,object_version,purpose,policy_version,requested_by,state,expires_at,reason,run_version,result_version,created_by)
                VALUES(:id,:org,:case,:object_type,:object_id,:object_version,:purpose,:policy_version,:actor,'REQUESTED',now()+(:ttl * interval '1 second'),:reason,:run_version,:result_version,:actor)"""),
                dict(
                    body,
                    id=identifier,
                    org=scope.actor.org_id,
                    case=scope.case_id,
                    actor=scope.actor.user_id,
                    ttl=rule.ttl_seconds,
                ),
            )
            result = self.detail(connection, scope, identifier)
            self.receipts.remember(connection, scope, "requestApproval", key, digest, result)
            audit(connection, scope, "approval.request", "approval", identifier, 1, request)
            return result

    def decide(
        self, scope: Scope, identifier: UUID, body: dict[str, Any], request: Request, key: str, *, revoke: bool = False
    ) -> dict[str, Any]:
        operation = "revokeApproval" if revoke else "decideApproval"
        digest = hashlib.sha256(canonical([str(identifier), body])).hexdigest()
        with self.database.transaction(scope) as connection:
            current = self.detail(connection, scope, identifier, lock=True)
            old = self.receipts.replay(connection, scope, operation, key, digest)
            if old is not None:
                return old
            match(request, current)
            if body["expected_version"] != current["approval"]["version"]:
                raise BusinessError("APPROVAL_VERSION_CONFLICT", 409)
            state = current["approval"]["state"]
            if self.rules is None:
                raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)
            rule = self.rules.approval(scope, current["approval"]["purpose"], current["approval"]["policy_version"])
            if rule.version != current["approval"]["policy_version"]:
                raise BusinessError("APPROVAL_RULE_VERSION_INVALID", 503)
            duties = self.require_duties()
            raw = row(connection, "approval_request", "approval_id", identifier)
            records = [
                dict(record)
                for record in (
                    connection.execute(
                        text(
                            "SELECT * FROM mt.approval_decision WHERE case_id=:case AND approval_id=:id ORDER BY created_at,decision_id"
                        ),
                        dict(case=scope.case_id, id=identifier),
                    )
                    .mappings()
                    .all()
                )
            ]
            facts = duties.collect(scope, raw, records, connection=connection, extra_actors=frozenset({scope.actor}))
            if revoke:
                if state not in {"REQUESTED", "APPROVED", "RETURNED"}:
                    raise BusinessError("APPROVAL_STATE_CONFLICT", 409)
                decision, target = "revoke", "REVOKED"
            else:
                if state != "REQUESTED":
                    raise BusinessError("APPROVAL_STATE_CONFLICT", 409)
                if current["binding"]["requested_by"] == str(scope.actor.user_id):
                    raise BusinessError("INDEPENDENT_APPROVER_REQUIRED", 403)
                if any(d["actor_id"] == str(scope.actor.user_id) for d in current["decisions"]):
                    raise BusinessError("APPROVER_ALREADY_DECIDED", 409)
                person_id = duties.candidate(scope.actor, facts)
                decision = body["decision"]
                target = {"reject": "REJECTED", "return": "RETURNED", "approve": "REQUESTED"}[decision]
                if decision == "approve" and len(facts.approved_people | {person_id}) >= rule.independent_approvers:
                    duties.validate_approval(replace(facts, approved_people=facts.approved_people | {person_id}), rule)
                    target = "APPROVED"
            for evidence_id in body.get("evidence_ids", []):
                evidence = row(connection, "evidence_item", "evidence_id", UUID(evidence_id))
                if evidence["case_id"] != scope.case_id:
                    raise BusinessError("EVIDENCE_BINDING_INVALID", 422)
                if current["binding"]["object_type"] == "task" and (
                    str(evidence["task_id"]),
                    evidence["run_version"],
                    evidence["result_version"],
                ) != (
                    current["binding"]["object_id"],
                    current["approval"]["run_version"],
                    current["approval"]["result_version"],
                ):
                    raise BusinessError("EVIDENCE_BINDING_INVALID", 422)
            connection.execute(
                text("""INSERT INTO mt.approval_decision(decision_id,org_id,case_id,approval_id,decision,decision_actor_id,reason,evidence_refs,policy_version,created_by)
                VALUES(:id,:org,:case,:approval,:decision,:actor,:reason,CAST(:evidence AS jsonb),:policy,:actor)"""),
                dict(
                    id=uuid4(),
                    org=scope.actor.org_id,
                    case=scope.case_id,
                    approval=identifier,
                    decision=decision,
                    actor=scope.actor.user_id,
                    reason=body["reason"],
                    evidence=json.dumps(
                        dict(
                            evidence_ids=body.get("evidence_ids", []),
                            independence=duties.decision_proof(scope.actor, facts),
                        )
                    ),
                    policy=rule.version,
                ),
            )
            connection.execute(
                text(
                    "UPDATE mt.approval_request SET state=:state,row_version=row_version+1,updated_at=now() WHERE approval_id=:id AND case_id=:case"
                ),
                dict(state=target, id=identifier, case=scope.case_id),
            )
            result = self.detail(connection, scope, identifier)
            self.receipts.remember(connection, scope, operation, key, digest, result)
            audit(
                connection,
                scope,
                "approval.revoke" if revoke else "approval.decide",
                "approval",
                identifier,
                result["approval"]["version"],
                request,
            )
            return result
