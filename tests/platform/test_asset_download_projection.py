"""Pure download boundaries; no database, server or authorized media required."""

import hashlib
from uuid import UUID

import pytest
from business_app.errors import BusinessError


def helpers():
    # Keep the first RED as a missing-behavior assertion, rather than collection failure.
    import importlib.util

    assert importlib.util.find_spec("business_app.asset_download") is not None, "asset download helpers missing"
    from business_app import asset_download

    return asset_download


@pytest.mark.parametrize(
    "raw,condition,expected",
    [
        (None, None, (200, 0, 6)),
        ("bytes=1-3", None, (206, 1, 4)),
        ("bytes=3-", None, (206, 3, 6)),
        ("bytes=-2", None, (206, 4, 6)),
        ("bytes=-20", None, (206, 0, 6)),
        ("bytes=0-100", None, (206, 0, 6)),
        ("bytes=1-3", '"old"', (200, 0, 6)),
        ("bytes=1-3", 'W/"tag"', (200, 0, 6)),
        ("bytes=1-3", '"tag"', (206, 1, 4)),
    ],
)
def test_single_range_and_if_range_match(raw, condition, expected):
    assert helpers().select_range(6, raw, condition, '"tag"') == expected


@pytest.mark.parametrize(
    "value",
    [
        "bytes=",
        "bytes=-",
        "bytes=-0",
        "bytes=6-",
        "bytes=4-2",
        "bytes=0-1,3-4",
        "items=0-1",
        "bytes=+1-2",
        "bytes=１-２",
    ],
)
def test_invalid_or_unsatisfiable_range_rejects(value):
    with pytest.raises(BusinessError) as caught:
        helpers().select_range(6, value, None, '"tag"')
    assert (caught.value.code, caught.value.http_status) == ("RANGE_INVALID", 416)


def test_empty_asset_download_without_range_and_empty_range_refusal():
    assert helpers().select_range(0, None, None, '"tag"') == (200, 0, 0)
    with pytest.raises(BusinessError) as caught:
        helpers().select_range(0, "bytes=0-", None, '"tag"')
    assert caught.value.http_status == 416


@pytest.mark.parametrize("raw,condition", [([], []), (["bytes=0-1"], ['"tag"'])])
def test_bounded_single_headers(raw, condition):
    assert helpers().validate_download_request(False, raw, condition) == (
        raw[0] if raw else None,
        condition[0] if condition else None,
    )


@pytest.mark.parametrize(
    "query,raw,condition",
    [
        (True, [], []),
        (False, ["bytes=0-1", "bytes=2-3"], []),
        (False, [], ['"tag"', '"tag"']),
        (False, [""], []),
        (False, ["x" * 129], []),
        (False, [], ["x" * 129]),
        (False, ["bytes=0-1\r\nX-Evil: yes"], []),
    ],
)
def test_query_duplicate_empty_or_oversized_headers_reject(query, raw, condition):
    with pytest.raises(BusinessError) as caught:
        helpers().validate_download_request(query, raw, condition)
    assert caught.value.http_status == 422


def test_integrity_checks_full_content_even_when_caller_only_requests_prefix():
    module = helpers()
    expected = hashlib.sha256(b"ABCDEF").hexdigest()
    assert module.buffer_verified(iter([b"ABC", b"DEF"]), 6, expected, 6) == b"ABCDEF"
    with pytest.raises(BusinessError) as caught:
        module.buffer_verified(iter([b"ABC", b"XYZ"]), 6, expected, 6)
    assert caught.value.code == "ASSET_OBJECT_BINDING_INVALID"


@pytest.mark.parametrize("blocks,size", [([b"ABC"], 6), ([b"ABCDEFx"], 6), (["ABCDEF"], 6)])
def test_truncated_extra_or_nonbyte_storage_output_rejects(blocks, size):
    with pytest.raises(BusinessError) as caught:
        helpers().buffer_verified(iter(blocks), size, hashlib.sha256(b"ABCDEF").hexdigest(), 6)
    assert caught.value.http_status == 503


def test_buffer_always_closes_underlying_reader_on_integrity_failure():
    closed = []

    def reader():
        try:
            yield b"too long"
        finally:
            closed.append(True)

    with pytest.raises(BusinessError):
        helpers().buffer_verified(reader(), 1, hashlib.sha256(b"A").hexdigest(), 10)
    assert closed == [True]


def test_zero_length_integrity_and_controlled_filename():
    module = helpers()
    assert module.buffer_verified(iter([]), 0, hashlib.sha256(b"").hexdigest(), 1) == b""
    identifier = UUID("12345678-1234-4234-8234-123456789abc")
    assert module.download_headers(identifier, '"tag"') == {
        "ETag": '"tag"',
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
        "Content-Disposition": f'attachment; filename="asset-{identifier}.bin"',
        "X-Content-Type-Options": "nosniff",
    }


def test_development_limit_refuses_before_storage_is_consumed():
    consumed = []

    def reader():
        consumed.append(True)
        yield b"ABC"

    with pytest.raises(BusinessError) as caught:
        helpers().buffer_verified(reader(), 3, hashlib.sha256(b"ABC").hexdigest(), 2)
    assert (caught.value.code, caught.value.http_status) == ("ASSET_DOWNLOAD_DEVELOPMENT_LIMIT_EXCEEDED", 503)
    assert consumed == []


@pytest.mark.parametrize("size,digest", [(-1, "0" * 64), (True, "0" * 64), (1, "wrong")])
def test_invalid_registered_integrity_metadata_fails_closed(size, digest):
    with pytest.raises(BusinessError) as caught:
        helpers().buffer_verified(iter([]), size, digest, 6)
    assert caught.value.code == "ASSET_OBJECT_BINDING_INVALID"
