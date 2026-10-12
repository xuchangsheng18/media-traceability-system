# 生成类型与契约共享

2026-10-12；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

generated/business-api.d.ts和inference-api.d.ts由openapi-typescript7.13.0生成；外部业务与内部入口分别有唯一来源，模型Schema继续独立管理。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
npm --prefix frontend run generate:contracts
/opt/conda/glwy/envs/py310/bin/python scripts/verify_generated_contracts.py
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

生成的是TS类型声明，不是完整SDK或运行时校验；不能手改生成文件。跨模块正式事件总线仍待实现。

## 1.1工程补充

1.1增加generated/poc-event.d.ts；唯一源schemas/events/poc.analysis.requested.v1.schema.json，由临时包装生成，共3份类型。详见[契约生成](../docs/03-development/contract-generation.md)。
