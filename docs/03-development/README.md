# 开发、契约与CI

2026-10-12；CPU研发工程已验证，正式基线NOT_FROZEN。

- [第二阶段23步状态](stage-two-readiness.md)：逐项事实、边界和待办。
- [工程入口](repository-bootstrap.md)、[编码规则](coding-standards.md)。
- [CI实际门禁](ci-cd.md)、[生成类型与消息约定](contract-generation.md)。
- [运行手册](../10-deployment/development-runbook.md)、[验证报告](../02-architecture/technical-validation-report.md)。

基础框架完成不等于全部170任务实现；从任务卡核验具体输入、权限、依赖和验收，新增业务应执行其专用验证。

## 1.1工程补充

本轮新增[迁移/事件/租约手册](migrations-and-events.md)、[CI平台说明](ci-cd.md)及[剩余条件与关闭标准](stage-two-gap-register.md)；开发结论和正式冻结分开。

## 第一阶段资料入口

[第一阶段24步、来源和材料](../00-project/stage-one/README.md)记录输入整理做法；与第二阶段23步、根170研发任务分开。当前两阶段的正式冻结都未完成。

## 审批之外还需完成什么

[两阶段19项未完成工作](../00-project/phase-readiness-register.md)将第一阶段7项与第二阶段12项的当前证据、缺失工作、关闭标准和后续业务交付边界逐项列明。优先落实资源/存储、关键接口和处理/结果关联、规则/指标/排期；完整业务研发及生产级安全/灾备/容量按适用任务推进。

[36需求处理与读取映射](../00-project/requirement-processing-map.md)为候选设计；[最新资源快照](../00-project/validation/resource-readiness-snapshot.json)和[仓库治理快照](../00-project/validation/repository-governance-snapshot.json)是时点观测，不等于配额或治理验收。
