# 测试与判定

2026-10-13文档状态更新；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

tests/poc有15项后端；tests/sql含25常规断言和48首发排序/证据案例；资料夹具覆盖输入/Schema。前端2项及浏览器1项在frontend目录。集成21项、故障恢复5项、媒体/查询6项由scripts执行。

## 验证入口

Linux仓库根目录运行，前置为已锁py311、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py311/bin/python scripts/run_ci.py all
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

数量、scope和结果以docs/00-project/validation为准。无GPU、真实业务模型、20/100并发或生产审批结论；Mock/资料检查不能代替实测。

1.1后端15单元，包括7事件Schema测试及额外字段拒绝；迁移/竞态、源PTS与冷备测试由scripts进入完整21门禁。真实8Celery/VFR/生产灾备不计为通过。


[第二阶段代表性验证](../docs/09-testing/stage-two-representative-validation.md)记录21项隔离/中文查询、11项VFR媒体和6组运维交付控制；托管25道工程门禁的实际结果见[GitHub报告](../docs/00-project/validation/github-actions-report.json)。这些结果未覆盖真实业务模型、正式身份或完整62表实现。

## 首批真实业务基础更新

[首批实现、运行与限制](../docs/03-development/stage-three/business-foundation-implementation.md)：独立迁移/RLS、5上传及7历史读取已有真实数据库/HTTP/消息/恢复验证；原PoC保留。新快照0.2及旧0.1识别分开，不宣称完整业务或正式环境已验收。
