# getSource：getSource

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/sources/{id}`；operationId=`getSource`；源指针=`/paths/~1sources~1{id}/get`。

实现范围：**DEV_PARTIAL**；真实数据库或显式适配端口已实现，默认未接入的权威依赖返回503；实际结果按本批测试记录。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取真实记录或执行明确授权的受控操作；具体边界见剩余接口实现说明。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`source.read`。

每次核验当前身份/功能权限和单位/案件范围；组织级策略不借用虚构案件。

来源任务：[T021 实现数据来源授权登记](../../../tasks/backend/T021.md)、[T029 实现第三方接入适配器协议](../../../tasks/backend/T029.md)。

关联需求：；关联候选表：source_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: Source |  |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Source`，详细字段见[数据结构](../data-structures.md#source)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| source_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.source_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：source_registry.name：名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键。来源引用不是写入许可，完整处理按操作核验。 |
| source_type | 必须 | string; enum=["authorized_business", "public_licensed", "user_submission", "synthetic"] | 候选字段来源：source_registry.source_type：素材来源类别的编码；分类词表由接入配置定义，当前DDL未枚举限制。来源引用不是写入许可，完整处理按操作核验。 |
| authorization_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：source_registry.authorization_ref：来源授权凭据的受控引用，供核查用途和期限；不存访问令牌或明文密钥。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | array; minItems=1; uniqueItems=true; items=string; minLength=1; maxLength=128 | 候选字段来源：source_registry.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 候选字段来源：source_registry.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| authorization_status | 必须 | string; enum=["pending", "verified", "expired", "revoked"] | 候选字段来源：source_registry.authorization_status：来源或数据集用途授权的当前审核状态，未验证状态不得解释为可正式使用。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：source_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "source_id": "7a6ac87e-366f-5815-b6b8-56057ae0001f",
  "case_id": "7499aa91-4678-50cd-9baa-21adfeb1421a",
  "name": "synthetic-v1",
  "source_type": "authorized_business",
  "authorization_ref": "synthetic-v1",
  "purpose": [
    "synthetic-v1"
  ],
  "expires_at": "2030-01-01T00:00:00Z",
  "authorization_status": "pending",
  "version": 1
}
```

文档与路由不代表正式接入、真实模型或完整业务验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/source_id | source_registry.source_id | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/case_id | source_registry.case_id | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/name | source_registry.name | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/source_type | source_registry.source_type | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/authorization_ref | source_registry.authorization_ref | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/purpose | source_registry.purpose | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/expires_at | source_registry.expires_at | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/authorization_status | source_registry.authorization_status | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | source_registry.row_version | 同案件来源元数据读取，到期的verified显示expired；登记或读取不等于取得正式用途授权。服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
