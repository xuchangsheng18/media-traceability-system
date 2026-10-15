# getApproval：getApproval

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/approvals/{id}`；operationId=`getApproval`；源指针=`/paths/~1approvals~1{id}/get`。

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
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: ApprovalDetail |  |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`ApprovalDetail`，详细字段见[数据结构](../data-structures.md#approvaldetail)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| approval | 必须 | Approval | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding | 必须 | object; additionalProperties=false | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.case_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.object_type | 必须（父对象存在时） | string; enum=["task", "report", "evidence_package", "feedback", "model_release", "operation"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.object_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.requested_by | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions | 必须 | array; items=object; additionalProperties=false | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].decision_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].decision | 必须（父对象存在时） | string; enum=["approve", "reject", "return", "revoke", "invalidate"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].actor_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].reason | 必须（父对象存在时） | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].evidence_ids | 必须（父对象存在时） | array; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].created_at | 必须（父对象存在时） | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "approval": {
    "approval_id": "00000000-0000-4000-8000-000000000001",
    "state": "REQUESTED",
    "version": 1,
    "object_version": 1,
    "purpose": "synthetic-example",
    "policy_version": "synthetic-example",
    "expires_at": null,
    "decision_actor_id": null,
    "run_version": null,
    "result_version": null
  },
  "binding": {
    "case_id": "00000000-0000-4000-8000-000000000001",
    "object_type": "task",
    "object_id": "00000000-0000-4000-8000-000000000001",
    "requested_by": "00000000-0000-4000-8000-000000000001"
  },
  "decisions": []
}
```

文档与路由不代表正式接入、真实模型或完整业务验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/approval | 服务层输入/聚合，不直接生成数据库列 | 服务层按本操作源Schema组合的结构容器，不是一列JSON或新增业务表；其叶字段按逐行映射处理。 |
| response/approval.approval_id | approval_decision.approval_id, approval_request.approval_id | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.state | approval_request.state | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.version | approval_decision.row_version, approval_request.row_version, audit_event.row_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.object_version | approval_request.object_version, approval_request.result_version, audit_event.object_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.purpose | approval_request.purpose | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.policy_version | approval_decision.policy_version, approval_request.policy_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.expires_at | approval_request.expires_at | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.decision_actor_id | approval_decision.decision_actor_id | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.run_version | approval_request.run_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/approval.result_version | approval_request.result_version | 审批当前有效状态/版本投影：服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。；到期、来源撤销或结果变更使现行批准无效。 |
| response/binding | 服务层输入/聚合，不直接生成数据库列 | 服务层按本操作源Schema组合的结构容器，不是一列JSON或新增业务表；其叶字段按逐行映射处理。 |
| response/binding.case_id | approval_request.case_id | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/binding.object_type | approval_request.object_type | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/binding.object_id | approval_request.object_id | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/binding.requested_by | approval_request.requested_by | 审批申请的精确案件/对象/申请人绑定；客户端不得替代认证申请人。 |
| response/decisions | 服务层输入/聚合，不直接生成数据库列 | 服务层按本操作源Schema组合的结构容器，不是一列JSON或新增业务表；其叶字段按逐行映射处理。 |
| response/decisions[].decision_id | approval_decision.decision_id | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/decisions[].decision | approval_decision.decision | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/decisions[].actor_id | approval_decision.decision_actor_id | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/decisions[].reason | approval_decision.reason | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/decisions[].evidence_ids | approval_decision.evidence_refs | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |
| response/decisions[].created_at | approval_decision.created_at | 追加式审批历史字段；证据数组存于evidence_refs.evidence_ids，审批人数按独立主体及实际规则计算。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
