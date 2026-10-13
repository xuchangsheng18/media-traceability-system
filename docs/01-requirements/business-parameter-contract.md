# 可配置业务规则与参数

结构源为[business-parameters.schema.json](../../schemas/controls/business-parameters.schema.json)，当前配置为[business-parameters.candidate.json](../../config/business-parameters.candidate.json)。14类参数均有状态、值、依据引用和版本；未知必须为null。CONFIRMED必须具有非空依据/版本和符合各自范围的值。确认记录存在性仍需责任方核验，不由字符串授予权限。

覆盖风险标签与人工阈值、RETURNED处理、未知首发、用途审批与双人事项、回流用途、分类保留日数/冻结例外、20和100并发性质、可用率及RPO/RTO。阈值限定[0,1]且与标签版本一致；保留日数为正整数，法律冻结存在时不得按普通到期删除；具体日数不编造。

技术候选RETURNED支持两条明确路径：补证不改变模型输入时保留run_version、追加result_version并回WAIT_REVIEW；输入/模型/策略改变时创建新run_version，从QUEUED重新计算。两条均保留原结果，重算或结果变化不自动继承批准。适用returned_mode未确定时拒绝自动流转，交由有权责任方登记原因和规则。

正式动作逐次要求当前身份/案件/用途、资产有效、所需规则参数和当前对象版本批准；回流禁止封存测试；同人不能满足独立双人条件；复核不授予导出或训练权。未确认参数返回明确原因，不采用隐含阈值、默认保存年限或默认放行。
