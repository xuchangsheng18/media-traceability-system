"""Offline material validation/preparation only; no adoption, database, network or execution."""

import argparse
import hashlib
import json
import os
import stat
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from business_app.task_creation_development import TaskCreationDevelopmentSettings
    from business_app.task_creation_materials import CanonicalMaterial, MaterialBundle

ROOT = Path(__file__).resolve().parents[1]
_KINDS = ("policy", "plan", "capability", "input")
_DESCRIPTOR_IO = os.name == "posix" and all(
    hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK")
)


class PreparationError(ValueError):
    """Fixed local error code; never include input contents, paths or raw exceptions."""


class SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.exit(2, '{"status":"FAILED","code":"TASK_PREPARATION_ARGUMENT_INVALID"}\n')


def _absolute(path: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise PreparationError("TASK_PREPARATION_ABSOLUTE_PATH_REQUIRED")
    return path


def _open_directory(path: Path) -> int:
    if not _DESCRIPTOR_IO:
        raise PreparationError("TASK_PREPARATION_SECURE_LINUX_IO_REQUIRED")
    path = _absolute(path)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _read_material(path: Path, maximum: int) -> bytes:
    path = _absolute(path)
    parent = _open_directory(path.parent)
    try:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
    finally:
        os.close(parent)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise PreparationError("TASK_PREPARATION_REGULAR_INPUT_REQUIRED")
        if before.st_size > maximum:
            raise PreparationError("TASK_MATERIAL_BUDGET_EXCEEDED")
        blocks = []
        remaining = maximum + 1
        while remaining:
            block = source.read(min(65536, remaining))
            if not block:
                break
            blocks.append(block)
            remaining -= len(block)
        raw = b"".join(blocks)
        after = os.fstat(source.fileno())
        if len(raw) > maximum:
            raise PreparationError("TASK_MATERIAL_BUDGET_EXCEEDED")
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise PreparationError("TASK_PREPARATION_INPUT_CHANGED")
        return raw


def _output_path(path: Path) -> Path:
    path = _absolute(path)
    resolved = path.resolve()
    repository = ROOT.resolve()
    if resolved.is_relative_to(repository) or repository.is_relative_to(resolved):
        raise PreparationError("TASK_PREPARATION_EXTERNAL_OUTPUT_REQUIRED")
    return path


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _material_files(bundle: "MaterialBundle") -> list[tuple[str, str, "CanonicalMaterial"]]:
    fixed = [
        ("policy", "policy.canonical.json", bundle.policy),
        ("plan", "execution-plan.canonical.json", bundle.plan),
        ("capability", "capability-manifest.canonical.json", bundle.capability),
        ("input", "input-manifest.canonical.json", bundle.inputs),
    ]
    return fixed + [
        ("node_input", f"node-input-{index:06d}.canonical.json", material)
        for index, material in enumerate(bundle.node_inputs, 1)
    ]


def _manifest(bundle: "MaterialBundle", limits: dict[str, int]) -> tuple[dict[str, Any], list[tuple[str, bytes]]]:
    entries = []
    files = []
    for kind, name, material in _material_files(bundle):
        raw = material.canonical_bytes
        if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != material.sha256:
            raise PreparationError("TASK_PREPARATION_CANONICAL_BYTES_INVALID")
        entries.append(
            dict(
                kind=kind,
                filename=name,
                schema_id=material.schema_id,
                document_id=material.document_id,
                version=material.version,
                canonicalization_version=material.canonicalization_version,
                sha256=material.sha256,
                source_sha256=material.source_sha256,
                size_bytes=len(raw),
            )
        )
        files.append((name, raw))
    manifest = dict(
        schema_version="task-material-preparation-v1",
        status="OFFLINE_MATERIALS_ONLY_NOT_ADOPTED",
        limits=limits,
        artifacts=entries,
        database_written=False,
        network_accessed=False,
        active_mapping_created=False,
        task_created=False,
        handlers_executed=False,
        authority_or_license_verified=False,
        budgets_are_caller_inputs_not_formal_acceptance=True,
    )
    return manifest, files


def _write_exclusive(directory: int, name: str, raw: bytes, created: list[tuple[str, tuple[int, int]]]) -> None:
    descriptor = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory
    )
    try:
        created.append((name, _identity(os.fstat(descriptor))))
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise PreparationError("TASK_PREPARATION_WRITE_INCOMPLETE")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_owned_files(directory: int, created: list[tuple[str, tuple[int, int]]]) -> None:
    for name, identity in reversed(created):
        try:
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if stat.S_ISREG(current.st_mode) and _identity(current) == identity:
                os.unlink(name, dir_fd=directory)
        except OSError:
            pass


def _save_prepared(output: Path, files: list[tuple[str, bytes]]) -> None:
    output = _output_path(output)
    parent = _open_directory(output.parent)
    directory = None
    owned_directory = None
    created: list[tuple[str, tuple[int, int]]] = []
    complete = False
    try:
        try:
            os.mkdir(output.name, 0o700, dir_fd=parent)
        except FileExistsError:
            raise PreparationError("TASK_PREPARATION_OUTPUT_ALREADY_EXISTS") from None
        owned_directory = _identity(os.stat(output.name, dir_fd=parent, follow_symlinks=False))
        directory = os.open(output.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
        if _identity(os.fstat(directory)) != owned_directory:
            raise PreparationError("TASK_PREPARATION_OUTPUT_CHANGED")
        for name, raw in files:
            _write_exclusive(directory, name, raw, created)
        os.fsync(directory)
        visible = _open_directory(output)
        try:
            if _identity(os.fstat(visible)) != owned_directory:
                raise PreparationError("TASK_PREPARATION_OUTPUT_CHANGED")
        finally:
            os.close(visible)
        os.fsync(parent)
        complete = True
    finally:
        if not complete and directory is not None:
            _remove_owned_files(directory, created)
        if directory is not None:
            os.close(directory)
        if not complete and owned_directory is not None:
            try:
                current = os.stat(output.name, dir_fd=parent, follow_symlinks=False)
                if stat.S_ISDIR(current.st_mode) and _identity(current) == owned_directory:
                    # Empty only; unknown/new files are preserved. Never recursively remove paths.
                    os.rmdir(output.name, dir_fd=parent)
            except OSError:
                pass
        os.close(parent)


def _finish_preparation(
    bundle: "MaterialBundle",
    limits: dict[str, int],
    output: Path | None,
    configuration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest, files = _manifest(bundle, limits)
    if configuration is not None:
        manifest["development_configuration"] = configuration
    manifest_bytes = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()
    if output is not None:
        _save_prepared(output, [*files, ("manifest.json", manifest_bytes)])
    result: dict[str, Any] = dict(
        status="PREPARED_OFFLINE_NOT_ADOPTED" if output is not None else "VALIDATED_OFFLINE_NOT_ADOPTED",
        artifact_count=len(files),
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        output_written=output is not None,
        database_written=False,
        network_accessed=False,
        active_mapping_created=False,
        task_created=False,
        authority_or_license_verified=False,
    )
    if configuration is not None:
        result["development_configuration"] = configuration
    return result


def run(action: str, paths: dict[str, Path], limits: dict[str, int], output: Path | None = None) -> dict[str, Any]:
    if action not in {"validate", "prepare"} or set(paths) != set(_KINDS):
        raise PreparationError("TASK_PREPARATION_ARGUMENT_INVALID")
    if set(limits) != {"max_bytes", "max_nodes", "max_capabilities"} or any(
        type(value) is not int or value <= 0 for value in limits.values()
    ):
        raise PreparationError("TASK_MATERIAL_LIMIT_INVALID")
    if (action == "prepare") != (output is not None):
        raise PreparationError("TASK_PREPARATION_ARGUMENT_INVALID")
    if output is not None:
        _output_path(output)
    # Fixed trusted module only. Material handler IDs are data, never import paths or commands.
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from business_app.task_creation_materials import MaterialBudgets, prepare_material_bundle

    budgets = MaterialBudgets(**limits)
    raw = [_read_material(paths[kind], budgets.max_bytes) for kind in _KINDS]
    bundle = prepare_material_bundle(*raw, budgets=budgets)
    return _finish_preparation(bundle, limits, output)


def _development_observation(
    settings: "TaskCreationDevelopmentSettings", bundle: "MaterialBundle", source_size: int
) -> dict[str, Any]:
    from business_app.task_creation_development import CANONICALIZATION_VERSION

    canonical_size = sum(
        len(value.canonical_bytes) for value in (bundle.policy, bundle.plan, bundle.capability, bundle.inputs)
    )
    if canonical_size > settings.max_bundle_bytes:
        raise PreparationError("TASK_PREPARATION_BUNDLE_BUDGET_EXCEEDED")
    snapshot_size = sum(len(value.canonical_bytes) for value in bundle.node_inputs)
    if snapshot_size > settings.max_snapshots_bytes:
        raise PreparationError("TASK_PREPARATION_SNAPSHOT_BUDGET_EXCEEDED")
    plan = bundle.plan.as_dict()
    capabilities = bundle.capability.as_dict()
    declared = [node["handler"]["handler_id"] for node in plan["nodes"]]
    declared += [handler["handler_id"] for handler in capabilities["handlers"]]
    if any(identifier not in settings.allowed_handler_ids for identifier in declared):
        raise PreparationError("TASK_PREPARATION_HANDLER_NOT_ALLOWED")
    return dict(
        runtime_profile=settings.runtime_profile,
        environment=settings.environment,
        revision=settings.revision,
        canonicalization_version=CANONICALIZATION_VERSION,
        sha256=settings.sha256,
        aggregate_bytes=dict(
            source_documents=source_size, canonical_documents=canonical_size, node_snapshots=snapshot_size
        ),
        enforced_limits=dict(
            max_material_bytes=settings.max_material_bytes,
            max_nodes=settings.max_nodes,
            max_capabilities=settings.max_capabilities,
            max_bundle_bytes=settings.max_bundle_bytes,
            max_snapshots_bytes=settings.max_snapshots_bytes,
            allowed_handler_ids=list(settings.allowed_handler_ids),
        ),
    )


def run_development(
    action: str,
    paths: dict[str, Path],
    configuration_path: Path,
    *,
    runtime_profile: str,
    output: Path | None = None,
) -> dict[str, Any]:
    """Enforce offline byte budgets; never activate, import or execute handlers."""
    if (
        action not in {"validate-development", "prepare-development"}
        or set(paths) != set(_KINDS)
        or any(not isinstance(path, Path) for path in paths.values())
        or (action == "prepare-development") != (output is not None)
    ):
        raise PreparationError("TASK_PREPARATION_ARGUMENT_INVALID")
    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from business_app.task_creation_development import load_task_creation_development
    from business_app.task_creation_materials import prepare_material_bundle

    # Config/profile rejection happens before material reads and output selection.
    settings = load_task_creation_development(configuration_path, runtime_profile=runtime_profile)
    if output is not None:
        _output_path(output)
    budgets = settings.material_budgets()
    limits = dict(max_bytes=budgets.max_bytes, max_nodes=budgets.max_nodes, max_capabilities=budgets.max_capabilities)
    raw = []
    source_size = 0
    for kind in _KINDS:
        value = _read_material(paths[kind], budgets.max_bytes)
        source_size += len(value)
        if source_size > settings.max_bundle_bytes:
            raise PreparationError("TASK_PREPARATION_BUNDLE_BUDGET_EXCEEDED")
        raw.append(value)
    bundle = prepare_material_bundle(*raw, budgets=budgets)
    observation = _development_observation(settings, bundle, source_size)
    return _finish_preparation(bundle, limits, output, observation)


def _positive(value: str) -> int:
    try:
        result = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("EXPLICIT_POSITIVE_INTEGER_REQUIRED") from None
    if result <= 0:
        raise argparse.ArgumentTypeError("EXPLICIT_POSITIVE_INTEGER_REQUIRED")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = SafeParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True, parser_class=SafeParser)
    for action in ("validate", "prepare", "validate-development", "prepare-development"):
        current = actions.add_parser(action)
        for kind in _KINDS:
            current.add_argument("--" + kind, type=Path, required=True)
        if action.endswith("-development"):
            current.add_argument("--runtime-profile", choices=("development", "test"), required=True)
            current.add_argument("--development-config", type=Path, required=True)
        else:
            for limit in ("max-bytes", "max-nodes", "max-capabilities"):
                current.add_argument("--" + limit, type=_positive, required=True)
        if action in {"prepare", "prepare-development"}:
            current.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        paths = {kind: getattr(args, kind) for kind in _KINDS}
        if args.action.endswith("-development"):
            result = run_development(
                args.action,
                paths,
                args.development_config,
                runtime_profile=args.runtime_profile,
                output=getattr(args, "output", None),
            )
        else:
            result = run(
                args.action,
                paths,
                {name: getattr(args, name) for name in ("max_bytes", "max_nodes", "max_capabilities")},
                getattr(args, "output", None),
            )
    except (OSError, ValueError, RuntimeError) as error:
        safe_material_codes = {
            "TASK_MATERIAL_INVALID",
            "TASK_MATERIAL_LIMIT_INVALID",
            "TASK_MATERIAL_BUDGET_EXCEEDED",
            "TASK_MATERIAL_BINDING_INVALID",
            "TASK_CREATION_DEVELOPMENT_CONFIG_INVALID",
            "TASK_CREATION_DEVELOPMENT_PROFILE_NOT_APPROVED",
            "TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED",
        }
        code = (
            str(error)
            if isinstance(error, PreparationError) or str(error) in safe_material_codes
            else "TASK_PREPARATION_LOCAL_OR_MATERIAL_INVALID"
        )
        print(json.dumps(dict(status="FAILED", code=code, output_complete=False)))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
