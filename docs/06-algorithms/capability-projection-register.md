# 34能力：原响应保存与业务投影

[机器登记](capability-projection-register.json)逐能力保存请求/响应源摘要、必填输入、payload路径、源任务和公开投影候选。全量原响应先按本能力Schema保存，再由应用投影；通用Finding不能替代所有payload。

## M01 risk.image_classification

输入：decoded_original；输出：classification。源任务：T062,T113,T130,T131。

结构：[请求](../../schemas/model/M01.request.schema.json)、[响应](../../schemas/model/M01.response.schema.json)。全部payload路径：`labels, labels[].calibrated_score, labels[].label, labels[].raw_score, labels[].threshold_version`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M02 risk.object_detection

输入：decoded_original；输出：detections。源任务：T063,T132。

结构：[请求](../../schemas/model/M02.request.schema.json)、[响应](../../schemas/model/M02.response.schema.json)。全部payload路径：`detections, detections[].bbox, detections[].frame_id, detections[].label, detections[].score, detections[].timestamp_ms`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M03 risk.small_object

输入：decoded_original；输出：detections。源任务：T133。

结构：[请求](../../schemas/model/M03.request.schema.json)、[响应](../../schemas/model/M03.response.schema.json)。全部payload路径：`detections, detections[].bbox, detections[].frame_id, detections[].label, detections[].score, detections[].timestamp_ms`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M04 risk.video_action

输入：analysis_copy；输出：temporal_events。源任务：T064,T135。

结构：[请求](../../schemas/model/M04.request.schema.json)、[响应](../../schemas/model/M04.response.schema.json)。全部payload路径：`events, events[].label, events[].score, events[].time_range`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M05 risk.temporal_event

输入：analysis_copy；输出：temporal_events。源任务：T136。

结构：[请求](../../schemas/model/M05.request.schema.json)、[响应](../../schemas/model/M05.response.schema.json)。全部payload路径：`events, events[].label, events[].score, events[].time_range`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M06 risk.audio_event

输入：audio；输出：temporal_events。源任务：T065,T137。

结构：[请求](../../schemas/model/M06.request.schema.json)、[响应](../../schemas/model/M06.response.schema.json)。全部payload路径：`events, events[].label, events[].score, events[].time_range`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M07 risk.consistency

输入：multimodal；输出：relations。源任务：T067,T138,T139。

结构：[请求](../../schemas/model/M07.request.schema.json)、[响应](../../schemas/model/M07.response.schema.json)。全部payload路径：`relations, relations[].left_evidence_ids, relations[].relation, relations[].right_evidence_ids, relations[].score`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M08 risk.fusion

输入：multimodal；输出：classification。源任务：T068,T140。

结构：[请求](../../schemas/model/M08.request.schema.json)、[响应](../../schemas/model/M08.response.schema.json)。全部payload路径：`labels, labels[].calibrated_score, labels[].label, labels[].raw_score, labels[].threshold_version`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M09 forensic.image_localization

输入：original_bytes；输出：masks。源任务：T072,T142,T143,T144,T145。

结构：[请求](../../schemas/model/M09.request.schema.json)、[响应](../../schemas/model/M09.response.schema.json)。全部payload路径：`masks, masks[].height, masks[].object_ref, masks[].score, masks[].time_range, masks[].width`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M10 forensic.tamper_type

输入：original_bytes；输出：classification。源任务：T073,T146。

结构：[请求](../../schemas/model/M10.request.schema.json)、[响应](../../schemas/model/M10.response.schema.json)。全部payload路径：`labels, labels[].calibrated_score, labels[].label, labels[].raw_score, labels[].threshold_version`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M11 forensic.video_temporal

输入：original_bytes；输出：temporal_events。源任务：T074,T147,T148。

结构：[请求](../../schemas/model/M11.request.schema.json)、[响应](../../schemas/model/M11.response.schema.json)。全部payload路径：`events, events[].label, events[].score, events[].time_range`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M12 forensic.video_spatial

输入：decoded_original；输出：masks。源任务：T075,T149。

结构：[请求](../../schemas/model/M12.request.schema.json)、[响应](../../schemas/model/M12.response.schema.json)。全部payload路径：`masks, masks[].height, masks[].object_ref, masks[].score, masks[].time_range, masks[].width`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M13 forensic.deepfake

输入：face_track；输出：classification。源任务：T076,T150。

结构：[请求](../../schemas/model/M13.request.schema.json)、[响应](../../schemas/model/M13.response.schema.json)。全部payload路径：`labels, labels[].calibrated_score, labels[].label, labels[].raw_score, labels[].threshold_version, labels[].track_id`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M14 forensic.avsync

输入：audio_face；输出：temporal_events。源任务：T076,T151。

结构：[请求](../../schemas/model/M14.request.schema.json)、[响应](../../schemas/model/M14.response.schema.json)。全部payload路径：`events, events[].label, events[].score, events[].time_range`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M15 retrieval.image_embedding

输入：analysis_copy；输出：embedding。源任务：T080,T154,T155。

结构：[请求](../../schemas/model/M15.request.schema.json)、[响应](../../schemas/model/M15.response.schema.json)。全部payload路径：`dimension, dtype, normalization, vector_ref`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M16 retrieval.local_features

输入：decoded_original；输出：local_features。源任务：T083。

结构：[请求](../../schemas/model/M16.request.schema.json)、[响应](../../schemas/model/M16.response.schema.json)。全部payload路径：`descriptor_dimension, feature_ref, keypoint_count`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M17 retrieval.local_match

输入：features；输出：local_matches。源任务：T083。

结构：[请求](../../schemas/model/M17.request.schema.json)、[响应](../../schemas/model/M17.response.schema.json)。全部payload路径：`candidate_asset_id, match_count, match_ref, query_asset_id`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M18 retrieval.geometry

输入：features；输出：geometry。源任务：T084。

结构：[请求](../../schemas/model/M18.request.schema.json)、[响应](../../schemas/model/M18.response.schema.json)。全部payload路径：`coverage, inliers, transform, verified`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M19 retrieval.frame_embedding

输入：analysis_copy；输出：embedding。源任务：T080,T158,T159。

结构：[请求](../../schemas/model/M19.request.schema.json)、[响应](../../schemas/model/M19.response.schema.json)。全部payload路径：`dimension, dtype, normalization, vector_ref`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M20 retrieval.temporal_alignment

输入：features；输出：source_mapping。源任务：T087,T088,T160。

结构：[请求](../../schemas/model/M20.request.schema.json)、[响应](../../schemas/model/M20.response.schema.json)。全部payload路径：`mappings, mappings[].direction, mappings[].query_range, mappings[].score, mappings[].source_asset_id, mappings[].source_range, mappings[].speed_ratio, unknown_ranges`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M21 retrieval.segment_localizer

输入：features；输出：source_mapping。源任务：T161。

结构：[请求](../../schemas/model/M21.request.schema.json)、[响应](../../schemas/model/M21.response.schema.json)。全部payload路径：`mappings, mappings[].direction, mappings[].query_range, mappings[].score, mappings[].source_asset_id, mappings[].source_range, mappings[].speed_ratio, unknown_ranges`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M22 retrieval.source_boundary

输入：features；输出：source_mapping。源任务：T089,T162。

结构：[请求](../../schemas/model/M22.request.schema.json)、[响应](../../schemas/model/M22.response.schema.json)。全部payload路径：`mappings, mappings[].direction, mappings[].query_range, mappings[].score, mappings[].source_asset_id, mappings[].source_range, mappings[].speed_ratio, unknown_ranges`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M23 origin.content_cluster

输入：verified_relations；输出：cluster_relations。源任务：T090,T164。

结构：[请求](../../schemas/model/M23.request.schema.json)、[响应](../../schemas/model/M23.response.schema.json)。全部payload路径：`relations, relations[].evidence_ids, relations[].left_asset_id, relations[].relation, relations[].right_asset_id`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M24 origin.first_source_rank

输入：cluster_features；输出：ranked_candidates。源任务：T092,T165。

结构：[请求](../../schemas/model/M24.request.schema.json)、[响应](../../schemas/model/M24.response.schema.json)。全部payload路径：`candidates, candidates[].asset_id, candidates[].counter_evidence_ids, candidates[].evidence_ids, candidates[].probability, candidates[].published_at, candidates[].rank, cluster_id, coverage_note, model_version, scope, status`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M25 model.calibration

输入：scores；输出：calibration。源任务：T141,T153,T163。

结构：[请求](../../schemas/model/M25.request.schema.json)、[响应](../../schemas/model/M25.response.schema.json)。全部payload路径：`artifact_ref, calibration_version, method, split`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M26 propagation.path

输入：graph；输出：graph。源任务：T094,T095,T097。

结构：[请求](../../schemas/model/M26.request.schema.json)、[响应](../../schemas/model/M26.response.schema.json)。全部payload路径：`cluster_id, edges, nodes, version`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M27 propagation.inferred_edge

输入：graph；输出：graph。源任务：T096。

结构：[请求](../../schemas/model/M27.request.schema.json)、[响应](../../schemas/model/M27.response.schema.json)。全部payload路径：`cluster_id, edges, nodes, version`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M28 claim.extract

输入：text；输出：claims。源任务：T098,T166,T167。

结构：[请求](../../schemas/model/M28.request.schema.json)、[响应](../../schemas/model/M28.response.schema.json)。全部payload路径：`claims, warnings`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M29 claim.evidence_relation

输入：claims_evidence；输出：relations。源任务：T099,T168。

结构：[请求](../../schemas/model/M29.request.schema.json)、[响应](../../schemas/model/M29.response.schema.json)。全部payload路径：`relations, relations[].left_evidence_ids, relations[].relation, relations[].right_evidence_ids, relations[].score`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M30 claim.grounding

输入：claims_evidence；输出：grounding。源任务：T106,T169。

结构：[请求](../../schemas/model/M30.request.schema.json)、[响应](../../schemas/model/M30.response.schema.json)。全部payload路径：`sentences, sentences[].evidence_ids, sentences[].sentence_id, sentences[].supported, sentences[].text, sentences[].violation`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M31 media.ocr

输入：decoded_original；输出：text_segments。源任务：T048。

结构：[请求](../../schemas/model/M31.request.schema.json)、[响应](../../schemas/model/M31.response.schema.json)。全部payload路径：`segments, segments[].bbox, segments[].score, segments[].text, segments[].time_range`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M32 media.asr

输入：audio；输出：text_segments。源任务：T049。

结构：[请求](../../schemas/model/M32.request.schema.json)、[响应](../../schemas/model/M32.response.schema.json)。全部payload路径：`segments, segments[].bbox, segments[].score, segments[].text, segments[].time_range`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M33 media.audio_fingerprint

输入：audio；输出：fingerprint。源任务：T047,T086。

结构：[请求](../../schemas/model/M33.request.schema.json)、[响应](../../schemas/model/M33.response.schema.json)。全部payload路径：`algorithm_version, duration_ms, fingerprint_ref`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。

## M34 model.compression

输入：model_bundle；输出：release_bundle。源任务：T170。

结构：[请求](../../schemas/model/M34.request.schema.json)、[响应](../../schemas/model/M34.response.schema.json)。全部payload路径：`backend, bundle_id, bundle_sha256, calibration_version, index_version, license_record_ref, model_version`。

保存：task_result.summary.capability_outputs中按model_id选择数组条目，完整response按源Schema校验；不把model_id当数组下标。案件/任务/run绑定、能力常量、模型/前处理/映射版本、失败reason、固定ObjectRef摘要均核验。公开专用投影和业务后端仍待对应任务实现。
