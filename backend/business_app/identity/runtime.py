"""Own both authentication resources; partial initialization never leaks them."""

import ssl

from ..auth import AuthorityProvider
from ..db import Database
from .config import IdentityRuntimeConfig
from .tokens import IntrospectionVerifier, MappedTokenAuthority


class IdentityResources:
    def __init__(
        self, verifier: IntrospectionVerifier, lookup: Database, policy: AuthorityProvider | None = None
    ) -> None:
        self.verifier, self.lookup = verifier, lookup
        self.authority = MappedTokenAuthority(verifier, lookup, policy)
        self.closed = False

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            try:
                self.verifier.close()
            finally:
                self.lookup.close()


def open_identity(config: IdentityRuntimeConfig, policy: AuthorityProvider | None = None) -> IdentityResources:
    verifier = None
    lookup = None
    try:
        context = ssl.create_default_context(cafile=str(config.ca_file))
        verifier = IntrospectionVerifier(config.introspection, ssl_context=context)
        lookup = Database(config.lookup_dsn)
        return IdentityResources(verifier, lookup, policy)
    except Exception:
        if verifier is not None:
            verifier.close()
        if lookup is not None:
            lookup.close()
        raise RuntimeError("IDENTITY_INITIALIZATION_FAILED") from None
