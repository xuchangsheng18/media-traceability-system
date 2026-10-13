# 受理报告草稿生成：createReportDraft

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `556c92bd7b22602c83bd71aa3ea5cc11cdefb48926a18c03428b293860e2f7ba`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/reports/drafts`；operationId=`createReportDraft`；源指针=`/paths/~1reports~1drafts/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

受理报告草稿生成；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`report.draft`。

核验功能权限及单位/案件/对象/用途；UUID、客户端case_id或已有URL不替代当前服务端授权。

来源任务：[T106 实现证据约束核查摘要](../../../tasks/backend/T106.md)。

关联需求：FR-CLAIM-003、FR-REVIEW-003、ER-T106；关联候选表：report、report_evidence。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/ReportDraft`；字段与完整约束见[数据结构](../data-structures.md#reportdraft)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：report.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；report_evidence.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：report.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：report.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：report.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| template_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：report.template_version：生成报告使用的模板版本，确保历史报告可以重现。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：report_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "case_id": "2f2a6464-f05f-595c-be55-d8ae323e595a",
  "task_id": "74197f6f-5fd4-55b6-a4f1-f04c909fac2f",
  "run_version": 1,
  "result_version": 1,
  "template_version": "synthetic-v1",
  "evidence_ids": [
    "f2893cbd-3458-5562-bc09-2cf6f5a98a85"
  ]
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 202 | 契约成功响应；异步受理不代表结果完成 | application/json: Report | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Report`，详细字段见[数据结构](../data-structures.md#report)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| report_id | 必须 | string; format="uuid" | 候选字段来源：report.report_id：主键，由应用提供UUID；不视为访问凭证；report_evidence.report_id：报告版本记录标识。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；report.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；report_evidence.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：report.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.run_version：分析对象绑定运行版本；report.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.result_version：分析对象绑定结果版本；report.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；report.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；report.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version；report_evidence.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["DRAFT", "GENERATING", "READY", "FAILED", "SUPERSEDED"] | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；report.state：报告生成与下载状态的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证；report.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| object_ref | 必须 | anyOf(ObjectRef; null) | 候选字段来源：object_version.object_id：主键，由应用提供UUID；不视为访问凭证；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.version_id：对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：evidence_item.evidence_id：主键，由应用提供UUID；不视为访问凭证；report_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：approval_request.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；report.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；report_evidence.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "report_id": "b41e8ff6-25ff-59fd-967f-26724328e31f",
  "case_id": "d771f5dd-73d3-5f6c-b1bc-0eb497ce1160",
  "task_id": "5433b977-9dab-5570-9aaf-949591d902a0",
  "run_version": 1,
  "result_version": 1,
  "version": 1,
  "state": "DRAFT",
  "approval_id": "0998e387-dfb4-5995-a0a4-9499207a1787",
  "object_ref": {
    "object_id": "c5bbed22-eaa7-5b11-8a8a-38bed901e1c1",
    "version_id": "synthetic-v1",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "evidence_ids": [
    "edd41e42-384e-5d34-96f2-634ad14ef036"
  ],
  "created_at": "2030-01-01T00:00:00Z"
}
```

202返回报告状态；GET /api/v1/reports/{id}查询，草稿不是批准报告或执法结论。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/case_id | report.case_id, report_evidence.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/task_id | report.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/run_version | report.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/result_version | report.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/template_version | report.template_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/evidence_ids | report_evidence.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/report_id | report.report_id, report_evidence.report_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/case_id | report.case_id, report_evidence.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/task_id | report.task_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/run_version | report.run_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/result_version | report.result_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | report.row_version, report.version, report_evidence.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/state | report.state | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/approval_id | report.approval_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref | object_version.object_id, object_version.sha256, object_version.version_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref.object_id | report.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref.version_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/object_ref.sha256 | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/evidence_ids | report_evidence.evidence_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/created_at | report.created_at, report_evidence.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-CLAIM-003-E、TC-CLAIM-003-N、TC-REVIEW-003-E、TC-REVIEW-003-N、TV-T106-E、TV-T106-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
