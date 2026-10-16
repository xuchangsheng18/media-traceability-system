# T011/T012 身份关系数据库实施计划

本轮沿用用户已选择的当前会话直接实施方式；设计见[身份关系设计](t012-identity-relations-design.md)，原有正式输入缺口不因开发而批准。

## 本批步骤

- [x] 在现有 Linux py310 与隔离测试库运行原业务/平台回归，记录起点。
- [x] 先编写身份映射、到期/撤销、同单位外键、不可改绑、版本冲突、管理权限和旧库升级的失败测试。
- [x] 新增 `backend/business_migrations/0004_identity_relations.sql`；保持0001—0003摘要，增加映射表、复合约束和受限查询/管理角色。
- [x] 在 `backend/business_app/identity/directory.py` 实现内部 `IdentityDirectory`，提供创建/绑定、精确映射查询和带 expected_version 的停用/撤销；不增加HTTP入口。
- [x] 新增数据库补充字典、更新T011设计/机器实体及校验器；原62表825字段作为初始化基线保留，增量后实际结构单列。
- [x] 运行实际PostgreSQL专项、既有业务/平台/工程回归、格式、静态类型及文档导航漂移检查；仅实际通过的范围登记完成。
- [x] 新建独立、无真实人员数据的身份研发库并迁移，保存连接信息于Git外私有运行目录；已有目标必须先校验，不覆盖。
- [x] 评审、同步T011/T012任务卡、分步导航和完整清单；按既有授权提交并同步GitHub及Linux，记录实际结果。

## 共享接口和验收重点

`IdentityDirectory(connection)`消费受限管理/查询角色的真实SQLAlchemy Connection；`resolve(issuer,subject)`产出包含 identity_id、user_id、org_id、mapping_version 与当前 row_version 的不可变映射对象，不产出登录令牌或权限允许。现有AuthorityProvider保持独立，T013待正式协议后再接入。

重点检查：同名外部主体不同提供方、撤销后再绑定、旧跨单位脏成员、缺失/非法参数、失效与并发版本、软禁用后的案件RLS、运行角色权限隔离。迁移和约束需数据库实测，不以文档/Schema校验替代。

实际执行结果记录于 `docs/00-project/validation/t012-identity-relations-report.json`。完整T011、T012、T013验收及生产部署不在本批自动关闭范围内。
