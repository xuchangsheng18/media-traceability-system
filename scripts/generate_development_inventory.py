"""Extract task scope and static implementation evidence without importing product code."""

import argparse
import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = "docs/03-development/t001-t123-implementation-inventory"
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
MAIN = "backend/business_app/main.py"
SOURCES = (
    "tasks/backlog.yaml",
    "tasks/source-task-cards.json",
    "tasks/execution-status.json",
    "docs/03-api/openapi.yaml",
    "docs/03-api/inference-openapi.yaml",
    "docs/04-database/table-catalog.json",
    MAIN,
)
GROUPS = (
    (1, 18, "工程基础、身份权限与审计"),
    (19, 30, "来源登记、上传、导入及媒体资源"),
    (31, 40, "任务编排、节点执行及任务页面"),
    (41, 50, "媒体解析、抽帧、OCR/ASR及时间轴"),
    (51, 60, "模型注册、推理、发布及运维"),
    (61, 78, "风险识别与篡改取证"),
    (79, 97, "图片视频检索、首发及传播"),
    (98, 108, "主张核查、证据、复核及报告"),
    (109, 116, "数据集、训练及评测工具"),
    (117, 123, "安全、监控、恢复及容量验证"),
)


def read_json(root, path):
    return json.loads((root / path).read_text(encoding="utf-8-sig"))


def literal(node, label):
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        raise ValueError(f"Cannot statically resolve {label}; update inventory extraction explicitly")
    return node.value


def keyword(call, name, default=None):
    return next((item.value for item in call.keywords if item.arg == name), default)


def local_reference(document, value):
    """Resolve contract-local JSON pointers; reject unexamined external references."""
    visited = set()
    while isinstance(value, dict) and "$ref" in value:
        reference = value["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/") or reference in visited:
            raise ValueError(f"Unsupported or cyclic contract reference: {reference}")
        visited.add(reference)
        target = document
        for piece in reference[2:].split("/"):
            target = target[piece.replace("~1", "/").replace("~0", "~")]
        value = dict(target, **{key: item for key, item in value.items() if key != "$ref"})
    return value


def contract_operations(root, path):
    document = yaml.safe_load((root / path).read_text(encoding="utf-8"))
    prefix = document["servers"][0]["url"].rstrip("/")
    result = {}
    for route, item in document["paths"].items():
        item = local_reference(document, item)
        for method, operation in item.items():
            if method not in METHODS:
                continue
            operation = local_reference(document, operation)
            identifier = operation["operationId"]
            if identifier in result:
                raise ValueError(f"Duplicate contract operationId: {identifier}")
            parameters = {}
            for candidate in item.get("parameters", []) + operation.get("parameters", []):
                parameter = local_reference(document, candidate)
                parameters[(parameter["in"], parameter["name"])] = {
                    "name": parameter["name"],
                    "in": parameter["in"],
                    "required": parameter.get("required", False),
                    "schema": local_reference(document, parameter.get("schema", {})),
                }
            result[identifier] = {
                "operation_id": identifier,
                "contract_path": path,
                "method": method.upper(),
                "path": prefix + route,
                "parameters": list(parameters.values()),
                "response_statuses": sorted(operation["responses"]),
            }
    return result


def included_router_sources(root, main_path=MAIN):
    """Follow only explicitly included router imports, never every decorated file."""
    main_file = root / main_path
    tree = ast.parse(main_file.read_text(encoding="utf-8"))
    imported = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.level or not node.module:
            continue
        directory = main_file.parent
        for _ in range(node.level - 1):
            directory = directory.parent
        module = directory.joinpath(*node.module.split("."))
        candidate = module.with_suffix(".py")
        if not candidate.is_file():
            candidate = module / "__init__.py"
        for alias in node.names:
            imported[alias.asname or alias.name] = (candidate, alias.name)
    included = {}
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "include_router":
            continue
        if not call.args or not isinstance(call.args[0], ast.Name) or call.args[0].id not in imported:
            raise ValueError("Cannot statically resolve included business router")
        file, symbol = imported[call.args[0].id]
        if not file.is_file() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing or external included router: {file}")
        prefix_node = keyword(call, "prefix")
        included[(file.relative_to(root).as_posix(), symbol)] = {
            "include_prefix": literal(prefix_node, "include_router prefix") if prefix_node else "",
            "included_at": {"source_path": main_path, "line": call.lineno},
        }
    return included


def route_registrations(root):
    included = included_router_sources(root)
    result = {}
    for (path, symbol), inclusion in sorted(included.items()):
        tree = ast.parse((root / path).read_text(encoding="utf-8"))
        prefix = None
        for node in tree.body:
            if not isinstance(node, ast.Assign) or not any(
                isinstance(target, ast.Name) and target.id == symbol for target in node.targets
            ):
                continue
            if not isinstance(node.value, ast.Call):
                continue
            prefix_node = keyword(node.value, "prefix")
            prefix = literal(prefix_node, "APIRouter prefix") if prefix_node else ""
        if prefix is None:
            raise ValueError(f"Cannot statically resolve APIRouter {symbol} in {path}")
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                owner = decorator.func.value
                if not isinstance(owner, ast.Name) or owner.id != symbol or decorator.func.attr not in METHODS:
                    continue
                operation = keyword(decorator, "operation_id")
                identifier = literal(operation, "explicit route operation_id")
                if identifier in result:
                    raise ValueError(f"Duplicate business route operation_id: {identifier}")
                result[identifier] = {
                    "operation_id": identifier,
                    "method": decorator.func.attr.upper(),
                    "path": inclusion["include_prefix"] + prefix + literal(decorator.args[0], "route path"),
                    "python_function": node.name,
                    "source_path": path,
                    "line": node.lineno,
                    "included_at": inclusion["included_at"],
                    "evidence_kind": "STATIC_INCLUDED_ROUTER_REGISTRATION_NOT_RUNTIME_OR_ACCEPTANCE",
                }
    return result, sorted({path for path, _ in included})


def sql_code(text):
    """Blank comments, strings and dollar bodies, preserving source line numbers."""
    chars = list(text)
    length = len(text)
    i = 0
    while i < length:
        start = i
        if text.startswith("--", i):
            end = text.find("\n", i)
            i = length if end < 0 else end
        elif text.startswith("/*", i):
            depth = 1
            i += 2
            while i < length and depth:
                if text.startswith("/*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("Unclosed SQL block comment")
        elif text[i] == "'":
            i += 1
            while i < length:
                if text.startswith("''", i):
                    i += 2
                elif text[i] == "'":
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("Unclosed SQL string")
        elif text[i] == "$" and (tag := re.match(r"\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$", text[i:])):
            delimiter = tag.group()
            end = text.find(delimiter, i + len(delimiter))
            if end < 0:
                raise ValueError("Unclosed SQL dollar body")
            i = end + len(delimiter)
        else:
            i += 1
            continue
        for position in range(start, i):
            if chars[position] not in "\r\n":
                chars[position] = " "
    return "".join(chars)


def migration_objects(root):
    tables: dict[str, list[dict[str, Any]]] = {}
    functions: dict[str, list[dict[str, Any]]] = {}
    files = []
    table_pattern = re.compile(r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?mt\.([a-z_][a-z_0-9]*)\s*\(", re.I)
    function_pattern = re.compile(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+mt\.([a-z_][a-z_0-9]*)\s*\(", re.I)
    for file in sorted((root / "backend/business_migrations").glob("[0-9][0-9][0-9][0-9]_*.sql")):
        path = file.relative_to(root).as_posix()
        files.append(path)
        code = sql_code(file.read_text(encoding="utf-8"))
        for pattern, output in [(table_pattern, tables), (function_pattern, functions)]:
            for match in pattern.finditer(code):
                output.setdefault(match[1], []).append(
                    {
                        "source_path": path,
                        "line": code.count("\n", 0, match.start()) + 1,
                        "schema": "mt",
                        "evidence_kind": "VERSIONED_SQL_DEFINITION_NOT_TARGET_DATABASE_DEPLOYMENT",
                    }
                )
    return tables, functions, files


def body_nodes(function):
    """Do not attribute nested functions' SQL to the surrounding method."""
    pending = list(reversed(function.body))
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield node
        pending.extend(reversed(list(ast.iter_child_nodes(node))))


def signature_parameters(function):
    """Only names/kinds; defaults and annotations may contain private values."""
    args = function.args
    return {
        "positional_only": [item.arg for item in args.posonlyargs],
        "positional_or_keyword": [item.arg for item in args.args],
        "var_positional": args.vararg.arg if args.vararg else None,
        "keyword_only": [item.arg for item in args.kwonlyargs],
        "var_keyword": args.kwarg.arg if args.kwarg else None,
    }


def backend_method_sources(root, known_tables):
    """Index definitions and direct literal SQL, without resolving dynamic SQL."""
    methods, files = [], []

    def visit(nodes, module, path, owners=()):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, module, path, owners + (node.name,))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                references: set[str] = set()
                dynamic_sql = False
                for candidate in body_nodes(node):
                    if not isinstance(candidate, ast.Call) or not candidate.args:
                        continue
                    callee = candidate.func
                    sql_call = (isinstance(callee, ast.Name) and callee.id == "text") or (
                        isinstance(callee, ast.Attribute) and callee.attr in {"text", "execute", "exec_driver_sql"}
                    )
                    if not sql_call:
                        continue
                    argument = candidate.args[0]
                    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                        code = sql_code(argument.value)
                        references.update(
                            name
                            for name in re.findall(r"\bmt\.([a-z_][a-z_0-9]*)\b", code, re.I)
                            if name in known_tables
                        )
                    elif isinstance(argument, (ast.JoinedStr, ast.BinOp, ast.Name)):
                        dynamic_sql = True
                qualified = ".".join((module,) + owners + (node.name,))
                methods.append(
                    {
                        "qualified_name": qualified,
                        "python_name": node.name,
                        "source_path": path,
                        "line": node.lineno,
                        "parameter_names": signature_parameters(node),
                        "direct_literal_sql_tables": sorted(references),
                        "dynamic_or_indirect_sql_argument_present": dynamic_sql,
                        "evidence_kind": "STATIC_METHOD_AND_DIRECT_LITERAL_SQL_REFERENCES_NOT_RUNTIME_OR_COMPLETE_DAO",
                    }
                )
                visit(node.body, module, path, owners + (node.name,))
            else:
                visit(ast.iter_child_nodes(node), module, path, owners)

    for file in sorted((root / "backend/business_app").rglob("*.py")):
        path = file.relative_to(root).as_posix()
        files.append(path)
        module = ".".join(file.relative_to(root / "backend").with_suffix("").parts)
        visit(ast.parse(file.read_text(encoding="utf-8")).body, module, path)
    return methods, files


def work_kind(number):
    if number in {118, 119, 122, 123}:
        return "integration_security_or_capacity_validation"
    if 109 <= number <= 116:
        return "dataset_training_evaluation_tools"
    if 41 <= number <= 99:
        return "development_with_model_or_data_dependencies"
    return "engineering_or_business_development"


def build_inventory(root):
    backlog = yaml.safe_load((root / SOURCES[0]).read_text(encoding="utf-8"))["tasks"]
    source = read_json(root, SOURCES[1])
    ledger_document = read_json(root, SOURCES[2])
    ledger = {row["task_id"]: row for row in ledger_document["tasks"]}
    expected = [f"T{number:03}" for number in range(1, 171)]
    if [row["id"] for row in backlog] != expected or set(ledger) != set(expected) or set(source) != set(expected):
        raise ValueError("Expected all170 source tasks and exact backlog/ledger/source identity")
    if any(row["name"] != source[row["id"]]["name"] or row["name"] != ledger[row["id"]]["name"] for row in backlog):
        raise ValueError("Task source and execution ledger names disagree")
    canonical = contract_operations(root, SOURCES[3])
    internal = contract_operations(root, SOURCES[4])
    if set(canonical) & set(internal):
        raise ValueError("Business and internal contract operation IDs overlap")
    all_operations = dict(canonical, **internal)
    registrations, router_files = route_registrations(root)
    for identifier, registration in registrations.items():
        contract = all_operations.get(identifier)
        if not contract or any(registration[field] != contract[field] for field in ("method", "path")):
            raise ValueError(f"Registered route does not match authoritative contract: {identifier}")
    tables, functions, migration_files = migration_objects(root)
    methods, backend_files = backend_method_sources(root, set(tables))
    catalog = read_json(root, SOURCES[5])
    rows = []
    for task in backlog[:123]:
        identifier = task["id"]
        state = ledger[identifier]
        fields = source[identifier]["fields"]
        number = int(identifier[1:])
        operation_scope = []
        for operation in task["operation_ids"]:
            if operation not in all_operations:
                raise ValueError(f"Task operation has no authoritative contract: {identifier}/{operation}")
            operation_scope.append(
                {
                    "operation_id": operation,
                    "contract": all_operations[operation],
                    "business_registration": registrations.get(operation),
                    "runtime_or_end_to_end_verified_by_inventory": False,
                }
            )
        table_scope = [
            {
                "table_name": name,
                "catalog_description": catalog.get(name, {}).get("description"),
                "catalog_declared": name in catalog,
                "create_table_migrations": tables.get(name, []),
                "target_database_observed_by_inventory": False,
            }
            for name in task["table_names"]
        ]
        rows.append(
            {
                "task_id": identifier,
                "name": task["name"],
                "task_card": task["doc_file"],
                "group": next(name for start, end, name in GROUPS if start <= number <= end),
                "work_kind": work_kind(number),
                "source_role": task["source_role"],
                "actual_owner": state.get("actual_owner"),
                "source_dependencies": task["source_dependencies"],
                "execution_dependencies_candidate": task["execution_dependencies_candidate"],
                "outside_authorized_scope_dependencies": [
                    dependency for dependency in task["execution_dependencies_candidate"] if int(dependency[1:]) >= 124
                ],
                "source_work_scope": fields["工作范围"],
                "source_interface_data_contract": fields["接口或数据契约"],
                "source_acceptance": fields["验收标准"],
                "source_test_requirements": fields["测试要求"],
                "source_ci_gate": fields["CI门禁"],
                "operation_ids": task["operation_ids"],
                "table_names": task["table_names"],
                "model_ids": task["model_ids"],
                "dataset_ids": task["dataset_ids"],
                "input_refs": task["input_refs"],
                "planned_output_refs": task["output_refs_planned"],
                "declared_blocking_questions": task["blocking_questions"],
                "ledger_status": state["status"],
                "whole_task_verified": state.get("full_task_verified", False),
                "completed_substeps_count": len(state.get("completed_steps", [])),
                "remaining_work_items_count": len(state.get("remaining_steps", [])),
                "actual_completed_summary": state.get("summary_completed"),
                "actual_remaining_summary": state.get("summary_remaining"),
                "completed_steps": state.get("completed_steps", []),
                "remaining_steps": state.get("remaining_steps", []),
                "database_scope": table_scope,
                "database_method_references": [
                    {
                        "qualified_name": method["qualified_name"],
                        "source_path": method["source_path"],
                        "line": method["line"],
                        "parameter_names": method["parameter_names"],
                        "matched_declared_tables": sorted(
                            set(method["direct_literal_sql_tables"]) & set(task["table_names"])
                        ),
                        "evidence_kind": "STATIC_TABLE_INTERSECTION_NOT_TASK_IMPLEMENTATION_OR_RUNTIME_PROOF",
                    }
                    for method in methods
                    if set(method["direct_literal_sql_tables"]) & set(task["table_names"])
                ],
                "api_scope": operation_scope,
                "prerequisites_verified_by_inventory": False,
            }
        )
    declared_operations = {operation for row in rows for operation in row["operation_ids"]}
    declared_tables = {name for row in rows for name in row["table_names"]}
    summary = {
        "all_source_tasks": len(ledger),
        "authorized_task_count": len(rows),
        "all_completed_substeps": sum(len(row.get("completed_steps", [])) for row in ledger.values()),
        "all_remaining_work_items": sum(len(row.get("remaining_steps", [])) for row in ledger.values()),
        "all_whole_tasks_verified": sum(bool(row.get("full_task_verified", False)) for row in ledger.values()),
        "authorized_completed_substeps": sum(row["completed_substeps_count"] for row in rows),
        "authorized_remaining_work_items": sum(row["remaining_work_items_count"] for row in rows),
        "authorized_whole_tasks_verified": sum(row["whole_task_verified"] for row in rows),
        "authorized_status_counts": dict(Counter(row["ledger_status"] for row in rows)),
        "distinct_declared_tables": len(declared_tables),
        "distinct_declared_operations": len(declared_operations),
        "canonical_business_operation_count": len(canonical),
        "canonical_internal_operation_count": len(internal),
        "registered_business_operation_count": len(set(registrations) & set(canonical)),
        "registered_internal_operation_count": len(set(registrations) & set(internal)),
        "unregistered_canonical_business_operation_count": len(set(canonical) - set(registrations)),
        "declared_operations_registered_in_business_source": len(declared_operations & set(registrations)),
        "declared_operations_without_explicit_business_registration": len(declared_operations - set(registrations)),
        "versioned_create_table_count": len(tables),
        "versioned_sql_function_name_count": len(functions),
        "backend_python_definition_count": len(methods),
        "backend_python_definitions_with_direct_literal_sql_tables": sum(
            bool(method["direct_literal_sql_tables"]) for method in methods
        ),
        "declared_tables_without_catalog_or_migration_source": sorted(
            name for name in declared_tables if name not in catalog or name not in tables
        ),
    }
    refs = sorted(set(SOURCES) | set(router_files) | set(migration_files) | set(backend_files))
    return {
        "schema_version": 1,
        "scope": "T001_T123_READ_ONLY_SOURCE_AND_LEDGER_EXTRACTION_NOT_IMPLEMENTATION_OR_ACCEPTANCE",
        "observed_date_from_ledger": ledger_document["observed_date"],
        "generator": "scripts/generate_development_inventory.py",
        "source_hash_encoding": "sha256_of_utf8_text_with_CRLF_and_CR_normalized_to_LF",
        "source_file_sha256": {
            path: hashlib.sha256((root / path).read_text(encoding="utf-8").encode("utf-8")).hexdigest() for path in refs
        },
        "active_environment_boundary": "Current Linux/Miniforge py310/CPU development; Python candidates remain deferred; historical source-card versions are provenance, not newly adopted baselines.",
        "interpretation": [
            "Source scope, dependencies, acceptance and tests are copied from backlog/source cards; current ownership and completed/remaining work are copied from the execution ledger.",
            "Only routers explicitly included by business create_app are statically indexed. Registration is not a successful request, deployment, permission decision or complete task acceptance.",
            "Canonical business API count, task-declared operation subset and actually registered business source count are distinct; no counter is hardcoded to a prior snapshot.",
            "health may be served by the independent PoC application. Historic devLogin does not authorize adding password login around formal OIDC.",
            "CREATE TABLE and SQL function definitions are versioned source evidence; this extractor never connects to a database or imports product code.",
            "Backend method definitions expose only qualified names, locations and parameter names. Task method references intersect declared tables with direct literal SQL schema references; comments, SQL string values and nested function bodies do not create parent-method matches. Dynamic/indirect SQL and transitive calls are not resolved, so this is not a complete DAO or task-implementation proof.",
            "No table declaration or operation ID means no such direct scope was declared; it does not authorize manufacturing a table, endpoint or successful model output.",
            "Task count, verified development substeps and remaining work items are different units; no completion percentage or acceptance is inferred.",
            "Tasks T124-T170 are preserved but are outside this development extraction; T092 dependency on T164 remains explicit.",
        ],
        "summary": summary,
        "unregistered_canonical_business_operation_ids": sorted(set(canonical) - set(registrations)),
        "tasks": rows,
        "registered_route_source_index": sorted(registrations.values(), key=lambda row: row["operation_id"]),
        "versioned_table_source_index": tables,
        "versioned_sql_function_source_index": functions,
        "backend_python_method_source_index": methods,
    }


def escaped(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def link(path, line=None):
    # GitHub file anchors retain exact method locations without claiming execution.
    target = "../../" + path + (f"#L{line}" if line else "")
    return f"[{path}{':' + str(line) if line else ''}](<{target}>)"


def method_signature(method):
    parameters = method["parameter_names"]
    parts = list(parameters["positional_only"])
    if parts:
        parts.append("/")
    parts.extend(parameters["positional_or_keyword"])
    if parameters["var_positional"]:
        parts.append("*" + parameters["var_positional"])
    elif parameters["keyword_only"]:
        parts.append("*")
    parts.extend(parameters["keyword_only"])
    if parameters["var_keyword"]:
        parts.append("**" + parameters["var_keyword"])
    return method["qualified_name"] + "(" + ", ".join(parts) + ")"


def render_markdown(document):
    summary = document["summary"]
    lines = [
        "# T001—T123开发任务、数据表、接口与方法落实清单",
        "",
        "自动生成：`python scripts/generate_development_inventory.py`；漂移检查：同命令加`--check`。不得独立修改派生结果。",
        "",
        f"任务台账日期：{document['observed_date_from_ledger']}。本清单只读取代码、契约、迁移及现存台账，不连接数据库、不执行迁移、不导入业务代码。",
        "",
        f"全部170任务：{summary['all_completed_substeps']}条已验证子步骤、{summary['all_remaining_work_items']}条剩余工作、{summary['all_whole_tasks_verified']}项整任务验收。T001—T123：{summary['authorized_completed_substeps']}条已验证子步骤、{summary['authorized_remaining_work_items']}条剩余工作、{summary['authorized_whole_tasks_verified']}项整任务验收。三种计数单位不同，不据此计算任务完成率。",
        "",
        f"T001—T123声明{summary['distinct_declared_tables']}张不同表、{summary['distinct_declared_operations']}个不同操作ID；完整业务契约含{summary['canonical_business_operation_count']}个操作，当前源码显式注册其中{summary['registered_business_operation_count']}个，尚有{summary['unregistered_canonical_business_operation_count']}个未注册；内部推理契约/源码另计{summary['canonical_internal_operation_count']}/{summary['registered_internal_operation_count']}。当前版本迁移中发现{summary['versioned_create_table_count']}张表定义、{summary['versioned_sql_function_name_count']}个不同SQL函数名称。",
        "",
        f"后端Python静态索引包含{summary['backend_python_definition_count']}个函数/方法定义，其中{summary['backend_python_definitions_with_direct_literal_sql_tables']}个在直接SQL字面量中引用已定义表。完整限定名、参数名与位置见机器清单的`backend_python_method_source_index`；下方按任务列出与声明表直接相交的方法。动态SQL、间接调用和服务转发不作推断，未列出不代表没有方法实现。",
        "",
        "已有表定义不等于目标库已创建；路由与Python方法存在不等于运行服务已部署或业务成功。所有当前实际状态沿用任务台账，不自动接受任务。未知负责人保持未确定。",
        "",
        "当前环境沿用Linux、Miniforge py310和CPU；Python候选继续暂缓，原任务卡的历史Python版本仅保留来源。`health`可位于独立PoC入口；历史`devLogin`不能作为新增密码登录的授权。",
        "",
        "完整字段、原验收和测试要求、完成证据、逐项剩余工作及来源SHA-256见[机器清单](t001-t123-implementation-inventory.json)。[实施顺序](t001-t123-development-sequence.md)与[本批读取实现计划](t001-t123-catalog-read-implementation-plan.md)分别记录开发安排和具体修改边界。",
        "",
        "## 123项任务导航",
        "",
        "| 任务与源名称 | 当前状态 | 已验证子步/剩余 | 数据表 | 声明接口中已有业务注册/总数 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in document["tasks"]:
        state = (
            "部分已验证"
            if row["ledger_status"] == "PARTIAL_VERIFIED_SCOPE"
            else ("整任务已验证" if row["whole_task_verified"] else "尚无充分已验证交付")
        )
        registered = sum(bool(item["business_registration"]) for item in row["api_scope"])
        lines.append(
            f"| [{row['task_id']} {escaped(row['name'])}](#{row['task_id'].lower()}) | {state} | {row['completed_substeps_count']}/{row['remaining_work_items_count']} | {escaped('、'.join(row['table_names']) or '未声明直接落库')} | {registered}/{len(row['api_scope'])} |"
        )
    for row in document["tasks"]:
        lines.extend(
            [
                "",
                f'<a id="{row["task_id"].lower()}"></a>',
                f"## {row['task_id']} {row['name']}",
                "",
                f"任务卡：{link(row['task_card'])}；分组：{row['group']}；源责任角色：{row['source_role']}；实际负责人：{row['actual_owner'] or '未确定'}。",
                "",
                f"原工作范围：{row['source_work_scope']}",
                "",
                f"原接口/数据约定：{row['source_interface_data_contract']}",
                "",
                f"源依赖：{row['source_dependencies']}；执行依赖候选：{'、'.join(row['execution_dependencies_candidate']) or '无'}；依赖是否具备仍需实际核验。",
                "",
                f"当前已验证范围：{row['actual_completed_summary'] or '尚无足以登记的本任务已验证交付。'}",
                "",
                f"未完成事项：{row['actual_remaining_summary'] or '见任务卡和机器台账，不能从空摘要推定完成。'}",
                "",
            ]
        )
        if row["outside_authorized_scope_dependencies"]:
            lines.extend(
                [
                    "**范围外依赖**："
                    + "、".join(row["outside_authorized_scope_dependencies"])
                    + "；不得因本清单包含当前任务而自动扩展授权。",
                    "",
                ]
            )
        if row["database_scope"]:
            lines.append("表与创建源码：")
            lines.append("")
            for table in row["database_scope"]:
                refs = (
                    "、".join(link(item["source_path"], item["line"]) for item in table["create_table_migrations"])
                    or "未发现版本化CREATE TABLE，待核对"
                )
                lines.append(
                    f"- `mt.{table['table_name']}`：{table['catalog_description'] or '未发现目录描述'}；{refs}。本清单不证明运行库已采用。"
                )
            lines.append("")
        else:
            lines.extend(["未声明直接落库表，不能为填满清单自行增加数据实体。", ""])
        if row["database_method_references"]:
            lines.extend(["关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：", ""])
            for method in row["database_method_references"]:
                lines.append(
                    f"- `{method_signature(method)}`；{link(method['source_path'], method['line'])}；表："
                    + "、".join(method["matched_declared_tables"])
                    + "。"
                )
            lines.append("")
        elif row["table_names"]:
            lines.extend(
                ["未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。", ""]
            )
        if row["api_scope"]:
            lines.extend(
                [
                    "| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |",
                    "| --- | --- | --- | --- |",
                ]
            )
            for api in row["api_scope"]:
                contract = api["contract"]
                query = (
                    "、".join(
                        parameter["name"] + ("（必填）" if parameter["required"] else "（可选）")
                        for parameter in contract["parameters"]
                        if parameter["in"] == "query"
                    )
                    or "无"
                )
                registration = api["business_registration"]
                method = (
                    (f"`{registration['python_function']}`；" + link(registration["source_path"], registration["line"]))
                    if registration
                    else "未发现显式业务路由注册；不推定其他服务状态"
                )
                lines.append(
                    f"| `{api['operation_id']}` | `{contract['method']} {contract['path']}` | {query} | {method} |"
                )
            lines.append("")
        else:
            lines.extend(["未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。", ""])
    lines.extend(
        [
            "## 全部版本化表定义",
            "",
            "以下为当前迁移源码，不是已连接数据库的查询结果。",
            "",
            "| 表 | 创建迁移与位置 |",
            "| --- | --- |",
        ]
    )
    for name, entries in document["versioned_table_source_index"].items():
        lines.append(
            f"| `mt.{name}` | " + "、".join(link(item["source_path"], item["line"]) for item in entries) + " |"
        )
    lines.extend(
        [
            "",
            "## SQL函数与版本定义",
            "",
            "同名函数的各版本定义均保留；它们是迁移源码索引，不证明当前运行实例的有效函数体。",
            "",
            "| SQL函数名称 | 版本迁移及位置 |",
            "| --- | --- |",
        ]
    )
    for name, entries in document["versioned_sql_function_source_index"].items():
        lines.append(
            f"| `mt.{name}` | " + "、".join(link(item["source_path"], item["line"]) for item in entries) + " |"
        )
    lines.extend(
        [
            "",
            "## 适用边界与后续实际工作",
            "",
            "- 优先复用已有迁移、SQL访问、权限、案件/单位范围和审计；数据表或方法清单不替代任务实现。新增持久化结构使用后续增量迁移，不向现有库运行初始化。",
            "- T013本人身份接管、MFA、密钥验证与实际恢复仍按任务卡逐项核验；备份目录、RPO/RTO及维护窗口等未知输入保持未确定，不把公开口令当已妥善保护。",
            "- 六角色已确认的设计输入不等于正式策略已采用；正式来源授权、分类/用途事实不足时拒绝相应业务动作。",
            "- 模型、权重许可、用途授权数据及适用GPU未落实的算法任务保持剩余；合成CPU编码器不能充当全部正式模型。",
            "- 20/100并发、准确率和正式验收口径需有效输入及真实执行；现有CI门禁继续保留，Python候选暂缓不等于维护风险已接受。",
            "- 本清单仅整理T001—T123；其他47任务仍保留在总台账。未知人员、工时、日期或批准不得编造。",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without writing generated files")
    args = parser.parse_args(argv)
    document = build_inventory(ROOT)
    outputs = {
        BASE + ".json": json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        BASE + ".md": render_markdown(document),
    }
    stale = []
    for path, content in outputs.items():
        target = ROOT / path
        if not target.is_file() or target.read_text(encoding="utf-8") != content:
            stale.append(path)
            if not args.check:
                target.write_text(content, encoding="utf-8")
    if args.check and stale:
        print("Inventory drift: " + ", ".join(stale))
        return 1
    print(json.dumps({"status": "PASS", "check_only": args.check, "summary": document["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
