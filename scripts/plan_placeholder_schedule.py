"""User-authorized placeholder staffing scenario; never writes actual personnel or dates."""
import argparse
import csv
import io
import json

from generate_interface_docs import ROOT, digest, read
from plan_project_schedule import build_plan

INPUT = "docs/00-project/execution-planning-scenario-inputs.json"


def outputs():
    inputs = read(INPUT)
    assert inputs["scenario_only"] and inputs["actual_people_confirmed"] is False
    assert all(r["placeholder"] and r["name"].startswith("占位") for r in inputs["planning_inputs"]["resources"])
    plan = build_plan(read("tasks/backlog.yaml")["tasks"], inputs["planning_inputs"])
    assert plan["actual_capacity_plan"]["missing_input_count"] == 0
    capacity = plan.pop("actual_capacity_plan")
    capacity["status"] = "PLACEHOLDER_CAPACITY_SCENARIO_NOT_ACTUAL_PLAN"
    plan["scenario_capacity_plan"] = capacity
    plan.update(scope="user_requested_placeholder_staffing_scenario_all_170_tasks_not_actual_personnel",
                actual_people_confirmed=False, all_calendar_dates_assumed=True, scenario_assumptions=inputs["assumptions"],
                source_hashes={p: digest(p) for p in [INPUT, "tasks/backlog.yaml", "scripts/plan_placeholder_schedule.py", "scripts/plan_project_schedule.py"]})
    resources = {r["resource_id"]: r for r in inputs["planning_inputs"]["resources"]}
    for row in plan["records"]:
        row["scenario_resource_id"] = row.pop("actual_assignee_resource_id")
        row["scenario_resource_name"] = resources[row["scenario_resource_id"]]["name"]
        row["scenario_start_date"] = row.pop("capacity_plan_start_date")
        row["scenario_finish_date"] = row.pop("capacity_plan_finish_date")
        row["assumed_remaining_effort_hours"] = row.pop("remaining_effort_hours")
        row["assumed_external_release_date"] = row.pop("external_release_date")
    milestones = []
    for label in ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "PARALLEL_DATA_TRAINING"]:
        rows = [r for r in plan["records"] if r["batch"] == label]
        milestones.append({"batch": label, "tasks": len(rows), "scenario_first_start": min(r["scenario_start_date"] for r in rows),
                           "scenario_last_finish": max(r["scenario_finish_date"] for r in rows)})
    plan["scenario_milestones"] = milestones
    plan["source_target_month_for_comparison_only"] = "2027-06"
    plan["exceeds_source_target_month_under_assumptions"] = capacity["finish_date"] > "2027-06-30"
    text = "# 占位人员与假设排期\n\n用户明确要求先填写占位人员、后续替换实际信息。本方案中的姓名/投入/起点/资源日期均为**规划假设**；实际[人员容量输入](execution-planning-inputs.json)仍未确认。本方案不产生实际任务完成、真实到岗或正式交付承诺。\n\n"
    text += f"假设起点：{inputs['planning_inputs']['actual_plan_start_date']}；计算末日：{capacity['finish_date']}。按源建议工时上限×8小时作为保守假设剩余工时，未减去21条部分PoC证据。工作日仅周一至周五，不宣称已包含法定节假日/请假；单主责任人资源串行，占位联合参与仍需补实际分工。\n\n"
    if plan["exceeds_source_target_month_under_assumptions"]:
        text += "**工期差异：**此占位方案超过源资料2027年6月建设末月，不能据此承诺按原周期交付。实际人员确认后应增加算法/后端投入、调整并行分工及里程碑；保留12模块/170任务，不能用删功能或改工时凑日期。GPU只模拟到位前置，未核实设备配额与占用时段，实际还需资源约束。\n\n"
    text += "| 占位ID | 暂定职责 | 每工作日假设有效小时 | 实际姓名/到岗 |\n| --- | --- | --- | --- |\n"
    for resource in resources.values():
        text += f"| {resource['resource_id']} | {resource['name']} | {resource['effective_hours_per_workday']} | 未确认 |\n"
    text += "\n资源到位假设：授权样本2026-11-02，GPU2026-11-16，仅用于排期模拟；真实数据卡和资源清单未据此填写到位事实。\n\n| 分期 | 任务数 | 假设开始 | 假设末日 |\n| --- | --- | --- | --- |\n"
    for m in milestones:
        text += f"| {m['batch']} | {m['tasks']} | {m['scenario_first_start']} | {m['scenario_last_finish']} |\n"
    text += "\n完整逐任务表见[占位排期CSV](../../tasks/execution-schedule-scenario.csv)，机器结果见[scenario.json](execution-schedule-scenario.json)，可调整[假设输入](execution-planning-scenario-inputs.json)。假设的人员工时/资源日期/分工改变后重新计算。实际信息确认后转入实际输入表，保留差异和复核；不直接把本方案字段批量标成真实。\n"
    stream = io.StringIO(newline="")
    fields = ["task_id", "name", "batch", "source_role", "scenario_resource_id", "scenario_resource_name", "assumed_remaining_effort_hours",
              "scenario_start_date", "scenario_finish_date", "assumed_external_release_date", "observed_verification_status"]
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(plan["records"])
    return {"docs/00-project/execution-schedule-scenario.json": json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            "docs/00-project/execution-schedule-scenario.md": text, "tasks/execution-schedule-scenario.csv": stream.getvalue()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    differences = []
    for path, content in outputs().items():
        target = ROOT / path
        if args.check:
            if not target.is_file() or target.read_bytes() != content.encode():
                differences.append(path)
        else:
            target.write_bytes(content.encode())
    print(json.dumps({"status": "FAIL" if differences else "PASS", "scenario_only": True, "actual_people_confirmed": False, "differences": differences}))
    return bool(differences)


if __name__ == "__main__":
    raise SystemExit(main())
