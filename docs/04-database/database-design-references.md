# 数据库修订的官方机制依据

核查日期2026-10-12。官方资料用于确认数据库与接口规范的技术机制；本项目字段业务含义、排序策略和授权要求由本地设计及本轮工程提案给出，不能声称是网上查得的公安业务规则。

| 来源 | 核验机制 | 本项目采用方式 |
| --- | --- | --- |
| [PostgreSQL 16 Constraints](https://www.postgresql.org/docs/16/ddl-constraints.html) | CHECK用于行值检查；UNIQUE约束组合唯一；复合外键约束关系；CHECK结果为NULL不能替代NOT NULL | 将名次范围、批次内唯一和同案件/簇引用分开执行 |
| [PostgreSQL 16 CREATE TRIGGER](https://www.postgresql.org/docs/16/sql-createtrigger.html) | 约束触发器可延迟到事务末，支持SET CONSTRAINTS提前检查 | 原子写入头表和候选，提交时检查数量与连续名次 |
| [PostgreSQL 16 Date Time Types](https://www.postgresql.org/docs/16/datatype-datetime.html) | 带时区时间戳表示时间点，输出按会话时区转换，不保存原始时区名称 | 修正“创建时间UTC”容易引起的误解；接口携带时区 |
| [PostgreSQL 16 Row Security Policies](https://www.postgresql.org/docs/16/ddl-rowsecurity.html) | RLS控制行可见性，超级用户等可绕过，表所有者与FORCE规则须区分 | 新表沿用案件RLS并限制运行角色权限，不承诺防超级用户 |
| [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html) | Schema Object与JSON Schema 2020-12体系衔接 | 保持本项目3.1.0候选契约，同步接口和生成Schema |
| [JSON Schema Array](https://json-schema.org/understanding-json-schema/reference/array) | maxItems限制数组长度，uniqueItems比较完整元素 | 候选数组最多3项；逐字段唯一和连续名次另做语义校验 |

首发排序快照结构、候选0条语义和稳定并列规则属于[本项目修订提案](first-source-ranking.md)。官方规范没有规定本项目应使用哪些业务字段，也不替代数据授权、审批或模型验收。

## 本轮补充核查

- [PostgreSQL 16 JSON函数](https://www.postgresql.org/docs/16/functions-json.html)：字段提取在缺失或结构不匹配时可能返回SQL NULL；本项目使用明确的类型检查及IS DISTINCT FROM，防止漏键被当作通过。
- [PostgreSQL 16 UUID类型](https://www.postgresql.org/docs/16/datatype-uuid.html)：数据库UUID输入可接受大小写及省略连字符等形式；JSON证据引用的标准连字符要求是本项目与API保持一致的工程约定。
- [PostgreSQL 16 JSON类型](https://www.postgresql.org/docs/16/datatype-json.html)：JSONB存储JSON数据；本项目字段键、数组格式、UUID与同案件存在性由显式触发器执行，不把JSONB类型误称为完整业务Schema验证。

以上网页于2026-10-12核查，使用PostgreSQL16文档，对应当前隔离测试版本；业务授权、首发规则和具体字段解释仍以本地项目提案为来源。
