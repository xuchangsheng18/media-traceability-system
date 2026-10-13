# 登记模型候选：registerModel

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `072aa69af85cff9b18212db91b8ac493a9aacc6f1df04ffadb9a7456f1424388`。契约未冻结，文档存在不代表接口已实现。

`POST /api/v1/models`；operationId=`registerModel`；源指针=`/paths/~1models/post`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式53业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

登记模型候选；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`model.manage`。

组织级模型/配置/索引管理；系统管理员不自动取得案件原件，依赖数据仍核验用途。

来源任务：[T052 实现模型注册表](../../../tasks/algorithm/T052.md)。

关联需求：FR-OPS-001、ER-T052、NFR-COMPAT-001；关联候选表：model_registry。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| Idempotency-Key | header | True | string; minLength=1; maxLength=128 |

请求体必须出现：`True`；支持媒体类型：`application/json`。

结构源：`#/components/schemas/ModelCreate`；字段与完整约束见[数据结构](../data-structures.md#modelcreate)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.name：名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| capability | 必须 | string; enum=["risk.image_classification", "risk.object_detection", "risk.small_object", "risk.video_action", "risk.temporal_event", "risk.audio_event", "risk.consistency", "risk.fusion", "forensic.image_localization", "forensic.tamper_type", "forensic.video_temporal", "forensic.video_spatial", "forensic.deepfake", "forensic.avsync", "retrieval.image_embedding", "retrieval.local_features", "retrieval.local_match", "retrieval.geometry", "retrieval.frame_embedding", "retrieval.temporal_alignment", "retrieval.segment_localizer", "retrieval.source_boundary", "origin.content_cluster", "origin.first_source_rank", "model.calibration", "propagation.path", "propagation.inferred_edge", "claim.extract", "claim.evidence_relation", "claim.grounding", "media.ocr", "media.asr", "media.audio_fingerprint", "model.compression"] | 候选字段来源：model_registry.capability：模型或索引提供的能力编码，取值对应内部推理能力契约。来源引用不是写入许可，完整处理按操作核验。 |
| digest | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：model_registry.digest：注册模型权重或模型包的SHA-256，具体制品范围记录于模型卡；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| model_card_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.model_card_ref：模型卡的受控版本引用，说明用途、限制和训练评测信息。来源引用不是写入许可，完整处理按操作核验。 |
| license_record_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.license_record_ref：代码与权重许可核查记录引用，需覆盖本项目预定用途。来源引用不是写入许可，完整处理按操作核验。 |
| backend | 必须 | string; enum=["pytorch", "onnxruntime", "triton", "other_reviewed"] | 候选字段来源：model_registry.backend：实际运行推理后端标识，例如经选型的框架适配器；不是模型名称。来源引用不是写入许可，完整处理按操作核验。 |
| environment_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.environment_ref：可重建运行环境说明或镜像摘要的受控引用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

结构样例（合成占位数据，非运行结果）：

```json
{
  "name": "synthetic-v1",
  "version": "synthetic-v1",
  "capability": "risk.image_classification",
  "digest": "0000000000000000000000000000000000000000000000000000000000000000",
  "dataset_version": "synthetic-v1",
  "model_card_ref": "synthetic-v1",
  "license_record_ref": "synthetic-v1",
  "backend": "pytorch",
  "environment_ref": "synthetic-v1"
}
```

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 201 | 契约成功响应；异步受理不代表结果完成 | application/json: Model | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`Model`，详细字段见[数据结构](../data-structures.md#model)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| model_id | 必须 | string; format="uuid" | 候选字段来源：model_registry.model_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.name：名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| capability | 必须 | string; enum=["risk.image_classification", "risk.object_detection", "risk.small_object", "risk.video_action", "risk.temporal_event", "risk.audio_event", "risk.consistency", "risk.fusion", "forensic.image_localization", "forensic.tamper_type", "forensic.video_temporal", "forensic.video_spatial", "forensic.deepfake", "forensic.avsync", "retrieval.image_embedding", "retrieval.local_features", "retrieval.local_match", "retrieval.geometry", "retrieval.frame_embedding", "retrieval.temporal_alignment", "retrieval.segment_localizer", "retrieval.source_boundary", "origin.content_cluster", "origin.first_source_rank", "model.calibration", "propagation.path", "propagation.inferred_edge", "claim.extract", "claim.evidence_relation", "claim.grounding", "media.ocr", "media.asr", "media.audio_fingerprint", "model.compression"] | 候选字段来源：model_registry.capability：模型或索引提供的能力编码，取值对应内部推理能力契约。来源引用不是写入许可，完整处理按操作核验。 |
| digest | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：model_registry.digest：注册模型权重或模型包的SHA-256，具体制品范围记录于模型卡；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| model_card_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.model_card_ref：模型卡的受控版本引用，说明用途、限制和训练评测信息。来源引用不是写入许可，完整处理按操作核验。 |
| license_record_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.license_record_ref：代码与权重许可核查记录引用，需覆盖本项目预定用途。来源引用不是写入许可，完整处理按操作核验。 |
| backend | 必须 | string; enum=["pytorch", "onnxruntime", "triton", "other_reviewed"] | 候选字段来源：model_registry.backend：实际运行推理后端标识，例如经选型的框架适配器；不是模型名称。来源引用不是写入许可，完整处理按操作核验。 |
| environment_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.environment_ref：可重建运行环境说明或镜像摘要的受控引用。来源引用不是写入许可，完整处理按操作核验。 |
| status | 必须 | string; enum=["REGISTERED", "EVALUATED", "CANDIDATE", "APPROVED", "ACTIVE", "RETIRED"] | 候选字段来源：model_registry.status：模型版本与许可引用的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| row_version | 必须 | integer; minimum=1 | 候选字段来源：model_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "model_id": "56378b68-7c26-5115-9761-25bee53e7c39",
  "name": "synthetic-v1",
  "version": "synthetic-v1",
  "capability": "risk.image_classification",
  "digest": "0000000000000000000000000000000000000000000000000000000000000000",
  "dataset_version": "synthetic-v1",
  "model_card_ref": "synthetic-v1",
  "license_record_ref": "synthetic-v1",
  "backend": "pytorch",
  "environment_ref": "synthetic-v1",
  "status": "REGISTERED",
  "row_version": 1
}
```

201登记候选，许可、评测和发布审批分别核验，不自动成为正式在线业务模型。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| request/name | model_registry.name | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/version | model_registry.row_version, model_registry.version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/capability | model_registry.capability | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/digest | model_registry.digest | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/dataset_version | model_registry.dataset_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/model_card_ref | model_registry.model_card_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/license_record_ref | model_registry.license_record_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/backend | model_registry.backend | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| request/environment_ref | model_registry.environment_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/model_id | model_registry.model_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/name | model_registry.name | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/version | model_registry.row_version, model_registry.version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/capability | model_registry.capability | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/digest | model_registry.digest | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/dataset_version | model_registry.dataset_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/model_card_ref | model_registry.model_card_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/license_record_ref | model_registry.license_record_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/backend | model_registry.backend | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/environment_ref | model_registry.environment_ref | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/status | model_registry.status | 相应对象状态或健康聚合；按Schema与操作区分 |
| response/row_version | model_registry.row_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TV-T002-E、TV-T002-N、TV-T003-E、TV-T003-N、TV-T051-E、TV-T051-N、TV-T052-E、TV-T052-N、TV-T053-E、TV-T053-N、TV-T054-E、TV-T054-N、TV-T081-E、TV-T081-N、TV-T170-E、TV-T170-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
