# 第一、第二阶段剩余工作总导航

第一阶段24步、第二阶段23步与170业务任务分别管理。核查19项工作：版式核验在记录范围内已完成；剩余18项，包括第一阶段6项、第二阶段12项。工程补充、实际输入、实现/联调、正式验收与冻结分别判断。13接口缺口与这些事项交叉，不能相加计算完成率。真实人员/责任人尚未全部确认，10人占位排期只作假设；已确认的任务负责人按实际输入和任务卡登记。

容量问题位于Linux服务器172.16.58.179的Docker Desktop虚拟机内，为PostgreSQL研发数据卷所在文件系统。仓库快照时点`2026-10-14T13:24:30.139139+00:00`：df使用率13%，可用约644.42 GiB。不是本地Windows D盘或GitHub容量，也不代表Linux宿主/workspace全部空间不足。容量已高于5GiB研发构建保护值；扩容不是本会话执行，维护/整盘备份及正式恢复仍未核验。

机器阅读见[remaining-work-navigation.json](<remaining-work-navigation.json>)；工作状态唯一源为[phase-readiness-register.json](<phase-readiness-register.json>)，本文不修改状态或授予权限。

## 第1阶段剩余工作

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S1-N02 / P0<br>步1,2,23<br>项目/业务/文档管理（实际姓名待定） | 来源身份、版本优先级与变更权责<br>待落实实际条件及对应交付 | 确认正式权威版本、适用范围、V2/V1.0身份冲突处置及实际变更责任人；唯一工程来源规则已完成。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s1-n02>)<br>[source-document-inventory.md](<source-document-inventory.md>)、[document-conversion-plan.md](<document-conversion-plan.md>) |
| S1-N03 / P0<br>步4,6,10,11<br>业务/安全/架构（实际姓名待定） | 术语、业务规则与状态参数细化<br>待落实实际条件及对应交付 | 确定风险/人工阈值、RETURNED后继、首发未知、审批目的与回流/保留规则的适用参数和例外。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s1-n03>)<br>[glossary.md](<glossary.md>)、[task-state-machine.md](<../05-workflows/task-state-machine.md>) |
| S1-N04 / P0<br>步7,8,12,14,19,21<br>架构/前后端/算法/测试（实际姓名待定） | 需求到内部处理与结果读取的语义闭环<br>待落实实际条件及对应交付 | 13项契约缺口和真实业务实现/联调按对应任务继续；正式规则需实际依据。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s1-n04>)<br>[requirement-processing-map.md](<requirement-processing-map.md>)、[source-section-map.md](<stage-one/source-section-map.md>) |
| S1-N05 / P0<br>步9,18<br>业务验收/测试/算法/运维（实际姓名待定） | 可执行的指标和验收测量协议<br>待落实实际条件及对应交付 | 补真实封存样本/分层数量、正式目标、负载/资源/版本，实施对应真实验收。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s1-n05>)<br>[non-functional-requirements.md](<../01-requirements/non-functional-requirements.md>)、[acceptance-criteria.md](<../09-testing/acceptance-criteria.md>) |
| S1-N06 / P0<br>步15<br>数据/业务授权/算法（实际姓名待定） | 数据集计数、标签和可用输入清单<br>待落实实际条件及对应交付 | 落实来源/用途材料、标签版本/质检、原件与派生/内容簇计数及独立封存集规则；盘点实际可用样本。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s1-n06>)<br>[dataset-catalog.md](<../07-datasets/dataset-catalog.md>)、[annotation-specification.md](<../07-datasets/annotation-specification.md>) |
| S1-N07 / P0<br>步17,19,23<br>项目计划/各研发负责人（实际姓名待定） | 人员投入、实际进度和分期执行台账<br>待落实实际条件及对应交付 | 实际人员/投入、剩余工时、计划起点/工作日历和数据/GPU到位日未提供，实际日历排期待补。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s1-n07>)<br>[backlog.yaml](<../../tasks/backlog.yaml>)、[dependency-report.md](<../../tasks/dependency-report.md>) |

## 第2阶段剩余工作

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S2-N01 / P0<br>步19<br>架构/前后端/算法/测试（实际姓名待定） | 整体接口流程和必要服务契约<br>待落实实际条件及对应交付 | 其余业务操作和真实身份/来源/审批规则等正式接入仍需实施验证；已有子范围不重记为未实现，也不据此关闭全部13项正式缺口。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n01>)<br>[interface-gap-register.md](<../03-api/interface-gap-register.md>)、[contract-generation.md](<../03-development/contract-generation.md>) |
| S2-N02 / P0<br>步7<br>数据库/后端/安全（实际姓名待定） | 业务数据库访问层与升级迁移<br>待落实实际条件及对应交付 | 按剩余任务补齐所有业务访问和逐表场景、生产升级/回退/特权边界验证；初始化SQL不能代替实际迁移，也不把现有隔离验证当正式生产部署。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n02>)<br>[database-design.md](<../04-database/database-design.md>)、[poc-database.md](<../04-database/poc-database.md>) |
| S2-N03 / P0<br>步9,19,20<br>后端/算法/测试（实际姓名待定） | 完整任务编排、取消与多worker故障<br>待落实实际条件及对应交付 | 实施实际调度器与多worker消息故障演练；当前8数据库竞争者不是8Celery worker，全业务DAG未运行。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n03>)<br>[task-state-machine.md](<../05-workflows/task-state-machine.md>)、[migrations-and-events.md](<../03-development/migrations-and-events.md>) |
| S2-N04 / P0<br>步15<br>身份平台/业务安全/后端（实际姓名待定） | 正式身份与案件/单位隔离<br>待落实实际条件及对应交付 | 提供真实issuer/密钥或获准身份协议及用户/单位/案件映射，再验证签验、撤销、用途及正式权限策略。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n04>)<br>[security-baseline.md](<../02-architecture/security-baseline.md>)、[permission-matrix.md](<../08-security/permission-matrix.md>) |
| S2-N05 / P0<br>步1,2,8,16<br>Linux及Docker运维/资源管理（实际姓名待定） | 项目配额与研发数据卷容量<br>待落实实际条件及对应交付 | 补实际扩容维护/整盘备份与恢复记录、项目独占配额和维护人；数据/权重/GPU授权及正式资源验收仍需落实。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n05>)<br>[resource-readiness-snapshot.json](<validation/resource-readiness-snapshot.json>)、[resource-and-team-inventory.md](<../02-architecture/resource-and-team-inventory.md>) |
| S2-N06 / P0<br>步12,13<br>数据/算法/GPU运维（实际姓名待定） | 业务模型、OCR/ASR及GPU验证<br>待落实实际条件及对应交付 | 提供有用途授权的数据目录、权重许可/来源/摘要、实际GPU与驱动，实施逐能力训练/推理和独立封存盲测；M15合成CPU不代替业务能力。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n06>)<br>[model-catalog.yaml](<../06-algorithms/model-catalog.yaml>)、[model-evaluation.md](<../06-algorithms/model-evaluation.md>) |
| S2-N07 / P1<br>步14<br>媒体/算法/后端/测试（实际姓名待定） | 真实媒体、VFR和全时间轴链路<br>待落实实际条件及对应交付 | 实际授权媒体的多编码/VFR/缺模态/裁剪/转码链路及OCR/ASR、长视频性能仍需实现和实测；本轮仅自建夹具。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n07>)<br>[media-timestamp-report.json](<validation/media-timestamp-report.json>)、[TB-ADR-010-media-processing.md](<../02-architecture/architecture-decisions/TB-ADR-010-media-processing.md>) |
| S2-N08 / P1<br>步10,11<br>检索/算法/后端/测试（实际姓名待定） | 中文/规模化检索与传播图验证<br>待落实实际条件及对应交付 | 确定正式中文分词/排序选型，实施实际大索引/向量及传播图业务、授权过滤和规模性能；4条文本不是业务检索指标。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n08>)<br>[technical-validation-report.md](<../02-architecture/technical-validation-report.md>)、[media-query-report.json](<validation/media-query-report.json>) |
| S2-N09 / P0<br>步8,15<br>业务审核/安全/后端/存储（实际姓名待定） | 正式安全与证据防篡改机制<br>待落实实际条件及对应交付 | 落实双人审批适用规则、可信时间/签名、保留期、WORM/密钥及管理员边界，实施下载每次授权核验和到期/撤销演练。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n09>)<br>[security-baseline.md](<../02-architecture/security-baseline.md>)、[audit-requirements.md](<../08-security/audit-requirements.md>) |
| S2-N10 / P1<br>步8,16<br>运维/数据库/安全/测试（实际姓名待定） | 生产灾备、PITR和密钥恢复<br>待落实实际条件及对应交付 | 提供真实异地目标和密钥恢复授权、批准RPO/RTO；实施全业务异机恢复及对账，不能用开发冷备结果证明生产灾备。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n10>)<br>[development-backup-restore.md](<../10-deployment/development-backup-restore.md>)、[development-recovery-report.json](<validation/development-recovery-report.json>) |
| S2-N11 / P0<br>步1,17<br>技术/软件准入/许可审查/安全（实际姓名待定） | 支持版本、OS物料和离线交付<br>待落实实际条件及对应交付 | 按TB-ADR-002验证3.13主候选/3.12备选或有实际维护依据的3.10例外，落实精确生产Python/OS、依赖/模型/CPU-GPU兼容、新锁/全CI与准入决定；补未托管二进制/FFmpeg源码与notices、模型许可、漏洞扫描及离线交付；未自动安装或升级当前环境。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n11>)<br>[environment-constraints.md](<../02-architecture/environment-constraints.md>)、[licenses.md](<../02-architecture/licenses.md>) |
| S2-N12 / P1<br>步21,22,23<br>仓库管理/构建发布/安全（实际姓名待定） | CI组织治理与受控制品交付<br>待落实实际条件及对应交付 | 落实私有仓库保护功能套餐/管理员配置、签名与离线镜像库/依赖缓存/保留策略；运行中镜像缺失须先重新构建验真再导出。 | [前置条件、全部证据及关闭标准](<remaining-work-navigation.md#s2-n12>)<br>[repository-governance-snapshot.json](<validation/repository-governance-snapshot.json>)、[ci-cd.md](<../03-development/ci-cd.md>) |

## 逐项要求与证据

## S1-N01

**图表、流程图与原型视觉核验**。原阶段1，步骤3，优先级P1。

当前状态：记录范围内已完成。所需责任角色：文档/业务/技术复核，实际姓名未确认。

已有完成范围：10原件只读导出，357页Word＋12页PPT共369页，66张全页概览和关键图表放大检查，8项发现已有仓库处置。

仍需完成：本轮核验范围已完成；正式Word出版版如另行修订，应另做交付版全页核验。

执行前置：正式出版稿如修订，需另行全页交付核验。

关闭标准：有原件页/形状位置、渲染或人工核对记录和差异处置；不以文字存在性代替视觉。

阶段边界：第一阶段输入质量项；不要求实现原型全部功能。

文档/证据：[source-content-audit.md](<stage-one/source-content-audit.md>)、[visual-layout-audit.md](<stage-one/visual-layout-audit.md>)、[visual-layout-audit.json](<stage-one/visual-layout-audit.json>)。

## S1-N02

**来源身份、版本优先级与变更权责**。原阶段1，步骤1,2,23，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：项目/业务/文档管理，实际姓名未确认。

已有完成范围：10原件摘要与成对修订稿保留，V2文件名/正文身份冲突已登记。 仓库唯一源/技术优先关系与变更字段已落实；10原件身份及版本冲突如实保留。

仍需完成：确认正式权威版本、适用范围、V2/V1.0身份冲突处置及实际变更责任人；唯一工程来源规则已完成。

执行前置：正式依据版本与适用范围、V2文件名/V1.0正文身份处理依据、实际变更责任人。

关闭标准：有可核验的来源身份/版本优先关系和变更记录；对应引用一致。

阶段边界：第一阶段设计输入身份；正式批准另登记。

文档/证据：[source-document-inventory.md](<source-document-inventory.md>)、[document-conversion-plan.md](<document-conversion-plan.md>)、[source-authority-and-change-control.md](<source-authority-and-change-control.md>)、[source-authority-register.json](<source-authority-register.json>)。

## S1-N03

**术语、业务规则与状态参数细化**。原阶段1，步骤4,6,10,11，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：业务/安全/架构，实际姓名未确认。

已有完成范围：术语/规则/状态机候选已形成，Q事项保留。 14类参数有状态/值/依据/版本及范围约束；RETURNED两条路径和缺项拒绝已有校验工具。

仍需完成：确定风险/人工阈值、RETURNED后继、首发未知、审批目的与回流/保留规则的适用参数和例外。

执行前置：本地来源确认的规则版本；14类参数的适用值/例外/依据，未确定的值保持UNCONFIRMED。

关闭标准：规则版本、触发条件、输入/输出、异常/例外及测试逐项可执行，不从建议值生成事实。

阶段边界：本阶段需明确设计；正式业务动作待相关规则和授权。

文档/证据：[glossary.md](<glossary.md>)、[task-state-machine.md](<../05-workflows/task-state-machine.md>)、[business-rule-review.md](<review-package/business-rule-review.md>)、[business-parameter-contract.md](<../01-requirements/business-parameter-contract.md>)、[business-parameters.candidate.json](<../../config/business-parameters.candidate.json>)、[business-parameters.schema.json](<../../schemas/controls/business-parameters.schema.json>)、[business-parameter-source-audit.json](<../01-requirements/business-parameter-source-audit.json>)。

## S1-N04

**需求到内部处理与结果读取的语义闭环**。原阶段1，步骤7,8,12,14,19,21，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：架构/前后端/算法/测试，实际姓名未确认。

已有完成范围：首批上传/历史的实际代码、迁移、语义绑定和异常检查已落实；仍未完成全部13项正式关闭与170任务。

仍需完成：13项契约缺口和真实业务实现/联调按对应任务继续；正式规则需实际依据。

执行前置：业务规则和来源授权、34能力输入/结果身份与公开投影、13项接口缺口的唯一契约。

关闭标准：逐需求的入口、内部契约、持久化/结果读取及异常/测试语义一致；缺字段进入唯一契约。

阶段边界：技术复核与契约设计材料已补；正式规则、能力专用输入/公开投影完整性及实际实现/联调仍待对应任务。

文档/证据：[requirement-processing-map.md](<requirement-processing-map.md>)、[source-section-map.md](<stage-one/source-section-map.md>)、[system-interface-specification.md](<../03-api/system-interface-specification.md>)、[requirement-semantic-review.md](<requirement-semantic-review.md>)、[result-identity-and-projection.md](<../05-workflows/result-identity-and-projection.md>)、[historical-result-reading.md](<../03-api/historical-result-reading.md>)、[workflow-contracts.md](<../05-workflows/workflow-contracts.md>)、[capability-projection-register.json](<../06-algorithms/capability-projection-register.json>)、[business-foundation-implementation.md](<../03-development/stage-three/business-foundation-implementation.md>)、[business-foundation-report.json](<validation/business-foundation-report.json>)、[business-recovery-report.json](<validation/business-recovery-report.json>)。

## S1-N05

**可执行的指标和验收测量协议**。原阶段1，步骤9,18，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：业务验收/测试/算法/运维，实际姓名未确认。

已有完成范围：24项测量协议及8组失败/未知/分母公式夹具已完成；源目标不变，真实验收结果未执行。 24项执行配置已有逐项缺失检查，不生成正式成绩；源目标与正式目标分开。

仍需完成：补真实封存样本/分层数量、正式目标、负载/资源/版本，实施对应真实验收。

执行前置：24项指标的实际封存样本/分层数、正式目标、版本/资源/负载与执行人。

关闭标准：协议能按同版本和固定样本复现，失败计入；算法/系统/安全与容量分开判断。

阶段边界：第一阶段需明确验收方法；真实全业务测试属于后续交付。

文档/证据：[non-functional-requirements.md](<../01-requirements/non-functional-requirements.md>)、[acceptance-criteria.md](<../09-testing/acceptance-criteria.md>)、[model-evaluation.md](<../06-algorithms/model-evaluation.md>)、[metric-protocols.md](<../09-testing/metric-protocols.md>)、[acceptance-metric-reference-report.json](<validation/acceptance-metric-reference-report.json>)、[acceptance-execution-configuration.md](<../09-testing/acceptance-execution-configuration.md>)、[acceptance-execution-inputs.json](<../09-testing/acceptance-execution-inputs.json>)。

## S1-N06

**数据集计数、标签和可用输入清单**。原阶段1，步骤15，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：数据/业务授权/算法，实际姓名未确认。

已有完成范围：15目录/标注/分组切分Schema与数据卡结构存在，实际样本规模未知。 15张实际数据卡及唯一ID/分组计数工具已形成；64条合成训练证据单列，真实授权数据数量未知。

仍需完成：落实来源/用途材料、标签版本/质检、原件与派生/内容簇计数及独立封存集规则；盘点实际可用样本。

执行前置：真实来源/用途依据、标签和质检版本、样本元信息、实际目录/数量及到位日。

关闭标准：数据卡有真实状态和用途/来源，计数可复算、划分防泄漏；未知保持未知。

阶段边界：本阶段需定义规则/资源输入；不要求先完成全部训练或20万样本目标。

文档/证据：[dataset-catalog.md](<../07-datasets/dataset-catalog.md>)、[annotation-specification.md](<../07-datasets/annotation-specification.md>)、[dataset-split-policy.md](<../07-datasets/dataset-split-policy.md>)、[actual-input-inventory.md](<../07-datasets/actual-input-inventory.md>)、[actual-input-inventory.json](<../07-datasets/actual-input-inventory.json>)。

## S1-N07

**人员投入、实际进度和分期执行台账**。原阶段1，步骤17,19,23，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：项目计划/各研发负责人，实际姓名未确认。

已有完成范围：170任务源工时397—491人日已复算，21条部分开发证据登记；可计算排期输入/工具/CSV已建立。 完整170任务输入/容量算法保留，自动预检查逐字段列实际人员/日历/剩余工时/到位日缺项。 用户已授权10名占位人员、假设投入与到位日的170任务排期方案；实际人员仍未确认。

仍需完成：实际人员/投入、剩余工时、计划起点/工作日历和数据/GPU到位日未提供，实际日历排期待补。

执行前置：实际人员/有效投入、剩余工时证据、工作日历/计划起点与数据/GPU到位日；占位10人不作实际输入。

关闭标准：有逐任务证据与实际排期，部分实现/完整验收分别登记；原工时与重估差异保留。

阶段边界：第一阶段计划与交接输入；完整170任务实现属于后续研发。

文档/证据：[backlog.yaml](<../../tasks/backlog.yaml>)、[dependency-report.md](<../../tasks/dependency-report.md>)、[scope-review.md](<review-package/scope-review.md>)、[execution-schedule.md](<execution-schedule.md>)、[execution-planning-inputs.json](<execution-planning-inputs.json>)、[stage-one-input-preflight-report.json](<validation/stage-one-input-preflight-report.json>)、[execution-schedule-scenario.md](<execution-schedule-scenario.md>)、[execution-planning-scenario-inputs.json](<execution-planning-scenario-inputs.json>)。

## S2-N01

**整体接口流程和必要服务契约**。原阶段2，步骤19，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：架构/前后端/算法/测试，实际姓名未确认。

已有完成范围：73操作候选契约已详细化；独立业务实际42外部/1内部入口及所选上传/历史/审批/复核/导出/控制子范围已有真实代码和隔离验证。完整操作范围与正式协议仍按接口缺口逐项落实。

仍需完成：其余业务操作和真实身份/来源/审批规则等正式接入仍需实施验证；已有子范围不重记为未实现，也不据此关闭全部13项正式缺口。

执行前置：13项缺口的设计输入、状态/版本/权限/异步终态规则；外部平台接口资料。

关闭标准：关键流程受理到终态可读取，唯一契约/映射/追踪/类型齐备，按对应任务真实联调。

阶段边界：关键边界/契约设计属第二阶段；全部业务API实现按后续模块交付。

文档/证据：[interface-gap-register.md](<../03-api/interface-gap-register.md>)、[contract-generation.md](<../03-development/contract-generation.md>)、[interface-gap-register.json](<../03-api/interface-gap-register.json>)、[system-interface-specification.md](<../03-api/system-interface-specification.md>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)、[business-foundation-implementation.md](<../03-development/stage-three/business-foundation-implementation.md>)、[business-foundation-report.json](<validation/business-foundation-report.json>)、[business-recovery-report.json](<validation/business-recovery-report.json>)。

## S2-N02

**业务数据库访问层与升级迁移**。原阶段2，步骤7，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：数据库/后端/安全，实际姓名未确认。

已有完成范围：独立业务工程已建立62表版本迁移及RLS基础，并实现所选上传、历史和控制访问层；与原5表PoC分离。迁移/权限/恢复有隔离实测，未部署正式生产数据库。

仍需完成：按剩余任务补齐所有业务访问和逐表场景、生产升级/回退/特权边界验证；初始化SQL不能代替实际迁移，也不把现有隔离验证当正式生产部署。

执行前置：业务表范围与唯一SQL/字典、逐表案件/单位隔离分类、增量迁移及升级副本/恢复方案。

关闭标准：相关模块迁移可验证、版本摘要/兼容/恢复明确，真实数据访问与案件域测试通过。

阶段边界：第二阶段需确定数据访问/事务和代表性验证；62表全业务实现按后续任务。

文档/证据：[database-design.md](<../04-database/database-design.md>)、[poc-database.md](<../04-database/poc-database.md>)、[migrations-and-events.md](<../03-development/migrations-and-events.md>)、[authorization-prototype.sql](<../../tests/sql/authorization-prototype.sql>)、[authorization-isolation-prototype.md](<../04-database/authorization-isolation-prototype.md>)、[stage-two-isolation-report.json](<validation/stage-two-isolation-report.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)、[business-foundation-implementation.md](<../03-development/stage-three/business-foundation-implementation.md>)、[business-foundation-report.json](<validation/business-foundation-report.json>)、[business-recovery-report.json](<validation/business-recovery-report.json>)。

## S2-N03

**完整任务编排、取消与多worker故障**。原阶段2，步骤9,19,20，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：后端/算法/测试，实际姓名未确认。

已有完成范围：复核36候选DAG、7类域事件和现有原子领取/旧租约拒绝；列出真实多worker、取消、续租、乱序和死信的执行前置条件。

仍需完成：实施实际调度器与多worker消息故障演练；当前8数据库竞争者不是8Celery worker，全业务DAG未运行。

执行前置：36候选DAG的实际节点/worker绑定、消息队列故障环境、取消/续租/死信处理与授权规则。

关闭标准：节点和运行版本不可错写；真实故障/重投/取消/续租及补偿有对应证据。

阶段边界：第二阶段需明确协议/故障方式并验证代表性场景；完整业务编排按任务交付。

文档/证据：[task-state-machine.md](<../05-workflows/task-state-machine.md>)、[migrations-and-events.md](<../03-development/migrations-and-events.md>)、[workflow-contracts.md](<../05-workflows/workflow-contracts.md>)、[stage-two-implementation-plan.md](<../03-development/stage-two-implementation-plan.md>)、[migration-fencing-report.json](<validation/migration-fencing-report.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N04

**正式身份与案件/单位隔离**。原阶段2，步骤15，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：身份平台/业务安全/后端，实际姓名未确认。

已有完成范围：研发Bearer/固定案件与正式业务应用分离；独立业务RLS和跨单位/案件、撤销后拒绝、历史读取有实测。真实身份提供方缺失时拒绝正式动作。

仍需完成：提供真实issuer/密钥或获准身份协议及用户/单位/案件映射，再验证签验、撤销、用途及正式权限策略。

执行前置：正式身份协议及issuer/验签材料、主体/单位/案件权威映射、功能矩阵与撤销时限。

关闭标准：当前授权、撤销/过期、跨案件和管理员越权有真实拒绝测试。

阶段边界：第二阶段需明确边界/技术验证；生产身份/全业务隔离在真实接入前完成。

文档/证据：[security-baseline.md](<../02-architecture/security-baseline.md>)、[permission-matrix.md](<../08-security/permission-matrix.md>)、[authorization-isolation-prototype.md](<../04-database/authorization-isolation-prototype.md>)、[stage-two-isolation-report.json](<validation/stage-two-isolation-report.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N05

**项目配额与研发数据卷容量**。原阶段2，步骤1,2,8,16，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：Linux及Docker运维/资源管理，实际姓名未确认。

已有完成范围：2026-10-14实测Docker.raw虚拟容量约786.88GiB，卷内13%使用、约644GiB可用，容量高于5GiB研发保护值；扩容不是本会话执行，维护记录/完整备份恢复未核验。

仍需完成：补实际扩容维护/整盘备份与恢复记录、项目独占配额和维护人；数据/权重/GPU授权及正式资源验收仍需落实。

执行前置：Docker虚拟机数据盘的实际扩容或迁移目标、备份/恢复条件、资源配额、GPU权限和维护人。

关闭标准：配额/路径可执行并实测，能容纳目标素材/权重/索引/备份，记录余量与告警。

阶段边界：第二阶段资源基线项；批量数据和大模型/索引引入前必须落实。

文档/证据：[resource-readiness-snapshot.json](<validation/resource-readiness-snapshot.json>)、[resource-and-team-inventory.md](<../02-architecture/resource-and-team-inventory.md>)、[stage-two-operations.candidate.json](<../../config/stage-two-operations.candidate.json>)、[stage_two_readiness.py](<../../scripts/stage_two_readiness.py>)、[stage-two-operations-and-offline-delivery.md](<../10-deployment/stage-two-operations-and-offline-delivery.md>)、[stage-two-resource-report.json](<validation/stage-two-resource-report.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N06

**业务模型、OCR/ASR及GPU验证**。原阶段2，步骤12,13，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：数据/算法/GPU运维，实际姓名未确认。

已有完成范围：复核15实际数据卡、24验收执行输入与34能力投影，未知用途/数据量/GPU/模型许可继续拒绝正式验收。

仍需完成：提供有用途授权的数据目录、权重许可/来源/摘要、实际GPU与驱动，实施逐能力训练/推理和独立封存盲测；M15合成CPU不代替业务能力。

执行前置：用途授权数据目录、权重来源/许可/摘要、独立封存测试集、实际GPU及驱动。

关闭标准：模型版本/前后处理/维度/时间语义、资源/错误与独立效果证据明确，不以mock/Schema代替。

阶段边界：第二阶段需选型和代表性PoC；全部34能力后端与正式精度按后续算法任务。

文档/证据：[model-catalog.yaml](<../06-algorithms/model-catalog.yaml>)、[model-evaluation.md](<../06-algorithms/model-evaluation.md>)、[inference-interfaces.md](<../03-api/inference-interfaces.md>)、[actual-input-inventory.json](<../07-datasets/actual-input-inventory.json>)、[acceptance-execution-inputs.json](<../09-testing/acceptance-execution-inputs.json>)、[capability-projection-register.json](<../06-algorithms/capability-projection-register.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N07

**真实媒体、VFR和全时间轴链路**。原阶段2，步骤14，优先级P1。

当前状态：待落实实际条件及对应交付。所需责任角色：媒体/算法/后端/测试，实际姓名未确认。

已有完成范围：新增11项实际FFmpeg检查：8帧VFR、非零PTS、抽帧像素、音频样本与时间原点、字幕区间及90度旋转坐标。

仍需完成：实际授权媒体的多编码/VFR/缺模态/裁剪/转码链路及OCR/ASR、长视频性能仍需实现和实测；本轮仅自建夹具。

执行前置：实际授权多编码/VFR/缺模态/长视频素材、映射链路及OCR/ASR模型。

关闭标准：真实素材的源/派生时间与空间映射、边界和异常输出有证据。

阶段边界：媒体技术组合/代表性映射为第二阶段验证，全部业务流水线按后续交付。

文档/证据：[media-timestamp-report.json](<validation/media-timestamp-report.json>)、[TB-ADR-010-media-processing.md](<../02-architecture/architecture-decisions/TB-ADR-010-media-processing.md>)、[verify_stage_two_media.py](<../../scripts/verify_stage_two_media.py>)、[stage-two-representative-validation.md](<../09-testing/stage-two-representative-validation.md>)、[stage-two-media-report.json](<validation/stage-two-media-report.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N08

**中文/规模化检索与传播图验证**。原阶段2，步骤10,11，优先级P1。

当前状态：待落实实际条件及对应交付。所需责任角色：检索/算法/后端/测试，实际姓名未确认。

已有完成范围：新增真实中文字符词项、标点边界、AND查询、空查询拒绝和GIN索引执行计划检查；普通SQL传播环路验证沿用。

仍需完成：确定正式中文分词/排序选型，实施实际大索引/向量及传播图业务、授权过滤和规模性能；4条文本不是业务检索指标。

执行前置：正式中文分词/排序选择与版本、实际索引规模、查询指标/负载及案件权限过滤。

关闭标准：固定候选库/版本及真实工作负载下有正确性、延迟、资源和故障证据。

阶段边界：第二阶段确定方案与代表性机制；大规模业务/20与100并发按后续验收。

文档/证据：[technical-validation-report.md](<../02-architecture/technical-validation-report.md>)、[media-query-report.json](<validation/media-query-report.json>)、[verify_stage_two_isolation.py](<../../scripts/verify_stage_two_isolation.py>)、[stage-two-representative-validation.md](<../09-testing/stage-two-representative-validation.md>)、[stage-two-isolation-report.json](<validation/stage-two-isolation-report.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N09

**正式安全与证据防篡改机制**。原阶段2，步骤8,15，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：业务审核/安全/后端/存储，实际姓名未确认。

已有完成范围：追加结果UPDATE/DELETE拒绝和撤销后写入拒绝的真实验证；明确管理员绕过RLS/修改存储的边界，未称WORM或正式批准。

仍需完成：落实双人审批适用规则、可信时间/签名、保留期、WORM/密钥及管理员边界，实施下载每次授权核验和到期/撤销演练。

执行前置：双人审批适用规则、保留期、WORM/签名/可信时间、密钥与特权管理边界。

关闭标准：普通/特权、到期/撤销、固定证据版本完整性有对应机制与测试，适用规范明确。

阶段边界：第二阶段需安全架构/代表性验证；完整正式机制在相关业务/生产启用前。

文档/证据：[security-baseline.md](<../02-architecture/security-baseline.md>)、[audit-requirements.md](<../08-security/audit-requirements.md>)、[evidence-state-machine.md](<../05-workflows/evidence-state-machine.md>)、[authorization-isolation-prototype.md](<../04-database/authorization-isolation-prototype.md>)、[business-parameters.candidate.json](<../../config/business-parameters.candidate.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N10

**生产灾备、PITR和密钥恢复**。原阶段2，步骤8,16，优先级P1。

当前状态：待落实实际条件及对应交付。所需责任角色：运维/数据库/安全/测试，实际姓名未确认。

已有完成范围：本批实际pg_dump/restore、固定版本对象及两次历史快照在独立研发目标恢复成功；生产灾备条件仍未落实。

仍需完成：提供真实异地目标和密钥恢复授权、批准RPO/RTO；实施全业务异机恢复及对账，不能用开发冷备结果证明生产灾备。

执行前置：批准RPO/RTO、另一主机/异地位置、WAL归档、密钥恢复授权和索引重建方案。

关闭标准：目标时间/权限下实际独立恢复，数据/对象/模型/索引/密钥可用，演练记录可复核。

阶段边界：第二阶段确定方案与开发恢复验证；生产级演练在正式发布前。

文档/证据：[development-backup-restore.md](<../10-deployment/development-backup-restore.md>)、[development-recovery-report.json](<validation/development-recovery-report.json>)、[stage-two-implementation-plan.md](<../03-development/stage-two-implementation-plan.md>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)、[business-foundation-implementation.md](<../03-development/stage-three/business-foundation-implementation.md>)、[business-foundation-report.json](<validation/business-foundation-report.json>)、[business-recovery-report.json](<validation/business-recovery-report.json>)。

## S2-N11

**支持版本、OS物料和离线交付**。原阶段2，步骤1,17，优先级P0。

当前状态：待落实实际条件及对应交付。所需责任角色：技术/软件准入/许可审查/安全，实际姓名未确认。

已有完成范围：保留指定Miniforge py310；新增实际5镜像OS物料/SPDX清单及来源覆盖说明，登记旧web镜像无法inspect的事实。 生产Python候选顺序、验证标准和3.10例外条件已写入现有ADR/版本配置及待填证据表；实际研发环境保持。

仍需完成：按TB-ADR-002验证3.13主候选/3.12备选或有实际维护依据的3.10例外，落实精确生产Python/OS、依赖/模型/CPU-GPU兼容、新锁/全CI与准入决定；补未托管二进制/FFmpeg源码与notices、模型许可、漏洞扫描及离线交付；未自动安装或升级当前环境。

执行前置：生产Python/OS准入目标、FFmpeg等未托管二进制及源码notices、模型许可和漏洞扫描工具。

关闭标准：选定目标精确锁/重建/兼容CI通过，包/二进制/权重来源与物料/分发范围可核验。

阶段边界：当前py310研发无需被本清单改动；生产版本/离线制品在相应交付前。

文档/证据：[environment-constraints.md](<../02-architecture/environment-constraints.md>)、[licenses.md](<../02-architecture/licenses.md>)、[compatibility-matrix.md](<../02-architecture/compatibility-matrix.md>)、[collect_stage_two_software.py](<../../scripts/collect_stage_two_software.py>)、[stage-two-software-report.json](<validation/stage-two-software-report.json>)、[image-sbom.spdx.json](<validation/image-sbom.spdx.json>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)。

## S2-N12

**CI组织治理与受控制品交付**。原阶段2，步骤21,22,23，优先级P1。

当前状态：待落实实际条件及对应交付。所需责任角色：仓库管理/构建发布/安全，实际姓名未确认。

已有完成范围：将新增6组控制、21项隔离/中文、11项媒体与镜像物料采集接入CI；准备无秘密离线制品摘要检查及必需分支检查配置。

仍需完成：落实私有仓库保护功能套餐/管理员配置、签名与离线镜像库/依赖缓存/保留策略；运行中镜像缺失须先重新构建验真再导出。

执行前置：私有仓库治理功能与管理人、必须检查/评审规则、制品库/签名/离线依赖/保留策略。

关闭标准：实际配置与适用检查能阻断失败，受控制品可按源码/锁/摘要追溯；无法查询保留未知。

阶段边界：第二阶段定义开发门禁和治理边界；组织发布/生产制品控制在实际交付前。

文档/证据：[repository-governance-snapshot.json](<validation/repository-governance-snapshot.json>)、[ci-cd.md](<../03-development/ci-cd.md>)、[ci.yml](<../../.github/workflows/ci.yml>)、[validate_stage_two_completion.py](<../../scripts/validate_stage_two_completion.py>)、[stage-two-operations-and-offline-delivery.md](<../10-deployment/stage-two-operations-and-offline-delivery.md>)、[stage-two-completion-matrix.json](<../03-development/stage-two-completion-matrix.json>)、[main-protection-readback.json](<validation/main-protection-readback.json>)、[main-protection-enforcement-report.json](<validation/main-protection-enforcement-report.json>)。

## 13项接口缺口的入口

正式条件仍保持开放；IF-G01新增GET已进入唯一契约并实际实现，IF-G01/09首批技术范围见[实际实现说明](<../03-development/stage-three/business-foundation-implementation.md>)。其余候选新增路径仍不可调用，来源为唯一[业务OpenAPI](<../03-api/openapi.yaml>)及相关Schema。

| 编号/工作 | 仍需工作 | 关闭标准/计划任务 |
| --- | --- | --- |
| IF-G01 上传续传与校验状态查询 | 复用UploadSession/UploadPart/UploadResult组成投影，定义已接收分片、总量/摘要、到期/校验终态，asset_id仅VALID后可分析。 | 补唯一契约/样例/映射/类型，测中断续传、重复/摘要冲突、到期和异步成功/失败。<br>T022,T023,T024,T026,T027 |
| IF-G02 审批读取与撤销链路 | 复用Approval，定义有权对象列表/详情/决定历史、游标/ETag、目的/版本/到期；撤销是否走现有decisions需规则决定，不能自动赋予审批权。 | 正式规则确认后补契约/SQL映射/追踪，测跨案件、两人独立性、到期与重算使旧批准失效。<br>T016,T102,T107,T108,T170 |
| IF-G03 复核工作台读取与版本冲突 | 复用Review设计有权待办/记录读取，明确task/run/result/review绑定、筛选、ETag和只追加历史，不自动放行报告。 | 补源契约和追踪，测提交前读取版本、同时复核冲突、退回后历史可查。<br>T102,T103 |
| IF-G04 反馈审批与回流状态读取 | 复用反馈结构补受控数据版本投影、撤销停止/去重；用途/划分核验，禁止封存测试集回流。 | 补契约/数据卡/审批引用，测拒绝、撤销、重复消费与样本计数不重复。<br>T108,T109,T126,T127 |
| IF-G05 模型灰度及回滚操作查询 | 以ActionAck.object_id绑定发布操作，定义状态、release_bundle/模型/索引版本、失败/进度/回滚终态。 | 补操作Schema/映射与受理至终态链路，测不兼容拒绝、幂等/失败后回滚、许可/批准。<br>T057,T060,T170 |
| IF-G06 审计导出作业及产物读取 | 以object_id绑定导出，补状态和固定ObjectRef；限定组织/案件/时间、批准目的、脱敏/到期；下载按Range/当前授权核验。 | 补唯一结构/投影及来源确认，测受理/失败/终态/摘要下载和撤销后下一Range拒绝。<br>T017,T018 |
| IF-G07 正式身份与角色案件授权边界 | 确认身份方协议、主体映射、令牌/撤销、授权同步/审计；先确定统一平台或仓库管理API的责任，不能制造第二权限源。 | 取得Q-05/Q-16/Q-25决定和实际材料，补协议/Schema与授权、撤销、越权联调证据。<br>T011,T012,T013,T014,T015 |
| IF-G08 来源授权验证和失效同步 | 明确权威授权记录、用途/到期/撤销版本及适配器/事件；客户端authorization_status不能完成授权。确定动作后才加入OpenAPI。 | 补核验协议与追踪，撤销后分析/导出/训练回流拒绝且历史和审计可追溯。<br>T021,T029,T108 |
| IF-G09 按历史运行结果查询 | 版本字段成组必填；严格按当前案件/对象和task/run/result匹配、404不回退最新。快照保存34能力原响应，列表/完整专用公开投影及后端联调仍待实现。 | 补路径/参数/字段/追踪，测两次重算后精确版本、旧结果不可变和跨案件拒绝。<br>T031,T035,T038,T039,T102,T104 |
| IF-G10 第三方数据平台适配器协议 | 逐平台登记批准方式/版本、来源标识、发布时间/观测时间/可见范围、签验、游标/去重/限流，不虚构URL或账号。 | 取得Q-17/Q-28和平台资料后补协议，测重复、签验/到期错误、字段缺失及限流。<br>T021,T028,T029 |
| IF-G11 全业务DAG与跨模块事件 | 先决定API/消息边界，定义必要事件的结构版本、生产消费方、运行身份、去重/租约fencing、顺序/重试/取消/死信与授权；每个实际事件单独Schema。 | 确定DAG/取消后补必要Schema/类型，测真实多worker、重复乱序、旧运行/超时及死信恢复。<br>T031,T036,T037,T038,T039,T053,T055 |
| IF-G12 配置值、聚合ETag及策略生效 | 明确资源/聚合强ETag与原子更新；配置引用唯一版本，数值待资源/规则决定；草案、批准和生效分别定义。 | 形成决定及适用契约，测同键不同摘要、旧ETag、权限/重算失效、稳定分页/背压。<br>T007,T009,T016,T061,T069,T102 |
| IF-G13 内部34能力服务语义与一致性 | 模型Schema保持唯一；调用/响应核验path/body能力、model/run/request身份、对象版本/摘要、授权、deadline和输出语义；支持列表应匹配实际部署。 | 逐能力补实现/授权样本验证，测能力错配、非法对象、超时/取消；不拿mock或Schema当准确率通过。<br>T051,T053,T054,T055,T056 |

完整来源与候选路径见[interface-gap-register.json](<../03-api/interface-gap-register.json>)和[interface-gap-register.md](<../03-api/interface-gap-register.md>)。

## 正式评审与冻结条件

冻结事项单列，未重复计入18项非签字工作；审批不能代替真实输入或运行证据。

- 第一阶段22—24步：落实实际输入和适用决定，33项问题形成有效处置记录、实际责任人、范围/例外；引用候选摘要后冻结。
- 第二阶段22—23步：技术评审明确适用环境/版本/遗留处理，附实际资源与代表性证据；按有效决定冻结，正式基线标签须有批准依据。

填写入口：[review-resolution-inputs.json](<stage-one/review-resolution-inputs.json>)、[review-decisions.yaml](<review-decisions.yaml>)、[freeze-checklist.md](<freeze-checklist.md>)、[technical-baseline-review.md](<review-package/technical-baseline-review.md>)。没有正式决定时两阶段均NOT_FROZEN。

## 实际输入、实施与同步

实际人员/日历填写[execution-planning-inputs.json](<execution-planning-inputs.json>)；数据填写[actual-input-inventory.json](<../07-datasets/actual-input-inventory.json>)及15数据卡；指标填写[acceptance-execution-inputs.json](<../09-testing/acceptance-execution-inputs.json>)；第二阶段资源/平台填写[stage-two-external-inputs.json](<../03-development/stage-two-external-inputs.json>)。

后续业务/生产按[实施计划](<../03-development/stage-two-implementation-plan.md>)和[170任务卡](<../../tasks/README.md>)推进；完整62表、DAG和业务模型不是本次导航更新的完成事项。

本地、GitHub、Linux仓库读取同一套相对链接。GitHub仓库为[media-traceability-system](https://github.com/xuchangsheng18/media-traceability-system)，服务器仓库为`/workspace/glwy/projects/media-traceability-system`。实际同步看[server-sync-receipt.json](<server-sync-receipt.json>)，CI看[github-actions-report.json](<validation/github-actions-report.json>)。

维护时编辑唯一台账/专项来源，再运行`python scripts/update_docs_navigation.py`生成；`python scripts/generate_remaining_work_navigation.py --check`核验派生内容。更新导航不会自动关闭任务。
