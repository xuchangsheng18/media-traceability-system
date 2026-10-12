# 固化批准版本证据包：sealEvidence

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `c3471938106ec4211159d46b93c972416c2a678cd967214b2d23c48a12d8b2e7`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/evidence-packages/{case_id}/seal`；operationId=`sealEvidence`；源指针=`/paths/~1evidence-packages~1{case_id}~1seal/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

固化批准版本证据包；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`evidence.seal`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T104 实现证据固化与完整性校验](../../../tasks/backend/T104.md)、[T105 实现可信时间与签名适配层](../../../tasks/backend/T105.md)。

关联需求：FR-REVIEW-002、ER-T104、ER-T105、NFR-AUDIT-001、NFR-AVAIL-002；关联候选表：evidence_package、package_item、object_version、audit_event。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| case_id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/SealRequest`；字段与完整约束见[数据结构](../data-structures.md#sealrequest)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：evidence_package.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：evidence_package.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：package_item.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| operation_token | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| retention_policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：evidence_package.retention_policy_version：用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效；object_version.retention_policy_version：用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "task_id": "2b981c72-ecc2-52e4-829d-83e883b12725",
  "run_version": 1,
  "result_version": 1,
  "evidence_ids": [
    "a493b888-4d68-57cf-98d3-2aee80149b3b"
  ],
  "approval_id": "929862ff-647d-5680-822e-c175b403baa4",
  "operation_token": "synthetic-v1",
  "retention_policy_version": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: EvidencePackage | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`EvidencePackage`，详细字段见[数据结构](../data-structures.md#evidencepackage)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| package_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.package_id：主键，由应用提供UUID；不视为访问凭证；package_item.package_id：固化证据包的版本记录标识。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；evidence_package.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；object_version.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；package_item.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；evidence_package.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；evidence_package.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version；object_version.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；package_item.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| manifest | 必须 | array; minItems=0; items=Evidence | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| manifest_sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：evidence_package.manifest_sha256：固化证据包规范化清单的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| signature_status | 必须 | string; enum=["not_signed", "mock", "verified", "failed"] | 候选字段来源：evidence_package.signature_status：证据包签名处理状态；状态文字不能代替签名验证证据。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["DRAFT", "SEALED", "SUPERSEDED"] | 候选字段来源：evidence_package.state：固化证据包版本的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：audit_event.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；evidence_package.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；object_version.created_at：对象版本登记入库时刻；TIMESTAMPTZ保存时间点，显示时区由会话决定，不保留原始时区名称；package_item.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "package_id": "e8cb0e6c-e165-5a59-a620-80fd3ff593d8",
  "case_id": "be06835d-1e51-58f0-9d39-83ee726a35c0",
  "task_id": "8c08272f-5307-5dac-a540-98b2962b3af5",
  "version": 1,
  "manifest": [
    {
      "evidence_id": "caba225b-3165-5c83-8196-73cd47fc7355",
      "case_id": "a0c77333-9207-5cfb-ba58-deca82197a3e",
      "task_id": "2e9d71b8-0768-5f0a-8408-28ef1c0f519c",
      "run_version": 1,
      "result_version": 1,
      "kind": "original",
      "asset_id": "7d22b8e1-0ddf-5a52-ae12-2185b8725fa8",
      "object_ref": {
        "object_id": "a63e95cb-376f-508a-ab64-d9ea3f44381c",
        "version_id": "synthetic-v1",
        "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
      },
      "time_range": {
        "start_ms": 0,
        "end_ms": 1000
      },
      "bbox": {
        "x": 0.1,
        "y": 0.1,
        "width": 0.4,
        "height": 0.4
      },
      "mapping_version": "synthetic-v1",
      "model_name": "synthetic-v1",
      "model_version": "synthetic-v1",
      "authorization_version": "synthetic-v1",
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "version": 1,
      "created_at": "2030-01-01T00:00:00Z"
    }
  ],
  "manifest_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "approval_id": "5c929a00-75cf-5acf-bda7-be7b7fc088a6",
  "signature_status": "not_signed",
  "state": "DRAFT",
  "created_at": "2030-01-01T00:00:00Z"
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/task_id | evidence_package.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/run_version | evidence_package.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/result_version | evidence_package.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/evidence_ids | package_item.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/approval_id | evidence_package.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/operation_token | 服务层输入/聚合，不直接生成数据库列 | 一次性随机凭据只返回本次；DB只存token_sha256 |
| request/retention_policy_version | evidence_package.retention_policy_version, object_version.retention_policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/package_id | evidence_package.package_id, package_item.package_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/case_id | audit_event.case_id, evidence_package.case_id, object_version.case_id, package_item.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/task_id | evidence_package.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | audit_event.row_version, evidence_package.row_version, evidence_package.version, object_version.row_version, package_item.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].evidence_id | package_item.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].case_id | audit_event.case_id, evidence_package.case_id, object_version.case_id, package_item.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].task_id | evidence_package.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].run_version | evidence_package.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].result_version | evidence_package.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].kind | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].asset_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].object_ref | object_version.object_id, object_version.sha256, object_version.version_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].object_ref.object_id | audit_event.object_id, object_version.object_id, package_item.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].object_ref.version_id | object_version.version_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].object_ref.sha256 | object_version.sha256, package_item.sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].time_range | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].time_range.start_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].time_range.end_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].bbox | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].bbox.x | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].bbox.y | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].bbox.width | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].bbox.height | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].mapping_version | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].model_name | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].model_version | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].authorization_version | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].sha256 | object_version.sha256, package_item.sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].version | audit_event.row_version, evidence_package.row_version, evidence_package.version, object_version.row_version, package_item.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest[].created_at | audit_event.created_at, evidence_package.created_at, object_version.created_at, package_item.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/manifest_sha256 | evidence_package.manifest_sha256 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/approval_id | evidence_package.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/signature_status | evidence_package.signature_status | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | evidence_package.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/created_at | audit_event.created_at, evidence_package.created_at, object_version.created_at, package_item.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-REVIEW-002-E、TC-REVIEW-002-N、TV-T008-E、TV-T008-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T025-E、TV-T025-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T105-E、TV-T105-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N、TV-T121-E、TV-T121-N、TV-T124-E、TV-T124-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
