# 读取首发候选排序快照：getFirstSource

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `83f2f8bb7b2cb2a59a26bd1e706a09b308358c6ad33658f84e6f1f9a50d01730`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/clusters/{id}/first-source`；operationId=`getFirstSource`；源指针=`/paths/~1clusters~1{id}~1first-source/get`。

实现范围：**DEV_PARTIAL**；独立业务HTTP/真实PostgreSQL/RLS已实现；默认无权威身份提供方返回503，测试提供方仅在fixture注入。。当前73业务契约保持正式未冻结；独立业务工程的实际子范围见本页实现状态，PoC入口另列。

## 调用目的与权限

读取首发候选排序快照；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`origin.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T093 实现首发候选查询服务](../../../tasks/backend/T093.md)。

关联需求：FR-ORIGIN-002、FR-ORIGIN-003、ER-T093；关联候选表：content_cluster、cluster_member、first_source_candidate、first_source_ranking。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| ranking_id | query | False | string; format="uuid" |
| history | query | False | object; additionalProperties=false |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: FirstSource | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128; X-Task-Id: string; format="uuid"; X-Run-Version: integer; minimum=1; X-Result-Version: integer; minimum=1 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`FirstSource`，详细字段见[数据结构](../data-structures.md#firstsource)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| cluster_id | 必须 | string; format="uuid" | 候选字段来源：first_source_ranking.cluster_id：高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证。来源引用不是写入许可，完整处理按操作核验。 |
| scope | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：content_cluster.scope：内容簇覆盖的比较范围标识或说明；整体同源与指定片段范围必须区分。来源引用不是写入许可，完整处理按操作核验。 |
| candidates | 必须 | array; minItems=0; maxItems=3; items=object; additionalProperties=false | 候选字段来源：first_source_candidate.ranking_id：所属首发排序快照ID；与案件及簇共同绑定first_source_ranking，不能混合不同计算结果。来源引用不是写入许可，完整处理按操作核验。 |
| candidates[].asset_id | 必须（父对象存在时） | string; format="uuid" | 本批次列为首发候选的媒体资产标识；必须属于同案件及本簇cluster_member，不能引用簇外素材 |
| candidates[].rank | 必须（父对象存在时） | integer; minimum=1; maximum=3 | 本次排序批次内的候选名次，从1连续排列到候选数量，最多3；不是确定首发结论 |
| candidates[].probability | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| candidates[].published_at | 必须（父对象存在时） | anyOf(string; format="date-time"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| candidates[].evidence_ids | 必须（父对象存在时） | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| candidates[].counter_evidence_ids | 必须（父对象存在时） | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["candidate", "insufficient", "reviewed"] | 候选字段来源：first_source_ranking.status：candidate为待核查候选，insufficient为证据不足，reviewed为已复核快照；reviewed仍非法律结论。来源引用不是写入许可，完整处理按操作核验。 |
| coverage_note | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：first_source_ranking.coverage_note：本次观察的平台、时间和素材覆盖范围及缺失说明；不能声称覆盖未知全网。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：first_source_ranking.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |
| ranking_id | 必须 | string; format="uuid" | 候选字段来源：first_source_ranking.ranking_id：一次首发排序结果快照的唯一标识；重算或复核更正生成新快照。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：first_source_ranking.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：first_source_ranking.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：first_source_ranking.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1 | 候选字段来源：first_source_ranking.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| candidate_count | 必须 | integer; minimum=0; maximum=3 | 候选字段来源：first_source_ranking.candidate_count：该快照应包含的候选总数；事务提交时必须与明细数量相等，0表示有结果但无足够候选。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "cluster_id": "5e96cd6e-b9f5-536f-8141-ceaf9571e0d9",
  "scope": "synthetic-v1",
  "candidates": [
    {
      "asset_id": "da63f23b-1d1e-5058-9383-de3a4a6f7667",
      "rank": 1,
      "probability": 0.5,
      "published_at": "2030-01-01T00:00:00Z",
      "evidence_ids": [
        "f66ae965-54be-597f-85fe-870910f0c261"
      ],
      "counter_evidence_ids": []
    }
  ],
  "status": "candidate",
  "coverage_note": "synthetic-v1",
  "model_version": "synthetic-v1",
  "ranking_id": "11111111-1111-4111-8111-111111111111",
  "task_id": "22222222-2222-4222-8222-222222222222",
  "run_version": 1,
  "result_version": 1,
  "policy_version": "synthetic-v1",
  "candidate_count": 1
}
```

按精确task/run/result及当前权限读取不可变快照，7项HTTP和版本头已实测；尚无实际业务结果生产器，缺失快照404、旧映射未登记503。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/cluster_id | first_source_ranking.cluster_id | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/scope | content_cluster.scope | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidates | first_source_candidate.ranking_id | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidates[].asset_id | first_source_candidate.asset_id | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidates[].rank | first_source_candidate.rank | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidates[].probability | first_source_candidate.probability | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidates[].published_at | first_source_candidate.published_at | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidates[].evidence_ids | first_source_candidate.evidence_refs | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidates[].counter_evidence_ids | first_source_candidate.evidence_refs | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/status | first_source_ranking.status | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/coverage_note | first_source_ranking.coverage_note | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/model_version | first_source_ranking.model_version | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/ranking_id | first_source_ranking.ranking_id | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/task_id | first_source_ranking.task_id | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/run_version | first_source_ranking.run_version | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/result_version | first_source_ranking.result_version | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/policy_version | first_source_ranking.policy_version | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |
| response/candidate_count | first_source_ranking.candidate_count | 按ranking_id关联单份快照；证据数组从evidence_refs对应键投影，需应用校验引用。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-ORIGIN-002-E、TC-ORIGIN-002-N、TC-ORIGIN-003-E、TC-ORIGIN-003-N、TV-T093-E、TV-T093-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
