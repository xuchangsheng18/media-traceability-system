# getAuditExport：getAuditExport

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/audit/exports/{id}`；operationId=`getAuditExport`；源指针=`/paths/~1audit~1exports~1{id}/get`。

实现范围：**DEV_PARTIAL**；真实数据库或显式适配端口已实现，默认未接入的权威依赖返回503；实际结果按本批测试记录。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取真实记录或执行明确授权的受控操作；具体边界见剩余接口实现说明。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`audit.export`。

每次核验当前身份/功能权限和单位/案件范围；组织级策略不借用虚构案件。

来源任务：[T017 实现操作审计事件模型](../../../tasks/platform/T017.md)、[T018 开发审计查询页面与接口](../../../tasks/frontend/T018.md)。

关联需求：；关联候选表：audit_export、approval_request。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: AuditExportStatus |  |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`AuditExportStatus`，详细字段见[数据结构](../data-structures.md#auditexportstatus)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| export_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| state | 必须 | string; enum=["REQUESTED", "READY", "FAILED", "EXPIRED", "REVOKED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifact | 必须 | anyOf(ObjectRef; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| size_bytes | 必须 | anyOf(integer; minimum=0; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| error_code | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "export_id": "00000000-0000-4000-8000-000000000001",
  "case_id": "00000000-0000-4000-8000-000000000001",
  "state": "REQUESTED",
  "version": 1,
  "artifact": null,
  "size_bytes": null,
  "expires_at": null,
  "error_code": null
}
```

文档与路由不代表正式接入、真实模型或完整业务验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/export_id | audit_export.export_id | 真实审计作业账本的标识、案件、状态及行版本。 |
| response/case_id | audit_export.case_id | 真实审计作业账本的标识、案件、状态及行版本。 |
| response/state | audit_export.state | 真实审计作业账本的标识、案件、状态及行版本。 |
| response/version | audit_export.row_version | 真实审计作业账本的标识、案件、状态及行版本。 |
| response/artifact | audit_export.artifact_ref | 固定导出产物元数据存于artifact_ref；object_id/version_id/sha256另核验同案件object_version，过期、撤销或无READY产物拒绝下载。 |
| response/artifact.object_id | audit_export.artifact_ref | 固定导出产物元数据存于artifact_ref；object_id/version_id/sha256另核验同案件object_version，过期、撤销或无READY产物拒绝下载。 |
| response/artifact.version_id | audit_export.artifact_ref | 固定导出产物元数据存于artifact_ref；object_id/version_id/sha256另核验同案件object_version，过期、撤销或无READY产物拒绝下载。 |
| response/artifact.sha256 | audit_export.artifact_ref | 固定导出产物元数据存于artifact_ref；object_id/version_id/sha256另核验同案件object_version，过期、撤销或无READY产物拒绝下载。 |
| response/size_bytes | audit_export.artifact_ref | 固定导出产物元数据存于artifact_ref；object_id/version_id/sha256另核验同案件object_version，过期、撤销或无READY产物拒绝下载。 |
| response/expires_at | audit_export.artifact_ref | 固定导出产物元数据存于artifact_ref；object_id/version_id/sha256另核验同案件object_version，过期、撤销或无READY产物拒绝下载。 |
| response/error_code | audit_export.artifact_ref | 固定导出产物元数据存于artifact_ref；object_id/version_id/sha256另核验同案件object_version，过期、撤销或无READY产物拒绝下载。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
