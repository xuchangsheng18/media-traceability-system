# 第二阶段接口与数据库文件导航

2026-10-13。该页承接第二阶段第7步（数据库）、第19步（接口/事件）和第20步（最小工程）。整体接口/62表业务设计与已运行PoC/5表分别导航；不从设计文件推导正式部署。

## 阅读顺序

1. 整体接口说明→逐操作目录→OpenAPI/模型Schema→字段与权限/版本/事件规则。
2. 数据库设计→ER→字典/SQL→逐字段来源→接口映射→任务引用/校验。
3. 实际PoC API/5表与迁移→相应运行证据，再核对13接口缺口和后续业务迁移/RLS。

## 整体接口及契约文件

| 内容 | 文件入口 | 含义和使用要求 |
| --- | --- | --- |
| 整体接口范围 | [系统整体接口说明](<../03-api/system-interface-specification.md>) | 七类接口面、53业务操作/83组件/34能力、服务边界和完整性要求。 |
| 逐操作/模块目录 | [53操作与12模块导航](<../03-api/detailed-interface-index.md>) | 跳转每个操作的参数、请求/响应、权限、版本、异步终态、样例和任务引用。 |
| 业务结构唯一源 | [业务OpenAPI](<../03-api/openapi.yaml>) | 外部接口结构源；候选53操作，不代表全部已实现。 |
| 内部调用入口唯一源 | [内部推理OpenAPI](<../03-api/inference-openapi.yaml>) | 内部调用入口；能力请求/响应结构以schemas/model为源。 |
| 业务字段说明 | [83组件字段说明](<../03-api/data-structures.md>) | 必填/可空/枚举/约束及完整Schema的只读派生。 |
| 内部能力字段 | [34能力接口说明](<../03-api/inference-interfaces.md>) | 能力路径/请求/响应/身份/来源摘要；业务模型未据此验收。 |
| 能力Schema源 | [68模型Schema](<../../schemas/model>) | 34请求+34响应的唯一能力结构来源；不作为业务HTTP的第二结构源。 |
| 共用行为 | [接口共用规则](<../03-api/common-interface-rules.md>) | 鉴权、追踪、分页、幂等、ETag、版本、异步、错误及Range。 |
| 服务与事件 | [服务/事件契约](<../03-api/service-and-event-contracts.md>) | 边界及研发事件；完整业务调度实施另判。 |
| 工作流/结果事件 | [工作流契约](<../05-workflows/workflow-contracts.md>) | 候选DAG、节点结果、7类域事件和运行版本身份。 |
| 严格历史读取 | [历史结果读取](<../03-api/historical-result-reading.md>) | 7现有操作的精确task/run/result选择与不回退最新规则，业务联调未完成。 |
| 接口缺口 | [13项接口缺口](<../03-api/interface-gap-register.md>) | 未冻结设计/实现和关闭标准；拟议路径不可调用。 |
| 接口追踪 | [接口来源索引](<../03-api/interface-catalog.json>) | 操作/模块/能力的来源和任务/测试引用，非运行证明。 |
| 样例 | [请求响应样例](<../03-api/examples>) | 结构校验夹具，不能充当实际业务结果。 |
| 生成类型 | [4份生成类型](<../../shared-contracts/generated>) | 由唯一来源生成，禁止反向手改Schema；结构约束仍需运行验证。 |
| 已运行研发API | [PoC接口及范围](<../03-api/poc-api.md>) | 固定测试案件/图片上传/任务/合成CPU入口，与53操作设计分开。 |

## 业务数据库及研发迁移文件

| 内容 | 文件入口 | 含义和使用要求 |
| --- | --- | --- |
| 业务设计与关系 | [数据库设计](<../04-database/database-design.md>) | 62表候选职责、身份与关系，业务访问层尚未全部实施。 |
| 业务字段字典 | [62表/824字段字典](<../04-database/data-dictionary.md>) | 逐字段类型、空值、约束和来源；不从一句来源契约推导已确认业务规则。 |
| 空库DDL唯一源 | [初始化SQL](<../04-database/initial-schema.sql>) | 用于新隔离空库；不得当既有数据库增量升级脚本。 |
| ER关系 | [ER图](<../04-database/er-diagram.md>) | 结合复合外键、案件范围及设计阅读；关系图不是部署证明。 |
| 表/字段机器目录 | [表目录](<../04-database/table-catalog.json>) | 62表824字段的可检查结构，须与SQL/字典一致。 |
| 逐字段来源 | [字段来源契约](<../04-database/field-provenance.json>) | 精确源文件/指针与来源性质；说明cluster_id、asset_id、rank等依据。 |
| 接口字段投影 | [接口—数据库映射说明](<../04-database/api-field-mapping.md>) | 区分请求/响应、列投影和运行时组合，不以同名认定同一对象。 |
| 映射机器源 | [接口字段映射JSON](<../04-database/api-field-mapping.json>) | 配合CSV查看精确结构引用和列/投影关系。 |
| 映射表格 | [接口字段映射CSV](<../04-database/api-field-mapping.csv>) | 便于逐字段对照；同步JSON/SQL/Schema，不能独立成为第二定义源。 |
| 表与任务 | [62表任务引用](<../04-database/table-task-usage.md>) | 候选职责、源追踪与任务卡引用；不代表已被实际代码使用。 |
| 首发排序规则 | [首发候选排序](<../04-database/first-source-ranking.md>) | cluster/asset关系、1—3名次、去重、并列/未知和观察范围。 |
| 数据库检查 | [SQL验证范围与命令](<../04-database/database-validation.md>) | 空库/约束/反例测试，不当所有业务访问层或生产升级通过。 |
| 实际研发库 | [研发5表说明](<../04-database/poc-database.md>) | 实际PoC assets/jobs/outbox/audit/迁移账本，区别于62表业务设计。 |
| 已运行研发迁移 | [PoC版本迁移](<../../backend/migrations>) | 0001/0002仅针对开发库；正式62表迁移仍需按任务实施。 |
| 迁移/事件机制 | [迁移与旧租约保护](<migrations-and-events.md>) | 版本账本、摘要、事件/追踪与租约fencing；非生产RLS完整部署。 |
| 隔离权限原型 | [RLS/历史追加原型](<../04-database/authorization-isolation-prototype.md>) | 代表性临时库验证；正式身份、全业务表和特权防篡改未因此完成。 |

## 相互对应与实际状态

API字段须按[字段投影](<../04-database/api-field-mapping.json>)定位数据库列/运行组合，再用[字段来源](<../04-database/field-provenance.json>)核对来源文件/指针；模型结构不与业务HTTP结构混为一份。SQL/字典/Schema/映射/生成类型变化须同步。

cluster_id、asset_id、rank等字段的来源契约是逐字段可追踪的结构/设计依据，不能靠“见来源契约”一句作为实际约束说明。请联合阅读字典、field-provenance、映射和首发排序规范。

53业务操作/83组件/34能力、62表824字段是当前候选设计；PoC和代表性隔离实验有独立证据，完整业务API/62表访问迁移/RLS未全部实现。13接口缺口仍开放，初始化SQL不得直接作用于既有库。状态见[第二阶段23步实际状态](<stage-two-readiness.md>)、[12项补齐与剩余](<stage-two-completion-matrix.md>)和[两阶段总导航](<../00-project/remaining-work-navigation.md>)。

证据：[interface-documentation-report.json](<../00-project/validation/interface-documentation-report.json>)、[database-contract-report.json](<../00-project/validation/database-contract-report.json>)、[database-foundation-report.json](<../00-project/validation/database-foundation-report.json>)、[migration-fencing-report.json](<../00-project/validation/migration-fencing-report.json>)、[stage-two-isolation-report.json](<../00-project/validation/stage-two-isolation-report.json>)。检查通过范围与实际业务验收分别判断。
