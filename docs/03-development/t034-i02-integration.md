# T034-I02受限SQL、事实与guard工程候选

2026-10-22（北京时间）。本批16文件代码已实现，依据[已批准计划](t034-creation-implementation-plan.md)推进；负责人/指定复核人均徐昌胜，登记不代表本人已审。当前为SOURCE_CANDIDATE_WITH_FAILED_OR_INCOMPLETE_GATE；[精确回执](../00-project/validation/t034-i02-integration-report.json)区分限定通过、完整回归实际失败和未运行项，不能作为可运行发布/正式验收证明。

固定SQL metadata/execution为21/9列，LOOKUP精确asset/read-only/无锁无正文，CASE要求同根上下文/evidence并持锁重查唯一revision/head及三摘要。原receipt字节和受限投影分别处理；有限事实不能覆盖既有SQL核心。4表列级UPDATE仅满足PG16 FOR SHARE，RLS加字典序先执行的INVOKER语句guard拒绝所有case_reader DML（包括0行epoch副作用）。非超级迁移owner需要管理员明确的临时SET-only准备与finally撤权，不能隐式提升session_user。字段、ACL、锁序及安装前提见[数据库读口说明](../04-database/task-creation-scope-read-contract.md)。

最终178项SQL/T015/历史组合、544项纯组合和279文件Mypy、Ruff/format绑定同一16源码cohort并通过，范围重叠不相加。此前源码完整业务脚本保留expected0/actual2、BLOCKED_OR_FAIL、test_count0、1800.263秒窗口；运行未完成，没有完整PASS或可用完整测试总数，后续业务失败探针未执行。不能拿178/544或旧CI填补该门禁。此前1092项权限回归有1项默认支持声明失败；保留旧断言修复为专用端口显式接线才增加createTask声明。当前SQL组合包含该原失败断言和两个默认/显式端口用例。历史权限回归状态为`HISTORICAL_PERMISSIONS_FAILURE_BEFORE_ADVERTISEMENT_FIX`，最终只按同source/本轮nonce实际终态更新metadata回执，不把该范围通过当完整业务回归通过。原工作流、超时、失败探针语义、断言、skip和main保护均不改。

实际结构RED、零行副作用4例RED及修复、初轮pure旧断言冲突、import/格式/类型与owner/recovery安装夹具失败全部保留；最终独立core/SQL审查覆盖说明见回执，未声称所有测试文件本人独立复核。真实采用/收据语义/Proof发行者、当前handler许可/发布/可用性、分类/独立恢复/E04实际预算仍缺，unknown不填true。没有I03原子创建、I04 HTTP挂载或真实202；原16SQL、原100包锁、公共契约和前端不变，未做共享迁移/重启。

依据用户最新委托，已选定[内部研发配置与采用设计](t034-internal-development-decisions.md)，包括256KiB材料、16节点、64引用、30秒Proof和24小时控制回执等显式研发初始值；尚未应用到运行配置或授予真实业务权。

候选C05未计数。T034保持4已证/4组剩余，T001—T123累计154已证、434组剩余，全部170任务622组剩余、整卡验收0。代码与限定通过结果已展示，完整门禁及真实前置条件未齐，I02/I05未完成；下一批先定位完整回归失败/超时，不放宽门禁。源码可同步开发分支供审查，三端提交/CI另按实际回执，不合并main或升级共享环境。prior CI仅绑定其旧精确源码，不能证明本批。算法与Python候选继续暂缓。
