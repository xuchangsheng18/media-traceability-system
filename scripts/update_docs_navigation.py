"""Refresh the actual docs file index, retaining specific existing descriptions."""

import json
import re
from pathlib import Path
from urllib.parse import unquote

from generate_remaining_work_navigation import build as remaining_navigation
from generate_requirements_document import build as requirements_document
from generate_stage_status_navigation import build as stage_status_navigation
from generate_stage_three_docs import build as stage_three_documents

ROOT = Path(__file__).resolve().parents[1]


def main():
    for path, content in stage_three_documents().items():
        (ROOT / path).write_bytes(content.encode("utf-8"))
    content, summary = requirements_document()
    (ROOT / summary["document"]).write_bytes(content.encode("utf-8"))
    for path, content in stage_status_navigation().items():
        (ROOT / path).write_bytes(content.encode("utf-8"))
    for path, content in remaining_navigation().items():
        (ROOT / path).write_bytes(content.encode("utf-8"))
    nav = ROOT / "docs/README.md"
    old = nav.read_text(encoding="utf-8")
    descriptions = {}
    for line in old.splitlines():
        match = re.match(r"\| \[[^\]]+\]\((<[^>]+>|[^)]+)\) \| (.+) \|$", line)
        if match:
            descriptions[unquote(match[1].strip("<>"))] = match[2]
    prefix = old.split("## 当前文件完整索引", 1)[0]
    prefix = prefix.split("## 第一阶段实际材料", 1)[0]
    prefix = prefix.split("## 第二阶段实际工程文档", 1)[0]
    prefix = prefix.replace(
        "当前为规划和开发输入候选，NOT_FROZEN。资料已经归档不等于系统已经实现，结构校验也不等于所有业务语义通过。",
        "当前CPU研发最小工程已运行并通过本机CI；正式业务/生产仍NOT_FROZEN。文档、结构校验、研发闭环与正式业务验收分别判定。",
    )
    entries = {
        "03-development/t001-t011-foundation-review.md": "T012前11项任务逐项对照：本轮格式自动覆盖、7服务真实cgroup核验、当前GitHub治理和仍缺实测/真实输入的事项；不冒充整任务完成。",
        "00-project/validation/t001-t011-foundation-review-report.json": "保留T001—T011源验收/测试/依赖全文，逐项结论与证据及当前实际验证；整任务均未正式验收。",
        "00-project/validation/development-container-limits-report.json": "Compose、Docker设置与实际cgroup v2 CPU/内存/pids只读比对；缺失/无限/漂移拒绝，不代表临时盘或压力隔离已验证。",
        "08-security/access-control-model.md": "T011六角色、九个实体及身份/单位/案件关系；候选权限评审与后续0004持久化分别列证据，尚无正式身份授权。",
        "03-development/t012-identity-relations-design.md": "身份提供方与内部用户映射、同单位案件关系、稳定键、软禁用、撤销、管理/查询分权及正式接入边界。",
        "03-development/t012-identity-relations-plan.md": "本批测试、0004增量迁移、内部DAO、空研发库、资料和同步步骤；实际完成状态按实测报告和任务卡核对。",
        "04-database/identity-relations.md": "新增身份映射13列、单位开关和角色撤销2列、复合约束及恢复要求；区分原62表825字段与迁移后63表840字段。",
        "04-database/identity-relations-catalog.json": "0004逐列类型/约束/源码位置和摘要、既有表增量、实际结构版本及没有新增外部API字段的说明。",
        "00-project/validation/t012-identity-relations-report.json": "实际py310/PostgreSQL身份专项、完整回归、源码摘要及独立空研发库验证；不含连接凭据，不代表真实身份认证或整任务验收。",
        "08-security/access-control-model.json": "T011候选机器模型：六角色、41权限码、73操作逐项绑定；职责/限制/待定均非正式ALLOW，分类政策为空。",
        "03-development/t011-access-model-implementation.md": "T002/T010本批依赖、T011四项实施、测试证据与剩余条件；不关闭整任务或正式冻结。",
        "00-project/validation/t011-access-model-report.json": "实际py310专属设计校验与合成评审测试、源码摘要及范围；不证明正式身份或运行时授权。",
        "00-project/validation/t011-dependency-report.json": "T002配置追踪13例及T010模板/本批影响核对，限于T011所需依赖，不关闭上游整卡。",
        "03-development/stage-three/remaining-interface-implementation-plan.md": "剩余11类接口实施范围、顺序及正式前置条件；用户已授权继续实施。",
        "03-development/stage-three/remaining-interface-implementation.md": "剩余11类接口真实代码/数据库/ETag/授权/模型边界说明；73操作102组件、实际42外部及1内部挂载，正式条件另判。",
        "03-development/stage-three/foundation-implementation-plan.md": "六项整改实施顺序、共享维护/平台条件、Codex桌面与环境验收及每批同步；设计范围及详细计划已认可，当前会话实施，计划本身非完成证据。",
        "03-development/stage-three/python-type-check-implementation-plan.md": "独立mypy候选锁/制品、真实类型治理、错误阻断和CI步骤；原100包锁保持，独立检查已实测，CI及后续状态看验证报告。",
        "03-development/stage-three/business-interface-implementation-plan.md": "独立业务迁移/RLS、上传续传和7历史读取的文件/签名/失败测试/恢复计划；73操作825字段0.2快照方案已认可，首批所选工程已实施；后续接口按实际说明和验证报告核验。",
        "03-development/stage-three/readiness.md": "第三阶段16步及57条原验收逐条状态：文档、实测、部分/待落实与适用差异各列证据范围，与24/23步和170任务分开。",
        "03-development/stage-three/deliverables.json": "16源步骤、57条验收审查及实际状态/证据/限制；文档和配置生效独立判定，不伪造人员或批准。",
        "03-development/development-environment-validation-report.md": "第三阶段实际py310/Node/统一命令/独立工具层/三进程浏览器/扫描结果及未执行范围。",
        "03-development/development-environment-baseline.md": "Development Environment Baseline 1.0候选；沿用1.1-py310工程源，正式冻结条件未满足。",
        "00-project/validation/stage-three-runtime-report.json": "实际13项Linux/托管CPU命令与环境；共享栈未重启，GPU/Windows原生/生产未驗。",
        "00-project/validation/stage-three-demo-report.json": "三临时进程11项实测含三服务脱敏日志/trace及依赖停止503/502，1例浏览器；mock标记，无DB/权重/GPU访问。",
        "00-project/validation/stage-three-dependency-scan-report.json": "Python/npm实际已知漏洞扫描、退出状态和包跳过；不是全面安全或PythonEOL/OS准入证明。",
        "00-project/validation/stage-three-foundation-audit-report.json": "开发基础实际审查：共享VM100%及31其他容器、私有保护403、格式AST保全、两端Codex配置启用、Torch官方摘要/12,240载荷和13接口未闭项；正式条件仍待。",
        "00-project/validation/stage-three-platform-observation.json": "只读GitHub真实所有者、私有性、保护标志/规则查询及Actions；不冒充已配置权限。",
        "01-requirements/functional-requirements.md": "单文档详细需求：36业务需求逐项输入/流程/输出/异常/权限/验收与开发关联，全文170任务展开及10NFR/16规则/24协议；源目标、工程证据和未决/正式状态分别标注。",
        "00-project/remaining-work-navigation.md": "两阶段剩余工作总导航：第一阶段6项、第二阶段12项，含已补范围、前置/责任角色/关闭标准、13接口缺口及正式冻结条件；资源位置明确为Linux上的Docker虚拟机数据盘。",
        "00-project/remaining-work-navigation.json": "从19项权威台账与专项来源生成的同源导航索引/摘要；不作新的工作状态源、不关闭任务、不编造人员。",
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
        "03-development/ci-cd.md": "本机21及托管25门禁保留为历史；当前扩展检查数量、源码和制品以最新报告为准，非生产发布。",
        "03-development/contract-generation.md": "两份OpenAPI及事件/工作流Schema生成4份TS类型；唯一来源包装、版本信封与旧消息兼容桥接。",
        "03-development/stage-two-readiness.md": "23步实际开发状态和未完成的正式条件。",
        "03-development/stage-two-deliverables.json": "逐步机器对照；保留计划并区分开发验证与正式完成。",
        "10-deployment/development-runbook.md": "真实启动、复建、SSH页面访问、令牌、端口、卷、停止与排查。",
        "03-api/poc-api.md": "已实现PoC入口和73操作正式契约的区别，鉴权/错误与合成模型范围。",
        "04-database/poc-database.md": "独立开发5表含账本/审计、逐字段来源、outbox与旧租约拒绝；区别于62表业务字典/SQL。",
        "00-project/review-package/technical-baseline-review.md": "实际技术评审输入与待正式确认事项，不能自动充当批准。",
        "00-project/validation/environment-inventory.json": "实际宿主/引擎/服务版本、上限和时点快照；不是峰值或独占配额。",
        "00-project/validation/ci-all-report.json": "最近完整门禁逐命令状态、耗时及环境；托管与源码身份按报告实际字段读取。",
        "00-project/validation/ci-report.json": "最近一次正常CI入口执行报告；详细阶段与范围须核对。",
        "00-project/validation/ci-failure-probe-report.json": "故意插入失败后的真实非零门禁报告；FAIL为探针预期。",
        "00-project/validation/ci-failure-gate-report.json": "验证故意失败确实阻断构建/部署的判定，PASS不等于探针本身成功。",
        "00-project/validation/runtime-lock-report.json": "实际Python补丁与全部第三方包是否匹配精确锁。",
        "00-project/validation/lock-reproduction-report.json": "全新venv按精确锁安装后的依赖与导入结果。",
        "00-project/validation/generated-contract-report.json": "4份TS类型临时重新生成后的字节一致性，新增workflow来源包装仍需运行Schema检查。",
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
    entries.update(
        {
            "00-project/phase-readiness-register.md": "19项工作核查（第一阶段7/第二阶段12）：版式核验按本轮范围完成，18项仍有条件；技术补充与正式/真实交付分开。",
            "00-project/phase-readiness-register.json": "19项非签字工作机器清单，关联原24/23步与已有缺口；无虚构人员/完成/批准。",
            "00-project/requirement-processing-map.md": "36业务需求→来源任务/内部能力→结果身份及读取；逐条技术语义已复核，七条源未绑API保留，正式规则/实现另判。",
            "00-project/requirement-processing-map.json": "上述逐需求源指针/摘要、原始引用与候选流程；不改主追踪或新增可调用HTTP。",
            "00-project/requirement-flow-proposals.json": "12模块默认与36条逐需求复核覆盖：入口/读取/身份/缺口解释；不形成第二API结构源或运行实现证明。",
            "00-project/requirement-semantic-review.md": "36需求逐条复核原验收/任务/能力/入口/结果读取，解释错误映射修正和投影缺口；无正式业务批准。",
            "00-project/requirement-semantic-review.json": "36条技术语义结论、来源摘要、结果身份和明确未实现范围；主追踪原引用保持。",
            "00-project/execution-planning-inputs.json": "可编辑实际人员/有效工时/日历/剩余工时/证据/到位日输入；未知为null，部分证据与tasks/execution-status.json同源，不等于整任务完成。",
            "00-project/execution-schedule.md": "170任务原工时397—491人日、条件依赖计算及人力容量排期规则；实际日历输入不足未生成交付日期。",
            "00-project/execution-schedule.json": "逐任务工时/依赖/证据与未填写实际日期；源状态不改、完整验收未凭PoC归零。",
            "05-workflows/result-identity-and-projection.md": "案件/资产/task/run/result/cluster身份、应用投影及版本化读取规则，含簇成员/首发rank与insufficient零证据处置。",
            "09-testing/metric-protocols.md": "24项验收方法：单位/分母/公式/失败/未知/分层/源目标及真实条件；8组公式夹具不充当算法性能成绩。",
            "09-testing/metric-protocols.json": "24协议机器定义及待填样本/模型/版本/资源字段，approved_target为null、真实验收未执行。",
            "00-project/validation/stage-one-completion-report.json": "本轮5组图表来源/36语义/24协议8公式/170排期容量与循环/6个零证据正反契约案例；非正式验收。",
            "00-project/validation/acceptance-metric-reference-report.json": "8组自建公式计算证据：失败不删分母、未知单列和引用语义支持；不代表真实业务达标。",
            "00-project/validation/phase-readiness-report.json": "4项19缺口分类/36需求来源/派生漂移/快照语义检查，非业务或生产验收。",
            "00-project/validation/resource-readiness-snapshot.json": "2026-10-13只读宿主/研发卷容量及服务/GPU工具观测；非独占配额或GPU缺失/兼容证明。",
            "00-project/validation/repository-governance-snapshot.json": "实际GitHub主分支/规则集查询/Actions时点快照；不可查询不等于不存在，本轮未修改治理配置。",
            "03-api/system-interface-specification.md": "第二阶段整体接口入口：七类服务边界、73操作/102结构/34能力、详细阅读标准及13项开放缺口。",
            "03-api/detailed-interface-index.md": "73份逐操作说明及12模块导航；方法/路径、来源、实现边界和明细落点。",
            "03-api/data-structures.md": "102业务组件逐字段必填/可空/约束与完整源Schema的只读派生，不形成第二编辑源。",
            "03-api/inference-interfaces.md": "34能力逐请求/响应字段、路径、任务/数据及Schema摘要，只有M15合成CPU子范围已实测。",
            "03-api/common-interface-rules.md": "身份/权限、追踪、分页、幂等、ETag、异步、错误/Range和版本；未定配置保持待定。",
            "03-api/service-and-event-contracts.md": "服务/私有存储/DB调用及PoC事件字段和故障边界，全业务消息未完成。",
            "03-api/interface-catalog.json": "73操作、12模块和34能力的唯一来源摘要及详细路径/需求/测试引用，不当实施证明。",
            "03-api/interface-annotations.json": "73操作的工程用途/授权范围/下一步与实现状态解释；不独立定义Schema或授予权限。",
            "03-api/interface-gap-register.md": "13项接口设计/实施缺口、候选路径/方案/影响与关闭标准，候选路径不可调用。",
            "03-api/interface-gap-register.json": "上述开放缺口的机器索引；姓名未知/未批准，不改任务依赖。",
            "00-project/validation/interface-documentation-report.json": "6项明细覆盖/生成漂移/12模块/68能力分支/13缺口/源码实现边界检查，非全接口运行验收。",
            "03-development/migrations-and-events.md": "专用开发迁移/摘要、版本事件、原始追踪与旧租约拒绝；明确旧库接管及并发边界。",
            "03-development/stage-two-gap-register.md": "剩余正式条件、输入、责任角色与关闭标准；不补造姓名和批准。",
            "03-development/stage-two-gap-register.json": "上述条件机器索引，真实状态与负责人未知值保留。",
            "10-deployment/development-backup-restore.md": "维护时段开发冷备、原VersionId/DB/模型隔离恢复；凭据与生产RPO/RTO边界。",
            "00-project/validation/github-actions-report.json": "实际GitHub run、源码SHA、结论、制品摘要/门禁验真；配置和执行严格分开。",
            "00-project/validation/migration-fencing-report.json": "15项隔离迁移/权限/8数据库竞争者检查，非8Celery传输验收。",
            "00-project/validation/media-timestamp-report.json": "真实非零原点合成抽帧PTS和像素核验；未证明VFR业务链路。",
            "00-project/validation/development-recovery-report.json": "8项5表/原对象版本/权重恢复，已有私有凭据保留，非生产灾备。",
        }
    )
    entries.update(
        {
            "03-development/stage-two-completion-matrix.md": "第二阶段12类剩余工作的本轮补齐、实际证据、23步对应与仍需输入/实现；不将后续170业务任务强制当第二阶段全部完成。",
            "03-development/stage-two-completion-matrix.json": "12项阶段核查与补充/实际条件机器台账，正式完成false，真实负责人仍未知。",
            "03-development/stage-two-external-inputs.json": "16类实际资源/身份/数据/模型/GPU/生产/治理输入，未知为null，占位人员不当实际责任人。",
            "03-development/stage-two-implementation-plan.md": "资源、身份、13接口、DAG、模型媒体检索、证据灾备六批工作与实际前置/验收；170任务仍依各任务卡。",
            "04-database/authorization-isolation-prototype.md": "隔离RLS/案件单位/撤销/结果追加真实原型与可信中间件、共享角色和特权绕过边界；非62表部署。",
            "09-testing/stage-two-representative-validation.md": "21项隔离中文、11项VFR媒体、6组运维交付检查与物料采集的实际命令/断言和未测范围。",
            "10-deployment/stage-two-operations-and-offline-delivery.md": "99%容量处理、候选阈值、镜像OS物料、离线摘要/复建与治理；未声称扩容/全部制品/正式保护已完成。",
            "00-project/validation/stage-two-isolation-report.json": "新隔离PostgreSQL16的14权限历史+7中文词项GIN检查，既有数据库未修改，正式身份/业务表未联调。",
            "00-project/validation/stage-two-media-report.json": "11项8帧VFR/非零PTS/抽帧像素/音频/字幕/90度旋转原件摘要检查，不充当真实OCR/ASR或业务媒体验收。",
            "00-project/validation/stage-two-supplement-report.json": "6组材料覆盖/容量分级/离线正反摘要检查；正式和全部业务仍未完成。",
            "00-project/validation/stage-two-completion-report.json": "2026-10-12阶段工程总结历史快照，21门禁及当时run按原时点读；本轮新增6组检查另见stage-two-supplement-report。",
            "00-project/validation/stage-two-resource-report.json": "真实卷容量快照按候选阈值评估；最新状态须看采样时间及同步回执，历史CRITICAL不是当前结论。",
            "00-project/validation/stage-two-software-report.json": "7服务/5镜像的已安装OS物料采集、ID/RepoDigest/缺镜像覆盖；非漏洞扫描或许可批准。",
            "00-project/validation/image-sbom.spdx.json": "实际运行镜像与已安装OS包SPDX2.3清单；许可未知NOASSERTION，未托管二进制/Python/npm/权重另盘。",
        }
    )
    first_entries = {
        "00-project/execution-planning-scenario-inputs.json": "用户授权的10人占位工时/角色/起点/数据和GPU日期假设，后续替换；不填为实际人员或资源事实。",
        "00-project/execution-schedule-scenario.md": "170任务按占位容量生成日期与分期；明确超过源2027年6月末月，需调整投入/分工，未删功能或承诺实际日期。",
        "00-project/execution-schedule-scenario.json": "逐任务假设角色/日期/工时与源周期差异，actual_people_confirmed=false，实际输入表保持未确认。",
        "01-requirements/business-parameter-source-audit.md": "14类参数本地V1.4实际条款与V1.3交叉检查；候选可用率/RETURNED保留性质，未确认值不冒充批准。",
        "01-requirements/business-parameter-source-audit.json": "逐参数精确正文行/文本、来源候选与未定值，登记CLOSED在当前Task枚举未定义的差异。",
        "00-project/stage-one/remaining-work-completion.md": "第一阶段六类工程补充、阶段22—24接入及仍需真实输入；不把配置/Schema/工具当业务运行或正式冻结。",
        "00-project/source-authority-and-change-control.md": "唯一工程结构源、成对修订稿与历史身份、优先关系和变更/迁移/验证记录规则；正式依据仍需确认。",
        "00-project/source-authority-register.json": "10原件摘要/版本身份、2处V2/V1.0冲突及13类唯一结构源；实际负责人/正式依据未填。",
        "00-project/stage-one/review-resolution-inputs.json": "33问题可填写意见/责任人/依据/范围/例外/证据入口；不自动修改主Q或生成正式决定。",
        "01-requirements/business-parameter-contract.md": "14类业务参数的值/状态/依据/版本、RETURNED两路径与未知拒绝，适用规则不凭建议值确定。",
        "03-api/historical-result-reading.md": "7现有操作history成组参数、精确task/run/result与响应绑定头，404不回退最新；正式业务API尚未实现。",
        "05-workflows/workflow-contracts.md": "普通媒体/模型/投影/发布节点、7类事件、旧租约/取消/幂等与完整结果快照的单一Schema设计。",
        "05-workflows/dag-index.json": "36需求保守串行候选节点图、原任务引用和外部输入前提；不是170运行节点或已运行worker。",
        "06-algorithms/capability-projection-register.md": "34能力逐请求/响应/专用payload路径及全量原响应保存规则；公开专用投影实现单独登记。",
        "06-algorithms/capability-projection-register.json": "34结构摘要、输入字段/源任务、summary数组选择器与payload路径；不编造实体表或模型效果。",
        "09-testing/acceptance-execution-configuration.md": "24项实际样本/版本/资源/负载/目标/人员配置与NOT_EVALUABLE缺项，READY也不是验收成绩。",
        "09-testing/acceptance-execution-inputs.json": "24协议待填实际执行配置；正式目标和环境保持null，按Schema及适用指标检查。",
        "07-datasets/actual-input-inventory.md": "D01—D15实际元信息与计数口径，真实授权数量未知；64合成训练样本单列，不计正式数据。",
        "07-datasets/actual-input-inventory.json": "15规划数据卡/目录摘要、未知业务计数及真实合成证明；无真实数据扫描、导入或训练。",
        "00-project/validation/stage-one-controls-report.json": "8组来源、规则、RETURNED、36DAG/34模型快照、7历史读取/事件fencing、15数据卡/计数、24配置/33评审及170占位排期/14本地来源正反检查。",
        "00-project/validation/stage-one-input-preflight-report.json": "真实条件缺项报告：14参数/24验收/15数据/170排期/33评审；状态外部输入待填和NOT_READY，禁止冒称正式PASS。",
        "00-project/stage-one/README.md": "第一阶段24步总入口：本地来源、材料归属、候选状态和正式未冻结边界。",
        "00-project/stage-one/four-item-completion.md": "本轮图表/36语义/24验收协议/170排期四项总览及第二阶段接入；实际人员和日期不足明确保留。",
        "00-project/stage-one/visual-layout-audit.md": "9Word357页＋12页原型全页概览/关键页放大核验，8项阅读处置；保留原件，未声称全页逐像素交付审校。",
        "00-project/stage-one/visual-layout-audit.json": "10原件/PDF/369页PNG摘要、实际Office16.0只读渲染、页级几何/浏览范围和8项发现；CI不冒称重做人工看图。",
        "00-project/stage-one/steps-and-deliverables.md": "已在现有24步对应表更新实际材料/技术状态、操作、产物、待办及正式状态；不另建状态展示页，不与170业务任务完成率混同。",
        "00-project/stage-one/deliverables.json": "24步机器清单、源手册摘要、实际路径、状态和未确认事项；无虚构批准/负责人。",
        "00-project/stage-one/handoff.md": "第一阶段输入如何被第二阶段技术工程消费；两种基线与实际研发任务分别判断。",
        "00-project/stage-one/materials-manifest.json": "14份本地历史材料来源、原始字节摘要与身份；不混入正式业务原件清单。",
        "00-project/stage-one/history/README.md": "历史材料导航，限定旧61表/空服务器/旧工具环境的时点与适用范围。",
        "00-project/consistency-audit-report.md": "当前输入审查、已修复资料缺口和未决正式条件；不拿引用或结构通过代替业务批准。",
        "04-database/table-task-usage.md": "当前62表与任务引用阅读表，区分职责提案、需求引用与API引用，非实际代码使用证明。",
        "04-database/table-task-usage.json": "逐关系来源指针和摘要，完整覆盖62表；职责和实现批准明确为false。",
        "_converted/original/短视频与图片智能识别溯源系统功能模块界面原型图.md": "补回本地PPT逐页文字转换，来源摘要与原件一致；不代表视觉无损还原。",
        "guides/README.md": "三份手册与24/23步、170任务的关系及当前落点；手册是流程来源。",
        "00-project/validation/stage-one-validation-report.json": "12项来源/24步/62表/原件内容/章节映射/33项评审/候选摘要检查；不代替批准。",
        "00-project/stage-one/source-content-audit.md": "历史结构检查：9Word/495表/12PPT/92批注/200链接/2图/1700字段；158目录登记，当时视觉未验证，本轮补充另见visual-layout-audit。",
        "00-project/stage-one/source-content-audit.json": "可复算的原件/转换摘要、段落/表格/批注/链接/形状位置及逐任务字段证据；文字存在性不等于语义或版式一致。",
        "00-project/stage-one/source-section-map.md": "955处来源标题的准确原件位置与候选工程阅读/变更入口；未批准、未宣称全部实现。",
        "00-project/stage-one/source-section-map.json": "上述映射的原件摘要、准确位置、标题、实际目标路径和候选状态；可逐项核验。",
        "00-project/stage-one/review-register.json": "33项主Q的原文/指针/状态、七类主评审、已有任务引用与建议影响、所需输入和关闭条件；无代签。",
        "00-project/stage-one/input-baseline-candidate.md": "当前输入候选的选择范围、排除项、旧快照关系及正式冻结条件；NOT_FROZEN。",
        "00-project/stage-one/input-baseline-candidate.json": "当前第一阶段输入集合、大小与SHA-256，可复算且无批准编号；不当全仓同步凭据。",
        "00-project/review-package/README.md": "七类详细评审导航，覆盖33项主Q，区分台账明确引用和建议检查范围。",
    }
    imported = json.loads((ROOT / "docs/00-project/stage-one/materials-manifest.json").read_text(encoding="utf-8"))
    for item in imported["records"]:
        path = item["archived_path"].removeprefix("docs/")
        first_entries[path] = "第一阶段历史资料，按原始字节归档；旧计数、环境、未同步描述及候选决定不代表当前状态。"
    descriptions.update(first_entries)
    descriptions.update(entries)
    for path in (ROOT / "docs/05-workflows/dags").glob("*.json"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "该需求的普通处理/模型/投影/发布候选节点图，模型输入与原任务引用保留；外部输入未落实，未运行。"
        )
    for path in (ROOT / "docs/07-datasets/data-cards").glob("*.json"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "该数据集实际来源/授权/计数/标签/质检/切分/负责人/到位日填写入口；未知null，不自动发布或冻结。"
        )
    for path in (ROOT / "docs/03-api/operations").glob("*.md"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "逐操作派生说明：参数/请求/响应/结构样例、授权/版本/异步下一步、字段映射及任务/测试计划；未实现与缺口明确。"
        )
    for path in (ROOT / "docs/03-api/modules").glob("*.md"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "该模块三条来源业务需求、已有操作/任务及详细入口；直接API未绑定不等于需求删除或全部内部处理已完成。"
        )
    first_section = (
        "\n## 第一阶段实际材料\n\n第一阶段来源、做法与当前交付入口：\n\n| 文档 | 含义与严格判定要求 |\n| --- | --- |\n"
    )
    for path, description in first_entries.items():
        first_section += f"| [{path}](<{path}>) | {description} |\n"
    section = "\n## 第二阶段实际工程文档\n\n当前入口与适用要求：\n\n| 文档 | 含义与严格判定要求 |\n| --- | --- |\n"
    for path, description in entries.items():
        section += f"| [{path}](<{path}>) | {description} |\n"
    section += "\n源Word、170任务和正式业务契约保持；PoC的可运行/真实合成模型与正式业务/GPU/生产冻结分开。当前版本和完整运行依赖在仓库根config/versions.yaml、config/locks和frontend/package-lock.json，不由旧手册示例推定。\n"
    files = sorted(p for p in (ROOT / "docs").rglob("*") if p.is_file() and p != nav)
    index = f"\n## 当前文件完整索引\n\n以下按实际文件生成，共{len(files)}份；文件存在不代表正式批准。旧输入快照/历史报告按其时间与scope阅读。\n\n| 实际文件 | 含义与使用要求 |\n| --- | --- |\n"
    for path in files:
        relative = path.relative_to(ROOT / "docs").as_posix()
        description = descriptions.get(relative)
        if not description:
            if "architecture-decisions/TB-ADR-" in relative:
                description = (
                    "已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。"
                )
            elif path.suffix == ".md":
                title = next(
                    (
                        line.lstrip("# ")
                        for line in path.read_text(encoding="utf-8").splitlines()
                        if line.startswith("# ")
                    ),
                    path.stem,
                )
                description = "说明文档：" + title.replace("|", "\\|") + "；结合正文的状态、来源和适用范围阅读。"
            elif "validation/" in relative:
                description = "实际或历史验证记录；须核对时间、status、scope、环境和未执行项，不当正式验收。"
            else:
                description = "项目结构化资料或来源附件；按所在专题的来源、版本与质量要求使用。"
        index += f"| [{relative}](<{relative}>) | {description} |\n"
    nav.write_bytes((prefix.rstrip() + "\n" + first_section + section + index).encode("utf-8"))
    print(f"Indexed {len(files)} actual docs files")


if __name__ == "__main__":
    main()
