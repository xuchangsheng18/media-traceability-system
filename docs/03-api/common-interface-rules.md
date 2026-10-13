# 共用接口规则与联调要求

沿用[业务结构源](openapi.yaml)、[接口设计](api-design.md)和[错误码](error-codes.md)。源中未声明的参数、响应头或可调用路径不能从文字推导新增；正式配置数值仍须确认。

| 项目 | 规则 | 核验与未决边界 |
| --- | --- | --- |
| 地址/标识 | /api/v1相对基础路径；operationId唯一 | /poc不是正式业务别名，正式网关/域名与网络准入待定 |
| 身份 | security继承或操作覆盖；devLogin明确security=[]且仅开发 | bearerAuth没有指定必须JWT；正式身份/令牌撤销IF-G07 |
| 授权范围 | 功能权限＋组织/案件/对象/用途，逐请求检查当前授权 | 模型/配置为组织级；审批按对象类型；管理员不自动访问案件 |
| 追踪 | 源X-Request-Id为可选UUID，未提供由服务端生成，贯穿任务/消息/结果/Problem | 请求头/正文身份一致须校验；request_id不是授权或业务对象ID |
| 必填/可空 | required决定必须出现，anyOf含null决定允许null | 必填可空不能省略；枚举大小写/UUID/时间/摘要格式按源 |
| 幂等 | 对声明Idempotency-Key的操作绑定主体＋操作＋摘要；同键同摘要原效果，不同摘要409 | 保存期、并发/取消/重算精确边界IF-G12；超时先查询 |
| 条件并发 | 声明If-Match则强ETag与原子条件更新；缺失428、旧版本412、状态不允许409 | 聚合ETag精确目标IF-G12，body expected_version不能替代条件更新 |
| 分页 | 只用已定义limit/cursor，opaque游标与稳定排序/有效授权绑定 | 未定义case_id/排序参数不自动成为接口能力；拒绝任意SQL |
| 异步 | 202受理；对应查询决定实际成功/失败与结果版本 | ActionAck不自动提供轮询；上传/发布/审计导出缺口IF-G01/05/06 |
| 错误 | application/problem+json；HTTP与type/title/status及项目code/message/request_id/details | 401身份、403权限、404按统一隐藏、422字段/语义；不回堆栈或秘密 |
| 重试/背压 | 429/503按实际Retry-After和有界退避；409/412先刷新状态/版本 | 没有源声明的响应头不保证必有；重试仍需有效授权与幂等 |
| Range下载 | 固定ObjectRef版本/摘要；200/206/416与If-Range按源 | 每个Range重验撤销/权限；no-store；已有token/URL不永久放行 |
| 时间/空间 | 时区ISO8601；媒体半开毫秒区间；归一化bbox；版本显式 | 起止/素材边界、对象域、维度/证据存在性须业务校验 |
| 版本 | API路径、info.version、对象row/run/result/review版本含义各异 | 契约版本不是Python版本，事件版本不是运行版本；破坏性变更需兼容/迁移评审 |
| 秘密与样例 | 结构样例是合成夹具；消息不放令牌/原件/任意URL | 文档不授予真实数据用途或网络准入 |

详细操作以源parameters/responses为准；通用错误列表不能证明每个服务已实现每个分支，具体错误条件和测试逐任务登记。现有PoC鉴权、幂等、Problem和结果核验实测不能外推为53接口验收。

格式依据：[OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html)、[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)、[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)。code/message/request_id/details是项目扩展，不能表述为RFC规定的所有业务服务必填字段。

## 第一阶段工程控制补充（2026-10-13）

[精确历史读取](historical-result-reading.md)为7个操作增加扁平history对象，版本字段成组必填、未命中不回退最新，响应绑定头按选择器核对。
