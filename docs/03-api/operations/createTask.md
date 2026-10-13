# 受理分析任务：createTask

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/analysis/tasks`；operationId=`createTask`；源指针=`/paths/~1analysis~1tasks/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

受理分析任务；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`task.create`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T034 实现任务创建接口](../../../tasks/backend/T034.md)。

关联需求：ER-T034、NFR-AVAIL-001；关联候选表：analysis_task、outbox_event、idempotency_record。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/TaskCreate`；字段与完整约束见[数据结构](../data-structures.md#taskcreate)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；idempotency_record.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；outbox_event.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| scene | 必须 | string; enum=["accident_rumor", "harmful_content", "repost_tamper_trace"] | 候选字段来源：analysis_task.scene：分析场景编码，用于选择任务处理流程；实际场景词表仍依业务配置。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：analysis_task.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| modules | 必须 | array; minItems=1; uniqueItems=true; items=string; enum=["INGEST", "RESOURCE", "MEDIA", "RISK", "FORENSIC", "IMGRET", "VIDTRACE", "ORIGIN", "PROPAGATION", "CLAIM", "REVIEW", "OPS"] | 候选字段来源：analysis_task.modules：任务请求运行的模块编码列表；服务端检查模块是否允许、依赖是否满足。来源引用不是写入许可，完整处理按操作核验。 |
| priority | 必须 | string; enum=["low", "normal", "high"] | 候选字段来源：analysis_task.priority：调度优先级；只影响排队策略，不改变权限或审核要求。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "39848f72-9889-59ba-a4cd-37c53594601e",
  "asset_id": "7ac60435-47ca-5243-99bb-929d3c4b2b33",
  "scene": "accident_rumor",
  "policy_version": "synthetic-v1",
  "modules": [
    "INGEST"
  ],
  "priority": "low"
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

202返回task_id/status_url；GET /api/v1/analysis/tasks/{id}查询。任务成功、人工复核、报告批准是不同条件。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | analysis_task.case_id, idempotency_record.case_id, outbox_event.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/asset_id | analysis_task.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/scene | analysis_task.scene | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/policy_version | analysis_task.policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/modules | analysis_task.modules | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/priority | analysis_task.priority | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/task_id | analysis_task.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | analysis_task.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/status_url | 服务层输入/聚合，不直接生成数据库列 | 根据task_id生成相对查询URL |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TV-T031-E、TV-T031-N、TV-T032-E、TV-T032-N、TV-T033-E、TV-T033-N、TV-T034-E、TV-T034-N、TV-T035-E、TV-T035-N、TV-T036-E、TV-T036-N、TV-T037-E、TV-T037-N、TV-T038-E、TV-T038-N、TV-T039-E、TV-T039-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
