"""Derive shared remaining-work navigation from authoritative registers; never close a task."""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENTRAL = "docs/00-project/remaining-work-navigation.md"
MACHINE = "docs/00-project/remaining-work-navigation.json"
START = "<!-- phase-remaining-navigation:start -->"
END = "<!-- phase-remaining-navigation:end -->"
SOURCES = ["docs/00-project/phase-readiness-register.json",
           "docs/03-development/stage-two-completion-matrix.json",
           "docs/03-api/interface-gap-register.json",
           "docs/00-project/validation/resource-readiness-snapshot.json",
           "scripts/generate_remaining_work_navigation.py"]
ROLES = {
    "S1-N01": "文档/业务/技术复核", "S1-N02": "项目/业务/文档管理", "S1-N03": "业务/安全/架构",
    "S1-N04": "架构/前后端/算法/测试", "S1-N05": "业务验收/测试/算法/运维",
    "S1-N06": "数据/业务授权/算法", "S1-N07": "项目计划/各研发负责人",
    "S2-N01": "架构/前后端/算法/测试", "S2-N02": "数据库/后端/安全", "S2-N03": "后端/算法/测试",
    "S2-N04": "身份平台/业务安全/后端", "S2-N05": "Linux及Docker运维/资源管理",
    "S2-N06": "数据/算法/GPU运维", "S2-N07": "媒体/算法/后端/测试", "S2-N08": "检索/算法/后端/测试",
    "S2-N09": "业务审核/安全/后端/存储", "S2-N10": "运维/数据库/安全/测试",
    "S2-N11": "技术/软件准入/许可审查/安全", "S2-N12": "仓库管理/构建发布/安全",
}
PREREQUISITES = {
    "S1-N02": "正式依据版本与适用范围、V2文件名/V1.0正文身份处理依据、实际变更责任人。",
    "S1-N03": "本地来源确认的规则版本；14类参数的适用值/例外/依据，未确定的值保持UNCONFIRMED。",
    "S1-N04": "业务规则和来源授权、34能力输入/结果身份与公开投影、13项接口缺口的唯一契约。",
    "S1-N05": "24项指标的实际封存样本/分层数、正式目标、版本/资源/负载与执行人。",
    "S1-N06": "真实来源/用途依据、标签和质检版本、样本元信息、实际目录/数量及到位日。",
    "S1-N07": "实际人员/有效投入、剩余工时证据、工作日历/计划起点与数据/GPU到位日；占位10人不作实际输入。",
    "S2-N01": "13项缺口的设计输入、状态/版本/权限/异步终态规则；外部平台接口资料。",
    "S2-N02": "业务表范围与唯一SQL/字典、逐表案件/单位隔离分类、增量迁移及升级副本/恢复方案。",
    "S2-N03": "36候选DAG的实际节点/worker绑定、消息队列故障环境、取消/续租/死信处理与授权规则。",
    "S2-N04": "正式身份协议及issuer/验签材料、主体/单位/案件权威映射、功能矩阵与撤销时限。",
    "S2-N05": "Docker虚拟机数据盘的实际扩容或迁移目标、备份/恢复条件、资源配额、GPU权限和维护人。",
    "S2-N06": "用途授权数据目录、权重来源/许可/摘要、独立封存测试集、实际GPU及驱动。",
    "S2-N07": "实际授权多编码/VFR/缺模态/长视频素材、映射链路及OCR/ASR模型。",
    "S2-N08": "正式中文分词/排序选择与版本、实际索引规模、查询指标/负载及案件权限过滤。",
    "S2-N09": "双人审批适用规则、保留期、WORM/签名/可信时间、密钥与特权管理边界。",
    "S2-N10": "批准RPO/RTO、另一主机/异地位置、WAL归档、密钥恢复授权和索引重建方案。",
    "S2-N11": "生产Python/OS准入目标、FFmpeg等未托管二进制及源码notices、模型许可和漏洞扫描工具。",
    "S2-N12": "私有仓库治理功能与管理人、必须检查/评审规则、制品库/签名/离线依赖/保留策略。",
}


def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def link(target, path, label=None, anchor=""):
    relative = posixpath.relpath(path, posixpath.dirname(target) or ".")
    return f"[{label or path.rsplit('/', 1)[-1]}](<{relative}{anchor}>)"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def insert_block(original, block):
    if START in original:
        before, rest = original.split(START, 1)
        _, after = rest.split(END, 1)
        return before + block + after
    # Place it prominently before the first level-two heading.
    position = original.find("\n## ")
    if position < 0:
        return original.rstrip()+"\n\n"+block+"\n"
    return original[:position].rstrip()+"\n\n"+block+"\n"+original[position:]


def build():
    ledger = read(SOURCES[0])
    second = {item["id"]: item for item in read(SOURCES[1])["items"]}
    gaps = read(SOURCES[2])["items"]
    resource = read(SOURCES[3])
    items = []
    for original in ledger["items"]:
        item = dict(original)
        detailed = second.get(item["id"])
        if detailed:
            item["navigation_completed_part"] = detailed["completed_this_round"]
            item["navigation_remaining_work"] = detailed["remaining_actual_requirements"]
        else:
            item["navigation_completed_part"] = item["current_evidence"]
            item["navigation_remaining_work"] = item["remaining_work"]
        # The remaining source-identity input must be explicit after engineering controls exist.
        if item["id"] == "S1-N02":
            item["navigation_remaining_work"] = "确认正式权威版本、适用范围、V2/V1.0身份冲突处置及实际变更责任人；唯一工程来源规则已完成。"
        item["navigation_status"] = "记录范围内已完成" if item["completion_asserted"] else "待落实实际条件及对应交付"
        item["required_role"] = ROLES[item["id"]]
        item["prerequisites"] = PREREQUISITES.get(item["id"], "正式出版稿如修订，需另行全页交付核验。")
        assert all((ROOT/path).is_file() for path in item["evidence_refs"])
        items.append(item)
    remaining = [item for item in items if not item["completion_asserted"]]
    assert len(items) == 19 and len(remaining) == 18
    assert sum(item["stage"] == 1 for item in remaining) == 6
    assert sum(item["stage"] == 2 for item in remaining) == 12
    assert len(gaps) == 13 and all(gap["candidate_routes_callable"] is (gap["id"] == "IF-G01") for gap in gaps)
    volume = resource["development_postgres_volume_filesystem"]
    attribution = (f"容量问题位于Linux服务器172.16.58.179的Docker Desktop虚拟机内，"
                   f"为PostgreSQL研发数据卷所在文件系统。仓库快照时点`{resource['observed_at']}`："
                   f"df使用率{volume['used_percent_observed']}，可用约{volume['available_bytes']/1024**3:.2f} GiB。"
                   "不是本地Windows D盘或GitHub容量，也不代表Linux宿主/workspace全部空间不足；尚未记录扩容完成。")
    machine = {"revision": "phase-remaining-navigation-20261013", "scope": "derived_navigation_only_no_task_or_approval_changes",
               "authoritative_register": SOURCES[0], "source_hashes": {
                   path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in SOURCES},
               "stage_one_steps": 24, "stage_two_steps": 23, "business_tasks_preserved": 170,
               "audited_items": 19, "remaining_non_signature_items": 18,
               "stage_one_remaining": 6, "stage_two_remaining": 12,
               "interface_gaps": 13, "interface_gaps_overlap_stage_items": True,
               "formal_stage_one_frozen": False, "formal_stage_two_frozen": False,
               "resource_attribution": attribution, "items": items,
               "formal_freeze_conditions": [
                   {"stage": 1, "steps": [22, 23, 24], "status": "NOT_FROZEN", "actual_signatories": None,
                    "requirements": "落实实际输入和适用决定，33项问题形成有效处置记录、实际责任人、范围/例外；引用候选摘要后冻结。"},
                   {"stage": 2, "steps": [22, 23], "status": "NOT_FROZEN", "actual_signatories": None,
                    "requirements": "技术评审明确适用环境/版本/遗留处理，附实际资源与代表性证据；按有效决定冻结，正式基线标签须有批准依据。"}]}

    def table(target, stage):
        text = "| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |\n| --- | --- | --- | --- |\n"
        for item in remaining:
            if item["stage"] != stage:
                continue
            identity = f"{item['id']} / {item['priority']}<br>步" + ",".join(map(str, item["original_stage_steps"]))
            identity += "<br>"+item["required_role"]+"（实际姓名待定）"
            details = link(target, CENTRAL, "前置条件、全部证据及关闭标准", "#"+item["id"].lower())
            evidence = "、".join(link(target, path) for path in item["evidence_refs"][:2])
            text += f"| {cell(identity)} | {cell(item['title'])}<br>{cell(item['navigation_status'])} | {cell(item['navigation_remaining_work'])} | {details}<br>{evidence} |\n"
        return text

    intro = ("第一阶段24步、第二阶段23步与170业务任务分别管理。核查19项工作：版式核验在记录范围内已完成；"
             "剩余18项，包括第一阶段6项、第二阶段12项。工程补充、实际输入、实现/联调、正式验收与冻结分别判断。"
             "13接口缺口与这些事项交叉，不能相加计算完成率。真实人员/责任人未确认，10人占位排期只作假设。\n\n")
    central = "# 第一、第二阶段剩余工作总导航\n\n"+intro+attribution+"\n\n"
    central += "机器阅读见"+link(CENTRAL, MACHINE)+"；工作状态唯一源为"+link(CENTRAL, SOURCES[0])+"，本文不修改状态或授予权限。\n\n"
    for stage in [1, 2]:
        central += f"## 第{stage}阶段剩余工作\n\n"+table(CENTRAL, stage)+"\n"
    central += "## 逐项要求与证据\n\n"
    for item in items:
        central += f"## {item['id']}\n\n**{item['title']}**。原阶段{item['stage']}，步骤"+",".join(map(str, item["original_stage_steps"]))+f"，优先级{item['priority']}。\n\n"
        central += f"当前状态：{item['navigation_status']}。所需责任角色：{item['required_role']}，实际姓名未确认。\n\n"
        central += "已有完成范围："+item["navigation_completed_part"]+"\n\n"
        central += "仍需完成："+item["navigation_remaining_work"]+"\n\n"
        central += "执行前置："+item["prerequisites"]+"\n\n"
        central += "关闭标准："+item["closure_criteria"]+"\n\n"
        central += "阶段边界："+item["phase_boundary"]+"\n\n"
        central += "文档/证据："+"、".join(link(CENTRAL, path) for path in item["evidence_refs"])+"。\n\n"
    central += "## 13项接口缺口的入口\n\n正式条件仍保持开放；IF-G01新增GET已进入唯一契约并实际实现，IF-G01/09首批技术范围见"+link(CENTRAL,"docs/03-development/stage-three/business-foundation-implementation.md","实际实现说明")+"。其余候选新增路径仍不可调用，来源为唯一"+link(CENTRAL, "docs/03-api/openapi.yaml", "业务OpenAPI")+"及相关Schema。\n\n"
    central += "| 编号/工作 | 仍需工作 | 关闭标准/计划任务 |\n| --- | --- | --- |\n"
    for gap in gaps:
        central += f"| {gap['id']} {cell(gap['title'])} | {cell(gap['proposed_detail'])} | {cell(gap['closure_criteria'])}<br>"+",".join(gap["task_ids"])+" |\n"
    central += "\n完整来源与候选路径见"+link(CENTRAL, SOURCES[2])+"和"+link(CENTRAL, "docs/03-api/interface-gap-register.md")+"。\n\n"
    central += "## 正式评审与冻结条件\n\n冻结事项单列，未重复计入18项非签字工作；审批不能代替真实输入或运行证据。\n\n"
    for freeze in machine["formal_freeze_conditions"]:
        central += f"- 第一阶段22—24步：{freeze['requirements']}\n" if freeze["stage"] == 1 else f"- 第二阶段22—23步：{freeze['requirements']}\n"
    central += "\n填写入口："+"、".join(link(CENTRAL, path) for path in ["docs/00-project/stage-one/review-resolution-inputs.json", "docs/00-project/review-decisions.yaml", "docs/00-project/freeze-checklist.md", "docs/00-project/review-package/technical-baseline-review.md"])+"。没有正式决定时两阶段均NOT_FROZEN。\n\n"
    central += "## 实际输入、实施与同步\n\n"
    central += "实际人员/日历填写"+link(CENTRAL, "docs/00-project/execution-planning-inputs.json")+"；数据填写"+link(CENTRAL, "docs/07-datasets/actual-input-inventory.json")+"及15数据卡；指标填写"+link(CENTRAL, "docs/09-testing/acceptance-execution-inputs.json")+"；第二阶段资源/平台填写"+link(CENTRAL, "docs/03-development/stage-two-external-inputs.json")+"。\n\n"
    central += "后续业务/生产按"+link(CENTRAL, "docs/03-development/stage-two-implementation-plan.md", "实施计划")+"和"+link(CENTRAL, "tasks/README.md", "170任务卡")+"推进；完整62表、DAG和业务模型不是本次导航更新的完成事项。\n\n"
    central += "本地、GitHub、Linux仓库读取同一套相对链接。GitHub仓库为[media-traceability-system](https://github.com/xuchangsheng18/media-traceability-system)，服务器仓库为`/workspace/glwy/projects/media-traceability-system`。实际同步看"+link(CENTRAL, "docs/00-project/server-sync-receipt.json")+"，CI看"+link(CENTRAL, "docs/00-project/validation/github-actions-report.json")+"。\n\n"
    central += "维护时编辑唯一台账/专项来源，再运行`python scripts/update_docs_navigation.py`生成；`python scripts/generate_remaining_work_navigation.py --check`核验派生内容。更新导航不会自动关闭任务。\n"
    output = {CENTRAL: central, MACHINE: json.dumps(machine, ensure_ascii=False, indent=2)+"\n"}
    for target in ["README.md", "docs/README.md", "docs/00-project/README.md",
                   "docs/00-project/stage-one/README.md", "docs/03-development/README.md"]:
        original = (ROOT/target).read_text(encoding="utf-8")
        block = START+"\n## 第一、第二阶段剩余工作总导航\n\n"+intro+attribution+"\n\n"
        block += "完整逐项导航："+link(target, CENTRAL, "剩余任务、前置条件、关闭标准及13接口缺口")+"；"+link(target, MACHINE, "同源机器索引")+"。\n\n"
        for stage in [1, 2]:
            block += f"### 第{stage}阶段\n\n"+table(target, stage)+"\n"
        block += "已完成的S1-N01版式核验及19项全部已有证据在总导航保留，避免重新列为未开展。正式输入冻结（第一阶段22—24步）和技术冻结（第二阶段22—23步）仍NOT_FROZEN，实际决定/责任人及适用范围需落实。\n\n"
        block += "资源/身份/授权数据和实际责任人填写"+link(target, "docs/03-development/stage-two-external-inputs.json", "实际输入表")+"；人员/实际排期填写"+link(target, "docs/00-project/execution-planning-inputs.json", "人员排期输入")+"。170业务任务后续按"+link(target, "docs/03-development/stage-two-implementation-plan.md", "实施计划")+"推进。\n"+END
        output[target] = insert_block(original, block)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    differences = []
    for path, content in outputs.items():
        destination = ROOT/path
        if args.check:
            if not destination.exists() or destination.read_bytes() != content.encode("utf-8"):
                differences.append(path)
        else:
            destination.write_bytes(content.encode("utf-8"))
    print(json.dumps({"status": "FAIL" if differences else "PASS", "derived_files": len(outputs),
                      "remaining_stage_one": 6, "remaining_stage_two": 12, "differences": differences}))
    return bool(differences)


if __name__ == "__main__":
    raise SystemExit(main())
