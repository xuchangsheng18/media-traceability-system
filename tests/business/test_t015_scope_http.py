"""Existing real handler positives and default refusals must survive scope integration."""

from business_app.main import create_app
from fastapi.testclient import TestClient

from tests.business.test_controls import control_context as control_context


def test_internal_inference_needs_work_proof_before_backend_or_object_reads(control_context):
    from tests.business.test_adapters_and_execution import inference_app, model_response

    class Backend:
        calls = 0

        def execute(self, payload):
            self.calls += 1
            return model_response(payload)

    backend = Backend()
    app, payload = inference_app(control_context, backend)
    app.state.inference_gateway.work_authorization = None
    with TestClient(app) as client:
        response = client.post(
            "/internal/v1/inference/" + payload["capability"],
            json=payload,
            headers={"Authorization": "Bearer self-owned-service-token"},
        )
    assert (response.status_code, response.json()["code"]) == (503, "CONDITIONAL_POLICY_UNCONFIGURED")
    assert backend.calls == 0


def test_default_application_still_refuses_unconfigured_real_policy(business_context):
    app = create_app(business_context["settings"], business_context["authority"])
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sources",
            params={"case_id": str(business_context["case_id"])},
            headers={"Authorization": "Bearer test-only-valid-token"},
        )
    assert response.status_code == 503
    assert "test-only-valid-token" not in response.text


def test_known_synthetic_case_can_still_use_real_source_list_handler(business_context):
    app = create_app(
        business_context["settings"],
        business_context["authority"],
        permission_authority=business_context["permission_authority"],
        conditional_permissions=business_context["conditional_permissions"],
        authorization_fence=business_context["authorization_fence"],
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/sources",
            params={"case_id": str(business_context["case_id"])},
            headers={"Authorization": "Bearer test-only-valid-token"},
        )
    assert response.status_code == 200
    assert [item["source_id"] for item in response.json()["items"]] == [str(business_context["source_id"])]
