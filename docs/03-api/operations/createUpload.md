# 创建分片上传会话：createUpload

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/uploads`；operationId=`createUpload`；源指针=`/paths/~1uploads/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

创建分片上传会话；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`asset.upload`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T022 实现分片上传初始化](../../../tasks/backend/T022.md)。

关联需求：FR-INGEST-002、ER-T022；关联候选表：upload_session、source_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/UploadCreate`；字段与完整约束见[数据结构](../data-structures.md#uploadcreate)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；upload_session.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| source_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.source_id：主键，由应用提供UUID；不视为访问凭证；upload_session.source_id：数据来源登记标识，指向source_registry.source_id。来源引用不是写入许可，完整处理按操作核验。 |
| filename | 必须 | string; minLength=1; maxLength=255 | 候选字段来源：upload_session.filename：上传时提供的展示文件名；不得直接拼接为服务器文件路径。来源引用不是写入许可，完整处理按操作核验。 |
| size_bytes | 必须 | integer; minimum=1 | 候选字段来源：upload_session.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0。来源引用不是写入许可，完整处理按操作核验。 |
| mime | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：upload_session.mime：探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名。来源引用不是写入许可，完整处理按操作核验。 |
| sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：upload_session.sha256：上传方声明的完整文件SHA-256，合并后必须以实际字节重新计算核对；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "3928e21f-5a0a-5e38-b1c7-148d650580c7",
  "source_id": "c07707dd-b7e5-5135-abe0-1dd2d128b8ed",
  "filename": "synthetic-v1",
  "size_bytes": 1,
  "mime": "synthetic-v1",
  "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: UploadSession | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`UploadSession`，详细字段见[数据结构](../data-structures.md#uploadsession)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| upload_id | 必须 | string; format="uuid" | 候选字段来源：upload_session.upload_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| part_size_bytes | 必须 | integer; minimum=1 | 候选字段来源：upload_session.part_size_bytes：上传会话约定的标准分片大小，单位字节；末片可小于此值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["UPLOADING", "VALIDATING", "COMPLETED", "REJECTED", "EXPIRED"] | 候选字段来源：upload_session.state：上传会话的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| expires_at | 必须 | string; format="date-time" | 候选字段来源：source_registry.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区；upload_session.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：source_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；upload_session.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "upload_id": "8132008d-1d2f-5dbd-b868-e893e70a2608",
  "part_size_bytes": 1,
  "state": "UPLOADING",
  "expires_at": "2030-01-01T00:00:00Z",
  "version": 1
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | source_registry.case_id, upload_session.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/source_id | source_registry.source_id, upload_session.source_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/filename | upload_session.filename | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/size_bytes | upload_session.size_bytes | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/mime | upload_session.mime | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/sha256 | upload_session.sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/upload_id | upload_session.upload_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/part_size_bytes | upload_session.part_size_bytes | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | upload_session.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/expires_at | source_registry.expires_at, upload_session.expires_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | source_registry.row_version, upload_session.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-INGEST-002-E、TC-INGEST-002-N、TV-T022-E、TV-T022-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
