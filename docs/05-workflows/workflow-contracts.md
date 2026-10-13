# 完整任务节点、事件与运行结果契约

唯一结构源为[dag.schema.json](../../schemas/workflow/dag.schema.json)、[run-result.schema.json](../../schemas/workflow/run-result.schema.json)及[workflow.domain.v1.schema.json](../../schemas/events/workflow.domain.v1.schema.json)。[36需求图索引](dag-index.json)逐需求保留源任务引用，普通媒体、模型、投影和发布明确区分；170项目任务不是170个运行时节点。

每个模型输入按对应请求Schema核验，任务/运行/请求身份固定；索引、证据、融合上游输入必须显式绑定，不能由前一模型的任意JSON冒充。当前36图为保守串行技术模板，外部输入未落实，不能直接当已运行编排。后续并行改版须保存dag_version和字段绑定。

节点必需性与缺失处理一致：required失败使该执行失败；可选SKIPPED必须有原因，不能跳过必需节点。重复node_id、环、未知依赖、模型/能力错配和跨运行写回拒绝。优先级/并发/重试/超时/续租值由版本配置给出；未给值不自动调度。

取消意图与停止确认分开；停止确认及租约回收后拒绝旧fencing写回。消息按event_id去重；节点幂等键为(task_id,run_version,node_id,attempt)，结果发布按(task_id,run_version,result_version)唯一。乱序事件不能回退节点终态；重试增加attempt并取得新租约，不复用旧提交权。失败/死信保留原因、输入摘要和审计，再按有权恢复策略重投。

发布在校验案件/运行/fencing的事务中写不可变task_result.summary；快照保留全部34能力的原响应结构和普通媒体输出。字段映射见[34能力投影登记](../06-algorithms/capability-projection-register.md)。事件结构已经定义，真实总线/worker和所有模型并未因此实现。

## 入口分支与普通操作

每个候选图以entry_variants选择已有operation_id及其源请求。READ_ONLY和CONTROL_TRANSACTION只执行授权/操作处理/响应，不能凭空要求asset ObjectRef或新建分析结果；分析/同步模型调用走媒体和模型分支。同步模型调用若要持久化task_result，必须先建立有效内部任务/run记录以满足外键，不冒充客户端已有task_id。

先评估active_entry_modes；未选分支记NOT_SELECTED，不能当缺失模型SKIPPED或失败。已选分支的required条件仍严格执行；模型输入/派生对象/外部索引由显式来源绑定，不能由任意前驱JSON代替。普通上传校验等处理由所选操作的源任务和请求契约承担，不自动当模型服务。
