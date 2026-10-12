# 短视频与图片智能识别溯源系统

当前已完成用户指定Miniforge py310的CPU研发最小工程：环境盘点、版本锁定、前后端/数据库/对象/队列/真实推理闭环和本机21道CI门禁；GitHub实际运行另见平台报告。正式业务/生产NOT_FROZEN。保留12模块、170任务、不少于3类场景；本轮没有宣称全部业务实现。

服务器仓库：`/workspace/glwy/projects/media-traceability-system`；Python：`/opt/conda/glwy/envs/py310/bin/python`（3.10.22）。应用容器明确使用打包的同一py310。Python3.10已结束支持；生产前迁移并重新验证，见[环境约束](docs/02-architecture/environment-constraints.md)。

## 运行

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py pack
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py build
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py up
/opt/conda/glwy/envs/py310/bin/python scripts/run_ci.py all
```

页面在服务器回环地址 `http://127.0.0.1:14180`；从本机通过SSH转发访问。启动前提、首次复建、研发令牌取得方法和停止操作见[运行手册](docs/10-deployment/development-runbook.md)。秘密与权重在仓库外/命名卷中，不入Git。

页面上传自建PNG/JPEG→S3版本化原件和独立分析副本→PostgreSQL事务任务/outbox→RabbitMQ→Celery→独立PyTorch CPU推理→结果保存与展示。模型synthetic-cpu-encoder/demo-1真实训练和推理、mock=false，是8维合成工程验证模型，不是SSCD或正式业务模型。

## 阶段材料与阅读顺序

| 阶段 | 工作范围 | 当前入口与状态 |
| --- | --- | --- |
| 第一阶段 | 24步，来源归档→需求/契约/数据/任务/测试→评审与输入冻结 | [第一阶段材料导航](docs/00-project/stage-one/README.md)、[24步操作与交付](docs/00-project/stage-one/steps-and-deliverables.md)；候选已整理，正式NOT_FROZEN |
| 第二阶段 | 23步，环境/资源→选型与版本→最小工程→CI→技术评审与冻结 | [23步状态](docs/03-development/stage-two-readiness.md)；开发工程/CI已验证，正式NOT_FROZEN |

先核对第一阶段输入与来源，再阅读第二阶段技术执行依据；[阶段衔接](docs/00-project/stage-one/handoff.md)明确哪些输入由实际工程消费。24步、23步与170研发任务是三套编号。

第一阶段本轮补齐[原件内容核对](docs/00-project/stage-one/source-content-audit.md)、[955处来源章节映射](docs/00-project/stage-one/source-section-map.md)、[33项具体评审清单](docs/00-project/review-package/README.md)和[当前候选输入摘要](docs/00-project/stage-one/input-baseline-candidate.md)。12项自动检查验证来源与摘要，不代替视觉核对、业务签认或170任务实现。

## 文档入口

- [完整文档导航](docs/README.md)：逐文件职责、要求、来源和实际索引。
- [技术基线](docs/02-architecture/technical-baseline.md)、[23步状态](docs/03-development/stage-two-readiness.md)。
- [技术验证报告](docs/02-architecture/technical-validation-report.md)、[CI说明](docs/03-development/ci-cd.md)、[版本锁](config/versions.yaml)。
- [业务任务卡](tasks/README.md)、[工程规则](AGENTS.md)、[未决问题](docs/00-project/open-questions.md)。

## 各目录

| 目录 | 当前职责 |
| --- | --- |
| [frontend](frontend/README.md) | Vue/TS研发界面、依赖锁、类型/单元/浏览器测试 |
| [backend](backend/README.md) | FastAPI、配置/错误/日志、PoC迁移、事务任务与worker |
| [ai-services](ai-services/README.md) | 真实CPU合成训练与M15契约推理；后续正式模型 |
| [shared-contracts](shared-contracts/README.md) | 从两份OpenAPI及事件Schema生成的3份TS类型 |
| [schemas](schemas/README.md) | 模型/数据Schema、夹具及语义检查 |
| [config](config/README.md) | 精确版本、包/镜像/环境摘要、资源样例 |
| [deploy](deploy/README.md) | 7服务Compose、镜像构建、代理及命名卷 |
| [scripts](scripts/README.md) | 启动、资料/SQL/集成/恢复、CI和清单工具 |
| [tests](tests/README.md) | 后端、SQL、夹具与工程验证 |
| [datasets](datasets/README.md) | 数据元信息；研发合成数据；敏感样本不入库 |
| [prompts](prompts/README.md) | 提示词来源与版本化要求 |
| [tasks](tasks/README.md) | 170源任务与单独的研发工程证据，不混淆完成状态 |
| [docs](docs/README.md) | 来源原件、设计、技术决定与实测记录 |

## 判定范围

本机CI真实运行，含15项后端、2项前端、1项浏览器、21项集成、5项恢复、6项媒体/查询、73项SQL断言/案例及契约/输入检查，详细数量和命令以报告为准。新增15项迁移/竞态、源PTS映射与8项冷备恢复。用户指定[私有GitHub](https://github.com/xuchangsheng18/media-traceability-system)采用Actions执行同源门禁，实际平台run、源码SHA与制品结论见[平台报告](docs/00-project/validation/github-actions-report.json)。

开发5表（含审计和迁移账本）与正式62表/824字段设计分开；仅单固定测试案件。正式身份/案件隔离、审批、审计、WORM、业务模型/GPU、20/100并发、中文/大型索引、生产灾备/密钥恢复和生产准入仍需后续验证。Desktop虚拟磁盘余量约1.9GiB，新增大模型/素材前先落实容量；宿主磁盘空闲不能代替虚拟机余量。

源Word及其SHA256保持；Git保存本轮研发快照，origin采用用户提供私有GitHub，没有创建已批准生产基线标签。同步证据见docs/00-project/server-sync-receipt.json。

当前1.1补充的使用要求见[迁移事件手册](docs/03-development/migrations-and-events.md)、[开发冷恢复](docs/10-deployment/development-backup-restore.md)与[剩余条件/关闭标准](docs/03-development/stage-two-gap-register.md)。

## 整体接口详细入口

[系统整体接口说明](docs/03-api/system-interface-specification.md)、[53份逐操作/12模块导航](docs/03-api/detailed-interface-index.md)、[83组件字段](docs/03-api/data-structures.md)、[34内部能力](docs/03-api/inference-interfaces.md)已显式整理。第二阶段第19步保留PoC实测，整体接口仍有[13项开放缺口](docs/03-api/interface-gap-register.md)；候选路径不可调用，未标全系统接口冻结。
