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
