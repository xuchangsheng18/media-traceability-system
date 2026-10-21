"""Pure report projection checks using self-owned, nonbusiness fixture values."""

import importlib.util
from datetime import datetime, timezone
from uuid import uuid4

import pytest


def inputs():
    report, org, case, task, evidence, asset, object_id = [uuid4() for _ in range(7)]
    item = dict(
        report_id=report,
        org_id=org,
        case_id=case,
        task_id=task,
        run_version=2,
        result_version=3,
        version=4,
        state="DRAFT",
        approval_id=None,
        object_id=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    links = [
        dict(
            evidence_id=evidence,
            org_id=org,
            case_id=case,
            task_id=task,
            run_version=2,
            result_version=3,
            asset_id=asset,
        )
    ]
    obj = dict(object_id=object_id, org_id=org, case_id=case, version_id="immutable/1", sha256="a" * 64)
    return item, links, obj


def projection():
    assert importlib.util.find_spec("business_app.registry_reads") is not None, "Report projection is missing"
    from business_app.registry_reads import project_report

    return project_report


def test_report_projection_returns_only_persisted_contract_metadata():
    project = projection()
    item, links, _ = inputs()
    value = project(item, links, None)
    assert value == dict(
        report_id=str(item["report_id"]),
        case_id=str(item["case_id"]),
        task_id=str(item["task_id"]),
        run_version=2,
        result_version=3,
        version=4,
        state="DRAFT",
        approval_id=None,
        object_ref=None,
        evidence_ids=[str(links[0]["evidence_id"])],
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_report_projection_uses_exact_registered_object_reference():
    project = projection()
    item, links, obj = inputs()
    item.update(state="READY", object_id=obj["object_id"])
    value = project(item, links, obj)
    assert value["object_ref"] == dict(object_id=str(obj["object_id"]), version_id="immutable/1", sha256="a" * 64)


@pytest.mark.parametrize(
    "defect",
    [
        "no_evidence",
        "task",
        "run",
        "result",
        "case",
        "org",
        "duplicate",
        "missing_object",
        "wrong_object",
        "wrong_object_case",
        "ready_without_object",
    ],
)
def test_report_projection_rejects_incomplete_or_cross_bound_metadata(defect):
    project = projection()
    from business_app.errors import BusinessError

    item, links, obj = inputs()
    if defect == "no_evidence":
        links = []
    elif defect in {"task", "case", "org"}:
        links[0][defect + "_id"] = uuid4()
    elif defect in {"run", "result"}:
        links[0][defect + "_version"] += 1
    elif defect == "duplicate":
        links += links
    elif defect == "ready_without_object":
        item["state"] = "READY"
    else:
        item["object_id"] = obj["object_id"]
        if defect == "missing_object":
            obj = None
        elif defect == "wrong_object":
            obj["object_id"] = uuid4()
        else:
            obj["case_id"] = uuid4()
    with pytest.raises(BusinessError) as error:
        project(item, links, obj if item["object_id"] is not None else None)
    assert error.value.http_status == 503
