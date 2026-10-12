# CPU研发PoC接口与正式契约关系

正式业务结构唯一源仍为openapi.yaml（53操作）；内部入口仍为inference-openapi.yaml；模型M15结构仍为schemas/model。PoC没有实现全部53操作，也没有改写正式上传会话/案件/审核API。

| 路径 | 当前行为 |
| --- | --- |
| GET /healthz | 进程存活、研发配置，不代表所有依赖正常 |
| GET /api/v1/health | Bearer鉴权、数据库SELECT1；status与request_id；对齐既有Health字段 |
| POST /poc/assets | PNG/JPEG的base64，201；原件保留、摘要/版本、独立RGB分析副本 |
| POST /poc/jobs | 202；UUID资产；必需Idempotency-Key；数据库事务写任务和outbox；冲突409 |
| GET /poc/jobs/{job_id} | 固定测试案件范围；404隐藏未知；返回状态、attempts、版本化结果/错误 |
| GET /poc/openapi.json | FastAPI生成的当前PoC实现描述，仅研发辅助，不作为正式业务源 |
| POST 内部 /internal/v1/inference/retrieval.image_embedding | 独立内部Bearer；实际M15 Schema；仅synthetic-cpu-encoder/demo-1；8维CPU向量 |

API错误返回application/problem+json：type/title/status/code/message/request_id/details；不回显输入值和堆栈。X-Request-ID与错误/健康响应对应。内部模型方法的错误仍由其研发FastAPI返回，正式内部Problem覆盖有待统一，不能声称全部正式错误契约已实现。

M15结构通用可接嵌入模型，当前名称明确为合成CPU模型，不冒充SSCD。结果有mock=false、模型/前处理/映射版本、对象version_id和摘要；findings为空，不出执法判断。请求字段包括case/task/run_version、deadline和authorization_version，但PoC授权版本是开发标签，不是正式策略。

对象上传是JSON base64开发入口，不支持生产分片上传/断点续传；任务无正式取消接口。健康业务接口已有测试，完整53操作与审批、导出、回流按原170任务继续实现。
