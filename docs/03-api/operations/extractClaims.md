# 提取结构化主张：extractClaims

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/claims/extract`；operationId=`extractClaims`；源指针=`/paths/~1claims~1extract/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

提取结构化主张；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`claim.analyze`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T098 实现结构化主张抽取服务](../../../tasks/algorithm/T098.md)。

关联需求：FR-CLAIM-001、ER-T098；关联候选表：claim、text_segment。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/ClaimExtract`；字段与完整约束见[数据结构](../data-structures.md#claimextract)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：claim.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；text_segment.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：claim.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；text_segment.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| source_segment_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：claim.source_segment_refs：主张对应文本或媒体片段引用对象，需定位到资产、片段和时间或字符范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "ea18b8a6-0826-5b92-b2a5-bb415987a577",
  "asset_id": "256895b2-4766-5e40-8c0c-df709078cb17",
  "source_segment_ids": [
    "bfcab501-4ac1-5ede-a2df-89df443fa654"
  ]
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: ClaimList | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`ClaimList`，详细字段见[数据结构](../data-structures.md#claimlist)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| claims | 必须 | array; minItems=0; items=Claim | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "claims": [
    {
      "claim_id": "76fff428-10bb-54e5-83e3-2f72cfdf5dce",
      "case_id": "1f56fb2d-dfe9-5951-91f6-c1c26eea76bd",
      "asset_id": "6362cf60-fed1-508a-8322-97445072ecd4",
      "subject": "synthetic-v1",
      "action": "synthetic-v1",
      "time": "synthetic-v1",
      "place": "synthetic-v1",
      "result": "synthetic-v1",
      "source_segment_ids": [
        "0bb525e1-d611-5569-ae83-eca423a1d2c3"
      ],
      "model_version": "synthetic-v1"
    }
  ],
  "warnings": []
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | claim.case_id, text_segment.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/asset_id | claim.asset_id, text_segment.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/source_segment_ids | claim.source_segment_refs | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].claim_id | claim.claim_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].case_id | claim.case_id, text_segment.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].asset_id | claim.asset_id, text_segment.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].subject | claim.subject | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].action | claim.action | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].time | claim.claim_time | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].place | claim.place | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].result | claim.result | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].source_segment_ids | claim.source_segment_refs | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claims[].model_version | claim.model_version, text_segment.model_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/warnings | 服务层输入/聚合，不直接生成数据库列 | 非正式告警与限制投影 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-CLAIM-001-E、TC-CLAIM-001-N、TV-T098-E、TV-T098-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
