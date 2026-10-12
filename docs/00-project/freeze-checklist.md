# 开发输入冻结检查表

当前NOT_FROZEN。以下区分机器证据、可评审材料和责任方确认；任何单项检查通过都不能独立触发正式冻结。当前快照入口为[候选输入清单](stage-one/input-baseline-candidate.md)，旧baseline文件清单保留历史身份。

| 检查项 | 当前证据 | 当前状态与关闭要求 |
| --- | --- | --- |
| 原件身份与成对版本 | source-inventory.json、source-content-audit.json | 10份字节保护；正式来源身份/优先级待Q-23核验 |
| 转换文字、表格、图片、批注与链接 | stage-one/source-content-audit.md | 正文存在性及1700来源字段核对通过；视觉版式未核验，不当无损转换 |
| 来源章节与工程路径 | stage-one/source-section-map.json | 准确原件位置+候选路由；各专题语义映射待人工复核 |
| 24步产物、170任务、62表关系 | stage-one/deliverables.json、table-task-usage.json与验证报告 | 结构检查按实际报告；不表示任务或数据库业务已实施 |
| 33项问题的评审准备 | review-package/README.md、stage-one/review-register.json | 已有具体输入/影响建议/关闭条件；决定与负责人仍为空 |
| 范围、指标、权限、数据用途及取证规范 | review-decisions.yaml、open-questions.yaml | 逐动作确认有效授权、适用范围和例外；无法用CI签认 |
| 人员、资源和分期排期 | tasks/backlog.yaml、Q-15/Q-29/Q-33 | 无已批准人员/配额/排期，不能从角色推导人名 |
| 当前输入候选摘要 | stage-one/input-baseline-candidate.json | 文件集合及SHA可验证，生成候选不等于正式批准 |
| 跨文件决定应用及差异 | review-decision-application-report.md | 已应用开发指令；正式决定为空，尚无正式应用事件 |
| 正式基线批准 | baseline-1.0.md、责任方决定/授权记录 | 未取得；批准后需形成版本、范围、遗留及签认，再按仓库规则产生正式基线 |
