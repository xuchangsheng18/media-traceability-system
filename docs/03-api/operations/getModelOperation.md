# getModelOperation：getModelOperation

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/model-operations/{id}`；operationId=`getModelOperation`；源指针=`/paths/~1model-operations~1{id}/get`。

实现范围：**DEV_PARTIAL**；组织权限、发布包/模型绑定及终态检查已实现；实际发布记录来自显式部署适配器，默认503。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取真实记录或执行明确授权的受控操作；具体边界见剩余接口实现说明。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`model.read`。

每次核验当前身份/功能权限和单位/案件范围；组织级策略不借用虚构案件。

来源任务：[T057 实现模型灰度发布](../../../tasks/algorithm/T057.md)、[T060 开发模型运维页面](../../../tasks/frontend/T060.md)、[T170 实施模型压缩导出与发布候选冻结](../../../tasks/algorithm/T170.md)。

关联需求：；关联候选表：model_registry、model_release。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 实际案件/来源权限核验后的当前上传记录 | application/json: ModelOperation |  |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`ModelOperation`，详细字段见[数据结构](../data-structures.md#modeloperation)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| operation_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| org_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| release_bundle_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mode | 必须 | string; enum=["shadow", "canary", "activate", "rollback"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| state | 必须 | string; enum=["REQUESTED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| progress | 必须 | number; minimum=0; maximum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| index_version | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| error_code | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "operation_id": "00000000-0000-4000-8000-000000000001",
  "org_id": "00000000-0000-4000-8000-000000000001",
  "release_bundle_id": "00000000-0000-4000-8000-000000000001",
  "model_id": "00000000-0000-4000-8000-000000000001",
  "mode": "shadow",
  "state": "REQUESTED",
  "version": 1,
  "progress": 0,
  "model_version": "synthetic-example",
  "index_version": null,
  "error_code": null
}
```

文档与路由不代表正式接入、真实模型或完整业务验收。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/operation_id | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/org_id | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/release_bundle_id | model_release.release_id | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/model_id | model_release.model_id | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/mode | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/state | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/version | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/progress | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/model_version | model_registry.version | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/index_version | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |
| response/error_code | 服务层输入/聚合，不直接生成数据库列 | 实际部署适配器的操作记录字段；所列SQL列只作发布包/模型绑定核验。operation_id、version、progress、state及error_code不得从模型健康或model_registry.row_version拼造。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
