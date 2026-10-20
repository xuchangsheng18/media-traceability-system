"""Work delegation and service identity are separate, bound trusted inputs."""

from contextlib import contextmanager
from dataclasses import replace
from uuid import uuid4

import pytest
from business_app.errors import BusinessError
from business_app.types import Actor, Scope

from tests.business.test_t014_permissions import permission_module


def trust_fixture():
    module = permission_module("work")
    types = permission_module("rule_types")
    actor = Actor(uuid4(), uuid4())
    subject = types.ExecutionSubject(actor, uuid4(), "synthetic-map-v1", "upload_validation", uuid4())
    clock = [1000.0]

    class Delegations:
        value = module.WorkDelegation(subject, "a" * 64, 1004.0)

        def read(self, bound_actor, kind, identifier):
            if (bound_actor, kind, identifier) != (actor, "upload_validation", subject.work_id):
                raise RuntimeError("Unknown delegation")
            return self.value

    class Services:
        value = module.WorkServiceProof("synthetic-validator", "upload_validation", subject.work_id, "b" * 64, 1002.0)

        def read(self, service_id, kind, identifier):
            if (service_id, kind, identifier) != ("synthetic-validator", "upload_validation", subject.work_id):
                raise RuntimeError("Unknown service identity")
            return self.value

    delegations, services = Delegations(), Services()
    trust = module.WorkTrust(
        delegations, services, {"upload_validation": "synthetic-validator"}, clock=lambda: clock[0]
    )
    return module, subject, clock, delegations, services, trust


def test_work_subject_uses_live_delegation_and_distinct_service_without_a_user_token():
    _, subject, _, _, _, trust = trust_fixture()
    assert trust.resolve(Scope(subject.actor, uuid4()), subject.work_kind, subject.work_id) == subject
    fact = trust.read(subject)
    assert fact.subject == subject and fact.valid_until == 1002.0
    assert not hasattr(subject, "expires_at") and not hasattr(subject, "issuer")


@pytest.mark.parametrize(
    "defect",
    [
        "delegation_missing",
        "service_missing",
        "actor",
        "identity",
        "work",
        "service",
        "service_work",
        "delegation_expiry",
        "service_expiry",
        "malformed",
    ],
)
def test_work_trust_rejects_unbound_unknown_expired_or_truthy_facts(defect):
    module, subject, _, delegations, services, trust = trust_fixture()
    if defect in {"delegation_missing", "service_missing"}:
        trust = module.WorkTrust(
            None if defect == "delegation_missing" else delegations,
            None if defect == "service_missing" else services,
            {"upload_validation": "synthetic-validator"},
            clock=lambda: 1000.0,
        )
    elif defect in {"actor", "identity", "work"}:
        if defect == "actor":
            changed = replace(subject, actor=Actor(uuid4(), subject.actor.org_id))
        elif defect == "identity":
            changed = replace(subject, identity_id=uuid4())
        else:
            changed = replace(subject, work_id=uuid4())
        delegations.value = replace(delegations.value, subject=changed)
    elif defect in {"service", "service_work", "service_expiry"}:
        if defect == "service":
            services.value = replace(services.value, service_id=str(subject.actor.user_id))
        elif defect == "service_work":
            services.value = replace(services.value, work_id=uuid4())
        else:
            services.value = replace(services.value, valid_until=1000.0)
    elif defect == "delegation_expiry":
        delegations.value = replace(delegations.value, valid_until=1000.0)
    else:
        services.value = True
    with pytest.raises(BusinessError) as denied:
        trust.read(subject)
    assert denied.value.http_status == 503


def test_noop_work_port_cannot_open_an_unfenced_business_path():
    from business_app.permissions.context import protected_work

    class Noop:
        @contextmanager
        def open(self, scope, kind, identifier, operation_id):
            yield

    side_effects = []
    with pytest.raises(BusinessError) as denied:
        with protected_work(
            Noop(), Scope(Actor(uuid4(), uuid4()), uuid4()), "upload_validation", uuid4(), "validateUploadWork"
        ):
            side_effects.append("business write would run")
    assert denied.value.http_status == 503
    assert side_effects == []
