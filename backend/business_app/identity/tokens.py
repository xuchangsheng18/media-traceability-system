"""Optional RFC 7662 adapter; installation and issuer approval are explicit.

Introspection establishes identity only. Case/source permission decisions stay
with the separately supplied authority. No token or identity cache is kept.
"""

import json
import math
import re
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..auth import AuthorityProvider
from ..db import Database
from ..errors import BusinessError
from ..permissions.types import Principal
from ..types import Actor, Scope
from .directory import IdentityDirectory, valid_key


@dataclass(frozen=True)
class IntrospectionSettings:
    endpoint: str
    issuer: str
    audience: str
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    timeout_seconds: float
    max_response_bytes: int
    max_token_bytes: int

    def __post_init__(self) -> None:
        try:
            url = httpx.URL(self.endpoint)
            valid = (
                url.scheme == "https"
                and bool(url.host)
                and not url.userinfo
                and not url.query
                and not url.fragment
                and all(valid_key(value, 2048) for value in (self.endpoint, self.issuer, self.audience, self.client_id))
                and isinstance(self.client_secret, str)
                and bool(self.client_secret)
                and type(self.timeout_seconds) in (int, float)
                and math.isfinite(self.timeout_seconds)
                and self.timeout_seconds > 0
                and all(type(value) is int and value > 0 for value in (self.max_response_bytes, self.max_token_bytes))
            )
        except (TypeError, ValueError, httpx.InvalidURL):
            valid = False
        if not valid:
            raise ValueError("INTROSPECTION_CONFIGURATION_INVALID")


@dataclass(frozen=True)
class VerifiedIdentity:
    issuer: str
    subject: str
    expires_at: int


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_RESPONSE_FIELD")
        result[key] = value
    return result


class IntrospectionVerifier:
    def __init__(
        self,
        settings: IntrospectionSettings,
        *,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], float] = time.time,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        if ssl_context is not None and (
            not isinstance(ssl_context, ssl.SSLContext)
            or ssl_context.verify_mode != ssl.CERT_REQUIRED
            or not ssl_context.check_hostname
        ):
            raise ValueError("IDENTITY_TLS_VERIFICATION_REQUIRED")
        self.settings, self.clock = settings, clock
        self.client = httpx.Client(
            timeout=settings.timeout_seconds,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
            verify=ssl_context if ssl_context is not None else True,
        )

    def close(self) -> None:
        self.client.close()

    def verify(self, token: str) -> VerifiedIdentity:
        if (
            not isinstance(token, str)
            or len(token) > self.settings.max_token_bytes
            or re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", token) is None
        ):
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        deadline = time.monotonic() + self.settings.timeout_seconds
        try:
            with self.client.stream(
                "POST",
                self.settings.endpoint,
                auth=httpx.BasicAuth(quote_plus(self.settings.client_id), quote_plus(self.settings.client_secret)),
                data={"token": token, "token_type_hint": "access_token"},
                headers={"Accept": "application/json"},
            ) as response:
                if (
                    response.status_code != 200
                    or response.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json"
                ):
                    raise ValueError("INVALID_INTROSPECTION_RESPONSE")
                body = bytearray()
                # A peer can keep every individual read below HTTPX's timeout.
                # Inspect progress without waiting to fill a large output chunk.
                for chunk in response.iter_bytes(chunk_size=1):
                    if time.monotonic() >= deadline:
                        raise ValueError("INTROSPECTION_RESPONSE_DEADLINE_EXCEEDED")
                    body.extend(chunk)
                    if len(body) > self.settings.max_response_bytes:
                        raise ValueError("INTROSPECTION_RESPONSE_TOO_LARGE")
                if time.monotonic() >= deadline:
                    raise ValueError("INTROSPECTION_RESPONSE_DEADLINE_EXCEEDED")
            claims = json.loads(body.decode("utf-8"), object_pairs_hook=unique_object)
            if not isinstance(claims, dict) or type(claims.get("active")) is not bool:
                raise ValueError("INVALID_ACTIVE_FIELD")
        except (httpx.HTTPError, UnicodeError, ValueError, RecursionError):
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        if claims["active"] is not True:
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        audience = claims.get("aud")
        audience_valid = audience == self.settings.audience or (
            isinstance(audience, list)
            and all(isinstance(item, str) for item in audience)
            and self.settings.audience in audience
        )
        expiry = claims.get("exp")
        current = self.clock()
        if type(current) not in (int, float) or not math.isfinite(current):
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        if (
            claims.get("iss") != self.settings.issuer
            or not isinstance(claims.get("sub"), str)
            or not valid_key(claims["sub"], 1024)
            or not audience_valid
            or not isinstance(claims.get("token_type"), str)
            or claims["token_type"].lower() != "bearer"
            or type(expiry) is not int
            or expiry <= current
            or any(
                name in claims and (type(claims[name]) is not int or not 0 <= claims[name] <= current)
                for name in ("nbf", "iat")
            )
        ):
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        return VerifiedIdentity(self.settings.issuer, claims["sub"], expiry)


class MappedTokenAuthority:
    """Compose live token state, least-privilege identity lookup and case policy.

    Caller owns both lifetimes. No adapter is automatically installed by create_app.
    The database connection needs mt_identity_lookup, never directory management.
    """

    def __init__(
        self, verifier: IntrospectionVerifier, lookup: Database, policy: AuthorityProvider | None = None
    ) -> None:
        self.verifier, self.lookup, self.policy = verifier, lookup, policy

    def authenticate(self, bearer: str) -> Actor:
        return self.authenticate_principal(bearer).actor

    def authenticate_principal(self, bearer: str) -> Principal:
        verified = self.verifier.verify(bearer)
        try:
            with self.lookup.engine.begin() as connection:
                unsafe = connection.execute(
                    text(
                        "SELECT rolsuper OR rolbypassrls OR pg_has_role(current_user,'mt_directory_manager','MEMBER') FROM pg_roles WHERE rolname=current_user"
                    )
                ).scalar_one()
                if unsafe:
                    raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
                mapping = IdentityDirectory(connection).resolve(verified.issuer, verified.subject)
        except SQLAlchemyError:
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503) from None
        # Network/database work cannot turn an expired token into a valid identity.
        current = self.verifier.clock()
        if type(current) not in (int, float) or not math.isfinite(current):
            raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
        if verified.expires_at <= current:
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        return Principal(
            actor=Actor(user_id=mapping.user_id, org_id=mapping.org_id),
            issuer=verified.issuer,
            subject=verified.subject,
            expires_at=verified.expires_at,
        )

    def authorize_case(self, actor: Actor, case_id: UUID, action: str) -> Scope:
        if self.policy is None:
            raise BusinessError("FORMAL_POLICY_UNCONFIGURED", 503)
        scope = self.policy.authorize_case(actor, case_id, action)
        if scope.actor != actor or scope.case_id != case_id:
            raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
        return scope

    def authorize_source(self, scope: Scope, source_id: UUID, purpose: str) -> None:
        if self.policy is None:
            raise BusinessError("FORMAL_POLICY_UNCONFIGURED", 503)
        self.policy.authorize_source(scope, source_id, purpose)
