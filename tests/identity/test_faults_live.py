"""Real sockets/TLS and PostgreSQL faults; no fake successful identity provider."""

import socket
import ssl
import threading
import time
from contextlib import contextmanager
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psycopg
import pytest
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.identity.tokens import IntrospectionVerifier, MappedTokenAuthority
from psycopg.conninfo import make_conninfo

from tests.identity.test_oidc_live import verifier
from tools.identity_oidc_probe import PrivateValue, authorization_code_login


@contextmanager
def fault_endpoint(config, mode):
    stopping = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Authorization headers and request bodies stay private.

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if mode == "disconnect":
                self.connection.shutdown(socket.SHUT_RDWR)
                return
            if mode == "timeout":
                stopping.wait(1)
            statuses = {"upstream_auth": 401, "server": 500, "redirect": 307}
            payloads = {
                "slow_body": b'{"active":false}',
                "invalid_json": b"{broken",
                "duplicate": b'{"active":true,"active":false}',
                "oversize": b" " * 70000,
            }
            body = payloads.get(mode, b'{"active":false}')
            try:
                self.send_response(statuses.get(mode, 200))
                self.send_header("Content-Type", "text/html" if mode == "wrong_type" else "application/json")
                self.send_header("Content-Length", str(len(body)))
                if mode == "redirect":
                    self.send_header("Location", config["issuer"] + "/protocol/openid-connect/token/introspect")
                self.end_headers()
                for offset in range(0, len(body), 1 if mode == "slow_body" else len(body)):
                    if stopping.is_set():
                        break
                    self.wfile.write(body[offset : offset + (1 if mode == "slow_body" else len(body))])
                    self.wfile.flush()
                    if mode == "slow_body":
                        stopping.wait(0.04)
            except (OSError, ssl.SSLError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    pki = Path(config["ca_file"]).parent
    context.load_cert_chain(pki / "gateway.crt", pki / "gateway.key")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    try:
        yield "https://localhost:" + str(server.server_port) + "/introspect"
    finally:
        stopping.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


@pytest.mark.parametrize(
    "mode",
    [
        "disconnect",
        "timeout",
        "slow_body",
        "upstream_auth",
        "server",
        "redirect",
        "invalid_json",
        "duplicate",
        "oversize",
        "wrong_type",
    ],
)
def test_real_tls_protocol_faults_deny_without_fallback(identity_realm, mode):
    config = identity_realm
    token = authorization_code_login(config)
    control = verifier(config)
    try:
        assert control.verify(token.access_token).subject == config["user_id"]
        with fault_endpoint(config, mode) as endpoint:
            checker = IntrospectionVerifier(
                replace(control.settings, endpoint=endpoint, timeout_seconds=0.15),
                ssl_context=ssl.create_default_context(cafile=config["ca_file"]),
            )
            try:
                start = time.monotonic()
                with pytest.raises(BusinessError) as failure:
                    checker.verify(token.access_token)
                assert time.monotonic() - start < 3
                assert failure.value.http_status == 503
                assert str(failure.value) == "IDENTITY_AUTHORITY_UNAVAILABLE"
                assert token.access_token not in str(failure.value)
                assert config["api_secret"] not in str(failure.value)
            finally:
                checker.close()
    finally:
        control.close()


def test_real_tls_unknown_ca_denies_a_previously_valid_token(identity_realm):
    config = identity_realm
    token = authorization_code_login(config)
    control = verifier(config)
    wrong = IntrospectionVerifier(control.settings)  # No project CA in the default trust store.
    try:
        assert control.verify(token.access_token).subject == config["user_id"]
        with pytest.raises(BusinessError) as failure:
            wrong.verify(token.access_token)
        assert failure.value.http_status == 503
        assert str(failure.value) == "IDENTITY_AUTHORITY_UNAVAILABLE"
    finally:
        control.close()
        wrong.close()


@pytest.mark.parametrize(
    "token", ["not.a.jwt", "bad token", "x" * 16385, ""], ids=["malformed", "whitespace", "oversize", "empty"]
)
def test_real_issuer_rejects_malformed_or_oversized_bearer(identity_realm, token):
    checker = verifier(identity_realm)
    try:
        with pytest.raises(BusinessError) as failure:
            checker.verify(token)
        assert failure.value.http_status == 401
        assert str(failure.value) == "AUTHENTICATION_REQUIRED"
    finally:
        checker.close()


@pytest.mark.parametrize("mode", ["bad_password", "connection_refused", "statement_timeout", "pool_timeout"])
def test_real_database_faults_never_return_an_actor(live_mapping, mode):
    _, ctx, bundle, resources, _, runtime = live_mapping
    assert resources.authority.authenticate(bundle.access_token) == ctx["actor"]
    values = {}
    reservation = socket.socket()
    reservation.bind(("127.0.0.1", 0))
    if mode == "connection_refused":
        values["port"] = reservation.getsockname()[1]
    if mode == "bad_password":
        values["password"] = PrivateValue("self-owned-deliberately-wrong-password")
    lookup = Database(make_conninfo(runtime.lookup_dsn, **values), statement_timeout_ms=100, pool_timeout_seconds=0.15)
    lock = psycopg.connect(ctx["admin_dsn"]) if mode == "statement_timeout" else None
    occupied = lookup.engine.connect() if mode == "pool_timeout" else None
    try:
        if lock is not None:
            lock.execute("LOCK TABLE mt.users IN ACCESS EXCLUSIVE MODE")
        authority = MappedTokenAuthority(resources.verifier, lookup)
        start = time.monotonic()
        with pytest.raises(BusinessError) as failure:
            authority.authenticate(bundle.access_token)
        assert time.monotonic() - start < 4
        assert failure.value.http_status == 503
        assert str(failure.value) == "IDENTITY_AUTHORITY_UNAVAILABLE"
    finally:
        if occupied is not None:
            occupied.close()
        if lock is not None:
            lock.rollback()
            lock.close()
        lookup.close()
        reservation.close()
