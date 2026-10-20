"""Real node leases and fencing; no empty or missing algorithm is marked successful."""

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import Connection, text

from ..auth import AuthorityProvider
from ..contracts import REGISTRY, SCHEMAS
from ..db import Database
from ..errors import BusinessError
from ..permissions.context import WorkPort, protected_work
from ..types import Scope
from .common import now, row


@dataclass(frozen=True)
class Lease:
    node_id: UUID
    token: str
    epoch: int
    task_id: UUID


class Execution:
    def __init__(
        self,
        database: Database,
        authority: AuthorityProvider | None,
        lease_seconds: int | None,
        work_authorization: WorkPort | None = None,
    ) -> None:
        if lease_seconds is not None and lease_seconds <= 0:
            raise ValueError("EXPLICIT_NODE_LEASE_REQUIRED")
        self.database, self.authority, self.lease_seconds = database, authority, lease_seconds
        self.work_authorization = work_authorization

    def authorize(self, scope: Scope, task_id: UUID) -> None:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        if self.authority.authorize_case(scope.actor, scope.case_id, "task.execute") != scope:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        with self.database.transaction(scope) as connection:
            source = connection.execute(
                text(
                    "SELECT a.source_id FROM mt.analysis_task t JOIN mt.media_asset a ON a.case_id=t.case_id AND a.asset_id=t.asset_id WHERE t.task_id=:id AND t.case_id=:case"
                ),
                dict(id=task_id, case=scope.case_id),
            ).scalar_one_or_none()
            if source is None:
                raise BusinessError("TASK_NOT_FOUND", 404)
            self.authority.authorize_source(scope, source, "analysis")

    def claim(self, scope: Scope, node_id: UUID, *, task_id: UUID | None = None) -> Lease:
        if self.lease_seconds is None:
            raise BusinessError("NODE_LEASE_UNCONFIRMED", 503)
        if self.work_authorization is None:
            raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
        if not isinstance(task_id, UUID) or task_id.int == 0:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        with protected_work(self.work_authorization, scope, "task_execution", task_id, "startTaskNodeWork"):
            return self._claim_bound(scope, node_id, task_id)

    def _claim_bound(self, scope: Scope, node_id: UUID, task_id: UUID) -> Lease:
        if self.lease_seconds is None:
            raise BusinessError("NODE_LEASE_UNCONFIRMED", 503)
        self.authorize(scope, task_id)
        with self.database.transaction(scope) as connection:
            task = row(connection, "analysis_task", "task_id", task_id, lock=True)
            item = row(connection, "task_node_run", "run_id", node_id, lock=True)
            if item["task_id"] != task_id:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            if (
                task["state"] in {"CANCEL_REQUESTED", "CANCELLED", "ARCHIVED", "FAILED", "SUCCEEDED"}
                or task["run_version"] != item["run_version"]
            ):
                raise BusinessError("TASK_EXECUTION_STATE_CONFLICT", 409)
            expired = (
                item["state"] == "RUNNING"
                and item["started_at"] is not None
                and item["started_at"] + timedelta(seconds=self.lease_seconds) <= now()
            )
            if item["state"] != "READY" and not expired:
                raise BusinessError("NODE_NOT_CLAIMABLE", 409)
            lease = Lease(node_id, uuid4().hex, int(item["fencing_epoch"]) + 1, task_id)
            connection.execute(
                text(
                    "UPDATE mt.task_node_run SET state='RUNNING',lease_token=:token,fencing_epoch=:epoch,started_at=now(),ended_at=NULL,reason=NULL,row_version=row_version+1,updated_at=now() WHERE run_id=:id AND case_id=:case"
                ),
                dict(token=lease.token, epoch=lease.epoch, id=node_id, case=scope.case_id),
            )
            return lease

    def finish_without_result(self, scope: Scope, lease: Lease, state: str, reason: str) -> None:
        if self.lease_seconds is None:
            raise BusinessError("NODE_LEASE_UNCONFIRMED", 503)
        if state not in {"FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED", "CANCELLED"} or not reason.strip():
            raise BusinessError("VERIFIED_NODE_RESULT_PRODUCER_REQUIRED", 503)
        task_id = lease.task_id
        if not isinstance(task_id, UUID) or task_id.int == 0:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        kind, operation = (
            ("task_cancellation", "cancelTaskWork")
            if state == "CANCELLED"
            else ("task_execution", "finishTaskNodeWork")
        )
        with protected_work(self.work_authorization, scope, kind, task_id, operation):
            self._finish_bound(scope, lease, state, reason, task_id)

    def _finish_bound(self, scope: Scope, lease: Lease, state: str, reason: str, task_id: UUID) -> None:
        if self.lease_seconds is None:
            raise BusinessError("NODE_LEASE_UNCONFIRMED", 503)
        if state == "CANCELLED":
            if (
                self.authority is None
                or self.authority.authorize_case(scope.actor, scope.case_id, "task.cancel") != scope
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        else:
            self.authorize(scope, task_id)
        with self.database.transaction(scope) as connection:
            task = row(connection, "analysis_task", "task_id", task_id, lock=True)
            item = row(connection, "task_node_run", "run_id", lease.node_id, lock=True)
            if item["task_id"] != task_id:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            if (
                item["state"] != "RUNNING"
                or item["lease_token"] != lease.token
                or item["fencing_epoch"] != lease.epoch
                or item["started_at"] is None
                or (
                    item["started_at"] + timedelta(seconds=self.lease_seconds) <= now()
                    and not (state == "CANCELLED" and task["state"] == "CANCEL_REQUESTED")
                )
            ):
                raise BusinessError("NODE_LEASE_STALE", 409)
            if task["run_version"] != item["run_version"] or (
                task["state"] in {"CANCEL_REQUESTED", "CANCELLED"} and state != "CANCELLED"
            ):
                raise BusinessError("TASK_EXECUTION_STATE_CONFLICT", 409)
            connection.execute(
                text(
                    "UPDATE mt.task_node_run SET state=:state,reason=:reason,ended_at=now(),lease_token=NULL,row_version=row_version+1,updated_at=now() WHERE run_id=:id AND case_id=:case"
                ),
                dict(state=state, reason=reason, id=lease.node_id, case=scope.case_id),
            )

    def status(self, connection: Connection, scope: Scope, task_id: UUID, *, lock: bool = False) -> dict[str, Any]:
        item = row(connection, "analysis_task", "task_id", task_id, lock)
        available = (
            connection.execute(
                text(
                    "SELECT 1 FROM mt.task_result WHERE case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result"
                ),
                dict(case=scope.case_id, task=task_id, run=item["run_version"], result=item["result_version"]),
            ).scalar_one_or_none()
            is not None
        )
        return dict(
            task_id=str(task_id),
            case_id=str(scope.case_id),
            state=item["state"],
            run_version=int(item["run_version"]),
            result_version=int(item["result_version"]),
            version=int(item["row_version"]),
            result_available=available,
        )

    def transition(
        self,
        connection: Connection,
        scope: Scope,
        task_id: UUID,
        version: int,
        before: str,
        after: str,
        request_id: UUID,
        reason: str,
    ) -> None:
        task = row(connection, "analysis_task", "task_id", task_id)
        run = (
            connection.execute(
                text("SELECT * FROM mt.task_run WHERE case_id=:case AND task_id=:task AND run_version=:run"),
                dict(case=scope.case_id, task=task_id, run=task["run_version"]),
            )
            .mappings()
            .one_or_none()
        )
        if run is None:
            raise BusinessError("TASK_RUN_NOT_FOUND", 404)
        identifier = uuid4()
        event = dict(
            schema_version="1.0.0",
            event_type="workflow.run.cancel_requested.v1"
            if after == "CANCEL_REQUESTED"
            else "workflow.run.cancelled.v1",
            event_id=str(identifier),
            occurred_at=now().isoformat(),
            request_id=str(request_id),
            producer_role="scheduler",
            binding=dict(
                org_id=str(scope.actor.org_id),
                case_id=str(scope.case_id),
                task_id=str(task_id),
                run_version=int(task["run_version"]),
                result_version=None,
                policy_version=run["policy_version"],
                dag_version=run["dag_version"],
            ),
            node_id=None,
            attempt=None,
            fencing_epoch=int(run["fencing_epoch"]),
            state=after,
            result_snapshot_ref=None,
            reason=reason,
        )
        Draft202012Validator(
            SCHEMAS["urn:media-trace:stage-one:domain-event:0.1.0"], registry=REGISTRY, format_checker=FormatChecker()
        ).validate(event)
        connection.execute(
            text(
                "INSERT INTO mt.task_event(event_id,org_id,case_id,task_id,run_version,from_state,to_state,reason,request_id,created_by) VALUES(:id,:org,:case,:task,:run,:before,:after,:reason,:request,:actor)"
            ),
            dict(
                id=identifier,
                org=scope.actor.org_id,
                case=scope.case_id,
                task=task_id,
                run=task["run_version"],
                before=before,
                after=after,
                reason=reason,
                request=request_id,
                actor=scope.actor.user_id,
            ),
        )
        connection.execute(
            text(
                "INSERT INTO mt.outbox_event(event_id,org_id,case_id,topic,aggregate_id,aggregate_version,payload,created_by) VALUES(:id,:org,:case,:topic,:task,:version,CAST(:payload AS jsonb),:actor)"
            ),
            dict(
                id=identifier,
                org=scope.actor.org_id,
                case=scope.case_id,
                topic=event["event_type"],
                task=task_id,
                version=version,
                payload=json.dumps(event),
                actor=scope.actor.user_id,
            ),
        )

    def reconcile_cancel(
        self, scope: Scope, task_id: UUID, run_version: int, expected_version: int, request_id: UUID
    ) -> bool:
        with protected_work(self.work_authorization, scope, "task_cancellation", task_id, "cancelTaskWork"):
            return self._reconcile_bound(scope, task_id, run_version, expected_version, request_id)

    def _reconcile_bound(
        self, scope: Scope, task_id: UUID, run_version: int, expected_version: int, request_id: UUID
    ) -> bool:
        if self.authority is None or self.authority.authorize_case(scope.actor, scope.case_id, "task.cancel") != scope:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        with self.database.transaction(scope) as connection:
            task = self.status(connection, scope, task_id, lock=True)
            if task["run_version"] != run_version:
                raise BusinessError("CANCEL_REQUEST_STALE", 409)
            if task["state"] == "CANCELLED" and task["version"] == expected_version + 1:
                return True
            if task["state"] != "CANCEL_REQUESTED" or task["version"] != expected_version:
                raise BusinessError("CANCEL_REQUEST_STALE", 409)
            nodes = (
                connection.execute(
                    text(
                        "SELECT run_id,state FROM mt.task_node_run WHERE case_id=:case AND task_id=:task AND run_version=:run FOR UPDATE"
                    ),
                    dict(case=scope.case_id, task=task_id, run=run_version),
                )
                .mappings()
                .all()
            )
            for node in nodes:
                if node["state"] in {"PENDING", "READY", "DEFERRED"}:
                    connection.execute(
                        text(
                            "UPDATE mt.task_node_run SET state='CANCELLED',reason='CANCELLED_BEFORE_EXECUTION',started_at=coalesce(started_at,now()),ended_at=now(),lease_token=NULL,row_version=row_version+1,updated_at=now() WHERE run_id=:id"
                        ),
                        dict(id=node["run_id"]),
                    )
            if any(node["state"] == "RUNNING" for node in nodes):
                return False
            connection.execute(
                text(
                    "UPDATE mt.analysis_task SET state='CANCELLED',row_version=row_version+1,updated_at=now() WHERE task_id=:id AND case_id=:case"
                ),
                dict(id=task_id, case=scope.case_id),
            )
            self.transition(
                connection,
                scope,
                task_id,
                expected_version + 1,
                "CANCEL_REQUESTED",
                "CANCELLED",
                request_id,
                "All registered nodes stopped; no algorithm result generated",
            )
            return True

    def nodes(self, scope: Scope, task_id: UUID, run_version: int) -> dict[str, Any]:
        with self.database.transaction(scope) as connection:
            if (
                connection.execute(
                    text("SELECT 1 FROM mt.task_run WHERE case_id=:case AND task_id=:task AND run_version=:run"),
                    dict(case=scope.case_id, task=task_id, run=run_version),
                ).scalar_one_or_none()
                is None
            ):
                raise BusinessError("TASK_RUN_NOT_FOUND", 404)
            items = (
                connection.execute(
                    text(
                        "SELECT * FROM mt.task_node_run WHERE case_id=:case AND task_id=:task AND run_version=:run ORDER BY node_code,attempt LIMIT 1001"
                    ),
                    dict(case=scope.case_id, task=task_id, run=run_version),
                )
                .mappings()
                .all()
            )
            if len(items) > 1000:
                raise BusinessError("NODE_READ_DEVELOPMENT_LIMIT_EXCEEDED", 503)
            return dict(
                task_id=str(task_id),
                run_version=run_version,
                items=[
                    dict(
                        node_id=str(v["run_id"]),
                        node_code=v["node_code"],
                        attempt=int(v["attempt"]),
                        state=v["state"],
                        required=v["required"],
                        reason=v["reason"],
                        version=int(v["row_version"]),
                        fencing_epoch=int(v["fencing_epoch"]),
                        started_at=v["started_at"].isoformat() if v["started_at"] else None,
                        ended_at=v["ended_at"].isoformat() if v["ended_at"] else None,
                    )
                    for v in items
                ],
            )
