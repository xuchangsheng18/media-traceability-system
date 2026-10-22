# T034-I02计划绑定与执行材料纯边界

2026-10-22（北京时间）。依据[已批准计划](t034-creation-implementation-plan.md)推进纯PlanBinding/ExecutionMaterials组件；责任人及指定复核人沿用徐昌胜，责任登记不等于本人已审。原[批准记录](../00-project/validation/t034-i01-i05-implementation-approval-20261022.json)及20c1be01计划基线保留。I02未整步完成。

本批只新增task_creation_authority模块及其纯测试。固定请求/主体、A/B独立摘要、revision/head和映射/策略/计划/能力/输入身份与摘要的纯数据边界，复用已有I01严格材料校验，冻结规范字节及隔离投影；输入不一致时拒绝，不选择默认计划或任意handler。调用者传入的校验收据及当前事实指纹仅为opaque规范JSON字节/独立摘要；这不是正式采用、许可准入Schema，也不证明数据库current-head、撤销顺序或动态能力真实成立。具体支持字段/错误及边界以[精确源码和回执](../00-project/validation/t034-plan-authority-report.json)为准。

| 内部入口或类型 | 本批实现的精确含义 |
| --- | --- |
| `PlanBinding` | 保存完整旧Proof及请求A、独立B、revision/head行版本、mapping身份、完整policy身份、映射窗口、校验回执精确字节/摘要、恢复代际和当前事实精确字节/指纹。任一身份/版本不是采用批准。 |
| `ExecutionMaterials` | 保存隔离的PlanBinding及I01 MaterialBundle；包含policy/plan/capability/input规范字节和每节点输入快照，不包含执行结果或数据库锁。 |
| `freeze_plan_binding(context, proof, **metadata, budgets, clock)` | 逐项校验并深复制完整绑定；显式预算校验opaque对象的严格JSON、规范字节及摘要；Proof须在当前身份与映射窗口内。不验证调用者来源可信。 |
| `freeze_execution_materials(context, binding, policy_raw, plan_raw, capability_raw, input_raw, budgets, clock)` | 复用I01解析器且要求输入本身为规范字节；核对请求场景、有序modules、priority、policy版本、asset及三份完整材料身份/摘要，生成各节点输入快照。 |
| `recheck_plan_binding(context, expected, current, budgets, clock)` | 比较调用者提供的两份完整观测；同材料摘要但revision/head/回执/事实/代际变化仍拒绝。只允许Proof期限延长且不得越过当前身份或固定映射窗口。不是数据库或权威提供者读取。 |
| `recheck_execution_materials(context, expected, current, budgets, clock)` | 重建并比较所有材料与输入/节点快照；不因asset_id或plan摘要相同而忽略对象版本、来源授权版本等输入变化。两类recheck结束前重新采样时钟，拒绝调用过程中跨过原Proof或有效窗口。 |

上表中的`budgets`均为调用者必须显式提供的既有MaterialBudgets，不设业务默认数值；实际函数中的关键字专用参数见源码。非法材料、缺失类型或损坏快照使用既有503拒绝；完整观测发生稳定绑定变化使用既有AUTHORIZATION_CHANGED。身份过期及明确Proof拒绝沿用原有401/403边界；本批不新增公共HTTP错误或端点。

本批没有SQL、实际数据库读取/锁、真实提供方、guard/条件授权接线、HTTP挂载、ACTIVE采用或真实202，不生成任务/run/outbox。上下文及材料组件存在不等于权限ALLOW。I02仍须固定LOOKUP/CASE函数、当前事实/能力和guard生命周期；I03原子创建、I04 HTTP、I05适用全回归继续待办。已发布0016不修改；后续SQL只用0017及新增迁移，全部原契约、锁与门禁保持。

最终392项纯组合包含本批84项及未改的原308项（Context/旧绑定127、材料147、离线工具34）；原308是回归覆盖，不当新增工作。Ruff/格式和272文件类型检查、一次新鲜源码审查及失败实际原因见专项回执。新组件缺失RED仅证明新增结构尚不存在，不表述旧业务越权漏洞，不以收集/import/环境失败替代业务RED。无数据库、浏览器、前端或完整权限回归fresh主张，不复制旧PASS为当前证据。

prior CI39772836414绑定4cee65a07af4ff9deb6ee23a5516613c0d29080e，在本批资料编制时观测状态`in_progress`、结论`None`；这不验证本批新源码。pending不复用过期artifact，completed只投影本次实际platform-digest/job-owned/source/attempt/window结果；扫描报告缺自身source仅诊断，匹配不等于适用性、风险接受或安全通过。后续状态、payload的GitHub/Linux精确提交与CI以专项回执最新观察为准，不因本地通过清除扫描失败。

本批仅新增T034一条已证子步骤：4已证/4组剩余，T001—T123累计154条已证、434组剩余，全部170任务622组剩余、整卡验收0项。E01采用权威、E02精确生效材料/映射、E03真实当前分类/来源/身份/恢复/handler事实、E04预算与期限均未确认；不猜填或自动放行。Python候选、算法、训练和效果评测继续暂缓，未做共享升级或正式验收。
