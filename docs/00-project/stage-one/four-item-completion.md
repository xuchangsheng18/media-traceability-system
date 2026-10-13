# 第一阶段四项补充及第二阶段衔接

2026-10-13。图表核验、映射技术语义复核和验收方法已补充；170任务的证据及可计算排期材料已建立。**实际人员容量与日历交付日期仍缺真实输入，不能宣称四项全部正式关闭。**第一阶段24步、第二阶段23步、12模块170任务和不少于3类场景保持。

| 工作 | 本轮实际完成 | 尚需区分的条件 | 当前入口 |
| --- | --- | --- | --- |
| 图表版式核验 | 10原件摘要不变；357页Word＋12页原型的66张概览全部浏览，关键图表放大检查；8项阅读/解释问题登记处置 | 未重排历史Word；未声称全369页100%逐像素交付审校或批注气泡审查 | [版式核验](visual-layout-audit.md)、[页级证据](visual-layout-audit.json) |
| 映射语义复核 | 36功能需求逐项核对原验收、任务、能力、入口与结果身份；纠正事实抽取/关系核查错误读取、资源模块入口过宽、簇读取缺口及运维入口 | 技术复核不是正式业务规则批准；13项接口缺口及完整业务实现保持明确 | [36条结论](../requirement-semantic-review.md)、[结果身份与投影](../../05-workflows/result-identity-and-projection.md) |
| 验收口径 | 24项协议写明统计单位、分母、公式、失败/未知处理、分层、版本及来源目标；8组自建公式夹具可运行 | 实际样本量、正式目标、版本/负载/资源及真实结果未提供；20/100并发性质未自动决定 | [测量协议](../../09-testing/metric-protocols.md)、[公式验证](../validation/acceptance-metric-reference-report.json) |
| 实际排期 | 170任务完整台账；源建议397—491人日复算；21条开发子范围证据；按依赖/人员容量/资源到位日计算的工具和输入表 | 实际负责人、有效工时、剩余工时、起点/工作日历及数据/GPU到位日未提供，因此日历日期保持null | [排期](../execution-schedule.md)、[待填输入](../execution-planning-inputs.json)、[CSV任务表](../../../tasks/execution-schedule.csv) |

“insufficient无证据”此前与Relation/M29证据数组至少1条约束冲突，本轮修复为insufficient允许0条；supports/contradicts等仍要求真实证据。两份OpenAPI、对应Schema和派生TypeScript已同步，6组正反案例检查。无证据结论保存设计为运行结果摘要，不创建虚假的证据关联，不移除数据库真实证据外键，也没有改动运行数据库或服务。

## 对应原阶段步骤

第一阶段第3步接入版式证据，第7/8/12/14/19/21步接入逐需求语义与投影，第9/18步接入测量协议，第17步接入完整任务排期台账。第二阶段第2步消费实际人员/资源输入，第3步消费验收协议，第19步消费Relation/M29修订及身份投影，第21步执行新增5项补充检查。正式冻结与真实业务验收仍各自判定。

## 核验与同步的读取方式

[补充自动检查](../validation/stage-one-completion-report.json)覆盖5组资料/语义/公式/排期/契约检查；[第一阶段12项](../validation/stage-one-validation-report.json)、[接口6项](../validation/interface-documentation-report.json)和[两阶段4项](../validation/phase-readiness-report.json)保持。最新实际平台run、源码摘要和21工程门禁以[GitHub报告](../validation/github-actions-report.json)为准；服务器文件摘要以[同步回执](../server-sync-receipt.json)为准。报告通过不代表全部业务任务实现。

实际排期缺失信息已向用户询问。补齐输入后运行plan_project_schedule.py重建JSON/CSV/阅读页；没有用虚构姓名、假定日期或原37周建议代替实际计划。
