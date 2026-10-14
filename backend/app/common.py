import base64
import hashlib
import io
import os
from pathlib import Path

import boto3
from botocore.config import Config
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CASE_ID = "00000000-0000-4000-8000-000000000001"
BUCKET = "mt-poc-assets"
MAX_BYTES = 1024 * 1024
MAX_IMAGE_PIXELS = 4_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def s3():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def decode_image(encoded: str) -> bytes:
    if len(encoded) > MAX_BYTES * 2:
        raise ValueError("FILE_TOO_LARGE")
    try:
        raw = base64.b64decode(encoded, validate=True)
        if not raw or len(raw) > MAX_BYTES:
            raise ValueError("FILE_TOO_LARGE")
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in {"PNG", "JPEG"} or image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("UNSUPPORTED_IMAGE")
            image.verify()
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("INVALID_IMAGE") from exc
    return raw


def put_object(object_id: str, data: bytes, kind="inputs") -> dict[str, str]:
    digest = hashlib.sha256(data).hexdigest()
    response = s3().put_object(Bucket=BUCKET, Key=f"{kind}/{object_id}", Body=data, Metadata={"sha256": digest})
    version = response.get("VersionId")
    if not version:
        raise RuntimeError("S3_VERSION_ID_MISSING")
    return {"object_id": object_id, "version_id": version, "sha256": digest}


def get_object(ref: dict[str, str], kind="inputs") -> bytes:
    response = s3().get_object(Bucket=BUCKET, Key=f"{kind}/{ref['object_id']}", VersionId=ref["version_id"])
    data = response["Body"].read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != ref["sha256"]:
        raise ValueError("OBJECT_INTEGRITY_FAILED")
    return data
