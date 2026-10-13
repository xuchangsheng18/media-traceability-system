# 需求映射语义复核

36条需求逐条按来源验收语句、任务范围、现有请求/响应、内部模型payload及结果身份完成技术复核。以下结论是可执行的设计输入；正式业务规则和运行结果仍分别核验。主追踪未被改写。机器记录见[requirement-semantic-review.json](requirement-semantic-review.json)，完整流程见[requirement-processing-map.md](requirement-processing-map.md)。

本轮纠正模块默认入口过宽、同步响应误绑报告查询、索引管理误作视频业务入口、首发排序误作聚类成员读取、取消/重算误作监控读入口五类问题。未覆盖的结构被明确保留为缺口，不以一句“见来源契约”掩盖。

## 逐需求结论

### FR-INGEST-001

来源验收：无来源授权不得处理。任务：T021, T028, T029；能力：普通处理，无模型绑定。

入口：createSource, createImport；结果：listSources, getImport。身份：Source.source_id / ImportStatus.import_id。

登记来源用途后再导入；客户端授权状态不具批准效力，服务端核验当前来源授权。普通单文件上传为关联流程，不替代本条来源登记。

关联：IF-G08, IF-G10。

### FR-INGEST-002

来源验收：重复分片不重复登记。任务：T022, T023, T024；能力：普通处理，无模型绑定。

入口：createUpload, putUploadPart, completeUpload；结果：仍缺完整读取。身份：UploadSession.upload_id / UploadPart.part_no / UploadResult.upload_id。

按upload_id与part_no重试；同编号同摘要重复不增计，冲突拒绝。completeUpload返回VALIDATING后缺进度/分片/终态读取，不能以getImport查询上传，也不能提前使用asset_id。

关联：IF-G01。

### FR-INGEST-003

来源验收：不合格素材隔离并显示原因。任务：T024, T025, T026, T027；能力：普通处理，无模型绑定。

入口：completeUpload；结果：getAsset, downloadAsset。身份：UploadResult.asset_id / Asset.state / ObjectRef.version_id。

合并摘要、格式与恶意素材检查在后端处理；VALID且当前授权生效才允许分析。QUARANTINED/REJECTED保留原因；当前UploadResult没有完整拒绝原因和异步终态读取，下载不是校验状态接口。

关联：IF-G01, IF-G08。

### FR-RESOURCE-001

来源验收：原件与版本可查。任务：T019, T020, T025, T030；能力：普通处理，无模型绑定。

入口：listAssets, getAsset；结果：getAsset, downloadAsset。身份：Asset.asset_id / kind / object_ref / version。

资源管理只读取原件/副本；已移除上一版不相关searchImage入口。Asset有kind和固定ObjectRef但未返回完整parent_asset_id、lineage及转换参数，不能声称完整血缘已覆盖。

关联：IF-G09。

### FR-RESOURCE-002

来源验收：近重复不能自动确认为同源。任务：T027, T079, T082, T090；能力：M23。

入口：completeUpload, searchImage；结果：getSearchJob。身份：UploadResult.duplicate_of / SearchJob.search_id / SourceMatch.relation。

摘要相同仅在有权范围内判完全重复；近重复是检索及几何/时序验证候选。M23只产出关系建议，不允许语义相似或partial_copy自动并整内容簇；两种结果分别返回。

关联：IF-G01, IF-G09, IF-G13。

### FR-RESOURCE-003

来源验收：查询不能泄露其他案件资产。任务：T015, T021, T025, T030；能力：普通处理，无模型绑定。

入口：getCurrentUser, listAssets, getAsset；结果：listAssets, getAsset, downloadAsset。身份：Asset.case_id / source_id / object_ref。

逐次读取及每个Range请求均校验当前单位、案件、用途与到期/撤销；文件哈希或历史批准不是访问权。生命周期过滤和跨案拒绝由访问层执行。

关联：IF-G07, IF-G08。

### FR-MEDIA-001

来源验收：副本不覆盖原件。任务：T041, T042, T043；能力：普通处理，无模型绑定。

入口：createTask；结果：getAsset。身份：Task.task_id / Asset.asset_id / ObjectRef / asset_lineage。

T041—T043执行ffprobe/标准化副本，属于普通媒体处理而非模型能力。输入原件ObjectRef不可覆盖；完整编码/流/派生参数尚缺对外投影，不能把Asset的mime/宽高时长摘要当全部元数据。

关联：IF-G11, IF-G13。

### FR-MEDIA-002

来源验收：帧和片段回指原始时间。任务：T044, T045, T046, T047；能力：M33。

入口：createTask；结果：getTimeline。身份：Timeline.asset_id / mapping_version / TimelineItem。

T044—T047负责镜头/帧/音轨/字幕和原始PTS映射，M33只覆盖音频指纹。音轨/字幕对象版本和派生资产绑定需补完整契约；Timeline投影不等于全部媒体输出已返回。

关联：IF-G11, IF-G13。

### FR-MEDIA-003

来源验收：缺失模态显示影响范围。任务：T048, T049, T050, T066；能力：M31, M32。

入口：createTask；结果：getTimeline。身份：Timeline.asset_id / mapping_version / text_segment。

OCR=M31、ASR=M32，普通媒体处理先生成输入；OCR框映射原件空间，ASR按原音轨时间。缺失/失败模态需进入任务missing_modalities及对应时间范围，不能以空文本假装识别完成。

关联：IF-G09, IF-G11, IF-G13。

### FR-RISK-001

来源验收：结果绑定标签与模型版本。任务：T061, T062, T063, T130, T131, T132, T133；能力：M01, M02, M03。

入口：createTask；结果：getRiskFindings, getTaskEvidence。身份：Findings.binding / Finding / Evidence。

createPolicy/listPolicies属于配置前置，已从结果入口中分离。M01/M02/M03输出标签/目标候选；应用融合绑定标签、模型、阈值及结果版本。框/类别投影覆盖逐字段核验，不能用策略列表读取风险结果。

关联：IF-G09, IF-G11, IF-G12, IF-G13。

### FR-RISK-002

来源验收：缺失或冲突不输出确定法律结论。任务：T064, T065, T066, T067, T134, T135, T136, T137, T138, T139；能力：M04, M05, M06, M07。

入口：createTask；结果：getRiskFindings, getTaskEvidence。身份：Findings.binding / missing_modalities / evidence_refs。

M04—M07分别处理动作、事件、音频、跨模态关系；融合节点须按原时间区间对齐并保存冲突和缺失范围。跨模态矛盾不是违法或法律结论；一般Finding未完整表达全部融合payload，保留投影差异。

关联：IF-G09, IF-G11, IF-G13。

### FR-RISK-003

来源验收：转人工依据规则版本。任务：T068, T069, T070, T140, T141；能力：M08, M25。

入口：createTask；结果：getRiskFindings, getTaskEvidence。身份：Findings.binding / risk_finding / finding_evidence。

M08融合与M25校准后，依policy_version/threshold_version触发人工分流；任务计算完成不能替代审核通过。必须保存原始分数、校准值、缺失模态和转人工原因。

关联：IF-G09, IF-G11, IF-G12, IF-G13。

### FR-FORENSIC-001

来源验收：区域掩码回指原件。任务：T071, T072, T073, T142, T143, T144, T145, T146；能力：M09, M10。

入口：createTask；结果：getForensics, getTaskEvidence。身份：Findings.binding / ObjectRef / mapping_version。

M09/M10产生疑似区域和类型；掩码固定ObjectRef并回映射原图。当前Findings通用投影不足以证明掩码/类型payload完整外露，不能只凭Schema存在判定闭环。

关联：IF-G09, IF-G11, IF-G13。

### FR-FORENSIC-002

来源验收：异常片段保留起止边界。任务：T074, T075, T076, T147, T148, T149, T150, T151, T152；能力：M11, M12, M13, M14。

入口：createTask；结果：getForensics, getTaskEvidence。身份：Findings.binding / TimeRange / mapping_version。

M11—M14覆盖时间、空间、深伪和音画异常；半开区间[start_ms,end_ms)使用原件时间，轨迹映射原件坐标。逐能力失败/缺失与证据保留，未查明异常不能强制输出真伪。

关联：IF-G09, IF-G11, IF-G13。

### FR-FORENSIC-003

来源验收：低可靠性标记而非强制判真伪。任务：T077, T078, T153；能力：M25。

入口：createTask；结果：getForensics, getTaskEvidence。身份：Findings.binding / warnings / M25 payload。

M25校准仅在对应模型/任务/数据域下有效；低可靠性、OOD和证据不足应输出可见状态。Findings的warnings可提示但不是所有可靠性字段的确定映射，阈值与投影仍需唯一契约。

关联：IF-G09, IF-G12, IF-G13。

### FR-IMGRET-001

来源验收：权限范围内候选可查。任务：T079, T080, T081, T082, T085, T154, T155；能力：M15, M19。

入口：searchImage, searchImageRegion；结果：getSearchJob。身份：SearchAccepted.search_id / SearchJob / SearchResults。

整图/局部请求明确查询资产与区域；M15/M19召回，固定索引/模型/过滤范围。getIndex/switchIndex是管理前置，不能当查询结果。接收202后仅SUCCEEDED且result非空可展示正式候选。

关联：IF-G09, IF-G13。

### FR-IMGRET-002

来源验收：匹配点区域及变换可解释。任务：T083, T084；能力：M16, M17, M18。

入口：searchImage, searchImageRegion；结果：getSearchJob。身份：SearchJob.search_id / SourceMatch.verification_type / evidence_refs。

M16—M18做匹配点、几何变换和验证；几何证据、查询/候选区域及坐标映射需明示。source_match的relation和verification_type可表示验证类别，不能把召回相似度当几何验证成功。

关联：IF-G09, IF-G13。

### FR-IMGRET-003

来源验收：语义相似不直接确认同源。任务：T082, T084, T085, T156, T157；能力：M18。

入口：searchImage, searchImageRegion；结果：getSearchJob。身份：SourceMatch.relation / verification_type / index_version。

将semantic_candidate、partial_copy/contains与高可信full_copy分别解释；T156难负样本不读取封存验收集。源绑定M18保留，未据模块默认引入全部能力。

关联：IF-G09, IF-G13。

### FR-VIDTRACE-001

来源验收：查询来源区间明确。任务：T080, T081, T086, T158, T159；能力：M15, M19, M33。

入口：searchVideo；结果：getSearchJob。身份：SearchJob.search_id / SearchResults / source_match。

按M15/M19帧特征与M33音频指纹召回；原追踪仅getIndex/switchIndex为管理关联，补充视频查询技术入口。保留查询/来源时间区间及索引版本，不能由索引查询替代视频结果。

关联：IF-G09, IF-G11, IF-G13。

### FR-VIDTRACE-002

来源验收：变速方向和时间映射保留。任务：T087, T088, T160, T161, T163；能力：M20, M21, M25。

入口：searchVideo；结果：getSearchJob。身份：M20/M21 payload.mappings / SourceMatch query/source range。

M20/M21及M25完成对齐/校准；query_range与source_range分别为各自原时间，direction和speed_ratio不能丢失。所有未知段单列；重算不能将旧mapping_version或旧索引静默替换。

关联：IF-G09, IF-G11, IF-G13。

### FR-VIDTRACE-003

来源验收：未知来源不编造候选。任务：T089, T162；能力：M22。

入口：searchVideo；结果：getSearchJob。身份：M22 payload / SourceMatch per-segment range。

逐查询片段保存来源资产、源区间和验证证据；多源拼接允许多个来源及unknown_ranges。A—拼接Q—B的片段关系不推导A与B整内容同源。

关联：IF-G09, IF-G11, IF-G13。

### FR-ORIGIN-001

来源验收：不跨未验证簇排序。任务：T090, T164；能力：M23。

入口：createTask；结果：仍缺完整读取。身份：M23.payload.relations / content_cluster.cluster_id / cluster_member。

M23只输出关系，未返回cluster_id/成员簇。候选应用事务按当前案件验证full_copy后生成UUID并落content_cluster/cluster_member，部分包含不合并；任务到簇及成员读取接口仍缺。已移除将getFirstSource当聚类完整读取的映射。

关联：IF-G09, IF-G11, IF-G13。

### FR-ORIGIN-002

来源验收：候选绑定真实时间证据。任务：T091, T092, T093, T165；能力：M24。

入口：createTask；结果：getFirstSource。身份：FirstSource.ranking_id / task_id / run_version / result_version / cluster_id。

M24输出簇内候选，应用分配ranking_id并保存不可变批次。cluster_id指真实簇，asset_id必须同案同簇，rank为连续1..candidate_count且最多3；rank不是发布时间。指定ranking_id读取，概率不是原创确定性。

关联：IF-G09, IF-G11, IF-G13。

### FR-ORIGIN-003

来源验收：无法确认保留未知状态。任务：T091, T092, T093；能力：M24。

入口：createTask；结果：getFirstSource。身份：FirstSource.evidence_ids / counter_evidence_ids / coverage_note / status。

支持与反对证据分开；published_at来自可核验发布时间，discovered_at不可自动代替。真值/覆盖不足保留insufficient、未知发布时间/概率可null，不凑满3条且不跨簇补候选。

关联：IF-G09, IF-G11, IF-G13。

### FR-PROPAGATION-001

来源验收：推断边标概率与证据。任务：T094, T095, T096；能力：M26, M27。

入口：createTask；结果：getPropagation。身份：Graph.cluster_id / version / GraphEdge.origin / probability / evidence_ids。

M26/M27与普通图处理分工；observed来自记录，inferred带模型与证据，human来自复核记录。图快照按版本固定，当前Graph缺完整task/run/result绑定，不能把候选边当事实传播。

关联：IF-G09, IF-G11, IF-G13。

### FR-PROPAGATION-002

来源验收：时间方向和关系来源可查。任务：T095, T097；能力：M26。

入口：createTask；结果：getPropagation。身份：Graph.version / GraphNode / GraphEdge。

展示的是指定图版本的时间线与版本差异；关系时间不能仅用数据库created_at代替发布时间/观察时间。当前响应未定义前后版本差异投影与完整来源时间字段，登记为未覆盖。

关联：IF-G09, IF-G11, IF-G13。

### FR-PROPAGATION-003

来源验收：更正关系保存新版本。任务：T096, T097, T102；能力：M26, M27。

入口：decidePropagationEdge, createReview；结果：decidePropagationEdge, getPropagation。身份：GraphDecision / GraphEdge.version / Review.review_version。

人工确认/驳回只改明确edge_id和期望版本；理由/证据/审批按适用规则处理。原边与模型概率保留，产生新关系版本和审计；getPropagation不能代替复核待办读取。

关联：IF-G02, IF-G03, IF-G09, IF-G12。

### FR-CLAIM-001

来源验收：主张关联来源片段。任务：T098, T166, T167；能力：M28。

入口：extractClaims；结果：extractClaims。身份：ClaimList.claims / Claim.claim_id / source segment。

当前契约同步返回ClaimList，结果从同次响应读取；已移除getReport映射。M28抽取主体、事件、时间地点等字段并绑定来源片段；后续历史claim查询尚无专用契约。

关联：IF-G09, IF-G13。

### FR-CLAIM-002

来源验收：不足证据保留不足状态。任务：T099, T168；能力：M29。

入口：verifyClaim；结果：verifyClaim。身份：Relation.claim_id / relation / evidence_ids / model_version。

当前同步返回Relation，结果从同次响应读取；白名单检索与M29关系判断分别校验，已移除getReport映射。本轮已修正Relation及M29/inference：insufficient允许空证据，其他关系仍要求证据；持久化无证据状态存于固定task_result摘要且不虚构关系行，实际服务联调仍未完成。

关联：IF-G09, IF-G13。

### FR-CLAIM-003

来源验收：无有效依据句不进入报告。任务：T106, T169；能力：M30。

入口：createReportDraft；结果：getReport。身份：Report.report_id / state / evidence_ids / ObjectRef。

M30生成带引用摘要，报告草稿受理后查report_id终态；DRAFT/READY与正式批准不同。句级引用必须语义支持且固定版本；只有ID存在/JSON合法不能证明内容可入报告。

关联：IF-G09, IF-G13。

### FR-REVIEW-001

来源验收：复核绑定结果版本。任务：T100, T101, T102, T103, T108；能力：普通处理，无模型绑定。

入口：createReview, requestApproval, decideApproval, requestFeedback；结果：createReview, requestApproval, decideApproval, getTaskEvidence。身份：Review task/run/result/review_version / Approval / FeedbackRecord。

提交响应可读但缺工作台/审批/反馈历史查询；退回补证和request_rerun按不同动作办理，重算产生新运行/结果版本而不覆盖旧意见。反馈不等于已获训练用途授权。

关联：IF-G02, IF-G03, IF-G04, IF-G09, IF-G12。

### FR-REVIEW-002

来源验收：原件与固化内容不可普通覆盖。任务：T104, T105；能力：普通处理，无模型绑定。

入口：sealEvidence；结果：sealEvidence。身份：EvidencePackage.package_id / version / manifest_sha256 / manifest。

固化响应包含清单；固定证据ObjectRef.version_id及摘要，保留包版本。现有接口缺包列表/历史详情/签验读取，不借用报告读取；mock/not_signed状态不得表述为正式签验通过。

关联：IF-G09。

### FR-REVIEW-003

来源验收：导出受权限审批并留痕。任务：T106, T107；能力：M30。

入口：createReportDraft, createReport；结果：getReport, downloadReport。身份：Report.report_id / run_version / result_version / approval_id / object_ref。

草稿和正式报告生成分开；READY仅产物生成成功，导出仍校验当前权限、目的及有效批准。旧批准不随重算继承；下载绑定固定产物版本，撤销后下一Range拒绝。

关联：IF-G02, IF-G09, IF-G12。

### FR-OPS-001

来源验收：配置变更追踪及授权。任务：T011, T012, T013, T014, T016, T017, T018, T051, T052, T058, T060, T061；能力：普通处理，无模型绑定。

入口：registerModel, recordEvaluation, createPolicy, requestApproval, decideApproval；结果：listModels, listEvaluations, listPolicies, listAuditEvents。身份：Model / Evaluation / Policy / Approval。

按管理对象分别配置和查询；开发devLogin不是正式身份接入，rolloutModel为发布动作且不是标签配置入口。角色/阈值激活撤销及管理API责任仍待定；不混同组织权限与案件数据范围。

关联：IF-G02, IF-G05, IF-G06, IF-G07, IF-G12。

### FR-OPS-002

来源验收：指标异常能诊断。任务：T035, T040, T055, T056, T059, T117, T118, T119, T120；能力：普通处理，无模型绑定。

入口：listTasks, getTask, getModelHealth；结果：listTasks, getTask, getModelHealth。身份：Task.state / nodes / Health。

只读任务/模型健康有契约；cancelTask/rerunTask为独立控制动作，已移出监控读入口。GPU、队列、存储、索引监控目前由运维指标规划，不能把Health当全量监控或任务完成证据。

关联：IF-G05, IF-G11, IF-G13。

### FR-OPS-003

来源验收：回滚恢复有版本和演练记录。任务：T057, T060, T121, T122, T123, T124, T170；能力：M34。

入口：rolloutModel；结果：listModels, getModelHealth。身份：ActionAck.object_id / release_bundle / Model.version。

rolloutModel含灰度/rollback，但202后的操作终态查询仍缺，健康只能旁证；备份恢复是受控离线运维流程，M34运行转换不代表所有包可部署。数据库/对象/模型/索引/密钥恢复分别对账。

关联：IF-G05, IF-G13。

## 实施与关闭

技术语义复核已执行；发现的接口/字段差异由[结果身份与投影](../05-workflows/result-identity-and-projection.md)及[接口缺口](../03-api/interface-gap-register.md)逐项承接。每个运行任务需正例、异常、权限撤销、两次重算与精确历史选择验证后关闭。当前没有将34能力、53操作或170任务标为业务完成。
