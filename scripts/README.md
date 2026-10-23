# 工程与验证工具

2026-10-13文档状态更新；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

poc_control.py控制独立开发栈；run_ci.py串行质量门禁；verify_poc、resilience、media_and_queries、sql_baseline提供真实检查；verify_runtime_lock、generated_contracts、ci_failure_gate、check_repository_secrets及collect_environment记录证据。原资料/字典/导航脚本仍保留。

## 验证入口

Linux仓库根目录运行，前置为已锁py311、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py311/bin/python scripts/run_ci.py all
/opt/conda/glwy/envs/py311/bin/python scripts/verify_ci_failure_gate.py
/opt/conda/glwy/envs/py311/bin/python scripts/check_repository_secrets.py
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

完整CI会启动开发栈，恢复检查短暂停止/重启本项目服务；SQL创建新临时无网络容器并清理。资料校验不证明业务实现；主动失败探针FAIL为预期并另有PASS判定。

现有1.1工程包含verify_migrations_and_fencing.py（15隔离项）、verify_media_timestamps.py（非零源PTS）、verify_development_recovery.py（8冷恢复项，维护时段暂停本项目服务）；run_ci.py本批扩展为32道工程门禁配置，实际运行见平台报告（21道为原1.1历史范围）。

plan_project_schedule.py重建170任务JSON/CSV/阅读页；evaluate_acceptance_metrics.py运行8组参考公式；validate_stage_one_completion.py执行5项图表证据/语义/指标/容量/零证据契约检查，均不代替真实业务验收。

stage_one_controls.py生成实际输入预检查，或对显式提供的授权元信息清单只输出聚合计数；validate_stage_one_controls.py执行正反边界；generate_workflow_types.py生成第四份类型。

generate_requirements_document.py把既有来源集中展示到原functional-requirements.md，覆盖36业务条目、170任务展开及非功能/规则/验收；--check核验同源内容和覆盖，不能作为业务已实现证明。更新完整导航会同时重建该需求阅读视图。


现有验证还包括verify_stage_two_isolation.py的21项隔离/中文查询、verify_stage_two_media.py的11项VFR媒体及validate_stage_two_completion.py的6组交付控制；软件采集记录实际镜像OS物料。实际命令、结论和边界见[23步状态](../docs/03-development/stage-two-readiness.md)及[代表性验证](../docs/09-testing/stage-two-representative-validation.md)。

第三阶段统一入口为dev.py/dev.ps1；stage_three_quality负责独立工具层及扫描，verify_stage_three_demo执行三进程和浏览器夹具，validate_stage_three区分资料检查与实际运行，generate_stage_three_docs生成既有阶段状态/验证视图。所有命令和范围见[第三阶段导航](../docs/03-development/stage-three/readiness.md)。
