# T014 六角色规则下一批隔离实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking. 沿用用户已选择的当前会话直接实施方式；不自动委派。

**Goal:** 把已确认的 PR01、PR02、PR04落实为可隔离验证的六角色规则、可信角色事实、对象条件、独立人员审批及撤销控制。保留现有42操作统一入口；31个未挂载操作随各自业务任务实现，不用空接口填数。

**Architecture:** 保留当前功能权限入口及案件/RLS/来源检查。新增完整角色事实读取、纯规则计算和业务对象条件检查，分开证明“有此功能资格”与“此对象允许此动作”。对写入使用同一事务内的事实重验及数据库授权变更栅栏；工作节点、幂等回放与制品交付重新核验。仅显式隔离装配启用候选规则，普通应用没有正式规则时继续拒绝。

**Tech Stack:** 既有 Linux、Miniforge Python3.10.22、FastAPI、SQLAlchemy/psycopg、PostgreSQL16、pytest、现有独立 Ruff/mypy 工具。原100包锁、Node锁和已存在0001—0006迁移不变；不创建Python候选、不新增策略平台。

**Spec:** [已确认的规则方案](../08-security/t014-six-role-rule-proposal.md)及[机器表](../08-security/t014-six-role-rule-proposal.json)，用户原话“认可作为下一批隔离实现输入”；源[T014](../../tasks/platform/T014.md)、[依赖复核](t014-dependency-and-scope-review.md)、[现有实现](t014-unified-permission-implementation.md)。2026-10-20形成新计划，用户明确回复“认可新计划，按P01—P07直接实施”，状态 **VERIFIED_P01_P07_ISOLATED_SCOPE_NOT_SHARED_ADOPTED**。此前五项[统一入口实施计划](t014-unified-permission-implementation-plan.md)原样保留；对规则输入的确认不冒充本计划审阅或共享采用。

2026-10-21后续核对：本计划P01—P07的原隔离完成记录保留；后续T015及前后端开发、当前CI与启动边界见[本批验证](../00-project/validation/development-continuation-report.json)。不把后续代码的CI状态倒写为原计划结论。


2026-10-21续批复核：已确认的PR01/PR02/PR04继续沿本计划P01—P07实施成果；当前默认拒绝前后端、会话代际、连接目标和历史派生输入修复见本批验证。下一项T016方案见[operation_token实施计划](t016-operation-token-implementation-plan.md)；该方案及T001—T123范围登记不代表后续任务已开发完成。

## Global Constraints

- PR01：六角色×41权限共246格，72格为带条件的候选功能来源、174格无角色授权来源；无角色授权的格不能生成ALLOW。兼任时按可信完整角色集合与职责冲突计算，不能由HTTP头任选角色。
- PR02：seal、report_export（含审计导出）、training_feedback、model_release要求2名独立人员；review、confirmation要求1名。排除申请者、材料提交者、执行者及模型评测签记者等适用冲突。两账号、两个subject乃至两个内部用户行都不能在缺人员关联依据时自动算两个人。
- PR04：候选审批TTL为1800秒，`now >= expires_at`失效；不得自动续期。无跨请求的正向决定缓存。撤销提交至后续新请求拒绝的候选最大时限5秒，记录最大观测值；现有master管理会话300秒保持。5秒不表示长计算线程必须在5秒内被杀死。
- PR03正式分类/用途映射未确定。内容动作缺所需分类、用途、委托或人员事实时拒绝；测试只能用明确标注的自建合成标签/人员/委托，不能录入正式种子。
- PR05共享策略采用、0006及后续迁移执行、维护窗口未批准；本轮仅源码与隔离数据库。PR06/T013真实本人交接、密钥保护与恢复仍独立未完成。
- 外部OpenAPI的73操作/41权限、请求响应字段、六种审批purpose保持；`model_release`是组织级且`case_id=null`。当前case-only适配器不支持时503，不伪造案件。新增端口/SQL为内部实现；需要修改外部契约时停止该项并提出差异。
- 401保留Bearer提示；已认证无功能资格403；对象越界沿现有404；必需规则/可信事实不可用503。错误不返回跨案件事实、令牌、密钥或完整SQL。
- 保留原权限、业务、认证、安全断言及CI门禁。综合联调、性能和正式验收可后置，但本批实现必需的正反例、迁移、故障与CI同时完成。测试计划条数不登记为通过数。
- 编写计划时170任务台账90条已验证子步骤、621条剩余工作、0项整任务验收；本计划不增加完成数。T001—T123的新批量开发授权按[范围与顺序](t001-t123-development-sequence.md)执行，T124及以后不自动实施。

## Review Focus

1. 仅按“当前权限匹配的角色”检查冲突会漏掉另一活动角色：P01/P02读取全部有效角色，即使其未绑定当前权限；反例断言冲突被拒绝。
2. 审批旧票、别名账号、同人两个内部用户行、事后改变执行人：P04按可信稳定人员ID、对象版本与当前适用关系重算；缺映射503，同人不得增加票数。
3. `policy.manage`跨kind、对象换case、组织模型发布借案件绕过：P03按服务端对象/策略kind/确切用途判定，反例无写入且组织级适配仍拒绝。
4. 入口检查后撤销与提交并发、旧游标/成功回执、排队后授权变更：P05使用数据库变更栅栏，P06重放/节点/交付复查；检查不得只放在HTTP入口。
5. 恢复/回切旧数据库或旧策略使撤销失效，以及时钟回退/查询故障：P05/P06要求独立恢复代际有效，未知拒绝；测时间边界和异常，不声称已解决T013真实恢复。

## 文件和接口边界

| 文件（计划位置） | 职责及上下游 |
| --- | --- |
| backend/business_app/permissions/rule_types.py | 以下内部不可变事实和决定类型；复用Principal、Actor、Scope，不改它们的现有字段 |
| backend/business_app/permissions/role_facts.py | RoleFactsReader/RoleDirectory，精确主体绑定、完整角色集合、规范摘要、事务内读取 |
| backend/business_migrations/0007_role_facts.sql | 新函数mt.lookup_role_facts；复用专用mt_permission_lookup，不增加表直读或目录管理权 |
| backend/business_app/permissions/six_role.py | 246格、兼任冲突、条件集合、TTL/批准人数的纯计算；不能把提案的runtime_allow=false直接改成生产ALLOW |
| backend/business_app/permissions/object_facts.py | 服务端对象解析及现有DAO/权威来源端口适配；未知人员/分类/委托显式不可用 |
| backend/business_app/permissions/conditional.py | 绑定操作、主体、对象、策略、角色和事实摘要；对象规则/提交前复查 |
| backend/business_app/permissions/duties.py | 独立人员和对象职责冲突；申请/批准/执行分离 |
| backend/business_migrations/0008_authorization_fence.sql | 新增授权变更代际/锁及相关触发器；不变更外部业务字段，无正式授权种子 |
| backend/business_app/permissions/fence.py | 与业务事务共用的授权重验及数据库栅栏 |
| backend/business_app/main.py、auth.py、controls/router.py、controls/common.py | 显式内部端口装配；在真实对象解析后调用条件检查，保留统一入口和现有AuthorityProvider |
| backend/business_app/controls/approvals.py、reviews.py、exports.py、execution.py | 适用职责分离、审批消费、节点和交付复查 |
| backend/business_app/uploads/service.py、worker.py、repository.py；history/router.py、repository.py | 上传/后台/历史列表/旧游标及回执适用检查；不重构无关业务 |
| tests/platform/test_t014_six_role.py；tests/business/test_t014_role_facts.py、test_t014_object_rules.py、test_t014_duties.py、test_t014_revocation.py | 下列新增正反例；原测试保留 |
| tests/business/conftest.py、t014_requests.py及原create_app测试调用处 | 只显式补齐测试端口和合成输入，禁止降低断言/默认全角色放行 |
| scripts/verify_t014_permissions.py、.github/workflows/ci.yml、config/stage-three-profile.json | 新测试和必要类型范围接入既有门禁，输出安全汇总 |

已只读确认上表既有文件及`backend/business_app/uploads/worker.py`存在；新文件是计划，不是已有成果。实施前再次检查其他工作流改动及新迁移编号是否被占用。

共用类型在P01/P03定义，后续任务仅复用：

- `ActiveRole(role_id: UUID, code: str, binding_id: UUID, binding_version: int, role_version: int, expires_at: float | None)`。
- `RoleFacts(principal: Principal, permission: str, eligible: bool, active_roles: tuple[ActiveRole, ...], permission_role_ids: tuple[UUID, ...], version_digest: str)`。完整活动角色与能提供当前功能的角色分列；空/未知不产生许可。
- `RoleFactsReader.read_roles(principal: Principal, permission: str, *, connection: Connection | None = None) -> RoleFacts`；传入connection时不得另开连接，否则提交前复查无法与事务锁绑定。
- `RuleTarget(org_id: UUID, kind: str, object_id: UUID | None, object_version: int | None, case_id: UUID | None, purpose: str | None, policy_kind: str | None)`。列表用明确的case_collection/policy_collection；本人身份用self；不借空对象绕过。
- `ConditionFacts(principal: Principal, target: RuleTarget, checks: Mapping[str, bool | None], version_digest: str, valid_until: int)`；仅由受信读取器构造，checks的键来自机器表条件定义，未取得的必需条件为None，不能默认True。
- `RuleSnapshot(version: str, sha256: str, recovery_generation: str, valid_until: int)`为外部显式提供的不可变规则快照身份；不能仅凭提案文件自称正式有效，缺有效装配即拒绝。
- `AuthorizationEvidence(principal: Principal, operation_id: str, target: RuleTarget, role_digest: str, condition_digest: str, policy_version: str, recovery_generation: str, valid_until: int)`只在请求/工作上下文短暂使用，不成为永久通行证。

### Task 1: P01 新增可信完整角色事实与增量读取

**Files:** 创建rule_types.py、role_facts.py、0007_role_facts.sql、test_t014_role_facts.py；仅按需要复用permissions/directory.py校验。保留0006及现有PermissionReader.read接口。

**Interfaces:** 消费Principal和Database；产出上述ActiveRole、RoleFacts、RoleFactsReader及`RoleDirectory(database: Database, *, clock: Callable[[], float])`。SQL `mt.lookup_role_facts(wanted_issuer text,wanted_subject text,expected_user uuid,expected_org uuid,wanted_permission text)`返回0006精确身份/权限事实及`active_roles jsonb`、`permission_role_ids jsonb`；全角色查询不得按wanted_permission过滤。该函数只授予专用lookup角色。事务内另用`mt.lookup_actor_role_facts(wanted_issuer text,wanted_subject text,wanted_permission text)`，仅授予mt_runtime且expected_user/org取已设置的mt.actor_id()/mt.org_id()；不让业务角色任意指定别人的主体，不把lookup角色成员权授给mt_runtime。两入口返回同结构，摘要绑定同一主体；事务入口不能设置整个业务事务为只读或另开lookup连接。

- [x] RED：新增`test_all_active_roles_include_nonmatching_permission_role`（无当前功能绑定的冲突角色仍出现在集合）、`test_role_facts_exact_principal_and_expiry`（issuer/subject/user/org任一失配或到期拒绝）、`test_role_lookup_is_function_only`（目录直读/写入/提权均拒绝）、`test_transaction_role_lookup_is_bound_to_session_actor`（同连接当前主体可读，替换subject/单位或未设上下文拒绝）。运行`python -m pytest tests/business/test_t014_role_facts.py -q`，先使用具名能力断言/数据库检查得到预期失败，再加入实现；不要以ImportError/测试收集失败代替功能RED。
- [x] 实现角色读取和规范摘要；按稳定ID排序，包含全部角色绑定、身份/用户/单位/权限版本和有效期；重复/未知结构、错误布尔/数值、超时均拒绝。复用专用非管理角色，PUBLIC无执行权，固定search_path，禁止新增任意表名SQL。
- [x] GREEN：同命令加`tests/business/test_migrations.py tests/business/test_t014_permissions.py`；实测空库、0006升级、事务失败回滚、旧记录及0001—0006摘要保全。随后提交本项代码/测试；共享数据库不迁移。

### Task 2: P02 246格纯规则计算与静态兼任

**Files:** 创建six_role.py、test_t014_six_role.py；消费P01类型；不改T011来源矩阵和原角色种子。

**Interfaces:** `SixRoleRules(snapshot: RuleSnapshot)`；`entry(facts: RoleFacts) -> tuple[str, ...]`返回候选条件分支，**不表示对象已获准**；同一分支的全部条件是AND，不同合法来源分支是OR，禁止拼接不同角色的半套条件。`approval_rule(purpose: str, version: str) -> ApprovalRule`复用现有类型。同文件`SixRoleEntryAuthority(reader: RoleFactsReader, rules: SixRoleRules)`实现既有`check(principal: Principal, permission: str) -> None`，只确认功能候选并重读摘要，P03仍必需。显式隔离工件从已确认机器表编译并绑定摘要，不由运行时任意读取用户路径。现有PermissionAuthority仍以None默认拒绝；新入口适配器不能免除后续条件检查。

- [x] RED：`test_all_246_cells_match_confirmed_input`断言6/41/246及72/174分布；`test_auditor_writer_combination_is_denied`、`test_nonmatching_role_still_triggers_conflict`、`test_unknown_or_unregistered_combination_is_denied`。单角色可候选；data_admin+case_investigator为本版显式兼任集合；其他多角色组合未经登记拒绝，不由UI切换忽略冲突角色。
- [x] 实现entry及用途规则；一个条件来源失败不能由另一无关角色放大，评估必须绑定具体条件分支。`development.login`永不因此获准；system_admin不获得案件内容或policy.manage万能许可。
- [x] GREEN：`python -m pytest tests/platform/test_t014_six_role.py -q`；断言六种purpose人数分别为1/2、TTL精确1800秒、未知purpose/版本503，数值不能从客户端覆盖。提交本项；这些为纯逻辑/合成事实测试，不记为246次真实HTTP通过。

### Task 3: P03 实际对象条件、策略kind与显式隔离装配

**Files:** 创建object_facts.py、conditional.py、test_t014_object_rules.py；修改main.py、auth.py、controls/router.py/common.py、history/router.py/repository.py、uploads/service.py/repository.py和实际受影响测试端口装配处。

**Interfaces:** 消费P01/P02；`ObjectFactsReader.read(principal: Principal, operation_id: str, target: RuleTarget, *, connection: Connection | None = None) -> ConditionFacts`；`ConditionalPermissionAuthority.authorize(principal: Principal, operation_id: str, target: RuleTarget, *, connection: Connection | None = None) -> AuthorizationEvidence`。`create_app`新增仅关键字内部端口`conditional_permissions: ConditionalPermissionAuthority | None = None`，所有条件依赖缺配置时503；旧AuthorityProvider的authenticate/authorize_case/authorize_source签名保持。

- [x] RED：`test_policy_manage_is_bound_to_exact_kind`断言retention仅数据管理员，threshold/analysis仅算法管理员，risk_taxonomy/review仅业务审核员；`test_object_case_cannot_be_replaced_by_request_case`精确404；`test_missing_classification_or_authoritative_purpose_is_unavailable`精确503且无成功回执/对象/outbox写入。
- [x] 实现RuleTarget/ConditionFacts/Evidence及服务端对象解析。逐个42操作使用现有资源查询解析真实org/case/owner/version；列表在SQL范围内过滤并校验分页/数量/游标，不能先搜全库后隐藏。SELF仅自身；OPS接口尚未挂载；来源仅元信息不含原件下载。导入/上传分别使用import/upload，分析/训练分别analysis/training；读取/下载用途没有权威映射时不可发明枚举或返回允许。
- [x] 对需人员、审计委托、复核分派、模型发布资格或分类标签且现有表/权威端口没有事实的条件，端口返回明确不可用；提供隔离合成适配器只在测试中装配。对已存在的SQL事实实现真实受限适配器；不将全True字典当生产适配器。
- [x] GREEN：上述文件及原42操作拒绝用例通过；追加`test_model_release_remains_org_scoped_and_unavailable_without_adapter`（case_id=null、不伪造case）、`test_no_new_unmounted_operation_is_claimed`（31仍单列）。快照装配仅用于隔离应用，普通默认配置不安装规则。提交本项，列出仍缺权威输入的每类条件。

### Task 4: P04 动态职责分离、独立人员与审批消费

**Files:** 创建duties.py、test_t014_duties.py；修改controls/approvals.py、reviews.py、exports.py，复用ApprovalRule及追加式审批记录。

**Interfaces:** `VerifiedPerson(actor: Actor, person_id: UUID, mapping_version: str, valid_until: int)`；`HumanIdentityReader.resolve(actor: Actor) -> VerifiedPerson`；`DutyFacts(applicant: UUID, submitters: frozenset[UUID], executors: frozenset[UUID], evaluators: frozenset[UUID], approved_people: frozenset[UUID], version_digest: str)`中的UUID均为person_id。`IndependentDuties.check(principal: Principal, target: RuleTarget, facts: DutyFacts, rule: ApprovalRule) -> None`。人员来源必须是显式可信映射；当前没有正式人员映射提供者，正式动作缺配置503，不自行把user_id或姓名当person_id。隔离夹具可为不同用户建立明确同人/异人映射。

- [x] RED：`test_two_subjects_or_two_users_for_same_person_count_once`、`test_applicant_submitter_executor_or_evaluator_cannot_approve`、`test_changed_executor_invalidates_approval_consumption`、`test_one_approval_cannot_satisfy_high_risk_rule`；已有申请者自批断言保留，票数不足不能写APPROVED。
- [x] 接入申请、决定、查询有效状态和消费路径；对当前对象关系和人员版本重新计算。历史票/原审批不删除；RETURNED/REJECTED/REVOKED/INVALIDATED均不能消费。对象/run/result/policy/制品摘要及用途继续精确绑定。未挂载的模型发布只测纯规则和默认拒绝，不补虚假成功适配器。
- [x] GREEN：`python -m pytest tests/business/test_t014_duties.py tests/business/test_controls.py -q`；追加`test_approval_expiry_at_1800_seconds_is_invalid`（1800秒边界失效、1799秒仅在其余条件全有效时可用）及无人员提供者503。提交本项；两个测试人员不登记为两名实际项目批准人。

### Task 5: P05 数据库撤销栅栏、提交前复查与恢复代际

**Files:** 创建0008_authorization_fence.sql、fence.py、test_t014_revocation.py；修改conditional.py及实际写入事务调用点。消费RoleFactsReader、ObjectFactsReader和Evidence。

**Interfaces:** `AuthorizationFence.hold(connection: Connection, evidence: AuthorizationEvidence | WorkAuthorizationEvidence) -> None`在业务事务内取得稳定授权代际共享锁，再在同一连接重读并核对全部所需事实/策略版本/代际；返回None才允许继续提交。WorkAuthorizationEvidence定义见P06，P05先测HTTP证据，P06再加入工作证据。0008新增单行`mt.authorization_epoch`（epoch正整数）及授权目录变更触发器；数据库角色/权限/身份/成员关系变更统一更新此行，写入方与撤销方在同一锁上排序。新窄函数`mt.hold_authorization_epoch()`固定search_path、撤销PUBLIC执行，mt_runtime仅获执行权，不获epoch表修改权；触发器以受控权限更新。不得让两个独立连接分别加锁/检查却称同事务。锁顺序固定为授权epoch→对象/审批行，所有调用遵守，反例检查死锁或超时安全拒绝。不改写0001—0007，不将新角色种子或正式制度塞入迁移。项目内全局锁方案仅为当前隔离研发候选，吞吐影响须实际测量后报告。

- [x] RED：双独立连接执行`test_revoke_committed_before_fence_blocks_business_commit`、`test_business_commit_before_revoke_is_ordered_and_audited`、`test_role_insert_conflict_cannot_bypass_fence`；分别固定事务顺序并断言授权撤销先提交时无业务成功副作用，不能只用sleep制造偶然通过。
- [x] 实现触发器覆盖身份/用户/单位/角色/权限/绑定/案件成员变更，新增/撤销均更新epoch；对象/来源行和业务版本仍在当前事务重验。受控部署规则快照变更也须参与同一代际控制；未配置规则代际来源503。锁等待/数据库故障拒绝并回滚，测试目标的超时预算显式配置，不悄悄写入正式值。
- [x] `recovery_generation`必须来自明确的恢复后新代际确认；仅恢复旧数据库/旧epoch不能自证有效，未知代际503。新增反例`test_restored_or_rolled_back_policy_does_not_reactivate_revoked_grant`、`test_clock_rollback_or_failed_fact_read_is_denied`。跨Keycloak与数据库不是同一原子事务，不声称外部身份撤销零竞态；按T013权威检查与候选时限分别验证。
- [x] GREEN：`python -m pytest tests/business/test_t014_revocation.py tests/business/test_migrations.py -q`；空库/0006→0007→0008/失败回滚/隔离备份恢复保全通过。提交本项。真实恢复代际、共享锁采用和容量结论仍待T013/PR05，不凭隔离测试关闭。

### Task 6: P06 工作节点、旧回执/游标、制品交付及5秒测量

**Files:** 修改backend/business_app/uploads/worker.py、controls/execution.py/exports.py、uploads/repository.py及history实际分页入口；扩展test_t014_revocation.py、test_t014_runtime.py、t014_requests.py。复用现有worker类，不新建平行实现。

**Interfaces:** P01的rule_types.py追加`ExecutionSubject(actor: Actor, identity_id: UUID, mapping_version: str, work_kind: str, work_id: UUID)`及`WorkRoleFacts(subject: ExecutionSubject, permission: str, eligible: bool, active_roles: tuple[ActiveRole, ...], permission_role_ids: tuple[UUID, ...], version_digest: str, valid_until: int)`。主体由数据库upload/task/audit_export作业与创建者关系解析，不接受队列自报授权集合。`RoleFactsReader.read_for_work(subject: ExecutionSubject, permission: str, *, connection: Connection | None = None) -> WorkRoleFacts`读取实时身份绑定，并验证数据库中精确作业关联；不能伪造一个未有JWT的Principal。`ConditionalPermissionAuthority.authorize_work(subject: ExecutionSubject, operation_id: str, target: RuleTarget, *, connection: Connection | None = None) -> WorkAuthorizationEvidence`，后者将HTTP Evidence中的principal替换为subject，其余绑定字段相同；P05复用同一栅栏。后台服务身份另验，不复用/存储用户Bearer；工作委托期限由可信事实提供、未知拒绝，不能拿最初HTTP的Evidence永久放行。

- [x] RED：`test_replay_and_cursor_are_denied_after_revocation`、`test_queued_job_revalidates_actor_identity_and_scope`、`test_node_finish_and_export_delivery_revalidate`；旧成功回执/已生成文件存在时仍拒绝，原失败/审计记录不删除。身份映射未知/重绑定也拒绝。
- [x] 接入每节点开始、结果写入前及下载交付前检查；长节点允许安全中止或丢弃未提交输出，不让撤销后的结果落业务库/成功回执。组织级/未挂载动作仍缺适配时503，不增加隐式后台旁路。
- [x] GREEN：在隔离实例执行`test_committed_revocation_rejects_new_requests_within_five_seconds`；记录撤销事务提交时刻、轮询单调时钟、首个稳定拒绝时刻及最大观测延迟，要求每个观测≤5秒且最终持续拒绝，不能用平均值/P95替代。数据库故障、identity/role/membership/permission变更、策略换版分别测；不把一次测量承诺为所有部署SLA。
- [x] 运行新增回归及原`tests/business/test_t014_runtime.py`；提交本项。跨机器时间和外部Keycloak故障另保留证据边界。

### Task 7: P07 42操作适用回归、CI和三端同步

**Files:** 修改verify_t014_permissions.py、CI及必要类型范围；更新测试设计、实施报告、T014任务卡、execution-status、分步导航及只含安全摘要的验证报告。

- [x] 按42操作逐项列当前条件、实际测试ID、结果及“不适用/缺权威输入/未实现”；246格逻辑测试与HTTP覆盖分开。新正例必须同时满足可信事实与对象条件；去掉任一条件的反例应失败且无副作用。31未挂载项目保持未实现。
- [x] 执行`python -m pytest tests/business tests/platform/test_t014.py tests/platform/test_t014_six_role.py tests/platform/test_t013_tokens.py -q --tb=short --junitxml PRIVATE_PATH`；执行现有format-check、lint、type-check、T011候选模型和适用身份回归。原32门禁、失败探针及CI依赖保留；新增门禁失败必须阻断通过。
- [x] 执行文档/阶段/输入/导航/排期漂移检查；复核12份原件、原锁、0001—0006摘要。仅有实际代码和通过证据的子范围可登记完成，缺正式规则/本人接管不关闭整卡。T001—T123逐批记录，T092对范围外T164的依赖不删除。
- [x] 明确逐项验收状态后提交开发分支；核对精确提交的托管CI及制品来源。源码同步Linux采用fast-forward，保留其他工作流及预存.idea文件；记录清单摘要及实际服务观察。源码同步不执行数据库迁移/重启/策略安装。

## 关闭范围、回退和后续入口

本批可关闭的是上述实际实现并测过的隔离规则子范围，不能关闭PR03/05/06、T013真实交接或T014整卡。正式许可、分类、人员/委托、外部服务事实缺失时继续拒绝；这不阻止独立纯逻辑与有事实依据的隔离实现。0007/0008采用前必须有同实例隔离恢复及可靠升级证据；共享回退不删除迁移或历史票，使用受控前向修复/新代际。新代码仍可回切到前一提交，但不回切为已撤销的授权决定。

计划自查：PR01对应P01—P03，PR02对应P02/P04，PR04对应P04—P06，门禁/导航对应P07；五个Review Focus均有具名反例。类型由前项定义后复用；纯规则、真实SQL/HTTP、合成权威事实、本人真实操作分别报告。未满足的人员、分类、组织级适配、恢复代际和共享采用均明示，未用TBD或文档存在性替代实现。P01—P07计划已获确认，沿用当前会话直接实施；各项实际进度与结果另登记，不因计划批准而视为完成。
