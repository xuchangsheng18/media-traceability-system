# 查询来源清单：listSources

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `c3471938106ec4211159d46b93c972416c2a678cd967214b2d23c48a12d8b2e7`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/sources`；operationId=`listSources`；源指针=`/paths/~1sources/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

查询来源清单；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`source.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T021 实现数据来源授权登记](../../../tasks/backend/T021.md)。

关联需求：FR-INGEST-001、FR-RESOURCE-003、ER-T021、NFR-DATA-001；关联候选表：source_registry。表引用不证明代码已使用或有访问授权。

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
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: SourcePage | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`SourcePage`，详细字段见[数据结构](../data-structures.md#sourcepage)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Source | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "items": [
    {
      "source_id": "78eac2cb-7ea5-5704-a1a4-ee4906f93bdd",
      "case_id": "c8b0d5fb-1ca7-5f81-b54a-6ea9b3f2ee88",
      "name": "synthetic-v1",
      "source_type": "authorized_business",
      "authorization_ref": "synthetic-v1",
      "purpose": [
        "synthetic-v1"
      ],
      "expires_at": "2030-01-01T00:00:00Z",
      "authorization_status": "pending",
      "version": 1
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
| response/items[].source_id | source_registry.source_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].case_id | source_registry.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].name | source_registry.name | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].source_type | source_registry.source_type | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].authorization_ref | source_registry.authorization_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].purpose | source_registry.purpose | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].expires_at | source_registry.expires_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].authorization_status | source_registry.authorization_status | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].version | source_registry.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/next_cursor | 服务层输入/聚合，不直接生成数据库列 | 服务端根据稳定排序与授权条件编码，不持久化权限范围 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-INGEST-001-E、TC-INGEST-001-N、TC-RESOURCE-003-E、TC-RESOURCE-003-N、TV-T021-E、TV-T021-N、TV-T108-E、TV-T108-N、TV-T109-E、TV-T109-N、TV-T110-E、TV-T110-N、TV-T111-E、TV-T111-N、TV-T112-E、TV-T112-N、TV-T126-E、TV-T126-N、TV-T127-E、TV-T127-N、TV-T156-E、TV-T156-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
