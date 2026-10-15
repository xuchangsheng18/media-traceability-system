"""Normal versions and identifiers must not inherit the policy content-reference restriction."""

from business_app.contracts import validate_api


def test_plain_control_versions_and_identifiers_keep_their_own_contract():
    validate_api(
        "ReviewContext",
        dict(
            task_id="00000000-0000-4000-8000-000000000001",
            run_version=1,
            result_version=1,
            policy_version="policy-dev-1",
            snapshot_sha256="a" * 64,
            object_version=1,
            review_version=0,
        ),
    )
    validate_api(
        "SourceAuthorizationUpdate",
        dict(
            source_id="00000000-0000-4000-8000-000000000001",
            case_id="00000000-0000-4000-8000-000000000001",
            authorization_ref="self-owned-authority",
            authorization_version="fixture/2",
            purpose=["analysis"],
            authorization_status="revoked",
            expires_at=None,
        ),
    )


def test_policy_definition_alone_requires_content_addressed_reference():
    import pytest
    from business_app.errors import BusinessError

    with pytest.raises(BusinessError):
        validate_api(
            "PolicyDefinition",
            dict(definition_ref="mutable-reference", version="fixture/1", sha256="a" * 64, values={}),
        )
    validate_api(
        "PolicyDefinition",
        dict(definition_ref="urn:sha256:" + "a" * 64, version="fixture/1", sha256="a" * 64, values={}),
    )
