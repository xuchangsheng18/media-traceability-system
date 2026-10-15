# getPolicy：getPolicy

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/policies/{id}`；operationId=`getPolicy`；源指针=`/paths/~1policies~1{id}/get`。

实现范围：**DEV_PARTIAL**；真实数据库或显式适配端口已实现，默认未接入的权威依赖返回503；实际结果按本批测试记录。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取真实记录或执行明确授权的受控操作；具体边界见剩余接口实现说明。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`policy.read`。

每次核验当前身份/功能权限和单位/案件范围；组织级策略不借用虚构案件。

来源任务：[T061 定义风险标签和版本管理](../../../tasks/algorithm/T061.md)、[T069 实现风险转人工规则](../../../tasks/algorithm/T069.md)。

关联需求：；关联候选表：policy_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: Policy |  |
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

文档与路由不代表正式接入、真实模型或完整业务验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/policy_id | policy_registry.policy_id | 组织策略版本读取；现有DRAFT/APPROVED状态不代表已激活，草稿定义变更需另建版本。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/kind | policy_registry.kind | 组织策略版本读取；现有DRAFT/APPROVED状态不代表已激活，草稿定义变更需另建版本。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | policy_registry.row_version, policy_registry.version | 组织策略版本读取；现有DRAFT/APPROVED状态不代表已激活，草稿定义变更需另建版本。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/definition_ref | policy_registry.definition_ref | 组织策略版本读取；现有DRAFT/APPROVED状态不代表已激活，草稿定义变更需另建版本。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/approval_id | policy_registry.approval_id | 组织策略版本读取；现有DRAFT/APPROVED状态不代表已激活，草稿定义变更需另建版本。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/status | policy_registry.status | 组织策略版本读取；现有DRAFT/APPROVED状态不代表已激活，草稿定义变更需另建版本。相应对象状态或健康聚合；按Schema与操作区分 |
| response/row_version | policy_registry.row_version | 组织策略版本读取；现有DRAFT/APPROVED状态不代表已激活，草稿定义变更需另建版本。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
