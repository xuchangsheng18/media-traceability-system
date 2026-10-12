# 内部模型调用详细说明

自动派生，禁止独立修改结构；权威源 `docs/03-api/inference-openapi.yaml`，SHA-256 `5f8d735bedd4eb5b1aa7e182d83c6c714815ad53781aebf3eb9ce109e61bce3b`。契约未冻结，文档存在不代表接口已实现。

调用入口 `POST /internal/v1/inference/{capability}`；业务调用方是已授权任务的worker/模型网关，使用独立serviceAuth。该内部口不能作为前端直接接口，不能将调用令牌/任意URL装入消息。路径capability须与请求能力一致，按对应独立Schema校验，再核验案件/用途、对象版本/摘要、期限及运行身份。

OpenAPI响应码：`200, 401, 403, 503`。源oneOf各有34个请求/响应分支，模型能力的编辑源仍是schemas/model；目前只实测M15的合成CPU子范围。其他33能力未因Schema存在而运行通过。

## M01 图片多标签风险分类

能力：`risk.image_classification`；路径：`POST /internal/v1/inference/risk.image_classification`；输入路径：`decoded_original`；输出种类：`classification`。

关联任务：T062, T113, T130, T131；数据集：D01；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M01.request.schema.json](../../schemas/model/M01.request.schema.json)；SHA-256：`5e0c46c8437e662016ce516f0c2a1bb31da2b41c24b8d903b5e8595be23b4a2c`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.image_classification" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="decoded_original" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M01.response.schema.json](../../schemas/model/M01.response.schema.json)；SHA-256：`eb14e0e01f75c7f81c44ad3e002fa229da656c4f6bada1687826ebcfb8054a6b`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.image_classification" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="classification" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M02 敏感目标检测

能力：`risk.object_detection`；路径：`POST /internal/v1/inference/risk.object_detection`；输入路径：`decoded_original`；输出种类：`detections`。

关联任务：T063, T132；数据集：D02；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M02.request.schema.json](../../schemas/model/M02.request.schema.json)；SHA-256：`8f54f991ae47b70d5354f3bbd8fd875b57c093aff14985f5a6786452c1f10b5f`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.object_detection" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="decoded_original" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M02.response.schema.json](../../schemas/model/M02.response.schema.json)；SHA-256：`8d7355453b72e1ab6e59c96434872d5f147da3fd798288af027fc02eeb06a83b`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.object_detection" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="detections" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M03 小目标检测

能力：`risk.small_object`；路径：`POST /internal/v1/inference/risk.small_object`；输入路径：`decoded_original`；输出种类：`detections`。

关联任务：T133；数据集：D02；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M03.request.schema.json](../../schemas/model/M03.request.schema.json)；SHA-256：`d43995493ae87eb64e92e928dea0b61d3255aab598a6e4c843d57cedbdda17db`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.small_object" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="decoded_original" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M03.response.schema.json](../../schemas/model/M03.response.schema.json)；SHA-256：`0cee1382efacf2a1bcff8e9b9d5b7309b3e39694b0b720b5c3009434b3739b4c`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.small_object" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="detections" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M04 视频行为识别

能力：`risk.video_action`；路径：`POST /internal/v1/inference/risk.video_action`；输入路径：`analysis_copy`；输出种类：`temporal_events`。

关联任务：T064, T135；数据集：D03；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M04.request.schema.json](../../schemas/model/M04.request.schema.json)；SHA-256：`a1e1b17099dc06eb8368a40d33e051dfab663b3de5d7164a0da40aebd5de5dd4`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.video_action" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="analysis_copy" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M04.response.schema.json](../../schemas/model/M04.response.schema.json)；SHA-256：`1a61254088a92506716927fea66b224923c97dcd954b5e309a3b5bbdaa23719d`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.video_action" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="temporal_events" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M05 视频事件时间定位

能力：`risk.temporal_event`；路径：`POST /internal/v1/inference/risk.temporal_event`；输入路径：`analysis_copy`；输出种类：`temporal_events`。

关联任务：T136；数据集：D03；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M05.request.schema.json](../../schemas/model/M05.request.schema.json)；SHA-256：`72d8905d4b1e4b6141a4dbfbcc16163de4be2435eca5171cd00bca95a42d2553`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.temporal_event" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="analysis_copy" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M05.response.schema.json](../../schemas/model/M05.response.schema.json)；SHA-256：`ba6a0aaaa225c5d959def6183cc2b9b74447f23e308ebf6eff531e7ad242e2e8`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.temporal_event" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="temporal_events" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M06 音频事件识别

能力：`risk.audio_event`；路径：`POST /internal/v1/inference/risk.audio_event`；输入路径：`audio`；输出种类：`temporal_events`。

关联任务：T065, T137；数据集：D04；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M06.request.schema.json](../../schemas/model/M06.request.schema.json)；SHA-256：`f2f7398b4e4b10a899688c155b0f5f500c229a66c4ed45de563b5295ec1b17cb`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.audio_event" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="audio" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M06.response.schema.json](../../schemas/model/M06.response.schema.json)；SHA-256：`e4466e2b8228cf691c6fb97174e132e9d39d1c6cdca6d77a7d3485f5a8cc40ce`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.audio_event" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="temporal_events" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M07 跨模态矛盾检测

能力：`risk.consistency`；路径：`POST /internal/v1/inference/risk.consistency`；输入路径：`multimodal`；输出种类：`relations`。

关联任务：T067, T138, T139；数据集：D05；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M07.request.schema.json](../../schemas/model/M07.request.schema.json)；SHA-256：`332ac665a3fb6ecef423deced0b39c8c0d7ee7db282c0d18117edd58bd92c7c2`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.consistency" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="multimodal" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M07.response.schema.json](../../schemas/model/M07.response.schema.json)；SHA-256：`8d47afd241df29fe9968a6470454aab6645fe3e5ccb3336ca83625e557176369`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.consistency" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="relations" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M08 多模态风险融合

能力：`risk.fusion`；路径：`POST /internal/v1/inference/risk.fusion`；输入路径：`multimodal`；输出种类：`classification`。

关联任务：T068, T140；数据集：D01, D02, D03, D04, D05；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M08.request.schema.json](../../schemas/model/M08.request.schema.json)；SHA-256：`a1f694cdbdd42ac78edee5a137f75d2ddbfbfd0fee151ae38772b25feb5e9b38`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.fusion" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="multimodal" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M08.response.schema.json](../../schemas/model/M08.response.schema.json)；SHA-256：`9a960fdd6380c7b76f25d163014402fd07c44d9c1193cc2300508785d7488374`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="risk.fusion" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="classification" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M09 图片篡改检测定位

能力：`forensic.image_localization`；路径：`POST /internal/v1/inference/forensic.image_localization`；输入路径：`original_bytes`；输出种类：`masks`。

关联任务：T072, T142, T143, T144, T145；数据集：D06；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M09.request.schema.json](../../schemas/model/M09.request.schema.json)；SHA-256：`f08a4b64f31f3e94cd1e48f249550ffe0526758b706bcf244f6b17ccc485b4a0`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.image_localization" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="original_bytes" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M09.response.schema.json](../../schemas/model/M09.response.schema.json)；SHA-256：`e307119c883ac51300f4b0c308af43b95d48825c06c3541994880e8969019567`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.image_localization" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="masks" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M10 图片篡改类型分类

能力：`forensic.tamper_type`；路径：`POST /internal/v1/inference/forensic.tamper_type`；输入路径：`original_bytes`；输出种类：`classification`。

关联任务：T073, T146；数据集：D06；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M10.request.schema.json](../../schemas/model/M10.request.schema.json)；SHA-256：`604e7703b7de68d22e977a462fee25ced990d2f52ffcc224716754b5758878fe`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.tamper_type" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="original_bytes" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M10.response.schema.json](../../schemas/model/M10.response.schema.json)；SHA-256：`09ecc9a1f2a2520480463006fe4b5c4a457f2dea6ae56e0361564657dbadfc41`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.tamper_type" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="classification" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M11 视频时间篡改检测

能力：`forensic.video_temporal`；路径：`POST /internal/v1/inference/forensic.video_temporal`；输入路径：`original_bytes`；输出种类：`temporal_events`。

关联任务：T074, T147, T148；数据集：D07；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M11.request.schema.json](../../schemas/model/M11.request.schema.json)；SHA-256：`38a137aaff2b37447c7e86acbc4050904805648d974056076a832084dcf8e2f1`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.video_temporal" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="original_bytes" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M11.response.schema.json](../../schemas/model/M11.response.schema.json)；SHA-256：`377b4232d5932b680ee598b1aca0664aaa4be47a298c6043eb7db24c6889b4a7`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.video_temporal" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="temporal_events" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M12 视频空间篡改

能力：`forensic.video_spatial`；路径：`POST /internal/v1/inference/forensic.video_spatial`；输入路径：`decoded_original`；输出种类：`masks`。

关联任务：T075, T149；数据集：D07；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M12.request.schema.json](../../schemas/model/M12.request.schema.json)；SHA-256：`fc42712453a04fb3aa67c151ca700e5003c62f59e21df5279a5662a96f319aed`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.video_spatial" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="decoded_original" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M12.response.schema.json](../../schemas/model/M12.response.schema.json)；SHA-256：`a7c46cb6414375530f15641075f4d18a96fbd90f75bfbab5fa1a5e7b7e7a8007`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.video_spatial" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="masks" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M13 人脸深度伪造

能力：`forensic.deepfake`；路径：`POST /internal/v1/inference/forensic.deepfake`；输入路径：`face_track`；输出种类：`classification`。

关联任务：T076, T150；数据集：D08；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M13.request.schema.json](../../schemas/model/M13.request.schema.json)；SHA-256：`5dcbf588f723f8277a16f5c7e15b75c5bcec1c782fc975511f04e64f55832e91`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.deepfake" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="face_track" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M13.response.schema.json](../../schemas/model/M13.response.schema.json)；SHA-256：`c1c4d168c880fe1f06a068d3f14a78545b468fb71c58182a889a83dbdb0093e9`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.deepfake" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="classification" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M14 音画同步

能力：`forensic.avsync`；路径：`POST /internal/v1/inference/forensic.avsync`；输入路径：`audio_face`；输出种类：`temporal_events`。

关联任务：T076, T151；数据集：D08；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M14.request.schema.json](../../schemas/model/M14.request.schema.json)；SHA-256：`382402b148fdee5f37e57f5fb96fbbab1c8fed335e165e0c8c22faefe3a89255`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.avsync" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="audio_face" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M14.response.schema.json](../../schemas/model/M14.response.schema.json)；SHA-256：`dad9dd6ecfa49a45dac1570793dcc89c83eb0ac9a66b0440c299b5a2acb462c3`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="forensic.avsync" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="temporal_events" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M15 图片复制检测向量

能力：`retrieval.image_embedding`；路径：`POST /internal/v1/inference/retrieval.image_embedding`；输入路径：`analysis_copy`；输出种类：`embedding`。

关联任务：T080, T154, T155；数据集：D09, D15；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M15.request.schema.json](../../schemas/model/M15.request.schema.json)；SHA-256：`b6ff27909ba2ceae33ccfb8dced6110a6960574870163fb5a5d449279f5b1a04`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.image_embedding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="analysis_copy" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M15.response.schema.json](../../schemas/model/M15.response.schema.json)；SHA-256：`451f39aeb437ee7aec9d5ab96a778e2fdb653f4ae6749b6786c42ff9ee906d6e`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.image_embedding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="embedding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M16 局部特征提取

能力：`retrieval.local_features`；路径：`POST /internal/v1/inference/retrieval.local_features`；输入路径：`decoded_original`；输出种类：`local_features`。

关联任务：T083；数据集：D09；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M16.request.schema.json](../../schemas/model/M16.request.schema.json)；SHA-256：`e62346b0e461ceadb9f3fbd1b2de70673f534614692f90975027eb10ceaf3231`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.local_features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="decoded_original" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M16.response.schema.json](../../schemas/model/M16.response.schema.json)；SHA-256：`e543297889bc2104fd483a9f4cb2246fa713538e727ab638540a541d9b12f26a`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.local_features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="local_features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M17 局部特征匹配

能力：`retrieval.local_match`；路径：`POST /internal/v1/inference/retrieval.local_match`；输入路径：`features`；输出种类：`local_matches`。

关联任务：T083；数据集：D09；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M17.request.schema.json](../../schemas/model/M17.request.schema.json)；SHA-256：`258ea6c04c4851a93c5f8e54eee772a0f904170c7da9cbab875b85fde79c830a`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.local_match" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M17.response.schema.json](../../schemas/model/M17.response.schema.json)；SHA-256：`12cb5b771e0ae99913a925525aa3d4a15074bc9fa36d3d6efd645f787bb2c00b`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.local_match" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="local_matches" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M18 几何验证

能力：`retrieval.geometry`；路径：`POST /internal/v1/inference/retrieval.geometry`；输入路径：`features`；输出种类：`geometry`。

关联任务：T084；数据集：D09；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M18.request.schema.json](../../schemas/model/M18.request.schema.json)；SHA-256：`23e297885bc372439eef98474a46d0a34bdd044c9311cb368142fb822698682c`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.geometry" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M18.response.schema.json](../../schemas/model/M18.response.schema.json)；SHA-256：`8b3cb98646268d511bb3421d70ed9368034c3bec156c960d89e26d6274d51cda`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.geometry" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="geometry" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M19 视频关键帧复制向量

能力：`retrieval.frame_embedding`；路径：`POST /internal/v1/inference/retrieval.frame_embedding`；输入路径：`analysis_copy`；输出种类：`embedding`。

关联任务：T080, T158, T159；数据集：D10；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M19.request.schema.json](../../schemas/model/M19.request.schema.json)；SHA-256：`ebb1ffe9801b7c2a3dea96f0df227e1e1b07fe98b38c77bc56159af09ab3b556`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.frame_embedding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="analysis_copy" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M19.response.schema.json](../../schemas/model/M19.response.schema.json)；SHA-256：`29ee7960b06c23ef8fa13eae41ae3e20be8ee6a41f5348d996c534389eed8b08`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.frame_embedding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="embedding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M20 视频序列对齐

能力：`retrieval.temporal_alignment`；路径：`POST /internal/v1/inference/retrieval.temporal_alignment`；输入路径：`features`；输出种类：`source_mapping`。

关联任务：T087, T088, T160；数据集：D10；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M20.request.schema.json](../../schemas/model/M20.request.schema.json)；SHA-256：`2138dbe6f27ebc4cd5d2151b605efe916d5ddcb9081e69df7f212f5c04b78f7a`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.temporal_alignment" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M20.response.schema.json](../../schemas/model/M20.response.schema.json)；SHA-256：`e6589811fa8fead2143120608da0cba651a1eea0c133804e9a606c8b92c244a5`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.temporal_alignment" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="source_mapping" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M21 学习型片段定位

能力：`retrieval.segment_localizer`；路径：`POST /internal/v1/inference/retrieval.segment_localizer`；输入路径：`features`；输出种类：`source_mapping`。

关联任务：T161；数据集：D10；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M21.request.schema.json](../../schemas/model/M21.request.schema.json)；SHA-256：`446fb004ec37df342e775841a56f96100bd7372ab2c0d6d5324f4d590d2b21df`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.segment_localizer" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M21.response.schema.json](../../schemas/model/M21.response.schema.json)；SHA-256：`66efc59d6f4eefe125c3826f6e3f35ac7c1cfe183dbc7da2b9d06f76a65ae1ea`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.segment_localizer" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="source_mapping" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M22 多源拼接边界

能力：`retrieval.source_boundary`；路径：`POST /internal/v1/inference/retrieval.source_boundary`；输入路径：`features`；输出种类：`source_mapping`。

关联任务：T089, T162；数据集：D11；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M22.request.schema.json](../../schemas/model/M22.request.schema.json)；SHA-256：`42370fe693b339c1ae60998531e0166f5f95eebb4335c4f85a8d5e8573f10a99`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.source_boundary" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M22.response.schema.json](../../schemas/model/M22.response.schema.json)；SHA-256：`a4f47676a9c1c4b5b42c5a50ccc878c8a3daa8f3dadbedb747d3489abb9c8909`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="retrieval.source_boundary" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="source_mapping" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M23 同源内容聚类

能力：`origin.content_cluster`；路径：`POST /internal/v1/inference/origin.content_cluster`；输入路径：`verified_relations`；输出种类：`cluster_relations`。

关联任务：T090, T164；数据集：D09, D10, D11；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M23.request.schema.json](../../schemas/model/M23.request.schema.json)；SHA-256：`d954cc49fd22131a8634b10e963bc316355edda8ee300445ff579eb67b456e9b`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="origin.content_cluster" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="verified_relations" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M23.response.schema.json](../../schemas/model/M23.response.schema.json)；SHA-256：`779b2809a04814c4c785fa25240baa89c7f2361831640e337bd520e200a8e3f1`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="origin.content_cluster" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="cluster_relations" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M24 首发候选排序

能力：`origin.first_source_rank`；路径：`POST /internal/v1/inference/origin.first_source_rank`；输入路径：`cluster_features`；输出种类：`ranked_candidates`。

关联任务：T092, T165；数据集：D12；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M24.request.schema.json](../../schemas/model/M24.request.schema.json)；SHA-256：`9559019daa61e5228584497902ff5397278e29e77dc283be49a0ce0c77a0c764`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="origin.first_source_rank" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="cluster_features" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M24.response.schema.json](../../schemas/model/M24.response.schema.json)；SHA-256：`fbc5bf151e576d2e0ce0294fcf8f00f89ab00210daa502860753d96752b7715f`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="origin.first_source_rank" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="ranked_candidates" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M25 概率校准

能力：`model.calibration`；路径：`POST /internal/v1/inference/model.calibration`；输入路径：`scores`；输出种类：`calibration`。

关联任务：T141, T153, T163；数据集：D01, D06, D10, D12；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M25.request.schema.json](../../schemas/model/M25.request.schema.json)；SHA-256：`315f4f01cf668671d0e05d1f6496e7f67de17fd9e2b9b826d94ac2229887b508`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="model.calibration" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="scores" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M25.response.schema.json](../../schemas/model/M25.response.schema.json)；SHA-256：`8e5d251b24e4da32f9625ea37a8f33921e56af4f769b0b5c3304a48927ff8ddc`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="model.calibration" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="calibration" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M26 传播路径分析

能力：`propagation.path`；路径：`POST /internal/v1/inference/propagation.path`；输入路径：`graph`；输出种类：`graph`。

关联任务：T094, T095, T097；数据集：D12；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M26.request.schema.json](../../schemas/model/M26.request.schema.json)；SHA-256：`0fd995974d223b2872952b95449b36bf5416c30b144da7f79be28fd10c5865fa`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="propagation.path" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="graph" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M26.response.schema.json](../../schemas/model/M26.response.schema.json)；SHA-256：`118ce756f9467587a484b90f4ed9a399fd5e9b842935df7ba37480166ff0ba55`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="propagation.path" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="graph" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M27 隐式传播关系

能力：`propagation.inferred_edge`；路径：`POST /internal/v1/inference/propagation.inferred_edge`；输入路径：`graph`；输出种类：`graph`。

关联任务：T096；数据集：D12；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M27.request.schema.json](../../schemas/model/M27.request.schema.json)；SHA-256：`9485deaa26ccbced2b803cbb8c6dcb2f0d80656378c6a42481b81b21a134533e`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="propagation.inferred_edge" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="graph" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M27.response.schema.json](../../schemas/model/M27.response.schema.json)；SHA-256：`101bb5a5cc58b4117921631afe54485f3a20a9ccb745cf7f6763554867071844`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="propagation.inferred_edge" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="graph" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M28 结构化主张抽取

能力：`claim.extract`；路径：`POST /internal/v1/inference/claim.extract`；输入路径：`text`；输出种类：`claims`。

关联任务：T098, T166, T167；数据集：D13；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M28.request.schema.json](../../schemas/model/M28.request.schema.json)；SHA-256：`2667776eeb7cef19b6301b12dc6e1a0792bca3a6f1cb63dee89986ac592e5d69`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="claim.extract" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="text" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M28.response.schema.json](../../schemas/model/M28.response.schema.json)；SHA-256：`6f9e308aa5a3de545d71332ecdb781500e8121c275eec8950f7b8835e0ab6e1d`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="claim.extract" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="claims" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M29 证据关系判断

能力：`claim.evidence_relation`；路径：`POST /internal/v1/inference/claim.evidence_relation`；输入路径：`claims_evidence`；输出种类：`relations`。

关联任务：T099, T168；数据集：D14；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M29.request.schema.json](../../schemas/model/M29.request.schema.json)；SHA-256：`ba51f21659c2060ebe7ee1c607337d837615b7a48f122c329570aac92b5ea94e`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="claim.evidence_relation" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="claims_evidence" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M29.response.schema.json](../../schemas/model/M29.response.schema.json)；SHA-256：`63700d32cc905d60125b275bca38d15b7b8f403d9aa5b156267ea8324a2394cc`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="claim.evidence_relation" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="relations" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M30 无证据生成检测

能力：`claim.grounding`；路径：`POST /internal/v1/inference/claim.grounding`；输入路径：`claims_evidence`；输出种类：`grounding`。

关联任务：T106, T169；数据集：D13, D14；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M30.request.schema.json](../../schemas/model/M30.request.schema.json)；SHA-256：`4c3661daf93b612c75ff41fbbd706e3970f7a1389b2638cede34199a7f573925`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="claim.grounding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="claims_evidence" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M30.response.schema.json](../../schemas/model/M30.response.schema.json)；SHA-256：`d881032e059536b73ec9d006eb62600bbf09d5f0238d588dc93d1fd28e8e3c37`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="claim.grounding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="grounding" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M31 OCR

能力：`media.ocr`；路径：`POST /internal/v1/inference/media.ocr`；输入路径：`decoded_original`；输出种类：`text_segments`。

关联任务：T048；数据集：D01, D05, D13；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M31.request.schema.json](../../schemas/model/M31.request.schema.json)；SHA-256：`8d2bb0a5f4e344527602657d5da7a8f3551e4b37eb12945f67e7bd91932c766c`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="media.ocr" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="decoded_original" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M31.response.schema.json](../../schemas/model/M31.response.schema.json)；SHA-256：`5b22e54b53eabcf7e69a7abf925a6cf9c807ffa94c03be987f090c3cd679dc1d`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="media.ocr" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="text_segments" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M32 ASR

能力：`media.asr`；路径：`POST /internal/v1/inference/media.asr`；输入路径：`audio`；输出种类：`text_segments`。

关联任务：T049；数据集：D03, D04, D05, D13；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M32.request.schema.json](../../schemas/model/M32.request.schema.json)；SHA-256：`5db779f49931dcea86083ed450a4a497cad1797aa17034c2b8e69a0a05102e70`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="media.asr" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="audio" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M32.response.schema.json](../../schemas/model/M32.response.schema.json)；SHA-256：`c95aaa58accf2fe321992fea52fec6c723d4ce2bb7d0286f7860ea0a30d972a9`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="media.asr" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="text_segments" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M33 音频指纹

能力：`media.audio_fingerprint`；路径：`POST /internal/v1/inference/media.audio_fingerprint`；输入路径：`audio`；输出种类：`fingerprint`。

关联任务：T047, T086；数据集：D04, D10；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M33.request.schema.json](../../schemas/model/M33.request.schema.json)；SHA-256：`b62bcf07e623e876d90464f37c0321bfb325514e2c82bcc48520b4aba5f5f704`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="media.audio_fingerprint" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="audio" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M33.response.schema.json](../../schemas/model/M33.response.schema.json)；SHA-256：`e7f9c72c3ddf0629ba864f95b71a050253b13187a5f33184dfe8e008ac8d81fb`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="media.audio_fingerprint" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="fingerprint" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

## M34 模型压缩

能力：`model.compression`；路径：`POST /internal/v1/inference/model.compression`；输入路径：`model_bundle`；输出种类：`release_bundle`。

关联任务：T170；数据集：D01, D06, D09, D10, D13；候选/许可/运行状态：`candidate_pending_review / unverified / not_verified`。

### request字段

结构源：[schemas/model/M34.request.schema.json](../../schemas/model/M34.request.schema.json)；SHA-256：`1abb9fc19653c9f461f6adfa6c047babb60d0de256fe8fe23090c88be5b22508`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="model.compression" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| input_kind | 必须 | const="model_bundle" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| asset_ids | 必须 | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_refs | 必须 | array; minItems=1; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_segment_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| deadline_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

### response字段

结构源：[schemas/model/M34.response.schema.json](../../schemas/model/M34.response.schema.json)；SHA-256：`da5e4dc4e3045af6faf4ba61b3da7cef5c59055042dfbfabb486caee2c44ef5c`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| capability | 必须 | const="model.compression" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| preprocessing_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| output_kind | 必须 | const="release_bundle" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifacts | 必须 | array; minItems=0; items=ObjectRef | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| latency_ms | 必须 | number; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mock | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| payload | 必须 | anyOf(object; additionalProperties=false; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

SUCCEEDED必须满足能力payload及身份绑定；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不能夹带结果，reason与缺失模态须明确。时间/bbox范围、维度/dtype/归一化、证据存在性和授权范围还需业务校验。

研发实现与统一Problem细节见[poc-api.md](poc-api.md)；输出mock=false只说明该次使用真实合成模型，不能说明业务准确率通过。服务协议/期限/路径能力一致等待实施校验见[缺口清单](interface-gap-register.md)。
