"""Loopback demo gateway contracts, using only synthetic files and HTTP fixtures."""

import asyncio
import importlib
import importlib.util
import logging
from types import SimpleNamespace

import httpx
import pytest


@pytest.fixture
def dist(tmp_path):
    build = tmp_path / "dist"
    (build / "assets").mkdir(parents=True)
    (build / "index.html").write_text('<html><script src="/assets/index-a123.js"></script></html>', encoding="utf8")
    (build / "assets/index-a123.js").write_text('document.title = "synthetic demo";', encoding="utf8")
    (build / "assets/index-a123.css").write_text("body { color: black; }", encoding="utf8")
    (build / "favicon.ico").write_bytes(b"synthetic icon")
    return build


def gateway(dist, handler=None, **kwargs):
    assert importlib.util.find_spec("scripts.business_demo_gateway") is not None, "D03 gateway is not implemented"
    module = importlib.import_module("scripts.business_demo_gateway")
    if handler is None:
        handler = lambda request: httpx.Response(200, json={"upstream": "synthetic"})
    return module.create_app(dist, 14200, 14212, transport=httpx.MockTransport(handler), **kwargs)


def send(app, method, path, **kwargs):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://demo.test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


def raw_send(app, raw_path, *, method="GET", headers=(), chunks=(b"",)):
    """Keep malicious raw paths and independently supplied length/chunk fixtures intact."""

    async def run():
        events = []
        incoming = iter(chunks)
        remaining = len(chunks)

        async def receive():
            nonlocal remaining
            if remaining:
                remaining -= 1
                return {"type": "http.request", "body": next(incoming), "more_body": bool(remaining)}
            return {"type": "http.disconnect"}

        async def collect(message):
            events.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": raw_path.decode("ascii"),
            "raw_path": raw_path,
            "query_string": b"",
            "root_path": "",
            "headers": list(headers),
            "server": ("127.0.0.1", 14213),
            "client": ("127.0.0.1", 10000),
        }
        await app(scope, receive, collect)
        start = next(event for event in events if event["type"] == "http.response.start")
        body = b"".join(event.get("body", b"") for event in events if event["type"] == "http.response.body")
        return httpx.Response(start["status"], headers=start["headers"], content=body)

    return asyncio.run(run())


@pytest.mark.parametrize(
    "path,body,media_type",
    [
        ("/", b"<html>", "text/html"),
        ("/index.html", b"<html>", "text/html"),
        ("/assets/index-a123.js", b"synthetic demo", "javascript"),
        ("/assets/index-a123.css", b"color: black", "text/css"),
        ("/favicon.ico", b"synthetic icon", "image/"),
    ],
)
def test_serves_real_build_files_with_private_response_policy(dist, path, body, media_type):
    response = send(gateway(dist), "GET", path)
    assert response.status_code == 200
    assert body in response.content
    assert media_type in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_health_is_benign_and_does_not_probe_upstreams(dist):
    def unexpected(request):
        pytest.fail("health must not contact an upstream")

    response = send(gateway(dist, unexpected), "GET", "/_demo/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "loopback-development"}
    assert str(dist) not in response.text


@pytest.mark.parametrize(
    "path,want",
    [
        ("/api", "http://127.0.0.1:14200/api"),
        ("/api/v1/health", "http://127.0.0.1:14200/api/v1/health"),
        ("/poc", "http://127.0.0.1:14200/poc"),
        ("/poc/jobs/fixture", "http://127.0.0.1:14200/poc/jobs/fixture"),
        ("/business/api/v1", "http://127.0.0.1:14212/api/v1"),
        (
            "/business/api/v1/reviews?cursor=a%2Fb%2B%3D&term=a+b&term=%25&empty=",
            "http://127.0.0.1:14212/api/v1/reviews?cursor=a%2Fb%2B%3D&term=a+b&term=%25&empty=",
        ),
    ],
)
def test_only_exact_prefixes_use_fixed_loopback_origins_and_preserve_query(dist, path, want):
    seen = []

    def upstream(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"synthetic": True})

    response = send(gateway(dist, upstream), "GET", path)
    assert response.status_code == 200
    assert seen == [want]


@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
def test_allowed_methods_keep_payload_and_only_forward_authorized_headers(dist, method):
    seen = []

    def upstream(request):
        seen.append(request)
        return httpx.Response(201, content=b"synthetic accepted")

    response = send(
        gateway(dist, upstream),
        method,
        "/business/api/v1/uploads/fixture/parts/1",
        content=b"synthetic payload",
        headers={
            "Host": "attacker.invalid",
            "Authorization": "Bearer synthetic-fixture",
            "Content-Type": "application/octet-stream",
            "Accept": "application/json",
            "Idempotency-Key": "synthetic-idempotency",
            "If-Match": '"v3"',
            "X-Request-Id": "synthetic-request",
            "Cookie": "synthetic=forbidden",
            "Proxy-Authorization": "Basic synthetic",
            "Forwarded": "host=attacker.invalid",
            "X-Forwarded-Host": "attacker.invalid",
            "X-Untrusted": "forbidden",
        },
    )
    assert response.status_code == 201
    assert len(seen) == 1
    request = seen[0]
    assert request.method == method
    assert request.content == b"synthetic payload"
    assert request.headers["host"] == "127.0.0.1:14212"
    for name, value in {
        "authorization": "Bearer synthetic-fixture",
        "content-type": "application/octet-stream",
        "accept": "application/json",
        "idempotency-key": "synthetic-idempotency",
        "if-match": '"v3"',
        "x-request-id": "synthetic-request",
    }.items():
        assert request.headers[name] == value
    for name in ("cookie", "proxy-authorization", "forwarded", "x-forwarded-host", "x-untrusted"):
        assert name not in request.headers


def test_mounted_upload_part_receives_its_required_sha256_header(dist):
    from business_app.uploads.router import router
    from fastapi import FastAPI

    from scripts.business_demo_gateway import create_app

    # Exercise the mounted route's real required-header, size and digest checks;
    # only the database-backed scope/persistence boundary uses a synthetic fixture.
    upstream = FastAPI()
    upstream.include_router(router)
    upstream.state.upload_service = SimpleNamespace(
        repository=SimpleNamespace(settings=SimpleNamespace(part_size_bytes=256000)),
        scope=lambda request, action, **kwargs: object(),
        put_part=lambda scope, identifier, number, data, digest, key: {
            "part_no": number,
            "sha256": digest,
            "size_bytes": len(data),
            "idempotency_key": key,
        },
    )
    app = create_app(dist, transport=httpx.ASGITransport(app=upstream))
    response = send(
        app,
        "PUT",
        "/business/api/v1/uploads/10000000-0000-4000-8000-000000000001/parts/1",
        content=b"test",
        headers={
            "Content-Type": "application/octet-stream",
            "Idempotency-Key": "synthetic-part-key",
            "X-Part-Sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "part_no": 1,
        "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        "size_bytes": 4,
        "idempotency_key": "synthetic-part-key",
    }


@pytest.mark.parametrize(
    "range_value,if_range,status,body,range_headers",
    [
        ("bytes=0-9", '"v7"', 206, b'{"syntheti', {"Content-Range": "bytes 0-9/18", "Accept-Ranges": "bytes"}),
        ("bytes=1-2,4-5", '"v7"', 416, b'{"error":"RANGE_INVALID"}', {}),
        ("bytes=0-9", '"old"', 200, b'{"synthetic":true}', {"Accept-Ranges": "bytes"}),
    ],
)
def test_audit_export_range_contract_reaches_upstream_and_preserves_response(
    dist,
    range_value,
    if_range,
    status,
    body,
    range_headers,
):
    def upstream(request):
        assert request.url.path == "/api/v1/audit/exports/10000000-0000-4000-8000-000000000001/content"
        if request.headers.get("range") != range_value or request.headers.get("if-range") != if_range:
            return httpx.Response(422, json={"error": "SYNTHETIC_MISSING_RANGE_HEADERS"})
        return httpx.Response(
            status,
            content=body,
            headers={
                **range_headers,
                "ETag": '"v7"',
                "Content-Type": "application/json",
                "Content-Disposition": 'attachment; filename="synthetic-export.json"',
                "Set-Cookie": "synthetic=forbidden",
            },
        )

    response = send(
        gateway(dist, upstream),
        "GET",
        "/business/api/v1/audit/exports/10000000-0000-4000-8000-000000000001/content",
        headers={"Range": range_value, "If-Range": if_range},
    )
    assert response.status_code == status
    assert response.content == body
    for name, value in range_headers.items():
        assert response.headers[name] == value
    if status != 206:
        assert "content-range" not in response.headers
    assert response.headers["etag"] == '"v7"'
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize(
    "name,value", [("X-Part-Sha256", "synthetic-digest"), ("Range", "bytes=0-9"), ("If-Range", '"v7"')]
)
def test_added_contract_headers_remain_subject_to_connection_filtering(dist, name, value):
    seen = []

    def upstream(request):
        seen.append(request)
        return httpx.Response(200)

    response = send(
        gateway(dist, upstream), "GET", "/business/api/v1/auth/me", headers={name: value, "Connection": name}
    )
    assert response.status_code == 200
    assert name not in seen[0].headers


def test_basic_credentials_and_connection_nominated_headers_are_not_forwarded(dist):
    seen = []

    def upstream(request):
        seen.append(request)
        return httpx.Response(200)

    app = gateway(dist, upstream)
    send(
        app,
        "GET",
        "/api",
        headers={"Authorization": "Basic synthetic", "Connection": "X-Request-Id", "X-Request-Id": "synthetic-request"},
    )
    assert "authorization" not in seen[0].headers
    assert "x-request-id" not in seen[0].headers


def test_response_preserves_versions_and_safe_headers_without_cookies_or_redirect_headers(dist):
    safe = {
        "Content-Type": "application/json",
        "Content-Disposition": 'attachment; filename="fixture.json"',
        "ETag": '"v7"',
        "X-Task-Id": "synthetic-task",
        "X-Run-Version": "2",
        "X-Result-Version": "7",
        "X-Request-Id": "synthetic-request",
        "X-Trace-Id": "synthetic-trace",
        "WWW-Authenticate": "Bearer",
    }

    def upstream(request):
        return httpx.Response(
            401,
            headers={
                **safe,
                "Set-Cookie": "synthetic=forbidden",
                "Location": "https://invalid",
                "Server": "private-server",
                "Cache-Control": "public, max-age=999",
            },
            json={"error": "synthetic denial"},
        )

    response = send(gateway(dist, upstream), "GET", "/business/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json() == {"error": "synthetic denial"}
    for name, value in safe.items():
        assert response.headers[name] == value
    for name in ("set-cookie", "location", "server"):
        assert name not in response.headers
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("status", [300, 301, 302, 303, 304, 307, 308, 399])
def test_upstream_redirect_is_a_generic_failure_and_never_followed(dist, status):
    seen = []

    def upstream(request):
        seen.append(request)
        return httpx.Response(status, headers={"Location": "http://attacker.invalid/private?synthetic=secret"})

    response = send(gateway(dist, upstream), "GET", "/api")
    assert response.status_code == 502
    assert len(seen) == 1
    assert "location" not in response.headers
    assert "attacker" not in response.text


@pytest.mark.parametrize(
    "failure,status", [(httpx.ConnectError, 503), (httpx.ReadTimeout, 502), (httpx.RemoteProtocolError, 502)]
)
def test_transport_failure_has_safe_body_and_no_sensitive_log(dist, caplog, failure, status):
    def upstream(request):
        raise failure("synthetic-private-upstream-details", request=request)

    with caplog.at_level(logging.DEBUG):
        response = send(gateway(dist, upstream), "GET", "/api?synthetic-private-query=1")
    assert response.status_code == status
    assert "synthetic-private" not in response.text
    assert "synthetic-private" not in caplog.text
    assert response.headers["cache-control"] == "no-store"


def test_oversized_declared_body_is_refused_before_read_or_upstream(dist):
    def unexpected(request):
        pytest.fail("oversized body reached upstream")

    response = raw_send(
        gateway(dist, unexpected, max_body_bytes=8),
        b"/poc/assets",
        method="POST",
        headers=((b"content-length", b"9"),),
        chunks=(b"",),
    )
    assert response.status_code == 413


@pytest.mark.parametrize("headers", [(), ((b"content-length", b"1"),)])
def test_chunked_or_lying_length_body_cannot_exceed_limit(dist, headers):
    def unexpected(request):
        pytest.fail("oversized streamed body reached upstream")

    response = raw_send(
        gateway(dist, unexpected, max_body_bytes=8),
        b"/poc/assets",
        method="POST",
        headers=headers,
        chunks=(b"1234", b"5678", b"9"),
    )
    assert response.status_code == 413


def test_body_exactly_at_limit_is_forwarded(dist):
    seen = []

    def upstream(request):
        seen.append(request.content)
        return httpx.Response(202)

    response = raw_send(
        gateway(dist, upstream, max_body_bytes=8), b"/poc/assets", method="POST", chunks=(b"1234", b"5678")
    )
    assert response.status_code == 202
    assert seen == [b"12345678"]


@pytest.mark.parametrize("lengths", [(b"-1",), (b"invalid",), (b"4", b"4"), (b"4,4",)])
def test_ambiguous_or_invalid_content_length_is_refused(dist, lengths):
    response = raw_send(
        gateway(dist),
        b"/api",
        method="POST",
        headers=tuple((b"content-length", value) for value in lengths),
        chunks=(b"1234",),
    )
    assert response.status_code == 400


@pytest.mark.parametrize("method", ["DELETE", "PATCH", "OPTIONS", "TRACE", "HEAD"])
def test_proxy_rejects_methods_outside_existing_get_post_put_contract(dist, method):
    def unexpected(request):
        pytest.fail("unsupported method reached upstream")

    response = send(gateway(dist, unexpected), method, "/business/api/v1/auth/me")
    assert response.status_code == 405
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "path",
    [
        "/apis",
        "/api-other",
        "/poc-other",
        "/business",
        "/business/api/v10",
        "/business/api",
        "/business/api/v1other",
        "/docs",
        "/openapi.json",
        "/unknown",
    ],
)
def test_unknown_paths_and_prefix_lookalikes_are_not_upstream_or_spa_fallbacks(dist, path):
    def unexpected(request):
        pytest.fail("unknown path reached upstream")

    response = send(gateway(dist, unexpected), "GET", path)
    assert response.status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        b"/assets/../index.html",
        b"/assets/%2e%2e/index.html",
        b"/assets/%252e%252e/index.html",
        b"/api/./v1",
        b"/api//v1",
        b"//api/v1",
        b"/api\\v1",
        b"/api/%5cv1",
        b"/api/%255cv1",
        b"/api/%2f%2fattacker.invalid",
        b"/api/%00",
        b"/api/%ZZ",
        b"/api/%25252e%25252e/private",
    ],
)
def test_raw_traversal_backslash_and_ambiguous_paths_are_refused(dist, path):
    def unexpected(request):
        pytest.fail("unsafe path reached upstream")

    response = raw_send(gateway(dist, unexpected), path)
    assert response.status_code in {400, 404}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "path",
    [
        "/.env",
        "/config.private.json",
        "/public.txt",
        "/assets/.hidden.js",
        "/assets/config.private.js",
        "/assets/index-a123.js.map",
        "/assets/source.ts",
        "/assets/private/index.js",
        "/assets/nested/.hidden/index.js",
    ],
)
def test_only_generated_assets_are_public_even_when_other_files_exist(dist, path):
    target = dist / path.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("synthetic-private-file", encoding="utf8")
    response = send(gateway(dist), "GET", path)
    assert response.status_code == 404
    assert "synthetic-private-file" not in response.text


def test_symlink_file_and_directory_cannot_expose_files_outside_dist(dist, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "index.js").write_text("synthetic-private-file", encoding="utf8")
    (dist / "assets/link.js").symlink_to(outside / "index.js")
    (dist / "assets/linked").symlink_to(outside, target_is_directory=True)
    app = gateway(dist)
    for path in ("/assets/link.js", "/assets/linked/index.js"):
        response = send(app, "GET", path)
        assert response.status_code == 404


@pytest.mark.parametrize(
    "defect", ["missing-index", "missing-assets", "symlink-index", "symlink-assets", "symlink-dist"]
)
def test_factory_refuses_any_directory_without_a_real_build_shape(dist, tmp_path, defect):
    if defect == "missing-index":
        (dist / "index.html").unlink()
    elif defect == "missing-assets":
        (dist / "assets/index-a123.js").unlink()
        (dist / "assets/index-a123.css").unlink()
        (dist / "assets").rmdir()
    elif defect == "symlink-index":
        (dist / "index.html").unlink()
        (dist / "index.html").symlink_to(tmp_path / "outside.html")
    elif defect == "symlink-assets":
        alternate = tmp_path / "assets"
        (dist / "assets").rename(alternate)
        (dist / "assets").symlink_to(alternate, target_is_directory=True)
    else:
        alternate = tmp_path / "linked-dist"
        alternate.symlink_to(dist, target_is_directory=True)
        dist = alternate
    with pytest.raises(ValueError, match="BUILD"):
        gateway(dist)


@pytest.mark.parametrize(
    "setting,value",
    [("poc_port", 0), ("business_port", 65536), ("poc_port", True), ("max_body_bytes", 0), ("max_body_bytes", True)],
)
def test_factory_refuses_invalid_ports_and_body_limits(dist, setting, value):
    module = importlib.import_module("scripts.business_demo_gateway")
    values = {"poc_port": 14200, "business_port": 14212, "max_body_bytes": 2 * 1024 * 1024, setting: value}
    with pytest.raises(ValueError):
        module.create_app(dist, **values)
