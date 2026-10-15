"""Render 24-step artifact status and second-stage API/database navigation from existing sources."""
import argparse
import json
import posixpath
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST = "docs/00-project/stage-one/steps-and-deliverables.md"
SECOND = "docs/02-architecture/technical-baseline.md"
START = "<!-- phase-contract-file-navigation:start -->"
END = "<!-- phase-contract-file-navigation:end -->"
SOURCE = "docs/00-project/stage-one/deliverables.json"
LEDGER = "docs/00-project/phase-readiness-register.json"
STATUSES = {
    "CANDIDATE_RECORDED": "资料已整理登记；正式适用条件待确认",
    "CANDIDATE_STRUCTURE_VALIDATED": "候选结构已校验；业务实现/验收另判",
    "TEXT_AND_VISUAL_REVIEW_COMPLETED_WITH_RECORDED_SCOPE": "文字与图表核验在记录范围内完成",
    "CANDIDATE_STRUCTURE_AND_ISOLATED_SQL_VALIDATED": "候选结构及隔离SQL已验证；正式部署另判",
    "STRUCTURE_VALIDATED_WITH_FORMAL_GAPS": "一致性结构检查通过；正式条件仍有缺口",
    "33_QUESTIONS_IN_7_DETAILED_REVIEW_PACKETS": "33问题/7类评审包已形成；实际决定待提供",
    "EXISTING_SELECTIONS_APPLIED_FORMAL_REVIEW_PENDING": "已有授权选择已同步；正式评审待完成",
    "NOT_FROZEN": "正式输入基线未冻结",
}
INTERFACES = [
    ("剩余接口实际实现", "docs/03-development/stage-three/remaining-interface-implementation.md", "11类缺口实际子范围", "审批/复核/审计/配置及适配、任务控制和内部协议的真实代码、验证与正式接入边界。"),
    ("整体接口范围", "docs/03-api/system-interface-specification.md", "系统整体接口说明", "七类接口面、73业务操作/102组件/34能力、服务边界和完整性要求。"),
    ("逐操作/模块目录", "docs/03-api/detailed-interface-index.md", "73操作与12模块导航", "跳转每个操作的参数、请求/响应、权限、版本、异步终态、样例和任务引用。"),
    ("业务结构唯一源", "docs/03-api/openapi.yaml", "业务OpenAPI", "外部接口结构源；候选73操作，不代表全部已实现。"),
    ("内部调用入口唯一源", "docs/03-api/inference-openapi.yaml", "内部推理OpenAPI", "内部调用入口；能力请求/响应结构以schemas/model为源。"),
    ("业务字段说明", "docs/03-api/data-structures.md", "102组件字段说明", "必填/可空/枚举/约束及完整Schema的只读派生。"),
    ("内部能力字段", "docs/03-api/inference-interfaces.md", "34能力接口说明", "能力路径/请求/响应/身份/来源摘要；业务模型未据此验收。"),
    ("能力Schema源", "schemas/model/", "68模型Schema", "34请求+34响应的唯一能力结构来源；不作为业务HTTP的第二结构源。"),
    ("共用行为", "docs/03-api/common-interface-rules.md", "接口共用规则", "鉴权、追踪、分页、幂等、ETag、版本、异步、错误及Range。"),
    ("服务与事件", "docs/03-api/service-and-event-contracts.md", "服务/事件契约", "边界及研发事件；完整业务调度实施另判。"),
    ("工作流/结果事件", "docs/05-workflows/workflow-contracts.md", "工作流契约", "候选DAG、节点结果、7类域事件和运行版本身份。"),
    ("严格历史读取", "docs/03-api/historical-result-reading.md", "历史结果读取", "7现有操作的精确task/run/result选择与不回退最新规则，所选历史读取已实测；完整业务生产器及正式接入另判。"),
    ("接口缺口", "docs/03-api/interface-gap-register.md", "13项接口缺口", "正式条件与技术子范围分别登记；已挂载路径按逐操作实测，其余候选路径不可调用。"),
    ("接口追踪", "docs/03-api/interface-catalog.json", "接口来源索引", "操作/模块/能力的来源和任务/测试引用，非运行证明。"),
    ("样例", "docs/03-api/examples/", "请求响应样例", "结构校验夹具，不能充当实际业务结果。"),
    ("生成类型", "shared-contracts/generated/", "4份生成类型", "由唯一来源生成，禁止反向手改Schema；结构约束仍需运行验证。"),
    ("已运行研发API", "docs/03-api/poc-api.md", "PoC接口及范围", "固定测试案件/图片上传/任务/合成CPU入口，与73操作设计分开。"),
]
DATABASES = [
    ("业务设计与关系", "docs/04-database/database-design.md", "数据库设计", "62表候选职责、身份与关系，业务访问层尚未全部实施。"),
    ("业务字段字典", "docs/04-database/data-dictionary.md", "62表/825字段字典", "逐字段类型、空值、约束和来源；不从一句来源契约推导已确认业务规则。"),
    ("空库DDL唯一源", "docs/04-database/initial-schema.sql", "初始化SQL", "用于新隔离空库；不得当既有数据库增量升级脚本。"),
    ("ER关系", "docs/04-database/er-diagram.md", "ER图", "结合复合外键、案件范围及设计阅读；关系图不是部署证明。"),
    ("表/字段机器目录", "docs/04-database/table-catalog.json", "表目录", "62表825字段的可检查结构，须与SQL/字典一致。"),
    ("逐字段来源", "docs/04-database/field-provenance.json", "字段来源契约", "精确源文件/指针与来源性质；说明cluster_id、asset_id、rank等依据。"),
    ("接口字段投影", "docs/04-database/api-field-mapping.md", "接口—数据库映射说明", "区分请求/响应、列投影和运行时组合，不以同名认定同一对象。"),
    ("映射机器源", "docs/04-database/api-field-mapping.json", "接口字段映射JSON", "配合CSV查看精确结构引用和列/投影关系。"),
    ("映射表格", "docs/04-database/api-field-mapping.csv", "接口字段映射CSV", "便于逐字段对照；同步JSON/SQL/Schema，不能独立成为第二定义源。"),
    ("表与任务", "docs/04-database/table-task-usage.md", "62表任务引用", "候选职责、源追踪与任务卡引用；不代表已被实际代码使用。"),
    ("首发排序规则", "docs/04-database/first-source-ranking.md", "首发候选排序", "cluster/asset关系、1—3名次、去重、并列/未知和观察范围。"),
    ("数据库检查", "docs/04-database/database-validation.md", "SQL验证范围与命令", "空库/约束/反例测试，不当所有业务访问层或生产升级通过。"),
    ("实际研发库", "docs/04-database/poc-database.md", "研发5表说明", "实际PoC assets/jobs/outbox/audit/迁移账本，区别于62表业务设计。"),
    ("已运行研发迁移", "backend/migrations/", "PoC版本迁移", "0001/0002仅针对开发库；正式62表迁移仍需按任务实施。"),
    ("迁移/事件机制", "docs/03-development/migrations-and-events.md", "迁移与旧租约保护", "版本账本、摘要、事件/追踪与租约fencing；非生产RLS完整部署。"),
    ("隔离权限原型", "docs/04-database/authorization-isolation-prototype.md", "RLS/历史追加原型", "代表性临时库验证；正式身份、全业务表和特权防篡改未因此完成。"),
]


def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def link(target, path, label=None):
    relative = posixpath.relpath(path, posixpath.dirname(target))
    return f"[{label or path.rstrip('/').rsplit('/', 1)[-1]}](<{relative}>)"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def entry_section(target, source, heading="##"):
    entry = source["development_entry"]
    assert entry["foundation_development_can_start"] is True
    assert entry["full_stage_technical_completion"] is False and entry["formal_freeze_or_production_admission_asserted"] is False
    text = f"{heading} 技术完成程度与开发准入\n\n"
    text += "用于启动基础开发的工程输入和代表性最小工程已经具备，但两阶段整体技术闭环仍未完成。可以按具体任务子范围进入基础开发；正式身份/数据/GPU/全业务实现及生产准入按所需条件继续。\n\n"
    text += "已具备的技术范围：\n\n"+"\n".join("- "+value for value in entry["completed_technical_scope"])+"\n\n"
    text += "现在可推进：\n\n"+"\n".join("- "+value for value in entry["start_now"])+"\n\n"
    text += "| 开发范围/门槛 | 当前判断 | 执行条件 |\n| --- | --- | --- |\n"
    for gate in entry["gates"]:
        refs = "、".join(link(target, path) for path in gate.get("evidence_refs", []))
        text += f"| {gate['id']} | {gate['state']} | {cell(gate['requirement'])}"+("<br>"+refs if refs else "")+" |\n"
    text += "\n每个任务开始前检查：\n\n"+"\n".join("- "+value for value in entry["required_per_task_checks"])+"\n\n"
    text += "现有输入对开发的帮助：统一"+link(target, "docs/03-api/openapi.yaml", "接口结构")+"、"+link(target, "docs/04-database/field-provenance.json", "字段来源")+"和"+link(target, "docs/04-database/api-field-mapping.json", "持久化投影")+"；用"+link(target, "tasks/README.md", "任务卡")+"明确输入/依赖/子范围，用生成类型与CI发现漂移。它们减少重复定义和字段/版本错配，不替代真实业务规则或数据授权。\n\n"
    return text


def build():
    source, ledger = read(SOURCE), read(LEDGER)
    assert len(source["steps"]) == source["steps_count"] == 24
    assert [item["step"] for item in source["steps"]] == list(range(1, 25))
    records = []
    for index, step in enumerate(source["steps"]):
        assert step["artifact_status"] in STATUSES
        assert all((ROOT/path).exists() for path in step["outputs"])
        assert step["formal_completion_asserted"] is False and step["owner_name"] is None
        related = [item for item in ledger["items"] if item["stage"] == 1 and step["step"] in item["original_stage_steps"]]
        records.append({"step": step["step"], "title": step["title"], "source_pointer": f"/steps/{index}",
                        "artifact_status": step["artifact_status"], "technical_status_cn": STATUSES[step["artifact_status"]],
                        "completed_material_work": step["operation"], "outputs": step["outputs"], "output_paths_available": True,
                        "remaining_or_scope_note": step["remaining"], "related_remaining_item_ids": [item["id"] for item in related if not item["completion_asserted"]],
                        "formal_completion_asserted": False, "actual_owner": None, "full_business_implementation_asserted": False})
    first = "# 第一阶段24步：实际状态、操作与交付\n\n"
    first += "2026-10-13更新。已补齐的状态直接并入本对应表，不另建展示页。每一步按现有产物台账和证据说明技术状态、待完成事项与正式状态。状态唯一源为"+link(FIRST, SOURCE)+"。原手册标题/步骤保留，第一阶段正式输入基线仍NOT_FROZEN。\n\n"
    first += "## 状态判定\n\n“资料已整理登记”表示候选文档/配置已形成；“结构已校验”表示相应材料检查通过；图表/隔离SQL仅按已记录范围判定。第22步评审包已形成，第23步仅应用已有授权选择，第24步正式冻结未完成。实际责任人和正式业务决定尚未提供。\n\n"
    first += entry_section(FIRST, source)
    first += "## 24步逐项实际状态\n\n| 步骤/工作 | 已完成材料工作及技术状态 | 尚需完成/适用边界 | 实际文件与证据 | 正式状态 |\n| --- | --- | --- | --- | --- |\n"
    for item in records:
        refs = "、".join(link(FIRST, path) for path in item["outputs"])
        remaining = cell(item["remaining_or_scope_note"])
        if item["related_remaining_item_ids"]:
            remaining += "<br>关联未闭合事项："+",".join(item["related_remaining_item_ids"])
        first += f"| {item['step']} {cell(item['title'])} | {cell(item['technical_status_cn'])}<br>{cell(item['completed_material_work'])}<br>源状态：{item['artifact_status']} | {remaining} | {refs} | 未宣称正式完成；实际负责人待定 |\n"
    first += "\n原来源标题、操作和实际产物均保留在本表；实际缺项/前置/关闭标准见"+link(FIRST, "docs/00-project/remaining-work-navigation.md", "两阶段剩余工作总导航")+"。\n\n"
    first += "技术证据见"+"、".join(link(FIRST, path) for path in ["docs/00-project/validation/stage-one-validation-report.json", "docs/00-project/stage-one/visual-layout-audit.md", "docs/00-project/requirement-semantic-review.md", "docs/00-project/validation/stage-one-controls-report.json", "docs/00-project/validation/stage-one-input-preflight-report.json"])+"；未知真实输入仍保持待定。24步不是170业务任务的完成率，资料冻结与后续业务实现分别判断。\n"
    second = "## 接口与数据库文件导航\n\n"
    second += "2026-10-13。该页承接第二阶段第7步（数据库）、第19步（接口/事件）和第20步（最小工程）。整体接口/62表业务设计与已运行PoC/5表分别导航；不从设计文件推导正式部署。\n\n"
    second += entry_section(SECOND, read("docs/03-development/stage-two-deliverables.json"), "###")
    second += "### 阅读顺序\n\n1. 整体接口说明→逐操作目录→OpenAPI/模型Schema→字段与权限/版本/事件规则。\n2. 数据库设计→ER→字典/SQL→逐字段来源→接口映射→任务引用/校验。\n3. 实际PoC API/5表与迁移→相应运行证据，再核对13接口缺口和后续业务迁移/RLS。\n\n"
    for title, entries in [("整体接口及契约文件", INTERFACES), ("业务数据库及研发迁移文件", DATABASES)]:
        second += f"### {title}\n\n| 内容 | 文件入口 | 含义和使用要求 |\n| --- | --- | --- |\n"
        for category, path, label, meaning in entries:
            assert (ROOT/path).exists(), path
            second += f"| {category} | {link(SECOND, path, label)} | {cell(meaning)} |\n"
        second += "\n"
    second += "### 相互对应与实际状态\n\n"
    second += "API字段须按"+link(SECOND, "docs/04-database/api-field-mapping.json", "字段投影")+"定位数据库列/运行组合，再用"+link(SECOND, "docs/04-database/field-provenance.json", "字段来源")+"核对来源文件/指针；模型结构不与业务HTTP结构混为一份。SQL/字典/Schema/映射/生成类型变化须同步。\n\n"
    second += "cluster_id、asset_id、rank等字段的来源契约是逐字段可追踪的结构/设计依据，不能靠“见来源契约”一句作为实际约束说明。请联合阅读字典、field-provenance、映射和首发排序规范。\n\n"
    second += "73业务操作/102组件/34能力、62表825字段是当前候选设计；PoC和代表性隔离实验有独立证据，完整业务API/62表访问迁移/RLS未全部实现。13项正式条件仍开放；新增业务接口/约束迁移的实际子范围见剩余接口实现说明，初始化SQL不得直接作用于既有库。状态见"+link(SECOND, "docs/03-development/stage-two-readiness.md", "第二阶段23步实际状态")+"、"+link(SECOND, "docs/03-development/stage-two-completion-matrix.md", "12项补齐与剩余")+"和"+link(SECOND, "docs/00-project/remaining-work-navigation.md", "两阶段总导航")+"。\n\n"
    second += "证据："+"、".join(link(SECOND, path) for path in ["docs/00-project/validation/interface-documentation-report.json", "docs/00-project/validation/database-contract-report.json", "docs/00-project/validation/database-foundation-report.json", "docs/00-project/validation/migration-fencing-report.json", "docs/00-project/validation/stage-two-isolation-report.json"])+"。检查通过范围与实际业务验收分别判断。\n"
    original = (ROOT/SECOND).read_text(encoding="utf-8")
    block = START+"\n"+second.rstrip()+"\n"+END
    if START in original:
        before, rest = original.split(START, 1)
        _, after = rest.split(END, 1)
        integrated = before+block+after
    else:
        integrated = original.rstrip()+"\n\n"+block+"\n"
    return {FIRST: first, SECOND: integrated}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    differences = []
    outputs = build()
    for path, content in outputs.items():
        file = ROOT/path
        if args.check:
            if not file.exists() or file.read_bytes() != content.encode("utf-8"):
                differences.append(path)
        else:
            file.write_bytes(content.encode("utf-8"))
    print(json.dumps({"status": "FAIL" if differences else "PASS", "derived_files": len(outputs),
                      "first_stage_steps": 24, "interface_navigation_entries": len(INTERFACES),
                      "database_navigation_entries": len(DATABASES), "differences": differences}))
    return bool(differences)


if __name__ == "__main__":
    raise SystemExit(main())
