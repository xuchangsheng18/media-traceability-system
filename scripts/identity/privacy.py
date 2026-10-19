"""Bounded credential-material review; findings never include credential text."""

import hashlib
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "jwt_material": re.compile(rb"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{16,}\b"),
    "private_key_material": re.compile(
        rb"-----BEGIN ((?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY)-----[\r\n]+[A-Za-z0-9+/=\r\n]{100,}-----END \1-----"
    ),
    "github_token_material": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
}


def scan_bytes(data: bytes, private_values: tuple[bytes, ...]) -> list[dict[str, object]]:
    positions: set[tuple[int, str]] = set()
    for value in private_values:
        if len(value) < 12:
            continue
        start = data.find(value)
        while start >= 0:
            positions.add((start, "known_private_value"))
            start = data.find(value, start + len(value))
    for rule, pattern in PATTERNS.items():
        positions.update((match.start(), rule) for match in pattern.finditer(data))
    return [{"rule": rule, "line": data[:offset].count(b"\n") + 1} for offset, rule in sorted(positions)]


def audit_history(repo: Path, private_values: tuple[bytes, ...]) -> dict[str, object]:
    """Review reachable blobs, including deleted files, without returning their contents."""
    objects = [
        line.split(b" ", 1)[0]
        for line in subprocess.check_output(["git", "rev-list", "--objects", "--all"], cwd=repo).splitlines()
    ]
    raw = subprocess.check_output(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=repo,
        input=b"\n".join(objects) + b"\n",
    )
    rows = [line.split() for line in raw.splitlines()]
    if len(rows) != len(objects) or any(len(row) != 3 for row in rows):
        raise RuntimeError("IDENTITY_HISTORY_OBJECTS_INCOMPLETE")
    blobs = [(oid, int(size)) for oid, kind, size in rows if kind == b"blob"]
    findings = []
    total = 0
    with subprocess.Popen(
        ["git", "cat-file", "--batch"], cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE
    ) as process:
        if process.stdin is None or process.stdout is None:
            raise RuntimeError("IDENTITY_HISTORY_OBJECTS_INCOMPLETE")
        for oid, size in blobs:
            if size > 64 * 1024**2:
                raise RuntimeError("IDENTITY_HISTORY_BLOB_EXCEEDS_REVIEW_BOUND")
            process.stdin.write(oid + b"\n")
            process.stdin.flush()
            header = process.stdout.readline().split()
            if header != [oid, b"blob", str(size).encode()]:
                raise RuntimeError("IDENTITY_HISTORY_OBJECTS_INCOMPLETE")
            data = process.stdout.read(size)
            if len(data) != size or process.stdout.read(1) != b"\n":
                raise RuntimeError("IDENTITY_HISTORY_OBJECTS_INCOMPLETE")
            matches = scan_bytes(data, private_values)
            if matches:
                findings.append({"blob": oid.decode(), "findings": matches})
            total += size
        process.stdin.close()
        if process.wait(timeout=30):
            raise RuntimeError("IDENTITY_HISTORY_OBJECTS_INCOMPLETE")
    refs = subprocess.check_output(["git", "show-ref"], cwd=repo)
    return dict(
        status="FINDINGS_REQUIRE_REVIEW" if findings else "PASS_BOUNDED_AVAILABLE_HISTORY_SCAN",
        reachable_blobs=len(blobs),
        bytes_scanned=total,
        refs_sha256=hashlib.sha256(refs).hexdigest(),
        findings=findings,
        known_private_value_count=len(private_values),
        scope="all_reachable_raw_Git_blobs_at_recorded_refs_not_deleted_unreachable_objects_or_decompressed_binary_contents",
        full_DLP_or_unknown_credential_detection=False,
        credential_values_printed=False,
    )
