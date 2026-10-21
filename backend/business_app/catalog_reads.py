"""Current catalog metadata under case, per-item and transaction-end authorization."""

from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from .controls.common import page
from .data_scope import DataScope, ResourceBinding
from .db import Database
from .errors import BusinessError
from .permissions.conditional import ConditionalPort
from .scope_collections import CollectionScope, require_resource
from .scope_context import current_data_scope
from .settings import BusinessSettings
from .types import Scope


class CatalogCollection(CollectionScope):
    """Keep the actual candidate proof until all projection queries have finished."""

    def allowed_ids(
        self, connection: Connection, scope: DataScope | None, candidates: tuple[ResourceBinding, ...]
    ) -> tuple[UUID, ...]:
        allowed = super().allowed_ids(connection, scope, candidates)
        self.candidates, self.visible, self.proof = candidates, allowed, self.fingerprint
        return allowed

    def finish(self, connection: Connection, scope: DataScope | None) -> None:
        visible = super().allowed_ids(connection, scope, self.candidates)
        if visible != self.visible or self.fingerprint != self.proof:
            raise BusinessError("AUTHORIZATION_CHANGED", 503)


class CatalogReads:
    def __init__(self, database: Database, settings: BusinessSettings) -> None:
        self.database, self.settings = database, settings

    @staticmethod
    def asset(connection: Connection, scope: Scope, identifier: UUID) -> dict[str, Any]:
        require_resource(connection, current_data_scope(), "asset", identifier)
        item = (
            connection.execute(
                text(
                    "SELECT a.*,o.version_id,o.sha256 AS registered_sha256,o.size_bytes AS registered_size "
                    "FROM mt.media_asset a JOIN mt.object_version o "
                    "ON o.org_id=a.org_id AND o.case_id=a.case_id AND o.object_id=a.object_id "
                    "WHERE a.org_id=:org AND a.case_id=:case AND a.asset_id=:id "
                    "/* catalog_asset_projection */"
                ),
                dict(org=scope.actor.org_id, case=scope.case_id, id=identifier),
            )
            .mappings()
            .one_or_none()
        )
        if item is None:
            raise BusinessError("RESOURCE_NOT_FOUND", 404)
        if item["sha256"] != item["registered_sha256"] or item["size_bytes"] != item["registered_size"]:
            raise BusinessError("ASSET_OBJECT_BINDING_INVALID", 503)
        return dict(
            asset_id=str(item["asset_id"]),
            case_id=str(item["case_id"]),
            content_id=str(item["content_id"]),
            source_id=str(item["source_id"]),
            kind=item["kind"],
            object_ref=dict(object_id=str(item["object_id"]), version_id=item["version_id"], sha256=item["sha256"]),
            mime=item["mime"],
            size_bytes=int(item["size_bytes"]),
            duration_ms=item["duration_ms"],
            width=item["width"],
            height=item["height"],
            state=item["state"],
            version=int(item["row_version"]),
            created_at=item["created_at"].isoformat(),
        )

    @staticmethod
    def task(connection: Connection, scope: Scope, item: dict[str, Any]) -> dict[str, Any]:
        require_resource(connection, current_data_scope(), "task", item["task_id"])
        attempts = (
            connection.execute(
                text(
                    "SELECT node_code,state,attempt,reason,required FROM mt.task_node_run "
                    "WHERE org_id=:org AND case_id=:case AND task_id=:task AND run_version=:run "
                    "ORDER BY node_code,attempt DESC LIMIT 1001 FOR SHARE"
                ),
                dict(org=scope.actor.org_id, case=scope.case_id, task=item["task_id"], run=item["run_version"]),
            )
            .mappings()
            .all()
        )
        if len(attempts) > 1000:
            raise BusinessError("NODE_READ_DEVELOPMENT_LIMIT_EXCEEDED", 503)
        latest: dict[str, dict[str, Any]] = {}
        for attempt in attempts:
            latest.setdefault(attempt["node_code"], dict(attempt))
        return dict(
            task_id=str(item["task_id"]),
            case_id=str(item["case_id"]),
            asset_id=str(item["asset_id"]),
            state=item["state"],
            run_version=int(item["run_version"]),
            result_version=int(item["result_version"]),
            policy_version=item["policy_version"],
            version=int(item["row_version"]),
            progress=item["progress"],
            nodes=list(latest.values()),
            missing_modalities=item["missing_modalities"],
            report_eligibility=item["report_eligibility"],
            created_at=item["created_at"].isoformat(),
        )

    def list(
        self, scope: Scope, operation: str, cursor: str | None, limit: int, conditions: ConditionalPort
    ) -> dict[str, Any]:
        table, key = {"listAssets": ("media_asset", "asset_id"), "listTasks": ("analysis_task", "task_id")}[operation]
        collection = CatalogCollection(conditions)
        with self.database.transaction(scope) as connection:
            rows, following = page(
                connection,
                table,
                key,
                scope,
                self.settings.cursor_secret,
                cursor,
                limit,
                where="org_id=:org AND case_id=:case",
                filters=dict(catalog_operation=operation),
                collection=collection,
                bind_visibility=True,
            )
            items = [
                self.asset(connection, scope, item[key])
                if operation == "listAssets"
                else self.task(connection, scope, item)
                for item in rows
            ]
            self.database.before_commit(connection, lambda: collection.finish(connection, current_data_scope()))
        return dict(items=items, next_cursor=following)
