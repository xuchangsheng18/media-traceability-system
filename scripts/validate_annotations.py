"""Offline, bounded annotation checks against the existing D01-D15 contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
from pathlib import Path, PureWindowsPath
from typing import Any, NoReturn
from uuid import UUID

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
MAX_FILES = 64
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_DEPTH = 64
MAX_ERRORS = 100
DATASETS = tuple(f"D{number:02}" for number in range(1, 16))
UNVERIFIED = [
    "mask_bytes_and_dimensions",
    "mapping_correctness",
    "actual_source_authorization",
    "human_reviewer_identity",
    "independent_double_annotation",
    "arbitration",
    "business_taxonomy_and_label_correctness",
]


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("JSON_INVALID")
        result[key] = value
    return result


def _constant(_value: str) -> None:
    raise ValueError("JSON_INVALID")


def _shape(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise ValueError("JSON_DEPTH_LIMIT")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("JSON_INVALID")
    if isinstance(value, dict):
        for child in value.values():
            _shape(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _shape(child, depth + 1)


def read_schema(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("SCHEMA_REFERENCE_INVALID")
    return value


def _refs(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"$ref", "$dynamicRef"}:
                if not isinstance(child, str):
                    raise ValueError("SCHEMA_REFERENCE_INVALID")
                result.append(child)
            else:
                result.extend(_refs(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(_refs(child))
    return result


def validators() -> dict[str, Draft202012Validator]:
    paths = [ROOT / "schemas/api/common.schema.json"] + [
        ROOT / f"schemas/dataset/{dataset}.annotation.schema.json" for dataset in DATASETS
    ]
    schemas = [read_schema(path) for path in paths]
    identifiers = {schema["$id"] for schema in schemas}
    if len(identifiers) != len(paths):
        raise ValueError("SCHEMA_REFERENCE_INVALID")
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
        for ref in _refs(schema):
            base = ref.split("#", 1)[0]
            if base and (not base.startswith("urn:media-trace:") or base not in identifiers):
                raise ValueError("SCHEMA_REFERENCE_INVALID")
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas)
    return {
        dataset: Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        for dataset, schema in zip(DATASETS, schemas[1:])
    }


def _safe_components(path: Path) -> None:
    for candidate in [*reversed(path.parents), path]:
        info = candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("INPUT_PATH_INVALID")


def _read(root: Path, name: str, remaining: int) -> bytes:
    relative = Path(name)
    windows = PureWindowsPath(name)
    if (
        not name
        or relative.is_absolute()
        or windows.drive
        or windows.root
        or ".." in relative.parts
        or ".." in windows.parts
        or ":" in name
    ):
        raise ValueError("INPUT_PATH_INVALID")
    target = root / relative
    _safe_components(target)
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("INPUT_PATH_INVALID")
    limit = min(MAX_FILE_BYTES, remaining)
    if info.st_size > limit:
        raise ValueError("INPUT_BYTES_LIMIT")
    descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError("INPUT_PATH_INVALID")
        payload = stream.read(limit + 1)
        if len(payload) > limit or len(payload) != opened.st_size:
            raise ValueError("INPUT_BYTES_LIMIT")
        _safe_components(target)
        latest = target.lstat()
        if (latest.st_dev, latest.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("INPUT_PATH_INVALID")
    return payload


def _semantics(value: Any, duration: int | None) -> int:
    count = 0
    if isinstance(value, dict):
        if "start_ms" in value and "end_ms" in value:
            if value["end_ms"] <= value["start_ms"]:
                count += 1
            if duration is not None and value["end_ms"] > duration:
                count += 1
        if all(key in value for key in ("x", "y", "width", "height")):
            if value["x"] + value["width"] > 1 + 1e-12 or value["y"] + value["height"] > 1 + 1e-12:
                count += 1
        count += sum(_semantics(child, duration) for child in value.values())
    elif isinstance(value, list):
        count += sum(_semantics(child, duration) for child in value)
    return count


def _sampling_arguments_valid(sample_count: int | None, sample_seed: str | None) -> bool:
    if sample_count is None and sample_seed is None:
        return True
    if (
        type(sample_count) is not int
        or sample_count < 1
        or not isinstance(sample_seed, str)
        or not sample_seed.strip()
        or len(sample_seed) > 128
    ):
        return False
    try:
        sample_seed.encode("utf-8")
    except UnicodeError:
        return False
    return True


def validate_files(
    root: Path, names: list[str], *, sample_count: int | None = None, sample_seed: str | None = None
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "FAIL",
        "scope": "OFFLINE_ANNOTATION_STRUCTURE_AND_BOUNDED_SEMANTICS_ONLY",
        "whole_task_accepted": False,
        "training_or_freeze_authorized": False,
        "results": [],
        "errors": [],
    }
    if not _sampling_arguments_valid(sample_count, sample_seed):
        report["errors"] = ["SAMPLING_ARGUMENTS_INVALID"]
        return report
    if not names or len(names) > MAX_FILES:
        report["errors"] = ["INPUT_COUNT_LIMIT"]
        return report
    root = Path(root)
    try:
        if not root.is_absolute() or ".." in root.parts:
            raise ValueError("INPUT_ROOT_INVALID")
        _safe_components(root)
        if not root.is_dir():
            raise ValueError("INPUT_ROOT_INVALID")
        checks = validators()
    except (OSError, ValueError, KeyError, TypeError):
        report["errors"] = ["INPUT_ROOT_OR_SCHEMA_INVALID"]
        return report
    total = 0
    seen: dict[tuple[str, str, str], str] = {}
    for index, name in enumerate(names):
        result: dict[str, Any] = {"input_index": index, "code": "INPUT_INVALID"}
        report["results"].append(result)
        try:
            payload = _read(root, name, MAX_TOTAL_BYTES - total)
            total += len(payload)
            value = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
            _shape(value)
            if not isinstance(value, dict) or value.get("dataset_id") not in DATASETS:
                raise ValueError("SCHEMA_INVALID")
            dataset = value["dataset_id"]
            error_count = 0
            for _error in checks[dataset].iter_errors(value):
                error_count += 1
                if error_count >= MAX_ERRORS:
                    break
            if error_count:
                result.update(code="SCHEMA_INVALID", error_count=error_count)
                continue
            duration = value["payload"]["duration_ms"] if dataset in {"D03", "D04"} else None
            if _semantics(value, duration):
                raise ValueError("SEMANTIC_INVALID")
            sample_id = str(UUID(value["sample_id"]))
            key = (dataset, sample_id, value["annotation_version"])
            canonical_value = {**value, "sample_id": sample_id}
            canonical = hashlib.sha256(
                json.dumps(canonical_value, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            if key in seen:
                raise ValueError("BATCH_DUPLICATE" if seen[key] == canonical else "BATCH_CONFLICT")
            seen[key] = canonical
            result.update(
                code="VALID",
                dataset_id=dataset,
                size_bytes=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
                not_verified=UNVERIFIED + (["media_duration"] if duration is None else []),
            )
        except (OSError, ValueError, TypeError, RecursionError) as error:
            # Error text and JSON-schema messages may contain input values or paths.
            # Export only a fixed vocabulary, never exception strings.
            allowed = {
                "INPUT_PATH_INVALID",
                "INPUT_BYTES_LIMIT",
                "JSON_INVALID",
                "JSON_DEPTH_LIMIT",
                "SCHEMA_INVALID",
                "SEMANTIC_INVALID",
                "BATCH_DUPLICATE",
                "BATCH_CONFLICT",
            }
            result["code"] = str(error) if type(error) is ValueError and str(error) in allowed else "INPUT_INVALID"
    report["total_bytes_read"] = total
    report["status"] = "PASS" if all(item["code"] == "VALID" for item in report["results"]) else "FAIL"
    if report["status"] == "PASS" and sample_count is not None and sample_seed is not None:
        if sample_count > len(report["results"]):
            report.update(status="FAIL", errors=["SAMPLING_ARGUMENTS_INVALID"])
            return report
        seed = sample_seed.encode("utf-8")
        # Reuse hashes of the already validated bytes. Never select before full
        # validation, reread a file, or inspect a sample outside the explicit batch.
        ranked = sorted(
            report["results"],
            key=lambda item: (
                hashlib.sha256(seed + bytes.fromhex(item["sha256"])).digest(),
                item["input_index"],
            ),
        )
        report["sampling"] = dict(
            algorithm="sha256-seed-utf8-input-sha256-bytes-v1",
            seed_digest=hashlib.sha256(seed).hexdigest(),
            input_indices=[item["input_index"] for item in ranked[:sample_count]],
        )
    return report


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ValueError("CLI_ARGUMENTS_INVALID")


def main() -> int:
    parser = _Parser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--sample-count", type=int)
    parser.add_argument("--sample-seed")
    try:
        arguments = parser.parse_args()
        if not _sampling_arguments_valid(arguments.sample_count, arguments.sample_seed):
            raise ValueError("CLI_ARGUMENTS_INVALID")
    except ValueError:
        print(json.dumps({"status": "FAIL", "errors": ["CLI_ARGUMENTS_INVALID"]}))
        return 2
    report = validate_files(
        arguments.input_root, arguments.inputs, sample_count=arguments.sample_count, sample_seed=arguments.sample_seed
    )
    print(json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
