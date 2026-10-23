# T034不可变请求与计划绑定内核

2026-10-22，按[非算法工程版快速计划](non-algorithm-fast-delivery-plan-20261028.md)交付独立内部内核。目的：在后续任务创建事务之前固定现有请求、主体及提供方证明，避免字段、策略或能力变化被旧证明掩盖。本批没有挂载createTask、创建任务、写数据库或发出执行许可。

## 依据与实际依赖

结构继续取自`schemas/api/common.schema.json`的TaskCreate：case_id、asset_id、scene、policy_version、modules、priority；没有新增公共字段、scene、module、状态或错误码。复用`contracts.validate_api`、`controls.common.canonical`、Actor/Scope及既有显式SourceRegistrationAuthority模式。既有T015数据范围规则要求服务器主体、单位和案件UUID非零；请求中的资产UUID结构有效不等于资产存在、VALID或获准使用。

T033取消专用写入及T015既有范围测试只能作为相应依赖证据，不能代替创建资产事实、正式策略及执行能力。候选DAG结构不是执行授权；内核不自动读取或选用`docs/05-workflows/dags`。完整T034源验收要求和依赖继续保留在[任务卡](../../tasks/backend/T034.md)。

## 内部接口

| 内部入口 | 行为和边界 |
| --- | --- |
| freeze_task_create(scope, body) | 校验现有Schema和服务器Scope，核对案件；构造新的Actor和不可变TaskCreateRequest，保存资产、场景、策略、模块顺序、优先级、规范JSON字节和SHA256。此函数不是认证或授权。 |
| TaskPlanAuthority.resolve(request, connection=…) | 无默认实现的内部提供方协议。部署方后续提供真实映射及版本；只声明Protocol、构造Proof或测试提供方均不会授予执行权。 |
| resolve_task_plan(authority, request, …) | 重建并校验输入快照，传给提供方独立副本；严格验型，核对完整请求、明确许可标记、authority版本、policy摘要、plan ID/版本/摘要、capability ID/版本/摘要及有效期；返回独立副本。 |
| recheck_task_plan(authority, expected, …) | 重新解析并比较全部稳定字段。仅允许有效期延长；缩短、内容或版本变化拒绝。原证明跨过截止时间也拒绝。未来事务调用者必须将它接入授权事务栅栏，本批没有完成该接线。 |

摘要沿用现有JSON语义：排序对象键，保留modules顺序、priority、策略字符串和UUID原始字面大小写；不静默trim、casefold或排序数组。内部UUID另行解析，用于精确对象绑定。Proof只有不可变字段，不携带可变DAG字典或可执行节点。内部版本及引用采用1—128字符结构预算，摘要为64位小写十六进制；这些约束不修改公共policy_version的词法。

返回的请求、Actor和Proof重新构造，提供方保留原对象后变更不会污染已接收快照。时间经校验后转换为UTC，避免可变tzinfo改变已返回证明的截止时刻。提供方应是受信服务器代码；本内核不是恶意Python代码的沙箱或密码学凭证验证器。

错误复用现有注册：公共结构不合法为INPUT_INVALID/422；无效服务器Scope为AUTHORITY_SCOPE_INVALID/503；明确拒绝、撤销或合法证明绑定其他上下文为PERMISSION_REQUIRED/403；缺提供方、错误结构、过期、时钟或适配器故障为CONDITIONAL_FACTS_UNAVAILABLE/503；重查发现变化为AUTHORIZATION_CHANGED/503。原异常文本不进入业务错误。

## 本批实施和验证

先写现有契约冻结测试，观察缺失模块的实际失败；实现后首轮63项通过。新增可变时区截止回归先复现失败，再将返回时间规范化为UTC。随后执行包含64项新测试的受影响纯回归、锁定Ruff检查和完整类型检查。准确命令、源码摘要、数量、复核及同步见[限定验证回执](../00-project/validation/t034-request-plan-binding-report.json)。

本批不修改前端、已挂载路由、共享数据库或依赖；不无故重跑未受影响的前端/浏览器及数据库整套回归。托管CI按本批精确提交单独记录。测试中的Provider均明确为自建夹具，不证明真实身份、资产授权或正式映射已经可用。

## 未完成条件和下一批

1. 落实真实scene—policy—modules—plan/capability映射、authority来源、保管/更新及撤销规则；当前没有默认提供方。
2. 增量接入统一权限对象事实、createTask资产目标及受限SQL目录，核验资产所属单位/案件、状态、来源授权和策略/能力版本。
3. 实现任务、run、node、outbox、审计及幂等回执同事务创建，提交前重新核验范围和本内核证明；失败时全部回滚。
4. 前述条件实际通过后挂载HTTP和页面，核验相同键同摘要重放、不同摘要冲突、并发、撤销、缺提供方及恢复，不用恒定503或空成功计作落地。

T034实际开发负责人和指定复核人已由用户确认为徐昌胜，见[责任登记](../00-project/validation/t034-role-assignment.json)；投入、实际复核及验收决定仍未确认，同人兼任不当作独立双人复核。Python候选、算法、训练和效果评测继续暂缓。原100包锁及CI门禁保留；本批仅源码交付，不是共享采用、正式软件准入或整任务验收。
