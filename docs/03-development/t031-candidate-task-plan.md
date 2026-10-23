# T031候选任务DAG的不可变解析层

2026-10-22按照[非算法工程计划](non-algorithm-fast-delivery-plan-20261028.md)的“先计划解析子范围”推进[T031](../../tasks/backend/T031.md)。本批新增后端可复用解析代码，不挂载`createTask`，不启动调度器、不生成分析结果、不写任务数据库。准确源码、实际命令及最终结果见[专项回执](../00-project/validation/t031-candidate-task-plan-report.json)。

## 输入与复用依据

结构继续以[dag.schema.json](../../schemas/workflow/dag.schema.json)为唯一来源，复用业务后端已有`SCHEMAS`和`REGISTRY`。语义规则与现有`scripts/stage_one_controls.py`中的`validate_dag`、`active_node_plan`保持对应，并执行原离线控制验证入口，不把原脚本导入运行服务。未修改Schema、36份候选图或任何源文档。

T010现有变更/ADR规范和T020现有资产表、上传登记事务足够支撑纯解析子范围，不意味着这些前置任务已经全部验收。后续任务创建仍须实际核验有效资产、来源用途、权限、策略、版本及同事务写入。本批不因T024、T013或N01未整卡关闭而停下独立解析代码，也不将这些外部条件消除。

## 代码入口和不可变输出

`backend/business_app/task_plan.py`提供内部函数：

```python
parse_candidate_dag(raw: bytes, *, max_bytes: int, max_nodes: int) -> CandidateDAG
```

调用方必须明确提供正整数资源预算，布尔值不能充当整数；先检查原始字节数，解码后检查节点数。这是工程输入预算，不是项目业务阈值，也没有给共享环境设置未经确认的默认值。

解析仅接收UTF-8 JSON，重复对象键、非JSON数字、格式错误和非法Unicode统一拒绝；错误不包含原始计划内容。之后通过现有Schema和图语义校验，输出嵌套冻结dataclass、tuple和bytes：

- `CandidateBinding`保存字段与显式来源说明；`CandidateNode`保存依赖、必需性、模型Schema身份、输出与入口模式。
- `CandidateEntry`保存原操作ID、模式、请求结构来源和内部run要求。
- `CandidateDAG`保留原候选身份、来源任务、外部输入、全部节点、入口及原始/规范化SHA-256。
- `CandidateDAG.select(operation_id)`返回`CandidateSelection`，分别保留所选节点及未选节点ID。未知操作拒绝，不回退默认入口。

原始摘要绑定精确文件字节；规范化摘要绑定键排序后的JSON内容。空白或对象键顺序变化可保持规范化摘要相同，但数组顺序仍属于内容，不能将它称为语义等价图摘要。拓扑顺序独立按节点ID稳定排序。输入解码后的可变结构不作为输出对象共享。

## 校验及入口分支

拒绝重复节点、未知依赖、自环及多节点环；必需节点必须使用`FAIL_REQUIRED`，可选节点使用`SKIP_OPTIONAL_WITH_REASON`。模型节点必须匹配已有M01—M34请求/响应Schema及完整必填字段绑定，非模型节点的`model_id`必须为空。全图恰有一个publish、最终为response，入口操作ID不得重复。

选择READ_ONLY或CONTROL_TRANSACTION时，不允许选中media、model或publish节点。现有`response.emit`同时引用两个分支，其某个依赖按入口未选是合法结构；未选分支单独列出，**不写成task_node_run的NOT_SELECTED状态**，也不当作可选模型SKIPPED或必需节点失败。依据见[工作流契约](../05-workflows/workflow-contracts.md)。

本层校验字段来源说明的结构和模型必填绑定，不执行来源表达式、不下载权重或读取对象，不验证外部提供者真实存在，也不把结构字符串当访问授权。

## 测试与当前限制

新增测试逐一读取36张现有候选图并选择全部声明入口；覆盖负向图结构、模型绑定、重复JSON、资源预算、冻结对象、摘要及未选依赖。初始75项测试在功能缺失时失败，解析实现后通过；审查发现孤立Unicode代理字符边界后，补两项实际失败回归并修复。最终测试数量及类型/格式结果以专项回执为准，重复运行不相加计数。

本批相邻回归复用现有租约、取消与工作权限测试，以及原离线控制验证和失败探针。前端、公共API、SQL和迁移未变，不重复已经通过且未受影响的浏览器构建检查。

36张图仍是`ENGINEERING_CANDIDATE`、`candidate-1`。解析成功只表示候选结构可读且满足本层规则；冻结dataclass和摘要不是权限、签名、策略采用或可执行资格证明。后续不得直接把本对象当获准计划传给调度器。

## 下一步及未完成

1. 形成并核验真实场景/模块到受信策略、版本化DAG、能力可用性的解析关系；当前没有正式映射，不自行补造三级策略或模型成功。
2. T032/T033/T034按原依赖逐步接入固定运行/节点版本、状态转移、同事务幂等/审计/outbox及有效资产、用途、权限复核，之后才挂载任务创建接口。
3. 调度、重试、取消、恢复、结果发布和完整任务验收仍待后续实际实现；不由候选图或75项测试推定完成。
4. 实际T031开发负责人、复核人和剩余工时尚未确认，不能沿用其他任务登记自动填入。

前轮[CI最终证据](../00-project/validation/t024-durability-final-ci-report.json)显示业务952项等全量通过，但整体CI因9条Python漏洞及Torch扫描覆盖不足失败。旧副本不替代新结果，原100包锁及CI门禁保持。算法与Python候选继续暂缓；源码同步不代表共享运行服务升级。
