# 模型能力及数据映射

| 模型 | 方向 | 能力 | 输入路径 | 输出 | 候选 | 任务 | 数据集 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | 图片多标签风险分类 | risk.image_classification | decoded_original | classification | ConvNeXt-B | T062,T113,T130,T131 | D01 | candidate_pending_review |
| M02 | 敏感目标检测 | risk.object_detection | decoded_original | detections | RT-DETR-R50 | T063,T132 | D02 | candidate_pending_review |
| M03 | 小目标检测 | risk.small_object | decoded_original | detections | SAHI＋RT-DETR | T133 | D02 | candidate_pending_review |
| M04 | 视频行为识别 | risk.video_action | analysis_copy | temporal_events | VideoMAE V2 | T064,T135 | D03 | candidate_pending_review |
| M05 | 视频事件时间定位 | risk.temporal_event | analysis_copy | temporal_events | ActionFormer | T136 | D03 | candidate_pending_review |
| M06 | 音频事件识别 | risk.audio_event | audio | temporal_events | BEATs | T065,T137 | D04 | candidate_pending_review |
| M07 | 跨模态矛盾检测 | risk.consistency | multimodal | relations | Qwen2.5-VL＋NLI头 | T067,T138,T139 | D05 | candidate_pending_review |
| M08 | 多模态风险融合 | risk.fusion | multimodal | classification | Multimodal Transformer | T068,T140 | D01,D02,D03,D04,D05 | candidate_pending_review |
| M09 | 图片篡改检测定位 | forensic.image_localization | original_bytes | masks | TruFor | T072,T142,T143,T144,T145 | D06 | candidate_pending_review |
| M10 | 图片篡改类型分类 | forensic.tamper_type | original_bytes | classification | ConvNeXt＋取证特征 | T073,T146 | D06 | candidate_pending_review |
| M11 | 视频时间篡改检测 | forensic.video_temporal | original_bytes | temporal_events | VideoMAE＋时序Transformer | T074,T147,T148 | D07 | candidate_pending_review |
| M12 | 视频空间篡改 | forensic.video_spatial | decoded_original | masks | TruFor＋XMem | T075,T149 | D07 | candidate_pending_review |
| M13 | 人脸深度伪造 | forensic.deepfake | face_track | classification | VideoMAE等分类骨干；SBI仅训练增强候选 | T076,T150 | D08 | candidate_pending_review |
| M14 | 音画同步 | forensic.avsync | audio_face | temporal_events | VocaLiST | T076,T151 | D08 | candidate_pending_review |
| M15 | 图片复制检测向量 | retrieval.image_embedding | analysis_copy | embedding | SSCD | T080,T154,T155 | D09,D15 | candidate_pending_review |
| M16 | 局部特征提取 | retrieval.local_features | decoded_original | local_features | SuperPoint | T083 | D09 | candidate_pending_review |
| M17 | 局部特征匹配 | retrieval.local_match | features | local_matches | LightGlue | T083 | D09 | candidate_pending_review |
| M18 | 几何验证 | retrieval.geometry | features | geometry | MAGSAC++/USAC | T084 | D09 | candidate_pending_review |
| M19 | 视频关键帧复制向量 | retrieval.frame_embedding | analysis_copy | embedding | SSCD/DINOv2适配版 | T080,T158,T159 | D10 | candidate_pending_review |
| M20 | 视频序列对齐 | retrieval.temporal_alignment | features | source_mapping | 局部DTW＋Smith-Waterman | T087,T088,T160 | D10 | candidate_pending_review |
| M21 | 学习型片段定位 | retrieval.segment_localizer | features | source_mapping | Temporal Transformer | T161 | D10 | candidate_pending_review |
| M22 | 多源拼接边界 | retrieval.source_boundary | features | source_mapping | TCN | T089,T162 | D11 | candidate_pending_review |
| M23 | 同源内容聚类 | origin.content_cluster | verified_relations | cluster_relations | 高可信整内容关系聚类；片段/包含关系独立表达 | T090,T164 | D09,D10,D11 | candidate_pending_review |
| M24 | 首发候选排序 | origin.first_source_rank | cluster_features | ranked_candidates | LightGBM LambdaMART | T092,T165 | D12 | candidate_pending_review |
| M25 | 概率校准 | model.calibration | scores | calibration | 等渗回归/温度缩放/Platt候选 | T141,T153,T163 | D01,D06,D10,D12 | candidate_pending_review |
| M26 | 传播路径分析 | propagation.path | graph | graph | 时间约束图推理＋PageRank | T094,T095,T097 | D12 | candidate_pending_review |
| M27 | 隐式传播关系 | propagation.inferred_edge | graph | graph | LightGBM/XGBoost | T096 | D12 | candidate_pending_review |
| M28 | 结构化主张抽取 | claim.extract | text | claims | Qwen2.5-7B/14B | T098,T166,T167 | D13 | candidate_pending_review |
| M29 | 证据关系判断 | claim.evidence_relation | claims_evidence | relations | DeBERTa-v3/XLM-R NLI | T099,T168 | D14 | candidate_pending_review |
| M30 | 无证据生成检测 | claim.grounding | claims_evidence | grounding | NLI＋规则 | T106,T169 | D13,D14 | candidate_pending_review |
| M31 | OCR | media.ocr | decoded_original | text_segments | PaddleOCR PP-OCR | T048 | D01,D05,D13 | candidate_pending_review |
| M32 | ASR | media.asr | audio | text_segments | FunASR Paraformer | T049 | D03,D04,D05,D13 | candidate_pending_review |
| M33 | 音频指纹 | media.audio_fingerprint | audio | fingerprint | Chromaprint | T047,T086 | D04,D10 | candidate_pending_review |
| M34 | 模型压缩 | model.compression | model_bundle | release_bundle | 蒸馏＋ONNX INT8 | T170 | D01,D06,D09,D10,D13 | candidate_pending_review |
