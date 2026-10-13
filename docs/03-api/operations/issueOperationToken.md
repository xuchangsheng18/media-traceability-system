# 签发受限操作确认凭据：issueOperationToken

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/operation-tokens`；operationId=`issueOperationToken`；源指针=`/paths/~1operation-tokens/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

签发受限操作确认凭据；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`operation.confirm`。

按object_type/purpose核验组织或案件对象；模型发布可为组织级，操作确认不能等同业务批准。

来源任务：[T016 实现高风险操作二次确认](../../../tasks/platform/T016.md)。

关联需求：FR-OPS-001、ER-T016、NFR-SEC-001；关联候选表：operation_token。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/OperationTokenRequest`；字段与完整约束见[数据结构](../data-structures.md#operationtokenrequest)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：operation_token.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| object_id | 必须 | string; format="uuid" | 候选字段来源：operation_token.object_id：该记录绑定的业务目标对象ID；沿用关联审批请求的对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：operation_token.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：operation_token.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "approval_id": "141b1f82-5034-5ab9-be25-179a17b2736d",
  "object_id": "fd27383e-f22c-5fe1-b1de-a9f9a668704b",
  "object_version": 1,
  "purpose": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: OperationToken | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`OperationToken`，详细字段见[数据结构](../data-structures.md#operationtoken)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| operation_token | 必须 | string; minLength=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expires_at | 必须 | string; format="date-time" | 候选字段来源：operation_token.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：operation_token.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "operation_token": "synthetic-v1",
  "expires_at": "2030-01-01T00:00:00Z",
  "object_version": 1
}
```

操作确认只防误操作，不替代身份、权限或审批；执行仍核验撤销、版本、到期与单次使用规则。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/approval_id | operation_token.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/object_id | operation_token.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/object_version | operation_token.object_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/purpose | operation_token.purpose | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/operation_token | 服务层输入/聚合，不直接生成数据库列 | 一次性随机凭据只返回本次；DB只存token_sha256 |
| response/expires_at | operation_token.expires_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_version | operation_token.object_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TV-T011-E、TV-T011-N、TV-T012-E、TV-T012-N、TV-T013-E、TV-T013-N、TV-T014-E、TV-T014-N、TV-T015-E、TV-T015-N、TV-T016-E、TV-T016-N、TV-T018-E、TV-T018-N、TV-T118-E、TV-T118-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
