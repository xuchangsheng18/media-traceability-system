# 数据库设计文档导航

本轮0.4-review候选。先读设计与字典，再核对SQL、接口映射和排序契约。

2026-10-22新增[T032固定运行与任务事件约束](task-event-run-integrity.md)：0015只增加事件到固定运行的复合外键及现有状态词汇CHECK；隔离升级、失败回滚与共享采用分开记录，不改变原字典字段或历史迁移。

T016新增[案件操作令牌0011扩展](operation-token-extension.md)和[安全及真实消费者边界](../08-security/t016-operation-token-boundaries.md)：原15列增加12列，完整0011为64表861列；服务端案件签发、摘要存储及同根消费分别记录。0001—0010保留。2026-10-21的新随机交付预览库已有0001—0011迁移记录；旧共享库和原14202业务实例未因该次交付升级，正式动作及角色执行关系另验。具体证据和实例边界见下节。

## 字典版本、迁移版本与运行实例

| 范围 | 准确含义与证据 |
| --- | --- |
| 当前初始化设计 | [initial-schema.sql](initial-schema.sql)与[表目录](table-catalog.json)为62表825字段，供新空库设计与字段追溯；不等于所有表的业务访问已实现。 |
| 历史0001与追加0002 | [0001源摘要](../../backend/business_migrations/baseline-source.json)固定62表824字段；[0002](../../backend/business_migrations/0002_upload_result.sql)追加`upload_session.duplicate_of`后为825字段。824是历史版本计数，不应用当前825字段SQL覆盖历史0001。 |
| 完整0011结构 | 身份扩展0004与授权代际0008累计增加2张表；应用0001—0011后为64表861字段。迁移账本`mt_meta.schema_migrations`及独立PoC五表不计入业务表数。 |
| 新交付预览实例 | [2026-10-21交付验证](../00-project/validation/development-delivery-validation.json)的`runtime_migrations`记录0001—0011，且明确仅迁移新随机目标；业务API为Linux回环14212，网关14213，本机入口为`http://127.0.0.1:14183/`。该条引用既有交付记录；本轮另以只读事务查询pg_catalog和迁移账本，确认64表861列及0001—0011，见[本批实例核对](../00-project/validation/t001-t123-catalog-read-report.json)。未读取业务行或修改数据库。 |
| 原实例与共享库 | [运行手册](../10-deployment/business-development-runbook.md)保留原14202实例及数据；上述新目标的迁移记录不能证明原实例或共享库已升级。源码同步也不等于迁移采用。 |
| 后续源码与前端更新 | [PPT页面更新证据](../00-project/validation/ppt-interface-alignment.json)记录后端源码仍为`8b7fc475b5a0e8c3e7687559a6f09b65e39e1373`，数据库未变。本轮新增[0012迁移](../../backend/business_migrations/0012_catalog_reads.sql)，39项读取和1项迁移保护测试通过，仍属源码及隔离验证范围，本页不登记其已被14212或共享库采用。 |

任务、表与后端方法的逐项入口见[数据库设计中的实施清点入口](database-design.md)。表已创建、方法已实现、运行实例已采用和整任务验收须分别记录。

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
