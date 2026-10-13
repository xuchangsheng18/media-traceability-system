# 受控下载固定报告版本：downloadReport

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/reports/{id}/content`；operationId=`downloadReport`；源指针=`/paths/~1reports~1{id}~1content/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

受控下载固定报告版本；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`report.export`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T107 实现核查报告生成](../../../tasks/backend/T107.md)。

关联需求：FR-REVIEW-003、ER-T107、NFR-AUDIT-001；关联候选表：report、approval_request、audit_event。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| Range | header | False | string; minLength=1; maxLength=128 |
| If-Range | header | False | string; minLength=1; maxLength=128 |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 受控二进制内容，逐请求和Range均鉴权 | application/octet-stream: string; format="binary" | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128; Cache-Control: const="no-store" |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 206 | 受控二进制内容，逐请求和Range均鉴权 | application/octet-stream: string; format="binary" | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128; Cache-Control: const="no-store"; Content-Range: string; minLength=1; maxLength=128 |
| 416 | 请求范围无法满足 | application/problem+json: Problem |  |
逐次Range核验report_export批准、当前授权和固定报告/对象版本；撤销后下一请求拒绝，READY不自动准许导出。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-REVIEW-003-E、TC-REVIEW-003-N、TV-T008-E、TV-T008-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
