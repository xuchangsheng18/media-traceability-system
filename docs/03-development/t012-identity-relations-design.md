# T011/T012 身份映射、单位与案件关系实现设计

2026-10-16；本轮范围由用户明确要求“设计和完善身份与用户映射、单位和案件关系、数据库建立起来”。沿用已认可的独立业务迁移和当前会话执行方式，补齐既有身份数据底座；不是新增身份供应商或正式授权制度。

## 目标和选择

采用独立的 `user_identities` 映射表，保留 `users.user_id` 为稳定内部主键和已有 `subject` 兼容字段。外部身份以 `(issuer, subject)` 精确区分；不以姓名、邮箱或旧 subject 自动合并，不自动登记或启用未映射账号。相比只加 issuer 列，独立映射支持同一内部用户经明确登记关联多个身份方，撤销单个映射也不更换业务历史主键。相比改用新身份平台，不增加运行依赖或擅定认证协议。

## 数据关系和约束

- 单位一对多用户、单位一对多案件；用户通过显式成员关系进入同单位案件。用户/案件已有主键及所属单位不可普通修改；跨单位共享和人员调动另走后续生效规则，不通过改 org_id 迁走历史。
- 新映射记录包含 identity_id、user_id、org_id、issuer、subject、enabled、expires_at、revoked_at、mapping_version 和既有四个追踪字段 created_at/updated_at/row_version/created_by；默认不启用。`(issuer,subject)` 终身唯一，撤销后不回收给其他内部用户；user/org 和外部键不可修改。
- users 增加 `(user_id,org_id)` 唯一约束；案件成员与映射均以此复合外键阻止跨单位关联。既有脏成员会使升级原子失败，禁止静默删除或自动改单位。
- organizations 增加 enabled，默认 true 保留原目录行为；单位开关本身不授予用户、角色、案件或来源权限。用户原 enabled 默认 false 保持；user_roles 增加 revoked_at，撤销不硬删除。
- 查询映射同时检查映射启用/到期/撤销、用户启用、单位启用；查不到或失效统一拒绝，不区分存在性。现有案件 RLS 增加单位停用检查，不改变来源、用途或正式权限的独立校验。

## 访问边界和生命周期

管理访问为内部 Python 数据访问层，只接受数据库管理员建立的专用 `mt_directory_manager` 权限连接；该角色 NOLOGIN/NOSUPERUSER/NOBYPASSRLS，不授给 mt_runtime，不增加 HTTP 管理接口。可创建单位、用户、案件、成员及身份映射，并以 expected_version 条件执行软禁用和撤销；不授 DELETE/TRUNCATE。明确说明该连接是组织目录管理权，真实人事流程、审批和账号交付仍待落实。

映射查询经专用 `mt_identity_lookup` 角色调用受限 SECURITY DEFINER 函数；固定 search_path、撤销 PUBLIC 执行权限，不开放全表查询。Python 映射器只做已验证外部主体到内部用户的映射，**不验证令牌、不创建登录会话、不接入现有 AuthorityProvider**。未来 T013 必须先验证真实令牌，再调用映射器；不能让客户端自报 issuer/subject 充当认证。

所有读取重查当前状态，不做权限缓存。已有 row_version 表示本行并发版本，不冒充完整策略修订协议或不可变审计。旧用户不自动获得新映射；旧内部用户、业务外键和结果历史继续保留。

## 迁移、恢复和字典

新增 0004 迁移，保留 0001—0003 字节与摘要。62表825字段的历史初始化源不改写；0004 后实际业务库为63表840字段，新增内容由数据库补充字典和机器扩展清单明确描述。外部 API 与模型 Schema 没有字段变化；新增内部持久化来源逐项链接迁移，不生成虚假 API 映射。

升级前备份及排查跨单位成员；失败时整批事务回滚。迁移后新增身份映射不得用 DROP TABLE 回退；需恢复隔离备份到独立目标，或前向修复并逐项对账原用户、案件、成员和新增映射。不会向已有共享 PoC/生产库执行本迁移。

## 验证

先编写实际 PostgreSQL 测试并观察失败，再实现。覆盖：同 subject 不同 issuer 不串号、同外部身份不能改绑/复用、空白非法键拒绝、默认禁用、用户/单位停用、映射到期及撤销、跨单位成员/映射、主键/所属单位不可变、并发版本冲突、运行角色不能管理身份、查询角色不能枚举原表、旧库升级/重放/坏数据升级回滚和旧业务回归。使用 Linux py310 与独立测试库，不替换100包锁，不重启共享7服务。

正式身份方、发行者白名单/密钥、真实单位案件目录、正式角色矩阵、撤销同步时限及实际责任人继续待输入；当前成果仅关闭已实测开发子范围。

## 依据

- [T011](../../tasks/platform/T011.md)、[T012](../../tasks/platform/T012.md)、[现有权限设计](../08-security/access-control-model.md)。
- [OpenID Connect Core §5.7](https://openid.net/specs/openid-connect-core-1_0.html#ClaimStability)：issuer/sub 联合区分身份；本轮仅采用标识原则，不预设正式接入协议。
- [PostgreSQL 16约束](https://www.postgresql.org/docs/16/ddl-constraints.html)、[函数安全](https://www.postgresql.org/docs/16/sql-createfunction.html)：跨表一致性使用复合外键，受限权限函数固定查找路径。
