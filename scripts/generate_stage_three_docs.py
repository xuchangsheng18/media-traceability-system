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
    evidence_checked = current["status"] == "PASS"
    origin = paths[0]
    content = "# 第三阶段16步实际状态与导航\n\n2026-10-14；仓库和Codex研发环境实施，正式Development Environment Baseline 1.0仍NOT_FROZEN。第一阶段24步、第二阶段23步、第三阶段16步与170业务任务分别管理；本阶段不开展完整业务研发。\n\n"
    content += "两份Word原件已按字节归档，正文阅读版保留来源与提示词参考身份。当前用户已指定GitHub和Miniforge py310并要求同步，可继续已授权工程工作；原手册中的已批准Technical Baseline 1.0前提并未自动满足，当前实际为研发1.1-py310-cpu。审批、人事、正式网络/分支保护与资源条件分别登记。\n\n"
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
    content += (
        "| 步 | 原步骤与责任 | 已落实内容/产物 | 当前工程判定 | 正式/实际剩余条件 |\n| --- | --- | --- | --- | --- |\n"
    )
    for item in record["steps"]:
        outputs = "、".join(link(path, origin) for path in item["outputs"])
        status = item["development_status"]
        if item["step"] in {7, 8, 9, 12, 13, 15}:
            status += "；一致性检查" + ("PASS" if evidence_checked else "未完成")
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
        content += "实际操作：" + item["operation"] + "。剩余条件：" + item["remaining"] + "\n\n"
    content += "## 源建议与既有工程的适用差异\n\n"
    content += "- 仓库名称沿用用户指定media-traceability-system；不另建示例名、不重复账号/环境。\n- 一级目录沿用原13目录，补data-pipeline/tools预留职责；不搬移原文件，不增加重复Schema。\n- Element Plus/ECharts、Transformers/MMEngine、Black/MyPy/ESLint/Stylelint等并未由实际技术源选定；本次不将它们伪装为已安装或冻结。当前实际质量范围是Ruff、TS、Pytest/Vitest、契约、pre-commit和依赖/秘密检查。新增工具或全量旧代码格式规范另评审/验证。\n- 最小工程复用已有7服务和真实合成M15，mock=false并有明确非业务标识；不会改成假业务模型。已有后端/api/v1/health是鉴权后的数据库SELECT1，进程存活用/healthz，内部推理有/healthz。另建仓库内tools/stage_three_demo夹具实现三独立进程的Vue健康页、/api/v1/health、/api/v1/ready和模拟推理入口，并经浏览器实际验证。夹具不连已有数据库/对象存储、不加载权重，不是53业务API或34能力的新增实现。\n- Windows默认入口经SSH协调Linux py310，实际Windows原生py310安装未开展；Linux与GitHub隔离Runner是当前可验证的组合。\n- pre-commit配置与隔离工具层可以运行，Git hook是否安装由开发者选择；配置存在不等于实际钩子/平台保护已生效。\n\n"
    content += (
        "## 开发入口与容量保护\n\nLinux使用已验证的`/opt/conda/glwy/envs/py310/bin/python scripts/dev.py help`；当前服务器make未安装，Makefile仅作已有make环境的可选等价入口。Windows：`& .\\scripts\\dev.ps1 help`，SSH协调入口已验证，原生安装未验证。全部命令、环境与审计见"
        + link("CONTRIBUTING.md", origin)
        + "。dev默认观察已运行栈，clean默认只预览缓存；完整构建/集成在共享服务器上须显式命令标志和足够容量。\n\n"
    )
    content += "服务器研发数据盘位于Linux的Docker Desktop虚拟机，既有快照为99%使用率；本次未扩容，不能把宿主/workspace空闲容量当卷内容量。当前防护阈值5GiB只是研发操作保护，正式项目配额仍待确定。Docker服务变化和恢复类验证优先在GitHub独立临时Runner执行；当前共享栈维持运行。\n\n"
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
        + "。扫描跳过包不能判安全，CPU Torch发行包的版本/漏洞/供应商维护需进一步核查；Python3.10 EOL、镜像OS、模型许可与数据DLP独立管理。\n\n"
    )
    report += "未执行/限制：共享Docker数据盘容量未整改，本轮未在该栈重新执行构建/恢复；Windows原生安装、GPU/CUDA/真实模型、正式网络/业务数据、主分支保护正反验证及冻结未完成。三服务模拟夹具只证明健康/就绪、调用、trace和页面；真实模型/业务能力另验。模板、资料PASS、代表性模型/数据库结果都不代替这些工作。现有应用代码与锁保持，完整工程复建由实际GitHub run认定。\n"
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
