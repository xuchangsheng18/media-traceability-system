# 创建审批申请：requestApproval

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/approvals`；operationId=`requestApproval`；源指针=`/paths/~1approvals/post`。

实现范围：**DEV_PARTIAL**；独立业务开发工程已挂载真实访问/校验；权威提供方未配置时拒绝，不提供生产模拟成功。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

创建审批申请；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`approval.request`。

按object_type/purpose核验组织或案件对象；模型发布可为组织级，操作确认不能等同业务批准。

来源任务：[T016 实现高风险操作二次确认](../../../tasks/platform/T016.md)、[T102 实现人工复核工作流](../../../tasks/backend/T102.md)、[T108 实现样本纠错与回流审批](../../../tasks/backend/T108.md)。

关联需求：FR-PROPAGATION-003、FR-REVIEW-001、FR-OPS-001、ER-T016、ER-T102、ER-T108、NFR-SEC-001、NFR-AUDIT-001、NFR-DATA-001；关联候选表：approval_request。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/ApprovalCreate`；字段与完整约束见[数据结构](../data-structures.md#approvalcreate)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：approval_request.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限。来源引用不是写入许可，完整处理按操作核验。 |
| object_type | 必须 | string; enum=["task", "report", "evidence_package", "feedback", "model_release", "operation"] | 候选字段来源：approval_request.object_type：审批或审计目标对象类型，决定object_id应指向哪种业务对象。来源引用不是写入许可，完整处理按操作核验。 |
| object_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批；approval_request.result_version：分析对象绑定结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; enum=["review", "seal", "report_export", "training_feedback", "model_release", "confirmation"] | 候选字段来源：approval_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_request.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：approval_request.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.run_version：分析对象绑定运行版本。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.result_version：分析对象绑定结果版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "07e676aa-d4bf-5691-b1a5-572139e5c6ae",
  "object_type": "task",
  "object_id": "975a5912-0412-5fd8-8a83-a17930f70057",
  "object_version": 1,
  "purpose": "review",
  "policy_version": "synthetic-v1",
  "reason": "synthetic-v1",
  "run_version": 1,
  "result_version": 1
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: Approval | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Approval`，详细字段见[数据结构](../data-structures.md#approval)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：approval_decision.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过；approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["REQUESTED", "APPROVED", "REJECTED", "RETURNED", "REVOKED", "EXPIRED", "INVALIDATED"] | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_decision.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批；approval_request.result_version：分析对象绑定结果版本；audit_event.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_decision.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析；approval_request.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 候选字段来源：approval_request.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| decision_actor_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：approval_decision.decision_actor_id：作出审批决定的用户标识，由认证上下文与职责分离规则核验。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.run_version：分析对象绑定运行版本。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.result_version：分析对象绑定结果版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "approval_id": "eea80c33-3db7-58e6-94f3-37e54d1cfe23",
  "state": "REQUESTED",
  "version": 1,
  "object_version": 1,
  "purpose": "synthetic-v1",
  "policy_version": "synthetic-v1",
  "expires_at": "2030-01-01T00:00:00Z",
  "decision_actor_id": "88c73d69-2717-536b-8984-9cc8bfd18d7d",
  "run_version": 1,
  "result_version": 1
}
```

201创建REQUESTED申请，不签发批准；缺审批读取/有效状态与撤销链路，见IF-G02。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | approval_request.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/object_type | approval_request.object_type | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/object_id | approval_request.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/object_version | approval_request.object_version, approval_request.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/purpose | approval_request.purpose | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/policy_version | approval_request.policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/reason | approval_request.reason | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/run_version | approval_request.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/result_version | approval_request.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/approval_id | approval_request.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | approval_request.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | approval_request.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_version | approval_request.object_version, approval_request.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/purpose | approval_request.purpose | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/policy_version | approval_request.policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/expires_at | approval_request.expires_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/decision_actor_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/run_version | approval_request.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result_version | approval_request.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TC-PROPAGATION-003-E、TC-PROPAGATION-003-N、TC-REVIEW-001-E、TC-REVIEW-001-N、TV-T008-E、TV-T008-N、TV-T011-E、TV-T011-N、TV-T012-E、TV-T012-N、TV-T013-E、TV-T013-N、TV-T014-E、TV-T014-N、TV-T015-E、TV-T015-N、TV-T016-E、TV-T016-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T021-E、TV-T021-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N、TV-T109-E、TV-T109-N、TV-T110-E、TV-T110-N、TV-T111-E、TV-T111-N、TV-T112-E、TV-T112-N、TV-T118-E、TV-T118-N、TV-T126-E、TV-T126-N、TV-T127-E、TV-T127-N、TV-T156-E、TV-T156-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
