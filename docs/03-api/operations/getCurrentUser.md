# 读取当前用户与范围：getCurrentUser

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/auth/me`；operationId=`getCurrentUser`；源指针=`/paths/~1auth~1me/get`。

实现范围：**DEV_PARTIAL**；独立业务开发工程已挂载真实访问/校验；权威提供方未配置时拒绝，不提供生产模拟成功。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取当前用户与范围；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`identity.read`。

当前已验证主体及有效范围；不允许客户端指定任意主体，角色不自动授予案件内容访问。

来源任务：[T013 实现认证与令牌校验](../../../tasks/platform/T013.md)、[T014 实现接口级权限控制](../../../tasks/platform/T014.md)、[T015 实现数据范围访问控制](../../../tasks/platform/T015.md)。

关联需求：FR-RESOURCE-003、FR-OPS-001、ER-T013、ER-T014、ER-T015、NFR-SEC-001；关联候选表：users、user_roles、case_membership。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: CurrentUser | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`CurrentUser`，详细字段见[数据结构](../data-structures.md#currentuser)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| user_id | 必须 | string; format="uuid" | 候选字段来源：case_membership.user_id：用户与认证主体标识，指向users.user_id；user_roles.user_id：用户与认证主体标识，指向users.user_id；users.user_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| org_id | 必须 | string; format="uuid" | 候选字段来源：case_membership.org_id：记录所属单位标识；单位授权范围由服务端认证上下文确定；users.org_id：记录所属单位标识；单位授权范围由服务端认证上下文确定。来源引用不是写入许可，完整处理按操作核验。 |
| roles | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| permissions | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "user_id": "5c6b3497-cd91-5273-9bfd-500a51527582",
  "org_id": "03c903c9-210a-5ad6-84c2-560b37c8f9ec",
  "roles": [
    "synthetic-v1"
  ],
  "permissions": [
    "synthetic-v1"
  ],
  "case_ids": [
    "1b37ab11-4526-53f9-8d49-5a919c8c68e4"
  ]
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/user_id | case_membership.user_id, user_roles.user_id, users.user_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/org_id | case_membership.org_id, users.org_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/roles | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/permissions | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/case_ids | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TC-RESOURCE-003-E、TC-RESOURCE-003-N、TV-T011-E、TV-T011-N、TV-T012-E、TV-T012-N、TV-T013-E、TV-T013-N、TV-T014-E、TV-T014-N、TV-T015-E、TV-T015-N、TV-T016-E、TV-T016-N、TV-T018-E、TV-T018-N、TV-T118-E、TV-T118-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
