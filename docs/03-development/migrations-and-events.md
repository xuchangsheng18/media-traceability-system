# 开发迁移、版本事件与任务写回手册

适用1.1-py310-cpu开发栈。迁移仅作用于media_trace_poc；正式62表升级应另建逐版本方案。管理员连接用于初始化/迁移，运行应用使用列级受限poc_app。

## 升级和失败处理

1. 保留当前源版本和仓库外开发备份，确认维护时段；执行初始化入口前停止本项目worker/API，防止旧worker继续写回。
2. 在锁定py310运行 `python scripts/poc_control.py up`。初始化调用run_migrations：校验专用数据库名，取得事务级advisory lock，创建账本并按文件名顺序执行未应用SQL；应用记录摘要。既有版本摘要变化或缺失立即失败，事务回滚。
3. 0002为新增字段/表及历史回填，不覆盖原件/结果。没有历史请求ID的任务写入trace_origin=migration_job_id；已有任务此前的执行历史无法补造。
4. 检查健康、迁移账本、集成及隔离竞态验证。故障先停止本项目入口，保留日志，修复新增迁移或向隔离克隆恢复；本轮没有down迁移或自动回退到旧worker的兼容承诺。

不要修改已执行0001/0002，也不要用initial-schema.sql对已有库重复初始化。开发旧库接管目前仅校验列名集合，发现未知来源旧库须先审查类型、默认值、FK和CHECK。初始化角色与凭据由私有runtime产生，禁止入Git或粘贴到报告。

## 事件唯一来源

[poc.analysis.requested.v1.schema.json](../../schemas/events/poc.analysis.requested.v1.schema.json)是唯一可编辑结构源；固定schema_version=1.0.0、event_type=poc.analysis.requested.v1。包含稳定event_id、UTC日期occurred_at、request_id、trace_origin、case_id、producer及payload.job_id/asset_id，拒绝额外字段和秘密值。task_id仍为job_id；执行run_version由领取后数据库生成，不从队列消息信任。

API同一事务保存任务、事件和创建审计。dispatcher以SKIP LOCKED领取outbox批次，发布持久消息并等待确认后标记；可能重复投递。worker验证Schema并原子领取，发送M15请求，验证响应Schema以及请求/任务/执行/模型/前处理/映射身份，再作条件写回。过期令牌、旧成功或旧失败均不得覆盖新执行结果；每次状态转移追加开发审计。

为消化1.0已经排队的UUID字符串消息，当前worker允许从DB查回该任务的权威outbox信封再验证；不是接受任意无版本业务事件。下一次移除旧协议前，应验证队列已排空、保留升级证据并补兼容测试。

## 追踪与测试边界

API创建请求ID随任务、outbox、worker、M15请求/响应和审计传播；查询本身的新HTTP请求ID与任务原始ID分别返回。API和内部推理共用安全Problem及日志处理；不打印输入正文、凭据或堆栈。历史回填不可表述为原始API追踪。

[migration-fencing-report.json](../00-project/validation/migration-fencing-report.json)15项包括升级/重复运行/改写拒绝、8个独立数据库竞争者仅一个领取、过期及旧租约拒绝、新执行成功、原件引用/审计/账本权限拒绝。使用新建隔离数据库并清理临时资源，不代表8个真实Celery进程、正式取消/DAG、RLS或管理员不可篡改审计已经验收。

机制参考[PostgreSQL16事务锁](https://www.postgresql.org/docs/16/explicit-locking.html)与[Celery任务重投递说明](https://docs.celeryq.dev/en/stable/userguide/tasks.html)；网站说明不代替本项目实际报告。
