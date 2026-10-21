# 登记策略草案：createPolicy

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/policies`；operationId=`createPolicy`；源指针=`/paths/~1policies/post`。

实现范围：**DEV_PARTIAL**；独立业务开发工程已挂载真实访问/校验；权威提供方未配置时拒绝，不提供生产模拟成功。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

登记策略草案；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`policy.manage`。

组织级模型/配置/索引管理；系统管理员不自动取得案件原件，依赖数据仍核验用途。

来源任务：[T061 定义风险标签和版本管理](../../../tasks/algorithm/T061.md)、[T068 实现综合风险融合与校准](../../../tasks/algorithm/T068.md)、[T069 实现风险转人工规则](../../../tasks/algorithm/T069.md)、[T102 实现人工复核工作流](../../../tasks/backend/T102.md)。

关联需求：FR-RISK-001、FR-RISK-003、FR-PROPAGATION-003、FR-REVIEW-001、FR-OPS-001、ER-T061、ER-T068、ER-T069、ER-T102、NFR-AUDIT-001；关联候选表：policy_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/PolicyCreate`；字段与完整约束见[数据结构](../data-structures.md#policycreate)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| kind | 必须 | string; enum=["risk_taxonomy", "threshold", "review", "retention", "analysis"] | 候选字段来源：policy_registry.kind：策略类别，如标签、阈值、流程或保留规则；类别词表由配置登记。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；policy_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| definition_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.definition_ref：完整策略定义文档或配置的受控引用，应可定位不可变版本。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：policy_registry.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| status | 必须 | string; enum=["DRAFT", "APPROVED"] | 候选字段来源：policy_registry.status：标签阈值流程保留等策略的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "kind": "risk_taxonomy",
  "version": "synthetic-v1",
  "definition_ref": "synthetic-v1",
  "approval_id": "41d4a59d-a6dd-536a-9077-ed4fb5b6bfcd",
  "status": "DRAFT"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: Policy | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Policy`，详细字段见[数据结构](../data-structures.md#policy)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| policy_id | 必须 | string; format="uuid" | 候选字段来源：policy_registry.policy_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| kind | 必须 | string; enum=["risk_taxonomy", "threshold", "review", "retention", "analysis"] | 候选字段来源：policy_registry.kind：策略类别，如标签、阈值、流程或保留规则；类别词表由配置登记。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；policy_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| definition_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.definition_ref：完整策略定义文档或配置的受控引用，应可定位不可变版本。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：policy_registry.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| status | 必须 | string; enum=["DRAFT", "APPROVED"] | 候选字段来源：policy_registry.status：标签阈值流程保留等策略的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| row_version | 必须 | integer; minimum=1 | 候选字段来源：policy_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "policy_id": "041359d3-0d0e-5ab4-8eba-a2a2ae9c873b",
  "kind": "risk_taxonomy",
  "version": "synthetic-v1",
  "definition_ref": "synthetic-v1",
  "approval_id": "a54d63b9-82c9-50a1-9d5f-932efe85070a",
  "status": "DRAFT",
  "row_version": 1
}
```

201登记版本化草案，DRAFT不能自动生效；批准、激活/撤销协议IF-G12待确定。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/kind | policy_registry.kind | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/version | policy_registry.row_version, policy_registry.version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/definition_ref | policy_registry.definition_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/approval_id | policy_registry.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/status | policy_registry.status | 相应对象状态或健康聚合；按Schema与操作区分 |
| response/policy_id | policy_registry.policy_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/kind | policy_registry.kind | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | policy_registry.row_version, policy_registry.version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/definition_ref | policy_registry.definition_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/approval_id | policy_registry.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/status | policy_registry.status | 相应对象状态或健康聚合；按Schema与操作区分 |
| response/row_version | policy_registry.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TC-PROPAGATION-003-E、TC-PROPAGATION-003-N、TC-REVIEW-001-E、TC-REVIEW-001-N、TC-RISK-001-E、TC-RISK-001-N、TC-RISK-003-E、TC-RISK-003-N、TV-T008-E、TV-T008-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T061-E、TV-T061-N、TV-T068-E、TV-T068-N、TV-T069-E、TV-T069-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
