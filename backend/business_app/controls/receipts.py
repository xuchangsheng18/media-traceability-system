from dataclasses import replace
from typing import Any

from sqlalchemy import Connection

from ..db import Database
from ..errors import BusinessError
from ..settings import BusinessSettings
from ..types import Scope
from ..uploads.repository import UploadRepository


class ControlReceipts(UploadRepository):
    def __init__(self, database: Database, settings: BusinessSettings) -> None:
        self.control_ttl = settings.control_ttl_seconds
        super().__init__(
            database, replace(settings, upload_ttl_seconds=settings.control_ttl_seconds or settings.upload_ttl_seconds)
        )

    def replay(
        self, connection: Connection, scope: Scope, operation: str, key: str, digest: str
    ) -> dict[str, Any] | None:
        if self.control_ttl is None:
            raise BusinessError("CONTROL_RECEIPT_TTL_UNCONFIRMED", 503)
        return super().replay(connection, scope, operation, key, digest)
