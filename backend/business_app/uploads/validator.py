import hashlib
import io
from typing import Any

from PIL import Image


def inspect_uploaded_media(data: bytes, expected_sha256: str, declared_mime: str) -> dict[str, Any] | None:
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        return None
    try:
        with Image.open(io.BytesIO(data)) as image:
            mime = {"PNG": "image/png", "JPEG": "image/jpeg"}.get(image.format or "")
            if mime != declared_mime or image.width * image.height > 4_000_000:
                return None
            metadata = {"mime": mime, "width": image.width, "height": image.height}
            image.verify()
            return metadata
    except (ValueError, OSError, Image.DecompressionBombError):
        return None
