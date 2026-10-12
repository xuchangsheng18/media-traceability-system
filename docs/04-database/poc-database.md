# 最小工程数据库与业务字典边界

专用数据库media_trace_poc，schema为poc，版本迁移 [0001_poc.sql](../../backend/migrations/0001_poc.sql)。正式业务提案仍以initial-schema.sql、data-dictionary.md、field-provenance.json和api-field-mapping.csv为源；62表824字段并未部署成完整业务应用。

| 表 | 作用 | 关键约束 |
| --- | --- | --- |
| poc.assets | 固定测试案件资产；原件和分析副本的ObjectRef | asset UUID主键；(case_id,asset_id)唯一；正大小；版本引用/摘要由对象适配校验 |
| poc.jobs | 任务状态、结果、尝试次数和35秒租约 | job UUID主键；(case_id,idempotency_key)唯一；跨案件复合资产FK；4态CHECK |
| poc.outbox | 事务后待投递队列的数据库事实 | job唯一且FK；sent_at空表示待发送；SKIP LOCKED批次发送 |

创建任务与outbox在同一事务；发布确认后记sent_at。先发消息后提交可能重复，worker以数据库状态/租约约束处理；不是exactly-once保证。queue持久化与outbox故障恢复通过单worker检查。

PoC中租约过期可恢复，尝试最多3；失败有error_code。尚未实现旧租约fencing、多worker并发与正式取消，故不将PoC状态机直接作为全部正式任务实现。

应用角色poc_app无超级用户和BYPASSRLS，只授予poc的SELECT/INSERT/UPDATE；固定开发案件，不是多单位RLS产品。初始脚本使用IF NOT EXISTS便于首次配置重复运行，但字段变更必须新增迁移，不能修改旧文件后假定生产升级已完成。

首发cluster_id/asset_id/rank等原业务字段的“来源契约”已经指向可检验的SQL、OpenAPI与字段映射；它不是某个外部网站的通用默认定义。PoC没有替代首发业务表。另在全新临时无网络PostgreSQL中实际运行25常规＋48首发排序/证据案例，验证字典基础约束。
