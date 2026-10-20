# T015增量数据范围约束与事务说明

本页对应本地隔离研发候选`88f6f651bd82237db24c7ca663c6d21522314465`。P02代码已形成，当前461项业务回归及质量检查通过；隔离启动路径造成的报告生成失败已定位，修正后完整入口仍待核验；[执行进度](../00-project/validation/t015-data-scope-progress.json)与[定向证据](../00-project/validation/t015-data-scope-p02-progress.json)区分已验证子范围和待完成验证。尚未向共享数据库安装本迁移，也不表示T015整卡验收。

## 结构与迁移边界

[0010_data_scope.sql](../../backend/business_migrations/0010_data_scope.sql)接续0009，不改0001—0009，不增加业务表或字段。现有开发结构仍为64表、849字段；历史62表、825字段原件保留。迁移通过既有摘要台账和单事务执行，不能用初始化脚本覆盖已有数据库。发布后的修复须新增前向迁移，不能通过删策略、修改0010摘要或恢复旧宽权限回切。

| 表类别 | 数量 | 当前限制 |
| --- | --- | --- |
| 案件业务 | 45 | 原有效成员约束与新org、精确case条件同时成立；同一用户属于A/B案件也不能在A根事务读取或写入B |
| 单位业务 | 6 | 保留原单位与ACL条件；CASE和ORGANIZATION仅在原功能授权下访问本单位行，LOOKUP不开放原始业务表 |
| 身份、角色与成员目录 | 8 | 保留原本人/单位可见及最小ACL；角色目录新增RLS时保留既有目录管理写入路径，不向runtime增加管理继承 |
| 单位/案件混合 | 4 | approval_request、approval_decision、operation_token、audit_event：CASE仅精确案件；ORGANIZATION仅本单位case_id为空的行 |
| 内部授权代际 | 1 | authorization_epoch继续不授予runtime直接表访问；沿用原受限代际函数 |

该表是语义分类与约束目录，不是64表全部CRUD已测。当前SQL、HTTP、对象操作的实际覆盖分别登记；任务和历史版本还需P03的DAO关联约束。

## 三种事务

| 模式 | 可访问范围 | 构造与复查 |
| --- | --- | --- |
| CASE | 当前证据固定的单位和单一案件 | 消费T014请求/工作证据，绑定事务局部值，使用同一连接hold/finish原栅栏；传入其他case拒绝 |
| ORGANIZATION | 当前单位适用元数据和case_id为空的单位审计 | 不允许直接读取案件正文；本人案件ID经专用函数返回后逐case.read核验 |
| LOOKUP | 固定kind、精确ID的最小授权元数据 | 核验Principal或当前WorkTrust，先设置PostgreSQL只读事务；不持授权共享行锁，不返回业务正文，不直接形成ALLOW |

局部设置仅为`app.actor_id`、`app.org_id`、`app.scope_mode`、`app.case_id`、`app.operation_id`、`app.lookup_kind`、`app.lookup_id`，全部使用绑定参数。退出或回滚不把这些值及ContextVar留给下一请求。嵌套复用原根连接，禁止换actor/org/case/operation或降级LOOKUP；同一任务的进一步缩小由后续DAO约束落实。

只传Actor、Scope或自行构造DataScope不能取得业务访问。业务连接拒绝SUPERUSER、BYPASSRLS、目录/查找管理继承、schema owner继承及列明的高权限组。受信事实读取器只能复用当前根连接和相同配置目标，不能借另一连接替换范围。

## 新增固定函数

| 函数 | 含义与边界 |
| --- | --- |
| mt.scope_operation() | 识别当前已登记的真实业务/工作操作；未知操作不产生有效模式 |
| mt.scope_mode() | 识别CASE、ORGANIZATION、LOOKUP；缺失或未知值不放行业务行 |
| mt.scope_case_id() | 读取精确case UUID，空值、错误格式或零UUID不形成案件范围 |
| mt.scope_allows_case(uuid) | 同时验证CASE模式、精确案件及原有效成员资格 |
| mt.current_actor_case_ids() | getCurrentUser的单位事务仅枚举本人有效成员案件ID，不开放案件正文或他人目录 |
| mt.scope_lookup_kind_allowed(text,text) | 固定kind/operation纯谓词；实际SQL矩阵与Python目录逐格对照，不能传入表名或投影 |
| mt.lookup_scope_metadata(text,uuid) | 固定15种资源的最小定位/条件元数据，精确org、case、ID及适用成员关系；不是通用查询函数 |

函数均撤销PUBLIC执行权限，按需授予mt_runtime。两个读取元数据的SECURITY DEFINER函数固定search_path；对FORCE RLS依赖表增加实际迁移owner的SELECT策略，并实测非超级用户owner。该owner策略不授予runtime，也不替代业务身份验证。

元数据仅包含固定ID/版本、适用owner/purpose/kind、成员及来源版本/期限、imports/reviews/clusters必要关联等。正文、details、snapshot、claim_text、artifact字节、凭据和任意文件路径不在输出投影内。数据库内部对原行计算摘要用于发现变化，不返回原行。案件ARCHIVED状态沿用原有效成员语义并参与版本事实，未把缺乏正式依据的状态转换擅自设成自动撤权；定位仍不等于业务授权。

## 真实调用链

授权前ObjectFactsReader通过SqlScopeLookup只读定位；授权后的条件重验复用CASE/ORGANIZATION根连接及同一事实构造逻辑。来源状态、用途、版本和期限仍核验，补充分类/委托/职责端口缺失继续拒绝。

节点claim需要受信队列的task_id，返回的内部Lease保存该task_id，结束时仍核验节点归属与fencing；公开API参数不变。内部推理在服务身份之外复用task_execution工作授权，输入读取前及后端返回后分别取得当前证据；不把五秒事实刷新当长任务超时，也不跨后端计算持有旧数据库事务。

业务测试中的合成事实、目录输入和工作上下文仅在tests显式装配；应用默认不加载。真实恢复代际、正式提供者、现场性能、原生服务迁移和整卡验收仍按各自证据判断。

事务只读、限制性策略与owner行为依据：[PostgreSQL事务设置](https://www.postgresql.org/docs/16/sql-set-transaction.html)、[行级安全](https://www.postgresql.org/docs/16/ddl-rowsecurity.html)；内部摘要使用[官方二进制字符串函数](https://www.postgresql.org/docs/16/functions-binarystring.html)。
