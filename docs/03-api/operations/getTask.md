# 读取任务与运行状态：getTask

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `bffa82adf57b9ccf1888d5589e7b3d54f03915c7b150bac6dcc627779d4769b4`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/analysis/tasks/{id}`；operationId=`getTask`；源指针=`/paths/~1analysis~1tasks~1{id}/get`。

实现范围：**DEV_PARTIAL**；独立业务HTTP/真实PostgreSQL/RLS已实现；默认无权威身份提供方返回503，测试提供方仅在fixture注入。。正式55业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

读取任务与运行状态；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`task.read`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T035 实现任务查询和进度接口](../../../tasks/backend/T035.md)、[T040 开发任务监控页面](../../../tasks/frontend/T040.md)。

关联需求：FR-OPS-002、ER-T035、ER-T040、NFR-AVAIL-001；关联候选表：analysis_task、task_node_run。表引用不证明代码已使用或有访问授权。

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
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: Task | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128; X-Task-Id: string; format="uuid"; X-Run-Version: integer; minimum=1; X-Result-Version: integer; minimum=1 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Task`，详细字段见[数据结构](../data-structures.md#task)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.task_id：主键，由应用提供UUID；不视为访问凭证；task_node_run.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；task_node_run.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["CREATED", "QUEUED", "RUNNING", "WAIT_REVIEW", "REVIEWING", "SUCCEEDED", "FAILED", "RETURNED", "CANCEL_REQUESTED", "CANCELLED", "ARCHIVED"] | 候选字段来源：analysis_task.state：分析任务当前投影的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；task_node_run.state：节点尝试与租约的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算；task_node_run.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：analysis_task.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；task_node_run.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| progress | 必须 | number; minimum=0; maximum=1 | 候选字段来源：analysis_task.progress：当前运行版本的进度比例，0到1；不是准确率或任务正式通过率。来源引用不是写入许可，完整处理按操作核验。 |
| nodes | 必须 | array; minItems=0; items=NodeStatus | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 候选字段来源：analysis_task.missing_modalities：输入缺失的模态列表，例如无音轨；空数组表示未登记缺失，不等于全部分析成功。来源引用不是写入许可，完整处理按操作核验。 |
| report_eligibility | 必须 | string; enum=["draft_only", "reviewable", "formal_eligible"] | 候选字段来源：analysis_task.report_eligibility：当前结果允许的报告使用等级；正式报告仍需核验审批和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：analysis_task.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；task_node_run.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "task_id": "654a33d1-be36-5083-86bb-074f16f3ffb2",
  "case_id": "e8edc894-777b-500b-a7e6-02f7b2e16dff",
  "asset_id": "31b80417-7871-5f03-98a7-9f2b81ca0d4f",
  "state": "CREATED",
  "run_version": 1,
  "result_version": 1,
  "policy_version": "synthetic-v1",
  "version": 1,
  "progress": 0.5,
  "nodes": [
    {
      "node_code": "synthetic-v1",
      "state": "PENDING",
      "attempt": 1,
      "reason": "synthetic-v1",
      "required": true
    }
  ],
  "missing_modalities": [],
  "report_eligibility": "draft_only",
  "created_at": "2030-01-01T00:00:00Z"
}
```

按精确task/run/result及当前权限读取不可变快照，7项HTTP和版本头已实测；尚无实际业务结果生产器，缺失快照404、旧映射未登记503。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/task_id | analysis_task.task_id, task_node_run.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/case_id | analysis_task.case_id, task_node_run.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/asset_id | analysis_task.asset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | analysis_task.state, task_node_run.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/run_version | analysis_task.run_version, task_node_run.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result_version | analysis_task.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/policy_version | analysis_task.policy_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | analysis_task.row_version, task_node_run.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/progress | analysis_task.progress | 当前运行节点完成投影，同时存任务当前进度 |
| response/nodes | 服务层输入/聚合，不直接生成数据库列 | task_node_run聚合；按task_id/run_version查询 |
| response/nodes[].node_code | task_node_run.node_code | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/nodes[].state | analysis_task.state, task_node_run.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/nodes[].attempt | task_node_run.attempt | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/nodes[].reason | task_node_run.reason | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/nodes[].required | task_node_run.required | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/missing_modalities | analysis_task.missing_modalities | 任务/能力完成矩阵，不能隐藏缺失 |
| response/report_eligibility | analysis_task.report_eligibility | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/created_at | analysis_task.created_at, task_node_run.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-002-E、TC-OPS-002-N、TV-T031-E、TV-T031-N、TV-T032-E、TV-T032-N、TV-T033-E、TV-T033-N、TV-T034-E、TV-T034-N、TV-T035-E、TV-T035-N、TV-T036-E、TV-T036-N、TV-T037-E、TV-T037-N、TV-T038-E、TV-T038-N、TV-T039-E、TV-T039-N、TV-T040-E、TV-T040-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
