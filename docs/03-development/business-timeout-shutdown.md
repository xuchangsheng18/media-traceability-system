# Business验证器有界超时收尾

2026-10-23补齐完整business验证器的有界超时收尾：执行上限仍1800秒，Linux独立组SIGINT→5秒清理宽限→TERM→2秒→KILL，最终drain/reap最多2秒；先冻结超时瞬间进度，超时仍TIMEOUT/退出2/complete=false及规范0计数，partial JUnit仅独立观测。真实finally缺失RED之后，新旧相邻诊断组合72项、原失败探针及Ruff/格式/289文件类型通过。旧1800秒全组TIMEOUT未关闭，旧last-selector两参数23.47秒通过只属原cohort，不证明挂起位置或根因；本批无完整DB/T014重跑、DB或逃逸孙进程清理验收，Windows DEVNULL直子进程兜底不当原生验证。0新增C，T034仍4C/4R。

## 适用范围

本批只改[验证器](../../scripts/verify_business_foundation.py)及三个诊断测试文件，业务代码、18份SQL迁移、102份Schema、公共接口、原100包锁和CI门禁不变。新内部`_run_pytest`正常返回CompletedProcess；run_checks只消费退出码、私有JUnit和来源校验的进度，不把原始stdout/stderr、命令、环境、PID或异常文本写入公开回执。原monkeypatch只改拦截目标到该适配器，原断言和其余AST保持。

## Linux超时顺序与边界

| 阶段 | 实际控制与可声称的范围 |
| --- | --- |
| 执行 | 独立新session/进程组，PIPE私有捕获；执行限时仍1800秒 |
| 到期 | 先保存该次nonce对应的来源校验进度，再向拥有的组发送SIGINT，给finally固定5秒机会 |
| 升级 | TERM后固定2秒，再KILL；即使leader已退出也不提前poll/wait回收，避免其PGID被复用 |
| 收尾 | 统一最多2秒drain/reap预算；逃逸孙进程持pipe时关闭本方端点并有界wait，不无限等待 |
| 结果 | 原限时已失败，始终TIMEOUT、退出2、complete=false；信号尝试和leader回收不等于PG成员或SQL资源均清理完成 |

宽限是超时后的收尾机会，不是放宽原执行门禁。callback或信号异常不输出原始错误，仍尝试后续kill/reap。清理状态仅包含固定策略、预算、尝试布尔、信号失败计数、直接子进程回收及输出drain观察；process_group_cleanup_verified与database_cleanup_verified保持false。

非Linux采用直接子进程terminate/kill和DEVNULL，避免Windows后台PIPE reader锁阻塞关闭；不宣称独立组、孙进程清理或Windows原生验收。Linux上的fallback分支夹具也不能替代Windows现场验证。

## 进度与部分JUnit

到期前的checkpoint只采一次，收尾更新为finished不能覆盖原观测。它只表示最后看到的source-checked阶段，不能证明哪个测试挂起或超时原因。TIMEOUT的test_count及规范totals均为0，含义是没有完整套件成绩；新增interrupted_junit_observed与partial_totals只保存可解析、非负且有界的四项计数观察，永不解释为PASS或项目完成数。已有安全failure_diagnostics仍保留，参数、XML失败正文和原始日志不公开。

## 实际证据与验收

最终新源码组合72项通过，原故意失败探针退出1且预期失败得到验证，Ruff、格式及289文件类型检查通过；见[精确回执](../00-project/validation/business-timeout-shutdown-report.json)。组合范围重叠，不与历史组相加。真实RED先通过TIMEOUT、0计数和隐私断言，随后在finally产物缺失处失败；它证明旧强制停止没有给该自建finalizer机会，不是旧全组1800秒超时的根因。

| 核验项 | 本批结论 |
| --- | --- |
| 自建finally机会、不会进入下一测试、瞬间checkpoint、私有值隔离 | Linux隔离适用范围通过 |
| 正常子进程不发终止信号；合作/不合作及持pipe的自建子孙边界 | 隔离进程夹具通过；观察不是所有后代清理证明 |
| 原TIMEOUT/退出2/complete=false/规范0计数及失败探针 | 保留并通过回归 |
| 实际数据库清理、全business/T014、新源码托管CI及Windows原生 | 本批未验证或待独立运行 |

旧last-selector的两参数在原cohort以23.47秒通过，保留原源码和回执；它不能关闭旧全组TIMEOUT，也不能把setup阶段观测解释为测试根因。旧完整business结果仍是1800秒TIMEOUT；本批未重跑完整数据库门禁，未删除、归属或确认先前隔离资源已清理。7097旧CI即使身份子作业通过，也不能借作本轮新验证器源码的CI结论。

## 后续与任务状态

先按真实资源和依赖条件再运行适用完整门禁，精确绑定本轮提交、源码及CI终态，并保留失败。T034仍须继续独立连接并发、恢复、未知commit结果、真实提供方/采用/Proof、HTTP和E04运行预算；不以验证器修复替代业务能力。所有170源任务和历史证据保留，154条已证、T001—T123余434、全部余622、0整卡验收；本批零新增完成步骤，T034仍4C/4R。算法和Python候选继续暂缓。
