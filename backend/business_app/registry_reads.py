"""Read existing report metadata with exact evidence and object-version bindings."""

from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from .contracts import validate_response
from .data_scope import TaskBinding
from .db import Database
from .errors import BusinessError
from .scope_collections import bind_task_scope, require_root
from .scope_context import current_data_scope
from .types import Scope


def project_report(
    item: dict[str, Any], evidence: list[dict[str, Any]], object_record: dict[str, Any] | None
) -> dict[str, Any]:
    """Project persisted facts only; incomplete references cannot become a success."""
    identity = ("org_id", "case_id", "task_id", "run_version", "result_version")
    if (
        not evidence
        or len({row["evidence_id"] for row in evidence}) != len(evidence)
        or any(any(row.get(key) != item[key] for key in identity) for row in evidence)
        or (item["state"] == "READY" and item["object_id"] is None)
    ):
        raise BusinessError("REPORT_METADATA_BINDING_INVALID", 503)
    reference = None
    if item["object_id"] is not None:
        if object_record is None or any(
            object_record.get(key) != item[key] for key in ("object_id", "org_id", "case_id")
        ):
            raise BusinessError("REPORT_METADATA_BINDING_INVALID", 503)
        reference = dict(
            object_id=str(object_record["object_id"]),
            version_id=object_record["version_id"],
            sha256=object_record["sha256"],
        )
    value = dict(
        report_id=str(item["report_id"]),
        case_id=str(item["case_id"]),
        task_id=str(item["task_id"]),
        run_version=int(item["run_version"]),
        result_version=int(item["result_version"]),
        version=int(item["version"]),
        state=item["state"],
        approval_id=str(item["approval_id"]) if item["approval_id"] is not None else None,
        object_ref=reference,
        evidence_ids=[str(row["evidence_id"]) for row in evidence],
        created_at=item["created_at"].isoformat(),
    )
    validate_response("Report", value)
    return value


class RegistryReads:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def report(connection: Connection, scope: Scope, identifier: UUID) -> dict[str, Any]:
        root = current_data_scope()
        authorization = require_root(connection, root)
        target = authorization.evidence.target
        if (
            root is None
            or root.operation_id != "getReport"
            or root.actor != scope.actor
            or root.case_id != scope.case_id
            or target.kind != "report"
            or target.object_id != identifier
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        params = dict(org=scope.actor.org_id, case=scope.case_id, id=identifier)
        item = (
            connection.execute(
                text("SELECT * FROM mt.report WHERE org_id=:org AND case_id=:case AND report_id=:id FOR SHARE"),
                params,
            )
            .mappings()
            .one_or_none()
        )
        if item is None:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        bind_task_scope(
            connection, root, TaskBinding(item["task_id"], int(item["run_version"]), int(item["result_version"]))
        )
        evidence = (
            connection.execute(
                text(
                    "SELECT e.evidence_id,e.org_id,e.case_id,e.task_id,e.run_version,e.result_version,e.asset_id "
                    "FROM mt.report_evidence r JOIN mt.evidence_item e "
                    "ON e.org_id=r.org_id AND e.case_id=r.case_id AND e.evidence_id=r.evidence_id "
                    "WHERE r.org_id=:org AND r.case_id=:case AND r.report_id=:id "
                    "ORDER BY e.evidence_id LIMIT 1001 /* registry_report_projection */"
                ),
                params,
            )
            .mappings()
            .all()
        )
        if len(evidence) > 1000:
            # Match the existing catalog node-read development resource bound.
            # This is an explicit development refusal, never a business evidence limit.
            raise BusinessError("REPORT_READ_DEVELOPMENT_LIMIT_EXCEEDED", 503)
        object_record = None
        if item["object_id"] is not None:
            object_record = (
                connection.execute(
                    text(
                        "SELECT object_id,org_id,case_id,version_id,sha256 FROM mt.object_version "
                        "WHERE org_id=:org AND case_id=:case AND object_id=:object"
                    ),
                    dict(params, object=item["object_id"]),
                )
                .mappings()
                .one_or_none()
            )
        return project_report(
            dict(item), [dict(row) for row in evidence], dict(object_record) if object_record else None
        )
