# 申请样本训练回流：requestFeedback

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/feedback/samples`；operationId=`requestFeedback`；源指针=`/paths/~1feedback~1samples/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

申请样本训练回流；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`feedback.request`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T108 实现样本纠错与回流审批](../../../tasks/backend/T108.md)。

关联需求：FR-REVIEW-001、ER-T108、NFR-AUDIT-001、NFR-DATA-001；关联候选表：feedback_request、approval_request。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/Feedback`；字段与完整约束见[数据结构](../data-structures.md#feedback)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；feedback_request.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| finding_id | 必须 | string; format="uuid" | 候选字段来源：feedback_request.finding_id：申请回流的风险发现标识；用途审批通过也须另核验来源授权。来源引用不是写入许可，完整处理按操作核验。 |
| label_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：feedback_request.label_version：本次标注使用的标签体系版本。来源引用不是写入许可，完整处理按操作核验。 |
| label | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：feedback_request.label：人工确认或申请使用的训练标签；不可直接把模型预测视为真值。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | const="training" | 候选字段来源：approval_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符；feedback_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| source_authorization_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：feedback_request.source_authorization_ref：允许该素材用于指定回流或训练用途的来源授权记录引用。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：approval_request.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "a368a201-5630-569a-bda7-5c719394d43c",
  "finding_id": "bcfbfa39-c0c7-51a5-bd28-c18c7934863a",
  "label_version": "synthetic-v1",
  "label": "synthetic-v1",
  "purpose": "training",
  "source_authorization_ref": "synthetic-v1",
  "reason": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: FeedbackRecord | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`FeedbackRecord`，详细字段见[数据结构](../data-structures.md#feedbackrecord)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| feedback_id | 必须 | string; format="uuid" | 候选字段来源：feedback_request.feedback_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证；feedback_request.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["REQUESTED", "APPROVED", "REJECTED", "REVOKED", "APPLIED"] | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；feedback_request.state：纠错训练用途申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；feedback_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "feedback_id": "6f9c8d09-833d-5df1-826c-4225d4f166c2",
  "approval_id": "f714d553-db29-5fb6-8bdb-8c85ac04082f",
  "state": "REQUESTED",
  "version": 1
}
```

201返回申请/审批关联，不代表已进训练集。用途/划分分别核验，禁止封存测试集回流；状态查询见IF-G04。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | approval_request.case_id, feedback_request.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/finding_id | feedback_request.finding_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/label_version | feedback_request.label_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/label | feedback_request.label | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/purpose | approval_request.purpose, feedback_request.purpose | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/source_authorization_ref | feedback_request.source_authorization_ref | 用途授权引用；服务端核验，不信任文本即批准 |
| request/reason | approval_request.reason | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/feedback_id | feedback_request.feedback_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/approval_id | approval_request.approval_id, feedback_request.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | approval_request.state, feedback_request.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | approval_request.row_version, feedback_request.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-REVIEW-001-E、TC-REVIEW-001-N、TV-T008-E、TV-T008-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T021-E、TV-T021-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N、TV-T109-E、TV-T109-N、TV-T110-E、TV-T110-N、TV-T111-E、TV-T111-N、TV-T112-E、TV-T112-N、TV-T126-E、TV-T126-N、TV-T127-E、TV-T127-N、TV-T156-E、TV-T156-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
