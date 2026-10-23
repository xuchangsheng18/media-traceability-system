import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from sqlalchemy import Connection, text

from ..auth import AuthorityProvider
from ..contracts import REGISTRY, ROOT
from ..data_scope import ResourceBinding, TaskBinding
from ..db import Database
from ..errors import BusinessError
from ..objects import ObjectStore
from ..scope_collections import bind_task_scope, require_resource
from ..scope_context import bind_data_scope, current_data_scope
from ..scoped_objects import ScopedObjects
from ..types import ObjectRef, ResultKey, Scope
from .projection import nested_dicts, project

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
        if snapshot["capability_outputs"] or snapshot["ordinary_media_outputs"]:
            raise BusinessError("RESULT_PRODUCER_NOT_IN_SELECTED_BATCH", 503)

    def verify_current_inputs(
        self, connection: Connection, scope: Scope, snapshot: dict[str, Any], *, writing: bool = False
    ) -> None:
        if self.authority is None:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        for ref in nested_dicts(snapshot):
            if not {"object_id", "version_id", "sha256"} <= ref.keys():
                continue
            row = (
                connection.execute(
                    text("""SELECT o.version_id,o.sha256,a.source_id,a.asset_id FROM mt.object_version o
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
            try:
                task = snapshot["binding"]
                binding = ResourceBinding(
                    "media_input" if writing else "history_input",
                    row["asset_id"] if writing else UUID(ref["object_id"]),
                    task=TaskBinding(UUID(task["task_id"]))
                    if writing
                    else TaskBinding(UUID(task["task_id"]), task["run_version"], task["result_version"]),
                )
                for _ in ScopedObjects(self.store, self.authority).read(
                    connection,
                    current_data_scope(),
                    binding,
                    ObjectRef(UUID(ref["object_id"]), ref["version_id"], ref["sha256"]),
                ):
                    pass
            except (RuntimeError, FileNotFoundError, ValueError):
                raise BusinessError("SNAPSHOT_INTEGRITY_FAILED", 503) from None
        for body in nested_dicts(snapshot):
            if "asset_id" in body:
                source = connection.execute(
                    text("SELECT source_id FROM mt.media_asset WHERE case_id=:case AND asset_id=:asset"),
                    {"case": scope.case_id, "asset": UUID(body["asset_id"])},
                ).scalar_one_or_none()
                if source is None:
                    raise BusinessError("SNAPSHOT_ASSET_BINDING_INVALID", 409)
                self.authority.authorize_source(scope, source, "analysis")
            evidence_ids = []
            if "evidence_id" in body:
                evidence_ids.append(body["evidence_id"])
            for field in ["evidence_ids", "counter_evidence_ids"]:
                if field in body:
                    evidence_ids.extend(body[field])
            for evidence_id in evidence_ids:
                recorded = (
                    connection.execute(
                        text("""SELECT e.task_id,e.run_version,e.result_version,e.asset_id,a.source_id
                FROM mt.evidence_item e JOIN mt.media_asset a ON a.case_id=e.case_id AND a.asset_id=e.asset_id
                WHERE e.case_id=:case AND e.evidence_id=:evidence"""),
                        {"case": scope.case_id, "evidence": UUID(evidence_id)},
                    )
                    .mappings()
                    .one_or_none()
                )
                binding = snapshot["binding"]
                if recorded is None or (
                    str(recorded["task_id"]),
                    recorded["run_version"],
                    recorded["result_version"],
                ) != (binding["task_id"], binding["run_version"], binding["result_version"]):
                    raise BusinessError("SNAPSHOT_EVIDENCE_BINDING_INVALID", 409)
                self.authority.authorize_source(scope, recorded["source_id"], "analysis")

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
            bind_task_scope(connection, current_data_scope(), TaskBinding(key.task_id))
            task = (
                connection.execute(
                    text(
                        "SELECT t.asset_id,a.object_id FROM mt.analysis_task t JOIN mt.media_asset a ON a.case_id=t.case_id AND a.asset_id=t.asset_id WHERE t.case_id=:case AND t.task_id=:task FOR UPDATE OF t"
                    ),
                    {"case": scope.case_id, "task": key.task_id},
                )
                .mappings()
                .one_or_none()
            )
            if task is None:
                raise BusinessError("TASK_NOT_FOUND", 404)
            if str(task["object_id"]) not in {ref["object_id"] for ref in snapshot["input_refs"]}:
                raise BusinessError("SNAPSHOT_TASK_INPUT_INVALID", 409)
            input_sha = hashlib.sha256(canonical({"input_refs": snapshot["input_refs"]})).hexdigest()
            self.verify_current_inputs(connection, scope, snapshot, writing=True)
            for entry in snapshot.get("api_projections", []):
                if str(UUID(entry["resource_id"])) != entry["resource_id"]:
                    raise BusinessError("SNAPSHOT_RESOURCE_ID_NOT_CANONICAL", 422)
                response = project(snapshot, entry["operation_id"], UUID(entry["resource_id"]))
                if entry["operation_id"] == "getTask" and UUID(response["asset_id"]) != task["asset_id"]:
                    raise BusinessError("SNAPSHOT_BINDING_INVALID", 409)
            run = (
                connection.execute(
                    text(
                        "SELECT policy_version,dag_version,input_sha256 FROM mt.task_run WHERE case_id=:case AND task_id=:task AND run_version=:run"
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
                        "sha": input_sha,
                        "dag": binding["dag_version"],
                        "policy": binding["policy_version"],
                        "actor": scope.actor.user_id,
                    },
                )
            elif (
                run["policy_version"] != binding["policy_version"]
                or run["dag_version"] != binding["dag_version"]
                or run["input_sha256"] != input_sha
            ):
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
            for entry in snapshot.get("api_projections", []):
                if entry["operation_id"] == "getFirstSource":
                    self.persist_ranking(connection, scope, key, entry["response"])
        return key

    def persist_ranking(self, connection: Connection, scope: Scope, key: ResultKey, response: dict[str, Any]) -> None:
        candidates = response["candidates"]
        if (
            response["candidate_count"] != len(candidates)
            or [c["rank"] for c in candidates] != list(range(1, len(candidates) + 1))
            or len({c["asset_id"] for c in candidates}) != len(candidates)
        ):
            raise BusinessError("SNAPSHOT_RANKING_INVALID", 409)
        if not candidates and response["status"] != "insufficient":
            raise BusinessError("SNAPSHOT_RANKING_INVALID", 409)
        ranking, cluster = UUID(response["ranking_id"]), UUID(response["cluster_id"])
        if str(ranking) != response["ranking_id"]:
            raise BusinessError("SNAPSHOT_RESOURCE_ID_NOT_CANONICAL", 422)
        exists = connection.execute(
            text("SELECT cluster_id FROM mt.content_cluster WHERE case_id=:case AND cluster_id=:cluster"),
            {"case": scope.case_id, "cluster": cluster},
        ).scalar_one_or_none()
        previous = connection.execute(
            text("SELECT ranking_id FROM mt.first_source_ranking WHERE case_id=:case AND ranking_id=:ranking"),
            {"case": scope.case_id, "ranking": ranking},
        ).scalar_one_or_none()
        if exists is None or previous is not None:
            raise BusinessError("SNAPSHOT_RANKING_BINDING_INVALID", 409)
        # Result producers need a shared evidence transaction before populated candidates can be admitted.
        for candidate in candidates:
            member = connection.execute(
                text(
                    "SELECT asset_id FROM mt.cluster_member WHERE case_id=:case AND cluster_id=:cluster AND asset_id=:asset"
                ),
                {"case": scope.case_id, "cluster": cluster, "asset": UUID(candidate["asset_id"])},
            ).scalar_one_or_none()
            if member is None:
                raise BusinessError("SNAPSHOT_RANKING_MEMBER_INVALID", 409)
            for evidence in candidate["evidence_ids"] + candidate["counter_evidence_ids"]:
                recorded = connection.execute(
                    text(
                        "SELECT evidence_id FROM mt.evidence_item WHERE case_id=:case AND task_id=:task AND run_version=:run AND result_version=:result AND evidence_id=:evidence"
                    ),
                    {
                        "case": scope.case_id,
                        "task": key.task_id,
                        "run": key.run_version,
                        "result": key.result_version,
                        "evidence": UUID(evidence),
                    },
                ).scalar_one_or_none()
                if recorded is None:
                    raise BusinessError("SNAPSHOT_EVIDENCE_BINDING_INVALID", 409)
        connection.execute(
            text("""INSERT INTO mt.first_source_ranking(ranking_id,org_id,case_id,cluster_id,task_id,run_version,result_version,candidate_count,model_version,policy_version,coverage_note,status,created_by)
        VALUES(:ranking,:org,:case,:cluster,:task,:run,:result,:count,:model,:policy,:coverage,:status,:actor)"""),
            {
                "ranking": ranking,
                "org": scope.actor.org_id,
                "case": scope.case_id,
                "cluster": cluster,
                "task": key.task_id,
                "run": key.run_version,
                "result": key.result_version,
                "count": len(candidates),
                "model": response["model_version"],
                "policy": response["policy_version"],
                "coverage": response["coverage_note"],
                "status": response["status"],
                "actor": scope.actor.user_id,
            },
        )
        for candidate in candidates:
            connection.execute(
                text("""INSERT INTO mt.first_source_candidate(candidate_id,org_id,case_id,cluster_id,asset_id,rank,probability,published_at,model_version,evidence_refs,coverage_note,status,created_by,ranking_id)
            VALUES(:id,:org,:case,:cluster,:asset,:rank,:probability,:published,:model,CAST(:evidence AS jsonb),:coverage,:status,:actor,:ranking)"""),
                {
                    "id": uuid4(),
                    "org": scope.actor.org_id,
                    "case": scope.case_id,
                    "cluster": cluster,
                    "asset": UUID(candidate["asset_id"]),
                    "rank": candidate["rank"],
                    "probability": candidate["probability"],
                    "published": candidate["published_at"],
                    "model": response["model_version"],
                    "evidence": json.dumps(
                        {
                            "evidence_ids": candidate["evidence_ids"],
                            "counter_evidence_ids": candidate["counter_evidence_ids"],
                        }
                    ),
                    "coverage": response["coverage_note"],
                    "status": response["status"],
                    "actor": scope.actor.user_id,
                    "ranking": ranking,
                },
            )

    def load_exact(self, scope: Scope, key: ResultKey) -> dict[str, Any]:
        with self.database.transaction(scope) as connection:
            limited = bind_task_scope(
                connection, current_data_scope(), TaskBinding(key.task_id, key.run_version, key.result_version)
            )
            with bind_data_scope(limited):
                return self._load_exact_bound(connection, scope, key)

    def _load_exact_bound(self, connection: Connection, scope: Scope, key: ResultKey) -> dict[str, Any]:
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
            kind = (
                "task"
                if operation_id in {"getTask", "getRiskFindings", "getForensics", "getTaskEvidence"}
                else "asset"
                if operation_id == "getTimeline"
                else "cluster"
            )
            require_resource(connection, current_data_scope(), kind, resource_id)
            if kind == "task":
                bind_task_scope(connection, current_data_scope(), TaskBinding(resource_id))
            entry: dict[str, Any] = {"operation_id": operation_id, "resource_id": str(resource_id)}
            if ranking_id is not None:
                entry["response"] = {"ranking_id": str(ranking_id)}
            selector = json.dumps({"snapshot": {"api_projections": [entry]}})
            ordering = (
                "run_version DESC,result_version DESC,created_at DESC,result_id DESC"
                if operation_id in {"getTask", "getRiskFindings", "getForensics", "getTaskEvidence"}
                else "created_at DESC,result_id DESC"
            )
            row = connection.execute(
                text(
                    """SELECT task_id,run_version,result_version FROM mt.task_result WHERE case_id=:case
                AND summary @> CAST(:selector AS jsonb) ORDER BY """
                    + ordering
                    + " LIMIT 1"
                ),
                {"case": scope.case_id, "selector": selector},
            ).one_or_none()
            if row is None:
                raise BusinessError("RESULT_NOT_FOUND", 404)
            key = ResultKey(row.task_id, int(row.run_version), int(row.result_version))
            bind_task_scope(
                connection, current_data_scope(), TaskBinding(key.task_id, key.run_version, key.result_version)
            )
        return key, self.load_exact(scope, key)
