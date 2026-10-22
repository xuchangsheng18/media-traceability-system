"""Self-owned projection fixtures; no database or identity authority is fabricated."""

import base64
import copy
import hashlib
import hmac
import json
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from business_app.errors import BusinessError
from business_app.history.evidence_paging import page_evidence
from business_app.types import Actor, ResultKey, Scope


@pytest.fixture
def paging():
    scope = Scope(Actor(uuid4(), uuid4()), uuid4())
    key = ResultKey(uuid4(), 3, 2)
    # Deliberately non-UUID-sorted order is the immutable producer's order.
    items = [
        {
            "evidence_id": str(UUID(int=value)),
            "case_id": str(scope.case_id),
            "task_id": str(key.task_id),
            "run_version": key.run_version,
            "result_version": key.result_version,
            "kind": "original",
            "asset_id": str(uuid4()),
            "object_ref": None,
            "time_range": None,
            "bbox": None,
            "mapping_version": "synthetic-paging-test/1",
            "model_name": None,
            "model_version": None,
            "authorization_version": "synthetic-only",
            "sha256": "1" * 64,
            "version": 1,
            "created_at": "2026-10-22T00:00:00Z",
        }
        for value in [5, 1, 4, 2, 3]
    ]
    return {"items": items, "next_cursor": None}, scope, key, uuid4().hex


def page(paging, **kwargs):
    return page_evidence(*paging, **kwargs)


def assert_error(code, status, function):
    with pytest.raises(BusinessError) as failure:
        function()
    assert (failure.value.code, failure.value.http_status) == (code, status)


def test_traversal_preserves_order_and_original_projection(paging):
    before = copy.deepcopy(paging[0])
    selected = []
    cursor = None
    for size in [2, 2, 1]:
        response = page(paging, limit=2, cursor=cursor)
        assert len(response["items"]) == size
        selected.extend(response["items"])
        cursor = response["next_cursor"]
        if size == 2:
            assert len(cursor) == 96 and "=" not in cursor
    assert cursor is None and selected == before["items"]
    assert paging[0] == before


@pytest.mark.parametrize("count,limit", [(0, 1), (1, 1), (5, 5), (5, 100)])
def test_complete_or_empty_page_has_no_continuation(paging, count, limit):
    body, scope, key, secret = paging
    selected = dict(body, items=body["items"][:count])
    assert page_evidence(selected, scope, key, secret, limit) == selected


@pytest.mark.parametrize("limit", [0, -1, 101, True, 1.0, "2", None])
def test_direct_invalid_bounds_fail_closed(paging, limit):
    assert_error("PAGE_CURSOR_INVALID", 422, lambda: page(paging, limit=limit))


@pytest.mark.parametrize("cursor", ["", "A" * 129, 42, b"not-text"])
def test_direct_invalid_cursor_bounds_fail_closed(paging, cursor):
    assert_error("PAGE_CURSOR_INVALID", 422, lambda: page(paging, cursor=cursor))


@pytest.mark.parametrize("secret", ["", "x" * 31, None])
def test_no_default_or_short_secret(paging, secret):
    body, scope, key, _ = paging
    assert_error("RESPONSE_CONTRACT_UNAVAILABLE", 503, lambda: page_evidence(body, scope, key, secret))


@pytest.mark.parametrize("part", [0, 9, 39, 40, 71])
def test_each_token_component_is_authenticated(paging, part):
    token = page(paging, limit=2)["next_cursor"]
    raw = bytearray(base64.urlsafe_b64decode(token))
    raw[part] ^= 1
    altered = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    assert_error("PAGE_CURSOR_INVALID", 422, lambda: page(paging, limit=2, cursor=altered))


@pytest.mark.parametrize("field", ["actor", "org", "case", "task", "run", "result", "limit", "secret"])
def test_cursor_cannot_cross_binding(paging, field):
    body, scope, key, secret = paging
    token = page(paging, limit=2)["next_cursor"]
    limit = 2
    if field == "actor":
        scope = replace(scope, actor=replace(scope.actor, user_id=uuid4()))
    elif field == "org":
        scope = replace(scope, actor=replace(scope.actor, org_id=uuid4()))
    elif field == "case":
        scope = replace(scope, case_id=uuid4())
    elif field == "task":
        key = replace(key, task_id=uuid4())
    elif field == "run":
        key = replace(key, run_version=key.run_version + 1)
    elif field == "result":
        key = replace(key, result_version=key.result_version + 1)
    elif field == "limit":
        limit = 1
    else:
        secret = uuid4().hex
    assert_error("PAGE_CURSOR_INVALID", 422, lambda: page_evidence(body, scope, key, secret, limit, token))


@pytest.mark.parametrize("change", ["order", "content", "removed", "added"])
def test_authenticated_same_key_changed_projection_is_stale(paging, change):
    token = page(paging, limit=2)["next_cursor"]
    body = paging[0]
    if change == "order":
        body["items"].reverse()
    elif change == "content":
        body["items"][4]["mapping_version"] = "changed-synthetic-version"
    elif change == "removed":
        body["items"].pop()
    else:
        item = copy.deepcopy(body["items"][0])
        item["evidence_id"] = str(uuid4())
        body["items"].append(item)
    assert_error("PAGE_CURSOR_STALE", 409, lambda: page(paging, limit=2, cursor=token))


def signed_offset(paging, offset):
    _, scope, key, secret = paging
    token = page(paging, limit=2)["next_cursor"]
    raw = offset.to_bytes(8, "big") + base64.urlsafe_b64decode(token)[8:40]
    binding = json.dumps(
        [
            "evidence-snapshot-page/1",
            str(scope.actor.user_id),
            str(scope.actor.org_id),
            str(scope.case_id),
            str(key.task_id),
            key.run_version,
            key.result_version,
            2,
        ],
        separators=(",", ":"),
    ).encode()
    tag = hmac.new(secret.encode(), binding + raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + tag).decode().rstrip("=")


@pytest.mark.parametrize("offset", [0, 1, 3, 5, 6, (1 << 64) - 1])
def test_authenticated_invalid_offset_or_nonissuer_boundary_is_rejected(paging, offset):
    assert_error("PAGE_CURSOR_INVALID", 422, lambda: page(paging, limit=2, cursor=signed_offset(paging, offset)))


@pytest.mark.parametrize(
    "alter",
    [
        lambda s: s + "=",
        lambda s: s + "\n",
        lambda s: " " + s,
        lambda s: s[:-1],
        lambda s: s + "A",
        lambda s: s[:12] + "+" + s[13:],
        lambda s: s[:12] + "/" + s[13:],
        lambda s: s[:12] + "中" + s[13:],
    ],
)
def test_noncanonical_base64_encodings_are_rejected(paging, alter):
    token = alter(page(paging, limit=2)["next_cursor"])
    assert_error("PAGE_CURSOR_INVALID", 422, lambda: page(paging, limit=2, cursor=token))


@pytest.mark.parametrize("raw", [b"\xff" * 71, b"\xff" * 73])
def test_unused_bit_variants_never_become_a_valid_token(paging, raw):
    # Valid 72-byte tokens have no unused bits. Alternate short encodings do;
    # change those bits as a D02 canonical-text regression as well as size check.
    encoded = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    last = alphabet.index(encoded[-1])
    altered = encoded[:-1] + alphabet[last ^ 1]
    assert_error("PAGE_CURSOR_INVALID", 422, lambda: page(paging, limit=2, cursor=altered))


def test_duplicate_evidence_identity_never_gets_an_ambiguous_page(paging):
    paging[0]["items"][1]["evidence_id"] = paging[0]["items"][0]["evidence_id"].upper()
    assert_error("RESPONSE_CONTRACT_UNAVAILABLE", 503, lambda: page(paging, limit=2))


@pytest.mark.parametrize("cursor", [None, "untrusted-token"])
def test_partial_producer_projection_is_not_replaced_by_local_success(paging, cursor):
    paging[0]["next_cursor"] = "producer-continuation-not-an-entire-snapshot"
    assert_error("EVIDENCE_PAGING_SOURCE_INCOMPLETE", 503, lambda: page(paging, limit=2, cursor=cursor))


@pytest.mark.parametrize("missing", ["items", "next_cursor", "evidence_id", "run_version"])
def test_invalid_complete_projection_fails_closed(paging, missing):
    body = paging[0]
    if missing in body:
        del body[missing]
    else:
        del body["items"][-1][missing]
    assert_error("RESPONSE_CONTRACT_UNAVAILABLE", 503, lambda: page(paging, limit=2))
