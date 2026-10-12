# 业务需求、内部处理与结果读取对应

36条业务需求的主来源、任务/模型/表/测试引用保持原值。入口与结果读取是独立标记的候选设计，未更改主追踪、接口结构、任务状态或批准；源操作未直接绑定不等于内部计算需求丢失。机器记录见[requirement-processing-map.json](requirement-processing-map.json)。

对七条无直接operation_ids的需求，已补内部任务/Schema与候选读取说明；节点调度、持久化对象身份和完整结果返回仍需语义设计/实现，不将本文作为完整DAG或新增可调用路径。

## FR-INGEST-001 登记来源与授权用途

源位置：`docs/00-project/requirement-traceability.yaml/requirements/0`。

主追踪已有API：createSource, listSources, createImport, getImport；任务：T021, T028, T029。

来源任务卡：[T021.md](../../tasks/backend/T021.md)、[T028.md](../../tasks/backend/T028.md)、[T029.md](../../tasks/backend/T029.md)。

候选流程入口：createSource, createImport；候选结果读取：listSources, getImport。

来源/分片/导入按已声明契约；上传VALIDATING终态缺查询，不能把受理当有效资产。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：import_item, import_job, source_registry；计划测试：TC-INGEST-001-N, TC-INGEST-001-E。

关联接口缺口：IF-G01, IF-G08, IF-G10；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-INGEST-002 分片上传及断点续传

源位置：`docs/00-project/requirement-traceability.yaml/requirements/1`。

主追踪已有API：createUpload, putUploadPart, completeUpload；任务：T022, T023, T024。

来源任务卡：[T022.md](../../tasks/backend/T022.md)、[T023.md](../../tasks/backend/T023.md)、[T024.md](../../tasks/backend/T024.md)。

候选流程入口：createUpload, putUploadPart, completeUpload；候选结果读取：当前尚无完整读取契约。

来源/分片/导入按已声明契约；上传VALIDATING终态缺查询，不能把受理当有效资产。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：media_asset, source_registry, upload_part, upload_session；计划测试：TC-INGEST-002-N, TC-INGEST-002-E。

关联接口缺口：IF-G01, IF-G08, IF-G10；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-INGEST-003 合并哈希和格式安全校验

源位置：`docs/00-project/requirement-traceability.yaml/requirements/2`。

主追踪已有API：completeUpload, downloadAsset；任务：T024, T025, T026, T027。

来源任务卡：[T024.md](../../tasks/backend/T024.md)、[T025.md](../../tasks/backend/T025.md)、[T026.md](../../tasks/backend/T026.md)、[T027.md](../../tasks/backend/T027.md)。

候选流程入口：completeUpload；候选结果读取：getAsset, downloadAsset。

来源/分片/导入按已声明契约；上传VALIDATING终态缺查询，不能把受理当有效资产。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：audit_event, media_asset, object_version, upload_part, upload_session；计划测试：TC-INGEST-003-N, TC-INGEST-003-E。

关联接口缺口：IF-G01, IF-G08, IF-G10；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RESOURCE-001 管理原始及派生媒体

源位置：`docs/00-project/requirement-traceability.yaml/requirements/3`。

主追踪已有API：listAssets, getAsset, downloadAsset；任务：T019, T020, T025, T030。

来源任务卡：[T019.md](../../tasks/backend/T019.md)、[T020.md](../../tasks/backend/T020.md)、[T025.md](../../tasks/backend/T025.md)、[T030.md](../../tasks/frontend/T030.md)。

候选流程入口：listAssets, searchImage；候选结果读取：getAsset, downloadAsset, getSearchJob。

资源读取和检索候选分开，来源用途与授权生命周期逐次核验。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：asset_lineage, audit_event, media_asset, object_version；计划测试：TC-RESOURCE-001-N, TC-RESOURCE-001-E。

关联接口缺口：IF-G08, IF-G09；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RESOURCE-002 区分完全重复与近重复候选

源位置：`docs/00-project/requirement-traceability.yaml/requirements/4`。

主追踪已有API：completeUpload, searchImage, getSearchJob；任务：T027, T079, T082, T090。

来源任务卡：[T027.md](../../tasks/backend/T027.md)、[T079.md](../../tasks/algorithm/T079.md)、[T082.md](../../tasks/algorithm/T082.md)、[T090.md](../../tasks/backend/T090.md)。

候选流程入口：listAssets, searchImage；候选结果读取：getAsset, downloadAsset, getSearchJob。

资源读取和检索候选分开，来源用途与授权生命周期逐次核验。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M23 origin.content_cluster | verified_relations / cluster_relations | [请求](../../schemas/model/M23.request.schema.json)、[响应](../../schemas/model/M23.response.schema.json) |

候选表：index_registry, media_asset, search_job, source_match, upload_part, upload_session；计划测试：TC-RESOURCE-002-N, TC-RESOURCE-002-E。

关联接口缺口：IF-G08, IF-G09；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RESOURCE-003 按权限及生命周期检索资产

源位置：`docs/00-project/requirement-traceability.yaml/requirements/5`。

主追踪已有API：getCurrentUser, createSource, listSources, listAssets, getAsset, downloadAsset；任务：T015, T021, T025, T030。

来源任务卡：[T015.md](../../tasks/platform/T015.md)、[T021.md](../../tasks/backend/T021.md)、[T025.md](../../tasks/backend/T025.md)、[T030.md](../../tasks/frontend/T030.md)。

候选流程入口：listAssets, searchImage；候选结果读取：getAsset, downloadAsset, getSearchJob。

资源读取和检索候选分开，来源用途与授权生命周期逐次核验。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：asset_lineage, audit_event, case_membership, media_asset, object_version, source_registry, user_roles, users；计划测试：TC-RESOURCE-003-N, TC-RESOURCE-003-E。

关联接口缺口：IF-G08, IF-G09；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-MEDIA-001 解析媒体元数据并保留原件

源位置：`docs/00-project/requirement-traceability.yaml/requirements/6`。

主追踪已有API：未直接绑定；任务：T041, T042, T043。

来源任务卡：[T041.md](../../tasks/backend/T041.md)、[T042.md](../../tasks/backend/T042.md)、[T043.md](../../tasks/backend/T043.md)。

候选流程入口：createTask；候选结果读取：getAsset, getTimeline。

T041/T042/T043承接原件探测和标准化副本。主来源无模型/直接API绑定；候选入口为统一分析任务，getAsset仅含mime/尺寸/时长等摘要，完整元数据/派生血缘的返回与对象关联尚需确定。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：无；计划测试：TC-MEDIA-001-N, TC-MEDIA-001-E。

关联接口缺口：IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-MEDIA-002 提取关键帧与音轨字幕

源位置：`docs/00-project/requirement-traceability.yaml/requirements/7`。

主追踪已有API：未直接绑定；任务：T044, T045, T046, T047。

来源任务卡：[T044.md](../../tasks/backend/T044.md)、[T045.md](../../tasks/backend/T045.md)、[T046.md](../../tasks/backend/T046.md)、[T047.md](../../tasks/backend/T047.md)。

候选流程入口：createTask；候选结果读取：getAsset, getTimeline。

T044—T047为镜头/帧/音轨字幕处理，主来源M33为音频指纹，不能把指纹Schema当全部视频解码契约。getTimeline有frame/shot/audio/subtitle等候选投影，派生资产和映射身份待设计/实现。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M33 media.audio_fingerprint | audio / fingerprint | [请求](../../schemas/model/M33.request.schema.json)、[响应](../../schemas/model/M33.response.schema.json) |

候选表：无；计划测试：TC-MEDIA-002-N, TC-MEDIA-002-E。

关联接口缺口：IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-MEDIA-003 OCR和ASR对齐统一时间轴

源位置：`docs/00-project/requirement-traceability.yaml/requirements/8`。

主追踪已有API：getTimeline；任务：T048, T049, T050, T066。

来源任务卡：[T048.md](../../tasks/backend/T048.md)、[T049.md](../../tasks/backend/T049.md)、[T050.md](../../tasks/backend/T050.md)、[T066.md](../../tasks/algorithm/T066.md)。

候选流程入口：createTask；候选结果读取：getAsset, getTimeline。

候选DAG触发媒体处理；getAsset只含部分媒体摘要，getTimeline为帧/镜头/OCR/ASR等投影。完整元数据、派生对象/时轴关联仍需设计。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M31 media.ocr | decoded_original / text_segments | [请求](../../schemas/model/M31.request.schema.json)、[响应](../../schemas/model/M31.response.schema.json) |
| M32 media.asr | audio / text_segments | [请求](../../schemas/model/M32.request.schema.json)、[响应](../../schemas/model/M32.response.schema.json) |

候选表：keyframe, media_asset, shot, text_segment；计划测试：TC-MEDIA-003-N, TC-MEDIA-003-E。

关联接口缺口：IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RISK-001 多标签和敏感目标定位

源位置：`docs/00-project/requirement-traceability.yaml/requirements/9`。

主追踪已有API：createPolicy, listPolicies；任务：T061, T062, T063, T130, T131, T132, T133。

来源任务卡：[T061.md](../../tasks/algorithm/T061.md)、[T062.md](../../tasks/algorithm/T062.md)、[T063.md](../../tasks/algorithm/T063.md)、[T130.md](../../tasks/algorithm/T130.md)、[T131.md](../../tasks/algorithm/T131.md)、[T132.md](../../tasks/algorithm/T132.md)、[T133.md](../../tasks/algorithm/T133.md)。

候选流程入口：createTask；候选结果读取：getRiskFindings, getTaskEvidence。

候选内部能力与融合后由风险/证据读取；标签/阈值/模态缺失与时间映射需语义核验。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M01 risk.image_classification | decoded_original / classification | [请求](../../schemas/model/M01.request.schema.json)、[响应](../../schemas/model/M01.response.schema.json) |
| M02 risk.object_detection | decoded_original / detections | [请求](../../schemas/model/M02.request.schema.json)、[响应](../../schemas/model/M02.response.schema.json) |
| M03 risk.small_object | decoded_original / detections | [请求](../../schemas/model/M03.request.schema.json)、[响应](../../schemas/model/M03.response.schema.json) |

候选表：policy_registry；计划测试：TC-RISK-001-N, TC-RISK-001-E。

关联接口缺口：IF-G09, IF-G11, IF-G12, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RISK-002 对齐文字语音视觉及动作

源位置：`docs/00-project/requirement-traceability.yaml/requirements/10`。

主追踪已有API：未直接绑定；任务：T064, T065, T066, T067, T134, T135, T136, T137, T138, T139。

来源任务卡：[T064.md](../../tasks/algorithm/T064.md)、[T065.md](../../tasks/algorithm/T065.md)、[T066.md](../../tasks/algorithm/T066.md)、[T067.md](../../tasks/algorithm/T067.md)、[T134.md](../../tasks/data/T134.md)、[T135.md](../../tasks/algorithm/T135.md)、[T136.md](../../tasks/algorithm/T136.md)、[T137.md](../../tasks/algorithm/T137.md)、[T138.md](../../tasks/data/T138.md)、[T139.md](../../tasks/algorithm/T139.md)。

候选流程入口：createTask；候选结果读取：getRiskFindings, getTaskEvidence。

M04—M07是行为/事件/音频/一致性能力来源，内部对齐和融合按任务处理；候选风险/证据读取须包含映射和缺失模态，不能自行新增HTTP或把能力存在当完整融合。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M04 risk.video_action | analysis_copy / temporal_events | [请求](../../schemas/model/M04.request.schema.json)、[响应](../../schemas/model/M04.response.schema.json) |
| M05 risk.temporal_event | analysis_copy / temporal_events | [请求](../../schemas/model/M05.request.schema.json)、[响应](../../schemas/model/M05.response.schema.json) |
| M06 risk.audio_event | audio / temporal_events | [请求](../../schemas/model/M06.request.schema.json)、[响应](../../schemas/model/M06.response.schema.json) |
| M07 risk.consistency | multimodal / relations | [请求](../../schemas/model/M07.request.schema.json)、[响应](../../schemas/model/M07.response.schema.json) |

候选表：无；计划测试：TC-RISK-002-N, TC-RISK-002-E。

关联接口缺口：IF-G09, IF-G11, IF-G12, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RISK-003 输出风险证据与模态冲突

源位置：`docs/00-project/requirement-traceability.yaml/requirements/11`。

主追踪已有API：getRiskFindings, createPolicy, listPolicies；任务：T068, T069, T070, T140, T141。

来源任务卡：[T068.md](../../tasks/algorithm/T068.md)、[T069.md](../../tasks/algorithm/T069.md)、[T070.md](../../tasks/frontend/T070.md)、[T140.md](../../tasks/algorithm/T140.md)、[T141.md](../../tasks/algorithm/T141.md)。

候选流程入口：createTask；候选结果读取：getRiskFindings, getTaskEvidence。

候选内部能力与融合后由风险/证据读取；标签/阈值/模态缺失与时间映射需语义核验。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M08 risk.fusion | multimodal / classification | [请求](../../schemas/model/M08.request.schema.json)、[响应](../../schemas/model/M08.response.schema.json) |
| M25 model.calibration | scores / calibration | [请求](../../schemas/model/M25.request.schema.json)、[响应](../../schemas/model/M25.response.schema.json) |

候选表：finding_evidence, policy_registry, risk_finding；计划测试：TC-RISK-003-N, TC-RISK-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G12, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-FORENSIC-001 定位图片疑似篡改区域

源位置：`docs/00-project/requirement-traceability.yaml/requirements/12`。

主追踪已有API：未直接绑定；任务：T071, T072, T073, T142, T143, T144, T145, T146。

来源任务卡：[T071.md](../../tasks/algorithm/T071.md)、[T072.md](../../tasks/algorithm/T072.md)、[T073.md](../../tasks/algorithm/T073.md)、[T142.md](../../tasks/data/T142.md)、[T143.md](../../tasks/algorithm/T143.md)、[T144.md](../../tasks/algorithm/T144.md)、[T145.md](../../tasks/algorithm/T145.md)、[T146.md](../../tasks/algorithm/T146.md)。

候选流程入口：createTask；候选结果读取：getForensics, getTaskEvidence。

M09/M10承接疑似区域/类型，getForensics可作候选结果投影，掩码对象、原件坐标及可靠性需完整语义/业务验证。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M09 forensic.image_localization | original_bytes / masks | [请求](../../schemas/model/M09.request.schema.json)、[响应](../../schemas/model/M09.response.schema.json) |
| M10 forensic.tamper_type | original_bytes / classification | [请求](../../schemas/model/M10.request.schema.json)、[响应](../../schemas/model/M10.response.schema.json) |

候选表：无；计划测试：TC-FORENSIC-001-N, TC-FORENSIC-001-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-FORENSIC-002 分析视频时空及音画异常

源位置：`docs/00-project/requirement-traceability.yaml/requirements/13`。

主追踪已有API：未直接绑定；任务：T074, T075, T076, T147, T148, T149, T150, T151, T152。

来源任务卡：[T074.md](../../tasks/algorithm/T074.md)、[T075.md](../../tasks/algorithm/T075.md)、[T076.md](../../tasks/algorithm/T076.md)、[T147.md](../../tasks/data/T147.md)、[T148.md](../../tasks/algorithm/T148.md)、[T149.md](../../tasks/algorithm/T149.md)、[T150.md](../../tasks/algorithm/T150.md)、[T151.md](../../tasks/algorithm/T151.md)、[T152.md](../../tasks/algorithm/T152.md)。

候选流程入口：createTask；候选结果读取：getForensics, getTaskEvidence。

M11—M14承接视频时间/空间/深伪/音画能力，候选结果读取仍需源时间轴、轨迹/模态/证据关联，不能把静态Schema当全视频链路。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M11 forensic.video_temporal | original_bytes / temporal_events | [请求](../../schemas/model/M11.request.schema.json)、[响应](../../schemas/model/M11.response.schema.json) |
| M12 forensic.video_spatial | decoded_original / masks | [请求](../../schemas/model/M12.request.schema.json)、[响应](../../schemas/model/M12.response.schema.json) |
| M13 forensic.deepfake | face_track / classification | [请求](../../schemas/model/M13.request.schema.json)、[响应](../../schemas/model/M13.response.schema.json) |
| M14 forensic.avsync | audio_face / temporal_events | [请求](../../schemas/model/M14.request.schema.json)、[响应](../../schemas/model/M14.response.schema.json) |

候选表：无；计划测试：TC-FORENSIC-002-N, TC-FORENSIC-002-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-FORENSIC-003 输出可靠性与证据不足

源位置：`docs/00-project/requirement-traceability.yaml/requirements/14`。

主追踪已有API：getForensics；任务：T077, T078, T153。

来源任务卡：[T077.md](../../tasks/algorithm/T077.md)、[T078.md](../../tasks/frontend/T078.md)、[T153.md](../../tasks/algorithm/T153.md)。

候选流程入口：createTask；候选结果读取：getForensics, getTaskEvidence。

取证计算可由内部能力执行，掩码/轨迹/音画映射与版本需校验；读取候选不等于法定结论。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M25 model.calibration | scores / calibration | [请求](../../schemas/model/M25.request.schema.json)、[响应](../../schemas/model/M25.response.schema.json) |

候选表：finding_evidence, tamper_finding；计划测试：TC-FORENSIC-003-N, TC-FORENSIC-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-IMGRET-001 整图局部及关键帧多路召回

源位置：`docs/00-project/requirement-traceability.yaml/requirements/15`。

主追踪已有API：searchImage, searchImageRegion, getSearchJob, getIndex, switchIndex；任务：T079, T080, T081, T082, T085, T154, T155。

来源任务卡：[T079.md](../../tasks/algorithm/T079.md)、[T080.md](../../tasks/algorithm/T080.md)、[T081.md](../../tasks/algorithm/T081.md)、[T082.md](../../tasks/algorithm/T082.md)、[T085.md](../../tasks/algorithm/T085.md)、[T154.md](../../tasks/data/T154.md)、[T155.md](../../tasks/algorithm/T155.md)。

候选流程入口：searchImage, searchImageRegion；候选结果读取：getSearchJob。

异步检索返回search_id；候选、几何验证、同源关系分别核验，不能用微型向量PoC代替完整查询。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M15 retrieval.image_embedding | analysis_copy / embedding | [请求](../../schemas/model/M15.request.schema.json)、[响应](../../schemas/model/M15.response.schema.json) |
| M19 retrieval.frame_embedding | analysis_copy / embedding | [请求](../../schemas/model/M19.request.schema.json)、[响应](../../schemas/model/M19.response.schema.json) |

候选表：audit_event, index_registry, media_asset, search_job, source_match；计划测试：TC-IMGRET-001-N, TC-IMGRET-001-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-IMGRET-002 进行局部几何验证

源位置：`docs/00-project/requirement-traceability.yaml/requirements/16`。

主追踪已有API：searchImage；任务：T083, T084。

来源任务卡：[T083.md](../../tasks/algorithm/T083.md)、[T084.md](../../tasks/algorithm/T084.md)。

候选流程入口：searchImage, searchImageRegion；候选结果读取：getSearchJob。

异步检索返回search_id；候选、几何验证、同源关系分别核验，不能用微型向量PoC代替完整查询。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M16 retrieval.local_features | decoded_original / local_features | [请求](../../schemas/model/M16.request.schema.json)、[响应](../../schemas/model/M16.response.schema.json) |
| M17 retrieval.local_match | features / local_matches | [请求](../../schemas/model/M17.request.schema.json)、[响应](../../schemas/model/M17.response.schema.json) |
| M18 retrieval.geometry | features / geometry | [请求](../../schemas/model/M18.request.schema.json)、[响应](../../schemas/model/M18.response.schema.json) |

候选表：index_registry, media_asset, source_match；计划测试：TC-IMGRET-002-N, TC-IMGRET-002-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-IMGRET-003 区分相似候选与高可信同源

源位置：`docs/00-project/requirement-traceability.yaml/requirements/17`。

主追踪已有API：searchImage, searchImageRegion, getSearchJob, getIndex, switchIndex；任务：T082, T084, T085, T156, T157。

来源任务卡：[T082.md](../../tasks/algorithm/T082.md)、[T084.md](../../tasks/algorithm/T084.md)、[T085.md](../../tasks/algorithm/T085.md)、[T156.md](../../tasks/algorithm/T156.md)、[T157.md](../../tasks/algorithm/T157.md)。

候选流程入口：searchImage, searchImageRegion；候选结果读取：getSearchJob。

异步检索返回search_id；候选、几何验证、同源关系分别核验，不能用微型向量PoC代替完整查询。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M18 retrieval.geometry | features / geometry | [请求](../../schemas/model/M18.request.schema.json)、[响应](../../schemas/model/M18.response.schema.json) |

候选表：audit_event, index_registry, media_asset, search_job, source_match；计划测试：TC-IMGRET-003-N, TC-IMGRET-003-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-VIDTRACE-001 按关键帧召回候选来源

源位置：`docs/00-project/requirement-traceability.yaml/requirements/18`。

主追踪已有API：getIndex, switchIndex；任务：T080, T081, T086, T158, T159。

来源任务卡：[T080.md](../../tasks/algorithm/T080.md)、[T081.md](../../tasks/algorithm/T081.md)、[T086.md](../../tasks/algorithm/T086.md)、[T158.md](../../tasks/data/T158.md)、[T159.md](../../tasks/algorithm/T159.md)。

候选流程入口：searchVideo；候选结果读取：getSearchJob。

候选召回/时序对齐/多源定位在内部处理，查询与源半开区间、未知段及结果身份仍需全链路定义。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M15 retrieval.image_embedding | analysis_copy / embedding | [请求](../../schemas/model/M15.request.schema.json)、[响应](../../schemas/model/M15.response.schema.json) |
| M19 retrieval.frame_embedding | analysis_copy / embedding | [请求](../../schemas/model/M19.request.schema.json)、[响应](../../schemas/model/M19.response.schema.json) |
| M33 media.audio_fingerprint | audio / fingerprint | [请求](../../schemas/model/M33.request.schema.json)、[响应](../../schemas/model/M33.response.schema.json) |

候选表：audit_event, index_registry；计划测试：TC-VIDTRACE-001-N, TC-VIDTRACE-001-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-VIDTRACE-002 时序对齐定位来源区间

源位置：`docs/00-project/requirement-traceability.yaml/requirements/19`。

主追踪已有API：未直接绑定；任务：T087, T088, T160, T161, T163。

来源任务卡：[T087.md](../../tasks/algorithm/T087.md)、[T088.md](../../tasks/algorithm/T088.md)、[T160.md](../../tasks/algorithm/T160.md)、[T161.md](../../tasks/algorithm/T161.md)、[T163.md](../../tasks/algorithm/T163.md)。

候选流程入口：searchVideo；候选结果读取：getSearchJob。

M20/M21/M25承接时序定位和校准，searchVideo/getSearchJob为候选外部链路；查询区间与源区间、速度/倒放/未知段语义和历史结果选择尚需核验。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M20 retrieval.temporal_alignment | features / source_mapping | [请求](../../schemas/model/M20.request.schema.json)、[响应](../../schemas/model/M20.response.schema.json) |
| M21 retrieval.segment_localizer | features / source_mapping | [请求](../../schemas/model/M21.request.schema.json)、[响应](../../schemas/model/M21.response.schema.json) |
| M25 model.calibration | scores / calibration | [请求](../../schemas/model/M25.request.schema.json)、[响应](../../schemas/model/M25.response.schema.json) |

候选表：无；计划测试：TC-VIDTRACE-002-N, TC-VIDTRACE-002-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-VIDTRACE-003 多源拼接逐段映射

源位置：`docs/00-project/requirement-traceability.yaml/requirements/20`。

主追踪已有API：searchVideo, getSearchJob；任务：T089, T162。

来源任务卡：[T089.md](../../tasks/algorithm/T089.md)、[T162.md](../../tasks/algorithm/T162.md)。

候选流程入口：searchVideo；候选结果读取：getSearchJob。

候选召回/时序对齐/多源定位在内部处理，查询与源半开区间、未知段及结果身份仍需全链路定义。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M22 retrieval.source_boundary | features / source_mapping | [请求](../../schemas/model/M22.request.schema.json)、[响应](../../schemas/model/M22.response.schema.json) |

候选表：index_registry, search_job, source_match；计划测试：TC-VIDTRACE-003-N, TC-VIDTRACE-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-ORIGIN-001 按高可信边形成内容簇

源位置：`docs/00-project/requirement-traceability.yaml/requirements/21`。

主追踪已有API：未直接绑定；任务：T090, T164。

来源任务卡：[T090.md](../../tasks/backend/T090.md)、[T164.md](../../tasks/data/T164.md)。

候选流程入口：createTask；候选结果读取：getFirstSource。

M23和T090/T164承接高可信整内容聚类，候选统一任务调度。getFirstSource只返回排序快照；cluster_id/簇成员与任务结果身份的持久化/读取尚需设计，不能将片段关系闭包自动合并整簇。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M23 origin.content_cluster | verified_relations / cluster_relations | [请求](../../schemas/model/M23.request.schema.json)、[响应](../../schemas/model/M23.response.schema.json) |

候选表：无；计划测试：TC-ORIGIN-001-N, TC-ORIGIN-001-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-ORIGIN-002 内容簇内排序Top-3

源位置：`docs/00-project/requirement-traceability.yaml/requirements/22`。

主追踪已有API：getFirstSource；任务：T091, T092, T093, T165。

来源任务卡：[T091.md](../../tasks/backend/T091.md)、[T092.md](../../tasks/backend/T092.md)、[T093.md](../../tasks/backend/T093.md)、[T165.md](../../tasks/algorithm/T165.md)。

候选流程入口：createTask；候选结果读取：getFirstSource。

高可信聚类→排序是候选DAG；已有查询返回ranking快照，cluster_id从任务到持久化/用户读取的关联仍需明确，不能把排序API当全部聚类结果接口。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M24 origin.first_source_rank | cluster_features / ranked_candidates | [请求](../../schemas/model/M24.request.schema.json)、[响应](../../schemas/model/M24.response.schema.json) |

候选表：cluster_member, content_cluster, first_source_candidate, first_source_ranking；计划测试：TC-ORIGIN-002-N, TC-ORIGIN-002-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-ORIGIN-003 展示支持反对及覆盖不确定性

源位置：`docs/00-project/requirement-traceability.yaml/requirements/23`。

主追踪已有API：getFirstSource；任务：T091, T092, T093。

来源任务卡：[T091.md](../../tasks/backend/T091.md)、[T092.md](../../tasks/backend/T092.md)、[T093.md](../../tasks/backend/T093.md)。

候选流程入口：createTask；候选结果读取：getFirstSource。

高可信聚类→排序是候选DAG；已有查询返回ranking快照，cluster_id从任务到持久化/用户读取的关联仍需明确，不能把排序API当全部聚类结果接口。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M24 origin.first_source_rank | cluster_features / ranked_candidates | [请求](../../schemas/model/M24.request.schema.json)、[响应](../../schemas/model/M24.response.schema.json) |

候选表：cluster_member, content_cluster, first_source_candidate, first_source_ranking；计划测试：TC-ORIGIN-003-N, TC-ORIGIN-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-PROPAGATION-001 管理显式及推断传播关系

源位置：`docs/00-project/requirement-traceability.yaml/requirements/24`。

主追踪已有API：getPropagation, decidePropagationEdge；任务：T094, T095, T096。

来源任务卡：[T094.md](../../tasks/backend/T094.md)、[T095.md](../../tasks/backend/T095.md)、[T096.md](../../tasks/backend/T096.md)。

候选流程入口：createTask, decidePropagationEdge；候选结果读取：getPropagation。

图写入/推断与人工决定分别处理，完整对象版本/查询规模/内部任务入口尚需实施验证。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M26 propagation.path | graph / graph | [请求](../../schemas/model/M26.request.schema.json)、[响应](../../schemas/model/M26.response.schema.json) |
| M27 propagation.inferred_edge | graph / graph | [请求](../../schemas/model/M27.request.schema.json)、[响应](../../schemas/model/M27.response.schema.json) |

候选表：propagation_edge, propagation_node, review_record；计划测试：TC-PROPAGATION-001-N, TC-PROPAGATION-001-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-PROPAGATION-002 展示时间线和版本差异

源位置：`docs/00-project/requirement-traceability.yaml/requirements/25`。

主追踪已有API：getPropagation, decidePropagationEdge；任务：T095, T097。

来源任务卡：[T095.md](../../tasks/backend/T095.md)、[T097.md](../../tasks/frontend/T097.md)。

候选流程入口：createTask, decidePropagationEdge；候选结果读取：getPropagation。

图写入/推断与人工决定分别处理，完整对象版本/查询规模/内部任务入口尚需实施验证。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M26 propagation.path | graph / graph | [请求](../../schemas/model/M26.request.schema.json)、[响应](../../schemas/model/M26.response.schema.json) |

候选表：propagation_edge, propagation_node, review_record；计划测试：TC-PROPAGATION-002-N, TC-PROPAGATION-002-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-PROPAGATION-003 人工确认或驳回推断边

源位置：`docs/00-project/requirement-traceability.yaml/requirements/26`。

主追踪已有API：getPropagation, decidePropagationEdge, createReview, requestApproval, decideApproval, createPolicy；任务：T096, T097, T102。

来源任务卡：[T096.md](../../tasks/backend/T096.md)、[T097.md](../../tasks/frontend/T097.md)、[T102.md](../../tasks/backend/T102.md)。

候选流程入口：createTask, decidePropagationEdge；候选结果读取：getPropagation。

图写入/推断与人工决定分别处理，完整对象版本/查询规模/内部任务入口尚需实施验证。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M26 propagation.path | graph / graph | [请求](../../schemas/model/M26.request.schema.json)、[响应](../../schemas/model/M26.response.schema.json) |
| M27 propagation.inferred_edge | graph / graph | [请求](../../schemas/model/M27.request.schema.json)、[响应](../../schemas/model/M27.response.schema.json) |

候选表：approval_decision, approval_request, audit_event, policy_registry, propagation_edge, propagation_node, review_evidence, review_record；计划测试：TC-PROPAGATION-003-N, TC-PROPAGATION-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-CLAIM-001 抽取结构化主张

源位置：`docs/00-project/requirement-traceability.yaml/requirements/27`。

主追踪已有API：extractClaims；任务：T098, T166, T167。

来源任务卡：[T098.md](../../tasks/algorithm/T098.md)、[T166.md](../../tasks/data/T166.md)、[T167.md](../../tasks/algorithm/T167.md)。

候选流程入口：extractClaims, verifyClaim, createReportDraft；候选结果读取：getReport。

现有主张提取/关系响应可作为读取投影，摘要异步生成用报告状态查询；引用支持不能只看JSON/ID存在。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M28 claim.extract | text / claims | [请求](../../schemas/model/M28.request.schema.json)、[响应](../../schemas/model/M28.response.schema.json) |

候选表：claim, text_segment；计划测试：TC-CLAIM-001-N, TC-CLAIM-001-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-CLAIM-002 检索白名单证据并判断关系

源位置：`docs/00-project/requirement-traceability.yaml/requirements/28`。

主追踪已有API：verifyClaim；任务：T099, T168。

来源任务卡：[T099.md](../../tasks/algorithm/T099.md)、[T168.md](../../tasks/algorithm/T168.md)。

候选流程入口：extractClaims, verifyClaim, createReportDraft；候选结果读取：getReport。

现有主张提取/关系响应可作为读取投影，摘要异步生成用报告状态查询；引用支持不能只看JSON/ID存在。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M29 claim.evidence_relation | claims_evidence / relations | [请求](../../schemas/model/M29.request.schema.json)、[响应](../../schemas/model/M29.response.schema.json) |

候选表：claim, claim_evidence_relation；计划测试：TC-CLAIM-002-N, TC-CLAIM-002-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-CLAIM-003 生成带证据引用摘要

源位置：`docs/00-project/requirement-traceability.yaml/requirements/29`。

主追踪已有API：createReportDraft；任务：T106, T169。

来源任务卡：[T106.md](../../tasks/backend/T106.md)、[T169.md](../../tasks/algorithm/T169.md)。

候选流程入口：extractClaims, verifyClaim, createReportDraft；候选结果读取：getReport。

现有主张提取/关系响应可作为读取投影，摘要异步生成用报告状态查询；引用支持不能只看JSON/ID存在。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M30 claim.grounding | claims_evidence / grounding | [请求](../../schemas/model/M30.request.schema.json)、[响应](../../schemas/model/M30.response.schema.json) |

候选表：report, report_evidence；计划测试：TC-CLAIM-003-N, TC-CLAIM-003-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-REVIEW-001 人工复核会审及退回重算

源位置：`docs/00-project/requirement-traceability.yaml/requirements/30`。

主追踪已有API：getTaskEvidence, decidePropagationEdge, createReview, requestApproval, decideApproval, requestFeedback, createPolicy；任务：T100, T101, T102, T103, T108。

来源任务卡：[T100.md](../../tasks/backend/T100.md)、[T101.md](../../tasks/backend/T101.md)、[T102.md](../../tasks/backend/T102.md)、[T103.md](../../tasks/frontend/T103.md)、[T108.md](../../tasks/backend/T108.md)。

候选流程入口：createReview, requestApproval, sealEvidence, createReport, requestFeedback；候选结果读取：getTaskEvidence, getReport, downloadReport。

结果证据读取已有候选；复核/审批/反馈工作台和状态读取仍缺，不能用报告查询替代。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：approval_decision, approval_request, audit_event, evidence_item, feedback_request, policy_registry, propagation_edge, review_evidence, review_record, task_evidence；计划测试：TC-REVIEW-001-N, TC-REVIEW-001-E。

关联接口缺口：IF-G02, IF-G03, IF-G04, IF-G09, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-REVIEW-002 固化证据并保留版本

源位置：`docs/00-project/requirement-traceability.yaml/requirements/31`。

主追踪已有API：sealEvidence；任务：T104, T105。

来源任务卡：[T104.md](../../tasks/backend/T104.md)、[T105.md](../../tasks/backend/T105.md)。

候选流程入口：createReview, requestApproval, sealEvidence, createReport, requestFeedback；候选结果读取：getTaskEvidence, getReport, downloadReport。

结果证据读取已有候选；复核/审批/反馈工作台和状态读取仍缺，不能用报告查询替代。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：audit_event, evidence_package, object_version, package_item；计划测试：TC-REVIEW-002-N, TC-REVIEW-002-E。

关联接口缺口：IF-G02, IF-G03, IF-G04, IF-G09, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-REVIEW-003 生成报告及受控导出

源位置：`docs/00-project/requirement-traceability.yaml/requirements/32`。

主追踪已有API：createReportDraft, createReport, getReport, downloadReport；任务：T106, T107。

来源任务卡：[T106.md](../../tasks/backend/T106.md)、[T107.md](../../tasks/backend/T107.md)。

候选流程入口：createReview, requestApproval, sealEvidence, createReport, requestFeedback；候选结果读取：getTaskEvidence, getReport, downloadReport。

结果证据读取已有候选；复核/审批/反馈工作台和状态读取仍缺，不能用报告查询替代。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M30 claim.grounding | claims_evidence / grounding | [请求](../../schemas/model/M30.request.schema.json)、[响应](../../schemas/model/M30.response.schema.json) |

候选表：approval_request, audit_event, report, report_evidence；计划测试：TC-REVIEW-003-N, TC-REVIEW-003-E。

关联接口缺口：IF-G02, IF-G03, IF-G04, IF-G09, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-OPS-001 管理角色模型标签阈值规则

源位置：`docs/00-project/requirement-traceability.yaml/requirements/33`。

主追踪已有API：devLogin, getCurrentUser, requestApproval, decideApproval, issueOperationToken, registerModel, listModels, getModelHealth, rolloutModel, recordEvaluation, listEvaluations, listAuditEvents, exportAudit, createPolicy, listPolicies；任务：T011, T012, T013, T014, T016, T017, T018, T051, T052, T058, T060, T061。

来源任务卡：[T011.md](../../tasks/platform/T011.md)、[T012.md](../../tasks/platform/T012.md)、[T013.md](../../tasks/platform/T013.md)、[T014.md](../../tasks/platform/T014.md)、[T016.md](../../tasks/platform/T016.md)、[T017.md](../../tasks/platform/T017.md)、[T018.md](../../tasks/frontend/T018.md)、[T051.md](../../tasks/algorithm/T051.md)、[T052.md](../../tasks/algorithm/T052.md)、[T058.md](../../tasks/algorithm/T058.md)、[T060.md](../../tasks/frontend/T060.md)、[T061.md](../../tasks/algorithm/T061.md)。

候选流程入口：registerModel, rolloutModel, createPolicy, exportAudit；候选结果读取：listModels, getModelHealth, getIndex, listPolicies, listAuditEvents。

组织级配置/模型与案件数据范围分开；健康检查不等于发布操作完成，审计导出查询缺口开放，训练/备份可为离线运维任务。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：approval_decision, approval_request, audit_event, audit_export, case_membership, index_registry, model_evaluation, model_registry, model_release, operation_token, policy_registry, user_roles, users；计划测试：TC-OPS-001-N, TC-OPS-001-E。

关联接口缺口：IF-G05, IF-G06, IF-G07, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-OPS-002 监控任务GPU队列存储及索引

源位置：`docs/00-project/requirement-traceability.yaml/requirements/34`。

主追踪已有API：listTasks, getTask, cancelTask, rerunTask, getModelHealth；任务：T035, T040, T055, T056, T059, T117, T118, T119, T120。

来源任务卡：[T035.md](../../tasks/backend/T035.md)、[T040.md](../../tasks/frontend/T040.md)、[T055.md](../../tasks/algorithm/T055.md)、[T056.md](../../tasks/algorithm/T056.md)、[T059.md](../../tasks/algorithm/T059.md)、[T117.md](../../tasks/testing/T117.md)、[T118.md](../../tasks/testing/T118.md)、[T119.md](../../tasks/testing/T119.md)、[T120.md](../../tasks/backend/T120.md)。

候选流程入口：registerModel, rolloutModel, createPolicy, exportAudit；候选结果读取：listModels, getModelHealth, getIndex, listPolicies, listAuditEvents。

组织级配置/模型与案件数据范围分开；健康检查不等于发布操作完成，审计导出查询缺口开放，训练/备份可为离线运维任务。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：analysis_task, model_registry, outbox_event, task_event, task_node_run, task_run；计划测试：TC-OPS-002-N, TC-OPS-002-E。

关联接口缺口：IF-G05, IF-G06, IF-G07, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-OPS-003 灰度回滚及备份恢复

源位置：`docs/00-project/requirement-traceability.yaml/requirements/35`。

主追踪已有API：listModels, getModelHealth, rolloutModel；任务：T057, T060, T121, T122, T123, T124, T170。

来源任务卡：[T057.md](../../tasks/algorithm/T057.md)、[T060.md](../../tasks/frontend/T060.md)、[T121.md](../../tasks/deployment/T121.md)、[T122.md](../../tasks/testing/T122.md)、[T123.md](../../tasks/testing/T123.md)、[T124.md](../../tasks/testing/T124.md)、[T170.md](../../tasks/algorithm/T170.md)。

候选流程入口：registerModel, rolloutModel, createPolicy, exportAudit；候选结果读取：listModels, getModelHealth, getIndex, listPolicies, listAuditEvents。

组织级配置/模型与案件数据范围分开；健康检查不等于发布操作完成，审计导出查询缺口开放，训练/备份可为离线运维任务。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M34 model.compression | model_bundle / release_bundle | [请求](../../schemas/model/M34.request.schema.json)、[响应](../../schemas/model/M34.response.schema.json) |

候选表：approval_request, index_registry, model_registry, model_release；计划测试：TC-OPS-003-N, TC-OPS-003-E。

关联接口缺口：IF-G05, IF-G06, IF-G07, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

