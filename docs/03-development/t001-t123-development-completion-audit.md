# T001—T123 开发完成度源码审计

2026-10-24工程续批：活动Python基线及原始审计记录按[迁移说明](python311-migration.md)区分。3ca42b6c的PR身份恢复就绪用例失败，正补严格管理就绪及安全诊断，见[T013复核](t013-admin-readiness.md)；新临时测试实例的完整业务2427项、权限1112项、范围131项、令牌187项、原失败探针及真实浏览器联调分别通过，原存储超时仍保留，新提交完整CI仍待。总导航依据实际回执更新，原123项审计及170项源任务的未完条件保留，本批不增加完成数。

审计日期：2026-10-21。范围为123张源任务卡；本报告仅新增审计材料，不代表整卡验收、真实模型达标或生产通过。逐文件摘要绑定审计时源码；共享目录后续实现须另复核。

已审计 **123** 项，声明代码完整 **0** 项。分类：{"SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE": 12, "PARTIAL_IMPLEMENTATION": 65, "CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN": 46}。这不是“123项没有代码”：基础工程已有源码及有限历史测试，其他任务有部分实现或契约/夹具。全部条款尚未逐条完成源码与实际执行证据闭环，因此不声称codingcomplete。

当前静态业务路由51/73，缺22。本轮补登记、受控下载及模型/评测列表，旧27项台账保留起点记录并增加当前状态。实际命令和失败修复见[本轮回执](../00-project/validation/t001-t123-resource-registry-report.json)。

原始只读审计未运行业务测试、数据库、Git或服务命令；其证据引用保持原适用范围。后续实际实现及运行结果单列在本轮回执，不回填成原审计已执行。原100包锁和Python候选保持原边界。

本轮后继复核：T021登记、T025/T030下载及页面、T052/T058只读列表已补代码和限定验证，仍有各卡源功能缺口。下面原批次项中对应功能仅代表完整范围；已实现部分以本段及当前机器审计为准。

新增两张官方CC0小样本已实际保存并解码；[公开研发数据说明](../07-datasets/public-development-data.md)记录许可、摘要、路径及Linux联网限制。T060读取页面见[实际回执](../00-project/validation/t060-readonly-ui-report.json)，全任务仍未关闭。

## 后续批次与尚缺范围

### B01_READINESS_SOURCE_DOWNLOAD_REGISTRY（优先级1；登记/下载/只读目录已完成限定子范围）

- health dependency readiness provider + permission guarded route (503 on missing infrastructure, no model health invention)
- downloadAsset immutable version/SHA/authorization/revocation/audit stream + asset UI
- createSource authoritative registration/idempotency/audit with source UI (client cannot self-attest authorization)
- listModels registry reads and getModelHealth factual provider; model UI; unknown capability stays unavailable

### B02_TASK_DAG_WORKER（优先级2）

- createTask idempotent task/run/outbox transaction
- versioned DAG resolver/scheduler with required/optional/missing modality
- worker lease/checkpoint/backoff/cancel/rerun and real progress producer
- task create/cancel/rerun/DAG UI

### B03_MEDIA_AND_MODEL_ADAPTERS（优先级3）

- safe metadata/ffprobe/derived media/frame/audio/subtitle workers
- OCR/ASR adapters and original coordinate/time mapping
- HTTP adapter/configurable test Mock; batch/health/circuit management
- registry write/evaluation/rollout/drift tools and model UI

### B04_ALGORITHM_AND_RESULTS_UI（优先级4）

- risk/forensics feature and adapter producers + evidence cards
- versioned retrieval/index/local matching/DTW/source mapping/cluster tools
- first-source feature/training/ranking and propagation producers
- claims/allowed evidence retrieval/grounded drafts/reports/sealing/feedback consumers
- risk/forensics/source/graph/review/report interactive pages

### B05_DATA_TRAINING_EVALUATION（优先级3）

- annotation quality tooling; split manifest generator; reproducible edits; hard negatives review
- train/evaluate CLI pipeline around existing reference metrics with immutable artifacts
- implement missing NDCG/relation and stratified metric protocols; never train on frozen test set

### B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD（优先级4）

- SAST/binary coverage and full new-flow security regressions
- LLM tool whitelist/evidence injection security harness
- full business telemetry/alerts and restore/PITR invariant harness
- 20/100 configurable load harness and frozen run manifests; actual runs await approved resources

## 前端流程与API映射

| 源任务 | 已有源码边界 | 待实现流程 |
|---|---|---|
| T022,T023,T024 | UploadView + api.ts/state.ts development PoC flow | Business identity/source/session upload mapping and full business upload E2E |
| T030 | 列表/详情与校验后受控下载 | 来源授权明细、血缘、真实后端组合E2E |
| T040 | TaskCatalogPanel/TasksView current nodes/events/history reads | createTask/cancel/rerun buttons, real refresh/progress/DAG/checkpoint |
| T018 | AuditView query/export transport | Contract-backed server full filters and real export/revocation audit E2E |
| T060 | /models模型/评测只读分页及129单元/36浏览器传输测试 | 真实健康、灰度/漂移、获批发布/回滚及真实后端组合E2E |
| T070,T078,T097,T101 | Backend persisted result projections; task UI textual reads | Result-specific risk/forensics/propagation/evidence original-media interaction |
| T103 | PendingReviews/Approvals/Tasks read interfaces | Draft/annotation/original-media localization/current-version review submission workflow |
| T107,T108 | getReport read and partial review controls | Report render/download/approval UI and authorized feedback pipeline |

## 123项逐项审计

每项列原名称、源验收、源码/有限测试、明确代码缺口和实际输入。JSON包含逐验收子句追踪、符号行号与文件摘要；所有子句状态保持UNVERIFIED_OR_PARTIAL，避免以通用表/Schema或模拟结果充当完整实现。

### T001 建立单仓库目录与基础README

源卡：[tasks/platform/T001.md](../../tasks/platform/T001.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：仓库结构与设计一致；README包含启动、测试、提交规范；不得包含真实密钥。

已观察源码/结构：`CONTRIBUTING.md`；`README.md`；`docs/00-project/server-sync-receipt.json`；`docs/02-architecture/repository-layout.md`；`docs/03-development/stage-three/foundation-closeout-implementation.md`

有限测试/历史报告：`docs/00-project/validation/repository-docs-validation.json`

剩余代码/核验：本次未定位明确新增代码缺口；逐条核验目录职责、启动/测试/提交入口和秘密检查，实际复核独立登记。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T002 配置Python后端工程

源卡：[tasks/platform/T002.md](../../tasks/platform/T002.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：服务可启动；缺少必要配置时给出明确错误；依赖版本锁定。

已观察源码/结构：`backend/app/main.py`；`backend/app/settings.py`；`backend/app/tracing.py`；`backend/business_app/development.py`；`backend/business_app/main.py`；`backend/business_app/settings.py`；`config/versions.yaml`；`docs/03-development/stage-three/foundation-closeout-implementation.md`；`docs/10-deployment/business-development-runbook.md`；`scripts/business_development.py`

有限测试/历史报告：`docs/00-project/validation/ci-all-report.json`；`docs/00-project/validation/development-continuation-report.json`；`docs/00-project/validation/stage-three-python-types-report.json`；`tests/business/test_development_startup.py`；`tests/stage_three/test_foundation_configuration.py`

剩余代码/核验：补业务应用health提供者与路由，依赖失败返回503；核对当前原生启动配置，不把PoC健康视为业务就绪。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

### T003 配置Vue前端工程

源卡：[tasks/frontend/T003.md](../../tasks/frontend/T003.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：开发服务器可启动；严格类型检查通过；API地址环境化。

已观察源码/结构：`docs/03-development/stage-three/foundation-closeout-implementation.md`；`frontend/package.json`；`frontend/src/App.vue`；`frontend/src/api.ts`；`frontend/src/main.ts`；`frontend/src/router.ts`；`frontend/src/state.ts`；`frontend/src/views/HealthView.vue`；`frontend/vite.config.ts`

有限测试/历史报告：`docs/00-project/validation/ci-all-report.json`；`frontend/e2e/foundation.pw.ts`

剩余代码/核验：基础Vue入口已存在；业务health接入单列T002/T004，复验环境化API和网关地址。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

### T004 建立本地容器开发环境

源卡：[tasks/platform/T004.md](../../tasks/platform/T004.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：一条命令启动；隔离数据卷和密钥；按获准项目配额设置CPU、内存、进程和临时盘限制，核对实际cgroup生效；不认定单机容器为生产高可用。

已观察源码/结构：`deploy/docker-compose.yml`；`docs/02-architecture/architecture-decisions/TB-ADR-004-object-storage.md`；`docs/03-development/native-linux-implementation-plan.md`；`docs/03-development/native-n01-admission-decisions.md`；`docs/03-development/native-n01-candidate-adoption-review.md`；`docs/03-development/native-n01-nested-license-use-review.md`；`scripts/verify_development_limits.py`

有限测试/历史报告：`docs/00-project/validation/ci-all-report.json`；`docs/00-project/validation/development-container-limits-report.json`；`docs/00-project/validation/native-binary-probe-report.json`；`docs/00-project/validation/native-build-package-verification-report.json`；`docs/00-project/validation/native-n01-admission-decisions/component-admission-review.json`；`docs/00-project/validation/native-n01-admission-decisions/component-scoped-admission-proposal.json`；`docs/00-project/validation/native-n01-admission-decisions/cve-wheel-regression-report.json`；`docs/00-project/validation/native-n01-admission-decisions/cve-wheel-review.json`；`docs/00-project/validation/native-n01-admission-decisions/decoder-boundary-review.json`；`docs/00-project/validation/native-n01-admission-decisions/eight-component-limited-review-decision.json`；`docs/00-project/validation/native-n01-admission-decisions/library-provider-notice-review.json`；`docs/00-project/validation/native-n01-admission-decisions/message-boundary-regression-proof.json`；`docs/00-project/validation/native-n01-admission-decisions/n01-plan-verification.json`；`docs/00-project/validation/native-n01-admission-decisions/nine-cve-disposition-review.json`；`docs/00-project/validation/native-n01-admission-decisions/publisher-notice-version-scope-review.json`；`docs/00-project/validation/native-n01-admission-decisions/runtime-package-notice-review.json`；`docs/00-project/validation/native-n01-admission-decisions/same-entity-internal-use-decision.json`；`docs/00-project/validation/native-n01-admission-decisions/software-admission-register.json`；`docs/00-project/validation/native-n01-admission-decisions/two-publisher-notice-review.json`；`docs/00-project/validation/native-n01-admission-decisions/upstream-contact-status.json`；`docs/00-project/validation/native-n01-round3-admission-report.json`；`docs/00-project/validation/native-n01-round4-admission-report.json`；`docs/00-project/validation/native-n01-round5-admission-report.json`；`docs/00-project/validation/native-n01-round6-admission-report.json`；`docs/00-project/validation/native-n01-round7-admission-report.json`；`docs/00-project/validation/native-n01-round8-admission-report.json`；`docs/00-project/validation/native-n01-round8/review-decision.json`；`docs/00-project/validation/native-n01-runtime-report.json`；`docs/00-project/validation/native-primary-artifact-verification-report.json`；`tests/stage_three/test_development_limits.py`

剩余代码/核验：现有容器/原生脚本存在；完整启动链与配额实际采用未追踪，不重复创建Python候选或改原100包锁。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

### T005 配置代码格式化与静态检查

源卡：[tasks/platform/T005.md](../../tasks/platform/T005.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：本地和CI命令一致；示例违规代码能被拦截。

已观察源码/结构：`.pre-commit-config.yaml`；`config/stage-three-profile.json`；`docs/03-development/stage-three/foundation-closeout-implementation.md`；`frontend/package.json`；`ruff.toml`；`scripts/dev.py`；`scripts/stage_three_quality.py`；`scripts/verify-frontend-quality.mjs`

有限测试/历史报告：`docs/00-project/validation/native-n01-runtime-report.json`；`docs/00-project/validation/stage-three-python-types-report.json`；`tests/stage_three/test_dev.py`

剩余代码/核验：本次未定位新增格式/类型门禁代码缺口；按同源入口复验新增代码及违规样例拦截。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T006 建立基础持续集成流水线

源卡：[tasks/platform/T006.md](../../tasks/platform/T006.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：任一门禁失败阻止合并；产出测试报告；缓存不影响正确性。

已观察源码/结构：`.github/workflows/ci.yml`

有限测试/历史报告：`docs/00-project/validation/ci-failure-gate-report.json`；`docs/00-project/validation/github-actions-report.json`；`docs/00-project/validation/main-protection-enforcement-report.json`；`docs/00-project/validation/main-protection-readback.json`

剩余代码/核验：流水线与合并门禁实现存在；平台绕过权限、Runner/Secret治理属于实际平台核验。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T007 建立统一配置和密钥规范

源卡：[tasks/platform/T007.md](../../tasks/platform/T007.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：仓库无真实密钥；敏感配置不写日志；启动时校验必需项。

已观察源码/结构：`.env.example`；`backend/app/settings.py`；`backend/business_app/settings.py`；`config/README.md`；`docs/03-development/stage-three/foundation-closeout-implementation.md`

有限测试/历史报告：`tests/stage_three/test_foundation_configuration.py`

剩余代码/核验：配置校验/秘密注入已有源码；本批新服务配置补齐必需项检查并核验敏感日志。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T008 建立统一日志与请求追踪

源卡：[tasks/platform/T008.md](../../tasks/platform/T008.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：所有API日志可关联请求；令牌、密码、原始敏感文本被过滤。

已观察源码/结构：`backend/app/observability.py`；`backend/app/tracing.py`；`backend/app/worker.py`；`backend/business_app/main.py`；`backend/business_app/uploads/messaging.py`；`docs/03-development/stage-three/foundation-closeout-implementation.md`

有限测试/历史报告：`docs/00-project/validation/ci-all-report.json`；`docs/00-project/validation/trace-regression-report.json`；`tests/business/test_upload_validation.py`；`tests/poc/test_event_contract.py`；`tests/stage_three/test_foundation_tracing.py`

剩余代码/核验：已有trace/脱敏实现；未来DAG跨进程消费者补传播上下文，新增路径均纳入脱敏回归。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T009 建立统一异常与错误码框架

源卡：[tasks/platform/T009.md](../../tasks/platform/T009.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：未知异常不泄露堆栈；已知异常映射稳定；错误码不可重复。

已观察源码/结构：`backend/app/main.py`；`backend/app/observability.py`；`backend/business_app/errors.py`；`backend/business_app/main.py`；`docs/03-development/stage-three/foundation-closeout-implementation.md`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_foundation_errors.py`；`tests/business/test_history_http.py`

剩余代码/核验：统一业务异常处理已有实现；新接口复用错误/请求ID/缓存策略，未知异常继续脱敏。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T010 建立架构决策记录和变更模板

源卡：[tasks/platform/T010.md](../../tasks/platform/T010.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：重要决策有状态、背景、方案、影响和回滚；模板可直接复用。

已观察源码/结构：`.github/PULL_REQUEST_TEMPLATE.md`；`docs/02-architecture/architecture-decisions/TB-ADR-002-backend-stack.md`；`docs/03-development/change-templates/database-change.md`；`docs/03-development/change-templates/model-change.md`；`docs/03-development/change-templates/requirement-change.md`；`docs/03-development/development-environment-change-request.md`；`docs/03-development/stage-three/foundation-closeout-implementation.md`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：ADR和变更模板已有；本次未发现需要新增应用代码的源验收条款，具体复核不能由模板代替。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T011 设计用户角色与数据范围模型

源卡：[tasks/platform/T011.md](../../tasks/platform/T011.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：覆盖管理员、数据管理员、算法管理员、审核员、核查人员和审计员；默认拒绝。

已观察源码/结构：`docs/03-development/t011-access-model-implementation.md`；`docs/03-development/t012-identity-relations-design.md`；`docs/04-database/identity-relations.md`；`docs/08-security/access-control-model.json`；`docs/08-security/access-control-model.md`；`docs/08-security/permission-matrix.md`；`schemas/security/access-control-model.schema.json`；`scripts/validate_access_control_model.py`；`tools/access_control_review.py`

有限测试/历史报告：`docs/00-project/validation/t011-access-model-report.json`；`docs/00-project/validation/t011-dependency-report.json`；`docs/00-project/validation/t012-identity-relations-report.json`；`tests/platform/test_t011.py`

剩余代码/核验：六角色/范围模型与校验工具已有；未获得正式ALLOW/分类用途细则时保持默认拒绝。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T012 实现用户角色数据库模型

源卡：[tasks/platform/T012.md](../../tasks/platform/T012.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：唯一约束、外键和软禁用正确；迁移升级可验证；可逆回退或不可逆恢复/前向修复方案齐全。

已观察源码/结构：`backend/business_app/identity/directory.py`；`backend/business_migrations/0001_business_baseline.sql`；`backend/business_migrations/0004_identity_relations.sql`；`backend/business_migrations/0005_role_catalog.sql`；`docs/04-database/identity-relations.md`；`docs/04-database/role-catalog-extension.json`；`docs/04-database/role-catalog-extension.md`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/t012-identity-relations-report.json`；`docs/00-project/validation/t012-role-model-report.json`；`tests/business/test_identity_directory.py`；`tests/business/test_migrations.py`；`tests/business/test_role_directory.py`

剩余代码/核验：角色身份表、约束和迁移已有；逐条追踪唯一/外键/软禁用与升级恢复证据，未定位具体新增模型缺口。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T013 实现认证与令牌校验

源卡：[tasks/platform/T013.md](../../tasks/platform/T013.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：过期、伪造、禁用用户均被拒绝；生产接口可替换为统一身份认证。

已观察源码/结构：`.github/workflows/ci.yml`；`.github/workflows/identity.yml`；`backend/business_app/auth.py`；`backend/business_app/controls/providers.py`；`backend/business_app/controls/router.py`；`backend/business_app/identity/tokens.py`；`docs/03-development/t013-admin-handover-validation.md`；`docs/03-development/t013-bootstrap-management-replacement.md`；`docs/03-development/t013-named-admin-adoption-checklist.md`；`docs/03-development/t013-recovery-validation.md`；`docs/03-development/t013-token-validation.md`；`docs/10-deployment/keycloak-identity-runbook.md`；`scripts/identity/checks.py`；`scripts/identity/ci.py`；`scripts/identity/handover.py`；`scripts/identity/management.py`；`scripts/identity/management_config.py`；`scripts/identity/privacy.py`；`scripts/identity/reconcile.py`；`scripts/identity/restore.py`；`scripts/identity/retirement.py`；`tools/identity_admin_tokens.mjs`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/t013-admin-handover-report.json`；`docs/00-project/validation/t013-bootstrap-management-ci-report.json`；`docs/00-project/validation/t013-bootstrap-management-report.json`；`docs/00-project/validation/t013-gateway-log-privacy-report.json`；`docs/00-project/validation/t013-identity-ci-report.json`；`docs/00-project/validation/t013-known-signer-copies-review.json`；`docs/00-project/validation/t013-named-admin-adoption-progress.json`；`docs/00-project/validation/t013-owner-mfa-management-validation.json`；`docs/00-project/validation/t013-owner-mfa-negative-attestation.json`；`docs/00-project/validation/t013-recovery-report.json`；`docs/00-project/validation/t013-recovery-subkeys-owner-validation.json`；`docs/00-project/validation/t013-reprotected-signer-owner-validation.json`；`docs/00-project/validation/t013-rotation-fault-report.json`；`docs/00-project/validation/t013-rotation-fault/linux-scoped-report.json`；`docs/00-project/validation/t013-rotation-fault/slow-body-red.json`；`docs/00-project/validation/t013-token-validation-report.json`；`tests/business/test_authorization.py`；`tests/business/test_token_identity.py`；`tests/identity/test_admin_handover_live.py`；`tests/identity/test_faults_live.py`；`tests/identity/test_key_rotation_live.py`；`tests/identity/test_management_live.py`；`tests/identity/test_recovery_live.py`；`tests/platform/test_t013_handover.py`；`tests/platform/test_t013_identity_checks.py`；`tests/platform/test_t013_management.py`；`tests/platform/test_t013_tokens.py`

剩余代码/核验：已有OIDC/token与恢复管理代码；补真实恢复后旧凭据失效及bootstrap退役闭环，不能增加密码登录替代OIDC。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T014 实现接口级权限控制

源卡：[tasks/platform/T014.md](../../tasks/platform/T014.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：未认证401、无权限403；所有受保护接口默认启用。

已观察源码/结构：`.github/workflows/ci.yml`；`backend/business_app/controls/approvals.py`；`backend/business_app/controls/execution.py`；`backend/business_app/controls/exports.py`；`backend/business_app/controls/reviews.py`；`backend/business_app/controls/router.py`；`backend/business_app/db.py`；`backend/business_app/main.py`；`backend/business_app/permissions/catalog.py`；`backend/business_app/permissions/conditional.py`；`backend/business_app/permissions/context.py`；`backend/business_app/permissions/directory.py`；`backend/business_app/permissions/duties.py`；`backend/business_app/permissions/fence.py`；`backend/business_app/permissions/guard.py`；`backend/business_app/permissions/object_facts.py`；`backend/business_app/permissions/policy.py`；`backend/business_app/permissions/role_facts.py`；`backend/business_app/permissions/six_role.py`；`backend/business_app/permissions/work.py`；`backend/business_app/permissions/work_subject.py`；`backend/business_app/uploads/messaging.py`；`backend/business_app/uploads/worker.py`；`backend/business_migrations/0006_permission_lookup.sql`；`backend/business_migrations/0007_role_facts.sql`；`backend/business_migrations/0008_authorization_fence.sql`；`backend/business_migrations/0009_work_role_facts.sql`；`docs/03-development/t014-unified-permission-implementation.md`；`docs/08-security/t014-interface-scope-matrix.json`；`docs/09-testing/t014-isolated-operation-coverage.json`；`scripts/verify_t014_permissions.py`

有限测试/历史报告：`docs/00-project/validation/t001-t123-api-continuation-report.json`；`docs/00-project/validation/t014-full-regression-report.json`；`docs/00-project/validation/t014-isolated-ci-report.json`；`docs/00-project/validation/t014-isolated-fence-report.json`；`docs/00-project/validation/t014-isolated-rule-progress.json`；`docs/00-project/validation/t014-isolated-validation-report.json`；`docs/00-project/validation/t014-isolated-work-report.json`；`docs/00-project/validation/t014-permissions-report.json`；`tests/business/t014_requests.py`；`tests/business/test_t014_duties.py`；`tests/business/test_t014_object_rules.py`；`tests/business/test_t014_permissions.py`；`tests/business/test_t014_revocation.py`；`tests/business/test_t014_role_facts.py`；`tests/business/test_t014_runtime.py`；`tests/business/test_t014_work.py`；`tests/platform/test_permission_catalog_cache.py`；`tests/platform/test_t014.py`；`tests/platform/test_t014_gate.py`；`tests/platform/test_t014_six_role.py`；`tests/platform/test_t014_work_trust.py`

剩余代码/核验：现有受保护路由统一guard/fence已有；新26个未挂载契约及后续消费者需接统一权限和作用域，不因路由登记而标完整覆盖。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T015 实现数据范围访问控制

源卡：[tasks/platform/T015.md](../../tasks/platform/T015.md)；判断：`SOURCE_PRESENT_ACCEPTANCE_TRACE_INCOMPLETE`。

源验收：跨单位和跨案件访问被拒绝；管理员越权需显式授权。

已观察源码/结构：`backend/business_app/controls/common.py`；`backend/business_app/controls/router.py`；`backend/business_app/data_scope.py`；`backend/business_app/db.py`；`backend/business_app/history/repository.py`；`backend/business_app/scope_catalog.py`；`backend/business_app/scope_collections.py`；`backend/business_migrations/0001_business_baseline.sql`；`docs/04-database/data-scope-extension.md`；`docs/09-testing/t015-data-scope-coverage.json`；`scripts/verify_t015_scope.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/development-continuation-report.json`；`docs/00-project/validation/t015-data-scope-p01-report.json`；`docs/00-project/validation/t015-data-scope-p03-report.json`；`docs/00-project/validation/t015-data-scope-report.json`；`tests/business/test_control_contract_integrity.py`；`tests/business/test_sql_foundation.py`；`tests/business/test_t015_collections.py`；`tests/platform/test_t015_data_scope.py`；`tests/platform/test_t015_gate.py`

剩余代码/核验：作用域查询/对象传播已有；补全业务CLI证据及后续新读写消费者作用域/撤销集成。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T016 实现高风险操作二次确认

源卡：[tasks/platform/T016.md](../../tasks/platform/T016.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：二次确认仅防误操作，不代替业务审批；服务端按获准策略核验审批链。operation_token一次性、短时有效，绑定用户、用途、对象/操作版本及批准记录；正式策略未取得不放行受控操作，全程审计。

已观察源码/结构：`backend/business_app/controls/approvals.py`；`backend/business_app/controls/operation_tokens.py`；`backend/business_app/controls/providers.py`；`backend/business_app/controls/router.py`；`backend/business_app/db.py`；`backend/business_app/scope_context.py`；`backend/business_migrations/0011_operation_token.sql`；`docs/08-security/t016-operation-token-boundaries.md`；`frontend/src/business/api.ts`；`frontend/src/business/session.ts`；`frontend/src/views/ApprovalsView.vue`；`scripts/verify_t016_tokens.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/development-continuation-report.json`；`docs/00-project/validation/t016-development-progress.json`；`docs/00-project/validation/t016-operation-token-report.json`；`tests/business/test_controls.py`；`tests/business/test_t016_operation_token_recovery.py`；`tests/business/test_t016_operation_tokens.py`；`tests/business/test_t016_permission_facts.py`

剩余代码/核验：token签发/一次消费已有；封存/报告等真实消费者与相应前端需绑定用户用途对象版本批准，契约无token字段的操作不得擅加字段。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T017 实现操作审计事件模型

源卡：[tasks/platform/T017.md](../../tasks/platform/T017.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：事件追加写；包含操作者、对象、动作、结果、时间和request_id。

已观察源码/结构：`backend/business_app/controls/common.py`；`backend/business_migrations/0003_control_integrity.sql`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_controls.py`

剩余代码/核验：补登录、查询、下载和拒绝事件全覆盖；审计追加写、结果及request_id一致性需在新增入口接入。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T018 开发审计查询页面与接口

源卡：[tasks/frontend/T018.md](../../tasks/frontend/T018.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：仅审计权限可访问；导出留痕并脱敏；支持时间、用户、对象过滤。

已观察源码/结构：`backend/business_app/controls/exports.py`；`backend/business_app/controls/router.py`；`docs/10-deployment/business-development-runbook.md`；`frontend/src/business/api.ts`；`frontend/src/views/AuditView.vue`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/development-continuation-report.json`；`tests/business/test_controls.py`

剩余代码/核验：审计列表/导出页面及后端已有；全库时间/用户/对象筛选缺契约字段，现有仅当前页筛选；补脱敏导出下载审计联调。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T019 设计内容与媒体资产模型

源卡：[tasks/backend/T019.md](../../tasks/backend/T019.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：区分逻辑内容、原始媒体和派生媒体；记录授权、哈希、父对象和保存期限。

已观察源码/结构：`backend/business_migrations/0001_business_baseline.sql`；`docs/04-database/table-catalog.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：内容/媒体/来源/血缘结构存在于表目录及迁移；逐条补授权/摘要/父对象/保留期限的设计到访问层映射，不能仅凭建表判整卡完成。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T020 实现内容与媒体资产表

源卡：[tasks/backend/T020.md](../../tasks/backend/T020.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：SHA-256和对象键有合理索引；迁移升级及回退/恢复方案可验证；原始与派生约束正确。

已观察源码/结构：`backend/business_app/uploads/repository.py`；`backend/business_migrations/0001_business_baseline.sql`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_migrations.py`

剩余代码/核验：已有上传资产访问与基线表；补完整生命周期/血缘/来源状态访问及原始派生约束业务回归。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T021 实现数据来源授权登记

源卡：[tasks/backend/T021.md](../../tasks/backend/T021.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：无有效来源不得批量导入；到期来源触发告警；修改有审计。

已观察源码/结构：`frontend/src/business/sources.ts`；`frontend/src/views/SourcesView.vue`；`backend/business_app/permissions/object_facts.py`；`backend/business_app/controls/imports.py`；`backend/business_app/controls/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_adapters_and_execution.py`

剩余代码/核验：登记、列表/详情与授权同步代码和页面已有隔离验证；继续接真实来源权威，落实来源责任人与合法用途及真实身份/权威/数据库组合联调，不把回执当当前用途授权。；补到期后台告警及与真实权威相关的完整变更追踪和运维处置；现有同步审计/状态可读不等于后台告警或已到期授权续期。；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

本轮限定实现与验证见[实际回执](../00-project/validation/t001-t123-resource-registry-report.json)，未据此关闭整卡。


当前新增限定成果：[来源页面及到期元数据回执](../00-project/validation/t021-source-console-report.json)，包括194项单元、41项浏览器夹具和12项SQL/HTTP回归；真实权威联调与整卡验收仍待。


本批补充：[后端、前端、数据与测试实测](../00-project/validation/backend-frontend-data-test-report.json)；原回执保留历史范围，当前仍未关闭整卡。


本批补充：[后端、前端、数据与测试实测](../00-project/validation/backend-frontend-data-test-report.json)；原回执保留历史范围，当前仍未关闭整卡。

### T022 实现分片上传初始化

源卡：[tasks/backend/T022.md](../../tasks/backend/T022.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：校验大小、类型、授权与会话状态；重复幂等键返回同一会话。upload_id只作标识，不作访问凭证；对象访问由当前身份和权限控制。

已观察源码/结构：`backend/business_app/uploads/router.py`；`backend/business_app/uploads/service.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_uploads.py`

剩余代码/核验：业务分片初始化已有；前端当前PoC上传需接业务createUpload身份/来源/会话与配额处理。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T023 实现分片接收与校验

源卡：[tasks/backend/T023.md](../../tasks/backend/T023.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：重复分片幂等；错误哈希拒绝；不能写入其他用户会话。

已观察源码/结构：`backend/business_app/uploads/router.py`；`backend/business_app/uploads/service.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_uploads.py`

剩余代码/核验：业务分片接收已有；补业务前端PUT/哈希/重试恢复和配额清理联调，验证大文件并发跨会话。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T024 实现分片合并与完整哈希

源卡：[tasks/backend/T024.md](../../tasks/backend/T024.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：哈希不一致不入库；重复完成幂等；临时文件有清理策略。

已观察源码/结构：`backend/business_app/uploads/router.py`；`backend/business_app/uploads/validator.py`；`backend/business_app/uploads/worker.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_upload_validation.py`

剩余代码/核验：业务合并worker存在；补实际部署worker启动与全媒体校验生产链，崩溃重放/缺对象恢复回归。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T025 实现MinIO对象存储适配器

源卡：[tasks/backend/T025.md](../../tasks/backend/T025.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：上传/下载均校验权限；记录对象version_id和SHA-256；校验实际候选产品的版本控制与对象锁兼容性，锁定与保留策略待审批。

已观察源码/结构：`backend/business_app/objects.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/ci-all-report.json`；`tests/business/test_recovery.py`

剩余代码/核验：受控FileStore下载已有本轮实现；继续正式存储产品版本/对象锁、WORM/保留、恢复及权限适配；不能由FileStore证明正式证据存储。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

本轮限定实现与验证见[实际回执](../00-project/validation/t001-t123-resource-registry-report.json)，未据此关闭整卡。

### T026 实现媒体格式探测与安全校验

源卡：[tasks/backend/T026.md](../../tasks/backend/T026.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：允许格式、签名/容器探测、查毒及资源预算均通过才发布资产；查毒不可用或恶意内容隔离；解析非特权且限制网络和协议。

已观察源码/结构：`backend/business_app/uploads/router.py`；`backend/business_app/uploads/validator.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_upload_validation.py`

剩余代码/核验：现有有限图片校验；实现查毒适配器、视频容器/异常压缩/时长预算及非特权网络协议隔离；不可用时隔离拒绝发布。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T027 实现SHA-256完全重复检测

源卡：[tasks/backend/T027.md](../../tasks/backend/T027.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：不得覆盖既有对象；重复文件复用分析结果需经过权限和版本校验。

已观察源码/结构：`backend/business_app/uploads/repository.py`；`backend/business_app/uploads/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_uploads.py`

剩余代码/核验：精确哈希关联已有；补批量并发重复权限及版本复用策略，禁止跨案件越权复用或覆盖原件。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T028 实现批量清单导入

源卡：[tasks/backend/T028.md](../../tasks/backend/T028.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：逐条状态、可重试、错误不阻断全批；来源和授权必填。

已观察源码/结构：`backend/business_app/controls/imports.py`；`backend/business_app/controls/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_adapters_and_execution.py`

剩余代码/核验：实现授权CSV/JSON清单解析、逐条错误/可重试队列、对象文件批量接入及补偿；现有ObjectRef导入不是清单解析。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T029 实现第三方接入适配器协议

源卡：[tasks/backend/T029.md](../../tasks/backend/T029.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：只接获准来源；URL使用scheme/host/port及DNS/IP验证，默认禁重定向；必要跳转逐跳验证，日志和授权可追溯。

已观察源码/结构：`docs/03-api/openapi.yaml`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现第三方API/消息协议适配器、来源允许清单和DNS/IP出站/逐跳重定向校验，记录授权与请求审计。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B00_EXISTING_FOUNDATION_TRACE_AND_CONSUMERS`。

### T030 开发媒体资产管理页面

源卡：[tasks/frontend/T030.md](../../tasks/frontend/T030.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：支持筛选和详情；原始对象不可直接编辑；下载受权限和审计控制。

已观察源码/结构：`backend/business_app/catalog_reads.py`；`backend/business_app/catalog_router.py`；`backend/business_migrations/0012_catalog_reads.sql`；`docs/03-api/openapi.yaml`；`frontend/src/business/catalog.ts`；`frontend/src/views/AssetsView.vue`

有限测试/历史报告：`docs/00-project/validation/t001-t123-api-continuation-report.json`；`docs/00-project/validation/t001-t123-catalog-read-report.json`；`frontend/e2e/foundation.pw.ts`；`frontend/src/business/catalog.test.ts`；`tests/business/test_catalog_reads.py`

剩余代码/核验：资产页读取与受控下载已有本轮实现；继续完整血缘与来源状态展示、真实后端/权威组合联调。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

本轮限定实现与验证见[实际回执](../00-project/validation/t001-t123-resource-registry-report.json)，未据此关闭整卡。

### T031 设计分析任务与节点执行模型

源卡：[tasks/backend/T031.md](../../tasks/backend/T031.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：支持快速筛查、深度核查、取证溯源三级策略；节点可重试和恢复。

已观察源码/结构：`backend/business_migrations/0001_business_baseline.sql`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_sql_foundation.py`

剩余代码/核验：任务/节点/事件表已存在；补三级策略到运行DAG/重试恢复模型的可执行映射。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T032 实现任务及节点数据库模型

源卡：[tasks/backend/T032.md](../../tasks/backend/T032.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：状态使用受控枚举；版本和时间字段完备；迁移升级及回退/恢复方案可验证。

已观察源码/结构：`backend/business_app/history/repository.py`；`backend/business_migrations/runner.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_migrations.py`

剩余代码/核验：表及部分访问层已有；补调度节点全部状态/版本关联访问，升级/前向修复验证独立记录。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T033 实现任务状态机

源卡：[tasks/backend/T033.md](../../tasks/backend/T033.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：有效资产才能创建分析任务；非法转换返回TASK_STATE_CONFLICT；RETURNED补证回审核，重算关联新版本入队；终态历史不可覆盖，正式路径由Q-24确认。

已观察源码/结构：`backend/business_app/controls/execution.py`；`backend/business_app/uploads/repository.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_execution_cancel.py`

剩余代码/核验：现有取消/上传状态机仅部分；实现全分析任务合法迁移/节点聚合、部分/延期能力、超时与事件顺序。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T034 实现任务创建接口

源卡：[tasks/backend/T034.md](../../tasks/backend/T034.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：校验资产授权与状态、策略版本及幂等；相同键同摘要返回原任务，摘要不同返回冲突；不以upload_id替代task_id。

已观察源码/结构：`docs/03-api/openapi.yaml`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现createTask资产授权/状态/策略校验与摘要绑定幂等事务，生成任务/run/outbox；前端创建流程需接通。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T035 实现任务查询和进度接口

源卡：[tasks/backend/T035.md](../../tasks/backend/T035.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：仅授权范围可见；进度单调限定同一run_version与固定DAG；重算新版本单列，部分/延期能力明确，不泄露堆栈。

已观察源码/结构：`backend/business_app/catalog_reads.py`；`backend/business_app/catalog_router.py`；`backend/business_app/controls/execution.py`；`backend/business_app/history/router.py`；`backend/business_migrations/0012_catalog_reads.sql`；`docs/03-api/openapi.yaml`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/t001-t123-catalog-read-report.json`；`tests/business/test_catalog_reads.py`；`tests/business/test_history_http.py`

剩余代码/核验：listTasks/历史getTask/节点事件已实现；补真实同run固定DAG进度计算、重算新版本展示和部分能力语义。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T036 实现异步队列与优先级

源卡：[tasks/backend/T036.md](../../tasks/backend/T036.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：固定broker/版本支持项目worker拓扑、确认与重投；Kafka执行路线需另证明官方限制的处置。提交后故障可恢复，重复事件无重复业务效果，最终业务状态以SQL为准。

已观察源码/结构：`backend/business_app/uploads/messaging.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_execution_cancel.py`；`tests/business/test_recovery.py`

剩余代码/核验：现有上传outbox/消息仅部分；实现全DAG消费者、长短队列优先级/背压/配额及确认重投恢复。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T037 实现DAG任务编排器

源卡：[tasks/backend/T037.md](../../tasks/backend/T037.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：必需/可选边按契约满足；合法SKIPPED可满足可选边，失败/未执行不冒充成功；无音轨等不死等，部分能力不形成完整正式结果。

已观察源码/结构：`docs/05-workflows`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现版本化DAG解析/调度器、必需/可选边满足、SKIPPED合法性及缺模态/部分能力收敛。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T038 实现节点级重试与检查点

源卡：[tasks/backend/T038.md](../../tasks/backend/T038.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：唯一幂等键包含任务/运行版本/节点/输入摘要；租约回收后旧进程结果拒绝；允许重试重新入队，历史尝试留痕。

已观察源码/结构：`backend/business_app/controls/execution.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_adapters_and_execution.py`；`tests/business/test_execution_cancel.py`

剩余代码/核验：现有租约/fence存在；实现节点重试退避、checkpoint续跑、超时/OOM/永久错误策略与旧执行发布拒绝。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T039 实现任务取消和退回重算

源卡：[tasks/backend/T039.md](../../tasks/backend/T039.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：协作取消确认停止；补证与重算分流，重算关联新run_version回QUEUED；保留历史、原因、权限及审批，正式制度按Q-24。

已观察源码/结构：`backend/business_app/controls/execution.py`；`backend/business_app/controls/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_execution_cancel.py`

剩余代码/核验：cancelTask控制已有；实现实际worker停止确认、rerunTask新run编排与重算/补证分流。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T040 开发任务监控页面

源卡：[tasks/frontend/T040.md](../../tasks/frontend/T040.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：状态实时刷新；操作受权限控制；节点错误可定位。

已观察源码/结构：`backend/business_app/catalog_router.py`；`backend/business_app/controls/router.py`；`backend/business_app/history/router.py`；`frontend/src/business/catalog.ts`；`frontend/src/business/task-read.ts`；`frontend/src/components/TaskCatalogPanel.vue`；`frontend/src/views/PendingReviewsView.vue`；`frontend/src/views/TasksView.vue`

有限测试/历史报告：`docs/00-project/validation/development-delivery-validation.json`；`docs/00-project/validation/ppt-interface-alignment.json`；`docs/00-project/validation/t001-t123-api-continuation-report.json`；`frontend/e2e/foundation.pw.ts`；`frontend/src/business/task-read.test.ts`

剩余代码/核验：任务列表/节点事件/历史读取UI已有；补创建/取消/重算动作、实时刷新、DAG/检查点及可定位错误交互。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B02_TASK_DAG_WORKER`。

### T041 实现图片元数据解析

源卡：[tasks/backend/T041.md](../../tasks/backend/T041.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：异常EXIF不中断；保留原始摘要；敏感定位信息按权限脱敏。

已观察源码/结构：`backend/business_app/uploads/validator.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_upload_validation.py`

剩余代码/核验：现有图片安全解码仅部分；实现ImageMetadataResult生产，色彩/EXIF/质量/重采样及定位脱敏。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T042 实现视频ffprobe解析

源卡：[tasks/backend/T042.md](../../tasks/backend/T042.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：保存各流PTS/time_base/start_time和VFR、缺失时间戳标记；不以帧号/平均帧率一律代替播放时间；估算时间标记来源。

已观察源码/结构：`scripts/verify_stage_two_media.py`

有限测试/历史报告：`docs/00-project/validation/stage-two-media-report.json`

剩余代码/核验：实现安全ffprobe正式解析服务与各流PTS/time_base/start_time/VFR/缺时标；现有自建夹具脚本不是业务生产者。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T043 实现标准化媒体副本生成

源卡：[tasks/backend/T043.md](../../tasks/backend/T043.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：只生成派生副本并记mapping_version；每能力声明原件字节/原件解码像素/允许副本，取证输入不默认使用重编码副本；原件摘要不变。

已观察源码/结构：`scripts/verify_stage_two_media.py`

有限测试/历史报告：`docs/00-project/validation/stage-two-media-report.json`

剩余代码/核验：实现标准分析副本worker、色彩/旋转/转码策略与版本映射/血缘，能力输入原字节/原像素/副本显式选择。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T044 实现镜头边界检测

源卡：[tasks/backend/T044.md](../../tasks/backend/T044.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：支持硬切与渐变基础场景；短镜头规则配置化；结果可重复。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现镜头硬切/渐变检测生产服务、短镜头配置及确定性输出。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T045 实现固定间隔抽帧

源卡：[tasks/backend/T045.md](../../tasks/backend/T045.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：帧时间误差受控；长视频分批；重复任务不重复写。

已观察源码/结构：`scripts/verify_stage_two_media.py`

有限测试/历史报告：`docs/00-project/validation/stage-two-media-report.json`

剩余代码/核验：实现精确PTS固定间隔抽帧worker、长视频分批与幂等派生帧存储。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T046 实现镜头代表帧选择

源卡：[tasks/backend/T046.md](../../tasks/backend/T046.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：每镜头至少一帧；最小时间间隔生效；评分参数配置化。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现每镜头代表帧评分/TopK、最小间隔与配置版本输出。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T047 实现音轨与字幕提取

源卡：[tasks/backend/T047.md](../../tasks/backend/T047.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：无音轨/字幕正常处理；时间轴与原视频一致；血缘完整。

已观察源码/结构：`schemas/model/M33.request.schema.json`；`schemas/model/M33.response.schema.json`；`scripts/verify_stage_two_media.py`

有限测试/历史报告：`docs/00-project/validation/stage-two-media-report.json`

剩余代码/核验：实现正式音轨/内嵌字幕提取派生资产、缺模态状态与原视频时间轴映射。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T048 接入OCR并建立时间片段

源卡：[tasks/backend/T048.md](../../tasks/backend/T048.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：保留框坐标和模型版本；低置信标记而非静默删除。

已观察源码/结构：`schemas/model/M31.request.schema.json`；`schemas/model/M31.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现OCR后端适配器/片段生产、框坐标/版本/低置信标记与跨帧重复合并。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T049 接入ASR并建立时间片段

源卡：[tasks/backend/T049.md](../../tasks/backend/T049.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：长音频分段；无语音可识别；模型与词表版本记录。

已观察源码/结构：`schemas/model/M32.request.schema.json`；`schemas/model/M32.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现ASR后端适配器/长音频分段、无语音状态、词表版本与时间片段生产。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T050 实现媒体统一时间轴服务

源卡：[tasks/backend/T050.md](../../tasks/backend/T050.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：原件和分析副本的时间/坐标映射有版本；毫秒区间与变速/倒放关系明确；OCR/ASR、掩码及关键帧能定位原件。

已观察源码/结构：`backend/business_app/history/projection.py`；`backend/business_app/history/router.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：已有getTimeline投影；实现时间/坐标映射生产服务，变速倒放关系与OCR/ASR/掩码/关键帧原件定位。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T051 定义统一模型输入输出契约

源卡：[tasks/algorithm/T051.md](../../tasks/algorithm/T051.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：Schema可表达分类/框/时间/掩码/向量；明确分数、missing_modality、部分能力、输入字节/像素路径与前处理版本；版本化及错误可校验。

已观察源码/结构：`backend/business_app/inference.py`；`schemas/model/M15.request.schema.json`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_remaining_contracts.py`

剩余代码/核验：34能力Schema和网关校验已有；逐能力补输入路径/前处理/部分能力语义及真实适配器兼容校验，Schema不代表模型已实现。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T052 实现模型注册表

源卡：[tasks/algorithm/T052.md](../../tasks/algorithm/T052.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：版本唯一；上线/下线需权限；模型卡必填；修改审计。

已观察源码/结构：`backend/business_app/controls/router.py`；`backend/business_app/registry_reads.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：模型列表读取已有本轮实现；继续模型登记写入、唯一版本及模型卡的服务约束、修改审计、上下线和管理页面。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

本轮限定实现与验证见[实际回执](../00-project/validation/t001-t123-resource-registry-report.json)，未据此关闭整卡。

### T053 实现统一推理网关

源卡：[tasks/algorithm/T053.md](../../tasks/algorithm/T053.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：业务服务不导入模型代码；超时/错误/trace统一；实际backend锁版本并验证维护补丁路径及环境；Mock只计接口验证。

已观察源码/结构：`backend/business_app/inference.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`docs/00-project/validation/ci-all-report.json`；`tests/business/test_remaining_contracts.py`

剩余代码/核验：网关路由/授权/Schema校验已有；实现真实ModelBackend逐能力适配与超时/故障/版本维护路径。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T054 实现HTTP与本地Mock适配器

源卡：[tasks/algorithm/T054.md](../../tasks/algorithm/T054.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：适配器可替换；Mock可配置成功、失败、超时和异常输出。

已观察源码/结构：`backend/business_app/inference.py`；`tools/stage_three_demo/app.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现可替换HTTP适配器与可配置成功/失败/超时/畸形输出Mock；Mock结果只用于接口测试。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T055 实现推理批处理与GPU队列

源卡：[tasks/algorithm/T055.md](../../tasks/algorithm/T055.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：批量结果顺序正确；超时不长期阻塞，显存/队列背压可观察；当前无已确认GPU，GPU专项测试保持未执行，CPU/Mock不计入GPU达标。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现按模型/尺寸/等待窗合批、顺序恢复、显存/队列背压/优先级与超时取消；GPU验收另需实际设备。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T056 实现模型健康检查与熔断

源卡：[tasks/algorithm/T056.md](../../tasks/algorithm/T056.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：连续失败触发；半开恢复；降级被记录且不隐藏版本变化。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现getModelHealth真实探测与版本绑定、连续失败熔断/半开恢复/降级记录；不能把记录存在视作健康。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

### T057 实现模型灰度发布

源卡：[tasks/algorithm/T057.md](../../tasks/algorithm/T057.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：灰度配置有审批；正式结论使用主版本；对比结果隔离。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现rolloutModel批准绑定、单位/比例/场景灰度路由及隔离双写对比；正式结论固定主版本。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T058 实现模型评测记录管理

源卡：[tasks/algorithm/T058.md](../../tasks/algorithm/T058.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：没有合格评测记录不能进入发布审批；报告不可覆盖。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：评测列表读取已有本轮实现；继续真实评测登记/写入、指标及报告生产、分组指标、合格评测对发布审批的约束和页面。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

本轮限定实现与验证见[实际回执](../00-project/validation/t001-t123-resource-registry-report.json)，未据此关闭整卡。

### T059 实现输入输出漂移监测

源卡：[tasks/algorithm/T059.md](../../tasks/algorithm/T059.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：不保存不必要原始敏感内容；阈值可配置；按模型版本区分。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现按模型版本的输入质量/嵌入/置信度/人工纠错漂移统计、阈值与敏感内容最小保存。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B03_MEDIA_AND_MODEL_ADAPTERS`。

### T060 开发模型运维页面

源卡：[tasks/frontend/T060.md](../../tasks/frontend/T060.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：模型上线/回滚页面有二次确认，并显示获准发布策略、包版本和批准记录；二次确认不代替审批，后端校验发布授权和权限分离，失效或未批准包不得正式上线。

已观察源码/结构：`frontend/src/router.ts`；`frontend/src/business/models.ts`；`frontend/src/views/ModelsView.vue`；`frontend/src/business/models.ts`；`frontend/src/views/ModelsView.vue`

有限测试/历史报告：[T060只读页面实际回执](../00-project/validation/t060-readonly-ui-report.json)：129项单元及36项浏览器传输测试通过，不代表真实后端组合或完整任务验收。

剩余代码/核验：当前模型与已登记评测只读页面已实现；补真实健康、灰度/漂移、获批发布/二次确认/回滚交互及真实后端/身份组合E2E。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B01_READINESS_SOURCE_DOWNLOAD_REGISTRY`。

### T061 定义风险标签和版本管理

源卡：[tasks/algorithm/T061.md](../../tasks/algorithm/T061.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：标签变更不覆盖历史；未知和证据不足可表达；权限与审计完整。

已观察源码/结构：`backend/business_app/controls/definitions.py`；`backend/business_app/controls/router.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：已有createPolicy/listPolicies通用版本定义；实现风险标签未知/证据不足语义、历史绑定及标签管理UI。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T062 接入图片多标签分类模型

源卡：[tasks/algorithm/T062.md](../../tasks/algorithm/T062.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：使用Sigmoid多标签；返回原始与校准分数、阈值、模型版本。

已观察源码/结构：`schemas/model/M01.request.schema.json`；`schemas/model/M01.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M01多标签模型适配/推理，Sigmoid原始/校准分数、类别阈值和版本生产。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T063 接入敏感目标检测模型

源卡：[tasks/algorithm/T063.md](../../tasks/algorithm/T063.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：坐标归一化；视频结果带时间戳；类别与标签版本匹配。

已观察源码/结构：`schemas/model/M02.request.schema.json`；`schemas/model/M02.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M02目标检测适配、归一化框/视频时间戳与标签版本对应。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T064 接入视频行为识别模型

源卡：[tasks/algorithm/T064.md](../../tasks/algorithm/T064.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：窗口重叠结果合并；边界不越界；模型版本记录。

已观察源码/结构：`schemas/model/M04.request.schema.json`；`schemas/model/M04.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M04视频行为窗口推理、重叠合并/边界校验/版本记录。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T065 接入音频事件识别模型

源卡：[tasks/algorithm/T065.md](../../tasks/algorithm/T065.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：静音和无音轨正常处理；结果绑定音轨和模型版本。

已观察源码/结构：`schemas/model/M06.request.schema.json`；`schemas/model/M06.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M06音频事件适配、静音/无音轨分流与音轨版本绑定。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T066 实现多模态时间对齐

源卡：[tasks/algorithm/T066.md](../../tasks/algorithm/T066.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：处理缺失模态；时间单位一致；不因缺失模态丢弃窗口。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现多模态窗口时间对齐及missing_modality保留，统一毫秒与原件映射。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T067 实现跨模态矛盾检测

源卡：[tasks/algorithm/T067.md](../../tasks/algorithm/T067.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：输出一致、矛盾、无关或证据不足；绑定两侧证据。

已观察源码/结构：`schemas/model/M07.request.schema.json`；`schemas/model/M07.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M07矛盾检测，输出一致/矛盾/无关/证据不足及双侧证据绑定。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T068 实现综合风险融合与校准

源卡：[tasks/algorithm/T068.md](../../tasks/algorithm/T068.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：按类别独立阈值；不得以单一总分替代重点类别；结果可解释。

已观察源码/结构：`backend/business_app/controls/definitions.py`；`backend/business_app/controls/router.py`；`schemas/model/M08.request.schema.json`；`schemas/model/M08.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：通用Policy已有；实现M08融合/类别独立阈值/校准/解释与策略版本记录。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T069 实现风险转人工规则

源卡：[tasks/algorithm/T069.md](../../tasks/algorithm/T069.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：触发原因明确；优先级可配置；规则版本可追溯。

已观察源码/结构：`backend/business_app/controls/definitions.py`；`backend/business_app/controls/router.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：通用Policy已有；实现风险转人工原因/优先级/版本规则执行及复核队列生产。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T070 开发风险识别研判界面

源卡：[tasks/frontend/T070.md](../../tasks/frontend/T070.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：点击结论定位帧/时间/区域；显示模型版本、阈值和人工状态。

已观察源码/结构：`backend/business_app/history/router.py`；`frontend/src/router.ts`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：getRiskFindings读取已有；实现风险研判UI，结论到帧/时间/区域联动及版本/阈值/人工状态。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T071 实现图片取证基础特征

源卡：[tasks/algorithm/T071.md](../../tasks/algorithm/T071.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：每项特征记录算法版本；不把单项异常直接作为篡改结论。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现图片基础取证特征生产与算法版本/证据输出，单项异常不得直接作篡改结论。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T072 接入图片篡改区域模型

源卡：[tasks/algorithm/T072.md](../../tasks/algorithm/T072.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：掩码尺寸可回映射原图；保存模型版本；支持证据不足。

已观察源码/结构：`schemas/model/M09.request.schema.json`；`schemas/model/M09.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M09区域篡改适配、掩码回原图映射与证据不足状态。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T073 实现复制粘贴与局部生成分类

源卡：[tasks/algorithm/T073.md](../../tasks/algorithm/T073.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：类型与区域一致；低置信不强制分类；提供特征证据。

已观察源码/结构：`schemas/model/M10.request.schema.json`；`schemas/model/M10.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M10复制粘贴/局部生成类型与区域联合输出、低置信及特征证据。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T074 实现视频时间结构异常检测

源卡：[tasks/algorithm/T074.md](../../tasks/algorithm/T074.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：定位删除、插入、重排、变速、倒放和重复片段候选。

已观察源码/结构：`schemas/model/M11.request.schema.json`；`schemas/model/M11.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M11时间结构异常候选生产，覆盖删除/插入/重排/变速/倒放/重复片段。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T075 实现视频空间篡改跟踪

源卡：[tasks/algorithm/T075.md](../../tasks/algorithm/T075.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：短暂误检可过滤；区域轨迹可视化；不越出帧边界。

已观察源码/结构：`schemas/model/M12.request.schema.json`；`schemas/model/M12.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M12空间区域轨迹/短误检过滤及帧边界约束，配套轨迹可视化。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T076 接入深度伪造与音画同步检测

源卡：[tasks/algorithm/T076.md](../../tasks/algorithm/T076.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：按人脸轨迹输出；无脸内容不报错；压缩条件下分组评测。

已观察源码/结构：`schemas/model/M13.request.schema.json`；`schemas/model/M13.response.schema.json`；`schemas/model/M14.request.schema.json`；`schemas/model/M14.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M13/M14人脸轨迹深伪/音画同步适配，无脸状态及压缩分组评测。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T077 实现篡改多证据融合

源卡：[tasks/algorithm/T077.md](../../tasks/algorithm/T077.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：结论区分确认候选和证据不足；冲突证据进入人工复核。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现篡改多证据融合，确认候选/证据不足/冲突转人工规则。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T078 开发篡改取证界面

源卡：[tasks/frontend/T078.md](../../tasks/frontend/T078.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：证据与原媒体坐标/时间联动；显示算法限制和人工状态。

已观察源码/结构：`backend/business_app/history/router.py`；`frontend/src/router.ts`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：getForensics读取已有；实现篡改取证UI原件坐标/时间联动、限制与人工状态。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T079 实现图片感知哈希特征

源卡：[tasks/algorithm/T079.md](../../tasks/algorithm/T079.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：同一图片稳定；模型/算法版本记录；完全重复与近重复分开。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现稳定感知哈希生产/版本与近重复匹配，区分SHA完全重复。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T080 实现视觉与复制检测向量生成

源卡：[tasks/algorithm/T080.md](../../tasks/algorithm/T080.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：归一化规则明确；不同版本隔离；失败可重试。

已观察源码/结构：`ai-services/inference/service.py`；`schemas/model/M15.request.schema.json`；`schemas/model/M15.response.schema.json`；`schemas/model/M19.request.schema.json`；`schemas/model/M19.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M15/M19真实视觉/复制向量适配、归一化/版本隔离/失败重试；synthetic-encoder非业务模型。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T081 建立Milvus索引与版本管理

源卡：[tasks/algorithm/T081.md](../../tasks/algorithm/T081.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：保留≥2000万索引源目标，按20万/200万/2000万逐级验证；权限条件由服务端生成并复核返回资产；实测写入可见性。

已观察源码/结构：`scripts/verify_media_and_queries.py`

有限测试/历史报告：`docs/00-project/validation/media-query-report.json`

剩余代码/核验：实现Milvus业务写入/读取/重建/版本切换、可见性与权限复核；3条SQL向量PoC不能替代。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T082 实现图片多路候选召回

源卡：[tasks/algorithm/T082.md](../../tasks/algorithm/T082.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：召回在当前授权域内执行；结果逐对象复核；近似相似不得直接确认同源；版本不匹配报错。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现searchImage/getSearchJob多路召回/融合与逐对象授权复核，版本冲突拒绝。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T083 实现局部特征提取与匹配

源卡：[tasks/algorithm/T083.md](../../tasks/algorithm/T083.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：代码/权重/提取器许可分别核验，LightGlue许可不覆盖SuperPoint；整图/局部/低纹理与资源条件明确，许可未闭环不作正式发布。

已观察源码/结构：`schemas/model/M16.request.schema.json`；`schemas/model/M16.response.schema.json`；`schemas/model/M17.request.schema.json`；`schemas/model/M17.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M16/M17特征提取/匹配及资源场景边界；提取器/代码/权重许可证分别核验。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T084 实现RANSAC几何验证

源卡：[tasks/algorithm/T084.md](../../tasks/algorithm/T084.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：验证失败不得标记高可信同源；参数配置化；生成匹配证据图。

已观察源码/结构：`schemas/model/M18.request.schema.json`；`schemas/model/M18.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M18 RANSAC几何验证、参数版本和匹配证据图，失败不标高可信同源。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T085 实现图片局部区域检索

源卡：[tasks/algorithm/T085.md](../../tasks/algorithm/T085.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：坐标校验；输出候选匹配区域；区域权限继承原资产。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现searchImageRegion区域坐标校验/候选匹配区域与原资产权限继承。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T086 实现视频帧检索候选聚合

源卡：[tasks/algorithm/T086.md](../../tasks/algorithm/T086.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：过滤孤立单帧；保留帧时间对应；候选Top-N可配置。

已观察源码/结构：`schemas/model/M33.request.schema.json`；`schemas/model/M33.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现视频帧检索聚合、孤立单帧过滤、对应时间与TopN配置。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T087 实现视频相似度矩阵构建

源卡：[tasks/algorithm/T087.md](../../tasks/algorithm/T087.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：时间戳顺序正确；大矩阵分块；可生成可视化。

已观察源码/结构：`schemas/model/M20.request.schema.json`；`schemas/model/M20.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M20时序相似度矩阵分块计算、时间排序及可视化。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T088 实现局部DTW与倒放对齐

源卡：[tasks/algorithm/T088.md](../../tasks/algorithm/T088.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：不能由单帧确认；边界回映射正确；参数配置化。

已观察源码/结构：`schemas/model/M20.request.schema.json`；`schemas/model/M20.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M20局部DTW/倒放路径对齐与原件边界映射，不由单帧确认。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T089 实现多源拼接来源映射

源卡：[tasks/algorithm/T089.md](../../tasks/algorithm/T089.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：覆盖率和未匹配区段明确；重叠来源有冲突处理；平均定位误差可计算。

已观察源码/结构：`schemas/model/M22.request.schema.json`；`schemas/model/M22.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M22多源片段来源映射与searchVideo/getSearchJob、覆盖/未匹配/冲突/定位误差输出。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T090 实现高可信同源内容聚类

源卡：[tasks/backend/T090.md](../../tasks/backend/T090.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：语义相似不直接入簇；A—拼接Q—B不能仅按连通合成整内容簇；合并/拆分审核，首发范围明确，防泄漏组与业务簇分开。

已观察源码/结构：`schemas/model/M23.request.schema.json`；`schemas/model/M23.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M23高可信同源聚类、整内容与片段区别、审核合并拆分及防泄漏组隔离。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T091 实现首发排序特征工程

源卡：[tasks/backend/T091.md](../../tasks/backend/T091.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：缺失值与来源证据明确；不把缺失当负面；特征版本化。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现首发排序特征生产，缺失/来源证据/版本及观察范围表达。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T092 训练和注册首发排序模型

源卡：[tasks/backend/T092.md](../../tasks/backend/T092.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：训练数据/许可/簇真值明确，Top-3源目标及正式性质按Q-13/Q-22；工程训练完成和正式发布达标分别记，特征贡献及覆盖未知可复查。

已观察源码/结构：`schemas/model/M24.request.schema.json`；`schemas/model/M24.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M24训练CLI/工件注册与可复现清单、特征贡献/未知覆盖，工程运行与模型发布分开。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T093 实现首发候选查询服务

源卡：[tasks/backend/T093.md](../../tasks/backend/T093.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：措辞限定授权数据范围；证据不足不输出确定原创；人工状态可见。

已观察源码/结构：`backend/business_app/history/projection.py`；`backend/business_app/history/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_history.py`

剩余代码/核验：getFirstSource已有历史排名投影；实现真实排序生产及缺失时间/时区/并列/证据不足处理。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T094 设计传播图谱数据模型

源卡：[tasks/backend/T094.md](../../tasks/backend/T094.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：显式与推断关系分离；边含时间、概率、证据和确认状态。

已观察源码/结构：`backend/business_migrations/0001_business_baseline.sql`；`schemas/model/M26.request.schema.json`；`schemas/model/M26.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：图谱表/模型Schema为结构基础；补显式/推断边来源、概率、时间、证据和确认状态到访问模型的映射。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T095 实现传播图谱写入与查询

源卡：[tasks/backend/T095.md](../../tasks/backend/T095.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：写入幂等；权限过滤；路径结果带证据ID。

已观察源码/结构：`backend/business_app/history/projection.py`；`backend/business_app/history/router.py`；`schemas/model/M26.request.schema.json`；`schemas/model/M26.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：getPropagation仅读取结果快照；实现图谱写入幂等、权限过滤路径查询与证据ID。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T096 实现隐式传播关系推断

源卡：[tasks/backend/T096.md](../../tasks/backend/T096.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：不得覆盖显式关系；低概率不默认展示为事实；可人工确认或驳回。

已观察源码/结构：`schemas/model/M27.request.schema.json`；`schemas/model/M27.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现M27隐式关系推断及decidePropagationEdge人工确认/驳回，不能覆盖显式关系。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T097 开发传播时间线和图谱界面

源卡：[tasks/frontend/T097.md](../../tasks/frontend/T097.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：显式/推断边视觉区分；点击显示证据；大图支持聚合。

已观察源码/结构：`backend/business_app/history/router.py`；`frontend/src/router.ts`；`schemas/model/M26.request.schema.json`；`schemas/model/M26.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：getPropagation读取已有；实现时间线/图谱UI，显式/推断视觉区分、证据定位与大图聚合。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T098 实现结构化主张抽取服务

源卡：[tasks/algorithm/T098.md](../../tasks/algorithm/T098.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：只输出结构化JSON；未知为null；每项引用输入片段；提示模板版本化。

已观察源码/结构：`schemas/model/M28.request.schema.json`；`schemas/model/M28.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现extractClaims/M28结构化主张服务、输入片段引用/null未知与提示版本。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T099 实现权威证据检索与关系判断

源卡：[tasks/algorithm/T099.md](../../tasks/algorithm/T099.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：仅访问授权白名单证据源；URL出站按§9.7控制；每条关系关联可定位证据，不以网页/模型文本作为工具命令。

已观察源码/结构：`schemas/model/M29.request.schema.json`；`schemas/model/M29.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现verifyClaim/M29授权证据检索/关系判断、来源允许清单/出站边界与可定位证据。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T100 实现统一证据对象模型

源卡：[tasks/backend/T100.md](../../tasks/backend/T100.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：证据引用原件、时间/坐标映射、模型/结果/授权版本；统一Schema可校验且先于算法正式联调；不要求机械等到第十一组才实施。

已观察源码/结构：`backend/business_app/history/repository.py`；`backend/business_migrations/0001_business_baseline.sql`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：证据Schema/表/历史投影已有；实现生产者统一Evidence写入/原件映射/模型结果授权版本完整校验。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T101 实现风险与取证证据卡片接口

源卡：[tasks/backend/T101.md](../../tasks/backend/T101.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：核心结论均有证据；支持过滤类型和人工状态；坐标时间可定位。

已观察源码/结构：`backend/business_app/history/projection.py`；`backend/business_app/history/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_history.py`

剩余代码/核验：getTaskEvidence投影已有；实现真实发现聚合与风险/取证证据卡片过滤和前端定位。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T102 实现人工复核工作流

源卡：[tasks/backend/T102.md](../../tasks/backend/T102.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：服务端核验当前对象权限和审批授权；策略缺失/失效不批准。并发提交校验review_version，记录理由、证据和审计，变更后重新审批；会审/职责分离按Q-18/Q-20/Q-24/Q-32确认。

已观察源码/结构：`backend/business_app/controls/reviews.py`；`backend/business_app/controls/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_adapters_and_execution.py`；`tests/business/test_controls.py`

剩余代码/核验：复核/审批控制已有；补真实结果的RETURNED/补证后继、撤销更正和适用正式规则接入。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T103 开发人工复核工作台

源卡：[tasks/frontend/T103.md](../../tasks/frontend/T103.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：证据可定位，显示对象/策略版本、待审或失效原因和允许动作；二次确认仅防误操作，不等于独立复核；模拟/未批准结果有标识，草稿可保存。

已观察源码/结构：`backend/business_app/controls/reviews.py`；`backend/business_app/controls/router.py`；`backend/business_app/history/router.py`；`frontend/src/views/ApprovalsView.vue`；`frontend/src/views/PendingReviewsView.vue`；`frontend/src/views/TasksView.vue`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_controls.py`

剩余代码/核验：PendingReviews/Approvals和任务读取已有；补复核草稿/标注/帧区域定位/版本动作/提交交互，待审列表不是完整复核工作台。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T104 实现证据固化与完整性校验

源卡：[tasks/backend/T104.md](../../tasks/backend/T104.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：绑定对象版本和SHA-256清单；候选对象锁/完整性实测通过。更正建立新版本并触发关联批准校验，原记录保留；保留/legal hold策略及权限按Q-19/Q-20/Q-31确认，技术固化不自动认定证据效力。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现sealEvidence对象版本摘要清单/不可变固化及更正版本与批准失效关联；正式对象锁需实际产品实测。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T105 实现可信时间与签名适配层

源卡：[tasks/backend/T105.md](../../tasks/backend/T105.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：时间来源、证书/算法、验证链和故障策略可追溯；提供获准服务/授权依据及配置版本。模拟签名标识明确，未确认Q-26不宣称正式可信服务已接入。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现可信时间/签名服务适配、证书算法链验证/故障策略与配置版本；模拟签名明确标识。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T106 实现证据约束核查摘要

源卡：[tasks/backend/T106.md](../../tasks/backend/T106.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：逐句核验事实与证据支持关系，无证据拒绝或转人工；生成内容保持草稿/未批准身份，外部内容和模型不得触发批准或导出权限。

已观察源码/结构：`schemas/model/M30.request.schema.json`；`schemas/model/M30.response.schema.json`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现createReportDraft/M30逐句证据约束摘要、无证据拒绝/人工与草稿身份保存。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T107 实现核查报告生成

源卡：[tasks/backend/T107.md](../../tasks/backend/T107.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：报告、结果、证据摘要与有效批准绑定；服务端校验当前权限/用途/策略和版本，缺少批准不作为正式报告导出。变更后旧批准按获准策略失效，下载授权可撤销并留审计；批准角色/独立性仍待Q-20/Q-32确认。

已观察源码/结构：`backend/business_app/registry_reads.py`；`backend/business_app/registry_router.py`；`backend/business_migrations/0013_report_reads.sql`

有限测试/历史报告：`docs/00-project/validation/t001-t123-api-continuation-report.json`；`tests/business/test_registry_reads.py`；`tests/business/test_report_migration.py`

剩余代码/核验：getReport元数据已有；实现createReport版本模板/渲染/证据批准绑定及downloadReport撤销和下载审计。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T108 实现样本纠错与回流审批

源卡：[tasks/backend/T108.md](../../tasks/backend/T108.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：业务复核不自动批准训练使用；用途授权、脱敏/去重/质检和隔离检查通过后按批准版本入库。用途或授权撤销按获准政策处置并记录，不擅定删除期限。

已观察源码/结构：`backend/business_app/controls/reviews.py`；`backend/business_app/controls/router.py`

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_adapters_and_execution.py`

剩余代码/核验：已有反馈请求拒绝/控制部分；实现requestFeedback用途授权、脱敏去重质检/冻结集隔离及入库worker/撤销处理。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Effective authority/purpose/classification/approval/retention policy and provider bindings; absent policy must fail closed. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B04_ALGORITHM_AND_RESULTS_UI`。

### T109 建立标注规范与标签质检工具

源卡：[tasks/data/T109.md](../../tasks/data/T109.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：强制必填和边界合法；支持未知/证据不足；双人标注和仲裁。

已观察源码/结构：`scripts/validate_annotations.py`；`tests/data/test_annotation_validation.py`；`scripts/validate_annotations.py`；`tests/data/test_annotation_validation.py`；`scripts/validate_annotations.py`；`tests/data/test_annotation_validation.py`；`scripts/validate_annotations.py`；`tests/data/test_annotation_validation.py`；`schemas/dataset/catalog.schema.json`；`scripts/validate_inputs.py`

有限测试/历史报告：本批Linux标注与开发入口实测见[限定回执](../00-project/validation/backend-frontend-data-test-report.json)，结构、冲突和机械抽样不代替真实标注/仲裁验收。

剩余代码/核验：已有离线结构、边界和机械抽样质检；继续落实正式标签词典/来源用途、真实时间与掩码映射证据、内容簇补查及人工流程，不将Schema通过当业务标签正确。；Schema/边界/批内重复冲突、机械确定性抽样及CLI回归已执行；仍需实际人工抽检、一致性/仲裁及适用真实标注流程的测试。；部分必填/边界、unknown/insufficient已验证；双人独立标注、真实reviewer身份、仲裁及正式口径仍无完整实现/证据，整卡验收未完成。；落实实际负责人及剩余工时；对照本卡源依赖、适用外部条件和验收标准记录实际结果，仍有代码/测试缺口时不能仅靠审批关闭。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。


本批补充：[后端、前端、数据与测试实测](../00-project/validation/backend-frontend-data-test-report.json)；原回执保留历史范围，当前仍未关闭整卡。


本批补充：[后端、前端、数据与测试实测](../00-project/validation/backend-frontend-data-test-report.json)；原回执保留历史范围，当前仍未关闭整卡。

### T110 实现原始素材分组划分

源卡：[tasks/data/T110.md](../../tasks/data/T110.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：原始素材及增强版本同组不跨集合；多源组合样本检查来源组交叉；比例可配置，清单/哈希/种子可复查；授权及事件/人物外推分层另记录。

已观察源码/结构：`schemas/dataset/split-manifest.schema.json`；`scripts/validate_inputs.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：split Schema/跨组校验已有；实现分组划分生成工具、多源组合交叉约束、比例/种子/哈希清单及授权分层记录。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。

### T111 实现可控编辑数据增强流水线

源卡：[tasks/data/T111.md](../../tasks/data/T111.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：不覆盖原始样本；每个增强可复现；标注同步变换。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现可复现编辑增强工具与参数种子/派生清单，坐标/掩码/时间标注同步变换且原件不可覆盖。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。

### T112 建立难负样本挖掘流程

源卡：[tasks/data/T112.md](../../tasks/data/T112.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：未经人工确认不作为金标准；记录触发模型与相似度。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现难负样本候选挖掘工具与触发模型/相似度/人工确认状态，禁止封存测试集挖掘。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。

### T113 实现风险模型训练与评测流水线

源卡：[tasks/backend/T113.md](../../tasks/backend/T113.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：流水线建设以输入清单、Macro-F1/召回/校准公式与失败计数、冒烟和复算通过判定；95%/0.85源目标保留，真实模型候选发布另按生效MetricProtocol，不以代码运行判达标。

已观察源码/结构：`schemas/model/M01.request.schema.json`；`schemas/model/M01.response.schema.json`；`scripts/evaluate_acceptance_metrics.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：classification/ECE参考计算已有；实现M01训练/评测CLI、输入清单/工件/分组/失败统计和复算；代码运行不证明95%/0.85。

实际输入：Authorized model weights/runtime, exact version/license and purpose-authorized data; schemas/synthetic encoder do not supply these. Purpose-authorized dataset inventory/labels/group truth and frozen evaluation split; no actual dataset supplied by this audit. Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。

### T114 实现篡改模型评测流水线

源卡：[tasks/backend/T114.md](../../tasks/backend/T114.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：保留IoU≥0.70及视频篡改召回≥90%源目标，正式口径按Q-13；掩码映射原件，漏检正例IoU=0，逐图宏平均与面积分层、负例误报单列。

已观察源码/结构：`scripts/evaluate_acceptance_metrics.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：mask_iou参考计算已有；实现篡改评测流水线、原件掩码/面积分层/视频召回/失败及负例误报完整统计。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。

### T115 实现同源与片段检索评测流水线

源卡：[tasks/backend/T115.md](../../tasks/backend/T115.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：评测代码/分母/失败计数/时间误差与复算正确；95%/90%及≤1秒源目标保留，在模型发布包上按生效协议受控评测，工程完成与模型达标分开。

已观察源码/结构：`scripts/evaluate_acceptance_metrics.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：retrieval/boundaries参考计算已有；实现整图/片段检索评测运行器、分母失败/未匹配/时间误差与版本清单复算。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。

### T116 实现首发和大模型核查评测

源卡：[tasks/backend/T116.md](../../tasks/backend/T116.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：Top-3/NDCG/校准/关系及引用支持指标实现可复算；Top-3≥90%为保留源目标，范围/真值/未知按生效协议，独立测试不用于选择候选。

已观察源码/结构：`scripts/evaluate_acceptance_metrics.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：origin_top3/ECE/citations参考计算已有；实现NDCG/关系与引用支持评测运行器、独立测试隔离及未知真值处理。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B05_DATA_TRAINING_EVALUATION`。

### T117 建立应用安全自动化扫描

源卡：[tasks/testing/T117.md](../../tasks/testing/T117.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：严重/高危问题阻止合并或发布；误报有审批豁免期限。

已观察源码/结构：`docs/02-architecture/licenses.md`；`scripts/stage_three_quality.py`

有限测试/历史报告：`docs/00-project/validation/github-actions-report.json`；`docs/00-project/validation/stage-three-dependency-scan-report.json`

剩余代码/核验：现有依赖扫描/CI门禁；补适用SAST、镜像/系统二进制/Torch未托管组件覆盖与有期限豁免执行。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD`。

### T118 实施上传与接口安全测试

源卡：[tasks/testing/T118.md](../../tasks/testing/T118.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：早期上传/任务接口验证通过单列阶段结果；T102/T107/T108就绪后审批/导出/回流专项复测及适用高危用例全部关闭才签本任务最终完成。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：`docs/00-project/validation/business-foundation-report.json`；`tests/business/test_authorization.py`；`tests/business/test_control_contract_integrity.py`；`tests/business/test_upload_validation.py`

剩余代码/核验：上传/权限/审批部分测试已有；补业务全链完成后导出/反馈/恶意文件/SSRF/限流资源最终安全回归及整改闭环。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD`。

### T119 实施大模型安全测试

源卡：[tasks/testing/T119.md](../../tasks/testing/T119.md)；判断：`CONTRACT_DESIGN_OR_TEST_ONLY_NO_TASK_RUNTIME_PROVEN`。

源验收：工具白名单有效；无证据句拦截；攻击输入不改变系统权限。

已观察源码/结构：未在所审源码路径中定位任务专用运行实现；源卡/契约为设计依据。

有限测试/历史报告：`tests/fixtures/claim-insufficient-cases.json`

剩余代码/核验：claim-insufficient夹具仅资料；实现LLM注入/工具允许清单/无证据句/权限不变测试运行器，覆盖真实服务集成。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD`。

### T120 实现监控指标与告警

源卡：[tasks/backend/T120.md](../../tasks/backend/T120.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：排队/解码/推理/端到端、失败重试、CPU/内存/磁盘与配额可观察；无GPU不显示虚假GPU指标；日志/trace不替代全量审计。

已观察源码/结构：`backend/app/observability.py`；`docs/00-project/server-sync-receipt.json`

有限测试/历史报告：`docs/00-project/validation/ci-all-report.json`；`docs/00-project/validation/resource-readiness-snapshot.json`

剩余代码/核验：PoC observability存在；实现全业务排队/解码/推理/端到端/重试与资源配额指标、仪表盘/告警及响应。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD`。

### T121 实现备份恢复与灾备演练

源卡：[tasks/deployment/T121.md](../../tasks/deployment/T121.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：真实恢复、权限/授权、报告版本与原件摘要验证通过；备份损坏、WAL缺段及恢复点不一致可检测；同盘复制不作为独立灾备。

已观察源码/结构：`scripts/verify_development_recovery.py`

有限测试/历史报告：`docs/00-project/validation/business-recovery-report.json`；`docs/00-project/validation/development-recovery-report.json`；`tests/business/test_recovery.py`

剩余代码/核验：研发冷备/恢复脚本已有；补全业务异机/PITR恢复运行器和损坏/WAL缺段/恢复点不一致检测及业务不变量验证。

实际输入：Declared unresolved source questions: Q-33; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD`。

### T122 执行20并发验收性能测试

源卡：[tasks/testing/T122.md](../../tasks/testing/T122.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：20及100均待确认；冻结素材、模型、索引、资源与计时范围后记录P50/P95/P99、吞吐、错误、排队和成功率；不得凭源标题认定已批准验收基线。

已观察源码/结构：`scripts/evaluate_acceptance_metrics.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：latency参考计算已有；实现可配置20并发负载发生器/冻结清单/排队计时/错误成功率报告，实际验收需批准负载。

实际输入：Declared unresolved source questions: Q-33, Q-13, Q-14; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD`。

### T123 执行100并发容量与长稳测试

源卡：[tasks/testing/T123.md](../../tasks/testing/T123.md)；判断：`PARTIAL_IMPLEMENTATION`。

源验收：不预判100为可选扩展或非硬指标；按批准负载执行，无数据损坏并明确瓶颈、错误率和资源需求；资源未落实保持未验证。

已观察源码/结构：`scripts/evaluate_acceptance_metrics.py`

有限测试/历史报告：未定位任务专用实际执行报告；契约夹具不是运行验收。

剩余代码/核验：实现100并发与长稳运行器/容量资源采集、数据一致性校验和瓶颈报告，实际验收需资源与批准负载。

实际输入：Declared unresolved source questions: Q-33, Q-13, Q-14; distinguish policy confirmation from code that can be implemented now. Actual provider/resource/configuration, product/version/license and measured deployment evidence appropriate to this task; CPU or mocks cannot prove GPU/scale/DR. Actual reviewer/source acceptance decision and original acceptance testing; no fabricated historical date or effort.

下一批：`B06_SECURITY_OBSERVABILITY_RECOVERY_LOAD`。

2026-10-24续批：6b4c93f6两路CI身份407项中各2项bootstrap退役后重启超时；公开就绪后通过原个人MFA流程重新认证并执行只读就绪，不回退已退役凭据，保留180秒和全部原断言。106项限定单元、303份源码类型及两项接管通过事件、剩余两项恢复独立JUnit通过（分步验证，非完整身份门禁）；新head托管CI仍待，不增加完成子步骤。 仍保留170任务、154条已证子范围、622组剩余工作、0整卡验收；T013仍13C/3R。

2026-10-24安全续批：main40027591632实际因运行2/质量3条依赖匹配失败；filelock4.2.1、setuptools84.1.0已核验官方制品并完成Linux工程验证，新精确head CI及有效扫描仍待，不计新增完成。 [回执](../00-project/validation/python311-security-followup-20261024.json)；仍154条已验证子范围、622组剩余工作、0整卡验收。

2026-10-24续批：[质量工具安全修复与固定身份诊断](python311-quality-identity-followup-20261024.md)。4f两路CI失败均保留，新精确head门禁待验；113项诊断及工具缓存修复不折算整任务完成，原完成/剩余计数不变。
