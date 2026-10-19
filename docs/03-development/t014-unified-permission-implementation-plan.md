# T014 统一权限代码与回归实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking. 本计划建议当前会话直接逐项执行；仅在用户明确选择委派时使用子代理。

**Goal:** 实现当前42个业务操作的统一最小权限入口、真实只读权限事实查询及适用参数化回归，明确另外31个契约操作与正式授权/交接未完成范围。

**Architecture:** 从唯一OpenAPI派生权限目录，在业务路由入口统一认证与检查。专用只读数据库角色返回当前绑定事实，独立策略端口才形成明确决定；缺策略保持拒绝。案件/对象/来源检查继续由现有服务执行。

**Tech Stack:** 既有Linux/Miniforge Python3.10.22、FastAPI、SQLAlchemy/psycopg、PostgreSQL16、pytest；原100包锁及现有依赖不变。

**Spec:** [已获认可的统一权限设计](t014-unified-permission-design.md)，连同[权限矩阵](../08-security/t014-interface-scope-matrix.md)和[异常测试设计](../09-testing/t014-authorization-test-design.md)。用户2026-10-19明确认可本计划，由当前会话直接逐项实施；这不是正式授权、运行采用或整卡验收。

## Global Constraints

- 仅当前Linux/py310/CPU研发环境；Python候选继续暂缓。
- 六角色正式允许值、职责冲突、分类/用途及撤销SLA未确认；不建立正式授权种子，不以候选职责放行。
- 迁移为新增0006，前五项迁移、外部API字段/路径、原始材料和运行锁不变；只在隔离数据库执行。
- 现有42个业务操作进入实际HTTP权限回归；另外31项未挂载操作单列，不把404作为权限成功证据。
- 恢复私钥继续留G盘U盘；共享身份服务切换、bootstrap退役及真实恢复需满足实际交接、恢复和维护前置。
- 测试在Git外源码快照和专用测试实例执行，保存失败过程及测试生成报告，不覆盖共享源码或其他工作流。

## Review Focus

1. 认证后权限查询期间身份映射撤销或令牌到期：读取器重验同一issuer/subject及预期user/org，查询结束再核对期限，失败拒绝；任务1、2测试固定。
2. 多条Authorization、空Bearer或非Bearer：统一入口精确拒绝，不能由另一个旧检查入口接受；任务1、3测试固定。
3. 策略服务返回另一用户/单位/权限/事实摘要或旧版本决定：返回503而非接受布尔真；任务2测试固定。
4. 新路由在应用建立后、启动前追加，或者方法/operationId重复：启动覆盖审计失败；任务3测试固定。
5. 合法动作请求重放旧游标/幂等回执时权限已撤销：权限在业务回执读取前检查，后台执行另重验；任务4测试固定。

## 文件与接口安排

| 文件 | 单一职责 |
| --- | --- |
| backend/business_app/permissions/types.py | Principal、PermissionFact、PermissionDecision及权限端口类型 |
| backend/business_app/permissions/catalog.py | 从OpenAPI精确读取操作、方法、路径与41个权限；不维护第二权限表 |
| backend/business_app/permissions/directory.py | 专用非管理连接，只调用权限事实函数 |
| backend/business_app/permissions/policy.py | 事实/决定精确绑定、明确拒绝和缺策略故障 |
| backend/business_app/permissions/guard.py | require_permission、统一路由依赖与启动覆盖审计 |
| backend/business_migrations/0006_permission_lookup.sql | 只读事实函数与专用角色；无业务角色种子 |
| backend/business_app/identity/tokens.py | 复用现有认证逻辑，额外暴露已验证主体上下文，原authenticate返回Actor保持兼容 |
| backend/business_app/auth.py、uploads/service.py、history/router.py、controls/common.py | 统一读取请求已验证主体，保留数据范围及写入前复查 |
| backend/business_app/main.py、errors.py | 路由挂载和覆盖审计；401提示头和通用权限错误登记 |
| tests/platform/test_t014.py、tests/business/test_t014_permissions.py | 入口与全42操作拒绝参数化；真实SQL权限/撤销和数据范围回归 |
| tests/business/conftest.py及实际使用create_app的业务测试 | 显式注入合成测试权限端口，禁止默认允许；不删除或放宽原业务断言 |
| scripts/verify_t014_permissions.py、.github/workflows/ci.yml | 只发布脱敏结果及源码绑定；将新增测试接入实际门禁 |

新增permissions包的`__init__.py`保持最小，无隐式账号/配置初始化。

已查明直接导入业务应用工厂的既有测试为`test_adapters_and_execution.py`、`test_authorization.py`、`test_controls.py`、`test_foundation_errors.py`、`test_uploads.py`和`test_upload_validation.py`（均位于tests/business）；间接复用它们的测试保持原输入/断言。OpenAPI的Problem.code是1—128字符字符串，未枚举固定代码，因此新增PERMISSION_REQUIRED不改变结构；仍需实测其403响应满足既有Problem Schema。

### Task 1: 固定认证上下文和权限目录

**接口：** `Principal(actor: Actor, issuer: str, subject: str, expires_at: int)`；`MappedTokenAuthority.authenticate_principal(bearer: str) -> Principal`；原`authenticate(bearer) -> Actor`复用它。`load_catalog(root: Path) -> dict[str, OperationPermission]`，OperationPermission含operation_id、method、path、permission和公开例外状态。

- [ ] 编写`test_authenticate_principal_preserves_exact_issuer_subject_mapping`、`test_principal_expired_after_database_lookup_is_rejected`和`test_catalog_matches_all_73_operations_and_41_permissions`；断言用户/单位/issuer/subject完全一致，过期401，目录精确73/41/1公开例外。
- [ ] 运行`python -m pytest tests/platform/test_t014.py tests/business/test_token_identity.py -q`，确认新增能力缺失导致预期失败；保存安全失败ID。
- [ ] 实现上述接口，不保存令牌正文，不建立跨请求主体缓存；原T013令牌异常/故障语义保留。
- [ ] 运行上述测试及`tests/platform/test_t013_tokens.py`，预期全部通过、零失败/错误/跳过；按实际输出记录数量。
- [ ] 提交本任务源代码和测试，记录源码摘要及T013回归影响。

### Task 2: 只读权限事实、策略决定与增量迁移

**接口：** `PermissionFact(principal: Principal, permission: str, eligible: bool, version_digest: str)`；`PermissionDecision(actor: Actor, permission: str, allowed: bool, policy_version: str, fact_digest: str)`。`PermissionReader.read(principal: Principal, permission: str) -> PermissionFact`；`PermissionPolicy.version: str`、`decide(fact: PermissionFact) -> PermissionDecision`；`DirectoryPermissionAuthority.check(principal: Principal, permission: str) -> None`。

**SQL接口：** `mt.lookup_permission(wanted_issuer text,wanted_subject text,expected_user uuid,expected_org uuid,wanted_permission text)`，返回精确映射身份/用户/单位版本、所需权限码、当前有效绑定事实及参与绑定的稳定ID/版本JSON。读取器对排序后的规范事实计算version_digest。无有效身份返回零行并按认证失效拒绝；有效身份但无绑定返回eligible=false。函数只检查事实，不返回正式ALLOW。

- [ ] 编写`test_permission_lookup_role_cannot_read_or_write_catalog`、`test_permission_lookup_rejects_mismatched_identity_or_unit`、`test_revoked_or_expired_binding_is_ineligible`和`test_old_or_misbound_policy_decision_is_unavailable`。断言专用角色无直接目录表读写/管理权；失配身份拒绝；expires_at相等失效；错误决定503；缺策略503；已认证无许可403。
- [ ] 运行`python -m pytest tests/business/test_t014_permissions.py tests/business/test_migrations.py -q`，核对新增函数/实现缺失的失败。
- [ ] 新增0006及读取/策略模块。角色必须NOLOGIN/NOSUPERUSER/NOBYPASSRLS/NOCREATEROLE/NOCREATEDB/NOREPLICATION；撤销PUBLIC执行，固定search_path，无直接表授权。权限端口缺策略时不调用正式动作；无管理账号兜底。
- [ ] 追加从0005升级、全新建库、失败事务、账本摘要、既有记录保全和隔离备份恢复测试；执行同一命令，预期全部通过且旧五项迁移摘要不变。
- [ ] 提交本任务。现有共享数据库不执行该迁移，不创建正式权限数据。

### Task 3: 统一入口、默认保护与401响应

**接口：** `require_permission(permission_code: str)`返回FastAPI依赖；`authorize_business_route(request: Request) -> None`从已匹配路由精确找权限；`audit_protected_routes(app: FastAPI) -> None`检查所有已注册业务路由。`create_app(..., permission_authority: PermissionAuthority | None = None)`新增显式可选端口；默认缺配置拒绝。请求内保留Principal并在复用前核对同一认证头绑定及有效期限。

- [ ] 编写`test_all_42_mounted_business_operations_require_authentication`、`test_all_42_operations_deny_missing_permission`、`test_new_or_duplicated_business_route_fails_startup_audit`、`test_business_401_has_bearer_challenge`及`test_duplicate_authorization_header_is_rejected`；预期固定401/403/配置失败，不能接受宽泛状态集合。
- [ ] 运行`python -m pytest tests/platform/test_t014.py -q`，确认未挂统一入口前新增反例失败。
- [ ] 在main的三个业务router挂载统一依赖并在启动时审计；内部推理保持专用服务身份。补BusinessError的401提示头，登记`PERMISSION_REQUIRED`通用403错误，Problem字段结构保持。
- [ ] 统一既有主体提取入口；保留authorize_case、RLS、authorize_source及后台重验。getCurrentUser必须先通过identity.read，其case.read不是该权限的别名。
- [ ] 运行该测试集和原错误/内部推理回归；42路由需全部401/403明确通过，31未挂载只列未实现。提交本任务。

### Task 4: 全量适用权限回归和业务副作用核验

**接口：** 测试夹具显式提供合成Principal、PermissionAuthority和按测试建立的授权集合；共享测试辅助代码不得进入生产入口。既有业务测试的允许前提必须明确，新的T014反例逐一撤销其中一个条件。

- [ ] 建立按42个operationId列出的真实请求夹具及对应资源；全部使用有效UUID/请求头/JSON及必要版本/幂等前置。编写六角色默认拒绝、撤销后旧会话、同单位跨案件、跨单位、历史/下载对象替换与游标/回执重放反例，先确认缺少检查时失败。
- [ ] 将当前业务测试的create_app调用显式接入测试权限端口，逐文件复用原夹具与断言；不以自动全角色允许修复测试。
- [ ] 对每组反例检查数据库、对象、outbox/队列与成功回执无新增业务副作用；案例要求失败审计时分别核对，不把失败审计当越权写入。
- [ ] 在隔离源码快照执行`python -m pytest tests/business tests/platform/test_t014.py tests/platform/test_t013_tokens.py -q --tb=short --junitxml PRIVATE_PATH`，预期零失败/错误/跳过；保留原失败与修复过程。单独导出42操作/场景通过表及31未实现清单。
- [ ] 执行后台授权/取消/重试和事务连接复用回归，记录未解决的并发/撤销SLA边界；提交本任务。

### Task 5: 接入门禁、审查与状态同步

**接口：** `scripts/verify_t014_permissions.py`在明确隔离目标运行上述检查，只发布计数、operationId、源码摘要和未执行项，退出非零时门禁失败；原始凭据/日志留Git外。

- [ ] 将T014测试及路由覆盖审计纳入engineering，增加受控失败探针验证新检查确实阻止通过；不删除原32项检查。
- [ ] 执行`python scripts/dev.py format-check`、`python scripts/dev.py lint`、`python scripts/stage_three_types.py check`、`python scripts/validate_access_control_model.py --run-tests`和适用身份回归。源修改后的CI必须对应精确提交，旧CI不作为新增代码验收。
- [ ] 更新本批权限矩阵、测试设计实际状态、T014卡片、任务台账和分步导航；只增加有代码和实测证据的子步骤，正式权限/T013交接恢复未通过时整卡不关闭。
- [ ] 按既有生成器刷新NOT_FROZEN候选及全仓清单，执行`python scripts/validate_stage_one.py`、`python scripts/validate_inputs.py`、`python scripts/validate_repository_docs.py`、`python scripts/validate_documentation_completion.py`及任务/排期漂移检查。
- [ ] 复核产品代码、迁移最小权限、正反断言、12份原件/旧锁/旧迁移摘要和暂缓项；修复实际问题后提交。同步GitHub开发分支和Linux源码，核验托管CI并保留失败/在途状态与服务器回执。

## 本批关闭和后续工作

任务1—5完成后仅声明统一权限代码及当前42操作适用回归的实际范围。T014整卡还需要正式授权和实际验收条件；31未挂载操作属于对应业务功能任务，不能由权限空壳代替。T013真实密钥测试、本人MFA接管、共享采用和恢复单列推进，未得到真实证据不勾选。

该计划不包含把恢复私钥上传Linux、在对话输入口令、共享停写/切换或bootstrap删除。相关操作采用独立本人步骤和维护方案；不会自动实施T015及后续业务任务。

自查结论：设计中的目录/42操作/只读事实与策略隔离/新增迁移/401语义/22类回归/CI和状态分别对应任务1—5；五项Review Focus均有明确归属测试。正式权限规则、31未挂载业务功能和T013本人交接/真实恢复仍是单列未关闭项，不以文档或夹具测试替代。
