import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from sqlalchemy import Connection, text

from ..auth import AuthorityProvider
from ..contracts import REGISTRY, ROOT
from ..db import Database
from ..errors import BusinessError
from ..objects import ObjectStore
from ..types import ObjectRef, ResultKey, Scope
from .projection import project

CURRENT_SCHEMA = "urn:media-trace:stage-one:run-result:0.2.0"
LEGACY_SCHEMA = "urn:media-trace:stage-one:run-result:0.1.0"


def canonical(snapshot: dict[str, Any]) -> bytes:
    try:
        return json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
    except (ValueError, TypeError):
        raise BusinessError("SNAPSHOT_INVALID", 422) from None


class ResultRepository:
    def __init__(self, database: Database, store: ObjectStore, authority: AuthorityProvider | None) -> None:
        self.database, self.store, self.authority = database, store, authority

    def validate_snapshot(self, snapshot: dict[str, Any], schema_id: str = CURRENT_SCHEMA) -> None:
        file = "run-result.schema.json" if schema_id == CURRENT_SCHEMA else "run-result.v0_1.schema.json"
        if schema_id not in {CURRENT_SCHEMA, LEGACY_SCHEMA}:
            raise BusinessError("SNAPSHOT_SCHEMA_UNSUPPORTED", 503)
        schema = json.loads((ROOT / "schemas/workflow" / file).read_text())
        try:
            Draft202012Validator(schema, registry=REGISTRY, format_checker=FormatChecker()).validate(snapshot)
        except ValidationError:
            raise BusinessError("SNAPSHOT_INVALID", 422) from None

    def verify_current_inputs(self, connection: Connection, scope: Scope, snapshot: dict[str, Any]) -> None:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        for ref in snapshot["input_refs"]:
            row = (
                connection.execute(
                    text("""SELECT o.version_id,o.sha256,a.source_id FROM mt.object_version o
                JOIN mt.media_asset a ON a.case_id=o.case_id AND a.object_id=o.object_id
                WHERE o.case_id=:case AND o.object_id=:id"""),
                    {"case": scope.case_id, "id": UUID(ref["object_id"])},
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["version_id"] != ref["version_id"] or row["sha256"] != ref["sha256"]:
                raise BusinessError("SNAPSHOT_OBJECT_BINDING_INVALID", 409)
            self.authority.authorize_source(scope, row["source_id"], "analysis")
            # Exhausting the immutable stream verifies actual bytes, not just the DB digest.
            for _ in self.store.read(ObjectRef(UUID(ref["object_id"]), ref["version_id"], ref["sha256"])):
                pass

    def append_snapshot(self, scope: Scope, snapshot: dict[str, Any]) -> ResultKey:
        self.validate_snapshot(snapshot)
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        granted = self.authority.authorize_case(scope.actor, scope.case_id, "task.create")
        if granted != scope:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        binding = snapshot["binding"]
        key = ResultKey(UUID(binding["task_id"]), int(binding["run_version"]), int(binding["result_version"]))
        if UUID(binding["org_id"]) != scope.actor.org_id or UUID(binding["case_id"]) != scope.case_id:
            raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
        if snapshot["formal_eligibility"] != "draft_only":
            raise BusinessError("FORMAL_POLICY_UNCONFIGURED", 503)
        encoded = canonical(snapshot)
        sha = hashlib.sha256(encoded).hexdigest()
        with self.database.transaction(scope) as connection:
            task = (
                connection.execute(
                    text("SELECT asset_id FROM mt.analysis_task WHERE case_id=:case AND task_id=:task"),
                    {"case": scope.case_id, "task": key.task_id},
                )
                .mappings()
                .one_or_none()
            )
            if task is None:
                raise BusinessError("TASK_NOT_FOUND", 404)
            self.verify_current_inputs(connection, scope, snapshot)
            for entry in snapshot.get("api_projections", []):
                response = project(snapshot, entry["operation_id"], UUID(entry["resource_id"]))
                if entry["operation_id"] == "getTask" and UUID(response["asset_id"]) != task["asset_id"]:
                    raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
            run = (
                connection.execute(
                    text(
                        "SELECT policy_version,dag_version FROM mt.task_run WHERE case_id=:case AND task_id=:task AND run_version=:run"
                    ),
                    {"case": scope.case_id, "task": key.task_id, "run": key.run_version},
                )
                .mappings()
                .one_or_none()
            )
            if run is None:
                connection.execute(
                    text("""INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,policy_version,created_by)
                    VALUES(:id,:org,:case,:task,:run,:sha,:dag,:policy,:actor)"""),
                    {
                        "id": uuid4(),
                        "org": scope.actor.org_id,
                        "case": scope.case_id,
                        "task": key.task_id,
                        "run": key.run_version,
                        "sha": hashlib.sha256(canonical({"input_refs": snapshot["input_refs"]})).hexdigest(),
                        "dag": binding["dag_version"],
                        "policy": binding["policy_version"],
                        "actor": scope.actor.user_id,
                    },
                )
            elif run["policy_version"] != binding["policy_version"] or run["dag_version"] != binding["dag_version"]:
                raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
            connection.execute(
                text("""INSERT INTO mt.task_result(result_id,org_id,case_id,task_id,run_version,result_version,sha256,policy_version,summary,created_by)
                VALUES(:id,:org,:case,:task,:run,:result,:sha,:policy,CAST(:summary AS jsonb),:actor)"""),
                {
                    "id": uuid4(),
                    "org": scope.actor.org_id,
                    "case": scope.case_id,
                    "task": key.task_id,
                    "run": key.run_version,
                    "result": key.result_version,
                    "sha": sha,
                    "policy": binding["policy_version"],
                    "summary": json.dumps(
                        {"snapshot_schema_id": CURRENT_SCHEMA, "snapshot": snapshot},
                        ensure_ascii=False,
                        allow_nan=False,
                    ),
                    "actor": scope.actor.user_id,
                },
            )
        return key

    def load_exact(self, scope: Scope, key: ResultKey) -> dict[str, Any]:
        with self.database.transaction(scope) as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT sha256,summary FROM mt.task_result WHERE case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result"
                    ),
                    {"case": scope.case_id, "task": key.task_id, "run": key.run_version, "result": key.result_version},
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise BusinessError("RESULT_NOT_FOUND", 404)
            envelope = row["summary"]
            if not isinstance(envelope, dict) or set(envelope) != {"snapshot_schema_id", "snapshot"}:
                raise BusinessError("LEGACY_SNAPSHOT_MAPPING_UNAVAILABLE", 503)
            snapshot = dict(envelope["snapshot"])
            self.validate_snapshot(snapshot, envelope["snapshot_schema_id"])
            if hashlib.sha256(canonical(snapshot)).hexdigest() != row["sha256"]:
                raise BusinessError("SNAPSHOT_INTEGRITY_FAILED", 503)
            binding = snapshot["binding"]
            if (UUID(binding["task_id"]), binding["run_version"], binding["result_version"]) != (
                key.task_id,
                key.run_version,
                key.result_version,
            ):
                raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
            if UUID(binding["org_id"]) != scope.actor.org_id or UUID(binding["case_id"]) != scope.case_id:
                raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
            self.verify_current_inputs(connection, scope, snapshot)
            return snapshot

    def load_latest(
        self, scope: Scope, operation_id: str, resource_id: UUID, ranking_id: UUID | None = None
    ) -> tuple[ResultKey, dict[str, Any]]:
        with self.database.transaction(scope) as connection:
            entry: dict[str, Any] = {"operation_id": operation_id, "resource_id": str(resource_id)}
            if ranking_id is not None:
                entry["response"] = {"ranking_id": str(ranking_id)}
            selector = json.dumps({"snapshot": {"api_projections": [entry]}})
            row = connection.execute(
                text("""SELECT task_id,run_version,result_version FROM mt.task_result WHERE case_id=:case
                AND summary @> CAST(:selector AS jsonb) ORDER BY run_version DESC,result_version DESC,created_at DESC,result_id DESC LIMIT 1"""),
                {"case": scope.case_id, "selector": selector},
            ).one_or_none()
            if row is None:
                raise BusinessError("RESULT_NOT_FOUND", 404)
            key = ResultKey(row.task_id, int(row.run_version), int(row.result_version))
        return key, self.load_exact(scope, key)
