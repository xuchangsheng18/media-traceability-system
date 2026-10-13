# 申请模型灰度激活或回滚：rolloutModel

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/models/{id}/rollouts`；operationId=`rolloutModel`；源指针=`/paths/~1models~1{id}~1rollouts/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

申请模型灰度激活或回滚；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`model.release`。

组织级模型/配置/索引管理；系统管理员不自动取得案件原件，依赖数据仍核验用途。

来源任务：[T057 实现模型灰度发布](../../../tasks/algorithm/T057.md)、[T060 开发模型运维页面](../../../tasks/frontend/T060.md)、[T170 实施模型压缩导出与发布候选冻结](../../../tasks/algorithm/T170.md)。

关联需求：FR-OPS-001、FR-OPS-003、ER-T057、ER-T060、ER-T170、NFR-COMPAT-001、NFR-AI-001；关联候选表：model_release、approval_request、index_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |
| If-Match | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/Rollout`；字段与完整约束见[数据结构](../data-structures.md#rollout)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| release_bundle_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证；model_release.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| operation_token | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_release.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| mode | 必须 | string; enum=["shadow", "canary", "activate", "rollback"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| percentage | 必须 | number; minimum=0; maximum=100 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| index_version | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：index_registry.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本；model_release.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "release_bundle_id": "bd14a18d-b3df-5780-ad0f-659f5395970a",
  "approval_id": "e0cdd1b7-2a2e-573d-8abd-96298f9baad0",
  "operation_token": "synthetic-v1",
  "expected_version": 1,
  "mode": "shadow",
  "percentage": 0.5,
  "index_version": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 202 | 契约成功响应；异步受理不代表结果完成 | application/json: ActionAck | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 412 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 428 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`ActionAck`，详细字段见[数据结构](../data-structures.md#actionack)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| object_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键；audit_event.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_export.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_release.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；audit_export.state：审计导出作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；index_registry.state：索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；model_release.state：模型发布包的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.request_id：贯穿接口、任务和审计的请求追踪标识；不充当权限凭证。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "object_id": "cb2fc0da-fcb0-56f5-b97a-5b3ac871a487",
  "version": 1,
  "state": "synthetic-v1",
  "request_id": "475ac694-56aa-515f-9ef7-16e7fc2db444"
}
```

202返回ActionAck；mode已有shadow/canary/activate/rollback。缺进度/失败/最终切换查询IF-G05，模型健康不是灰度完成。

该接口声明If-Match：必须服务端原子核验对象版本；缺少条件428、旧版本412、状态不许可409。ETag绑定对象/聚合的精确范围仍按业务设计及缺口评审，body expected_version不能代替条件更新。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/release_bundle_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/approval_id | approval_request.approval_id, model_release.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/operation_token | 服务层输入/聚合，不直接生成数据库列 | 一次性随机凭据只返回本次；DB只存token_sha256 |
| request/expected_version | approval_request.row_version, index_registry.row_version, model_release.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/mode | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/percentage | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/index_version | index_registry.index_version, model_release.index_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_id | approval_request.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | approval_request.row_version, index_registry.row_version, model_release.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | approval_request.state, index_registry.state, model_release.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/request_id | 服务层输入/聚合，不直接生成数据库列 | 请求追踪/审计，不作为业务对象ID |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TC-OPS-003-E、TC-OPS-003-N、TV-T002-E、TV-T002-N、TV-T003-E、TV-T003-N、TV-T051-E、TV-T051-N、TV-T052-E、TV-T052-N、TV-T053-E、TV-T053-N、TV-T054-E、TV-T054-N、TV-T057-E、TV-T057-N、TV-T058-E、TV-T058-N、TV-T060-E、TV-T060-N、TV-T081-E、TV-T081-N、TV-T113-E、TV-T113-N、TV-T114-E、TV-T114-N、TV-T115-E、TV-T115-N、TV-T116-E、TV-T116-N、TV-T125-E、TV-T125-N、TV-T128-E、TV-T128-N、TV-T141-E、TV-T141-N、TV-T153-E、TV-T153-N、TV-T163-E、TV-T163-N、TV-T165-E、TV-T165-N、TV-T167-E、TV-T167-N、TV-T170-E、TV-T170-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
