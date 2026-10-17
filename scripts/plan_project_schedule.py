"""Compute source-work dependency bounds and actual-input capacity plans separately."""
import argparse
import csv
import datetime
import io
import json
import math
import re

from generate_interface_docs import ROOT, digest, read

INPUT = "docs/00-project/execution-planning-inputs.json"
JSON_OUT = "docs/00-project/execution-schedule.json"
MD_OUT = "docs/00-project/execution-schedule.md"
CSV_OUT = "tasks/execution-schedule.csv"


def effort_range(text):
    match = re.fullmatch(r"(\d+)(?:[～~—-](\d+))?人日", text)
    assert match, "UNPARSEABLE_SOURCE_EFFORT:" + text
    low = int(match[1])
    high = int(match[2] or match[1])
    assert 0 < low <= high
    return low, high


def topological(tasks):
    pending = {t["id"]: t for t in tasks}
    order = []
    while pending:
        ready = sorted(tid for tid, task in pending.items() if set(task["execution_dependencies_candidate"]) <= set(order))
        assert ready, "UNKNOWN_DEPENDENCY_OR_CYCLE"
        for tid in ready:
            order.append(tid)
            del pending[tid]
    return order


def batch(task_id):
    number = int(task_id[1:])
    for lower, upper, label in [(1, 10, "B1"), (11, 40, "B2"), (41, 60, "B3"), (61, 89, "B4"),
                                (90, 99, "B5"), (100, 100, "B3"), (101, 108, "B6"), (117, 124, "B7")]:
        if lower <= number <= upper:
            return label
    return "PARALLEL_DATA_TRAINING"


def build_plan(tasks, inputs):
    order = topological(tasks)
    source = {t["id"]: t for t in tasks}
    actual = {row["task_id"]: row for row in inputs["task_execution_inputs"]}
    assert set(actual) == set(source) and len(actual) == len(inputs["task_execution_inputs"])
    resources = {r["resource_id"]: r for r in inputs["resources"]}
    assert len(resources) == len(inputs["resources"])
    missing = []
    if inputs["calendar"].get("weekday_assumption_confirmed") is not True:
        missing.append("confirmed_working_calendar")
    if inputs["actual_plan_start_date"] is None:
        missing.append("actual_plan_start_date")
    if not resources:
        missing.append("actual_personnel_and_effective_weekly_hours")
    for resource in resources.values():
        assert isinstance(resource["name"], str) and resource["name"].strip()
        hours = resource["effective_hours_per_workday"]
        if hours is None:
            missing.append(resource["resource_id"] + ":effective_hours_per_workday")
        else:
            assert type(hours) in (int, float) and math.isfinite(hours) and 0 < hours <= 24
    records, timing = [], {}
    workload = {}
    for task_id in order:
        task = source[task_id]
        execution = actual[task_id]
        low, high = effort_range(task["source_effort"])
        deps = task["execution_dependencies_candidate"]
        early_low = max((timing[d][0] for d in deps), default=0)
        early_high = max((timing[d][1] for d in deps), default=0)
        timing[task_id] = (early_low + low, early_high + high)
        total = workload.setdefault(task["source_role"], {"tasks": 0, "source_effort_low_person_days": 0, "source_effort_high_person_days": 0})
        total["tasks"] += 1
        total["source_effort_low_person_days"] += low
        total["source_effort_high_person_days"] += high
        assert execution["verification_status"] in ["NO_FULL_TASK_VERIFICATION_EVIDENCE", "PARTIAL_VERIFIED_SCOPE", "FULL_TASK_VERIFIED"]
        if execution["verification_status"] == "FULL_TASK_VERIFIED":
            assert execution["full_task_verification_refs"] and execution["actual_start"] and execution["actual_end"]
            assert execution["verified_by"] and execution["remaining_effort_hours"] == 0
        else:
            if execution["resource_id"] is None:
                missing.append(task_id + ":actual_assignee")
            if execution["remaining_effort_hours"] is None:
                missing.append(task_id + ":reestimated_remaining_effort_hours")
        if execution["resource_id"] is not None:
            assert execution["resource_id"] in resources
        assert execution["remaining_effort_hours"] is None or execution["remaining_effort_hours"] >= 0
        assert execution["verification_status"] == "FULL_TASK_VERIFIED" or execution["remaining_effort_hours"] != 0
        for reference in execution["partial_scope_evidence"] + execution["full_task_verification_refs"]:
            assert (ROOT / reference["path"]).is_file(), reference
        records.append({"task_id": task_id, "name": task["name"], "batch": batch(task_id),
                        "source_role": task["source_role"], "source_task_status_unchanged": task["status"],
                        "source_effort": task["source_effort"], "source_effort_low_person_days": low, "source_effort_high_person_days": high,
                        "execution_dependencies_candidate": deps, "dependency_only_start_low_day_offset": early_low,
                        "dependency_only_finish_low_day_offset": early_low + low,
                        "dependency_only_start_high_day_offset": early_high,
                        "dependency_only_finish_high_day_offset": early_high + high,
                        "observed_verification_status": execution["verification_status"],
                        "partial_scope_evidence": execution["partial_scope_evidence"],
                        "actual_assignee_resource_id": execution["resource_id"],
                        "actual_assignee_name": resources[execution["resource_id"]]["name"] if execution["resource_id"] else None,
                        "remaining_effort_hours": execution["remaining_effort_hours"],
                        "actual_start": execution["actual_start"], "actual_end": execution["actual_end"],
                        "capacity_plan_start_date": None, "capacity_plan_finish_date": None,
                        "external_release_date": execution["external_release_date"],
                        "material_or_resource_dependencies": execution["material_or_resource_dependencies"]})
        if execution["material_or_resource_dependencies"] and execution["external_release_date"] is None:
            missing.append(task_id + ":material_or_resource_release_date")
    capacity = {"status": "NOT_COMPUTABLE_ACTUAL_INPUTS_MISSING", "missing_input_count": len(missing),
                "missing_inputs": missing, "calendar_commitment_asserted": False}
    if not missing:
        start = datetime.date.fromisoformat(inputs["actual_plan_start_date"])
        workdays = set(inputs["calendar"]["working_weekdays"])
        assert workdays and workdays <= set(range(7))
        holidays = {datetime.date.fromisoformat(d) for d in inputs["calendar"]["explicit_nonworking_dates"]}
        dates = []
        day = start
        for _ in range(20000):
            if day.weekday() in workdays and day not in holidays:
                dates.append(day)
            day += datetime.timedelta(days=1)
        busy_until = {rid: 0 for rid in resources}
        finishes = {}
        for record in records:
            task_id = record["task_id"]
            execution = actual[task_id]
            if execution["verification_status"] == "FULL_TASK_VERIFIED":
                finishes[task_id] = 0
                continue
            resource_id = execution["resource_id"]
            earliest = max([busy_until[resource_id]] + [finishes[d] for d in record["execution_dependencies_candidate"]])
            if execution["external_release_date"] is not None:
                release = datetime.date.fromisoformat(execution["external_release_date"])
                earliest = max(earliest, next(i for i, d in enumerate(dates) if d >= release))
            duration = math.ceil(execution["remaining_effort_hours"] / resources[resource_id]["effective_hours_per_workday"])
            finish = earliest + duration
            assert duration > 0 and finish <= len(dates)
            record["capacity_plan_start_date"] = dates[earliest].isoformat()
            record["capacity_plan_finish_date"] = dates[finish-1].isoformat()
            busy_until[resource_id] = finish
            finishes[task_id] = finish
        capacity = {"status": "COMPUTED_FROM_PROVIDED_ACTUAL_INPUTS_NOT_APPROVED_COMMITMENT",
                    "missing_input_count": 0, "missing_inputs": [], "calendar_commitment_asserted": False,
                    "finish_date": max((r["capacity_plan_finish_date"] for r in records if r["capacity_plan_finish_date"]), default=None),
                    "assumption": "one task occupies its named responsible resource at a time; conservative whole working-day rounding; secondary participants require separate allocation"}
    totals = {"tasks": len(records), "source_effort_low_person_days": sum(r["source_effort_low_person_days"] for r in records),
              "source_effort_high_person_days": sum(r["source_effort_high_person_days"] for r in records),
              "unconstrained_dependency_critical_path_low_workdays": max((r["dependency_only_finish_low_day_offset"] for r in records), default=0),
              "unconstrained_dependency_critical_path_high_workdays": max((r["dependency_only_finish_high_day_offset"] for r in records), default=0),
              "full_tasks_verified": sum(r["observed_verification_status"] == "FULL_TASK_VERIFIED" for r in records),
              "partial_scope_tasks": sum(r["observed_verification_status"] == "PARTIAL_VERIFIED_SCOPE" for r in records)}
    return {"scope": "all_170_tasks_actual_evidence_inputs_and_source_work_dependency_bounds",
            "revision": "stage-one-four-items-20261013", "source_task_states_changed": False,
            "original_scope_modules": 12, "minimum_business_scenarios": 3, "source_sprint_weeks": 37,
            "source_sprint_weeks_is_approved_calendar": False, "dependency_bounds_are_remaining_actual_effort": False,
            "dependency_bound_assumptions": "source whole task person-day estimates treated as task durations for a hypothetical single lead resource per task; unlimited such resources; candidate dependencies; no holidays/data/GPU waiting or added effort; conditional reference, not universal lower bound or promised dates",
            "totals": totals, "workload_by_unsplit_source_role": workload, "actual_capacity_plan": capacity,
            "records": records}


def outputs():
    plan = build_plan(read("tasks/backlog.yaml")["tasks"], read(INPUT))
    plan["source_hashes"] = {p: digest(p) for p in ["tasks/backlog.yaml", INPUT, "scripts/plan_project_schedule.py"]}
    totals = plan["totals"]
    text = "# 任务实际进度与可计算排期\n\n全部170任务逐条纳入；来源状态不改写，已验证的开发子范围与完整任务验收分开。可编辑输入见[execution-planning-inputs.json](execution-planning-inputs.json)，完整机器排期见[execution-schedule.json](execution-schedule.json)，逐任务表见[execution-schedule.csv](../../tasks/execution-schedule.csv)。\n\n"
    text += f"来源建议工时复算为{totals['source_effort_low_person_days']}—{totals['source_effort_high_person_days']}人日。在每任务由一个主资源投入、1人日暂作1有效工作日、不同任务资源无限的假设下，依赖路径为{totals['unconstrained_dependency_critical_path_low_workdays']}—{totals['unconstrained_dependency_critical_path_high_workdays']}工作日。它是条件参考计算，不是普遍工期下限，也不是剩余实际工期；未扣除未知已完成工作、未包含数据/GPU等待、新增控制与实验失败。原37周迭代保留为来源建议。\n\n"
    text += f"当前有{totals['partial_scope_tasks']}条任务登记了开发子范围证据，完整任务验收登记{totals['full_tasks_verified']}条。没有把未提供验收的任务计为完整完成，也没有从draft状态推出实际0%进度。\n\n"
    text += "## 实际排期所需输入\n\n实际人员、有效工时、剩余工时重估、计划起点、确认的工作日历和材料/GPU到位日期填入后，脚本生成按人力容量和候选依赖排序的日历表；信息缺失时实际日期保持null。联合责任角色需明确参与工时，不能默认一人同时做所有算法/标注/安全工作。\n\n"
    text += f"实际容量排期状态：`{plan['actual_capacity_plan']['status']}`；缺少输入字段{plan['actual_capacity_plan']['missing_input_count']}个，逐项见JSON。容量排期即使计算完成仍需实际负责人核对，不自动成为批准承诺。\n\n"
    text += "## 按来源角色的工作量\n\n| 来源角色（联合角色不拆算） | 任务数 | 建议人日下限 | 建议人日上限 |\n| --- | --- | --- | --- |\n"
    for role, values in plan["workload_by_unsplit_source_role"].items():
        text += f"| {role} | {values['tasks']} | {values['source_effort_low_person_days']} | {values['source_effort_high_person_days']} |\n"
    text += "\n## 七批及并行数据算法\n\nB1工程10条；B2身份/接入/控制30条；B3媒体/网关及T100共21条；B4风险/取证/检索29条；B5首发/传播/核查10条；B6复核/报告8条；B7测试/运维/验收8条；并行数据训练54条。按逐任务前置执行，不强制整批串行。T118早期安全扫描后须T102/T107/T108最终复测；T124还需全170适用交付矩阵及T170真实发布包。\n\n"
    text += "## 更新与重排\n\n1. 将实际人员资源ID、姓名、每工作日有效工时及日历填入输入。\n2. 每任务登记实际开始/结束、子范围证据和剩余工时；完整任务关闭有验收证据、复核人与时间，不能凭部分PoC归零。\n3. 对依赖授权数据/GPU等输入登记到位日；未到位阻断相应真实验证。\n4. 运行`python scripts/plan_project_schedule.py`重建JSON/CSV/阅读页，保留输入及源码摘要；`--check`检查漂移。\n5. 人员/资源不足时更新投入或里程碑；12模块、170任务及≥3场景范围保持，20/100性质不因排期自动降级。\n"
    stream = io.StringIO(newline="")
    fields = ["task_id", "name", "batch", "source_role", "source_effort", "observed_verification_status",
              "actual_assignee_resource_id", "actual_assignee_name", "remaining_effort_hours", "capacity_plan_start_date", "capacity_plan_finish_date",
              "dependency_only_start_low_day_offset", "dependency_only_finish_low_day_offset", "dependency_only_start_high_day_offset", "dependency_only_finish_high_day_offset"]
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(plan["records"])
    return {JSON_OUT: json.dumps(plan, ensure_ascii=False, indent=2) + "\n", MD_OUT: text, CSV_OUT: stream.getvalue()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    differences = []
    generated = outputs()
    for path, content in generated.items():
        target = ROOT / path
        if args.check:
            if not target.is_file() or target.read_bytes() != content.encode():
                differences.append(path)
        else:
            target.write_bytes(content.encode())
    print(json.dumps({"status": "FAIL" if differences else "PASS", "derived_files": len(generated), "differences": differences}))
    return bool(differences)


if __name__ == "__main__":
    raise SystemExit(main())
