"""Serve an existing frontend build and fixed loopback APIs for a Linux demo.

Factory: create_app(dist, poc_port=14200, business_port=14212,
                    max_body_bytes=2097152, transport=None).
The optional httpx async transport is for isolated tests. No identities or
policies are created. Only GET/POST/PUT reach upstreams; static files use GET.
Run with the existing backend environment and --dist /absolute/build/path.
"""

import argparse
import logging
import mimetypes
import os
import re
import stat
from pathlib import Path
from urllib.parse import unquote

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.requests import ClientDisconnect

DEFAULT_MAX_BODY_BYTES = 2 * 1024 * 1024
REQUEST_HEADERS = {
    "content-type",
    "accept",
    "idempotency-key",
    "if-match",
    "x-request-id",
    "x-part-sha256",
    "range",
    "if-range",
}
RESPONSE_HEADERS = {
    "content-type",
    "content-disposition",
    "etag",
    "x-task-id",
    "x-run-version",
    "x-result-version",
    "x-request-id",
    "x-trace-id",
    "www-authenticate",
    "content-range",
    "accept-ranges",
}
ASSET_SUFFIXES = {
    ".js",
    ".css",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".avif",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
}
METHODS = ("GET", "POST", "PUT", "HEAD", "DELETE", "PATCH", "OPTIONS", "TRACE", "CONNECT")


def _quiet_network_logs() -> None:
    # httpx INFO and httpcore DEBUG include URLs; access logs include query strings.
    for name in (
        "uvicorn.access",
        "httpx",
        "httpcore",
        "httpcore.connection",
        "httpcore.http11",
        "httpcore.http2",
        "httpcore.proxy",
        "httpcore.socks",
    ):
        logging.getLogger(name).disabled = True


class _PrivateResponses:
    """Apply the response policy even to framework-generated 404/405 errors."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def private_send(message):
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message["headers"]
                    if name.lower() not in {b"cache-control", b"x-content-type-options"}
                ]
                message = {
                    **message,
                    "headers": headers + [(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")],
                }
            await send(message)

        await self.app(scope, receive, private_send)


def _directory_fd(path: Path) -> int:
    """Walk every directory with no-follow dirfds, including build ancestors."""
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _read_build_file(root: Path, relative: Path) -> bytes:
    descriptor = _directory_fd(root)
    try:
        for part in relative.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        with os.fdopen(file_descriptor, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise OSError("BUILD_REGULAR_FILE_REQUIRED")
            return source.read()
    finally:
        os.close(descriptor)


def _build_root(dist: Path) -> Path:
    root = Path(os.path.abspath(dist))
    try:
        if os.name != "posix" or root == Path(root.anchor):
            raise ValueError("REAL_FRONTEND_BUILD_REQUIRED")
        _read_build_file(root, Path("index.html"))
        descriptor = _directory_fd(root / "assets")
        os.close(descriptor)
    except (OSError, ValueError) as from_error:
        raise ValueError("REAL_FRONTEND_BUILD_REQUIRED") from from_error
    return root


def _safe_path(raw: bytes) -> str | None:
    try:
        path = raw.decode("ascii")
        current = path
        for _ in range(8):
            if (
                not current.startswith("/")
                or "//" in current
                or "\\" in current
                or "?" in current
                or "#" in current
                or any(ord(char) < 32 or ord(char) == 127 for char in current)
                or any(part in {".", ".."} for part in current.split("/"))
                or re.search(r"%(?![0-9a-fA-F]{2})", current)
            ):
                return None
            decoded = unquote(current, errors="strict")
            if decoded == current:
                return path
            current = decoded
    except (UnicodeError, ValueError):
        pass
    return None


def _public_file(path: str) -> Path | None:
    if path in {"/", "/index.html"}:
        return Path("index.html")
    if path == "/favicon.ico":
        return Path("favicon.ico")
    if not path.startswith("/assets/"):
        return None
    relative = Path(path[1:])
    if relative.suffix.lower() not in ASSET_SUFFIXES:
        return None
    for part in relative.parts:
        lowered = part.lower()
        if (
            part.startswith(".")
            or lowered in {"private", "secrets", "node_modules", "__pycache__"}
            or ".private" in lowered
            or ".secret" in lowered
        ):
            return None
    return relative


def _error(status: int, code: str) -> JSONResponse:
    return JSONResponse({"error": code}, status_code=status)


async def _body(request: Request, limit: int) -> bytes | Response:
    lengths = request.headers.getlist("content-length")
    if lengths:
        if len(lengths) != 1 or not re.fullmatch(r"[0-9]+", lengths[0]):
            return _error(400, "INVALID_REQUEST_LENGTH")
        if len(lengths[0]) > 20 or int(lengths[0]) > limit:
            return _error(413, "REQUEST_BODY_TOO_LARGE")
    content = bytearray()
    try:
        async for chunk in request.stream():
            if len(content) + len(chunk) > limit:
                return _error(413, "REQUEST_BODY_TOO_LARGE")
            content.extend(chunk)
    except ClientDisconnect:
        return _error(400, "REQUEST_INCOMPLETE")
    return bytes(content)


def create_app(
    dist: Path,
    poc_port: int = 14200,
    business_port: int = 14212,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Create a POSIX build-only gateway; transport injection never changes origins."""
    for port in (poc_port, business_port):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("LOOPBACK_PORT_REQUIRED")
    if type(max_body_bytes) is not int or max_body_bytes < 1:
        raise ValueError("POSITIVE_BODY_LIMIT_REQUIRED")
    root = _build_root(dist)
    _quiet_network_logs()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
    app.add_middleware(_PrivateResponses)

    @app.api_route("/{path:path}", methods=list(METHODS))
    async def dispatch(request: Request):
        path = _safe_path(request.scope.get("raw_path", b""))
        if path is None:
            return _error(400, "INVALID_REQUEST_PATH")
        if path == "/_demo/health" and request.method == "GET":
            return JSONResponse({"status": "ok", "mode": "loopback-development"})
        upstream_path = path
        port = None
        if path in {"/api", "/poc"} or path.startswith(("/api/", "/poc/")):
            port = poc_port
        elif path == "/business/api/v1" or path.startswith("/business/api/v1/"):
            port = business_port
            upstream_path = path[len("/business") :]
        if port is None:
            relative = _public_file(path)
            if relative is None:
                return _error(404, "NOT_FOUND")
            if request.method != "GET":
                return _error(405, "METHOD_NOT_ALLOWED")
            try:
                content = _read_build_file(root, relative)
            except OSError:
                return _error(404, "NOT_FOUND")
            media_type = mimetypes.guess_type(relative.name)[0] or "application/octet-stream"
            return Response(content, media_type=media_type)
        if request.method not in {"GET", "POST", "PUT"}:
            return _error(405, "METHOD_NOT_ALLOWED")
        content = await _body(request, max_body_bytes)
        if isinstance(content, Response):
            return content
        connection_headers = {value.strip().lower() for value in request.headers.get("connection", "").split(",")}
        headers = {
            name: value
            for name, value in request.headers.items()
            if name in REQUEST_HEADERS and name not in connection_headers
        }
        authorization = request.headers.get("authorization", "")
        if (
            authorization.lower().startswith("bearer ")
            and authorization[7:].strip()
            and "authorization" not in connection_headers
        ):
            headers["authorization"] = authorization
        query = request.scope.get("query_string", b"")
        raw_target = upstream_path.encode("ascii") + (b"?" + query if query else b"")
        try:
            url = httpx.URL(scheme="http", host="127.0.0.1", port=port, raw_path=raw_target)
            async with httpx.AsyncClient(
                transport=transport, trust_env=False, follow_redirects=False, timeout=httpx.Timeout(30, connect=5)
            ) as client:
                upstream = await client.request(request.method, url, headers=headers, content=content)
        except httpx.ConnectError:
            return _error(503, "UPSTREAM_UNAVAILABLE")
        except (httpx.HTTPError, ValueError):
            return _error(502, "UPSTREAM_REQUEST_FAILED")
        if 300 <= upstream.status_code < 400:
            return _error(502, "UPSTREAM_REDIRECT_REFUSED")
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name in RESPONSE_HEADERS and not any(ord(char) < 32 or ord(char) == 127 for char in value)
        }
        return Response(upstream.content, status_code=upstream.status_code, headers=response_headers)

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist", type=Path, required=True, help="Existing build with index.html and a real assets directory"
    )
    parser.add_argument("--port", type=int, default=14213)
    parser.add_argument("--poc-port", type=int, default=14200)
    parser.add_argument("--business-port", type=int, default=14212)
    parser.add_argument("--max-body-bytes", type=int, default=DEFAULT_MAX_BODY_BYTES)
    args = parser.parse_args(argv)
    try:
        if not 1024 <= args.port <= 65535:
            raise ValueError("DEVELOPMENT_PORT_REQUIRED")
        app = create_app(args.dist, args.poc_port, args.business_port, args.max_body_bytes)
        import uvicorn

        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False, proxy_headers=False, server_header=False)
        return 0
    except Exception:
        print('{"status":"DEMO_GATEWAY_STARTUP_FAILED","raw_details_withheld":true}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
