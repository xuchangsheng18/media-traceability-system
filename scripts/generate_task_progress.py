"""Render reviewed task progress without converting partial evidence into acceptance."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = "tasks/execution-status.json"
START = "<!-- task-progress:start -->"
END = "<!-- task-progress:end -->"
LABELS = {
    "PARTIAL_VERIFIED_SCOPE": "已验证部分范围；未关闭",
    "NO_FULL_TASK_VERIFICATION_EVIDENCE": "尚无本任务已验证交付；未关闭",
}


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def validate(ledger, source, planning):
    expected = {f"T{i:03}" for i in range(1, 171)}
    rows = ledger["tasks"]
    assert len(rows) == 170 and {r["task_id"] for r in rows} == set(source) == expected
    assert not ledger["formal_accepted"] and not ledger["completion_percentage_asserted"]
    assert (
        hashlib.sha256((ROOT / "tasks/source-task-cards.json").read_bytes()).hexdigest()
        == ledger["source_task_cards_sha256"]
    )
    actual = {r["task_id"]: r for r in planning["task_execution_inputs"]}
    assert set(actual) == expected
    for row in rows:
        task = row["task_id"]
        assert row["name"] == source[task]["name"]
        assert row["status"] in LABELS and not row["full_task_verified"]
        assert row["actual_owner"] is None and row["remaining_steps"]
        assert row["status"] == actual[task]["verification_status"]
        assert bool(row["completed_steps"]) == (row["status"] == "PARTIAL_VERIFIED_SCOPE")
        assert {e["path"] for s in row["completed_steps"] for e in s["evidence"]} == {
            e["path"] for e in actual[task]["partial_scope_evidence"]
        }
        assert not actual[task]["full_task_verification_refs"]
        assert actual[task]["remaining_effort_hours"] is None and actual[task]["actual_end"] is None
        path = ROOT / row["card"]
        assert path.is_file() and path.resolve().is_relative_to((ROOT / "tasks").resolve())
        assert path.name == task + ".md"
        assert row["summary_completed"] and row["summary_remaining"]
        for step in row["completed_steps"]:
            assert step["description"] and step["evidence"]
            assert step["kind"] in {"DEVELOPMENT", "PROTOTYPE"}
            for evidence in step["evidence"]:
                evidence_path = (ROOT / evidence["path"]).resolve()
                assert evidence_path.is_relative_to(ROOT) and evidence_path.is_file(), evidence["path"]
                assert evidence["scope"]
        assert all(s["description"] and s["category"] for s in row["remaining_steps"])


def cell(text):
    return text.replace("|", "\\|").replace("\n", " ")


def self_test(ledger, source, planning):
    """Reject false acceptance, missing evidence, omissions and inconsistent authorities."""
    mutations = [
        lambda value: value["tasks"][0].update(full_task_verified=True),
        lambda value: value["tasks"][0].update(status="FULL_TASK_VERIFIED"),
        lambda value: value["tasks"][0].update(remaining_steps=[]),
        lambda value: value["tasks"][0].update(name="changed source name"),
        lambda value: value["tasks"].pop(),
        lambda value: value["tasks"][0]["completed_steps"][0]["evidence"][0].update(path="../missing-evidence"),
        lambda value: value["tasks"][0].update(status="NO_FULL_TASK_VERIFICATION_EVIDENCE"),
    ]
    for mutate in mutations:
        invalid = copy.deepcopy(ledger)
        mutate(invalid)
        try:
            validate(invalid, source, planning)
        except AssertionError:
            continue
        raise AssertionError("invalid task progress accepted")
    return len(mutations)


def link(path, card):
    import posixpath

    target = posixpath.relpath(path, posixpath.dirname(card))
    return f"[{path}](<{target}>)"


def block(row, ledger, source):
    task, card = row["task_id"], row["card"]
    text = f"{START}\n## 当前完成步骤与剩余工作\n\n"
    text += f"核对日期：{ledger['observed_date']}。**{LABELS[row['status']]}**。实际负责人、剩余工时及实际完成日期未确认；整任务验收未登记。本节是当前执行记录，文后源计划及历史补充保留追溯。\n\n"
    earlier = ledger["tasks"][: ledger["tasks"].index(row)]
    first = 1 + sum(len(item["completed_steps"]) + len(item["remaining_steps"]) for item in earlier)
    last = first + len(row["completed_steps"]) + len(row["remaining_steps"]) - 1
    text += (
        "分步导航：[170项任务及全局序号](../README.md#分步任务导航)、"
        + link("docs/00-project/task-execution-steps.txt", card)
        + f"。本卡已完成子步骤 **{len(row['completed_steps'])}条**，剩余工作 **{len(row['remaining_steps'])}条**；在逐项清单中对应全局编号 **{first:04}—{last:04}**。\n\n"
    )
    if row.get("specific_validation_report"):
        report = read(row["specific_validation_report"])
        assert report["status"] == "PASS" and report["task_id"] == task
        assert report["runtime_authorization_asserted"] is False and report["production_enabled"] is False
        tests = report["test_run"]
        assert tests["exit_code"] == tests["failures"] == tests["errors"] == tests["skipped"] == 0
        assert tests["tests"] > 0
        text += (
            "同源[状态台账](../execution-status.json)、[全部170任务](../README.md)；本任务以"
            + link(row["specific_validation_report"], card)
            + "中的源码摘要、环境和执行时间为证据。共享历史CI不自动覆盖本批设计；最新托管和同步另见对应报告。开发子范围不代替整任务验收。\n\n"
        )
    else:
        text += f"同源[状态台账](../execution-status.json)、[全部170任务](../README.md)；实现审查快照 `{ledger['implementation_source_commit'][:12]}`，既有实现验证源码 `{ledger['validated_implementation_source_commit'][:12]}`，归档验证 [CI #{ledger['validated_ci_run_id']}](<{ledger['validated_ci_run_url']}>)。本轮资料校验及同步另见最新回执；开发子范围证据不能代替本卡完整验收。\n\n"
    if row.get("acceptance_review_ref"):
        text += (
            "本轮按源验收标准的逐项结论和未闭条件见"
            + link(row["acceptance_review_ref"], card)
            + "；本轮核验限于T001—T011，整任务未因研发检查通过而自动关闭。\n\n"
        )
    if row.get("development_validation_report"):
        development = read(row["development_validation_report"])
        assert development["status"] == "PASS" and development["task_id"] == task
        assert not development["production_enabled"] and not development["runtime_authorization_asserted"]
        totals = development["identity_test_run"]
        assert totals["tests"] > 0 and totals["failures"] == totals["errors"] == totals["skipped"] == 0
        text += (
            "本批身份关系增量的实际命令、源码摘要、PostgreSQL专项与独立研发库以"
            + link(row["development_validation_report"], card)
            + "为准；上面的共享历史CI不自动覆盖新增实现。\n\n"
        )
    if row.get("role_model_validation_report"):
        model = read(row["role_model_validation_report"])
        assert model["status"] == "PASS" and model["task_id"] == task
        assert not model["production_enabled"] and not model["runtime_authorization_asserted"]
        totals = model["full_regression"]
        assert totals["tests"] > 0 and totals["failures"] == totals["errors"] == totals["skipped"] == 0
        text += (
            "本批角色/权限目录、绑定、0005升级与恢复的真实PostgreSQL验证见"
            + link(row["role_model_validation_report"], card)
            + "；已覆盖源模型验收的研发范围，正式身份和后续整链验收仍待落实。\n\n"
        )
    text += "### 已完成步骤及证据\n\n"
    if row["completed_steps"]:
        text += "| 步骤 | 已完成的具体范围 | 证据及适用边界 |\n| --- | --- | --- |\n"
        for number, step in enumerate(row["completed_steps"], 1):
            refs = "；".join(link(e["path"], card) + "：" + cell(e["scope"]) for e in step["evidence"])
            label = "原型验证" if step["kind"] == "PROTOTYPE" else "研发子范围"
            text += f"| {task}-C{number:02}（{label}） | {cell(step['description'])} | {refs} |\n"
    else:
        text += "尚无足以登记为本任务已验证交付的实现证据。已有任务说明、候选契约、共享工程或其他任务的测试，均不自动算成本任务完成步骤；这也不表示已经证明仓库完全不存在相关代码。\n"
    if row["completed_steps"]:
        paths = {e["path"] for s in row["completed_steps"] for e in s["evidence"]}
        text += "\n### 已执行验证与未执行边界\n\n"
        if row.get("specific_validation_report"):
            report = read(row["specific_validation_report"])
            text += f"本任务专属入口：`python scripts/validate_access_control_model.py --run-tests`，在Python {report['python']}执行{report['test_run']['tests']}项合成设计评审测试，失败/错误/跳过均为0。覆盖默认拒绝、显式夹具候选允许、角色和单位/案件/对象/用途/标签/版本及到期撤销边界；不是业务服务授权、真实身份或生产验证。当前精确摘要与结果见本任务专属报告。\n\n"
        if "docs/00-project/validation/business-foundation-report.json" in paths:
            text += "已执行入口：`python scripts/verify_business_foundation.py run`，隔离业务开发测试的数量和源码以最新business-foundation-report及同步回执为准；是相关子范围的共享回归证据，不是本任务的全部验收。采用自建夹具/测试权威适配器，真实身份、正式规则或模型的联调不在该证明范围。\n\n"
        if (
            "docs/00-project/validation/ci-all-report.json" in paths
            or "docs/00-project/validation/github-actions-report.json" in paths
        ):
            text += "已执行入口：隔离Runner中 `python scripts/dev.py ci --allow-stack-changes`，逐道研发门禁及数量以最新ci-all-report与GitHub制品为准。不得在共享环境直接照抄允许改栈参数；该命令不证明全部源功能或生产验收。\n\n"
        if any(s["kind"] == "PROTOTYPE" for s in row["completed_steps"]):
            scripts = sorted(p for p in paths if p.startswith("scripts/") and p.endswith(".py"))
            text += (
                "已执行原型入口："
                + "、".join(f"`python {p}`" for p in scripts)
                + "；仅采用报告标注的自建夹具和规模，正式服务/真实业务验证尚未完成。\n\n"
            )
        text += "本次新增状态记录的检查入口：`python scripts/generate_task_progress.py --check`、`python scripts/validate_inputs.py`；只验证台账、卡片、引用与输入结构，不是补齐剩余业务功能的测试。\n"
    text += "\n### 未完成的剩余工作\n\n"
    for number, step in enumerate(row["remaining_steps"], 1):
        text += f"- [ ] **{task}-R{number:02}／{step['category']}**：{step['description']}\n"
    fields = source[task]["fields"]
    text += "\n### 关闭本卡必须满足\n\n"
    text += f"原验收要求：{fields['验收标准']}\n\n原测试要求：{fields['测试要求']}\n\n"
    text += "关闭前逐项关联剩余工作、实际改动、输入/代码版本、真实执行命令及结果、异常/权限/回归证据和实际复核人。适用外部条件缺失时保留阻塞项，不能只因签字或CI通过就关闭。下文 `tests/.../test_txxx.py` 等计划位置不等于文件已存在，当前真实证据以上表为准。\n"
    return text + END


def outputs():
    ledger = read(LEDGER)
    source = read("tasks/source-task-cards.json")
    planning = read("docs/00-project/execution-planning-inputs.json")
    validate(ledger, source, planning)
    self_test(ledger, source, planning)
    result = {}
    for row in ledger["tasks"]:
        path = ROOT / row["card"]
        old = path.read_text(encoding="utf-8-sig")
        current = block(row, ledger, source)
        if START in old:
            assert old.count(START) == old.count(END) == 1
            before, rest = old.split(START)
            _, after = rest.split(END)
            updated = before + current + after
        else:
            heading, body = old.split("\n", 1)
            updated = heading + "\n\n" + current + "\n" + body
        updated = updated.replace(
            "本卡状态：待评审/未执行；实际测试：未执行；审批：待确认；是否可正式关闭：否。",
            "来源编制时记录：待评审/未执行。此句仅保留历史；当前完成步骤、实际证据及剩余工作以文首执行记录为准，正式审批仍待确认。",
        )
        updated = updated.replace(
            "## 2026-10-12研发工程实施补充\n", "## 2026-10-12研发工程实施补充（历史快照，非当前状态）\n"
        )
        updated = updated.replace("本轮研发实施证据见文末", "当前研发实施证据见文首，文末补充为历史快照")
        updated = updated.replace(
            "状态：待评审独立执行卡；尚未实现。",
            "来源编制时说明：待评审独立执行卡；该历史描述不代表当前执行状态，当前以文首记录为准。",
        )
        result[row["card"]] = updated
    counts = {key: sum(r["status"] == key for r in ledger["tasks"]) for key in LABELS}
    text = "# 独立任务卡与执行清单\n\n170条源任务一任务一文件；角色、源工时、源依赖、工作范围和原验收要求保留。**每张卡文首均列当前完成步骤、真实证据、未完成清单和关闭条件**。计划输出路径、Mock、候选Schema和其他任务的成功不能充当本卡实现证据。\n\n"
    text += f"核对日期：{ledger['observed_date']}。登记开发/原型子范围证据 **{counts['PARTIAL_VERIFIED_SCOPE']}项**；尚无本任务已验证交付 **{counts['NO_FULL_TASK_VERIFICATION_EVIDENCE']}项**；完整任务验收 **0/170**。这些数是证据分类，不是功能完成率或剩余工作量。T001—T010是源工程底座10任务，与资料整理24步、技术基线23步及Codex环境16步分别编号。\n\n"
    text += "[当前机器台账](execution-status.json)保存本表及卡片的执行记录；[源字段](source-task-cards.json)、[源索引](backlog.yaml)保留来源状态；[候选依赖](execution-dependencies-candidate.json)不自动当已满足依赖。实际人员、日期及工时在[实际输入](../docs/00-project/execution-planning-inputs.json)中仍为未确认；[排期](../docs/00-project/execution-schedule.md)与本台账的验证状态一致。\n\n"
    text += "T012之前的11项任务可直接查看[当前完成与剩余逐项清单](../docs/03-development/t001-t011-foundation-review.md#当前完成情况2026-10-17)；它与各卡C/R步骤同源，历史复核另有日期。\n\n"
    text += "## 使用和更新规则\n\n按卡片的C编号查看已完成步骤，按R编号领取剩余工作；任务关闭仍须逐项满足原验收和测试要求。上传/历史读取/审批等仅登记实际实现的子范围；正式身份、规则、真实模型和生产验收仍有缺口。材料齐全或开发测试通过不会自动把170项源任务标为完成。最新实际测试数量和源码见CI报告。\n\n"
    text += "第二阶段23步入口见[交付清单](../docs/03-development/stage-two-readiness.md)，全部接口和数据库见[项目文档导航](../docs/README.md)。`output_refs_planned`与卡内计划测试是后续提案；实际证据列仅引用现有文件。更新台账后运行 `python scripts/generate_task_progress.py` 和相应资料生成器；提交前运行同命令加 `--check`，输入校验也会检查本表与170张卡没有漂移。\n\n"
    completed = sum(len(row["completed_steps"]) for row in ledger["tasks"])
    remaining = sum(len(row["remaining_steps"]) for row in ledger["tasks"])
    text += f"## 分步任务导航\n\n当前台账共 **{completed + remaining}条执行事项**：已完成子步骤 **{completed}条**，剩余工作 **{remaining}条**。全局编号按台账中的任务顺序排列，任务卡内C编号表示已完成子步骤，R编号表示剩余工作；编号用于查阅，实际执行仍按源依赖与适用条件。\n\n"
    text += f"逐项入口：[0001—{completed + remaining:04}完整清单](../docs/00-project/task-execution-steps.txt)；[同源台账](execution-status.json)；[项目文档导航](../docs/README.md)。下表逐项给出已完成数、剩余数和全局编号范围，点击任务编号查看具体C/R步骤及证据。记录粒度不同，不按这些数量换算统一功能完成率；整任务验收仍按各卡关闭条件。\n\n"
    text += "## 170任务当前状态与剩余工作\n\n| 任务 | 名称 | 类别 | 当前状态 | 已完成子步骤 | 剩余工作项 | 全局编号 | 已完成范围 | 未完成的主要工作 |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    next_number = 1
    for row in ledger["tasks"]:
        category = row["card"].split("/")[1]
        target = row["card"].removeprefix("tasks/")
        completed_count, remaining_count = len(row["completed_steps"]), len(row["remaining_steps"])
        last_number = next_number + completed_count + remaining_count - 1
        text += f"| [{row['task_id']}]({target}) | {cell(row['name'])} | {category} | {LABELS[row['status']]} | {completed_count} | {remaining_count} | {next_number:04}—{last_number:04} | {cell(row['summary_completed'])} | {cell(row['summary_remaining'])} |\n"
        next_number = last_number + 1
    result["tasks/README.md"] = text
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    differences = []
    for path, content in outputs().items():
        target = ROOT / path
        if args.check:
            if target.read_bytes() != content.encode():
                differences.append(path)
        else:
            target.write_bytes(content.encode())
    print(
        json.dumps(
            {
                "status": "FAIL" if differences else "PASS",
                "task_cards": 170,
                "negative_guard_cases": 7,
                "full_task_acceptance_asserted": False,
                "differences": differences,
            },
            ensure_ascii=False,
        )
    )
    return bool(differences)


if __name__ == "__main__":
    raise SystemExit(main())
