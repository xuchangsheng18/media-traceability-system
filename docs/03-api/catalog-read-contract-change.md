# 案件内资产及任务读取契约补充

2026-10-21，用户明确回复“同意增加case_id并同步相关文件”。本次只为尚未挂载的`listAssets`和`listTasks`增加必填UUID查询参数`case_id`；两个操作的HTTP方法、路径、原limit/cursor、权限码和响应Schema均保持原定义。变更源为[业务OpenAPI](openapi.yaml)，派生操作页、操作索引和TypeScript类型由生成器同步。

| 操作 | HTTP入口 | 读取方法的要求 |
| --- | --- | --- |
| getAsset | `GET /api/v1/assets/{id}` | 读取真实资产元数据及固定ObjectRef，核对同单位/案件、来源、读取用途和分类；不提供直接对象路径或下载旁路。 |
| listAssets | `GET /api/v1/assets?case_id=…&limit=…&cursor=…` | 案件范围及每项对象授权后分页；无权记录不进入结果或计数，拒绝跨案件/身份/操作游标。 |
| listTasks | `GET /api/v1/analysis/tasks?case_id=…&limit=…&cursor=…` | 从当前任务表列出任务，包含尚无结果的排队/运行任务，不从历史分析投影拼造当前状态。 |

必填案件参数不构成授权。服务端仍校验实际身份、角色、单位、有效案件关系、来源及用途；缺权威事实时拒绝。页大小仍取已有1—100范围。游标必须规范编码并与本次身份、案件、操作和分页条件一致；切换案件应从第一页重新查询。

本批代码、增量迁移、实际测试及未验收范围见[实施计划](../03-development/t001-t123-catalog-read-implementation-plan.md)和[验证回执](../00-project/validation/t001-t123-catalog-read-report.json)。接口定义、代码挂载、隔离测试、正在运行的实例版本、共享采用分别记录。新0012不等于当前0011演示库已经升级。

历史[36项需求语义复核](../00-project/requirement-semantic-review.json)及其旧摘要保持原字节。当前契约的衔接依据为[限定变更记录](../08-security/catalog-read-contract-adoption.json)和记录所指的旧原文副本；资料校验逐一核对旧摘要、当前摘要、明确确认范围及两个必填UUID参数，去除这两个新增参数后要求完整契约结构与旧文档一致。其他字段、路径或权限变化仍会失败，这次衔接不构成新的业务批准或运行验收。
