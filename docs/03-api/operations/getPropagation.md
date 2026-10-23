# 读取传播关系图：getPropagation

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/propagation/{cluster_id}`；operationId=`getPropagation`；源指针=`/paths/~1propagation~1{cluster_id}/get`。

实现范围：**DEV_PARTIAL**；独立业务HTTP/真实PostgreSQL/RLS已实现；默认无权威身份提供方返回503，测试提供方仅在fixture注入。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取传播关系图；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`propagation.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T095 实现传播图谱写入与查询](../../../tasks/backend/T095.md)、[T097 开发传播时间线和图谱界面](../../../tasks/frontend/T097.md)。

关联需求：FR-PROPAGATION-001、FR-PROPAGATION-002、FR-PROPAGATION-003、ER-T095、ER-T097；关联候选表：propagation_node、propagation_edge。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| cluster_id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| history | query | False | object; additionalProperties=false |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: Graph | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128; X-Task-Id: string; format="uuid"; X-Run-Version: integer; minimum=1; X-Result-Version: integer; minimum=1 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Graph`，详细字段见[数据结构](../data-structures.md#graph)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| cluster_id | 必须 | string; format="uuid" | 候选字段来源：propagation_node.cluster_id：高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：propagation_edge.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；propagation_node.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| nodes | 必须 | array; minItems=0; items=GraphNode | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| edges | 必须 | array; minItems=0; items=GraphEdge | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "cluster_id": "d2fbfc42-aa54-523d-a1ab-fef6968a962c",
  "version": 1,
  "nodes": [
    {
      "node_id": "b23dbe39-b5ed-5baa-9f1f-c94943eab339",
      "type": "content",
      "display_label": "synthetic-v1"
    }
  ],
  "edges": [
    {
      "edge_id": "6b601837-ebe3-5ef7-8c9e-aba80057a001",
      "from_node_id": "73403a02-b8e4-54d2-8b34-34bbe6149f74",
      "to_node_id": "aa803c17-e09d-550f-b92c-0dd1b731e054",
      "relation": "synthetic-v1",
      "origin": "observed",
      "probability": 0.5,
      "evidence_ids": [
        "515b5926-ae5f-5a03-bcf4-ad65bce0d6e3"
      ],
      "version": 1,
      "state": "candidate"
    }
  ]
}
```

按精确task/run/result及当前权限读取不可变快照，7项HTTP和版本头已实测；尚无实际业务结果生产器，缺失快照404、旧映射未登记503。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/cluster_id | propagation_node.cluster_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | propagation_edge.row_version, propagation_node.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/nodes | 服务层输入/聚合，不直接生成数据库列 | task_node_run聚合；按task_id/run_version查询 |
| response/nodes[].node_id | propagation_node.node_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/nodes[].type | propagation_node.type | Problem URI或证据类型，按Schema区分 |
| response/nodes[].display_label | propagation_node.display_label | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].edge_id | propagation_edge.edge_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].from_node_id | propagation_edge.from_node_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].to_node_id | propagation_edge.to_node_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].relation | propagation_edge.relation | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].origin | propagation_edge.origin | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].probability | propagation_edge.probability | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].evidence_ids | propagation_edge.evidence_refs | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].version | propagation_edge.row_version, propagation_node.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/edges[].state | propagation_edge.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-PROPAGATION-001-E、TC-PROPAGATION-001-N、TC-PROPAGATION-002-E、TC-PROPAGATION-002-N、TC-PROPAGATION-003-E、TC-PROPAGATION-003-N、TV-T095-E、TV-T095-N、TV-T097-E、TV-T097-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
