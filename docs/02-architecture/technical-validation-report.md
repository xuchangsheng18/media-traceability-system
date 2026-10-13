# 第二阶段技术验证报告

2026-10-13复核，1.1-py310-cpu。开发节点172.16.58.179，Miniforge py310/Python3.10.22，CPU。服务器原1.1完整CI记录为21门禁PASS；当前配置为25道，托管实际结论另认平台报告与源码SHA。结论仅适用于下列实际开发检查，正式业务/生产NOT_FROZEN。

| 检查 | 证据 | 精确适用范围 |
| --- | --- | --- |
| 环境与锁 | [environment-inventory.json](../00-project/validation/environment-inventory.json)、[runtime-lock-report.json](../00-project/validation/runtime-lock-report.json)、[lock-reproduction-report.json](../00-project/validation/lock-reproduction-report.json) | 真实宿主/VM/服务、100包精确锁、原1.0全新venv安装；未改用户py310 |
| 完整本机CI | [ci-all-report.json](../00-project/validation/ci-all-report.json) | 21门禁，后端15单元、前端2单元、TS/wheel/镜像、1浏览器 |
| 托管平台 | [github-actions-report.json](../00-project/validation/github-actions-report.json) | 独立一次性GitHub Runner；按status/run/head SHA/制品摘要认结果，不冒用本机报告 |
| 输入/字段 | [local-validation-report.json](../00-project/validation/local-validation-report.json)、[database-contract-report.json](../00-project/validation/database-contract-report.json) | 10资料项、17数据库契约项、335夹具；设计62表824字段，非全业务实现 |
| 正式SQL基础 | [database-foundation-report.json](../00-project/validation/database-foundation-report.json) | 新建隔离数据库25常规+48首发/证据=73断言/案例，报告51执行记录 |
| 生成契约 | [generated-contract-report.json](../00-project/validation/generated-contract-report.json) | 两份OpenAPI与一份事件Schema生成共4份TS类型，无字节漂移 |
| 迁移/竞态 | [migration-fencing-report.json](../00-project/validation/migration-fencing-report.json) | 15项；8数据库竞争者单领取、摘要篡改拒绝、旧租约拒绝、列/表权限；非8Celery完整演练 |
| 开发集成 | [poc-integration-report.json](../00-project/validation/poc-integration-report.json) | 21项真实对象/SQL/queue/worker/CPU、状态/审计/原始追踪、内部Problem |
| 故障恢复 | [poc-resilience-report.json](../00-project/validation/poc-resilience-report.json) | 5项broker/租约/重启持久/版本读回/幂等冲突 |
| 合成媒体/查询 | [media-query-report.json](../00-project/validation/media-query-report.json) | 6项10帧编解码、微型simple全文/3向量/带环SQL与内部契约 |
| 抽帧源时间 | [media-timestamp-report.json](../00-project/validation/media-timestamp-report.json) | 非零5秒原点，抽源帧0/5；PTS5000/5500、time_base1/1000→源5000/5500ms与派生0/500ms；未测VFR/正式视频链路 |
| 冷备与隔离恢复 | [development-recovery-report.json](../00-project/validation/development-recovery-report.json) | 8项、5表全部行、45对象原VersionId/摘要及权重恢复；已有私有凭据保留，不是生产WAL/PITR/RPO/RTO |
| 浏览器/训练 | [poc-browser-report.json](../00-project/validation/poc-browser-report.json)、[poc-ui.png](../00-project/validation/poc-ui.png)、[synthetic-training-experiment.json](../00-project/validation/synthetic-training-experiment.json) | 真实端到端、截图前清空令牌；原64随机张量120步合成训练，非业务准确率 |
| 代表性权限/中文查询 | [stage-two-isolation-report.json](../00-project/validation/stage-two-isolation-report.json) | 21项隔离RLS/撤销/追加历史及4条自建中文GIN词项查询；未接正式身份、未证明62表已部署或业务语义检索达标 |
| 合成VFR媒体 | [stage-two-media-report.json](../00-project/validation/stage-two-media-report.json) | 11项8帧VFR、音频、字幕、旋转坐标；真实媒体/OCR/ASR与长视频性能仍未验收 |
| 交付控制及软件物料 | [stage-two-supplement-report.json](../00-project/validation/stage-two-supplement-report.json)、[stage-two-software-report.json](../00-project/validation/stage-two-software-report.json) | 6组运维/离线控制和实际镜像OS采集；资源CRITICAL、许可/漏洞/离线交付未因采集而关闭 |
| 现场只读复核 | [同步与复核回执](../00-project/server-sync-receipt.json)的repository_readiness_review | 7服务健康、5项HTTP检查、12处运行代码摘要匹配；不代替完整链路重测、并发/真实数据或生产验收 |
| 失败/秘密 | [ci-failure-gate-report.json](../00-project/validation/ci-failure-gate-report.json)、[repository-secrets-report.json](../00-project/validation/repository-secrets-report.json) | 主动失败阻断构建/部署；开发凭据确切值检查非全DLP |
| 依赖审计 | [python-audit-report.json](../00-project/validation/python-audit-report.json)、[npm-sbom.cdx.json](../00-project/validation/npm-sbom.cdx.json) | Python元信息/npm物料及audit；torch CPU被pip-audit跳过，非全部OS漏洞/许可审查 |

1.0历史证据位于validation/history/1.0-py310-cpu，按原时间/scope阅读。源Word及摘要不改；新功能增加测试，未删除测试或放宽断言。开发冷恢复临时S3对启动瞬态5xx作限次等待，其他错误仍失败。

未完成正式身份、62表业务迁移/逐表隔离、审批/WORM、真实模型/GPU与授权测试集、真实媒体全链路/大型中文索引、完整DAG/取消/长任务续租、生产灾备/密钥/正式指标/20和100并发、完整OS漏洞/许可审查、独占资源/人员和有效评审。代表性RLS、合成VFR和物料采集已执行，不能重新列为完全未开展，也不能升级为相应完整业务验收。完整关闭条件见[剩余条件登记](../03-development/stage-two-gap-register.md)及[12项清单](../03-development/stage-two-completion-matrix.md)。
