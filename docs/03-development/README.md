# 开发、契约与CI

- [T013自建Keycloak身份系统完整设计](t013-keycloak-identity-design.md)、[8步实施计划](t013-keycloak-implementation-plan.md)、[实际执行状态](../00-project/validation/t013-keycloak-execution-report.json)、[22项状态登记](../00-project/validation/t013-keycloak-acceptance-ledger.json)：步骤1—6研发验证通过，步骤7隔离恢复演练通过，步骤8源码及1,501项文件清单已同步；22项中13项范围内通过、9项未执行。GitHub集成创建PR返回403，托管CI、正式准入和身份交接仍未完成。T013整卡未关闭。
- [T013令牌核验与身份映射首批实现](t013-token-validation.md)：可选远端核验、最小权限数据库查询、禁用/到期/撤销测试及未完成的正式身份接入范围。

2026-10-13更新；CPU研发工程已验证，正式基线NOT_FROZEN。

直接入口：[接口与数据库文件导航](../02-architecture/technical-baseline.md#接口与数据库文件导航)、[系统整体接口](../03-api/README.md)、[业务数据库](../04-database/README.md)、[第一阶段24步实际状态](../00-project/stage-one/steps-and-deliverables.md)。整体业务契约/62表与实际PoC/5表分开阅读。

- [第二阶段23步状态](stage-two-readiness.md)：逐项事实、边界和待办。
- [第三阶段16步](stage-three/readiness.md)、[实际验证报告](development-environment-validation-report.md)、[开发环境基线候选](development-environment-baseline.md)。
- [工程入口](repository-bootstrap.md)、[编码规则](coding-standards.md)。
- [CI实际门禁](ci-cd.md)、[生成类型与消息约定](contract-generation.md)。
- [运行手册](../10-deployment/development-runbook.md)、[验证报告](../02-architecture/technical-validation-report.md)。

现有工程包含[迁移/事件/租约机制](migrations-and-events.md)、代表性隔离权限/中文查询、VFR媒体及镜像OS物料验证；CI工程门禁的实际结果见[CI说明](ci-cd.md)与平台报告。[交付对照](stage-two-completion-matrix.md)、[实施计划](stage-two-implementation-plan.md)和[实际输入](stage-two-external-inputs.json)已纳入23步状态，剩余条件见[关闭标准](stage-two-gap-register.md)。

基础框架完成不等于全部170任务实现；从任务卡核验具体输入、权限、依赖和验收，新增业务应执行其专用验证。

<!-- phase-remaining-navigation:start -->
## 第一、第二阶段剩余工作总导航

第一阶段24步、第二阶段23步与170业务任务分别管理。核查19项工作：版式核验在记录范围内已完成；剩余18项，包括第一阶段6项、第二阶段12项。工程补充、实际输入、实现/联调、正式验收与冻结分别判断。13接口缺口与这些事项交叉，不能相加计算完成率。真实人员/责任人尚未全部确认，10人占位排期只作假设；已确认的任务负责人按实际输入和任务卡登记。

容量问题位于Linux服务器172.16.58.179的Docker Desktop虚拟机内，为PostgreSQL研发数据卷所在文件系统。仓库快照时点`2026-10-14T13:24:30.139139+00:00`：df使用率13%，可用约644.42 GiB。不是本地Windows D盘或GitHub容量，也不代表Linux宿主/workspace全部空间不足。容量已高于5GiB研发构建保护值；扩容不是本会话执行，维护/整盘备份及正式恢复仍未核验。

完整逐项导航：[剩余任务、前置条件、关闭标准及13接口缺口](<../00-project/remaining-work-navigation.md>)；[同源机器索引](<../00-project/remaining-work-navigation.json>)。

### 第1阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S1-N02 / P0<br>步1,2,23<br>项目/业务/文档管理（实际姓名待定） | 来源身份、版本优先级与变更权责<br>待落实实际条件及对应交付 | 确认正式权威版本、适用范围、V2/V1.0身份冲突处置及实际变更责任人；唯一工程来源规则已完成。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s1-n02>)<br>[source-document-inventory.md](<../00-project/source-document-inventory.md>)、[document-conversion-plan.md](<../00-project/document-conversion-plan.md>) |
| S1-N03 / P0<br>步4,6,10,11<br>业务/安全/架构（实际姓名待定） | 术语、业务规则与状态参数细化<br>待落实实际条件及对应交付 | 确定风险/人工阈值、RETURNED后继、首发未知、审批目的与回流/保留规则的适用参数和例外。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s1-n03>)<br>[glossary.md](<../00-project/glossary.md>)、[task-state-machine.md](<../05-workflows/task-state-machine.md>) |
| S1-N04 / P0<br>步7,8,12,14,19,21<br>架构/前后端/算法/测试（实际姓名待定） | 需求到内部处理与结果读取的语义闭环<br>待落实实际条件及对应交付 | 13项契约缺口和真实业务实现/联调按对应任务继续；正式规则需实际依据。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s1-n04>)<br>[requirement-processing-map.md](<../00-project/requirement-processing-map.md>)、[source-section-map.md](<../00-project/stage-one/source-section-map.md>) |
| S1-N05 / P0<br>步9,18<br>业务验收/测试/算法/运维（实际姓名待定） | 可执行的指标和验收测量协议<br>待落实实际条件及对应交付 | 补真实封存样本/分层数量、正式目标、负载/资源/版本，实施对应真实验收。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s1-n05>)<br>[non-functional-requirements.md](<../01-requirements/non-functional-requirements.md>)、[acceptance-criteria.md](<../09-testing/acceptance-criteria.md>) |
| S1-N06 / P0<br>步15<br>数据/业务授权/算法（实际姓名待定） | 数据集计数、标签和可用输入清单<br>待落实实际条件及对应交付 | 落实来源/用途材料、标签版本/质检、原件与派生/内容簇计数及独立封存集规则；盘点实际可用样本。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s1-n06>)<br>[dataset-catalog.md](<../07-datasets/dataset-catalog.md>)、[annotation-specification.md](<../07-datasets/annotation-specification.md>) |
| S1-N07 / P0<br>步17,19,23<br>项目计划/各研发负责人（实际姓名待定） | 人员投入、实际进度和分期执行台账<br>待落实实际条件及对应交付 | 实际人员/投入、剩余工时、计划起点/工作日历和数据/GPU到位日未提供，实际日历排期待补。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s1-n07>)<br>[backlog.yaml](<../../tasks/backlog.yaml>)、[dependency-report.md](<../../tasks/dependency-report.md>) |

### 第2阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S2-N01 / P0<br>步19<br>架构/前后端/算法/测试（实际姓名待定） | 整体接口流程和必要服务契约<br>待落实实际条件及对应交付 | 其余业务操作和真实身份/来源/审批规则等正式接入仍需实施验证；已有子范围不重记为未实现，也不据此关闭全部13项正式缺口。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n01>)<br>[interface-gap-register.md](<../03-api/interface-gap-register.md>)、[contract-generation.md](<contract-generation.md>) |
| S2-N02 / P0<br>步7<br>数据库/后端/安全（实际姓名待定） | 业务数据库访问层与升级迁移<br>待落实实际条件及对应交付 | 按剩余任务补齐所有业务访问和逐表场景、生产升级/回退/特权边界验证；初始化SQL不能代替实际迁移，也不把现有隔离验证当正式生产部署。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n02>)<br>[database-design.md](<../04-database/database-design.md>)、[poc-database.md](<../04-database/poc-database.md>) |
| S2-N03 / P0<br>步9,19,20<br>后端/算法/测试（实际姓名待定） | 完整任务编排、取消与多worker故障<br>待落实实际条件及对应交付 | 实施实际调度器与多worker消息故障演练；当前8数据库竞争者不是8Celery worker，全业务DAG未运行。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n03>)<br>[task-state-machine.md](<../05-workflows/task-state-machine.md>)、[migrations-and-events.md](<migrations-and-events.md>) |
| S2-N04 / P0<br>步15<br>身份平台/业务安全/后端（实际姓名待定） | 正式身份与案件/单位隔离<br>待落实实际条件及对应交付 | 提供真实issuer/密钥或获准身份协议及用户/单位/案件映射，再验证签验、撤销、用途及正式权限策略。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n04>)<br>[security-baseline.md](<../02-architecture/security-baseline.md>)、[permission-matrix.md](<../08-security/permission-matrix.md>) |
| S2-N05 / P0<br>步1,2,8,16<br>Linux及Docker运维/资源管理（实际姓名待定） | 项目配额与研发数据卷容量<br>待落实实际条件及对应交付 | 补实际扩容维护/整盘备份与恢复记录、项目独占配额和维护人；数据/权重/GPU授权及正式资源验收仍需落实。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n05>)<br>[resource-readiness-snapshot.json](<../00-project/validation/resource-readiness-snapshot.json>)、[resource-and-team-inventory.md](<../02-architecture/resource-and-team-inventory.md>) |
| S2-N06 / P0<br>步12,13<br>数据/算法/GPU运维（实际姓名待定） | 业务模型、OCR/ASR及GPU验证<br>待落实实际条件及对应交付 | 提供有用途授权的数据目录、权重许可/来源/摘要、实际GPU与驱动，实施逐能力训练/推理和独立封存盲测；M15合成CPU不代替业务能力。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n06>)<br>[model-catalog.yaml](<../06-algorithms/model-catalog.yaml>)、[model-evaluation.md](<../06-algorithms/model-evaluation.md>) |
| S2-N07 / P1<br>步14<br>媒体/算法/后端/测试（实际姓名待定） | 真实媒体、VFR和全时间轴链路<br>待落实实际条件及对应交付 | 实际授权媒体的多编码/VFR/缺模态/裁剪/转码链路及OCR/ASR、长视频性能仍需实现和实测；本轮仅自建夹具。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n07>)<br>[media-timestamp-report.json](<../00-project/validation/media-timestamp-report.json>)、[TB-ADR-010-media-processing.md](<../02-architecture/architecture-decisions/TB-ADR-010-media-processing.md>) |
| S2-N08 / P1<br>步10,11<br>检索/算法/后端/测试（实际姓名待定） | 中文/规模化检索与传播图验证<br>待落实实际条件及对应交付 | 确定正式中文分词/排序选型，实施实际大索引/向量及传播图业务、授权过滤和规模性能；4条文本不是业务检索指标。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n08>)<br>[technical-validation-report.md](<../02-architecture/technical-validation-report.md>)、[media-query-report.json](<../00-project/validation/media-query-report.json>) |
| S2-N09 / P0<br>步8,15<br>业务审核/安全/后端/存储（实际姓名待定） | 正式安全与证据防篡改机制<br>待落实实际条件及对应交付 | 落实双人审批适用规则、可信时间/签名、保留期、WORM/密钥及管理员边界，实施下载每次授权核验和到期/撤销演练。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n09>)<br>[security-baseline.md](<../02-architecture/security-baseline.md>)、[audit-requirements.md](<../08-security/audit-requirements.md>) |
| S2-N10 / P1<br>步8,16<br>运维/数据库/安全/测试（实际姓名待定） | 生产灾备、PITR和密钥恢复<br>待落实实际条件及对应交付 | 提供真实异地目标和密钥恢复授权、批准RPO/RTO；实施全业务异机恢复及对账，不能用开发冷备结果证明生产灾备。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n10>)<br>[development-backup-restore.md](<../10-deployment/development-backup-restore.md>)、[development-recovery-report.json](<../00-project/validation/development-recovery-report.json>) |
| S2-N11 / P0<br>步1,17<br>技术/软件准入/许可审查/安全（实际姓名待定） | 支持版本、OS物料和离线交付<br>待落实实际条件及对应交付 | 按TB-ADR-002验证3.13主候选/3.12备选或有实际维护依据的3.10例外，落实精确生产Python/OS、依赖/模型/CPU-GPU兼容、新锁/全CI与准入决定；补未托管二进制/FFmpeg源码与notices、模型许可、漏洞扫描及离线交付；未自动安装或升级当前环境。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n11>)<br>[environment-constraints.md](<../02-architecture/environment-constraints.md>)、[licenses.md](<../02-architecture/licenses.md>) |
| S2-N12 / P1<br>步21,22,23<br>仓库管理/构建发布/安全（实际姓名待定） | CI组织治理与受控制品交付<br>待落实实际条件及对应交付 | 落实私有仓库保护功能套餐/管理员配置、签名与离线镜像库/依赖缓存/保留策略；运行中镜像缺失须先重新构建验真再导出。 | [前置条件、全部证据及关闭标准](<../00-project/remaining-work-navigation.md#s2-n12>)<br>[repository-governance-snapshot.json](<../00-project/validation/repository-governance-snapshot.json>)、[ci-cd.md](<ci-cd.md>) |

已完成的S1-N01版式核验及19项全部已有证据在总导航保留，避免重新列为未开展。正式输入冻结（第一阶段22—24步）和技术冻结（第二阶段22—23步）仍NOT_FROZEN，实际决定/责任人及适用范围需落实。

资源/身份/授权数据和实际责任人填写[实际输入表](<stage-two-external-inputs.json>)；人员/实际排期填写[人员排期输入](<../00-project/execution-planning-inputs.json>)。170业务任务后续按[实施计划](<stage-two-implementation-plan.md>)推进。
<!-- phase-remaining-navigation:end -->

## 第一阶段资料入口

[第一阶段24步、来源和材料](../00-project/stage-one/README.md)记录输入整理做法；与第二阶段23步、根170研发任务分开。当前两阶段的正式冻结都未完成。

## 审批之外还需完成什么

[两阶段19项工作核查](../00-project/phase-readiness-register.md)列明当前证据、缺失工作、关闭标准和后续业务交付边界；版式核验在记录范围内已完成，剩余第一阶段6项、第二阶段12项仍有实际条件。优先落实资源/存储、关键接口和处理/结果关联、规则/指标/排期；完整业务研发及生产级安全/灾备/容量按适用任务推进。

[36需求处理与读取映射](../00-project/requirement-processing-map.md)为候选设计；[最新资源快照](../00-project/validation/resource-readiness-snapshot.json)和[仓库治理快照](../00-project/validation/repository-governance-snapshot.json)是时点观测，不等于配额或治理验收。
