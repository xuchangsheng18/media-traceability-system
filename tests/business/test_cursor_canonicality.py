"""Parser regression fixtures; full database/HTTP coverage remains in the business suite."""

import base64
import hashlib
import hmac
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import pytest
from business_app.controls.common import page
from business_app.errors import BusinessError
from business_app.types import Actor, Scope
from business_app.uploads.repository import UploadRepository

SCOPE = Scope(Actor(UUID(int=11), UUID(int=12)), UUID(int=13))
SECRET = "synthetic-cursor-test-only"
SNAPSHOT = hashlib.sha256(b"synthetic-snapshot").hexdigest()
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def mappings(self):
        return self

    def all(self):
        return self.value


class ControlsConnection:
    signature = SNAPSHOT

    def execute(self, statement, params):
        if "SELECT encode" in str(statement):
            return Result(self.signature)
        rows = [{"object_id": UUID(int=(1 << 128) - i)} for i in (3, 2, 1)]
        return Result(
            [r for r in rows if params["after"] is None or r["object_id"] > params["after"]][: params["limit"]]
        )


def controls(cursor=None, scope=SCOPE, connection=None):
    return page(
        cast(Any, connection or ControlsConnection()), "synthetic_fixture", "object_id", scope, SECRET, cursor, 1
    )


def nonzero_pad_bits(value):
    body = value.rstrip("=")
    assert len(body) % 4 in (2, 3)
    index = ALPHABET.index(body[-1])
    return body[:-1] + ALPHABET[index | 1] + value[len(body) :]


def malformed(value, kind):
    if kind == "alphabet":
        changed = value.translate(str.maketrans("-_", "+/"))
        assert changed != value
        return changed
    if kind == "whitespace":
        return value[:4] + "\n" + value[4:]
    if kind == "extra_padding":
        return value + "="
    if kind == "tail":
        return value + "=Yg=="
    if kind == "pad_bits":
        return nonzero_pad_bits(value)
    if kind == "short":
        return base64.urlsafe_b64encode(b"short").decode()
    raise AssertionError(kind)


@pytest.mark.parametrize("kind", ["alphabet", "whitespace", "extra_padding", "tail", "pad_bits", "short"])
def test_controls_reject_noncanonical_cursor(kind):
    _, cursor = controls()
    candidate = malformed(cursor, kind)
    if kind == "short":
        candidate = candidate.rstrip("=")
    with pytest.raises(BusinessError) as error:
        controls(candidate)
    assert (error.value.code, error.value.http_status) == ("PAGE_CURSOR_INVALID", 422)


def test_controls_issued_cursor_and_snapshot_binding():
    first, cursor = controls()
    second, _ = controls(cursor)
    assert first[0]["object_id"] < second[0]["object_id"]
    assert "=" not in cursor
    connection = ControlsConnection()
    connection.signature = "00" * 32
    with pytest.raises(BusinessError) as error:
        controls(cursor, connection=connection)
    assert error.value.code == "PAGE_CURSOR_STALE"


@pytest.mark.parametrize("field", ["user", "org", "case", "signature"])
def test_controls_retain_hmac_and_scope_binding(field):
    _, cursor = controls()
    scope = SCOPE
    if field == "signature":
        raw = bytearray(base64.urlsafe_b64decode(cursor + "="))
        raw[-1] ^= 1
        cursor = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    elif field == "case":
        scope = replace(SCOPE, case_id=UUID(int=99))
    else:
        scope = replace(SCOPE, actor=replace(SCOPE.actor, **{field + "_id": UUID(int=99)}))
    with pytest.raises(BusinessError) as error:
        controls(cursor, scope)
    assert error.value.code == "PAGE_CURSOR_INVALID"


class PartsConnection:
    def execute(self, statement, params):
        return Result(
            [{"part_no": n, "sha256": "0" * 64, "size_bytes": 1} for n in (1, 2, 3) if n > params["after"]][
                : params["limit"]
            ]
        )


class PartsDatabase:
    @contextmanager
    def transaction(self, scope):
        yield PartsConnection()


@pytest.fixture
def upload_parser():
    # These collaborators deliberately implement only the parser's in-memory SQL surface.
    repository = cast(
        Any, UploadRepository(cast(Any, PartsDatabase()), cast(Any, SimpleNamespace(cursor_secret=SECRET)))
    )
    repository.session = lambda scope, upload, connection: {"row_version": 1}
    upload_id = UUID(int=20)
    issued = repository.parts(SCOPE, upload_id, None, 1)["next_cursor"]
    return repository, upload_id, issued


def signed(value):
    return value + "." + hmac.new(SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


@pytest.mark.parametrize("kind", ["whitespace", "extra_padding", "tail", "pad_bits", "short"])
def test_upload_rejects_even_test_issuer_signed_noncanonical_text(upload_parser, kind):
    repository, upload_id, issued = upload_parser
    value, _ = issued.split(".")
    with pytest.raises(BusinessError) as error:
        repository.parts(SCOPE, upload_id, signed(malformed(value, kind)), 1)
    assert (error.value.code, error.value.http_status) == ("INPUT_INVALID", 422)


def test_upload_issued_cursor_and_session_binding(upload_parser):
    repository, upload_id, issued = upload_parser
    assert repository.parts(SCOPE, upload_id, issued, 1)["items"][0]["part_no"] == 2
    repository.session = lambda scope, upload, connection: {"row_version": 2}
    with pytest.raises(BusinessError) as error:
        repository.parts(SCOPE, upload_id, issued, 1)
    assert error.value.code == "UPLOAD_CURSOR_STALE"


def test_upload_cursor_cannot_select_another_upload(upload_parser):
    repository, _, issued = upload_parser
    with pytest.raises(BusinessError) as error:
        repository.parts(SCOPE, UUID(int=99), issued, 1)
    assert (error.value.code, error.value.http_status) == ("UPLOAD_CURSOR_STALE", 409)


@pytest.mark.parametrize("kind", ["extra_padding", "tail", "signature"])
def test_upload_unsigned_changes_remain_rejected(upload_parser, kind):
    repository, upload_id, issued = upload_parser
    value, signature = issued.split(".")
    changed = value + "." + ("0" * 64) if kind == "signature" else malformed(value, kind) + "." + signature
    with pytest.raises(BusinessError) as error:
        repository.parts(SCOPE, upload_id, changed, 1)
    assert error.value.code == "INPUT_INVALID"
