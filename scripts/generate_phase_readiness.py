"""Generate phase-gap reading views and candidate requirement-processing lineage."""
import argparse
import json

from generate_interface_docs import ROOT, digest, escaped, jdump, read

PREFIX = "docs/00-project/"


def outputs():
    trace_path = PREFIX + "requirement-traceability.yaml"
    trace = read(trace_path)["requirements"]
    tasks = {t["id"]: t for t in read("tasks/backlog.yaml")["tasks"]}
    models = {m["id"]: m for m in read("docs/06-algorithms/model-catalog.yaml")["models"]}
    proposals = read(PREFIX + "requirement-flow-proposals.json")
    records = []
    for index, requirement in enumerate(trace):
        if requirement["type"] != "functional":
            continue
        rid = requirement["requirement_id"]
        module = rid.split("-")[1]
        proposal = dict(proposals["modules"][module])
        proposal.update(proposals["overrides"].get(rid, {}))
        contracts = []
        for model_id in requirement["model_ids"]:
            model = models[model_id]
            contracts.append({"model_id": model_id, "capability": model["capability"],
                              "input_kind": model["input_kind"], "output_kind": model["output_kind"],
                              "request_schema": f"schemas/model/{model_id}.request.schema.json",
                              "response_schema": f"schemas/model/{model_id}.response.schema.json"})
        records.append({"requirement_id": rid, "name": requirement["name"], "module": module,
                        "source_pointer": f"/requirements/{index}",
                        "declared_task_ids": requirement["task_ids"], "declared_operation_ids": requirement["operation_ids"],
                        "declared_model_ids": requirement["model_ids"], "declared_dataset_ids": requirement["dataset_ids"],
                        "declared_table_names": requirement["table_names"], "declared_test_ids": requirement["test_ids"],
                        "task_card_refs": [tasks[t]["doc_file"] for t in requirement["task_ids"]],
                        "internal_contract_refs": contracts,
                        "candidate_entry_operations": proposal["entry_operations"],
                        "candidate_result_operations": proposal["result_operations"],
                        "processing_and_reading_note": proposal["note"], "interface_gap_ids": proposal["interface_gap_ids"],
                        "binding_status": "CANDIDATE_FLOW_REQUIRES_SEMANTIC_REVIEW",
                        "new_HTTP_paths_created": False, "full_business_implementation_asserted": False,
                        "formal_approved": False})
    source_paths = [trace_path, "tasks/backlog.yaml", "docs/06-algorithms/model-catalog.yaml",
                    "docs/03-api/operation-index.json", "docs/03-api/interface-gap-register.json",
                    PREFIX + "requirement-flow-proposals.json", "scripts/generate_phase_readiness.py"]
    model_schema_paths = sorted({c[k] for r in records for c in r["internal_contract_refs"] for k in ["request_schema", "response_schema"]})
    source_paths.extend(model_schema_paths)
    mapping = {"revision": "phase-readiness-20261013", "source_hashes": {p: digest(p) for p in source_paths},
               "scope": "36_business_requirements_exact_declared_refs_plus_candidate_processing_reading_routes",
               "business_requirements": len(records), "direct_API_unbound_requirements": [r["requirement_id"] for r in records if not r["declared_operation_ids"]],
               "formal_frozen": False, "records": records}
    mapping_text = "# 业务需求、内部处理与结果读取对应\n\n"
    mapping_text += "36条业务需求的主来源、任务/模型/表/测试引用保持原值。入口与结果读取是独立标记的候选设计，未更改主追踪、接口结构、任务状态或批准；源操作未直接绑定不等于内部计算需求丢失。机器记录见[requirement-processing-map.json](requirement-processing-map.json)。\n\n"
    mapping_text += "对七条无直接operation_ids的需求，已补内部任务/Schema与候选读取说明；节点调度、持久化对象身份和完整结果返回仍需语义设计/实现，不将本文作为完整DAG或新增可调用路径。\n\n"
    for item in records:
        mapping_text += f"## {item['requirement_id']} {item['name']}\n\n源位置：`{trace_path}{item['source_pointer']}`。\n\n"
        mapping_text += "主追踪已有API：" + (", ".join(item["declared_operation_ids"]) or "未直接绑定") + "；任务：" + ", ".join(item["declared_task_ids"]) + "。\n\n"
        mapping_text += "来源任务卡：" + "、".join(f"[{p.rsplit('/',1)[-1]}](../../{p})" for p in item["task_card_refs"]) + "。\n\n"
        mapping_text += "候选流程入口：" + (", ".join(item["candidate_entry_operations"]) or "按离线/私有处理任务继续设计") + "；候选结果读取：" + (", ".join(item["candidate_result_operations"]) or "当前尚无完整读取契约") + "。\n\n"
        mapping_text += item["processing_and_reading_note"] + "\n\n"
        if item["internal_contract_refs"]:
            mapping_text += "| 来源能力 | 输入/输出路径 | 结构源 |\n| --- | --- | --- |\n"
            for capability in item["internal_contract_refs"]:
                mapping_text += f"| {capability['model_id']} {capability['capability']} | {capability['input_kind']} / {capability['output_kind']} | [请求](../../{capability['request_schema']})、[响应](../../{capability['response_schema']}) |\n"
            mapping_text += "\n"
        else:
            mapping_text += "主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。\n\n"
        mapping_text += "候选表：" + (", ".join(item["declared_table_names"]) or "无") + "；计划测试：" + ", ".join(item["declared_test_ids"]) + "。\n\n"
        mapping_text += "关联接口缺口：" + (", ".join(item["interface_gap_ids"]) or "按相关任务的完整语义和验收条件核验") + "；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。\n\n"
    ledger = read(PREFIX + "phase-readiness-register.json")
    resource = read(PREFIX + "validation/resource-readiness-snapshot.json")
    governance = read(PREFIX + "validation/repository-governance-snapshot.json")
    text = "# 第一、第二阶段：审批之外的未完成工作\n\n"
    text += "2026-10-13。第一阶段为开发输入整理，第二阶段为技术基线/代表性最小验证；170业务研发任务另按交付计划实施。当前原件/导航/结构、CPU最小工程与CI已有证据，仍存在资料核验、规则参数、契约/技术实现和真实资源缺口。正式签认不能代替这些工作。机器清单见[phase-readiness-register.json](phase-readiness-register.json)。\n\n"
    text += "## 读表范围\n\n每项区分“本阶段需要明确的输入/设计/验证”和“后续对应功能启用或生产前的实现”。不能把全部业务研发强行计入第二阶段，也不能用PoC通过把后续工作标完成。审批签字本身未计为下表独立完成项；有外部材料/规则依赖的项仍需输入，不能自动关闭。\n\n"
    for stage in [1, 2]:
        text += f"## 第{stage}阶段\n\n| 编号/优先级 | 工作与当前范围 | 仍需完善 | 关闭标准与阶段边界 |\n| --- | --- | --- | --- |\n"
        for item in ledger["items"]:
            if item["stage"] != stage:
                continue
            refs = "、".join(f"[{p.rsplit('/',1)[-1]}](../../{p})" for p in item["evidence_refs"])
            text += f"| {item['id']} / {item['priority']} | {escaped(item['title'])}；{escaped(item['current_evidence'])}<br>{refs} | {escaped(item['remaining_work'])} | {escaped(item['closure_criteria'])}<br>{escaped(item['phase_boundary'])} |\n"
        text += "\n"
    text += "## 本轮可直接完成的资料补充\n\n已新增[36需求→内部处理→结果读取映射](requirement-processing-map.md)，准确保留来源引用并补七条未直接绑API需求的候选流程；它是可评审材料，语义/运行验证仍开放。已新增本清单并接入两阶段导航、来源及机械校验，没有改写正式决定或任务完成状态。\n\n"
    volume = resource["development_postgres_volume_filesystem"]
    text += f"资源只读观测时间：`{resource['observed_at']}`；研发PostgreSQL卷所在文件系统可用约 **{volume['available_bytes']/1024**3:.2f} GiB**，df使用率 **{volume['used_percent_observed']}**。宿主机剩余空间不能直接当该卷可用空间，也不代表项目独占配额。GPU工具可用性={resource['gpu']['tool_available']}，没有据工具不可用宣称GPU不存在。详见[时点快照](validation/resource-readiness-snapshot.json)。\n\n"
    text += f"仓库治理观测时间：`{governance['observed_at']}`；GitHub报告main protected={governance['branch']['protected_reported_by_provider']}；rulesets查询结果为 `{governance['rulesets']['query']}`，不可据不可查询认定规则集为空。Actions已启用不等于组织治理闭合。详见[治理快照](validation/repository-governance-snapshot.json)，本轮没有修改设置。\n\n"
    text += "## 建议推进顺序\n\n1. 落实当前数据卷容量和项目资源范围，形成实际可执行的存储计划。\n2. 补需求/内部处理/结果对象身份的语义闭环，以及13项接口缺口的关键契约。\n3. 明确规则/指标/数据计数、负责人投入和分期范围，形成可执行的验证方案。\n4. 按选定代表性功能进行任务编排、授权、模型/媒体/查询验证；其余功能按后续任务交付。\n5. 进入正式环境前落实版本迁移、完整安全/备份/制品/治理与正式场景/容量验证，再办理适用冻结。\n\n"
    text += "当前py310研发指令保持；Python3.10维护状态参见[官方维护表](https://devguide.python.org/versions/)，生产目标与迁移验证仍需落实。旧原件/历史报告按其时点保存，不从新快照倒改历史。\n"
    return {PREFIX + "requirement-processing-map.json": jdump(mapping) + "\n",
            PREFIX + "requirement-processing-map.md": mapping_text,
            PREFIX + "phase-readiness-register.md": text}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = outputs()
    differences = []
    for path, content in result.items():
        file = ROOT / path
        if args.check:
            if not file.exists() or file.read_bytes() != content.encode():
                differences.append(path)
        else:
            file.write_bytes(content.encode())
    print(json.dumps({"status": "FAIL" if differences else "PASS", "derived_files": len(result), "differences": differences}))
    return bool(differences)


if __name__ == "__main__":
    raise SystemExit(main())
