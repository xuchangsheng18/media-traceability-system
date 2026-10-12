# 短视频与图片智能识别溯源系统

当前已完成用户指定Miniforge py310的CPU研发最小工程：环境盘点、版本锁定、前后端/数据库/对象/队列/真实推理闭环和本机CI。正式业务/生产NOT_FROZEN。保留12模块、170任务、不少于3类场景；本轮没有宣称全部业务实现。

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
| [shared-contracts](shared-contracts/README.md) | 从两份权威OpenAPI生成的TS类型 |
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

本机CI真实运行，含7项后端、2项前端、1项浏览器、15项集成、5项恢复、6项媒体/查询、73项SQL断言/案例及契约/输入检查，详细数量和命令以报告为准。.gitlab-ci.yml已有同源门禁配置；未注册远程托管项目或Runner，不能声称托管CI成功。

PoC3表与正式62表/824字段设计分开；仅单固定测试案件。正式身份/案件隔离、审批、审计、WORM、业务模型/GPU、20/100并发、中文/大型索引、灾备和生产准入仍需后续验证。Desktop虚拟磁盘余量约1.9GiB，新增大模型/素材前先落实容量；宿主磁盘空闲不能代替虚拟机余量。

源Word及其SHA256保持；Git保存本轮研发快照，没有创建已批准生产基线标签或虚构origin。同步证据见docs/00-project/server-sync-receipt.json。
