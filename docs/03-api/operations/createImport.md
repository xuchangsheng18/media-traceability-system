# 受理清单导入：createImport

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `c3471938106ec4211159d46b93c972416c2a678cd967214b2d23c48a12d8b2e7`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/imports`；operationId=`createImport`；源指针=`/paths/~1imports/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

受理清单导入；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.import`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T028 实现批量清单导入](../../../tasks/backend/T028.md)。

关联需求：FR-INGEST-001、ER-T028；关联候选表：import_job、import_item。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/ImportRequest`；字段与完整约束见[数据结构](../data-structures.md#importrequest)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：import_item.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；import_job.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| entries | 必须 | array; minItems=1; items=ImportEntry | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "f4dbd448-2240-5f07-8781-dcd3479fd6fb",
  "entries": [
    {
      "source_id": "bc80a95c-bb9d-567a-a372-4bf2d0225555",
      "object_ref": {
        "object_id": "8b272141-e150-5daf-8df3-033261fec4da",
        "version_id": "synthetic-v1",
        "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
      },
      "filename": "synthetic-v1",
      "mime": "synthetic-v1"
    }
  ]
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 202 | 契约成功响应；异步受理不代表结果完成 | application/json: ImportStatus | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`ImportStatus`，详细字段见[数据结构](../data-structures.md#importstatus)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| import_id | 必须 | string; format="uuid" | 候选字段来源：import_item.import_id：所属批量导入作业标识，指向import_job.import_id；import_job.import_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：import_item.state：逐条导入结果的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；import_job.state：批量清单导入作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| items | 必须 | array; minItems=0; items=object; additionalProperties=false | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].ordinal | 必须（父对象存在时） | integer; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].asset_id | 必须（父对象存在时） | anyOf(string; format="uuid"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].state | 必须（父对象存在时） | string; enum=["pending", "accepted", "rejected"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].error_code | 必须（父对象存在时） | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "import_id": "b1c4e897-0ad9-5baa-8743-476e5b6f5271",
  "state": "synthetic-v1",
  "items": [
    {
      "ordinal": 1,
      "asset_id": "61cee66b-a915-526d-86f4-ce47e8d4fce6",
      "state": "pending",
      "error_code": "synthetic-v1"
    }
  ]
}
```

202返回导入标识；GET /api/v1/imports/{id}读取实际状态与失败项，受理不是全部导入完成。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | import_item.case_id, import_job.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries[].source_id | import_item.source_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries[].object_ref | object_version.object_id, object_version.sha256, object_version.version_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries[].object_ref.object_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries[].object_ref.version_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries[].object_ref.sha256 | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries[].filename | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/entries[].mime | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/import_id | import_item.import_id, import_job.import_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | import_item.state, import_job.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items | 服务层输入/聚合，不直接生成数据库列 | 分页/聚合投影，明细按子结构对应表 |
| response/items[].ordinal | import_item.ordinal | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].asset_id | import_item.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].state | import_item.state, import_job.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].error_code | import_item.error_code | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-INGEST-001-E、TC-INGEST-001-N、TV-T028-E、TV-T028-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
