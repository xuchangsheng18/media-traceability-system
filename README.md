# 短视频与图片智能识别溯源系统

当前已完成用户指定Miniforge py310的CPU研发最小工程：环境盘点、版本锁定、前后端/数据库/对象/队列/真实推理闭环和本机21道CI门禁；GitHub实际运行另见平台报告。正式业务/生产NOT_FROZEN。保留12模块、170任务、不少于3类场景；本轮没有宣称全部业务实现。

服务器仓库：`/workspace/glwy/projects/media-traceability-system`；Python：`/opt/conda/glwy/envs/py310/bin/python`（3.10.22）。应用容器明确使用打包的同一py310。Python3.10已结束支持；生产前迁移并重新验证，见[环境约束](docs/02-architecture/environment-constraints.md)。

<!-- phase-remaining-navigation:start -->
## 第一、第二阶段剩余工作总导航

第一阶段24步、第二阶段23步与170业务任务分别管理。核查19项工作：版式核验在记录范围内已完成；剩余18项，包括第一阶段6项、第二阶段12项。工程补充、实际输入、实现/联调、正式验收与冻结分别判断。13接口缺口与这些事项交叉，不能相加计算完成率。真实人员/责任人未确认，10人占位排期只作假设。

容量问题位于Linux服务器172.16.58.179的Docker Desktop虚拟机内，为PostgreSQL研发数据卷所在文件系统。仓库快照时点`2026-10-13T04:53:08.550543+00:00`：df使用率99%，可用约1.63 GiB。不是本地Windows D盘或GitHub容量，也不代表Linux宿主/workspace全部空间不足；尚未记录扩容完成。

完整逐项导航：[剩余任务、前置条件、关闭标准及13接口缺口](<docs/00-project/remaining-work-navigation.md>)；[同源机器索引](<docs/00-project/remaining-work-navigation.json>)。

### 第1阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S1-N02 / P0<br>步1,2,23<br>项目/业务/文档管理（实际姓名待定） | 来源身份、版本优先级与变更权责<br>已有工程补充；实际条件/交付仍待落实 | 确认正式权威版本、适用范围、V2/V1.0身份冲突处置及实际变更责任人；唯一工程来源规则已完成。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n02>)<br>[source-document-inventory.md](<docs/00-project/source-document-inventory.md>)、[document-conversion-plan.md](<docs/00-project/document-conversion-plan.md>) |
| S1-N03 / P0<br>步4,6,10,11<br>业务/安全/架构（实际姓名待定） | 术语、业务规则与状态参数细化<br>已有工程补充；实际条件/交付仍待落实 | 确定风险/人工阈值、RETURNED后继、首发未知、审批目的与回流/保留规则的适用参数和例外。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n03>)<br>[glossary.md](<docs/00-project/glossary.md>)、[task-state-machine.md](<docs/05-workflows/task-state-machine.md>) |
| S1-N04 / P0<br>步7,8,12,14,19,21<br>架构/前后端/算法/测试（实际姓名待定） | 需求到内部处理与结果读取的语义闭环<br>已有工程补充；实际条件/交付仍待落实 | 13项契约缺口和真实业务实现/联调按对应任务继续；正式规则需实际依据。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n04>)<br>[requirement-processing-map.md](<docs/00-project/requirement-processing-map.md>)、[source-section-map.md](<docs/00-project/stage-one/source-section-map.md>) |
| S1-N05 / P0<br>步9,18<br>业务验收/测试/算法/运维（实际姓名待定） | 可执行的指标和验收测量协议<br>已有工程补充；实际条件/交付仍待落实 | 补真实封存样本/分层数量、正式目标、负载/资源/版本，实施对应真实验收。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n05>)<br>[non-functional-requirements.md](<docs/01-requirements/non-functional-requirements.md>)、[acceptance-criteria.md](<docs/09-testing/acceptance-criteria.md>) |
| S1-N06 / P0<br>步15<br>数据/业务授权/算法（实际姓名待定） | 数据集计数、标签和可用输入清单<br>已有工程补充；实际条件/交付仍待落实 | 落实来源/用途材料、标签版本/质检、原件与派生/内容簇计数及独立封存集规则；盘点实际可用样本。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n06>)<br>[dataset-catalog.md](<docs/07-datasets/dataset-catalog.md>)、[annotation-specification.md](<docs/07-datasets/annotation-specification.md>) |
| S1-N07 / P0<br>步17,19,23<br>项目计划/各研发负责人（实际姓名待定） | 人员投入、实际进度和分期执行台账<br>已有工程补充；实际条件/交付仍待落实 | 实际人员/投入、剩余工时、计划起点/工作日历和数据/GPU到位日未提供，实际日历排期待补。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n07>)<br>[backlog.yaml](<tasks/backlog.yaml>)、[dependency-report.md](<tasks/dependency-report.md>) |

### 第2阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S2-N01 / P0<br>步19<br>架构/前后端/算法/测试（实际姓名待定） | 整体接口流程和必要服务契约<br>已有工程补充；实际条件/交付仍待落实 | 补上传、审批、复核、反馈、发布、导出状态读取的唯一源契约/映射/样例/生成类型与业务联调；身份/来源平台协议需实际资料。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n01>)<br>[interface-gap-register.md](<docs/03-api/interface-gap-register.md>)、[contract-generation.md](<docs/03-development/contract-generation.md>) |
| S2-N02 / P0<br>步7<br>数据库/后端/安全（实际姓名待定） | 业务数据库访问层与升级迁移<br>已有工程补充；实际条件/交付仍待落实 | 按任务卡实现62表业务访问和版本迁移，逐表建立RLS/关联隔离与升级回退；不能将代表性两表套用为62表全部部署。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n02>)<br>[database-design.md](<docs/04-database/database-design.md>)、[poc-database.md](<docs/04-database/poc-database.md>) |
| S2-N03 / P0<br>步9,19,20<br>后端/算法/测试（实际姓名待定） | 完整任务编排、取消与多worker故障<br>已有工程补充；实际条件/交付仍待落实 | 实施实际调度器与多worker消息故障演练；当前8数据库竞争者不是8Celery worker，全业务DAG未运行。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n03>)<br>[task-state-machine.md](<docs/05-workflows/task-state-machine.md>)、[migrations-and-events.md](<docs/03-development/migrations-and-events.md>) |
| S2-N04 / P0<br>步15<br>身份平台/业务安全/后端（实际姓名待定） | 正式身份与案件/单位隔离<br>已有工程补充；实际条件/交付仍待落实 | 取得身份issuer/JWKS或其他正式协议、角色/单位/案件权威映射和撤销SLA，实施验证后联调；共享DB设置不能充当身份认证。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n04>)<br>[security-baseline.md](<docs/02-architecture/security-baseline.md>)、[permission-matrix.md](<docs/08-security/permission-matrix.md>) |
| S2-N05 / P0<br>步1,2,8,16<br>Linux及Docker运维/资源管理（实际姓名待定） | 项目配额与研发数据卷容量<br>已有工程补充；实际条件/交付仍待落实 | 落实Docker虚拟机数据盘扩容或经批准迁移，独占资源配额、维护人、权重/样本容量和GPU权限；完成后重新读取卷内df。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n05>)<br>[resource-readiness-snapshot.json](<docs/00-project/validation/resource-readiness-snapshot.json>)、[resource-and-team-inventory.md](<docs/02-architecture/resource-and-team-inventory.md>) |
| S2-N06 / P0<br>步12,13<br>数据/算法/GPU运维（实际姓名待定） | 业务模型、OCR/ASR及GPU验证<br>已有工程补充；实际条件/交付仍待落实 | 提供有用途授权的数据目录、权重许可/来源/摘要、实际GPU与驱动，实施逐能力训练/推理和独立封存盲测；M15合成CPU不代替业务能力。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n06>)<br>[model-catalog.yaml](<docs/06-algorithms/model-catalog.yaml>)、[model-evaluation.md](<docs/06-algorithms/model-evaluation.md>) |
| S2-N07 / P1<br>步14<br>媒体/算法/后端/测试（实际姓名待定） | 真实媒体、VFR和全时间轴链路<br>已有工程补充；实际条件/交付仍待落实 | 实际授权媒体的多编码/VFR/缺模态/裁剪/转码链路及OCR/ASR、长视频性能仍需实现和实测；本轮仅自建夹具。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n07>)<br>[media-timestamp-report.json](<docs/00-project/validation/media-timestamp-report.json>)、[TB-ADR-010-media-processing.md](<docs/02-architecture/architecture-decisions/TB-ADR-010-media-processing.md>) |
| S2-N08 / P1<br>步10,11<br>检索/算法/后端/测试（实际姓名待定） | 中文/规模化检索与传播图验证<br>已有工程补充；实际条件/交付仍待落实 | 确定正式中文分词/排序选型，实施实际大索引/向量及传播图业务、授权过滤和规模性能；4条文本不是业务检索指标。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n08>)<br>[technical-validation-report.md](<docs/02-architecture/technical-validation-report.md>)、[media-query-report.json](<docs/00-project/validation/media-query-report.json>) |
| S2-N09 / P0<br>步8,15<br>业务审核/安全/后端/存储（实际姓名待定） | 正式安全与证据防篡改机制<br>已有工程补充；实际条件/交付仍待落实 | 落实双人审批适用规则、可信时间/签名、保留期、WORM/密钥及管理员边界，实施下载每次授权核验和到期/撤销演练。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n09>)<br>[security-baseline.md](<docs/02-architecture/security-baseline.md>)、[audit-requirements.md](<docs/08-security/audit-requirements.md>) |
| S2-N10 / P1<br>步8,16<br>运维/数据库/安全/测试（实际姓名待定） | 生产灾备、PITR和密钥恢复<br>已有工程补充；实际条件/交付仍待落实 | 提供真实异地目标和密钥恢复授权、批准RPO/RTO；实施全业务异机恢复及对账，不能用开发冷备结果证明生产灾备。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n10>)<br>[development-backup-restore.md](<docs/10-deployment/development-backup-restore.md>)、[development-recovery-report.json](<docs/00-project/validation/development-recovery-report.json>) |
| S2-N11 / P0<br>步1,17<br>技术/软件准入/许可审查/安全（实际姓名待定） | 支持版本、OS物料和离线交付<br>已有工程补充；实际条件/交付仍待落实 | 确定支持中的生产Python/OS并重锁全CI；补未托管二进制/FFmpeg源码与notices、模型许可、漏洞数据库扫描及软件准入；不自动升级当前环境。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n11>)<br>[environment-constraints.md](<docs/02-architecture/environment-constraints.md>)、[licenses.md](<docs/02-architecture/licenses.md>) |
| S2-N12 / P1<br>步21,22,23<br>仓库管理/构建发布/安全（实际姓名待定） | CI组织治理与受控制品交付<br>已有工程补充；实际条件/交付仍待落实 | 落实私有仓库保护功能套餐/管理员配置、签名与离线镜像库/依赖缓存/保留策略；运行中镜像缺失须先重新构建验真再导出。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n12>)<br>[repository-governance-snapshot.json](<docs/00-project/validation/repository-governance-snapshot.json>)、[ci-cd.md](<docs/03-development/ci-cd.md>) |

已完成的S1-N01版式核验及19项全部已有证据在总导航保留，避免重新列为未开展。正式输入冻结（第一阶段22—24步）和技术冻结（第二阶段22—23步）仍NOT_FROZEN，实际决定/责任人及适用范围需落实。

资源/身份/授权数据和实际责任人填写[实际输入表](<docs/03-development/stage-two-external-inputs.json>)；人员/实际排期填写[人员排期输入](<docs/00-project/execution-planning-inputs.json>)。170业务任务后续按[实施计划](<docs/03-development/stage-two-implementation-plan.md>)推进。
<!-- phase-remaining-navigation:end -->

## 运行

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py pack
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py build
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py up
/opt/conda/glwy/envs/py310/bin/python scripts/run_ci.py all
```

页面在服务器回环地址 `http://127.0.0.1:14180`；从本机通过SSH转发访问。启动前提、首次复建、研发令牌取得方法和停止操作见[运行手册](docs/10-deployment/development-runbook.md)。秘密与权重在仓库外/命名卷中，不入Git。

页面上传自建PNG/JPEG→S3版本化原件和独立分析副本→PostgreSQL事务任务/outbox→RabbitMQ→Celery→独立PyTorch CPU推理→结果保存与展示。模型synthetic-cpu-encoder/demo-1真实训练和推理、mock=false，是8维合成工程验证模型，不是SSCD或正式业务模型。

## 阶段材料与阅读顺序

| 阶段 | 工作范围 | 当前入口与状态 |
| --- | --- | --- |
| 第一阶段 | 24步，来源归档→需求/契约/数据/任务/测试→评审与输入冻结 | [24步实际状态](docs/00-project/stage-one/stage-one-readiness.md)、[第一阶段材料导航](docs/00-project/stage-one/README.md)、[24步操作与交付](docs/00-project/stage-one/steps-and-deliverables.md)；候选已整理，正式NOT_FROZEN |
| 第二阶段 | 23步，环境/资源→选型与版本→最小工程→CI→技术评审与冻结 | [23步实际状态](docs/03-development/stage-two-readiness.md)、[接口与数据库文件导航](docs/03-development/stage-two-interface-database-navigation.md)、[整体接口](docs/03-api/README.md)、[业务数据库](docs/04-database/README.md)；开发工程/CI已验证，正式NOT_FROZEN |

先核对第一阶段输入与来源，再阅读第二阶段技术执行依据；[阶段衔接](docs/00-project/stage-one/handoff.md)明确哪些输入由实际工程消费。24步、23步与170研发任务是三套编号。

第一阶段本轮补齐[原件内容核对](docs/00-project/stage-one/source-content-audit.md)、[955处来源章节映射](docs/00-project/stage-one/source-section-map.md)、[33项具体评审清单](docs/00-project/review-package/README.md)和[当前候选输入摘要](docs/00-project/stage-one/input-baseline-candidate.md)。12项自动检查验证来源与摘要，不代替视觉核对、业务签认或170任务实现。

## 文档入口

- [完整文档导航](docs/README.md)：逐文件职责、要求、来源和实际索引。
- [技术基线](docs/02-architecture/technical-baseline.md)、[23步状态](docs/03-development/stage-two-readiness.md)。
- [技术验证报告](docs/02-architecture/technical-validation-report.md)、[CI说明](docs/03-development/ci-cd.md)、[版本锁](config/versions.yaml)。
- [业务任务卡](tasks/README.md)、[工程规则](AGENTS.md)、[未决问题](docs/00-project/open-questions.md)。

## 各目录

| 目录 | 当前职责 |
| --- | --- |
| [frontend](frontend/README.md) | Vue/TS研发界面、依赖锁、类型/单元/浏览器测试 |
| [backend](backend/README.md) | FastAPI、配置/错误/日志、PoC迁移、事务任务与worker |
| [ai-services](ai-services/README.md) | 真实CPU合成训练与M15契约推理；后续正式模型 |
| [shared-contracts](shared-contracts/README.md) | 从两份OpenAPI及事件Schema生成的4份TS类型 |
| [schemas](schemas/README.md) | 模型/数据Schema、夹具及语义检查 |
| [config](config/README.md) | 精确版本、包/镜像/环境摘要、资源样例 |
| [deploy](deploy/README.md) | 7服务Compose、镜像构建、代理及命名卷 |
| [scripts](scripts/README.md) | 启动、资料/SQL/集成/恢复、CI和清单工具 |
| [tests](tests/README.md) | 后端、SQL、夹具与工程验证 |
| [datasets](datasets/README.md) | 数据元信息；研发合成数据；敏感样本不入库 |
| [prompts](prompts/README.md) | 提示词来源与版本化要求 |
| [tasks](tasks/README.md) | 170源任务与单独的研发工程证据，不混淆完成状态 |
| [docs](docs/README.md) | 来源原件、设计、技术决定与实测记录 |

## 判定范围

本机CI真实运行，含15项后端、2项前端、1项浏览器、21项集成、5项恢复、6项媒体/查询、73项SQL断言/案例及契约/输入检查，详细数量和命令以报告为准。新增15项迁移/竞态、源PTS映射与8项冷备恢复。用户指定[私有GitHub](https://github.com/xuchangsheng18/media-traceability-system)采用Actions执行同源门禁，实际平台run、源码SHA与制品结论见[平台报告](docs/00-project/validation/github-actions-report.json)。

开发5表（含审计和迁移账本）与正式62表/824字段设计分开；仅单固定测试案件。正式身份/案件隔离、审批、审计、WORM、业务模型/GPU、20/100并发、业务中文检索/大型索引、生产灾备/密钥恢复和生产准入仍需后续验证。2026-10-13仓库快照中Linux服务器上的Docker虚拟机研发数据卷所在文件系统余量约1.63GiB、df99%；新增大模型/素材前先落实容量。宿主空闲、Windows本地D盘与GitHub容量分别判断。

源Word及其SHA256保持；Git保存本轮研发快照，origin采用用户提供私有GitHub，没有创建已批准生产基线标签。同步证据见docs/00-project/server-sync-receipt.json。

当前1.1补充的使用要求见[迁移事件手册](docs/03-development/migrations-and-events.md)、[开发冷恢复](docs/10-deployment/development-backup-restore.md)与[剩余条件/关闭标准](docs/03-development/stage-two-gap-register.md)。

## 整体接口详细入口

[系统整体接口说明](docs/03-api/system-interface-specification.md)、[53份逐操作/12模块导航](docs/03-api/detailed-interface-index.md)、[83组件字段](docs/03-api/data-structures.md)、[34内部能力](docs/03-api/inference-interfaces.md)已显式整理。第二阶段第19步保留PoC实测，整体接口仍有[13项开放缺口](docs/03-api/interface-gap-register.md)；候选路径不可调用，未标全系统接口冻结。

## 审批之外的剩余工作

[两阶段19项统一清单](docs/00-project/phase-readiness-register.md)列第一阶段7项、第二阶段12项的资料/设计/资源/实现/验证及完成标准；[36需求处理与读取映射](docs/00-project/requirement-processing-map.md)保持原主追踪，逐条技术语义已复核，正式规则/实现与运行待对应任务核验。审批不能代替这些工作，后续完整业务研发与本阶段技术设计分别安排。

## 图表、语义、验收与排期补充（2026-10-13）

[四项总览](docs/00-project/stage-one/four-item-completion.md)包含357页Word＋12页原型核验、36需求逐项技术语义复核、24测量协议及170任务证据/容量排期。insufficient零证据契约已同步修正；补充5项检查纳入CI。实际人员和资源到位日未知，因此未生成实际交付承诺；完整业务与正式冻结分别判断。

## 第一阶段工程控制补充（2026-10-13）

[第一阶段六类工程补充](docs/00-project/stage-one/remaining-work-completion.md)已接入来源/规则/历史读取/编排事件/34能力投影/验收/数据/排期控制；实际外部输入未提供，正式冻结仍待定。

## 第二阶段2026-10-13补充

[12类补齐与剩余条件](docs/03-development/stage-two-completion-matrix.md)、[实施计划](docs/03-development/stage-two-implementation-plan.md)和[实际外部输入](docs/03-development/stage-two-external-inputs.json)已纳入阶段导航。新增隔离权限/中文查询21项、VFR媒体11项、运维/离线摘要6组检查以及镜像OS物料采集；CI工程门禁扩为25道。实际PASS以本轮服务器和托管报告为准，正式身份/业务模型/资源及生产冻结仍未完成。
