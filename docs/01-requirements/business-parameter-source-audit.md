# 业务参数的本地来源审查

按用户要求审查本地总体设计V1.4及成对任务书V1.3；机器结果见[business-parameter-source-audit.json](business-parameter-source-audit.json)。转换正文与原件摘要由第一阶段内容审计保护，下面给出实际条款行。来源明确的规则用于设计，候选数值不升级为正式批准。

| 参数 | 原文位置 | 实际发现与当前处理 |
| --- | --- | --- |
| risk_label_version | [V1.4第491行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | VALUE_OR_SCOPE_EXPLICITLY_UNCONFIRMED_IN_SOURCE；候选=无已确认值；正式值待填 |
| review_thresholds | [V1.4第491行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | VALUE_OR_SCOPE_EXPLICITLY_UNCONFIRMED_IN_SOURCE；候选=无已确认值；正式值待填 |
| returned_mode | [V1.4第373行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=['supplement_same_run', 'recompute_new_run', 'reason_selected']；正式值待填 |
| unknown_origin_policy | [V1.4第1397行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=['insufficient_no_certain_origin']；正式值待填 |
| approval_purposes | [V1.4第517行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=无已确认值；正式值待填 |
| dual_approval_purposes | [V1.4第491行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | VALUE_OR_SCOPE_EXPLICITLY_UNCONFIRMED_IN_SOURCE；候选=无已确认值；正式值待填 |
| feedback_allowed_purposes | [V1.4第523行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=无已确认值；正式值待填 |
| retention_days_by_data_class | [V1.4第150行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | VALUE_OR_SCOPE_EXPLICITLY_UNCONFIRMED_IN_SOURCE；候选=无已确认值；正式值待填 |
| legal_hold_policy | [V1.4第11行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=无已确认值；正式值待填 |
| accepted_concurrency_20 | [V1.4第1409行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=无已确认值；正式值待填 |
| accepted_concurrency_100 | [V1.4第1409行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=无已确认值；正式值待填 |
| availability_target | [V1.4第1413行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | SOURCE_CANDIDATE_OR_EXPLICIT_RULE_NOT_FORMAL_PARAMETER_APPROVAL；候选=[0.995, 0.999]；正式值待填 |
| rpo_seconds | [V1.4第1414行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | VALUE_OR_SCOPE_EXPLICITLY_UNCONFIRMED_IN_SOURCE；候选=无已确认值；正式值待填 |
| rto_seconds | [V1.4第1414行](<../_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | VALUE_OR_SCOPE_EXPLICITLY_UNCONFIRMED_IN_SOURCE；候选=无已确认值；正式值待填 |

源文确有RETURNED补证/重算设计，当前可执行规则按参数选择路径；CLOSED分支与当前API枚举存在差异，保留待决定，不自动新增或映射终态。人工阈值、双人范围、具体保存年限、RPO/RTO和20/100性质在原文中仍待确认；可用率99.5%/99.9%属于源建议。
