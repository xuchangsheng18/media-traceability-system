# 请求取消任务：cancelTask

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `c3471938106ec4211159d46b93c972416c2a678cd967214b2d23c48a12d8b2e7`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/analysis/tasks/{id}/cancel`；operationId=`cancelTask`；源指针=`/paths/~1analysis~1tasks~1{id}~1cancel/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

请求取消任务；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`task.cancel`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T039 实现任务取消和退回重算](../../../tasks/backend/T039.md)、[T040 开发任务监控页面](../../../tasks/frontend/T040.md)。

关联需求：FR-OPS-002、ER-T039、ER-T040、NFR-AVAIL-001；关联候选表：analysis_task、task_event、outbox_event。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |
| If-Match | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/TaskAction`；字段与完整约束见[数据结构](../data-structures.md#taskaction)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：task_event.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |
| expected_run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；outbox_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；task_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "reason": "synthetic-v1",
  "expected_run_version": 1,
  "expected_version": 1,
  "approval_id": "18751be0-58d5-5391-9f5f-9df1f6d1f26a"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 202 | 契约成功响应；异步受理不代表结果完成 | application/json: Accepted | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 412 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 428 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Accepted`，详细字段见[数据结构](../data-structures.md#accepted)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.task_id：主键，由应用提供UUID；不视为访问凭证；task_event.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本；task_run.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["CREATED", "QUEUED", "RUNNING", "CANCEL_REQUESTED"] | 候选字段来源：analysis_task.state：分析任务当前投影的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| status_url | 必须 | string; pattern="^/api/v1/analysis/tasks/" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "task_id": "194f184a-50c0-5378-881c-c45cb624de83",
  "state": "CREATED",
  "status_url": "/api/v1/analysis/tasks/00000000-0000-4000-8000-000000000001"
}
```

202表示取消意图；继续查任务状态，对应运行确实CANCELLED才算停止，旧运行写回仍受fencing核验。

该接口声明If-Match：必须服务端原子核验对象版本；缺少条件428、旧版本412、状态不许可409。ETag绑定对象/聚合的精确范围仍按业务设计及缺口评审，body expected_version不能代替条件更新。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/reason | task_event.reason | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/expected_run_version | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/expected_version | analysis_task.row_version, outbox_event.row_version, task_event.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/approval_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/task_id | analysis_task.task_id, task_event.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | analysis_task.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/status_url | 服务层输入/聚合，不直接生成数据库列 | 根据task_id生成相对查询URL |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-002-E、TC-OPS-002-N、TV-T031-E、TV-T031-N、TV-T032-E、TV-T032-N、TV-T033-E、TV-T033-N、TV-T034-E、TV-T034-N、TV-T035-E、TV-T035-N、TV-T036-E、TV-T036-N、TV-T037-E、TV-T037-N、TV-T038-E、TV-T038-N、TV-T039-E、TV-T039-N、TV-T040-E、TV-T040-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
