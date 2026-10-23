# 后端与任务进程

2026-10-13文档状态更新；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

app/main.py提供PoC API、请求ID、安全Problem与鉴权；settings.py验证配置；db.py管理SQL连接；worker.py承担outbox、消息执行和租约恢复；migrations/0001和0002仅用于独立开发库，由摘要账本管理。

## 验证入口

Linux仓库根目录运行，前置为已锁py311、Node及独立开发栈（适用时）：

```sh
PYTHONPATH=backend /opt/conda/glwy/envs/py311/bin/python -m pytest tests/poc -q
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

正式53操作、统一身份/RLS、正式多worker传输/故障演练、审核/导出/回流仍按源任务实现；PoC不是完整业务后端。

现有1.1工程包含app/migrations.py账本/摘要、app/contracts.py事件与M15验证、app/leases.py条件领取/写回、app/observability.py统一追踪/Problem、0002增量迁移；开发现有5表含审计/账本，见[数据库定义](../docs/04-database/poc-database.md)。

## 首批真实业务基础更新

[首批实现、运行与限制](../docs/03-development/stage-three/business-foundation-implementation.md)：独立迁移/RLS、5上传及7历史读取已有真实数据库/HTTP/消息/恢复验证；原PoC保留。新快照0.2及旧0.1识别分开，不宣称完整业务或正式环境已验收。
