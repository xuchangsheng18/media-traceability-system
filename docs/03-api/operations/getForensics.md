# 读取取证候选结果：getForensics

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `bffa82adf57b9ccf1888d5589e7b3d54f03915c7b150bac6dcc627779d4769b4`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/analysis/tasks/{id}/forensics`；operationId=`getForensics`；源指针=`/paths/~1analysis~1tasks~1{id}~1forensics/get`。

实现范围：**DEV_PARTIAL**；独立业务HTTP/真实PostgreSQL/RLS已实现；默认无权威身份提供方返回503，测试提供方仅在fixture注入。。正式55业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

读取取证候选结果；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`task.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T078 开发篡改取证界面](../../../tasks/frontend/T078.md)。

关联需求：FR-FORENSIC-003、ER-T078；关联候选表：tamper_finding、finding_evidence。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| id | path | True | string; format="uuid" |
| X-Request-Id | header | False | string; format="uuid" |
| history | query | False | object; additionalProperties=false |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: Findings | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128; X-Task-Id: string; format="uuid"; X-Run-Version: integer; minimum=1; X-Result-Version: integer; minimum=1 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Findings`，详细字段见[数据结构](../data-structures.md#findings)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| binding | 必须 | VersionBinding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "binding": {
    "task_id": "585bbf8b-9170-5607-ba83-92baec618b0d",
    "run_version": 1,
    "result_version": 1,
    "policy_version": "synthetic-v1"
  },
  "findings": [
    {
      "finding_id": "8bfc2e6e-5fc1-532d-8424-be174048d283",
      "kind": "classification",
      "label": "synthetic-v1",
      "raw_score": 0.5,
      "calibrated_score": 0.5,
      "threshold_version": "synthetic-v1",
      "model_name": "synthetic-v1",
      "model_version": "synthetic-v1",
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
      "mask_ref": {
        "object_id": "5974515a-5213-53bd-b9ee-dc5f189399c2",
        "version_id": "synthetic-v1",
        "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
      },
      "evidence_ids": [
        "6c86eb3f-659f-56b0-b36d-7c7fd2e8da3a"
      ],
      "status": "candidate",
      "mapping_version": "synthetic-v1",
      "track_id": "synthetic-v1",
      "frame_id": "5d29a18e-6ee4-5f78-8fb8-43439fb30129"
    }
  ],
  "missing_modalities": [],
  "warnings": []
}
```

按精确task/run/result及当前权限读取不可变快照，7项HTTP和版本头已实测；尚无实际业务结果生产器，缺失快照404、旧映射未登记503。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/binding | 服务层输入/聚合，不直接生成数据库列 | task/run/result/policy绑定投影 |
| response/binding.task_id | tamper_finding.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/binding.run_version | tamper_finding.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/binding.result_version | tamper_finding.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/binding.policy_version | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].finding_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].kind | tamper_finding.type | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].label | tamper_finding.type | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].raw_score | tamper_finding.score | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].calibrated_score | tamper_finding.calibrated_score | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].threshold_version | tamper_finding.threshold_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].model_name | tamper_finding.model_name | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].model_version | tamper_finding.model_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].time_range | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].time_range.start_ms | tamper_finding.start_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].time_range.end_ms | tamper_finding.end_ms | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].bbox | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].bbox.x | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].bbox.y | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].bbox.width | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].bbox.height | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].mask_ref | tamper_finding.payload | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].mask_ref.object_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].mask_ref.version_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].mask_ref.sha256 | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].evidence_ids | finding_evidence.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].status | tamper_finding.status | 相应对象状态或健康聚合；按Schema与操作区分 |
| response/findings[].mapping_version | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].track_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/findings[].frame_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/missing_modalities | 服务层输入/聚合，不直接生成数据库列 | 任务/能力完成矩阵，不能隐藏缺失 |
| response/warnings | 服务层输入/聚合，不直接生成数据库列 | 非正式告警与限制投影 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-FORENSIC-003-E、TC-FORENSIC-003-N、TV-T078-E、TV-T078-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
