# 服务调用、事件和存储契约

整体接口包含前端HTTP、服务调用、消息、版本化对象和外部适配器。权威来源见[整体说明](system-interface-specification.md)；全业务消息和第三方协议仍有开放缺口。

## 实际研发链路

浏览器经/poc/assets和/poc/jobs访问backend；backend写S3固定版本对象，在事务中写独立开发5表的任务/outbox；发布器持久发布Rabbit消息并确认；Celery从DB原子领取租约，调用内部M15合成CPU推理，核验结构/运行身份后按租约token/run/attempt条件写回，追加审计；浏览器轮询/poc/jobs/{job_id}。

| 调用/载体 | 身份/结构 | 版本/故障语义 | 当前范围 |
| --- | --- | --- | --- |
| 用户→backend | 研发Bearer；/poc/openapi.json实际描述 | /poc/jobs幂等；固定研发案件 | 正式分片/取消/DAG/审批未实现 |
| outbox→worker | [poc.analysis.requested.v1](../../schemas/events/poc.analysis.requested.v1.schema.json) | 保留event_id/request_id；持久发布确认；DB幂等领取及旧租约拒绝 | 一个PoC事件，不是12模块总线 |
| worker→inference | 独立内部令牌，M15请求/响应Schema | 模型/运行/请求身份、deadline及固定ObjectRef，再核验输出 | 真实8维合成CPU，不是SSCD/业务准确率 |
| 服务→S3 | 私有适配器，version_id/sha256 | 原件保留、分析副本独立、读取摘要对账 | 研发版本与冷恢复实测，生产WORM另验收 |
| 服务→SQL | 应用角色、事务、迁移账本/摘要 | 任务/outbox事务、租约、追加审计 | 正式62表/RLS/审批不能当PoC已完成 |

## PoC事件字段

| 字段 | 源类型/必须 | 含义与核验 |
| --- | --- | --- |
| schema_version | string const 1.0.0，必须 | 消息结构版本，独立于运行/源码/模型版本 |
| event_type | string const poc.analysis.requested.v1，必须 | 分析受理事件，不用于其他模块 |
| event_id | UUID，必须 | 持久事件身份，重发保留，不能形成重复业务效果 |
| occurred_at | date-time，必须 | 事件时间，不是平台发布时间/可信固化时间证明 |
| request_id | UUID，必须 | 原始任务追踪，贯穿worker/推理/结果/审计 |
| trace_origin | api或migration_job_id，必须 | 正常提交或旧记录迁移的追踪来源 |
| case_id | UUID，必须 | 研发案件引用，格式不等于权限 |
| producer | backend.poc或migration.poc.v1，必须 | 限定标签，不等同认证主体 |
| payload.job_id | UUID，必须 | DB任务身份；消费时核验状态/版本/范围 |
| payload.asset_id | UUID，必须 | 已登记资产，不自由指定对象URL |

信封/payload均additionalProperties=false。租约和模型输入从有效DB任务核验，不把租约token或秘密装入消息。旧UUID消息仅为查DB恢复信封的迁移桥接，不是正式新格式。JSON序列化、持久发布/确认、故障重投和原子领取有各自作用，不能由消息Schema推导“恰好一次业务执行”。

全业务节点、优先级、取消/重算、结果事件、真实多worker超时/续租/乱序/死信见IF-G11；身份/授权撤销见IF-G07/08，平台签验/游标/字段转换见IF-G10。必要事件进入schemas/events单一结构源并生成类型，不虚构主题、消费方、外部URL或批准。

[3份类型生成与漂移检查](../03-development/contract-generation.md)是编译时声明；运行时还需Schema与业务语义/授权检查。实际结果见[技术验证](../02-architecture/technical-validation-report.md)，计划与实测分开。
