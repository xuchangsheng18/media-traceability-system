# 契约生成与消息约定

正式业务API以docs/03-api/openapi.yaml为唯一编辑源；内部入口以inference-openapi.yaml为源；模型能力以schemas/model为源；本轮开发事件以schemas/events/poc.analysis.requested.v1.schema.json为源。generated文件不能独立修改形成第二份结构定义。

```sh
cd frontend
npm ci
npm run generate:contracts
cd ..
/opt/conda/glwy/envs/py310/bin/python scripts/verify_generated_contracts.py
```

当前生成business-api.d.ts、inference-api.d.ts、poc-event.d.ts、workflow.d.ts共4份。openapi-typescript7.13.0负责生成；generate-event-types.mjs与generate_workflow_types.py将权威JSON Schema装入临时OpenAPI3.1容器，临时文件不是另一份维护源。门禁分别临时再生成并逐字节比较；TS类型不提供运行时JSON验证，也不代表已实现全部55个正式接口。

Celery poc.dispatch无参数；poc.analyze携带完整版本信封，JSON序列化，task_id=job_id，argsrepr隐藏正文。信封保持event_id和任务原始request_id，不含令牌、原件或任意URL；发布持久化并确认。实际worker和API校验Schema，推理结果按M15 Schema与身份再核验。旧UUID消息仅作查回DB信封的迁移桥接。详细语义见[迁移与事件手册](migrations-and-events.md)。本轮只建立PoC事件，不宣称跨12模块事件总线已完成。

## 整体接口明细与来源一致性

第二阶段整体入口为[system-interface-specification.md](../03-api/system-interface-specification.md)，详细文件由业务OpenAPI、任务/追踪、字段来源及34模型Schema生成。接口解释仅维护在interface-annotations.json，字段/路径仍维护唯一OpenAPI。

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/generate_interface_docs.py
/opt/conda/glwy/envs/py310/bin/python scripts/generate_interface_docs.py --check
/opt/conda/glwy/envs/py310/bin/python scripts/validate_interface_docs.py
```

新增6项材料检查，包括展开权威共享引用后对齐68个模型请求/响应分支，不能将内联副本与URN引用的字面差异当漂移。该检查发现M24内部OpenAPI漏maxItems=3与两个证据列表uniqueItems=true，已按模型源同步。55业务操作/85结构/34能力的详细文档不等于全部运行，13项缺口仍开放。

事件类型生成入口改为直接用当前Node调用锁定openapi-typescript的JS CLI，使Windows与Linux均可执行；临时目录删除前核验范围。当前4份类型均临时重新生成并检查，约束如uniqueItems/maxItems仍由运行时Schema检查，不由TypeScript类型替代。

## 第一阶段工程控制补充（2026-10-13）

第四份workflow.d.ts由generate_workflow_types.py在临时目录包装本地Schema生成；业务/内部/Poc事件三份保留。verify_generated_contracts.py检查4份字节一致性。

2026-10-13当前派生类型共4份，新增workflow.d.ts从工作流/控制和模型来源包装生成；详见scripts/generate_workflow_types.py，不另建手写结构源。
