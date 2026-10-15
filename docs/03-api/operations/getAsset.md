# 读取媒体资产详情：getAsset

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/assets/{id}`；operationId=`getAsset`；源指针=`/paths/~1assets~1{id}/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取媒体资产详情；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T030 开发媒体资产管理页面](../../../tasks/frontend/T030.md)。

关联需求：FR-RESOURCE-001、FR-RESOURCE-003、ER-T030；关联候选表：media_asset、asset_lineage。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: Asset | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Asset`，详细字段见[数据结构](../data-structures.md#asset)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：asset_lineage.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；media_asset.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| content_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.content_id：所属逻辑内容标识，指向content_item.content_id。来源引用不是写入许可，完整处理按操作核验。 |
| source_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.source_id：数据来源登记标识，指向source_registry.source_id。来源引用不是写入许可，完整处理按操作核验。 |
| kind | 必须 | string; enum=["original", "derived"] | 候选字段来源：media_asset.kind：媒体身份：original为原始输入，derived为派生副本。来源引用不是写入许可，完整处理按操作核验。 |
| object_ref | 必须 | ObjectRef | 候选字段来源：object_version.object_id：主键，由应用提供UUID；不视为访问凭证；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.version_id：对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version。来源引用不是写入许可，完整处理按操作核验。 |
| mime | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：media_asset.mime：探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名。来源引用不是写入许可，完整处理按操作核验。 |
| size_bytes | 必须 | integer; minimum=1 | 候选字段来源：media_asset.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0。来源引用不是写入许可，完整处理按操作核验。 |
| duration_ms | 必须 | anyOf(integer; minimum=0; null) | 候选字段来源：media_asset.duration_ms：媒体时长，单位毫秒；静态图像或未知时长允许NULL，0不能替代未知。来源引用不是写入许可，完整处理按操作核验。 |
| width | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：media_asset.width：媒体帧或图像宽度，单位像素；有值时为正整数。来源引用不是写入许可，完整处理按操作核验。 |
| height | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：media_asset.height：媒体帧或图像高度，单位像素；有值时为正整数。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["VALIDATING", "VALID", "QUARANTINED", "ARCHIVED"] | 候选字段来源：media_asset.state：原始或派生媒体的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：asset_lineage.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；media_asset.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：asset_lineage.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；media_asset.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "asset_id": "bcfa1eea-81f7-5b10-bc70-7fd3e066e6cd",
  "case_id": "8350107a-5eba-571e-86ab-d178398bd72f",
  "content_id": "d0c2aef1-c26e-5db5-842b-43faa523a096",
  "source_id": "3153cc5a-e4b0-5495-9dd3-ea86f65d1378",
  "kind": "original",
  "object_ref": {
    "object_id": "e6cc990e-7331-585f-b19d-f101e93fdeb9",
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
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/asset_id | media_asset.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/case_id | asset_lineage.case_id, media_asset.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/content_id | media_asset.content_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/source_id | media_asset.source_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/kind | media_asset.kind | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref | object_version.object_id, object_version.sha256, object_version.version_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref.object_id | media_asset.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref.version_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref.sha256 | media_asset.sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/mime | media_asset.mime | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/size_bytes | media_asset.size_bytes | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/duration_ms | media_asset.duration_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/width | media_asset.width | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/height | media_asset.height | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | media_asset.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | asset_lineage.row_version, media_asset.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/created_at | asset_lineage.created_at, media_asset.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-RESOURCE-001-E、TC-RESOURCE-001-N、TC-RESOURCE-003-E、TC-RESOURCE-003-N、TV-T030-E、TV-T030-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
