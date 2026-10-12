# 读取媒体时间轴：getTimeline

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `c3471938106ec4211159d46b93c972416c2a678cd967214b2d23c48a12d8b2e7`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/assets/{id}/timeline`；operationId=`getTimeline`；源指针=`/paths/~1assets~1{id}~1timeline/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

读取媒体时间轴；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T050 实现媒体统一时间轴服务](../../../tasks/backend/T050.md)。

关联需求：FR-MEDIA-003、ER-T050；关联候选表：keyframe、shot、text_segment、media_asset。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: Timeline | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Timeline`，详细字段见[数据结构](../data-structures.md#timeline)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：keyframe.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证；shot.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；text_segment.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：keyframe.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；media_asset.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；shot.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；text_segment.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本。来源引用不是写入许可，完整处理按操作核验。 |
| items | 必须 | array; minItems=0; items=TimelineItem | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "asset_id": "9c4aea67-eb04-50ce-8652-5f781c894880",
  "mapping_version": "synthetic-v1",
  "items": [
    {
      "item_id": "101ad973-465c-50f9-9904-5e9c7f4d453b",
      "kind": "frame",
      "time_range": {
        "start_ms": 0,
        "end_ms": 1000
      },
      "mapping_version": "synthetic-v1",
      "asset_id": "4f214d97-05c0-51eb-84c2-8d91d80ad27d",
      "text": "synthetic-v1",
      "bbox": {
        "x": 0.1,
        "y": 0.1,
        "width": 0.4,
        "height": 0.4
      },
      "evidence_id": "421766de-8f3d-5d3f-bb49-6b99e17d7150"
    }
  ]
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/asset_id | keyframe.asset_id, media_asset.asset_id, shot.asset_id, text_segment.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/mapping_version | keyframe.mapping_version, media_asset.mapping_version, shot.mapping_version, text_segment.mapping_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items | 服务层输入/聚合，不直接生成数据库列 | 分页/聚合投影，明细按子结构对应表 |
| response/items[].item_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].kind | media_asset.kind, text_segment.type | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].time_range | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].time_range.start_ms | shot.start_ms, text_segment.start_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].time_range.end_ms | shot.end_ms, text_segment.end_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].mapping_version | keyframe.mapping_version, media_asset.mapping_version, shot.mapping_version, text_segment.mapping_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].asset_id | keyframe.asset_id, media_asset.asset_id, shot.asset_id, text_segment.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].text | text_segment.text | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].bbox | text_segment.bbox | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].bbox.x | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].bbox.y | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].bbox.width | media_asset.width | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].bbox.height | media_asset.height | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].evidence_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-MEDIA-003-E、TC-MEDIA-003-N、TV-T050-E、TV-T050-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
