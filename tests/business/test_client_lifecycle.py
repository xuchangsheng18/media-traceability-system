"""Fixture teardown must close the lifespan entered by prepared_upload."""

import pytest

from tests.business.test_controls import control_context


def test_control_context_teardown_stops_entered_upload_client_portal(business_context):
    lifecycle = getattr(control_context, "__wrapped__")(business_context)
    context = next(lifecycle)
    client = context["http"]
    portal = client.portal
    try:
        assert portal is not None
        assert portal.call(lambda: True) is True
        lifecycle.close()
        with pytest.raises(RuntimeError, match="not running"):
            portal.call(lambda: True)
        assert client.portal is None
    finally:
        lifecycle.close()
        # Also reap the entered client when this regression fails against the
        # old HTTPX-only close(), so the failing test leaves no portal behind.
        if client.portal is not None:
            client.__exit__(None, None, None)
