# listApprovals：listApprovals

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/approvals`；operationId=`listApprovals`；源指针=`/paths/~1approvals/get`。

实现范围：**DEV_PARTIAL**；真实数据库或显式适配端口已实现，默认未接入的权威依赖返回503；实际结果按本批测试记录。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取真实记录或执行明确授权的受控操作；具体边界见剩余接口实现说明。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`approval.read`。

每次核验当前身份/功能权限和单位/案件范围；组织级策略不借用虚构案件。

来源任务：[T016 实现高风险操作二次确认](../../../tasks/platform/T016.md)、[T102 实现人工复核工作流](../../../tasks/backend/T102.md)、[T108 实现样本纠错与回流审批](../../../tasks/backend/T108.md)。

关联需求：；关联候选表：approval_request、approval_decision。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| case_id | query | True | string; format="uuid" |
| limit | query | False | integer; minimum=1; maximum=100; default=20 |
| cursor | query | False | string; minLength=1; maxLength=128 |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: ApprovalPage |  |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`ApprovalPage`，详细字段见[数据结构](../data-structures.md#approvalpage)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; items=ApprovalDetail | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "items": [],
  "next_cursor": null
}
```

文档与路由不代表正式接入、真实模型或完整业务验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/items | 服务层输入/聚合，不直接生成数据库列 | 服务层按本操作源Schema组合的结构容器，不是一列JSON或新增业务表；其叶字段按逐行映射处理。 |
| response/items[].approval | 服务层输入/聚合，不直接生成数据库列 | 服务层按本操作源Schema组合的结构容器，不是一列JSON或新增业务表；其叶字段按逐行映射处理。 |
| response/items[].approval.approval_id | approval_decision.approval_id, approval_request.approval_id | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.state | approval_request.state | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.version | approval_decision.row_version, approval_request.row_version, audit_event.row_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.object_version | approval_request.object_version, approval_request.result_version, audit_event.object_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.purpose | approval_request.purpose | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.policy_version | approval_decision.policy_version, approval_request.policy_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.expires_at | approval_request.expires_at | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.decision_actor_id | approval_decision.decision_actor_id | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.run_version | approval_request.run_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].approval.result_version | approval_request.result_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/items[].binding | 服务层输入/聚合，不直接生成数据库列 | 服务层按本操作源Schema组合的结构容器，不是一列JSON或新增业务表；其叶字段按逐行映射处理。 |
| response/items[].binding.case_id | approval_request.case_id | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/items[].binding.object_type | approval_request.object_type | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/items[].binding.object_id | approval_request.object_id | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/items[].binding.requested_by | approval_request.requested_by | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/items[].decisions | 服务层输入/聚合，不直接生成数据库列 | 服务层按本操作源Schema组合的结构容器，不是一列JSON或新增业务表；其叶字段按逐行映射处理。 |
| response/items[].decisions[].decision_id | approval_decision.decision_id | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/items[].decisions[].decision | approval_decision.decision | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/items[].decisions[].actor_id | approval_decision.decision_actor_id | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/items[].decisions[].reason | approval_decision.reason | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/items[].decisions[].evidence_ids | approval_decision.evidence_refs | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/items[].decisions[].created_at | approval_decision.created_at | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/next_cursor | 服务层输入/聚合，不直接生成数据库列 | 服务端签名分页游标绑定主体、单位、案件、过滤条件、页大小及当前账本版本；伪造422，账本变化409。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
