# 提交人工复核记录：createReview

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/reviews`；operationId=`createReview`；源指针=`/paths/~1reviews/post`。

实现范围：**DEV_PARTIAL**；独立业务开发工程已挂载真实访问/校验；权威提供方未配置时拒绝，不提供生产模拟成功。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

提交人工复核记录；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`review.perform`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T102 实现人工复核工作流](../../../tasks/backend/T102.md)、[T103 开发人工复核工作台](../../../tasks/frontend/T103.md)。

关联需求：FR-PROPAGATION-003、FR-REVIEW-001、ER-T102、ER-T103、NFR-AUDIT-001；关联候选表：review_record、review_evidence、audit_event。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |
| If-Match | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/ReviewCreate`；字段与完整约束见[数据结构](../data-structures.md#reviewcreate)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：review_record.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| expected_review_version | 必须 | integer; minimum=0 | 候选字段来源：review_record.review_version：针对结果形成的复核版本号，复核更正不能覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| decision | 必须 | string; enum=["confirm_candidate", "reject_candidate", "return_for_evidence", "request_rerun"] | 候选字段来源：review_record.decision：本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：review_record.comments：复核意见原文，说明证据取舍及处理理由，后续更正追加版本。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：review_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：review_record.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "task_id": "de9f1aa5-09d4-575e-8825-f0989c723d6b",
  "run_version": 1,
  "result_version": 1,
  "expected_review_version": 1,
  "decision": "confirm_candidate",
  "reason": "synthetic-v1",
  "evidence_ids": [
    "eaa644c7-01e6-5c06-8b6d-836d045156e1"
  ],
  "policy_version": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: Review | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
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

201追加复核版本，绑定task/run/result/review；不替代报告导出或训练回流批准。工作台读取缺口IF-G03。

该接口声明If-Match：必须服务端原子核验对象版本；缺少条件428、旧版本412、状态不许可409。ETag绑定对象/聚合的精确范围仍按业务设计及缺口评审，body expected_version不能代替条件更新。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/task_id | review_record.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/run_version | review_record.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/result_version | review_record.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/expected_review_version | review_record.review_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/decision | review_record.decision | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/reason | review_record.comments | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/evidence_ids | review_evidence.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/policy_version | review_record.policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/review_id | review_evidence.review_id, review_record.review_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/reviewer_id | review_record.reviewer_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/task_id | review_record.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/run_version | review_record.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result_version | review_record.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/expected_review_version | review_record.review_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/decision | review_record.decision | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/reason | review_record.comments | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/evidence_ids | review_evidence.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/policy_version | review_record.policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/review_version | review_record.review_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/created_at | audit_event.created_at, review_evidence.created_at, review_record.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-PROPAGATION-003-E、TC-PROPAGATION-003-N、TC-REVIEW-001-E、TC-REVIEW-001-N、TV-T008-E、TV-T008-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T102-E、TV-T102-N、TV-T103-E、TV-T103-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
