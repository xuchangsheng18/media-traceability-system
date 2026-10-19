"""Real HTTP authorization-code/MFA driver for the disposable master realm only."""

import base64
import hashlib
import hmac
import html
import re
import secrets
import struct
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

import httpx

from tools.identity_oidc_probe import PrivateValue


class HumanAdmin:
    def __init__(self, lab, token):
        self.lab, self.token = lab, token

    def request(self, method, path, *, body=None, expected=(200,)):
        with self.lab.http() as http:
            response = http.request(
                method, self.lab.admin_url + path, json=body, headers={"Authorization": "Bearer " + self.token}
            )
        if response.status_code not in expected:
            raise RuntimeError("IDENTITY_HANDOVER_HUMAN_ADMIN_OPERATION_FAILED")
        return response


class HumanLogin:
    def __init__(self, lab, client_id, username, password):
        self.lab, self.client_id, self.username, self.password = lab, client_id, username, password
        self.issuer = lab.public_url + "/realms/master"
        self.verifier = PrivateValue(secrets.token_urlsafe(48))
        self.state = PrivateValue(secrets.token_urlsafe(24))
        self.http = lab.http()
        self._page: httpx.Response | None = None

    @property
    def page(self) -> httpx.Response:
        if self._page is None:
            raise RuntimeError("IDENTITY_HANDOVER_LOGIN_NOT_STARTED")
        return self._page

    def password_step(self, authorization_url=None):
        challenge = base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest()).decode().rstrip("=")
        self._page = self.http.get(
            authorization_url
            or (
                self.issuer
                + "/protocol/openid-connect/auth?"
                + urlencode(
                    dict(
                        client_id=self.client_id,
                        redirect_uri=self.lab.redirect,
                        response_type="code",
                        scope="openid",
                        state=self.state,
                        code_challenge=challenge,
                        code_challenge_method="S256",
                    )
                )
            )
        )
        self.post_form({"username": self.username, "password": self.password})
        return self

    def form(self):
        if self.page.status_code != 200:
            raise RuntimeError("IDENTITY_HANDOVER_FORM_MISSING")
        match = re.search(r'<form[^>]*\baction="([^"]+)"', self.page.text)
        if match is None:
            raise RuntimeError("IDENTITY_HANDOVER_FORM_MISSING")
        action = html.unescape(match.group(1))
        parsed = urlsplit(action)
        if parsed._replace(path="", query="", fragment="").geturl() not in {self.lab.public_url, self.lab.admin_url}:
            raise RuntimeError("IDENTITY_HANDOVER_FORM_ORIGIN_MISMATCH")
        if not parsed.path.startswith("/realms/master/login-actions/") or parsed.fragment:
            raise RuntimeError("IDENTITY_HANDOVER_FORM_ORIGIN_MISMATCH")
        return action

    def post_form(self, values):
        self._page = self.http.post(self.form(), data=values)
        for _ in range(8):
            if self.page.status_code != 302:
                break
            target = urljoin(str(self.page.url), self.page.headers.get("location", ""))
            parsed = urlsplit(target)
            if parsed._replace(query="", fragment="").geturl() == self.lab.redirect:
                break
            if not target.startswith(self.issuer + "/login-actions/"):
                raise RuntimeError("IDENTITY_HANDOVER_UNEXPECTED_REDIRECT")
            self._page = self.http.get(target)

    def otp_secret(self):
        match = re.search(r'name="totpSecret"\s+value="([^"]+)"', self.page.text)
        if match is None:
            raise RuntimeError("IDENTITY_HANDOVER_OTP_ENROLMENT_MISSING")
        value = PrivateValue(html.unescape(match.group(1)))
        self.lab.private_values.append(value)
        return value

    def requires_otp(self):
        return (
            self.page.status_code == 200
            and ('name="totp"' in self.page.text or 'name="otp"' in self.page.text)
            and not self.callback_ready()
        )

    def callback_ready(self):
        parsed = urlsplit(self.page.headers.get("location", ""))
        return self.page.status_code == 302 and parsed._replace(query="", fragment="").geturl() == self.lab.redirect

    def exchange(self):
        if not self.callback_ready():
            raise RuntimeError("IDENTITY_HANDOVER_MFA_CALLBACK_MISSING")
        values = parse_qs(urlsplit(self.page.headers["location"]).query)
        if values.get("state") != [self.state] or len(values.get("code", [])) != 1:
            raise RuntimeError("IDENTITY_HANDOVER_CALLBACK_STATE_INVALID")
        code = PrivateValue(values["code"][0])
        self.lab.private_values.append(code)
        response = self.http.post(
            self.issuer + "/protocol/openid-connect/token",
            data=dict(
                grant_type="authorization_code",
                client_id=self.client_id,
                redirect_uri=self.lab.redirect,
                code=code,
                code_verifier=self.verifier,
            ),
        )
        if response.status_code != 200:
            raise RuntimeError("IDENTITY_HANDOVER_CODE_EXCHANGE_FAILED")
        result = response.json()
        self.lab.private_values.extend(PrivateValue(v) for k, v in result.items() if k.endswith("token"))
        return PrivateValue(result["access_token"])

    def close(self):
        self.http.close()


def otp(secret, *, after_counter=None):
    deadline = time.monotonic() + 35
    while after_counter is not None and int(time.time()) // 30 <= after_counter:
        if time.monotonic() > deadline:
            raise RuntimeError("IDENTITY_HANDOVER_FRESH_OTP_TIMEOUT")
        time.sleep(0.25)
    # Keycloak's totpSecret form field is the raw ASCII secret, not its displayed base32 encoding.
    counter = int(time.time()) // 30
    digest = hmac.new(secret.encode(), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return PrivateValue(f"{value:06d}"), counter
