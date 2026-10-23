"""Fetch exactly two pinned CC0 publisher samples into an explicit external directory."""

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "datasets/public-development/manifest.json"
DEFAULT_BUDGET = 512 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
BASE = "https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/"


class FetchError(ValueError):
    pass


@dataclass(frozen=True)
class Asset:
    identifier: str
    filename: str
    url: str
    sha256: str
    size_bytes: int


ASSETS = (
    Asset(
        "chelsea",
        "chelsea.png",
        BASE + "chelsea.png",
        "596aa1e7cb875eb79f437e310381d26b338a81c2da23439704a73c4651e8c4bb",
        240512,
    ),
    Asset(
        "horse",
        "horse.png",
        BASE + "horse.png",
        "c7fb60789fe394c485f842291ea3b21e50d140f39d6dcb5fb9917cc178225455",
        16633,
    ),
)


def expected_manifest() -> dict[str, Any]:
    creators = {"chelsea": "Stefan van der Walt", "horse": "Andreas Preuss (marauder)"}
    return {
        "schema_version": 1,
        "pack_id": "scikit-image-v0.25.2-two-cc0-images",
        "use_scope": "offline_development",
        "formal_case_import": False,
        "training_authorized": False,
        "acceptance_use": False,
        "truth_status": "no_task_domain_ground_truth",
        "declares_download_or_decode_result": False,
        "files": [
            {
                "id": asset.identifier,
                "filename": asset.filename,
                "url": asset.url,
                "sha256": asset.sha256,
                "size_bytes": asset.size_bytes,
                "content_type": "image/png",
                "creator": creators[asset.identifier],
                "license_id": "CC0-1.0",
                "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                "per_image_license_source": "https://scikit-image.org/docs/0.25.x/api/skimage.data.html#skimage.data."
                + asset.identifier,
                "hash_source": BASE + "_registry.py",
                "allowed_development_uses": ["image_decode", "metadata_parse", "transform_and_coordinate_bookkeeping"],
                "annotation_boundary": "Publisher sample description is not a business label or model accuracy ground truth.",
            }
            for asset in ASSETS
        ],
    }


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise FetchError("MANIFEST_UNAVAILABLE") from None
    if value != expected_manifest():
        raise FetchError("MANIFEST_PIN_MISMATCH")
    return value


def reject_symlinks(path: Path) -> None:
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise FetchError("SYMLINK_OR_REPARSE_POINT_FORBIDDEN")


def validate_destination(destination: Path) -> Path:
    if not destination.is_absolute():
        raise FetchError("DESTINATION_MUST_BE_ABSOLUTE")
    if ".." in destination.parts:
        raise FetchError("DESTINATION_TRAVERSAL_FORBIDDEN")
    reject_symlinks(destination)
    target = destination.resolve()
    if target.is_relative_to(ROOT) or ROOT.is_relative_to(target):
        raise FetchError("DESTINATION_MUST_BE_OUTSIDE_REPOSITORY")
    if target.exists() and not target.is_dir():
        raise FetchError("DESTINATION_MUST_BE_DIRECTORY")
    return target


def validate_asset(asset: Asset) -> None:
    if asset.filename != asset.identifier + ".png" or re.fullmatch(r"[a-z]+\.png", asset.filename) is None:
        raise FetchError("OUTPUT_PATH_INVALID")
    parsed = urlsplit(asset.url)
    if (
        asset.url not in {item.url for item in ASSETS}
        or parsed.scheme != "https"
        or parsed.netloc != "raw.githubusercontent.com"
        or parsed.hostname != "raw.githubusercontent.com"
    ):
        raise FetchError("SOURCE_URL_NOT_PINNED")
    if type(asset.size_bytes) is not int or not 0 < asset.size_bytes < 1024 * 1024:
        raise FetchError("FILE_SIZE_INVALID")
    if re.fullmatch(r"[a-f0-9]{64}", asset.sha256) is None:
        raise FetchError("DIGEST_INVALID")


def verify_file(path: Path, asset: Asset) -> None:
    reject_symlinks(path)
    if not path.is_file() or path.stat().st_size != asset.size_bytes:
        raise FetchError("EXISTING_FILE_SIZE_MISMATCH")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        header = stream.read(8)
        if header != PNG_SIGNATURE:
            raise FetchError("PNG_SIGNATURE_INVALID")
        digest.update(header)
        count = len(header)
        while block := stream.read(min(65536, asset.size_bytes - count + 1)):
            count += len(block)
            if count > asset.size_bytes:
                raise FetchError("FILE_SIZE_MISMATCH")
            digest.update(block)
    if count != asset.size_bytes or digest.hexdigest() != asset.sha256:
        raise FetchError("FILE_DIGEST_MISMATCH")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FetchError("REDIRECT_FORBIDDEN")


def fetch_asset(asset: Asset, destination: Path, opener: Any, *, timeout: float) -> dict[str, Any]:
    validate_asset(asset)
    destination = validate_destination(destination)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise FetchError("TIMEOUT_INVALID")
    destination.mkdir(parents=True, exist_ok=True)
    validate_destination(destination)
    target = destination / asset.filename
    reject_symlinks(target)
    result = dict(id=asset.identifier, sha256=asset.sha256, size_bytes=asset.size_bytes, reused=False)
    if target.exists():
        verify_file(target, asset)
        return dict(result, reused=True)
    temporary: Path | None = None
    try:
        request = urllib.request.Request(asset.url, headers={"Accept": "image/png", "Accept-Encoding": "identity"})
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200:
                raise FetchError("HTTP_STATUS_INVALID")
            if response.geturl() != asset.url:
                raise FetchError("RESPONSE_URL_CHANGED")
            if response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "image/png":
                raise FetchError("CONTENT_TYPE_INVALID")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise FetchError("CONTENT_ENCODING_INVALID")
            declared = response.headers.get("Content-Length")
            if declared is not None and (
                not declared.isascii() or not declared.isdecimal() or int(declared) != asset.size_bytes
            ):
                raise FetchError("CONTENT_LENGTH_INVALID")
            descriptor, name = tempfile.mkstemp(prefix=".public-data-", dir=destination)
            temporary = Path(name)
            with os.fdopen(descriptor, "wb") as output:
                count = 0
                while block := response.read(min(65536, asset.size_bytes - count + 1)):
                    count += len(block)
                    if count > asset.size_bytes:
                        raise FetchError("RESPONSE_SIZE_EXCEEDED")
                    output.write(block)
                output.flush()
                os.fsync(output.fileno())
        verify_file(temporary, asset)
        validate_destination(destination)
        reject_symlinks(target)
        try:
            # Atomic no-replace publication on the same filesystem; never overwrite a racing writer.
            os.link(temporary, target)
        except FileExistsError:
            verify_file(target, asset)
            result["reused"] = True
        return result
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def manifest_matches(target: Path, payload: bytes) -> bool:
    reject_symlinks(target)
    if not target.is_file() or target.stat().st_size != len(payload):
        return False
    with target.open("rb") as source:
        return source.read(len(payload) + 1) == payload


def publish_manifest(destination: Path, payload: bytes) -> None:
    destination = validate_destination(destination)
    target = destination / "manifest.json"
    reject_symlinks(target)
    if target.exists():
        if not manifest_matches(target, payload):
            raise FetchError("EXISTING_MANIFEST_MISMATCH")
        return
    descriptor, name = tempfile.mkstemp(prefix=".public-data-", dir=destination)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        validate_destination(destination)
        try:
            os.link(temporary, target)
        except FileExistsError:
            reject_symlinks(target)
            if not manifest_matches(target, payload):
                raise FetchError("EXISTING_MANIFEST_MISMATCH") from None
    finally:
        temporary.unlink(missing_ok=True)


def fetch(destination: Path, *, budget_bytes: int = DEFAULT_BUDGET, timeout: float = 10) -> dict[str, Any]:
    manifest = load_manifest()
    if type(budget_bytes) is not int or not sum(asset.size_bytes for asset in ASSETS) <= budget_bytes < 1024 * 1024:
        raise FetchError("TOTAL_BUDGET_INVALID")
    destination = validate_destination(destination)
    for filename in [*(asset.filename for asset in ASSETS), "manifest.json"]:
        reject_symlinks(destination / filename)
    payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    if (destination / "manifest.json").exists() and not manifest_matches(destination / "manifest.json", payload):
        raise FetchError("EXISTING_MANIFEST_MISMATCH")
    opener = urllib.request.build_opener(NoRedirect())
    files = [fetch_asset(asset, destination, opener, timeout=timeout) for asset in ASSETS]
    publish_manifest(destination, payload)
    return {"status": "PINNED_BYTES_VERIFIED_NOT_DECODED", "formal_case_import": False, "files": files}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination", required=True, type=Path, help="Explicit absolute directory outside this repository"
    )
    parser.add_argument("--budget-bytes", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    try:
        result = fetch(args.destination, budget_bytes=args.budget_bytes, timeout=args.timeout)
    except (FetchError, OSError, urllib.error.URLError) as error:
        code = str(error) if isinstance(error, FetchError) else "PUBLIC_DATA_FETCH_FAILED"
        print(json.dumps({"status": "FAILED", "code": code}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
