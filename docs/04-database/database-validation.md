# 数据库候选验证说明

校验器首先执行SQL语法解析；真实DDL与行为验证仅在临时PostgreSQL16容器的内存数据卷中进行，网络隔离、无主机端口、无业务卷。测试数据为合成UUID与文本。

验证包括新库初始化、主键/唯一/范围约束、跨案件外键、默认无上下文不可见、有效成员可见、授权撤销后不可见、证据及审计更新删除截断拒绝、原件修改拒绝、已消费token重用拒绝、固化批准的目的与版本检查。

运行记录与SQL摘要在docs/00-project/validation/sql-validation-report.json。它不证明应用接口、统一身份、真实对象锁、公安网络、合法审批流程或备份恢复已经通过。

重跑时使用新建空隔离数据库；由有权人员调用psql -v ON_ERROR_STOP=1 -f docs/04-database/initial-schema.sql，再执行tests/sql/integrity-tests.sql。现有业务库禁止直接初始化。

## 本轮基础修订验证

在仓库根目录运行`python scripts/validate_database_foundation.py --ssh-host 172.16.58.179`。脚本只使用已有PostgreSQL镜像，在无网络、无端口、无主机业务卷的临时容器执行修订DDL、原25项测试和当前48项首发排序与证据测试，最后清理容器。检查结果见[数据库报告](../00-project/validation/database-foundation-report.json)。

`python scripts/validate_database_contracts.py`检查825个字段的定义/SQL/注释一致性及首发响应语义；见[契约报告](../00-project/validation/database-contract-report.json)。这是基础约束验证，不是生产迁移、并发压力或模型效果验收。历史sql-validation-report只适用于其中记录的旧SQL摘要。
