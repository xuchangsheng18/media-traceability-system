# 业务需求、内部处理与结果读取对应

36条业务需求的主来源、任务/模型/表/测试引用保持原值。本轮已逐需求执行技术语义复核并纠正模块默认入口过宽和错误结果读取；正式规则与运行实现仍分别登记。机器记录见[requirement-processing-map.json](requirement-processing-map.json)，逐条结论见[语义复核](requirement-semantic-review.md)。

七条无直接operation_ids的来源需求保持完整；内部处理、结果身份和当前投影的覆盖/缺口逐项写明。本文不代表完整DAG或所有接口已运行。共同规则见[结果身份与投影](../05-workflows/result-identity-and-projection.md)。

## FR-INGEST-001 登记来源与授权用途

源位置：`docs/00-project/requirement-traceability.yaml/requirements/0`。

主追踪已有API：createSource, listSources, createImport, getImport；任务：T021, T028, T029。

来源任务卡：[T021.md](../../tasks/backend/T021.md)、[T028.md](../../tasks/backend/T028.md)、[T029.md](../../tasks/backend/T029.md)。

候选流程入口：createSource, createImport；候选结果读取：listSources, getImport。

登记来源用途后再导入；客户端授权状态不具批准效力，服务端核验当前来源授权。普通单文件上传为关联流程，不替代本条来源登记。

结果身份：Source.source_id / ImportStatus.import_id。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：import_item, import_job, source_registry；计划测试：TC-INGEST-001-N, TC-INGEST-001-E。

关联接口缺口：IF-G08, IF-G10；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-INGEST-002 分片上传及断点续传

源位置：`docs/00-project/requirement-traceability.yaml/requirements/1`。

主追踪已有API：createUpload, putUploadPart, completeUpload；任务：T022, T023, T024。

来源任务卡：[T022.md](../../tasks/backend/T022.md)、[T023.md](../../tasks/backend/T023.md)、[T024.md](../../tasks/backend/T024.md)。

候选流程入口：createUpload, putUploadPart, completeUpload；候选结果读取：当前尚无完整读取契约。

按upload_id与part_no重试；同编号同摘要重复不增计，冲突拒绝。completeUpload返回VALIDATING后缺进度/分片/终态读取，不能以getImport查询上传，也不能提前使用asset_id。

结果身份：UploadSession.upload_id / UploadPart.part_no / UploadResult.upload_id。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：media_asset, source_registry, upload_part, upload_session；计划测试：TC-INGEST-002-N, TC-INGEST-002-E。

关联接口缺口：IF-G01；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-INGEST-003 合并哈希和格式安全校验

源位置：`docs/00-project/requirement-traceability.yaml/requirements/2`。

主追踪已有API：completeUpload, downloadAsset；任务：T024, T025, T026, T027。

来源任务卡：[T024.md](../../tasks/backend/T024.md)、[T025.md](../../tasks/backend/T025.md)、[T026.md](../../tasks/backend/T026.md)、[T027.md](../../tasks/backend/T027.md)。

候选流程入口：completeUpload；候选结果读取：getAsset, downloadAsset。

合并摘要、格式与恶意素材检查在后端处理；VALID且当前授权生效才允许分析。QUARANTINED/REJECTED保留原因；当前UploadResult没有完整拒绝原因和异步终态读取，下载不是校验状态接口。

结果身份：UploadResult.asset_id / Asset.state / ObjectRef.version_id。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：audit_event, media_asset, object_version, upload_part, upload_session；计划测试：TC-INGEST-003-N, TC-INGEST-003-E。

关联接口缺口：IF-G01, IF-G08；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RESOURCE-001 管理原始及派生媒体

源位置：`docs/00-project/requirement-traceability.yaml/requirements/3`。

主追踪已有API：listAssets, getAsset, downloadAsset；任务：T019, T020, T025, T030。

来源任务卡：[T019.md](../../tasks/backend/T019.md)、[T020.md](../../tasks/backend/T020.md)、[T025.md](../../tasks/backend/T025.md)、[T030.md](../../tasks/frontend/T030.md)。

候选流程入口：listAssets, getAsset；候选结果读取：getAsset, downloadAsset。

资源管理只读取原件/副本；已移除上一版不相关searchImage入口。Asset有kind和固定ObjectRef但未返回完整parent_asset_id、lineage及转换参数，不能声称完整血缘已覆盖。

结果身份：Asset.asset_id / kind / object_ref / version。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：asset_lineage, audit_event, media_asset, object_version；计划测试：TC-RESOURCE-001-N, TC-RESOURCE-001-E。

关联接口缺口：IF-G09；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RESOURCE-002 区分完全重复与近重复候选

源位置：`docs/00-project/requirement-traceability.yaml/requirements/4`。

主追踪已有API：completeUpload, searchImage, getSearchJob；任务：T027, T079, T082, T090。

来源任务卡：[T027.md](../../tasks/backend/T027.md)、[T079.md](../../tasks/algorithm/T079.md)、[T082.md](../../tasks/algorithm/T082.md)、[T090.md](../../tasks/backend/T090.md)。

候选流程入口：completeUpload, searchImage；候选结果读取：getSearchJob。

摘要相同仅在有权范围内判完全重复；近重复是检索及几何/时序验证候选。M23只产出关系建议，不允许语义相似或partial_copy自动并整内容簇；两种结果分别返回。

结果身份：UploadResult.duplicate_of / SearchJob.search_id / SourceMatch.relation。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M23 origin.content_cluster | verified_relations / cluster_relations | [请求](../../schemas/model/M23.request.schema.json)、[响应](../../schemas/model/M23.response.schema.json) |

候选表：index_registry, media_asset, search_job, source_match, upload_part, upload_session；计划测试：TC-RESOURCE-002-N, TC-RESOURCE-002-E。

关联接口缺口：IF-G01, IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RESOURCE-003 按权限及生命周期检索资产

源位置：`docs/00-project/requirement-traceability.yaml/requirements/5`。

主追踪已有API：getCurrentUser, createSource, listSources, listAssets, getAsset, downloadAsset；任务：T015, T021, T025, T030。

来源任务卡：[T015.md](../../tasks/platform/T015.md)、[T021.md](../../tasks/backend/T021.md)、[T025.md](../../tasks/backend/T025.md)、[T030.md](../../tasks/frontend/T030.md)。

候选流程入口：getCurrentUser, listAssets, getAsset；候选结果读取：listAssets, getAsset, downloadAsset。

逐次读取及每个Range请求均校验当前单位、案件、用途与到期/撤销；文件哈希或历史批准不是访问权。生命周期过滤和跨案拒绝由访问层执行。

结果身份：Asset.case_id / source_id / object_ref。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：asset_lineage, audit_event, case_membership, media_asset, object_version, source_registry, user_roles, users；计划测试：TC-RESOURCE-003-N, TC-RESOURCE-003-E。

关联接口缺口：IF-G07, IF-G08；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-MEDIA-001 解析媒体元数据并保留原件

源位置：`docs/00-project/requirement-traceability.yaml/requirements/6`。

主追踪已有API：未直接绑定；任务：T041, T042, T043。

来源任务卡：[T041.md](../../tasks/backend/T041.md)、[T042.md](../../tasks/backend/T042.md)、[T043.md](../../tasks/backend/T043.md)。

候选流程入口：createTask；候选结果读取：getAsset。

T041—T043执行ffprobe/标准化副本，属于普通媒体处理而非模型能力。输入原件ObjectRef不可覆盖；完整编码/流/派生参数尚缺对外投影，不能把Asset的mime/宽高时长摘要当全部元数据。

结果身份：Task.task_id / Asset.asset_id / ObjectRef / asset_lineage。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：无；计划测试：TC-MEDIA-001-N, TC-MEDIA-001-E。

关联接口缺口：IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-MEDIA-002 提取关键帧与音轨字幕

源位置：`docs/00-project/requirement-traceability.yaml/requirements/7`。

主追踪已有API：未直接绑定；任务：T044, T045, T046, T047。

来源任务卡：[T044.md](../../tasks/backend/T044.md)、[T045.md](../../tasks/backend/T045.md)、[T046.md](../../tasks/backend/T046.md)、[T047.md](../../tasks/backend/T047.md)。

候选流程入口：createTask；候选结果读取：getTimeline。

T044—T047负责镜头/帧/音轨/字幕和原始PTS映射，M33只覆盖音频指纹。音轨/字幕对象版本和派生资产绑定需补完整契约；Timeline投影不等于全部媒体输出已返回。

结果身份：Timeline.asset_id / mapping_version / TimelineItem。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M33 media.audio_fingerprint | audio / fingerprint | [请求](../../schemas/model/M33.request.schema.json)、[响应](../../schemas/model/M33.response.schema.json) |

候选表：无；计划测试：TC-MEDIA-002-N, TC-MEDIA-002-E。

关联接口缺口：IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-MEDIA-003 OCR和ASR对齐统一时间轴

源位置：`docs/00-project/requirement-traceability.yaml/requirements/8`。

主追踪已有API：getTimeline；任务：T048, T049, T050, T066。

来源任务卡：[T048.md](../../tasks/backend/T048.md)、[T049.md](../../tasks/backend/T049.md)、[T050.md](../../tasks/backend/T050.md)、[T066.md](../../tasks/algorithm/T066.md)。

候选流程入口：createTask；候选结果读取：getTimeline。

OCR=M31、ASR=M32，普通媒体处理先生成输入；OCR框映射原件空间，ASR按原音轨时间。缺失/失败模态需进入任务missing_modalities及对应时间范围，不能以空文本假装识别完成。

结果身份：Timeline.asset_id / mapping_version / text_segment。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M31 media.ocr | decoded_original / text_segments | [请求](../../schemas/model/M31.request.schema.json)、[响应](../../schemas/model/M31.response.schema.json) |
| M32 media.asr | audio / text_segments | [请求](../../schemas/model/M32.request.schema.json)、[响应](../../schemas/model/M32.response.schema.json) |

候选表：keyframe, media_asset, shot, text_segment；计划测试：TC-MEDIA-003-N, TC-MEDIA-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RISK-001 多标签和敏感目标定位

源位置：`docs/00-project/requirement-traceability.yaml/requirements/9`。

主追踪已有API：createPolicy, listPolicies；任务：T061, T062, T063, T130, T131, T132, T133。

来源任务卡：[T061.md](../../tasks/algorithm/T061.md)、[T062.md](../../tasks/algorithm/T062.md)、[T063.md](../../tasks/algorithm/T063.md)、[T130.md](../../tasks/algorithm/T130.md)、[T131.md](../../tasks/algorithm/T131.md)、[T132.md](../../tasks/algorithm/T132.md)、[T133.md](../../tasks/algorithm/T133.md)。

候选流程入口：createTask；候选结果读取：getRiskFindings, getTaskEvidence。

createPolicy/listPolicies属于配置前置，已从结果入口中分离。M01/M02/M03输出标签/目标候选；应用融合绑定标签、模型、阈值及结果版本。框/类别投影覆盖逐字段核验，不能用策略列表读取风险结果。

结果身份：Findings.binding / Finding / Evidence。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

M04—M07分别处理动作、事件、音频、跨模态关系；融合节点须按原时间区间对齐并保存冲突和缺失范围。跨模态矛盾不是违法或法律结论；一般Finding未完整表达全部融合payload，保留投影差异。

结果身份：Findings.binding / missing_modalities / evidence_refs。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M04 risk.video_action | analysis_copy / temporal_events | [请求](../../schemas/model/M04.request.schema.json)、[响应](../../schemas/model/M04.response.schema.json) |
| M05 risk.temporal_event | analysis_copy / temporal_events | [请求](../../schemas/model/M05.request.schema.json)、[响应](../../schemas/model/M05.response.schema.json) |
| M06 risk.audio_event | audio / temporal_events | [请求](../../schemas/model/M06.request.schema.json)、[响应](../../schemas/model/M06.response.schema.json) |
| M07 risk.consistency | multimodal / relations | [请求](../../schemas/model/M07.request.schema.json)、[响应](../../schemas/model/M07.response.schema.json) |

候选表：无；计划测试：TC-RISK-002-N, TC-RISK-002-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-RISK-003 输出风险证据与模态冲突

源位置：`docs/00-project/requirement-traceability.yaml/requirements/11`。

主追踪已有API：getRiskFindings, createPolicy, listPolicies；任务：T068, T069, T070, T140, T141。

来源任务卡：[T068.md](../../tasks/algorithm/T068.md)、[T069.md](../../tasks/algorithm/T069.md)、[T070.md](../../tasks/frontend/T070.md)、[T140.md](../../tasks/algorithm/T140.md)、[T141.md](../../tasks/algorithm/T141.md)。

候选流程入口：createTask；候选结果读取：getRiskFindings, getTaskEvidence。

M08融合与M25校准后，依policy_version/threshold_version触发人工分流；任务计算完成不能替代审核通过。必须保存原始分数、校准值、缺失模态和转人工原因。

结果身份：Findings.binding / risk_finding / finding_evidence。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

M09/M10产生疑似区域和类型；掩码固定ObjectRef并回映射原图。当前Findings通用投影不足以证明掩码/类型payload完整外露，不能只凭Schema存在判定闭环。

结果身份：Findings.binding / ObjectRef / mapping_version。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

M11—M14覆盖时间、空间、深伪和音画异常；半开区间[start_ms,end_ms)使用原件时间，轨迹映射原件坐标。逐能力失败/缺失与证据保留，未查明异常不能强制输出真伪。

结果身份：Findings.binding / TimeRange / mapping_version。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

M25校准仅在对应模型/任务/数据域下有效；低可靠性、OOD和证据不足应输出可见状态。Findings的warnings可提示但不是所有可靠性字段的确定映射，阈值与投影仍需唯一契约。

结果身份：Findings.binding / warnings / M25 payload。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M25 model.calibration | scores / calibration | [请求](../../schemas/model/M25.request.schema.json)、[响应](../../schemas/model/M25.response.schema.json) |

候选表：finding_evidence, tamper_finding；计划测试：TC-FORENSIC-003-N, TC-FORENSIC-003-E。

关联接口缺口：IF-G09, IF-G12, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-IMGRET-001 整图局部及关键帧多路召回

源位置：`docs/00-project/requirement-traceability.yaml/requirements/15`。

主追踪已有API：searchImage, searchImageRegion, getSearchJob, getIndex, switchIndex；任务：T079, T080, T081, T082, T085, T154, T155。

来源任务卡：[T079.md](../../tasks/algorithm/T079.md)、[T080.md](../../tasks/algorithm/T080.md)、[T081.md](../../tasks/algorithm/T081.md)、[T082.md](../../tasks/algorithm/T082.md)、[T085.md](../../tasks/algorithm/T085.md)、[T154.md](../../tasks/data/T154.md)、[T155.md](../../tasks/algorithm/T155.md)。

候选流程入口：searchImage, searchImageRegion；候选结果读取：getSearchJob。

整图/局部请求明确查询资产与区域；M15/M19召回，固定索引/模型/过滤范围。getIndex/switchIndex是管理前置，不能当查询结果。接收202后仅SUCCEEDED且result非空可展示正式候选。

结果身份：SearchAccepted.search_id / SearchJob / SearchResults。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

M16—M18做匹配点、几何变换和验证；几何证据、查询/候选区域及坐标映射需明示。source_match的relation和verification_type可表示验证类别，不能把召回相似度当几何验证成功。

结果身份：SearchJob.search_id / SourceMatch.verification_type / evidence_refs。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

将semantic_candidate、partial_copy/contains与高可信full_copy分别解释；T156难负样本不读取封存验收集。源绑定M18保留，未据模块默认引入全部能力。

结果身份：SourceMatch.relation / verification_type / index_version。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

按M15/M19帧特征与M33音频指纹召回；原追踪仅getIndex/switchIndex为管理关联，补充视频查询技术入口。保留查询/来源时间区间及索引版本，不能由索引查询替代视频结果。

结果身份：SearchJob.search_id / SearchResults / source_match。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

M20/M21及M25完成对齐/校准；query_range与source_range分别为各自原时间，direction和speed_ratio不能丢失。所有未知段单列；重算不能将旧mapping_version或旧索引静默替换。

结果身份：M20/M21 payload.mappings / SourceMatch query/source range。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

逐查询片段保存来源资产、源区间和验证证据；多源拼接允许多个来源及unknown_ranges。A—拼接Q—B的片段关系不推导A与B整内容同源。

结果身份：M22 payload / SourceMatch per-segment range。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M22 retrieval.source_boundary | features / source_mapping | [请求](../../schemas/model/M22.request.schema.json)、[响应](../../schemas/model/M22.response.schema.json) |

候选表：index_registry, search_job, source_match；计划测试：TC-VIDTRACE-003-N, TC-VIDTRACE-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-ORIGIN-001 按高可信边形成内容簇

源位置：`docs/00-project/requirement-traceability.yaml/requirements/21`。

主追踪已有API：未直接绑定；任务：T090, T164。

来源任务卡：[T090.md](../../tasks/backend/T090.md)、[T164.md](../../tasks/data/T164.md)。

候选流程入口：createTask；候选结果读取：当前尚无完整读取契约。

M23只输出关系，未返回cluster_id/成员簇。候选应用事务按当前案件验证full_copy后生成UUID并落content_cluster/cluster_member，部分包含不合并；任务到簇及成员读取接口仍缺。已移除将getFirstSource当聚类完整读取的映射。

结果身份：M23.payload.relations / content_cluster.cluster_id / cluster_member。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

M24输出簇内候选，应用分配ranking_id并保存不可变批次。cluster_id指真实簇，asset_id必须同案同簇，rank为连续1..candidate_count且最多3；rank不是发布时间。指定ranking_id读取，概率不是原创确定性。

结果身份：FirstSource.ranking_id / task_id / run_version / result_version / cluster_id。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

支持与反对证据分开；published_at来自可核验发布时间，discovered_at不可自动代替。真值/覆盖不足保留insufficient、未知发布时间/概率可null，不凑满3条且不跨簇补候选。

结果身份：FirstSource.evidence_ids / counter_evidence_ids / coverage_note / status。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M24 origin.first_source_rank | cluster_features / ranked_candidates | [请求](../../schemas/model/M24.request.schema.json)、[响应](../../schemas/model/M24.response.schema.json) |

候选表：cluster_member, content_cluster, first_source_candidate, first_source_ranking；计划测试：TC-ORIGIN-003-N, TC-ORIGIN-003-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-PROPAGATION-001 管理显式及推断传播关系

源位置：`docs/00-project/requirement-traceability.yaml/requirements/24`。

主追踪已有API：getPropagation, decidePropagationEdge；任务：T094, T095, T096。

来源任务卡：[T094.md](../../tasks/backend/T094.md)、[T095.md](../../tasks/backend/T095.md)、[T096.md](../../tasks/backend/T096.md)。

候选流程入口：createTask；候选结果读取：getPropagation。

M26/M27与普通图处理分工；observed来自记录，inferred带模型与证据，human来自复核记录。图快照按版本固定，当前Graph缺完整task/run/result绑定，不能把候选边当事实传播。

结果身份：Graph.cluster_id / version / GraphEdge.origin / probability / evidence_ids。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

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

候选流程入口：createTask；候选结果读取：getPropagation。

展示的是指定图版本的时间线与版本差异；关系时间不能仅用数据库created_at代替发布时间/观察时间。当前响应未定义前后版本差异投影与完整来源时间字段，登记为未覆盖。

结果身份：Graph.version / GraphNode / GraphEdge。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M26 propagation.path | graph / graph | [请求](../../schemas/model/M26.request.schema.json)、[响应](../../schemas/model/M26.response.schema.json) |

候选表：propagation_edge, propagation_node, review_record；计划测试：TC-PROPAGATION-002-N, TC-PROPAGATION-002-E。

关联接口缺口：IF-G09, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-PROPAGATION-003 人工确认或驳回推断边

源位置：`docs/00-project/requirement-traceability.yaml/requirements/26`。

主追踪已有API：getPropagation, decidePropagationEdge, createReview, requestApproval, decideApproval, createPolicy；任务：T096, T097, T102。

来源任务卡：[T096.md](../../tasks/backend/T096.md)、[T097.md](../../tasks/frontend/T097.md)、[T102.md](../../tasks/backend/T102.md)。

候选流程入口：decidePropagationEdge, createReview；候选结果读取：decidePropagationEdge, getPropagation。

人工确认/驳回只改明确edge_id和期望版本；理由/证据/审批按适用规则处理。原边与模型概率保留，产生新关系版本和审计；getPropagation不能代替复核待办读取。

结果身份：GraphDecision / GraphEdge.version / Review.review_version。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M26 propagation.path | graph / graph | [请求](../../schemas/model/M26.request.schema.json)、[响应](../../schemas/model/M26.response.schema.json) |
| M27 propagation.inferred_edge | graph / graph | [请求](../../schemas/model/M27.request.schema.json)、[响应](../../schemas/model/M27.response.schema.json) |

候选表：approval_decision, approval_request, audit_event, policy_registry, propagation_edge, propagation_node, review_evidence, review_record；计划测试：TC-PROPAGATION-003-N, TC-PROPAGATION-003-E。

关联接口缺口：IF-G02, IF-G03, IF-G09, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-CLAIM-001 抽取结构化主张

源位置：`docs/00-project/requirement-traceability.yaml/requirements/27`。

主追踪已有API：extractClaims；任务：T098, T166, T167。

来源任务卡：[T098.md](../../tasks/algorithm/T098.md)、[T166.md](../../tasks/data/T166.md)、[T167.md](../../tasks/algorithm/T167.md)。

候选流程入口：extractClaims；候选结果读取：extractClaims。

当前契约同步返回ClaimList，结果从同次响应读取；已移除getReport映射。M28抽取主体、事件、时间地点等字段并绑定来源片段；后续历史claim查询尚无专用契约。

结果身份：ClaimList.claims / Claim.claim_id / source segment。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M28 claim.extract | text / claims | [请求](../../schemas/model/M28.request.schema.json)、[响应](../../schemas/model/M28.response.schema.json) |

候选表：claim, text_segment；计划测试：TC-CLAIM-001-N, TC-CLAIM-001-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-CLAIM-002 检索白名单证据并判断关系

源位置：`docs/00-project/requirement-traceability.yaml/requirements/28`。

主追踪已有API：verifyClaim；任务：T099, T168。

来源任务卡：[T099.md](../../tasks/algorithm/T099.md)、[T168.md](../../tasks/algorithm/T168.md)。

候选流程入口：verifyClaim；候选结果读取：verifyClaim。

当前同步返回Relation，结果从同次响应读取；白名单检索与M29关系判断分别校验，已移除getReport映射。本轮已修正Relation及M29/inference：insufficient允许空证据，其他关系仍要求证据；持久化无证据状态存于固定task_result摘要且不虚构关系行，实际服务联调仍未完成。

结果身份：Relation.claim_id / relation / evidence_ids / model_version。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M29 claim.evidence_relation | claims_evidence / relations | [请求](../../schemas/model/M29.request.schema.json)、[响应](../../schemas/model/M29.response.schema.json) |

候选表：claim, claim_evidence_relation；计划测试：TC-CLAIM-002-N, TC-CLAIM-002-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-CLAIM-003 生成带证据引用摘要

源位置：`docs/00-project/requirement-traceability.yaml/requirements/29`。

主追踪已有API：createReportDraft；任务：T106, T169。

来源任务卡：[T106.md](../../tasks/backend/T106.md)、[T169.md](../../tasks/algorithm/T169.md)。

候选流程入口：createReportDraft；候选结果读取：getReport。

M30生成带引用摘要，报告草稿受理后查report_id终态；DRAFT/READY与正式批准不同。句级引用必须语义支持且固定版本；只有ID存在/JSON合法不能证明内容可入报告。

结果身份：Report.report_id / state / evidence_ids / ObjectRef。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M30 claim.grounding | claims_evidence / grounding | [请求](../../schemas/model/M30.request.schema.json)、[响应](../../schemas/model/M30.response.schema.json) |

候选表：report, report_evidence；计划测试：TC-CLAIM-003-N, TC-CLAIM-003-E。

关联接口缺口：IF-G09, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-REVIEW-001 人工复核会审及退回重算

源位置：`docs/00-project/requirement-traceability.yaml/requirements/30`。

主追踪已有API：getTaskEvidence, decidePropagationEdge, createReview, requestApproval, decideApproval, requestFeedback, createPolicy；任务：T100, T101, T102, T103, T108。

来源任务卡：[T100.md](../../tasks/backend/T100.md)、[T101.md](../../tasks/backend/T101.md)、[T102.md](../../tasks/backend/T102.md)、[T103.md](../../tasks/frontend/T103.md)、[T108.md](../../tasks/backend/T108.md)。

候选流程入口：createReview, requestApproval, decideApproval, requestFeedback；候选结果读取：createReview, requestApproval, decideApproval, getTaskEvidence。

提交响应可读但缺工作台/审批/反馈历史查询；退回补证和request_rerun按不同动作办理，重算产生新运行/结果版本而不覆盖旧意见。反馈不等于已获训练用途授权。

结果身份：Review task/run/result/review_version / Approval / FeedbackRecord。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：approval_decision, approval_request, audit_event, evidence_item, feedback_request, policy_registry, propagation_edge, review_evidence, review_record, task_evidence；计划测试：TC-REVIEW-001-N, TC-REVIEW-001-E。

关联接口缺口：IF-G02, IF-G03, IF-G04, IF-G09, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-REVIEW-002 固化证据并保留版本

源位置：`docs/00-project/requirement-traceability.yaml/requirements/31`。

主追踪已有API：sealEvidence；任务：T104, T105。

来源任务卡：[T104.md](../../tasks/backend/T104.md)、[T105.md](../../tasks/backend/T105.md)。

候选流程入口：sealEvidence；候选结果读取：sealEvidence。

固化响应包含清单；固定证据ObjectRef.version_id及摘要，保留包版本。现有接口缺包列表/历史详情/签验读取，不借用报告读取；mock/not_signed状态不得表述为正式签验通过。

结果身份：EvidencePackage.package_id / version / manifest_sha256 / manifest。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：audit_event, evidence_package, object_version, package_item；计划测试：TC-REVIEW-002-N, TC-REVIEW-002-E。

关联接口缺口：IF-G09；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-REVIEW-003 生成报告及受控导出

源位置：`docs/00-project/requirement-traceability.yaml/requirements/32`。

主追踪已有API：createReportDraft, createReport, getReport, downloadReport；任务：T106, T107。

来源任务卡：[T106.md](../../tasks/backend/T106.md)、[T107.md](../../tasks/backend/T107.md)。

候选流程入口：createReportDraft, createReport；候选结果读取：getReport, downloadReport。

草稿和正式报告生成分开；READY仅产物生成成功，导出仍校验当前权限、目的及有效批准。旧批准不随重算继承；下载绑定固定产物版本，撤销后下一Range拒绝。

结果身份：Report.report_id / run_version / result_version / approval_id / object_ref。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M30 claim.grounding | claims_evidence / grounding | [请求](../../schemas/model/M30.request.schema.json)、[响应](../../schemas/model/M30.response.schema.json) |

候选表：approval_request, audit_event, report, report_evidence；计划测试：TC-REVIEW-003-N, TC-REVIEW-003-E。

关联接口缺口：IF-G02, IF-G09, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-OPS-001 管理角色模型标签阈值规则

源位置：`docs/00-project/requirement-traceability.yaml/requirements/33`。

主追踪已有API：devLogin, getCurrentUser, requestApproval, decideApproval, issueOperationToken, registerModel, listModels, getModelHealth, rolloutModel, recordEvaluation, listEvaluations, listAuditEvents, exportAudit, createPolicy, listPolicies；任务：T011, T012, T013, T014, T016, T017, T018, T051, T052, T058, T060, T061。

来源任务卡：[T011.md](../../tasks/platform/T011.md)、[T012.md](../../tasks/platform/T012.md)、[T013.md](../../tasks/platform/T013.md)、[T014.md](../../tasks/platform/T014.md)、[T016.md](../../tasks/platform/T016.md)、[T017.md](../../tasks/platform/T017.md)、[T018.md](../../tasks/frontend/T018.md)、[T051.md](../../tasks/algorithm/T051.md)、[T052.md](../../tasks/algorithm/T052.md)、[T058.md](../../tasks/algorithm/T058.md)、[T060.md](../../tasks/frontend/T060.md)、[T061.md](../../tasks/algorithm/T061.md)。

候选流程入口：registerModel, recordEvaluation, createPolicy, requestApproval, decideApproval；候选结果读取：listModels, listEvaluations, listPolicies, listAuditEvents。

按管理对象分别配置和查询；开发devLogin不是正式身份接入，rolloutModel为发布动作且不是标签配置入口。角色/阈值激活撤销及管理API责任仍待定；不混同组织权限与案件数据范围。

结果身份：Model / Evaluation / Policy / Approval。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：approval_decision, approval_request, audit_event, audit_export, case_membership, index_registry, model_evaluation, model_registry, model_release, operation_token, policy_registry, user_roles, users；计划测试：TC-OPS-001-N, TC-OPS-001-E。

关联接口缺口：IF-G02, IF-G05, IF-G06, IF-G07, IF-G12；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-OPS-002 监控任务GPU队列存储及索引

源位置：`docs/00-project/requirement-traceability.yaml/requirements/34`。

主追踪已有API：listTasks, getTask, cancelTask, rerunTask, getModelHealth；任务：T035, T040, T055, T056, T059, T117, T118, T119, T120。

来源任务卡：[T035.md](../../tasks/backend/T035.md)、[T040.md](../../tasks/frontend/T040.md)、[T055.md](../../tasks/algorithm/T055.md)、[T056.md](../../tasks/algorithm/T056.md)、[T059.md](../../tasks/algorithm/T059.md)、[T117.md](../../tasks/testing/T117.md)、[T118.md](../../tasks/testing/T118.md)、[T119.md](../../tasks/testing/T119.md)、[T120.md](../../tasks/backend/T120.md)。

候选流程入口：listTasks, getTask, getModelHealth；候选结果读取：listTasks, getTask, getModelHealth。

只读任务/模型健康有契约；cancelTask/rerunTask为独立控制动作，已移出监控读入口。GPU、队列、存储、索引监控目前由运维指标规划，不能把Health当全量监控或任务完成证据。

结果身份：Task.state / nodes / Health。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

主追踪没有模型ID；媒体探测/存储/权限等普通处理沿用任务卡，不凭空创建模型能力。

候选表：analysis_task, model_registry, outbox_event, task_event, task_node_run, task_run；计划测试：TC-OPS-002-N, TC-OPS-002-E。

关联接口缺口：IF-G05, IF-G11, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

## FR-OPS-003 灰度回滚及备份恢复

源位置：`docs/00-project/requirement-traceability.yaml/requirements/35`。

主追踪已有API：listModels, getModelHealth, rolloutModel；任务：T057, T060, T121, T122, T123, T124, T170。

来源任务卡：[T057.md](../../tasks/algorithm/T057.md)、[T060.md](../../tasks/frontend/T060.md)、[T121.md](../../tasks/deployment/T121.md)、[T122.md](../../tasks/testing/T122.md)、[T123.md](../../tasks/testing/T123.md)、[T124.md](../../tasks/testing/T124.md)、[T170.md](../../tasks/algorithm/T170.md)。

候选流程入口：rolloutModel；候选结果读取：listModels, getModelHealth。

rolloutModel含灰度/rollback，但202后的操作终态查询仍缺，健康只能旁证；备份恢复是受控离线运维流程，M34运行转换不代表所有包可部署。数据库/对象/模型/索引/密钥恢复分别对账。

结果身份：ActionAck.object_id / release_bundle / Model.version。技术复核状态：`TECHNICAL_REVIEW_COMPLETED_REMAINING_CONTRACT_GAPS_IDENTIFIED`。

| 来源能力 | 输入/输出路径 | 结构源 |
| --- | --- | --- |
| M34 model.compression | model_bundle / release_bundle | [请求](../../schemas/model/M34.request.schema.json)、[响应](../../schemas/model/M34.response.schema.json) |

候选表：approval_request, index_registry, model_registry, model_release；计划测试：TC-OPS-003-N, TC-OPS-003-E。

关联接口缺口：IF-G05, IF-G13；全部详见[接口缺口](../03-api/interface-gap-register.md)。实现/验收均未由本文宣称完成。

