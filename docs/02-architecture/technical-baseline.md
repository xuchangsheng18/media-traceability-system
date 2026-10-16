# Technical Baseline 1.1 — py310 CPU 研发基线

2026-10-16更新；状态 `DEVELOPMENT_VALIDATED`；正式业务/生产基线 `NOT_FROZEN`。用户指定 Miniforge py310，已据此完成环境盘点、开发技术选择和锁定、真实最小工程及GitHub接入。本机21门禁历史保留，现有托管配置为32道工程门禁，实际源码/run/制品证据见[GitHub报告](../00-project/validation/github-actions-report.json)。

T012之前的逐项工程核验、实际cgroup检查和仍未关闭的条件见[T001—T011复核](../03-development/t001-t011-foundation-review.md)；新增cgroup工作流检查与32项run_ci门禁分别记数。

| 交付 | 权威入口 | 判定 |
| --- | --- | --- |
| 环境与资源 | [环境约束](environment-constraints.md)、[资源清单](resource-and-team-inventory.md) | 实际节点、宿主/虚拟机差异、CPU配置及配额已记录 |
| 技术选择 | [方案比较](technology-options.md)、[14项TB-ADR](architecture-decisions/README.md) | 本轮研发执行选择；不是生产批准 |
| 版本与制品 | [versions.yaml](../../config/versions.yaml)、[锁文件](../../config/locks/) | Python、npm、基础镜像、环境包、权重都有实际版本/摘要 |
| 整体接口导航 | [接口与数据库文件导航](#接口与数据库文件导航)、[接口专题](../03-api/README.md)、[整体接口说明](../03-api/system-interface-specification.md)、[73操作明细](../03-api/detailed-interface-index.md) | 整体系统接口及服务边界；候选契约与已运行PoC分别判断，13项接口缺口仍开放 |
| 接口结构与规则 | [业务OpenAPI](../03-api/openapi.yaml)、[内部OpenAPI](../03-api/inference-openapi.yaml)、[102组件](../03-api/data-structures.md)、[34能力](../03-api/inference-interfaces.md)、[共用规则](../03-api/common-interface-rules.md) | 唯一结构源与逐字段/权限/幂等/版本要求；不从Schema存在认定全部API或模型运行 |
| 业务数据库设计 | [数据库专题](../04-database/README.md)、[设计](../04-database/database-design.md)、[字典](../04-database/data-dictionary.md)、[SQL](../04-database/initial-schema.sql)、[ER图](../04-database/er-diagram.md) | 62表825字段候选业务设计；初始化DDL用于新隔离空库，不能替代既有数据库版本迁移 |
| 字段来源与接口投影 | [字段来源](../04-database/field-provenance.json)、[API映射](../04-database/api-field-mapping.md)、[映射JSON](../04-database/api-field-mapping.json)、[表任务引用](../04-database/table-task-usage.md)、[首发排序](../04-database/first-source-ranking.md) | 核对cluster/asset/rank等来源指针、数据库列与API投影；任务引用不代表业务访问层已实施 |
| 最小工程 | [运行手册](../10-deployment/development-runbook.md)、[PoC API](../03-api/poc-api.md)、[PoC 数据库](../04-database/poc-database.md) | 浏览器→API→对象/SQL→RabbitMQ→worker→CPU推理→结果已运行 |
| 研发数据库与升级 | [研发5表](../04-database/poc-database.md)、[研发版本迁移](../../backend/migrations/)、[迁移事件机制](../03-development/migrations-and-events.md)、[RLS原型](../04-database/authorization-isolation-prototype.md) | 当前5表实际研发工程及代表性隔离机制；正式62表业务访问/迁移/RLS尚未全部实施 |
| CI与检查 | [CI说明](../03-development/ci-cd.md)、[技术验证报告](technical-validation-report.md)、[GitHub实际报告](../00-project/validation/github-actions-report.json) | 本机21门禁历史；托管32门禁及资料/导航检查按实际run和源码SHA判定 |
| 阶段状态与变更 | [第一阶段24步实际状态](../00-project/stage-one/steps-and-deliverables.md)、[第二阶段23步状态](../03-development/stage-two-readiness.md)、[变更控制](technical-baseline-change-control.md) | 保留全部12模块170任务；材料/开发实测/正式冻结分别判定 |

服务：Vue 页面、FastAPI API、PostgreSQL16.15、SeaweedFS4.48、RabbitMQ4.3.6、Celery5.6.3 worker、独立 PyTorch2.14.1+cpu 推理。容器内实际解释器为 Python3.10.22，不使用宿主系统 Python 替代。部署独立项目 `media-trace-py310`、专用网络和5个数据/配置卷；不修改其他项目。

模型为 `synthetic-cpu-encoder/demo-1`，120步真实合成训练、8维向量，复用 M15 Schema；不等同 SSCD，不输出执法结论、不证明业务准确率。大规模检索、真实传播分析、OCR/ASR及其他业务模型没有通过本轮验收。业务提案62表与开发5表（含账本/审计）分开。

正式基线尚需：生产软件准入/国产化/安全边界、受支持Python、身份与案件隔离、完整许可与镜像扫描、真实业务模型/GPU/正式指标、生产灾备与密钥恢复、资源配额、CI组织治理、实际责任人和有效评审。不能把本轮研发验证自动升级为23步全部正式冻结或170项功能已完成。

生产Python按[TB-ADR-002](architecture-decisions/TB-ADR-002-backend-stack.md#生产python选型与验证条件)优先验证3.13、3.12备选；[versions.yaml](../../config/versions.yaml)区分已验证py310与未验证生产候选，[实际输入表](../03-development/stage-two-external-inputs.json)登记待填证据。3.10生产例外须有具体依赖限制、持续补丁维护、实际责任人与有效决定；本次未安装或切换任何候选环境。

<!-- phase-contract-file-navigation:start -->
## 接口与数据库文件导航

2026-10-13。该页承接第二阶段第7步（数据库）、第19步（接口/事件）和第20步（最小工程）。整体接口/62表业务设计与已运行PoC/5表分别导航；不从设计文件推导正式部署。

### 技术完成程度与开发准入

用于启动基础开发的工程输入和代表性最小工程已经具备，但两阶段整体技术闭环仍未完成。可以按具体任务子范围进入基础开发；正式身份/数据/GPU/全业务实现及生产准入按所需条件继续。

已具备的技术范围：

- 用户Miniforge py310环境、精确锁、7服务CPU最小工程、迁移/租约/媒体/RLS代表性验证及托管工程门禁已有证据（当前数量及源码见GitHub报告）。
- 整体接口/数据库及现有24/23步状态已接入原文档，输入和运行边界明确。

现在可推进：

- 按任务卡复核/完善现有前后端框架、配置/错误/追踪、生成类型及CI。
- 按唯一契约实现业务模块与适配器；未定业务参数保持可配置及缺项拒绝，不放行正式业务动作。
- 使用自建无敏感夹具和隔离环境开发接口、数据库迁移、权限/事件处理及相应测试。

| 开发范围/门槛 | 当前判断 | 执行条件 |
| --- | --- | --- |
| DEV-FOUNDATION | READY_WITH_DEFINED_SCOPE | 现有框架/锁/契约和代表性工程证据支持基础开发；按具体任务子范围实施。 |
| DEV-DISK | SNAPSHOT_OBSERVED_RECHECK_BEFORE_HEAVY_WORK | 容量及采样时间读取最新同步回执与资源报告；当前5GiB仅为研发操作保护，每次重操作前实时核验。历史容量不足不当当前状态；实际配额、维护与正式恢复另验。<br>[server-sync-receipt.json](<../00-project/server-sync-receipt.json>)、[resource-readiness-snapshot.json](<../00-project/validation/resource-readiness-snapshot.json>) |
| DEV-CONTRACT | PER_TASK_GAPS_MUST_CLOSE | 13整体接口缺口、62表访问迁移及完整DAG依对应任务先补契约/绑定/实现，不自动当全部完成。 |
| DEV-REAL-INPUTS | WAIT_ACTUAL_INPUTS_AND_IMPLEMENTATION | 正式身份、授权数据/真实权重、GPU/驱动、实际规模/并发、人员和资源需真实材料；模拟身份/合成CPU只作研发。 |
| DEV-PRODUCTION | NOT_READY_NOT_FROZEN | 生产Python按TB-ADR-002逐候选验证/重锁/全CI与准入；3.10例外需实际补丁维护和有效决定。WORM/审批/保留、PITR/密钥/异机恢复、许可扫描及治理仍须实施验证后正式冻结/启用。<br>[TB-ADR-002-backend-stack.md](<architecture-decisions/TB-ADR-002-backend-stack.md>)、[versions.yaml](<../../config/versions.yaml>)、[stage-two-external-inputs.json](<../03-development/stage-two-external-inputs.json>) |

每个任务开始前检查：

- 任务输入/执行依赖和源工时差异已读；明确本次子范围和未实现部分。
- 接口、SQL/字典/映射及运行身份在唯一来源间一致；缺项登记并先补本次所需契约。
- 测试使用自建或具备本次用途授权的输入；不能用Mock/结构通过代替真实业务效果。
- 任何正式动作仍核验有效身份、案件范围、规则/批准及输入用途；未知默认拒绝。
- 开始大体积服务器构建/镜像/素材写入前重新采集容量并通过候选容量检查。

现有输入对开发的帮助：统一[接口结构](<../03-api/openapi.yaml>)、[字段来源](<../04-database/field-provenance.json>)和[持久化投影](<../04-database/api-field-mapping.json>)；用[任务卡](<../../tasks/README.md>)明确输入/依赖/子范围，用生成类型与CI发现漂移。它们减少重复定义和字段/版本错配，不替代真实业务规则或数据授权。

### 阅读顺序

1. 整体接口说明→逐操作目录→OpenAPI/模型Schema→字段与权限/版本/事件规则。
2. 数据库设计→ER→字典/SQL→逐字段来源→接口映射→任务引用/校验。
3. 实际PoC API/5表与迁移→相应运行证据，再核对13接口缺口和后续业务迁移/RLS。

### 整体接口及契约文件

| 内容 | 文件入口 | 含义和使用要求 |
| --- | --- | --- |
| 剩余接口实际实现 | [11类缺口实际子范围](<../03-development/stage-three/remaining-interface-implementation.md>) | 审批/复核/审计/配置及适配、任务控制和内部协议的真实代码、验证与正式接入边界。 |
| 整体接口范围 | [系统整体接口说明](<../03-api/system-interface-specification.md>) | 七类接口面、73业务操作/102组件/34能力、服务边界和完整性要求。 |
| 逐操作/模块目录 | [73操作与12模块导航](<../03-api/detailed-interface-index.md>) | 跳转每个操作的参数、请求/响应、权限、版本、异步终态、样例和任务引用。 |
| 业务结构唯一源 | [业务OpenAPI](<../03-api/openapi.yaml>) | 外部接口结构源；候选73操作，不代表全部已实现。 |
| 内部调用入口唯一源 | [内部推理OpenAPI](<../03-api/inference-openapi.yaml>) | 内部调用入口；能力请求/响应结构以schemas/model为源。 |
| 业务字段说明 | [102组件字段说明](<../03-api/data-structures.md>) | 必填/可空/枚举/约束及完整Schema的只读派生。 |
| 内部能力字段 | [34能力接口说明](<../03-api/inference-interfaces.md>) | 能力路径/请求/响应/身份/来源摘要；业务模型未据此验收。 |
| 能力Schema源 | [68模型Schema](<../../schemas/model>) | 34请求+34响应的唯一能力结构来源；不作为业务HTTP的第二结构源。 |
| 共用行为 | [接口共用规则](<../03-api/common-interface-rules.md>) | 鉴权、追踪、分页、幂等、ETag、版本、异步、错误及Range。 |
| 服务与事件 | [服务/事件契约](<../03-api/service-and-event-contracts.md>) | 边界及研发事件；完整业务调度实施另判。 |
| 工作流/结果事件 | [工作流契约](<../05-workflows/workflow-contracts.md>) | 候选DAG、节点结果、7类域事件和运行版本身份。 |
| 严格历史读取 | [历史结果读取](<../03-api/historical-result-reading.md>) | 7现有操作的精确task/run/result选择与不回退最新规则，所选历史读取已实测；完整业务生产器及正式接入另判。 |
| 接口缺口 | [13项接口缺口](<../03-api/interface-gap-register.md>) | 正式条件与技术子范围分别登记；已挂载路径按逐操作实测，其余候选路径不可调用。 |
| 接口追踪 | [接口来源索引](<../03-api/interface-catalog.json>) | 操作/模块/能力的来源和任务/测试引用，非运行证明。 |
| 样例 | [请求响应样例](<../03-api/examples>) | 结构校验夹具，不能充当实际业务结果。 |
| 生成类型 | [4份生成类型](<../../shared-contracts/generated>) | 由唯一来源生成，禁止反向手改Schema；结构约束仍需运行验证。 |
| 已运行研发API | [PoC接口及范围](<../03-api/poc-api.md>) | 固定测试案件/图片上传/任务/合成CPU入口，与73操作设计分开。 |

### 业务数据库及研发迁移文件

| 内容 | 文件入口 | 含义和使用要求 |
| --- | --- | --- |
| 业务设计与关系 | [数据库设计](<../04-database/database-design.md>) | 62表候选职责、身份与关系，业务访问层尚未全部实施。 |
| 业务字段字典 | [62表/825字段字典](<../04-database/data-dictionary.md>) | 逐字段类型、空值、约束和来源；不从一句来源契约推导已确认业务规则。 |
| 空库DDL唯一源 | [初始化SQL](<../04-database/initial-schema.sql>) | 用于新隔离空库；不得当既有数据库增量升级脚本。 |
| ER关系 | [ER图](<../04-database/er-diagram.md>) | 结合复合外键、案件范围及设计阅读；关系图不是部署证明。 |
| 表/字段机器目录 | [表目录](<../04-database/table-catalog.json>) | 62表825字段的可检查结构，须与SQL/字典一致。 |
| 逐字段来源 | [字段来源契约](<../04-database/field-provenance.json>) | 精确源文件/指针与来源性质；说明cluster_id、asset_id、rank等依据。 |
| 接口字段投影 | [接口—数据库映射说明](<../04-database/api-field-mapping.md>) | 区分请求/响应、列投影和运行时组合，不以同名认定同一对象。 |
| 映射机器源 | [接口字段映射JSON](<../04-database/api-field-mapping.json>) | 配合CSV查看精确结构引用和列/投影关系。 |
| 映射表格 | [接口字段映射CSV](<../04-database/api-field-mapping.csv>) | 便于逐字段对照；同步JSON/SQL/Schema，不能独立成为第二定义源。 |
| 表与任务 | [62表任务引用](<../04-database/table-task-usage.md>) | 候选职责、源追踪与任务卡引用；不代表已被实际代码使用。 |
| 首发排序规则 | [首发候选排序](<../04-database/first-source-ranking.md>) | cluster/asset关系、1—3名次、去重、并列/未知和观察范围。 |
| 数据库检查 | [SQL验证范围与命令](<../04-database/database-validation.md>) | 空库/约束/反例测试，不当所有业务访问层或生产升级通过。 |
| 实际研发库 | [研发5表说明](<../04-database/poc-database.md>) | 实际PoC assets/jobs/outbox/audit/迁移账本，区别于62表业务设计。 |
| 已运行研发迁移 | [PoC版本迁移](<../../backend/migrations>) | 0001/0002仅针对开发库；正式62表迁移仍需按任务实施。 |
| 迁移/事件机制 | [迁移与旧租约保护](<../03-development/migrations-and-events.md>) | 版本账本、摘要、事件/追踪与租约fencing；非生产RLS完整部署。 |
| 隔离权限原型 | [RLS/历史追加原型](<../04-database/authorization-isolation-prototype.md>) | 代表性临时库验证；正式身份、全业务表和特权防篡改未因此完成。 |

### 相互对应与实际状态

API字段须按[字段投影](<../04-database/api-field-mapping.json>)定位数据库列/运行组合，再用[字段来源](<../04-database/field-provenance.json>)核对来源文件/指针；模型结构不与业务HTTP结构混为一份。SQL/字典/Schema/映射/生成类型变化须同步。

cluster_id、asset_id、rank等字段的来源契约是逐字段可追踪的结构/设计依据，不能靠“见来源契约”一句作为实际约束说明。请联合阅读字典、field-provenance、映射和首发排序规范。

73业务操作/102组件/34能力、62表825字段是当前候选设计；PoC和代表性隔离实验有独立证据，完整业务API/62表访问迁移/RLS未全部实现。13项正式条件仍开放；新增业务接口/约束迁移的实际子范围见剩余接口实现说明，初始化SQL不得直接作用于既有库。状态见[第二阶段23步实际状态](<../03-development/stage-two-readiness.md>)、[12项补齐与剩余](<../03-development/stage-two-completion-matrix.md>)和[两阶段总导航](<../00-project/remaining-work-navigation.md>)。

证据：[interface-documentation-report.json](<../00-project/validation/interface-documentation-report.json>)、[database-contract-report.json](<../00-project/validation/database-contract-report.json>)、[database-foundation-report.json](<../00-project/validation/database-foundation-report.json>)、[migration-fencing-report.json](<../00-project/validation/migration-fencing-report.json>)、[stage-two-isolation-report.json](<../00-project/validation/stage-two-isolation-report.json>)。检查通过范围与实际业务验收分别判断。
<!-- phase-contract-file-navigation:end -->

当前开发补充：独立业务工程已实现62表版本迁移/RLS基础、5项上传、7项历史读取及本批控制接口技术子范围，42个外部和1个内部入口；PoC5表保持独立。具体实际状态与正式前置条件见[本批说明](../03-development/stage-three/remaining-interface-implementation.md)。早期“未实施”说明只对应当时批次，不能覆盖本批已验证实现；完整业务与生产验收仍未完成。
