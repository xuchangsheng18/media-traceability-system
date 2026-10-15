# getReview：getReview

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/reviews/{id}`；operationId=`getReview`；源指针=`/paths/~1reviews~1{id}/get`。

实现范围：**DEV_PARTIAL**；真实数据库或显式适配端口已实现，默认未接入的权威依赖返回503；实际结果按本批测试记录。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取真实记录或执行明确授权的受控操作；具体边界见剩余接口实现说明。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`review.read`。

每次核验当前身份/功能权限和单位/案件范围；组织级策略不借用虚构案件。

来源任务：[T102 实现人工复核工作流](../../../tasks/backend/T102.md)、[T103 开发人工复核工作台](../../../tasks/frontend/T103.md)。

关联需求：；关联候选表：review_record、review_evidence。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: Review |  |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Review`，详细字段见[数据结构](../data-structures.md#review)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| review_id | 必须 | string; format="uuid" | 候选字段来源：review_evidence.review_id：所引用业务复核记录标识；review_record.review_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| reviewer_id | 必须 | string; format="uuid" | 候选字段来源：review_record.reviewer_id：执行本次业务复核的用户标识，需有对应功能和案件权限。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：review_record.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| expected_review_version | 必须 | integer; minimum=0 | 候选字段来源：review_record.review_version：针对结果形成的复核版本号，复核更正不能覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| decision | 必须 | string; enum=["confirm_candidate", "reject_candidate", "return_for_evidence", "request_rerun"] | 候选字段来源：review_record.decision：本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：review_record.comments：复核意见原文，说明证据取舍及处理理由，后续更正追加版本。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：review_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：review_record.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| review_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.review_version：针对结果形成的复核版本号，复核更正不能覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：audit_event.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；review_evidence.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；review_record.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "review_id": "ebd153a1-3451-520b-8290-d2abff1de521",
  "reviewer_id": "7ab90336-d2b1-5653-983c-33f75f7a3445",
  "task_id": "2a1ddf40-b898-521d-be36-5c473aa0e61c",
  "run_version": 1,
  "result_version": 1,
  "expected_review_version": 1,
  "decision": "confirm_candidate",
  "reason": "synthetic-v1",
  "evidence_ids": [
    "7426731a-c101-5ea4-86b6-1cc245e1dd81"
  ],
  "policy_version": "synthetic-v1",
  "review_version": 1,
  "created_at": "2030-01-01T00:00:00Z"
}
```

文档与路由不代表正式接入、真实模型或完整业务验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/review_id | review_evidence.review_id, review_record.review_id | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/reviewer_id | review_record.reviewer_id | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/task_id | review_record.task_id | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/run_version | review_record.run_version | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result_version | review_record.result_version | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/expected_review_version | review_record.review_version | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/decision | review_record.decision | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/reason | review_record.comments | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/evidence_ids | review_evidence.evidence_id | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/policy_version | review_record.policy_version | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/review_version | review_record.review_version | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/created_at | audit_event.created_at, review_evidence.created_at, review_record.created_at | 读取不可变复核记录：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
