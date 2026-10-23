"""Decode only the exact URL-safe Base64 text emitted by a cursor issuer."""

import base64


def decode_cursor(value: str, *, padded: bool) -> bytes:
    raw = base64.b64decode(value if padded else value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    encoded = base64.urlsafe_b64encode(raw).decode("ascii")
    if value != (encoded if padded else encoded.rstrip("=")):
        raise ValueError("NONCANONICAL_CURSOR_ENCODING")
    return raw
