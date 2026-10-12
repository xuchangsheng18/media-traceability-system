# 后端与任务进程

2026-10-12；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

app/main.py提供PoC API、请求ID、安全Problem与鉴权；settings.py验证配置；db.py管理SQL连接；worker.py承担outbox、消息执行和租约恢复；migrations/0001_poc.sql仅用于独立开发库。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
PYTHONPATH=backend /opt/conda/glwy/envs/py310/bin/python -m pytest tests/poc -q
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

正式53操作、统一身份/RLS、多worker fencing、审核/导出/回流仍按源任务实现；PoC不是完整业务后端。
