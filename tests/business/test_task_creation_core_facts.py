"""Actual isolated SQL source facts plus explicit test-only authority probes."""

import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

import psycopg
import pytest
from business_app.errors import BusinessError
from business_app.permissions.object_facts import ObjectFactsReader
from business_app.permissions.rule_types import ConditionFacts
from business_app.permissions.task_creation_context import bind_task_creation_context, freeze_task_creation_context
from business_app.scope_context import current_scope_transaction

from tests.business.test_t015_scope_sql import principal, two_cases


@contextmanager
def arranged(context, *, task_creation=None, supplemental=None):
    records = two_cases(context)
    identity = principal(context)
    body = dict(
        case_id=str(context["case_id"]),
        asset_id=str(records[0]["asset"]),
        scene="accident_rumor",
        policy_version="self-owned/policy/1",
        modules=["MEDIA"],
        priority="normal",
    )
    reader = ObjectFactsReader(context["database"], task_creation=task_creation, supplemental=supplemental)
    with bind_task_creation_context(freeze_task_creation_context(identity, body)):
        target = reader.resolve_http(identity, "createTask", {}, {}, body)
        yield reader, identity, target, body, records[0]


def test_create_task_source_analysis_is_real_core_and_missing_capabilities_stay_unknown(business_context):
    with arranged(business_context) as (reader, identity, target, _body, _record):
        before = reader.read(identity, "createTask", target)
        after = reader.read(identity, "createTask", target)
    assert before.checks["source"] is before.checks["analysis_purpose"] is True
    assert before.checks["model_task_version"] is before.checks["capability"] is None
    assert "classification" not in before.checks
    assert before.version_digest == after.version_digest


class NeverFacts:
    def read(self, *args, **kwargs):
        raise AssertionError("Unresolved capability reader must not mask a definitive source refusal")


@pytest.mark.parametrize("refusal", ["revoked", "pending", "purpose", "expired"])
def test_create_task_definitive_source_refusal_keeps_false_and_freshness(business_context, refusal):
    with arranged(business_context, task_creation=NeverFacts()) as (reader, identity, target, _body, record):
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            if refusal in {"revoked", "pending"}:
                connection.execute(
                    "UPDATE mt.source_registry SET authorization_status=%s WHERE source_id=%s",
                    (refusal, record["source"]),
                )
            elif refusal == "purpose":
                connection.execute(
                    "UPDATE mt.source_registry SET purpose=ARRAY['training'] WHERE source_id=%s", (record["source"],)
                )
            else:
                connection.execute(
                    "UPDATE mt.source_registry SET expires_at=%s WHERE source_id=%s",
                    (datetime.now(timezone.utc) - timedelta(seconds=10), record["source"]),
                )
        facts = reader.read(identity, "createTask", target)
    assert facts.checks["source"] is facts.checks["analysis_purpose"] is False
    assert facts.checks["capability"] is facts.checks["model_task_version"] is None
    # A stale fact envelope must not turn a definitive false into generic503.
    assert facts.valid_until > time.time()


@pytest.mark.parametrize("name", ["analysis_purpose", "capability", "model_task_version"])
def test_generic_supplement_cannot_supply_task_core_authority(business_context, name):
    class UnboundSupplement:
        def read(self, identity, operation, target, *, connection):
            return ConditionFacts(identity, target, MappingProxyType({name: True}), "c" * 64, time.time() + 30)

    with arranged(business_context, supplemental=UnboundSupplement()) as (reader, identity, target, _body, _record):
        with pytest.raises(BusinessError) as error:
            reader.read(identity, "createTask", target)
    assert error.value.code == "CONDITIONAL_FACTS_UNAVAILABLE" and error.value.http_status == 503


def test_dedicated_task_port_receives_current_exact_lookup_connection(business_context):
    observations = []

    class ExplicitProbe:
        def read(self, identity, operation, target, *, connection):
            root = current_scope_transaction()
            assert root is not None and root.connection is connection
            assert root.scope.operation_id == operation == "createTask"
            assert root.scope.lookup is not None
            assert root.scope.lookup.identifier == target.object_id
            observations.append(root)
            return ConditionFacts(
                identity,
                target,
                MappingProxyType(dict(model_task_version=None, capability=False)),
                "d" * 64,
                time.time() + 30,
            )

    with arranged(business_context, task_creation=ExplicitProbe()) as (reader, identity, target, _body, _record):
        facts = reader.read(identity, "createTask", target)
    assert len(observations) == 1
    assert facts.checks["capability"] is False and facts.checks["model_task_version"] is None


def test_create_task_valid_source_with_invalid_asset_is_conflict(business_context):
    with arranged(business_context) as (reader, identity, target, _body, record):
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            connection.execute("UPDATE mt.media_asset SET state='QUARANTINED' WHERE asset_id=%s", (record["asset"],))
        # Resolving again takes the actual new row_version, not stale target409.
        target = reader.resolve_http(identity, "createTask", {}, {}, _body)
        with pytest.raises(BusinessError) as error:
            reader.read(identity, "createTask", target)
    assert (error.value.code, error.value.http_status) == ("ASSET_STATE_CONFLICT", 409)


@pytest.mark.parametrize("configured", [False, True])
def test_task_creation_facts_advertisement_requires_explicit_provider(business_context, configured):
    from business_app.scope_catalog import registered_operation

    reader = ObjectFactsReader(business_context["database"], task_creation=NeverFacts() if configured else None)
    assert ("createTask" in reader.supported_operation_ids) is configured
    # SQL scope support alone is not a mounted HTTP route or an ALLOW.
    assert registered_operation("createTask") is True
