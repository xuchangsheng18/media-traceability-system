# 查询异步检索结果：getSearchJob

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `556c92bd7b22602c83bd71aa3ea5cc11cdefb48926a18c03428b293860e2f7ba`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/search/jobs/{id}`；operationId=`getSearchJob`；源指针=`/paths/~1search~1jobs~1{id}/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

查询异步检索结果；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.search`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T082 实现图片多路候选召回](../../../tasks/algorithm/T082.md)、[T085 实现图片局部区域检索](../../../tasks/algorithm/T085.md)、[T089 实现多源拼接来源映射](../../../tasks/algorithm/T089.md)。

关联需求：FR-RESOURCE-002、FR-IMGRET-001、FR-IMGRET-003、FR-VIDTRACE-003、ER-T082、ER-T085、ER-T089；关联候选表：search_job、source_match。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: SearchJob | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`SearchJob`，详细字段见[数据结构](../data-structures.md#searchjob)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| search_id | 必须 | string; format="uuid" | 候选字段来源：search_job.search_id：主键，由应用提供UUID；不视为访问凭证；source_match.search_id：产生匹配候选的异步检索作业标识。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["SUCCEEDED", "QUEUED", "RUNNING", "FAILED"] | 候选字段来源：search_job.state：异步检索任务的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| result | 必须 | anyOf(SearchResults; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| error_code | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：search_job.error_code：失败原因的稳定错误码；无失败时允许NULL，用户说明与诊断堆栈分开。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "search_id": "386b9431-4f66-5386-9416-e4defe72aac3",
  "state": "SUCCEEDED",
  "result": {
    "search_id": "6da81533-bbbd-5601-94bd-aa3b41559a5c",
    "index_version": "synthetic-v1",
    "candidates": [
      {
        "candidate_asset_id": "7051b6cd-78e8-54da-b97e-4a8dee534563",
        "score": 0.5,
        "relation": "similar",
        "verification": "unverified",
        "evidence_ids": [
          "c34461d6-3291-51fd-842f-13fe92755f51"
        ],
        "query_range": {
          "start_ms": 0,
          "end_ms": 1000
        },
        "source_range": {
          "start_ms": 0,
          "end_ms": 1000
        },
        "direction": "forward",
        "speed_ratio": 1.0
      }
    ],
    "unknown_ranges": [],
    "warnings": []
  },
  "error_code": "synthetic-v1"
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/search_id | search_job.search_id, source_match.search_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | search_job.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.search_id | search_job.search_id, source_match.search_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.index_version | search_job.index_version, source_match.index_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].candidate_asset_id | source_match.candidate_asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].score | source_match.score | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].relation | source_match.relation | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].verification | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].evidence_ids | source_match.evidence_refs | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].query_range | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].query_range.start_ms | source_match.query_start_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].query_range.end_ms | source_match.query_end_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].source_range | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].source_range.start_ms | source_match.source_start_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].source_range.end_ms | source_match.source_end_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].direction | source_match.direction | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.candidates[].speed_ratio | source_match.speed_ratio | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.unknown_ranges | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.unknown_ranges[].start_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.unknown_ranges[].end_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result.warnings | 服务层输入/聚合，不直接生成数据库列 | 非正式告警与限制投影 |
| response/error_code | search_job.error_code | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-IMGRET-001-E、TC-IMGRET-001-N、TC-IMGRET-003-E、TC-IMGRET-003-N、TC-RESOURCE-002-E、TC-RESOURCE-002-N、TC-VIDTRACE-003-E、TC-VIDTRACE-003-N、TV-T082-E、TV-T082-N、TV-T085-E、TV-T085-N、TV-T089-E、TV-T089-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
