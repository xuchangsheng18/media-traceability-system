"""Live TLS/proxy boundaries; all tests require the real three-service target."""

import socket
import ssl

import httpx
import pytest


def test_live_discovery_and_forwarded_headers(identity_config, identity_http):
    issuer = identity_config["public_url"] + "/realms/master"
    response = identity_http.get(
        issuer + "/.well-known/openid-configuration",
        headers={
            "X-Forwarded-Host": "attacker.invalid",
            "X-Forwarded-Proto": "http",
            "Forwarded": "host=attacker.invalid;proto=http",
        },
    )
    assert response.status_code == 200
    assert response.json()["issuer"] == issuer


@pytest.mark.parametrize(
    "path",
    [
        "/admin/realms/master",
        "/%61dmin/realms/master",
        "//admin/realms/master",
        "/admin%2frealms/master",
        "/%2561dmin/realms/master",
        "/Admin/realms/master",
        "/health/ready",
        "/metrics",
    ],
)
def test_public_admin_and_path_bypasses_denied(identity_config, identity_http, path):
    response = identity_http.get(identity_config["public_url"] + path)
    assert response.status_code in {400, 404}


def test_wrong_host_denied(identity_config, identity_http):
    response = identity_http.get(
        identity_config["public_url"] + "/realms/master/.well-known/openid-configuration",
        headers={"Host": "attacker.invalid"},
    )
    assert response.status_code == 400


def test_management_url_uses_private_origin(identity_config, identity_http):
    response = identity_http.get(identity_config["admin_url"] + "/admin/master/console/")
    assert response.status_code in {200, 302, 303}
    if response.is_redirect:
        assert response.headers["location"].startswith(identity_config["public_url"] + "/realms/master/")


def test_unknown_ca_and_wrong_hostname_are_rejected(identity_config):
    with httpx.Client(trust_env=False, timeout=5) as client:
        with pytest.raises(httpx.ConnectError, match="CERTIFICATE_VERIFY_FAILED"):
            client.get(identity_config["public_url"] + "/realms/master/.well-known/openid-configuration")
    context = ssl.create_default_context(cafile=identity_config["ca_file"])
    with socket.create_connection(("172.16.58.179", 18443), timeout=5) as connection:
        with pytest.raises(ssl.SSLCertVerificationError):
            context.wrap_socket(connection, server_hostname="wrong-hostname.invalid")
