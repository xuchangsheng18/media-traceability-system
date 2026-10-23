import copy
from datetime import datetime, timezone
from uuid import uuid4

import psycopg


def prepare_history(context):
    from tests.business.test_upload_validation import complete, event, prepared_upload, worker

    app, http, upload, descriptor = prepared_upload(context)
    assert complete(http, upload, descriptor, key=uuid4().hex).status_code == 202
    worker(app, context).consume_validation(event(context, upload))
    result = http.get(f"/api/v1/uploads/{upload}", headers={"Authorization": "Bearer test-only-valid-token"}).json()
    asset = result["result"]["asset_id"]
    task, cluster = uuid4(), uuid4()
    with psycopg.connect(context["admin_dsn"]) as connection:
        ref = connection.execute(
            "SELECT o.object_id,o.version_id,o.sha256 FROM mt.object_version o JOIN mt.media_asset a ON a.case_id=o.case_id AND a.object_id=o.object_id WHERE a.asset_id=%s",
            (asset,),
        ).fetchone()
        assert ref is not None
        connection.execute(
            """INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility,created_by)
            VALUES(%s,%s,%s,%s,'synthetic-test-only','normal','CREATED','policy-dev-1',ARRAY[]::text[],'draft_only',%s)""",
            (task, context["actor"].org_id, context["case_id"], asset, context["actor"].user_id),
        )
        connection.execute(
            "INSERT INTO mt.content_cluster(cluster_id,org_id,case_id,scope,policy_version,status) VALUES(%s,%s,%s,'test-only-no-observations','policy-dev-1','candidate')",
            (cluster, context["actor"].org_id, context["case_id"]),
        )
    return dict(
        context,
        app=app,
        http=http,
        task_id=task,
        cluster_id=cluster,
        asset_id=asset,
        input_ref={"object_id": str(ref[0]), "version_id": ref[1], "sha256": ref[2]},
    )


def snapshot(context, run_version, result_version=1):
    binding = {
        "org_id": str(context["actor"].org_id),
        "case_id": str(context["case_id"]),
        "task_id": str(context["task_id"]),
        "run_version": run_version,
        "result_version": result_version,
        "policy_version": "policy-dev-1",
        "dag_version": "test-persistence-only/1",
    }
    task = {
        "task_id": binding["task_id"],
        "case_id": binding["case_id"],
        "asset_id": context["asset_id"],
        "state": "CREATED",
        "run_version": run_version,
        "result_version": result_version,
        "policy_version": "policy-dev-1",
        "version": 1,
        "progress": 0,
        "nodes": [],
        "missing_modalities": ["analysis-not-executed"],
        "report_eligibility": "draft_only",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    responses = [dict(operation_id="getTask", resource_id=binding["task_id"], response=task)]
    short_binding = {k: binding[k] for k in ["task_id", "run_version", "result_version", "policy_version"]}
    findings = {
        "binding": short_binding,
        "findings": [],
        "missing_modalities": ["analysis-not-executed"],
        "warnings": ["self-generated persistence test, no model result"],
    }
    responses += [
        dict(operation_id="getRiskFindings", resource_id=binding["task_id"], response=copy.deepcopy(findings)),
        dict(operation_id="getForensics", resource_id=binding["task_id"], response=copy.deepcopy(findings)),
        dict(
            operation_id="getTaskEvidence", resource_id=binding["task_id"], response={"items": [], "next_cursor": None}
        ),
        dict(
            operation_id="getTimeline",
            resource_id=context["asset_id"],
            response={"asset_id": context["asset_id"], "mapping_version": "test-persistence-only/1", "items": []},
        ),
        dict(
            operation_id="getFirstSource",
            resource_id=str(context["cluster_id"]),
            response={
                "cluster_id": str(context["cluster_id"]),
                "scope": "test-only-no-observations",
                "candidates": [],
                "status": "insufficient",
                "coverage_note": "no algorithm executed; self-owned test snapshot",
                "model_version": "not-executed",
                "ranking_id": str(uuid4()),
                **short_binding,
                "candidate_count": 0,
            },
        ),
        dict(
            operation_id="getPropagation",
            resource_id=str(context["cluster_id"]),
            response={"cluster_id": str(context["cluster_id"]), "version": 1, "nodes": [], "edges": []},
        ),
    ]

    return {
        "binding": binding,
        "request_id": str(uuid4()),
        "published_at": datetime.now(timezone.utc).isoformat(),
        "input_refs": [copy.deepcopy(context["input_ref"])],
        "capability_outputs": [],
        "ordinary_media_outputs": [],
        "projection_refs": [
            {
                "operation_id": entry["operation_id"],
                "schema_id": "urn:media-trace:api:0.1.0#/$defs/"
                + {
                    "getTask": "Task",
                    "getRiskFindings": "Findings",
                    "getForensics": "Findings",
                    "getTaskEvidence": "EvidencePage",
                    "getTimeline": "Timeline",
                    "getFirstSource": "FirstSource",
                    "getPropagation": "Graph",
                }[entry["operation_id"]],
                "json_pointer": f"/api_projections/{index}/response",
                "mapping_version": "history-api-projection/1",
            }
            for index, entry in enumerate(responses)
        ],
        "api_projections": responses,
        "missing_modalities": ["analysis-not-executed"],
        "formal_eligibility": "draft_only",
    }
