"""Explicit Linux custody file for the existing independent GenerationReader port.

No database read, signature claim, automatic renewal or default wiring. The
operator must independently maintain the pinned identity and this private file.
This internal-development adapter cannot establish institutional custody itself.
"""

import json
import math
import os
import re
import stat
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from ..errors import BusinessError
from ..identity.directory import valid_key
from .fence import GenerationProof

ROOT = Path(__file__).resolve().parents[3]
MAX_BYTES = 16384


def _unavailable() -> BusinessError:
    return BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)


@dataclass(frozen=True)
class GenerationIdentity:
    database_name: str
    database_oid: int
    policy_version: str
    policy_sha256: str
    recovery_generation: str
    minimum_epoch: int


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _unavailable()
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise _unavailable()


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def parse_generation_manifest(
    raw: bytes, *, expected: GenerationIdentity, max_age_seconds: int, now: float
) -> GenerationProof:
    try:
        if (
            type(raw) is not bytes
            or not 0 < len(raw) <= MAX_BYTES
            or type(expected) is not GenerationIdentity
            or type(max_age_seconds) is not int
            or not 0 < max_age_seconds <= 30
            or not _number(now)
        ):
            raise _unavailable()
        binding = asdict(expected)
        if (
            any(
                type(value) is not str or not valid_key(value, 1024)
                for value in (expected.database_name, expected.policy_version, expected.recovery_generation)
            )
            or type(expected.database_oid) is not int
            or not 0 < expected.database_oid <= 2**32 - 1
            or type(expected.minimum_epoch) is not int
            or not 0 < expected.minimum_epoch <= 2**63 - 1
            or type(expected.policy_sha256) is not str
            or re.fullmatch(r"[a-f0-9]{64}", expected.policy_sha256) is None
        ):
            raise _unavailable()
        value = json.loads(raw.decode("utf8"), object_pairs_hook=_unique, parse_constant=_constant)
        if type(value) is not dict or set(value) != {"schema_version", "confirmed_at", "valid_until", *binding}:
            raise _unavailable()
        if value["schema_version"] != "1.0.0":
            raise _unavailable()
        for key, wanted in binding.items():
            actual = value[key]
            if type(actual) is not type(wanted) or (actual < wanted if key == "minimum_epoch" else actual != wanted):
                raise _unavailable()
        if not 0 < value["minimum_epoch"] <= 2**63 - 1:
            raise _unavailable()
        confirmed, deadline = value["confirmed_at"], value["valid_until"]
        if (
            not _number(confirmed)
            or not _number(deadline)
            or not confirmed <= now < deadline
            or now - confirmed > max_age_seconds
            or deadline - confirmed > max_age_seconds
        ):
            raise _unavailable()
        return GenerationProof(
            value["recovery_generation"],
            value["policy_version"],
            value["policy_sha256"],
            value["database_name"],
            value["database_oid"],
            value["minimum_epoch"],
            confirmed,
            deadline,
        )
    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
        raise _unavailable() from None


def _identity(value: os.stat_result) -> tuple[int, ...]:
    return tuple(
        getattr(value, name)
        for name in (
            "st_dev",
            "st_ino",
            "st_uid",
            "st_gid",
            "st_mode",
            "st_nlink",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
    )


def _directory_identity(value: os.stat_result) -> tuple[int, ...]:
    return value.st_dev, value.st_ino, value.st_uid, value.st_gid, value.st_mode


def _trusted_ancestor(value: os.stat_result) -> bool:
    # A root-owned sticky temporary directory protects other users' entries.
    # Other namespaces must not permit a different user/group to replace them.
    return value.st_uid in {0, os.getuid()} and (
        not stat.S_IMODE(value.st_mode) & 0o022 or value.st_uid == 0 and bool(value.st_mode & stat.S_ISVTX)
    )


def _read_private(path: Path) -> bytes:
    descriptors: list[int] = []
    try:
        if (
            os.name != "posix"
            or sys.platform != "linux"
            or not isinstance(path, Path)
            or not path.is_absolute()
            or ".." in path.parts
            or len(path.parts) < 3
            or path.is_relative_to(ROOT)
            or path.resolve().is_relative_to(ROOT)
        ):
            raise _unavailable()
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        parent = os.open(path.anchor, flags)
        descriptors.append(parent)
        ancestry: list[tuple[int, int, str, os.stat_result]] = []
        if not _trusted_ancestor(os.fstat(parent)):
            raise _unavailable()
        for component in path.parts[1:-1]:
            previous = parent
            parent = os.open(component, flags, dir_fd=previous)
            descriptors.append(parent)
            observed = os.fstat(parent)
            if not _trusted_ancestor(observed):
                raise _unavailable()
            ancestry.append((previous, parent, component, observed))
        parent_before = os.fstat(parent)
        if parent_before.st_uid != os.getuid() or stat.S_IMODE(parent_before.st_mode) & 0o077:
            raise _unavailable()
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        descriptors.append(descriptor)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) not in {0o400, 0o600}
            or before.st_nlink != 1
            or not 0 < before.st_size <= MAX_BYTES
        ):
            raise _unavailable()
        blocks: list[bytes] = []
        count = 0
        while count <= MAX_BYTES:
            block = os.read(descriptor, MAX_BYTES + 1 - count)
            if not block:
                break
            blocks.append(block)
            count += len(block)
        if (
            count != before.st_size
            or _identity(before) != _identity(os.fstat(descriptor))
            or _identity(parent_before) != _identity(os.fstat(parent))
            or _identity(before) != _identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
        ):
            raise _unavailable()
        for ancestor, child, component, observed in ancestry:
            if _directory_identity(observed) != _directory_identity(os.fstat(child)) or _directory_identity(
                observed
            ) != _directory_identity(os.stat(component, dir_fd=ancestor, follow_symlinks=False)):
                raise _unavailable()
        return b"".join(blocks)
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
        raise _unavailable() from None
    finally:
        close_failed = False
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                close_failed = True
        if close_failed:
            raise _unavailable()


class PrivateGenerationReader:
    def __init__(
        self, path: Path, *, expected: GenerationIdentity, max_age_seconds: int, clock: Callable[[], float] = time.time
    ) -> None:
        self.path, self.expected, self.max_age_seconds, self.clock = path, expected, max_age_seconds, clock
        self._lock = Lock()
        self._last_time: float | None = None
        self._last_proof: GenerationProof | None = None

    def read(self) -> GenerationProof:
        with self._lock:
            try:
                now = self.clock()
                if not _number(now) or self._last_time is not None and now < self._last_time:
                    raise _unavailable()
                # Failed or expired observations also advance the clock floor.
                self._last_time = now
                result = parse_generation_manifest(
                    _read_private(self.path), expected=self.expected, max_age_seconds=self.max_age_seconds, now=now
                )
                if self._last_proof is not None and (
                    result.confirmed_at < self._last_proof.confirmed_at
                    or result.minimum_epoch < self._last_proof.minimum_epoch
                ):
                    raise _unavailable()
                final = self.clock()
                if not _number(final) or final < now:
                    raise _unavailable()
                self._last_time = final
                if final >= result.valid_until:
                    raise _unavailable()
                self._last_proof = result
                return result
            except Exception:
                raise _unavailable() from None
