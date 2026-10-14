# 核查主张与证据关系：verifyClaim

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `bffa82adf57b9ccf1888d5589e7b3d54f03915c7b150bac6dcc627779d4769b4`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/claims/{id}/verify`；operationId=`verifyClaim`；源指针=`/paths/~1claims~1{id}~1verify/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式55业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

核查主张与证据关系；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`claim.analyze`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T099 实现权威证据检索与关系判断](../../../tasks/algorithm/T099.md)。

关联需求：FR-CLAIM-002、ER-T099；关联候选表：claim、claim_evidence_relation。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/ClaimVerify`；字段与完整约束见[数据结构](../data-structures.md#claimverify)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：claim.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；claim_evidence_relation.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：claim_evidence_relation.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "b469d78c-6e57-5a5e-b12a-e5bfd6a7eb6d",
  "evidence_ids": [
    "cdb06098-66ad-524f-a16f-3e8e692d50f1"
  ],
  "policy_version": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: Relation | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Relation`，详细字段见[数据结构](../data-structures.md#relation)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| claim_id | 必须 | string; format="uuid" | 候选字段来源：claim.claim_id：主键，由应用提供UUID；不视为访问凭证；claim_evidence_relation.claim_id：被证据支持、反对或关联的主张标识。来源引用不是写入许可，完整处理按操作核验。 |
| relation | 必须 | string; enum=["supports", "contradicts", "partially_supports", "unrelated", "insufficient"] | 候选字段来源：claim_evidence_relation.relation：主张与证据的关系类别，支持、反对或不足等取值以CHECK枚举为准。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=0; items=string; format="uuid" | 候选字段来源：claim_evidence_relation.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| score | 必须 | number; minimum=0; maximum=1 | 候选字段来源：claim_evidence_relation.score：主张证据关系对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：claim.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本；claim_evidence_relation.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "claim_id": "38d128c6-b4fc-5e0b-896c-05b26c757366",
  "relation": "supports",
  "evidence_ids": [
    "d657aabc-6541-55cf-9167-784b9d869fff"
  ],
  "score": 0.5,
  "model_version": "synthetic-v1"
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | claim.case_id, claim_evidence_relation.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/evidence_ids | claim_evidence_relation.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/policy_version | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/claim_id | claim.claim_id, claim_evidence_relation.claim_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/relation | claim_evidence_relation.relation | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/evidence_ids | claim_evidence_relation.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/score | claim_evidence_relation.score | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/model_version | claim.model_version, claim_evidence_relation.model_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-CLAIM-002-E、TC-CLAIM-002-N、TV-T099-E、TV-T099-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
