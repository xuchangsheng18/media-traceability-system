# Technical Baseline 1.1 — py310 CPU 研发基线

2026-10-13更新；状态 `DEVELOPMENT_VALIDATED`；正式业务/生产基线 `NOT_FROZEN`。用户指定 Miniforge py310，已据此完成环境盘点、开发技术选择和锁定、真实最小工程及GitHub接入。本机21门禁历史保留，现有托管配置为25道工程门禁，实际源码/run/制品证据见[GitHub报告](../00-project/validation/github-actions-report.json)。

| 交付 | 权威入口 | 判定 |
| --- | --- | --- |
| 环境与资源 | [环境约束](environment-constraints.md)、[资源清单](resource-and-team-inventory.md) | 实际节点、宿主/虚拟机差异、CPU配置及配额已记录 |
| 技术选择 | [方案比较](technology-options.md)、[14项TB-ADR](architecture-decisions/README.md) | 本轮研发执行选择；不是生产批准 |
| 版本与制品 | [versions.yaml](../../config/versions.yaml)、[锁文件](../../config/locks/) | Python、npm、基础镜像、环境包、权重都有实际版本/摘要 |
| 整体接口导航 | [接口与数据库文件导航](../03-development/stage-two-interface-database-navigation.md)、[接口专题](../03-api/README.md)、[整体接口说明](../03-api/system-interface-specification.md)、[53操作明细](../03-api/detailed-interface-index.md) | 整体系统接口及服务边界；候选契约与已运行PoC分别判断，13项接口缺口仍开放 |
| 接口结构与规则 | [业务OpenAPI](../03-api/openapi.yaml)、[内部OpenAPI](../03-api/inference-openapi.yaml)、[83组件](../03-api/data-structures.md)、[34能力](../03-api/inference-interfaces.md)、[共用规则](../03-api/common-interface-rules.md) | 唯一结构源与逐字段/权限/幂等/版本要求；不从Schema存在认定全部API或模型运行 |
| 业务数据库设计 | [数据库专题](../04-database/README.md)、[设计](../04-database/database-design.md)、[字典](../04-database/data-dictionary.md)、[SQL](../04-database/initial-schema.sql)、[ER图](../04-database/er-diagram.md) | 62表824字段候选业务设计；初始化DDL用于新隔离空库，不能替代既有数据库版本迁移 |
| 字段来源与接口投影 | [字段来源](../04-database/field-provenance.json)、[API映射](../04-database/api-field-mapping.md)、[映射JSON](../04-database/api-field-mapping.json)、[表任务引用](../04-database/table-task-usage.md)、[首发排序](../04-database/first-source-ranking.md) | 核对cluster/asset/rank等来源指针、数据库列与API投影；任务引用不代表业务访问层已实施 |
| 最小工程 | [运行手册](../10-deployment/development-runbook.md)、[PoC API](../03-api/poc-api.md)、[PoC 数据库](../04-database/poc-database.md) | 浏览器→API→对象/SQL→RabbitMQ→worker→CPU推理→结果已运行 |
| 研发数据库与升级 | [研发5表](../04-database/poc-database.md)、[研发版本迁移](../../backend/migrations/)、[迁移事件机制](../03-development/migrations-and-events.md)、[RLS原型](../04-database/authorization-isolation-prototype.md) | 当前5表实际研发工程及代表性隔离机制；正式62表业务访问/迁移/RLS尚未全部实施 |
| CI与检查 | [CI说明](../03-development/ci-cd.md)、[技术验证报告](technical-validation-report.md)、[GitHub实际报告](../00-project/validation/github-actions-report.json) | 本机21门禁历史；托管25门禁及资料/导航检查按实际run和源码SHA判定 |
| 阶段状态与变更 | [第一阶段24步实际状态](../00-project/stage-one/stage-one-readiness.md)、[第二阶段23步状态](../03-development/stage-two-readiness.md)、[变更控制](technical-baseline-change-control.md) | 保留全部12模块170任务；材料/开发实测/正式冻结分别判定 |

服务：Vue 页面、FastAPI API、PostgreSQL16.15、SeaweedFS4.48、RabbitMQ4.3.6、Celery5.6.3 worker、独立 PyTorch2.14.1+cpu 推理。容器内实际解释器为 Python3.10.22，不使用宿主系统 Python 替代。部署独立项目 `media-trace-py310`、专用网络和5个数据/配置卷；不修改其他项目。

模型为 `synthetic-cpu-encoder/demo-1`，120步真实合成训练、8维向量，复用 M15 Schema；不等同 SSCD，不输出执法结论、不证明业务准确率。大规模检索、真实传播分析、OCR/ASR及其他业务模型没有通过本轮验收。业务提案62表与开发5表（含账本/审计）分开。

正式基线尚需：生产软件准入/国产化/安全边界、受支持Python、身份与案件隔离、完整许可与镜像扫描、真实业务模型/GPU/正式指标、生产灾备与密钥恢复、资源配额、CI组织治理、实际责任人和有效评审。不能把本轮研发验证自动升级为23步全部正式冻结或170项功能已完成。
