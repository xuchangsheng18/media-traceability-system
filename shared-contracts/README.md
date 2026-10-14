# 生成类型与契约共享

2026-10-13文档状态更新；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

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

现有类型包含generated/poc-event.d.ts；唯一源schemas/events/poc.analysis.requested.v1.schema.json，由临时包装生成；连同workflow.d.ts共4份类型。详见[契约生成](../docs/03-development/contract-generation.md)。

第四份generated/workflow.d.ts从workflow/event/controls及34模型响应单一源生成，运行scripts/generate_workflow_types.py；漂移校验增加第四份，Schema与运行语义仍须验证。

## 首批真实业务基础更新

[首批实现、运行与限制](../docs/03-development/stage-three/business-foundation-implementation.md)：独立迁移/RLS、5上传及7历史读取已有真实数据库/HTTP/消息/恢复验证；原PoC保留。新快照0.2及旧0.1识别分开，不宣称完整业务或正式环境已验收。
