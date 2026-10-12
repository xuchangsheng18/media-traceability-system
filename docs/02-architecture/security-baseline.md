# 研发安全基线与生产差距

本配置只处理自建素材与固定测试案件。API 和内部推理分别使用随机令牌；令牌、S3 凭据、数据库及队列密码存于仓库外 `/workspace/glwy/runtime/media-traceability-system`，目录 0700，凭据与 env 文件 0600。S3 JSON 仅在私有目录及专用命名卷内供服务读取。

所有发布端口绑定 127.0.0.1；远程页面通过 SSH 转发访问。内部 bridge 并非出站阻断，HTTP 只适用于本轮本地/隧道研发。Docker inspect 和管理权限能够读取容器环境，不能把 env 注入称为生产密钥管理平台。

API 默认为未认证请求返回 401；任务查询限制固定测试案件；数据库应用角色无超级用户和 BYPASSRLS，限定poc业务表SELECT/INSERT和指定状态/租约列UPDATE；无DELETE或账本权限。此 PoC 没有用户/单位范围决策、RLS 业务策略或正式证据审批。

输入限制：PNG/JPEG；原件最多 1 MiB；最大像素 400 万；前端上传不接受任意对象 URL；服务内部从固定桶和受控前缀读取 version_id 并核对 SHA-256。原件字节与分析副本分开。开发凭据的确切值由 [check_repository_secrets.py](../../scripts/check_repository_secrets.py) 检查是否进入源仓库；该检查不是全面 DLP 或完整秘密扫描。

原始请求ID随任务、事件、worker、推理与追加审计传播；查询自身HTTP请求ID另行返回，结构化日志仅记录路由模板、方法、状态和耗时，不记录正文、认证头、文件名或凭据。错误使用安全 Problem；配置错误统一 CONFIGURATION_INVALID，不打印字段值。

生产差距：统一身份与撤销、功能权限和案件/单位隔离、TLS、出口规则、审计不可篡改、密码轮换、对象 WORM/保留、访问撤销、生产灾备与密钥恢复、等保及软件准入均须单独实现和验收。Python 3.10 已结束支持，不能直接将该研发镜像批准为生产版本。

1.1新增普通角色审计UPDATE/DELETE拒绝及原件引用修改拒绝，15项隔离检查通过；开发审计不限制管理员，不能称为不可篡改证据。详见[迁移事件手册](../03-development/migrations-and-events.md)。
