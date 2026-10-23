# T034 I01：任务创建材料与运行绑定数据说明

2026-10-22（北京时间）。本文件说明[0016增量迁移](../../backend/business_migrations/0016_task_creation_plan_bindings.sql)及其适用边界。它是I01内部基础说明，文档生成本身不增加开发完成数，不表示材料已获采用、任务创建接口已实现或共享数据库已升级。

依据：[实施计划第3节](../03-development/t034-creation-implementation-plan.md)、[创建接入设计](../03-development/t034-creation-integration-design.md)、[T034任务卡](../../tasks/backend/T034.md)。实际运行命令、源码摘要、失败及未验事项以[本批验证回执](../00-project/validation/t034-i01-material-foundation-report.json)为准；这里不预先登记测试通过。

## 1. 范围与统计口径

I01增加三份材料、一份不可变映射修订、一份可变采用头及一份不可变运行快照，共六张内部表。迁移不新增公共OpenAPI字段，不注册`createTask`，不安装计划读取或采用管理函数，不配置真实计划提供方，不派发任务或执行算法。

| 表 | 字段数 | 数据范围及用途 |
| --- | ---: | --- |
| `task_policy_artifact` | 11 | 组织私有，固定完整策略身份与材料字节 |
| `task_plan_artifact` | 10 | 组织私有，固定执行计划身份与材料字节 |
| `task_capability_manifest` | 10 | 组织私有，固定整份执行能力清单身份与材料字节 |
| `task_plan_mapping_revision` | 27 | 组织私有、明确适用案件，固定适用条件和三份材料引用 |
| `task_plan_mapping_head` | 12 | 组织私有、明确适用案件，保存精确适用元组的当前修订指针 |
| `task_run_plan` | 36 | 案件范围，追加保存一次运行的请求与材料绑定 |
| 合计 | 106 | 全部为新增字段，未向旧表增加列 |

迁移研发结构的预期统计为旧64表、861列增加至**70表、967列**，最终以回执中的实际数据库查询核验。项目源设计的**62张提案业务表**是另一统计口径；六张内部运行基础表不能覆盖源提案、替代原任务范围，也不是新增六项已验收业务功能。

下文各表字段均为`NOT NULL`。时间类型均为`timestamptz`；新表UUID字段均拒绝全零UUID。创建者、变更者及其组织以复合外键绑定真实存在的`users`记录；这不自动证明相应人员具有采用或审批权限。客户端`TaskCreate`不能提供创建者、创建时间、材料采用状态或这些内部字段。

## 2. 字节、摘要与格式身份

| 名称 | 精确定义 | I01数据库核验及限制 |
| --- | --- | --- |
| A／`request_body_sha256` | 冻结公共请求正文的规范UTF-8字节摘要；保留modules顺序及JSON字符串字面形式 | 与`request_body_bytes`的SHA-256一致；不将大小写不同的UUID字符串改成同一份原正文 |
| B／`authorization_request_digest` | 沿用权限目录对`{path,query,body}`计算的摘要，包含其既有序列化语义 | I01仅检查64位小写hex格式；数据库没有B的完整输入，不能从A重算B，也不要求A与B相等 |
| `PolicyDefinition.sha256` | 既有策略定义内部`values`规范字节的摘要，对应`definition_ref`的内容身份 | 由材料解析器核验定义内部关系；它不是完整策略材料的摘要 |
| `policy_sha256` | 完整策略材料`canonical_bytes`的SHA-256 | 数据库检查完整字节摘要，不用定义内部values摘要替代 |
| `plan_sha256`／`capability_sha256` | 各自完整计划／整份能力清单规范字节的SHA-256 | 分别计算、分别绑定；能力三元组指整份清单，不是单个M编号 |
| `input_sha256` | 本次运行输入清单`input_manifest_bytes`的SHA-256 | 与所关联`task_run.input_sha256`及策略版本一起通过复合外键核验；不等同原件摘要或尚未物化的节点输出摘要 |
| `validation_receipt_sha256` | 材料校验回执精确字节的SHA-256 | 绑定revision与run快照；摘要相符不证明回执签发者可信、许可有效或材料获准采用 |

所有SHA字段均要求64位小写十六进制。具有对应bytea列的摘要还要求`encode(sha256(bytea列),'hex')`精确相等，字节列不得为空。数据库不使用`jsonb::text`重构规范正文；同一语义的不同字节不会被数据库悄悄当成同一材料。

内部规范化版本固定为`task-material-json-utf8-sortkeys-v1`。三份artifact的数据库列`schema_version`保存**格式身份URI**：

| 材料 | 数据库`schema_version`固定值 |
| --- | --- |
| policy | `urn:media-trace:api:0.1.0#/$defs/PolicyDefinition` |
| plan | `urn:media-trace:task-execution-plan:1.0.0` |
| capability | `urn:media-trace:task-capability-manifest:1.0.0` |

计划、能力及输入清单JSON文档中的`schema_id`与`schema_version: 1.0.0`是解析器文档字段，不能与数据库上述格式身份列或实际计划采用版本混淆。输入清单格式身份为`urn:media-trace:task-input-manifest:1.0.0`。

**两层验证分别成立：** 材料解析器负责严格UTF-8/JSON、重复键、Schema、图依赖、输入输出及显式资源预算等结构语义；I01数据库负责字节摘要、固定格式标识、关系键、时间相对顺序、不可变性和访问边界。SQL的bytea摘要CHECK不解析整份JSON、不证明Schema通过，也不核实真实handler、动态许可或采用权威。数据库测试中的自建字节行只证明相应SQL约束，不能当作已通过材料解析器或已采用的业务输入。

## 3. 六表字段

### 3.1 `task_policy_artifact`（11列）

| 字段 | 类型 | 含义及约束 |
| --- | --- | --- |
| `org_id` | uuid | 材料所属组织；引用`organizations.org_id` |
| `policy_id` | uuid | 既有`policy_registry`中的策略标识 |
| `policy_kind` | text | 策略种类，1—128字符；必须与被引用registry行一致 |
| `policy_version` | text | 策略身份版本，1—128字符；必须与被引用registry行一致 |
| `canonical_bytes` | bytea | 完整策略材料的规范字节，不是仅values子对象 |
| `policy_sha256` | text | 完整材料摘要，格式及对应字节同时校验 |
| `schema_version` | text | 固定为既有PolicyDefinition格式身份URI |
| `canonicalization_version` | text | 固定为本节约定的规范化版本 |
| `provenance_ref` | text | 非空来源依据引用；字符串存在本身不证明依据有效 |
| `created_by` | uuid | 追加者；与`org_id`共同引用`users(user_id,org_id)` |
| `created_at` | timestamptz | 追加时间，默认`now()` |

主键为`(org_id,policy_id,policy_kind,policy_version)`，另有包含`policy_sha256`的完整唯一键。迁移为旧`policy_registry`追加`UNIQUE(org_id,policy_id)`和`UNIQUE(org_id,policy_id,kind,version)`，以完整复合外键防止策略身份错配；不改旧列、不改变旧行状态。registry中的`DRAFT/APPROVED`均不单独构成采用依据。I01关系键也不替代定义引用与正文语义的后续受控核验。

### 3.2 `task_plan_artifact`（10列）

| 字段 | 类型 | 含义及约束 |
| --- | --- | --- |
| `org_id` | uuid | 所属组织，引用`organizations` |
| `plan_id` | text | 执行计划身份，1—128字符 |
| `plan_version` | text | 计划版本，1—128字符 |
| `canonical_bytes` | bytea | 完整执行计划规范字节 |
| `plan_sha256` | text | 完整计划字节摘要 |
| `schema_version` | text | 固定执行计划格式身份URI |
| `canonicalization_version` | text | 固定规范化版本 |
| `provenance_ref` | text | 非空来源依据引用 |
| `created_by` | uuid | 同组织追加者，复合引用`users` |
| `created_at` | timestamptz | 追加时间，默认`now()` |

主键为`(org_id,plan_id,plan_version)`；另有`(org_id,plan_id,plan_version,plan_sha256)`唯一键。已有身份不能覆盖为另一份正文，内容相同也不能绕过追加不可变约束执行普通UPDATE。

### 3.3 `task_capability_manifest`（10列）

| 字段 | 类型 | 含义及约束 |
| --- | --- | --- |
| `org_id` | uuid | 所属组织，引用`organizations` |
| `capability_id` | text | 整份执行能力清单身份，1—128字符 |
| `capability_version` | text | 清单版本，1—128字符 |
| `canonical_bytes` | bytea | 整份清单规范字节 |
| `capability_sha256` | text | 整份清单字节摘要 |
| `schema_version` | text | 固定能力清单格式身份URI |
| `canonicalization_version` | text | 固定规范化版本 |
| `provenance_ref` | text | 非空来源依据引用；不代替逐项许可核验 |
| `created_by` | uuid | 同组织追加者，复合引用`users` |
| `created_at` | timestamptz | 追加时间，默认`now()` |

主键为`(org_id,capability_id,capability_version)`；另有包含`capability_sha256`的完整唯一键。清单记录不代表其handler已部署、模型已准入、许可仍有效或依赖已满足。

### 3.4 `task_plan_mapping_revision`（27列）

| 字段 | 类型 | 含义及约束 |
| --- | --- | --- |
| `revision_id` | uuid | 不可变修订标识，主键 |
| `org_id` | uuid | 所属组织，引用`organizations` |
| `case_id` | uuid | 明确适用案件；与`org_id`复合引用`cases` |
| `mapping_id` | text | 映射身份，1—128字符 |
| `mapping_version` | text | 映射版本，1—128字符 |
| `authority_version` | text | 采用权威版本身份，1—128字符；文本不自动产生权威 |
| `scene` | text | 仅`accident_rumor/harmful_content/repost_tamper_trace` |
| `modules` | text[] | 一维、下界1、非空、无NULL、无重复且仅含既有12模块；保留顺序 |
| `priority` | text | 仅`low/normal/high` |
| `policy_id` | uuid | 精确策略标识 |
| `policy_kind` | text | 精确策略种类，1—128字符 |
| `policy_version` | text | 精确策略版本，1—128字符 |
| `policy_sha256` | text | 精确策略材料摘要 |
| `plan_id` | text | 精确计划身份，1—128字符 |
| `plan_version` | text | 精确计划版本，1—128字符 |
| `plan_sha256` | text | 精确计划材料摘要 |
| `capability_id` | text | 精确整份能力清单身份，1—128字符 |
| `capability_version` | text | 精确清单版本，1—128字符 |
| `capability_sha256` | text | 精确清单摘要 |
| `valid_from` | timestamptz | 映射声明的生效起点 |
| `valid_until` | timestamptz | 映射声明的截止时点，严格晚于起点 |
| `adoption_basis_ref` | text | 非空采用依据引用；需后续核验实际权威 |
| `recovery_generation` | text | 恢复代际身份，1—128字符 |
| `validation_receipt_bytes` | bytea | 不可变材料校验回执字节 |
| `validation_receipt_sha256` | text | 回执字节摘要 |
| `created_by` | uuid | 同组织追加者，复合引用`users` |
| `created_at` | timestamptz | 追加时间，默认`now()` |

`(org_id,mapping_id,mapping_version)`唯一，`(org_id,case_id,revision_id)`也唯一。三份材料分别通过含组织、完整身份/版本和摘要的复合FK绑定。另有分别覆盖映射/权威、policy、plan、capability、回执/代际/有效期、精确适用元组的紧凑唯一键，供head与run快照精确引用；不依赖一个过宽的“全部字段”索引。

模块词表沿用`INGEST/RESOURCE/MEDIA/RISK/FORENSIC/IMGRET/VIDTRACE/ORIGIN/PROPAGATION/CLAIM/REVIEW/OPS`。例如`[MEDIA,RESOURCE]`与`[RESOURCE,MEDIA]`是不同适用顺序，不在数据库里排序合并。

### 3.5 `task_plan_mapping_head`（12列）

| 字段 | 类型 | 含义及约束 |
| --- | --- | --- |
| `org_id` | uuid | 组织身份，引用`organizations` |
| `case_id` | uuid | 明确适用案件，与组织复合引用`cases` |
| `scene` | text | 既有三场景之一 |
| `policy_id` | uuid | 精确策略身份 |
| `policy_version` | text | 策略版本，1—128字符 |
| `modules` | text[] | 已校验的有序模块列表 |
| `priority` | text | 既有三种优先级之一 |
| `revision_id` | uuid | 当前指向的不可变revision |
| `state` | text | 仅内部`INACTIVE/ACTIVE/REVOKED`；无默认值，更无默认ACTIVE |
| `row_version` | bigint | 正数，默认1；初始插入要求1，更新严格加1 |
| `changed_by` | uuid | 同组织变更者，复合引用`users` |
| `changed_at` | timestamptz | 变更时间，默认`now()`；后续受控管理入口负责更新实际变更时间 |

主键为`(org_id,case_id,scene,policy_id,policy_version,modules,priority)`。包含revision及上述适用字段的复合外键，保证指针不能指向另一个案件、场景、模块顺序或优先级的修订。触发器禁止变更主键适用身份，要求UPDATE严格递增版本，拒绝DELETE和TRUNCATE。

I01没有允许业务调用的管理函数，manager的读写policy仍显式拒绝，迁移未写任何head。上述结构支持后续设计，不代表已有ACTIVE映射。初始版本约束也不构成真实备份导入或非初始版本恢复的验证结论。

### 3.6 `task_run_plan`（36列）

| 字段 | 类型 | 含义及约束 |
| --- | --- | --- |
| `case_id` | uuid | 固定运行所属案件 |
| `task_id` | uuid | 固定任务标识 |
| `run_version` | bigint | 正数运行版本 |
| `org_id` | uuid | 所属组织；与案件复合绑定 |
| `created_by` | uuid | 同组织写入者，复合引用`users` |
| `created_at` | timestamptz | 快照追加时间，默认`now()` |
| `request_body_bytes` | bytea | 本次冻结请求规范字节 |
| `request_body_sha256` | text | A摘要，必须与冻结请求字节相符 |
| `authorization_request_digest` | text | 独立B摘要；不要求与A相等 |
| `revision_id` | uuid | 本次采用证明绑定的不可变修订 |
| `mapping_id` | text | 精确映射身份，1—128字符 |
| `mapping_version` | text | 精确映射版本，1—128字符 |
| `authority_version` | text | 精确权威版本身份，1—128字符 |
| `head_row_version` | bigint | 当次证明观察到的head正数版本；不是指向当前可变head的FK |
| `policy_id` | uuid | 精确策略身份 |
| `policy_kind` | text | 精确策略种类，1—128字符 |
| `policy_version` | text | 精确策略版本，1—128字符 |
| `policy_sha256` | text | 冻结策略材料摘要，与`policy_bytes`一致 |
| `policy_bytes` | bytea | 冻结完整策略材料字节 |
| `plan_id` | text | 精确计划身份，1—128字符 |
| `plan_version` | text | 精确计划版本，1—128字符 |
| `plan_sha256` | text | 冻结计划摘要，与`plan_bytes`一致 |
| `plan_bytes` | bytea | 冻结计划规范字节 |
| `capability_id` | text | 精确能力清单身份，1—128字符 |
| `capability_version` | text | 精确清单版本，1—128字符 |
| `capability_sha256` | text | 冻结清单摘要，与`capability_bytes`一致 |
| `capability_bytes` | bytea | 冻结整份清单规范字节 |
| `input_manifest_bytes` | bytea | 本次运行输入清单规范字节 |
| `input_sha256` | text | 运行输入清单摘要，与上述字节及既有run记录绑定 |
| `validation_receipt_bytes` | bytea | 本次固定材料校验回执字节 |
| `validation_receipt_sha256` | text | 回执摘要，与字节及revision中的摘要绑定 |
| `mapping_valid_from` | timestamptz | revision有效起点的冻结副本 |
| `mapping_valid_until` | timestamptz | revision有效截止副本，严格晚于起点 |
| `proof_observed_at` | timestamptz | 证明观测时点，不早于冻结映射起点 |
| `proof_valid_until` | timestamptz | 晚于观测时点且不晚于冻结映射截止时点 |
| `recovery_generation` | text | 精确恢复代际，1—128字符 |

主键为`(case_id,task_id,run_version)`，引用既有`task_run`同一运行；迁移为旧run追加`UNIQUE(case_id,task_id,run_version,input_sha256,policy_version)`，以另一个复合FK同时核验运行输入摘要和策略版本。

run快照分别以复合FK核对同一revision的映射/权威、policy、plan、capability、回执摘要、恢复代际及有效期，不能只改其中一份引用或换成同摘要的另一revision。对应bytea的SHA又分别接受CHECK。数据库不把`head_row_version`关联为当前head外键，因此后续head撤销或切换不应破坏已经保存的历史run事实。

时间CHECK只证明本行与固定revision的相对窗口；当前时刻是否仍有效、当前head是否仍为原revision、权限/来源/能力是否撤销，都需I02/I03的实际权威、锁和事务末核验。I01未证明这些正向业务条件。

## 4. 不可变性与角色边界

三份artifact、revision及run_plan通过既有`mt.reject_mutation()`触发器拒绝UPDATE、DELETE和TRUNCATE。head允许的后续修改仍须精确版本及稳定身份；不能通过普通覆盖改写历史材料。

六表均开启`ENABLE ROW LEVEL SECURITY`及`FORCE ROW LEVEL SECURITY`。RLS与表ACL共同约束，不能只看某个GRANT就判断已允许读取。

`task_run_plan`还沿用T015对所有可供runtime读取的CASE表要求的强制策略：`request_data_scope AS RESTRICTIVE TO mt_runtime`，同时对读取和写入核验`org_id=mt.org_id() AND mt.scope_allows_case(case_id)`。它与下列操作级PERMISSIVE策略共同生效，保留`createTask`、CASE模式及插入者条件；即使后续新增较宽的PERMISSIVE策略，也不能绕过这一组织/案件范围底线。新增测试精确核对该策略的名称、RESTRICTIVE类型、角色、ALL命令及USING/WITH CHECK表达式；实际执行结果仍以本批验证回执为准。

| 角色 | 表ACL | I01实际RLS及作用域 |
| --- | --- | --- |
| `mt_runtime` | 五私表无任何表权限；run_plan仅SELECT/INSERT | run_plan要求同org、合法CASE/createTask、案件成员关系；插入还要求`created_by=actor_id`。I01没有注册createTask，所以当前正向runtime读写仍拒绝 |
| `mt_task_plan_lookup` | 五私表仅SELECT及必要scope helper EXECUTE；无写权限、无旧表SELECT | 至少要求同org、registered createTask、合法CASE及案件范围；revision/head还要求同case。未注册createTask时不能靠手写GUC读出材料 |
| `mt_task_plan_manager` | 五私表SELECT/INSERT及head UPDATE；没有DELETE/TRUNCATE | I01未安装受控管理入口，读、插入及head更新policy均显式false；不能把占位ACL当作已生效管理范围 |

两新角色均为NOLOGIN、NOINHERIT、NOSUPERUSER、NOBYPASSRLS、NOCREATEROLE、NOCREATEDB、NOREPLICATION。迁移拒绝不安全的既有角色属性及这些角色的既有成员关系，不给runtime或真实人员授予成员资格。`Database._unprivileged`还拒绝持这两个角色成员资格的业务连接，防止以后错误授予继承权限时继续作为普通业务连接使用。

`scope_catalog.TABLE_SCOPES`将五私表显式列为ORG且`runtime_select=False`，将run_plan列为CASE；ORG分类只表达材料所属范围，不赋予组织内普通用户直接读取权限。I01不新增LOOKUP正文通道，不增加raw-GUC绕过注册scope的例外，也没有真实采用账号或默认映射。

## 5. 升级、验证及后续衔接

迁移通过既有`business_migrations.runner.apply_migrations`在事务内执行并登记摘要。0001—0015文件保持不变；本增量不回填旧task/run的计划，不重算旧摘要、不删除或改写历史行。完整升级中任一步失败应回滚本次DDL及0016账本记录；实际证据以本批回执为准。

新测试入口为[tests/business/test_task_creation_migration.py](../../tests/business/test_task_creation_migration.py)。其中包括空库、历史升级/回放及故障回滚、字段/RLS/ACL、精确字节/FK、A/B区别、有序模块、head版本、不可变性、私有角色/伪造scope拒绝和新角色继承防线。数据库测试仅使用新建随机隔离库；命令例如`python -m pytest tests/business/test_task_creation_migration.py -q`是验证入口说明，不是已经运行通过的声明。

本轮不创建正式ACTIVE映射，不将自建测试人员/材料行装入共享环境，不启用HTTP创建、任务消费者或算法；源码同步不代表共享迁移已经应用。

**迁移后续规则：** 实施计划中的“同一拟0016”是该文件尚未发布时的规划描述。I01的0016一旦提交并进入迁移账本，I02的scope注册、固定读取函数、管理作用域及其他后续变更必须使用**0017或下一个未占用编号**的增量迁移，不得回头修改0016内容或摘要。I02/I03还须分别证明真实采用权威与材料、当前head及撤销锁序、动态能力、实际输入、原子创建和精确重放；I01结构成立不能代替这些步骤。
