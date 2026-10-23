"""Offline boundary tests; synthetic transfer bytes are never official data evidence."""

import hashlib
import importlib.util
import io
import json
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def tool():
    source = ROOT / "scripts/fetch_public_development_data.py"
    assert source.is_file(), "bounded public development data fetcher is not implemented"
    spec = importlib.util.spec_from_file_location("public_data_fetcher", source)
    assert spec is not None and spec.loader is not None
    import sys

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Response(io.BytesIO):
    def __init__(self, body, *, url, status=200, content_type="image/png", length=None, encoding=None):
        super().__init__(body)
        self.status, self.url = status, url
        self.headers = {"Content-Type": content_type}
        if length is not None:
            self.headers["Content-Length"] = str(length)
        if encoding is not None:
            self.headers["Content-Encoding"] = encoding

    def geturl(self):
        return self.url


class Opener:
    def __init__(self, response):
        self.response, self.calls = response, []

    def open(self, request, *, timeout):
        self.calls.append((request.full_url, timeout))
        return self.response


def transfer(tmp_path, **response_options):
    module = tool()
    payload = b"\x89PNG\r\n\x1a\nself-owned offline transfer fixture"
    asset = replace(module.ASSETS[0], sha256=hashlib.sha256(payload).hexdigest(), size_bytes=len(payload))
    opener = Opener(Response(payload, url=asset.url, **response_options))
    destination = tmp_path / "outside-repository"
    destination.mkdir()
    return module, asset, payload, opener, destination


def test_pinned_manifest_contains_only_the_two_approved_official_files():
    module = tool()
    manifest = module.load_manifest()
    assert [(item["id"], item["size_bytes"], item["sha256"]) for item in manifest["files"]] == [
        ("chelsea", 240512, "596aa1e7cb875eb79f437e310381d26b338a81c2da23439704a73c4651e8c4bb"),
        ("horse", 16633, "c7fb60789fe394c485f842291ea3b21e50d140f39d6dcb5fb9917cc178225455"),
    ]
    assert all(item["license_id"] == "CC0-1.0" and item["creator"] for item in manifest["files"])
    assert manifest["formal_case_import"] is manifest["training_authorized"] is manifest["acceptance_use"] is False
    assert sum(item["size_bytes"] for item in manifest["files"]) < module.DEFAULT_BUDGET < 1024 * 1024


def test_verified_transfer_is_atomic_and_preserves_its_exact_bytes(tmp_path):
    module, asset, payload, opener, destination = transfer(tmp_path)
    value = module.fetch_asset(asset, destination, opener, timeout=3)
    assert (destination / asset.filename).read_bytes() == payload
    assert value == {"id": asset.identifier, "sha256": asset.sha256, "size_bytes": len(payload), "reused": False}
    assert opener.calls == [(asset.url, 3)]
    assert sorted(path.name for path in destination.iterdir()) == [asset.filename]


def test_existing_valid_file_is_checked_and_reused_without_network(tmp_path):
    module, asset, payload, opener, destination = transfer(tmp_path)
    path = destination / asset.filename
    path.write_bytes(payload)
    before = path.stat().st_mtime_ns
    value = module.fetch_asset(asset, destination, opener, timeout=3)
    assert value["reused"] is True and not opener.calls
    assert path.read_bytes() == payload and path.stat().st_mtime_ns == before


def test_existing_tampered_file_is_rejected_without_overwrite_or_network(tmp_path):
    module, asset, payload, opener, destination = transfer(tmp_path)
    path = destination / asset.filename
    path.write_bytes(payload[:-1] + b"!")
    with pytest.raises(module.FetchError, match="DIGEST"):
        module.fetch_asset(asset, destination, opener, timeout=3)
    assert path.read_bytes() != payload and not opener.calls


@pytest.mark.parametrize("defect", ["hash", "truncated", "overflow", "signature"])
def test_bad_response_never_publishes_a_partial_file(tmp_path, defect):
    module, asset, payload, _, destination = transfer(tmp_path)
    body = payload[:-1] + b"!" if defect == "hash" else payload[:-1] if defect == "truncated" else payload + b"!"
    if defect == "signature":
        body = b"not-a-png" + payload[9:]
        asset = replace(asset, sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))
    opener = Opener(Response(body, url=asset.url))
    with pytest.raises(module.FetchError):
        module.fetch_asset(asset, destination, opener, timeout=3)
    assert list(destination.iterdir()) == []


@pytest.mark.parametrize(
    "options",
    [
        {"content_type": "text/html"},
        {"content_type": ""},
        {"length": 999999},
        {"length": "invalid"},
        {"encoding": "gzip"},
        {"status": 302},
        {"status": 404},
    ],
)
def test_bad_http_metadata_is_rejected_before_publication(tmp_path, options):
    module, asset, _, opener, destination = transfer(tmp_path, **options)
    with pytest.raises(module.FetchError):
        module.fetch_asset(asset, destination, opener, timeout=3)
    assert list(destination.iterdir()) == []


def test_redirected_response_and_unsafe_urls_are_rejected(tmp_path):
    module, asset, payload, _, destination = transfer(tmp_path)
    opener = Opener(Response(payload, url="https://untrusted.example/chelsea.png"))
    with pytest.raises(module.FetchError, match="URL"):
        module.fetch_asset(asset, destination, opener, timeout=3)
    for url in [
        asset.url.replace("https:", "http:"),
        "https://raw.githubusercontent.com.evil.example/x",
        asset.url + "?extra=1",
    ]:
        with pytest.raises(module.FetchError, match="URL"):
            module.fetch_asset(replace(asset, url=url), destination, opener, timeout=3)
    with pytest.raises(module.FetchError, match="REDIRECT"):
        module.NoRedirect().redirect_request(None, None, 302, "redirect", {}, asset.url)
    assert not list(destination.iterdir())


@pytest.mark.parametrize("filename", ["../escaped.png", "sub/image.png", "sub\\image.png", "/absolute.png"])
def test_output_filenames_cannot_escape_destination(tmp_path, filename):
    module, asset, _, opener, destination = transfer(tmp_path)
    with pytest.raises(module.FetchError, match="PATH"):
        module.fetch_asset(replace(asset, filename=filename), destination, opener, timeout=3)
    assert not opener.calls and not list(destination.iterdir())


def test_destination_must_be_explicit_absolute_and_outside_repository(tmp_path):
    module = tool()
    for destination in [
        Path("relative"),
        ROOT,
        ROOT / "datasets/public-development/raw",
        ROOT.parent,
        tmp_path / "child/../external",
    ]:
        with pytest.raises(module.FetchError, match="DESTINATION"):
            module.validate_destination(destination)
    assert module.validate_destination(tmp_path / "external") == (tmp_path / "external").resolve()


def test_large_existing_manifest_is_rejected_without_reading_it_all(tmp_path, monkeypatch):
    module = tool()
    target = tmp_path / "manifest.json"
    target.write_bytes(b"x" * (module.DEFAULT_BUDGET + 1))

    def forbidden_read(path):
        raise AssertionError("an oversized existing manifest must not be loaded into memory")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(module.FetchError, match="MANIFEST"):
        module.publish_manifest(tmp_path, b"{}\n")
    assert target.stat().st_size == module.DEFAULT_BUDGET + 1


def test_manifest_publication_rejects_repository_before_creating_tempfile(tmp_path, monkeypatch):
    module = tool()
    repository = tmp_path / "repository"
    repository.mkdir()
    monkeypatch.setattr(module, "ROOT", repository)

    def forbidden_tempfile(*args, **kwargs):
        raise AssertionError("repository validation must happen before any write")

    monkeypatch.setattr(module.tempfile, "mkstemp", forbidden_tempfile)
    with pytest.raises(module.FetchError, match="DESTINATION"):
        module.publish_manifest(repository, b"{}\n")
    assert list(repository.iterdir()) == []


def test_symlink_destination_and_existing_output_are_rejected(tmp_path):
    module, asset, payload, opener, destination = transfer(tmp_path)
    outside = tmp_path / "linked-target"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("This Windows account cannot create symlinks; Linux regression must exercise it")
    with pytest.raises(module.FetchError, match="SYMLINK"):
        module.validate_destination(link / "child")
    target = outside / "actual.png"
    target.write_bytes(payload)
    (destination / asset.filename).symlink_to(target)
    with pytest.raises(module.FetchError, match="SYMLINK"):
        module.fetch_asset(asset, destination, opener, timeout=3)
    assert target.read_bytes() == payload and not opener.calls


def test_manifest_tampering_and_too_small_total_budget_fail_before_fetch(tmp_path):
    module = tool()
    manifest = module.load_manifest()
    manifest["files"][0]["url"] = "https://untrusted.example/image.png"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(module.FetchError, match="MANIFEST"):
        module.load_manifest(path)
    destination = tmp_path / "unused"
    with pytest.raises(module.FetchError, match="BUDGET"):
        module.fetch(destination, budget_bytes=1)
    assert not destination.exists()


def test_concurrent_publication_does_not_overwrite_a_new_existing_file(tmp_path, monkeypatch):
    module, asset, payload, opener, destination = transfer(tmp_path)
    original = module.os.link

    def race(source, target):
        Path(target).write_bytes(b"another-writer")
        return original(source, target)

    monkeypatch.setattr(module.os, "link", race)
    with pytest.raises(module.FetchError):
        module.fetch_asset(asset, destination, opener, timeout=3)
    assert (destination / asset.filename).read_bytes() == b"another-writer"
    assert sorted(path.name for path in destination.iterdir()) == [asset.filename]
