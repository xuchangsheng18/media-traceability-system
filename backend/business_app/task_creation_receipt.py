"""Deterministic structural material receipts, never trusted adoption evidence.

Local source bytes and the loaded Schema registry are observations. They are not
attestations of executed bytecode, a released validator or authenticated facts.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import REGISTRY, SCHEMAS
from .task_creation_development import CANONICALIZATION_VERSION as CONFIG_CANONICALIZATION_VERSION
from .task_creation_development import TaskCreationDevelopmentSettings
from .task_creation_materials import CANONICALIZATION_VERSION as MATERIAL_CANONICALIZATION_VERSION
from .task_creation_materials import prepare_material_bundle

SCHEMA_ID = "urn:media-trace:task-material-structure-receipt:1.0.0"
CANONICALIZATION_VERSION = "task-structure-receipt-json-utf8-sortkeys-v1"
STATUS = "MATERIAL_STRUCTURE_VALIDATED_NOT_ADOPTED"
ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = tuple(
    sorted(
        (
            "backend/business_app/task_creation_receipt.py",
            "backend/business_app/task_creation_materials.py",
            "backend/business_app/task_creation_development.py",
            "backend/business_app/contracts.py",
            "scripts/task_creation_adoption.py",
        )
    )
)
_KINDS = ("policy", "plan", "capability", "input")
_LIMITATIONS = (
    "adopted",
    "authority_verified",
    "licence_verified",
    "current_facts_verified",
    "handlers_executed",
    "database_written",
    "network_accessed",
    "task_created",
    "active_mapping_created",
)


def _error(code: str = "INVALID") -> ValueError:
    return ValueError("TASK_STRUCTURE_RECEIPT_" + code)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
            "utf8"
        )
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise _error() from None


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _error()
        value[key] = item
    return value


def _constant(_: str) -> None:
    raise _error()


@dataclass(frozen=True)
class StructureReceipt:
    canonical_bytes: bytes
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_bytes)
        if not isinstance(value, dict):
            raise _error()
        return value


def _source_observation(relative: str) -> dict[str, Any]:
    """Read only a caller-independent fixed inventory, with bounded Linux I/O."""
    descriptors: list[int] = []
    close_failed = False
    try:
        if relative not in SOURCE_PATHS or os.name != "posix" or sys.platform != "linux":
            raise OSError
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        directory = os.open(ROOT.anchor, flags)
        descriptors.append(directory)
        for part in (*ROOT.parts[1:], *Path(relative).parts[:-1]):
            directory = os.open(part, flags, dir_fd=directory)
            descriptors.append(directory)
        parent_before = os.fstat(directory)
        descriptor = os.open(
            Path(relative).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=directory
        )
        descriptors.append(descriptor)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= 1048576:
            raise OSError
        blocks = []
        size = 0
        while size <= 1048576:
            block = os.read(descriptor, min(65536, 1048577 - size))
            if not block:
                break
            blocks.append(block)
            size += len(block)
        after = os.fstat(descriptor)
        parent_after = os.fstat(directory)
        visible = os.stat(Path(relative).name, dir_fd=directory, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if (
            size != before.st_size
            or any(getattr(before, name) != getattr(after, name) for name in fields)
            or any(getattr(parent_before, name) != getattr(parent_after, name) for name in fields)
            or any(getattr(before, name) != getattr(visible, name) for name in fields)
        ):
            raise OSError
        raw = b"".join(blocks)
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
        raise _error("INVENTORY_UNAVAILABLE") from None
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                close_failed = True
    if close_failed:
        raise _error("INVENTORY_UNAVAILABLE")
    return dict(path=relative, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))


def _validate(value: Any) -> None:
    try:
        Draft202012Validator({"$ref": SCHEMA_ID}, registry=REGISTRY).validate(value)
    except Exception:
        raise _error() from None


def _settings(settings: TaskCreationDevelopmentSettings) -> None:
    if type(settings) is not TaskCreationDevelopmentSettings:
        raise _error()
    settings.__post_init__()


def create_structure_receipt(
    raw_materials: tuple[bytes, ...], settings: TaskCreationDevelopmentSettings
) -> StructureReceipt:
    """Reparse actual bytes; do not accept a caller's pre-validated bundle/flag."""
    _settings(settings)
    if (
        type(raw_materials) is not tuple
        or len(raw_materials) != 4
        or any(type(raw) is not bytes for raw in raw_materials)
    ):
        raise _error()
    if sum(map(len, raw_materials)) > settings.max_bundle_bytes:
        raise _error("BUDGET_EXCEEDED")
    bundle = prepare_material_bundle(*raw_materials, budgets=settings.material_budgets())
    materials = (bundle.policy, bundle.plan, bundle.capability, bundle.inputs)
    canonical_size = sum(len(material.canonical_bytes) for material in materials)
    snapshot_size = sum(len(material.canonical_bytes) for material in bundle.node_inputs)
    if canonical_size > settings.max_bundle_bytes or snapshot_size > settings.max_snapshots_bytes:
        raise _error("BUDGET_EXCEEDED")
    declared = [node["handler"]["handler_id"] for node in bundle.plan.as_dict()["nodes"]]
    declared += [handler["handler_id"] for handler in bundle.capability.as_dict()["handlers"]]
    if any(identifier not in settings.allowed_handler_ids for identifier in declared):
        raise _error("BINDING_INVALID")
    document = dict(
        schema_id=SCHEMA_ID,
        schema_version="1.0.0",
        canonicalization_version=CANONICALIZATION_VERSION,
        material_canonicalization_version=MATERIAL_CANONICALIZATION_VERSION,
        status=STATUS,
        validator_protocol="offline-task-material-structure-validation-v1",
        development_configuration=dict(
            runtime_profile=settings.runtime_profile,
            environment=settings.environment,
            revision=settings.revision,
            canonicalization_version=CONFIG_CANONICALIZATION_VERSION,
            sha256=settings.sha256,
            aggregate_bytes=dict(
                source_documents=sum(map(len, raw_materials)),
                canonical_documents=canonical_size,
                node_snapshots=snapshot_size,
            ),
            enforced_limits=dict(
                max_material_bytes=settings.max_material_bytes,
                max_nodes=settings.max_nodes,
                max_capabilities=settings.max_capabilities,
                max_bundle_bytes=settings.max_bundle_bytes,
                max_snapshots_bytes=settings.max_snapshots_bytes,
                allowed_handler_ids=list(settings.allowed_handler_ids),
            ),
        ),
        materials=[
            dict(
                kind=kind,
                schema_id=material.schema_id,
                document_id=material.document_id,
                document_version=material.version,
                canonicalization_version=material.canonicalization_version,
                source_sha256=material.source_sha256,
                source_size_bytes=len(raw),
                canonical_sha256=material.sha256,
                canonical_size_bytes=len(material.canonical_bytes),
            )
            for kind, material, raw in zip(_KINDS, materials, raw_materials)
        ],
        node_inputs=[
            dict(
                node_code=material.document_id,
                schema_id=material.schema_id,
                input_version=material.version,
                canonical_sha256=material.sha256,
                canonical_size_bytes=len(material.canonical_bytes),
            )
            for material in bundle.node_inputs
        ],
        schema_registry=dict(
            canonicalization_version="local-schema-registry-json-v1",
            sha256=hashlib.sha256(_canonical(SCHEMAS)).hexdigest(),
            schema_count=len(SCHEMAS),
        ),
        observed_source_inventory=dict(
            semantics="LOCAL_SOURCE_BYTES_OBSERVED_NOT_EXECUTED_CODE_OR_RELEASE_ATTESTATION",
            files=[_source_observation(name) for name in SOURCE_PATHS],
        ),
        limitations={name: False for name in _LIMITATIONS},
    )
    canonical = _canonical(document)
    if len(canonical) > settings.max_material_bytes:
        raise _error("BUDGET_EXCEEDED")
    _validate(document)
    return StructureReceipt(canonical, hashlib.sha256(canonical).hexdigest())


def verify_structure_receipt(
    raw: bytes, raw_materials: tuple[bytes, ...], settings: TaskCreationDevelopmentSettings
) -> StructureReceipt:
    """Closed canonical receipt plus exact recomputation; never trusted adoption."""
    _settings(settings)
    if type(raw) is not bytes:
        raise _error()
    if len(raw) > settings.max_material_bytes:
        raise _error("BUDGET_EXCEEDED")
    try:
        value = json.loads(raw.decode("utf8"), object_pairs_hook=_unique, parse_constant=_constant)
        canonical = _canonical(value)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise _error() from None
    if len(canonical) > settings.max_material_bytes:
        raise _error("BUDGET_EXCEEDED")
    if raw != canonical:
        raise _error()
    _validate(value)
    expected = create_structure_receipt(raw_materials, settings)
    if canonical != expected.canonical_bytes:
        raise _error("BINDING_INVALID")
    return expected
