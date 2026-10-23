"""Pure request-context scheduling tests; no identity, permission or creation ALLOW."""

import asyncio
import copy
import hashlib
import importlib
import importlib.util
import json
import threading
from dataclasses import FrozenInstanceError, replace
from uuid import UUID, uuid4

import pytest
from business_app.errors import BusinessError
from business_app.permissions.context import current_authorization
from business_app.permissions.object_facts import digest
from business_app.permissions.types import Principal
from business_app.types import Actor
from starlette.concurrency import run_in_threadpool

NOW = 1_800_000_000


def module():
    assert importlib.util.find_spec("business_app.permissions.task_creation_context") is not None, (
        "Task creation context component is not implemented; structural boundary only, not an old authorization bypass"
    )
    return importlib.import_module("business_app.permissions.task_creation_context")


def principal():
    return Principal(Actor(uuid4(), uuid4()), "https://self-owned.example.test", "self-owned-subject", NOW + 600)


def body():
    return dict(
        case_id="abcdef12-3456-4789-9abc-def012345678",
        asset_id=str(uuid4()),
        scene="accident_rumor",
        policy_version="self-owned/策略/1",
        modules=["INGEST", "RESOURCE"],
        priority="normal",
    )


def fixed_clock():
    return NOW


def make(value=None, identity=None):
    return module().freeze_task_creation_context(
        principal() if identity is None else identity, body() if value is None else value, clock=fixed_clock
    )


def current(m):
    return m.current_task_creation_context(clock=fixed_clock)


def test_creation_context_component_exists():
    module()


def test_context_freezes_exact_unicode_a_and_independent_authorization_b():
    m = module()
    p, value = principal(), body()
    context = m.freeze_task_creation_context(p, value, clock=fixed_clock)
    expected = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert context.request.canonical_body == expected
    assert context.request.request_sha256 == hashlib.sha256(expected).hexdigest()
    assert context.authorization_request_digest == digest(dict(path={}, query={}, body=value))
    assert context.authorization_request_digest != context.request.request_sha256
    assert "策略".encode() in expected and b"\\u7b56" not in expected
    assert context.principal == p and context.principal is not p
    assert context.principal.actor is not p.actor and context.request.actor is not p.actor
    assert context.principal.actor.user_id is not p.actor.user_id
    assert context.request.actor == p.actor and context.request.modules == ("INGEST", "RESOURCE")
    assert current(m) is None and current_authorization() is None
    assert not hasattr(context, "allowed") and not hasattr(context, "authorized")
    with pytest.raises(FrozenInstanceError):
        context.authorization_request_digest = "a" * 64


def test_later_body_and_principal_object_mutations_do_not_change_snapshot():
    m = module()
    p, value = principal(), body()
    context = m.freeze_task_creation_context(p, value, clock=fixed_clock)
    original = copy.deepcopy(context)
    value["modules"].reverse()
    value["priority"] = "high"
    object.__setattr__(p.actor.user_id, "int", 0)
    object.__setattr__(p, "subject", "changed")
    assert context == original
    assert context.principal.actor.user_id.int != 0
    with m.bind_task_creation_context(context, clock=fixed_clock):
        assert current(m) == original
    assert current(m) is None


@pytest.mark.parametrize("changed", ["uuid-literal", "modules-order", "priority", "unicode-policy"])
def test_literal_request_changes_are_preserved_in_both_independent_digests(changed):
    value, p = body(), principal()
    before = make(value, p)
    if changed == "uuid-literal":
        value["case_id"] = value["case_id"].upper()
    elif changed == "modules-order":
        value["modules"].reverse()
    elif changed == "priority":
        value["priority"] = "high"
    else:
        value["policy_version"] += "/变化"
    after = make(value, p)
    assert before.request.request_sha256 != after.request.request_sha256
    assert before.authorization_request_digest != after.authorization_request_digest
    if changed == "uuid-literal":
        assert before.request.case_id == after.request.case_id
    assert (
        after.request.canonical_body
        == json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("issuer", " https://self-owned.example.test"),
        ("issuer", ""),
        ("issuer", "issuer\n"),
        ("subject", ""),
        ("subject", "subject\x00"),
        ("subject", "x" * 1025),
        ("expires_at", True),
        ("expires_at", "1800000600"),
        ("actor", None),
    ],
)
def test_invalid_principal_fields_refuse_before_context_binding(field, value):
    m = module()
    p = replace(principal(), **{field: value})
    with pytest.raises(BusinessError) as error:
        m.freeze_task_creation_context(p, body(), clock=fixed_clock)
    assert (error.value.code, error.value.http_status) == ("AUTHORITY_ACTOR_INVALID", 503)
    assert current(m) is None


@pytest.mark.parametrize("field,value", [("user_id", UUID(int=0)), ("org_id", UUID(int=0)), ("user_id", "not-uuid")])
def test_actor_requires_exact_nonzero_uuid(field, value):
    p = principal()
    p = replace(p, actor=replace(p.actor, **{field: value}))
    with pytest.raises(BusinessError) as error:
        make(identity=p)
    assert (error.value.code, error.value.http_status) == ("AUTHORITY_ACTOR_INVALID", 503)


@pytest.mark.parametrize("identity", [None, object(), {"issuer": "self-owned"}])
def test_non_principal_is_not_promoted_to_identity(identity):
    with pytest.raises(BusinessError) as error:
        module().freeze_task_creation_context(identity, body(), clock=fixed_clock)
    assert (error.value.code, error.value.http_status) == ("AUTHORITY_ACTOR_INVALID", 503)


@pytest.mark.parametrize("expiry", [NOW, NOW - 1])
def test_expired_identity_cannot_create_or_enter_context(expiry):
    m = module()
    p = replace(principal(), expires_at=expiry)
    with pytest.raises(BusinessError) as error:
        m.freeze_task_creation_context(p, body(), clock=fixed_clock)
    assert (error.value.code, error.value.http_status) == ("AUTHENTICATION_REQUIRED", 401)
    assert current(m) is None


@pytest.mark.parametrize(
    "clock", [lambda: None, lambda: True, lambda: "now", lambda: float("nan"), lambda: float("inf")]
)
def test_invalid_clock_does_not_issue_context(clock):
    with pytest.raises(BusinessError) as error:
        module().freeze_task_creation_context(principal(), body(), clock=clock)
    assert (error.value.code, error.value.http_status) == ("IDENTITY_AUTHORITY_UNAVAILABLE", 503)


def test_clock_exception_is_normalized_without_private_error_text():
    def broken_clock():
        raise RuntimeError("PRIVATE CLOCK INPUT")

    with pytest.raises(BusinessError) as error:
        module().freeze_task_creation_context(principal(), body(), clock=broken_clock)
    assert error.value.code == "IDENTITY_AUTHORITY_UNAVAILABLE"
    assert "PRIVATE" not in str(error.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_id", str(UUID(int=0))),
        ("asset_id", str(UUID(int=0))),
        ("asset_id", "invalid"),
        ("modules", ["INGEST", "INGEST"]),
        ("modules", []),
        ("priority", "urgent"),
        ("policy_version", "\ud800"),
    ],
)
def test_invalid_public_body_never_creates_a_context(field, value):
    m = module()
    value = dict(body(), **{field: value})
    with pytest.raises(BusinessError) as error:
        m.freeze_task_creation_context(principal(), value, clock=fixed_clock)
    assert (error.value.code, error.value.http_status) == ("INPUT_INVALID", 422)
    assert current(m) is None


@pytest.mark.parametrize("field", ["actor", "case_id", "asset_id", "modules", "canonical_body", "request_sha256"])
def test_direct_request_field_replacement_cannot_enter_context(field):
    m = module()
    context = make()
    value = {
        "actor": Actor(uuid4(), context.principal.actor.org_id),
        "case_id": uuid4(),
        "asset_id": uuid4(),
        "modules": tuple(reversed(context.request.modules)),
        "canonical_body": context.request.canonical_body.replace(b'"normal"', b'"high"'),
        "request_sha256": "a" * 64,
    }[field]
    forged = replace(context, request=replace(context.request, **{field: value}))
    with pytest.raises(BusinessError) as error:
        with m.bind_task_creation_context(forged, clock=fixed_clock):
            pytest.fail("Mismatched context entered")
    assert (error.value.code, error.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)
    assert current(m) is None


@pytest.mark.parametrize("value", ["a" * 64, "A" * 64, "bad", None, True])
def test_direct_authorization_digest_substitution_is_refused(value):
    m = module()
    forged = replace(make(), authorization_request_digest=value)
    with pytest.raises(BusinessError) as error:
        with m.bind_task_creation_context(forged, clock=fixed_clock):
            pytest.fail("Bad digest entered")
    assert error.value.code == "AUTHORITY_SCOPE_INVALID"


@pytest.mark.parametrize("construction", ["uninitialized", "deleted-principal"])
def test_missing_principal_is_a_business_scope_refusal(construction):
    m = module()
    if construction == "uninitialized":
        damaged = object.__new__(m.TaskCreationContext)
    else:
        damaged = make()
        object.__delattr__(damaged, "principal")
    with pytest.raises(BusinessError) as error:
        with m.bind_task_creation_context(damaged, clock=fixed_clock):
            pytest.fail("Damaged context entered")
    assert (error.value.code, error.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)
    assert current(m) is None


def test_direct_valid_dataclass_is_revalidated_and_copied_not_authorized():
    m = module()
    value = make()
    direct = m.TaskCreationContext(value.principal, value.request, value.authorization_request_digest)
    with m.bind_task_creation_context(direct, clock=fixed_clock) as entered:
        assert entered == value and entered is not direct
        assert entered.principal is not direct.principal and entered.request is not direct.request
        assert current_authorization() is None
    assert current(m) is None


@pytest.mark.parametrize("value", [None, object(), {"request": "not-context"}])
def test_non_context_cannot_enter(value):
    with pytest.raises(BusinessError) as error:
        with module().bind_task_creation_context(value, clock=fixed_clock):
            pytest.fail("Unexpected context")
    assert error.value.code == "AUTHORITY_SCOPE_INVALID"


def test_parent_binding_and_each_getter_are_detached_from_caller_tampering():
    m = module()
    source = make()
    expected = copy.deepcopy(source)
    with m.bind_task_creation_context(source, clock=fixed_clock) as entered:
        object.__setattr__(source, "authorization_request_digest", "a" * 64)
        object.__setattr__(source.principal.actor.user_id, "int", 0)
        object.__setattr__(entered.request, "priority", "high")
        object.__setattr__(entered.principal.actor, "org_id", UUID(int=0))
        first = current(m)
        object.__setattr__(first.principal, "subject", "changed")
        object.__setattr__(first.principal.actor.org_id, "int", 0)
        assert current(m) == expected
        assert current(m) is not current(m)
    assert current(m) is None


def test_direct_principal_actor_replacement_cannot_rebind_the_frozen_request():
    m = module()
    context = make()
    forged = replace(
        context, principal=replace(context.principal, actor=Actor(uuid4(), context.principal.actor.org_id))
    )
    with pytest.raises(BusinessError) as error:
        with m.bind_task_creation_context(forged, clock=fixed_clock):
            pytest.fail("Another actor entered the frozen request")
    assert error.value.code == "AUTHORITY_SCOPE_INVALID"
    assert current(m) is None


def test_entry_expiry_after_token_install_restores_the_existing_parent():
    m = module()
    outer, inner = make(), make()
    ticks = iter([NOW, NOW + 600])
    with m.bind_task_creation_context(outer, clock=fixed_clock):
        with pytest.raises(BusinessError) as error:
            with m.bind_task_creation_context(inner, clock=lambda: next(ticks)):
                pytest.fail("Expired yielded context")
        assert error.value.code == "AUTHENTICATION_REQUIRED"
        assert current(m) == outer
    assert current(m) is None


def test_bad_getter_clock_fails_without_erasing_parent_state():
    m = module()
    context = make()
    with m.bind_task_creation_context(context, clock=fixed_clock):
        with pytest.raises(BusinessError) as error:
            m.current_task_creation_context(clock=lambda: True)
        assert error.value.code == "IDENTITY_AUTHORITY_UNAVAILABLE"
        assert current(m) == context
    assert current(m) is None


def test_context_rechecks_identity_expiry_on_entry_and_each_read():
    m = module()
    context = make()
    with pytest.raises(BusinessError) as error:
        with m.bind_task_creation_context(context, clock=lambda: NOW + 600):
            pytest.fail("Expired entry")
    assert error.value.code == "AUTHENTICATION_REQUIRED"
    with m.bind_task_creation_context(context, clock=fixed_clock):
        with pytest.raises(BusinessError) as error:
            m.current_task_creation_context(clock=lambda: NOW + 600)
        assert error.value.code == "AUTHENTICATION_REQUIRED"
        assert current(m) == context
    assert current(m) is None


def test_nested_exception_restores_exact_parent_and_outer_finally_clears():
    m = module()
    outer, inner = make(), make()
    with pytest.raises(RuntimeError, match="self-owned failure"):
        with m.bind_task_creation_context(outer, clock=fixed_clock):
            with pytest.raises(ValueError, match="nested"):
                with m.bind_task_creation_context(inner, clock=fixed_clock):
                    assert current(m) == inner
                    raise ValueError("nested")
            assert current(m) == outer
            raise RuntimeError("self-owned failure")
    assert current(m) is None


def test_concurrent_async_requests_keep_distinct_context_through_real_scheduling():
    m = module()
    first, second = make(), make()

    async def scenario():
        ready = [asyncio.Event(), asyncio.Event()]

        async def request(index, context):
            with m.bind_task_creation_context(context, clock=fixed_clock):
                ready[index].set()
                await ready[1 - index].wait()
                await asyncio.sleep(0)
                assert current(m) == context
                return current(m)

        assert current(m) is None
        actual = await asyncio.gather(request(0, first), request(1, second))
        assert actual == [first, second]
        assert current(m) is None

    asyncio.run(scenario())
    assert current(m) is None


def test_starlette_threadpool_reads_parent_snapshot_without_mutating_parent_slot():
    m = module()
    outer, inner = make(), make()

    async def scenario():
        parent_thread = threading.get_ident()

        def worker():
            assert threading.get_ident() != parent_thread
            observed = current(m)
            assert observed == outer
            object.__setattr__(observed.request, "priority", "high")
            assert current(m) == outer
            with m.bind_task_creation_context(inner, clock=fixed_clock):
                assert current(m) == inner
            assert current(m) == outer
            return current(m)

        with m.bind_task_creation_context(outer, clock=fixed_clock):
            assert await run_in_threadpool(worker) == outer
            assert current(m) == outer
        assert current(m) is None
        assert await run_in_threadpool(lambda: current(m)) is None

    asyncio.run(scenario())


def test_cancelled_async_request_resets_its_slot_without_leaking_to_parent():
    m = module()
    context, cleaned = make(), []

    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()

        async def request():
            try:
                with m.bind_task_creation_context(context, clock=fixed_clock):
                    entered.set()
                    await release.wait()
            finally:
                cleaned.append(current(m))

        task = asyncio.create_task(request())
        await entered.wait()
        assert current(m) is None
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert current(m) is None

    asyncio.run(scenario())
    assert cleaned == [None]
