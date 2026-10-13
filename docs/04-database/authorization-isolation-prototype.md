# 案件、单位隔离与结果追加验证

2026-10-13。唯一实验SQL为[authorization-prototype.sql](../../tests/sql/authorization-prototype.sql)，执行器为[verify_stage_two_isolation.py](../../scripts/verify_stage_two_isolation.py)。仅在新建PostgreSQL16临时容器内生成授权/结果两张实验表；不覆盖62表初始化源，不作为现有5表的升级迁移。

角色无超级用户或BYPASSRLS；结果表ENABLE与FORCE RLS；读和追加分别校验主体、单位、案件、未撤销授权和写权限。task/run/result组合保持唯一。应用无UPDATE/DELETE结果权限和改ACL权限；结果更正追加版本。

可信中间件应先验证身份、功能权限、目的和授权版本，再在每个数据库事务内设置LOCAL主体/单位/案件值。客户端字段不能成为可信上下文。连接复用后LOCAL值清除，缺少上下文默认不可读。READ COMMITTED下已撤销ACL在下一条语句重新检查；不能推导已有下载字节可以追回或长事务在其他隔离级别同样立即撤销。

该模式依赖可信共享数据库登录。持有该登录或执行任意SQL的人可以伪造自定义设置；它不替代身份提供方、不防御已被攻破的应用。管理员/BYPASSRLS仍可绕过策略；FORCE不表示特权不可篡改。真实身份协议、组织/案件权威授权来源、同步/撤销时限和功能矩阵尚未提供。

正式62表接入时，先逐表分类全局/单位/案件/关联继承范围，复合外键阻止跨案件关联；避免以可见数量差异暴露对象。权限策略由权威ACL决定，不从客户端authorization_status或本地草案授予权限。运行任务在领取、读对象、结果提交、导出每次下载和训练回流前再次核验；撤销失败/未知默认拒绝。专用迁移需要先在空库与升级副本分别验证，并保留摘要账本、恢复和前向修复方案。

实际结果见[21项隔离和中文查询报告](../00-project/validation/stage-two-isolation-report.json)，其中14项为隔离/历史权限，7项为中文检索。依据[PostgreSQL16 RLS官方说明](https://www.postgresql.org/docs/16/ddl-rowsecurity.html)及[事务配置函数](https://www.postgresql.org/docs/16/functions-admin.html)。正式身份联调和62表部署均未由本实验完成。
