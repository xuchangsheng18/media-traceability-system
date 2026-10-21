# 读取索引版本：getIndex

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/indices/{id}`；operationId=`getIndex`；源指针=`/paths/~1indices~1{id}/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取索引版本；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`index.manage`。

组织级模型/配置/索引管理；系统管理员不自动取得案件原件，依赖数据仍核验用途。

来源任务：[T081 建立Milvus索引与版本管理](../../../tasks/algorithm/T081.md)、[T157 优化复制向量与索引联合参数](../../../tasks/algorithm/T157.md)。

关联需求：FR-IMGRET-001、FR-IMGRET-003、FR-VIDTRACE-001、ER-T081、ER-T157、NFR-COMPAT-001、NFR-PERF-001；关联候选表：index_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: IndexVersion | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`IndexVersion`，详细字段见[数据结构](../data-structures.md#indexversion)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| index_id | 必须 | string; format="uuid" | 候选字段来源：index_registry.index_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| capability | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.capability：模型或索引提供的能力编码，取值对应内部推理能力契约。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |
| dimension | 必须 | integer; minimum=1 | 候选字段来源：index_registry.dimension：特征向量维度，必须为正整数并与模型及索引配置一致。来源引用不是写入许可，完整处理按操作核验。 |
| normalization | 必须 | string; enum=["l2", "none"] | 候选字段来源：index_registry.normalization：特征归一化方法，例如l2或none；应与训练、查询和索引构建保持一致。来源引用不是写入许可，完整处理按操作核验。 |
| index_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["BUILDING", "READY", "ACTIVE", "RETIRED"] | 候选字段来源：index_registry.state：索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| row_version | 必须 | integer; minimum=1 | 候选字段来源：audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "index_id": "425a4652-15d8-5e93-810b-52827c74dab9",
  "capability": "synthetic-v1",
  "model_version": "synthetic-v1",
  "dimension": 1,
  "normalization": "l2",
  "index_version": "synthetic-v1",
  "state": "BUILDING",
  "row_version": 1
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/index_id | index_registry.index_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/capability | index_registry.capability | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/model_version | index_registry.model_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/dimension | index_registry.dimension | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/normalization | index_registry.normalization | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/index_version | index_registry.index_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | index_registry.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/row_version | index_registry.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-IMGRET-001-E、TC-IMGRET-001-N、TC-IMGRET-003-E、TC-IMGRET-003-N、TC-VIDTRACE-001-E、TC-VIDTRACE-001-N、TV-T002-E、TV-T002-N、TV-T003-E、TV-T003-N、TV-T051-E、TV-T051-N、TV-T052-E、TV-T052-N、TV-T053-E、TV-T053-N、TV-T054-E、TV-T054-N、TV-T055-E、TV-T055-N、TV-T081-E、TV-T081-N、TV-T120-E、TV-T120-N、TV-T122-E、TV-T122-N、TV-T123-E、TV-T123-N、TV-T157-E、TV-T157-N、TV-T170-E、TV-T170-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
