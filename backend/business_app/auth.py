from typing import Protocol, cast
from uuid import UUID

from fastapi import Request

from .errors import BusinessError
from .types import Actor, Scope


class AuthorityProvider(Protocol):
    def authenticate(self, bearer: str) -> Actor: ...

    def authorize_case(self, actor: Actor, case_id: UUID, action: str) -> Scope: ...

    def authorize_source(self, scope: Scope, source_id: UUID, purpose: str) -> None: ...


def authorize_request(request: Request, case_id: UUID, action: str) -> Scope:
    authority = cast(AuthorityProvider | None, request.app.state.business_authority)
    if authority is None:
        raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or not header[7:]:
        raise BusinessError("AUTHENTICATION_REQUIRED", 401)
    actor = authority.authenticate(header[7:])
    scope = authority.authorize_case(actor, case_id, action)
    if scope.actor != actor or scope.case_id != case_id:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    return scope
