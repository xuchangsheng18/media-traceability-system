# 第一阶段开发输入材料

2026-10-13更新；候选输入已整理并通过结构与相关隔离SQL检查，正式输入基线仍NOT_FROZEN。第一阶段是将本地设计、任务、算法/数据、模型与原型材料转为开发可用的依据；第二阶段是选择和验证实际技术组合。两阶段分别判断，不能因第二阶段PoC/CI通过，就补造第一阶段签认。

现有[24步状态、操作与交付表](steps-and-deliverables.md)已更新，逐步列实际产物、技术状态、待办/边界和正式状态；机器状态直接维护在[deliverables.json](deliverables.json)，不再保留重复展示页。

- [24步操作与交付物](steps-and-deliverables.md)：原步骤、具体做法、实际文件、当前状态与限制。
- [机器交付清单](deliverables.json)：24步文件引用和明确未冻结状态。
- [第一阶段到第二阶段的衔接](handoff.md)：哪些资料被实际工程消费、哪些条件仍待确认。
- [资料导入清单](materials-manifest.json)：14份本地历史资料的来源路径、原始字节摘要和归档身份。
- [历史材料导航](history/README.md)：先核对历史范围再阅读旧核查结论。
- [材料核验记录](../validation/stage-one-validation-report.json)：路径、来源摘要、步骤、表/任务引用与状态检查，不代替业务验收。

<!-- phase-remaining-navigation:start -->
## 第一、第二阶段剩余工作总导航

第一阶段24步、第二阶段23步与170业务任务分别管理。核查19项工作：版式核验在记录范围内已完成；剩余18项，包括第一阶段6项、第二阶段12项。工程补充、实际输入、实现/联调、正式验收与冻结分别判断。13接口缺口与这些事项交叉，不能相加计算完成率。真实人员/责任人未确认，10人占位排期只作假设。

容量问题位于Linux服务器172.16.58.179的Docker Desktop虚拟机内，为PostgreSQL研发数据卷所在文件系统。仓库快照时点`2026-10-13T09:34:20.877814+00:00`：df使用率99%，可用约1.62 GiB。不是本地Windows D盘或GitHub容量，也不代表Linux宿主/workspace全部空间不足；尚未记录扩容完成。

完整逐项导航：[剩余任务、前置条件、关闭标准及13接口缺口](<../remaining-work-navigation.md>)；[同源机器索引](<../remaining-work-navigation.json>)。

### 第1阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S1-N02 / P0<br>步1,2,23<br>项目/业务/文档管理（实际姓名待定） | 来源身份、版本优先级与变更权责<br>待落实实际条件及对应交付 | 确认正式权威版本、适用范围、V2/V1.0身份冲突处置及实际变更责任人；唯一工程来源规则已完成。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s1-n02>)<br>[source-document-inventory.md](<../source-document-inventory.md>)、[document-conversion-plan.md](<../document-conversion-plan.md>) |
| S1-N03 / P0<br>步4,6,10,11<br>业务/安全/架构（实际姓名待定） | 术语、业务规则与状态参数细化<br>待落实实际条件及对应交付 | 确定风险/人工阈值、RETURNED后继、首发未知、审批目的与回流/保留规则的适用参数和例外。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s1-n03>)<br>[glossary.md](<../glossary.md>)、[task-state-machine.md](<../../05-workflows/task-state-machine.md>) |
| S1-N04 / P0<br>步7,8,12,14,19,21<br>架构/前后端/算法/测试（实际姓名待定） | 需求到内部处理与结果读取的语义闭环<br>待落实实际条件及对应交付 | 13项契约缺口和真实业务实现/联调按对应任务继续；正式规则需实际依据。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s1-n04>)<br>[requirement-processing-map.md](<../requirement-processing-map.md>)、[source-section-map.md](<source-section-map.md>) |
| S1-N05 / P0<br>步9,18<br>业务验收/测试/算法/运维（实际姓名待定） | 可执行的指标和验收测量协议<br>待落实实际条件及对应交付 | 补真实封存样本/分层数量、正式目标、负载/资源/版本，实施对应真实验收。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s1-n05>)<br>[non-functional-requirements.md](<../../01-requirements/non-functional-requirements.md>)、[acceptance-criteria.md](<../../09-testing/acceptance-criteria.md>) |
| S1-N06 / P0<br>步15<br>数据/业务授权/算法（实际姓名待定） | 数据集计数、标签和可用输入清单<br>待落实实际条件及对应交付 | 落实来源/用途材料、标签版本/质检、原件与派生/内容簇计数及独立封存集规则；盘点实际可用样本。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s1-n06>)<br>[dataset-catalog.md](<../../07-datasets/dataset-catalog.md>)、[annotation-specification.md](<../../07-datasets/annotation-specification.md>) |
| S1-N07 / P0<br>步17,19,23<br>项目计划/各研发负责人（实际姓名待定） | 人员投入、实际进度和分期执行台账<br>待落实实际条件及对应交付 | 实际人员/投入、剩余工时、计划起点/工作日历和数据/GPU到位日未提供，实际日历排期待补。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s1-n07>)<br>[backlog.yaml](<../../../tasks/backlog.yaml>)、[dependency-report.md](<../../../tasks/dependency-report.md>) |

### 第2阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S2-N01 / P0<br>步19<br>架构/前后端/算法/测试（实际姓名待定） | 整体接口流程和必要服务契约<br>待落实实际条件及对应交付 | 补上传、审批、复核、反馈、发布、导出状态读取的唯一源契约/映射/样例/生成类型与业务联调；身份/来源平台协议需实际资料。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n01>)<br>[interface-gap-register.md](<../../03-api/interface-gap-register.md>)、[contract-generation.md](<../../03-development/contract-generation.md>) |
| S2-N02 / P0<br>步7<br>数据库/后端/安全（实际姓名待定） | 业务数据库访问层与升级迁移<br>待落实实际条件及对应交付 | 按任务卡实现62表业务访问和版本迁移，逐表建立RLS/关联隔离与升级回退；不能将代表性两表套用为62表全部部署。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n02>)<br>[database-design.md](<../../04-database/database-design.md>)、[poc-database.md](<../../04-database/poc-database.md>) |
| S2-N03 / P0<br>步9,19,20<br>后端/算法/测试（实际姓名待定） | 完整任务编排、取消与多worker故障<br>待落实实际条件及对应交付 | 实施实际调度器与多worker消息故障演练；当前8数据库竞争者不是8Celery worker，全业务DAG未运行。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n03>)<br>[task-state-machine.md](<../../05-workflows/task-state-machine.md>)、[migrations-and-events.md](<../../03-development/migrations-and-events.md>) |
| S2-N04 / P0<br>步15<br>身份平台/业务安全/后端（实际姓名待定） | 正式身份与案件/单位隔离<br>待落实实际条件及对应交付 | 取得身份issuer/JWKS或其他正式协议、角色/单位/案件权威映射和撤销SLA，实施验证后联调；共享DB设置不能充当身份认证。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n04>)<br>[security-baseline.md](<../../02-architecture/security-baseline.md>)、[permission-matrix.md](<../../08-security/permission-matrix.md>) |
| S2-N05 / P0<br>步1,2,8,16<br>Linux及Docker运维/资源管理（实际姓名待定） | 项目配额与研发数据卷容量<br>待落实实际条件及对应交付 | 落实Docker虚拟机数据盘扩容或经批准迁移，独占资源配额、维护人、权重/样本容量和GPU权限；完成后重新读取卷内df。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n05>)<br>[resource-readiness-snapshot.json](<../validation/resource-readiness-snapshot.json>)、[resource-and-team-inventory.md](<../../02-architecture/resource-and-team-inventory.md>) |
| S2-N06 / P0<br>步12,13<br>数据/算法/GPU运维（实际姓名待定） | 业务模型、OCR/ASR及GPU验证<br>待落实实际条件及对应交付 | 提供有用途授权的数据目录、权重许可/来源/摘要、实际GPU与驱动，实施逐能力训练/推理和独立封存盲测；M15合成CPU不代替业务能力。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n06>)<br>[model-catalog.yaml](<../../06-algorithms/model-catalog.yaml>)、[model-evaluation.md](<../../06-algorithms/model-evaluation.md>) |
| S2-N07 / P1<br>步14<br>媒体/算法/后端/测试（实际姓名待定） | 真实媒体、VFR和全时间轴链路<br>待落实实际条件及对应交付 | 实际授权媒体的多编码/VFR/缺模态/裁剪/转码链路及OCR/ASR、长视频性能仍需实现和实测；本轮仅自建夹具。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n07>)<br>[media-timestamp-report.json](<../validation/media-timestamp-report.json>)、[TB-ADR-010-media-processing.md](<../../02-architecture/architecture-decisions/TB-ADR-010-media-processing.md>) |
| S2-N08 / P1<br>步10,11<br>检索/算法/后端/测试（实际姓名待定） | 中文/规模化检索与传播图验证<br>待落实实际条件及对应交付 | 确定正式中文分词/排序选型，实施实际大索引/向量及传播图业务、授权过滤和规模性能；4条文本不是业务检索指标。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n08>)<br>[technical-validation-report.md](<../../02-architecture/technical-validation-report.md>)、[media-query-report.json](<../validation/media-query-report.json>) |
| S2-N09 / P0<br>步8,15<br>业务审核/安全/后端/存储（实际姓名待定） | 正式安全与证据防篡改机制<br>待落实实际条件及对应交付 | 落实双人审批适用规则、可信时间/签名、保留期、WORM/密钥及管理员边界，实施下载每次授权核验和到期/撤销演练。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n09>)<br>[security-baseline.md](<../../02-architecture/security-baseline.md>)、[audit-requirements.md](<../../08-security/audit-requirements.md>) |
| S2-N10 / P1<br>步8,16<br>运维/数据库/安全/测试（实际姓名待定） | 生产灾备、PITR和密钥恢复<br>待落实实际条件及对应交付 | 提供真实异地目标和密钥恢复授权、批准RPO/RTO；实施全业务异机恢复及对账，不能用开发冷备结果证明生产灾备。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n10>)<br>[development-backup-restore.md](<../../10-deployment/development-backup-restore.md>)、[development-recovery-report.json](<../validation/development-recovery-report.json>) |
| S2-N11 / P0<br>步1,17<br>技术/软件准入/许可审查/安全（实际姓名待定） | 支持版本、OS物料和离线交付<br>待落实实际条件及对应交付 | 按TB-ADR-002验证3.13主候选/3.12备选或有实际维护依据的3.10例外，落实精确生产Python/OS、依赖/模型/CPU-GPU兼容、新锁/全CI与准入决定；补未托管二进制/FFmpeg源码与notices、模型许可、漏洞扫描及离线交付；未自动安装或升级当前环境。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n11>)<br>[environment-constraints.md](<../../02-architecture/environment-constraints.md>)、[licenses.md](<../../02-architecture/licenses.md>) |
| S2-N12 / P1<br>步21,22,23<br>仓库管理/构建发布/安全（实际姓名待定） | CI组织治理与受控制品交付<br>待落实实际条件及对应交付 | 落实私有仓库保护功能套餐/管理员配置、签名与离线镜像库/依赖缓存/保留策略；运行中镜像缺失须先重新构建验真再导出。 | [前置条件、全部证据及关闭标准](<../remaining-work-navigation.md#s2-n12>)<br>[repository-governance-snapshot.json](<../validation/repository-governance-snapshot.json>)、[ci-cd.md](<../../03-development/ci-cd.md>) |

已完成的S1-N01版式核验及19项全部已有证据在总导航保留，避免重新列为未开展。正式输入冻结（第一阶段22—24步）和技术冻结（第二阶段22—23步）仍NOT_FROZEN，实际决定/责任人及适用范围需落实。

资源/身份/授权数据和实际责任人填写[实际输入表](<../../03-development/stage-two-external-inputs.json>)；人员/实际排期填写[人员排期输入](<../execution-planning-inputs.json>)。170业务任务后续按[实施计划](<../../03-development/stage-two-implementation-plan.md>)推进。
<!-- phase-remaining-navigation:end -->

## 本地资料如何进入仓库

| 本地依据 | 仓库落点 | 使用要求 |
| --- | --- | --- |
| 五类原始业务资料 | [docs/source/original](../../source/original/) | 原件不覆盖，正式依据身份与适用业务范围仍须确认 |
| 总体设计V1.4和任务书V1.3 | [docs/source/revisions](../../source/revisions/) | 成对保存，来源摘要见source-inventory.json；不把评审稿当批准版 |
| 第一/第二阶段三份手册 | [docs/guides](../../guides/README.md) | 流程来源，第一阶段24步、第二阶段23步，不等同170任务 |
| 正文、表格、原型检索转换 | [docs/_converted](../../_converted/) | 以原件校对复杂表图，文字转换不保证视觉还原 |
| 第一阶段补齐包和双文档核查记录 | [history](history/README.md) | 按字节归档，历史61表/旧Python/空服务器描述不作为当前状态 |
| 需求、契约、数据、流程、模型、测试 | 各docs专题及根schemas/datasets/tasks | 保持现有唯一来源，通过24步表定位，不另建重复定义 |

## 当前能够确认的数量与范围

原件内容核对、955处来源章节映射、33项评审材料及候选输入摘要已整理，分别见[内容核对](source-content-audit.md)、[来源映射](source-section-map.md)、[评审导航](../review-package/README.md)和[候选摘要](input-baseline-candidate.md)。[版式/语义/测量协议/容量排期记录](four-item-completion.md)与[工程输入控制](remaining-work-completion.md)均已计入24步状态；实际人员、用途授权数据和真实日期仍未确定。

12模块、170条源任务、不少于3类场景保持。当前为36条业务需求＋170条源任务工程展开＋10条非功能要求＝216条追踪记录；不等于216个独立业务功能。正式API53操作、业务设计62表824字段、模型34能力/68Schema、15类数据目录、72业务场景及340任务场景计划。数量用于覆盖检查，不代表全部功能或验收通过。

阶段21的一致性检查与22的评审材料已形成；23仅同步实际收到的选择和已有决定，未补造正式签认；24为NOT_FROZEN检查稿。正式来源、业务/权限/指标及责任方确认按适用范围处理；真实模型/GPU/负载结果不是所有第一阶段文档编制的前提。

## 审批之外的输入缺口

[两阶段工作核查](../phase-readiness-register.md)列第一阶段7项资料/规则/口径/计划工作：版式核验在记录范围内已完成，另6项仍有实际条件；36需求技术语义已逐项复核，真实输入和正式业务规则仍待落实。[36需求处理映射](../requirement-processing-map.md)保留来源任务/内部Schema与候选结果读取，其中七条无直接API绑定的需求保留；候选设计不改主追踪/任务状态，正式规则和运行验证仍开放。
