# 短视频与图片智能识别溯源系统

2026-10-22本批T024目标上传队列隔离：[实现与旧队列边界](docs/03-development/t024-upload-queue-isolation.md)、[真实RED/GREEN与同步回执](docs/00-project/validation/t024-upload-queue-isolation-report.json)。v2单位/案件/上传独立队列解决同案件另一上传阻塞目标消费者；错投继续拒绝且不ACK。103项受影响隔离回归及既有失败探针、质量检查通过。新增1条子步骤，当前151条已证、434组剩余，全部170项622组剩余、整卡验收0项；旧队列未迁移、共享采用未验，同上传多消费者公平/毒消息处置仍待。

2026-10-22 T034决定更新：[D01/D02限定认可](docs/00-project/validation/t034-design-decision-20261022.json)、[I01—I05实施计划待审](docs/03-development/t034-creation-implementation-plan.md)。仅技术设计及D03计划准备，E01—E04实际输入未确认；未新增创建代码、SQL、运行采用或已证子步骤。

2026-10-22历史批次T103原件关联与下载：[实现与边界](docs/03-development/t103-evidence-original-access.md)、[实测及同步回执](docs/00-project/validation/t103-evidence-original-report.json)。仅original证据精确绑定有效原始资产后显式读取/下载，独立权限及大小/SHA-256/ETag核验、逐阶段失效已接线；959项前端、开发/生产各172项传输浏览器通过。新增1条子步骤，当批累计150条已证、434组剩余，全部170项622组剩余、整卡验收0项。播放/派生内容、持久草稿/标注和正式权威组合仍待；原锁npm双端0匹配仅诊断，不继承托管CI通过。

2026-10-22历史批次T103复核表单：[实现与边界](docs/03-development/t103-review-submission.md)、[实测及同步回执](docs/00-project/validation/t103-review-submit-report.json)。原样ETag和幂等提交、当前页内存草稿及不确定原请求重试已接线；755项前端、开发/生产各138项传输浏览器通过。新增1条子步骤，当批累计149条已证、434组剩余，全部170项622组剩余、整卡验收0项。正式规则/职责提供方、持久草稿/标注、媒体及真实工作流仍待；不把记录决定当批准或已重算。

2026-10-22历史批次T101/T103证据分页：[实现与边界](docs/03-development/evidence-snapshot-pagination.md)、[实测及同步回执](docs/00-project/validation/evidence-paging-report.json)。显式limit/cursor分页、每页当前授权与固定投影绑定及前端下一页已接线；省略参数保留旧响应，上游未取齐拒绝503。688项前端、开发/生产各114项传输浏览器通过；后端初轮135项为134通过/1项测试期望错误，修正后11项HTTP通过，59纯及65相邻测试保留初轮通过证据。新增2条子步骤，当批累计148条已证、434组剩余，全部170项622组剩余、整卡验收0项。过滤、真实producer、媒体播放、复核写入和完整工作流仍待；算法与Python候选继续暂缓。

2026-10-22历史批次T103证据定位：[实现与边界](docs/03-development/t103-evidence-location.md)、[实测及同步回执](docs/00-project/validation/t103-evidence-read-report.json)。精确历史证据读取与编号定位、时间/归一化区域、缺引用和不完整提示已接线；665项前端、开发/生产各103项传输浏览器通过。新增1条子步骤，当批累计146条已证、434组剩余，全部170项622组剩余、整卡验收0项；媒体字节/播放、证据分页、审批/草稿和真实权威组合仍待。

2026-10-22历史批次T103复核只读页面：[实现与边界](docs/03-development/t103-review-read-console.md)、[实测及同步回执](docs/00-project/validation/t103-review-read-report.json)。当前上下文与历史分页分别保留版本；487项前端、开发/生产各88项传输浏览器通过。新增1条子步骤，当批累计145条已证、434组剩余，全部170项622组剩余、整卡验收0项；审批/草稿、正式规则、真实权威组合及算法联调仍待。

2026-10-22历史批次T030共享会话：[修复与边界](docs/03-development/shared-session-rejection-lifecycle.md)、[实测及同步回执](docs/00-project/validation/shared-session-rejection-lifecycle-report.json)。旧401拒绝传播期间的新连接尝试保护已修复；6项受控调度新单元纳入396项前端，开发/生产各72项传输浏览器通过。新增1条子步骤，当批累计144条已证、434组剩余，全部170项622组剩余，整卡验收0项；非普通点击故障或真实权威验收，保留测试维护事项。算法与Python候选暂缓。

2026-10-22历史批次T030资产上下文清理：[修复与边界](docs/03-development/t030-asset-context-invalidation.md)、[实测及同步回执](docs/00-project/validation/t030-asset-context-invalidation-report.json)。同generation本地身份变化同步清除资产返回数据；有效RED后11项新增浏览器、390项前端、开发/生产各72项传输浏览器通过。新增1条工程子步骤，当批累计143条已证、434组剩余，全部170项622组剩余，整卡验收0项。真实权威组合、远端撤销和完整血缘仍待，保留1项异步负例覆盖改进；算法与Python候选暂缓。

2026-10-22历史批次T027并发SHA关联：[修复与边界](docs/03-development/t027-concurrent-sha-association.md)、[实测及同步回执](docs/00-project/validation/t027-concurrent-sha-association-report.json)。不同上传会话真实双连接RED后修复，7例并发边界及92项相邻回归通过；完整回归、精确CI和源码以回执逐项结果为准。新增1条工程子步骤，当批累计142条已证、434组剩余，全部170项622组剩余，整卡验收0项；算法与Python候选暂缓。

2026-10-22历史批次T030资产来源面板：[实现与边界](docs/03-development/t030-asset-source-panel.md)、[限定验证与同步回执](docs/00-project/validation/t030-asset-source-panel-report.json)。新增1条只读页面子步骤，390项前端、开发/生产各61项传输浏览器通过；真实权威组合联调和完整血缘未验收。T001—T123当批累计141条已证、434组剩余；全部170项622组剩余，整卡验收0项。T034新设计D01—D03仍待审，算法与Python候选继续暂缓。

2026-10-22历史待审T034创建接入：[具体设计](docs/03-development/t034-creation-integration-design.md)、[方案与CI/同步回执](docs/00-project/validation/t034-creation-integration-design-report.json)。真实映射、分阶段受限SQL、原子事务及HTTP接线方案已补齐，D01—D03待审；本批未实施产品代码或迁移，完成数不增加。方案编制时快照为140条已证、434组剩余；全部170项622组剩余、整卡验收0项。算法与Python候选继续暂缓。

2026-10-22历史批次T034请求/计划绑定：[实现与边界](docs/03-development/t034-request-plan-binding.md)、[限定实测回执](docs/00-project/validation/t034-request-plan-binding-report.json)。新增1条内部内核子步骤；T001—T123当批累计140条已证、434组剩余，全部170任务140条已证、622组剩余，整卡验收0项。64项新测试纳入243项受影响回归及258文件类型检查通过；真实提供方、创建事务和HTTP尚未完成。T024和T034的负责人/指定复核人均已确认为徐昌胜，未登记实际验收。

2026-10-22历史批次T039取消页面：[实现与边界](docs/03-development/task-cancellation-console.md)、[限定实测回执](docs/00-project/validation/task-cancellation-console-report.json)。新增1条工程子步骤；T001—T123当批累计139条已证、434组剩余，全部170任务139条已证、622组剩余，整卡验收0项。350项前端及开发/生产各55项传输浏览器通过；真实后端E2E、T034创建和真实worker停止未完成。

2026-10-22历史批次T033取消统一写入：[实现与边界](docs/03-development/t033-cancellation-atomic-writer.md)、[限定实测回执](docs/00-project/validation/t033-cancellation-atomic-writer-report.json)。新增1条工程子步骤；T001—T123当批累计138条已证、434组剩余，全部170任务138条已证、622组剩余，整卡验收0项。前置精确CI业务及权限通过，整体安全扫描失败；本批精确CI另核对。

2026-10-22历史批次T006安全失败定位：[实现与边界](docs/03-development/ci-safe-failure-diagnostics.md)、[限定实测回执](docs/00-project/validation/ci-safe-failure-diagnostics-report.json)。新增1条工程子步骤；T001—T123当批累计137条已证、434组剩余，全部170任务137条已证、622组剩余，整卡验收0项。原完整业务回归1项失败未定位，T033业务修改暂缓。

2026-10-22历史批次T032运行事件约束：[0015实现与边界](docs/04-database/task-event-run-integrity.md)、[限定实测回执](docs/00-project/validation/t032-task-event-integrity-report.json)。新增1条工程子步骤；T001—T123当批累计136条已证、434组剩余，全部170任务136条已证、622组剩余，整卡验收0项。

2026-10-22历史批次T031候选计划：[解析实现与边界](docs/03-development/t031-candidate-task-plan.md)、[限定实测回执](docs/00-project/validation/t031-candidate-task-plan-report.json)。新增1条工程子步骤；T001—T123当批累计135条已证、434组剩余，全部170任务135条已证、622组剩余，整卡验收0项。

2026-10-22历史批次T024落盘持久性：[实现与边界](docs/03-development/t024-object-durability.md)、[限定实测回执](docs/00-project/validation/t024-object-durability-report.json)。新增1条工程子步骤；T001—T123当批累计134条已证、434组剩余，全部170任务134条已证、622组剩余，整卡验收0项。

2026-10-22历史批次T024隔离worker联调：[实现与剩余条件](docs/03-development/t024-worker-isolated-integration.md)、[限定实测回执](docs/00-project/validation/t024-worker-isolated-integration-report.json)。新增1条worker子步骤；T001—T123当批累计133条已证、434组剩余，全部170任务为133条已证、622组剩余，整卡验收0项。

2026-10-22首批实际开发：[业务上传前端及剩余联调](docs/03-development/business-upload-first-batch.md)、[精确验证回执](docs/00-project/validation/business-upload-first-batch-report.json)。业务上传入口已实现，单元311项、浏览器51项分别在开发/生产构建通过；新增3条限定子步骤，T001—T123当批累计132条已证、434组剩余，整卡验收0项。

**10月28日提交目标：** [非算法工程版快速计划](docs/03-development/non-algorithm-fast-delivery-plan-20261028.md)、[范围与边界](docs/03-development/non-algorithm-delivery-scope.md)。用户要求算法暂缓；70项工程、20项混合拆分、30项算法延期、3项外部验收准备逐项列出；规划本身不增加完成数；当前实际进展见下方首批回执和任务导航。

2026-10-21优先续批：[后端→前端→数据→测试](docs/03-development/backend-frontend-data-test-priority-plan.md)、[实测回执](docs/00-project/validation/backend-frontend-data-test-report.json)。新增来源授权同步事务/页面和离线标注质检工具；T001—T123为129条已验证子步骤、434组剩余工作，整任务验收0项；源码同步与共享服务采用分别记录。

2026-10-21来源管理续批：[页面与后端修复](docs/03-development/t021-source-console-continuation.md)、[实际检查/CI/源码同步](docs/00-project/validation/t021-source-console-report.json)。新增案件来源列表/详情/登记，修复到期元数据读取；未知结果原键重试、权限变化清空草稿。该次记录为126条已验证子步骤、434组剩余工作，整任务验收0项；共享服务尚未切换。

2026-10-21当前状态：[T001—T123逐项开发审计](docs/03-development/t001-t123-development-completion-audit.md)、[本轮实际验证/CI/同步](docs/00-project/validation/t001-t123-resource-registry-report.json)。当前业务接口51/73已挂载、22项未挂载；新增来源登记、受控下载与资产页、模型/评测只读列表及[模型目录页面验证](docs/00-project/validation/t060-readonly-ui-report.json)。[2张CC0原图与5个可追溯派生文件](docs/07-datasets/public-development-data.md)已保存至仓库外并在Linux解码。123任务尚未全部开发完成，任务卡按真实子成果更新，原CI门禁和Python候选暂缓保持。0012—0014未应用既有演示/共享库，源码同步不等于服务采用。

此前一轮前后端与权限续批（历史47/26）：[27项起点接口逐项台账](docs/03-development/t001-t123-remaining-interface-register.md)、[本批计划](docs/03-development/t001-t123-api-continuation-plan.md)、[实际测试、CI与同步状态](docs/00-project/validation/t001-t123-api-continuation-report.json)。业务源码47项挂载、26项未挂载；新增真实报告元数据读取、资产只读列表/详情和案件任务列表。任务卡和分步导航已同步限定子范围，原CI门禁及Python候选暂缓不变；源码同步不代表0012/0013已应用或既有演示服务已重启。

T001—T123开发落实：[全部任务的表／接口／方法和状态](docs/03-development/t001-t123-implementation-inventory.md)、[本批读取计划](docs/03-development/t001-t123-catalog-read-implementation-plan.md)、[实际验证](docs/00-project/validation/t001-t123-catalog-read-report.json)。建表、方法源码、隔离验证和运行实例分别判定。

2026-10-21页面优化：[本地12页PPT与实际页面对照](docs/03-development/ppt-interface-alignment.md)、[本批验证及同步状态](docs/00-project/validation/ppt-interface-alignment.json)。现有页面按原型统一布局；待接入模块单列，业务权限与接口保持原行为。

2026-10-21研发演示交付：[本批前后端计划](docs/03-development/development-delivery-implementation-plan.md)、[启动与范围](docs/10-deployment/business-development-runbook.md)、[实际验证](docs/00-project/validation/development-delivery-validation.json)。工作台增加任务与结果、案件待复核队列；Linux演示入口托管真实前端构建并转发后端。实际启动、源码及CI状态见回执；真实身份/授权尚未装配，默认拒绝不当正式业务通过。[上一批记录](docs/00-project/validation/development-continuation-report.json)保留。
2026-10-17本批：[T001—T012逐项收口](docs/03-development/t001-t012-closeout.md)、[原生迁移设计](docs/03-development/native-linux-migration-design.md)、[N01—N08实施计划](docs/03-development/native-linux-implementation-plan.md)、[执行状态](docs/03-development/native-linux-execution-status.json)。设计/计划及候选上限已认可，从N01开始；main规则及engineering已回查，失败检查阻止合并已实测，[正反验证及PR处置](docs/00-project/validation/main-protection-enforcement-report.json)按实际记录更新。现有服务未切换。

开源许可：[Apache-2.0](LICENSE)，归属与第三方边界见[NOTICE](NOTICE)；用户确认的完整公开范围及实际切换验证见[仓库公开说明](docs/00-project/open-source-publication.md)。研发与生产验收状态按下文保留。

任务执行入口：[分步任务导航](tasks/README.md#分步任务导航)、[全部执行事项逐项清单](docs/00-project/task-execution-steps.txt)、[同源状态台账](tasks/execution-status.json)。分步导航逐项列出170项任务的完成子步骤数、剩余工作数、全局序号范围与任务卡入口。T012之前的状态见[T001—T011当前完成与剩余逐项清单](docs/03-development/t001-t011-foundation-review.md#当前完成情况2026-10-17)。

2026-10-20剩余工作入口：[T014已批准P01—P07隔离计划](docs/03-development/t014-isolated-six-role-implementation-plan.md)、[P01—P07实测与当前进度](docs/00-project/validation/t014-isolated-rule-progress.json)、[T001—T123逐项顺序](docs/03-development/t001-t123-development-sequence.md)、[T013本人MFA管理实际回执](docs/00-project/validation/t013-owner-mfa-management-validation.json)、[后续恢复及退役步骤](docs/03-development/t013-owner-action-checklist.md)。T014的P01—P07隔离实现、1009项完整回归、门禁和精确代码CI已验证，未启用共享正式ALLOW。Python候选继续暂缓；子步骤计数以实际台账为准。

T015当前限定验证：此前461项业务快照和128项CLI记录保留历史；[本批精确证据](docs/00-project/validation/t001-t123-resource-registry-report.json)已记录T015完整入口131项及失败探针、T0141092项、T016187项和29项迁移/owner/契约检查，各范围分别核验。P01—P07源计划覆盖、真实提供者、共享采用与整卡验收继续逐项保留，最新托管CI不继承历史通过。

2026-10-17已按用户指定登记邓昀为T001—T011实际负责人；有效工时、平台账号及验收结果仍待确认，见[任务责任登记](docs/03-development/repository-access-control.md)。

当前已完成用户指定Miniforge py310的CPU研发最小工程：环境盘点、版本锁定及前后端/数据库/对象/队列/真实合成推理闭环。本机21道CI记录为原1.1历史范围，托管CI本批已扩展检查，实际源码和数量见平台报告。正式业务/生产NOT_FROZEN。保留12模块、170任务、不少于3类场景；未宣称全部业务实现。

服务器仓库：`/workspace/glwy/projects/media-traceability-system`；Python：`/opt/conda/glwy/envs/py310/bin/python`（3.10.22）。应用容器明确使用打包的同一py310。Python3.10已结束支持；生产前迁移并重新验证，见[环境约束](docs/02-architecture/environment-constraints.md)。


<!-- development-entry-summary:start -->
基础开发可以按任务子范围开始；两阶段整体技术闭环和正式冻结仍未完成。最近Linux服务器Docker虚拟机研发卷观测13%、约644GiB可用；正式配额、维护及整盘恢复仍需核验；正式身份、授权数据/GPU及生产验收仍有真实条件。范围与检查见[现有技术基线中的开发准入](docs/02-architecture/technical-baseline.md#技术完成程度与开发准入)。
<!-- development-entry-summary:end -->
<!-- phase-remaining-navigation:start -->
## 第一、第二阶段剩余工作总导航

第一阶段24步、第二阶段23步与170业务任务分别管理。核查19项工作：版式核验在记录范围内已完成；剩余18项，包括第一阶段6项、第二阶段12项。工程补充、实际输入、实现/联调、正式验收与冻结分别判断。13接口缺口与这些事项交叉，不能相加计算完成率。真实人员/责任人尚未全部确认，10人占位排期只作假设；已确认的任务负责人按实际输入和任务卡登记。

容量问题位于Linux服务器172.16.58.179的Docker Desktop虚拟机内，为PostgreSQL研发数据卷所在文件系统。仓库快照时点`2026-10-14T13:24:30.139139+00:00`：df使用率13%，可用约644.42 GiB。不是本地Windows D盘或GitHub容量，也不代表Linux宿主/workspace全部空间不足。容量已高于5GiB研发构建保护值；扩容不是本会话执行，维护/整盘备份及正式恢复仍未核验。

完整逐项导航：[剩余任务、前置条件、关闭标准及13接口缺口](<docs/00-project/remaining-work-navigation.md>)；[同源机器索引](<docs/00-project/remaining-work-navigation.json>)。

### 第1阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S1-N02 / P0<br>步1,2,23<br>项目/业务/文档管理（实际姓名待定） | 来源身份、版本优先级与变更权责<br>待落实实际条件及对应交付 | 确认正式权威版本、适用范围、V2/V1.0身份冲突处置及实际变更责任人；唯一工程来源规则已完成。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n02>)<br>[source-document-inventory.md](<docs/00-project/source-document-inventory.md>)、[document-conversion-plan.md](<docs/00-project/document-conversion-plan.md>) |
| S1-N03 / P0<br>步4,6,10,11<br>业务/安全/架构（实际姓名待定） | 术语、业务规则与状态参数细化<br>待落实实际条件及对应交付 | 确定风险/人工阈值、RETURNED后继、首发未知、审批目的与回流/保留规则的适用参数和例外。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n03>)<br>[glossary.md](<docs/00-project/glossary.md>)、[task-state-machine.md](<docs/05-workflows/task-state-machine.md>) |
| S1-N04 / P0<br>步7,8,12,14,19,21<br>架构/前后端/算法/测试（实际姓名待定） | 需求到内部处理与结果读取的语义闭环<br>待落实实际条件及对应交付 | 13项契约缺口和真实业务实现/联调按对应任务继续；正式规则需实际依据。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n04>)<br>[requirement-processing-map.md](<docs/00-project/requirement-processing-map.md>)、[source-section-map.md](<docs/00-project/stage-one/source-section-map.md>) |
| S1-N05 / P0<br>步9,18<br>业务验收/测试/算法/运维（实际姓名待定） | 可执行的指标和验收测量协议<br>待落实实际条件及对应交付 | 补真实封存样本/分层数量、正式目标、负载/资源/版本，实施对应真实验收。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n05>)<br>[non-functional-requirements.md](<docs/01-requirements/non-functional-requirements.md>)、[acceptance-criteria.md](<docs/09-testing/acceptance-criteria.md>) |
| S1-N06 / P0<br>步15<br>数据/业务授权/算法（实际姓名待定） | 数据集计数、标签和可用输入清单<br>待落实实际条件及对应交付 | 落实来源/用途材料、标签版本/质检、原件与派生/内容簇计数及独立封存集规则；盘点实际可用样本。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n06>)<br>[dataset-catalog.md](<docs/07-datasets/dataset-catalog.md>)、[annotation-specification.md](<docs/07-datasets/annotation-specification.md>) |
| S1-N07 / P0<br>步17,19,23<br>项目计划/各研发负责人（实际姓名待定） | 人员投入、实际进度和分期执行台账<br>待落实实际条件及对应交付 | 实际人员/投入、剩余工时、计划起点/工作日历和数据/GPU到位日未提供，实际日历排期待补。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s1-n07>)<br>[backlog.yaml](<tasks/backlog.yaml>)、[dependency-report.md](<tasks/dependency-report.md>) |

### 第2阶段

| 编号/原步骤/责任角色 | 工作及已有状态 | 仍需完成 | 文档与关闭标准 |
| --- | --- | --- | --- |
| S2-N01 / P0<br>步19<br>架构/前后端/算法/测试（实际姓名待定） | 整体接口流程和必要服务契约<br>待落实实际条件及对应交付 | 其余业务操作和真实身份/来源/审批规则等正式接入仍需实施验证；已有子范围不重记为未实现，也不据此关闭全部13项正式缺口。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n01>)<br>[interface-gap-register.md](<docs/03-api/interface-gap-register.md>)、[contract-generation.md](<docs/03-development/contract-generation.md>) |
| S2-N02 / P0<br>步7<br>数据库/后端/安全（实际姓名待定） | 业务数据库访问层与升级迁移<br>待落实实际条件及对应交付 | 按剩余任务补齐所有业务访问和逐表场景、生产升级/回退/特权边界验证；初始化SQL不能代替实际迁移，也不把现有隔离验证当正式生产部署。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n02>)<br>[database-design.md](<docs/04-database/database-design.md>)、[poc-database.md](<docs/04-database/poc-database.md>) |
| S2-N03 / P0<br>步9,19,20<br>后端/算法/测试（实际姓名待定） | 完整任务编排、取消与多worker故障<br>待落实实际条件及对应交付 | 实施实际调度器与多worker消息故障演练；当前8数据库竞争者不是8Celery worker，全业务DAG未运行。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n03>)<br>[task-state-machine.md](<docs/05-workflows/task-state-machine.md>)、[migrations-and-events.md](<docs/03-development/migrations-and-events.md>) |
| S2-N04 / P0<br>步15<br>身份平台/业务安全/后端（实际姓名待定） | 正式身份与案件/单位隔离<br>待落实实际条件及对应交付 | 提供真实issuer/密钥或获准身份协议及用户/单位/案件映射，再验证签验、撤销、用途及正式权限策略。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n04>)<br>[security-baseline.md](<docs/02-architecture/security-baseline.md>)、[permission-matrix.md](<docs/08-security/permission-matrix.md>) |
| S2-N05 / P0<br>步1,2,8,16<br>Linux及Docker运维/资源管理（实际姓名待定） | 项目配额与研发数据卷容量<br>待落实实际条件及对应交付 | 补实际扩容维护/整盘备份与恢复记录、项目独占配额和维护人；数据/权重/GPU授权及正式资源验收仍需落实。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n05>)<br>[resource-readiness-snapshot.json](<docs/00-project/validation/resource-readiness-snapshot.json>)、[resource-and-team-inventory.md](<docs/02-architecture/resource-and-team-inventory.md>) |
| S2-N06 / P0<br>步12,13<br>数据/算法/GPU运维（实际姓名待定） | 业务模型、OCR/ASR及GPU验证<br>待落实实际条件及对应交付 | 提供有用途授权的数据目录、权重许可/来源/摘要、实际GPU与驱动，实施逐能力训练/推理和独立封存盲测；M15合成CPU不代替业务能力。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n06>)<br>[model-catalog.yaml](<docs/06-algorithms/model-catalog.yaml>)、[model-evaluation.md](<docs/06-algorithms/model-evaluation.md>) |
| S2-N07 / P1<br>步14<br>媒体/算法/后端/测试（实际姓名待定） | 真实媒体、VFR和全时间轴链路<br>待落实实际条件及对应交付 | 实际授权媒体的多编码/VFR/缺模态/裁剪/转码链路及OCR/ASR、长视频性能仍需实现和实测；本轮仅自建夹具。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n07>)<br>[media-timestamp-report.json](<docs/00-project/validation/media-timestamp-report.json>)、[TB-ADR-010-media-processing.md](<docs/02-architecture/architecture-decisions/TB-ADR-010-media-processing.md>) |
| S2-N08 / P1<br>步10,11<br>检索/算法/后端/测试（实际姓名待定） | 中文/规模化检索与传播图验证<br>待落实实际条件及对应交付 | 确定正式中文分词/排序选型，实施实际大索引/向量及传播图业务、授权过滤和规模性能；4条文本不是业务检索指标。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n08>)<br>[technical-validation-report.md](<docs/02-architecture/technical-validation-report.md>)、[media-query-report.json](<docs/00-project/validation/media-query-report.json>) |
| S2-N09 / P0<br>步8,15<br>业务审核/安全/后端/存储（实际姓名待定） | 正式安全与证据防篡改机制<br>待落实实际条件及对应交付 | 落实双人审批适用规则、可信时间/签名、保留期、WORM/密钥及管理员边界，实施下载每次授权核验和到期/撤销演练。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n09>)<br>[security-baseline.md](<docs/02-architecture/security-baseline.md>)、[audit-requirements.md](<docs/08-security/audit-requirements.md>) |
| S2-N10 / P1<br>步8,16<br>运维/数据库/安全/测试（实际姓名待定） | 生产灾备、PITR和密钥恢复<br>待落实实际条件及对应交付 | 提供真实异地目标和密钥恢复授权、批准RPO/RTO；实施全业务异机恢复及对账，不能用开发冷备结果证明生产灾备。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n10>)<br>[development-backup-restore.md](<docs/10-deployment/development-backup-restore.md>)、[development-recovery-report.json](<docs/00-project/validation/development-recovery-report.json>) |
| S2-N11 / P0<br>步1,17<br>技术/软件准入/许可审查/安全（实际姓名待定） | 支持版本、OS物料和离线交付<br>待落实实际条件及对应交付 | 按TB-ADR-002验证3.13主候选/3.12备选或有实际维护依据的3.10例外，落实精确生产Python/OS、依赖/模型/CPU-GPU兼容、新锁/全CI与准入决定；补未托管二进制/FFmpeg源码与notices、模型许可、漏洞扫描及离线交付；未自动安装或升级当前环境。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n11>)<br>[environment-constraints.md](<docs/02-architecture/environment-constraints.md>)、[licenses.md](<docs/02-architecture/licenses.md>) |
| S2-N12 / P1<br>步21,22,23<br>仓库管理/构建发布/安全（实际姓名待定） | CI组织治理与受控制品交付<br>待落实实际条件及对应交付 | 落实私有仓库保护功能套餐/管理员配置、签名与离线镜像库/依赖缓存/保留策略；运行中镜像缺失须先重新构建验真再导出。 | [前置条件、全部证据及关闭标准](<docs/00-project/remaining-work-navigation.md#s2-n12>)<br>[repository-governance-snapshot.json](<docs/00-project/validation/repository-governance-snapshot.json>)、[ci-cd.md](<docs/03-development/ci-cd.md>) |

已完成的S1-N01版式核验及19项全部已有证据在总导航保留，避免重新列为未开展。正式输入冻结（第一阶段22—24步）和技术冻结（第二阶段22—23步）仍NOT_FROZEN，实际决定/责任人及适用范围需落实。

资源/身份/授权数据和实际责任人填写[实际输入表](<docs/03-development/stage-two-external-inputs.json>)；人员/实际排期填写[人员排期输入](<docs/00-project/execution-planning-inputs.json>)。170业务任务后续按[实施计划](<docs/03-development/stage-two-implementation-plan.md>)推进。
<!-- phase-remaining-navigation:end -->

## 运行

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py310/bin/python scripts/dev.py help
/opt/conda/glwy/envs/py310/bin/python scripts/dev.py setup
/opt/conda/glwy/envs/py310/bin/python scripts/dev.py dev
```

统一入口为`/opt/conda/glwy/envs/py310/bin/python scripts/dev.py <命令>`。Windows默认使用`& .\scripts\dev.ps1 help`经SSH协调同一Linux py310。当前服务器未安装make；Makefile是已有make环境的可选别名，本机验证使用上述Python等价入口。dev默认检查原7服务；clean默认预览两个缓存目录。共享服务器的构建/完整集成须显式`--allow-stack-changes`且满足卷内容量保护，若实时卷容量低于保护值则拒绝执行，历史99%快照不能代替当前容量核验；GitHub隔离CPU Runner执行完整门禁。详细安装、工具层和验证见[CONTRIBUTING.md](CONTRIBUTING.md)。

页面在服务器回环地址 `http://127.0.0.1:14180`；从本机通过SSH转发访问。启动前提、首次复建、研发令牌取得方法和停止操作见[运行手册](docs/10-deployment/development-runbook.md)。秘密与权重在仓库外/命名卷中，不入Git。

页面上传自建PNG/JPEG→S3版本化原件和独立分析副本→PostgreSQL事务任务/outbox→RabbitMQ→Celery→独立PyTorch CPU推理→结果保存与展示。模型synthetic-cpu-encoder/demo-1真实训练和推理、mock=false，是8维合成工程验证模型，不是SSCD或正式业务模型。

## 阶段材料与阅读顺序

| 阶段 | 工作范围 | 当前入口与状态 |
| --- | --- | --- |
| 第一阶段 | 24步，来源归档→需求/契约/数据/任务/测试→评审与输入冻结 | [24步实际状态](docs/00-project/stage-one/steps-and-deliverables.md)、[第一阶段材料导航](docs/00-project/stage-one/README.md)；候选已整理，正式NOT_FROZEN |
| 第二阶段 | 23步，环境/资源→选型与版本→最小工程→CI→技术评审与冻结 | [23步实际状态](docs/03-development/stage-two-readiness.md)、[接口与数据库文件导航](docs/02-architecture/technical-baseline.md#接口与数据库文件导航)、[整体接口](docs/03-api/README.md)、[业务数据库](docs/04-database/README.md)；开发工程/CI已验证，正式NOT_FROZEN |
| 第三阶段 | 16步，仓库治理/目录→工作环境/质量/最小连通性→启动/CI→实际验证和环境冻结 | [16步状态与导航](docs/03-development/stage-three/readiness.md)、[实际验证](docs/03-development/development-environment-validation-report.md)；正式NOT_FROZEN |

先核对第一阶段输入与来源，再阅读第二阶段技术执行依据；[阶段衔接](docs/00-project/stage-one/handoff.md)明确哪些输入由实际工程消费。24步、23步、第三阶段16步与170研发任务分别编号。

第二阶段已完成环境盘点、py310版本锁定、最小工程和扩展CI工程门禁配置；代表性权限/中文查询、VFR媒体和软件物料验证见[23步状态](docs/03-development/stage-two-readiness.md)及[交付对照](docs/03-development/stage-two-completion-matrix.md)。后续按[实施计划](docs/03-development/stage-two-implementation-plan.md)和[实际输入表](docs/03-development/stage-two-external-inputs.json)推进，正式冻结仍未完成。

第一阶段已完成[原件内容核对](docs/00-project/stage-one/source-content-audit.md)、[955处来源章节映射](docs/00-project/stage-one/source-section-map.md)、[33项具体评审清单](docs/00-project/review-package/README.md)和[当前候选输入摘要](docs/00-project/stage-one/input-baseline-candidate.md)。图表版式、36需求技术语义、24测量协议及170任务容量排期的文档工作已完成，范围见[核验记录](docs/00-project/stage-one/four-item-completion.md)；[工程输入控制](docs/00-project/stage-one/remaining-work-completion.md)已接入现有状态表。实际人员、日期、正式规则和真实验收仍按对应待办落实。

第三阶段[16步及57条验收实际状态](docs/03-development/stage-three/readiness.md)集中展示两份归档手册、仓库治理、开发命令、Codex项目配置、独立工具层、三服务模拟夹具及脱敏日志/依赖故障验证；每条要求分别说明证据范围和缺项，正式开发环境冻结和平台权限仍按实际条件判断。

## 文档入口

- [单文档完整需求说明](docs/01-requirements/functional-requirements.md)：36条业务需求详细行为、170任务全文展开、规则/角色/场景、非功能与验收测量，以及开发关联和未决条件。
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

开发5表（含审计和迁移账本）与正式62表/825字段设计分开；仅单固定测试案件。正式身份/案件隔离、审批、审计、WORM、业务模型/GPU、20/100并发、业务中文检索/大型索引、生产灾备/密钥恢复和生产准入仍需后续验证。Linux服务器上的Docker虚拟机研发卷最新容量按资源快照和开发准入说明读取；大体积构建/权重素材写入前先落实容量。宿主空闲、Windows本地D盘与GitHub容量分别判断。

源Word及其SHA256保持；Git保存本轮研发快照，origin采用用户提供私有GitHub，没有创建已批准生产基线标签。同步证据见docs/00-project/server-sync-receipt.json。

现有1.1工程的使用要求见[迁移事件手册](docs/03-development/migrations-and-events.md)、[开发冷恢复](docs/10-deployment/development-backup-restore.md)与[剩余条件/关闭标准](docs/03-development/stage-two-gap-register.md)。

## 整体接口详细入口

[系统整体接口说明](docs/03-api/system-interface-specification.md)、[53份逐操作/12模块导航](docs/03-api/detailed-interface-index.md)、[83组件字段](docs/03-api/data-structures.md)、[34内部能力](docs/03-api/inference-interfaces.md)已显式整理。第二阶段第19步保留PoC实测，整体接口仍有[13项开放缺口](docs/03-api/interface-gap-register.md)；候选路径不可调用，未标全系统接口冻结。

## 审批之外的剩余工作

[两阶段19项统一清单](docs/00-project/phase-readiness-register.md)列第一阶段7项、第二阶段12项的资料/设计/资源/实现/验证及完成标准；[36需求处理与读取映射](docs/00-project/requirement-processing-map.md)保持原主追踪，逐条技术语义已复核，正式规则/实现与运行待对应任务核验。审批不能代替这些工作，后续完整业务研发与本阶段技术设计分别安排。
