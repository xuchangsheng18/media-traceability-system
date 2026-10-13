# 开发身份登录：devLogin

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `556c92bd7b22602c83bd71aa3ea5cc11cdefb48926a18c03428b293860e2f7ba`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/auth/login`；operationId=`devLogin`；源指针=`/paths/~1auth~1login/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

开发身份登录；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[]`；功能权限候选：`development.login`。

仅开发匿名登录入口，需关闭策略、限流及安全日志，不当生产身份。

来源任务：[T013 实现认证与令牌校验](../../../tasks/platform/T013.md)。

关联需求：FR-OPS-001、ER-T013、NFR-SEC-001；关联候选表：users。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/AuthLogin`；字段与完整约束见[数据结构](../data-structures.md#authlogin)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| username | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| password | 必须 | string; minLength=1; writeOnly=true | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "username": "synthetic-v1",
  "password": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: AuthSession | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`AuthSession`，详细字段见[数据结构](../data-structures.md#authsession)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| access_token | 必须 | string; minLength=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| token_type | 必须 | const="Bearer" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expires_in | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "access_token": "synthetic-v1",
  "token_type": "Bearer",
  "expires_in": 1
}
```

development-only且security=[]；生产关闭。当前PoC用预置研发Bearer，未实现此密码登录端点，不当正式单点登录。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/username | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/password | 服务层输入/聚合，不直接生成数据库列 | 开发适配器验散列，生产接口关闭；不得保存明文 |
| response/access_token | 服务层输入/聚合，不直接生成数据库列 | 开发身份提供者签发，不在业务表明文存储 |
| response/token_type | 服务层输入/聚合，不直接生成数据库列 | 固定Bearer |
| response/expires_in | 服务层输入/聚合，不直接生成数据库列 | 身份源到期计算 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TV-T011-E、TV-T011-N、TV-T012-E、TV-T012-N、TV-T013-E、TV-T013-N、TV-T014-E、TV-T014-N、TV-T015-E、TV-T015-N、TV-T016-E、TV-T016-N、TV-T018-E、TV-T018-N、TV-T118-E、TV-T118-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
