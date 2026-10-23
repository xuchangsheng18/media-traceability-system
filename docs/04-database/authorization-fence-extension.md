# 授权事务栅栏增量字典（0007—0009）

本页描述T014隔离研发迁移，不表示共享数据库已安装或正式权限已启用。原62表825字段字典、0004身份关系和0005目录补充保留各自版本含义；不能单独执行旧初始化SQL代表当前结构。0007只增加受限查询函数；0008增加1表6字段，应用0001—0008后为64表849字段；0009仅增加工作身份查询函数，表和字段数保持不变。实际测试进度以[逐项回执](../00-project/validation/t014-isolated-rule-progress.json)为准。

## 新表 `mt.authorization_epoch`

| 字段 | 类型及约束 | 精确含义 |
| --- | --- | --- |
| singleton | boolean，主键，默认true，CHECK(singleton) | 只允许true这一行；不是用户、单位或案件标识。 |
| epoch | bigint，NOT NULL，默认1，CHECK(epoch>0) | 当前数据库授权目录变化序号。不是令牌版本，也不能单独证明数据库恢复后仍有效。 |
| changed_at | timestamptz，NOT NULL，默认statement_timestamp() | 最近目录变更或明确激活时的数据库语句时间；不替代外部可信时间。 |
| policy_version | text，可空 | 经明确激活的候选策略版本；非空时长度1—1024。 |
| policy_sha256 | text，可空，非空时64位小写十六进制 | 精确规则输入摘要；不接受只凭文件名或版本号确认相同规则。 |
| recovery_generation | text，可空 | 独立确认的恢复代际，非空时长度1—1024；恢复旧数据库不能自动产生新值。 |

后三字段必须全部为空或全部非空。初始全部为空，表示未激活，业务栅栏拒绝相应动作。`PUBLIC`、`mt_runtime`、`mt_permission_lookup`、`mt_directory_manager`均无此表直接读写权限；没有正式用户、角色或ALLOW种子。

## 函数与事务要求

| 函数 | 执行者 | 行为及边界 |
| --- | --- | --- |
| lookup_role_facts（0007） | mt_permission_lookup | 精确issuer/subject/user/org查询全部活动角色，包含不提供当前权限的冲突角色；只返回事实。 |
| lookup_actor_role_facts（0007） | mt_runtime | 使用服务器事务绑定的actor/org读取上述事实；不能由调用者指定另一个用户。 |
| lookup_actor_work_role_facts（0009） | mt_runtime | 精确绑定活动identity_id、mapping_version和事务actor/org；不制造JWT，不单凭工作消息授予权限。 |
| hold_authorization_epoch（0008） | mt_runtime | 对代际行取得共享锁，返回epoch、数据库名/OID及策略/恢复代际；锁保留至事务结束。 |
| advance_authorization_epoch（0008） | mt_directory_manager及受控触发器 | 更新代际行，和业务共享锁排序；不授予业务表修改权限。 |
| activate_authorization_generation（0008） | mt_directory_manager | 校验策略版本、摘要、恢复代际及预期epoch，比较后递增；预期不符抛40001并回滚。 |
| bump_authorization_epoch（0008） | 受控触发器 | 供目录变更触发器使用，PUBLIC无执行权。 |

上述受限函数固定search_path；SQL源码为[0007](../../backend/business_migrations/0007_role_facts.sql)、[0008](../../backend/business_migrations/0008_authorization_fence.sql)、[0009](../../backend/business_migrations/0009_work_role_facts.sql)。旧迁移不被后续版本覆盖。目录触发器覆盖organizations、users、user_identities、roles、permissions、user_roles、role_permissions、case_membership、cases的INSERT/UPDATE/DELETE/TRUNCATE，按语句在变更前取得代际写锁；语句失败时序号变化随事务回滚。

0009只读取身份目录事实；upload_session.owner_id、analysis_task.created_by、audit_export.created_by与工作ID/单位/案件关系仍由业务运行账号在RLS下读取。工作委托期限和独立服务身份须有可信适配器另行核对，当前没有默认正式提供者。队列中的actor或权限集合不能代替这些检查，后台工作不存储用户Bearer。任务节点沿用41权限中的task.create或task.cancel，不增加task.execute种子，也不挂载新的业务HTTP操作。

应用侧必须在同一业务连接、同一根事务中按“代际共享锁 → 实时角色/对象/来源 → 业务写入 → 提交前复查”执行。不能用另一连接的检查代替本事务校验。初始精确对象版本校验及保留的行锁排除并发修改；本事务合法版本递增后，提交前仍复查当前条件和绑定，不要求对象版本仍等于写入前值。

## 恢复、失败和适用边界

独立代际证明还绑定数据库名、OID、最小epoch、精确策略摘要和有效期限。缺失、过期、回退、数据库错误或锁超时拒绝并回滚。显式恢复激活和独立证明必须另有可信来源，不能从恢复出来的同一份旧表自证有效。

外部代际提供者必须在受控恢复开始时停止确认旧代际，恢复后再独立确认新代际；本批未安装正式提供者。已测范围是同实例新隔离库恢复及显式代际变化。保持数据库名/OID且绕过恢复程序的原地回滚没有自动侦测证明，不能用本表或旧有效证明声明该场景已关闭；真实恢复/回切仍归T013后续验收。

本机制只在当前PostgreSQL实例内排序，不能使Keycloak、外部分类/人员事实与数据库成为一个原子事务。后台工作接入和最大5秒隔离测量属于P06；真实身份恢复、共享策略采用、全局锁吞吐与生产SLA另行验收。测试见[test_t014_revocation.py](../../tests/business/test_t014_revocation.py)和[test_migrations.py](../../tests/business/test_migrations.py)，并保留失败/回滚与真实隔离pg_dump/restore证据。
