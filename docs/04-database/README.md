# 数据库设计文档导航

本轮0.4-review候选。先读设计与字典，再核对SQL、接口映射和排序契约。

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

[PoC三表说明](poc-database.md)描述实际独立开发库与迁移，不覆盖62表824字段业务字典。首发排序/证据规则仍按现有业务来源与SQL校验，在新临时数据库实测；不能把数据库约束通过当全部业务已上线。
