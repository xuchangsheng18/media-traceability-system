"""RLS-backed object facts. Missing institutional facts remain unavailable."""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, replace
from datetime import datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import UUID

from sqlalchemy import Connection, text

from ..contracts import validate_api
from ..data_scope import LookupKey
from ..db import Database
from ..errors import BusinessError
from ..scope_lookup import SqlScopeLookup
from .policy import validate_principal
from .rule_types import ConditionFacts, ExecutionSubject, RuleTarget, WorkConditionFacts
from .types import Principal
from .work_subject import WORK_OPERATIONS, validate_execution_subject

if TYPE_CHECKING:
    from .work import WorkTrust

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
                "listPolicies": {"policy_collection", "policy"},
                "listApprovals": {"case", "approval"},
                "listSources": {"case", "source"},
                "listAuditEvents": {"case", "audit_event"},
                "getCurrentUser": {"user"},
                "getModelOperation": {"model_operation"},
                "listReviews": {"case", "review"},
                "listPendingReviews": {"case", "task"},
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
                    UUID(str(path["cluster_id" if operation_id == "getPropagation" else "id"])),
                    None,
                    None,
                    None,
                    None,
                    request_digest=binding,
                )
            located = SqlScopeLookup(self.database, clock=self.clock).read(
                principal, operation_id, LookupKey(raw.kind, cast(UUID, raw.object_id))
            )
            return replace(
                raw,
                case_id=located.target.case_id,
                object_version=located.target.object_version,
                purpose=raw.purpose or located.target.purpose,
                policy_kind=located.target.policy_kind,
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

    @staticmethod
    def review_candidates(
        connection: Connection, operation_id: str, org_id: UUID, case_id: UUID
    ) -> list[dict[str, Any]]:
        # Source status and RLS scope are applied before any page/count/cursor.
        # Trusted per-object read-purpose/classification is checked by the caller.
        if operation_id == "listReviews":
            projection = "r.review_id AS id,r.row_version"
            relation = "mt.review_record r JOIN mt.analysis_task t ON t.case_id=r.case_id AND t.org_id=r.org_id AND t.task_id=r.task_id"
            state = ""
        elif operation_id == "listPendingReviews":
            projection = "t.task_id AS id,t.row_version"
            relation = "mt.analysis_task t"
            state = " AND t.state IN ('WAIT_REVIEW','REVIEWING','RETURNED')"
        else:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        rows = (
            connection.execute(
                text(
                    f"SELECT {projection} FROM {relation} "
                    "JOIN mt.media_asset a ON a.case_id=t.case_id AND a.org_id=t.org_id AND a.asset_id=t.asset_id "
                    "JOIN mt.source_registry s ON s.case_id=a.case_id AND s.org_id=a.org_id AND s.source_id=a.source_id "
                    "WHERE t.case_id=:case AND t.org_id=:org AND s.authorization_status='verified' "
                    "AND (s.expires_at IS NULL OR s.expires_at>statement_timestamp())" + state + " FOR SHARE OF t,a,s"
                ),
                dict(case=case_id, org=org_id),
            )
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]

    def read(
        self, principal: Principal, operation_id: str, target: RuleTarget, *, connection: Connection | None = None
    ) -> ConditionFacts:
        validate_principal(principal, self.clock)
        value = self._read(principal, operation_id, target, connection=connection)
        if not isinstance(value, ConditionFacts):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        return value

    def read_for_work(
        self,
        subject: ExecutionSubject,
        operation_id: str,
        target: RuleTarget,
        *,
        connection: Connection | None = None,
        work_trust: WorkTrust | None = None,
    ) -> WorkConditionFacts:
        validate_execution_subject(subject)
        operation = WORK_OPERATIONS.get(operation_id)
        if operation is None or operation[2] != subject.work_kind or target.object_id != subject.work_id:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        value = self._read(subject, operation_id, target, connection=connection, work_trust=work_trust)
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
        work_trust: WorkTrust | None = None,
        envelopes: list[dict[str, Any]] | None = None,
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
        collection_leaf = (operation_id in CASE_LISTS and target.kind != "case") or (
            operation_id == "listPolicies" and target.kind == "policy"
        )
        if collection_leaf:
            from ..scope_collections import collection_metadata
            from ..scope_context import current_data_scope

            if connection is None or not isinstance(principal, Principal):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            envelopes = [collection_metadata(connection, current_data_scope(), principal, operation_id, target)]
        port = SqlScopeLookup(self.database, work_trust=work_trust, clock=self.clock)
        keys = (
            []
            if collection_leaf
            else [LookupKey("source", value) for value in sorted(target.source_ids, key=str)]
            if target.kind == "source_collection"
            else [LookupKey("user", principal.actor.user_id)]
            if target.kind in {"user", "policy_collection"}
            else [LookupKey("operation", cast(UUID, target.object_id))]
            if target.kind == "case"
            else [LookupKey(target.kind, cast(UUID, target.object_id))]
        )
        if connection is None:
            if len(keys) == 1:
                with port.connection(principal, operation_id, keys[0]) as current:
                    return self._read(
                        principal,
                        operation_id,
                        target,
                        connection=current,
                        work_trust=work_trust,
                        envelopes=[port.load(principal, operation_id, keys[0], connection=current)],
                    )
            collected = []
            for key in keys:
                with port.connection(principal, operation_id, key) as current:
                    collected.append(port.load(principal, operation_id, key, connection=current))
            with port.connection(principal, operation_id, keys[0]) as current:
                return self._read(
                    principal, operation_id, target, connection=current, work_trust=work_trust, envelopes=collected
                )
        if envelopes is None:
            envelopes = [port.load(principal, operation_id, key, connection=connection) for key in keys]

        def typed(value: Any) -> Any:
            if isinstance(value, list):
                return [typed(item) for item in value]
            if not isinstance(value, dict):
                return value
            return {
                key: UUID(item)
                if item is not None and (key.endswith("_id") or key in {"created_by", "requested_by"})
                else datetime.fromisoformat(item)
                if item is not None and key.endswith("_at")
                else typed(item)
                for key, item in value.items()
            }

        metadata = [typed(value) for value in envelopes]
        primary = metadata[0]
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
        checks["same_org"] = primary["same_org"]
        checks["self"] = target.kind == "user" and target.object_id == principal.actor.user_id
        item = primary["record"] if target.kind not in {"source_collection", "policy_collection", "user"} else {}
        if item:
            versions.append(item)
            if target.object_version is not None and item["row_version"] != target.object_version:
                raise BusinessError("AUTHORIZATION_OBJECT_STALE", 409)
            if target.policy_kind is not None and item.get("kind") != target.policy_kind:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
        case = item.get("case_id", target.case_id)
        if case is not None:
            if target.case_id is not None and case != target.case_id:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            memberships = primary["memberships"]
            if not memberships:
                raise BusinessError("RESOURCE_NOT_FOUND", 404)
            checks["case"] = True
            versions.extend(memberships)
            for membership in memberships:
                if membership["expires_at"] is not None:
                    deadline = min(deadline, membership["expires_at"].timestamp())
        checks["case"] = checks.get("case", False)
        checks["owner"] = item.get("requested_by", item.get("created_by")) == principal.actor.user_id
        if checks["owner"]:
            checks["control_authorized"] = True
            checks["own_or_delegated_request"] = True
        # Nonownership is definitive SQL evidence, but it does not disprove a
        # separate exact-object delegation. Only the trusted bound adapter may
        # supply these unresolved predicates; missing facts still mean unknown.
        checks["case_request_purpose"] = target.purpose in {
            "review",
            "seal",
            "report_export",
            "training_feedback",
            "confirmation",
        }
        checks["training_request"] = target.purpose == "training_feedback"
        checks["audit_request"] = target.purpose == "report_export" and target.kind == "operation"
        policy_header = operation_id == "listPolicies" and target.kind == "policy_collection"
        checks["policy_retention"] = target.policy_kind == "retention" or policy_header
        checks["policy_algorithm"] = target.policy_kind in {"threshold", "analysis"} or policy_header
        checks["policy_business"] = target.policy_kind in {"risk_taxonomy", "review"} or policy_header
        source_rows = {row["source_id"]: row for value in metadata for row in value["sources"]}
        sources = set(source_rows)
        if target.kind == "source_collection" and sources != set(target.source_ids):
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if any(value["record"].get("case_id") != case for value in metadata if target.kind == "source_collection"):
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        related = primary["related"]
        if target.kind == "import":
            if len(related) != item["requested_count"] or [v["ordinal"] for v in related] != list(range(len(related))):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
        if target.kind == "review" and len(related) != 1:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        versions.extend(related)
        purpose = (
            "import"
            if operation_id in {"createImport", "getImport"}
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
        # The collection entry checks case-level institutional scope only. Its
        # mandatory review_ids port separately evaluates every candidate before
        # the route constructs SQL pagination, including a valid empty result.
        collection = target.kind == "case" and operation_id in {"listReviews", "listPendingReviews"}
        source_ok = (bool(sources) or collection) and case is not None
        for source_id in sorted(sources, key=str):
            source = source_rows[source_id]
            if source["case_id"] != case or source["org_id"] != target.org_id:
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
            supplemental_port = getattr(self.supplemental, "read_for_work" if work else "read", None)
            if not callable(supplemental_port):
                raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
            extra = supplemental_port(principal, operation_id, target, connection=connection)
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
