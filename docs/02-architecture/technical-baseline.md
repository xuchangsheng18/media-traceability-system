# Technical Baseline 1.1 — py310 CPU 研发基线

2026-10-12；状态 `DEVELOPMENT_VALIDATED`；正式业务/生产基线 `NOT_FROZEN`。用户指定 Miniforge py310，已据此完成环境盘点、开发技术选择和锁定、真实最小工程与本机21门禁验证及GitHub接入。

| 交付 | 权威入口 | 判定 |
| --- | --- | --- |
| 环境与资源 | [环境约束](environment-constraints.md)、[资源清单](resource-and-team-inventory.md) | 实际节点、宿主/虚拟机差异、CPU配置及配额已记录 |
| 技术选择 | [方案比较](technology-options.md)、[14项TB-ADR](architecture-decisions/README.md) | 本轮研发执行选择；不是生产批准 |
| 版本与制品 | [versions.yaml](../../config/versions.yaml)、[锁文件](../../config/locks/) | Python、npm、基础镜像、环境包、权重都有实际版本/摘要 |
| 最小工程 | [运行手册](../10-deployment/development-runbook.md)、[PoC API](../03-api/poc-api.md)、[PoC 数据库](../04-database/poc-database.md) | 浏览器→API→对象/SQL→RabbitMQ→worker→CPU推理→结果已运行 |
| CI与检查 | [CI说明](../03-development/ci-cd.md)、[技术验证报告](technical-validation-report.md) | 本机21门禁真实运行；托管实际结果见github-actions-report.json |
| 范围与变更 | [23步状态](../03-development/stage-two-readiness.md)、[变更控制](technical-baseline-change-control.md) | 保留全部12模块170任务；开发快照与正式冻结分开 |

服务：Vue 页面、FastAPI API、PostgreSQL16.15、SeaweedFS4.48、RabbitMQ4.3.6、Celery5.6.3 worker、独立 PyTorch2.14.1+cpu 推理。容器内实际解释器为 Python3.10.22，不使用宿主系统 Python 替代。部署独立项目 `media-trace-py310`、专用网络和5个数据/配置卷；不修改其他项目。

模型为 `synthetic-cpu-encoder/demo-1`，120步真实合成训练、8维向量，复用 M15 Schema；不等同 SSCD，不输出执法结论、不证明业务准确率。大规模检索、真实传播分析、OCR/ASR及其他业务模型没有通过本轮验收。业务提案62表与开发5表（含账本/审计）分开。

正式基线尚需：生产软件准入/国产化/安全边界、受支持Python、身份与案件隔离、完整许可与镜像扫描、真实业务模型/GPU/正式指标、生产灾备与密钥恢复、资源配额、CI组织治理、实际责任人和有效评审。不能把本轮研发验证自动升级为23步全部正式冻结或170项功能已完成。
