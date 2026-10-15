# 系统整体接口设计说明

2026-10-12；第二阶段第19步整体设计与详细阅读入口。状态：DETAIL_DOCUMENTED_WITH_OPEN_CONTRACT_GAPS，正式NOT_FROZEN。第二阶段应明确整体服务边界、关键请求/响应/事件与共用规则，支持技术选型、最小验证和并行开发；不要求此时全部170任务的接口实现已完成。第一阶段提供候选输入，第二阶段补实际技术、服务调用与契约验证。

当前候选契约有73个外部操作、102个数据组件和34类模型能力。最新一批已补18个契约操作和已有12个操作的开发实现；实际挂载42个外部操作与1个内部入口，详见[剩余接口实现](../03-development/stage-three/remaining-interface-implementation.md)。正式条件继续开放。

## 阅读顺序

1. 本说明：整体服务边界和完整性判断。
2. [详细接口目录](detailed-interface-index.md)：73份逐操作说明、12模块导航。
3. [共用规则](common-interface-rules.md)：身份、请求头、参数、分页、状态/条件、错误/下载与版本。
4. [102个数据结构](data-structures.md)：字段、必填/可空、枚举/约束/组合及完整源Schema。
5. [34类内部能力](inference-interfaces.md)、[服务与消息](service-and-event-contracts.md)。
6. [13项接口缺口和拟补方案](interface-gap-register.md)：分别记录已纳入契约/实际挂载的技术子范围及未完成的正式条件。
7. [当前PoC实现](poc-api.md)：实际研发入口与实测范围，和正式业务候选分开。

## 系统接口边界

| 接口面 | 调用方 → 提供方 | 权威结构 | 当前范围 |
| --- | --- | --- | --- |
| 外部业务HTTP | 已授权客户端 → backend | [openapi.yaml](openapi.yaml)，/api/v1 | 73候选操作；独立业务工程42个实际挂载外部入口，PoC另含health；完整业务未验收 |
| 内部模型HTTP | worker/网关 → ai-services | [inference-openapi.yaml](inference-openapi.yaml)，独立serviceAuth；能力编辑源schemas/model | 一个参数化入口，34请求/响应分支；仅M15合成CPU实测 |
| 异步消息 | backend/outbox → Rabbit/Celery → worker | [PoC事件Schema](../../schemas/events/poc.analysis.requested.v1.schema.json) | 一个开发事件；新增取消请求/确认域事件及outbox、节点栅栏见IF-G11，完整业务DAG/消息部署仍未完成 |
| 版本化对象读写 | backend/worker → 私有S3适配器 | ObjectRef、固定version_id/sha256、存储ADR与适配器 | 用户下载经受控HTTP；不将永久S3链接当业务API |
| 关系数据访问 | backend/worker → PostgreSQL | [字典](../04-database/data-dictionary.md)、SQL/迁移、[API字段映射](../04-database/api-field-mapping.json) | 62表候选与5表PoC分开；数据库不是客户端直接访问的业务接口 |
| 正式身份/数据平台 | 权威提供方/适配器 ↔ backend | 实际提供方协议、主Q和批准范围 | 接入协议未取得；IF-G07/08/10，不编造URL或账号 |
| 离线训练/数据/发布包 | 数据/算法流水线 → 数据卡、模型发布候选 | schemas/dataset、model-catalog与数据集规范 | 不要求每个研发任务都有独立HTTP；用途/许可/测试集/发布批准仍须核验 |

12模块均保留三条业务需求。部分内部处理由统一任务/DAG触发，不能因为没有独立HTTP路径就删需求。主追踪有七条业务需求没有直接operation_ids：媒体解析与抽帧、风险多模态对齐、图片/视频取证计算、视频时序定位和高可信聚类；须继续核对内部能力、任务编排和结果读取是否闭合。

## 逐接口文件的要求

每个操作明确用途、方法/完整路径、operationId、源指针/摘要、状态、身份与功能/对象范围；列请求头/参数/体、必填与null差异、成功/失败HTTP、响应头/媒体类型/结构及结构样例；解释幂等/条件并发、异步下一步、版本/撤销，并关联任务、需求、候选表、字段处理和测试计划。

结构覆盖之外，还要证明用户流程闭合、异步终态可查询、当前权限可撤销、固定历史版本可读取。一个模块出现路径或Schema不能独立证明完整。

## 当前结论及变更要求

详细阅读文件已形成，现有唯一结构源和4份生成类型保持：business-api、inference-api、poc-event和workflow。类型来源与漂移检查见[契约生成](../03-development/contract-generation.md)。上传进度、审批/复核读取、反馈状态、发布/审计导出作业查询、历史运行、正式身份/授权同步及全业务消息仍有具体设计/实施缺口。第19步应标记“PoC验证、整体详细化、缺口开放”，不能标整体接口冻结、全系统联调或正式交付完成。

实施缺失操作时先确认边界，再更新唯一OpenAPI/事件Schema、operation-index、样例/字段映射、任务/需求/测试追踪及生成类型；新增数据库字段须迁移。正式权限、用途、指标和审批状态继续引用主Q与有效决定。

格式依据：[OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html)分别定义operationId、参数、请求体、响应和security；HTTP状态/条件/Range见[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，Problem结构见[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)。本轮沿用仓库版本，不自动升级技术锁。

首批独立业务工程已加入上传进度与分片GET，候选总数73、结构102；对应HTTP/事务逐项测试，正式身份/来源仍待实际平台接入。全部API、业务模型及生产验收不因这两项完成。实施入口见[首批计划](../03-development/stage-three/business-interface-implementation-plan.md)。
