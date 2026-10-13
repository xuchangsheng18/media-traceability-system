# 查询分析任务：listTasks

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `556c92bd7b22602c83bd71aa3ea5cc11cdefb48926a18c03428b293860e2f7ba`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/analysis/tasks`；operationId=`listTasks`；源指针=`/paths/~1analysis~1tasks/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

查询分析任务；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`task.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T035 实现任务查询和进度接口](../../../tasks/backend/T035.md)、[T040 开发任务监控页面](../../../tasks/frontend/T040.md)。

关联需求：FR-OPS-002、ER-T035、ER-T040、NFR-AVAIL-001；关联候选表：analysis_task。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| limit | query | False | integer; minimum=1; maximum=100; default=20 |
| cursor | query | False | string; minLength=1; maxLength=128 |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: TaskPage | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`TaskPage`，详细字段见[数据结构](../data-structures.md#taskpage)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Task | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "items": [
    {
      "task_id": "bef2285d-1f64-5646-bbd1-0f0ec8b345f4",
      "case_id": "c67a5c87-8fab-531e-8245-acb679d75cdc",
      "asset_id": "7214e01c-ec12-54d1-bfde-79e898e8df03",
      "state": "CREATED",
      "run_version": 1,
      "result_version": 1,
      "policy_version": "synthetic-v1",
      "version": 1,
      "progress": 0.5,
      "nodes": [
        {
          "node_code": "synthetic-v1",
          "state": "PENDING",
          "attempt": 1,
          "reason": "synthetic-v1",
          "required": true
        }
      ],
      "missing_modalities": [],
      "report_eligibility": "draft_only",
      "created_at": "2030-01-01T00:00:00Z"
    }
  ],
  "next_cursor": "synthetic-v1"
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/items | 服务层输入/聚合，不直接生成数据库列 | 分页/聚合投影，明细按子结构对应表 |
| response/items[].task_id | analysis_task.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].case_id | analysis_task.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].asset_id | analysis_task.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].state | analysis_task.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].run_version | analysis_task.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].result_version | analysis_task.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].policy_version | analysis_task.policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].version | analysis_task.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].progress | analysis_task.progress | 当前运行节点完成投影，同时存任务当前进度 |
| response/items[].nodes | 服务层输入/聚合，不直接生成数据库列 | task_node_run聚合；按task_id/run_version查询 |
| response/items[].nodes[].node_code | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].nodes[].state | analysis_task.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].nodes[].attempt | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].nodes[].reason | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].nodes[].required | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].missing_modalities | analysis_task.missing_modalities | 任务/能力完成矩阵，不能隐藏缺失 |
| response/items[].report_eligibility | analysis_task.report_eligibility | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].created_at | analysis_task.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/next_cursor | 服务层输入/聚合，不直接生成数据库列 | 服务端根据稳定排序与授权条件编码，不持久化权限范围 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-002-E、TC-OPS-002-N、TV-T031-E、TV-T031-N、TV-T032-E、TV-T032-N、TV-T033-E、TV-T033-N、TV-T034-E、TV-T034-N、TV-T035-E、TV-T035-N、TV-T036-E、TV-T036-N、TV-T037-E、TV-T037-N、TV-T038-E、TV-T038-N、TV-T039-E、TV-T039-N、TV-T040-E、TV-T040-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
