# 仓库当前状态与使用范围

2026-10-12；研发基线1.1-py310-cpu，DEVELOPMENT_VALIDATED；正式业务/生产NOT_FROZEN。原Word、12模块170任务及≥3场景完整保留。

| 对象 | 当前状态 |
| --- | --- |
| 设计、API、字典与来源 | 62表824字段，精确来源、SQL、Schema、测试及导航已形成；源摘要核验 |
| 环境与版本 | Miniforge py310/Python3.10.22，100包精确锁，npm锁与基础镜像摘要；干净venv安装通过 |
| 最小工程 | 前端/API/对象/SQL/队列/worker/真实合成CPU推理已运行 |
| 工程验证 | 本机CI、SQL、恢复、媒体、浏览器及失败门禁实际执行，见技术报告 |
| Git | 研发快照保存，origin采用用户提供的私有GitHub；无批准生产标签 |
| 托管CI | 私有GitHub Actions已配置；实际run和结论见validation/github-actions-report.json |
| 正式业务/生产 | PythonEOL迁移、身份/案件权限、业务模型/GPU、指标、容量、生产灾备/准入/审批等仍待落实 |

详情见[技术基线](../02-architecture/technical-baseline.md)、[23步状态](../03-development/stage-two-readiness.md)和[验证报告](../02-architecture/technical-validation-report.md)。开发5表没有覆盖62表业务实现；原任务状态不能被整个阶段文档一键标完成。
