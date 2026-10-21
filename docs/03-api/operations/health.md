# 依赖健康检查：health

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/health`；operationId=`health`；源指针=`/paths/~1health/get`。

实现范围：**DEV_PARTIAL**；按当前PoC说明核验开发子范围。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

依赖健康检查；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`health.read`。

服务健康范围，不能凭空要求绑定案件；研发实现只固定Bearer/数据库检查。

来源任务：[T002 配置Python后端工程](../../../tasks/platform/T002.md)、[T003 配置Vue前端工程](../../../tasks/frontend/T003.md)、[T004 建立本地容器开发环境](../../../tasks/platform/T004.md)。

关联需求：ER-T002、ER-T003、ER-T004、NFR-COMPAT-001、NFR-DEPLOY-001；关联候选表：无。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: Health | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Health`，详细字段见[数据结构](../data-structures.md#health)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| status | 必须 | string; enum=["ok", "degraded", "unavailable"] | 候选字段来源：model_registry.status：模型版本与许可引用的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "status": "ok",
  "request_id": "ba48af75-167b-57f6-871c-64a53cbbe2e1"
}
```

同路径研发实现只核验固定Bearer和数据库连通；不是正式身份/策略或全部依赖健康验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/status | 服务层输入/聚合，不直接生成数据库列 | 相应对象状态或健康聚合；按Schema与操作区分 |
| response/request_id | 服务层输入/聚合，不直接生成数据库列 | 请求追踪/审计，不作为业务对象ID |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TV-T002-E、TV-T002-N、TV-T003-E、TV-T003-N、TV-T004-E、TV-T004-N、TV-T007-E、TV-T007-N、TV-T051-E、TV-T051-N、TV-T052-E、TV-T052-N、TV-T053-E、TV-T053-N、TV-T054-E、TV-T054-N、TV-T055-E、TV-T055-N、TV-T081-E、TV-T081-N、TV-T120-E、TV-T120-N、TV-T121-E、TV-T121-N、TV-T170-E、TV-T170-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
