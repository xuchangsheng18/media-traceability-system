"""RLS-backed object facts. Missing institutional facts remain unavailable."""

import hashlib
import json
import math
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, replace
from types import MappingProxyType
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import Connection, text

from ..contracts import validate_api
from ..db import Database
from ..errors import BusinessError
from .policy import validate_principal
from .rule_types import ConditionFacts, ExecutionSubject, RuleTarget, WorkConditionFacts
from .types import Principal
from .work_subject import WORK_OPERATIONS, validate_execution_subject

# Fixed server-controlled identifiers only; never interpolate an HTTP table name.
RESOURCES = MappingProxyType(
    {
        "approval": ("approval_request", "approval_id"),
        "review": ("review_record", "review_id"),
        "export": ("audit_export", "export_id"),
        "feedback": ("feedback_request", "feedback_id"),
        "source": ("source_registry", "source_id"),
        "import": ("import_job", "import_id"),
        "task": ("analysis_task", "task_id"),
        "asset": ("media_asset", "asset_id"),
        "cluster": ("content_cluster", "cluster_id"),
        "upload": ("upload_session", "upload_id"),
        "policy": ("policy_registry", "policy_id"),
        "report": ("report", "report_id"),
        "evidence_package": ("evidence_package", "package_id"),
        "operation": ("cases", "case_id"),
    }
)
OPERATION_KINDS = MappingProxyType(
    {
        **dict.fromkeys(("decideApproval", "getApproval", "revokeApproval"), "approval"),
        "getImport": "import",
        "getTimeline": "asset",
        **dict.fromkeys(("completeUpload", "getUploadStatus", "listUploadParts", "putUploadPart"), "upload"),
        **dict.fromkeys(("downloadAuditExport", "getAuditExport"), "export"),
        **dict.fromkeys(
            (
                "getTaskEvidence",
                "getReviewContext",
                "cancelTask",
                "getForensics",
                "getRiskFindings",
                "getTask",
                "getTaskExecution",
                "listTaskEvents",
                "listTaskNodes",
            ),
            "task",
        ),
        "getFeedback": "feedback",
        "getFirstSource": "cluster",
        "getPropagation": "cluster",
        **dict.fromkeys(("getPolicy", "getPolicyDefinition"), "policy"),
        "getReview": "review",
        "syncSourceAuthorization": "source",
        "getSource": "source",
    }
)
CASE_LISTS = frozenset({"listApprovals", "listAuditEvents", "listPendingReviews", "listReviews", "listSources"})
BODY_SCHEMAS = MappingProxyType(
    {
        "createUpload": "UploadCreate",
        "createImport": "ImportRequest",
        "requestApproval": "ApprovalCreate",
        "createReview": "ReviewCreate",
        "exportAudit": "AuditExport",
        "createPolicy": "PolicyCreate",
        "decideApproval": "ApprovalDecision",
        "revokeApproval": "ApprovalRevoke",
        "cancelTask": "TaskAction",
        "completeUpload": "UploadComplete",
    }
)
SUPPORTED_OPERATIONS = (
    frozenset(OPERATION_KINDS)
    | CASE_LISTS
    | frozenset(
        {
            "createUpload",
            "createImport",
            "requestApproval",
            "createReview",
            "exportAudit",
            "createPolicy",
            "getCurrentUser",
            "getModelOperation",
            "listPolicies",
        }
    )
)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class SupplementalFacts(Protocol):
    """Trusted institutional adapter, never a dictionary supplied by the client."""

    def read(
        self, principal: Principal, operation_id: str, target: RuleTarget, *, connection: Connection
    ) -> ConditionFacts: ...


class ObjectFactsReader:
    supported_operation_ids = SUPPORTED_OPERATIONS

    def __init__(
        self,
        database: Database,
        *,
        clock: Callable[[], float] = time.time,
        supplemental: SupplementalFacts | None = None,
    ) -> None:
        self.database, self.clock, self.supplemental = database, clock, supplemental

    @staticmethod
    def _validate_target(operation_id: str, target: RuleTarget) -> None:
        expected = (
            {WORK_OPERATIONS[operation_id][1]}
            if operation_id in WORK_OPERATIONS
            else {OPERATION_KINDS[operation_id]}
            if operation_id in OPERATION_KINDS
            else {
                "createUpload": {"source"},
                "createImport": {"source_collection"},
                "requestApproval": {"task", "report", "evidence_package", "feedback", "model_release", "operation"},
                "createReview": {"task"},
                "exportAudit": {"approval"},
                "createPolicy": {"policy_collection"},
                "listPolicies": {"policy_collection"},
                "getCurrentUser": {"user"},
                "getModelOperation": {"model_operation"},
            }.get(operation_id, {"case"} if operation_id in CASE_LISTS else set())
        )
        if (
            not isinstance(target, RuleTarget)
            or not isinstance(target.org_id, UUID)
            or target.kind not in expected
            or (target.object_id is not None and not isinstance(target.object_id, UUID))
            or (target.case_id is not None and not isinstance(target.case_id, UUID))
            or (
                target.object_version is not None
                and (type(target.object_version) is not int or target.object_version < 1)
            )
            or type(target.source_ids) is not tuple
            or any(not isinstance(v, UUID) for v in target.source_ids)
            or len(set(target.source_ids)) != len(target.source_ids)
            or (
                target.request_digest is not None
                and (
                    not isinstance(target.request_digest, str)
                    or re.fullmatch(r"[0-9a-f]{64}", target.request_digest) is None
                )
            )
            or (target.policy_kind is not None and target.kind not in {"policy", "policy_collection"})
        ):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if target.kind == "policy_collection":
            if (
                target.object_id is not None
                or target.object_version is not None
                or target.case_id is not None
                or target.purpose is not None
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            if operation_id == "createPolicy" and target.policy_kind not in {
                "retention",
                "threshold",
                "analysis",
                "risk_taxonomy",
                "review",
            }:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            if operation_id == "listPolicies" and target.policy_kind is not None:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        elif target.kind == "source_collection":
            if (
                target.object_id is not None
                or target.case_id is None
                or not target.source_ids
                or target.purpose != "import"
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        elif target.object_id is None or (target.kind == "case" and target.object_id != target.case_id):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)

    def resolve_http(
        self,
        principal: Principal,
        operation_id: str,
        path: Mapping[str, Any],
        query: Mapping[str, Any],
        body: Mapping[str, Any],
    ) -> RuleTarget:
        if operation_id not in SUPPORTED_OPERATIONS:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if operation_id in BODY_SCHEMAS:
            validate_api(BODY_SCHEMAS[operation_id], dict(body))
        try:
            org = principal.actor.org_id
            binding = digest(dict(path=dict(path), query=dict(query), body=dict(body)))
            if operation_id == "getCurrentUser":
                return RuleTarget(org, "user", principal.actor.user_id, None, None, None, None, request_digest=binding)
            if operation_id == "getModelOperation":
                # The deployment operation provider owns operation->release resolution. There is
                # no authority adapter for the proposed rule yet; do not treat an operation id as a release id.
                return RuleTarget(
                    org, "model_operation", UUID(str(path["id"])), None, None, None, None, request_digest=binding
                )
            if operation_id in {"createPolicy", "listPolicies"}:
                return RuleTarget(
                    org, "policy_collection", None, None, None, None, body.get("kind"), request_digest=binding
                )
            if operation_id in CASE_LISTS:
                case = UUID(str(query["case_id"]))
                return RuleTarget(org, "case", case, None, case, None, None, request_digest=binding)
            if operation_id == "createUpload":
                return RuleTarget(
                    org,
                    "source",
                    UUID(str(body["source_id"])),
                    None,
                    UUID(str(body["case_id"])),
                    "upload",
                    None,
                    request_digest=binding,
                )
            if operation_id == "createImport":
                sources = tuple(sorted({UUID(str(item["source_id"])) for item in body["entries"]}, key=str))
                return RuleTarget(
                    org,
                    "source_collection",
                    None,
                    None,
                    UUID(str(body["case_id"])),
                    "import",
                    None,
                    source_ids=sources,
                    request_digest=binding,
                )
            if operation_id == "requestApproval":
                return RuleTarget(
                    org,
                    str(body["object_type"]),
                    UUID(str(body["object_id"])),
                    body["object_version"],
                    UUID(str(body["case_id"])) if body["case_id"] else None,
                    str(body["purpose"]),
                    None,
                    request_digest=binding,
                )
            if operation_id == "createReview":
                raw = RuleTarget(
                    org, "task", UUID(str(body["task_id"])), None, None, "review", None, request_digest=binding
                )
            elif operation_id == "exportAudit":
                if body["case_id"] is None:
                    raise BusinessError("ORGANIZATION_AUDIT_EXPORT_UNAVAILABLE", 503)
                raw = RuleTarget(
                    org,
                    "approval",
                    UUID(str(body["approval_id"])),
                    None,
                    UUID(str(body["case_id"])),
                    "report_export",
                    None,
                    request_digest=binding,
                )
            else:
                raw = RuleTarget(
                    org,
                    OPERATION_KINDS[operation_id],
                    UUID(str(path["id"])),
                    None,
                    None,
                    None,
                    None,
                    request_digest=binding,
                )
            with self.database.identity_transaction(principal.actor) as connection:
                item = self._object(connection, raw)
                return replace(
                    raw,
                    case_id=item.get("case_id"),
                    object_version=int(item["row_version"]),
                    purpose=raw.purpose or item.get("purpose") if isinstance(item.get("purpose"), str) else raw.purpose,
                    policy_kind=item.get("kind") if raw.kind == "policy" else None,
                )
        except (KeyError, TypeError, ValueError, AttributeError):
            raise BusinessError("INPUT_INVALID", 422) from None

    @staticmethod
    def _object(connection: Connection, target: RuleTarget, *, lock: bool = False) -> dict[str, Any]:
        pair = RESOURCES.get(target.kind)
        if pair is None or target.object_id is None:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        table, key = pair
        # Append-only tables have database UPDATE/DELETE/TRUNCATE rejection and no
        # runtime UPDATE privilege. Other rows retain a share lock through the fence.
        locking = lock and table not in {"review_record", "evidence_package"}
        item = (
            connection.execute(
                text(f"SELECT * FROM mt.{table} WHERE {key}=:id AND org_id=:org" + (" FOR SHARE" if locking else "")),
                dict(id=target.object_id, org=target.org_id),
            )
            .mappings()
            .one_or_none()
        )
        if item is None:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if target.case_id is not None and item.get("case_id") != target.case_id:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if target.object_version is not None and item["row_version"] != target.object_version:
            raise BusinessError("AUTHORIZATION_OBJECT_STALE", 409)
        if target.policy_kind is not None and item.get("kind") != target.policy_kind:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        return dict(item)

    def read(
        self, principal: Principal, operation_id: str, target: RuleTarget, *, connection: Connection | None = None
    ) -> ConditionFacts:
        validate_principal(principal, self.clock)
        value = self._read(principal, operation_id, target, connection=connection)
        if not isinstance(value, ConditionFacts):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        return value

    def read_for_work(
        self, subject: ExecutionSubject, operation_id: str, target: RuleTarget, *, connection: Connection | None = None
    ) -> WorkConditionFacts:
        validate_execution_subject(subject)
        operation = WORK_OPERATIONS.get(operation_id)
        if operation is None or operation[2] != subject.work_kind or target.object_id != subject.work_id:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        value = self._read(subject, operation_id, target, connection=connection)
        if not isinstance(value, WorkConditionFacts):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        return value

    def _read(
        self,
        principal: Principal | ExecutionSubject,
        operation_id: str,
        target: RuleTarget,
        *,
        connection: Connection | None = None,
    ) -> ConditionFacts | WorkConditionFacts:
        self._validate_target(operation_id, target)
        work = isinstance(principal, ExecutionSubject)
        if (
            operation_id not in (WORK_OPERATIONS if work else SUPPORTED_OPERATIONS)
            or target.org_id != principal.actor.org_id
        ):
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if target.kind == "model_release":
            raise BusinessError("ORGANIZATION_APPROVAL_ADAPTER_UNAVAILABLE", 503)
        if target.kind == "model_operation":
            raise BusinessError("MODEL_RULE_ADAPTER_UNAVAILABLE", 503)
        if connection is None:
            with self.database.identity_transaction(principal.actor) as current:
                return self._read(principal, operation_id, target, connection=current)
        actor_binding = connection.execute(text("SELECT mt.actor_id(),mt.org_id()")).one()
        if tuple(actor_binding) != (principal.actor.user_id, principal.actor.org_id):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        checks: dict[str, bool | None] = {}
        versions: list[object] = [asdict(target)]
        current_time = self.clock()
        if type(current_time) not in (float, int) or not math.isfinite(current_time):
            raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        deadline = (
            min(float(principal.expires_at), float(current_time) + 5)
            if isinstance(principal, Principal)
            else float(current_time) + 5
        )
        in_org = connection.execute(text("SELECT mt.actor_in_org()")).scalar_one()
        checks["same_org"] = bool(in_org)
        checks["self"] = target.kind == "user" and target.object_id == principal.actor.user_id
        if target.kind == "user" and not checks["self"]:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        item: dict[str, Any] = {}
        if target.kind in RESOURCES:
            item = self._object(connection, target, lock=True)
            versions.append(item)
        case = item.get("case_id", target.case_id)
        if case is not None:
            if target.case_id is not None and case != target.case_id:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            memberships = (
                connection.execute(
                    text(
                        "SELECT m.membership_id,m.row_version,m.expires_at,c.row_version AS case_version,c.status FROM mt.case_membership m JOIN mt.cases c ON c.case_id=m.case_id AND c.org_id=m.org_id WHERE m.case_id=:case AND m.org_id=:org AND m.user_id=:user AND m.revoked_at IS NULL AND (m.expires_at IS NULL OR m.expires_at>statement_timestamp())"
                    ),
                    dict(case=case, org=target.org_id, user=principal.actor.user_id),
                )
                .mappings()
                .all()
            )
            if (
                not memberships
                or not connection.execute(text("SELECT mt.can_access_case(:case)"), dict(case=case)).scalar_one()
            ):
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            checks["case"] = True
            versions.extend(dict(v) for v in memberships)
            for membership in memberships:
                if membership["expires_at"] is not None:
                    deadline = min(deadline, membership["expires_at"].timestamp())
        checks["case"] = checks.get("case", False)
        checks["owner"] = item.get("requested_by", item.get("created_by")) == principal.actor.user_id
        checks["control_authorized"] = True if checks["owner"] else None
        checks["own_or_delegated_request"] = True if checks["owner"] else None
        checks["case_request_purpose"] = target.purpose in {
            "review",
            "seal",
            "report_export",
            "training_feedback",
            "confirmation",
        }
        checks["training_request"] = target.purpose == "training_feedback"
        checks["audit_request"] = target.purpose == "report_export" and target.kind == "operation"
        checks["policy_retention"] = target.policy_kind == "retention" or operation_id == "listPolicies"
        checks["policy_algorithm"] = target.policy_kind in {"threshold", "analysis"} or operation_id == "listPolicies"
        checks["policy_business"] = target.policy_kind in {"risk_taxonomy", "review"} or operation_id == "listPolicies"
        sources = set(target.source_ids)
        if target.kind == "source" and target.object_id is not None:
            sources.add(target.object_id)
        elif item.get("source_id"):
            sources.add(item["source_id"])
        elif item.get("asset_id"):
            source_id = connection.execute(
                text("SELECT source_id FROM mt.media_asset WHERE case_id=:case AND asset_id=:asset FOR SHARE"),
                dict(case=case, asset=item["asset_id"]),
            ).scalar_one_or_none()
            if source_id:
                sources.add(source_id)
        purpose = (
            "import"
            if operation_id == "createImport"
            else "upload"
            if operation_id
            in {
                "createUpload",
                "completeUpload",
                "getUploadStatus",
                "listUploadParts",
                "putUploadPart",
                "validateUploadWork",
            }
            else "analysis"
            if isinstance(principal, ExecutionSubject) and principal.work_kind == "task_execution"
            else "training"
            if target.purpose == "training_feedback"
            else None
        )
        source_ok = bool(sources) and case is not None
        for source_id in sorted(sources, key=str):
            source = (
                connection.execute(
                    text(
                        "SELECT source_id,org_id,case_id,authorization_status,authorization_version,purpose,expires_at,row_version FROM mt.source_registry WHERE source_id=:id AND case_id=:case AND org_id=:org FOR SHARE"
                    ),
                    dict(id=source_id, case=case, org=target.org_id),
                )
                .mappings()
                .one_or_none()
            )
            if source is None:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            versions.append(dict(source))
            expires = source["expires_at"]
            source_ok = (
                source_ok
                and source["authorization_status"] == "verified"
                and (expires is None or expires.timestamp() > current_time)
            )
            if expires is not None:
                deadline = min(deadline, expires.timestamp())
            if purpose is not None:
                source_ok = source_ok and purpose in source["purpose"]
        checks["source"] = source_ok
        checks["source_purpose"] = source_ok if purpose is not None else None
        checks["analysis_purpose"] = source_ok if purpose == "analysis" else None
        # Classification, reads/downloads, human duty/person and audit delegation do
        # not exist in the present SQL schema. They cannot be inferred from a role.
        if self.supplemental is not None:
            port = getattr(self.supplemental, "read_for_work" if work else "read", None)
            if not callable(port):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            extra = port(principal, operation_id, target, connection=connection)
            if (
                not isinstance(extra, WorkConditionFacts if work else ConditionFacts)
                or (extra.subject if isinstance(extra, WorkConditionFacts) else extra.principal) != principal
                or extra.target != target
                or type(extra.valid_until) not in (int, float)
                or not math.isfinite(extra.valid_until)
                or extra.valid_until <= current_time
                or not isinstance(extra.version_digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", extra.version_digest) is None
                or not isinstance(extra.checks, Mapping)
            ):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            for name, value in extra.checks.items():
                if not isinstance(name, str) or name in checks or (value is not None and type(value) is not bool):
                    raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
                checks[name] = value
            versions.append(extra.version_digest)
            deadline = min(deadline, extra.valid_until)
        if isinstance(principal, ExecutionSubject):
            return WorkConditionFacts(principal, target, MappingProxyType(checks), digest(versions), deadline)
        return ConditionFacts(principal, target, MappingProxyType(checks), digest(versions), deadline)
