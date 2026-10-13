# 受理视频片段检索：searchVideo

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/search/video`；operationId=`searchVideo`；源指针=`/paths/~1search~1video/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

受理视频片段检索；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.search`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T089 实现多源拼接来源映射](../../../tasks/algorithm/T089.md)。

关联需求：FR-VIDTRACE-003、ER-T089；关联候选表：source_match、index_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/VideoSearch`；字段与完整约束见[数据结构](../data-structures.md#videosearch)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：source_match.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| range | 必须 | TimeRange | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| top_k | 必须 | integer; minimum=1; maximum=100 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| index_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本；source_match.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "b06cf05f-1504-5792-817c-8ca70f3d1095",
  "asset_id": "8b2472d1-3c96-522a-b91f-867780062a61",
  "range": {
    "start_ms": 0,
    "end_ms": 1000
  },
  "top_k": 1,
  "index_version": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 202 | 契约成功响应；异步受理不代表结果完成 | application/json: SearchAccepted | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`SearchAccepted`，详细字段见[数据结构](../data-structures.md#searchaccepted)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| search_id | 必须 | string; format="uuid" | 候选字段来源：source_match.search_id：产生匹配候选的异步检索作业标识。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["QUEUED", "RUNNING"] | 候选字段来源：index_registry.state：索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；media_asset.state：原始或派生媒体的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| status_url | 必须 | string; pattern="^/api/v1/search/jobs/" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "search_id": "c492a3dc-a0e7-5d58-8614-d3b41a4c83ee",
  "state": "QUEUED",
  "status_url": "/api/v1/search/jobs/00000000-0000-4000-8000-000000000001"
}
```

202返回search_id/status_url，通过GET /api/v1/search/jobs/{id}查询，SUCCEEDED才有非null结果。召回/几何或时序验证与整内容同源判断分开。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | source_match.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/asset_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/range | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/range.start_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/range.end_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/top_k | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/index_version | index_registry.index_version, source_match.index_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/search_id | source_match.search_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | index_registry.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/status_url | 服务层输入/聚合，不直接生成数据库列 | 根据task_id生成相对查询URL |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-VIDTRACE-003-E、TC-VIDTRACE-003-N、TV-T089-E、TV-T089-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
