# T015 数据范围访问控制实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking. 沿用已选择的当前会话直接实施方式；本文件仍需本人审阅，不自动委派或开始代码修改。

**Goal:** 为当前真实业务路径补齐服务器绑定的单位、案件、任务和对象访问范围，使遗漏DAO案件过滤、替换对象引用或复用旧上下文不能扩大已获准的访问。

**Architecture:** 复用T014认证、功能资格、对象事实、请求/工作证据和事务栅栏。新增内部不可变DataScope、明确的CASE／ORGANIZATION／LOOKUP事务、0010增量限制、统一集合筛选和对象访问入口；业务字节与数据库写入仍须经过完整授权。授权前仅查询精确最小元数据，授权后同一根事务持锁重验，防止“先有证据才能查询生成证据所需事实”的循环。

**Tech Stack:** 当前Linux、Miniforge Python3.10.22、FastAPI、SQLAlchemy/psycopg、PostgreSQL16、pytest和既有独立Ruff/mypy工具；保持原100包锁与当前Node锁。Python3.13／3.12候选继续暂缓。

**Spec:** [T015已获准书面设计](t015-data-scope-design.md)。本人原话“认可书面设计，编制实施计划”，所审阅版本SHA256为`600c07c45271d759a5e1e10ed0a7bbe748311b24dcb3cd4c09bd2165c84888a7`；批准记录见[设计审阅](../00-project/validation/t015-written-design-review.json)。原[T015](../../tasks/platform/T015.md)、[依赖实核](../00-project/validation/t015-dependency-preflight.json)和[负责人确认](../00-project/validation/t015-role-assignment.json)同时适用。**计划已获本人批准：认可P01—P07，按当前会话直接实施。P01—P07当前实际进度以逐项执行证据为准，不预填完成。**

## Global Constraints

- 原任务范围“按单位、案件、任务和密级过滤查询与写入”；契约“DataScope对象；repository查询约束”；验收“跨单位和跨案件访问被拒绝；管理员越权需显式授权”；测试“水平越权和批量查询测试”。源依赖仍为T014，不将其整卡未验收改成已验收。
- 仅当前Linux／Miniforge py310／CPU隔离研发。开发负责人、指定复核人均为徐昌胜；同人兼任不作为独立双人批准，工时和完成日期不编造。
- CASE固定一案件；ORGANIZATION只用于适用单位元数据和case_id为空的单位审计；LOOKUP仅精确、最小元数据及PostgreSQL只读事务，无业务内容出口。未知模式、零UUID案件、缺绑定均拒绝。
- 原Actor、Scope、ObjectRef、ResultKey及外部OpenAPI／模型Schema不改字段；新增类型是内部能力。73外部操作中当前42个已挂载、31个未挂载的区分保留；内部推理入口单列。
- 缺正式分类、用途、委托、人员、来源或工作信任事实时继续拒绝。正例使用明确合成适配器，不增加正式种子、全单位权限或管理员隐式绕过。
- 保留T014两名独立人员、高风险审批1800秒TTL、提交/交付重验、5秒事实刷新及恢复代际边界。5秒不改成长作业超时；不创建跨请求正向授权缓存。
- 新迁移暂定`0010_data_scope.sql`，实施前核对版本未被占用；不修改0001—0009，不增加业务表/字段，不改历史62表825字段原件。当前结构64表849字段与逐表实际CRUD覆盖分别记录。
- 保留原32项工程门禁、身份前置和全部安全断言；P06拟增加第33项T015门禁。下文测试名称、数量和命令均为计划，不是已通过证据。
- 仅同步开发分支源码；不合并main，不安装共享迁移/策略，不重启、不停写、不处理真实数据或秘密。T013真实恢复/退役、N01软件准入及T092→T164外部任务依赖保留。

## Review Focus

1. 用户同时合法属于A/B案件，DAO漏WHERE或JOIN仅按UUID：P02/P03必须证明A根范围不能读写B，而不是只测试完全无成员资格者。
2. 授权前事实查询依赖尚未生成的证据，或LOOKUP内调用FOR SHARE：P02必须证明真实正向认证链可启动、LOOKUP只读且不持授权共享锁，随后CASE重验不漏来源/版本。
3. 审批/审计/操作令牌的case_id可空及单位游标零UUID占位：P02/P03逐表分类；单位操作不能误拒绝，也不能因null或占位开放案件表。
4. 对象read返回生成器，离开授权上下文才开始取字节，或取下一块前发生撤销：P04在底层读取前及适用流式检查点复查，拒绝后停止输出，不能承诺收回已发送字节。
5. FastAPI线程切换、异步请求交错、连接池复用及异常退出：P02/P05实测ContextVar传播和清理；下一请求不能继承上一主体、mode、case或task范围。

## 文件、接口及测试执行约定

以下新文件均为计划位置，尚未创建产品代码。

| 文件 | 单一职责／本计划任务 |
| --- | --- |
| `backend/business_app/data_scope.py` | P01不可变类型、验证和稳定证据绑定；不读数据库 |
| `backend/business_app/scope_catalog.py` | P01固定定位种类/投影及64表语义分类；不接受请求表名 |
| `backend/business_app/scope_context.py` | P02当前范围、嵌套缩小及根连接生命周期 |
| `backend/business_app/scope_lookup.py` | P02精确授权前元数据及工作信任校验；不输出业务payload |
| `backend/business_migrations/0010_data_scope.sql`、`backend/business_app/db.py` | P02增量RLS/受限函数与同连接事务绑定 |
| `backend/business_app/permissions/{guard,object_facts,conditional,context,work}.py` | P02复用原认证、事实构造和栅栏；改为明确访问模式 |
| `backend/business_app/{auth,main}.py`、`controls/{common,router}.py`、`uploads/service.py`、`history/router.py` | P02真实HTTP/后台及对象定位接入；不改公开参数 |
| `backend/business_app/scope_collections.py` | P03任务/版本绑定及逐对象集合允许ID |
| `uploads/repository.py`、`history/repository.py`、`controls/{approvals,reviews,exports,execution,imports}.py` | P03逐DAO关联、分页/计数/游标范围，P04受控字节访问 |
| `backend/business_app/scoped_objects.py` | P04统一对象与业务绑定验证、流生命周期 |
| `backend/business_app/{objects,inference}.py`、`uploads/{service,worker}.py` | P04对象写入/读取、工作及孤儿记录适配；低层协议不变 |
| `tests/platform/test_t015_data_scope.py`、`tests/business/test_t015_{scope_sql,scope_http,collections,scoped_objects,scope_recovery}.py` | P01—P05具名测试；精确文件在对应任务列出 |
| `tests/business/{http_fixtures,conftest}.py` | 显式合成证据/权威夹具，绝不自动给生产入口ALLOW |
| `scripts/verify_t015_scope.py`、`tests/platform/test_t015_gate.py` | P06真实必需用例、报告和故障门禁 |
| `scripts/run_ci.py`、`.github/workflows/ci.yml`、`config/stage-three-profile.json` | P06第33门禁、原类型/格式范围及托管运行 |
| `docs/04-database/data-scope-extension.md`、`docs/09-testing/t015-data-scope-coverage.{json,md}` | P05/P07新限制、实际DAO及未实现路径的分开记录 |
| `tasks/execution-status.json`、`tasks/platform/T015.md`及原生成导航 | P07实际成果/证据/剩余状态；原170任务不变 |

表内省略前缀的产品路径均位于`backend/business_app/`。P02已有测试直接调用事务的适配位置已定位为`tests/business/test_authorization.py`、`test_history.py`、`test_identity_directory.py`、`test_role_directory.py`、`test_t014_object_rules.py`、`test_t014_revocation.py`、`test_t014_role_facts.py`；只有显式合成上下文适配，不删除原断言。

新内部类型与跨任务接口：

- `AccessMode(str, Enum)`：值固定`CASE`、`ORGANIZATION`、`LOOKUP`。
- `LookupKey(kind: str, identifier: UUID)`；kind只可来自固定目录。
- `TaskBinding(task_id: UUID, run_version: int | None = None, result_version: int | None = None)`：有result必须有run；已提供版本为正整数，bool不当int。
- `DataScope(actor: Actor, mode: AccessMode, operation_id: str, case_id: UUID | None, lookup: LookupKey | None, task_binding: TaskBinding | None, evidence_binding: str | None)`；frozen，不保存Bearer、任意权限集合或客户端密级。
- `ResourceBinding(kind: str, identifier: UUID, row_version: int | None = None, task: TaskBinding | None = None, part_no: int | None = None)`：服务器定位的实际业务资源；upload_part的identifier为upload_id，part_no必填；不是客户端授权声明。
- `LookupSpec(table: str, key: str, projection: tuple[str, ...], operation_ids: frozenset[str])`和`TableScopeRule(table: str, scope_class: Literal["CASE", "ORG", "DIRECTORY", "MIXED", "INTERNAL"], runtime_select: bool, lookup_kinds: tuple[str, ...])`：固定目录项，读权限标记不是全CRUD证明。
- `ScopeMetadata(target: RuleTarget, projection: Mapping[str, JsonValue], condition_checks: Mapping[str, bool | None], version_digest: str, valid_until: float)`：projection仅固定目录允许列；同一目标的相关事实在同一规范版本摘要中绑定，不放业务payload。
- `from_evidence(evidence: Evidence, *, clock: Callable[[], float] = time.time) -> DataScope`：消费现有HTTP/工作证据，按真实target产生CASE或ORGANIZATION；稳定摘要绑定主体/映射、operation、target、策略和恢复代际，独立核验新鲜度，不把confirmed_at/valid_until每次刷新当身份变更。
- `current_data_scope() -> DataScope | None`与`bind_data_scope(scope: DataScope) -> AbstractContextManager[None]`：P02实现；不能替代当前T014证据校验。
- `Database.scoped_transaction(scope: DataScope) -> AbstractContextManager[Connection]`：P02实现；保留`transaction(Scope)`、`identity_transaction(Actor)`签名，适用生产调用从当前T014证据派生和核对DataScope，缺证据拒绝业务访问。
- `SqlScopeLookup(database: Database, *, work_trust: WorkTrust | None = None)`及其`read(subject: Principal | ExecutionSubject, operation_id: str, key: LookupKey) -> ScopeMetadata`：P02实现。缺工作信任继续拒绝；不返回任意行JSON、内容、凭据或文件字节。
- `bind_task_scope(connection: Connection, scope: DataScope, task: TaskBinding) -> DataScope`、`CollectionScope.allowed_ids(connection: Connection, scope: DataScope, candidates: tuple[ResourceBinding, ...]) -> tuple[UUID, ...]`：P03实现；不切换operation或扩大案件范围。
- `ScopedObjects(store: ObjectStore, authority: AuthorityProvider | None)`及其`read(connection: Connection, scope: DataScope, binding: ResourceBinding, ref: ObjectRef) -> Iterator[bytes]`：P04实现；业务绑定查询使用传入同一连接，复用当前T014证据/栅栏和来源authority，先核对再调用底层read。

测试均在私有快照和自建隔离PostgreSQL中运行。后续命令里的`python`固定解析为`/opt/conda/glwy/envs/py310/bin/python`；`PYTHONPATH`为该快照的`backend`和仓库根。SQL/RabbitMQ目标由既有隔离测试配置读取，不在计划、Git或命令行复制DSN。启动前校验`MT_BUSINESS_TEST_ADMIN_DSN`、`MT_BUSINESS_TEST_BROKER_URL`及`MT_BUSINESS_PG_BIN`均指向已明确测试实例，拒绝PoC/共享库回退。格式和类型用已有`python scripts/dev.py`入口，不向原100包锁安装新工具。

### Task 1: P01 不可变范围、稳定绑定和固定目录

**Files:** 创建`backend/business_app/data_scope.py`、`scope_catalog.py`和`tests/platform/test_t015_data_scope.py`；只复用原`types.py`、`permissions/context.py`、`rule_types.py`及现有操作目录。

**Interfaces:** 消费原`Actor/Scope/ResultKey/RuleTarget/Evidence`；产出上文AccessMode、LookupKey、TaskBinding、DataScope、ResourceBinding、`from_evidence`。目录暴露`lookup_spec(kind: str) -> LookupSpec`和不可变`TABLE_SCOPES`；`LookupSpec`固定table/key、最小projection及适用operation_ids。

- [ ] **1. RED测试。** 编写`test_case_requires_exact_nonzero_case_and_actor`、`test_org_and_lookup_cannot_carry_case_or_task`、`test_unknown_mode_kind_operation_and_boolean_versions_are_rejected`、`test_evidence_renewal_preserves_binding_but_scope_change_does_not`。逐项断言case/org/operation/target替换改变绑定，纯新鲜度刷新不改变稳定身份，过期证据仍拒绝。测试“CASE构造成功不代表业务已授权”，P02还须当前T014证据。
- [ ] **2. 验证RED。** `python -m pytest tests/platform/test_t015_data_scope.py -q`；测试应在明确能力断言失败，不能以导入/收集错误作为RED。新模块未存在时先写对应`importlib.util.find_spec`能力断言，再导入待测类型。
- [ ] **3. 实现类型和目录。** frozen字段、严格UUID/枚举/整数/摘要检查；CASE不得带lookup，ORG不得带case/lookup/task，LOOKUP必须有key且不能带task。目录从已核对RESOURCES的14种实际定位种类开始，`operation`仍精确定位cases；新增使用点必须在同一目录显式登记，禁止任意表/列插值。
- [ ] **4. 分类检查。** `TABLE_SCOPES`逐项登记当前64表，分案件业务、单位业务、目录、可空案件混合表、无runtime直权内部表。`approval_request/approval_decision/operation_token/audit_event`列为混合类；`authorization_epoch`不增加runtime直读；目录和单位表不可按有无case列机械分类。登记尚无实际DAO的表，不能填“CRUD已通过”。
- [ ] **5. GREEN及提交。** 上述命令与`python -m pytest tests/platform/test_t014_six_role.py tests/platform/test_t014_work_trust.py -q`通过，动态目录集合与源64表定义一致。只提交本项类型/目录/测试，保留未实施P02的状态。

### Task 2: P02 增量RLS、三种事务与真实权限链垂直接入

**Files:** 新增`0010_data_scope.sql`、`scope_context.py`、`scope_lookup.py`、`tests/business/test_t015_scope_sql.py`、`test_t015_scope_http.py`；修改上表db、权限事实/guard/work及实际定位辅助入口；显式适配列出的既有事务测试与夹具。迁移和应用绑定为一个交付，不能只安装SQL便宣布可运行。

**Interfaces:** 消费P01；产出`current_data_scope`、`bind_data_scope`、`Database.scoped_transaction`、`SqlScopeLookup.read`及固定ScopeMetadata。SQL增加`mt.scope_mode()`、`mt.scope_case_id()`、`mt.scope_allows_case(uuid)`、`mt.current_actor_case_ids()`和固定`mt.lookup_scope_metadata(text,uuid)`；最后一项只返回目录列出的元数据，禁止通用查询/任意投影。

- [ ] **1. RED反例。** 在同一单位给同一用户A/B两案件资格，A范围执行`SELECT ... FROM mt.analysis_task`不带WHERE仍只能得A；跨案件INSERT/UPDATE/关联返回0或明确拒绝。另测`test_lookup_is_readonly_exact_target_and_has_no_payload`、`test_pre_authorization_metadata_needs_no_prior_evidence_or_share_lock`、`test_organization_mode_cannot_read_case_payload`、`test_forged_scope_without_evidence_cannot_open_business_transaction`。保留合法上传/历史/审批/单位策略和当前用户目录正例。
- [ ] **2. 验证RED。** `python -m pytest tests/business/test_t015_scope_sql.py tests/business/test_t015_scope_http.py -q`。记录当前漏过滤会返回B或缺DataScope入口的具名失败；不得把数据库未配置、fixture失败或收集错误当安全反例。
- [ ] **3. 实现SQL与最小函数。** 事务局部键固定为`app.actor_id/app.org_id/app.scope_mode/app.case_id/app.operation_id/app.lookup_kind/app.lookup_id`。CASE按同org、精确case、原有效成员关系AND约束；ORG拒绝案件表并限定混合表case_id为空；LOOKUP限固定资源种类/ID。用`AS RESTRICTIVE`与既有策略AND，保留原FORCE/ACL/不可变约束；不增加宽ALLOW或runtime管理继承。缺/错模式、无效UUID和未知kind均不能返回业务行。单位表和目录仍保留最小原ACL，不开放一般案件查询。
- [ ] **4. 实现授权前元数据桥。** `SqlScopeLookup`核验现有Principal或当前WorkTrust，使用只读LOOKUP；HTTP功能资格仍先由原入口核验。固定函数限定当前actor/org、有效关系、kind和精确ID，owner、search_path、PUBLIC撤权及EXECUTE ACL实测；不新增任意SECURITY DEFINER能力。最小投影为目标org/case/id/row_version、owner/purpose/kind、适用task/asset/source关联、有效成员/来源版本及期限；不包含content、details、snapshot、claim_text、artifact字节或凭据。imports/reviews/clusters的关联事实仅取精确目标的必要ID/版本；不提供集合枚举。抽出原ObjectFactsReader的同一规范事实构造器：授权前只读与授权后CASE持锁版本产生一致的ConditionFacts语义，不复制两套判定。现有补充权威端口仍必需。
- [ ] **5. 实现同连接绑定。** `identity_transaction(actor)`在已有证据时派生CASE/ORG；`transaction(scope)`再核对actor/case。授权前定位改走专用lookup入口，普通无证据identity_transaction拒绝业务访问。LOOKUP没有栅栏FOR SHARE或写操作；成功定位之后，真实授权事务重新核对对象/来源/版本并hold/finish原栅栏。嵌套只复用相同根连接，可缩小同一CASE任务，禁止切actor/org/case/operation、CASE→ORG或授权后降级LOOKUP；异常/回滚/池复用清空全部ContextVar和局部设置。测试合成证据仅在tests显式绑定，生产不增加测试开关。
- [ ] **6. 接通合法单位和工作路径。** `getCurrentUser`通过`mt.current_actor_case_ids()`仅取本人有效案件ID，再逐项原case.read核验；不在ORG直接SELECT案件内容。单位策略/audit的case_id=null合法；单位游标零UUID仅保留原编码绑定，不生成CASE或成员关系。未适配的组织模型批准/发布仍503。uploads/history/common/object_facts的精确定位、后台WorkTrust及内部推理复用既有身份链，不用客户端Scope或伪造JWT代替。
- [ ] **7. GREEN及提交。** 运行上述两文件、`tests/business/test_authorization.py tests/business/test_identity_directory.py tests/business/test_role_directory.py tests/business/test_t014_permissions.py tests/business/test_t014_object_rules.py tests/business/test_t014_work.py`，再运行`python scripts/verify_business_foundation.py run`。所有实际用例0失败/错误/跳过，原断言保留；双案件和原42操作拒绝回归成功后提交本项。完整业务执行新结构，不向共享库迁移。

### Task 3: P03 DAO任务/版本与集合分页范围

**Files:** 创建`scope_collections.py`、`tests/business/test_t015_collections.py`；修改`controls/router.py`、`common.py`、`approvals.py`、`reviews.py`、`exports.py`、`execution.py`、`imports.py`、`uploads/repository.py`、`history/repository.py`及`permissions/conditional.py`中实际候选筛选适配。

**Interfaces:** 消费P01/P02和既有ConditionalPermissionAuthority；产出`bind_task_scope`和`CollectionScope.allowed_ids`。每个ResourceBinding包含服务器核对的kind/ID/版本/适用任务；集合端口沿用原operation的功能权限，不借另一个operation授权。

- [ ] **1. RED测试。** 编写`test_same_case_task_and_history_version_swap_is_denied`、`test_related_join_requires_org_case_task_and_result_version`、`test_item_filter_precedes_limit_count_and_cursor`、`test_explicitly_denied_items_are_excluded_unknown_facts_fail_request`、`test_empty_allowed_collection_is_valid`。示例：同case三个候选中第1项明确拒绝、后2项允许，limit=1时返回第1个允许项，total只含2个允许项，不能先LIMIT后得空页。未知权威事实断言503和无结果/游标，不悄悄当空允许。
- [ ] **2. 验证RED。** `python -m pytest tests/business/test_t015_collections.py -q`，得到任务/批量查询的实际失败；没有业务生产者的路径列未实现，不造成功快照。
- [ ] **3. 实现任务与关联约束。** `bind_task_scope`用同连接校验analysis_task/task_run/task_result及实际resource关系，固定case和适用run/result；只有task_id不代表已授权某个历史版本。逐DAO保留org/case及task/run/result/version关联，审批对象、复核输入、来源和导出不能替换为同case任意ID。数据库只承诺单位/案件范围，任务隔离由本绑定及具名DAO反例共同证明。
- [ ] **4. 实现逐对象集合过滤。** 同连接取范围内最小候选，调用原权威/分类/用途/来源检查，明确403/404排除、未知/故障503失败。允许ID固定后才在SQL中分页/计数/生成游标；返回/交付前复查选中对象和允许集合版本。case级允许不代表所有对象允许；旧游标不续权，合法格式和D02严格编码、secret不变。
- [ ] **5. GREEN及提交。** 上述测试与`tests/business/test_history.py tests/business/test_t014_indirect_reads.py tests/business/test_t014_duties.py`通过；新增`test_cursor_after_source_revocation_does_not_leak_count`、`test_org_policy_cursor_placeholder_never_sets_case_context`及管理员无显式案件资格反例。完整矩阵逐行记录真实SQL、HTTP与未挂载边界后提交。

### Task 4: P04 对象、上传分片与导出字节统一约束

**Files:** 创建`scoped_objects.py`、`tests/business/test_t015_scoped_objects.py`；修改`objects.py`、`uploads/{service,worker}.py`、`history/repository.py`、`inference.py`、`controls/{imports,reviews,exports}.py`的实际字节入口；低层ObjectStore协议保持。

**Interfaces:** 消费P01 ResourceBinding、P02当前根范围/栅栏及P03任务绑定；产出`ScopedObjects.read`。每类业务绑定使用固定查询，不能把任意ObjectRef解释为下载授权。

- [ ] **1. RED测试。** `test_cross_case_object_ref_is_denied_before_store_read`使用Spy断言read次数为0；`test_upload_part_binding_does_not_require_object_version_row`证明合法未完成分片可用；`test_export_checks_exact_artifact_version_size_expiry_and_approval`逐项替换均拒绝。另测`test_generator_started_after_scope_exit_is_denied`及`test_revocation_between_blocks_stops_remaining_output`，分开记录已发送字节与未发送字节。
- [ ] **2. 验证RED。** `python -m pytest tests/business/test_t015_scoped_objects.py -q`；底层Spy或实际文件反例失败，不以不存在模型生产者当实现成功。
- [ ] **3. 实现固定绑定。** 分片通过upload_session/upload_part的org/case/upload/part与摘要；媒体经media_asset/object_version及来源；历史经精确ResultKey和输入引用；导出经audit_export/artifact_ref/object_version、大小/期限/审批和既有Export.check；模型制品仅在已有真实任务/模型/结果关联可证时允许，缺提供者继续503。所有绑定在底层read前完成，同case也须精确资源关系。
- [ ] **4. 实现流与写入边界。** 迭代期必须仍有同一有效根范围；实际响应采用原有完整性语义，部分已发送的流不宣称可撤回。写对象前检查，发布数据库引用前复查；文件/DB回滚不原子时追加精确孤儿记录，不删证据、不假称未落任何临时字节。覆盖客户端断流、hash/size错误、提交撤销及读迭代异常；不得以跳过底层完整性检查解决流问题。
- [ ] **5. GREEN及提交。** 上述文件、原`tests/business/test_uploads.py`、`test_history.py`、`test_t014_indirect_reads.py`及实际imports/exports/inference相关回归通过；通过AST/具名调用清单核对全部业务字节入口，剩余低层直接read只可在ScopedObjects或低层存储测试，未实现路径明确列出。提交代码、测试和调用清单。

### Task 5: P05 故障、升级与真实隔离恢复

**Files:** 创建`tests/business/test_t015_scope_recovery.py`、`docs/04-database/data-scope-extension.md`；修改`tests/business/test_migrations.py`的最新结构断言与新结构安全边界，保留旧版本快照和原SQL摘要。

**Interfaces:** 消费P02迁移和事务、P03/P04实际DAO/对象；复用`apply_migrations(dsn, directory) -> list[str]`及现有隔离pg_dump/pg_restore工具，不新增共享安装器。

- [ ] **1. RED故障。** 编写`test_upgrade_from_0009_and_partial_failure_are_atomic`、`test_reapply_checks_exact_old_and_new_migration_digests`、`test_restored_scope_policies_acl_and_generation_are_not_bypassed`、`test_pool_and_thread_context_do_not_leak_scope_after_failure`。用受控变体破坏一个限制/清理或恢复代际时得到具名失败；原迁移失败断言不降低。
- [ ] **2. 验证RED。** `python -m pytest tests/business/test_t015_scope_recovery.py tests/business/test_migrations.py -q`，仅新建`mt_business_test_*`库和专用角色。拒绝默认库/PoC/共享目标；记录实际失败原因而非配置缺失。
- [ ] **3. 实现兼容和前向修复证据。** 测空库到0010、0009升级、重复执行、改摘要拒绝及中途异常整体回滚；按既有原子runner执行。新增显式`fresh_scope_database`测试夹具从template0建立专用测试库，不能在已自动套用0010的business_template上冒充0009升级。以非超级用户owner和NOSUPERUSER/NOBYPASSRLS runtime检验固定函数owner、继承、search_path、PUBLIC/EXECUTE ACL及RLS。真实隔离dump/restore后重验64表目录、运行角色ACL、A/B/C范围与T014恢复代际未知拒绝；不是只比较schema字符串。
- [ ] **4. 固定代码回切边界。** 旧版代码缺新范围应拒绝而非恢复宽权限；需要修复时仅新增前向迁移，不能编辑0010或删除RLS。隔离验证“新结构+旧代码拒绝”“新结构+新代码合法操作成功”。未经维护窗口和独立采用批准，不生成共享库回退/删除命令。
- [ ] **5. GREEN及提交。** 上述命令及`tests/business/test_t014_revocation.py`通过；真实恢复测试明确禁止复活旧代际。跨线程并发、数据库超时/异常、用户/单位/成员撤销、过期、时钟回退及池复用均实测，报告测量范围，不声称认证现场/容量SLA。提交测试、必要修复和增量字典。

### Task 6: P06 必需证据、故障探针及CI接入

**Files:** 创建`scripts/verify_t015_scope.py`、`tests/platform/test_t015_gate.py`；修改`scripts/run_ci.py`、`.github/workflows/ci.yml`、`config/stage-three-profile.json`。不改身份workflow前置条件、必需engineering名称或原32条命令/断言。

**Interfaces:** `verify_t015_scope.py run`执行T015实际具名子集并输出安全报告；`failure-probe`插入一个确定断言失败，只有JUnit为1失败/0错误/0跳过及退出1才判预期失败。报告校验器`validate_report(report: dict[str, object], *, expected_commit: str, expected_source: dict[str, str]) -> None`供独立解析负测使用；无环境或缺必需证据不返回PASS。

- [ ] **1. RED解析器。** 对缺一条S01—S09必需用例、重复名称、空JUnit、skip、移除一个64表目录行、把目录检查冒充DAO覆盖、错误commit/源码摘要及缺真实失败探针分别断言拒绝。`python -m pytest tests/platform/test_t015_gate.py -q`先观察具名失败。
- [ ] **2. 实现报告。** 固定必需节点ID和精确JUnit断言；分开保存64表目录检查、真实SQL/HTTP/对象操作、31未挂载及缺正式提供者。记录source_commit、source_sha256、测试组/totals、运行ID、profile和适用边界，不发布原始DSN/日志。复用原保密与源树状态检查，禁止靠预填PASS或测试名称文本存在过门。
- [ ] **3. 接入第33门禁。** 在run_ci的validate增加一次T015真实run，原32命令原样保留；托管workflow验证其实际失败探针并保存安全report。原业务全量已包含新业务用例，额外子集仅用于T015必需节点证明，不再增加另一份相同全量回归。把新verifier纳入已有lint/format/type范围。
- [ ] **4. 保留足够执行预算。** 现有已成功代码CI `39392614922`的engineering实际3426秒，原上限3600秒仅余174秒。拟随T015新门禁把engineering预算改为90分钟，身份45分钟不变；新verifier内部上限1800秒，仅对该新增run_ci命令使用该值，原命令600秒不变。该预算是执行资源，不降低测试断言、必要检查或错误处理；实际超时仍失败，报告实际耗时，不把90分钟当SLA。
- [ ] **5. GREEN及提交。** 解析器通过；`python scripts/verify_t015_scope.py run`得到当前真实必要测试0失败/错误/跳过，`failure-probe`真实退出1且独立核对JUnit；检查`.github`源门禁仍名engineering、身份必须先成功。提交verifier、测试及CI/profile，不把第33门禁的计划数量写成已运行结果。

### Task 7: P07 全量回归、证据与三端交付

**Files:** 当前T015增量字典/测试覆盖、任务卡/台账、阶段/剩余工作导航、README与现有输入候选/文件清单；新安全报告`docs/00-project/validation/t015-data-scope-report.json`、`t015-implementation-ci-report.json`。仅真实执行后创建通过报告。

**Interfaces:** 消费P01—P06产物及真实JUnit/CI制品；继续使用已有任务/导航生成器及精确Git blob清单。每份报告绑定实际测试源码，不用历史CI替代新提交CI。

- [ ] **1. 完整回归。** 在新隔离快照依次执行`python scripts/dev.py lint`、`format-check`、`type-check`，以及`python -m pytest tests/business tests/platform/test_t014.py tests/platform/test_t014_six_role.py tests/platform/test_t014_gate.py tests/platform/test_t014_work_trust.py tests/platform/test_t013_tokens.py tests/platform/test_t015_data_scope.py tests/platform/test_t015_gate.py -q`；这保留已执行1009项的全部原测试模块，新增数量从JUnit实数记录。再执行原T014 verifier、T015 verifier及各自实际失败探针；不得并行争用同一测试模板/管理实例。
- [ ] **2. 资料和契约检查。** `python scripts/validate_inputs.py`、`validate_database_contracts.py`、`validate_repository_docs.py`、`validate_documentation_completion.py`、`validate_stage_three.py`、`generate_task_progress.py --check`、`plan_project_schedule.py --check`、`generate_stage_three_docs.py --check`、`generate_remaining_work_navigation.py --check`、`generate_stage_status_navigation.py --check`。对照受保护12原件、原100包锁、OpenAPI/模型Schema、0001—0009原摘要，差异只允许本计划范围。
- [ ] **3. 逐项验收对照。** S01—S09对应具名case和源码；跨单位/跨案件、管理员显式授权、任务/版本/对象及批量查询列通过/失败/未验证。64表仅目录的项标目录检查，真实DAO/HTTP/字节读取另列；未挂载31、缺正式适配器、T013实际恢复与现场SLA保留。限定子范围通过不登记整项T015正式验收。
- [ ] **4. 本地提交和GitHub。** 审查修改清单、LF/摘要及`git diff --check`后普通提交开发分支；正常推送，不force、不合并main。取得该精确提交的Actions实际结果、33门禁/13运行检查、身份/业务/T014/T015报告、制品大小与平台SHA256；失败或未完成如实登记，不能引用上一提交成功冒充。
- [ ] **5. Linux源码与最终回执。** 确认服务器在预期旧HEAD、已跟踪文件干净且原7份.idea内容不变，再仅快进源码；逐文件核对交付清单/精确Git字节。无需共享服务重启或迁移。最终回执提交CI独立观察，避免为声明自身未来CI成功而无限追加提交；同样source同步不表示运行采用。
- [ ] **6. 任务登记和交接。** 将真实子范围成果、命令、计数、源码/证据、实际复核及未验证条件写回T015、总分步导航和T001—T123顺序。设计/计划批准不计已完成代码步骤；整卡关闭仍满足原依赖与适用外部条件。只提出下一满足依赖任务，不自动跨入未经计划审阅的T016代码。

## 设计覆盖、自查与执行决定

| 书面设计 | 计划实现和验证 |
| --- | --- |
| §1—3任务/现状/复用方案 | Global Constraints、P01及P07原验收对照 |
| §4—5三模式、授权链和同连接 | P01/P02；RF01、RF02、RF05具名反例 |
| §6增量RLS、64表/固定函数/ACL | P01/P02/P05；混合null与目录、非超级用户owner、真实升级恢复 |
| §7逐DAO、任务/版本及批量分类 | P03；允许集合先于页/数/游标，明确拒绝与未知分开 |
| §8对象、上传、导出、孤儿 | P04；Spy/真实字节及生成器生命周期 |
| §9错误与默认拒绝 | P02—P05；401/403/404/503原语义和无副作用/无内容泄漏 |
| §10 S01—S09 | P02 SQL/HTTP，P03任务/批量，P04对象，P05恢复/故障，P06真实必需节点 |
| §11类型/CI/证据 | P06/P07；32保留＋1新增，真实失败探针和精确摘要 |
| §12—14范围、回切、未决与审阅 | P05/P07及本节；共享采用另行决定 |

自查要求：接口名/参数以上文定义为准；P03/P04不直接构造客户端范围；授权前LOOKUP与授权后持锁事实投影语义一致；原件/公开契约/锁/旧迁移不变；所有步骤一个可核对动作。不存在以“适当检查”替代精确失败条件，也没有预填测试通过。计划只增加资料，不增加完成子步骤、账号或权限。

本人已明确回复“认可P01—P07，按当前会话直接实施”；仅按本计划的限定隔离范围实施，逐项保留TDD和实际验证证据。正式分类/用途和权威映射未提供时保持拒绝；本计划不要求现在提供秘密或重复A01—A07，T013实际备份恢复/退役另行准备。
