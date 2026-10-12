"""Build an input candidate snapshot; never approve or change source files."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "docs/00-project/stage-one/"
OUTPUT = PREFIX + "input-baseline-candidate.json"
EXCLUDED = ["docs/00-project/validation/", PREFIX + "history/",
            OUTPUT, PREFIX + "input-baseline-candidate.md",
            "docs/00-project/baseline-file-list.txt", "docs/00-project/baseline-file-manifest.json",
            "docs/00-project/repository-file-manifest.json", "docs/00-project/server-sync-receipt.json"]
DIRECTORIES = ["docs/00-project", "docs/01-requirements", "docs/03-api", "docs/04-database",
               "docs/05-workflows", "docs/06-algorithms", "docs/07-datasets", "docs/08-security",
               "docs/09-testing", "docs/source", "docs/_converted", "docs/guides", "docs/assets/source",
               "tasks", "schemas", "datasets", "prompts"]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build():
    seeds = set(DIRECTORIES)
    for item in json.loads((ROOT / (PREFIX + "deliverables.json")).read_text(encoding="utf-8"))["steps"]:
        seeds.update(item["outputs"])
    for item in json.loads((ROOT / (PREFIX + "source-section-map.json")).read_text(encoding="utf-8"))["records"]:
        seeds.update(item["target_refs"])
    seeds.update(["scripts/stage_one_source_audit.py", "scripts/build_stage_one_candidate.py", "scripts/validate_stage_one.py"])
    files = set()
    for seed in sorted(seeds):
        path = ROOT / seed
        for item in path.rglob("*") if path.is_dir() else [path]:
            name = item.relative_to(ROOT).as_posix()
            if item.is_file() and not any(name.startswith(p) if p.endswith("/") else name == p for p in EXCLUDED):
                files.add(name)
    records = [{"path": name, "size_bytes": (ROOT / name).stat().st_size, "sha256": digest(name)} for name in sorted(files)]
    return {"format_version": 1, "revision": "stage-one-input-completion-20261012", "status": "NOT_FROZEN",
            "formal_frozen": False, "approval_record": None, "owner_name": None,
            "scope": "current_first_stage_input_candidate_not_server_sync_or_implementation_or_formal_baseline",
            "selection": {"directories": DIRECTORIES, "explicit_deliverables_and_section_targets": True,
                          "excluded": EXCLUDED, "runtime_reports_excluded_to_avoid_timestamp_churn": True},
            "files": records, "file_count": len(records),
            "historical_snapshots_preserved": [{"path": name, "sha256": digest(name)} for name in
                                               ["docs/00-project/baseline-file-list.txt", "docs/00-project/baseline-file-manifest.json"]]}


def main():
    snapshot = build()
    (ROOT / OUTPUT).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    content = ("# 当前第一阶段候选输入清单\n\n状态：**NOT_FROZEN**。没有批准编号或实际签认人。本清单标识当前用于评审/研发的输入文件，"
               "不表示全部代码任务实施、服务器同步或业务验收完成。机器版本见[input-baseline-candidate.json](input-baseline-candidate.json)。\n\n"
               f"本次候选共{snapshot['file_count']}个文件，按实际字节计算SHA-256；仅覆盖JSON selection定义的输入目录、24步交付及来源章节目标。"
               "运行验证报告、历史归档、旧快照、自身两文件与全仓同步清单排除，避免自引用及时间戳变化。"
               "校验时重新计算集合/大小/摘要，任何输入变化都需重新生成候选，不能仅修改摘要绕过审查。\n\n"
               "旧baseline-file-list.txt和baseline-file-manifest.json保留原字节摘要，仅作为历史输入快照；全仓同步另用repository-file-manifest.json与server-sync-receipt.json。\n\n"
               "正式冻结前需按[冻结检查表](../freeze-checklist.md)取得适用范围、权限/规则/指标/用途、人员资源、遗留及授权记录。"
               "批准后仍须保存该候选与决定的对应关系，不得从本文件推导批准或自动生成正式标签。\n")
    (ROOT / (PREFIX + "input-baseline-candidate.md")).write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"candidate_files": snapshot["file_count"], "status": snapshot["status"]}))


if __name__ == "__main__":
    main()
