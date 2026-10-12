# 受理批准审计导出：exportAudit

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `c3471938106ec4211159d46b93c972416c2a678cd967214b2d23c48a12d8b2e7`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/audit/exports`；operationId=`exportAudit`；源指针=`/paths/~1audit~1exports/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

受理批准审计导出；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`audit.export`。

核验审计组织/案件范围；case_id=null不是全库许可，跨范围策略待确认。

来源任务：[T018 开发审计查询页面与接口](../../../tasks/frontend/T018.md)。

关联需求：FR-OPS-001、ER-T018、NFR-SEC-001、NFR-AUDIT-001；关联候选表：audit_export、audit_event。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/AuditExport`；字段与完整约束见[数据结构](../data-structures.md#auditexport)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| start_at | 必须 | string; format="date-time" | 候选字段来源：audit_export.start_at：审计导出查询的起始时刻；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| end_at | 必须 | string; format="date-time" | 候选字段来源：audit_export.end_at：审计导出查询的结束时刻，必须与起始时刻构成有效区间；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：audit_event.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；audit_export.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：audit_export.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：audit_export.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "start_at": "2030-01-01T00:00:00Z",
  "end_at": "2030-01-01T00:00:00Z",
  "case_id": "ce31de4c-90ca-5d69-afb1-8b969e0dd246",
  "purpose": "synthetic-v1",
  "approval_id": "148763f3-12d6-5478-a7cb-b6c0c3e67ad4"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 202 | 契约成功响应；异步受理不代表结果完成 | application/json: ActionAck | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`ActionAck`，详细字段见[数据结构](../data-structures.md#actionack)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| object_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键；audit_event.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_export.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_release.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；audit_export.state：审计导出作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；index_registry.state：索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；model_release.state：模型发布包的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.request_id：贯穿接口、任务和审计的请求追踪标识；不充当权限凭证。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "object_id": "cb2fc0da-fcb0-56f5-b97a-5b3ac871a487",
  "version": 1,
  "state": "synthetic-v1",
  "request_id": "475ac694-56aa-515f-9ef7-16e7fc2db444"
}
```

202返回ActionAck，没有导出状态/产物下载接口IF-G06；不能将object_id当已生成文件地址。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/start_at | audit_export.start_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/end_at | audit_export.end_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/case_id | audit_event.case_id, audit_export.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/purpose | audit_export.purpose | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/approval_id | audit_export.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_id | audit_event.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | audit_event.row_version, audit_export.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | audit_export.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/request_id | audit_event.request_id | 请求追踪/审计，不作为业务对象ID |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TV-T008-E、TV-T008-N、TV-T011-E、TV-T011-N、TV-T012-E、TV-T012-N、TV-T013-E、TV-T013-N、TV-T014-E、TV-T014-N、TV-T015-E、TV-T015-N、TV-T016-E、TV-T016-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N、TV-T118-E、TV-T118-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
