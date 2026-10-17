"""RFC 7662 wire validation with synthetic transport, not a live identity system."""

import base64
from dataclasses import replace
from urllib.parse import parse_qs

import httpx
import pytest
from business_app.errors import BusinessError
from business_app.identity.tokens import IntrospectionSettings, IntrospectionVerifier


def settings():
    return IntrospectionSettings(
        endpoint="https://identity.example.test/introspect",
        issuer="https://identity.example.test",
        audience="synthetic-business-api",
        client_id="synthetic:client",
        client_secret="synthetic-test-secret",
        timeout_seconds=2,
        max_response_bytes=2048,
        max_token_bytes=128,
    )


def claims(**changes):
    result = dict(
        active=True,
        iss=settings().issuer,
        sub="synthetic-subject",
        aud=settings().audience,
        exp=101,
        nbf=90,
        iat=90,
        token_type="Bearer",
    )
    result.update(changes)
    return result


def verifier(body=None, *, handler=None):
    return IntrospectionVerifier(
        settings(),
        clock=lambda: 100,
        transport=httpx.MockTransport(
            handler or (lambda request: httpx.Response(200, json=claims() if body is None else body))
        ),
    )


def test_valid_token_uses_post_body_authenticated_endpoint_and_exact_identity():
    def handle(request):
        assert request.method == "POST" and request.url == settings().endpoint
        assert request.url.query == b""
        assert parse_qs(request.content.decode()) == {"token": ["synthetic-token"], "token_type_hint": ["access_token"]}
        assert (
            base64.b64decode(request.headers["Authorization"].split()[1]).decode()
            == "synthetic%3Aclient:synthetic-test-secret"
        )
        return httpx.Response(200, json=claims(aud=["another", settings().audience]))

    value = verifier(handler=handle)
    try:
        assert value.verify("synthetic-token").subject == "synthetic-subject"
    finally:
        value.close()


@pytest.mark.parametrize(
    "change",
    [
        dict(active=False),
        dict(iss="https://wrong.example.test"),
        dict(sub=""),
        dict(sub=" leading"),
        dict(aud="wrong"),
        dict(aud=[settings().audience, 1]),
        dict(exp=100),
        dict(exp=True),
        dict(exp=101.0),
        dict(exp=None),
        dict(nbf=101),
        dict(iat=101),
        dict(nbf=False),
        dict(token_type="refresh_token"),
        dict(token_type=1),
    ],
)
def test_invalid_active_claims_rejected(change):
    value = verifier(claims(**change))
    try:
        with pytest.raises(BusinessError, match="AUTHENTICATION_REQUIRED"):
            value.verify("synthetic-token")
    finally:
        value.close()


@pytest.mark.parametrize("body", [[], {}, {"active": 1}, {"active": "true"}])
def test_malformed_response_never_establishes_identity(body):
    value = verifier(body)
    try:
        with pytest.raises(BusinessError, match="IDENTITY_AUTHORITY_UNAVAILABLE"):
            value.verify("synthetic-token")
    finally:
        value.close()


@pytest.mark.parametrize(
    "kind", ["redirect", "upstream_auth", "server", "timeout", "invalid_json", "duplicate", "oversize", "wrong_type"]
)
def test_endpoint_failure_never_falls_back_or_leaks_token(kind):
    calls = []

    def handle(request):
        calls.append(request)
        if kind == "timeout":
            raise httpx.ReadTimeout("synthetic-token synthetic-test-secret", request=request)
        if kind == "redirect":
            return httpx.Response(307, headers={"Location": "https://untrusted.example.test"})
        if kind == "upstream_auth":
            return httpx.Response(401)
        if kind == "server":
            return httpx.Response(500)
        content = {
            "invalid_json": b"not json",
            "duplicate": b'{"active":true,"active":false}',
            "oversize": b" " * 2049,
            "wrong_type": b"{}",
        }[kind]
        return httpx.Response(
            200, content=content, headers={"content-type": "text/html" if kind == "wrong_type" else "application/json"}
        )

    value = verifier(handler=handle)
    try:
        with pytest.raises(BusinessError) as failure:
            value.verify("synthetic-token")
        assert str(failure.value) == "IDENTITY_AUTHORITY_UNAVAILABLE"
        assert failure.value.http_status == 503
        assert len(calls) == 1
    finally:
        value.close()


@pytest.mark.parametrize("token", ["", " token", "token token", "token\n", "token,token", "中", "x" * 129])
def test_bad_bearer_rejected_before_network(token):
    def handle(request):
        pytest.fail("invalid bearer reached authority")

    value = verifier(handler=handle)
    try:
        with pytest.raises(BusinessError, match="AUTHENTICATION_REQUIRED"):
            value.verify(token)
    finally:
        value.close()


def test_revocation_checked_on_every_request_without_positive_cache():
    responses = iter([claims(), {"active": False}])
    value = verifier(handler=lambda request: httpx.Response(200, json=next(responses)))
    try:
        value.verify("synthetic-token")
        with pytest.raises(BusinessError, match="AUTHENTICATION_REQUIRED"):
            value.verify("synthetic-token")
    finally:
        value.close()


@pytest.mark.parametrize(
    "change",
    [
        dict(endpoint="http://identity.example.test"),
        dict(endpoint="https://user:secret@identity.example.test"),
        dict(endpoint="https://identity.example.test?token=secret"),
        dict(endpoint="https://identity.example.test#part"),
        dict(issuer=""),
        dict(client_secret=""),
        dict(timeout_seconds=float("inf")),
        dict(timeout_seconds=True),
        dict(max_response_bytes=0),
        dict(max_token_bytes=True),
    ],
)
def test_unsafe_configuration_rejected(change):
    with pytest.raises(ValueError, match="INTROSPECTION_CONFIGURATION_INVALID"):
        replace(settings(), **change)


def test_settings_repr_hides_client_credentials():
    assert settings().client_secret not in repr(settings())
    assert settings().client_id not in repr(settings())
