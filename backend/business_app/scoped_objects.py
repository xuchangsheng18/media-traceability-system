"""Exact business bindings around immutable storage; no standalone download authority."""

import hashlib
import json
import re
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from typing import Any, BinaryIO
from uuid import UUID

from sqlalchemy import Connection, text

from .auth import AuthorityProvider
from .controls.providers import ExportRule
from .data_scope import AccessMode, DataScope, ResourceBinding
from .db import Database
from .errors import BusinessError
from .objects import ObjectStore, StoredObject
from .scope_collections import bind_task_scope, require_resource, require_root
from .scope_context import current_data_scope
from .types import ObjectRef, Scope

ExportCheck = Callable[[Connection, Scope, dict[str, Any]], ExportRule]


class ScopedObjects:
    def __init__(
        self, store: ObjectStore, authority: AuthorityProvider | None, *, export_check: ExportCheck | None = None
    ) -> None:
        self.store, self.authority, self.export_check = store, authority, export_check

    @staticmethod
    def _checkpoint(connection: Connection, scope: DataScope | None) -> DataScope:
        authorization = require_root(connection, scope)
        if scope is None or scope.mode is not AccessMode.CASE or authorization.fence is None:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        authorization.fence.finish(connection, authorization.evidence)
        return scope

    def _source(self, scope: DataScope, source: UUID, purpose: str) -> None:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        if scope.case_id is None:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        self.authority.authorize_source(Scope(scope.actor, scope.case_id), source, purpose)

    @staticmethod
    def _registered(connection: Connection, scope: DataScope, reference: ObjectRef) -> int:
        if (
            not isinstance(reference, ObjectRef)
            or not isinstance(reference.object_id, UUID)
            or reference.object_id.int == 0
            or not isinstance(reference.version_id, str)
            or not reference.version_id
            or not isinstance(reference.sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", reference.sha256) is None
        ):
            raise BusinessError("OBJECT_BINDING_INVALID", 503)
        size = connection.execute(
            text(
                "SELECT size_bytes FROM mt.object_version WHERE org_id=:org AND case_id=:case AND object_id=:id AND version_id=:version AND sha256=:sha FOR SHARE"
            ),
            dict(
                org=scope.actor.org_id,
                case=scope.case_id,
                id=reference.object_id,
                version=reference.version_id,
                sha=reference.sha256,
            ),
        ).scalar_one_or_none()
        if type(size) is not int or size < 0:
            raise BusinessError("OBJECT_BINDING_INVALID", 503)
        return size

    def _upload(self, connection: Connection, scope: DataScope, binding: ResourceBinding) -> dict[str, Any]:
        require_resource(connection, scope, "upload", binding.identifier)
        item = (
            connection.execute(
                text(
                    "SELECT source_id,owner_id,state,expires_at,size_bytes,part_size_bytes FROM mt.upload_session WHERE org_id=:org AND case_id=:case AND upload_id=:id FOR SHARE"
                ),
                dict(org=scope.actor.org_id, case=scope.case_id, id=binding.identifier),
            )
            .mappings()
            .one_or_none()
        )
        if item is None:
            raise BusinessError("UPLOAD_NOT_FOUND", 404)
        if item["owner_id"] != scope.actor.user_id or item["state"] not in {"UPLOADING", "VALIDATING"}:
            raise BusinessError("UPLOAD_STATE_CONFLICT", 409)
        if item["expires_at"] <= datetime.now(timezone.utc):
            raise BusinessError("UPLOAD_EXPIRED", 410)
        self._source(scope, item["source_id"], "upload")
        return dict(item)

    def _export(self, connection: Connection, scope: DataScope, binding: ResourceBinding) -> dict[str, Any]:
        require_resource(connection, scope, "export", binding.identifier)
        item = (
            connection.execute(
                text("SELECT * FROM mt.audit_export WHERE org_id=:org AND case_id=:case AND export_id=:id FOR SHARE"),
                dict(org=scope.actor.org_id, case=scope.case_id, id=binding.identifier),
            )
            .mappings()
            .one_or_none()
        )
        if item is None:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if self.export_check is None or scope.case_id is None:
            raise BusinessError("EXPORT_RULE_UNAVAILABLE", 503)
        self.export_check(connection, Scope(scope.actor, scope.case_id), dict(item))
        return dict(item)

    def _media(self, connection: Connection, scope: DataScope, binding: ResourceBinding, reference: ObjectRef) -> None:
        selector = "a.asset_id=:id" if binding.kind == "media_input" else "a.object_id=:id"
        rows = (
            connection.execute(
                text(
                    "SELECT a.asset_id,a.parent_asset_id,a.object_id,a.source_id,a.sha256,a.size_bytes FROM mt.media_asset a WHERE a.org_id=:org AND a.case_id=:case AND a.state='VALID' AND "
                    + selector
                    + " FOR SHARE OF a"
                ),
                dict(org=scope.actor.org_id, case=scope.case_id, id=binding.identifier),
            )
            .mappings()
            .all()
        )
        task = binding.task or scope.task_binding
        if binding.kind == "history_input" and task is None:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if task is not None:
            limited = bind_task_scope(connection, scope, task)
            task = limited.task_binding
            if task is None:
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            primary = connection.execute(
                text("SELECT asset_id FROM mt.analysis_task WHERE org_id=:org AND case_id=:case AND task_id=:task"),
                dict(org=scope.actor.org_id, case=scope.case_id, task=task.task_id),
            ).scalar_one()
            if binding.kind == "history_input" and task.result_version is not None:
                result = (
                    connection.execute(
                        text(
                            "SELECT sha256,summary FROM mt.task_result WHERE org_id=:org AND case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result"
                        ),
                        dict(
                            org=scope.actor.org_id,
                            case=scope.case_id,
                            task=task.task_id,
                            run=task.run_version,
                            result=task.result_version,
                        ),
                    )
                    .mappings()
                    .one()
                )
                envelope = result["summary"]
                snapshot = envelope.get("snapshot") if isinstance(envelope, dict) else None
                encoded = json.dumps(
                    snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
                ).encode()
                if not isinstance(snapshot, dict) or hashlib.sha256(encoded).hexdigest() != result["sha256"]:
                    raise BusinessError("SNAPSHOT_INTEGRITY_FAILED", 503)
                expected = dict(
                    object_id=str(reference.object_id), version_id=reference.version_id, sha256=reference.sha256
                )
                inputs = snapshot.get("input_refs", [])
                evidence_assets = (
                    connection.execute(
                        text(
                            "SELECT asset_id FROM mt.evidence_item WHERE org_id=:org AND case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result AND object_id=:object AND sha256=:sha"
                        ),
                        dict(
                            org=scope.actor.org_id,
                            case=scope.case_id,
                            task=task.task_id,
                            run=task.run_version,
                            result=task.result_version,
                            object=reference.object_id,
                            sha=reference.sha256,
                        ),
                    )
                    .scalars()
                    .all()
                )
                rows = [
                    r
                    for r in rows
                    if r["asset_id"] in evidence_assets
                    or (expected in inputs and (r["asset_id"] == primary or r["parent_asset_id"] == primary))
                ]
            else:
                rows = [r for r in rows if r["asset_id"] == primary or r["parent_asset_id"] == primary]
        if len(rows) != 1:
            raise BusinessError("OBJECT_BINDING_INVALID", 503)
        item = rows[0]
        require_resource(connection, scope, "asset", item["asset_id"])
        if (item["object_id"], item["sha256"]) != (reference.object_id, reference.sha256):
            raise BusinessError("OBJECT_BINDING_INVALID", 503)
        if item["size_bytes"] != self._registered(connection, scope, reference):
            raise BusinessError("OBJECT_BINDING_INVALID", 503)
        self._source(scope, item["source_id"], "import" if scope.operation_id == "createImport" else "analysis")

    def _read_binding(
        self, connection: Connection, scope: DataScope, binding: ResourceBinding, reference: ObjectRef
    ) -> int:
        if not isinstance(binding, ResourceBinding):
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        if binding.kind == "model_artifact":
            raise BusinessError("MODEL_ARTIFACT_PROVENANCE_UNAVAILABLE", 503)
        size = self._registered(connection, scope, reference)
        if binding.kind in {"media_input", "history_input"}:
            self._media(connection, scope, binding, reference)
        elif binding.kind == "upload_part":
            self._upload(connection, scope, binding)
            part = connection.execute(
                text(
                    "SELECT object_id,sha256,size_bytes FROM mt.upload_part WHERE org_id=:org AND case_id=:case AND upload_id=:upload AND part_no=:part FOR SHARE"
                ),
                dict(org=scope.actor.org_id, case=scope.case_id, upload=binding.identifier, part=binding.part_no),
            ).one_or_none()
            if part is None or tuple(part) != (reference.object_id, reference.sha256, size):
                raise BusinessError("OBJECT_BINDING_INVALID", 503)
        elif binding.kind == "export_artifact":
            item = self._export(connection, scope, binding)
            ref = item["artifact_ref"]
            if (
                item["state"] != "READY"
                or not isinstance(ref, dict)
                or any(
                    ref.get(k) != v
                    for k, v in dict(
                        object_id=str(reference.object_id),
                        version_id=reference.version_id,
                        sha256=reference.sha256,
                        size_bytes=size,
                    ).items()
                )
            ):
                raise BusinessError("EXPORT_OBJECT_BINDING_INVALID", 503)
            if self.export_check is None or scope.case_id is None:
                raise BusinessError("EXPORT_RULE_UNAVAILABLE", 503)
            if size > self.export_check(connection, Scope(scope.actor, scope.case_id), item).max_bytes:
                raise BusinessError("EXPORT_LIMIT_EXCEEDED", 413)
        else:
            raise BusinessError("OBJECT_BINDING_UNSUPPORTED", 503)
        return size

    def read(
        self, connection: Connection, scope: DataScope | None, binding: ResourceBinding, reference: ObjectRef
    ) -> Iterator[bytes]:
        # This function is deliberately a generator: validation also runs when
        # iteration starts, not merely when a caller obtains an iterator.
        bound = self._checkpoint(connection, scope)
        expected = self._read_binding(connection, bound, binding, reference)
        stream = self.store.read(reference)
        count = 0
        try:
            while True:
                self._checkpoint(connection, scope)
                if self._read_binding(connection, bound, binding, reference) != expected:
                    raise BusinessError("OBJECT_BINDING_INVALID", 503)
                try:
                    block = next(stream)
                except StopIteration:
                    break
                self._checkpoint(connection, scope)
                self._read_binding(connection, bound, binding, reference)
                count += len(block)
                if count > expected:
                    raise BusinessError("OBJECT_SIZE_INVALID", 503)
                yield block
            if count != expected:
                raise BusinessError("OBJECT_SIZE_INVALID", 503)
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                close()

    def _write_binding(self, connection: Connection, scope: DataScope, binding: ResourceBinding) -> int | None:
        if binding.kind in {"upload_part", "upload"}:
            item = self._upload(connection, scope, binding)
            if binding.kind == "upload":
                if scope.operation_id != "validateUploadWork" or item["state"] != "VALIDATING":
                    raise BusinessError("UPLOAD_STATE_CONFLICT", 409)
                return int(item["size_bytes"])
            if scope.operation_id != "putUploadPart" or item["state"] != "UPLOADING" or binding.part_no is None:
                raise BusinessError("UPLOAD_STATE_CONFLICT", 409)
            expected = min(
                int(item["part_size_bytes"]),
                int(item["size_bytes"]) - (binding.part_no - 1) * int(item["part_size_bytes"]),
            )
            if expected <= 0:
                raise BusinessError("UPLOAD_PART_SIZE_INVALID", 422)
            return expected
        if binding.kind == "export_artifact" and scope.operation_id == "processAuditExportWork":
            item = self._export(connection, scope, binding)
            if item["state"] != "REQUESTED":
                raise BusinessError("EXPORT_STATE_CONFLICT", 409)
            return None
        raise BusinessError("OBJECT_BINDING_UNSUPPORTED", 503)

    def put(self, database: Database, scope: Scope, binding: ResourceBinding, body: BinaryIO) -> StoredObject:
        with database.transaction(scope) as connection:
            bound = self._checkpoint(connection, current_data_scope())
            expected = self._write_binding(connection, bound, binding)
        # Disk writes can run concurrently; the later DB publication must still
        # use a fresh guarded root. No DB reference is published by this method.
        stored = self.store.put_part(scope, binding.identifier, binding.part_no or 1, body)
        try:
            with database.transaction(scope) as connection:
                bound = self._checkpoint(connection, current_data_scope())
                if self._write_binding(connection, bound, binding) != expected:
                    raise BusinessError("OBJECT_BINDING_INVALID", 503)
                if expected is not None and stored.size_bytes != expected:
                    raise BusinessError("UPLOAD_PART_SIZE_INVALID", 422)
            return stored
        except Exception:
            recorder = getattr(self.store, "record_orphan", None)
            if callable(recorder):
                recorder(stored, scope, binding.identifier, "OBJECT_WRITE_NOT_AUTHORIZED_FOR_PUBLICATION")
            raise
