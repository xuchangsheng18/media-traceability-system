# 提交指定分片：putUploadPart

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `bffa82adf57b9ccf1888d5589e7b3d54f03915c7b150bac6dcc627779d4769b4`。契约未冻结，文档存在不代表接口已实现。

`PUT /api/v1/uploads/{id}/parts/{part_no}`；operationId=`putUploadPart`；源指针=`/paths/~1uploads~1{id}~1parts~1{part_no}/put`。

实现范围：**DEV_PARTIAL**；独立业务HTTP/真实PostgreSQL/RLS已实现；默认无权威身份提供方返回503，测试提供方仅在fixture注入。。正式55业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

提交指定分片；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.upload`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T023 实现分片接收与校验](../../../tasks/backend/T023.md)。

关联需求：FR-INGEST-002、ER-T023；关联候选表：upload_part、upload_session。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| part_no | path | True | integer; minimum=1 |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |
| X-Part-Sha256 | header | True | string; pattern="^[a-f0-9]{64}$" |
| Content-Length | header | True | integer; minimum=1 |

请求体必须出现：`True`；支持媒体类型：`application/octet-stream`。

本接口为二进制请求，按源content/schema提交字节。分片编号、摘要和Content-Length必须与实际字节相符，不能改用JSON base64生产上传。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: UploadPart | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`UploadPart`，详细字段见[数据结构](../data-structures.md#uploadpart)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| part_no | 必须 | integer; minimum=1 | 候选字段来源：upload_part.part_no：上传分片编号，从1开始；同一会话内不得重复。来源引用不是写入许可，完整处理按操作核验。 |
| sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：media_asset.sha256：媒体资产字节的SHA-256，应与引用对象版本核对；存储64位小写十六进制，正则只检查格式不验证字节真实性；upload_part.sha256：该分片实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；upload_session.sha256：上传方声明的完整文件SHA-256，合并后必须以实际字节重新计算核对；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| size_bytes | 必须 | integer; minimum=1 | 候选字段来源：media_asset.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0；upload_part.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0；upload_session.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "part_no": 1,
  "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "size_bytes": 1
}
```

5项上传操作、摘要/PNG-JPEG校验、持久消息确认和重复恢复已实测；其他媒体/病毒扫描、S3及正式来源仍待验证。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/part_no | upload_part.part_no | 分片路径与正文回执一致，编号正整数 |
| response/sha256 | upload_part.sha256, upload_session.sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/size_bytes | upload_part.size_bytes, upload_session.size_bytes | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-INGEST-002-E、TC-INGEST-002-N、TV-T023-E、TV-T023-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
