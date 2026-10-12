# 契约生成与消息约定

正式业务API以docs/03-api/openapi.yaml为唯一编辑源；内部入口以inference-openapi.yaml为源；模型能力以schemas/model为源。shared-contracts/generated的TS文件只由openapi-typescript7.13.0生成，不作为可独立修改的第二份结构源。

```sh
cd frontend
npm ci
npm run generate:contracts
cd ..
/opt/conda/glwy/envs/py310/bin/python scripts/verify_generated_contracts.py
```

生成business-api.d.ts和inference-api.d.ts；门禁在临时目录重新生成逐字节比较，漂移失败。它们是类型声明，不是已实现全部业务的SDK，不提供运行时JSON验证；模型Schema仍由推理服务实际验证。

本轮Celery任务协议：poc.dispatch无参数；poc.analyze的args为单一job UUID字符串，task_id同job UUID，JSON序列化；任务的资产/案件从数据库读取，消息不含令牌、原件或任意URL。发布为持久消息且确认；数据库outbox是发送事实；重复投递由任务状态处理。本轮没有声称已建立跨模块完整业务事件总线或版本化事件信封。将来改变此开发协议须先处理已排队旧消息、新增版本/迁移并测试。
