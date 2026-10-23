# T034-I02请求上下文组件与未接线边界

2026-10-22（北京时间）。依据[已批准计划](t034-creation-implementation-plan.md)第4.1节推进I02首批纯组件；开发负责人和指定复核人沿用徐昌胜，责任登记不等于本人已审。批准时基线和范围沿用[原决定](../00-project/validation/t034-i01-i05-implementation-approval-20261022.json)，本批不新增实际采用权或预算确认。

新增TaskCreationContext冻结主体、TaskCreateRequest和独立授权摘要。复用既有freeze_task_create及object_facts.digest，A保留原请求正文规范摘要，B按现有path/query/body规则计算；二者语义不同，不要求相等，也不改原幂等语义。ContextVar仅通过显式上下文管理进入/重置，读取经过重查并返回隔离副本；未绑定时返回None。主体、请求、期限、时钟或摘要不一致时沿用现有拒绝，不生成业务成功。嵌套/异常恢复和并发隔离以实际测试回执为准；不能把上下文存在解释为权限ALLOW。

本批只新增[上下文模块](../../backend/business_app/permissions/task_creation_context.py)和[纯测试](../../tests/business/test_task_creation_context.py)。没有改guard、object_facts、main或公共契约/路由，没有接SQL、当前计划权威或真实提供方；没有DB迁移/查询或共享服务动作。I02还须固定LOOKUP/CASE函数、当前事实及能力、条件授权/guard生命周期接线和对应隔离验证；I03原子创建、I04 HTTP和I05整套也未完成。已发布0016固定，后续SQL只能0017及新增迁移。

最终127项纯回归包括63项上下文和64项未改的原请求/证明绑定测试；Ruff、格式和270文件类型检查通过，两文件精确源码及一次新鲜源码审查见[专项回执](../00-project/validation/t034-request-context-report.json)。缺新组件的一例断言仅为结构RED，不能表述旧业务漏洞或越权复现；不把import/收集失败当业务故障。无DB、完整权限、浏览器或前端回归fresh主张，I01旧验证保持其原源码和范围，不重复相加。

既有CI39766494694精确绑定源码587890f440987edefc8cc2ccb185888c668b40c9，在本批资料编制时观测的状态为`in_progress`、结论`None`，观察时刻见回执。未完成时不复用过期artifact或声称通过；完成后只能按实际owned/source/attempt核验结果另更新。它不是本批上下文代码CI；本批提交、GitHub/Linux源码同步及托管结果需后续实际回执，不因本地纯检查清除软件扫描失败。Python候选、算法、训练和效果评测继续暂缓。

本批仅新增T034一条已证子步骤：3已证/4组剩余，T001—T123累计153条已证、434组剩余，全部170任务622组剩余、整卡验收0项。I02未整步完成；E01采用/撤销权威、E02精确材料映射、E03真实分类/来源/身份/恢复/handler事实和E04预算期限仍未确认。未知项保持相应正式动作拒绝，不产生ACTIVE或真实202，不以测试、计划或上下文对象代替正式业务授权。
