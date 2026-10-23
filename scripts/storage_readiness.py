"""Bounded exact-version data readiness after an object-storage restart."""

import time
from typing import Any


def read_version_after_restart(client: Any, bucket: str, key: str, version: str, *, attempts: int = 40) -> bytes:
    if type(attempts) is not int or attempts <= 0:
        raise ValueError("POSITIVE_ATTEMPTS_REQUIRED")
    for attempt in range(attempts):
        try:
            result = client.get_object(Bucket=bucket, Key=key, VersionId=version)["Body"].read()
            if not isinstance(result, bytes):
                raise TypeError("OBJECT_BYTES_REQUIRED")
            return result
        except Exception as error:
            response = getattr(error, "response", None)
            metadata = response.get("ResponseMetadata") if isinstance(response, dict) else None
            status = metadata.get("HTTPStatusCode") if isinstance(metadata, dict) else None
            if status not in {500, 502, 503, 504} or attempt == attempts - 1:
                raise
            time.sleep(1)
    raise RuntimeError("OBJECT_RESTART_NOT_READY")
