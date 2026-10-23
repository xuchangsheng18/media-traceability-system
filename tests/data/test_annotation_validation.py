"""Bounded offline annotation validation; synthetic records only."""

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate_annotations.py"


@pytest.fixture
def module():
    spec = importlib.util.spec_from_file_location("annotation_validation_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def fixture(dataset="D01"):
    return json.loads((ROOT / f"tests/fixtures/dataset/{dataset}.annotation.json").read_text(encoding="utf-8"))


def write(tmp_path, value, name="input.json"):
    path = tmp_path / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return name


@pytest.mark.parametrize("number", range(1, 16))
def test_existing_positive_records_are_valid_without_claiming_acceptance(module, tmp_path, number):
    name = write(tmp_path, fixture(f"D{number:02}"))
    before = (tmp_path / name).read_bytes()
    report = module.validate_files(tmp_path, [name])
    assert report["status"] == "PASS"
    assert report["whole_task_accepted"] is False
    assert "independent_double_annotation" in report["results"][0]["not_verified"]
    assert (tmp_path / name).read_bytes() == before


@pytest.mark.parametrize("number", range(1, 16))
def test_existing_reviewed_without_reviewer_is_rejected(module, tmp_path, number):
    value = json.loads((ROOT / f"tests/fixtures/negative/D{number:02}.annotation.json").read_text(encoding="utf-8"))
    report = module.validate_files(tmp_path, [write(tmp_path, value)])
    assert report["status"] == "FAIL"
    assert report["results"][0]["code"] == "SCHEMA_INVALID"


@pytest.mark.parametrize(
    "change",
    [
        lambda v: v.pop("sample_id"),
        lambda v: v.update(sample_id="not-a-uuid"),
        lambda v: v.update(extra="private-person"),
        lambda v: v["payload"]["labels"][0].update(time_range={"start_ms": 4, "end_ms": 4}),
        lambda v: v["payload"]["labels"][0].update(time_range={"start_ms": 5, "end_ms": 4}),
        lambda v: v["payload"]["labels"][0].update(bbox={"x": 0.8, "y": 0, "width": 0.3, "height": 1}),
        lambda v: v["payload"]["labels"][0]["bbox"].update(width=0),
    ],
)
def test_invalid_fields_and_semantic_boundaries(module, tmp_path, change):
    value = fixture()
    change(value)
    assert module.validate_files(tmp_path, [write(tmp_path, value)])["status"] == "FAIL"


@pytest.mark.parametrize("dataset", ["D03", "D04"])
def test_duration_is_checked_only_from_actual_record_duration(module, tmp_path, dataset):
    value = fixture(dataset)
    value["payload"]["events"][0]["time_range"]["end_ms"] = value["payload"]["duration_ms"]
    name = write(tmp_path, value)
    result = module.validate_files(tmp_path, [name])["results"][0]
    assert result["code"] == "VALID"
    assert "media_duration" not in result["not_verified"]
    value["payload"]["events"][0]["time_range"]["end_ms"] += 1
    write(tmp_path, value)
    assert module.validate_files(tmp_path, [name])["status"] == "FAIL"


@pytest.mark.parametrize("status", ["unknown", "disputed", "draft"])
def test_unknown_and_disputed_are_preserved_without_forced_review(module, tmp_path, status):
    value = fixture()
    value.update(annotation_status=status, reviewer_refs=[])
    value["payload"]["labels"][0]["bbox"] = {"x": 0, "y": 0, "width": 1, "height": 1}
    name = write(tmp_path, value)
    assert module.validate_files(tmp_path, [name])["status"] == "PASS"
    assert json.loads((tmp_path / name).read_text())["annotation_status"] == status


@pytest.mark.parametrize("dataset", ["D05", "D14"])
def test_insufficient_relation_remains_legal(module, tmp_path, dataset):
    value = fixture(dataset)
    value["payload"]["relation"] = "insufficient"
    assert module.validate_files(tmp_path, [write(tmp_path, value)])["status"] == "PASS"


def test_hard_negative_review_requires_existing_human_confirmation_rule(module, tmp_path):
    value = fixture("D15")
    value["payload"]["human_confirmed"] = False
    assert module.validate_files(tmp_path, [write(tmp_path, value)])["status"] == "FAIL"


@pytest.mark.parametrize(
    "payload", ['{"dataset_id":"D01","dataset_id":"D02"}', '{"value":NaN}', '{"value":Infinity}', "[]", "{"]
)
def test_malformed_or_ambiguous_json_is_rejected(module, tmp_path, payload):
    (tmp_path / "input.json").write_text(payload, encoding="utf-8")
    assert module.validate_files(tmp_path, ["input.json"])["status"] == "FAIL"


@pytest.mark.parametrize("name", ["../outside.json", "nested/../input.json", "/absolute.json", "C:\\outside.json"])
def test_input_cannot_escape_explicit_root(module, tmp_path, name):
    assert module.validate_files(tmp_path, [name])["status"] == "FAIL"


def test_engineering_budgets_reject_before_processing(module, tmp_path, monkeypatch):
    name = write(tmp_path, fixture())
    monkeypatch.setattr(module, "MAX_FILES", 1)
    assert module.validate_files(tmp_path, [name, name])["status"] == "FAIL"
    monkeypatch.setattr(module, "MAX_FILE_BYTES", 3)
    assert module.validate_files(tmp_path, [name])["status"] == "FAIL"


def test_total_bytes_budget_is_enforced(module, tmp_path, monkeypatch):
    first = write(tmp_path, fixture(), "first.json")
    second = write(tmp_path, fixture("D02"), "second.json")
    monkeypatch.setattr(module, "MAX_TOTAL_BYTES", (tmp_path / first).stat().st_size)
    assert module.validate_files(tmp_path, [first, second])["status"] == "FAIL"


def test_symlink_is_refused(module, tmp_path):
    name = write(tmp_path, fixture())
    try:
        (tmp_path / "link.json").symlink_to(tmp_path / name)
    except OSError:
        pytest.skip("Symlink creation requires operating-system privilege")
    assert module.validate_files(tmp_path, ["link.json"])["status"] == "FAIL"


def test_offline_registry_never_accepts_network_reference(module, monkeypatch):
    schema = copy.deepcopy(json.loads((ROOT / "schemas/dataset/D01.annotation.schema.json").read_text()))
    schema["$ref"] = "https://example.invalid/private"
    monkeypatch.setattr(module, "read_schema", lambda path: schema)
    with pytest.raises(ValueError, match="SCHEMA_REFERENCE_INVALID"):
        module.validators()


def test_duplicate_or_conflicting_record_is_mechanical_failure(module, tmp_path):
    value = fixture()
    names = [write(tmp_path, value, "first.json"), write(tmp_path, value, "second.json")]
    report = module.validate_files(tmp_path, names)
    assert report["results"][1]["code"] == "BATCH_DUPLICATE"
    value["payload"]["risk_level"] = "another-synthetic-label"
    write(tmp_path, value, "second.json")
    assert module.validate_files(tmp_path, names)["results"][1]["code"] == "BATCH_CONFLICT"


@pytest.mark.parametrize("changed", [False, True])
def test_uuid_case_cannot_bypass_batch_duplicate_or_conflict(module, tmp_path, changed):
    value = fixture()
    value["sample_id"] = "abcdefab-1234-4567-89ab-abcdefabcdef"
    first = write(tmp_path, value, "first.json")
    other = copy.deepcopy(value)
    other["sample_id"] = other["sample_id"].upper()
    if changed:
        other["payload"]["labels"][0]["label"] = "self-owned-changed-label"
    second = write(tmp_path, other, "second.json")
    report = module.validate_files(tmp_path, [first, second])
    assert report["status"] == "FAIL"
    assert report["results"][1]["code"] == ("BATCH_CONFLICT" if changed else "BATCH_DUPLICATE")


def test_report_does_not_echo_paths_labels_or_personal_fields(module, tmp_path):
    value = fixture()
    value["payload"]["labels"][0]["label"] = "private-person-secret"
    value["extra-private-field"] = "private-person-secret"
    report = module.validate_files(tmp_path, [write(tmp_path, value, "private-person-secret.json")])
    assert "private-person-secret" not in json.dumps(report)
    assert "extra-private-field" not in json.dumps(report)


def test_cli_stdout_json_and_exit_code_without_side_effects(tmp_path):
    name = write(tmp_path, fixture())
    before = list(tmp_path.iterdir())
    command = [sys.executable, str(SCRIPT), "--input-root", str(tmp_path), "--inputs", name]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "PASS"
    (tmp_path / name).write_text("{}")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "FAIL"
    assert list(tmp_path.iterdir()) == before


def test_depth_and_nonfinite_exponent_are_rejected(module, tmp_path):
    for text in ["[" * 80 + "0" + "]" * 80, '{"value":1e999}']:
        (tmp_path / "input.json").write_text(text, encoding="utf-8")
        assert module.validate_files(tmp_path, ["input.json"])["status"] == "FAIL"


def test_reparse_point_is_rejected_without_windows_privilege(module, tmp_path, monkeypatch):
    from types import SimpleNamespace

    original = Path.lstat

    def reparse(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == tmp_path:
            return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
        return info

    monkeypatch.setattr(Path, "lstat", reparse)
    assert module.validate_files(tmp_path, ["input.json"])["status"] == "FAIL"


def test_cli_argument_error_is_redacted_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--private-person-secret"], capture_output=True, text=True, check=False
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["errors"] == ["CLI_ARGUMENTS_INVALID"]
    assert "private-person-secret" not in result.stdout + result.stderr


def sampling_batch(tmp_path):
    names = []
    for index in range(5):
        value = fixture()
        value["sample_id"] = "00000000-0000-4000-8000-" + f"{index + 1:012d}"
        names.append(write(tmp_path, value, f"record-{index}.json"))
    return names


def test_sampling_is_opt_in(module, tmp_path):
    report = module.validate_files(tmp_path, sampling_batch(tmp_path))
    assert report["status"] == "PASS" and "sampling" not in report


def test_sampling_reproduces_fixed_seed_rank_without_replacement_or_extra_reads(module, tmp_path, monkeypatch):
    names = sampling_batch(tmp_path)
    original = module._read
    reads = []

    def observed(root, name, remaining):
        reads.append(name)
        return original(root, name, remaining)

    monkeypatch.setattr(module, "_read", observed)
    report = module.validate_files(tmp_path, names, sample_count=3, sample_seed="self-owned-seed-a")
    assert report["status"] == "PASS"
    assert report["sampling"] == {
        "algorithm": "sha256-seed-utf8-input-sha256-bytes-v1",
        "seed_digest": hashlib.sha256(b"self-owned-seed-a").hexdigest(),
        "input_indices": [2, 4, 3],
    }
    assert reads == names and len(report["results"]) == 5
    reads.clear()
    repeated = module.validate_files(tmp_path, names, sample_count=3, sample_seed="self-owned-seed-a")
    assert repeated == report and reads == names
    assert "self-owned-seed-a" not in json.dumps(report)


def test_different_explicit_seed_changes_the_hand_checked_selection(module, tmp_path):
    names = sampling_batch(tmp_path)
    report = module.validate_files(tmp_path, names, sample_count=3, sample_seed="self-owned-seed-b")
    assert report["status"] == "PASS" and report["sampling"]["input_indices"] == [4, 1, 2]
    assert report["sampling"]["seed_digest"] == hashlib.sha256(b"self-owned-seed-b").hexdigest()


@pytest.mark.parametrize("count", [1, 5])
def test_sampling_accepts_both_count_boundaries_without_repeating_indices(module, tmp_path, count):
    names = sampling_batch(tmp_path)
    before = {name: (tmp_path / name).read_bytes() for name in names}
    report = module.validate_files(tmp_path, names, sample_count=count, sample_seed="self-owned-seed-a")
    assert report["status"] == "PASS"
    selected = report["sampling"]["input_indices"]
    assert selected == [2, 4, 3, 1, 0][:count] and len(set(selected)) == count
    assert {name: (tmp_path / name).read_bytes() for name in names} == before
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(names)


@pytest.mark.parametrize(
    "count,seed",
    [
        (None, "private-sample-seed"),
        (1, None),
        (True, "private-sample-seed"),
        (False, "private-sample-seed"),
        (1.0, "private-sample-seed"),
        ("1", "private-sample-seed"),
        (0, "private-sample-seed"),
        (-1, "private-sample-seed"),
        (6, "private-sample-seed"),
        (1, ""),
        (1, " \t"),
        (1, "x" * 129),
        (1, True),
        (1, 7),
    ],
)
def test_sampling_rejects_unpaired_or_invalid_parameters_without_seed_echo(module, tmp_path, count, seed):
    report = module.validate_files(tmp_path, sampling_batch(tmp_path), sample_count=count, sample_seed=seed)
    assert report["status"] == "FAIL" and report["errors"] == ["SAMPLING_ARGUMENTS_INVALID"]
    assert "sampling" not in report and "private-sample-seed" not in json.dumps(report)


def test_sampling_accepts_exact_seed_character_limit(module, tmp_path):
    report = module.validate_files(tmp_path, sampling_batch(tmp_path), sample_count=1, sample_seed="种" * 128)
    assert report["status"] == "PASS" and len(report["sampling"]["input_indices"]) == 1
    assert report["sampling"]["seed_digest"] == hashlib.sha256(("种" * 128).encode("utf-8")).hexdigest()


@pytest.mark.parametrize("defect", ["schema", "malformed", "path", "duplicate", "conflict", "total_budget"])
def test_sampling_never_hides_invalid_unsampled_records(module, tmp_path, monkeypatch, defect):
    names = sampling_batch(tmp_path)
    if defect == "schema":
        write(tmp_path, {}, names[-1])
    elif defect == "malformed":
        (tmp_path / names[-1]).write_text("{", encoding="utf-8")
    elif defect == "path":
        names[-1] = "../private-person.json"
    elif defect in {"duplicate", "conflict"}:
        value = json.loads((tmp_path / names[0]).read_text(encoding="utf-8"))
        if defect == "conflict":
            value["payload"]["labels"][0]["label"] = "self-owned-conflict"
        write(tmp_path, value, names[-1])
    else:
        monkeypatch.setattr(module, "MAX_TOTAL_BYTES", sum((tmp_path / name).stat().st_size for name in names[:-1]))
    report = module.validate_files(tmp_path, names, sample_count=1, sample_seed="self-owned-seed-a")
    assert report["status"] == "FAIL" and "sampling" not in report
    assert [value["input_index"] for value in report["results"]] == [0, 1, 2, 3, 4]
    assert report["results"][-1]["code"] != "VALID"


def test_cli_sampling_matches_repeated_explicit_selection_without_seed_echo(tmp_path):
    names = sampling_batch(tmp_path)
    command = [
        sys.executable,
        str(SCRIPT),
        "--input-root",
        str(tmp_path),
        "--inputs",
        *names,
        "--sample-count",
        "3",
        "--sample-seed",
        "self-owned-seed-a",
    ]
    first = subprocess.run(command, capture_output=True, text=True, check=False)
    second = subprocess.run(command, capture_output=True, text=True, check=False)
    assert first.returncode == second.returncode == 0, first.stderr + second.stderr
    assert first.stdout == second.stdout and not first.stderr and not second.stderr
    assert json.loads(first.stdout)["sampling"]["input_indices"] == [2, 4, 3]
    assert "self-owned-seed-a" not in first.stdout


@pytest.mark.parametrize(
    "options,exit_code",
    [
        (["--sample-count", "1"], 2),
        (["--sample-seed", "private-sample-seed"], 2),
        (["--sample-count", "true", "--sample-seed", "private-sample-seed"], 2),
        (["--sample-count", "1.5", "--sample-seed", "private-sample-seed"], 2),
        (["--sample-count", "0", "--sample-seed", "private-sample-seed"], 2),
        (["--sample-count", "1", "--sample-seed", ""], 2),
        (["--sample-count", "1", "--sample-seed", "x" * 129], 2),
        (["--sample-count", "6", "--sample-seed", "private-sample-seed"], 1),
    ],
)
def test_cli_sampling_rejects_invalid_arguments_with_safe_json(tmp_path, options, exit_code):
    command = [
        sys.executable,
        str(SCRIPT),
        "--input-root",
        str(tmp_path),
        "--inputs",
        *sampling_batch(tmp_path),
        *options,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == exit_code and not result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "FAIL" and "sampling" not in report
    assert "private-sample-seed" not in result.stdout and "x" * 129 not in result.stdout
