# 读取已接收分片用于续传：listUploadParts

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `bffa82adf57b9ccf1888d5589e7b3d54f03915c7b150bac6dcc627779d4769b4`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/uploads/{id}/parts`；operationId=`listUploadParts`；源指针=`/paths/~1uploads~1{id}~1parts/get`。

实现范围：**DEV_PARTIAL**；独立业务HTTP/真实PostgreSQL/RLS已实现；默认无权威身份提供方返回503，测试提供方仅在fixture注入。。正式55业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

读取已接收分片用于续传；当前身份、单位、案件和来源均重新核验。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.upload`。

先在当前主体RLS范围查找上传所属案件，再核验asset.upload及来源用途；UUID不是凭证。

来源任务：[T022 实现分片上传初始化](../../../tasks/backend/T022.md)、[T023 实现分片接收与校验](../../../tasks/backend/T023.md)、[T026 实现媒体格式探测与安全校验](../../../tasks/backend/T026.md)。

关联需求：；关联候选表：upload_session、upload_part。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| cursor | query | False | string; minLength=1 |
| limit | query | False | integer; minimum=1; maximum=100; default=100 |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: UploadPartPage |  |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`UploadPartPage`，详细字段见[数据结构](../data-structures.md#uploadpartpage)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; items=UploadPart | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| session_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "items": [],
  "next_cursor": null,
  "session_version": 1
}
```

5项上传操作、摘要/PNG-JPEG校验、持久消息确认和重复恢复已实测；其他媒体/病毒扫描、S3及正式来源仍待验证。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/items | upload_part.part_no, upload_part.sha256, upload_part.size_bytes | 已认可首批实现方案：当前案件/来源核验、实际分片账本和绑定会话版本的签名游标；不作正式冻结。 |
| response/next_cursor | 服务层输入/聚合，不直接生成数据库列 | 已认可首批实现方案：当前案件/来源核验、实际分片账本和绑定会话版本的签名游标；不作正式冻结。 |
| response/session_version | upload_session.row_version | 已认可首批实现方案：当前案件/来源核验、实际分片账本和绑定会话版本的签名游标；不作正式冻结。 |
| response/items[].part_no | upload_part.part_no | 会话/分片账本当前投影；到期与VALIDATING/COMPLETED/REJECTED状态按实际数据库及当前授权计算；duplicate_of在读取时重核来源，撤销则隐藏。 |
| response/items[].sha256 | upload_part.sha256 | 会话/分片账本当前投影；到期与VALIDATING/COMPLETED/REJECTED状态按实际数据库及当前授权计算；duplicate_of在读取时重核来源，撤销则隐藏。 |
| response/items[].size_bytes | upload_part.size_bytes | 会话/分片账本当前投影；到期与VALIDATING/COMPLETED/REJECTED状态按实际数据库及当前授权计算；duplicate_of在读取时重核来源，撤销则隐藏。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
