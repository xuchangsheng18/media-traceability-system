# 登记模型评测记录：recordEvaluation

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/model-evaluations`；operationId=`recordEvaluation`；源指针=`/paths/~1model-evaluations/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

登记模型评测记录；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`model.evaluate`。

组织级模型/配置/索引管理；系统管理员不自动取得案件原件，依赖数据仍核验用途。

来源任务：[T058 实现模型评测记录管理](../../../tasks/algorithm/T058.md)。

关联需求：FR-OPS-001、ER-T058、NFR-AI-001；关联候选表：model_evaluation。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/EvaluationCreate`；字段与完整约束见[数据结构](../data-structures.md#evaluationcreate)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| model_id | 必须 | string; format="uuid" | 候选字段来源：model_evaluation.model_id：模型注册记录标识，引用同单位的model_registry.model_id。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_id：数据集目录的稳定文本编号，例如D01；不是数据库UUID主键。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| protocol_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.protocol_id：评测协议标识，决定指标公式、样本计数、阈值及统计口径。来源引用不是写入许可，完整处理按操作核验。 |
| split | 必须 | string; enum=["validation", "calibration", "holdout"] | 候选字段来源：model_evaluation.split：此次评测使用的划分用途；封存holdout不能用于训练或调参。来源引用不是写入许可，完整处理按操作核验。 |
| sample_count | 必须 | integer; minimum=1 | 候选字段来源：model_evaluation.sample_count：按照评测协议统计的样本数，必须为正；不能混用帧数、素材组数和文件数。来源引用不是写入许可，完整处理按操作核验。 |
| failure_count | 必须 | integer; minimum=0 | 候选字段来源：model_evaluation.failure_count：处理失败样本数，范围0到sample_count，不应从评测分母中隐式删除。来源引用不是写入许可，完整处理按操作核验。 |
| metrics | 必须 | object; additionalProperties=false | 候选字段来源：model_evaluation.metrics：评测协议规定的指标结果对象；需保留失败计数和适用样本口径。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| metrics.macro_f1 | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.iou | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall_at_k | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.ece | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.boundary_mae_ms | 必须（父对象存在时） | anyOf(number; minimum=0; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifact_ref | 必须 | ObjectRef | 候选字段来源：model_evaluation.artifact_ref：评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "model_id": "cd0f72df-dbab-5b0a-9488-02b6d2575e81",
  "dataset_id": "synthetic-v1",
  "dataset_version": "synthetic-v1",
  "protocol_id": "synthetic-v1",
  "split": "validation",
  "sample_count": 1,
  "failure_count": 0,
  "metrics": {
    "macro_f1": 0.5,
    "recall": 0.5,
    "iou": 0.5,
    "recall_at_k": 0.5,
    "ece": 0.5,
    "boundary_mae_ms": 0.5
  },
  "artifact_ref": {
    "object_id": "bf1d8aa1-1d63-52db-818b-0faf318bf467",
    "version_id": "synthetic-v1",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  }
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: Evaluation | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Evaluation`，详细字段见[数据结构](../data-structures.md#evaluation)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| evaluation_id | 必须 | string; format="uuid" | 候选字段来源：model_evaluation.evaluation_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| model_id | 必须 | string; format="uuid" | 候选字段来源：model_evaluation.model_id：模型注册记录标识，引用同单位的model_registry.model_id。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_id：数据集目录的稳定文本编号，例如D01；不是数据库UUID主键。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| protocol_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.protocol_id：评测协议标识，决定指标公式、样本计数、阈值及统计口径。来源引用不是写入许可，完整处理按操作核验。 |
| split | 必须 | string; enum=["validation", "calibration", "holdout"] | 候选字段来源：model_evaluation.split：此次评测使用的划分用途；封存holdout不能用于训练或调参。来源引用不是写入许可，完整处理按操作核验。 |
| sample_count | 必须 | integer; minimum=1 | 候选字段来源：model_evaluation.sample_count：按照评测协议统计的样本数，必须为正；不能混用帧数、素材组数和文件数。来源引用不是写入许可，完整处理按操作核验。 |
| failure_count | 必须 | integer; minimum=0 | 候选字段来源：model_evaluation.failure_count：处理失败样本数，范围0到sample_count，不应从评测分母中隐式删除。来源引用不是写入许可，完整处理按操作核验。 |
| metrics | 必须 | object; additionalProperties=false | 候选字段来源：model_evaluation.metrics：评测协议规定的指标结果对象；需保留失败计数和适用样本口径。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| metrics.macro_f1 | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.iou | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall_at_k | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.ece | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.boundary_mae_ms | 必须（父对象存在时） | anyOf(number; minimum=0; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifact_ref | 必须 | ObjectRef | 候选字段来源：model_evaluation.artifact_ref：评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：model_evaluation.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "evaluation_id": "a3e81c94-e520-5019-b75d-f68c9a967c56",
  "model_id": "c195289f-6ebd-5604-80de-285b806c43a4",
  "dataset_id": "synthetic-v1",
  "dataset_version": "synthetic-v1",
  "protocol_id": "synthetic-v1",
  "split": "validation",
  "sample_count": 1,
  "failure_count": 0,
  "metrics": {
    "macro_f1": 0.5,
    "recall": 0.5,
    "iou": 0.5,
    "recall_at_k": 0.5,
    "ece": 0.5,
    "boundary_mae_ms": 0.5
  },
  "artifact_ref": {
    "object_id": "8a7ec953-a5b6-5ee3-ac43-274e3a66a242",
    "version_id": "synthetic-v1",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "created_at": "2030-01-01T00:00:00Z"
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/model_id | model_evaluation.model_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/dataset_id | model_evaluation.dataset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/dataset_version | model_evaluation.dataset_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/protocol_id | model_evaluation.protocol_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/split | model_evaluation.split | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/sample_count | model_evaluation.sample_count | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/failure_count | model_evaluation.failure_count | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/metrics | model_evaluation.metrics | model_evaluation.metrics JSONB；指标名由固定协议核对 |
| request/metrics.macro_f1 | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/metrics.recall | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/metrics.iou | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/metrics.recall_at_k | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/metrics.ece | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/metrics.boundary_mae_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/artifact_ref | model_evaluation.artifact_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/artifact_ref.object_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/artifact_ref.version_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/artifact_ref.sha256 | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/evaluation_id | model_evaluation.evaluation_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/model_id | model_evaluation.model_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/dataset_id | model_evaluation.dataset_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/dataset_version | model_evaluation.dataset_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/protocol_id | model_evaluation.protocol_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/split | model_evaluation.split | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/sample_count | model_evaluation.sample_count | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/failure_count | model_evaluation.failure_count | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/metrics | model_evaluation.metrics | model_evaluation.metrics JSONB；指标名由固定协议核对 |
| response/metrics.macro_f1 | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/metrics.recall | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/metrics.iou | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/metrics.recall_at_k | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/metrics.ece | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/metrics.boundary_mae_ms | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/artifact_ref | model_evaluation.artifact_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/artifact_ref.object_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/artifact_ref.version_id | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/artifact_ref.sha256 | 服务层输入/聚合，不直接生成数据库列 | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/created_at | model_evaluation.created_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TV-T058-E、TV-T058-N、TV-T113-E、TV-T113-N、TV-T114-E、TV-T114-N、TV-T115-E、TV-T115-N、TV-T116-E、TV-T116-N、TV-T125-E、TV-T125-N、TV-T128-E、TV-T128-N、TV-T141-E、TV-T141-N、TV-T153-E、TV-T153-N、TV-T163-E、TV-T163-N、TV-T165-E、TV-T165-N、TV-T167-E、TV-T167-N、TV-T170-E、TV-T170-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
