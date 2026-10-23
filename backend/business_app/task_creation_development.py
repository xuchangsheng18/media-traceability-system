"""Explicit frozen development configuration, never authority or runtime adoption.

These limits are parsed inputs. Loading them does not wire HTTP/SQL, enforce a
runtime deadline, publish a handler, or establish any current permission fact.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from .task_creation_materials import MaterialBudgets

CONFIGURATION_MAX_BYTES = 16384
CANONICALIZATION_VERSION = "task-creation-development-json-v1"
ENVIRONMENT = "linux-py311-cpu-internal-rnd"
RESERVED_HANDLER_ID = "internal-rnd-original-integrity"
ROOT = Path(__file__).resolve().parents[2]
_CEILINGS = {
    "max_material_bytes": 262144,
    "max_nodes": 16,
    "max_capabilities": 64,
    "max_bundle_bytes": 1048576,
    "max_snapshots_bytes": 4194304,
    "max_http_body_bytes": 16384,
    "proof_budget_seconds": 30,
    "control_ttl_seconds": 86400,
    "adoption_max_seconds": 604800,
    "generation_max_age_seconds": 30,
    "capability_lease_seconds": 60,
    "node_lease_seconds": 60,
    "max_object_bytes": 1048576,
    "handler_deadline_seconds": 10,
    "db_connect_timeout_seconds": 2,
    "db_pool_timeout_seconds": 2,
    "db_statement_timeout_ms": 2000,
    "db_lock_timeout_ms": 1000,
    "create_deadline_seconds": 10,
    "max_concurrent_handlers": 1,
    "prefetch_count": 1,
    "max_task_temp_bytes": 8388608,
    "max_incomplete_temp_tasks": 2,
}


def _invalid() -> ValueError:
    return ValueError("TASK_CREATION_DEVELOPMENT_CONFIG_INVALID")


def _profile(value: str) -> None:
    if type(value) is not str or value not in {"development", "test"}:
        raise ValueError("TASK_CREATION_DEVELOPMENT_PROFILE_NOT_APPROVED")


@dataclass(frozen=True)
class TaskCreationDevelopmentSettings:
    runtime_profile: str
    schema_version: str
    environment: str
    revision: str
    allowed_handler_ids: tuple[str, ...]
    max_material_bytes: int
    max_nodes: int
    max_capabilities: int
    max_bundle_bytes: int
    max_snapshots_bytes: int
    max_http_body_bytes: int
    proof_budget_seconds: int
    control_ttl_seconds: int
    adoption_max_seconds: int
    generation_max_age_seconds: int
    capability_lease_seconds: int
    node_lease_seconds: int
    max_object_bytes: int
    handler_deadline_seconds: int
    db_connect_timeout_seconds: int
    db_pool_timeout_seconds: int
    db_statement_timeout_ms: int
    db_lock_timeout_ms: int
    create_deadline_seconds: int
    max_concurrent_handlers: int
    prefetch_count: int
    max_task_temp_bytes: int
    max_incomplete_temp_tasks: int
    min_free_space_bytes: int

    def __post_init__(self) -> None:
        _profile(self.runtime_profile)
        if (
            type(self.schema_version) is not str
            or self.schema_version != "1.0.0"
            or type(self.environment) is not str
            or self.environment != ENVIRONMENT
            or type(self.revision) is not str
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", self.revision) is None
            or type(self.allowed_handler_ids) is not tuple
            or self.allowed_handler_ids != (RESERVED_HANDLER_ID,)
            or any(type(value) is not str for value in self.allowed_handler_ids)
        ):
            raise _invalid()
        for name, ceiling in _CEILINGS.items():
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise _invalid()
        if type(self.min_free_space_bytes) is not int or not 5368709120 <= self.min_free_space_bytes <= 2**63 - 1:
            raise _invalid()
        if not (
            self.max_material_bytes <= self.max_bundle_bytes <= 4 * self.max_material_bytes
            and self.max_material_bytes <= self.max_snapshots_bytes <= self.max_nodes * self.max_material_bytes
            and self.max_http_body_bytes <= self.max_material_bytes
            and self.max_object_bytes + self.max_bundle_bytes + self.max_snapshots_bytes <= self.max_task_temp_bytes
            and self.create_deadline_seconds <= self.proof_budget_seconds
            and self.handler_deadline_seconds <= self.node_lease_seconds
            and self.db_connect_timeout_seconds <= self.create_deadline_seconds
            and self.db_pool_timeout_seconds <= self.create_deadline_seconds
            and self.db_lock_timeout_ms <= self.db_statement_timeout_ms <= 1000 * self.create_deadline_seconds
            and self.prefetch_count == self.max_concurrent_handlers
        ):
            raise _invalid()

    def material_budgets(self) -> MaterialBudgets:
        return MaterialBudgets(self.max_material_bytes, self.max_nodes, self.max_capabilities)

    def as_dict(self) -> dict[str, Any]:
        value = {field.name: getattr(self, field.name) for field in fields(self) if field.name != "runtime_profile"}
        value["allowed_handler_ids"] = list(self.allowed_handler_ids)
        return {"task_creation_development": value}

    @property
    def canonical_bytes(self) -> bytes:
        # This is a configuration digest only, not a plan/receipt/current-fact digest.
        value = {
            "runtime_profile": self.runtime_profile,
            "canonicalization_version": CANONICALIZATION_VERSION,
            "configuration": self.as_dict(),
        }
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
            "utf8"
        )

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes).hexdigest()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for name, item in pairs:
        if name in value:
            raise _invalid()
        value[name] = item
    return value


def _constant(_: str) -> None:
    raise _invalid()


def parse_task_creation_development(raw: bytes, *, runtime_profile: str) -> TaskCreationDevelopmentSettings:
    _profile(runtime_profile)
    if type(raw) is not bytes or not 0 < len(raw) <= CONFIGURATION_MAX_BYTES:
        raise _invalid()
    try:
        value = json.loads(raw.decode("utf8"), object_pairs_hook=_unique, parse_constant=_constant)
        if type(value) is not dict or set(value) != {"task_creation_development"}:
            raise _invalid()
        document = value["task_creation_development"]
        expected = {field.name for field in fields(TaskCreationDevelopmentSettings)} - {"runtime_profile"}
        if type(document) is not dict or set(document) != expected or type(document["allowed_handler_ids"]) is not list:
            raise _invalid()
        return TaskCreationDevelopmentSettings(
            **dict(document, allowed_handler_ids=tuple(document["allowed_handler_ids"])),
            runtime_profile=runtime_profile,
        )
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        raise _invalid() from None


def _identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_uid,
        value.st_gid,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def load_task_creation_development(path: Path, *, runtime_profile: str) -> TaskCreationDevelopmentSettings:
    """Read a bounded Linux private file without following any path-component link.

    The 16KiB format read ceiling is distinct from the configurable HTTP limit.
    Every opened descriptor is closed; neither paths nor configuration bytes are
    included in errors. No environment variable or default configuration is read.
    """
    _profile(runtime_profile)
    descriptors: list[int] = []
    close_failed = False
    try:
        if (
            os.name != "posix"
            or sys.platform != "linux"
            or not isinstance(path, Path)
            or not path.is_absolute()
            or ".." in path.parts
        ):
            raise OSError
        if path.is_relative_to(ROOT) or path.resolve().is_relative_to(ROOT):
            raise OSError
        if len(path.parts) < 3:
            raise OSError
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        parent = os.open(path.anchor, directory_flags)
        descriptors.append(parent)
        for component in path.parts[1:-1]:
            parent = os.open(component, directory_flags, dir_fd=parent)
            descriptors.append(parent)
        parent_before = os.fstat(parent)
        if parent_before.st_uid != os.getuid() or stat.S_IMODE(parent_before.st_mode) & 0o077:
            raise OSError
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        descriptors.append(descriptor)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) not in {0o400, 0o600}
            or before.st_nlink != 1
            or not 0 < before.st_size <= CONFIGURATION_MAX_BYTES
        ):
            raise OSError
        blocks: list[bytes] = []
        size = 0
        while size <= CONFIGURATION_MAX_BYTES:
            block = os.read(descriptor, CONFIGURATION_MAX_BYTES + 1 - size)
            if not block:
                break
            blocks.append(block)
            size += len(block)
        if (
            size != before.st_size
            or _identity(before) != _identity(os.fstat(descriptor))
            or _identity(parent_before) != _identity(os.fstat(parent))
            or _identity(before) != _identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
        ):
            raise OSError
        raw = b"".join(blocks)
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
        raise ValueError("TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED") from None
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                close_failed = True
    if close_failed:
        raise ValueError("TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED")
    return parse_task_creation_development(raw, runtime_profile=runtime_profile)
