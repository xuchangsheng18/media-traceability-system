# 独立任务卡与执行清单

170条源任务已形成一任务一文件。角色、源工时与源依赖原文保留；执行依赖是待评审候选。input_refs是真实资料路径，output_refs_planned和runtime_test_file是后续实现位置提案，不能冒充已有代码或已通过测试。

## 第二阶段任务使用说明

第二阶段采用23步技术基线流程，与本目录170条源研发任务是两套不同编号体系。步骤1—23见[交付清单](../docs/03-development/stage-two-readiness.md)，不得把其中的步骤20当作源任务T020。

基线准备优先参考T001—T010及相关契约、存储、模型任务，但实际执行仍按任务卡依赖与本次授权范围。README补齐、文档校验和隔离SQL测试只计对应证据，不能把业务卡自动标为完成。

`backlog.yaml`是执行索引，独立Markdown卡是完整工作说明；`source-task-cards.json`保留源字段，`execution-dependencies-candidate.json`保存候选执行依赖。源依赖、候选依赖和已验证依赖必须分开。

后续每项任务记录实际负责人、输入版本、完成文件、运行验证、未完成项及相关技术决定。实际负责人未落实时不编造姓名。首发排序的补充规则已同步T091—T093。

| 任务 | 名称 | 类别 |
| --- | --- | --- |
| [T001](platform/T001.md) | 建立单仓库目录与基础README | platform |
| [T002](platform/T002.md) | 配置Python后端工程 | platform |
| [T003](frontend/T003.md) | 配置Vue前端工程 | frontend |
| [T004](platform/T004.md) | 建立本地容器开发环境 | platform |
| [T005](platform/T005.md) | 配置代码格式化与静态检查 | platform |
| [T006](platform/T006.md) | 建立基础持续集成流水线 | platform |
| [T007](platform/T007.md) | 建立统一配置和密钥规范 | platform |
| [T008](platform/T008.md) | 建立统一日志与请求追踪 | platform |
| [T009](platform/T009.md) | 建立统一异常与错误码框架 | platform |
| [T010](platform/T010.md) | 建立架构决策记录和变更模板 | platform |
| [T011](platform/T011.md) | 设计用户角色与数据范围模型 | platform |
| [T012](platform/T012.md) | 实现用户角色数据库模型 | platform |
| [T013](platform/T013.md) | 实现认证与令牌校验 | platform |
| [T014](platform/T014.md) | 实现接口级权限控制 | platform |
| [T015](platform/T015.md) | 实现数据范围访问控制 | platform |
| [T016](platform/T016.md) | 实现高风险操作二次确认 | platform |
| [T017](platform/T017.md) | 实现操作审计事件模型 | platform |
| [T018](frontend/T018.md) | 开发审计查询页面与接口 | frontend |
| [T019](backend/T019.md) | 设计内容与媒体资产模型 | backend |
| [T020](backend/T020.md) | 实现内容与媒体资产表 | backend |
| [T021](backend/T021.md) | 实现数据来源授权登记 | backend |
| [T022](backend/T022.md) | 实现分片上传初始化 | backend |
| [T023](backend/T023.md) | 实现分片接收与校验 | backend |
| [T024](backend/T024.md) | 实现分片合并与完整哈希 | backend |
| [T025](backend/T025.md) | 实现MinIO对象存储适配器 | backend |
| [T026](backend/T026.md) | 实现媒体格式探测与安全校验 | backend |
| [T027](backend/T027.md) | 实现SHA-256完全重复检测 | backend |
| [T028](backend/T028.md) | 实现批量清单导入 | backend |
| [T029](backend/T029.md) | 实现第三方接入适配器协议 | backend |
| [T030](frontend/T030.md) | 开发媒体资产管理页面 | frontend |
| [T031](backend/T031.md) | 设计分析任务与节点执行模型 | backend |
| [T032](backend/T032.md) | 实现任务及节点数据库模型 | backend |
| [T033](backend/T033.md) | 实现任务状态机 | backend |
| [T034](backend/T034.md) | 实现任务创建接口 | backend |
| [T035](backend/T035.md) | 实现任务查询和进度接口 | backend |
| [T036](backend/T036.md) | 实现异步队列与优先级 | backend |
| [T037](backend/T037.md) | 实现DAG任务编排器 | backend |
| [T038](backend/T038.md) | 实现节点级重试与检查点 | backend |
| [T039](backend/T039.md) | 实现任务取消和退回重算 | backend |
| [T040](frontend/T040.md) | 开发任务监控页面 | frontend |
| [T041](backend/T041.md) | 实现图片元数据解析 | backend |
| [T042](backend/T042.md) | 实现视频ffprobe解析 | backend |
| [T043](backend/T043.md) | 实现标准化媒体副本生成 | backend |
| [T044](backend/T044.md) | 实现镜头边界检测 | backend |
| [T045](backend/T045.md) | 实现固定间隔抽帧 | backend |
| [T046](backend/T046.md) | 实现镜头代表帧选择 | backend |
| [T047](backend/T047.md) | 实现音轨与字幕提取 | backend |
| [T048](backend/T048.md) | 接入OCR并建立时间片段 | backend |
| [T049](backend/T049.md) | 接入ASR并建立时间片段 | backend |
| [T050](backend/T050.md) | 实现媒体统一时间轴服务 | backend |
| [T051](algorithm/T051.md) | 定义统一模型输入输出契约 | algorithm |
| [T052](algorithm/T052.md) | 实现模型注册表 | algorithm |
| [T053](algorithm/T053.md) | 实现统一推理网关 | algorithm |
| [T054](algorithm/T054.md) | 实现HTTP与本地Mock适配器 | algorithm |
| [T055](algorithm/T055.md) | 实现推理批处理与GPU队列 | algorithm |
| [T056](algorithm/T056.md) | 实现模型健康检查与熔断 | algorithm |
| [T057](algorithm/T057.md) | 实现模型灰度发布 | algorithm |
| [T058](algorithm/T058.md) | 实现模型评测记录管理 | algorithm |
| [T059](algorithm/T059.md) | 实现输入输出漂移监测 | algorithm |
| [T060](frontend/T060.md) | 开发模型运维页面 | frontend |
| [T061](algorithm/T061.md) | 定义风险标签和版本管理 | algorithm |
| [T062](algorithm/T062.md) | 接入图片多标签分类模型 | algorithm |
| [T063](algorithm/T063.md) | 接入敏感目标检测模型 | algorithm |
| [T064](algorithm/T064.md) | 接入视频行为识别模型 | algorithm |
| [T065](algorithm/T065.md) | 接入音频事件识别模型 | algorithm |
| [T066](algorithm/T066.md) | 实现多模态时间对齐 | algorithm |
| [T067](algorithm/T067.md) | 实现跨模态矛盾检测 | algorithm |
| [T068](algorithm/T068.md) | 实现综合风险融合与校准 | algorithm |
| [T069](algorithm/T069.md) | 实现风险转人工规则 | algorithm |
| [T070](frontend/T070.md) | 开发风险识别研判界面 | frontend |
| [T071](algorithm/T071.md) | 实现图片取证基础特征 | algorithm |
| [T072](algorithm/T072.md) | 接入图片篡改区域模型 | algorithm |
| [T073](algorithm/T073.md) | 实现复制粘贴与局部生成分类 | algorithm |
| [T074](algorithm/T074.md) | 实现视频时间结构异常检测 | algorithm |
| [T075](algorithm/T075.md) | 实现视频空间篡改跟踪 | algorithm |
| [T076](algorithm/T076.md) | 接入深度伪造与音画同步检测 | algorithm |
| [T077](algorithm/T077.md) | 实现篡改多证据融合 | algorithm |
| [T078](frontend/T078.md) | 开发篡改取证界面 | frontend |
| [T079](algorithm/T079.md) | 实现图片感知哈希特征 | algorithm |
| [T080](algorithm/T080.md) | 实现视觉与复制检测向量生成 | algorithm |
| [T081](algorithm/T081.md) | 建立Milvus索引与版本管理 | algorithm |
| [T082](algorithm/T082.md) | 实现图片多路候选召回 | algorithm |
| [T083](algorithm/T083.md) | 实现局部特征提取与匹配 | algorithm |
| [T084](algorithm/T084.md) | 实现RANSAC几何验证 | algorithm |
| [T085](algorithm/T085.md) | 实现图片局部区域检索 | algorithm |
| [T086](algorithm/T086.md) | 实现视频帧检索候选聚合 | algorithm |
| [T087](algorithm/T087.md) | 实现视频相似度矩阵构建 | algorithm |
| [T088](algorithm/T088.md) | 实现局部DTW与倒放对齐 | algorithm |
| [T089](algorithm/T089.md) | 实现多源拼接来源映射 | algorithm |
| [T090](backend/T090.md) | 实现高可信同源内容聚类 | backend |
| [T091](backend/T091.md) | 实现首发排序特征工程 | backend |
| [T092](backend/T092.md) | 训练和注册首发排序模型 | backend |
| [T093](backend/T093.md) | 实现首发候选查询服务 | backend |
| [T094](backend/T094.md) | 设计传播图谱数据模型 | backend |
| [T095](backend/T095.md) | 实现传播图谱写入与查询 | backend |
| [T096](backend/T096.md) | 实现隐式传播关系推断 | backend |
| [T097](frontend/T097.md) | 开发传播时间线和图谱界面 | frontend |
| [T098](algorithm/T098.md) | 实现结构化主张抽取服务 | algorithm |
| [T099](algorithm/T099.md) | 实现权威证据检索与关系判断 | algorithm |
| [T100](backend/T100.md) | 实现统一证据对象模型 | backend |
| [T101](backend/T101.md) | 实现风险与取证证据卡片接口 | backend |
| [T102](backend/T102.md) | 实现人工复核工作流 | backend |
| [T103](frontend/T103.md) | 开发人工复核工作台 | frontend |
| [T104](backend/T104.md) | 实现证据固化与完整性校验 | backend |
| [T105](backend/T105.md) | 实现可信时间与签名适配层 | backend |
| [T106](backend/T106.md) | 实现证据约束核查摘要 | backend |
| [T107](backend/T107.md) | 实现核查报告生成 | backend |
| [T108](backend/T108.md) | 实现样本纠错与回流审批 | backend |
| [T109](data/T109.md) | 建立标注规范与标签质检工具 | data |
| [T110](data/T110.md) | 实现原始素材分组划分 | data |
| [T111](data/T111.md) | 实现可控编辑数据增强流水线 | data |
| [T112](data/T112.md) | 建立难负样本挖掘流程 | data |
| [T113](backend/T113.md) | 实现风险模型训练与评测流水线 | backend |
| [T114](backend/T114.md) | 实现篡改模型评测流水线 | backend |
| [T115](backend/T115.md) | 实现同源与片段检索评测流水线 | backend |
| [T116](backend/T116.md) | 实现首发和大模型核查评测 | backend |
| [T117](testing/T117.md) | 建立应用安全自动化扫描 | testing |
| [T118](testing/T118.md) | 实施上传与接口安全测试 | testing |
| [T119](testing/T119.md) | 实施大模型安全测试 | testing |
| [T120](backend/T120.md) | 实现监控指标与告警 | backend |
| [T121](deployment/T121.md) | 实现备份恢复与灾备演练 | deployment |
| [T122](testing/T122.md) | 执行20并发验收性能测试 | testing |
| [T123](testing/T123.md) | 执行100并发容量与长稳测试 | testing |
| [T124](testing/T124.md) | 完成三类业务场景验收 | testing |
| [T125](algorithm/T125.md) | 建立算法实验公共框架 | algorithm |
| [T126](data/T126.md) | 建立训练数据版本与数据卡 | data |
| [T127](data/T127.md) | 冻结公安业务独立测试集 | data |
| [T128](algorithm/T128.md) | 建立算法基线结果台账 | algorithm |
| [T129](data/T129.md) | 开展图片多标签风险数据分析 | data |
| [T130](algorithm/T130.md) | 训练图片多标签风险基线模型 | algorithm |
| [T131](algorithm/T131.md) | 优化风险类别不平衡与长尾召回 | algorithm |
| [T132](algorithm/T132.md) | 训练敏感目标检测模型 | algorithm |
| [T133](algorithm/T133.md) | 开展小目标低清目标专项优化 | algorithm |
| [T134](data/T134.md) | 构建视频行为训练片段与时间边界 | data |
| [T135](algorithm/T135.md) | 微调视频行为识别模型 | algorithm |
| [T136](algorithm/T136.md) | 训练视频事件时间定位模型 | algorithm |
| [T137](algorithm/T137.md) | 微调音频事件识别模型 | algorithm |
| [T138](data/T138.md) | 构建跨模态一致与矛盾训练集 | data |
| [T139](algorithm/T139.md) | 训练跨模态矛盾检测模型 | algorithm |
| [T140](algorithm/T140.md) | 训练多模态风险融合模型 | algorithm |
| [T141](algorithm/T141.md) | 实施风险概率校准和业务阈值优化 | algorithm |
| [T142](data/T142.md) | 构建图片篡改成组训练集 | data |
| [T143](algorithm/T143.md) | 训练图片噪声残差分支 | algorithm |
| [T144](algorithm/T144.md) | 训练RGB语义与边界分支 | algorithm |
| [T145](algorithm/T145.md) | 训练图片多分支融合篡改模型 | algorithm |
| [T146](algorithm/T146.md) | 训练图片篡改类型分类模型 | algorithm |
| [T147](data/T147.md) | 构建视频篡改与深伪训练集 | data |
| [T148](algorithm/T148.md) | 训练视频时间篡改检测模型 | algorithm |
| [T149](algorithm/T149.md) | 训练视频空间篡改检测与跟踪模型 | algorithm |
| [T150](algorithm/T150.md) | 微调人脸深度伪造检测模型 | algorithm |
| [T151](algorithm/T151.md) | 训练口型语音同步检测模型 | algorithm |
| [T152](algorithm/T152.md) | 实施跨压缩跨生成器泛化训练 | algorithm |
| [T153](algorithm/T153.md) | 实施篡改模型校准与不确定性估计 | algorithm |
| [T154](data/T154.md) | 构建图片复制检测对比学习样本 | data |
| [T155](algorithm/T155.md) | 训练图片复制检测向量模型 | algorithm |
| [T156](algorithm/T156.md) | 实施难负样本迭代训练 | algorithm |
| [T157](algorithm/T157.md) | 优化复制向量与索引联合参数 | algorithm |
| [T158](data/T158.md) | 构建视频帧复制检测训练集 | data |
| [T159](algorithm/T159.md) | 训练视频关键帧复制检测模型 | algorithm |
| [T160](algorithm/T160.md) | 优化视频帧相似度模型 | algorithm |
| [T161](algorithm/T161.md) | 训练学习型视频片段定位模型 | algorithm |
| [T162](algorithm/T162.md) | 训练多源拼接边界检测模型 | algorithm |
| [T163](algorithm/T163.md) | 实施视频检索分数校准 | algorithm |
| [T164](data/T164.md) | 构建首发排序训练内容簇 | data |
| [T165](algorithm/T165.md) | 开展首发排序模型消融与校准 | algorithm |
| [T166](data/T166.md) | 构建主张抽取监督微调数据 | data |
| [T167](algorithm/T167.md) | 微调主张抽取模型 | algorithm |
| [T168](algorithm/T168.md) | 构建并训练证据关系判断模型 | algorithm |
| [T169](algorithm/T169.md) | 研发无证据生成检测与句级引用校验 | algorithm |
| [T170](algorithm/T170.md) | 实施模型压缩导出与发布候选冻结 | algorithm |

## 本轮第二阶段工程证据

py310 CPU最小工程已实际运行；对应证据见[技术验证报告](../docs/02-architecture/technical-validation-report.md)和[23步状态](../docs/03-development/stage-two-readiness.md)。源170任务编号、目标、角色、人日、依赖和候选状态保留，不能把基础PoC通过当所有任务完成。T002源Python3.11候选与本轮用户指定3.10执行差异见TB-ADR-002。

## 1.1工程补充

1.1工程子范围证据：T004运行/恢复、T008/T009追踪/Problem、T031—T039迁移/单节点状态/outbox/租约、T042/T045/T050合成源PTS、T121冷恢复、T006私有GitHub接入。仅补证据，不改源目标/责任人/170任务完成状态。
