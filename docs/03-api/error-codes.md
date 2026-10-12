# 错误码与恢复

| 代码 | HTTP | 原因 |
| --- | --- | --- |
| AUTH_FORBIDDEN | 403 | 功能/案件/对象或用途无有效授权 |
| VALIDATION_FAILED | 422 | 字段或跨字段语义不合法 |
| UPLOAD_HASH_MISMATCH | 422 | 分片/完整摘要与声明不符 |
| MEDIA_UNSUPPORTED | 422 | 媒体实际格式/编码未支持 |
| MEDIA_SECURITY_REJECTED | 422 | 安全探测/查毒拒绝或隔离 |
| TASK_STATE_CONFLICT | 409 | 状态不允许当前操作 |
| IDEMPOTENCY_CONFLICT | 409 | 同键不同请求摘要 |
| VERSION_PRECONDITION_FAILED | 412 | If-Match对应版本已失效 |
| PRECONDITION_REQUIRED | 428 | 缺少必须的If-Match |
| MODEL_UNAVAILABLE | 503 | 模型后端/资源当前不可用 |
| MODEL_OUTPUT_INVALID | 422 | 模型输出结构或语义不合契约 |
| INDEX_VERSION_MISMATCH | 409 | 索引模型维度/版本不兼容 |
| EVIDENCE_INTEGRITY_FAILED | 409 | 证据版本或摘要对账失败 |
| LLM_EVIDENCE_VIOLATION | 422 | 事实句无有效引用或语义支持 |
| APPROVAL_POLICY_UNAVAILABLE | 409 | 正式策略缺失/失效，不放行正式动作 |
| APPROVAL_INVALIDATED | 409 | 批准目的/对象版本/状态不匹配 |
| LICENSE_UNVERIFIED | 409 | 发布许可用途未核准 |
| SERVICE_UNAVAILABLE | 503 | 安全或依赖服务不可用 |
| RATE_LIMITED | 429 | 流量或任务背压上限 |

401表示身份无效；对象不存在或按统一隐藏策略不可见返回404。错误正文只含脱敏字段；请求失败仍记录审计。重试503/429遵循服务端Retry-After和有界退避；409/412须先刷新状态和版本，不能盲重试。成功与失败均不能仅看队列状态代替业务事实。
