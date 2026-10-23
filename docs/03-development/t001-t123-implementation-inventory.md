# T001—T123开发任务、数据表、接口与方法落实清单

自动生成：`python scripts/generate_development_inventory.py`；漂移检查：同命令加`--check`。不得独立修改派生结果。

任务台账日期：2026-10-23。本清单只读取代码、契约、迁移及现存台账，不连接数据库、不执行迁移、不导入业务代码。

全部170任务：154条已验证子步骤、622条剩余工作、0项整任务验收。T001—T123：154条已验证子步骤、434条剩余工作、0项整任务验收。三种计数单位不同，不据此计算任务完成率。

T001—T123声明55张不同表、53个不同操作ID；完整业务契约含73个操作，当前源码显式注册其中51个，尚有22个未注册；内部推理契约/源码另计1/1。当前版本迁移中发现70张表定义、36个不同SQL函数名称。

后端Python静态索引包含585个函数/方法定义，其中69个在直接SQL字面量中引用已定义表。完整限定名、参数名与位置见机器清单的`backend_python_method_source_index`；下方按任务列出与声明表直接相交的方法。动态SQL、间接调用和服务转发不作推断，未列出不代表没有方法实现。

已有表定义不等于目标库已创建；路由与Python方法存在不等于运行服务已部署或业务成功。所有当前实际状态沿用任务台账，不自动接受任务。未知负责人保持未确定。

当前环境沿用Linux、Miniforge py310和CPU；Python候选继续暂缓，原任务卡的历史Python版本仅保留来源。`health`可位于独立PoC入口；历史`devLogin`不能作为新增密码登录的授权。

完整字段、原验收和测试要求、完成证据、逐项剩余工作及来源SHA-256见[机器清单](t001-t123-implementation-inventory.json)。[实施顺序](t001-t123-development-sequence.md)与[本批读取实现计划](t001-t123-catalog-read-implementation-plan.md)分别记录开发安排和具体修改边界。

## 123项任务导航

| 任务与源名称 | 当前状态 | 已验证子步/剩余 | 数据表 | 声明接口中已有业务注册/总数 |
| --- | --- | --- | --- | --- |
| [T001 建立单仓库目录与基础README](#t001) | 部分已验证 | 4/2 | 未声明直接落库 | 0/0 |
| [T002 配置Python后端工程](#t002) | 部分已验证 | 4/2 | 未声明直接落库 | 0/1 |
| [T003 配置Vue前端工程](#t003) | 部分已验证 | 2/2 | 未声明直接落库 | 0/1 |
| [T004 建立本地容器开发环境](#t004) | 部分已验证 | 5/3 | 未声明直接落库 | 0/1 |
| [T005 配置代码格式化与静态检查](#t005) | 部分已验证 | 4/2 | 未声明直接落库 | 0/0 |
| [T006 建立基础持续集成流水线](#t006) | 部分已验证 | 4/3 | 未声明直接落库 | 0/0 |
| [T007 建立统一配置和密钥规范](#t007) | 部分已验证 | 2/2 | 未声明直接落库 | 0/0 |
| [T008 建立统一日志与请求追踪](#t008) | 部分已验证 | 3/2 | 未声明直接落库 | 0/0 |
| [T009 建立统一异常与错误码框架](#t009) | 部分已验证 | 2/2 | 未声明直接落库 | 0/0 |
| [T010 建立架构决策记录和变更模板](#t010) | 部分已验证 | 2/2 | 未声明直接落库 | 0/0 |
| [T011 设计用户角色与数据范围模型](#t011) | 部分已验证 | 5/3 | 未声明直接落库 | 0/0 |
| [T012 实现用户角色数据库模型](#t012) | 部分已验证 | 6/3 | users、roles、permissions、user_roles | 0/0 |
| [T013 实现认证与令牌校验](#t013) | 部分已验证 | 13/3 | case_membership、user_roles、users | 1/2 |
| [T014 实现接口级权限控制](#t014) | 部分已验证 | 13/3 | case_membership、user_roles、users | 1/1 |
| [T015 实现数据范围访问控制](#t015) | 部分已验证 | 4/3 | case_membership、user_roles、users | 1/1 |
| [T016 实现高风险操作二次确认](#t016) | 部分已验证 | 4/4 | approval_decision、approval_request、audit_event、operation_token | 3/3 |
| [T017 实现操作审计事件模型](#t017) | 部分已验证 | 1/3 | audit_event | 0/0 |
| [T018 开发审计查询页面与接口](#t018) | 部分已验证 | 2/3 | audit_event、audit_export | 2/2 |
| [T019 设计内容与媒体资产模型](#t019) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T020 实现内容与媒体资产表](#t020) | 部分已验证 | 1/3 | source_registry、content_item、media_asset、asset_lineage | 0/0 |
| [T021 实现数据来源授权登记](#t021) | 部分已验证 | 6/3 | source_registry | 2/2 |
| [T022 实现分片上传初始化](#t022) | 部分已验证 | 2/3 | source_registry、upload_session | 1/1 |
| [T023 实现分片接收与校验](#t023) | 部分已验证 | 2/3 | upload_part、upload_session | 1/1 |
| [T024 实现分片合并与完整哈希](#t024) | 部分已验证 | 5/3 | media_asset、upload_part、upload_session | 1/1 |
| [T025 实现MinIO对象存储适配器](#t025) | 部分已验证 | 2/3 | audit_event、media_asset、object_version | 1/1 |
| [T026 实现媒体格式探测与安全校验](#t026) | 部分已验证 | 1/3 | media_asset、upload_part、upload_session | 1/1 |
| [T027 实现SHA-256完全重复检测](#t027) | 部分已验证 | 2/3 | media_asset、upload_part、upload_session | 1/1 |
| [T028 实现批量清单导入](#t028) | 部分已验证 | 1/3 | import_item、import_job | 2/2 |
| [T029 实现第三方接入适配器协议](#t029) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T030 开发媒体资产管理页面](#t030) | 部分已验证 | 6/4 | asset_lineage、audit_event、media_asset、object_version | 3/3 |
| [T031 设计分析任务与节点执行模型](#t031) | 部分已验证 | 2/3 | 未声明直接落库 | 0/0 |
| [T032 实现任务及节点数据库模型](#t032) | 部分已验证 | 2/3 | analysis_task、task_node_run、task_event | 0/0 |
| [T033 实现任务状态机](#t033) | 部分已验证 | 2/3 | 未声明直接落库 | 0/0 |
| [T034 实现任务创建接口](#t034) | 部分已验证 | 4/4 | analysis_task、idempotency_record、outbox_event | 0/1 |
| [T035 实现任务查询和进度接口](#t035) | 部分已验证 | 2/3 | analysis_task、task_node_run | 2/2 |
| [T036 实现异步队列与优先级](#t036) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T037 实现DAG任务编排器](#t037) | 尚无充分已验证交付 | 0/4 | report | 0/0 |
| [T038 实现节点级重试与检查点](#t038) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T039 实现任务取消和退回重算](#t039) | 部分已验证 | 2/3 | analysis_task、outbox_event、task_event、task_run | 1/2 |
| [T040 开发任务监控页面](#t040) | 部分已验证 | 2/4 | analysis_task、outbox_event、task_event、task_node_run、task_run | 3/4 |
| [T041 实现图片元数据解析](#t041) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T042 实现视频ffprobe解析](#t042) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T043 实现标准化媒体副本生成](#t043) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T044 实现镜头边界检测](#t044) | 尚无充分已验证交付 | 0/4 | shot | 0/0 |
| [T045 实现固定间隔抽帧](#t045) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T046 实现镜头代表帧选择](#t046) | 尚无充分已验证交付 | 0/4 | keyframe | 0/0 |
| [T047 实现音轨与字幕提取](#t047) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T048 接入OCR并建立时间片段](#t048) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T049 接入ASR并建立时间片段](#t049) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T050 实现媒体统一时间轴服务](#t050) | 尚无充分已验证交付 | 0/4 | keyframe、media_asset、shot、text_segment | 1/1 |
| [T051 定义统一模型输入输出契约](#t051) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T052 实现模型注册表](#t052) | 部分已验证 | 1/4 | model_registry | 1/2 |
| [T053 实现统一推理网关](#t053) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T054 实现HTTP与本地Mock适配器](#t054) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T055 实现推理批处理与GPU队列](#t055) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T056 实现模型健康检查与熔断](#t056) | 尚无充分已验证交付 | 0/4 | model_registry | 0/1 |
| [T057 实现模型灰度发布](#t057) | 尚无充分已验证交付 | 0/4 | approval_request、index_registry、model_release | 0/1 |
| [T058 实现模型评测记录管理](#t058) | 部分已验证 | 1/4 | model_evaluation | 1/2 |
| [T059 实现输入输出漂移监测](#t059) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T060 开发模型运维页面](#t060) | 部分已验证 | 1/4 | approval_request、index_registry、model_registry、model_release | 1/3 |
| [T061 定义风险标签和版本管理](#t061) | 尚无充分已验证交付 | 0/4 | policy_registry | 2/2 |
| [T062 接入图片多标签分类模型](#t062) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T063 接入敏感目标检测模型](#t063) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T064 接入视频行为识别模型](#t064) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T065 接入音频事件识别模型](#t065) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T066 实现多模态时间对齐](#t066) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T067 实现跨模态矛盾检测](#t067) | 尚无充分已验证交付 | 0/4 | claim | 0/0 |
| [T068 实现综合风险融合与校准](#t068) | 尚无充分已验证交付 | 0/4 | policy_registry | 2/2 |
| [T069 实现风险转人工规则](#t069) | 尚无充分已验证交付 | 0/4 | policy_registry | 2/2 |
| [T070 开发风险识别研判界面](#t070) | 尚无充分已验证交付 | 0/4 | finding_evidence、risk_finding | 1/1 |
| [T071 实现图片取证基础特征](#t071) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T072 接入图片篡改区域模型](#t072) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T073 实现复制粘贴与局部生成分类](#t073) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T074 实现视频时间结构异常检测](#t074) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T075 实现视频空间篡改跟踪](#t075) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T076 接入深度伪造与音画同步检测](#t076) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T077 实现篡改多证据融合](#t077) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T078 开发篡改取证界面](#t078) | 尚无充分已验证交付 | 0/4 | finding_evidence、tamper_finding | 1/1 |
| [T079 实现图片感知哈希特征](#t079) | 尚无充分已验证交付 | 0/4 | feature | 0/0 |
| [T080 实现视觉与复制检测向量生成](#t080) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T081 建立Milvus索引与版本管理](#t081) | 部分已验证 | 1/3 | audit_event、index_registry | 0/2 |
| [T082 实现图片多路候选召回](#t082) | 尚无充分已验证交付 | 0/4 | index_registry、media_asset、search_job、source_match | 0/2 |
| [T083 实现局部特征提取与匹配](#t083) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T084 实现RANSAC几何验证](#t084) | 尚无充分已验证交付 | 0/4 | index_registry、media_asset、source_match | 0/1 |
| [T085 实现图片局部区域检索](#t085) | 尚无充分已验证交付 | 0/4 | index_registry、media_asset、search_job、source_match | 0/3 |
| [T086 实现视频帧检索候选聚合](#t086) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T087 实现视频相似度矩阵构建](#t087) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T088 实现局部DTW与倒放对齐](#t088) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T089 实现多源拼接来源映射](#t089) | 尚无充分已验证交付 | 0/4 | index_registry、search_job、source_match | 0/2 |
| [T090 实现高可信同源内容聚类](#t090) | 尚无充分已验证交付 | 0/4 | content_cluster、cluster_member | 0/0 |
| [T091 实现首发排序特征工程](#t091) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T092 训练和注册首发排序模型](#t092) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T093 实现首发候选查询服务](#t093) | 部分已验证 | 1/3 | cluster_member、content_cluster、first_source_candidate | 1/1 |
| [T094 设计传播图谱数据模型](#t094) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T095 实现传播图谱写入与查询](#t095) | 尚无充分已验证交付 | 0/4 | propagation_edge、propagation_node | 1/1 |
| [T096 实现隐式传播关系推断](#t096) | 尚无充分已验证交付 | 0/4 | propagation_edge、review_record | 0/1 |
| [T097 开发传播时间线和图谱界面](#t097) | 尚无充分已验证交付 | 0/4 | propagation_edge、propagation_node、review_record | 1/2 |
| [T098 实现结构化主张抽取服务](#t098) | 尚无充分已验证交付 | 0/4 | claim、text_segment | 0/1 |
| [T099 实现权威证据检索与关系判断](#t099) | 尚无充分已验证交付 | 0/4 | claim、claim_evidence_relation | 0/1 |
| [T100 实现统一证据对象模型](#t100) | 尚无充分已验证交付 | 0/4 | evidence_item | 0/0 |
| [T101 实现风险与取证证据卡片接口](#t101) | 部分已验证 | 2/3 | evidence_item、task_evidence | 1/1 |
| [T102 实现人工复核工作流](#t102) | 部分已验证 | 1/3 | approval_decision、approval_request、audit_event、policy_registry、propagation_edge、review_evidence、review_record | 4/5 |
| [T103 开发人工复核工作台](#t103) | 部分已验证 | 6/3 | audit_event、evidence_item、review_evidence、review_record、task_evidence | 2/2 |
| [T104 实现证据固化与完整性校验](#t104) | 尚无充分已验证交付 | 0/4 | audit_event、evidence_package、object_version、package_item | 0/1 |
| [T105 实现可信时间与签名适配层](#t105) | 尚无充分已验证交付 | 0/4 | audit_event、evidence_package、object_version、package_item | 0/1 |
| [T106 实现证据约束核查摘要](#t106) | 尚无充分已验证交付 | 0/4 | report、report_evidence | 0/1 |
| [T107 实现核查报告生成](#t107) | 部分已验证 | 1/4 | approval_request、audit_event、report、report_evidence | 1/3 |
| [T108 实现样本纠错与回流审批](#t108) | 部分已验证 | 1/3 | approval_decision、approval_request、audit_event、feedback_request | 2/3 |
| [T109 建立标注规范与标签质检工具](#t109) | 部分已验证 | 1/4 | 未声明直接落库 | 0/0 |
| [T110 实现原始素材分组划分](#t110) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T111 实现可控编辑数据增强流水线](#t111) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T112 建立难负样本挖掘流程](#t112) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T113 实现风险模型训练与评测流水线](#t113) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T114 实现篡改模型评测流水线](#t114) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T115 实现同源与片段检索评测流水线](#t115) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T116 实现首发和大模型核查评测](#t116) | 尚无充分已验证交付 | 0/4 | claim | 0/0 |
| [T117 建立应用安全自动化扫描](#t117) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T118 实施上传与接口安全测试](#t118) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T119 实施大模型安全测试](#t119) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T120 实现监控指标与告警](#t120) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T121 实现备份恢复与灾备演练](#t121) | 部分已验证 | 1/3 | 未声明直接落库 | 0/0 |
| [T122 执行20并发验收性能测试](#t122) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |
| [T123 执行100并发容量与长稳测试](#t123) | 尚无充分已验证交付 | 0/4 | 未声明直接落库 | 0/0 |

<a id="t001"></a>
## T001 建立单仓库目录与基础README

任务卡：[tasks/platform/T001.md](<../../tasks/platform/T001.md>)；分组：工程基础、身份权限与审计；源责任角色：架构/全栈；实际负责人：邓昀。

原工作范围：按DES-001 §8.6核验并沿用既有backend、frontend、ai-services、shared-contracts、schemas、docs、tasks、prompts、config、deploy、scripts、tests目录；仅补充获准的缺项，建立职责与原目录映射，不直接迁移。

原接口/数据约定：根目录README；目录约定docs/architecture/repository-layout.md。

源依赖：无；执行依赖候选：无；依赖是否具备仍需实际核验。

当前已验证范围：沿用既有单仓库目录，根README、职责说明和170张源任务卡已归档；目录职责、统一开发/测试/提交入口和新增变更模板已在现有导航连接核对；当前Linux目录与资料校验、文档链接检查及已知运行秘密扫描通过；台账生成器可按逐条真实证据登记完整验收，不再硬编码零项

未完成事项：当前目录、资料/链接及已知运行秘密检查已有实测；仍需徐昌胜对照本卡源标准给出实际复核决定，不把未知历史日期或工时编造为已完成。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t002"></a>
## T002 配置Python后端工程

任务卡：[tasks/platform/T002.md](<../../tasks/platform/T002.md>)；分组：工程基础、身份权限与审计；源责任角色：后端；实际负责人：邓昀。

原工作范围：建立Python 3.11项目、依赖锁定、FastAPI入口、配置管理和日志初始化。

原接口/数据约定：GET /health；环境变量Settings模型。

源依赖：T001；执行依赖候选：T001；依赖是否具备仍需实际核验。

当前已验证范围：用户指定py310下FastAPI启动、配置校验和CPU研发闭环已有实测；补齐启动profile校验、私密配置隐藏和安全结构日志，配置异常与并行关联回归已覆盖 新增独立Linux/py310业务API开发启动工具、仓库外私密配置及最小权限角色检查；实际空研发库启动并验证未认证拒绝，非业务授权或生产采用。

未完成事项：用户已明确采用Miniforge py310，源3.11偏差保留；锁和配置测试通过。按新全部原生方案补本批服务启动/配置的实际验证；正式生产解释器另行验收。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `health` | `GET /api/v1/health` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t003"></a>
## T003 配置Vue前端工程

任务卡：[tasks/frontend/T003.md](<../../tasks/frontend/T003.md>)；分组：工程基础、身份权限与审计；源责任角色：前端；实际负责人：邓昀。

原工作范围：建立Vue 3、TypeScript、Vite、路由、状态管理和API客户端。

原接口/数据约定：前端/health页面调用GET /health。

源依赖：T001；执行依赖候选：T001；依赖是否具备仍需实际核验。

当前已验证范围：Vue3/TypeScript/Vite、API客户端、严格类型检查及页面冒烟已有开发证据；实现路由、内存共享状态、真实健康页、安全API基地址和同源代理；加入lint/格式/类型及真实浏览器回归

未完成事项：研发前端单元、类型、构建及浏览器检查通过；本批全部原生方案切换后复验API地址与网关。未来业务页面和正式身份UI按后续任务交付。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `health` | `GET /api/v1/health` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t004"></a>
## T004 建立本地容器开发环境

任务卡：[tasks/platform/T004.md](<../../tasks/platform/T004.md>)；分组：工程基础、身份权限与审计；源责任角色：DevOps；实际负责人：邓昀。

原工作范围：使用固定版本编排SQL、一个执行broker、对象存储、API/Web及媒体worker；缓存按需启用，全文/图/向量按能力逐项接入；不默认部署全部生产组件。

原接口/数据约定：docker compose配置；/health依赖状态。

源依赖：T002,T003；执行依赖候选：T002、T003；依赖是否具备仍需实际核验。

当前已验证范围：已有原始制品/依赖/恢复组合证据；本批9条官方源、96wheel/21826记录、18非法夹具及71项回归核验通过；八软件限定技术复核获认可。两处询问无有效许可答复，N01未整体准入

未完成事项：Python维护与9条正式处置、两项精确通知、必要软件准入决定及最终锁仍待；Python候选继续暂缓。当前无需重复授权或管理员操作，账号/服务/恢复/切换按后续N02—N07验收

未声明直接落库表，不能为填满清单自行增加数据实体。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `health` | `GET /api/v1/health` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t005"></a>
## T005 配置代码格式化与静态检查

任务卡：[tasks/platform/T005.md](<../../tasks/platform/T005.md>)；分组：工程基础、身份权限与审计；源责任角色：全栈；实际负责人：邓昀。

原工作范围：配置Ruff/Black或等价工具、mypy、ESLint、Prettier和提交前检查。

原接口/数据约定：pyproject、前端lint配置、pre-commit。

源依赖：T002,T003；执行依赖候选：T002、T003；依赖是否具备仍需实际核验。

当前已验证范围：Ruff、Python静态类型、TypeScript及pre-commit配置已有基础；ESLint/Prettier和前端类型纳入统一入口/CI；负向探针覆盖违规和缺工具；提交前入口含格式、类型和秘密检查；格式门禁改为目录覆盖，新Python模块自动进入格式和文本检查；本地/钩子实际Ruff负向与修复回归已补齐；当前Linux实际pre-commit钩子、格式、lint及类型检查均已复验通过；新增原生工具与存储就绪测试纳入同一检查范围

未完成事项：当前Linux钩子、格式/lint/类型已实际复验通过，新增检查纳入本地/CI同源入口；保留当前源码托管证据及实际复核记录。Windows仅作远程入口，不强行要求Windows原生钩子。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t006"></a>
## T006 建立基础持续集成流水线

任务卡：[tasks/platform/T006.md](<../../tasks/platform/T006.md>)；分组：工程基础、身份权限与审计；源责任角色：DevOps；实际负责人：邓昀。

原工作范围：建立后端、前端、迁移、单元测试和构建流水线。

原接口/数据约定：CI jobs：lint、typecheck、unit、build、migration-check。

源依赖：T004,T005；执行依赖候选：T004、T005；依赖是否具备仍需实际核验。

当前已验证范围：托管流水线、归档门禁和故障探针已有实测；历史32门禁及制品核对保留在具名回执；main规则engineering与普通PR失败禁止合并已有实证。当前源码CI需按资源接口/来源页面回执的精确提交重新核验，不沿用历史成功。；业务CI安全失败定位子范围：报告及标准输出保留最多20条已核对源码AST的测试函数/类选择器，剥离参数并省略异常消息、type及正文；6项新增用例含真实失败/跳过/通过子进程及37项相邻检查通过。原失败探针、1800秒上限和门禁不变；尚未定位或修复原1057项中的1项业务失败。；非超级用户0015清单断言已按真实RED/GREEN修复，原权限检查保留。；完整业务回归超时诊断已补齐：原1800秒不变，TIMEOUT/退出2及未完成明确记录；仅本次nonce、AST核对的去参数测试路径与setup/call/teardown/finished阶段可公开。59项真实子pytest/坏记录/深JSON回归、原失败探针及281文件类型/质量通过；不表示已定位性能根因或完整业务回归通过。

未完成事项：main配置及普通PR失败阻止合并已有实际证据；同PR正常恢复与清理结果见main-protection-enforcement-report.json。仍需完整绕过名单及适用平台管理权限核验，不将源码扫描当完整平台审计。；精确43e178d业务1095、T014权限1092、前端350、开发浏览器55/Compose组合56等通过，整体CI仍因Python25条、质量工具1条扫描匹配失败；Torch未覆盖。保留软件处置和Runner/Secret权限轮换、回收及平台审计要求；原锁不变，不放宽门禁，也不继承为后续T034源码通过。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t007"></a>
## T007 建立统一配置和密钥规范

任务卡：[tasks/platform/T007.md](<../../tasks/platform/T007.md>)；分组：工程基础、身份权限与审计；源责任角色：后端/DevOps；实际负责人：邓昀。

原工作范围：划分开发、测试、生产配置；密钥只从Secret或环境注入。

原接口/数据约定：Settings字段、.env.example、配置说明。

源依赖：T002,T004；执行依赖候选：T002、T004；依赖是否具备仍需实际核验。

当前已验证范围：环境示例、Git外私密配置和启动时必要配置校验已实现；development/test/production显式选择及缺失/非法配置脱敏已实现；无有效生产配置时拒绝启动

未完成事项：开发/测试配置、秘密注入与脱敏已有回归；根据全部原生方案生成新私密配置版本并核验。生产profile和正式生产轮换/撤销另行验收，不将其冒充本批研发交付。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t008"></a>
## T008 建立统一日志与请求追踪

任务卡：[tasks/platform/T008.md](<../../tasks/platform/T008.md>)；分组：工程基础、身份权限与审计；源责任角色：后端；实际负责人：邓昀。

原工作范围：统一日志和request_id，跨API、队列、节点及网关传播trace_id并关联task_id/run_version/attempt；敏感字段脱敏。

原接口/数据约定：X-Request-Id请求头；日志字段规范。

源依赖：T002；执行依赖候选：T002；依赖是否具备仍需实际核验。

当前已验证范围：PoC JSON请求日志、request_id及trace_origin传播已有验证；API结构日志、请求上下文隔离及trace_id响应头已实现，现有PoC队列/推理HTTP与上传验证消息传播关联编号；新增同事件循环8请求内部日志逐条身份核对、嵌套异常后上下文恢复、真实数据库上传事件重复消费与外层上下文隔离；三种受控错误均被测试拒绝

未完成事项：已实现API日志、队列与推理追踪回归通过；全部原生联调时复验跨进程关联和敏感字段过滤。未来完整业务DAG、采样平台及指标聚合按后续任务接入，避免无限扩大本任务。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t009"></a>
## T009 建立统一异常与错误码框架

任务卡：[tasks/platform/T009.md](<../../tasks/platform/T009.md>)；分组：工程基础、身份权限与审计；源责任角色：后端；实际负责人：邓昀。

原工作范围：实现业务异常、HTTP映射、错误码注册和统一响应。

原接口/数据约定：错误响应{code,message,request_id,details}。

源依赖：T002；执行依赖候选：T002；依赖是否具备仍需实际核验。

当前已验证范围：PoC错误响应及业务异常、参数错误和数据库错误处理已有部分实现；统一业务未知500/HTTPException/404/405及PoC错误脱敏；新增唯一错误码注册和安全回归

未完成事项：已知/未知异常、错误码唯一和脱敏回归通过；完成本批实际复核并在原生联调中回归已实现接口。后续新错误同步注册是持续维护责任。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t010"></a>
## T010 建立架构决策记录和变更模板

任务卡：[tasks/platform/T010.md](<../../tasks/platform/T010.md>)；分组：工程基础、身份权限与审计；源责任角色：架构；实际负责人：邓昀。

原工作范围：建立ADR、需求变更、模型变更和数据库变更模板。

原接口/数据约定：docs/adr与Pull Request模板。

源依赖：T001；执行依赖候选：T001；依赖是否具备仍需实际核验。

当前已验证范围：ADR文档和开发环境变更/恢复要求已归档；新增PR及需求/模型/数据库/ADR可复用模板，本批实施记录按模板核对影响、版本、验证、恢复与未验范围

未完成事项：既有模板保留并用于本次原生迁移的具体变更说明；实际复核人徐昌胜尚未登记验收决定，模板本身不产生审批。；实际负责人已指定为邓昀；仍需落实剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t011"></a>
## T011 设计用户角色与数据范围模型

任务卡：[tasks/platform/T011.md](<../../tasks/platform/T011.md>)；分组：工程基础、身份权限与审计；源责任角色：后端/安全；实际负责人：邓昀。

原工作范围：设计用户、角色、权限、单位、案件范围和数据密级模型。

原接口/数据约定：ERD；RBAC+ABAC权限矩阵。

源依赖：T002,T010；执行依赖候选：T002、T010；依赖是否具备仍需实际核验。

当前已验证范围：T002/T010本批依赖已核对；六角色/单位/案件/分类槽设计、41权限码及73操作矩阵与56项合成评审测试已有证据；身份/单位/案件关系及稳定映射增量设计已与实际数据库验证对齐

未完成事项：用户已选定六角色作为主要研发设计；具体ALLOW、职责冲突、单位案件/分类细则尚未提供，继续默认拒绝并逐项登记待决，不将候选职责映射当实际授权。；身份/权限完整运行集成按T013/T014衔接；本任务对六角色、范围模型和默认拒绝进行本批复核，后续业务能力不能被提前计为实现。；实际负责人已指定为邓昀；仍需补充权限矩阵复核记录，逐项对照源验收标准；当前候选设计与测试不能替代正式输入或整任务验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t012"></a>
## T012 实现用户角色数据库模型

任务卡：[tasks/platform/T012.md](<../../tasks/platform/T012.md>)；分组：工程基础、身份权限与审计；源责任角色：后端；实际负责人：徐昌胜。

原工作范围：实现用户、角色、权限和关联表及迁移。

原接口/数据约定：users、roles、permissions、user_roles。

源依赖：T011；执行依赖候选：T011；依赖是否具备仍需实际核验。

当前已验证范围：身份/单位/案件及角色权限关联模型、0001—0005迁移和受限内部DAO已实现；唯一/外键/软禁用/升级及恢复研发验证通过，另建63表843字段空库

未完成事项：模型、约束、迁移和恢复研发证据已存在；对照本卡原验收逐项复核。实际人员管理HTTP与运行授权按T013/T014/T017交付，不用未来接口替代当前模型测试。；现有业务研发数据库已为Linux原生，按新原生整体方案核对其工具/配置/数据目录和托管恢复；角色变更/撤销整链仍按T013/T014联调。；实际负责人已指定为徐昌胜；逐项记录本任务原验收标准的实测结论、实际复核及剩余工作，不以负责人登记代替验收。

表与创建源码：

- `mt.users`：用户与认证主体；[backend/business_migrations/0001_business_baseline.sql:166](<../../backend/business_migrations/0001_business_baseline.sql#L166>)。本清单不证明运行库已采用。
- `mt.roles`：角色目录；[backend/business_migrations/0001_business_baseline.sql:35](<../../backend/business_migrations/0001_business_baseline.sql#L35>)。本清单不证明运行库已采用。
- `mt.permissions`：权限目录；[backend/business_migrations/0001_business_baseline.sql:23](<../../backend/business_migrations/0001_business_baseline.sql#L23>)。本清单不证明运行库已采用。
- `mt.user_roles`：用户角色绑定；[backend/business_migrations/0001_business_baseline.sql:428](<../../backend/business_migrations/0001_business_baseline.sql#L428>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.identity.directory.IdentityDirectory.user_state(self, user_id)`；[backend/business_app/identity/directory.py:195](<../../backend/business_app/identity/directory.py#L195>)；表：users。
- `business_app.identity.directory.IdentityDirectory.permission_bindings(self, user_id)`；[backend/business_app/identity/directory.py:260](<../../backend/business_app/identity/directory.py#L260>)；表：permissions、roles、user_roles、users。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t013"></a>
## T013 实现认证与令牌校验

任务卡：[tasks/platform/T013.md](<../../tasks/platform/T013.md>)；分组：工程基础、身份权限与审计；源责任角色：后端/安全；实际负责人：徐昌胜。

原工作范围：实现统一认证适配层、访问令牌验证和会话失效。

原接口/数据约定：POST /auth/login（开发适配器）；GET /auth/me。

源依赖：T012；执行依赖候选：T012；依赖是否具备仍需实际核验。

当前已验证范围：认证/轮换/故障拒绝和隔离MFA管理已有研发证据；本人两E解密/同U盘恢复、第二轮签名保护/真实签名/新备份恢复，以及四份已知旧导出的加密归档和限定逻辑退役实核通过。 本人实名管理员、首次改密/OTP、专用PKCE/签名MFA管理会话及临时令牌文件清理已实核。 本人另已确认仅密码不能进入控制台、单次错误OTP被拒绝，登记为本人实测反馈。

未完成事项：第二独立介质暂无、离线私钥兼容真实身份恢复、恢复后旧凭据失效、共享bootstrap退役/受控回切，以及软件准入和实际整卡验收仍待。 本批仅补安全诊断，不关闭上述条件。

表与创建源码：

- `mt.case_membership`：显式案件授权；[backend/business_migrations/0001_business_baseline.sql:235](<../../backend/business_migrations/0001_business_baseline.sql#L235>)。本清单不证明运行库已采用。
- `mt.user_roles`：用户角色绑定；[backend/business_migrations/0001_business_baseline.sql:428](<../../backend/business_migrations/0001_business_baseline.sql#L428>)。本清单不证明运行库已采用。
- `mt.users`：用户与认证主体；[backend/business_migrations/0001_business_baseline.sql:166](<../../backend/business_migrations/0001_business_baseline.sql#L166>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.identity.directory.IdentityDirectory.user_state(self, user_id)`；[backend/business_app/identity/directory.py:195](<../../backend/business_app/identity/directory.py#L195>)；表：users。
- `business_app.identity.directory.IdentityDirectory.permission_bindings(self, user_id)`；[backend/business_app/identity/directory.py:260](<../../backend/business_app/identity/directory.py#L260>)；表：user_roles、users。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `devLogin` | `POST /api/v1/auth/login` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `getCurrentUser` | `GET /api/v1/auth/me` | 无 | `current_user`；[backend/business_app/controls/router.py:327](<../../backend/business_app/controls/router.py#L327>) |


<a id="t014"></a>
## T014 实现接口级权限控制

任务卡：[tasks/platform/T014.md](<../../tasks/platform/T014.md>)；分组：工程基础、身份权限与审计；源责任角色：后端/安全；实际负责人：徐昌胜。

原工作范围：实现路由权限装饰器和最小权限校验。

原接口/数据约定：require_permission(permission_code)。

源依赖：T012,T013；执行依赖候选：T012、T013；依赖是否具备仍需实际核验。

当前已验证范围：原统一权限四项及P01—P07隔离实现/实际回归/CI/源码交付已验证；完整回归1009项通过，246格逻辑、真实SQL/对象/独立人员审批、事务撤销、工作节点和交付证据分别列明；最终复核7项问题已按实际测试修复。；以内容摘要缓存已校验权限目录，保留每次真实文件读取、变更/缺失拒绝、身份事实不缓存；13项缓存与205项旧权限纯回归通过；首轮843项完整回归在约551秒内结束，保留1项旧注册清单断言失败及修复。最终完整门禁与CI结果按专项回执单列，未放宽原1200秒限制或246格规则。；四个既有接口接入统一权限与范围：下载用途及分类、来源登记的独立权威证明、单位内模型/评测集合逐条过滤和提交前复核；原246格、旧迁移和原CI超时保留，完整门禁及托管结果另见本批回执。

未完成事项：正式分类/用途/人员、工作委托和独立服务身份提供者、共享迁移/策略采用、T013真实身份恢复及旧凭据失效/退役、22未挂载操作及正式验收另列；不以本批通过关闭整任务。

表与创建源码：

- `mt.case_membership`：显式案件授权；[backend/business_migrations/0001_business_baseline.sql:235](<../../backend/business_migrations/0001_business_baseline.sql#L235>)。本清单不证明运行库已采用。
- `mt.user_roles`：用户角色绑定；[backend/business_migrations/0001_business_baseline.sql:428](<../../backend/business_migrations/0001_business_baseline.sql#L428>)。本清单不证明运行库已采用。
- `mt.users`：用户与认证主体；[backend/business_migrations/0001_business_baseline.sql:166](<../../backend/business_migrations/0001_business_baseline.sql#L166>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.identity.directory.IdentityDirectory.user_state(self, user_id)`；[backend/business_app/identity/directory.py:195](<../../backend/business_app/identity/directory.py#L195>)；表：users。
- `business_app.identity.directory.IdentityDirectory.permission_bindings(self, user_id)`；[backend/business_app/identity/directory.py:260](<../../backend/business_app/identity/directory.py#L260>)；表：user_roles、users。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getCurrentUser` | `GET /api/v1/auth/me` | 无 | `current_user`；[backend/business_app/controls/router.py:327](<../../backend/business_app/controls/router.py#L327>) |


<a id="t015"></a>
## T015 实现数据范围访问控制

任务卡：[tasks/platform/T015.md](<../../tasks/platform/T015.md>)；分组：工程基础、身份权限与审计；源责任角色：后端/安全；实际负责人：徐昌胜。

原工作范围：按单位、案件、任务和密级过滤查询与写入。

原接口/数据约定：DataScope对象；repository查询约束。

源依赖：T014；执行依赖候选：T014；依赖是否具备仍需实际核验。

当前已验证范围：S01—S09和第33门禁解析器已有验证；此前128项CLI保留为历史，本批隔离完整T015入口131项通过，预期失败探针退出1已核验；T0141092/T016187和29项迁移/owner/契约检查在各自回执单列，不混算独立测试总数。

未完成事项：现有T015严格入口131项及对应故障探针已通过；继续逐项核对P02/P04/P05源计划覆盖和真实提供者/全部DAO路径，补共享采用、真实身份联调及整卡验收。当前托管CI按精确提交独立核验。；权威身份/案件映射联调后做全路径越权回归，不以数据库上下文充当身份认证；徐昌胜已由本人明确指定为开发负责人和复核人；剩余工时、实际实施日期及复核决定仍待。对照本卡源依赖、适用外部条件和验收标准记录实际结果；姓名登记不关闭代码/测试缺口，同人兼任不当作独立双人复核。

表与创建源码：

- `mt.case_membership`：显式案件授权；[backend/business_migrations/0001_business_baseline.sql:235](<../../backend/business_migrations/0001_business_baseline.sql#L235>)。本清单不证明运行库已采用。
- `mt.user_roles`：用户角色绑定；[backend/business_migrations/0001_business_baseline.sql:428](<../../backend/business_migrations/0001_business_baseline.sql#L428>)。本清单不证明运行库已采用。
- `mt.users`：用户与认证主体；[backend/business_migrations/0001_business_baseline.sql:166](<../../backend/business_migrations/0001_business_baseline.sql#L166>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.identity.directory.IdentityDirectory.user_state(self, user_id)`；[backend/business_app/identity/directory.py:195](<../../backend/business_app/identity/directory.py#L195>)；表：users。
- `business_app.identity.directory.IdentityDirectory.permission_bindings(self, user_id)`；[backend/business_app/identity/directory.py:260](<../../backend/business_app/identity/directory.py#L260>)；表：user_roles、users。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getCurrentUser` | `GET /api/v1/auth/me` | 无 | `current_user`；[backend/business_app/controls/router.py:327](<../../backend/business_app/controls/router.py#L327>) |


<a id="t016"></a>
## T016 实现高风险操作二次确认

任务卡：[tasks/platform/T016.md](<../../tasks/platform/T016.md>)；分组：工程基础、身份权限与审计；源责任角色：前后端/安全；实际负责人：徐昌胜。

原工作范围：对批量导出、删除、证据解封和模型上线增加二次确认或审批钩子。

原接口/数据约定：POST /approvals；operation_token。

源依赖：T014；执行依赖候选：T014；依赖是否具备仍需实际核验。

当前已验证范围：审批后端/前端原子范围保留；新增案件令牌签发与同根消费内核，完整严格隔离结果见本批报告。

未完成事项：落实正式双人适用制度、token TTL及当前授权截止窗口、独立HMAC密钥保管/轮换/恢复，以及确认人与执行人角色关系；不把合成职责适配器当正式跨人委托。；逐项接入真实封存/报告/删除/解封/组织模型等消费者及前端；AuditExport现契约没有token字段，其公共兼容变更需另批审查。；准备真实提供方、备份恢复和0011升级窗口后另行采用；本批未迁移共享/预览库、未重启服务，真实业务E2E尚未验收。；2026-10-23两处CI迁移回归失败已用原源码实际复现并修复：非超级schema owner按既有0017安装前提接受管理员临时SET-only授权且finally撤回；旧令牌升级预期精确纳入0017。最终受影响SQL回归93项、T016专用完整门禁187项及两个原故意失败探针通过，Ruff/格式及281文件类型检查通过；范围重叠不相加。较早9项为格式冻结前源码，另列历史。本轮没有完整business/T014或新托管CI通过回执，不新增已完成子步骤，不登记整卡验收。 正式规则、真实提供方和消费者、共享采用与真实业务E2E仍待。；开发负责人和指定复核人均已确认徐昌胜；仍需实际剩余工时、本人对最终成果的复核及逐条源验收，不能仅凭CI通过关闭整卡。

表与创建源码：

- `mt.approval_decision`：审批历史决定；[backend/business_migrations/0001_business_baseline.sql:442](<../../backend/business_migrations/0001_business_baseline.sql#L442>)。本清单不证明运行库已采用。
- `mt.approval_request`：按目的独立审批申请；[backend/business_migrations/0001_business_baseline.sql:179](<../../backend/business_migrations/0001_business_baseline.sql#L179>)。本清单不证明运行库已采用。
- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.operation_token`：一次性确认授权记录；[backend/business_migrations/0001_business_baseline.sql:537](<../../backend/business_migrations/0001_business_baseline.sql#L537>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.approvals.Approvals.detail(self, connection, scope, identifier, *, lock, shared_binding)`；[backend/business_app/controls/approvals.py:109](<../../backend/business_app/controls/approvals.py#L109>)；表：approval_decision。
- `business_app.controls.approvals.Approvals.create(self, scope, body, request, key)`；[backend/business_app/controls/approvals.py:215](<../../backend/business_app/controls/approvals.py#L215>)；表：approval_request。
- `business_app.controls.approvals.Approvals.decide(self, scope, identifier, body, request, key, *, revoke)`；[backend/business_app/controls/approvals.py:248](<../../backend/business_app/controls/approvals.py#L248>)；表：approval_decision、approval_request。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event。
- `business_app.controls.operation_tokens.OperationTokens.issue(self, scope, body, request, key)`；[backend/business_app/controls/operation_tokens.py:290](<../../backend/business_app/controls/operation_tokens.py#L290>)；表：operation_token。
- `business_app.controls.operation_tokens.OperationTokens.consume(self, connection, scope, token, *, approval_id, action, object_id, object_version, request)`；[backend/business_app/controls/operation_tokens.py:382](<../../backend/business_app/controls/operation_tokens.py#L382>)；表：operation_token。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `requestApproval` | `POST /api/v1/approvals` | 无 | `request_approval`；[backend/business_app/controls/router.py:118](<../../backend/business_app/controls/router.py#L118>) |
| `decideApproval` | `POST /api/v1/approvals/{id}/decisions` | 无 | `decide_approval`；[backend/business_app/controls/router.py:129](<../../backend/business_app/controls/router.py#L129>) |
| `issueOperationToken` | `POST /api/v1/operation-tokens` | 无 | `issue_operation_token`；[backend/business_app/controls/router.py:55](<../../backend/business_app/controls/router.py#L55>) |


<a id="t017"></a>
## T017 实现操作审计事件模型

任务卡：[tasks/platform/T017.md](<../../tasks/platform/T017.md>)；分组：工程基础、身份权限与审计；源责任角色：后端；实际负责人：未确定。

原工作范围：记录登录、查询、下载、修改、审核、导出和配置变更。

原接口/数据约定：audit_event表；AuditService.append。

源依赖：T008,T012；执行依赖候选：T008、T012；依赖是否具备仍需实际核验。

当前已验证范围：已实现控制写操作的追加审计与事务失败回滚有验证

未完成事项：补登录/查询/下载/拒绝等全事件覆盖及统一关联字段；落实审计保留、管理员边界、防篡改及正式环境回归

表与创建源码：

- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t018"></a>
## T018 开发审计查询页面与接口

任务卡：[tasks/frontend/T018.md](<../../tasks/frontend/T018.md>)；分组：工程基础、身份权限与审计；源责任角色：前后端；实际负责人：未确定。

原工作范围：实现审计日志筛选、详情和受控导出。

原接口/数据约定：GET /audit/events；POST /audit/exports。

源依赖：T015,T017；执行依赖候选：T015、T017；依赖是否具备仍需实际核验。

当前已验证范围：后端审计查询、导出状态及授权下载子范围已实现 新增审计查询/详情、当前页筛选、批准绑定导出申请/状态/受控下载前端；构建及未登录页面检查通过；不是全库过滤或已批准导出成功。

未完成事项：全库时间/用户/对象筛选尚需公共契约补充，当前仅筛已返回页；前端正向业务/分页/脱敏/导出E2E、大小/失效/撤销与下载审计仍待验证。

表与创建源码：

- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.audit_export`：审计导出作业；[backend/business_migrations/0001_business_baseline.sql:465](<../../backend/business_migrations/0001_business_baseline.sql#L465>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports.create(self, scope, body, request, key)`；[backend/business_app/controls/exports.py:89](<../../backend/business_app/controls/exports.py#L89>)；表：audit_export。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event、audit_export。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.scoped_objects.ScopedObjects._export(self, connection, scope, binding)`；[backend/business_app/scoped_objects.py:123](<../../backend/business_app/scoped_objects.py#L123>)；表：audit_export。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `listAuditEvents` | `GET /api/v1/audit/events` | limit（可选）、cursor（可选）、case_id（必填） | `list_audit`；[backend/business_app/controls/router.py:250](<../../backend/business_app/controls/router.py#L250>) |
| `exportAudit` | `POST /api/v1/audit/exports` | 无 | `export_audit`；[backend/business_app/controls/router.py:267](<../../backend/business_app/controls/router.py#L267>) |


<a id="t019"></a>
## T019 设计内容与媒体资产模型

任务卡：[tasks/backend/T019.md](<../../tasks/backend/T019.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：数据/后端；实际负责人：未确定。

原工作范围：定义content_item、media_asset、source_registry和asset_lineage。

原接口/数据约定：ERD与字段字典。

源依赖：T010,T011；执行依赖候选：T010、T011；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成设计内容与媒体资产模型的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t020"></a>
## T020 实现内容与媒体资产表

任务卡：[tasks/backend/T020.md](<../../tasks/backend/T020.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：未确定。

原工作范围：创建核心表、索引和数据库迁移。

原接口/数据约定：content_item、media_asset、source_registry、asset_lineage。

源依赖：T019；执行依赖候选：T019；依赖是否具备仍需实际核验。

当前已验证范围：媒体基础表迁移及上传完成后的资产登记已实现

未完成事项：补完整媒体模型访问、查询、生命周期及约束回归；逐字段对照数据字典及API映射，不以空库建表代替业务访问实现

表与创建源码：

- `mt.source_registry`：来源与用途授权；[backend/business_migrations/0001_business_baseline.sql:405](<../../backend/business_migrations/0001_business_baseline.sql#L405>)。本清单不证明运行库已采用。
- `mt.content_item`：逻辑内容对象；[backend/business_migrations/0001_business_baseline.sql:489](<../../backend/business_migrations/0001_business_baseline.sql#L489>)。本清单不证明运行库已采用。
- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.asset_lineage`：多父对象血缘；[backend/business_migrations/0001_business_baseline.sql:670](<../../backend/business_migrations/0001_business_baseline.sql#L670>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset、source_registry。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.sync_source(request, id, body, idempotency_key)`；[backend/business_app/controls/router.py:391](<../../backend/business_app/controls/router.py#L391>)；表：source_registry。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset、source_registry。
- `business_app.source_registration.SourceRegistration.create(self, scope, body, request, key)`；[backend/business_app/source_registration.py:170](<../../backend/business_app/source_registration.py#L170>)；表：source_registry。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset、source_registry。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：source_registry。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：content_item、media_asset、source_registry。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t021"></a>
## T021 实现数据来源授权登记

任务卡：[tasks/backend/T021.md](<../../tasks/backend/T021.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：前后端；实际负责人：未确定。

原工作范围：登记来源类型、授权依据、用途、有效期和责任人。

原接口/数据约定：POST/GET /sources；来源管理页面。

源依赖：T020,T014；执行依赖候选：T020、T014；依赖是否具备仍需实际核验。

当前已验证范围：来源登记、元数据读取与管理页面已有限定证据；本批补齐授权同步的真实SQL事务、原If-Match及幂等安全和前端操作。166项来源回归、243前端单元、43浏览器通过，完整权限门禁状态另见回执，真实权威与整卡验收仍待。

未完成事项：登记、列表/详情与授权同步代码和页面已有隔离验证；继续接真实来源权威，落实来源责任人与合法用途及真实身份/权威/数据库组合联调，不把回执当当前用途授权。；补到期后台告警及与真实权威相关的完整变更追踪和运维处置；现有同步审计/状态可读不等于后台告警或已到期授权续期。；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

表与创建源码：

- `mt.source_registry`：来源与用途授权；[backend/business_migrations/0001_business_baseline.sql:405](<../../backend/business_migrations/0001_business_baseline.sql#L405>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：source_registry。
- `business_app.controls.router.sync_source(request, id, body, idempotency_key)`；[backend/business_app/controls/router.py:391](<../../backend/business_app/controls/router.py#L391>)；表：source_registry。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：source_registry。
- `business_app.source_registration.SourceRegistration.create(self, scope, body, request, key)`；[backend/business_app/source_registration.py:170](<../../backend/business_app/source_registration.py#L170>)；表：source_registry。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：source_registry。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：source_registry。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：source_registry。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createSource` | `POST /api/v1/sources` | 无 | `create_source`；[backend/business_app/source_registration_router.py:19](<../../backend/business_app/source_registration_router.py#L19>) |
| `listSources` | `GET /api/v1/sources` | limit（可选）、cursor（可选）、case_id（必填） | `list_sources`；[backend/business_app/controls/router.py:366](<../../backend/business_app/controls/router.py#L366>) |


<a id="t022"></a>
## T022 实现分片上传初始化

任务卡：[tasks/backend/T022.md](<../../tasks/backend/T022.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：未确定。

原工作范围：创建upload_session并返回分片参数。

原接口/数据约定：POST /uploads；输入filename,size,mime,sha256。

源依赖：T020,T014；执行依赖候选：T020、T014；依赖是否具备仍需实际核验。

当前已验证范围：分片上传初始化、权限和幂等约束已实现；前端上传研发子范围：已有案件/有效来源选择、有限预算文件SHA-256及精确六字段初始化已接入；身份/范围/来源到期清理和未知原请求重试已验证，不代表真实身份联调或配额并发验收。

未完成事项：本批前端初始化与预算内PNG/JPEG接线已有证据；仍需完成全部适用源参数、实际配额/并发控制及真实后端页面联调。；补实际身份、来源权威适配后的正反向验收；本批自建传输夹具不替代该验收。；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

表与创建源码：

- `mt.source_registry`：来源与用途授权；[backend/business_migrations/0001_business_baseline.sql:405](<../../backend/business_migrations/0001_business_baseline.sql#L405>)。本清单不证明运行库已采用。
- `mt.upload_session`：上传会话；[backend/business_migrations/0001_business_baseline.sql:846](<../../backend/business_migrations/0001_business_baseline.sql#L846>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：source_registry。
- `business_app.controls.router.sync_source(request, id, body, idempotency_key)`；[backend/business_app/controls/router.py:391](<../../backend/business_app/controls/router.py#L391>)；表：source_registry。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：source_registry。
- `business_app.scoped_objects.ScopedObjects._upload(self, connection, scope, binding)`；[backend/business_app/scoped_objects.py:102](<../../backend/business_app/scoped_objects.py#L102>)；表：upload_session。
- `business_app.source_registration.SourceRegistration.create(self, scope, body, request, key)`；[backend/business_app/source_registration.py:170](<../../backend/business_app/source_registration.py#L170>)；表：source_registry。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：source_registry。
- `business_app.uploads.repository.UploadRepository.session(self, scope, upload_id, connection)`；[backend/business_app/uploads/repository.py:25](<../../backend/business_app/uploads/repository.py#L25>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.create(self, scope, payload, *, idempotency_key)`；[backend/business_app/uploads/repository.py:93](<../../backend/business_app/uploads/repository.py#L93>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：source_registry、upload_session。
- `business_app.uploads.service.UploadService.scope(self, request, action, *, case_id, upload_id)`；[backend/business_app/uploads/service.py:31](<../../backend/business_app/uploads/service.py#L31>)；表：upload_session。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：source_registry、upload_session。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createUpload` | `POST /api/v1/uploads` | 无 | `create_upload`；[backend/business_app/uploads/router.py:19](<../../backend/business_app/uploads/router.py#L19>) |


<a id="t023"></a>
## T023 实现分片接收与校验

任务卡：[tasks/backend/T023.md](<../../tasks/backend/T023.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：未确定。

原工作范围：接收分片、校验长度和哈希并记录偏移。

原接口/数据约定：PUT /uploads/{id}/parts/{part_no}。

源依赖：T022；执行依赖候选：T022；依赖是否具备仍需实际核验。

当前已验证范围：分片摘要/偏移、重放及续传子范围已有真实HTTP/数据库测试；前端上传研发子范围：受业务会话保护的真实二进制分片、原字节/原键重试及完整分页/版本/逐片摘要续传核对已实现；Chrome本地接收器验证真实传输，不代表跨刷新、大文件或真实后端E2E。

未完成事项：本页保留文件的分片重试与版本/摘要核对已有证据；仍需全媒体、大文件、并发/断网及跨刷新重新选择文件后的完整绑定恢复。；完成实际配额、过期分片清理、失败恢复及源验收对照；页面重置不删除服务端旧会话。；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

表与创建源码：

- `mt.upload_part`：分片接收与校验；[backend/business_migrations/0001_business_baseline.sql:982](<../../backend/business_migrations/0001_business_baseline.sql#L982>)。本清单不证明运行库已采用。
- `mt.upload_session`：上传会话；[backend/business_migrations/0001_business_baseline.sql:846](<../../backend/business_migrations/0001_business_baseline.sql#L846>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.scoped_objects.ScopedObjects._upload(self, connection, scope, binding)`；[backend/business_app/scoped_objects.py:102](<../../backend/business_app/scoped_objects.py#L102>)；表：upload_session。
- `business_app.scoped_objects.ScopedObjects._read_binding(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:242](<../../backend/business_app/scoped_objects.py#L242>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.session(self, scope, upload_id, connection)`；[backend/business_app/uploads/repository.py:25](<../../backend/business_app/uploads/repository.py#L25>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.create(self, scope, payload, *, idempotency_key)`；[backend/business_app/uploads/repository.py:93](<../../backend/business_app/uploads/repository.py#L93>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.existing_part(self, scope, upload_id, number, sha256, size, key)`；[backend/business_app/uploads/repository.py:128](<../../backend/business_app/uploads/repository.py#L128>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.status(self, scope, upload_id)`；[backend/business_app/uploads/repository.py:231](<../../backend/business_app/uploads/repository.py#L231>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.parts(self, scope, upload_id, cursor, limit)`；[backend/business_app/uploads/repository.py:337](<../../backend/business_app/uploads/repository.py#L337>)；表：upload_part。
- `business_app.uploads.service.UploadService.scope(self, request, action, *, case_id, upload_id)`；[backend/business_app/uploads/service.py:31](<../../backend/business_app/uploads/service.py#L31>)；表：upload_session。
- `business_app.uploads.service.UploadService.put_part(self, scope, upload_id, number, data, claimed_sha, key)`；[backend/business_app/uploads/service.py:67](<../../backend/business_app/uploads/service.py#L67>)；表：upload_part。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：upload_part、upload_session。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `putUploadPart` | `PUT /api/v1/uploads/{id}/parts/{part_no}` | 无 | `put_upload_part`；[backend/business_app/uploads/router.py:26](<../../backend/business_app/uploads/router.py#L26>) |


<a id="t024"></a>
## T024 实现分片合并与完整哈希

任务卡：[tasks/backend/T024.md](<../../tasks/backend/T024.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：徐昌胜。

原工作范围：按序合并分片，计算完整SHA-256并原子完成会话。

原接口/数据约定：POST /uploads/{id}/complete。

源依赖：T023；执行依赖候选：T023；依赖是否具备仍需实际核验。

当前已验证范围：异步合并、完整性、原子状态及回执/outbox子范围已有验证；前端上传研发子范围：完整parts提交、原202回执与实际状态分离、有限轮询及COMPLETED＋VALID资产交接已实现并验证；后端worker/全媒体安全/真实恢复链路未因此通过。；worker隔离联调子范围：目标上传/单位/案件/发起人绑定在消费与ACK前核验；独立子进程配合真实RabbitMQ、随机PostgreSQL隔离库与文件对象存储，验证正常/重复交付、缺对象/整文件哈希拒绝、数据库提交后未ACK的重投重启及身份/成员/来源撤销拒绝。测试权威仅为夹具，不证明正式身份接入、常驻worker部署、全媒体安全或完整恢复验收。；以失败回归修复控制夹具正常退出泄漏，完整回归结果按专项回执分别记录。；Linux文件对象落盘屏障子范围：初始化逐级同步新目录及父目录，写入按文件→对象目录→根目录同步后才返回引用；目录同步故障不发布分片/资产回执，恢复后同请求或事件可重试。真实文件、9项RED→GREEN及相邻隔离回归有证据，不是断电、完整恢复、孤立回收或整卡验收。；真实同案件双上传的后目标先消费失败已复现后，改为v2单位/案件/上传三元组独立队列，保留目标与提交后ACK核验；两个上传可分别进展，不再由目标专属消费者取走另一上传消息。旧case队列保留、不自动搬运或清空；103项受影响隔离回归及现有失败探针、Ruff/格式/类型通过；不证明共享采用、同上传多消费者公平、毒消息处置或整卡验收。

未完成事项：仍需常驻worker运行入口、正式工作委托/身份与来源权威接入、实际对象存储组合及全媒体安全校验；本批独立进程与真实队列隔离验证不能替代共享服务部署或正式组合验收。；已验证交付绑定、提交后未ACK重投、文件/目录持久性屏障及同案件不同上传的目标队列隔离与独立进展；仍需同上传多消费者公平和并发、毒消息等待/死信处置、v2持久队列生命周期/容量与安全清理、旧case队列库存及实际迁移/回退验证、临时分片清理、硬崩溃后孤立对象识别/回收、真实文件系统故障和完整恢复组合。旧队列未自动搬运、清空或删除。；开发负责人和指定复核人均已由本人确认为徐昌胜；仍需确认剩余工时、实施日期、实际复核决定，并逐项关闭代码/测试缺口。同人兼任不算独立双人复核，角色登记不算实际验收。

表与创建源码：

- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.upload_part`：分片接收与校验；[backend/business_migrations/0001_business_baseline.sql:982](<../../backend/business_migrations/0001_business_baseline.sql#L982>)。本清单不证明运行库已采用。
- `mt.upload_session`：上传会话；[backend/business_migrations/0001_business_baseline.sql:846](<../../backend/business_migrations/0001_business_baseline.sql#L846>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset。
- `business_app.scoped_objects.ScopedObjects._upload(self, connection, scope, binding)`；[backend/business_app/scoped_objects.py:102](<../../backend/business_app/scoped_objects.py#L102>)；表：upload_session。
- `business_app.scoped_objects.ScopedObjects._read_binding(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:242](<../../backend/business_app/scoped_objects.py#L242>)；表：upload_part。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset。
- `business_app.uploads.repository.UploadRepository.session(self, scope, upload_id, connection)`；[backend/business_app/uploads/repository.py:25](<../../backend/business_app/uploads/repository.py#L25>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.create(self, scope, payload, *, idempotency_key)`；[backend/business_app/uploads/repository.py:93](<../../backend/business_app/uploads/repository.py#L93>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.existing_part(self, scope, upload_id, number, sha256, size, key)`；[backend/business_app/uploads/repository.py:128](<../../backend/business_app/uploads/repository.py#L128>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.status(self, scope, upload_id)`；[backend/business_app/uploads/repository.py:231](<../../backend/business_app/uploads/repository.py#L231>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.parts(self, scope, upload_id, cursor, limit)`；[backend/business_app/uploads/repository.py:337](<../../backend/business_app/uploads/repository.py#L337>)；表：upload_part。
- `business_app.uploads.service.UploadService.scope(self, request, action, *, case_id, upload_id)`；[backend/business_app/uploads/service.py:31](<../../backend/business_app/uploads/service.py#L31>)；表：upload_session。
- `business_app.uploads.service.UploadService.put_part(self, scope, upload_id, number, data, claimed_sha, key)`；[backend/business_app/uploads/service.py:67](<../../backend/business_app/uploads/service.py#L67>)；表：upload_part。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset、upload_part、upload_session。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `completeUpload` | `POST /api/v1/uploads/{id}/complete` | 无 | `complete_upload`；[backend/business_app/uploads/router.py:57](<../../backend/business_app/uploads/router.py#L57>) |


<a id="t025"></a>
## T025 实现MinIO对象存储适配器

任务卡：[tasks/backend/T025.md](<../../tasks/backend/T025.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：未确定。

原工作范围：封装经ADR评审的S3兼容对象产品；原MinIO任务名保留来源，社区/AIStor维护许可和业务/Milvus依赖分别核查。提供put/get/head、对象版本与摘要；逐请求撤销路径使用受控代理，不把预签名等同即时撤销。

原接口/数据约定：ObjectStore接口；put/get/head。

源依赖：T004,T024；执行依赖候选：T004、T024；依赖是否具备仍需实际核验。

当前已验证范围：PoC S3/SeaweedFS和业务独立FileStore均有开发读写/摘要验证；新增研发FileStore受控资产下载：固定对象版本/摘要/大小、案件和来源下载用途核验，完整字节校验与审计提交后才返回，支持Range/If-Range；不等于正式S3/WORM/恢复准入。

未完成事项：按适用正式存储实现版本/权限/保留及完整对象API；落实WORM/备份与生产准入；开发FileStore不等于正式证据存储

表与创建源码：

- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.object_version`：对象版本与摘要清单；[backend/business_migrations/0001_business_baseline.sql:356](<../../backend/business_migrations/0001_business_baseline.sql#L356>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset、object_version。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset、object_version。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event、object_version。
- `business_app.controls.exports.Exports.content(self, scope, identifier, request)`；[backend/business_app/controls/exports.py:228](<../../backend/business_app/controls/exports.py#L228>)；表：object_version。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset、object_version。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset、object_version。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset、object_version。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：object_version。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：object_version。
- `business_app.scoped_objects.ScopedObjects._registered(connection, scope, reference)`；[backend/business_app/scoped_objects.py:75](<../../backend/business_app/scoped_objects.py#L75>)；表：object_version。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset、object_version。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：object_version。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset、object_version。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `downloadAsset` | `GET /api/v1/assets/{id}/content` | 无 | `download_asset`；[backend/business_app/asset_download_router.py:16](<../../backend/business_app/asset_download_router.py#L16>) |


<a id="t026"></a>
## T026 实现媒体格式探测与安全校验

任务卡：[tasks/backend/T026.md](<../../tasks/backend/T026.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端/安全；实际负责人：未确定。

原工作范围：基于文件头和解码结果校验类型，接入查毒和异常压缩限制。

原接口/数据约定：MediaValidationResult；错误码MEDIA_SECURITY_REJECTED。

源依赖：T024；执行依赖候选：T024；依赖是否具备仍需实际核验。

当前已验证范围：PNG/JPEG文件头、完整解码及尺寸限制已有异常用例

未完成事项：实现查毒、异常压缩/时长预算、视频容器探测及安全解析隔离；验证查毒不可用拒绝、恶意媒体/超时/协议及网络边界；当前不能认定全媒体安全通过

表与创建源码：

- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.upload_part`：分片接收与校验；[backend/business_migrations/0001_business_baseline.sql:982](<../../backend/business_migrations/0001_business_baseline.sql#L982>)。本清单不证明运行库已采用。
- `mt.upload_session`：上传会话；[backend/business_migrations/0001_business_baseline.sql:846](<../../backend/business_migrations/0001_business_baseline.sql#L846>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset。
- `business_app.scoped_objects.ScopedObjects._upload(self, connection, scope, binding)`；[backend/business_app/scoped_objects.py:102](<../../backend/business_app/scoped_objects.py#L102>)；表：upload_session。
- `business_app.scoped_objects.ScopedObjects._read_binding(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:242](<../../backend/business_app/scoped_objects.py#L242>)；表：upload_part。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset。
- `business_app.uploads.repository.UploadRepository.session(self, scope, upload_id, connection)`；[backend/business_app/uploads/repository.py:25](<../../backend/business_app/uploads/repository.py#L25>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.create(self, scope, payload, *, idempotency_key)`；[backend/business_app/uploads/repository.py:93](<../../backend/business_app/uploads/repository.py#L93>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.existing_part(self, scope, upload_id, number, sha256, size, key)`；[backend/business_app/uploads/repository.py:128](<../../backend/business_app/uploads/repository.py#L128>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.status(self, scope, upload_id)`；[backend/business_app/uploads/repository.py:231](<../../backend/business_app/uploads/repository.py#L231>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.parts(self, scope, upload_id, cursor, limit)`；[backend/business_app/uploads/repository.py:337](<../../backend/business_app/uploads/repository.py#L337>)；表：upload_part。
- `business_app.uploads.service.UploadService.scope(self, request, action, *, case_id, upload_id)`；[backend/business_app/uploads/service.py:31](<../../backend/business_app/uploads/service.py#L31>)；表：upload_session。
- `business_app.uploads.service.UploadService.put_part(self, scope, upload_id, number, data, claimed_sha, key)`；[backend/business_app/uploads/service.py:67](<../../backend/business_app/uploads/service.py#L67>)；表：upload_part。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset、upload_part、upload_session。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `completeUpload` | `POST /api/v1/uploads/{id}/complete` | 无 | `complete_upload`；[backend/business_app/uploads/router.py:57](<../../backend/business_app/uploads/router.py#L57>) |


<a id="t027"></a>
## T027 实现SHA-256完全重复检测

任务卡：[tasks/backend/T027.md](<../../tasks/backend/T027.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：徐昌胜。

原工作范围：上传完成后查询完全相同资产并建立关联。

原接口/数据约定：POST /uploads/{id}/complete中duplicate_of仅引用当前可访问资产；跨案件同哈希不得暴露其他对象是否存在。

源依赖：T020,T24；执行依赖候选：T020、T024；依赖是否具备仍需实际核验。

当前已验证范围：案件内精确SHA重复检测及duplicate_of引用已有测试；不同上传会话完整SHA并发关联已用真实双连接复现并修复：原事务按单位/案件/实际SHA协调，获锁后单独查询；提交/回滚、两个已授权来源、跨案件/不同摘要、超时孤儿保留及重投重试7例和相邻隔离回归有证据，保留每份原件和独立资产。不等于压力、正式权威组合、分析结果复用或整卡验收。

未完成事项：已修复不同上传会话的并发SHA关联及提交/回滚/争用取消重试；仍需批量、多消费者压力/公平性与扩展身份/来源权限组合。完整Linux业务回归约1800秒后返回BLOCKED_OR_FAIL，未取得完整计数/异常类别，不将7例或92项相邻测试当全量通过。；保留独立对象/资产、同SHA跨案件不关联、两个已授权来源及撤销读取边界已有相邻证据；真实身份/来源/存储组合、对象清理和完整恢复、候选首项不可访问时的后续候选规则仍待，不复用分析结果或感知结论。；实际开发负责人和指定复核人均已确认为徐昌胜；剩余工时、实际实施日期、本人复核决定和逐项源卡验收仍待。同人兼任不等于独立双人复核，责任登记不替代验收。

表与创建源码：

- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.upload_part`：分片接收与校验；[backend/business_migrations/0001_business_baseline.sql:982](<../../backend/business_migrations/0001_business_baseline.sql#L982>)。本清单不证明运行库已采用。
- `mt.upload_session`：上传会话；[backend/business_migrations/0001_business_baseline.sql:846](<../../backend/business_migrations/0001_business_baseline.sql#L846>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset。
- `business_app.scoped_objects.ScopedObjects._upload(self, connection, scope, binding)`；[backend/business_app/scoped_objects.py:102](<../../backend/business_app/scoped_objects.py#L102>)；表：upload_session。
- `business_app.scoped_objects.ScopedObjects._read_binding(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:242](<../../backend/business_app/scoped_objects.py#L242>)；表：upload_part。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset。
- `business_app.uploads.repository.UploadRepository.session(self, scope, upload_id, connection)`；[backend/business_app/uploads/repository.py:25](<../../backend/business_app/uploads/repository.py#L25>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.create(self, scope, payload, *, idempotency_key)`；[backend/business_app/uploads/repository.py:93](<../../backend/business_app/uploads/repository.py#L93>)；表：upload_session。
- `business_app.uploads.repository.UploadRepository.existing_part(self, scope, upload_id, number, sha256, size, key)`；[backend/business_app/uploads/repository.py:128](<../../backend/business_app/uploads/repository.py#L128>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.status(self, scope, upload_id)`；[backend/business_app/uploads/repository.py:231](<../../backend/business_app/uploads/repository.py#L231>)；表：upload_part。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：upload_part、upload_session。
- `business_app.uploads.repository.UploadRepository.parts(self, scope, upload_id, cursor, limit)`；[backend/business_app/uploads/repository.py:337](<../../backend/business_app/uploads/repository.py#L337>)；表：upload_part。
- `business_app.uploads.service.UploadService.scope(self, request, action, *, case_id, upload_id)`；[backend/business_app/uploads/service.py:31](<../../backend/business_app/uploads/service.py#L31>)；表：upload_session。
- `business_app.uploads.service.UploadService.put_part(self, scope, upload_id, number, data, claimed_sha, key)`；[backend/business_app/uploads/service.py:67](<../../backend/business_app/uploads/service.py#L67>)；表：upload_part。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset、upload_part、upload_session。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `completeUpload` | `POST /api/v1/uploads/{id}/complete` | 无 | `complete_upload`；[backend/business_app/uploads/router.py:57](<../../backend/business_app/uploads/router.py#L57>) |


<a id="t028"></a>
## T028 实现批量清单导入

任务卡：[tasks/backend/T028.md](<../../tasks/backend/T028.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：未确定。

原工作范围：支持授权CSV/JSON清单和对象文件批量导入。

原接口/数据约定：POST /imports；GET /imports/{id}。

源依赖：T021,T026；执行依赖候选：T021、T026；依赖是否具备仍需实际核验。

当前已验证范围：已登记同案件/有效来源固定对象的导入事务已有验证

未完成事项：补授权CSV/JSON文件清单解析、逐条错误反馈和对象文件批量接入；补批量任务队列、错误补偿与全流程验收；已登记ObjectRef导入不等于清单文件解析完成，第三方采集另属T029

表与创建源码：

- `mt.import_item`：逐条导入结果；[backend/business_migrations/0001_business_baseline.sql:747](<../../backend/business_migrations/0001_business_baseline.sql#L747>)。本清单不证明运行库已采用。
- `mt.import_job`：批量清单导入作业；[backend/business_migrations/0001_business_baseline.sql:314](<../../backend/business_migrations/0001_business_baseline.sql#L314>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：import_item、import_job。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：import_item。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createImport` | `POST /api/v1/imports` | 无 | `create_import`；[backend/business_app/controls/router.py:513](<../../backend/business_app/controls/router.py#L513>) |
| `getImport` | `GET /api/v1/imports/{id}` | 无 | `get_import`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>) |


<a id="t029"></a>
## T029 实现第三方接入适配器协议

任务卡：[tasks/backend/T029.md](<../../tasks/backend/T029.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：后端；实际负责人：未确定。

原工作范围：定义合法授权第三方API和消息接入接口，不实现绕过访问控制逻辑。

原接口/数据约定：SourceAdapter.fetch/ack；事件Schema。

源依赖：T021；执行依赖候选：T021；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成第三方接入适配器协议的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t030"></a>
## T030 开发媒体资产管理页面

任务卡：[tasks/frontend/T030.md](<../../tasks/frontend/T030.md>)；分组：来源登记、上传、导入及媒体资源；源责任角色：前端；实际负责人：徐昌胜。

原工作范围：展示媒体元数据、版本、血缘、来源和权限状态。

原接口/数据约定：GET /assets、GET /assets/{id}。

源依赖：T20,T25,T27；执行依赖候选：T020、T025、T027；依赖是否具备仍需实际核验。

当前已验证范围：资产列表/详情真实后端支持已有专项验证；资产前端已接真实列表/详情GET：案件分页、当前页筛选、固定对象版本只读详情、权限/错误提示和案件/身份切换清除旧响应；单元74与浏览器26均通过，但浏览器使用自建传输夹具，不代表真实后端联调或受控下载。；资产详情页已接受控下载，仅VALID及asset.download启用；浏览器保存前核验大小、摘要与固定版本ETag，身份/案件/资产变化废弃晚响应。101项单元和31项自建传输浏览器测试通过，不冒充真实后端E2E。；资产详情已接既有getSource只读来源授权：精确案件/资产/来源绑定、独立asset.read/source.read、完整Source校验、状态/用途/有效期/依据/版本照实展示；身份/角色/权限/详情变化及卸载拒绝晚回复。40项新单元纳入390项完整前端，开发与生产各61项传输浏览器通过；不是实际权威联调或完整血缘。；资产父页同generation身份上下文变化已修复：同步观察用户/单位/角色/权限/案件列表，复用清理使旧列表、详情、来源及下载状态失效；有效RED后11项新增浏览器、390项前端及开发/生产各72项传输浏览器通过。仅本地已观察变化，不证明远端撤销、真实权威联调或完整血缘；异步负例等待存在1项非阻断覆盖改进。；共享session.call已形成旧401的拒绝传播窗口加入当前代条件，保留旧错误且不清除新连接尝试；真实客户端受控微任务6例GET/POST/二进制读取及新认证成功/失败有效RED后通过，396前端及开发/生产各72项传输浏览器通过。非普通点击故障或已建立用户丢失复现，不覆盖成功传播/远端撤销/PUT新窗口。

未完成事项：父页本地上下文清理及共享call旧401传播期间新连接尝试保护已有证据；完整资产血缘、真实身份/来源/后端组合联调、远端撤销通知及成功结果传播等独立边界仍待，不把受控微任务复现推广为普通点击或全部生命周期验收。；396项完整前端及开发/生产各72项传输浏览器通过（场景重叠），新增6项共享call受控调度单元；真实权威组合E2E仍待。保留两项非阻断覆盖/维护事项：资产异步负例等待原应用完成、共享session测试微任务层数耦合，不删除断言或跳过门禁。；逐项核对源验收标准并补实际证据：支持筛选和详情；原始对象不可直接编辑；下载受权限和审计控制。；实际开发负责人和指定复核人均已确认为徐昌胜；仍需剩余工时、实际实施日期、本人复核决定及逐项源卡验收。同人兼任不等于独立双人复核，责任登记不替代实际验收。

表与创建源码：

- `mt.asset_lineage`：多父对象血缘；[backend/business_migrations/0001_business_baseline.sql:670](<../../backend/business_migrations/0001_business_baseline.sql#L670>)。本清单不证明运行库已采用。
- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.object_version`：对象版本与摘要清单；[backend/business_migrations/0001_business_baseline.sql:356](<../../backend/business_migrations/0001_business_baseline.sql#L356>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset、object_version。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset、object_version。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event、object_version。
- `business_app.controls.exports.Exports.content(self, scope, identifier, request)`；[backend/business_app/controls/exports.py:228](<../../backend/business_app/controls/exports.py#L228>)；表：object_version。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset、object_version。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset、object_version。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset、object_version。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：object_version。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：object_version。
- `business_app.scoped_objects.ScopedObjects._registered(connection, scope, reference)`；[backend/business_app/scoped_objects.py:75](<../../backend/business_app/scoped_objects.py#L75>)；表：object_version。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset、object_version。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：object_version。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset、object_version。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `listAssets` | `GET /api/v1/assets` | case_id（必填）、limit（可选）、cursor（可选） | `list_assets`；[backend/business_app/catalog_router.py:37](<../../backend/business_app/catalog_router.py#L37>) |
| `getAsset` | `GET /api/v1/assets/{id}` | 无 | `get_asset`；[backend/business_app/catalog_router.py:27](<../../backend/business_app/catalog_router.py#L27>) |
| `downloadAsset` | `GET /api/v1/assets/{id}/content` | 无 | `download_asset`；[backend/business_app/asset_download_router.py:16](<../../backend/business_app/asset_download_router.py#L16>) |


<a id="t031"></a>
## T031 设计分析任务与节点执行模型

任务卡：[tasks/backend/T031.md](<../../tasks/backend/T031.md>)；分组：任务编排、节点执行及任务页面；源责任角色：架构/后端；实际负责人：未确定。

原工作范围：设计analysis_task、task_node_run、task_event和policy_version。

原接口/数据约定：任务状态图与DAG节点契约。

源依赖：T010,T020；执行依赖候选：T010、T020；依赖是否具备仍需实际核验。

当前已验证范围：任务/运行/节点/事件候选表和固定历史身份约束已有迁移验证；候选任务DAG解析子范围：复用既有Schema与注册表，新增嵌套不可变节点/绑定/入口快照、原始及规范化摘要、稳定拓扑及模型必填绑定校验；全部36候选图及77项解析回归有证据，未选分支与运行节点状态分离。不挂载createTask、不写库、不调度、不采用正式策略；不证明整卡验收。

未完成事项：候选DAG不可变解析已有实测；仍需受信场景/模块/策略映射、固定任务/运行/节点版本关联与实际业务访问，不把candidate-1当正式可执行计划。；对接真实调度和结果生产后完成任务级验收；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t032"></a>
## T032 实现任务及节点数据库模型

任务卡：[tasks/backend/T032.md](<../../tasks/backend/T032.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端；实际负责人：未确定。

原工作范围：创建任务、节点运行、事件和策略表及迁移。

原接口/数据约定：analysis_task、task_node_run、task_event。

源依赖：T031；执行依赖候选：T031；依赖是否具备仍需实际核验。

当前已验证范围：业务版本迁移与当前历史/上传所需任务表访问已有测试；固定运行事件存储子范围：0015增量增加同案件/任务/运行复合外键及现有11种前后状态枚举约束；合法历史保留、异常历史与末尾失败的原子回滚、追加写保护及受影响回归有实测。不实现通用状态迁移或任务创建，不修改旧迁移或共享库，不证明整卡验收。

未完成事项：0015固定运行事件关联和状态词汇约束已有实测；仍需完整任务创建访问层、全部版本升级与前向修复，不用候选DAG替代正式策略映射。；后续精确973a7d7业务回归1057项和T014权限1092项通过，但整体CI仍安全扫描失败；原c3370a2失败身份未保存，不推断唯一原因。；完成生产升级、关联隔离及失败回退验证；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

表与创建源码：

- `mt.analysis_task`：分析任务当前投影；[backend/business_migrations/0001_business_baseline.sql:642](<../../backend/business_migrations/0001_business_baseline.sql#L642>)。本清单不证明运行库已采用。
- `mt.task_node_run`：节点尝试与租约；[backend/business_migrations/0001_business_baseline.sql:1006](<../../backend/business_migrations/0001_business_baseline.sql#L1006>)。本清单不证明运行库已采用。
- `mt.task_event`：任务状态事件；[backend/business_migrations/0001_business_baseline.sql:935](<../../backend/business_migrations/0001_business_baseline.sql#L935>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.catalog_reads.CatalogReads.task(connection, scope, item)`；[backend/business_app/catalog_reads.py:78](<../../backend/business_app/catalog_reads.py#L78>)；表：task_node_run。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：analysis_task。
- `business_app.controls.execution.Execution._claim_bound(self, scope, node_id, task_id)`；[backend/business_app/controls/execution.py:71](<../../backend/business_app/controls/execution.py#L71>)；表：task_node_run。
- `business_app.controls.execution.Execution._finish_bound(self, scope, lease, state, reason, task_id)`；[backend/business_app/controls/execution.py:117](<../../backend/business_app/controls/execution.py#L117>)；表：task_node_run。
- `business_app.controls.execution.Execution.cancel_transition(self, connection, scope, task_id, run_version, expected_version, before, after, request_id, reason)`；[backend/business_app/controls/execution.py:177](<../../backend/business_app/controls/execution.py#L177>)；表：analysis_task、task_node_run。
- `business_app.controls.execution.Execution._append_cancel_event(self, connection, scope, task_id, run_version, version, before, after, request_id, reason, run)`；[backend/business_app/controls/execution.py:267](<../../backend/business_app/controls/execution.py#L267>)；表：task_event。
- `business_app.controls.execution.Execution._reconcile_bound(self, scope, task_id, run_version, expected_version, request_id)`；[backend/business_app/controls/execution.py:348](<../../backend/business_app/controls/execution.py#L348>)；表：task_node_run。
- `business_app.controls.execution.Execution.nodes(self, scope, task_id, run_version)`；[backend/business_app/controls/execution.py:394](<../../backend/business_app/controls/execution.py#L394>)；表：task_node_run。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：analysis_task。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：analysis_task。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：analysis_task。
- `business_app.scope_collections.bind_task_scope(connection, scope, task)`；[backend/business_app/scope_collections.py:86](<../../backend/business_app/scope_collections.py#L86>)；表：analysis_task。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：analysis_task。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：analysis_task、task_event、task_node_run。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：task_event、task_node_run。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t033"></a>
## T033 实现任务状态机

任务卡：[tasks/backend/T033.md](<../../tasks/backend/T033.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端；实际负责人：未确定。

原工作范围：分别维护上传会话和分析任务状态；分析状态转移校验当前状态与run_version，状态与审计在同一事务提交。

原接口/数据约定：TaskStateMachine.transition。

源依赖：T032,T017；执行依赖候选：T032、T017；依赖是否具备仍需实际核验。

当前已验证范围：上传及取消状态原子写、审计/outbox与部分状态约束已有验证；取消专用统一原子写入：收拢既有请求取消和停止后确认取消；校验单位/案件/任务、授权操作、运行/行版本及历史运行范围，条件更新投影并同事务写固定运行事件与outbox；savepoint覆盖被捕获故障，保留HTTP批准/ETag/幂等/审计及事务末撤销。38项新增用例和100项相邻数据库回归通过；不是全业务状态机或共享采用。

未完成事项：取消专用统一写入子范围已有实测；仍需全业务分析任务状态机、可信计划/策略/提供者映射及节点聚合；不能用取消通过代替任务创建、RETURNED、重算、复核或归档完成。；验证全部合法/非法迁移、部分/延期能力、超时及事件顺序；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t034"></a>
## T034 实现任务创建接口

任务卡：[tasks/backend/T034.md](<../../tasks/backend/T034.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端；实际负责人：徐昌胜。

原工作范围：按场景和模块创建异步分析任务。

原接口/数据约定：POST /analysis/tasks接收有效asset_id、场景和策略；202返回task_id及查询地址；Idempotency-Key绑定主体与请求摘要。

源依赖：T033,T015；执行依赖候选：T033、T015；依赖是否具备仍需实际核验。

当前已验证范围：不可变TaskCreate请求、主体/案件及精确JSON摘要冻结；显式无默认计划提供方的策略/计划/能力/authority版本与摘要绑定和时效重查已实现。64项新测试纳入243项受影响纯回归，Ruff和258文件类型检查通过；没有创建事务、HTTP或运行许可。；I01严格材料Schema、规范UTF-8/独立摘要、显式预算及不可变快照、离线validate/prepare工具和0016六表/私有ACL基础已实现；245项纯测试（147材料、64既有绑定、34工具）、230项受影响隔离DB回归、既有失败探针及Ruff/格式/268文件类型检查通过。仅内部基础，不含采用管理/计划读取函数、原子创建事务、createTask HTTP或真实202；E01—E04未确认，未生效映射或共享迁移。；I02首批请求上下文纯组件：冻结并重新核验主体/请求及A、B独立摘要，ContextVar显式绑定和finally恢复，读取仅返回隔离副本，不等于授权。127项纯回归（63上下文、64既有绑定）及Ruff/格式/270文件类型检查通过；仅新增两文件，未接guard/路由、受限SQL或当前事实，不含I02整步完成或真实202。；I02首批PlanBinding/ExecutionMaterials纯边界：冻结精确请求、revision/head及材料/输入绑定；不把调用者提供的收据/事实字节当真实采用、许可或当前权威。最终392项纯组合（本批84项及原308项）和Ruff/格式/272文件类型通过；无SQL、当前事实、guard/HTTP接线，I02未整步完成。

未完成事项：2026-10-23完成T034 I03持锁者真实写入后回滚的独立连接验证批次：两个独立Database/连接及不同后端PID，以pg_locks与pg_blocking_pids核对同一幂等事务锁的实际争用；持有者已成功INSERT analysis_task后，下一写入前受控异常真实传播并回滚，等待者随后独立创建一次完整写集合，Accepted/ETag及事件/审计归属于等待者请求，失败持有者集合及请求记录为0、task_result为0。本批回滚并发用例1项、相邻回滚/幂等边界8项、原失败探针及Ruff/格式/291文件类型通过；范围重叠不相加。仅新增测试、未修产品；受控异常不是漏洞RED，synthetic issuer不作正式提供方或HTTP授权。旧7097全组1800秒TIMEOUT保留，本cohort未重跑全组。C03、真实故障/恢复及代际、真实采用/Proof/HTTP仍未完成。0新增C，T034仍4C/4R。 原剩余工作和历史记录：2026-10-23完成T034 I03独立连接并发验证批次：两个独立Database/连接及不同后端PID，以pg_locks与pg_blocking_pids核对同一幂等事务锁的已授予/等待争用；持有者提交后等待者复用原Accepted与ETag，八组持久化写集合保持一次创建且业务结果为0。本批独立并发用例1项、相邻幂等/当前材料边界10项、原失败探针及Ruff/格式/290文件类型通过；范围重叠不相加。仅新增测试、未改产品；synthetic issuer不作正式提供方或HTTP授权。旧全组1800秒TIMEOUT保留，本cohort未重跑全组。C02/C03、真实故障/恢复及代际、真实采用/Proof/HTTP仍未完成。0新增C，T034仍4C/4R。 原剩余工作和历史记录：2026-10-23补齐完整business验证器的有界超时收尾：执行上限仍1800秒，Linux独立组SIGINT→5秒清理宽限→TERM→2秒→KILL，最终drain/reap最多2秒；先冻结超时瞬间进度，超时仍TIMEOUT/退出2/complete=false及规范0计数，partial JUnit仅独立观测。真实finally缺失RED之后，新旧相邻诊断组合72项、原失败探针及Ruff/格式/289文件类型通过。旧1800秒全组TIMEOUT未关闭，旧last-selector两参数23.47秒通过只属原cohort，不证明挂起位置或根因；本批无完整DB/T014重跑、DB或逃逸孙进程清理验收，Windows DEVNULL直子进程兜底不当原生验证。0新增C，T034仍4C/4R。 原剩余工作和历史记录：2026-10-23补齐T034-I03隔离原子创建候选：同根CASE/createTask、明确受信材料端口、A/B及当前采用绑定，双savepoint内完整八表和CREATED→QUEUED、精确历史Accepted/ETag重放及提交前复读已实现；新增0018只修generation.database_oid的JSON整数投影，0001—0017及严格reader不改。事务/新迁移组合82项、受影响组375项、原失败探针及Ruff/格式/288文件类型检查符合预期；完整business实际结果TIMEOUT另列原始汇总，T014未单独重跑，重叠数量不相加。本批无默认权威、可信采用/Proof、HTTP挂载、共享迁移或算法执行；并发、恢复、未知commit结果及E04运行预算仍未齐，0新增C，T034保持4C/4R。 The exact final-source complete business group hit the unchanged1800-second limit at test_t014_runtime function_permission unrelated case/unit setup. No complete JUnit totals or final full-group failure-probe were produced; count0 is unavailable totals, not zero executed tests or a pass. Root cause and cleanup after forced pytest timeout remain unverified. Preserve the failure and investigate without skipping tests or increasing the gate. I03 independent-connection same-key concurrency, recovery-generation invalidation, controlled rollback and unknown-commit/response-loss proofs remain separate unfinished evidence; serial replay is not concurrency or recovery acceptance. Actual authenticated management/adoption, current classification/handler/licence providers and a production-approved Proof issuer are still absent. Synthetic self-owned SQL fixtures are not deployment defaults or actual authority. I04 HTTP createTask mounting/injection and route-wide permission/fault/privacy verification, followed by applicable I05 full T014/current-source CI and delivery review, remain unfinished. E04 aggregate/runtime budgets, hard creation deadline, handler execution, queues/consumers, operational installation and shared adoption remain unintegrated. Python candidates and algorithms remain deferred. Existing T013 human custody/recovery, N01 software admission and unresolved historical/hosted CI failures are retained; this isolated T034 tranche neither accepts those risks nor closes those tasks.；2026-10-23补齐T034-I03隔离原子创建候选：同根CASE/createTask、明确受信材料端口、A/B及当前采用绑定，双savepoint内完整八表和CREATED→QUEUED、精确历史Accepted/ETag重放及提交前复读已实现；新增0018只修generation.database_oid的JSON整数投影，0001—0017及严格reader不改。事务/新迁移组合82项、受影响组375项、原失败探针及Ruff/格式/288文件类型检查符合预期；完整business实际结果TIMEOUT另列原始汇总，T014未单独重跑，重叠数量不相加。本批无默认权威、可信采用/Proof、HTTP挂载、共享迁移或算法执行；并发、恢复、未知commit结果及E04运行预算仍未齐，0新增C，T034保持4C/4R。 独立连接并发、真实恢复、未知提交及HTTP/提供方和本版托管终态仍分别核验。上一eb28缺具体失败断言，旧工程软件扫描失败保留。；逐项核对源验收标准并补实际证据：校验资产授权与状态、策略版本及幂等；相同键同摘要返回原任务，摘要不同返回冲突；不以upload_id替代task_id。；实际开发负责人和指定复核人均已由本人确认为徐昌胜；仍需投入工时、实际实施日期和复核决定，对照原依赖及验收逐项关闭代码/测试缺口。同人兼任不当作独立双人复核，责任登记不替代任务验收。

表与创建源码：

- `mt.analysis_task`：分析任务当前投影；[backend/business_migrations/0001_business_baseline.sql:642](<../../backend/business_migrations/0001_business_baseline.sql#L642>)。本清单不证明运行库已采用。
- `mt.idempotency_record`：主体请求摘要幂等；[backend/business_migrations/0001_business_baseline.sql:291](<../../backend/business_migrations/0001_business_baseline.sql#L291>)。本清单不证明运行库已采用。
- `mt.outbox_event`：事务发件箱；[backend/business_migrations/0001_business_baseline.sql:382](<../../backend/business_migrations/0001_business_baseline.sql#L382>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：analysis_task。
- `business_app.controls.execution.Execution.cancel_transition(self, connection, scope, task_id, run_version, expected_version, before, after, request_id, reason)`；[backend/business_app/controls/execution.py:177](<../../backend/business_app/controls/execution.py#L177>)；表：analysis_task。
- `business_app.controls.execution.Execution._append_cancel_event(self, connection, scope, task_id, run_version, version, before, after, request_id, reason, run)`；[backend/business_app/controls/execution.py:267](<../../backend/business_app/controls/execution.py#L267>)；表：outbox_event。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：analysis_task。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：analysis_task。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：analysis_task。
- `business_app.scope_collections.bind_task_scope(connection, scope, task)`；[backend/business_app/scope_collections.py:86](<../../backend/business_app/scope_collections.py#L86>)；表：analysis_task。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：analysis_task。
- `business_app.task_creation_service.TaskCreationService.create(self, scope, body, *, idempotency_key, request_id)`；[backend/business_app/task_creation_service.py:402](<../../backend/business_app/task_creation_service.py#L402>)；表：idempotency_record。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：analysis_task、outbox_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：outbox_event。
- `business_app.uploads.messaging.pump_outbox_once(service, authority, scope, broker_url, *, work_authorization, upload_id)`；[backend/business_app/uploads/messaging.py:57](<../../backend/business_app/uploads/messaging.py#L57>)；表：outbox_event。
- `business_app.uploads.repository.UploadRepository.replay(self, connection, scope, operation, key, digest)`；[backend/business_app/uploads/repository.py:51](<../../backend/business_app/uploads/repository.py#L51>)；表：idempotency_record。
- `business_app.uploads.repository.UploadRepository.remember(self, connection, scope, operation, key, digest, response)`；[backend/business_app/uploads/repository.py:74](<../../backend/business_app/uploads/repository.py#L74>)；表：idempotency_record。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：outbox_event。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：outbox_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createTask` | `POST /api/v1/analysis/tasks` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t035"></a>
## T035 实现任务查询和进度接口

任务卡：[tasks/backend/T035.md](<../../tasks/backend/T035.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端；实际负责人：未确定。

原工作范围：查询任务、节点、进度、错误和结果版本。

原接口/数据约定：GET /analysis/tasks/{id}；GET /analysis/tasks。

源依赖：T034；执行依赖候选：T034；依赖是否具备仍需实际核验。

当前已验证范围：固定历史运行、结果及当前执行节点/事件读取子范围已有验证；已实现案件级当前任务列表分页：逐项权限与来源核验、无历史结果任务、当前运行最新节点尝试投影及事务提交前复核；不代表真实DAG进度或任务生产者完成

未完成事项：补真实DAG进度计算与前端接入；验证同run进度单调、重算新版本分列及全部适用权限和错误场景；任务创建/生产者另按T034等依赖实施

表与创建源码：

- `mt.analysis_task`：分析任务当前投影；[backend/business_migrations/0001_business_baseline.sql:642](<../../backend/business_migrations/0001_business_baseline.sql#L642>)。本清单不证明运行库已采用。
- `mt.task_node_run`：节点尝试与租约；[backend/business_migrations/0001_business_baseline.sql:1006](<../../backend/business_migrations/0001_business_baseline.sql#L1006>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.catalog_reads.CatalogReads.task(connection, scope, item)`；[backend/business_app/catalog_reads.py:78](<../../backend/business_app/catalog_reads.py#L78>)；表：task_node_run。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：analysis_task。
- `business_app.controls.execution.Execution._claim_bound(self, scope, node_id, task_id)`；[backend/business_app/controls/execution.py:71](<../../backend/business_app/controls/execution.py#L71>)；表：task_node_run。
- `business_app.controls.execution.Execution._finish_bound(self, scope, lease, state, reason, task_id)`；[backend/business_app/controls/execution.py:117](<../../backend/business_app/controls/execution.py#L117>)；表：task_node_run。
- `business_app.controls.execution.Execution.cancel_transition(self, connection, scope, task_id, run_version, expected_version, before, after, request_id, reason)`；[backend/business_app/controls/execution.py:177](<../../backend/business_app/controls/execution.py#L177>)；表：analysis_task、task_node_run。
- `business_app.controls.execution.Execution._reconcile_bound(self, scope, task_id, run_version, expected_version, request_id)`；[backend/business_app/controls/execution.py:348](<../../backend/business_app/controls/execution.py#L348>)；表：task_node_run。
- `business_app.controls.execution.Execution.nodes(self, scope, task_id, run_version)`；[backend/business_app/controls/execution.py:394](<../../backend/business_app/controls/execution.py#L394>)；表：task_node_run。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：analysis_task。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：analysis_task。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：analysis_task。
- `business_app.scope_collections.bind_task_scope(connection, scope, task)`；[backend/business_app/scope_collections.py:86](<../../backend/business_app/scope_collections.py#L86>)；表：analysis_task。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：analysis_task。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：analysis_task、task_node_run。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：task_node_run。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `listTasks` | `GET /api/v1/analysis/tasks` | case_id（必填）、limit（可选）、cursor（可选） | `list_tasks`；[backend/business_app/catalog_router.py:54](<../../backend/business_app/catalog_router.py#L54>) |
| `getTask` | `GET /api/v1/analysis/tasks/{id}` | history（可选） | `task`；[backend/business_app/history/router.py:112](<../../backend/business_app/history/router.py#L112>) |


<a id="t036"></a>
## T036 实现异步队列与优先级

任务卡：[tasks/backend/T036.md](<../../tasks/backend/T036.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端/DevOps；实际负责人：未确定。

原工作范围：SQL任务/outbox持久化，成熟broker候选优先做故障PoC；Kafka接入/事件流与执行broker分开。长短队列、容量背压与优先级可配置，重复投递允许且消费者幂等，不承诺抢占已运行GPU。

原接口/数据约定：task.created事件；队列配置。

源依赖：T004,T034；执行依赖候选：T004、T034；依赖是否具备仍需实际核验。

当前已验证范围：上传验证真实RabbitMQ消息、确认/恢复和取消outbox基础已有测试

未完成事项：补完整DAG队列消费者、优先级/背压/并发配额；实施真实多worker投递故障/重放/崩溃恢复，不把数据库竞争者当Celery worker

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t037"></a>
## T037 实现DAG任务编排器

任务卡：[tasks/backend/T037.md](<../../tasks/backend/T037.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端；实际负责人：未确定。

原工作范围：按策略生成预处理、识别、取证、检索和报告节点依赖。

原接口/数据约定：AnalysisPolicy/DAG：节点状态、required/optional边、accepted_terminal_states、reason/missing_modality；任务能力完成矩阵及report_eligibility。

源依赖：T033,T036；执行依赖候选：T033、T036；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成DAG任务编排器的交付、异常/权限测试和源验收

表与创建源码：

- `mt.report`：报告生成与下载状态；[backend/business_migrations/0001_business_baseline.sql:1128](<../../backend/business_migrations/0001_business_baseline.sql#L1128>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：report。
- `business_app.registry_router.get_report(request, id)`；[backend/business_app/registry_router.py:20](<../../backend/business_app/registry_router.py#L20>)；表：report。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t038"></a>
## T038 实现节点级重试与检查点

任务卡：[tasks/backend/T038.md](<../../tasks/backend/T038.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端；实际负责人：未确定。

原工作范围：实现运行期retry_policy、超时退避和检查点；节点租约与fencing_token防止旧执行覆盖，永久错误和OOM不无限重投。

原接口/数据约定：NodeCheckpoint；retry_policy。

源依赖：T037；执行依赖候选：T037；依赖是否具备仍需实际核验。

当前已验证范围：节点租约/fencing及取消确认的过期边界已有数据库竞争测试

未完成事项：实现完整节点重试退避、checkpoint续跑及资源/OOM策略；真实多worker故障回归并证明旧持有者不能发布结果；确认取消不等于已停外部进程

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t039"></a>
## T039 实现任务取消和退回重算

任务卡：[tasks/backend/T039.md](<../../tasks/backend/T039.md>)；分组：任务编排、节点执行及任务页面；源责任角色：后端；实际负责人：未确定。

原工作范围：取消意图/停止确认与版本条件提交；退回补证与重算分流，旧fencing执行结果拒绝，进度按新run_version记录。

原接口/数据约定：POST /analysis/tasks/{id}/cancel；POST /analysis/tasks/{id}/rerun。

源依赖：T033,T037；执行依赖候选：T033、T037；依赖是否具备仍需实际核验。

当前已验证范围：取消请求202、条件写及当前租约/epoch确认子范围已有测试；取消操作页面已接既有真实getTaskExecution/cancelTask：强ETag与运行/控制版本、六种前态、明确确认及适用批准输入；未知结果冻结原body/key/ETag重试，身份/角色/权限/案件/任务切换清除旧状态。39项新单元、350项完整前端及开发/生产各55项传输浏览器用例通过；202仅受理，不证明真实worker停止或后端E2E，夹具结果版本契约补强单列。

未完成事项：现有取消后端和前端申请/原请求重试已有子范围验证；仍需重跑新run编排、真实worker取消投递/停止和正式规则采用，不把202当停止。；补真实身份/来源/规则组合的页面到后端E2E及执行中结果发布/恢复竞态；成功执行状态传输夹具result_version=0与契约min1的补强保留，不能当完整Schema合规或真实后端联调通过。；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

表与创建源码：

- `mt.analysis_task`：分析任务当前投影；[backend/business_migrations/0001_business_baseline.sql:642](<../../backend/business_migrations/0001_business_baseline.sql#L642>)。本清单不证明运行库已采用。
- `mt.outbox_event`：事务发件箱；[backend/business_migrations/0001_business_baseline.sql:382](<../../backend/business_migrations/0001_business_baseline.sql#L382>)。本清单不证明运行库已采用。
- `mt.task_event`：任务状态事件；[backend/business_migrations/0001_business_baseline.sql:935](<../../backend/business_migrations/0001_business_baseline.sql#L935>)。本清单不证明运行库已采用。
- `mt.task_run`：任务运行历史；[backend/business_migrations/0001_business_baseline.sql:958](<../../backend/business_migrations/0001_business_baseline.sql#L958>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：analysis_task。
- `business_app.controls.execution.Execution.cancel_transition(self, connection, scope, task_id, run_version, expected_version, before, after, request_id, reason)`；[backend/business_app/controls/execution.py:177](<../../backend/business_app/controls/execution.py#L177>)；表：analysis_task、task_run。
- `business_app.controls.execution.Execution._append_cancel_event(self, connection, scope, task_id, run_version, version, before, after, request_id, reason, run)`；[backend/business_app/controls/execution.py:267](<../../backend/business_app/controls/execution.py#L267>)；表：outbox_event、task_event。
- `business_app.controls.execution.Execution.nodes(self, scope, task_id, run_version)`；[backend/business_app/controls/execution.py:394](<../../backend/business_app/controls/execution.py#L394>)；表：task_run。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：analysis_task。
- `business_app.controls.router.list_events(request, id, run_version, cursor, limit)`；[backend/business_app/controls/router.py:768](<../../backend/business_app/controls/router.py#L768>)；表：task_run。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：analysis_task、task_run。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：analysis_task、task_run。
- `business_app.scope_collections.bind_task_scope(connection, scope, task)`；[backend/business_app/scope_collections.py:86](<../../backend/business_app/scope_collections.py#L86>)；表：analysis_task、task_run。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：analysis_task。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：analysis_task、outbox_event、task_event、task_run。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：outbox_event、task_event、task_run。
- `business_app.uploads.messaging.pump_outbox_once(service, authority, scope, broker_url, *, work_authorization, upload_id)`；[backend/business_app/uploads/messaging.py:57](<../../backend/business_app/uploads/messaging.py#L57>)；表：outbox_event。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：outbox_event。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：outbox_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `cancelTask` | `POST /api/v1/analysis/tasks/{id}/cancel` | 无 | `cancel_task`；[backend/business_app/controls/router.py:721](<../../backend/business_app/controls/router.py#L721>) |
| `rerunTask` | `POST /api/v1/analysis/tasks/{id}/rerun` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t040"></a>
## T040 开发任务监控页面

任务卡：[tasks/frontend/T040.md](<../../tasks/frontend/T040.md>)；分组：任务编排、节点执行及任务页面；源责任角色：前端；实际负责人：未确定。

原工作范围：展示任务列表、节点DAG、进度、错误、重试和取消。

原接口/数据约定：任务查询、取消与重算接口。

源依赖：T035,T039；执行依赖候选：T035、T039；依赖是否具备仍需实际核验。

当前已验证范围：按编号读取实时执行/节点/事件、精确历史结果和案件待复核队列；按12页PPT优化现有界面，57项单元与10项浏览器夹具通过；任务页新增案件内当前任务分页与筛选，选择任务衔接现有执行/节点/事件及历史结果读取；无结果和DEFERRED状态保留，不推算DAG百分比；74项前端单元和26项传输夹具浏览器回归通过。

未完成事项：任务创建/取消/重算的适用前端动作、真实DAG进度与检查点展示、真实后端身份组合联调及源验收仍待；当前案件任务列表和历史读取已有前端回归

表与创建源码：

- `mt.analysis_task`：分析任务当前投影；[backend/business_migrations/0001_business_baseline.sql:642](<../../backend/business_migrations/0001_business_baseline.sql#L642>)。本清单不证明运行库已采用。
- `mt.outbox_event`：事务发件箱；[backend/business_migrations/0001_business_baseline.sql:382](<../../backend/business_migrations/0001_business_baseline.sql#L382>)。本清单不证明运行库已采用。
- `mt.task_event`：任务状态事件；[backend/business_migrations/0001_business_baseline.sql:935](<../../backend/business_migrations/0001_business_baseline.sql#L935>)。本清单不证明运行库已采用。
- `mt.task_node_run`：节点尝试与租约；[backend/business_migrations/0001_business_baseline.sql:1006](<../../backend/business_migrations/0001_business_baseline.sql#L1006>)。本清单不证明运行库已采用。
- `mt.task_run`：任务运行历史；[backend/business_migrations/0001_business_baseline.sql:958](<../../backend/business_migrations/0001_business_baseline.sql#L958>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.catalog_reads.CatalogReads.task(connection, scope, item)`；[backend/business_app/catalog_reads.py:78](<../../backend/business_app/catalog_reads.py#L78>)；表：task_node_run。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：analysis_task。
- `business_app.controls.execution.Execution._claim_bound(self, scope, node_id, task_id)`；[backend/business_app/controls/execution.py:71](<../../backend/business_app/controls/execution.py#L71>)；表：task_node_run。
- `business_app.controls.execution.Execution._finish_bound(self, scope, lease, state, reason, task_id)`；[backend/business_app/controls/execution.py:117](<../../backend/business_app/controls/execution.py#L117>)；表：task_node_run。
- `business_app.controls.execution.Execution.cancel_transition(self, connection, scope, task_id, run_version, expected_version, before, after, request_id, reason)`；[backend/business_app/controls/execution.py:177](<../../backend/business_app/controls/execution.py#L177>)；表：analysis_task、task_node_run、task_run。
- `business_app.controls.execution.Execution._append_cancel_event(self, connection, scope, task_id, run_version, version, before, after, request_id, reason, run)`；[backend/business_app/controls/execution.py:267](<../../backend/business_app/controls/execution.py#L267>)；表：outbox_event、task_event。
- `business_app.controls.execution.Execution._reconcile_bound(self, scope, task_id, run_version, expected_version, request_id)`；[backend/business_app/controls/execution.py:348](<../../backend/business_app/controls/execution.py#L348>)；表：task_node_run。
- `business_app.controls.execution.Execution.nodes(self, scope, task_id, run_version)`；[backend/business_app/controls/execution.py:394](<../../backend/business_app/controls/execution.py#L394>)；表：task_node_run、task_run。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：analysis_task。
- `business_app.controls.router.list_events(request, id, run_version, cursor, limit)`；[backend/business_app/controls/router.py:768](<../../backend/business_app/controls/router.py#L768>)；表：task_run。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：analysis_task、task_run。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：analysis_task、task_run。
- `business_app.scope_collections.bind_task_scope(connection, scope, task)`；[backend/business_app/scope_collections.py:86](<../../backend/business_app/scope_collections.py#L86>)；表：analysis_task、task_run。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：analysis_task。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：analysis_task、outbox_event、task_event、task_node_run、task_run。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：outbox_event、task_event、task_node_run、task_run。
- `business_app.uploads.messaging.pump_outbox_once(service, authority, scope, broker_url, *, work_authorization, upload_id)`；[backend/business_app/uploads/messaging.py:57](<../../backend/business_app/uploads/messaging.py#L57>)；表：outbox_event。
- `business_app.uploads.repository.UploadRepository.complete(self, scope, upload_id, payload, key, request_id)`；[backend/business_app/uploads/repository.py:258](<../../backend/business_app/uploads/repository.py#L258>)；表：outbox_event。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：outbox_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `listTasks` | `GET /api/v1/analysis/tasks` | case_id（必填）、limit（可选）、cursor（可选） | `list_tasks`；[backend/business_app/catalog_router.py:54](<../../backend/business_app/catalog_router.py#L54>) |
| `getTask` | `GET /api/v1/analysis/tasks/{id}` | history（可选） | `task`；[backend/business_app/history/router.py:112](<../../backend/business_app/history/router.py#L112>) |
| `cancelTask` | `POST /api/v1/analysis/tasks/{id}/cancel` | 无 | `cancel_task`；[backend/business_app/controls/router.py:721](<../../backend/business_app/controls/router.py#L721>) |
| `rerunTask` | `POST /api/v1/analysis/tasks/{id}/rerun` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t041"></a>
## T041 实现图片元数据解析

任务卡：[tasks/backend/T041.md](<../../tasks/backend/T041.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：后端/算法；实际负责人：未确定。

原工作范围：提取格式、尺寸、色彩、EXIF、质量和重采样基础信息。

原接口/数据约定：ImageMetadataResult。

源依赖：T025,T037；执行依赖候选：T025、T037；依赖是否具备仍需实际核验。

当前已验证范围：上传验证可完整解码PNG/JPEG并检查尺寸；本批两张官方CC0原图已下载、同摘要同步Linux并用现有解码器实测，错误摘要/MIME拒绝；未实现完整ImageMetadataResult服务。

未完成事项：建立正式ImageMetadataResult生产服务，提取色彩/EXIF/质量/重采样信息；补多格式、坏EXIF及敏感定位脱敏测试；旧媒体PTS证据不属于图片元数据验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t042"></a>
## T042 实现视频ffprobe解析

任务卡：[tasks/backend/T042.md](<../../tasks/backend/T042.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：后端/算法；实际负责人：未确定。

原工作范围：安全调用ffprobe提取容器、编解码、时长、帧率、码率、时基、音轨和字幕。

原接口/数据约定：VideoMetadataResult。

源依赖：T025,T037；执行依赖候选：T025、T037；依赖是否具备仍需实际核验。

当前已验证范围：自建视频的FFmpeg解码、时基和源PTS验证原型已执行

未完成事项：实现正式ffprobe视频元数据解析服务，补授权多编码/VFR/损坏媒体及预算测试；当前FFmpeg夹具不证明ffprobe接口已实现；自建夹具结果不能替代授权真实媒体的任务验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t043"></a>
## T043 实现标准化媒体副本生成

任务卡：[tasks/backend/T043.md](<../../tasks/backend/T043.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：后端/算法；实际负责人：未确定。

原工作范围：生成内部分析副本并保留原始编码信息和血缘。

原接口/数据约定：DerivedAsset记录；media.normalized事件。

源依赖：T041,T042；执行依赖候选：T041、T042；依赖是否具备仍需实际核验。

当前已验证范围：自建媒体解码/旋转夹具验证原件摘要不变及像素映射

未完成事项：实现正式分析副本生成、转码/色彩/旋转策略与映射版本，不覆盖原件；自建夹具结果不能替代授权真实媒体的任务验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t044"></a>
## T044 实现镜头边界检测

任务卡：[tasks/backend/T044.md](<../../tasks/backend/T044.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：算法；实际负责人：未确定。

原工作范围：集成镜头检测组件并输出镜头起止时间。

原接口/数据约定：Shot列表{shot_id,start_ms,end_ms,score}。

源依赖：T043；执行依赖候选：T043；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成镜头边界检测的交付、异常/权限测试和源验收

表与创建源码：

- `mt.shot`：镜头时间区间；[backend/business_migrations/0001_business_baseline.sql:795](<../../backend/business_migrations/0001_business_baseline.sql#L795>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t045"></a>
## T045 实现固定间隔抽帧

任务卡：[tasks/backend/T045.md](<../../tasks/backend/T045.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：算法；实际负责人：未确定。

原工作范围：按可配置间隔抽取带精确时间戳的帧。

原接口/数据约定：Keyframe记录和对象存储图像。

源依赖：T043；执行依赖候选：T043；依赖是否具备仍需实际核验。

当前已验证范围：自建VFR片段的原PTS与帧映射验证已执行

未完成事项：实现正式关键帧抽取服务，补真实视频、长视频及完整时间映射；自建夹具结果不能替代授权真实媒体的任务验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t046"></a>
## T046 实现镜头代表帧选择

任务卡：[tasks/backend/T046.md](<../../tasks/backend/T046.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：算法；实际负责人：未确定。

原工作范围：按清晰度、信息熵和邻帧差异为每镜头选Top-K。

原接口/数据约定：keyframe.quality_score与选取原因。

源依赖：T044,T045；执行依赖候选：T044、T045；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成镜头代表帧选择的交付、异常/权限测试和源验收

表与创建源码：

- `mt.keyframe`：关键帧；[backend/business_migrations/0001_business_baseline.sql:874](<../../backend/business_migrations/0001_business_baseline.sql#L874>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t047"></a>
## T047 实现音轨与字幕提取

任务卡：[tasks/backend/T047.md](<../../tasks/backend/T047.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：算法；实际负责人：未确定。

原工作范围：提取音轨、内嵌字幕和时间戳，生成派生资产。

原接口/数据约定：AudioAsset、SubtitleSegment。

源依赖：T042,T043；执行依赖候选：T042、T043；依赖是否具备仍需实际核验。

当前已验证范围：自建音频/字幕抽取夹具已有验证

未完成事项：实现正式音轨/字幕提取与缺模态/编码/时基对齐及权限测试；自建夹具结果不能替代授权真实媒体的任务验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t048"></a>
## T048 接入OCR并建立时间片段

任务卡：[tasks/backend/T048.md](<../../tasks/backend/T048.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：算法；实际负责人：未确定。

原工作范围：对图片和关键帧执行OCR，合并相邻帧重复文本。

原接口/数据约定：TextSegment{type=OCR,start_ms,end_ms,bbox,text,score}。

源依赖：T046,T037；执行依赖候选：T046、T037；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入OCR并建立时间片段的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t049"></a>
## T049 接入ASR并建立时间片段

任务卡：[tasks/backend/T049.md](<../../tasks/backend/T049.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：算法；实际负责人：未确定。

原工作范围：对音轨执行ASR并输出字词或句级时间戳。

原接口/数据约定：TextSegment{type=ASR,start_ms,end_ms,text,score}。

源依赖：T047,T037；执行依赖候选：T047、T037；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入ASR并建立时间片段的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t050"></a>
## T050 实现媒体统一时间轴服务

任务卡：[tasks/backend/T050.md](<../../tasks/backend/T050.md>)；分组：媒体解析、抽帧、OCR/ASR及时间轴；源责任角色：后端；实际负责人：未确定。

原工作范围：聚合镜头、关键帧、OCR、ASR、字幕和后续风险事件。

原接口/数据约定：GET /assets/{id}/timeline。

源依赖：T044,T046,T048,T049；执行依赖候选：T044、T046、T048、T049；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成媒体统一时间轴服务的交付、异常/权限测试和源验收

表与创建源码：

- `mt.keyframe`：关键帧；[backend/business_migrations/0001_business_baseline.sql:874](<../../backend/business_migrations/0001_business_baseline.sql#L874>)。本清单不证明运行库已采用。
- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.shot`：镜头时间区间；[backend/business_migrations/0001_business_baseline.sql:795](<../../backend/business_migrations/0001_business_baseline.sql#L795>)。本清单不证明运行库已采用。
- `mt.text_segment`：OCR ASR字幕原文；[backend/business_migrations/0001_business_baseline.sql:818](<../../backend/business_migrations/0001_business_baseline.sql#L818>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getTimeline` | `GET /api/v1/assets/{id}/timeline` | history（可选） | `timeline`；[backend/business_app/history/router.py:132](<../../backend/business_app/history/router.py#L132>) |


<a id="t051"></a>
## T051 定义统一模型输入输出契约

任务卡：[tasks/algorithm/T051.md](<../../tasks/algorithm/T051.md>)；分组：模型注册、推理、发布及运维；源责任角色：算法平台；实际负责人：未确定。

原工作范围：定义推理请求、发现项、证据、警告和运行信息Schema。

原接口/数据约定：InferenceRequest、InferenceResponse、Finding、EvidenceRef。

源依赖：T010,T037；执行依赖候选：T010、T037；依赖是否具备仍需实际核验。

当前已验证范围：M01—M34输入输出Schema及网关结构/错误校验已有开发验证

未完成事项：逐能力确认输入字节/像素路径、前处理版本与部分能力语义；补真实适配器兼容/序列化及边界测试；34套Schema不等于34模型可用

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t052"></a>
## T052 实现模型注册表

任务卡：[tasks/algorithm/T052.md](<../../tasks/algorithm/T052.md>)；分组：模型注册、推理、发布及运维；源责任角色：后端/算法平台；实际负责人：未确定。

原工作范围：管理模型名称、版本、镜像摘要、指标、数据版本和状态。

原接口/数据约定：POST/GET /models；model_registry表。

源依赖：T051,T014；执行依赖候选：T051、T014；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付；listModels读取同单位真实模型元数据，集合及逐条授权先于分页，游标绑定身份/操作/页大小/可见事实，提交前重核；未实现registerModel写入、正式上下线、真实制品准入或模型管理页面。

未完成事项：模型登记写入、唯一版本/模型卡约束的服务验证、修改审计、正式制品与上下线管理、完整管理写操作页面及整任务验收仍待。；已登记模型/评测的只读前端见T060。

表与创建源码：

- `mt.model_registry`：模型版本与许可引用；[backend/business_migrations/0001_business_baseline.sql:106](<../../backend/business_migrations/0001_business_baseline.sql#L106>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.router.model_operation(request, id)`；[backend/business_app/controls/router.py:521](<../../backend/business_app/controls/router.py#L521>)；表：model_registry。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：model_registry。
- `business_app.model_catalog.ModelCatalog._item(connection, scope, operation, item)`；[backend/business_app/model_catalog.py:108](<../../backend/business_app/model_catalog.py#L108>)；表：model_registry。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `registerModel` | `POST /api/v1/models` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `listModels` | `GET /api/v1/models` | limit（可选）、cursor（可选） | `list_models`；[backend/business_app/model_catalog_router.py:34](<../../backend/business_app/model_catalog_router.py#L34>) |


<a id="t053"></a>
## T053 实现统一推理网关

任务卡：[tasks/algorithm/T053.md](<../../tasks/algorithm/T053.md>)；分组：模型注册、推理、发布及运维；源责任角色：算法平台；实际负责人：未确定。

原工作范围：按能力/版本路由独立PyTorch/ONNX Runtime服务或经评审Triton；保留ModelAdapter抽象，TorchServe不作常规长期首选；后端维护与兼容矩阵纳入评审。

原接口/数据约定：POST /inference/{capability}；内部SDK。

源依赖：T051,T052；执行依赖候选：T051、T052；依赖是否具备仍需实际核验。

当前已验证范围：网关权限、固定对象、deadline/结果边界及独立M15合成CPU链路有验证

未完成事项：实现逐能力真实模型后端和统一推理服务的完整管理/故障路径；补授权权重/数据及实际CPU-GPU资源、性能、并发和隔离验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t054"></a>
## T054 实现HTTP与本地Mock适配器

任务卡：[tasks/algorithm/T054.md](<../../tasks/algorithm/T054.md>)；分组：模型注册、推理、发布及运维；源责任角色：算法平台；实际负责人：未确定。

原工作范围：提供HTTP模型服务和测试Mock适配器。

原接口/数据约定：ModelAdapter.predict/health。

源依赖：T053；执行依赖候选：T053；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成HTTP与本地Mock适配器的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t055"></a>
## T055 实现推理批处理与GPU队列

任务卡：[tasks/algorithm/T055.md](<../../tasks/algorithm/T055.md>)；分组：模型注册、推理、发布及运维；源责任角色：算法平台；实际负责人：未确定。

原工作范围：按模型、尺寸和等待窗口合批，控制显存和优先级。

原接口/数据约定：BatchScheduler配置与指标。

源依赖：T053,T036；执行依赖候选：T053、T036；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成推理批处理与GPU队列的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t056"></a>
## T056 实现模型健康检查与熔断

任务卡：[tasks/algorithm/T056.md](<../../tasks/algorithm/T056.md>)；分组：模型注册、推理、发布及运维；源责任角色：算法平台；实际负责人：未确定。

原工作范围：探测模型实例，失败时熔断、恢复和可选版本降级。

原接口/数据约定：GET /models/{id}/health；熔断状态。

源依赖：T053；执行依赖候选：T053；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成模型健康检查与熔断的交付、异常/权限测试和源验收

表与创建源码：

- `mt.model_registry`：模型版本与许可引用；[backend/business_migrations/0001_business_baseline.sql:106](<../../backend/business_migrations/0001_business_baseline.sql#L106>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.router.model_operation(request, id)`；[backend/business_app/controls/router.py:521](<../../backend/business_app/controls/router.py#L521>)；表：model_registry。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：model_registry。
- `business_app.model_catalog.ModelCatalog._item(connection, scope, operation, item)`；[backend/business_app/model_catalog.py:108](<../../backend/business_app/model_catalog.py#L108>)；表：model_registry。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getModelHealth` | `GET /api/v1/models/{id}/health` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t057"></a>
## T057 实现模型灰度发布

任务卡：[tasks/algorithm/T057.md](<../../tasks/algorithm/T057.md>)；分组：模型注册、推理、发布及运维；源责任角色：算法平台；实际负责人：未确定。

原工作范围：按单位、任务比例或场景路由新模型，并支持双写对比。

原接口/数据约定：POST /models/{id}/rollouts。

源依赖：T052,T053；执行依赖候选：T052、T053；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成模型灰度发布的交付、异常/权限测试和源验收

表与创建源码：

- `mt.approval_request`：按目的独立审批申请；[backend/business_migrations/0001_business_baseline.sql:179](<../../backend/business_migrations/0001_business_baseline.sql#L179>)。本清单不证明运行库已采用。
- `mt.index_registry`：索引版本不混向量；[backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>)。本清单不证明运行库已采用。
- `mt.model_release`：模型发布包；[backend/business_migrations/0001_business_baseline.sql:513](<../../backend/business_migrations/0001_business_baseline.sql#L513>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.approvals.Approvals.create(self, scope, body, request, key)`；[backend/business_app/controls/approvals.py:215](<../../backend/business_app/controls/approvals.py#L215>)；表：approval_request。
- `business_app.controls.approvals.Approvals.decide(self, scope, identifier, body, request, key, *, revoke)`；[backend/business_app/controls/approvals.py:248](<../../backend/business_app/controls/approvals.py#L248>)；表：approval_request。
- `business_app.controls.router.model_operation(request, id)`；[backend/business_app/controls/router.py:521](<../../backend/business_app/controls/router.py#L521>)；表：model_release。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：model_release。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `rolloutModel` | `POST /api/v1/models/{id}/rollouts` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t058"></a>
## T058 实现模型评测记录管理

任务卡：[tasks/algorithm/T058.md](<../../tasks/algorithm/T058.md>)；分组：模型注册、推理、发布及运维；源责任角色：后端/算法平台；实际负责人：未确定。

原工作范围：保存数据集版本、总体和分组指标、报告文件。

原接口/数据约定：POST/GET /model-evaluations。

源依赖：T052；执行依赖候选：T052；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付；listEvaluations读取已持久化评测记录，验证同单位模型和登记对象的版本/摘要，保留失败数和协议/数据版本；不运行评测、不生成指标、不代替评测写入或发布审批。

未完成事项：真实评测记录写入、总体/分组指标生产者、报告生成/保存及合格评测对发布审批的约束、完整评测发起/写入页面和源验收仍待。；已登记模型/评测的只读前端见T060。

表与创建源码：

- `mt.model_evaluation`：不可覆盖评测记录；[backend/business_migrations/0001_business_baseline.sql:332](<../../backend/business_migrations/0001_business_baseline.sql#L332>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `recordEvaluation` | `POST /api/v1/model-evaluations` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `listEvaluations` | `GET /api/v1/model-evaluations` | limit（可选）、cursor（可选） | `list_evaluations`；[backend/business_app/model_catalog_router.py:43](<../../backend/business_app/model_catalog_router.py#L43>) |


<a id="t059"></a>
## T059 实现输入输出漂移监测

任务卡：[tasks/algorithm/T059.md](<../../tasks/algorithm/T059.md>)；分组：模型注册、推理、发布及运维；源责任角色：算法平台；实际负责人：未确定。

原工作范围：统计输入质量、嵌入分布、置信度和人工纠错变化。

原接口/数据约定：model_drift_metric；告警规则。

源依赖：T053,T058；执行依赖候选：T053、T058；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成输入输出漂移监测的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t060"></a>
## T060 开发模型运维页面

任务卡：[tasks/frontend/T060.md](<../../tasks/frontend/T060.md>)；分组：模型注册、推理、发布及运维；源责任角色：前端；实际负责人：未确定。

原工作范围：展示模型卡、版本、评测、灰度、漂移和回滚。

原接口/数据约定：模型管理相关API。

源依赖：T052,T057,T058,T059；执行依赖候选：T052、T057、T058、T059；依赖是否具备仍需实际核验。

当前已验证范围：新增/models只读页面：当前单位模型与已登记评测独立分页，model.read/身份或权限变化即时清空并废弃晚响应，元数据引用仅文本、null指标保持未提供；129项前端单元和36项自建传输浏览器回归通过，不代表真实后端E2E、健康或发布/回滚实现。

未完成事项：当前模型/评测只读页面已实现；仍需真实健康、灰度/漂移、获批发布/二次确认/回滚交互、真实后端身份组合联调及完整源验收。

表与创建源码：

- `mt.approval_request`：按目的独立审批申请；[backend/business_migrations/0001_business_baseline.sql:179](<../../backend/business_migrations/0001_business_baseline.sql#L179>)。本清单不证明运行库已采用。
- `mt.index_registry`：索引版本不混向量；[backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>)。本清单不证明运行库已采用。
- `mt.model_registry`：模型版本与许可引用；[backend/business_migrations/0001_business_baseline.sql:106](<../../backend/business_migrations/0001_business_baseline.sql#L106>)。本清单不证明运行库已采用。
- `mt.model_release`：模型发布包；[backend/business_migrations/0001_business_baseline.sql:513](<../../backend/business_migrations/0001_business_baseline.sql#L513>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.approvals.Approvals.create(self, scope, body, request, key)`；[backend/business_app/controls/approvals.py:215](<../../backend/business_app/controls/approvals.py#L215>)；表：approval_request。
- `business_app.controls.approvals.Approvals.decide(self, scope, identifier, body, request, key, *, revoke)`；[backend/business_app/controls/approvals.py:248](<../../backend/business_app/controls/approvals.py#L248>)；表：approval_request。
- `business_app.controls.router.model_operation(request, id)`；[backend/business_app/controls/router.py:521](<../../backend/business_app/controls/router.py#L521>)；表：model_registry、model_release。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：model_registry、model_release。
- `business_app.model_catalog.ModelCatalog._item(connection, scope, operation, item)`；[backend/business_app/model_catalog.py:108](<../../backend/business_app/model_catalog.py#L108>)；表：model_registry。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `listModels` | `GET /api/v1/models` | limit（可选）、cursor（可选） | `list_models`；[backend/business_app/model_catalog_router.py:34](<../../backend/business_app/model_catalog_router.py#L34>) |
| `getModelHealth` | `GET /api/v1/models/{id}/health` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `rolloutModel` | `POST /api/v1/models/{id}/rollouts` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t061"></a>
## T061 定义风险标签和版本管理

任务卡：[tasks/algorithm/T061.md](<../../tasks/algorithm/T061.md>)；分组：风险识别与篡改取证；源责任角色：业务/后端；实际负责人：未确定。

原工作范围：建立多标签体系、层级、定义、示例、阈值和版本。

原接口/数据约定：risk_taxonomy、risk_label、threshold_policy。

源依赖：T021,T052；执行依赖候选：T021、T052；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成定义风险标签和版本管理的交付、异常/权限测试和源验收

表与创建源码：

- `mt.policy_registry`：标签阈值流程保留等策略；[backend/business_migrations/0001_business_baseline.sql:133](<../../backend/business_migrations/0001_business_baseline.sql#L133>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：policy_registry。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createPolicy` | `POST /api/v1/policies` | 无 | `create_policy`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>) |
| `listPolicies` | `GET /api/v1/policies` | limit（可选）、cursor（可选） | `list_policies`；[backend/business_app/controls/router.py:639](<../../backend/business_app/controls/router.py#L639>) |


<a id="t062"></a>
## T062 接入图片多标签分类模型

任务卡：[tasks/algorithm/T062.md](<../../tasks/algorithm/T062.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：实现图片风险分类适配器和证据生成。

原接口/数据约定：capability=risk.image_classification。

源依赖：T053,T061,T041；执行依赖候选：T053、T061、T041；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入图片多标签分类模型的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t063"></a>
## T063 接入敏感目标检测模型

任务卡：[tasks/algorithm/T063.md](<../../tasks/algorithm/T063.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：检测火焰、烟雾、危险物品、事故车辆和敏感标识。

原接口/数据约定：ObjectFinding{label,bbox,score,frame_id}。

源依赖：T053,T061,T046；执行依赖候选：T053、T061、T046；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入敏感目标检测模型的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t064"></a>
## T064 接入视频行为识别模型

任务卡：[tasks/algorithm/T064.md](<../../tasks/algorithm/T064.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：对2～8秒窗口识别打斗、追逐、跌倒、碰撞和爆炸等事件。

原接口/数据约定：TemporalFinding{label,start_ms,end_ms,score}。

源依赖：T053,T050；执行依赖候选：T053、T050；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入视频行为识别模型的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t065"></a>
## T065 接入音频事件识别模型

任务卡：[tasks/algorithm/T065.md](<../../tasks/algorithm/T065.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：识别爆炸、撞击、呼喊等音频事件。

原接口/数据约定：AudioFinding{label,start_ms,end_ms,score}。

源依赖：T047,T053；执行依赖候选：T047、T053；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入音频事件识别模型的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t066"></a>
## T066 实现多模态时间对齐

任务卡：[tasks/algorithm/T066.md](<../../tasks/algorithm/T066.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：将视觉、目标、动作、OCR、ASR和音频事件映射到统一窗口。

原接口/数据约定：AlignedWindow{modalities,start_ms,end_ms}。

源依赖：T048,T049,T063,T064,T065；执行依赖候选：T048、T049、T063、T064、T065；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成多模态时间对齐的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t067"></a>
## T067 实现跨模态矛盾检测

任务卡：[tasks/algorithm/T067.md](<../../tasks/algorithm/T067.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：判断标题/字幕/语音主张与画面事件的一致性。

原接口/数据约定：ConsistencyFinding{claim_ids,visual_ids,relation,score}。

源依赖：T066,T053；执行依赖候选：T066、T053；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成跨模态矛盾检测的交付、异常/权限测试和源验收

表与创建源码：

- `mt.claim`：结构化主张与来源；[backend/business_migrations/0001_business_baseline.sql:696](<../../backend/business_migrations/0001_business_baseline.sql#L696>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t068"></a>
## T068 实现综合风险融合与校准

任务卡：[tasks/algorithm/T068.md](<../../tasks/algorithm/T068.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：融合多模态结果、业务规则和概率校准。

原接口/数据约定：RiskAssessment{category,raw_score,calibrated_score,evidence_ids}。

源依赖：T062-T067；执行依赖候选：T062、T063、T064、T065、T066、T067；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成综合风险融合与校准的交付、异常/权限测试和源验收

表与创建源码：

- `mt.policy_registry`：标签阈值流程保留等策略；[backend/business_migrations/0001_business_baseline.sql:133](<../../backend/business_migrations/0001_business_baseline.sql#L133>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：policy_registry。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createPolicy` | `POST /api/v1/policies` | 无 | `create_policy`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>) |
| `listPolicies` | `GET /api/v1/policies` | limit（可选）、cursor（可选） | `list_policies`；[backend/business_app/controls/router.py:639](<../../backend/business_app/controls/router.py#L639>) |


<a id="t069"></a>
## T069 实现风险转人工规则

任务卡：[tasks/algorithm/T069.md](<../../tasks/algorithm/T069.md>)；分组：风险识别与篡改取证；源责任角色：后端/业务；实际负责人：未确定。

原工作范围：对高风险低置信、模型冲突、分布外和强制类别进入复核。

原接口/数据约定：ReviewTrigger{reason,priority,evidence_ids}。

源依赖：T068,T033；执行依赖候选：T068、T033；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成风险转人工规则的交付、异常/权限测试和源验收

表与创建源码：

- `mt.policy_registry`：标签阈值流程保留等策略；[backend/business_migrations/0001_business_baseline.sql:133](<../../backend/business_migrations/0001_business_baseline.sql#L133>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：policy_registry。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createPolicy` | `POST /api/v1/policies` | 无 | `create_policy`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>) |
| `listPolicies` | `GET /api/v1/policies` | limit（可选）、cursor（可选） | `list_policies`；[backend/business_app/controls/router.py:639](<../../backend/business_app/controls/router.py#L639>) |


<a id="t070"></a>
## T070 开发风险识别研判界面

任务卡：[tasks/frontend/T070.md](<../../tasks/frontend/T070.md>)；分组：风险识别与篡改取证；源责任角色：前端；实际负责人：未确定。

原工作范围：播放器、时间轴、目标框、文本和证据卡片联动。

原接口/数据约定：GET /analysis/tasks/{id}/risk-findings。

源依赖：T050,T068,T069；执行依赖候选：T050、T068、T069；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成开发风险识别研判界面的交付、异常/权限测试和源验收

表与创建源码：

- `mt.finding_evidence`：发现与证据多对多；[backend/business_migrations/0001_business_baseline.sql:1321](<../../backend/business_migrations/0001_business_baseline.sql#L1321>)。本清单不证明运行库已采用。
- `mt.risk_finding`：风险候选发现；[backend/business_migrations/0001_business_baseline.sql:1185](<../../backend/business_migrations/0001_business_baseline.sql#L1185>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getRiskFindings` | `GET /api/v1/analysis/tasks/{id}/risk-findings` | history（可选） | `risk`；[backend/business_app/history/router.py:117](<../../backend/business_app/history/router.py#L117>) |


<a id="t071"></a>
## T071 实现图片取证基础特征

任务卡：[tasks/algorithm/T071.md](<../../tasks/algorithm/T071.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：从受控只读原件提取JPEG量化/EXIF/容器痕迹，噪声及像素特征按验证解码/缩放版本处理；不从标准化副本反推原始取证信号。

原接口/数据约定：ImageForensicFeatures。

源依赖：T041,T043；执行依赖候选：T041、T043；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成图片取证基础特征的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t072"></a>
## T072 接入图片篡改区域模型

任务卡：[tasks/algorithm/T072.md](<../../tasks/algorithm/T072.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：接入许可和环境可接受的取证模型；原TruFor采用RGB与学习噪声指纹并输出整图/定位/可靠性。项目三分支扩展单列训练消融，未校准不称概率。

原接口/数据约定：TamperFinding{type,score,mask_key,reliability_key}。

源依赖：T053,T071；执行依赖候选：T053、T071；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入图片篡改区域模型的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t073"></a>
## T073 实现复制粘贴与局部生成分类

任务卡：[tasks/algorithm/T073.md](<../../tasks/algorithm/T073.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：综合区域、噪声、几何和语义特征区分篡改类型。

原接口/数据约定：tamper_type与type_score。

源依赖：T071,T072；执行依赖候选：T071、T072；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成复制粘贴与局部生成分类的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t074"></a>
## T074 实现视频时间结构异常检测

任务卡：[tasks/algorithm/T074.md](<../../tasks/algorithm/T074.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：分析帧间相似、光流、时间戳、GOP、重复帧和音频连续性。

原接口/数据约定：TemporalTamperFinding。

源依赖：T042,T047；执行依赖候选：T042、T047；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成视频时间结构异常检测的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t075"></a>
## T075 实现视频空间篡改跟踪

任务卡：[tasks/algorithm/T075.md](<../../tasks/algorithm/T075.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：将逐帧篡改区域在视频中跟踪并聚合为时间段。

原接口/数据约定：TrackedTamperRegion{track_id,start_ms,end_ms,masks}。

源依赖：T072,T050；执行依赖候选：T072、T050；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成视频空间篡改跟踪的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t076"></a>
## T076 接入深度伪造与音画同步检测

任务卡：[tasks/algorithm/T076.md](<../../tasks/algorithm/T076.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：检测换脸、人脸时序异常、口型语音不同步和音轨替换。

原接口/数据约定：DeepfakeFinding与AVSyncFinding。

源依赖：T053,T047,T050；执行依赖候选：T053、T047、T050；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成接入深度伪造与音画同步检测的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t077"></a>
## T077 实现篡改多证据融合

任务卡：[tasks/algorithm/T077.md](<../../tasks/algorithm/T077.md>)；分组：风险识别与篡改取证；源责任角色：算法；实际负责人：未确定。

原工作范围：融合空间、时间、编码、元数据和音视频证据。

原接口/数据约定：ForensicAssessment{findings,evidence_ids,reliability}。

源依赖：T072-T076；执行依赖候选：T072、T073、T074、T075、T076；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成篡改多证据融合的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t078"></a>
## T078 开发篡改取证界面

任务卡：[tasks/frontend/T078.md](<../../tasks/frontend/T078.md>)；分组：风险识别与篡改取证；源责任角色：前端；实际负责人：未确定。

原工作范围：展示热力图、可靠性图、时间点、区域轨迹、GOP和音频异常。

原接口/数据约定：GET /analysis/tasks/{id}/forensics。

源依赖：T077,T050；执行依赖候选：T077、T050；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成开发篡改取证界面的交付、异常/权限测试和源验收

表与创建源码：

- `mt.finding_evidence`：发现与证据多对多；[backend/business_migrations/0001_business_baseline.sql:1321](<../../backend/business_migrations/0001_business_baseline.sql#L1321>)。本清单不证明运行库已采用。
- `mt.tamper_finding`：疑似篡改发现；[backend/business_migrations/0001_business_baseline.sql:1217](<../../backend/business_migrations/0001_business_baseline.sql#L1217>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getForensics` | `GET /api/v1/analysis/tasks/{id}/forensics` | history（可选） | `forensics`；[backend/business_app/history/router.py:122](<../../backend/business_app/history/router.py#L122>) |


<a id="t079"></a>
## T079 实现图片感知哈希特征

任务卡：[tasks/algorithm/T079.md](<../../tasks/algorithm/T079.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：计算pHash/PDQ等特征并版本化保存。

原接口/数据约定：feature表；HashFeature。

源依赖：T041,T020；执行依赖候选：T041、T020；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成图片感知哈希特征的交付、异常/权限测试和源验收

表与创建源码：

- `mt.feature`：模型特征元数据；[backend/business_migrations/0001_business_baseline.sql:721](<../../backend/business_migrations/0001_business_baseline.sql#L721>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t080"></a>
## T080 实现视觉与复制检测向量生成

任务卡：[tasks/algorithm/T080.md](<../../tasks/algorithm/T080.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：为图片和关键帧生成语义向量与复制检测向量。

原接口/数据约定：EmbeddingFeature{model_version,dimension,vector_ref}。

源依赖：T053,T041,T046；执行依赖候选：T053、T041、T046；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成视觉与复制检测向量生成的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t081"></a>
## T081 建立Milvus索引与版本管理

任务卡：[tasks/algorithm/T081.md](<../../tasks/algorithm/T081.md>)；分组：图片视频检索、首发及传播；源责任角色：数据/算法平台；实际负责人：未确定。

原工作范围：按模型/预处理/维数/度量管理collection、索引版本和过滤字段；构建校验后切换，回滚不混合向量。

原接口/数据约定：VectorIndexRegistry。

源依赖：T080；执行依赖候选：T080；依赖是否具备仍需实际核验。

当前已验证范围：少量SQL向量检索夹具已验证

未完成事项：实施正式向量索引及写入/过滤/重建接口和规模测试；补真实业务向量、授权过滤及Milvus等正式选型实测，不把3条SQL向量当生产索引

表与创建源码：

- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.index_registry`：索引版本不混向量；[backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getIndex` | `GET /api/v1/indices/{id}` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `switchIndex` | `POST /api/v1/indices/{id}/switch` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t082"></a>
## T082 实现图片多路候选召回

任务卡：[tasks/algorithm/T082.md](<../../tasks/algorithm/T082.md>)；分组：图片视频检索、首发及传播；源责任角色：算法/后端；实际负责人：未确定。

原工作范围：并行执行SHA-256、哈希、复制向量和语义向量召回并融合排名。

原接口/数据约定：POST /search/image；Candidate列表。

源依赖：T027,T079-T081；执行依赖候选：T027、T079、T080、T081；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成图片多路候选召回的交付、异常/权限测试和源验收

表与创建源码：

- `mt.index_registry`：索引版本不混向量；[backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>)。本清单不证明运行库已采用。
- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.search_job`：异步检索任务；[backend/business_migrations/0001_business_baseline.sql:773](<../../backend/business_migrations/0001_business_baseline.sql#L773>)。本清单不证明运行库已采用。
- `mt.source_match`：同源或片段映射候选；[backend/business_migrations/0001_business_baseline.sql:899](<../../backend/business_migrations/0001_business_baseline.sql#L899>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `searchImage` | `POST /api/v1/search/image` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `getSearchJob` | `GET /api/v1/search/jobs/{id}` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t083"></a>
## T083 实现局部特征提取与匹配

任务卡：[tasks/algorithm/T083.md](<../../tasks/algorithm/T083.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：集成SIFT或SuperPoint/LightGlue，输出匹配点。

原接口/数据约定：LocalMatch{query_points,candidate_points,scores}。

源依赖：T041；执行依赖候选：T041；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成局部特征提取与匹配的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t084"></a>
## T084 实现RANSAC几何验证

任务卡：[tasks/algorithm/T084.md](<../../tasks/algorithm/T084.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：估计单应矩阵、内点率、覆盖率、旋转和缩放。

原接口/数据约定：GeometryEvidence。

源依赖：T082,T083；执行依赖候选：T082、T083；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成RANSAC几何验证的交付、异常/权限测试和源验收

表与创建源码：

- `mt.index_registry`：索引版本不混向量；[backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>)。本清单不证明运行库已采用。
- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.source_match`：同源或片段映射候选；[backend/business_migrations/0001_business_baseline.sql:899](<../../backend/business_migrations/0001_business_baseline.sql#L899>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `searchImage` | `POST /api/v1/search/image` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t085"></a>
## T085 实现图片局部区域检索

任务卡：[tasks/algorithm/T085.md](<../../tasks/algorithm/T085.md>)；分组：图片视频检索、首发及传播；源责任角色：前后端/算法；实际负责人：未确定。

原工作范围：支持用户框选查询区域并检索图片或视频帧。

原接口/数据约定：POST /search/image-region。

源依赖：T082,T084；执行依赖候选：T082、T084；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成图片局部区域检索的交付、异常/权限测试和源验收

表与创建源码：

- `mt.index_registry`：索引版本不混向量；[backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>)。本清单不证明运行库已采用。
- `mt.media_asset`：原始或派生媒体；[backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>)。本清单不证明运行库已采用。
- `mt.search_job`：异步检索任务；[backend/business_migrations/0001_business_baseline.sql:773](<../../backend/business_migrations/0001_business_baseline.sql#L773>)。本清单不证明运行库已采用。
- `mt.source_match`：同源或片段映射候选；[backend/business_migrations/0001_business_baseline.sql:899](<../../backend/business_migrations/0001_business_baseline.sql#L899>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：media_asset。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：media_asset。
- `business_app.controls.approvals.Approvals.bind(self, connection, scope, item, *, shared)`；[backend/business_app/controls/approvals.py:40](<../../backend/business_app/controls/approvals.py#L40>)；表：media_asset。
- `business_app.controls.execution.Execution.authorize(self, scope, task_id)`；[backend/business_app/controls/execution.py:45](<../../backend/business_app/controls/execution.py#L45>)；表：media_asset。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：media_asset。
- `business_app.controls.operation_tokens.OperationTokens._source_snapshot(self, connection, scope, task_id)`；[backend/business_app/controls/operation_tokens.py:167](<../../backend/business_app/controls/operation_tokens.py#L167>)；表：media_asset。
- `business_app.controls.router.pending_reviews(request, case_id, cursor, limit)`；[backend/business_app/controls/router.py:169](<../../backend/business_app/controls/router.py#L169>)；表：media_asset。
- `business_app.controls.router.get_import(request, id)`；[backend/business_app/controls/router.py:470](<../../backend/business_app/controls/router.py#L470>)；表：media_asset。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：media_asset。
- `business_app.history.repository.ResultRepository.append_snapshot(self, scope, snapshot)`；[backend/business_app/history/repository.py:125](<../../backend/business_app/history/repository.py#L125>)；表：media_asset。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：media_asset。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：media_asset。
- `business_app.uploads.service.UploadService.status(self, request, upload_id)`；[backend/business_app/uploads/service.py:111](<../../backend/business_app/uploads/service.py#L111>)；表：media_asset。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：media_asset。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `searchImage` | `POST /api/v1/search/image` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `searchImageRegion` | `POST /api/v1/search/image-region` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `getSearchJob` | `GET /api/v1/search/jobs/{id}` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t086"></a>
## T086 实现视频帧检索候选聚合

任务卡：[tasks/algorithm/T086.md](<../../tasks/algorithm/T086.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：按来源视频聚合关键帧命中、覆盖率、连续性和相似度。

原接口/数据约定：VideoCandidateSummary。

源依赖：T080-T082；执行依赖候选：T080、T081、T082；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成视频帧检索候选聚合的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t087"></a>
## T087 实现视频相似度矩阵构建

任务卡：[tasks/algorithm/T087.md](<../../tasks/algorithm/T087.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：构建查询与候选关键帧余弦相似度矩阵并压缩存储。

原接口/数据约定：SimilarityMatrix元数据与对象键。

源依赖：T086；执行依赖候选：T086；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成视频相似度矩阵构建的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t088"></a>
## T088 实现局部DTW与倒放对齐

任务卡：[tasks/algorithm/T088.md](<../../tasks/algorithm/T088.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：支持正常、变速、倒放和局部片段的序列对齐。

原接口/数据约定：TemporalAlignment{query_range,source_range,path,speed,direction,score}。

源依赖：T087；执行依赖候选：T087；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成局部DTW与倒放对齐的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t089"></a>
## T089 实现多源拼接来源映射

任务卡：[tasks/algorithm/T089.md](<../../tasks/algorithm/T089.md>)；分组：图片视频检索、首发及传播；源责任角色：算法/后端；实际负责人：未确定。

原工作范围：按镜头独立检索并合并为查询片段到多个来源的映射。

原接口/数据约定：POST /search/video；SourceMapping列表。

源依赖：T044,T088；执行依赖候选：T044、T088；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成多源拼接来源映射的交付、异常/权限测试和源验收

表与创建源码：

- `mt.index_registry`：索引版本不混向量；[backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>)。本清单不证明运行库已采用。
- `mt.search_job`：异步检索任务；[backend/business_migrations/0001_business_baseline.sql:773](<../../backend/business_migrations/0001_business_baseline.sql#L773>)。本清单不证明运行库已采用。
- `mt.source_match`：同源或片段映射候选；[backend/business_migrations/0001_business_baseline.sql:899](<../../backend/business_migrations/0001_business_baseline.sql#L899>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `searchVideo` | `POST /api/v1/search/video` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `getSearchJob` | `GET /api/v1/search/jobs/{id}` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t090"></a>
## T090 实现高可信同源内容聚类

任务卡：[tasks/backend/T090.md](<../../tasks/backend/T090.md>)；分组：图片视频检索、首发及传播；源责任角色：算法/后端；实际负责人：未确定。

原工作范围：只使用通过几何或时序验证的关系构建内容簇。

原接口/数据约定：content_cluster/cluster_member及类型化关系：完全重复、整内容近重复、局部复制、来源包含、片段映射；各自版本与覆盖依据。

源依赖：T084,T089；执行依赖候选：T084、T089；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成高可信同源内容聚类的交付、异常/权限测试和源验收

表与创建源码：

- `mt.content_cluster`：高可信整内容簇；[backend/business_migrations/0001_business_baseline.sql:252](<../../backend/business_migrations/0001_business_baseline.sql#L252>)。本清单不证明运行库已采用。
- `mt.cluster_member`：簇成员整内容证据；[backend/business_migrations/0001_business_baseline.sql:1272](<../../backend/business_migrations/0001_business_baseline.sql#L1272>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.history.repository.ResultRepository.persist_ranking(self, connection, scope, key, response)`；[backend/business_app/history/repository.py:221](<../../backend/business_app/history/repository.py#L221>)；表：cluster_member、content_cluster。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t091"></a>
## T091 实现首发排序特征工程

任务卡：[tasks/backend/T091.md](<../../tasks/backend/T091.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：计算时间可信度、完整度、质量、音轨、水印、字幕、账号和图特征。

原接口/数据约定：FirstSourceFeatureSet。

源依赖：T090,T021；执行依赖候选：T090、T021；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成首发排序特征工程的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t092"></a>
## T092 训练和注册首发排序模型

任务卡：[tasks/backend/T092.md](<../../tasks/backend/T092.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：使用T164或等价已核查首发簇清单、参考来源和簇级切分训练LambdaMART及基线；验证/校准集调参，锁候选后受控独立评测。

原接口/数据约定：model capability=first_source_rank；评测报告。

源依赖：T091,T058；执行依赖候选：T091、T058、T164；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成训练和注册首发排序模型的交付、异常/权限测试和源验收

**范围外依赖**：T164；不得因本清单包含当前任务而自动扩展授权。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t093"></a>
## T093 实现首发候选查询服务

任务卡：[tasks/backend/T093.md](<../../tasks/backend/T093.md>)；分组：图片视频检索、首发及传播；源责任角色：后端；实际负责人：未确定。

原工作范围：返回Top-3候选、概率、不确定性和支持/反对证据。

原接口/数据约定：GET /clusters/{id}/first-source。

源依赖：T090-T092；执行依赖候选：T090、T091、T092；依赖是否具备仍需实际核验。

当前已验证范围：首发历史固定运行与既有候选排名读取已有验证

未完成事项：实现真实观察范围内首发排序生产与不确定性处理；补时区、缺失时间、并列及授权边界；读取已有排名不等于排序算法已运行

表与创建源码：

- `mt.cluster_member`：簇成员整内容证据；[backend/business_migrations/0001_business_baseline.sql:1272](<../../backend/business_migrations/0001_business_baseline.sql#L1272>)。本清单不证明运行库已采用。
- `mt.content_cluster`：高可信整内容簇；[backend/business_migrations/0001_business_baseline.sql:252](<../../backend/business_migrations/0001_business_baseline.sql#L252>)。本清单不证明运行库已采用。
- `mt.first_source_candidate`：首发候选及覆盖范围；[backend/business_migrations/0001_business_baseline.sql:1455](<../../backend/business_migrations/0001_business_baseline.sql#L1455>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.history.repository.ResultRepository.persist_ranking(self, connection, scope, key, response)`；[backend/business_app/history/repository.py:221](<../../backend/business_app/history/repository.py#L221>)；表：cluster_member、content_cluster、first_source_candidate。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getFirstSource` | `GET /api/v1/clusters/{id}/first-source` | ranking_id（可选）、history（可选） | `first_source`；[backend/business_app/history/router.py:137](<../../backend/business_app/history/router.py#L137>) |


<a id="t094"></a>
## T094 设计传播图谱数据模型

任务卡：[tasks/backend/T094.md](<../../tasks/backend/T094.md>)；分组：图片视频检索、首发及传播；源责任角色：数据/架构；实际负责人：未确定。

原工作范围：定义内容、账号、平台、事件、机构、地点、话题和关系证据。

原接口/数据约定：图Schema与关系类型字典。

源依赖：T090；执行依赖候选：T090；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成设计传播图谱数据模型的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t095"></a>
## T095 实现传播图谱写入与查询

任务卡：[tasks/backend/T095.md](<../../tasks/backend/T095.md>)；分组：图片视频检索、首发及传播；源责任角色：后端；实际负责人：未确定。

原工作范围：将发布、转发、同源、搬运和篡改关系写图并查询路径。

原接口/数据约定：GET /propagation/{cluster_id}；GraphRepository。

源依赖：T094；执行依赖候选：T094；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成传播图谱写入与查询的交付、异常/权限测试和源验收

表与创建源码：

- `mt.propagation_edge`：显式推断传播边；[backend/business_migrations/0001_business_baseline.sql:616](<../../backend/business_migrations/0001_business_baseline.sql#L616>)。本清单不证明运行库已采用。
- `mt.propagation_node`：传播图节点；[backend/business_migrations/0001_business_baseline.sql:563](<../../backend/business_migrations/0001_business_baseline.sql#L563>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getPropagation` | `GET /api/v1/propagation/{cluster_id}` | history（可选） | `propagation`；[backend/business_app/history/router.py:142](<../../backend/business_app/history/router.py#L142>) |


<a id="t096"></a>
## T096 实现隐式传播关系推断

任务卡：[tasks/backend/T096.md](<../../tasks/backend/T096.md>)；分组：图片视频检索、首发及传播；源责任角色：算法；实际负责人：未确定。

原工作范围：根据同源、时间方向、水印、字幕和账号关系计算推断边。

原接口/数据约定：InferredEdge{probability,evidence_ids,model_version}。

源依赖：T084,T089,T095；执行依赖候选：T084、T089、T095；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成隐式传播关系推断的交付、异常/权限测试和源验收

表与创建源码：

- `mt.propagation_edge`：显式推断传播边；[backend/business_migrations/0001_business_baseline.sql:616](<../../backend/business_migrations/0001_business_baseline.sql#L616>)。本清单不证明运行库已采用。
- `mt.review_record`：业务复核事实；[backend/business_migrations/0001_business_baseline.sql:1158](<../../backend/business_migrations/0001_business_baseline.sql#L1158>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.reviews.Reviews.context(self, connection, scope, task_id, *, lock)`；[backend/business_app/controls/reviews.py:34](<../../backend/business_app/controls/reviews.py#L34>)；表：review_record。
- `business_app.controls.reviews.Reviews.create(self, scope, body, request, key)`；[backend/business_app/controls/reviews.py:101](<../../backend/business_app/controls/reviews.py#L101>)；表：review_record。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `decidePropagationEdge` | `POST /api/v1/propagation/edges/{id}/decisions` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t097"></a>
## T097 开发传播时间线和图谱界面

任务卡：[tasks/frontend/T097.md](<../../tasks/frontend/T097.md>)；分组：图片视频检索、首发及传播；源责任角色：前端；实际负责人：未确定。

原工作范围：联动展示节点、关系、时间线、版本差异和关键节点。

原接口/数据约定：传播图查询接口。

源依赖：T093,T095,T096；执行依赖候选：T093、T095、T096；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成开发传播时间线和图谱界面的交付、异常/权限测试和源验收

表与创建源码：

- `mt.propagation_edge`：显式推断传播边；[backend/business_migrations/0001_business_baseline.sql:616](<../../backend/business_migrations/0001_business_baseline.sql#L616>)。本清单不证明运行库已采用。
- `mt.propagation_node`：传播图节点；[backend/business_migrations/0001_business_baseline.sql:563](<../../backend/business_migrations/0001_business_baseline.sql#L563>)。本清单不证明运行库已采用。
- `mt.review_record`：业务复核事实；[backend/business_migrations/0001_business_baseline.sql:1158](<../../backend/business_migrations/0001_business_baseline.sql#L1158>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.reviews.Reviews.context(self, connection, scope, task_id, *, lock)`；[backend/business_app/controls/reviews.py:34](<../../backend/business_app/controls/reviews.py#L34>)；表：review_record。
- `business_app.controls.reviews.Reviews.create(self, scope, body, request, key)`；[backend/business_app/controls/reviews.py:101](<../../backend/business_app/controls/reviews.py#L101>)；表：review_record。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getPropagation` | `GET /api/v1/propagation/{cluster_id}` | history（可选） | `propagation`；[backend/business_app/history/router.py:142](<../../backend/business_app/history/router.py#L142>) |
| `decidePropagationEdge` | `POST /api/v1/propagation/edges/{id}/decisions` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t098"></a>
## T098 实现结构化主张抽取服务

任务卡：[tasks/algorithm/T098.md](<../../tasks/algorithm/T098.md>)；分组：主张核查、证据、复核及报告；源责任角色：大模型/后端；实际负责人：未确定。

原工作范围：从标题、正文、OCR和ASR抽取主体、行为、时间、地点和结果。

原接口/数据约定：POST /claims/extract；Claim含source_segment_ids。

源依赖：T048,T049,T053；执行依赖候选：T048、T049、T053；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成结构化主张抽取服务的交付、异常/权限测试和源验收

表与创建源码：

- `mt.claim`：结构化主张与来源；[backend/business_migrations/0001_business_baseline.sql:696](<../../backend/business_migrations/0001_business_baseline.sql#L696>)。本清单不证明运行库已采用。
- `mt.text_segment`：OCR ASR字幕原文；[backend/business_migrations/0001_business_baseline.sql:818](<../../backend/business_migrations/0001_business_baseline.sql#L818>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `extractClaims` | `POST /api/v1/claims/extract` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t099"></a>
## T099 实现权威证据检索与关系判断

任务卡：[tasks/algorithm/T099.md](<../../tasks/algorithm/T099.md>)；分组：主张核查、证据、复核及报告；源责任角色：大模型/检索；实际负责人：未确定。

原工作范围：检索白名单证据库并判断支持、反驳、部分支持、无关或不足。

原接口/数据约定：POST /claims/{id}/verify；EvidenceRelation。

源依赖：T098,T021；执行依赖候选：T098、T021；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成权威证据检索与关系判断的交付、异常/权限测试和源验收

表与创建源码：

- `mt.claim`：结构化主张与来源；[backend/business_migrations/0001_business_baseline.sql:696](<../../backend/business_migrations/0001_business_baseline.sql#L696>)。本清单不证明运行库已采用。
- `mt.claim_evidence_relation`：主张证据关系；[backend/business_migrations/0001_business_baseline.sql:1249](<../../backend/business_migrations/0001_business_baseline.sql#L1249>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `verifyClaim` | `POST /api/v1/claims/{id}/verify` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t100"></a>
## T100 实现统一证据对象模型

任务卡：[tasks/backend/T100.md](<../../tasks/backend/T100.md>)；分组：主张核查、证据、复核及报告；源责任角色：后端；实际负责人：未确定。

原工作范围：统一帧、区域、时间段、匹配、文本、页面截图和模型证据。

原接口/数据约定：evidence_item表与EvidenceService。

源依赖：T051,T017,T020；执行依赖候选：T051、T017、T020；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成统一证据对象模型的交付、异常/权限测试和源验收

表与创建源码：

- `mt.evidence_item`：证据事实版本；[backend/business_migrations/0001_business_baseline.sql:1064](<../../backend/business_migrations/0001_business_baseline.sql#L1064>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：evidence_item。
- `business_app.history.repository.ResultRepository.persist_ranking(self, connection, scope, key, response)`；[backend/business_app/history/repository.py:221](<../../backend/business_app/history/repository.py#L221>)；表：evidence_item。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：evidence_item。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：evidence_item。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t101"></a>
## T101 实现风险与取证证据卡片接口

任务卡：[tasks/backend/T101.md](<../../tasks/backend/T101.md>)；分组：主张核查、证据、复核及报告；源责任角色：后端；实际负责人：徐昌胜。

原工作范围：将算法结果转换为统一证据卡片。

原接口/数据约定：GET /analysis/tasks/{id}/evidence。

源依赖：T068,T077,T084,T089,T100；执行依赖候选：T068、T077、T084、T089、T100；依赖是否具备仍需实际核验。

当前已验证范围：风险/取证/证据等固定历史结果读取子范围已有验证；既有getTaskEvidence显式limit/cursor按完整固定投影分页，省略参数保留旧响应；游标绑定主体/单位/案件/任务/运行/结果/limit、全投影摘要及位置，每页仍经当前授权和真实仓库校验。上游未取齐拒绝503，不回退最新。59纯测试及65相邻测试初轮通过，11项HTTP在修正缺运行的测试期望并补缺结果断言后通过，失败探针按预期失败；262文件类型、Ruff通过。不含真实算法producer、过滤或整卡验收。

未完成事项：完整固定投影已实现显式分页及每页当前权限重查；仍需类型/人工状态过滤、真实结果生产/聚合、原件定位与全部详情联动；上游部分投影仍拒绝分页，省略参数保留旧兼容响应。；核对全部真实模型结果、版本/原件映射和部分能力边界；算法/真实producer继续暂缓，不以自建历史测试行冒充真实输出或媒体有效性，完整快照逐页物化不当大数据性能通过。；开发负责人及指定复核人均已由用户确认为徐昌胜；工时、实际日期、本人已复核及源卡逐项验收仍待。责任登记不授予权限或构成独立双人复核。

表与创建源码：

- `mt.evidence_item`：证据事实版本；[backend/business_migrations/0001_business_baseline.sql:1064](<../../backend/business_migrations/0001_business_baseline.sql#L1064>)。本清单不证明运行库已采用。
- `mt.task_evidence`：任务证据引用；[backend/business_migrations/0001_business_baseline.sql:1408](<../../backend/business_migrations/0001_business_baseline.sql#L1408>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：evidence_item。
- `business_app.history.repository.ResultRepository.persist_ranking(self, connection, scope, key, response)`；[backend/business_app/history/repository.py:221](<../../backend/business_app/history/repository.py#L221>)；表：evidence_item。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：evidence_item。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：evidence_item。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getTaskEvidence` | `GET /api/v1/analysis/tasks/{id}/evidence` | limit（可选）、cursor（可选）、history（可选） | `evidence`；[backend/business_app/history/router.py:127](<../../backend/business_app/history/router.py#L127>) |


<a id="t102"></a>
## T102 实现人工复核工作流

任务卡：[tasks/backend/T102.md](<../../tasks/backend/T102.md>)；分组：主张核查、证据、复核及报告；源责任角色：后端；实际负责人：未确定。

原工作范围：按DES §5.4建立业务复核和独立审批请求，支持领取、确认、驳回、退回补证/重算及按获准策略会审；绑定对象、策略和审核版本。

原接口/数据约定：POST /reviews；review_record。

源依赖：T069,T101,T033；执行依赖候选：T069、T101、T033；依赖是否具备仍需实际核验。

当前已验证范围：复核追加写、ETag、固定证据及来源/策略版本子范围已有验证

未完成事项：落实正式复核状态、RETURNED后继、阈值与审批适用规则；补全状态流/前端与真实结果联调、异常/撤销/版本更正回归

表与创建源码：

- `mt.approval_decision`：审批历史决定；[backend/business_migrations/0001_business_baseline.sql:442](<../../backend/business_migrations/0001_business_baseline.sql#L442>)。本清单不证明运行库已采用。
- `mt.approval_request`：按目的独立审批申请；[backend/business_migrations/0001_business_baseline.sql:179](<../../backend/business_migrations/0001_business_baseline.sql#L179>)。本清单不证明运行库已采用。
- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.policy_registry`：标签阈值流程保留等策略；[backend/business_migrations/0001_business_baseline.sql:133](<../../backend/business_migrations/0001_business_baseline.sql#L133>)。本清单不证明运行库已采用。
- `mt.propagation_edge`：显式推断传播边；[backend/business_migrations/0001_business_baseline.sql:616](<../../backend/business_migrations/0001_business_baseline.sql#L616>)。本清单不证明运行库已采用。
- `mt.review_evidence`：复核证据引用；[backend/business_migrations/0001_business_baseline.sql:1388](<../../backend/business_migrations/0001_business_baseline.sql#L1388>)。本清单不证明运行库已采用。
- `mt.review_record`：业务复核事实；[backend/business_migrations/0001_business_baseline.sql:1158](<../../backend/business_migrations/0001_business_baseline.sql#L1158>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.approvals.Approvals.detail(self, connection, scope, identifier, *, lock, shared_binding)`；[backend/business_app/controls/approvals.py:109](<../../backend/business_app/controls/approvals.py#L109>)；表：approval_decision。
- `business_app.controls.approvals.Approvals.create(self, scope, body, request, key)`；[backend/business_app/controls/approvals.py:215](<../../backend/business_app/controls/approvals.py#L215>)；表：approval_request。
- `business_app.controls.approvals.Approvals.decide(self, scope, identifier, body, request, key, *, revoke)`；[backend/business_app/controls/approvals.py:248](<../../backend/business_app/controls/approvals.py#L248>)；表：approval_decision、approval_request。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event。
- `business_app.controls.reviews.Reviews.context(self, connection, scope, task_id, *, lock)`；[backend/business_app/controls/reviews.py:34](<../../backend/business_app/controls/reviews.py#L34>)；表：review_record。
- `business_app.controls.reviews.Reviews.wire(self, connection, identifier)`；[backend/business_app/controls/reviews.py:68](<../../backend/business_app/controls/reviews.py#L68>)；表：review_evidence。
- `business_app.controls.reviews.Reviews.create(self, scope, body, request, key)`；[backend/business_app/controls/reviews.py:101](<../../backend/business_app/controls/reviews.py#L101>)；表：review_evidence、review_record。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event、policy_registry。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `decidePropagationEdge` | `POST /api/v1/propagation/edges/{id}/decisions` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `createReview` | `POST /api/v1/reviews` | 无 | `create_review`；[backend/business_app/controls/router.py:243](<../../backend/business_app/controls/router.py#L243>) |
| `requestApproval` | `POST /api/v1/approvals` | 无 | `request_approval`；[backend/business_app/controls/router.py:118](<../../backend/business_app/controls/router.py#L118>) |
| `decideApproval` | `POST /api/v1/approvals/{id}/decisions` | 无 | `decide_approval`；[backend/business_app/controls/router.py:129](<../../backend/business_app/controls/router.py#L129>) |
| `createPolicy` | `POST /api/v1/policies` | 无 | `create_policy`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>) |


<a id="t103"></a>
## T103 开发人工复核工作台

任务卡：[tasks/frontend/T103.md](<../../tasks/frontend/T103.md>)；分组：主张核查、证据、复核及报告；源责任角色：前端；实际负责人：徐昌胜。

原工作范围：统一展示媒体、时间轴、风险、篡改、来源、传播和审核表单。

原接口/数据约定：复核与证据接口。

源依赖：T070,T078,T097,T102；执行依赖候选：T070、T078、T097、T102；依赖是否具备仍需实际核验。

当前已验证范围：待复核列表、上下文及历史记录后端子范围已有验证；待复核队列选择任务后，通过既有review.read接口读取当前上下文及独立历史分页，校验完整结构与任务绑定；本地身份/权限/案件、任务及页面变化清理旧内容并丢弃晚响应。487项前端及开发/生产各88项传输浏览器通过；不包含复核写入、正式规则、真实权威E2E或整卡验收。；当前上下文或历史复核选择精确任务/运行/结果后读取证据，校验3个历史响应头、17字段及案件版本绑定；支持关联证据编号定位、缺引用及不完整返回提示，时间毫秒半开区间与归一化区域展示。本地身份/范围/来源选择变化清理旧内容及晚响应。665项前端及开发/生产各103项传输浏览器通过；不含媒体字节读取、审批、算法生成或整卡验收。；证据页面显式limit20及精确历史选择，受控下一页保留不透明游标、逐页校验响应头/证据绑定并替换当前页；来源或身份变化及晚响应清理，页内缺引用不当全量不存在，错误不回退。688项前端（含201项证据reader）、开发/生产各114项传输浏览器通过；两模式重叠，不含真实权威E2E、媒体播放或复核写入。；复核表单复用服务端当前上下文及原样强ETag，提交既有ReviewCreate；草稿仅在当前页内存，身份/案件/上下文变化清理。未确认请求冻结body/幂等键/If-Match并仅原请求显式重试，回执严格绑定主体与版本。755项前端、开发/生产各138项传输浏览器通过；不含正式规则/职责提供方、持久草稿、真实权威E2E或任务退回/重算/批准。；对当前所选original且固定引用/证据摘要相等的证据显式读取关联资产，严格核验完整结构及original/VALID、案件、资产和对象版本/摘要；独立asset.read/asset.download权限，复用既有下载工具核验字节大小、SHA-256和ETag后保存；页/选择/重读/身份/离开及摘要阶段变化清理并丢弃晚响应。959项前端、开发/生产各172项传输浏览器通过；仅原件下载UI子范围，不含播放/派生内容、法律效力或真实权威E2E。

未完成事项：已接线上下文、历史、证据分页、复核表单/当前页内存草稿及严格绑定的原始证据原件下载；仍需服务端持久草稿契约、标注、派生证据内容、媒体播放/时间定位及完整结果联动；不将原件下载扩展为播放或所有证据支持。；正式规则及独立职责提供方未接，真实身份/来源/后端组合、批准拒绝一致、退回/撤销、多人步骤和完整流程仍待；四种记录决定不自动改变任务状态、启动重算或批准导出；结构、引用及字节核验不证明来源授权或证据法律效力，传输夹具不等于真实工作流，算法继续暂缓。；实际开发负责人和指定复核人均已确认为徐昌胜；实际工时/日期、本人复核决定和源卡逐项验收仍待。同人兼任不等于独立双人复核，责任登记不授予权限。

表与创建源码：

- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.evidence_item`：证据事实版本；[backend/business_migrations/0001_business_baseline.sql:1064](<../../backend/business_migrations/0001_business_baseline.sql#L1064>)。本清单不证明运行库已采用。
- `mt.review_evidence`：复核证据引用；[backend/business_migrations/0001_business_baseline.sql:1388](<../../backend/business_migrations/0001_business_baseline.sql#L1388>)。本清单不证明运行库已采用。
- `mt.review_record`：业务复核事实；[backend/business_migrations/0001_business_baseline.sql:1158](<../../backend/business_migrations/0001_business_baseline.sql#L1158>)。本清单不证明运行库已采用。
- `mt.task_evidence`：任务证据引用；[backend/business_migrations/0001_business_baseline.sql:1408](<../../backend/business_migrations/0001_business_baseline.sql#L1408>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event。
- `business_app.controls.reviews.Reviews.context(self, connection, scope, task_id, *, lock)`；[backend/business_app/controls/reviews.py:34](<../../backend/business_app/controls/reviews.py#L34>)；表：review_record。
- `business_app.controls.reviews.Reviews.wire(self, connection, identifier)`；[backend/business_app/controls/reviews.py:68](<../../backend/business_app/controls/reviews.py#L68>)；表：review_evidence。
- `business_app.controls.reviews.Reviews.create(self, scope, body, request, key)`；[backend/business_app/controls/reviews.py:101](<../../backend/business_app/controls/reviews.py#L101>)；表：review_evidence、review_record。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：evidence_item。
- `business_app.history.repository.ResultRepository.persist_ranking(self, connection, scope, key, response)`；[backend/business_app/history/repository.py:221](<../../backend/business_app/history/repository.py#L221>)；表：evidence_item。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：evidence_item。
- `business_app.scoped_objects.ScopedObjects._media(self, connection, scope, binding, reference)`；[backend/business_app/scoped_objects.py:140](<../../backend/business_app/scoped_objects.py#L140>)；表：evidence_item。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `getTaskEvidence` | `GET /api/v1/analysis/tasks/{id}/evidence` | limit（可选）、cursor（可选）、history（可选） | `evidence`；[backend/business_app/history/router.py:127](<../../backend/business_app/history/router.py#L127>) |
| `createReview` | `POST /api/v1/reviews` | 无 | `create_review`；[backend/business_app/controls/router.py:243](<../../backend/business_app/controls/router.py#L243>) |


<a id="t104"></a>
## T104 实现证据固化与完整性校验

任务卡：[tasks/backend/T104.md](<../../tasks/backend/T104.md>)；分组：主张核查、证据、复核及报告；源责任角色：后端/安全；实际负责人：未确定。

原工作范围：固化原始文件、结果、截图、日志和模型信息，生成清单哈希。

原接口/数据约定：POST /evidence-packages/{case_id}/seal；manifest。

源依赖：T100,T102,T025；执行依赖候选：T100、T102、T025；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成证据固化与完整性校验的交付、异常/权限测试和源验收

表与创建源码：

- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.evidence_package`：固化证据包版本；[backend/business_migrations/0001_business_baseline.sql:1099](<../../backend/business_migrations/0001_business_baseline.sql#L1099>)。本清单不证明运行库已采用。
- `mt.object_version`：对象版本与摘要清单；[backend/business_migrations/0001_business_baseline.sql:356](<../../backend/business_migrations/0001_business_baseline.sql#L356>)。本清单不证明运行库已采用。
- `mt.package_item`：固化包版本引用；[backend/business_migrations/0001_business_baseline.sql:1344](<../../backend/business_migrations/0001_business_baseline.sql#L1344>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：object_version。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：object_version。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event、object_version。
- `business_app.controls.exports.Exports.content(self, scope, identifier, request)`；[backend/business_app/controls/exports.py:228](<../../backend/business_app/controls/exports.py#L228>)；表：object_version。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：object_version。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：object_version。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：object_version。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：object_version。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：object_version。
- `business_app.scoped_objects.ScopedObjects._registered(connection, scope, reference)`；[backend/business_app/scoped_objects.py:75](<../../backend/business_app/scoped_objects.py#L75>)；表：object_version。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：object_version。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：object_version。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：object_version。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `sealEvidence` | `POST /api/v1/evidence-packages/{case_id}/seal` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t105"></a>
## T105 实现可信时间与签名适配层

任务卡：[tasks/backend/T105.md](<../../tasks/backend/T105.md>)；分组：主张核查、证据、复核及报告；源责任角色：安全/后端；实际负责人：未确定。

原工作范围：定义可信时间和数字签名接口，提供开发环境适配器。

原接口/数据约定：TimestampProvider、Signer接口。

源依赖：T104；执行依赖候选：T104；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成可信时间与签名适配层的交付、异常/权限测试和源验收

表与创建源码：

- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.evidence_package`：固化证据包版本；[backend/business_migrations/0001_business_baseline.sql:1099](<../../backend/business_migrations/0001_business_baseline.sql#L1099>)。本清单不证明运行库已采用。
- `mt.object_version`：对象版本与摘要清单；[backend/business_migrations/0001_business_baseline.sql:356](<../../backend/business_migrations/0001_business_baseline.sql#L356>)。本清单不证明运行库已采用。
- `mt.package_item`：固化包版本引用；[backend/business_migrations/0001_business_baseline.sql:1344](<../../backend/business_migrations/0001_business_baseline.sql#L1344>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.asset_download.AssetDownload.content(self, scope, identifier, request)`；[backend/business_app/asset_download.py:97](<../../backend/business_app/asset_download.py#L97>)；表：object_version。
- `business_app.catalog_reads.CatalogReads.asset(connection, scope, identifier)`；[backend/business_app/catalog_reads.py:40](<../../backend/business_app/catalog_reads.py#L40>)；表：object_version。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event、object_version。
- `business_app.controls.exports.Exports.content(self, scope, identifier, request)`；[backend/business_app/controls/exports.py:228](<../../backend/business_app/controls/exports.py#L228>)；表：object_version。
- `business_app.controls.imports.Imports.create(self, scope, body, request, key)`；[backend/business_app/controls/imports.py:50](<../../backend/business_app/controls/imports.py#L50>)；表：object_version。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.history.repository.ResultRepository.verify_current_inputs(self, connection, scope, snapshot, *, writing)`；[backend/business_app/history/repository.py:50](<../../backend/business_app/history/repository.py#L50>)；表：object_version。
- `business_app.inference.InferenceGateway.check_inputs(self, scope, payload)`；[backend/business_app/inference.py:89](<../../backend/business_app/inference.py#L89>)；表：object_version。
- `business_app.inference.InferenceGateway._finish_response(self, scope, identifier, payload, backend, value, deadline)`；[backend/business_app/inference.py:203](<../../backend/business_app/inference.py#L203>)；表：object_version。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：object_version。
- `business_app.scoped_objects.ScopedObjects._registered(connection, scope, reference)`；[backend/business_app/scoped_objects.py:75](<../../backend/business_app/scoped_objects.py#L75>)；表：object_version。
- `business_app.task_creation_service.TaskCreationService._asset(self, connection, scope, context, execution)`；[backend/business_app/task_creation_service.py:352](<../../backend/business_app/task_creation_service.py#L352>)；表：object_version。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。
- `business_app.uploads.repository.UploadRepository.put_part(self, scope, upload_id, part_no, stored, *, idempotency_key)`；[backend/business_app/uploads/repository.py:161](<../../backend/business_app/uploads/repository.py#L161>)；表：object_version。
- `business_app.uploads.worker.UploadValidationWorker._consume_bound(self, event, scope, upload)`；[backend/business_app/uploads/worker.py:47](<../../backend/business_app/uploads/worker.py#L47>)；表：object_version。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `sealEvidence` | `POST /api/v1/evidence-packages/{case_id}/seal` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t106"></a>
## T106 实现证据约束核查摘要

任务卡：[tasks/backend/T106.md](<../../tasks/backend/T106.md>)；分组：主张核查、证据、复核及报告；源责任角色：大模型/后端；实际负责人：未确定。

原工作范围：生成句级绑定evidence_id的核查摘要。

原接口/数据约定：POST /reports/drafts；句子含evidence_ids。

源依赖：T099,T101,T053；执行依赖候选：T099、T101、T053；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成证据约束核查摘要的交付、异常/权限测试和源验收

表与创建源码：

- `mt.report`：报告生成与下载状态；[backend/business_migrations/0001_business_baseline.sql:1128](<../../backend/business_migrations/0001_business_baseline.sql#L1128>)。本清单不证明运行库已采用。
- `mt.report_evidence`：报告证据引用；[backend/business_migrations/0001_business_baseline.sql:1368](<../../backend/business_migrations/0001_business_baseline.sql#L1368>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：report、report_evidence。
- `business_app.registry_router.get_report(request, id)`；[backend/business_app/registry_router.py:20](<../../backend/business_app/registry_router.py#L20>)；表：report。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createReportDraft` | `POST /api/v1/reports/drafts` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t107"></a>
## T107 实现核查报告生成

任务卡：[tasks/backend/T107.md](<../../tasks/backend/T107.md>)；分组：主张核查、证据、复核及报告；源责任角色：后端；实际负责人：未确定。

原工作范围：按模板生成版本化Word/PDF及证据目录；审批请求、报告展示状态和导出事件分别记录，支持退回、撤销、失效及受控导出。

原接口/数据约定：POST /reports；GET /reports/{id}。

源依赖：T102,T104,T106；执行依赖候选：T102、T104、T106；依赖是否具备仍需实际核验。

当前已验证范围：新增getReport真实数据库元数据读取：报告/证据/案件/任务及运行结果版本严格绑定、固定对象引用、全部证据来源和事务尾授权复核；32项投影/SQL/HTTP/0013升级回滚测试通过。不包含报告生成、渲染或下载。

未完成事项：报告生成生产者、版本化模板/渲染、审批及受控下载、完整证据约束报告验收仍待；getReport读取不替代这些工作

表与创建源码：

- `mt.approval_request`：按目的独立审批申请；[backend/business_migrations/0001_business_baseline.sql:179](<../../backend/business_migrations/0001_business_baseline.sql#L179>)。本清单不证明运行库已采用。
- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.report`：报告生成与下载状态；[backend/business_migrations/0001_business_baseline.sql:1128](<../../backend/business_migrations/0001_business_baseline.sql#L1128>)。本清单不证明运行库已采用。
- `mt.report_evidence`：报告证据引用；[backend/business_migrations/0001_business_baseline.sql:1368](<../../backend/business_migrations/0001_business_baseline.sql#L1368>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.approvals.Approvals.create(self, scope, body, request, key)`；[backend/business_app/controls/approvals.py:215](<../../backend/business_app/controls/approvals.py#L215>)；表：approval_request。
- `business_app.controls.approvals.Approvals.decide(self, scope, identifier, body, request, key, *, revoke)`；[backend/business_app/controls/approvals.py:248](<../../backend/business_app/controls/approvals.py#L248>)；表：approval_request。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.registry_reads.RegistryReads.report(connection, scope, identifier)`；[backend/business_app/registry_reads.py:62](<../../backend/business_app/registry_reads.py#L62>)；表：report、report_evidence。
- `business_app.registry_router.get_report(request, id)`；[backend/business_app/registry_router.py:20](<../../backend/business_app/registry_router.py#L20>)；表：report。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `createReport` | `POST /api/v1/reports` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |
| `getReport` | `GET /api/v1/reports/{id}` | 无 | `get_report`；[backend/business_app/registry_router.py:20](<../../backend/business_app/registry_router.py#L20>) |
| `downloadReport` | `GET /api/v1/reports/{id}/content` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t108"></a>
## T108 实现样本纠错与回流审批

任务卡：[tasks/backend/T108.md](<../../tasks/backend/T108.md>)；分组：主张核查、证据、复核及报告；源责任角色：前后端/算法平台；实际负责人：未确定。

原工作范围：记录纠错申请、训练/评测用途授权及独立回流审批；按获准策略进入训练集、难例库或另行管理的评测集，禁止自动污染冻结测试集。

原接口/数据约定：POST /feedback/samples；approval流程。

源依赖：T102,T058；执行依赖候选：T102、T058；依赖是否具备仍需实际核验。

当前已验证范围：纠错申请/审批快照读取及未落实数据血缘时拒绝APPLIED已有验证

未完成事项：实现实际样本纠错、用途授权及获准数据集写入worker；补脱敏/去重/质检/冻结集隔离与撤销流程；拒绝动作不是回流成功

表与创建源码：

- `mt.approval_decision`：审批历史决定；[backend/business_migrations/0001_business_baseline.sql:442](<../../backend/business_migrations/0001_business_baseline.sql#L442>)。本清单不证明运行库已采用。
- `mt.approval_request`：按目的独立审批申请；[backend/business_migrations/0001_business_baseline.sql:179](<../../backend/business_migrations/0001_business_baseline.sql#L179>)。本清单不证明运行库已采用。
- `mt.audit_event`：追加式审计事实；[backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>)。本清单不证明运行库已采用。
- `mt.feedback_request`：纠错训练用途申请；[backend/business_migrations/0001_business_baseline.sql:1296](<../../backend/business_migrations/0001_business_baseline.sql#L1296>)。本清单不证明运行库已采用。

关联后端方法（仅直接SQL表引用的静态交集，不是完整DAO或任务验收）：

- `business_app.controls.approvals.Approvals.detail(self, connection, scope, identifier, *, lock, shared_binding)`；[backend/business_app/controls/approvals.py:109](<../../backend/business_app/controls/approvals.py#L109>)；表：approval_decision。
- `business_app.controls.approvals.Approvals.create(self, scope, body, request, key)`；[backend/business_app/controls/approvals.py:215](<../../backend/business_app/controls/approvals.py#L215>)；表：approval_request。
- `business_app.controls.approvals.Approvals.decide(self, scope, identifier, body, request, key, *, revoke)`；[backend/business_app/controls/approvals.py:248](<../../backend/business_app/controls/approvals.py#L248>)；表：approval_decision、approval_request。
- `business_app.controls.common.audit(connection, scope, action, kind, identifier, version, request)`；[backend/business_app/controls/common.py:101](<../../backend/business_app/controls/common.py#L101>)；表：audit_event。
- `business_app.controls.exports.Exports._process_bound(self, scope, identifier)`；[backend/business_app/controls/exports.py:123](<../../backend/business_app/controls/exports.py#L123>)；表：audit_event。
- `business_app.controls.router.create_policy(request, body, idempotency_key)`；[backend/business_app/controls/router.py:557](<../../backend/business_app/controls/router.py#L557>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._write(self, connection, scope, context, execution, request_id, idempotency_key)`；[backend/business_app/task_creation_service.py:541](<../../backend/business_app/task_creation_service.py#L541>)；表：audit_event。
- `business_app.task_creation_service.TaskCreationService._collection_receipt(self, connection, scope, context, execution, seed, *, idempotency_key, initial)`；[backend/business_app/task_creation_service.py:692](<../../backend/business_app/task_creation_service.py#L692>)；表：audit_event。

| 操作ID | 契约HTTP方法和路径 | query参数 | 已注册业务Python方法及位置 |
| --- | --- | --- | --- |
| `requestApproval` | `POST /api/v1/approvals` | 无 | `request_approval`；[backend/business_app/controls/router.py:118](<../../backend/business_app/controls/router.py#L118>) |
| `decideApproval` | `POST /api/v1/approvals/{id}/decisions` | 无 | `decide_approval`；[backend/business_app/controls/router.py:129](<../../backend/business_app/controls/router.py#L129>) |
| `requestFeedback` | `POST /api/v1/feedback/samples` | 无 | 未发现显式业务路由注册；不推定其他服务状态 |


<a id="t109"></a>
## T109 建立标注规范与标签质检工具

任务卡：[tasks/data/T109.md](<../../tasks/data/T109.md>)；分组：数据集、训练及评测工具；源责任角色：数据/算法；实际负责人：未确定。

原工作范围：前期按风险标签与证据Schema建立内容/时间/区域/关系标注规范及质量校验；不等待T090完整视频聚类。后期接入内容簇补查，未知关系人工确认。

原接口/数据约定：标注Schema、validator和质量报告。

源依赖：T061,T090,T100；执行依赖候选：T061、T100；依赖是否具备仍需实际核验。

当前已验证范围：已实现D01—D15离线标注结构/格式/时间区域质检、批内UUID规范化重复/冲突、机械确定性抽样及脱敏CLI；101项工具测试及53项开发入口测试在Linux原py310通过。未证明正式标签、真实授权、双人和仲裁。

未完成事项：已有离线结构、边界和机械抽样质检；继续落实正式标签词典/来源用途、真实时间与掩码映射证据、内容簇补查及人工流程，不将Schema通过当业务标签正确。；Schema/边界/批内重复冲突、机械确定性抽样及CLI回归已执行；仍需实际人工抽检、一致性/仲裁及适用真实标注流程的测试。；部分必填/边界、unknown/insufficient已验证；双人独立标注、真实reviewer身份、仲裁及正式口径仍无完整实现/证据，整卡验收未完成。；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t110"></a>
## T110 实现原始素材分组划分

任务卡：[tasks/data/T110.md](<../../tasks/data/T110.md>)；分组：数据集、训练及评测工具；源责任角色：数据/算法；实际负责人：未确定。

原工作范围：按授权来源、原素材/父子编辑血缘、人工已知同源关系先划分；组合素材保守分组防泄漏，T090后补查而非唯一真值。

原接口/数据约定：dataset_split_manifest。

源依赖：T090,T109；执行依赖候选：T019、T021、T109；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成原始素材分组划分的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t111"></a>
## T111 实现可控编辑数据增强流水线

任务卡：[tasks/data/T111.md](<../../tasks/data/T111.md>)；分组：数据集、训练及评测工具；源责任角色：算法；实际负责人：未确定。

原工作范围：生成压缩、裁剪、旋转、镜像、字幕、水印、遮挡、变速、倒放和拼接版本。

原接口/数据约定：augmentation_manifest记录参数与父样本。

源依赖：T109,T110；执行依赖候选：T109、T110；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成可控编辑数据增强流水线的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t112"></a>
## T112 建立难负样本挖掘流程

任务卡：[tasks/data/T112.md](<../../tasks/data/T112.md>)；分组：数据集、训练及评测工具；源责任角色：算法/数据；实际负责人：未确定。

原工作范围：收集语义相似但非同源的图片和视频候选并人工确认。

原接口/数据约定：hard_negative候选和确认状态。

源依赖：T082,T084,T089；执行依赖候选：T082、T084、T089；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成难负样本挖掘流程的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t113"></a>
## T113 实现风险模型训练与评测流水线

任务卡：[tasks/backend/T113.md](<../../tasks/backend/T113.md>)；分组：数据集、训练及评测工具；源责任角色：算法；实际负责人：未确定。

原工作范围：训练多标签分类/融合模型并输出Macro-F1、分类召回和校准结果。

原接口/数据约定：训练配置、模型、模型卡、评测JSON。

源依赖：T062-T068,T110；执行依赖候选：T062、T063、T064、T065、T066、T067、T068、T110；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成风险模型训练与评测流水线的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t114"></a>
## T114 实现篡改模型评测流水线

任务卡：[tasks/backend/T114.md](<../../tasks/backend/T114.md>)；分组：数据集、训练及评测工具；源责任角色：算法；实际负责人：未确定。

原工作范围：评测图片IoU、视频篡改分类型召回和可靠性。

原接口/数据约定：forensics_evaluation报告。

源依赖：T072-T077,T110；执行依赖候选：T072、T073、T074、T075、T076、T077、T110；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成篡改模型评测流水线的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t115"></a>
## T115 实现同源与片段检索评测流水线

任务卡：[tasks/backend/T115.md](<../../tasks/backend/T115.md>)；分组：数据集、训练及评测工具；源责任角色：算法；实际负责人：未确定。

原工作范围：计算Recall@K、MRR、难负误命中率和时间定位误差。

原接口/数据约定：retrieval_evaluation报告。

源依赖：T082-T089,T110；执行依赖候选：T082、T083、T084、T085、T086、T087、T088、T089、T110；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成同源与片段检索评测流水线的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t116"></a>
## T116 实现首发和大模型核查评测

任务卡：[tasks/backend/T116.md](<../../tasks/backend/T116.md>)；分组：数据集、训练及评测工具；源责任角色：算法/大模型；实际负责人：未确定。

原工作范围：评测Top-3、NDCG、校准误差、主张抽取和证据关系。

原接口/数据约定：source_and_claim_evaluation报告。

源依赖：T092,T098,T099,T110；执行依赖候选：T092、T098、T099、T110；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成首发和大模型核查评测的交付、异常/权限测试和源验收

表与创建源码：

- `mt.claim`：结构化主张与来源；[backend/business_migrations/0001_business_baseline.sql:696](<../../backend/business_migrations/0001_business_baseline.sql#L696>)。本清单不证明运行库已采用。

未在直接SQL字面量中找到与这些表相交的方法；动态SQL和间接调用未展开，须继续核对实际实现。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t117"></a>
## T117 建立应用安全自动化扫描

任务卡：[tasks/testing/T117.md](<../../tasks/testing/T117.md>)；分组：安全、监控、恢复及容量验证；源责任角色：安全/DevOps；实际负责人：未确定。

原工作范围：集成依赖、SAST、镜像和密钥扫描。

原接口/数据约定：CI安全jobs与报告。

源依赖：T006；执行依赖候选：T006；依赖是否具备仍需实际核验。

当前已验证范围：密钥检查、Python/npm依赖及独立类型工具扫描已有研发证据

未完成事项：补适用SAST、镜像/系统二进制、Torch覆盖与未托管组件核查；落实软件/模型许可准入和正式修复决定，不以工具无报错认定全系统安全

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t118"></a>
## T118 实施上传与接口安全测试

任务卡：[tasks/testing/T118.md](<../../tasks/testing/T118.md>)；分组：安全、监控、恢复及容量验证；源责任角色：安全/测试；实际负责人：未确定。

原工作范围：覆盖恶意上传、路径穿越、注入、SSRF、重放、限流和越权。

原接口/数据约定：security test suite与报告。

源依赖：T022-T029,T034；执行依赖候选：T022、T023、T024、T025、T026、T027、T028、T029、T034；依赖是否具备仍需实际核验。

当前已验证范围：自建夹具的越权、重放、坏分片、伪媒体及跨案件测试已有验证

未完成事项：补全业务完成后的审批/导出/反馈最终安全复测；补恶意文件、SSRF、限流/大文件资源与正式身份联调及整改闭环

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t119"></a>
## T119 实施大模型安全测试

任务卡：[tasks/testing/T119.md](<../../tasks/testing/T119.md>)；分组：安全、监控、恢复及容量验证；源责任角色：安全/大模型；实际负责人：未确定。

原工作范围：测试提示注入、越权工具调用、证据污染、敏感泄露和无依据生成。

原接口/数据约定：LLM red-team数据集与报告。

源依赖：T098,T099,T106；执行依赖候选：T098、T099、T106；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成实施大模型安全测试的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t120"></a>
## T120 实现监控指标与告警

任务卡：[tasks/backend/T120.md](<../../tasks/backend/T120.md>)；分组：安全、监控、恢复及容量验证；源责任角色：DevOps；实际负责人：未确定。

原工作范围：监控API、队列、任务、GPU、存储、索引、模型和审计服务。

原接口/数据约定：Prometheus指标、Grafana面板、告警规则。

源依赖：T037,T053,T081；执行依赖候选：T037、T053、T081；依赖是否具备仍需实际核验。

当前已验证范围：研发健康与数据卷容量观测已有记录，最近13%且可用约644GiB

未完成事项：实现正式指标采集、仪表盘、告警及分级响应；落实配额/维护人/告警投递并做故障演练；健康查询不等于监控平台

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t121"></a>
## T121 实现备份恢复与灾备演练

任务卡：[tasks/deployment/T121.md](<../../tasks/deployment/T121.md>)；分组：安全、监控、恢复及容量验证；源责任角色：DevOps/数据；实际负责人：未确定。

原工作范围：按批准RPO/RTO实施SQL及对象/模型/配置备份；需要PITR时验证基础备份与连续WAL；隔离恢复后跨存储对账。

原接口/数据约定：备份脚本、恢复Runbook、演练记录。

源依赖：T020,T025,T081,T095,T104；执行依赖候选：T020、T025、T081、T095、T104；依赖是否具备仍需实际核验。

当前已验证范围：开发数据库/对象冷备恢复及业务双历史对账已有实测

未完成事项：落实正式异地目标、RPO/RTO、密钥及恢复授权；实施生产适用全业务异机恢复/PITR演练，开发冷备不能代替生产灾备

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t122"></a>
## T122 执行20并发验收性能测试

任务卡：[tasks/testing/T122.md](<../../tasks/testing/T122.md>)；分组：安全、监控、恢复及容量验证；源责任角色：测试/DevOps；实际负责人：未确定。

原工作范围：保留20混合任务负载档的性能验证任务；正式验收性质与成功率/时延范围按Q-14和Q-13确认。

原接口/数据约定：性能脚本和报告。

源依赖：T107,T120；执行依赖候选：T107、T120；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成执行20并发验收性能测试的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。


<a id="t123"></a>
## T123 执行100并发容量与长稳测试

任务卡：[tasks/testing/T123.md](<../../tasks/testing/T123.md>)；分组：安全、监控、恢复及容量验证；源责任角色：测试/DevOps；实际负责人：未确定。

原工作范围：保留100混合任务负载档的容量与长稳任务；源建议72小时仅为候选，持续时间和正式性质按Q-14确认。

原接口/数据约定：容量报告与扩容建议。

源依赖：T122；执行依赖候选：T122；依赖是否具备仍需实际核验。

当前已验证范围：尚无本任务已验证交付

未完成事项：完成执行100并发容量与长稳测试的交付、异常/权限测试和源验收

未声明直接落库表，不能为填满清单自行增加数据实体。

未声明外部操作ID；内部引擎、模型或工具能力需按源范围实施，不以生成空HTTP接口代替。

## 全部版本化表定义

以下为当前迁移源码，不是已连接数据库的查询结果。

| 表 | 创建迁移与位置 |
| --- | --- |
| `mt.organizations` | [backend/business_migrations/0001_business_baseline.sql:12](<../../backend/business_migrations/0001_business_baseline.sql#L12>) |
| `mt.permissions` | [backend/business_migrations/0001_business_baseline.sql:23](<../../backend/business_migrations/0001_business_baseline.sql#L23>) |
| `mt.roles` | [backend/business_migrations/0001_business_baseline.sql:35](<../../backend/business_migrations/0001_business_baseline.sql#L35>) |
| `mt.cases` | [backend/business_migrations/0001_business_baseline.sql:47](<../../backend/business_migrations/0001_business_baseline.sql#L47>) |
| `mt.dataset_version` | [backend/business_migrations/0001_business_baseline.sql:62](<../../backend/business_migrations/0001_business_baseline.sql#L62>) |
| `mt.index_registry` | [backend/business_migrations/0001_business_baseline.sql:84](<../../backend/business_migrations/0001_business_baseline.sql#L84>) |
| `mt.model_registry` | [backend/business_migrations/0001_business_baseline.sql:106](<../../backend/business_migrations/0001_business_baseline.sql#L106>) |
| `mt.policy_registry` | [backend/business_migrations/0001_business_baseline.sql:133](<../../backend/business_migrations/0001_business_baseline.sql#L133>) |
| `mt.role_permissions` | [backend/business_migrations/0001_business_baseline.sql:153](<../../backend/business_migrations/0001_business_baseline.sql#L153>) |
| `mt.users` | [backend/business_migrations/0001_business_baseline.sql:166](<../../backend/business_migrations/0001_business_baseline.sql#L166>) |
| `mt.approval_request` | [backend/business_migrations/0001_business_baseline.sql:179](<../../backend/business_migrations/0001_business_baseline.sql#L179>) |
| `mt.audit_event` | [backend/business_migrations/0001_business_baseline.sql:210](<../../backend/business_migrations/0001_business_baseline.sql#L210>) |
| `mt.case_membership` | [backend/business_migrations/0001_business_baseline.sql:235](<../../backend/business_migrations/0001_business_baseline.sql#L235>) |
| `mt.content_cluster` | [backend/business_migrations/0001_business_baseline.sql:252](<../../backend/business_migrations/0001_business_baseline.sql#L252>) |
| `mt.event_receipt` | [backend/business_migrations/0001_business_baseline.sql:271](<../../backend/business_migrations/0001_business_baseline.sql#L271>) |
| `mt.idempotency_record` | [backend/business_migrations/0001_business_baseline.sql:291](<../../backend/business_migrations/0001_business_baseline.sql#L291>) |
| `mt.import_job` | [backend/business_migrations/0001_business_baseline.sql:314](<../../backend/business_migrations/0001_business_baseline.sql#L314>) |
| `mt.model_evaluation` | [backend/business_migrations/0001_business_baseline.sql:332](<../../backend/business_migrations/0001_business_baseline.sql#L332>) |
| `mt.object_version` | [backend/business_migrations/0001_business_baseline.sql:356](<../../backend/business_migrations/0001_business_baseline.sql#L356>) |
| `mt.outbox_event` | [backend/business_migrations/0001_business_baseline.sql:382](<../../backend/business_migrations/0001_business_baseline.sql#L382>) |
| `mt.source_registry` | [backend/business_migrations/0001_business_baseline.sql:405](<../../backend/business_migrations/0001_business_baseline.sql#L405>) |
| `mt.user_roles` | [backend/business_migrations/0001_business_baseline.sql:428](<../../backend/business_migrations/0001_business_baseline.sql#L428>) |
| `mt.approval_decision` | [backend/business_migrations/0001_business_baseline.sql:442](<../../backend/business_migrations/0001_business_baseline.sql#L442>) |
| `mt.audit_export` | [backend/business_migrations/0001_business_baseline.sql:465](<../../backend/business_migrations/0001_business_baseline.sql#L465>) |
| `mt.content_item` | [backend/business_migrations/0001_business_baseline.sql:489](<../../backend/business_migrations/0001_business_baseline.sql#L489>) |
| `mt.model_release` | [backend/business_migrations/0001_business_baseline.sql:513](<../../backend/business_migrations/0001_business_baseline.sql#L513>) |
| `mt.operation_token` | [backend/business_migrations/0001_business_baseline.sql:537](<../../backend/business_migrations/0001_business_baseline.sql#L537>) |
| `mt.propagation_node` | [backend/business_migrations/0001_business_baseline.sql:563](<../../backend/business_migrations/0001_business_baseline.sql#L563>) |
| `mt.media_asset` | [backend/business_migrations/0001_business_baseline.sql:583](<../../backend/business_migrations/0001_business_baseline.sql#L583>) |
| `mt.propagation_edge` | [backend/business_migrations/0001_business_baseline.sql:616](<../../backend/business_migrations/0001_business_baseline.sql#L616>) |
| `mt.analysis_task` | [backend/business_migrations/0001_business_baseline.sql:642](<../../backend/business_migrations/0001_business_baseline.sql#L642>) |
| `mt.asset_lineage` | [backend/business_migrations/0001_business_baseline.sql:670](<../../backend/business_migrations/0001_business_baseline.sql#L670>) |
| `mt.claim` | [backend/business_migrations/0001_business_baseline.sql:696](<../../backend/business_migrations/0001_business_baseline.sql#L696>) |
| `mt.feature` | [backend/business_migrations/0001_business_baseline.sql:721](<../../backend/business_migrations/0001_business_baseline.sql#L721>) |
| `mt.import_item` | [backend/business_migrations/0001_business_baseline.sql:747](<../../backend/business_migrations/0001_business_baseline.sql#L747>) |
| `mt.search_job` | [backend/business_migrations/0001_business_baseline.sql:773](<../../backend/business_migrations/0001_business_baseline.sql#L773>) |
| `mt.shot` | [backend/business_migrations/0001_business_baseline.sql:795](<../../backend/business_migrations/0001_business_baseline.sql#L795>) |
| `mt.text_segment` | [backend/business_migrations/0001_business_baseline.sql:818](<../../backend/business_migrations/0001_business_baseline.sql#L818>) |
| `mt.upload_session` | [backend/business_migrations/0001_business_baseline.sql:846](<../../backend/business_migrations/0001_business_baseline.sql#L846>) |
| `mt.keyframe` | [backend/business_migrations/0001_business_baseline.sql:874](<../../backend/business_migrations/0001_business_baseline.sql#L874>) |
| `mt.source_match` | [backend/business_migrations/0001_business_baseline.sql:899](<../../backend/business_migrations/0001_business_baseline.sql#L899>) |
| `mt.task_event` | [backend/business_migrations/0001_business_baseline.sql:935](<../../backend/business_migrations/0001_business_baseline.sql#L935>) |
| `mt.task_run` | [backend/business_migrations/0001_business_baseline.sql:958](<../../backend/business_migrations/0001_business_baseline.sql#L958>) |
| `mt.upload_part` | [backend/business_migrations/0001_business_baseline.sql:982](<../../backend/business_migrations/0001_business_baseline.sql#L982>) |
| `mt.task_node_run` | [backend/business_migrations/0001_business_baseline.sql:1006](<../../backend/business_migrations/0001_business_baseline.sql#L1006>) |
| `mt.task_result` | [backend/business_migrations/0001_business_baseline.sql:1039](<../../backend/business_migrations/0001_business_baseline.sql#L1039>) |
| `mt.evidence_item` | [backend/business_migrations/0001_business_baseline.sql:1064](<../../backend/business_migrations/0001_business_baseline.sql#L1064>) |
| `mt.evidence_package` | [backend/business_migrations/0001_business_baseline.sql:1099](<../../backend/business_migrations/0001_business_baseline.sql#L1099>) |
| `mt.report` | [backend/business_migrations/0001_business_baseline.sql:1128](<../../backend/business_migrations/0001_business_baseline.sql#L1128>) |
| `mt.review_record` | [backend/business_migrations/0001_business_baseline.sql:1158](<../../backend/business_migrations/0001_business_baseline.sql#L1158>) |
| `mt.risk_finding` | [backend/business_migrations/0001_business_baseline.sql:1185](<../../backend/business_migrations/0001_business_baseline.sql#L1185>) |
| `mt.tamper_finding` | [backend/business_migrations/0001_business_baseline.sql:1217](<../../backend/business_migrations/0001_business_baseline.sql#L1217>) |
| `mt.claim_evidence_relation` | [backend/business_migrations/0001_business_baseline.sql:1249](<../../backend/business_migrations/0001_business_baseline.sql#L1249>) |
| `mt.cluster_member` | [backend/business_migrations/0001_business_baseline.sql:1272](<../../backend/business_migrations/0001_business_baseline.sql#L1272>) |
| `mt.feedback_request` | [backend/business_migrations/0001_business_baseline.sql:1296](<../../backend/business_migrations/0001_business_baseline.sql#L1296>) |
| `mt.finding_evidence` | [backend/business_migrations/0001_business_baseline.sql:1321](<../../backend/business_migrations/0001_business_baseline.sql#L1321>) |
| `mt.package_item` | [backend/business_migrations/0001_business_baseline.sql:1344](<../../backend/business_migrations/0001_business_baseline.sql#L1344>) |
| `mt.report_evidence` | [backend/business_migrations/0001_business_baseline.sql:1368](<../../backend/business_migrations/0001_business_baseline.sql#L1368>) |
| `mt.review_evidence` | [backend/business_migrations/0001_business_baseline.sql:1388](<../../backend/business_migrations/0001_business_baseline.sql#L1388>) |
| `mt.task_evidence` | [backend/business_migrations/0001_business_baseline.sql:1408](<../../backend/business_migrations/0001_business_baseline.sql#L1408>) |
| `mt.first_source_ranking` | [backend/business_migrations/0001_business_baseline.sql:1429](<../../backend/business_migrations/0001_business_baseline.sql#L1429>) |
| `mt.first_source_candidate` | [backend/business_migrations/0001_business_baseline.sql:1455](<../../backend/business_migrations/0001_business_baseline.sql#L1455>) |
| `mt.user_identities` | [backend/business_migrations/0004_identity_relations.sql:25](<../../backend/business_migrations/0004_identity_relations.sql#L25>) |
| `mt.authorization_epoch` | [backend/business_migrations/0008_authorization_fence.sql:2](<../../backend/business_migrations/0008_authorization_fence.sql#L2>) |
| `mt.task_policy_artifact` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:36](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L36>) |
| `mt.task_plan_artifact` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:54](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L54>) |
| `mt.task_capability_manifest` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:70](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L70>) |
| `mt.task_plan_mapping_revision` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:86](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L86>) |
| `mt.task_plan_mapping_head` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:133](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L133>) |
| `mt.task_run_plan` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:153](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L153>) |

## SQL函数与版本定义

同名函数的各版本定义均保留；它们是迁移源码索引，不证明当前运行实例的有效函数体。

| SQL函数名称 | 版本迁移及位置 |
| --- | --- |
| `mt.actor_id` | [backend/business_migrations/0001_business_baseline.sql:1487](<../../backend/business_migrations/0001_business_baseline.sql#L1487>) |
| `mt.org_id` | [backend/business_migrations/0001_business_baseline.sql:1490](<../../backend/business_migrations/0001_business_baseline.sql#L1490>) |
| `mt.actor_in_org` | [backend/business_migrations/0001_business_baseline.sql:1493](<../../backend/business_migrations/0001_business_baseline.sql#L1493>)、[backend/business_migrations/0004_identity_relations.sql:99](<../../backend/business_migrations/0004_identity_relations.sql#L99>) |
| `mt.can_access_case` | [backend/business_migrations/0001_business_baseline.sql:1497](<../../backend/business_migrations/0001_business_baseline.sql#L1497>)、[backend/business_migrations/0004_identity_relations.sql:104](<../../backend/business_migrations/0004_identity_relations.sql#L104>) |
| `mt.reject_mutation` | [backend/business_migrations/0001_business_baseline.sql:1507](<../../backend/business_migrations/0001_business_baseline.sql#L1507>) |
| `mt.preserve_asset_original` | [backend/business_migrations/0001_business_baseline.sql:1509](<../../backend/business_migrations/0001_business_baseline.sql#L1509>) |
| `mt.validate_seal` | [backend/business_migrations/0001_business_baseline.sql:1517](<../../backend/business_migrations/0001_business_baseline.sql#L1517>) |
| `mt.prevent_token_reuse` | [backend/business_migrations/0001_business_baseline.sql:1534](<../../backend/business_migrations/0001_business_baseline.sql#L1534>)、[backend/business_migrations/0011_operation_token.sql:69](<../../backend/business_migrations/0011_operation_token.sql#L69>) |
| `mt.check_first_source_item` | [backend/business_migrations/0001_business_baseline.sql:2144](<../../backend/business_migrations/0001_business_baseline.sql#L2144>) |
| `mt.check_first_source_complete` | [backend/business_migrations/0001_business_baseline.sql:2203](<../../backend/business_migrations/0001_business_baseline.sql#L2203>) |
| `mt.validate_control_link` | [backend/business_migrations/0003_control_integrity.sql:3](<../../backend/business_migrations/0003_control_integrity.sql#L3>) |
| `mt.protect_policy_definition` | [backend/business_migrations/0003_control_integrity.sql:32](<../../backend/business_migrations/0003_control_integrity.sql#L32>) |
| `mt.preserve_directory_keys` | [backend/business_migrations/0004_identity_relations.sql:47](<../../backend/business_migrations/0004_identity_relations.sql#L47>) |
| `mt.resolve_identity` | [backend/business_migrations/0004_identity_relations.sql:112](<../../backend/business_migrations/0004_identity_relations.sql#L112>) |
| `mt.preserve_role_catalog` | [backend/business_migrations/0005_role_catalog.sql:27](<../../backend/business_migrations/0005_role_catalog.sql#L27>) |
| `mt.lookup_permission` | [backend/business_migrations/0006_permission_lookup.sql:26](<../../backend/business_migrations/0006_permission_lookup.sql#L26>) |
| `mt.lookup_role_facts` | [backend/business_migrations/0007_role_facts.sql:2](<../../backend/business_migrations/0007_role_facts.sql#L2>) |
| `mt.lookup_actor_role_facts` | [backend/business_migrations/0007_role_facts.sql:27](<../../backend/business_migrations/0007_role_facts.sql#L27>) |
| `mt.advance_authorization_epoch` | [backend/business_migrations/0008_authorization_fence.sql:17](<../../backend/business_migrations/0008_authorization_fence.sql#L17>) |
| `mt.bump_authorization_epoch` | [backend/business_migrations/0008_authorization_fence.sql:25](<../../backend/business_migrations/0008_authorization_fence.sql#L25>) |
| `mt.hold_authorization_epoch` | [backend/business_migrations/0008_authorization_fence.sql:43](<../../backend/business_migrations/0008_authorization_fence.sql#L43>) |
| `mt.activate_authorization_generation` | [backend/business_migrations/0008_authorization_fence.sql:53](<../../backend/business_migrations/0008_authorization_fence.sql#L53>) |
| `mt.lookup_actor_work_role_facts` | [backend/business_migrations/0009_work_role_facts.sql:2](<../../backend/business_migrations/0009_work_role_facts.sql#L2>) |
| `mt.scope_operation` | [backend/business_migrations/0010_data_scope.sql:2](<../../backend/business_migrations/0010_data_scope.sql#L2>)、[backend/business_migrations/0011_operation_token.sql:2](<../../backend/business_migrations/0011_operation_token.sql#L2>)、[backend/business_migrations/0012_catalog_reads.sql:3](<../../backend/business_migrations/0012_catalog_reads.sql#L3>)、[backend/business_migrations/0013_report_reads.sql:3](<../../backend/business_migrations/0013_report_reads.sql#L3>)、[backend/business_migrations/0014_resource_registry.sql:3](<../../backend/business_migrations/0014_resource_registry.sql#L3>)、[backend/business_migrations/0017_task_creation_scope_reads.sql:45](<../../backend/business_migrations/0017_task_creation_scope_reads.sql#L45>) |
| `mt.scope_mode` | [backend/business_migrations/0010_data_scope.sql:15](<../../backend/business_migrations/0010_data_scope.sql#L15>) |
| `mt.scope_case_id` | [backend/business_migrations/0010_data_scope.sql:21](<../../backend/business_migrations/0010_data_scope.sql#L21>) |
| `mt.scope_allows_case` | [backend/business_migrations/0010_data_scope.sql:31](<../../backend/business_migrations/0010_data_scope.sql#L31>) |
| `mt.current_actor_case_ids` | [backend/business_migrations/0010_data_scope.sql:77](<../../backend/business_migrations/0010_data_scope.sql#L77>) |
| `mt.scope_lookup_kind_allowed` | [backend/business_migrations/0010_data_scope.sql:104](<../../backend/business_migrations/0010_data_scope.sql#L104>)、[backend/business_migrations/0011_operation_token.sql:16](<../../backend/business_migrations/0011_operation_token.sql#L16>)、[backend/business_migrations/0012_catalog_reads.sql:17](<../../backend/business_migrations/0012_catalog_reads.sql#L17>)、[backend/business_migrations/0013_report_reads.sql:17](<../../backend/business_migrations/0013_report_reads.sql#L17>)、[backend/business_migrations/0014_resource_registry.sql:17](<../../backend/business_migrations/0014_resource_registry.sql#L17>)、[backend/business_migrations/0017_task_creation_scope_reads.sql:59](<../../backend/business_migrations/0017_task_creation_scope_reads.sql#L59>) |
| `mt.lookup_scope_metadata` | [backend/business_migrations/0010_data_scope.sql:127](<../../backend/business_migrations/0010_data_scope.sql#L127>)、[backend/business_migrations/0013_report_reads.sql:39](<../../backend/business_migrations/0013_report_reads.sql#L39>)、[backend/business_migrations/0014_resource_registry.sql:41](<../../backend/business_migrations/0014_resource_registry.sql#L41>) |
| `mt.model_evaluation_artifact_metadata` | [backend/business_migrations/0014_resource_registry.sql:173](<../../backend/business_migrations/0014_resource_registry.sql#L173>) |
| `mt.task_plan_modules_valid` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:26](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L26>) |
| `mt.preserve_task_plan_head` | [backend/business_migrations/0016_task_creation_plan_bindings.sql:210](<../../backend/business_migrations/0016_task_creation_plan_bindings.sql#L210>) |
| `mt.reject_task_plan_case_reader_dml` | [backend/business_migrations/0017_task_creation_scope_reads.sql:179](<../../backend/business_migrations/0017_task_creation_scope_reads.sql#L179>) |
| `mt.task_create_execution_plan` | [backend/business_migrations/0017_task_creation_scope_reads.sql:203](<../../backend/business_migrations/0017_task_creation_scope_reads.sql#L203>) |
| `mt.task_create_plan_metadata` | [backend/business_migrations/0017_task_creation_scope_reads.sql:272](<../../backend/business_migrations/0017_task_creation_scope_reads.sql#L272>) |

## 适用边界与后续实际工作

- 优先复用已有迁移、SQL访问、权限、案件/单位范围和审计；数据表或方法清单不替代任务实现。新增持久化结构使用后续增量迁移，不向现有库运行初始化。
- T013本人身份接管、MFA、密钥验证与实际恢复仍按任务卡逐项核验；备份目录、RPO/RTO及维护窗口等未知输入保持未确定，不把公开口令当已妥善保护。
- 六角色已确认的设计输入不等于正式策略已采用；正式来源授权、分类/用途事实不足时拒绝相应业务动作。
- 模型、权重许可、用途授权数据及适用GPU未落实的算法任务保持剩余；合成CPU编码器不能充当全部正式模型。
- 20/100并发、准确率和正式验收口径需有效输入及真实执行；现有CI门禁继续保留，Python候选暂缓不等于维护风险已接受。
- 本清单仅整理T001—T123；其他47任务仍保留在总台账。未知人员、工时、日期或批准不得编造。
