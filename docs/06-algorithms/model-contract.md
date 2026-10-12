# 模型能力契约

34项为算法方向，含校准、几何、压缩方法，不等于34个独立训练模型或正式成果。候选、输入路径、输出类型、任务与数据集映射在model-catalog.yaml；每能力有独立request/response Schema。

统一信封含request_id、case_id、task_id、run_version、capability、model_name/version、input_kind、asset_ids、object_refs、preprocessing_version、mapping_version、missing_modalities、deadline_at和authorization_version。输出含status、output_kind、findings、artifacts、payload、warnings、reason、latency_ms及mock。

原字节取证、原件解码像素与允许分析副本分别声明；TruFor原RGB与学习噪声指纹机制和项目扩展分开。SBI仅训练增强候选；音画同步独立网络处理。PyTorch/ONNX/Triton是待验证后端，不强制所有模型统一导出；TorchServe不作为普通长期服务首选。

SUCCEEDED需有对应类型payload；FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED需reason和null payload；失败不能夹带正式结论。missing_modalities明确缺失，不因缺音轨死等；mock必须显式，正式发布拒绝mock包。

分类与框分数0到1，但不是法律概率；raw/calibrated/阈值版本分别记。bbox归一化并验证边界；半开时间区间验证起止与素材范围；模型输出的evidence_ids必须存在且在案件/授权范围内。大掩码和向量使用受控ObjectRef，尺寸、dtype、维度、归一化和前处理有版本。

许可记录覆盖代码、权重、特征子模型、用途、离线再分发及环境。SuperPoint与LightGlue分别核验；TruFor扩展训练与许可单列。不据开源仓库存在宣称项目已可交付。

官方来源W01/W02/W10/W12/W17/W18以及原设计附录D支持机制；本包校验实例不证明模型精度、GPU性能或许可已通过。

## M24首发候选增补

M24原始结果最多3条，名次从1连续排列且资产不重复。数据库ranking_id由业务层在校验授权、证据及版本后生成，算法不伪造持久化快照ID。D12训练/评测真值标注中的候选集合不是运行时排序响应，不将rank要求错误施加于该标注。规则详见[首发排序契约](../04-database/first-source-ranking.md)。

## 首发证据列表唯一性

M24与FirstSource的支持/反对证据列表增加uniqueItems；语义校验进一步识别UUID大小写形式的重复。数据库持久化还检查存在与同案件；模型原始输出的ID不能被直接视为可用证据。
