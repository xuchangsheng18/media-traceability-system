"""Pure authority-proof checks; every authority here is an explicit synthetic fixture."""

import importlib
import importlib.util
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from business_app.errors import BusinessError
from business_app.types import Actor, Scope

NOW = datetime(2026, 10, 21, 0, 0, tzinfo=timezone.utc)


def registration_module():
    assert importlib.util.find_spec("business_app.source_registration") is not None, "Source registration is missing"
    return importlib.import_module("business_app.source_registration")


def inputs():
    module = registration_module()
    scope = Scope(Actor(uuid4(), uuid4()), uuid4())
    body = dict(
        case_id=str(scope.case_id),
        name="self-owned source",
        source_type="synthetic",
        authorization_ref="self-owned-test-authority/reference/1",
        purpose=["upload", "analysis"],
        expires_at="2026-11-21T00:00:00Z",
    )
    proof = module.SourceRegistrationProof(
        org_id=scope.actor.org_id,
        case_id=scope.case_id,
        source_type="synthetic",
        authorization_ref="self-owned-test-authority/reference/1",
        purpose=("upload", "analysis"),
        expires_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        authorization_status="verified",
        authorization_version="synthetic-authority/1",
        valid_until=NOW + timedelta(minutes=1),
    )
    return module, scope, body, proof


class SyntheticAuthority:
    def __init__(self, proof):
        self.proof = proof

    def resolve(self, scope, body, *, connection):
        return self.proof


def resolve(module, scope, body, authority):
    return module.resolve_registration_proof(authority, scope, body, connection=None, clock=lambda: NOW)


@pytest.mark.parametrize("status", ["pending", "verified"])
def test_registration_uses_authority_status_and_authorization_version(status):
    module, scope, body, proof = inputs()
    result = resolve(module, scope, body, SyntheticAuthority(replace(proof, authorization_status=status)))
    assert result.authorization_status == status
    assert result.authorization_version == "synthetic-authority/1"
    assert result.purpose == ("upload", "analysis")


@pytest.mark.parametrize(
    "field,value",
    [
        ("org_id", uuid4()),
        ("case_id", uuid4()),
        ("source_type", "public_licensed"),
        ("authorization_ref", "unrelated-reference"),
        ("purpose", ("upload",)),
        ("purpose", ("upload", "analysis", "training")),
        ("expires_at", None),
        ("expires_at", datetime(2026, 12, 21, tzinfo=timezone.utc)),
    ],
)
def test_registration_rejects_proof_bound_to_different_request(field, value):
    module, scope, body, proof = inputs()
    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, SyntheticAuthority(replace(proof, **{field: value})))
    assert error.value.http_status == 403


@pytest.mark.parametrize("status", ["expired", "revoked"])
def test_registration_cannot_use_expired_or_revoked_authority(status):
    module, scope, body, proof = inputs()
    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, SyntheticAuthority(replace(proof, authorization_status=status)))
    assert error.value.http_status == 403


@pytest.mark.parametrize(
    "field,value",
    [
        ("org_id", "not-a-uuid"),
        ("source_type", ["synthetic"]),
        ("purpose", ["upload", "analysis"]),
        ("purpose", ("upload", "upload")),
        ("authorization_version", ""),
        ("authorization_version", None),
        ("authorization_status", "approved"),
        ("authorization_status", ["verified"]),
        ("valid_until", NOW),
        ("valid_until", NOW.replace(tzinfo=None)),
        ("expires_at", datetime(2026, 11, 21)),
    ],
)
def test_registration_refuses_malformed_or_stale_authority_proof(field, value):
    module, scope, body, proof = inputs()
    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, SyntheticAuthority(replace(proof, **{field: value})))
    assert error.value.http_status == 503


def test_registration_requires_explicit_authority_and_typed_proof():
    module, scope, body, _ = inputs()
    for authority in (None, object(), SyntheticAuthority({"authorization_status": "verified"})):
        with pytest.raises(BusinessError) as error:
            resolve(module, scope, body, authority)
        assert error.value.http_status == 503


def test_registration_hides_unavailable_authority_internals():
    module, scope, body, _ = inputs()

    class Unavailable:
        def resolve(self, scope, body, *, connection):
            raise OSError("private-adapter-address")

    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, Unavailable())
    assert error.value.http_status == 503
    assert "private-adapter-address" not in str(error.value)


def test_registration_rejects_request_expired_at_the_authority_boundary():
    module, scope, body, proof = inputs()
    body["expires_at"] = NOW.isoformat()
    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, SyntheticAuthority(replace(proof, expires_at=NOW)))
    assert error.value.http_status == 403


def test_registration_contract_rejects_client_supplied_authorization_status():
    module, scope, body, proof = inputs()
    body["authorization_status"] = "verified"
    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, SyntheticAuthority(proof))
    assert error.value.http_status == 422


def test_registration_requires_authoritative_explicit_no_expiration():
    module, scope, body, proof = inputs()
    body["expires_at"] = None
    result = resolve(module, scope, body, SyntheticAuthority(replace(proof, expires_at=None)))
    assert result.expires_at is None


def test_registration_accepts_contract_uuid_case_insensitively():
    module, scope, body, proof = inputs()
    body["case_id"] = body["case_id"].upper()
    result = resolve(module, scope, body, SyntheticAuthority(proof))
    assert result.case_id == scope.case_id


def test_registration_authority_cannot_mutate_the_validated_request():
    module, scope, body, proof = inputs()

    class MutatingAuthority:
        def resolve(self, scope, body, *, connection):
            body["purpose"].append("training")
            return proof

    result = resolve(module, scope, body, MutatingAuthority())
    assert result.purpose == ("upload", "analysis")
    assert body["purpose"] == ["upload", "analysis"]


@pytest.mark.parametrize(
    "fraction,microsecond",
    [("1", 100000), ("12", 120000), ("123", 123000), ("1234", 123400), ("12345", 123450), ("123456", 123456)],
)
@pytest.mark.parametrize("time_and_zone", [("00:00:00", "Z"), ("08:00:00", "+08:00")])
def test_registration_preserves_each_contract_fractional_second_digit(fraction, microsecond, time_and_zone):
    module, scope, body, proof = inputs()
    time, zone = time_and_zone
    body["expires_at"] = f"2026-11-21T{time}.{fraction}{zone}"
    expiry = datetime(2026, 11, 21, microsecond=microsecond, tzinfo=timezone.utc)
    result = resolve(module, scope, body, SyntheticAuthority(replace(proof, expires_at=expiry)))
    assert result.expires_at == expiry
    assert result.expires_at.microsecond == microsecond


@pytest.mark.parametrize("fraction,microsecond", [("1000000", 100000), ("123456000", 123456), ("000000000", 0)])
@pytest.mark.parametrize("zone", ["Z", "+00:00"])
def test_registration_accepts_lossless_zero_tail_beyond_microseconds(fraction, microsecond, zone):
    module, scope, body, proof = inputs()
    body["expires_at"] = f"2026-11-21T00:00:00.{fraction}{zone}"
    expiry = datetime(2026, 11, 21, microsecond=microsecond, tzinfo=timezone.utc)
    result = resolve(module, scope, body, SyntheticAuthority(replace(proof, expires_at=expiry)))
    assert result.expires_at == expiry


@pytest.mark.parametrize("fraction,microsecond", [("1234561", 123456), ("1234569", 123457), ("000000001", 0)])
def test_registration_refuses_unrepresentable_authority_precision_without_rounding(fraction, microsecond):
    module, scope, body, proof = inputs()
    from business_app.contracts import validate_api

    body["expires_at"] = f"2026-11-21T00:00:00.{fraction}Z"
    # The request satisfies the public date-time contract. Its exact expiry
    # cannot be bound by the current datetime/PostgreSQL microsecond proof.
    validate_api("SourceCreate", body)
    expiry = datetime(2026, 11, 21, microsecond=microsecond, tzinfo=timezone.utc)
    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, SyntheticAuthority(replace(proof, expires_at=expiry)))
    assert error.value.code == "SOURCE_AUTHORIZATION_REQUIRED"
    assert error.value.http_status == 403


def test_registration_fractional_expiry_must_still_equal_the_actual_authority_proof():
    module, scope, body, proof = inputs()
    body["expires_at"] = "2026-11-21T08:00:00.1234+08:00"
    expiry = datetime(2026, 11, 21, microsecond=123401, tzinfo=timezone.utc)
    with pytest.raises(BusinessError) as error:
        resolve(module, scope, body, SyntheticAuthority(replace(proof, expires_at=expiry)))
    assert error.value.code == "SOURCE_AUTHORIZATION_REQUIRED" and error.value.http_status == 403


def test_registration_preserves_a_one_microsecond_remaining_authority_window():
    module, scope, body, proof = inputs()
    body["expires_at"] = "2026-10-21T08:00:00.000001+08:00"
    expiry = NOW + timedelta(microseconds=1)
    result = resolve(module, scope, body, SyntheticAuthority(replace(proof, expires_at=expiry)))
    assert result.expires_at == expiry
