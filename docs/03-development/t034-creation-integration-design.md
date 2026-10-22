# T034真实映射、受限SQL、原子创建及HTTP接线设计

2026-10-22（北京时间）。状态：**D01_D02_ACCEPTED_IMPLEMENTATION_PLAN_PREPARED_REVIEW_PENDING**，本文件是已获D01/D02限定认可的技术设计，不是代码、迁移、映射采用或部署结果。依据源码`0ffdfb399e159945c025a7b126f1dd7373ecec56`、[T034任务卡](../../tasks/backend/T034.md)、[非算法交付范围](non-algorithm-delivery-scope.md)及[快速计划](non-algorithm-fast-delivery-plan-20261028.md)。开发负责人和指定复核人均为徐昌胜；实际复核、投入和验收仍需分别记录。

2026-10-22用户已认可D01、D02，D03实施计划已准备、尚待审阅。E01—E04真实采用、映射/能力/事实及预算未确认；本次不授权产品实施或生效采用，不增加已证步骤。当前决定见[限定决定记录](../00-project/validation/t034-design-decision-20261022.json)及[实施计划](t034-creation-implementation-plan.md)。

本轮目标是让后续实现者能按真实数据库、权限与HTTP契约落地创建链路。算法、权重、训练、效果评测及Python候选继续暂缓；原100包锁、现有CI与安全失败门禁保持。本次只形成并同步方案、当前证据和导航，**不增加业务完成数**。

## 1. 当前可复用实现与缺口

| 项目 | 当前真实实现 | 本方案拟补；尚未实现 |
| --- | --- | --- |
| 创建结构 | `schemas/api/common.schema.json`的TaskCreate六字段；三类scene、十二模块及priority已定义 | 不增加公共字段、状态或错误码 |
| 请求/证明内核 | `backend/business_app/task_creation.py`已冻结请求、独立Actor/案件、原JSON字节与摘要，并校验TaskPlanProof及重查 | 无真实提供方、可执行正文、任务写入或HTTP接线；64项内核测试不能代替它们 |
| 对象与功能权限 | `permissions/conditional.py`已有TASK_CREATE分支 | `object_facts.py`的BODY_SCHEMAS、SUPPORTED_OPERATIONS、目标校验和resolve_http均未接createTask |
| 受限定位 | `scope_catalog.py`及最新`0014_resource_registry.sql`限定表、列、操作与LOOKUP/CASE | Python资产操作集合、SQL的scope_operation及scope_lookup_kind_allowed均需增量加入createTask |
| 策略/正文 | policy_registry及FileDefinitions可保存策略元数据和内容寻址正文 | DRAFT/APPROVED行、definition_ref和文件存在都不能替代真实采用/撤销权威 |
| 执行资格 | model_registry、显式BackendRegistration、真实发布/输入版本有各自边界 | 登记不等于可执行；36份CandidateDAG均不自动成为获准运行计划 |
| 写入与栅栏 | Database同连接事务、before_commit、AuthorizationFence及ControlReceipts已存在 | task/run/精确计划/node/event/outbox/audit/HTTP回执的创建事务尚未存在 |
| HTTP | OpenAPI已定义POST `/api/v1/analysis/tasks`、createTask、task.create和202 Accepted | POST当前未挂载，404不证明已经验证权限 |

拟新增文件、表和函数在下文均标为“拟”；本轮没有创建这些产品文件或执行SQL。现有表名是**task_node_run**；HTTP成功结构名是**Accepted**。

## 2. 方案比较与推荐

| 方案 | 优点 | 限制与本轮选择 |
| --- | --- | --- |
| 同一PostgreSQL中的采用登记＋固定只读函数＋不可变正文快照 | 能与创建事务共享连接、锁与恢复代际；可审计具体采用版本 | **推荐**。需要增量表/函数及受控管理通道；不预置任何生效映射 |
| 外部权威服务 | 可复用以后已正式部署的策略平台 | 当前无真实提供方和可核验租约/撤销协议；提交前再请求一次仍有远端撤销与本地commit间隙，不能宣称严格原子撤销 |
| 本地配置或候选DAG直接选择 | 实现较少 | 不采用。配置存在、摘要正确或ENGINEERING_CANDIDATE不能证明业务采用、能力可执行或撤销顺序 |

正文在接入前可复用FileDefinitions的仓库外内容寻址方式准备；**事务使用的权威版本必须在采用时导入同库不可变规范字节并核验摘要**。创建事务只读该同库快照，不在持锁期间访问远程可变文件、下载权重、调用模型或投递RabbitMQ。

## 3. 真实映射提供方与执行材料

### 3.1 映射必须绑定的事实

拟提供方`SqlTaskPlanAuthority`实现现有`TaskPlanAuthority.resolve(request, connection=…)`，默认不配置。解析规则不是“找到第一条”：同一组织、明确适用案件、scene、精确policy身份/版本、有序modules及priority的适用元组，必须唯一匹配一份当前有效采用记录。

第一批只支持精确case_id，不实现组织通配、跨案件继承或优先级回退。head唯一键固定为`(org_id,case_id,scene,policy_id,policy_version,modules,priority)`；对同一请求若不同policy kind仍产生多个适用head，拒绝而不择一。revision用独立`revision_id`唯一标识，并保存`(org_id,mapping_id,mapping_version)`唯一键，不能把mapping_id误当revision_id。

- policy_registry现有唯一键为`(org_id,kind,version)`。采用记录必须固定真实policy_id及kind，并核对请求policy_version；不能仅按version跨kind挑选。
- 映射固定mapping_id/version、authority_version、采用依据、计划ID/版本/正文摘要、能力清单ID/版本/摘要、适用期、撤销状态与恢复代际。ID及批准依据来自真实登记，示例和测试ID不得填入生效配置。
- 保留请求原modules顺序、priority、policy字符串和UUID字面形式的摘要语义；不删模型模块、不自动降优先级、不把一个scene的采用推给另外两个scene。未明确允许的组合拒绝。
- 主体/单位/案件/资产、来源分析用途和分类权限仍由各自真实事实提供方证明；映射authorized=True不能包办它们。
- 不缓存ALLOW。可以缓存按精确摘要寻址的不可变字节，采用head、有效期、撤销及代际每次重新核对。

**第一批固定current-head语义：** head切换后旧revision立即不再允许新受理或旧key重放。本方案不新增旧版本继续采用的状态表或resolve_exact接口。旧回执保留作历史，同key不得改绑新head；原绑定不等于当前采用时拒绝。此限制属于D01的明确审阅项，不能在实现时悄悄改成“只要旧revision存在就可重放”。

### 3.2 Proof不是执行计划

现有TaskPlanProof只含绑定与摘要，不能从摘要恢复节点。本方案拟新增严格的内部ExecutionPlan结构及正文读取口：节点代码、依赖、required、missing_policy、handler ID/版本/代码摘要、输入输出Schema、输入映射及前后处理版本、输出引用和派发协议版本均在获准正文中明确。handler通过显式登记表解析，禁止导入正文中的任意Python路径、Shell命令或外部URL。

读取流程：由同一采用记录定位规范正文→核对plan_id/version/sha256→校验内部Schema、闭环依赖、预算和实际handler/能力版本→冻结执行材料→保存逐run快照。CandidateDAG可作人工编制依据，不能直接将其nodes拷入业务运行表或更改status后采用。

为避免“先获完整授权才能读正文、却又要靠正文获授权”的循环，采用导入时须完整验证同库policy/plan/能力正文，并在不可变revision保存绑定三份摘要、Schema/规范化版本、校验器代码版本/摘要和验证结果的校验回执。初始精确asset LOOKUP只返回此可信回执、实际必需handler/模型条目及其当前发布/许可/可用状态的受限事实；事实口逐项核验，缺任何材料就拒绝。LOOKUP不返回完整正文、不取行锁。CASE阶段取得授权后读取同摘要正文，重新完整验证并持有动态状态行锁；导入回执不能替代当前能力检查，也不单凭一列validated=True授权。

**多能力语义待D02确认：** 推荐将现有Proof的单个capability_id/version/hash明确绑定到一份真实采用的**执行能力清单版本**；清单逐项列出实际handler/模型发布及输入输出约束。它不是单个M编号，也不是仓库现在已经有的能力包。拟新增内部Schema与权威登记，不在公共TaskCreate中增加bundle字段，不预置清单ID，不将“模型已注册”推定为“能力已可执行”。

model_task_version只对获准正文实际列出的模型依赖逐项核验。普通handler计划必须由正文和真实清单共同证明“无模型依赖”，同时核验每个普通handler的版本、代码和输入输出；不虚构模型版本，不以算法暂缓把model_task_version或capability恒置True。空节点计划不受理。

算法暂缓时，只有批准正文中的必需非算法handler及真实输入均已落实才可受理。必需模型缺失、许可/发布或版本不可核实，创建前返回既有503，不能先造FAILED任务、写假分数或删节点制造成功。可选节点的SKIPPED/DEFERRED/NOT_SUPPORTED只能由获准正文明确，不能用于必需节点；这些是节点词汇，不是新的任务状态。

## 4. 权限事实与完整请求接线

TASK_CREATE实际是以下AND条件：same_org、case、source、analysis_purpose、model_task_version、capability、classification。功能权限通过并不替代其中任一条件。

### 4.1 拟采用的请求上下文方式

选择**请求范围内的不可变上下文**，不把完整body或计划字段塞入公共API，也不从digest反推请求：

1. guard完成真实Principal取得及严格body解析后，调用freeze_task_create；由服务器Actor/案件构造快照，目标仍是**已有资产**，不是尚不存在的task。
2. 拟新增`permissions/task_creation_context.py`，保存该冻结请求、Principal绑定和权限层原request_digest；通过token式ContextVar上下文管理器，在初始条件授权前进入，覆盖protected route的yield、处理器、同连接事务及最后fence复核，finally无条件恢复。
3. authorize_http、fence.hold/finish及创建服务从同一请求上下文取值，逐次核对主体、operation=createTask、asset/case和目标摘要。缺上下文、错请求、错线程传播或越界复用均503；内部非HTTP调用也必须显式进入同样受控上下文，不能仅凭任意Scope执行。
4. 不放在全局app.state可变槽位，不用仅以用户/任务ID索引的共享缓存。必须测试并发请求、线程池传播、嵌套/异常退出和晚回复的隔离；此设计不是任意Python代码沙箱。
5. ObjectFactsReader拟注入专用TaskCreationFactsReader，只为createTask读取这份快照并核验计划/能力；原SupplementalFacts接口继续提供真实classification等既有事实。不得让计划提供方覆盖其他来源的检查值。

### 4.2 必须同时修改的现有分支

| 位置 | 拟接线 |
| --- | --- |
| `permissions/object_facts.py` | BODY_SCHEMAS登记TaskCreate；SUPPORTED_OPERATIONS登记createTask；目标校验/resolve_http生成asset目标、显式case、analysis目的及请求摘要 |
| 同文件core事实读取 | 将createTask纳入analysis_purpose核心来源检查；现值为None且extra禁止覆盖已有键，不能只往SupplementalFacts塞True |
| 专用创建事实口 | 初始LOOKUP由精确采用的正文校验回执及实际能力逐项事实给出model_task_version/capability；CASE重读同摘要正文再核验。无模型计划须有显式无模型依赖证明；classification仍要求独立真实分类/用途依据 |
| `scope_catalog.py` | lookup_spec('asset')允许createTask；私有映射/正文表显式runtime_select=False，不沿用_ORG_TABLES默认可读分类 |
| 最新SQL目录的增量替换 | scope_operation识别createTask；scope_lookup_kind_allowed允许asset/createTask；不扩展其他对象或任意operation |
| `main.py`与guard | 显式注入提供方/事实口/创建服务，统一保护路由，保留audit_protected_routes及实际挂载OpenAPI投影 |

### 4.3 三种摘要分开保存

| 摘要 | 定义与用途 |
| --- | --- |
| request_body_sha256 | 现有freeze_task_create的规范UTF-8 body摘要：controls.common.canonical，ensure_ascii=False；用于创建幂等与冻结请求 |
| authorization_request_digest | 现有object_facts.digest(path/query/body)；用于权限目标绑定，其规范化和覆盖范围与前者不同，**不得直接相等比较** |
| plan/能力清单/输入清单摘要 | 各自精确规范字节的摘要；分别绑定执行正文、真实能力集合、资产/对象版本及输入映射，不以其中一个冒充另一个 |

## 5. 拟增量迁移0016及受限SQL

拟文件名`backend/business_migrations/0016_task_creation_plan_bindings.sql`；实施前再次核对迁移编号，若被其他工作占用则调整序号，不覆盖。以下是设计字段，**不是已创建的表**。

### 5.1 拟新增数据对象

| 对象 | 关键字段、键和保护 |
| --- | --- |
| `task_policy_artifact`（组织私有） | 精确org/policy_id/kind/version、policy_sha256及canonical_bytes、来源依据；绑定policy_registry身份和不可变正文，不在事务中只凭definition_ref访问文件 |
| `task_plan_artifact`（组织私有） | `(org_id,plan_id,plan_version)`唯一；canonical_bytes bytea、plan_sha256、内部schema/规范化版本及来源依据；内容追加且不可覆盖 |
| `task_capability_manifest`（组织私有） | 真实清单ID/version/hash、规范字节及逐项真实发布/handler引用；非算法也须有实际登记，禁止通用未知能力成功；D02审阅后实施 |
| `task_plan_mapping_revision`（组织私有） | 独立revision_id、mapping_id/version、精确policy_id/kind/version/hash、scene、有序modules、明确允许的priority、plan及capability三元组、采用依据、精确case_id、authority版本/有效期及正文验证回执；核心内容追加不可覆盖 |
| `task_plan_mapping_head`（组织私有） | 第3.1节精确适用唯一键对应一个current revision/state/row_version；head切换即旧采用不再允许；激活/撤销通过受控管理通道和审计；不seed任何ACTIVE映射 |
| `task_run_plan`（案件级） | PK及FK `(case_id,task_id,run_version)`→task_run；org、冻结body字节与A/B摘要、mapping revision、精确policy/plan/capability引用与摘要、执行正文规范字节、输入清单及摘要、证明期限/观测时间、创建人；追加、不可UPDATE/DELETE/TRUNCATE |

补policy_registry的`UNIQUE(org_id,policy_id)`供同单位FK；新组织级引用均带org，不做只按version的弱关联。新run_plan的org/case与task/run一致，节点及事件继续满足既有复合run FK。数据库核对精确字节用`encode(sha256(canonical_bytes),'hex')`，不使用jsonb::text代替现有Python规范字节；若另存JSONB投影须核对其对应正文，不能让投影悄悄覆盖正文。

新run输入清单明确记录资产SHA、实际对象ID/版本/摘要、来源授权版本及适用输入映射；新run的task_run.input_sha256绑定此版本化输入清单，不混用请求body摘要或笼统称原文件SHA。历史run不重算、不补造计划；是否在新写入上启用延迟约束触发器，应只要求本次创建/后续重算消费者提供真实计划，不强行回填已有历史行。

所有新表ENABLE/FORCE RLS。业务角色对私有组织表无直接SELECT/写权限，仅能调用固定函数；task_run_plan按CASE范围开放必要SELECT/INSERT，写入须有同根授权证据。管理者身份、写入/撤销协议、恢复代际与审计一起设计，不能给业务账号owner、BYPASSRLS、角色继承或通用读表权限。

拟设专用NOLOGIN、NOBYPASSRLS函数owner。它只获上述五张私有权威表及函数实际使用的asset/source、policy_registry、案件成员和动态能力/许可关系的必要SELECT，配套仅面向该owner的SELECT policy；policy仍核对transaction-local org/case/operation及固定函数所需范围。无UPDATE/DELETE、无通用动态查询权限，mt_runtime不得继承它。FORCE RLS下不给这个owner相应ACL/policy就无法正常读取；不能以关闭RLS或授BYPASSRLS修复。实际依赖表清单须在正式实施计划固定，不为尚不存在的能力/许可表编造已实现关系。

采用管理拟用独立NOLOGIN管理角色和固定采用/撤销函数，先取得epoch写锁再追加材料、改变head及写审计；业务runtime无此角色和函数执行权。管理登录映射须等E01真实权威确认，当前不创建账号、不授人权限。校验回执由受控采用工具产生并由管理函数校验，不能由普通runtime伪造后激活。

### 5.2 拟新增固定函数

| 函数 | 输入、返回与限制 |
| --- | --- |
| `mt.task_create_plan_metadata(asset_uuid,case_uuid,scene,policy_version,modules[],priority)` | 返回唯一current revision的精确身份/三份材料摘要/状态/期限、可信正文校验回执及逐项必要能力的受限版本/当前状态事实；不返回完整正文。LOOKUP要求只读事务、createTask、asset及精确lookup_id、主体单位/案件成员一致；CASE核对本单位/案件及参数资产归属 |
| `mt.task_create_execution_plan(asset_uuid,case_uuid,scene,policy_version,modules[],priority,revision_id,expected_policy_sha256,expected_plan_sha256,expected_capability_sha256)` | 仅CASE/createTask；同时核对完整适用元组、唯一current revision_id及policy/plan/capability三份摘要，取精确获准正文/验证回执与能力事实，并持有必要动态行锁到提交。不能凭plan_id或相同plan hash读取另一个采用revision |

**Python与SQL职责分开：** PostgreSQL看不到Python ContextVar，现Database也没有target asset/request digest GUC，本方案不声称已有这些SQL事实。仅受控Python包装器调用：初始LOOKUP metadata包装器核验真实Principal、冻结请求、current_scope_transaction/current_data_scope确实为同连接只读的精确asset LOOKUP及createTask；不调用拒绝LOOKUP的require_root，也不要求尚未产生的ALLOW evidence。CASE metadata/正文包装器才先用require_root、授权evidence.target和冻结上下文核验同一actor/org/case/asset、createTask及A/B摘要；缺证据/错目标拒绝。两类函数参数均从该冻结对象取得。SQL独立核验既有transaction-local scope/operation/成员及参数资产确实属于同org/case，再按显式全部参数匹配采用记录；SQL不宣称自己验证了Python请求摘要或CASE evidence的目标资产。运行进程内任意代码执行仍不是此设计的防护边界；如以后要求数据库单独强制精确授权目标，须另行设计由Database从真实evidence设置的transaction-local target/request绑定及测试，不能暗示本方案已经具备。

两者均采用固定关系和参数化值，无动态表名/列名/SQL片段；函数SECURITY DEFINER固定`search_path=pg_catalog,mt,pg_temp`、限定无登录owner、撤销PUBLIC，并在同一迁移事务只向mt_runtime授EXECUTE。函数返回0份、重复有效映射、错误scope、无正文、摘要错或事实未知时拒绝，不降级为“默认计划”。本文的函数参数是接口设计，正式SQL类型/返回列由实施计划固定并测试。

### 5.3 撤销和锁顺序

现有0008 epoch触发器只覆盖组织/用户/identity/角色/权限/成员/cases，**未覆盖policy、计划、能力或source**。不能仅说“用了fence，所以所有撤销已原子化”。

推荐新采用/撤销管理通道先取得epoch写顺序，再更新head/追加依据；创建在同一数据库事务先由fence保持epoch共享锁。需要稳定的policy/映射/能力行保持共享锁到提交，失效变更与它们冲突；能力锁覆盖实际可变的model_registry、model_release及真实许可/handler发布状态源，不能只锁不可变manifest。普通handler的运行进程可达性仍可能在commit后变化，属于真实调度/执行失败处理，不宣称数据库锁能保持进程存活。资产/来源沿现有CASE读取持锁及版本复核。采用/撤销必须由唯一受控管理通道执行并审计，不能任意外部UPDATE绕过；若动态许可源在远端且无同库可信状态/租约，保持不支持，不填恒真。

**沿现有实际调用顺序：epoch → 资产/来源 → policy/映射/能力（固定排序）→ 幂等事务锁 → 新task/run/node写入。** fence.hold在service之前，现有CASE lookup会锁资产/来源，不能把幂等锁写成全链路第一个锁。需要以独立连接验证与T024来源更新、已有权限管理/恢复路径的锁兼容；不要在已有持共享epoch的普通业务UPDATE上盲加需要升级epoch的触发器。

READ COMMITTED下每次复核读取当前状态；仅FOR KEY SHARE不足以阻止非键授权字段更新，相关行采用FOR SHARE。死锁/锁等待/预算耗尽按现有事务错误归一回滚；不换幂等键“修复”未知结果，不在同一事务内无限重试。外部权威不能纳入上述锁序时，保持不支持严格原子撤销，另行评审有效租约协议。

## 6. 原子创建及幂等重放

拟新增`task_creation_service.py`，复用Database/ControlReceipts；以完整CASE根授权和同一connection执行。服务内采用嵌套savepoint，保证调用者即使捕获Python异常，也不会保留本批半写；根事务/fence失败仍回滚整个请求。

1. guard认证、功能权限和完整对象事实通过；冻结同一TaskCreate，校验单值幂等头与无额外query。
2. Database设置局部scope并执行fence.hold；服务核对operation、actor/org/case/asset、mutation和权限目标摘要，不接受任意合法Scope作为写权限。
3. 在上述锁序内，用ControlReceipts.replay取得既有事务advisory锁并查HTTP回执。control_ttl_seconds未明确配置时仍503，不在代码硬编码TTL。
4. 若有旧回执：核验它指向的原task/run/run_plan、同一A/B摘要和当前身份/案件/资产/来源权限；原revision必须仍是当前有效head且与本次proof精确一致。head已升级或撤销时拒绝，不重放、不改绑，也不重建任务；不增加旧revision授权入口，不用不可变历史行存在推导仍有效。已有回执与当前proof绑定不同用既有IDEMPOTENCY_CONFLICT/409；当前授权无可用映射时，guard可能先503，不能为读取receipt绕过初始权限。此当前授权约束须随D01明确审阅，与源卡同摘要重放要求一起保留，不把收紧行为当既有已批准实现。
5. 无旧回执：核对资产存在且VALID、同单位/案件，来源verified、用途含analysis且未到期，分类/对象版本可核实；精确解析采用记录、正文、实际必需能力和输入清单。
6. 同一savepoint/事务写analysis_task、task_run、task_run_plan、获准节点尝试、task_event、outbox_event、audit_event、idempotency_record。UUID只生成本次真实新对象；不得以upload_id充task_id。
7. 使用现有合法状态。拟从CREATED在同事务内转QUEUED并写相应事件；初始run=1、progress=0、report_eligibility='draft_only'，row_version按已有更新机制维护，missing_modalities只来自已核实输入。节点按真实依赖为READY/PENDING，不提前成功，空节点计划拒绝。analysis_task.result_version遵循现有正数结构，**没有结果时不插task_result，事件result_version为null**，不制造result_version=0。202或无模型计划不获得reviewable/formal_eligible资格。
8. 事件使用既有`workflow.run.accepted.v1`封套和同一event_id的task_event/outbox关联，先写run满足0015 FK。outbox只是持久化派发意图；现有上传outbox pump不能充当任务调度消费者。T036/T037真实派发/受信worker依赖另核验，创建事务不直接发MQ或调模型。
9. 预先校验Accepted和事件Schema、ETag/回执绑定；before_commit注册recheck_task_plan、正文/输入/能力及原绑定复核，随后Database执行fence.finish；全部通过才commit和202。
10. 任一正文读取、SQL、节点、事件、outbox、审计、回执、时钟、授权末检或commit异常均失败且无部分对象。commit已成功但HTTP响应丢失时，满足步骤4的当前授权及head条件才用同key/同body重放精确原回执，不另建任务。

HTTP幂等回执表是**idempotency_record**；event_receipt是消息消费去重，本请求没有消费消息时不伪造它。拟保存createTask专用内部receipt封装，包含原Accepted及原ETag/版本快照、task/run/plan绑定；对外仍只返回Accepted三字段。任务后续运行、取消等不会重建旧受理回执；当前状态从status_url另查。

## 7. HTTP与启动接线

| 项目 | 固定采用的现有契约 |
| --- | --- |
| 路由/operation/权限 | POST `/api/v1/analysis/tasks`／createTask／task.create |
| 请求body | 仅case_id、asset_id、scene、policy_version、modules、priority |
| 头/query | 单值Idempotency-Key 1—128；X-Request-Id按现有UUID语义；不新增If-Match要求，不接受额外query或重复幂等头 |
| 成功 | 202＋Accepted `{task_id,state,status_url}`；创建仅受理，不返回RUNNING/完成；status_url精确指向本任务既有状态入口；ETag及X-Request-Id按现有响应框架 |
| 缓存与问题响应 | 沿用no-store/no-cache/nosniff、固定Problem和trace/request ID，不泄露提供方地址、堆栈或跨案件对象 |

拟新增`task_creation_router.py`，采用SourceRegistration路由模式；main.create_app显式增加可选plan authority/事实口/正文读取依赖和创建服务，并由protected依赖保护、审计挂载路由。缺真实配置时503，不能装测试身份/fixture provider为业务默认。仅路由挂载、拒绝测试或OpenAPI显示不增加“可用创建功能”完成数；需依赖齐备的隔离真实事务202证据和正式输入分别验收。

沿用既有错误：未认证401；明确权限/来源用途拒绝403；未知或跨范围case/asset/source用404隐藏；已存在但非VALID为ASSET_STATE_CONFLICT/409；不同摘要/过期或损坏幂等绑定为IDEMPOTENCY_CONFLICT/409；非法body/头422；未知映射/分类/能力为CONDITIONAL_FACTS_UNAVAILABLE/503；重查变化AUTHORIZATION_CHANGED/503；数据库错误DATABASE_UNAVAILABLE/503；回执TTL未配置CONTROL_RECEIPT_TTL_UNCONFIRMED/503。不得新造TASK_PLAN_*公开错误或改变现有HTTP字段来简化实现。

## 8. 实施切分及验证矩阵（均未执行）

这是假定本设计获审阅后的实施切分，**不是已批准的逐步实施计划**；正式计划再固定函数返回类型、完整迁移DDL、每步RED/GREEN命令和提交边界。

| 切分 | 拟文件/交付 | 必须验证的重点 |
| --- | --- | --- |
| I01权威登记与规范材料 | 拟0016、内部execution-plan/capability-manifest Schema、正文校验及受控采用准备工具 | 空库/已有历史升级；不seed ACTIVE；摘要/重复映射/跨org FK/私有ACL/历史不回填；预算缺失拒绝 |
| I02受限事实和请求上下文 | scope_catalog、object_facts、拟task_creation_context/facts/provider、固定SQL函数 | exact operation/kind/id、LOOKUP只读、CASE同根、不同A/B摘要、analysis_purpose核心分支、分类未知拒绝、并发上下文隔离 |
| I03原子服务 | 拟task_creation_service、run_plan与receipt投影 | 正常受理；逐写入点故障及外层捕获仍全回滚；响应丢失精确重放；同key不同body/过期/损坏回执冲突 |
| I04HTTP接线 | 拟router、main依赖注入及挂载审计、相关生成目录 | 六字段/头/query严格性、Accepted三字段/原ETag、401/403/404/409/422/503、无默认provider、任务读取兼容 |
| I05完整适用回归与回执 | 任务卡/总导航/实际CI/三端源码证明 | 权限、范围、令牌、路由及业务DB回归串行；原失败探针/扫描；新commit对应CI；不继承本文件为实现完成 |

关键负例逐项保留：

1. 首轮lookup后撤销角色/成员、来源analysis用途/期限、资产VALID或分类授权；最终事务不能沿用旧事实。
2. 同版本名称但plan/policy/capability正文摘要改变、原证明过期或期限缩短、采用撤销、恢复generation改变；全部关闭。
3. 同key同请求并发只产一个完整集合；独立连接验证真实锁竞争，不能用size=1连接池串行假装并发证据。
4. 同key不同priority/modules顺序/policy/UUID字面大小写按既有body摘要区分；权限目标摘要另算，不能混用。
5. 缺正文、错摘要、无handler、模型未发布/许可不明、必需节点不可用及恶意正文路径均无创建成功或MQ发送。
6. 每个task/run/plan/node/event/outbox/audit/receipt写入点、响应/事件Schema及before_commit/fence失败均核验零半写。
7. 新只读SQL不可枚举全组织、越过case/asset读取，runtime不可直接SELECT私有表、继承owner或修改采用记录；测试临时schema遮蔽和PUBLIC权限。
8. 备份恢复后旧连接、旧权限epoch/数据库OID、旧采用缓存与旧proof不得使用；缺独立GenerationReader继续拒绝。
9. 原receipt指向运行中或已取消任务且原revision仍为当前head时，重放仍是同一受理事实；head升级则拒绝旧key且不再建任务。当前已撤销授权不能凭key取回对象信息。
10. 上下文在线程池传播、并发双用户/案件、异常退出和嵌套调用不串用；无上下文的内部调用不能绕过guard。

## 9. 待确认、待提供及采用门槛

| 编号 | 具体内容 | 推荐/当前状态；确认不包含什么 |
| --- | --- | --- |
| D01技术设计 | 是否同意“同库采用head/不可变revision＋受限函数＋同事务快照/撤销锁序”，第一批精确案件适用且head升级即拒绝旧revision重放 | 用户已认可。仅技术设计，不创建生效映射、不执行迁移/安装；明确不支持旧版本并行继续采用 |
| D02内部语义 | 是否同意Proof单个capability三元组指向实际采用的执行能力清单版本，新增内部Schema/登记；无模型计划须有显式证据并逐项核验实际handler | 用户已认可。不是批准任一真实模型、ID或软件版本，不把两项条件恒置True |
| D03下一批范围 | 设计审阅后先编制I01—I05正式实施计划，沿用当前会话逐项执行方式再行审阅 | 已授权编制且计划已准备，实施计划仍待审；本轮不实施产品代码 |
| E01真实权威 | 采用/撤销负责人、真实批准依据及保管/更新渠道 | 未提供；徐昌胜负责开发/复核不自动成为业务采用权威 |
| E02真实映射 | 精确policy_id/kind/version/hash、各scene/有序modules/priority适用、计划正文/身份、实际能力/发布/许可和适用案件范围 | 未提供；不代填ACTIVE行或默认DAG |
| E03业务/运行事实 | 分类与分析用途依据、真实身份/来源/恢复提供方；任务派发及实际非算法handler | 逐项核对，缺项拒绝。算法相关仍暂缓 |
| E04预算配置 | control_ttl_seconds、证明期限、最大计划字节/节点/能力数量和运行资源限制 | 尚无本批新增确认值；不得猜业务阈值。保留已有显式设置，不据本设计采用新值 |

本轮无需管理员执行命令，也不需要密码、Token、私钥或真实案件数据。可先完成设计审阅和实施计划；实际可用202、共享采用和正式验收必须分别满足以上输入及真实测试，不能用签字或文件存在代替。

## 10. 已核对的官方技术依据

以下为技术设计依据，不是项目业务批准。推荐方案是在官方机制上结合本仓库实际栅栏顺序作出的设计判断。

- PostgreSQL16 [行锁与事务级advisory锁](https://www.postgresql.org/docs/16/explicit-locking.html)：相关共享行锁与事务级锁持有至事务结束；锁顺序与死锁处理按实际双会话测试验证。
- PostgreSQL16 [SECURITY DEFINER和权限](https://www.postgresql.org/docs/16/sql-createfunction.html)：固定安全search_path、临时schema最后、撤销默认PUBLIC EXECUTE并同事务选择授权。
- PostgreSQL16 [行安全策略](https://www.postgresql.org/docs/16/ddl-rowsecurity.html)：新增表同时处理策略、ACL、owner和FORCE RLS，不能认为开启RLS就限制了特权账号。
- PostgreSQL16 [bytea摘要函数](https://www.postgresql.org/docs/16/functions-binarystring.html)：按规范字节计算sha256，避免将JSONB展示文本当作已有应用摘要算法。

本设计、输入源码摘要、资料核验、最新CI观察和源码同步以[本轮方案回执](../00-project/validation/t034-creation-integration-design-report.json)为准；代码内核证据仍见[上一批回执](../00-project/validation/t034-request-plan-binding-report.json)，不被本文件覆盖。
