"""Generate read-only detailed API documentation from authoritative contracts."""
import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = "docs/03-api/"
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
MODULES = ["INGEST", "RESOURCE", "MEDIA", "RISK", "FORENSIC", "IMGRET", "VIDTRACE", "ORIGIN", "PROPAGATION", "CLAIM", "REVIEW", "OPS"]
NAMES = dict(zip(MODULES, ["数据接入", "资源库", "媒体预处理", "风险识别", "篡改取证", "图片检索", "视频溯源", "首发分析", "传播分析", "证据核查", "人工审核与报告", "系统运维"]))


@lru_cache(maxsize=256)
def read(path):
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def escaped(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def jdump(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def source_note(path):
    return f"自动派生，禁止独立修改结构；权威源 `{path}`，SHA-256 `{digest(path)}`。契约未冻结，文档存在不代表接口已实现。\n\n"


def describe(schema):
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    parts = [str(schema["type"])] if "type" in schema else []
    for key in ["format", "const", "enum", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minLength", "maxLength", "pattern", "minItems", "maxItems", "uniqueItems", "default", "readOnly", "writeOnly", "additionalProperties"]:
        if key in schema:
            parts.append(key + "=" + json.dumps(schema[key], ensure_ascii=False))
    for key in ["oneOf", "anyOf", "allOf"]:
        if key in schema:
            parts.append(key + "(" + "; ".join(describe(v) for v in schema[key]) + ")")
    if "items" in schema:
        parts.append("items=" + describe(schema["items"]))
    return "; ".join(parts) or "见完整Schema"


def fields(schema, prefix="", required_parent=True):
    rows = []
    for name, value in schema.get("properties", {}).items():
        path = prefix + name
        required = name in schema.get("required", [])
        rows.append((path, ("必须" if required else "可省略") + ("（父对象存在时）" if prefix else ""), describe(value), value.get("description", "未在源Schema写独立说明；结合业务规则与字段映射评审")))
        rows.extend(fields(value, path + ".", required_parent and required))
        if isinstance(value.get("items"), dict):
            rows.extend(fields(value["items"], path + "[].", required_parent and required))
    return rows


@lru_cache(maxsize=1)
def semantic_sources():
    meanings = {}
    for item in read("docs/04-database/field-provenance.json")["fields"]:
        for source in item["api_refs"]:
            meanings.setdefault(source["schema_pointer"], set()).add(item["table"] + "." + item["field"] + "：" + item["definition"])
    return meanings


def field_table(schema, component=None):
    text = "| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |\n| --- | --- | --- | --- |\n"
    for raw in fields(schema):
        row = list(raw)
        if component:
            pointer = "/components/schemas/" + component + "/properties/" + row[0]
            meanings = semantic_sources().get(pointer, set())
            if meanings:
                row[3] = "候选字段来源：" + "；".join(sorted(meanings)) + "。来源引用不是写入许可，完整处理按操作核验。"
        text += "| " + " | ".join(escaped(v) for v in row) + " |\n"
    return text + "\n是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。\n\n"


def outputs():
    spec = read(BASE + "openapi.yaml")
    index = read(BASE + "operation-index.json")
    trace = read("docs/00-project/requirement-traceability.yaml")["requirements"]
    backlog = read("tasks/backlog.yaml")["tasks"]
    tasks = {t["id"]: t for t in backlog}
    schemas = spec["components"]["schemas"]
    mappings = read("docs/04-database/api-field-mapping.json")["mapping"]
    semantics = read(BASE + "interface-annotations.json")
    docs, records = {}, []
    for item in index:
        op = spec["paths"][item["path"]][item["method"]]
        oid = op["operationId"]
        requirements = [r for r in trace if oid in r["operation_ids"]]
        modules = sorted({r["requirement_id"].split("-")[1] for r in requirements if r["requirement_id"].startswith("FR-")})
        annotation = semantics["operations"][oid]
        detail_path = BASE + "operations/" + oid + ".md"
        record = {"operation_id": oid, "method": item["method"].upper(), "path": "/api/v1" + item["path"],
                  "source_pointer": "/paths/" + item["path"].replace("~", "~0").replace("/", "~1") + "/" + item["method"],
                  "modules_from_business_trace": modules, "task_ids": op["x-task-ids"], "table_names": op["x-table-names"],
                  "requirement_ids": [r["requirement_id"] for r in requirements],
                  "test_ids": sorted({v for r in requirements for v in r.get("test_ids", [])}),
                  "detail_file": detail_path, "implementation_status": annotation["implementation_status"],
                  "formal_approved": False, "request_schema": item["request"], "response_schema": item["response"]}
        records.append(record)
        text = f"# {annotation['title']}：{oid}\n\n" + source_note(BASE + "openapi.yaml")
        text += f"`{record['method']} {record['path']}`；operationId=`{oid}`；源指针=`{record['source_pointer']}`。\n\n"
        text += f"实现范围：**{annotation['implementation_status']}**；{annotation['scope_note']}。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。\n\n"
        text += "## 调用目的与权限\n\n" + annotation["purpose"] + "\n\n"
        security = op.get("security", spec.get("security", []))
        text += "OpenAPI身份声明：`" + json.dumps(security, ensure_ascii=False) + "`；功能权限候选：`" + op["x-required-permission"] + "`。\n\n"
        text += annotation["authorization_scope"] + "\n\n"
        text += "来源任务：" + "、".join(f"[{tid} {tasks[tid]['name']}](../../../{tasks[tid]['doc_file']})" for tid in record["task_ids"]) + "。\n\n"
        text += "关联需求：" + "、".join(record["requirement_ids"]) + "；关联候选表：" + ("、".join(record["table_names"]) or "无") + "。表引用不证明代码已使用或有访问授权。\n\n"
        text += "## 参数与请求\n\n| 参数 | 位置 | 必填 | 结构限制 |\n| --- | --- | --- | --- |\n"
        for parameter in op.get("parameters", []):
            text += f"| {parameter['name']} | {parameter['in']} | {bool(parameter.get('required', False))} | {escaped(describe(parameter['schema']))} |\n"
        body = op.get("requestBody")
        if body:
            text += "\n请求体必须出现：`" + str(bool(body.get("required", False))) + "`；支持媒体类型：`" + ", ".join(body["content"]) + "`。\n\n"
            if item["request"]:
                text += f"结构源：`#/components/schemas/{item['request']}`；字段与完整约束见[数据结构](../data-structures.md#{item['request'].lower()})。\n\n" + field_table(schemas[item["request"]], item["request"])
                example = read(BASE + "examples/" + item["request"] + ".json")
                text += "结构样例（合成占位数据，非运行结果）：\n\n```json\n" + jdump(example) + "\n```\n\n"
            else:
                text += "本接口为二进制请求，按源content/schema提交字节。分片编号、摘要和Content-Length必须与实际字节相符，不能改用JSON base64生产上传。\n\n"
        else:
            text += "\n源契约未定义请求体；查询通过上述路径/查询参数传入。\n\n"
        text += "## 响应、状态与下一步\n\n| HTTP | 描述 | 媒体类型/结构 | 响应头 |\n| --- | --- | --- | --- |\n"
        for code, response in op["responses"].items():
            structures = [kind + ": " + describe(value.get("schema", {})) for kind, value in response.get("content", {}).items()]
            text += f"| {code} | {escaped(response['description'])} | {escaped('; '.join(structures))} | {escaped('; '.join(k+': '+describe(v.get('schema',{})) for k,v in response.get('headers',{}).items()))} |\n"
        if item["response"]:
            text += f"\n成功结构：`{item['response']}`，详细字段见[数据结构](../data-structures.md#{item['response'].lower()})。\n\n" + field_table(schemas[item["response"]], item["response"])
            text += "成功结构样例（不证明实际执行）：\n\n```json\n" + jdump(read(BASE + "examples/" + item["response"] + ".json")) + "\n```\n\n"
        text += annotation["completion_and_followup"] + "\n\n"
        conditional = any(p["name"] == "If-Match" for p in op.get("parameters", []))
        text += ("该接口声明If-Match：必须服务端原子核验对象版本；缺少条件428、旧版本412、状态不许可409。ETag绑定对象/聚合的精确范围仍按业务设计及缺口评审，body expected_version不能代替条件更新。" if conditional else "该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。") + "\n\n"
        text += "声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。\n\n"
        text += "## 字段与数据库对应\n\n| 方向/字段 | 当前映射 | 处理说明 |\n| --- | --- | --- |\n"
        for row in mappings:
            if row["operation_id"] == oid:
                text += f"| {row['direction']}/{row['field']} | {escaped(', '.join(row['targets']) or '服务层输入/聚合，不直接生成数据库列')} | {escaped(row['semantics'])} |\n"
        text += "\n映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。\n\n"
        text += "## 联调与验收条件\n\n关联计划用例：" + "、".join(record["test_ids"]) + "。这些ID是测试计划引用，不是本页接口的运行通过证据。\n\n"
        text += "实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。\n"
        docs[detail_path] = text
    data_text = "# 业务接口数据结构详表\n\n" + source_note(BASE + "openapi.yaml")
    data_text += "共102个源组件；先读[整体说明](system-interface-specification.md)。每个组件给出字段表及完整原始Schema；required、null、枚举、引用、条件组合均保留。字段语义尚未独立定义的情况明确标记，不能把UUID当授权或把0—1分数当业务/法律概率。\n\n"
    for name, schema in schemas.items():
        data_text += "## " + name + "\n\n源指针：`#/components/schemas/" + name + "`。\n\n" + field_table(schema, name) + "完整源结构（派生副本）：\n\n```json\n" + jdump(schema) + "\n```\n\n"
    docs[BASE + "data-structures.md"] = data_text
    module_records = []
    for module in MODULES:
        reqs = [r for r in trace if r["requirement_id"].startswith("FR-" + module + "-")]
        ids = {oid for r in reqs for oid in r["operation_ids"]}
        ops = [r for r in records if r["operation_id"] in ids]
        related_tasks = sorted({tid for r in reqs for tid in r["task_ids"]})
        file = BASE + "modules/" + module.lower() + ".md"
        module_records.append({"module": module, "name": NAMES[module], "requirement_ids": [r["requirement_id"] for r in reqs],
                               "declared_business_operations": sorted(ids), "source_task_ids": related_tasks, "doc_file": file,
                               "all_business_implemented": False})
        text = f"# {module} {NAMES[module]}接口导航\n\n" + source_note("docs/00-project/requirement-traceability.yaml")
        text += "整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。\n\n| 业务需求 | 已声明operationId | 任务 |\n| --- | --- | --- |\n"
        for r in reqs:
            text += f"| {r['requirement_id']} {r['name']} | {', '.join(r['operation_ids']) or '主追踪未直接绑定API，按整体流程/内部能力继续核验'} | {', '.join(r['task_ids'])} |\n"
        text += "\n| 详细操作 | 路径 | 实现状态 |\n| --- | --- | --- |\n"
        for operation in ops:
            text += f"| [{operation['operation_id']}](../operations/{operation['operation_id']}.md) | {operation['method']} {operation['path']} | {operation['implementation_status']} |\n"
        text += "\n模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。\n"
        docs[file] = text
    inference = read(BASE + "inference-openapi.yaml")
    inf_operation = inference["paths"]["/inference/{capability}"]["post"]
    models = read("docs/06-algorithms/model-catalog.yaml")["models"]
    inf_text = "# 内部模型调用详细说明\n\n" + source_note(BASE + "inference-openapi.yaml")
    inf_text += "调用入口 `POST /internal/v1/inference/{capability}`；业务调用方是已授权任务的worker/模型网关，使用独立serviceAuth。该内部口不能作为前端直接接口，不能将调用令牌/任意URL装入消息。路径capability须与请求能力一致，按对应独立Schema校验，再核验案件/用途、对象版本/摘要、期限及运行身份。\n\n"
    inf_text += "OpenAPI响应码：`" + ", ".join(inf_operation["responses"]) + "`。源oneOf各有34个请求/响应分支，模型能力的编辑源仍是schemas/model；目前只实测M15的合成CPU子范围。其他33能力未因Schema存在而运行通过。\n\n"
    for model in models:
        inf_text += f"## {model['id']} {model['name']}\n\n能力：`{model['capability']}`；路径：`POST /internal/v1/inference/{model['capability']}`；输入路径：`{model['input_kind']}`；输出种类：`{model['output_kind']}`。\n\n"
        inf_text += "关联任务：" + ", ".join(model["task_ids"]) + "；数据集：" + ", ".join(model["dataset_ids"]) + "；候选/许可/运行状态：`" + " / ".join(model[k] for k in ["status", "license_status", "runtime_status"]) + "`。\n\n"
        for kind in ["request", "response"]:
            path = f"schemas/model/{model['id']}.{kind}.schema.json"
            inf_text += f"### {kind}字段\n\n结构源：[{path}](../../{path})；SHA-256：`{digest(path)}`。\n\n" + field_table(read(path))
        inf_text += "SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。\n\n"
    inf_text += "研发实现与统一Problem细节见[poc-api.md](poc-api.md)；输出mock=false只说明该次使用真实合成模型，不能说明业务准确率通过。独立业务网关已实施服务身份适配、期限、路径/消息/版本/固定对象/来源校验，并在执行后复核取消及撤销，见[本批说明](../03-development/stage-three/remaining-interface-implementation.md)。缺真实服务身份或能力提供方时503；34能力Schema不表示34真实模型完成，正式条件见[缺口清单](interface-gap-register.md)。\n"
    docs[BASE + "inference-interfaces.md"] = inf_text
    contract_sources = [BASE + "openapi.yaml", BASE + "inference-openapi.yaml", BASE + "operation-index.json",
                        BASE + "interface-annotations.json", "docs/00-project/requirement-traceability.yaml",
                        "tasks/backlog.yaml", "docs/04-database/api-field-mapping.json", "docs/04-database/field-provenance.json", "docs/06-algorithms/model-catalog.yaml", "schemas/api/common.schema.json", "scripts/generate_interface_docs.py"]
    contract_sources.extend(f"schemas/model/{m['id']}.{kind}.schema.json" for m in models for kind in ["request", "response"])
    catalog = {"status": "DETAIL_DOCUMENTED_WITH_OPEN_CONTRACT_GAPS", "formal_frozen": False,
               "business_operation_count": len(records), "business_schema_count": len(schemas), "internal_capability_count": len(models),
               "source_hashes": {path: digest(path) for path in contract_sources}, "operations": records, "modules": module_records,
               "generated_docs": sorted(list(docs) + [BASE + "interface-catalog.json", BASE + "detailed-interface-index.md"]), "generation_source": "scripts/generate_interface_docs.py"}
    docs[BASE + "interface-catalog.json"] = jdump(catalog) + "\n"
    nav = "# 详细接口目录\n\n共73个外部业务候选操作、102个组件、34类内部能力，模块覆盖不等于流程/实现完整。先读[整体说明](system-interface-specification.md)、[统一规则](common-interface-rules.md)和[缺口与拟补方案](interface-gap-register.md)。以下由唯一来源生成，禁止直接改字段定义。\n\n| operationId | 方法/路径 | 主业务模块 | 详细文件 |\n| --- | --- | --- | --- |\n"
    for operation in records:
        nav += f"| {operation['operation_id']} | {operation['method']} {operation['path']} | {', '.join(operation['modules_from_business_trace']) or '共享/工程入口，按来源任务核验'} | [逐接口说明](operations/{operation['operation_id']}.md) |\n"
    nav += "\n## 模块目录\n\n" + "\n".join(f"- [{m['module']} {m['name']}]({m['doc_file'].removeprefix(BASE)})" for m in module_records)
    nav += "\n\n[完整数据结构](data-structures.md)、[内部34类能力](inference-interfaces.md)、[机器覆盖索引](interface-catalog.json)、[实际PoC接口](poc-api.md)。\n"
    docs[BASE + "detailed-interface-index.md"] = nav
    return docs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = outputs()
    differences = []
    for name, content in result.items():
        path = ROOT / name
        expected = content.encode("utf-8")
        if args.check:
            if not path.exists() or path.read_bytes() != expected:
                differences.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    print(json.dumps({"status": "FAIL" if differences else "PASS", "derived_files": len(result), "differences": differences}))
    return bool(differences)


if __name__ == "__main__":
    raise SystemExit(main())
