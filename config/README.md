# 版本、环境与资源

2026-10-13文档状态更新；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

versions.yaml记录当前py311与服务版本（旧py310锁保留回退）；locks目录含100包精确锁、Conda explicit、观测freeze、镜像摘要和环境包摘要；hardware-inventory.example.yaml区分宿主和Desktop虚拟机。

## 验证入口

Linux仓库根目录运行，前置为已锁py311、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py311/bin/python scripts/verify_runtime_lock.py
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

凭据存仓库外私有runtime，不放此目录。样例为开发时点，非生产设备配置、独占配额或GPU清单。

ci-bootstrap-lock.json固定GitHub复建用Miniforge安装包URL/SHA与Actions提交摘要；活动py311锁用于重建，原py310锁保留回退。固定摘要是复建输入，平台执行证据另存validation/github-actions-report.json。


实际资源/身份/用途授权数据仍填写[第二阶段输入表](../docs/03-development/stage-two-external-inputs.json)，尚未确认的值保持待定；服务器研发数据卷容量按[资源快照](../docs/00-project/validation/resource-readiness-snapshot.json)及[23步状态](../docs/03-development/stage-two-readiness.md)判断。
