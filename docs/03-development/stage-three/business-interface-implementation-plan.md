# 首批真实业务接口与数据库 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立独立业务数据库/迁移与访问基础，实际实现上传续传和精确历史结果读取。

**Architecture:** 保留backend/app及既有5表PoC；新增backend/business_app，在独立PostgreSQL实例和私有对象命名空间运行。先建立事务/RLS和拒绝默认授权的服务边界，再实现上传账本/校验任务及不可变结果读取，最后运行真实HTTP+数据库检查。

**Tech Stack:** 既有py310精确锁中的FastAPI、SQLAlchemy、psycopg、boto3、jsonschema、Celery及PostgreSQL16；首批不新增运行依赖或真实模型。

**Spec:** [已认可的设计范围](../development-environment-change-request.md)、[上传及其他缺口台账](../../03-api/interface-gap-register.md)、[历史读取协议](../../03-api/historical-result-reading.md)。以下具体字段/版本方案为本计划待审阅内容，尚未修改业务契约或实现代码。

## Global Constraints

- 原PoC/100包锁/合成M15/来源原件不改；新业务部署用独立Compose项目、数据库、卷及对象前缀。
- 现有候选62业务表/824字段是设计源，不是已运行数据库；只初始化空的独立目标，现有库不得直接执行initial-schema.sql。
- 未配置权威身份/来源提供方时相关业务请求503；无有效凭证401；案件不可见对象404。正式数据不得使用测试身份/来源夹具。
- 历史授权取当前有效权限/用途，不沿用旧快照的批准；精确版本不存在404，禁止回退最新。
- 不关闭IF-G07/08/11/13，不声称62表DAO全部实现、34能力或完整业务DAG已完成。
- 共享Docker数据卷达到容量保护条件前，不在当前共享引擎建立/重建新栈；可用托管隔离Runner验证。

## Review Focus

- 并发和网络中断：同分片相同摘要幂等，冲突409；数据库提交失败不能伪造已接收（任务3）。
- 重复或过期校验任务：重复消费不重复建资产，旧会话版本不能覆盖终态（任务4）。
- 当前授权被撤销：续传/校验/历史读取重新授权，拒绝后不泄露对象（任务2、4、6）。
- 历史混合版本：完整history组、路径对象、ranking及响应版本头一致（任务5、6）。
- 迁移恢复：中途失败/摘要漂移/已有未登记schema拒绝继续，独立恢复目标对账（任务1、7）。

## 文件和边界

| 新建/修改文件 | 责任 |
| --- | --- |
| backend/business_app/types.py、errors.py、settings.py、main.py | 共享类型/错误、显式业务配置、独立app工厂 |
| backend/business_app/auth.py、db.py | 权威提供方边界、当前案件授权、事务RLS上下文 |
| backend/business_migrations/0001_business_baseline.sql、0002_upload_result.sql、runner.py | 原824字段快照、追加字段迁移、独立账本/摘要/事务 |
| backend/business_app/objects.py | 固定对象版本和摘要；私有存储适配 |
| backend/business_app/uploads/{repository,service,router,validator,worker}.py | 分片账本、续传HTTP、真实异步校验 |
| backend/business_app/history/{repository,projection,router}.py | 不可变结果写入边界、精确选择及7操作投影 |
| tests/business/conftest.py、test_migrations.py、test_authorization.py、test_uploads.py、test_upload_validation.py、test_history.py | 隔离真实DB/对象/HTTP；测试身份禁止部署 |
| deploy/business-compose.yaml、scripts/verify_business_foundation.py | 独立研发栈和验证入口，沿用精确镜像摘要 |
| docs/03-api/openapi.yaml及既有操作索引/样例/注解、schemas、生成类型 | 唯一契约源、派生内容及任务对应 |
| docs/04-database/initial-schema.sql、table-catalog.json、data-dictionary.md及既有来源映射 | 追加字段与迁移一致，明确来源和执行状态 |

实施时先核对既有文件与生成入口；以上新包未创建。backend/pyproject.toml仍保留PoC发行名，新增包打包策略在任务2明确，不把app入口替换为业务入口。

## 首批固定接口及类型

共享`types.py`定义：`Actor(user_id: UUID, org_id: UUID)`；`Scope(actor: Actor, case_id: UUID)`；`JsonValue`为JSON标量/list/dict递归联合；`ObjectRef(object_id: UUID, version_id: str, sha256: str)`；`ResultKey(task_id: UUID, run_version: int, result_version: int)`。`errors.py`定义带code/http_status的`BusinessError`，禁止异常回显凭据/SQL/文件路径。

`auth.py`定义`AuthorityProvider` Protocol：`authenticate(bearer: str) -> Actor`、`authorize_case(actor: Actor, case_id: UUID, action: str) -> Scope`、`authorize_source(scope: Scope, source_id: UUID, purpose: str) -> None`。生产实现须来自实际协议，本批仅建立拒绝默认值及依赖注入；fixtures仅由测试conftest传入，app工厂不接受环境开关启用假身份。

`db.py`：`Database.transaction(scope: Scope) -> ContextManager[sqlalchemy.Connection]`，参数化SET LOCAL actor/org；`objects.py`：`ObjectStore.put_part(scope: Scope, upload_id: UUID, part_no: int, body: BinaryIO) -> StoredObject`、`read(ref: ObjectRef) -> Iterator[bytes]`；`StoredObject(ref: ObjectRef, size_bytes: int)`。适配器不得返回存储密钥/永久URL；固定对象版本必须与真实存储能力一致，无法核验版本/摘要则失败。

上传新增GET `/uploads/{id}`（operationId=getUploadStatus）和GET `/uploads/{id}/parts`（listUploadParts），服务根仍`/api/v1`。原3个操作保持createUpload=201、putUploadPart=200、completeUpload=202。候选操作由53增至55，仅在任务3实施后更新计数和派生物。

待审阅`UploadStatus`：`session: UploadSession`、`result: UploadResult|null`、`received_parts_count: integer>=0`、`received_bytes: integer>=0`、`total_size_bytes: integer>=1`；禁止额外字段。UPLOADING/EXPIRED的result为null；VALIDATING的asset_id为null；REJECTED不产生有效资产；COMPLETED对应VALID且asset_id存在。请求ID由当前请求生成/核验，幂等重放保留原受理响应。

listUploadParts返回`items: UploadPart[]`、`next_cursor: string|null`、`session_version: integer>=1`；按part_no升序，每页limit=1..100（默认100，研发分页参数，不是生产并发指标）。游标绑定会话及row_version，变动后409要求重读；游标仅从服务端签名，密钥放私有运行配置。

稳定duplicate_of需要给mt.upload_session追加可空UUID及同案件media_asset外键，并同步来源/SQL/字典/目录：候选62表824字段→62表825字段。原0001必须保存当前824字段源和实际SHA，0002追加该列；不能把更新后的825字段初始化SQL重新当作0001。

### Task 1: 独立迁移和数据库隔离

**Files:** 新建business_migrations三文件、deploy/business-compose.yaml、tests/business/conftest.py、test_migrations.py；更新数据库迁移说明。

**Interfaces:** `runner.py`产出`apply_migrations(dsn: str, directory: Path) -> list[str]`；迁移账本为mt_meta.schema_migrations（version、sha256、applied_at），独立执行元数据不算新增业务表。

- [ ] **Step 1: 写失败测试。** `test_empty_database_migrates_and_replay_noops`第一次应登记0001/0002、第二次无新增；`test_changed_migration_digest_rejected`改字节后拒绝；`test_untracked_existing_mt_schema_rejected`拒绝无账本旧schema；`test_mid_migration_failure_is_atomic`验证事务无半完成结构。conftest只创建随机隔离测试库并用显式管理员URL，不访问PoC库。
- [ ] **Step 2:** 跑`python -m pytest tests/business/test_migrations.py -q`确认FAIL；记录当前824字段源摘要，禁止从修改后的生成SQL回填历史迁移。
- [ ] **Step 3:** 实现账本、迁移摘要和事务锁；0001从当前SQL保留业务DDL/约束/RLS，去除外层BEGIN/COMMIT由runner管理；0002追加duplicate_of及FK。迁移权限与业务LOGIN分开，业务LOGIN为NOSUPERUSER/NOBYPASSRLS并受mt_runtime约束。
- [ ] **Step 4:** 在托管或获准独立PostgreSQL16验证真实重放/失败/漂移以及业务角色无迁移权限；核对62表825字段、原PoC5表未改。
- [ ] **Step 5:** 提交迁移及源摘要/说明，不提交私有DSN。

### Task 2: 独立app、真实事务与默认拒绝授权

**Files:** types.py、errors.py、settings.py、auth.py、db.py、main.py、test_authorization.py；修改打包声明包含app和business_app，不改变原PoC启动模块。

**Interfaces:** 定义上述共享类型/AuthorityProvider及Database.transaction；`main.py`产出`create_app(settings: BusinessSettings, authority: AuthorityProvider | None = None) -> FastAPI`。BusinessSettings含独立DSN、对象配置、明确研发限额/期限；缺项拒绝启动或503，不自动选择现有PoC数据源。

- [ ] **Step 1:** 写`test_no_authority_returns_503`、`test_invalid_token_returns_401`、`test_revoked_case_returns_404`和`test_RLS_context_does_not_leak_across_pool_reuse`；跨单位/跨案件直接SQL访问应读不到其他案件，事务退出后上下文不能残留。
- [ ] **Step 2:** 跑`python -m pytest tests/business/test_authorization.py -q`确认FAIL。
- [ ] **Step 3:** 实现app工厂/参数化事务、当前案件与来源动作校验；测试provider仅conftest注入。异常统一按OpenAPI Error返回，未知权威配置不建立第二权限源。
- [ ] **Step 4:** 重跑真实DB+HTTP授权检查，核对LOGIN不具有owner/superuser/BYPASSRLS；再跑原PoC检查确认启动兼容。
- [ ] **Step 5:** 提交共享基础；状态仍标权威身份平台未接入。

### Task 3: 分片账本、进度查询和续传HTTP

**Files:** objects.py、uploads/repository.py、service.py、router.py、test_uploads.py；修改OpenAPI、注解/样例/派生文件及数据库来源；更新所有硬编码53操作和824字段的检查/导航到准确新值，不放宽为“大于等于”。

**Interfaces:** `UploadRepository`产出`create(scope: Scope, payload: dict[str, JsonValue]) -> dict[str, JsonValue]`、`put_part(scope: Scope, upload_id: UUID, part_no: int, stored: StoredObject) -> dict[str, JsonValue]`、`status(scope: Scope, upload_id: UUID) -> dict[str, JsonValue]`、`parts(scope: Scope, upload_id: UUID, cursor: str | None, limit: int) -> dict[str, JsonValue]`。服务层每次调用先校验当前AuthorityProvider，再按唯一键与会话行锁提交。

- [ ] **Step 1:** 写`test_resume_after_client_disconnect`核对只重传缺失分片；`test_same_part_hash_is_idempotent`只有一行；`test_conflicting_part_is_409`旧分片保持；`test_expired_session_is_rejected`不能写；`test_DB_failure_does_not_report_received`不能出现账本成功；`test_cursor_bound_to_session_version`变动游标409；跨案件GET返回404、不泄露duplicate_of。
- [ ] **Step 2:** 跑`python -m pytest tests/business/test_uploads.py -q`确认FAIL，并对新增两个OpenAPI操作写正/反例契约检查。
- [ ] **Step 3:** 实现流式字节计数/摘要、私有版本对象、真实object_version和upload_part事务。part_no与大小受会话总大小/part_size约束，客户端sha不替代服务端重算；原文件名不拼本机路径。存储已写但DB失败的私有孤立对象记录恢复清单，不能误列已接收。
- [ ] **Step 4:** 在真实DB+支持固定版本的对象目标运行中断/冲突/到期/分页/权限检查；生成契约及TS类型并核对55操作，独立业务OpenAPI只发布实际挂载操作。
- [ ] **Step 5:** 提交端点、迁移/源映射和证据；只更新IF-G01“进度/分片已实现”子状态，终态尚依赖任务4。

### Task 4: 完成上传、校验任务和终态

**Files:** uploads/validator.py、worker.py、service.py、test_upload_validation.py；新建schemas/events/upload-validation.schema.json及独立路由/事件登记；复用业务outbox_event/idempotency_record，不改PoC事件。

**Interfaces:** `validator.py`产出`validate_upload(scope: Scope, upload_id: UUID, expected_version: int) -> dict[str, JsonValue]`；`worker.py`产出`consume_validation(event: dict[str, JsonValue]) -> None`。事件绑定org/case/upload/session_version/event_id/request_id，版本及Schema登记完成后才发送。

- [ ] **Step 1:** 写`test_complete_enqueues_once`断言同一事务VALIDATING+一个outbox；`test_missing_part_rejects_complete`、`test_full_digest_mismatch_rejects_asset`、`test_duplicate_event_does_not_duplicate_asset`、`test_stale_version_cannot_overwrite_terminal`、`test_source_revoked_before_validation`和`test_authority_outage_keeps_pending`。
- [ ] **Step 2:** 跑对应测试确认FAIL；明确开发limits/期限使用显式配置，不能把候选值当正式规则。
- [ ] **Step 3:** complete验证分片连续1..N/总大小/摘要声明，再提交outbox；独立发布器确认消息持久投递后置published_at，重复可接受。worker重算实际拼接字节的完整摘要、检测允许媒体并重核当前来源，写content_item/object_version/media_asset和会话终态事务。无权/无来源拒绝或保持不可执行，不生成VALID假成功；重复消费靠行锁/会话版本和幂等响应。
- [ ] **Step 4:** 跑真实消息+DB+对象终态检查，模拟提交前后中断/重复投递与权威暂不可用。任一不可核验对象版本、完整字节/摘要或格式条件时不能产出VALID。真实CPU解析成功不宣称模型检测准确率或生产病毒扫描完成。
- [ ] **Step 5:** 提交证据；只有任务3、4的HTTP/持久化/异常检查通过才关闭IF-G01所选实现范围，正式身份/来源条件另保留。

### Task 5: 不可变快照、版本选择与投影

**Files:** history/repository.py、projection.py、test_history.py；修改run-result.schema.json及对应生成类型/登记，保留v0.1原快照Schema为明确兼容来源；新建history snapshot mapping说明。

**Interfaces:** `ResultRepository.append_snapshot(scope: Scope, snapshot: dict[str, JsonValue]) -> ResultKey`、`load_exact(scope: Scope, key: ResultKey) -> dict[str, JsonValue]`、`load_latest(scope: Scope, operation_id: str, resource_id: UUID) -> tuple[ResultKey, dict[str, JsonValue]]`；`projection.py`产出`project(snapshot: dict[str, JsonValue], operation_id: str, resource_id: UUID, ranking_id: UUID | None = None) -> dict[str, JsonValue]`。

待审阅的写入Schema版本为`urn:media-trace:stage-one:run-result:0.2.0`：保留旧结构，增加`api_projections`数组，项为operation_id、resource_id(UUID)、response，响应逐一引用既有7个操作响应Schema。projection_refs中的json_pointer指向同一快照`/api_projections/N/response`，mapping_version登记为history-api-projection/1；这不是ObjectRef，也不改原模型response。旧0.1快照只经显式登记的已有payload映射读取，缺少可验证映射时报不可用，禁止现场拼造成功。

- [ ] **Step 1:** 写`test_two_runs_return_exact_old_snapshot`插入run1/result1与run2/result1并断言run1字节/摘要不变；`test_result_mutation_rejected_by_DB`拒绝UPDATE/DELETE/TRUNCATE；`test_missing_exact_version_is_404`；`test_invalid_projection_or_binding_rejected`拒绝操作Schema不符、指针越界、任务/路径绑定不符及ranking混合版本。
- [ ] **Step 2:** 跑历史测试确认FAIL；fixture的能力响应只标受控测试数据，不冒充真实模型执行证据。
- [ ] **Step 3:** 实现写入前Schema/对象引用/响应映射验证，将完整快照规范化JSON SHA-256和summary原子追加；规范化规定UTF-8、sort_keys=True、separators=(',', ':'),ensure_ascii=False,allow_nan=False，不允许NaN/Infinity。只读取既有append-only结果及同版本事实，不从可变最新字段覆盖历史响应。
- [ ] **Step 4:** 用真实DB验证不可变约束、两次重算、旧版本及0.1兼容拒绝行为；明确写入方法是持久化边界，尚不是完整DAG/34模型结果生产器。
- [ ] **Step 5:** 提交版本Schema、兼容登记及真实数据库证据。

### Task 6: 七个历史读取操作和现行授权

**Files:** history/router.py、test_history.py；修改历史协议说明、对应详细操作文件、独立app挂载和响应检查。

**Interfaces:** 消费任务2当前Scope及任务5ResultKey/project；7个已有operationId为getTask、getRiskFindings、getForensics、getTaskEvidence、getTimeline、getFirstSource、getPropagation，不新增历史路径。

- [ ] **Step 1:** 参数化7个操作写`test_history_group_must_be_complete`（半组、未知键、重复版本键→422）、`test_history_headers_match_snapshot`、`test_current_access_revoked_denies_old_result`、`test_path_and_ranking_must_match_result`、`test_omitted_history_preserves_latest_selection`和`test_no_snapshot_does_not_return_empty_success`。
- [ ] **Step 2:** 跑`python -m pytest tests/business/test_history.py -q`确认FAIL。
- [ ] **Step 3:** 实现扁平deepObject解析：任务路径history[run_version]/[result_version]成组；资产/簇/传播还需history[task_id]；按当前授权查询、精确绑定并设置X-Task-Id/X-Run-Version/X-Result-Version。省略history只按同案件/同路径实际快照选最新；无匹配404。
- [ ] **Step 4:** 对7条真实HTTP响应验证既有OpenAPI响应Schema和版本头；不能把空页/通用200或最新结果用作历史成功。读大型外置能力payload须固定对象版本/摘要核验，不省略缺失模态/未知区间。
- [ ] **Step 5:** 提交并关闭IF-G09所选读取实现范围，保持实际结果生产和正式身份平台的前置条件。

### Task 7: 批次回归、恢复与同步

**Files:** scripts/verify_business_foundation.py、CI专属业务验证步骤、文档状态/导航、迁移/接口报告与同步回执。

**Interfaces:** `verify_business_foundation.py`消费显式隔离运行配置；产出逐操作/迁移/RLS/对象/消息/历史/恢复的PASS/FAIL，未配置或前置不足记BLOCKED/NOT_RUN，不记PASS。

- [ ] **Step 1:** 写`test_verification_requires_isolated_target`、`test_failed_business_check_returns_nonzero`；实际测试库/Compose项目必须区别PoC，禁止缺配置时回退。
- [ ] **Step 2:** 实现统一验证并跑专项+既有契约/生成物/PoC回归；质量计划的Python类型检查应包含新业务包及测试。
- [ ] **Step 3:** 在全新隔离数据库冷迁移，再由同批备份恢复另一独立目标，对账上传账本、对象版本和两个历史快照；只核验本批数据，不称生产灾备。
- [ ] **Step 4:** 将本批检查接入真实GitHub CPU CI；保存提交SHA/锁/迁移摘要、通过及受控失败证据，不把原25门禁复用成新业务验收。
- [ ] **Step 5:** 按总体计划同步源码/文档到GitHub和Linux并核验摘要；未获容量/维护条件时Linux新栈部署标待实施，不能把源码同步当新栈已运行。

## 自检与缺口边界

共享类型和跨任务签名已明确；5类Review Focus分别有具体测试。IF-G01/09为首批，后续11项沿用总体计划的依赖顺序。新增55操作、825字段及快照0.2属于待审阅的具体变更；当前仓库仍为53/824/0.1，未提前改计数或关闭缺口。本计划不提供虚构身份平台、生产扫描、人员、日历排期或验收通过。

## 用户审阅决定

2026-10-14：用户明确回复“认可计划，由当前会话直接逐项实施（推荐）”。详细计划已认可，按当前会话直接实施；正文中的“待审阅”为编制时状态，具体完成情况仍按实测台账判定。此决定不批准共享引擎停机或正式生产冻结。
