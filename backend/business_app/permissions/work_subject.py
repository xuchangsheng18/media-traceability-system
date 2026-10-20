"""Server-defined work kinds and structural binding, without any token lifetime."""

from types import MappingProxyType
from uuid import UUID

from ..errors import BusinessError
from ..identity.directory import valid_key
from ..types import Actor
from .rule_types import ExecutionSubject

WORK_TABLES = MappingProxyType(
    {
        "upload_validation": ("upload_session", "upload_id", "owner_id"),
        "task_execution": ("analysis_task", "task_id", "created_by"),
        "task_cancellation": ("analysis_task", "task_id", "created_by"),
        "audit_export": ("audit_export", "export_id", "created_by"),
    }
)
WORK_OPERATIONS = MappingProxyType(
    {
        "validateUploadWork": ("asset.upload", "upload", "upload_validation"),
        "startTaskNodeWork": ("task.create", "task", "task_execution"),
        "finishTaskNodeWork": ("task.create", "task", "task_execution"),
        "cancelTaskWork": ("task.cancel", "task", "task_cancellation"),
        "processAuditExportWork": ("audit.export", "export", "audit_export"),
    }
)


def validate_execution_subject(subject: ExecutionSubject) -> None:
    if (
        not isinstance(subject, ExecutionSubject)
        or not isinstance(subject.actor, Actor)
        or not isinstance(subject.actor.user_id, UUID)
        or not isinstance(subject.actor.org_id, UUID)
        or not isinstance(subject.identity_id, UUID)
        or not isinstance(subject.work_id, UUID)
        or not valid_key(subject.mapping_version, 1024)
        or subject.work_kind not in WORK_TABLES
    ):
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
