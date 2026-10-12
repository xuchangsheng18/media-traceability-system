# 开发数据库、迁移与字段定义

2026-10-12，1.1-py310-cpu。专用数据库media_trace_poc、schema poc。正式业务62表824字段仍以initial-schema.sql、data-dictionary.md、field-provenance.json和api-field-mapping.csv为定义来源；当前开发5表不等于62表已实现。

| 表 | 职责 | 约束和权限 |
| --- | --- | --- |
| poc.assets | 固定测试案件的资产和原件/分析副本ObjectRef | UUID主键、案件复合唯一键；应用可插入/读取，不能修改原件引用或删除 |
| poc.jobs | 状态、结果、尝试次数、追踪与租约 | 案件/资产复合FK、案件/幂等键唯一、4态CHECK、最多3次尝试；仅状态/结果/租约等指定列可更新 |
| poc.outbox | 与任务事务一致的待发送事件 | job唯一FK、event_id唯一、JSON身份CHECK；应用仅可更新sent_at，事件不可普通覆盖 |
| poc.job_events | 任务状态变更的追加记录 | UUID主键、任务FK、类型枚举和正run_version；应用仅SELECT/INSERT，不能UPDATE/DELETE |
| poc.schema_migrations | 已执行迁移、源文件SHA-256及时间 | 仅迁移管理连接维护；应用没有读取/改写授权 |

## 新增字段的精确定义

| 字段 | 类型/约束 | 语义与来源 |
| --- | --- | --- |
| jobs.request_id | uuid NOT NULL | 创建任务的API请求ID；历史任务只能回填job_id，不能伪造丢失的原始ID |
| jobs.trace_origin | text NOT NULL，api或migration_job_id | 标识真实API来源或历史回填；由0002迁移和创建事务定义 |
| jobs.lease_token | uuid，可空 | 每次领取生成的新租约标识；终态或回队列清空，用于拒绝旧执行者写回 |
| jobs.run_version | integer NOT NULL CHECK(>0) | 每次成功领取的执行版本，从1开始；与模型请求/响应对应，不是任务ID或模型版本 |
| outbox.event_id | uuid NOT NULL UNIQUE | 一条逻辑事件的稳定ID；重复投递保持相同ID，不等同某次发送ID |
| outbox.event_payload | jsonb NOT NULL | 完整版本化信封；唯一结构源为schemas/events/poc.analysis.requested.v1.schema.json |
| job_events.request_id/run_version | uuid/正integer NOT NULL | 与对应任务执行相关联；历史回填身份通过jobs.trace_origin解释 |
| schema_migrations.sha256 | text NOT NULL，64位小写十六进制 | 对已执行SQL原始字节计算摘要，改写已执行文件将被拒绝 |

SQL列的完整定义见[0001](../../backend/migrations/0001_poc.sql)、[0002](../../backend/migrations/0002_event_leases_audit.sql)及[迁移实现](../../backend/app/migrations.py)。Schema验证补足JSON结构；数据库CHECK没有代替完整Schema或业务授权。

创建任务、outbox与job.created在同一事务；消息确认后更新sent_at。重复发送仍可能发生，系统保证条件领取和当前租约写回，不承诺exactly-once。租约35秒、最多3次，实际领取同时核对case/asset/request；写回同时核对状态、案件、lease_token、run_version及尚未过期。取消、DAG、长期任务续租与生产多单位策略仍未实现。

迁移采用版本账本、事务锁和摘要核验，不修改0001。旧3表升级检查列名集合后接管账本，该检查不等于完整比对旧库类型/约束。运行与失败处理见[迁移和事件手册](../03-development/migrations-and-events.md)。应用角色NOSUPERUSER/NOBYPASSRLS；当前固定测试案件，无正式RLS。追加审计仅限制普通应用权限，管理员仍可修改，不是WORM。

## “来源契约”的含义

data dictionary即数据字典：解释字段名称、类型、是否必填、约束、外键、业务含义和来源。“见来源契约”必须指到仓库中明确的SQL/Schema/OpenAPI字段和业务规则，不能作为没有定义的占位文字。原业务cluster_id是内容簇标识，asset_id是资产标识，rank是首发候选序位（1—3）；关联范围、唯一性、排序规则和接口位置由正式字典及其逐字段来源确定，不能从uuid/integer类型本身推断。参见[data-dictionary.md](data-dictionary.md)、[field-provenance.json](field-provenance.json)、[api-field-mapping.csv](api-field-mapping.csv)与[首发候选规则](first-source-ranking.md)。

正式SQL在全新隔离PostgreSQL16中验证25常规断言及48首发/证据案例，未向生产库初始化。开发迁移、8个并发数据库竞争者与旧租约拒绝另有15项实际验证；不是8个Celery进程的完整传输/故障验收。
