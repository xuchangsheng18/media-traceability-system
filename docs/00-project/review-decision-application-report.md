# 确认结果应用记录

正式决定源为[review-decisions.yaml](review-decisions.yaml)，当前decisions仍为空。下列记录来自已收到的用户开发指令，不是业务方正式签认，也没有关闭主Q或改写原件/任务来源字段。

| 已收到的选择 | 已应用位置/证据 | 仍需确认 |
| --- | --- | --- |
| 全12模块、170任务、至少3场景，分阶段交付 | [范围](project-scope.md)、[任务台账](../../tasks/backlog.yaml)、[阶段交付](stage-one/deliverables.json) | Q-21各期正式边界、Q-33人员与实际排期 |
| 当前Linux服务器、用户Miniforge py310 | [TB-ADR-002](../02-architecture/architecture-decisions/TB-ADR-002-backend-stack.md)、[版本锁](../../config/versions.yaml)、[运行时报告](validation/runtime-lock-report.json) | Q-28用途/真实数据准入、Q-30正式版本差异及许可；源3.11文字保留 |
| 已提供实际私有GitHub仓库地址 | [TB-ADR-014](../02-architecture/architecture-decisions/TB-ADR-014-github-hosted-ci.md)、[工作流](../../.github/workflows/ci.yml)、[实际托管证据](validation/github-actions-report.json) | 正式软件/网络/外发制度；托管CPU夹具不用于敏感数据 |
| 20/100并发仍待定 | [主Q](open-questions.yaml)、[验收评审](review-package/acceptance-review.md) | Q-13/Q-14/Q-22正式性质、口径及资源，不拿微型测试作验收 |

取得正式决定时：先核验决定编号及授权依据，在主记录登记范围/条件/遗留；再同步需求、接口、Schema、SQL迁移、任务和测试；保存变更事件与旧版，重跑适用门禁，重建本阶段候选摘要。没有有效决定时不代签、不从评审空栏生成批准。

## 本轮工程设计记录

ENG-S1-20261013登记用户授权的工程补充及范围，正式decisions保持空。来源原件/主Q/170源任务不自动改状态；完成Schema、配置、校验、类型和导航后重建候选摘要。正式决定输入取得后按逐项适用范围应用并复核。
