# 数据库设计文档导航

本轮0.4-review候选。先读设计与字典，再核对SQL、接口映射和排序契约。

新增[T011/T012身份、单位与案件关系](identity-relations.md)、[机器扩展字典](identity-relations-catalog.json)及[0004迁移](../../backend/business_migrations/0004_identity_relations.sql)。原初始化基线62表825字段保留；应用0001—0004后的实际库为63表840字段，适用版本须区分。

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

[62表任务引用](table-task-usage.md)及[逐关系来源](table-task-usage.json)补齐表的候选职责/追踪关系，明确未批准负责人和未证明代码使用。旧61表版本保存于第一阶段历史资料，当前SQL/字典仍保持唯一来源。

[案件单位隔离原型](authorization-isolation-prototype.md)提供新隔离PostgreSQL16的RLS/撤销/追加历史验证，区别于62表业务源与现有5表迁移。
