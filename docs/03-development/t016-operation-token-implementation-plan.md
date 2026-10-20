# T016 operation_token 隔离后端实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking. 本页为已授权执行的隔离实施计划；实际执行状态见本页与专项证据，计划文字不替代运行结果。

**Goal:** 在现有公共契约下实现案件级操作令牌签发，以及由真实业务调用方传入同一数据库事务的原子消费内核，逐项验证一次性、短时、当前批准和精确绑定。

**Architecture:** 复用 T014 的主体、功能资格、对象事实、独立人员与事务栅栏，以及 T015 的 LOOKUP／CASE 范围和固定元数据查询。公共签发接口沿用 `OperationTokenRequest`／`OperationToken`；服务端从批准记录确定案件、对象类型和受控动作，客户端字段只是待核对的声明。消费内核不创建公共消费端点，也不自行提交事务；动作执行器必须先具备自己的权限和业务前置条件。

**Tech Stack:** 既有 Linux／Miniforge py310／CPU、FastAPI、SQLAlchemy／psycopg、PostgreSQL16、pytest，密码摘要及推荐的 HMAC 方案使用标准库；保持原100包锁和现有 Node 锁，Python候选继续暂缓。

**Spec:** [源任务 T016](../../tasks/platform/T016.md)、[T001—T123执行顺序](t001-t123-development-sequence.md)、[唯一业务 OpenAPI](../03-api/openapi.yaml)、[共用接口规则](../03-api/common-interface-rules.md)、[接口字段映射](../04-database/api-field-mapping.csv)、[六角色隔离规则](../08-security/t014-six-role-rule-proposal.md)、[T014已批准隔离实施计划](t014-isolated-six-role-implementation-plan.md)、[T015实施计划](t015-data-scope-implementation-plan.md)。

## 当前状态与执行边界

编制日期：2026-10-21。用户已授权 T001—T123 逐批开发；主会话正在实际实施现有前端／启动边界硬化及对应验证、三端同步，见[前后端实施计划](business-console-implementation-plan.md)、[开发证据](../00-project/validation/development-continuation-report.json)和[同步回执](../00-project/server-sync-receipt.json)。本页不替代该批实际执行，不把本计划生成计为 T016 新代码完成，也不预填后续 CI 或同步成功。

编制时本页仅为计划；用户随后授权当前会话实施，实际负责人和复核人均为徐昌胜。当前已完成案件签发、同根消费及0011隔离代码，正在形成最终严格门禁和三端源码同步证据；见[开发进度](../00-project/validation/t016-development-progress.json)、[令牌扩展](../04-database/operation-token-extension.md)。共享/预览库未升级0011，真实消费者及正式采用仍保留各自前置。

## P01实际技术裁定

用户授权执行后采用D01的单值 `case task + seal → sealEvidence` 与D02的独立HMAC-SHA256秘密重建；公共字段不变。密钥只接受当前key_id及当前材料，轮换即拒绝旧凭据，不启用下文讨论的旧key宽限窗口。60秒仅为具名隔离测试输入，正式token TTL与密钥保管尚待采用决定。

当前task真实结构为单asset；来源快照仅按 `analysis_task.asset_id → media_asset.source_id → source_registry` 同根读取，绑定资产／来源ID、授权版本、状态、用途、截止与行版本，纳入已有request_sha256。未发明params列或多输入来源契约。三项有意义RED复现纯版本及本事务来源用途失效后，新增14项组合测试连同适用回归共74项通过；独立质量回执全部通过，完整门禁仍按进度报告核验。正式跨人委托、确认人与执行人角色关系及真实消费者单列。

## Global Constraints

- 仅在当前 Linux／py310 内部隔离研发实施；SQL验证使用新建随机命名的独立 PostgreSQL16 数据库和自建无敏感夹具。沿用[隔离数据库规则](../04-database/database-validation.md)和[业务开发入口](../10-deployment/business-development-runbook.md)，不向已有共享库或现有预览库应用0011。
- PR01／PR02／PR04 已批准的隔离输入继续有效：完整六角色集合；高风险用途两名独立批准人且不含申请／执行人；审批TTL1800秒、无跨请求正向授权缓存及适用撤销／提交前重验。审批TTL不是 operation_token TTL。
- 正式分类、共享采用、真实身份／委托／来源事实、生产发布及整卡验收仍按各自条件处理。缺这些正式条件不阻止内核编码和明确合成适配器下的隔离验证；普通启动缺可信提供方时继续401／503，不安装测试成功提供方。
- 外部请求／响应结构保持不变：签发请求仍为 `approval_id/object_id/object_version/purpose`，响应仍为 `operation_token/expires_at/object_version`，必填 `Idempotency-Key`；不增加客户端 `actor_id/org_id/case_id/approved/action` 或额外必填 `If-Match`。
- 实施前为42个外部操作、31个未挂载；本批实际挂载 `issueOperationToken` 后为43／30，总目录仍为73。PoC的health与内部推理1个入口分别记录，不混入这组计数。执行前以实际提交重新枚举，禁止只修改数字使门禁通过。
- 仅新增 `backend/business_migrations/0011_operation_token.sql`，执行前核对编号未占用；0001—0010的文件字节及账本摘要不改。无正式审批／身份／策略种子，无全单位业务读取或管理员隐式绕过。
- 令牌明文不进入数据库、幂等回执、日志、异常、审计详情、URL、Git或浏览器持久存储。批准链、对象事实、运行结果和审计历史不覆盖；失败／恢复状态可观察。

## Review Focus

1. 同一用户合法属于A、B两个案件，A事务却使用B的批准或令牌：数据库RLS、固定定位与服务绑定都必须拒绝；不能仅测试完全无成员资格者。
2. 相同幂等键的请求已提交但响应丢失：重试不能签发第二个有效凭据，也不能为重放把原凭据明文写进 `idempotency_record`。
3. 批准在签发后撤销、来源用途失效、人员关系变更或恢复代际切换：消费时重验当前事实，旧凭据不能继续放行。
4. 两个消费者竞争、业务写入失败或事务开始后令牌才过期：最多一笔成功；失败回滚令牌消费与业务写入；以实际消费时刻核验期限。
5. purpose相同但业务动作、对象类型或版本不同：令牌不能跨动作使用；歧义映射和未知规则必须拒绝，确认按钮不替代独立批准。

## 实施前核实的缺口及公共契约裁定点

以下保留编制时缺口；当前已按P01—P04补对应隔离代码，最终状态以实际报告为准。编制时 `controls/router.py` 没有签发路由。`permissions/object_facts.py` 的 `BODY_SCHEMAS/SUPPORTED_OPERATIONS/resolve_http/_validate_target` 没有该操作；`conditional.py` 没有 `six_role.py` 已引用的 `CONFIRM_CASE/CONFIRM_MODEL` 条件分支。Python `scope_catalog.lookup_spec` 与0010中的 `mt.scope_lookup_kind_allowed` 也没有登记该操作。因此仅挂载路由会在完整权限／范围链中拒绝，不能用简化夹具绕过这些缺口后声称接入完成。

### D01：现有请求能否确定精确动作

**现有请求本身不足以确定任意精确动作。** `purpose` 是最长128字符的字符串，不是operationId；请求也没有对象类型。批准记录能够补齐对象类型、案件、策略和版本，但仍需要可信且单值的 `(object_type, purpose, policy_version) → action` 规则。不能默认同purpose的所有动作都可消费。

**推荐方案，尚未因本页生成而采用：** 保持公共字段不变，引入服务端规则端口，返回唯一的内部action与token TTL；签发时持久化该action及规则版本，消费方传入自己的固定operationId核对。最低正例可选已有DDL明确约束的 `task + seal → sealEvidence`；已有审计实现的 `operation + report_export → exportAudit` 是另一可审查映射，后者的公共消费者接入另有D03契约差异。`task + report_export → createReport` 等未核实语义不能自动认定。首批只开放经本批技术裁定的无歧义组合，未知／多值／组织级模型组合503；测试用规则明确标注合成来源。

执行P01时记录实际选择、规则版本与测试；生产规则发布仍另行批准。若业务必须让同一批准用途由客户端选择多个动作，应先提出新增action字段的契约变更，再同步Schema／映射／迁移／客户端，不能在本批悄悄扩展公共请求。

### D02：幂等重放与令牌秘密

共用规则要求同主体、操作、摘要的相同幂等键保持原效果；现有 `ControlReceipts` 继承的通用实现会将完整响应JSON写入 `response_ref`。直接保存 `OperationToken` 响应将泄露明文凭据，与字段映射“DB只存token_sha256”冲突。

| 备选 | 可审查行为／限制 | 本计划建议 |
| --- | --- | --- |
| 独立密钥进行确定性HMAC派生，数据库只保留哈希和非秘密重建元数据 | 同一签发记录重建同一个不可预测凭据；重试仍重验主体、批准、期限与未消费状态；不生成第二条令牌。必须有独立私密密钥、key_id和恢复代际边界 | **推荐，尚待本批技术裁定**；可保持现有公共结构及同键重放原结果 |
| 随机凭据，仅内存保存重放材料 | 进程重启／多worker后无法重建原响应；不得失败后静默另发新凭据 | 不作为完整幂等方案 |
| 随机凭据，外部短期加密秘密存储支持重放 | 增加私密存储、独立加密密钥、密文生命周期与恢复要求；仍需明确是否允许可恢复凭据存储 | 本批不推荐，不将现有数据库JSON当秘密存储 |
| 首次返回后，同键同摘要一律409 | 无法遵守现有原效果重试预期，网络不确定时用户不能取得原凭据 | 须先明确改变公共幂等语义，不作为本批默认 |

推荐方案使用域分离的 HMAC-SHA256 与不可猜测签发标识，输入绑定 `token_id/actor/org/case/approval及其版本/object_type/object_id/object_version/purpose/action/expiry/policy_version/recovery_generation/key_id`；输出为至少256位伪随机秘密。`operation_token.token_sha256` 保存完整凭据的SHA-256。非秘密元数据不能单独生成有效凭据，哈希本身不能作为凭据接受。

密钥必须独立于cursor_secret、PoC令牌、身份平台签名密钥和批准策略摘要；通过仓库外受限私密文件／显式注入端口供给，不设内置密钥。普通启动缺密钥／key_id／明确token TTL时503。key_id不是秘密；密钥轮换后只在原有效期和未撤销代际内允许重建，不延长TTL；密钥缺失返回不可用，不另发新token。恢复旧库时原recovery_generation失效，必须拒绝旧记录而不是重建旧凭据。

本页不把HMAC方案、具体token TTL或key生命周期当正式批准。“只返回本次”须明确解释为只在受控响应返回、不落明文存储；若业务要求凭据绝不可再次返回，则与同键秘密重放有真实冲突，P01须记录裁定后再实现该分支，不能两种语义同时宣称满足。可先编写不依赖该选择的范围、原子消费与故障测试。

### D03：哪些消费者需要公共契约变化

| 消费者 | 现有契约／实现 | 本批处理及后续前置 |
| --- | --- | --- |
| `sealEvidence` | `SealRequest` 已有approval_id、operation_token、task/run/result及证据ID；业务应用未挂载 | 后续动作实现可保持请求字段；仍需核定批准用途、实际快照及动作原子写入，不把seal当unseal |
| `createReport` | `ReportCreate` 已有approval_id、operation_token；业务应用未挂载 | 不因本批新增请求字段；其purpose/action及报告生成规则仍需在对应任务核定 |
| `rolloutModel` | `Rollout` 已有approval_id、operation_token、expected_version、mode等；组织级发布尚无真实执行链 | 本批拒绝组织级签发；后续核定activate／rollback等子动作区分，现有token请求不足以默许所有mode |
| `exportAudit` | `AuditExport` 只有时间窗、case_id、purpose、approval_id，`additionalProperties: false`；现有真实导出路径未消费token | **需要另行审查公共契约差异**：若要求此消费者携带token，至少同步OpenAPI／映射／生成类型／后端／前端／测试与兼容策略；本批不悄悄增加必填token、不把未接入导出标成已由token控制 |
| 删除、证据解封、其他批量导出 | T016源范围包含这些动作，但当前无可直接复用的完整消费者契约／实现 | 在原任务中补明动作、版本、审批和恢复契约；不得新增空成功接口填覆盖率 |

因此最小“签发＋内部同事务消费内核”**可以保持公共契约不变**，但必须落实D01单值服务端映射和D02秘密重放裁定。其验证只能证明该子范围；不能声称所有高风险消费者已接入。

## 文件与接口

所有新增文件名为本计划预定位置，实施前核对未被另一批占用。

| 文件 | 具体职责 |
| --- | --- |
| `backend/business_app/controls/operation_tokens.py`（新） | 签发、当前批准绑定、秘密重建／摘要核验、同连接消费；不打开第二个消费事务、不安装默认成功规则 |
| `backend/business_app/controls/providers.py` | 新增内部 `OperationTokenRule` 和规则／密钥端口；规则返回唯一action、版本及正token TTL；秘密对象repr不泄露材料 |
| `backend/business_app/main.py`、`controls/router.py` | 显式装配服务及唯一签发路由，沿用权限依赖和源响应验证；缺提供方保持拒绝 |
| `backend/business_app/permissions/object_facts.py`、`conditional.py`、`scope_catalog.py` | 新操作body验证、批准定位、案件目标解析、CONFIRM_CASE完整条件和固定lookup登记；CONFIRM_MODEL继续明确未开放 |
| `backend/business_app/settings.py`、`development.py` | 仅在D02裁定需要时增加显式内部配置／注入；保持当前启动硬化、拒绝特权连接和测试提供方缺省为空，不重做原前端批次 |
| `backend/business_app/controls/receipts.py`（仅必要时） | token签发专用非秘密回执入口；不改变其他控制操作的既有完整回执语义 |
| `backend/business_migrations/0011_operation_token.sql`（新） | action／批准快照／key／规则与代际的必要内部绑定字段、约束、固定lookup登记和消费防护；不修改0001—0010 |
| `tests/business/test_t016_operation_tokens.py`、`test_t016_operation_token_recovery.py`（实际SQL升级／约束用例位于后者） | HTTP＋当前完整权限链、真实SQL竞争／回滚／升级／恢复／秘密边界；只用合成身份与规则 |
| `tests/business/http_fixtures.py`、`test_controls.py`、`t014_requests.py` | 明确新签发请求及批准资源，新增端口只在测试工厂注入；不扩大原测试身份的正式含义 |
| `tests/platform/test_t016.py`（新） | 单值动作规则、严格内部类型和密钥／TTL拒绝矩阵；落实源卡原计划测试位置 |
| `tests/business/test_migrations.py`、`test_t015_scope_sql.py`、`test_t014_object_rules.py`、`test_t014_runtime.py` | 0010→0011、SQL/Python目录一致、43操作真实资源拒绝和无副作用；保留原断言含义 |
| `tests/platform/test_t014.py`、`test_t014_gate.py`、`test_t015_gate.py` | 新挂载操作的认证／无权限／无策略／依赖失败矩阵及严格报告解析；不以404当权限通过 |
| `scripts/verify_t014_permissions.py`、`verify_t015_scope.py` | 43／30目录、必需nodeid／源摘要、固定新测试和报告依赖；范围改变必须实际执行验证 |
| `docs/08-security/t014-interface-scope-matrix.{json,md}`、`docs/09-testing/t014-isolated-operation-coverage.md`、`t015-data-scope-coverage.{json,md}` | 由实际挂载及调用证据更新矩阵、具体测试、未挂载清单；目录覆盖不等于正式ALLOW |
| `docs/04-database/operation-token-extension.md`（新）、`api-field-mapping.csv` | 记录0011的实际字段／约束与兼容边界；只补内部存储关系，公共字段不变 |
| `config/stage-three-profile.json`、`scripts/run_ci.py`、`.github/workflows/ci.yml` | 核查新脚本／文件已进入既有质量与实际CI命令。已有目录级质量覆盖足够时不作无意义修改；如增加必需入口必须实际接入和故障验证 |
| `docs/00-project/validation/t016-operation-token-report.json`（新）、T014/T015及business报告、`tasks/platform/T016.md`、任务台账 | 最终记录源码摘要、实际命令／结果和剩余消费者；本计划阶段不修改或预填这些文件 |

建议内部接口如下，P01裁定后固定，公共类型不受影响：

- `OperationTokenRule(action: str, version: str, ttl_seconds: int)`：frozen；必须非空、TTL为正整数，bool不当int。
- `OperationTokenRuleProvider.resolve(scope: Scope, approval: Mapping[str, Any]) -> OperationTokenRule`：可信服务端单值映射；未知组合抛业务不可用，不接收客户端action。
- `OperationTokenKeyProvider.get(key_id: str) -> bytes`：显式私密端口；未知key不可用，不记录返回值；轮换／恢复规则由同一端口执行。
- `OperationTokens.issue(scope: Scope, body: dict[str, Any], request: Request, key: str) -> dict[str, Any]`：返回源 `OperationToken`；根范围来自已核对批准记录；事务内核验与保存，不保存秘密回执。
- `OperationTokens.consume(connection: Connection, scope: Scope, token: str, *, approval_id: UUID, action: str, object_id: UUID, object_version: int, request: Request) -> None`：要求传入连接属于当前相同DataScope／证据／栅栏；按当前批准记录校验object_type／purpose／规则／版本／代际；在同连接条件消费，不自行commit、不把token当业务权限。

消费成功后的业务写入由调用方执行，并由相同根事务提交；内核测试用明确标注的合成事务副作用证明原子性，不创建伪业务消费者。未接入的公共动作保持原状态。

## 实施步骤

### P01：固定动作、秘密与权限范围的技术裁定

- [ ] 重新读取本页输入、主会话硬化完成后的实际源码／CI／同步回执；记录基线提交与工作树状态，不覆盖其他批次未提交改动。
- [ ] 记录D01首批唯一映射、D02选择、明确token TTL及key／代际行为。推荐值和方案未被本页自动批准；无正式值时隔离测试使用具名合成值，普通入口缺配置拒绝。
- [ ] 在 `tests/platform/test_t016.py` 写失败测试：歧义action、未知用途、组织级模型、非法TTL／key、客户端附加case/action字段均拒绝；确认按钮不能产生批准。
- [ ] 实际运行上述测试并保存有意义RED；不能把导入失败、零测试或计划文字当运行证据。实现最小内部规则／类型后转GREEN。

### P02：0011增量与固定元数据入口

- [ ] 编写0010→0011升级、空库全链、重复迁移no-op、旧摘要不变及原故障原子性测试，再编写0011。
- [ ] 新绑定字段必须具有明确存储版本；推荐为旧行保留可辨识的legacy空绑定、新代码拒绝其签发／消费，禁止从历史purpose猜测action或给旧token补造批准。若约束要求所有历史行已有新字段，应先实际检测并给出前向修复路径，不删除旧记录或悄悄延长有效期。
- [ ] 同步 `scope_lookup_kind_allowed` 与Python固定目录：只允许签发所需approval及明确目标kind的最小元数据，LOOKUP仍只读、无payload／token哈希／秘密出口。0011不打开operation_token通用lookup或任意SQL表名。
- [ ] 增强绑定不变性和实际消费时刻检查；旧触发器的 `now()` 固定在事务开始，不能单独证明长事务到期拒绝。保留跨单位／案件RLS及runtime最小ACL。
- [ ] 实测旧行保留、跨案件批准／主体关联拒绝、无BYPASSRLS所有者、SQL/Python全目录一致、0011失败全回滚。若增加字段，更新实际列数断言及扩展说明；不把原849直接改成猜测数。
- [ ] 回退策略为停止使用新服务、保留迁移和记录、向前修复；不能用退回旧代码重新接受legacy／旧代际token。共享升级仍另行审查，不因隔离库通过即安装到共享库。

### P03：案件级签发与完整鉴权链

- [ ] 增加 `issueOperationToken` 到body校验、固定定位、目标解析及条件事实；从批准ID取得可信案件与对象类型，核对请求object/purpose/version后构造CASE范围。
- [ ] 完整链测试使用真实SQL角色／对象事实与显式合成补充事实，不只使用无条件FixtureConditionals。核验operation.confirm资格、当前请求／执行人、独立批准人员、策略版本、来源用途、目标与task/run/result版本及撤销状态。
- [ ] 实现签发和专用幂等回执：相同键／摘要／主体在当前仍有效且未消费时取得同一凭据；不同摘要409，跨主体不能取得原凭据。过期／消费／撤销／代际变化后不重签或延长TTL；普通入口缺规则／key／事实拒绝。
- [ ] token到期不晚于明确token TTL、批准和适用授权／规则的真实截止；每次重试重新检查。用响应Schema验证200及ETag／request_id约定，不增加未声明的必填条件头。
- [ ] SQL、回执、日志／异常／审计只出现允许字段；测试精确扫描新令牌明文未落库或日志。公开报告不收录原始pytest堆栈／DSN／key／token。

### P04：同事务消费、竞争与恢复

- [ ] 先写真实SQL RED：同token两连接竞争最多一成功；消费后合成业务写入报错导致全部回滚；同令牌的后续合法事务可重试，已提交消费再次拒绝。
- [ ] 用原子条件更新或锁定＋条件更新检验token哈希、actor/org/case、批准ID、action、对象/版本、存储版本、expiry、consumed_at、规则与恢复代际；成功时同连接追加审计。哈希字符串、伪token_id、另一action与不属于当前根范围的Connection均拒绝。
- [ ] 签发之后分别撤销批准、撤销成员／角色／委托、改变来源用途／版本、改变人员关系、改变对象/run/result版本、轮换key／恢复代际；消费前与根提交前复核，不能因持有token跳过T014栅栏。
- [ ] 事务开始时有效但实际消费时过期必须拒绝。token短期有效性与原五秒事实刷新含义分开；不把五秒当所有事务或作业超时。
- [ ] 明确审计拒绝路径：沿用请求失败审计／安全记录边界；成功消费审计随业务事务回滚。若另存拒绝事件，不在已失败事务内假称已持久化，也不记秘密。

### P05：43／30目录、工程回归及证据

- [ ] 枚举实际ASGI路由与唯一OpenAPI：原42项逐个保留，只新增issueOperationToken，未挂载清单从31删该项得到30；运行时OpenAPI发布43外部＋既有内部入口，完整源目录仍73。
- [ ] 同步 `t014_requests.py` 的真实资源请求、`test_t014_runtime.py` 的副作用前快照、新操作四类拒绝用例；给签发准备真实合成批准资源，不能用404／422替代401／403／缺策略503。
- [ ] 同步测试函数名／参数化nodeid和 `verify_t014_permissions.py`、`test_t014_gate.py` 的严格必需清单；现有 `test_all_42_*`、计数42／31与report解析必须一致迁移。删除任意新操作证据、跳过或零测试仍导致失败。
- [ ] 更新T014接口矩阵的实际runtime_route、目标解析与证据，T015固定调用／未挂载清单和源摘要；T015 gate新增签发与token范围关联用例，不降低原九类sentinel或已有安全断言。
- [ ] 仅在干净、精确源码快照顺序执行必要SQL回归；同一管理实例不并跑SQL套件。通过后跑既有完整business verifier、T014/T015门禁和当前工程CI；保留原命令／超时策略，不因本批新增功能削减范围。
- [ ] 源公共结构未改时，生成类型与生成文档漂移检查应保持无变化；如D03另批获准改契约，必须从OpenAPI再生成，不能手改 `shared-contracts/generated/business-api.d.ts`。
- [ ] 按实际提交记录验证命令、开始／结束、通过／失败／未执行及源码摘要；托管CI绑定确切SHA和run URL，三端同步与现有运行进程是否加载新源码分别记。回执文件不能预先证明其自身未来提交的CI。

## 后续执行命令与证据要求

下列是可复用实施入口，并非每条命令均单独执行；本批实际命令、源码和结果见[进度记录](../00-project/validation/t016-development-progress.json)及其专项回执。`python`须为 `/opt/conda/glwy/envs/py310/bin/python`，测试在私有源码快照运行；`PYTHONPATH`按既有harness绑定快照根和backend，凭据从既有私密测试配置读取，不复制到计划或命令行。先执行统一入口help/status核对环境和目标。

```text
python scripts/dev.py help
python scripts/dev.py status
python -m pytest tests/platform/test_t016.py -q
python -m pytest tests/business/test_t016_operation_tokens.py tests/business/test_t016_operation_token_recovery.py tests/business/test_migrations.py -q
python -m pytest tests/platform/test_t014.py tests/platform/test_t014_gate.py tests/platform/test_t015_gate.py -q
python scripts/dev.py lint
python scripts/dev.py format-check
python scripts/dev.py type-check
python scripts/verify_generated_contracts.py
python scripts/verify_business_foundation.py run
python scripts/verify_t014_permissions.py run
python scripts/verify_t015_scope.py run
python scripts/verify_t016_tokens.py run
python scripts/verify_t016_tokens.py failure-probe
python scripts/validate_inputs.py --task T016
python scripts/validate_stage_three.py
```

按既有工程工作流运行完整CI，不在本计划执行现有共享栈的build／integration／restart。源卡资料校验仍是 `implementation_not_tested` 类型证据，不能代替上面的实际SQL／HTTP／故障验证；工程整体验证与专项验证分别保存。新增T016报告至少含任务／子范围、源码SHA／脏状态、迁移摘要、实际nodeid和计数、无skip／零测试判定、43／30清单、D01/D02裁定、formal_accepted=false及剩余消费者。

## 本批完成定义与保留事项

- [ ] P01—P05适用代码与测试实际完成；案件级签发沿用公共结构；同事务消费内核通过正常、重放、过期、换用户／用途／对象／版本、撤销、竞争、回滚与恢复测试；默认启动仍无测试授权。
- [ ] 0011在新隔离库完成空库及升级验证，0001—0010摘要未改；既有迁移／权限／范围／日志／前端硬化回归通过；实际43／30目录与严格报告门禁一致。
- [ ] 源任务只增加本批有证据的开发子范围；T016-R01正式双人适用制度与撤销规则、R02所有真实消费者／前端及正式规则联调、R03实际负责人／工时和整任务验收继续逐项登记，不因内核通过一并关闭。

D03的AuditExport公共差异、删除／解封、组织模型发布及各自业务生产器不在该最小子批内自动完成。正式共享采用、真实身份和真实数据仍待各自条件；它们与当前隔离实现／测试可以并行推进，不能笼统写成“正式环境缺条件，所以T016全部代码无法继续”。
