"""Render the 16 source steps, current evidence and explicit third-stage limitations."""

import argparse
import json
import posixpath
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "docs/03-development/stage-three/"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def link(path, origin, label=None):
    return f"[{label or path.rsplit('/', 1)[-1]}](<{posixpath.relpath(path, posixpath.dirname(origin))}>)"


def build():
    record = read(PREFIX + "deliverables.json")
    inventory = read(PREFIX + "source-inventory.json")
    paths = [
        PREFIX + "readiness.md",
        "docs/03-development/development-environment-validation-report.md",
        PREFIX + "README.md",
    ]
    current = read("docs/00-project/validation/stage-three-validation-report.json")
    runtime = read("docs/00-project/validation/stage-three-runtime-report.json")
    origin = paths[0]
    content = "# 第三阶段16步实际状态与导航\n\n2026-10-14；仓库和Codex研发环境实施，正式Development Environment Baseline 1.0仍NOT_FROZEN。第一阶段24步、第二阶段23步、第三阶段16步与170业务任务分别管理；本阶段不开展完整业务研发。\n\n"
    content += "两份Word原件已按字节归档，正文阅读版保留来源与提示词参考身份。当前用户已指定GitHub和Miniforge py310并要求同步，可继续已授权工程工作；原手册中的已批准Technical Baseline 1.0前提并未自动满足，当前实际为研发1.1-py310-cpu。审批、人事、正式网络/分支保护与资源条件分别登记。\n\n"
    content += "设计范围已获用户认可；[六项整改计划](foundation-implementation-plan.md)、[Python类型检查计划](python-type-check-implementation-plan.md)和[首批接口/数据库计划](business-interface-implementation-plan.md)已编制，详细计划已获用户认可，采用当前会话实施。独立Python类型检查已通过，CI按实际新run认定；新业务HTTP/迁移和共享扩容尚未实施；计划不能关闭缺口。\n\n"
    for source in inventory["records"]:
        content += (
            "- "
            + link(source["path"], origin)
            + "；"
            + link(source["converted_path"], origin, "全文阅读版")
            + "；SHA-256 `"
            + source["sha256"]
            + "`。\n"
        )
    content += (
        "\n第三阶段已有产物的机器对照见"
        + link(PREFIX + "deliverables.json", origin)
        + "，正式输入见"
        + link(PREFIX + "external-inputs.json", origin)
        + "；完整执行报告见"
        + link(paths[1], origin)
        + "。\n\n"
    )
    content += "57条原验收要求逐条登记。DOCUMENTED表示候选文档已写；VERIFIED_SELECTED_SCOPE表示仅在说明的研发范围有执行证据；PARTIAL表示仍有技术缺项；PENDING_EXTERNAL表示实际输入/配置/决定未落实；ADAPTED_EXISTING_REPOSITORY表示按已有仓库说明适用差异。工程状态与正式完成独立，不能将前两类换算成整个阶段的完成率。\n\n"
    content += (
        "| 步 | 原步骤与责任 | 已落实内容/产物 | 当前工程判定 | 正式/实际剩余条件 |\n| --- | --- | --- | --- | --- |\n"
    )
    for item in record["steps"]:
        outputs = "、".join(link(path, origin) for path in item["outputs"])
        status = item["development_status"]
        content += f"| {item['step']} | {item['title']}<br>{item['responsibility']} | {item['operation']}<br>{outputs} | {status} | {item['remaining']} |\n"
    content += "\n## 各步骤原输入和验收要求\n\n"
    for item in record["steps"]:
        content += f"### 第{item['step']}步 {item['title']}\n\n"
        content += (
            "源责任方式：" + item["responsibility"] + "。必要输入：" + item["required_input_from_guide"] + "。\n\n"
        )
        content += "源目标产物：" + item["planned_output_from_guide"] + "；本仓实际位置按上表输出阅读。\n\n"
        content += (
            "原验收要求（要求本身不等于已完成的判断）：\n\n"
            + "\n".join("- " + criterion for criterion in item["source_acceptance"])
            + "\n\n"
        )
        content += "实际操作：" + item["operation"].rstrip("。") + "。剩余条件：" + item["remaining"] + "\n\n"
        content += "| 原验收要求 | 当前状态 | 判定范围与限制 |\n| --- | --- | --- |\n"
        for review in item["acceptance_review"]:
            content += f"| {review['criterion']} | {review['status']} | {review['scope_note']} |\n"
        content += (
            "\n本步证据/候选产物："
            + "、".join(link(path, origin) for path in item["engineering_evidence"])
            + "。证据来源按机器清单逐条保留，候选文档本身不能证明配置生效。\n\n"
        )
    content += "## 源建议与既有工程的适用差异\n\n"
    content += "- 仓库名称沿用用户指定media-traceability-system；不另建示例名、不重复账号/环境。\n- 一级目录沿用原13目录，补data-pipeline/tools预留职责；不搬移原文件，不增加重复Schema。\n- Element Plus/ECharts、Transformers/MMEngine、Black/ESLint/Stylelint等并未由实际技术源选定；不将它们伪装为已安装或冻结。当前质量范围是Ruff、TS、Pytest/Vitest、契约、pre-commit和依赖/秘密检查；格式范围扩大至22文件，旧13文件的格式调整核对AST一致；独立Python类型检查22源文件通过，新增工具/类型修订有独立实测，CI按新run认定。\n- 最小工程复用已有7服务和真实合成M15，mock=false并有明确非业务标识；不会改成假业务模型。已有后端/api/v1/health是鉴权后的数据库SELECT1，进程存活用/healthz，内部推理有/healthz。另建仓库内tools/stage_three_demo夹具实现三独立进程的Vue健康页、/api/v1/health、/api/v1/ready和模拟推理入口，并经浏览器实际验证。夹具不连已有数据库/对象存储、不加载权重，不是53业务API或34能力的新增实现。\n- Windows默认入口经SSH协调Linux py310，实际Windows原生py310安装未开展；Linux与GitHub隔离Runner是当前可验证的组合。\n- 两端CLI实际加载完整AGENTS，精确项目可信登记后config/read项目配置层启用；桌面既有线程未因此宣称重载，根规则不当强制ACL。\n- pre-commit配置与隔离工具层可以运行，Git hook是否安装由开发者选择；配置存在不等于实际钩子/平台保护已生效。\n\n"
    content += (
        "## 开发入口与容量保护\n\nLinux使用已验证的`/opt/conda/glwy/envs/py310/bin/python scripts/dev.py help`；当前服务器make未安装，Makefile仅作已有make环境的可选等价入口。Windows：`& .\\scripts\\dev.ps1 help`，SSH协调入口已验证，原生安装未验证。全部命令、环境与审计见"
        + link("CONTRIBUTING.md", origin)
        + "。dev默认观察已运行栈，clean默认只预览缓存；build/integration-test/ci均须显式--allow-stack-changes。仅GitHub托管Runner的匹配工作区、独立临时runtime、default Docker上下文且无远程DOCKER_HOST时适用冷启动例外；仅GITHUB_ACTIONS标记不能绕过共享卷容量检查。无法读取容量则拒绝执行。此为研发操作保护，不是平台权限或安全隔离证明。\n\n"
    )
    content += "服务器研发数据盘位于Linux的Docker Desktop共享虚拟机；最新基础审查显示100%使用率、约0.73GiB可用，其他31个运行容器也使用该VM。扩容维护窗口未确认，宿主/workspace空闲不等于卷内容量。当前5GiB只是研发操作保护，正式配额仍待定。详见[开发基础审查](../../00-project/validation/stage-three-foundation-audit-report.json)及[变更和恢复方案](../development-environment-change-request.md)；Docker变化和恢复验证优先用GitHub独立临时Runner。\n\n"
    content += "## 正式完成与下一阶段\n\n当前允许按已明确输入继续合成CPU基础开发；不能将第三阶段文档或CI转为生产准入、真实数据授权、真实GPU/34模型达标或全部170任务完成。正式冻结还需人员/账号权限、实际技术与安全输入、主分支保护、资源整改、适用质量结果及完整批准。三服务夹具的ready/健康页/模拟入口与原PoC均有独立范围说明，不能把夹具成功充当真实模型/业务实现。\n\n"
    content += (
        "第一/第二阶段剩余工作仍按"
        + link("docs/00-project/remaining-work-navigation.md", origin)
        + "管理，未因此自动关闭；第三阶段正式基线见"
        + link("docs/03-development/development-environment-baseline.md", origin)
        + "及"
        + link("docs/03-development/development-environment-acceptance-record.md", origin)
        + "。\n"
    )
    report = (
        "# 第三阶段开发环境实际验证报告\n\n状态："
        + runtime["status"]
        + "；资料一致性："
        + current["status"]
        + "。正式冻结和完整业务验收均未断言。机器报告和具体来源摘要是执行依据，本文是阅读视图。\n\n"
    )
    report += (
        "验证资料："
        + link("docs/00-project/validation/stage-three-validation-report.json", paths[1])
        + "；实际命令/环境："
        + link("docs/00-project/validation/stage-three-runtime-report.json", paths[1])
        + "；实际托管源码/25工程门禁/制品："
        + link("docs/00-project/validation/github-actions-report.json", paths[1])
        + "。\n\n"
    )
    report += "| 项 | 当前记录与严格含义 |\n| --- | --- |\n"
    for item in runtime.get("checks", []):
        command = " ".join(item.get("command", []))
        report += f"| {item['name']} | {item['status']}；`{command}`；{item.get('scope', '')} |\n"
    report += "\n入口前置条件：当前Linux服务器make未安装，使用实际已验证的Python等价入口；Windows PowerShell经SSH的help/status已核验，Windows原生环境未安装/验证。共享栈容量保护实测会拒绝当前不足容量下的构建，未执行构建或更改服务。详见机器报告auxiliary_observations，不把未安装的可选工具记成PASS。\n\n"
    report += (
        "\n扫描原始输入/结果："
        + "、".join(
            link("docs/00-project/validation/" + name, paths[1])
            for name in [
                "stage-three-secrets-report.json",
                "stage-three-python-dependency-report.json",
                "stage-three-npm-dependency-report.json",
                "stage-three-quality-dependency-report.json",
                "stage-three-dependency-scan-report.json",
            ]
        )
        + "。原pip-audit跳过保持；新增基础审查已核对Torch官方wheel摘要及12,240安装载荷，OSV精确/基础版本查询均无返回条目，仍不代表所有二进制漏洞覆盖或准入。Python3.10维护、镜像OS、模型许可与数据DLP另核验。\n\n"
    )
    report += "三服务夹具新增实际结构日志关联与依赖停止验证：日志只包含固定事件/服务角色/方法/路由模板/状态/UUID/时长及模拟标识，不记录原始URL、请求体、头或令牌；同一request_id贯穿三服务。测试停止自建推理进程后核对ready=503、调用=502，且不回显输入。原始结果见stage-three-demo-report.json；只停止本验证创建的进程。\n\n"
    report += "未执行/限制：共享Docker数据盘容量未整改，本轮未在该栈重新执行构建/恢复；Windows原生安装、GPU/CUDA/真实模型、正式网络/业务数据、主分支保护正反验证及冻结未完成。三服务模拟夹具只证明健康/就绪、调用、trace、结构日志、故障和页面；真实模型/业务能力另验。模板、资料PASS、代表性模型/数据库结果都不代替这些工作。现有应用代码与锁保持，完整工程复建由实际GitHub run认定。\n"
    index = (
        "# 第三阶段材料与实际状态\n\n"
        + link(paths[0], paths[2], "16步实际操作、交付、适用差异和未完成条件")
        + "是本阶段总入口；"
        + link(paths[1], paths[2], "实际验证报告")
        + "记录运行范围。\n\n"
        + "\n".join(
            "- " + link(path, paths[2])
            for path in [
                PREFIX + "deliverables.json",
                PREFIX + "source-inventory.json",
                PREFIX + "external-inputs.json",
                PREFIX + "foundation-implementation-plan.md",
                PREFIX + "python-type-check-implementation-plan.md",
                PREFIX + "business-interface-implementation-plan.md",
                "docs/03-development/development-environment-baseline.md",
                "docs/03-development/development-environment-change-request.md",
                "docs/03-development/development-environment-acceptance-record.md",
            ]
        )
        + "\n\n正式NOT_FROZEN；引用手册不等于批准，部分步骤仍有具体技术/平台条件。\n"
    )
    return {paths[0]: content, paths[1]: report, paths[2]: index}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    differences = []
    for name, content in outputs.items():
        raw = content.encode("utf-8")
        if args.check:
            if not (ROOT / name).exists() or (ROOT / name).read_bytes() != raw:
                differences.append(name)
        else:
            (ROOT / name).write_bytes(raw)
    assert not differences, differences
    print(
        json.dumps(
            {
                "status": "PASS",
                "derived_files": len(outputs),
                "steps": 16,
                "formal_frozen": False,
                "differences": differences,
            }
        )
    )


if __name__ == "__main__":
    main()
