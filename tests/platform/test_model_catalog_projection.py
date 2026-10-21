"""Pure model metadata projections; synthetic rows never assert inference health."""

import importlib
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from business_app.contracts import validate_response
from business_app.errors import BusinessError


@pytest.fixture
def projections():
    return importlib.import_module("business_app.model_catalog")


@pytest.fixture
def records():
    org, model_id, evaluation_id, object_id = [uuid4() for _ in range(4)]
    model = dict(
        org_id=org,
        model_id=model_id,
        name="synthetic-model",
        version="synthetic-v1",
        capability="media.ocr",
        digest="a" * 64,
        dataset_version="synthetic-data-v1",
        model_card_ref="synthetic-card",
        license_record_ref="synthetic-license",
        backend="onnxruntime",
        environment_ref="synthetic-environment",
        status="REGISTERED",
        row_version=1,
        metric_json={"private": "not a public field"},
        created_by=uuid4(),
    )
    artifact = dict(org_id=str(org), object_id=str(object_id), version_id="immutable-v1", sha256="b" * 64)
    evaluation = dict(
        org_id=org,
        evaluation_id=evaluation_id,
        model_id=model_id,
        dataset_id="synthetic-data",
        dataset_version="synthetic-data-v1",
        protocol_id="synthetic-protocol",
        split="validation",
        sample_count=3,
        failure_count=1,
        metrics=dict(macro_f1=None, recall=0.5, iou=None, recall_at_k=None, ece=None, boundary_mae_ms=None),
        artifact_ref={key: value for key, value in artifact.items() if key != "org_id"},
        row_version=1,
        created_at=datetime(2026, 10, 21, tzinfo=timezone.utc),
    )
    return org, model, evaluation, artifact


def test_model_projection_is_exact_metadata_without_health_or_private_columns(projections, records):
    org, model, _, _ = records
    value = projections.project_model(model, org)
    validate_response("Model", value)
    assert value["model_id"] == str(model["model_id"]) and value["status"] == "REGISTERED"
    assert set(value) == {
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
    }


def test_evaluation_projection_preserves_real_metrics_and_immutable_reference(projections, records):
    org, model, evaluation, artifact = records
    value = projections.project_evaluation(evaluation, org, model, artifact)
    validate_response("Evaluation", value)
    assert value["metrics"] == evaluation["metrics"] and value["artifact_ref"] == evaluation["artifact_ref"]
    assert value["evaluation_id"] == str(evaluation["evaluation_id"])
    value["metrics"]["recall"] = 0.9
    assert evaluation["metrics"]["recall"] == 0.5


def test_evaluation_accepts_uppercase_uuid_for_the_same_registered_object(projections, records):
    org, model, evaluation, artifact = records
    artifact["object_id"] = "aabbccdd-1234-5678-90ab-aabbccddeeff"
    evaluation["artifact_ref"]["object_id"] = "AABBCCDD-1234-5678-90AB-AABBCCDDEEFF"
    value = projections.project_evaluation(evaluation, org, model, artifact)
    assert value["artifact_ref"]["object_id"] == "AABBCCDD-1234-5678-90AB-AABBCCDDEEFF"


@pytest.mark.parametrize(
    "field,value",
    [("object_id", "ffffffff-ffff-ffff-ffff-ffffffffffff"), ("version_id", "different-version"), ("sha256", "c" * 64)],
)
def test_requested_artifact_must_match_registered_uuid_version_and_hash(projections, records, field, value):
    org, model, evaluation, artifact = records
    evaluation["artifact_ref"][field] = value
    with pytest.raises(BusinessError) as caught:
        projections.project_evaluation(evaluation, org, model, artifact)
    assert caught.value.code == "MODEL_ARTIFACT_BINDING_INVALID"


@pytest.mark.parametrize("kind", ["model", "evaluation", "evaluation_model", "artifact"])
def test_cross_organization_provenance_fails_closed(projections, records, kind):
    org, model, evaluation, artifact = records
    if kind in {"model", "evaluation_model"}:
        model["org_id"] = uuid4()
    elif kind == "evaluation":
        evaluation["org_id"] = uuid4()
    else:
        artifact["org_id"] = str(uuid4())
    with pytest.raises(BusinessError) as caught:
        if kind == "model":
            projections.project_model(model, org)
        else:
            projections.project_evaluation(evaluation, org, model, artifact)
    assert caught.value.http_status == 503


@pytest.mark.parametrize(
    "field,value", [("object_id", str(uuid4())), ("version_id", "different-version"), ("sha256", "c" * 64)]
)
def test_artifact_registration_must_match_all_immutable_fields(projections, records, field, value):
    org, model, evaluation, artifact = records
    artifact[field] = value
    with pytest.raises(BusinessError) as caught:
        projections.project_evaluation(evaluation, org, model, artifact)
    assert caught.value.http_status == 503


@pytest.mark.parametrize(
    "defect", ["missing_artifact", "model_id", "failure_count", "missing_metrics", "nan", "extra_metric"]
)
def test_invalid_evaluation_does_not_invent_success_or_metrics(projections, records, defect):
    org, model, evaluation, artifact = deepcopy(records)
    if defect == "missing_artifact":
        artifact = None
    elif defect == "model_id":
        model["model_id"] = uuid4()
    elif defect == "failure_count":
        evaluation["failure_count"] = 4
    elif defect == "missing_metrics":
        evaluation["metrics"] = {}
    elif defect == "nan":
        evaluation["metrics"]["recall"] = float("nan")
    else:
        evaluation["metrics"]["invented_accuracy"] = 1
    with pytest.raises(BusinessError) as caught:
        projections.project_evaluation(evaluation, org, model, artifact)
    assert caught.value.http_status == 503


@pytest.mark.parametrize("field,value", [("digest", "bad"), ("row_version", True), ("status", "HEALTHY"), ("name", "")])
def test_malformed_model_metadata_is_unavailable(projections, records, field, value):
    org, model, _, _ = records
    model[field] = value
    with pytest.raises(BusinessError) as caught:
        projections.project_model(model, org)
    assert caught.value.http_status == 503
