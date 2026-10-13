# 提交传播边复核决定：decidePropagationEdge

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `556c92bd7b22602c83bd71aa3ea5cc11cdefb48926a18c03428b293860e2f7ba`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/propagation/edges/{id}/decisions`；operationId=`decidePropagationEdge`；源指针=`/paths/~1propagation~1edges~1{id}~1decisions/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

提交传播边复核决定；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`review.perform`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T096 实现隐式传播关系推断](../../../tasks/backend/T096.md)、[T097 开发传播时间线和图谱界面](../../../tasks/frontend/T097.md)、[T102 实现人工复核工作流](../../../tasks/backend/T102.md)。

关联需求：FR-PROPAGATION-001、FR-PROPAGATION-002、FR-PROPAGATION-003、FR-REVIEW-001、ER-T096、ER-T097、ER-T102、NFR-AUDIT-001；关联候选表：propagation_edge、review_record。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |
| If-Match | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/GraphDecision`；字段与完整约束见[数据结构](../data-structures.md#graphdecision)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：propagation_edge.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；review_record.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| decision | 必须 | string; enum=["confirm", "reject"] | 候选字段来源：review_record.decision：本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：review_record.comments：复核意见原文，说明证据取舍及处理理由，后续更正追加版本。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：propagation_edge.evidence_refs：支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "expected_version": 1,
  "decision": "confirm",
  "reason": "synthetic-v1",
  "evidence_ids": [
    "858c33f1-0278-57c1-b9f0-397ccbbf6078"
  ]
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: GraphEdge | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
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

成功结构：`GraphEdge`，详细字段见[数据结构](../data-structures.md#graphedge)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| edge_id | 必须 | string; format="uuid" | 候选字段来源：propagation_edge.edge_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| from_node_id | 必须 | string; format="uuid" | 候选字段来源：propagation_edge.from_node_id：传播关系起点节点标识。来源引用不是写入许可，完整处理按操作核验。 |
| to_node_id | 必须 | string; format="uuid" | 候选字段来源：propagation_edge.to_node_id：传播关系终点节点标识。来源引用不是写入许可，完整处理按操作核验。 |
| relation | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：propagation_edge.relation：传播关系类别；是否事实另由origin和证据决定。来源引用不是写入许可，完整处理按操作核验。 |
| origin | 必须 | string; enum=["observed", "inferred", "human"] | 候选字段来源：propagation_edge.origin：传播边依据类别，区分明确记录与算法推断；推断不能展示为事实。来源引用不是写入许可，完整处理按操作核验。 |
| probability | 必须 | anyOf(number; minimum=0; maximum=1; null) | 候选字段来源：propagation_edge.probability：传播关系推断的已校准概率，范围0至1；未校准时为NULL，不能据此把推断边改成事实边。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：propagation_edge.evidence_refs：支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：propagation_edge.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；propagation_node.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；review_record.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["candidate", "confirmed", "rejected"] | 候选字段来源：propagation_edge.state：显式推断传播边的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "edge_id": "ae8248dc-6de6-5f5f-83eb-8be276252be4",
  "from_node_id": "8556f93d-7568-5702-bea3-57517722a36e",
  "to_node_id": "1d9909c8-ca44-5fb8-9ccf-fd5601a20e07",
  "relation": "synthetic-v1",
  "origin": "observed",
  "probability": 0.5,
  "evidence_ids": [
    "c17d5174-7e68-5015-ae65-9f4be413feef"
  ],
  "version": 1,
  "state": "candidate"
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口声明If-Match：必须服务端原子核验对象版本；缺少条件428、旧版本412、状态不许可409。ETag绑定对象/聚合的精确范围仍按业务设计及缺口评审，body expected_version不能代替条件更新。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/expected_version | propagation_edge.row_version, review_record.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/decision | review_record.decision | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/reason | review_record.comments | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/evidence_ids | propagation_edge.evidence_refs | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edge_id | propagation_edge.edge_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/from_node_id | propagation_edge.from_node_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/to_node_id | propagation_edge.to_node_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/relation | propagation_edge.relation | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/origin | propagation_edge.origin | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/probability | propagation_edge.probability | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/evidence_ids | propagation_edge.evidence_refs | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | propagation_edge.row_version, review_record.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | propagation_edge.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-PROPAGATION-001-E、TC-PROPAGATION-001-N、TC-PROPAGATION-002-E、TC-PROPAGATION-002-N、TC-PROPAGATION-003-E、TC-PROPAGATION-003-N、TC-REVIEW-001-E、TC-REVIEW-001-N、TV-T008-E、TV-T008-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T096-E、TV-T096-N、TV-T097-E、TV-T097-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
