# 架构与技术基线

先读[研发技术基线](technical-baseline.md)、[环境约束](environment-constraints.md)、[资源清单](resource-and-team-inventory.md)和[技术验证报告](technical-validation-report.md)。当前真实CPU工程已运行，正式业务/生产仍NOT_FROZEN。

- [系统架构与正式业务边界](system-architecture.md)、[目录归属](repository-layout.md)。
- [技术比较](technology-options.md)、[14项TB-ADR](architecture-decisions/README.md)。
- [兼容矩阵](compatibility-matrix.md)、[许可](licenses.md)、[安全基线](security-baseline.md)。
- [非功能测量](non-functional-requirements.md)、[官方核验](stage-two-official-sources.md)、[变更控制](technical-baseline-change-control.md)。

Python研发与生产分别判断：[TB-ADR-002](architecture-decisions/TB-ADR-002-backend-stack.md#生产python选型与验证条件)列3.13主候选、3.12备选、完整验证/准入与3.10例外条件；[版本配置](../../config/versions.yaml)仅登记候选顺序，[实际证据](../03-development/stage-two-external-inputs.json)仍待填写。当前py310研发、已执行CI及正式生产未批准状态保持。

原件、范围、API和数据库来源关系不因最小工程被覆盖；PoC接口和5表开发数据库在各专题文档中明确区别于53操作/62表设计。
