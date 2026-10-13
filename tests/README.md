# 测试与判定

2026-10-12；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

tests/poc有15项后端；tests/sql含25常规断言和48首发排序/证据案例；资料夹具覆盖输入/Schema。前端2项及浏览器1项在frontend目录。集成21项、故障恢复5项、媒体/查询6项由scripts执行。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/run_ci.py all
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

数量、scope和结果以docs/00-project/validation为准。无GPU、真实业务模型、20/100并发或生产审批结论；Mock/资料检查不能代替实测。

## 1.1工程补充

1.1后端15单元，包括7事件Schema测试及额外字段拒绝；迁移/竞态、源PTS与冷备测试由scripts进入完整21门禁。真实8Celery/VFR/生产灾备不计为通过。

## 第二阶段2026-10-13补充

[12类补齐与剩余条件](../docs/03-development/stage-two-completion-matrix.md)、[实施计划](../docs/03-development/stage-two-implementation-plan.md)和[实际外部输入](../docs/03-development/stage-two-external-inputs.json)已纳入阶段导航。新增隔离权限/中文查询21项、VFR媒体11项、运维/离线摘要6组检查以及镜像OS物料采集；CI工程门禁扩为25道。实际PASS以本轮服务器和托管报告为准，正式身份/业务模型/资源及生产冻结仍未完成。
