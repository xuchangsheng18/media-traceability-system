# 版本、环境与资源

2026-10-12；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

versions.yaml记录py310与服务版本；locks目录含100包精确锁、Conda explicit、观测freeze、镜像摘要和环境包摘要；hardware-inventory.example.yaml区分宿主和Desktop虚拟机。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/verify_runtime_lock.py
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

凭据存仓库外私有runtime，不放此目录。样例为开发时点，非生产设备配置、独占配额或GPU清单。
