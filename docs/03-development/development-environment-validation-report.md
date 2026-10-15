# 第三阶段开发环境实际验证报告

状态：PASS；资料一致性：PASS。正式冻结和完整业务验收均未断言。机器报告和具体来源摘要是执行依据，本文是阅读视图。

验证资料：[stage-three-validation-report.json](<../00-project/validation/stage-three-validation-report.json>)；实际命令/环境：[stage-three-runtime-report.json](<../00-project/validation/stage-three-runtime-report.json>)；实际托管源码/门禁及制品：[github-actions-report.json](<../00-project/validation/github-actions-report.json>)。

| 项 | 当前记录与严格含义 |
| --- | --- |
| setup_existing_locks_and_separate_tools | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py setup --tools`；current_locked_CPU_development_only |
| lint_and_TS | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py lint`；current_locked_CPU_development_only |
| new_code_format_and_text | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py format-check`；current_locked_CPU_development_only |
| unit_and_frontend_tests | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py test`；current_locked_CPU_development_only |
| unique_contract_SQL_and_generated_types | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py contract-test`；current_locked_CPU_development_only |
| secret_and_dependency_scans | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py security-scan`；current_locked_CPU_development_only |
| actual_precommit_all_files_no_hooks_installed | PASS；`/home/runner/work/_temp/media-trace-runtime/stage-three-quality-tools/bin/python -m pre_commit run --all-files`；current_locked_CPU_development_only |
| actual_three_process_and_browser_fixture | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/verify_stage_three_demo.py`；current_locked_CPU_development_only |
| existing_stack_read_only_status | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py status`；current_locked_CPU_development_only |
| clean_preview_only | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py clean --dry-run`；current_locked_CPU_development_only |
| full_CI_entry_plan_only_actual_run_evidence_separate | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/dev.py ci --dry-run`；current_locked_CPU_development_only |
| original_runtime_lock_after_tool_layer | PASS；`/opt/conda/glwy/envs/py310/bin/python3.10 scripts/verify_runtime_lock.py`；current_locked_CPU_development_only |
| compose_syntax_without_dumping_secrets | PASS；`docker compose config --quiet`；existing_named_development_stack_read_only |

入口前置条件：当前Linux服务器make未安装，使用实际已验证的Python等价入口；Windows PowerShell经SSH的help/status已核验，Windows原生环境未安装/验证。早期容量不足时构建保护已实测拒绝；最新容量已满足研发保护值，本批未重启共享栈。详见机器报告auxiliary_observations，不把未安装的可选工具记成PASS。


扫描原始输入/结果：[stage-three-secrets-report.json](<../00-project/validation/stage-three-secrets-report.json>)、[stage-three-python-dependency-report.json](<../00-project/validation/stage-three-python-dependency-report.json>)、[stage-three-npm-dependency-report.json](<../00-project/validation/stage-three-npm-dependency-report.json>)、[stage-three-quality-dependency-report.json](<../00-project/validation/stage-three-quality-dependency-report.json>)、[stage-three-dependency-scan-report.json](<../00-project/validation/stage-three-dependency-scan-report.json>)。原pip-audit跳过保持；新增基础审查已核对Torch官方wheel摘要及12,240安装载荷，OSV精确/基础版本查询均无返回条目，仍不代表所有二进制漏洞覆盖或准入。Python3.10维护、镜像OS、模型许可与数据DLP另核验。

三服务夹具新增实际结构日志关联与依赖停止验证：日志只包含固定事件/服务角色/方法/路由模板/状态/UUID/时长及模拟标识，不记录原始URL、请求体、头或令牌；同一request_id贯穿三服务。测试停止自建推理进程后核对ready=503、调用=502，且不回显输入。原始结果见stage-three-demo-report.json；只停止本验证创建的进程。

未执行/限制：共享Docker数据盘最近快照：13%使用、约644GiB可用；采样2026-10-15T17:16:10.094428+00:00；本轮未执行扩容停机或共享栈恢复，维护备份与正式恢复未验收；Windows原生安装、GPU/CUDA/真实模型、正式网络/业务数据、主分支保护正反验证及冻结未完成。三服务模拟夹具只证明健康/就绪、调用、trace、结构日志、故障和页面；真实模型/业务能力另验。模板、资料PASS、代表性模型/数据库结果都不代替这些工作。本批完善现有应用基础代码，原100包Python锁保持；共享部署未更新，完整工程复建由实际GitHub run认定。
