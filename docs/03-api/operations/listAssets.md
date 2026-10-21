# 查询媒体资产：listAssets

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/assets`；operationId=`listAssets`；源指针=`/paths/~1assets/get`。

实现范围：**DEV_PARTIAL**；2026-10-21源码已在独立业务工程挂载，0012仅用于新建隔离测试库；现有研发预览服务及其0011数据库未切换。DEV_PARTIAL不代表现有服务已上线、正式策略准入或整任务验收；实际命令、未通过项和同步范围见[本批记录](../../00-project/validation/t001-t123-catalog-read-report.json)。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

查询媒体资产；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T030 开发媒体资产管理页面](../../../tasks/frontend/T030.md)。

关联需求：FR-RESOURCE-001、FR-RESOURCE-003、ER-T030；关联候选表：media_asset。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| case_id | query | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| limit | query | False | integer; minimum=1; maximum=100; default=20 |
| cursor | query | False | string; minLength=1; maxLength=128 |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: AssetPage | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`AssetPage`，详细字段见[数据结构](../data-structures.md#assetpage)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Asset | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "items": [
    {
      "asset_id": "2d5dee67-d28e-546f-8973-23ae6b4b06f0",
      "case_id": "074cf7ba-a9c8-5d22-8ef7-196fd8598921",
      "content_id": "db357a94-1509-5ce9-ae65-535c5bb25971",
      "source_id": "21ba8167-1f45-5808-85f6-32ae91cf543a",
      "kind": "original",
      "object_ref": {
        "object_id": "45da7eab-ce8a-59d8-9a30-0a1cf3bcf954",
        "version_id": "synthetic-v1",
        "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
      },
      "mime": "synthetic-v1",
      "size_bytes": 1,
      "duration_ms": 1000,
      "width": 1,
      "height": 1,
      "state": "VALIDATING",
      "version": 1,
      "created_at": "2030-01-01T00:00:00Z"
    }
  ],
  "next_cursor": "synthetic-v1"
}
```

必须提供已授权case_id；先逐项核验来源、分类和读取用途再分页，游标绑定身份、单位、案件、操作和limit，投影完成后在同事务内复核授权。有效空页只表示当前有权结果为空，不表示案件内没有其他资产；完整门禁及任务验收另列。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/items | 服务层输入/聚合，不直接生成数据库列 | 分页/聚合投影，明细按子结构对应表 |
| response/items[].asset_id | media_asset.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].case_id | media_asset.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].content_id | media_asset.content_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].source_id | media_asset.source_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].kind | media_asset.kind | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].object_ref | object_version.object_id, object_version.sha256, object_version.version_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].object_ref.object_id | media_asset.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].object_ref.version_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].object_ref.sha256 | media_asset.sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].mime | media_asset.mime | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].size_bytes | media_asset.size_bytes | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].duration_ms | media_asset.duration_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].width | media_asset.width | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].height | media_asset.height | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].state | media_asset.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].version | media_asset.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].created_at | media_asset.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/next_cursor | 服务层输入/聚合，不直接生成数据库列 | 服务端根据稳定排序与授权条件编码，不持久化权限范围 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-RESOURCE-001-E、TC-RESOURCE-001-N、TC-RESOURCE-003-E、TC-RESOURCE-003-N、TV-T030-E、TV-T030-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
