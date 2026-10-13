# 工程与验证工具

2026-10-12；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

poc_control.py控制独立开发栈；run_ci.py串行质量门禁；verify_poc、resilience、media_and_queries、sql_baseline提供真实检查；verify_runtime_lock、generated_contracts、ci_failure_gate、check_repository_secrets及collect_environment记录证据。原资料/字典/导航脚本仍保留。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/run_ci.py all
/opt/conda/glwy/envs/py310/bin/python scripts/verify_ci_failure_gate.py
/opt/conda/glwy/envs/py310/bin/python scripts/check_repository_secrets.py
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

完整CI会启动开发栈，恢复检查短暂停止/重启本项目服务；SQL创建新临时无网络容器并清理。资料校验不证明业务实现；主动失败探针FAIL为预期并另有PASS判定。

## 1.1工程补充

1.1新增verify_migrations_and_fencing.py（15隔离项）、verify_media_timestamps.py（非零源PTS）、verify_development_recovery.py（8冷恢复项，维护时段暂停本项目服务）；run_ci.py完整21门禁。

## 本轮补充（2026-10-13）

plan_project_schedule.py重建170任务JSON/CSV/阅读页；evaluate_acceptance_metrics.py运行8组参考公式；validate_stage_one_completion.py执行5项图表证据/语义/指标/容量/零证据契约检查，均不代替真实业务验收。
