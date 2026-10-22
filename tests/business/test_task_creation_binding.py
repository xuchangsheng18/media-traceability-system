"""Pure binding tests; all plan providers here are explicit self-owned fixtures."""

import hashlib
import importlib
import importlib.util
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone, tzinfo
from uuid import UUID, uuid4

import pytest
from business_app.controls.common import canonical
from business_app.errors import BusinessError
from business_app.types import Actor, Scope

NOW = datetime(2026, 10, 22, tzinfo=timezone.utc)


def module():
    assert importlib.util.find_spec("business_app.task_creation") is not None, "Task creation binding is missing"
    return importlib.import_module("business_app.task_creation")


def inputs():
    scope = Scope(Actor(uuid4(), uuid4()), uuid4())
    body = dict(
        case_id=str(scope.case_id),
        asset_id=str(uuid4()),
        scene="accident_rumor",
        policy_version="self-owned-test/policy/1",
        modules=["INGEST", "RESOURCE"],
        priority="normal",
    )
    return scope, body


def bound():
    m = module()
    scope, body = inputs()
    request = m.freeze_task_create(scope, body)
    proof = m.TaskPlanProof(
        request=request,
        authority_version="self-owned/1",
        policy_sha256="a" * 64,
        plan_id="self-owned-plan",
        plan_version="1",
        plan_sha256="b" * 64,
        capability_id="self-owned-capability",
        capability_version="1",
        capability_sha256="c" * 64,
        authorized=True,
        valid_until=NOW + timedelta(minutes=1),
    )
    return m, scope, body, request, proof


class Provider:
    def __init__(self, proof):
        self.proof = proof
        self.seen = []

    def resolve(self, request, *, connection):
        self.seen.append((request, connection))
        return self.proof


def resolve(m, request, provider, clock=lambda: NOW, connection=None):
    return m.resolve_task_plan(provider, request, connection=connection, clock=clock)


def test_freeze_preserves_existing_contract_and_exact_canonical_digest():
    m = module()
    scope, body = inputs()
    request = m.freeze_task_create(scope, body)
    assert request.actor == scope.actor and request.actor is not scope.actor
    assert request.case_id == scope.case_id and request.asset_id == UUID(body["asset_id"])
    assert request.modules == ("INGEST", "RESOURCE") and request.priority == "normal"
    assert request.canonical_body == canonical(body)
    assert request.request_sha256 == hashlib.sha256(canonical(body)).hexdigest()
    assert m.freeze_task_create(scope, dict(reversed(list(body.items())))) == request
    with pytest.raises(FrozenInstanceError):
        request.priority = "high"
    body["modules"].append("OPS")
    assert request.modules == ("INGEST", "RESOURCE")


@pytest.mark.parametrize(
    "field,value",
    [("modules", ["RESOURCE", "INGEST"]), ("priority", "high"), ("policy_version", " self-owned-test/policy/1 ")],
)
def test_request_digest_preserves_array_order_priority_and_literal_policy(field, value):
    m = module()
    scope, body = inputs()
    before = m.freeze_task_create(scope, body)
    body[field] = value
    after = m.freeze_task_create(scope, body)
    assert before.request_sha256 != after.request_sha256
    assert after.canonical_body == canonical(body)


def test_uuid_literal_case_is_preserved_in_digest_but_parsed_in_binding():
    m = module()
    scope, body = inputs()
    body["asset_id"] = "abcdef12-3456-4789-9abc-def012345678"
    before = m.freeze_task_create(scope, body)
    body["asset_id"] = body["asset_id"].upper()
    after = m.freeze_task_create(scope, body)
    assert before.asset_id == after.asset_id
    assert before.request_sha256 != after.request_sha256


@pytest.mark.parametrize(
    "field,value",
    [
        ("modules", []),
        ("modules", ["INGEST", "INGEST"]),
        ("modules", ["UNKNOWN"]),
        ("scene", "unknown"),
        ("priority", "urgent"),
        ("policy_version", ""),
        ("policy_version", "\ud800"),
        ("asset_id", "not-uuid"),
        ("case_id", None),
    ],
)
def test_invalid_public_request_is_rejected_without_provider(field, value):
    m = module()
    scope, body = inputs()
    body[field] = value
    with pytest.raises(BusinessError) as error:
        m.freeze_task_create(scope, body)
    assert (error.value.code, error.value.http_status) == ("INPUT_INVALID", 422)


def test_public_request_cannot_supply_provider_or_plan_fields():
    m = module()
    scope, body = inputs()
    body["plan_sha256"] = "d" * 64
    with pytest.raises(BusinessError) as error:
        m.freeze_task_create(scope, body)
    assert error.value.http_status == 422


@pytest.mark.parametrize("kind", ["actor", "organization", "case", "actor-type", "scope-type"])
def test_server_scope_requires_existing_nonzero_uuid_binding(kind):
    m = module()
    scope, body = inputs()
    zero = UUID(int=0)
    invalid_actor = Scope(scope.actor, scope.case_id)
    object.__setattr__(invalid_actor, "actor", None)
    scopes = {
        "actor": Scope(Actor(zero, scope.actor.org_id), scope.case_id),
        "organization": Scope(Actor(scope.actor.user_id, zero), scope.case_id),
        "case": Scope(scope.actor, zero),
        "actor-type": invalid_actor,
        "scope-type": object(),
    }
    with pytest.raises(BusinessError) as error:
        m.freeze_task_create(scopes[kind], body)
    assert (error.value.code, error.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)


def test_contract_valid_cross_case_request_is_denied():
    m = module()
    scope, body = inputs()
    body["case_id"] = str(uuid4())
    with pytest.raises(BusinessError) as error:
        m.freeze_task_create(scope, body)
    assert error.value.http_status == 403


def test_explicit_provider_binding_is_copied_and_connection_forwarded_without_io():
    m, _, _, request, proof = bound()
    provider, connection = Provider(proof), object()
    actual = resolve(m, request, provider, connection=connection)
    assert actual == proof and actual is not proof and actual.request is not proof.request
    assert provider.seen == [(request, connection)] and provider.seen[0][0] is not request
    object.__setattr__(proof, "plan_sha256", "d" * 64)
    object.__setattr__(proof.request.actor, "user_id", uuid4())
    assert actual.plan_sha256 == "b" * 64 and actual.request.actor != proof.request.actor
    assert not hasattr(actual, "task_id")


@pytest.mark.parametrize("kind", ["absent", "noncallable", "dict", "candidate"])
def test_missing_or_untyped_provider_is_never_execution_authority(kind):
    m, _, _, request, _ = bound()
    provider = {
        "absent": None,
        "noncallable": object(),
        "dict": Provider({"authorized": True}),
        "candidate": Provider(object()),
    }[kind]
    with pytest.raises(BusinessError) as error:
        resolve(m, request, provider)
    assert (error.value.code, error.value.http_status) == ("CONDITIONAL_FACTS_UNAVAILABLE", 503)


@pytest.mark.parametrize(
    "exception,status",
    [
        (OSError("private-provider-detail"), 503),
        (BusinessError("DATABASE_UNAVAILABLE", 503), 503),
        (BusinessError("HTTP_FORBIDDEN", 403), 403),
    ],
)
def test_provider_errors_are_normalized_without_private_detail(exception, status):
    m, _, _, request, _ = bound()

    class Failing:
        def resolve(self, request, *, connection):
            raise exception

    with pytest.raises(BusinessError) as error:
        resolve(m, request, Failing())
    assert error.value.http_status == status and "private-provider-detail" not in str(error.value)


@pytest.mark.parametrize("field", ["actor", "organization", "case", "asset", "scene", "modules", "policy", "priority"])
def test_well_formed_proof_for_other_context_is_denied(field):
    m, scope, body, request, proof = bound()
    if field == "actor":
        scope = Scope(Actor(uuid4(), scope.actor.org_id), scope.case_id)
    elif field == "organization":
        scope = Scope(Actor(scope.actor.user_id, uuid4()), scope.case_id)
    elif field == "case":
        scope = Scope(scope.actor, uuid4())
        body["case_id"] = str(scope.case_id)
    else:
        key, value = {
            "asset": ("asset_id", str(uuid4())),
            "scene": ("scene", "harmful_content"),
            "modules": ("modules", ["OPS"]),
            "policy": ("policy_version", "other/1"),
            "priority": ("priority", "high"),
        }[field]
        body[key] = value
    other = m.freeze_task_create(scope, body)
    with pytest.raises(BusinessError) as error:
        resolve(m, request, Provider(replace(proof, request=other)))
    assert error.value.http_status == 403


@pytest.mark.parametrize(
    "field,value",
    [
        ("policy_sha256", "wrong"),
        ("plan_sha256", "B" * 64),
        ("capability_sha256", None),
        ("plan_id", ""),
        ("plan_version", "x" * 129),
        ("authority_version", []),
        ("capability_id", None),
        ("authorized", 1),
        ("valid_until", NOW),
        ("valid_until", NOW.replace(tzinfo=None)),
    ],
)
def test_malformed_or_expired_proof_is_unavailable(field, value):
    m, _, _, request, proof = bound()
    with pytest.raises(BusinessError) as error:
        resolve(m, request, Provider(replace(proof, **{field: value})))
    assert error.value.http_status == 503


def test_explicit_revocation_is_denied():
    m, _, _, request, proof = bound()
    with pytest.raises(BusinessError) as error:
        resolve(m, request, Provider(replace(proof, authorized=False)))
    assert error.value.http_status == 403


def test_provider_cannot_mutate_validated_request_to_obtain_other_plan():
    m, _, body, request, proof = bound()

    class Mutating:
        def resolve(self, received, *, connection):
            object.__setattr__(received, "modules", ("OPS",))
            return replace(proof, request=received)

    with pytest.raises(BusinessError) as error:
        resolve(m, request, Mutating())
    assert error.value.http_status == 503
    assert request.modules == ("INGEST", "RESOURCE") and body["modules"] == ["INGEST", "RESOURCE"]


def test_forged_snapshot_digest_is_not_accepted():
    m, _, _, request, proof = bound()
    forged = replace(request, request_sha256="d" * 64)
    with pytest.raises(BusinessError) as error:
        resolve(m, forged, Provider(replace(proof, request=forged)))
    assert error.value.http_status == 503


@pytest.mark.parametrize("clock", [lambda: NOW.replace(tzinfo=None), lambda: None])
def test_invalid_clock_cannot_grant_binding(clock):
    m, _, _, request, proof = bound()
    with pytest.raises(BusinessError) as error:
        resolve(m, request, Provider(proof), clock=clock)
    assert error.value.http_status == 503


def test_clock_failure_is_normalized():
    m, _, _, request, proof = bound()

    def broken():
        raise OSError("private-clock-detail")

    with pytest.raises(BusinessError) as error:
        resolve(m, request, Provider(proof), clock=broken)
    assert error.value.http_status == 503 and "private-clock-detail" not in str(error.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("authority_version", "2"),
        ("policy_sha256", "d" * 64),
        ("plan_id", "other"),
        ("plan_version", "2"),
        ("plan_sha256", "d" * 64),
        ("capability_id", "other"),
        ("capability_version", "2"),
        ("capability_sha256", "d" * 64),
    ],
)
def test_recheck_rejects_all_stable_binding_changes_even_with_same_version(field, value):
    m, _, _, _, proof = bound()
    with pytest.raises(BusinessError) as error:
        m.recheck_task_plan(Provider(replace(proof, **{field: value})), proof, connection=None, clock=lambda: NOW)
    assert (error.value.code, error.value.http_status) == ("AUTHORIZATION_CHANGED", 503)


def test_recheck_allows_only_unchanged_binding_with_extended_freshness():
    m, _, _, _, proof = bound()
    extended = replace(proof, valid_until=proof.valid_until + timedelta(seconds=30))
    actual = m.recheck_task_plan(Provider(extended), proof, connection=None, clock=lambda: NOW)
    assert actual == extended


def test_recheck_rejects_shortened_freshness_and_expired_original():
    m, _, _, _, proof = bound()
    with pytest.raises(BusinessError) as error:
        m.recheck_task_plan(
            Provider(replace(proof, valid_until=NOW + timedelta(seconds=10))), proof, connection=None, clock=lambda: NOW
        )
    assert error.value.code == "AUTHORIZATION_CHANGED"
    with pytest.raises(BusinessError) as error:
        m.recheck_task_plan(
            Provider(replace(proof, valid_until=NOW + timedelta(minutes=2))),
            proof,
            connection=None,
            clock=lambda: proof.valid_until,
        )
    assert error.value.http_status == 503


def test_returned_deadline_cannot_change_with_provider_owned_mutable_timezone():
    m, _, _, request, proof = bound()

    class MutableZone(tzinfo):
        hours = 0

        def utcoffset(self, value):
            return timedelta(hours=self.hours)

        def dst(self, value):
            return timedelta(0)

        def tzname(self, value):
            return "self-owned-mutable-test-zone"

    zone = MutableZone()
    actual = resolve(m, request, Provider(replace(proof, valid_until=proof.valid_until.replace(tzinfo=zone))))
    zone.hours = 2
    assert actual.valid_until == NOW + timedelta(minutes=1)
