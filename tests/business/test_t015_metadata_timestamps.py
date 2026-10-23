"""Actual PostgreSQL timestamp JSON remains parseable on locked Python3.10."""

from uuid import UUID

import psycopg
import pytest
from business_app.types import Scope

from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t014_work import candidate_work
from tests.business.test_upload_validation import complete, prepared_upload


@pytest.mark.parametrize("fraction", ["1", "12", "1234", "12345"])
def test_short_fraction_postgres_timestamp_allows_real_work_authorization(permission_context, fraction):
    ctx = permission_context
    app, http, upload, descriptor = prepared_upload(ctx)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(
                "UPDATE mt.upload_session SET expires_at=%s::timestamptz WHERE upload_id=%s",
                ("2030-01-01T00:00:00." + fraction + "+00:00", UUID(upload)),
            )
        _, manager, _, _, _, _ = candidate_work(ctx, "upload_validation", upload)
        with manager.open(Scope(ctx["actor"], ctx["case_id"]), "upload_validation", UUID(upload), "validateUploadWork"):
            pass  # Actual role, work, metadata and transaction proof must all verify.
    finally:
        http.__exit__(None, None, None)
