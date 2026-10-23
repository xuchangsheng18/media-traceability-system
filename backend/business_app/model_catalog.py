"""Organization-bound persisted model metadata; no inference or health claims."""

import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from .catalog_reads import CatalogCollection
from .contracts import validate_response
from .controls.common import page
from .data_scope import AccessMode, DataScope
from .db import Database
from .errors import BusinessError
from .permissions.conditional import ConditionalPort
from .permissions.rule_types import AuthorizationEvidence
from .scope_collections import require_root
from .scope_context import current_data_scope
from .settings import BusinessSettings
from .types import Actor

MODEL_FIELDS = (
    "model_id",
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
    "row_version",
)
EVALUATION_FIELDS = (
    "evaluation_id",
    "model_id",
    "dataset_id",
    "dataset_version",
    "protocol_id",
    "split",
    "sample_count",
    "failure_count",
    "metrics",
    "artifact_ref",
    "created_at",
)


def _projection(row: Mapping[str, Any], org_id: UUID, fields: tuple[str, ...], schema: str) -> dict[str, Any]:
    try:
        if row["org_id"] != org_id:
            raise ValueError()
        value = {
            key: str(row[key])
            if isinstance(row[key], UUID)
            else row[key].isoformat()
            if isinstance(row[key], datetime)
            else deepcopy(row[key])
            for key in fields
        }
        # JSON Schema comparisons alone do not exclude every nonfinite float.
        json.dumps(value, allow_nan=False)
        validate_response(schema, value)
        return value
    except BusinessError:
        raise
    except (ValueError, TypeError, KeyError, OverflowError):
        raise BusinessError("RESPONSE_CONTRACT_UNAVAILABLE", 503) from None


def project_model(row: Mapping[str, Any], org_id: UUID) -> dict[str, Any]:
    return _projection(row, org_id, MODEL_FIELDS, "Model")


def project_evaluation(
    row: Mapping[str, Any],
    org_id: UUID,
    model: Mapping[str, Any],
    artifact: Mapping[str, Any] | None,
) -> dict[str, Any]:
    value = _projection(row, org_id, EVALUATION_FIELDS, "Evaluation")
    try:
        if (
            model["org_id"] != org_id
            or model["model_id"] != row["model_id"]
            or value["failure_count"] > value["sample_count"]
            or not isinstance(artifact, Mapping)
            or str(artifact["org_id"]) != str(org_id)
            or UUID(str(artifact["object_id"])) != UUID(value["artifact_ref"]["object_id"])
            or any(str(artifact[name]) != value["artifact_ref"][name] for name in ("version_id", "sha256"))
        ):
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise BusinessError("MODEL_ARTIFACT_BINDING_INVALID", 503) from None
    return value


class ModelCatalog:
    def __init__(self, database: Database, settings: BusinessSettings) -> None:
        self.database, self.settings = database, settings

    @staticmethod
    def _item(connection: Connection, scope: DataScope, operation: str, item: dict[str, Any]) -> dict[str, Any]:
        table, key = (
            ("model_registry", "model_id") if operation == "listModels" else ("model_evaluation", "evaluation_id")
        )
        row = (
            connection.execute(
                text(
                    f"SELECT * FROM mt.{table} WHERE org_id=:org AND {key}=:id"
                    + (" FOR SHARE" if operation == "listModels" else "")
                    + " /* model_catalog_projection */"
                ),
                dict(org=scope.actor.org_id, id=item[key]),
            )
            .mappings()
            .one_or_none()
        )
        if row is None or row["row_version"] != item["row_version"]:
            raise BusinessError("AUTHORIZATION_CHANGED", 503)
        if operation == "listModels":
            return project_model(dict(row), scope.actor.org_id)
        model = (
            connection.execute(
                text("SELECT org_id,model_id FROM mt.model_registry WHERE org_id=:org AND model_id=:model FOR SHARE"),
                dict(org=scope.actor.org_id, model=row["model_id"]),
            )
            .mappings()
            .one_or_none()
        )
        if model is None:
            raise BusinessError("MODEL_ARTIFACT_BINDING_INVALID", 503)
        artifact = connection.execute(
            text("SELECT mt.model_evaluation_artifact_metadata(:id)"), dict(id=row["evaluation_id"])
        ).scalar_one()
        return project_evaluation(dict(row), scope.actor.org_id, dict(model), artifact)

    def list(
        self, actor: Actor, operation: str, cursor: str | None, limit: int, conditions: ConditionalPort
    ) -> dict[str, Any]:
        if operation not in {"listModels", "listEvaluations"} or type(limit) is not int or not 1 <= limit <= 100:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        collection = CatalogCollection(conditions)
        with self.database.identity_transaction(actor) as connection:
            scope = current_data_scope()
            authorization = require_root(connection, scope)
            if (
                scope is None
                or scope.mode is not AccessMode.ORGANIZATION
                or scope.actor != actor
                or scope.operation_id != operation
                or not isinstance(authorization.evidence, AuthorizationEvidence)
                or authorization.evidence.target.kind != "model_collection"
            ):
                raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
            table, key = (
                ("model_registry", "model_id") if operation == "listModels" else ("model_evaluation", "evaluation_id")
            )
            rows, following = page(
                connection,
                table,
                key,
                scope,
                self.settings.cursor_secret,
                cursor,
                limit,
                where="org_id=:org",
                filters=dict(catalog_operation=operation),
                collection=collection,
                bind_visibility=True,
            )
            items = [self._item(connection, scope, operation, item) for item in rows]
            self.database.before_commit(connection, lambda: collection.finish(connection, current_data_scope()))
        return dict(items=items, next_cursor=following)
