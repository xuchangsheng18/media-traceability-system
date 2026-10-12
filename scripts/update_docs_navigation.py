"""Refresh the actual docs file index, retaining specific existing descriptions."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    nav = ROOT/"docs/README.md"
    old = nav.read_text(encoding="utf-8")
    descriptions = {}
    for line in old.splitlines():
        match = re.match(r"\| \[[^\]]+\]\((<[^>]+>|[^)]+)\) \| (.+) \|$", line)
        if match:
            descriptions[unquote(match[1].strip("<>"))] = match[2]
    prefix = old.split("## 当前文件完整索引", 1)[0]
    prefix = prefix.split("## 第二阶段实际工程文档", 1)[0]
    prefix = prefix.replace("当前为规划和开发输入候选，NOT_FROZEN。资料已经归档不等于系统已经实现，结构校验也不等于所有业务语义通过。",
                            "当前CPU研发最小工程已运行并通过本机CI；正式业务/生产仍NOT_FROZEN。文档、结构校验、研发闭环与正式业务验收分别判定。")
    entries = {
        "02-architecture/environment-constraints.md": "实际Linux、Miniforge py310、Desktop挂载/网络/CPU与PythonEOL边界。",
        "02-architecture/resource-and-team-inventory.md": "宿主、Desktop虚拟机与容器配额分别盘点；磁盘、GPU与责任人未决。",
        "02-architecture/technical-baseline.md": "1.1-py310-cpu研发执行基线，区别于正式生产冻结和全部业务实现。",
        "02-architecture/technology-options.md": "12个技术域的替代方案、研发执行选择、实测和扩展边界。",
        "02-architecture/compatibility-matrix.md": "实际锁定组合、安装/构建/运行兼容证据及升级路径。",
        "02-architecture/licenses.md": "包/镜像/FFmpeg/Desktop与权重的许可盘点、审核缺口和再分发要求。",
        "02-architecture/security-baseline.md": "研发鉴权、秘密、输入、日志和网络措施；正式身份/案件/审计等差距。",
        "02-architecture/technical-validation-report.md": "各真实检查结果、证据路径、范围和未测事项。",
        "02-architecture/technical-baseline-change-control.md": "开发快照、正式冻结、ADR/锁/迁移变更和恢复规则。",
        "02-architecture/stage-two-official-sources.md": "本轮官方兼容、机制与许可来源；网页不替代部署实测。",
        "02-architecture/non-functional-requirements.md": "引用原非功能需求源并登记实测口径，不另造正式指标。",
        "03-development/ci-cd.md": "本机21门禁及私有GitHub一次性托管CI；平台run/源码SHA/制品另认报告。",
        "03-development/contract-generation.md": "两份OpenAPI及事件Schema生成3份TS类型；版本信封与旧消息兼容桥接。",
        "03-development/stage-two-readiness.md": "23步实际开发状态和未完成的正式条件。",
        "03-development/stage-two-deliverables.json": "逐步机器对照；保留计划并区分开发验证与正式完成。",
        "10-deployment/development-runbook.md": "真实启动、复建、SSH页面访问、令牌、端口、卷、停止与排查。",
        "03-api/poc-api.md": "已实现PoC入口和53操作正式契约的区别，鉴权/错误与合成模型范围。",
        "04-database/poc-database.md": "独立开发5表含账本/审计、逐字段来源、outbox与旧租约拒绝；区别于62表业务字典/SQL。",
        "00-project/review-package/technical-baseline-review.md": "实际技术评审输入与待正式确认事项，不能自动充当批准。",
        "00-project/validation/environment-inventory.json": "实际宿主/引擎/服务版本、上限和时点快照；不是峰值或独占配额。",
        "00-project/validation/ci-all-report.json": "本机完整门禁逐命令实际状态、耗时与执行范围；托管执行为false。",
        "00-project/validation/ci-report.json": "最近一次正常CI入口执行报告；详细阶段与范围须核对。",
        "00-project/validation/ci-failure-probe-report.json": "故意插入失败后的真实非零门禁报告；FAIL为探针预期。",
        "00-project/validation/ci-failure-gate-report.json": "验证故意失败确实阻断构建/部署的判定，PASS不等于探针本身成功。",
        "00-project/validation/runtime-lock-report.json": "实际Python补丁与全部第三方包是否匹配精确锁。",
        "00-project/validation/lock-reproduction-report.json": "全新venv按精确锁安装后的依赖与导入结果。",
        "00-project/validation/generated-contract-report.json": "3份TS类型临时重新生成后的字节一致性。",
        "00-project/validation/poc-integration-report.json": "21项真实API/对象/SQL/队列/CPU/追踪/Problem结果检查，不是业务模型验收。",
        "00-project/validation/poc-resilience-report.json": "5项队列/过期租约/服务及版本对象重启/幂等冲突检查，服务恢复记录。",
        "00-project/validation/media-query-report.json": "6项合成媒体和微型SQL/向量/鉴权检查；不代表中文或大规模业务。",
        "00-project/validation/poc-browser-report.json": "Chromium实际上传与显示异步结果的测试记录。",
        "00-project/validation/poc-ui.png": "真实浏览器运行截图，保存前已清空研发令牌。",
        "00-project/validation/synthetic-training-experiment.json": "64随机张量120步真实CPU训练种子/损失；不当业务准确率。",
        "00-project/validation/python-components.json": "安装包版本与声明许可元信息；不是完整OS SBOM或正式许可审查。",
        "00-project/validation/python-audit-report.json": "pip-audit发现与跳过原因；CPU torch被跳过，不能声称全部无漏洞。",
        "00-project/validation/npm-sbom.cdx.json": "锁定前端依赖的CycloneDX物料清单；不涵盖OS镜像。",
        "00-project/validation/repository-secrets-report.json": "确切开发凭据值及已知秘密文件名检查，非完整DLP。",
    }
    entries.update({
        "03-development/migrations-and-events.md": "专用开发迁移/摘要、版本事件、原始追踪与旧租约拒绝；明确旧库接管及并发边界。",
        "03-development/stage-two-gap-register.md": "剩余正式条件、输入、责任角色与关闭标准；不补造姓名和批准。",
        "03-development/stage-two-gap-register.json": "上述条件机器索引，真实状态与负责人未知值保留。",
        "10-deployment/development-backup-restore.md": "维护时段开发冷备、原VersionId/DB/模型隔离恢复；凭据与生产RPO/RTO边界。",
        "00-project/validation/github-actions-report.json": "实际GitHub run、源码SHA、结论、制品摘要/门禁验真；配置和执行严格分开。",
        "00-project/validation/migration-fencing-report.json": "15项隔离迁移/权限/8数据库竞争者检查，非8Celery传输验收。",
        "00-project/validation/media-timestamp-report.json": "真实非零原点合成抽帧PTS和像素核验；未证明VFR业务链路。",
        "00-project/validation/development-recovery-report.json": "8项5表/原对象版本/权重恢复，已有私有凭据保留，非生产灾备。",
    })
    descriptions.update(entries)
    section = "\n## 第二阶段实际工程文档\n\n当前入口与适用要求：\n\n| 文档 | 含义与严格判定要求 |\n| --- | --- |\n"
    for path, description in entries.items():
        section += f"| [{path}](<{path}>) | {description} |\n"
    section += "\n源Word、170任务和正式业务契约保持；PoC的可运行/真实合成模型与正式业务/GPU/生产冻结分开。当前版本和完整运行依赖在仓库根config/versions.yaml、config/locks和frontend/package-lock.json，不由旧手册示例推定。\n"
    files = sorted(p for p in (ROOT/"docs").rglob("*") if p.is_file() and p != nav)
    index = f"\n## 当前文件完整索引\n\n以下按实际文件生成，共{len(files)}份；文件存在不代表正式批准。旧输入快照/历史报告按其时间与scope阅读。\n\n| 实际文件 | 含义与使用要求 |\n| --- | --- |\n"
    for path in files:
        relative = path.relative_to(ROOT/"docs").as_posix()
        description = descriptions.get(relative)
        if not description:
            if "architecture-decisions/TB-ADR-" in relative:
                description = "已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。"
            elif path.suffix == ".md":
                title = next((line.lstrip("# ") for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("# ")), path.stem)
                description = "说明文档："+title.replace("|", "\\|")+"；结合正文的状态、来源和适用范围阅读。"
            elif "validation/" in relative:
                description = "实际或历史验证记录；须核对时间、status、scope、环境和未执行项，不当正式验收。"
            else:
                description = "项目结构化资料或来源附件；按所在专题的来源、版本与质量要求使用。"
        index += f"| [{relative}](<{relative}>) | {description} |\n"
    nav.write_text(prefix.rstrip()+"\n"+section+index, encoding="utf-8")
    print(f"Indexed {len(files)} actual docs files")


if __name__ == "__main__":
    main()
