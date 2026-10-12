# 测试与判定

2026-10-12；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

tests/poc有7项后端；tests/sql含25常规断言和48首发排序/证据案例；资料夹具覆盖输入/Schema。前端2项及浏览器1项在frontend目录。集成15项、故障恢复5项、媒体/查询6项由scripts执行。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/run_ci.py all
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

数量、scope和结果以docs/00-project/validation为准。无GPU、真实业务模型、20/100并发或生产审批结论；Mock/资料检查不能代替实测。
