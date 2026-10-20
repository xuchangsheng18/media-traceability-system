# T015范围隔离的升级、恢复和目录判据

迁移`0010_data_scope.sql`沿用已批准的[数据范围设计](../03-development/t015-data-scope-design.md)，0001—0009原字节保留。实际升级工具仍是校验摘要的原子runner，不向已有共享数据库执行初始化或本轮迁移。

`tests/business/test_t015_scope_recovery.py`覆盖template0新库、0009升级、中途异常整体回滚、重复执行、旧/新摘要改变拒绝、真实pg_dump/pg_restore、恢复后案件RLS和旧代际拒绝、线程/异步上下文及旧客户端缺范围拒绝。测试只在随机命名隔离目标执行，不证明T013真实身份恢复或共享回切。

64表的分类目录与真实DAO/HTTP/字节操作分列。CASE／ORG／MIXED业务表保留FORCE RLS；DIRECTORY目录表保留原有owner与专用角色边界、运行角色RLS和新增restrictive策略，不能错误断言其原本全部FORCE。`user_identities`和`authorization_epoch`没有普通runtime表直读权限。修正新测试草稿中“所有目录表都FORCE”的错误预期，不修改旧SQL、不扩大运行角色权限；实际恢复测试还保留移除restrictive策略后能检出泄漏的负控制。

`scripts/verify_t015_scope.py`将S01—S09的实际JUnit节点、64表实际目录、SQL/HTTP/对象/恢复四类运行证据、精确源码和真实失败探针绑定；解析器样例不是业务运行证明。计数必须为整数，布尔值不冒充0/1；Python优化模式也不能移除门禁验证。原32条工程门禁保留，新增第33条的执行结果以实际回执为准。

新业务开发启动工具只在**另建空的研发库**应用这组版本，默认没有业务身份和正式权限。它不代表共享0010迁移已采用，更不能将新库无业务数据误当原有数据迁移/恢复通过。
