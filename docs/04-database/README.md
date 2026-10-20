# 数据库设计文档导航

本轮0.4-review候选。先读设计与字典，再核对SQL、接口映射和排序契约。

T015新增[数据范围迁移与事务说明](data-scope-migration.md)及[0010迁移](../../backend/business_migrations/0010_data_scope.sql)：三种模式、64表分类、7个固定函数、受限元数据和原ACL边界。当前P02代码已形成，完整业务验证运行中，见[实际进度](../00-project/validation/t015-data-scope-progress.json)；0009后的64表849字段保持不变，不代表共享库已安装或所有表CRUD已验收。

新增[T011/T012身份、单位与案件关系](identity-relations.md)、[机器扩展字典](identity-relations-catalog.json)及[0004迁移](../../backend/business_migrations/0004_identity_relations.sql)。原初始化基线62表825字段保留；应用0001—0004后的实际库为63表840字段，适用版本须区分。

本批[T012角色/权限目录及绑定](role-catalog-extension.md)、[逐字段扩展字典](role-catalog-extension.json)、[0005迁移](../../backend/business_migrations/0005_role_catalog.sql)和[实际实施/验收](../03-development/t012-role-model-implementation.md)补齐目录软禁用、终态撤销、受限管理及恢复。0005后实际63表843字段；独立空开发库和368项回归见[专属报告](../00-project/validation/t012-role-model-report.json)。内部模型没有自动接入认证或正式授权。

本批[T014权限事实查询](../03-development/t014-unified-permission-implementation.md)及[0006迁移](../../backend/business_migrations/0006_permission_lookup.sql)新增专用只读角色和固定查询函数，不增加业务表或字段，仍为63表843字段。函数返回当前身份、角色和权限绑定事实；明确策略端口另作决定，缺正式策略拒绝。最小权限、0005升级、账本与独立恢复见[权限专项报告](../00-project/validation/t014-permissions-report.json)，共享数据库尚未应用0006。

- [api-field-mapping.csv](api-field-mapping.csv)
- [api-field-mapping.json](api-field-mapping.json)
- [api-field-mapping.md](api-field-mapping.md)
- [data-dictionary.md](data-dictionary.md)
- [database-design-references.md](database-design-references.md)
- [database-design.md](database-design.md)
- [database-revision-audit.md](database-revision-audit.md)
- [database-validation.md](database-validation.md)
- [er-diagram.md](er-diagram.md)
- [field-provenance.json](field-provenance.json)
- [first-source-ranking.md](first-source-ranking.md)
- [initial-schema.sql](initial-schema.sql)
- [table-catalog.json](table-catalog.json)

## 本轮最小工程与字典区别

[开发五表说明](poc-database.md)描述实际独立开发库与迁移，不覆盖62表825字段业务字典。首发排序/证据规则仍按现有业务来源与SQL校验，在新临时数据库实测；不能把数据库约束通过当全部业务已上线。

## 第一阶段第13/19步

[62表任务引用](table-task-usage.md)及[逐关系来源](table-task-usage.json)补齐初始化基线的候选职责/追踪关系，明确未批准负责人和未证明代码使用。旧61表版本保存于第一阶段历史资料；62表基线SQL与字典保持同源，0004身份扩展另以上文补充字典和版本迁移为来源。

[案件单位隔离原型](authorization-isolation-prototype.md)提供新隔离PostgreSQL16的RLS/撤销/追加历史验证，区别于62表业务源与现有5表迁移。
