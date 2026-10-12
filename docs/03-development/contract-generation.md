# 契约生成与消息约定

正式业务API以docs/03-api/openapi.yaml为唯一编辑源；内部入口以inference-openapi.yaml为源；模型能力以schemas/model为源；本轮开发事件以schemas/events/poc.analysis.requested.v1.schema.json为源。generated文件不能独立修改形成第二份结构定义。

```sh
cd frontend
npm ci
npm run generate:contracts
cd ..
/opt/conda/glwy/envs/py310/bin/python scripts/verify_generated_contracts.py
```

生成business-api.d.ts、inference-api.d.ts、poc-event.d.ts共3份。openapi-typescript7.13.0负责生成；generate-event-types.mjs只将权威JSON Schema装入临时OpenAPI3.1容器，临时文件不是另一份维护源。门禁分别临时再生成并逐字节比较；TS类型不提供运行时JSON验证，也不代表已实现全部53个正式接口。

Celery poc.dispatch无参数；poc.analyze携带完整版本信封，JSON序列化，task_id=job_id，argsrepr隐藏正文。信封保持event_id和任务原始request_id，不含令牌、原件或任意URL；发布持久化并确认。实际worker和API校验Schema，推理结果按M15 Schema与身份再核验。旧UUID消息仅作查回DB信封的迁移桥接。详细语义见[迁移与事件手册](migrations-and-events.md)。本轮只建立PoC事件，不宣称跨12模块事件总线已完成。
