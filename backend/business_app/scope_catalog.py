"""Fixed metadata projections and table semantics; no query or ALLOW decision."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from .errors import BusinessError


@dataclass(frozen=True)
class LookupSpec:
    table: str
    key: str
    projection: tuple[str, ...]
    operation_ids: frozenset[str]


@dataclass(frozen=True)
class TableScopeRule:
    table: str
    scope_class: Literal["CASE", "ORG", "DIRECTORY", "MIXED", "INTERNAL"]
    runtime_select: bool
    lookup_kinds: tuple[str, ...]


# Only columns needed to establish a target or its SQL authorization facts.
# Object payloads, paths, output snapshots and credentials never belong here.
_RESOURCES = MappingProxyType(
    {
        "approval": (
            "approval_request",
            "approval_id",
            (
                "object_type",
                "object_id",
                "object_version",
                "purpose",
                "requested_by",
                "state",
                "expires_at",
                "policy_version",
                "run_version",
                "result_version",
            ),
        ),
        "review": (
            "review_record",
            "review_id",
            ("task_id", "run_version", "result_version", "reviewer_id", "review_version", "policy_version"),
        ),
        "export": ("audit_export", "export_id", ("approval_id", "purpose", "state", "start_at", "end_at")),
        "feedback": (
            "feedback_request",
            "feedback_id",
            ("finding_id", "approval_id", "purpose", "state", "label_version"),
        ),
        "source": (
            "source_registry",
            "source_id",
            ("authorization_status", "authorization_version", "purpose", "expires_at"),
        ),
        "import": ("import_job", "import_id", ("state", "requested_count")),
        "task": ("analysis_task", "task_id", ("asset_id", "run_version", "result_version", "state", "policy_version")),
        "asset": ("media_asset", "asset_id", ("source_id", "parent_asset_id", "mapping_version", "state")),
        "model": (
            "model_registry",
            "model_id",
            (
                "name",
                "version",
                "capability",
                "digest",
                "dataset_version",
                "model_card_ref",
                "license_record_ref",
                "backend",
                "environment_ref",
                "status",
            ),
        ),
        "model_evaluation": (
            "model_evaluation",
            "evaluation_id",
            (
                "model_id",
                "dataset_id",
                "dataset_version",
                "protocol_id",
                "split",
                "sample_count",
                "failure_count",
                "artifact_ref",
            ),
        ),
        "cluster": ("content_cluster", "cluster_id", ("scope", "policy_version", "status")),
        "upload": ("upload_session", "upload_id", ("source_id", "owner_id", "asset_id", "state", "expires_at")),
        "policy": ("policy_registry", "policy_id", ("kind", "version", "status", "approval_id")),
        "report": (
            "report",
            "report_id",
            ("task_id", "run_version", "result_version", "version", "approval_id", "state"),
        ),
        "evidence_package": (
            "evidence_package",
            "package_id",
            ("task_id", "run_version", "result_version", "version", "approval_id", "state"),
        ),
        "operation": ("cases", "case_id", ("status",)),
        "user": ("users", "user_id", ("enabled",)),
    }
)
LOOKUP_KINDS = frozenset(_RESOURCES)
RESOURCE_BINDING_KINDS = LOOKUP_KINDS | frozenset(
    {
        "case",
        "audit_event",
        "upload_part",
        "media_input",
        "history_input",
        "asset_content",
        "export_artifact",
        "model_artifact",
    }
)
# Fixed action root for a separately authorized consumer. This is not an HTTP
# implementation or a role grant; no consumer route is mounted by this catalog.
INTERNAL_CONSUMER_OPERATIONS = frozenset({"sealEvidence"})


def registered_operation(identifier: str) -> bool:
    # Local imports keep this pure catalog usable while Database and the existing
    # object-fact reader import each other. They do not create a connection.
    from .permissions.object_facts import SUPPORTED_OPERATIONS
    from .permissions.work_subject import WORK_OPERATIONS

    return isinstance(identifier, str) and identifier in (
        SUPPORTED_OPERATIONS | WORK_OPERATIONS.keys() | INTERNAL_CONSUMER_OPERATIONS
    )


def lookup_spec(kind: str) -> LookupSpec:
    from .permissions.object_facts import OPERATION_KINDS, RESOURCES
    from .permissions.work_subject import WORK_OPERATIONS

    if not isinstance(kind, str) or kind not in _RESOURCES:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    table, key, extra = _RESOURCES[kind]
    if kind != "user" and RESOURCES.get(kind) != (table, key):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    operations = {name for name, value in OPERATION_KINDS.items() if value == kind}
    operations.update(name for name, value in WORK_OPERATIONS.items() if value[1] == kind)
    if kind == "source":
        operations.update(("createUpload", "createImport"))
    if kind == "task":
        operations.add("createReview")
        operations.update(("issueOperationToken", "sealEvidence"))
    if kind == "approval":
        operations.add("exportAudit")
    if kind == "review":
        operations.add("listReviews")
    if kind == "task":
        operations.add("listPendingReviews")
        operations.add("listTasks")
    if kind == "asset":
        operations.add("listAssets")
    if kind == "model":
        operations.add("listModels")
    if kind == "model_evaluation":
        operations.add("listEvaluations")
    if kind == "operation":
        from .permissions.object_facts import CASE_LISTS

        operations.update(CASE_LISTS)
        operations.add("createSource")
    if kind == "user":
        operations.update(("getCurrentUser", "createPolicy", "listPolicies", "listModels", "listEvaluations"))
    if kind in {"task", "report", "evidence_package", "feedback", "operation"}:
        operations.add("requestApproval")
    columns: tuple[str, ...] = (key, "org_id", "row_version", "created_by")
    if kind not in {"policy", "user", "model", "model_evaluation"}:
        columns += ("case_id",)
    return LookupSpec(table, key, tuple(dict.fromkeys(columns + extra)), frozenset(operations))


_CASE_TABLES = (
    "analysis_task",
    "asset_lineage",
    "audit_export",
    "cases",
    "claim",
    "claim_evidence_relation",
    "cluster_member",
    "content_cluster",
    "content_item",
    "event_receipt",
    "evidence_item",
    "evidence_package",
    "feature",
    "feedback_request",
    "finding_evidence",
    "first_source_candidate",
    "first_source_ranking",
    "idempotency_record",
    "import_item",
    "import_job",
    "keyframe",
    "media_asset",
    "object_version",
    "outbox_event",
    "package_item",
    "propagation_edge",
    "propagation_node",
    "report",
    "report_evidence",
    "review_evidence",
    "review_record",
    "risk_finding",
    "search_job",
    "shot",
    "source_match",
    "source_registry",
    "tamper_finding",
    "task_event",
    "task_evidence",
    "task_node_run",
    "task_result",
    "task_run",
    "task_run_plan",
    "text_segment",
    "upload_part",
    "upload_session",
)
_ORG_TABLES = (
    "dataset_version",
    "index_registry",
    "model_evaluation",
    "model_registry",
    "model_release",
    "policy_registry",
)
_DIRECTORY_TABLES = (
    "organizations",
    "permissions",
    "roles",
    "role_permissions",
    "users",
    "user_roles",
    "case_membership",
    "user_identities",
)
_MIXED_TABLES = ("approval_request", "approval_decision", "operation_token", "audit_event")
_PRIVATE_TASK_PLAN_TABLES = (
    "task_policy_artifact",
    "task_plan_artifact",
    "task_capability_manifest",
    "task_plan_mapping_revision",
    "task_plan_mapping_head",
)


def _table_scopes() -> MappingProxyType[str, TableScopeRule]:
    result: dict[str, TableScopeRule] = {}
    groups: tuple[tuple[Literal["CASE", "ORG", "DIRECTORY", "MIXED", "INTERNAL"], tuple[str, ...]], ...] = (
        ("CASE", _CASE_TABLES),
        ("ORG", _ORG_TABLES + _PRIVATE_TASK_PLAN_TABLES),
        ("DIRECTORY", _DIRECTORY_TABLES),
        ("MIXED", _MIXED_TABLES),
        ("INTERNAL", ("authorization_epoch",)),
    )
    for category, names in groups:
        for table in names:
            if table in result:
                raise RuntimeError("DUPLICATE_SCOPE_TABLE")
            result[table] = TableScopeRule(
                table,
                category,
                table not in {"authorization_epoch", "user_identities", *_PRIVATE_TASK_PLAN_TABLES},
                tuple(sorted(kind for kind, value in _RESOURCES.items() if value[0] == table)),
            )
    return MappingProxyType(dict(sorted(result.items())))


TABLE_SCOPES = _table_scopes()
