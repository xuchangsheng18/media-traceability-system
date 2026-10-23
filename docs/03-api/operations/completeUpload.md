# 合并并校验上传：completeUpload

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/uploads/{id}/complete`；operationId=`completeUpload`；源指针=`/paths/~1uploads~1{id}~1complete/post`。

实现范围：**DEV_PARTIAL**；独立业务HTTP/真实PostgreSQL/RLS已实现；默认无权威身份提供方返回503，测试提供方仅在fixture注入。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

合并并校验上传；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.upload`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T024 实现分片合并与完整哈希](../../../tasks/backend/T024.md)、[T026 实现媒体格式探测与安全校验](../../../tasks/backend/T026.md)、[T027 实现SHA-256完全重复检测](../../../tasks/backend/T027.md)。

关联需求：FR-INGEST-002、FR-INGEST-003、FR-RESOURCE-002、ER-T024、ER-T026、ER-T027；关联候选表：upload_session、upload_part、media_asset。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/UploadComplete`；字段与完整约束见[数据结构](../data-structures.md#uploadcomplete)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| parts | 必须 | array; minItems=1; items=UploadPart | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "parts": [
    {
      "part_no": 1,
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "size_bytes": 1
    }
  ]
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 202 | 契约成功响应；异步受理不代表结果完成 | application/json: UploadResult | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`UploadResult`，详细字段见[数据结构](../data-structures.md#uploadresult)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| upload_id | 必须 | string; format="uuid" | 候选字段来源：upload_part.upload_id：所属上传会话标识，指向upload_session.upload_id；upload_session.upload_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证；upload_session.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| validation | 必须 | string; enum=["VALIDATING", "VALID", "REJECTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| duplicate_of | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：upload_session.duplicate_of：同案件重复资产引用；仅在完整摘要/媒体校验成功后登记，读取仍核验当前案件权限；NULL表示未确定重复。。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "upload_id": "8f77d51e-466d-5304-8b5d-5501588de6ad",
  "asset_id": "4d8b21b5-037e-59fc-a609-7185bdebffbc",
  "validation": "VALIDATING",
  "duplicate_of": "6101536a-0bb1-57d0-811c-ddb7f55a121b",
  "request_id": "1b2fbbaa-f709-5cea-9179-1d4ad6fbc979"
}
```

5项上传操作、摘要/PNG-JPEG校验、持久消息确认和重复恢复已实测；其他媒体/病毒扫描、S3及正式来源仍待验证。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/parts | 服务层输入/聚合，不直接生成数据库列 | 按upload_id聚合的upload_part，检查连续覆盖 |
| request/parts[].part_no | upload_part.part_no | 分片路径与正文回执一致，编号正整数 |
| request/parts[].sha256 | media_asset.sha256, upload_part.sha256, upload_session.sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/parts[].size_bytes | media_asset.size_bytes, upload_part.size_bytes, upload_session.size_bytes | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/upload_id | upload_part.upload_id, upload_session.upload_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/asset_id | media_asset.asset_id, upload_session.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/validation | 服务层输入/聚合，不直接生成数据库列 | 安全校验状态投影；未VALID不分析 |
| response/duplicate_of | upload_session.duplicate_of | 在当前可访问资产中查同摘要；禁止泄露其他案件 |
| response/request_id | 服务层输入/聚合，不直接生成数据库列 | 请求追踪/审计，不作为业务对象ID |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-INGEST-002-E、TC-INGEST-002-N、TC-INGEST-003-E、TC-INGEST-003-N、TC-RESOURCE-002-E、TC-RESOURCE-002-N、TV-T024-E、TV-T024-N、TV-T026-E、TV-T026-N、TV-T027-E、TV-T027-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
