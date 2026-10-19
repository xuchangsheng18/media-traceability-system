# T013 Keycloak Identity Implementation Plan

当前续验（2026-10-19）：管理员受控初始化、首次改密/MFA和bootstrap退出的补齐见[管理员交接验证](t013-admin-handover-validation.md)及[身份运维手册](../10-deployment/keycloak-identity-runbook.md)；实名登录名已由用户明确，实际接管仍待本人执行。密钥轮换、真实故障拒绝和CI补齐见[轮换批说明](t013-rotation-fault-validation.md)；重启持久性、历史凭据审查和恢复回切见[恢复批说明](t013-recovery-validation.md)。[22项当前登记](../00-project/validation/t013-keycloak-acceptance-ledger.json)记录实际范围和证据。下文2026-10-17的计数、提交、CI未执行状态和步骤表均为当日历史，不覆盖上述当前证据。T013仍未整卡验收，Python候选继续暂缓。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 沿用用户已选择的当前会话逐项实施方式，不另行分派。

**Goal:** 在指定Linux服务器建立独立、可真实验证和恢复的项目身份服务，显式接入T013适配器，并保持业务权限默认拒绝。

**Architecture:** 独立Keycloak/PostgreSQL/HTTPS网关三服务；公开身份入口18443，管理入口仅SSH回环18444。后端逐次introspection后按issuer+sub查既有业务映射，不由Keycloak角色直接授予案件权限。

**Tech Stack:** 当前Miniforge Python3.10.22、既有httpx/SQLAlchemy/psycopg；Keycloak26.8.1候选、PostgreSQL16、Nginx、Docker Compose、OpenSSL、GPG。镜像摘要由步骤1实际取得并锁定，禁止虚构摘要。

**Spec:** [完整书面设计](t013-keycloak-identity-design.md)。任务来源：[T013](../../tasks/platform/T013.md)，依赖[T012](../../tasks/platform/T012.md)。本计划是T013内部8个实施步骤，不是170任务中的T014—T020，也不改变第三阶段16步编号。

状态（2026-10-17）：用户已认可书面设计、8步计划及当前会话逐项实施。按本次实际测试，步骤1—6研发验证通过；步骤7的加密备份与网络隔离还原演练通过，但异地密钥托管、会话/secret恢复协调尚未验证；步骤8已完成开发分支推送、Linux源码快进和1,501项文件清单核对。22项验收登记现为13项范围内通过、9项未执行；GitHub集成创建PR返回403，当前实现提交的托管CI未运行。T013整卡保持未关闭，软件准入和正式身份管理员/用户交接仍未完成。详见[执行报告](../00-project/validation/t013-keycloak-execution-report.json)及[22项验收状态登记](../00-project/validation/t013-keycloak-acceptance-ledger.json)。

## 已核实执行状态（2026-10-17）

| 内部步骤 | 状态 | 实际证据 | 尚未满足的边界 |
| --- | --- | --- | --- |
| 1. 依赖锁定与只读预检 | 研发技术检查通过 | Linux py310预检、原7项服务健康、专用18443/18444端口归属核验；三镜像扫描为0个High/Critical | 正式软件准入未批准 |
| 2. 证书与私密卷 | 研发部署检查通过 | 证书/卷操作测试及现有容器私密挂载检查通过 | 证书轮换告警与正式密钥托管仍需运维责任人 |
| 3. 三服务与TLS边界 | 已部署并实测 | 三个身份容器健康；TLS/入口测试12项通过，原7服务保持健康 | 不能据此视为正式安全验收 |
| 4. 后端显式装配 | 实现及质量门禁通过 | 选定范围 lint、format、type通过；T013专项及业务映射回归包含在102项Linux测试中 | 正式业务入口仍未启用 |
| 5. Realm与OIDC验收 | 真实隔离realm通过 | 真实浏览器PKCE、签名、state/nonce、撤销、过期及secret轮换9项通过；测试realm清理 | 实名管理员/MFA交接和正式用户接入未完成 |
| 6. 身份与业务映射 | 真实隔离映射通过 | issuer+sub、未映射身份拒绝、用户/单位禁用、映射撤销、权限默认拒绝等6项通过 | 无真实人员映射；正式案件/来源授权未配置 |
| 7. 加密备份与隔离恢复 | 技术演练通过 | 加密数据库/配置/CA备份；network=none的新数据库卷还原；还原计数2 realm/16 client/1 synthetic user；原库未修改，测试临时密钥/卷已清理 | 未验证异地存储、正式密钥保管、会话撤销与secret轮换后的完整业务回切 |
| 8. 质量门禁、验收记账与同步 | 部分完成：源码和状态账已同步；正式验收与CI未完成 | Linux py310 lint、format、type通过；身份/令牌/业务回归102项通过；`feat/t013-keycloak-implementation-20261017` 已推送GitHub，Linux源码及本地实现提交 `42a92d0f66fcae9576a80a7ac69ce1b7f20ce2f8` 一致；1,501项服务器文件摘要全数匹配；22项状态登记为13项范围内通过、9项未执行 | 登记文件不等于22项正式验收证据包；GitHub集成创建PR返回403，当前实现提交的托管CI未运行；正式准入、管理员/MFA交接及生产恢复验收未完成 |

内部步骤状态只覆盖本设计的研发实施，不替代任务卡T013的原始完成标准、正式验收或整项目阶段验收。代码与文档已同步的是开发分支和Linux源码工作树，不代表主分支合并或运行服务升级。原T013仍按“部分范围已验证”记录。

## Global Constraints

- 独立Compose项目名 `media-trace-identity`；原7服务、100包运行锁和PoC登录方式保持不变。
- 唯一issuer `https://172.16.58.179:18443/realms/media-trace`；管理URL `https://localhost:18444`，宿主仅绑定127.0.0.1。
- Keycloak8443、健康检查9000、数据库5432不发布宿主端口；网关到Keycloak TLS、数据库verify-full。
- Keycloak1.5CPU/3GiB、PG1CPU/2GiB、网关0.5CPU/1GiB；数据库预留20GiB规划容量，另须容纳镜像和恢复副本，可用空间大于5368709120字节。
- 私密运行根目录 `/workspace/glwy/runtime/media-traceability-system/identity/`；目录0700、私密文件0600，容器按自身UID最小只读授权。
- 访问令牌300秒；SSO空闲1800秒、最长28800秒；refresh轮换、重复使用0；关闭remember-me/offline_access/自助注册/密码grant/隐式流。
- 管理员MFA，密码最短14字符；证书90天、提前30天告警；研发日志10MiB×3、事件7天、每日备份保留7份。这些为本次技术参数，不能代替正式业务制度。
- 逐次introspection，无有效结果缓存；建议网络超时2秒；禁用/终止会话/退出/撤销后的新请求拒绝目标10秒，失败不得降低断言。
- 不产生真实人员映射或案件授权；真实负责人、管理交接、普通用户MFA、准入及正式验收未知时不编造，也不宣称正式交付。
- 新公共API、业务SQL结构或原任务范围发生实质冲突时停止受影响部分，提交明确修订。所有数据库变更必须有版本迁移。

## Review Focus

1. Docker虚拟机路径与Linux同名路径不同：私密卷实际内容和权限须验证，不能把空目录当证书（步骤2/3）。
2. 管理UI虽私有，公开入口仍可能穿透admin API：编码路径、重复斜杠及代理头伪造必须拒绝（步骤3）。
3. ID token可能看似合法且有aud：真实Keycloak须拒绝其作为访问令牌，不能仅依赖JWT解析（步骤5）。
4. 恢复旧备份可能复活已撤销会话：切换前清会话、提高有效时间、轮换secret并实测旧凭据失败（步骤7）。
5. 配置装配中途失败可能泄露连接或降级身份：关闭已创建资源并保持默认拒绝（步骤4/6）。

## 文件与责任映射

下表新增路径均为**待实现文件**，不是已存在成果；后续各步骤复用此映射，不重复创建相同能力。

| 文件 | 责任 |
| --- | --- |
| `config/identity/versions.json` | 非秘密镜像版本、摘要、来源及扫描记录引用 |
| `deploy/identity/compose.yaml`、`Dockerfile.keycloak`、`nginx.conf`、`postgres.conf`、`pg_hba.conf` | 独立三服务、优化构建、TLS、路由与数据库边界 |
| `config/identity/realm.template.json` | 无secret的realm参数及客户端模板 |
| `scripts/identity/__init__.py`、`scripts/identity/{common,preflight,certificates,volumes,control,provision,backup,restore,verify}.py` | Python包及各自承担的配置/观察、预检、证书、卷传输、显式控制、初始化、加密备份、隔离恢复、验收汇总 |
| `backend/business_app/identity/{config,runtime,entrypoint}.py` | 私密加载、资源生命周期、独立ASGI显式入口 |
| `backend/business_app/identity/tokens.py`、`backend/business_app/db.py` | 在现有类上增加受控TLS与有界数据库连接，不复制认证实现 |
| `tests/platform/test_t013_{identity_config,identity_deploy,identity_operations}.py` | 配置、模板和运维动作的正反向测试 |
| `tests/business/test_token_identity.py` | 在现有精确映射测试中补装配/失效回归 |
| `tests/identity/{conftest,test_tls_gateway,test_oidc_live,test_mapping_live,test_recovery_live}.py`、`tools/identity_oidc_probe.py` | 显式目标的真实服务与临时授权码回调验收，无正式用户数据 |
| `.github/workflows/identity.yml`、`config/stage-three-profile.json` | 新增身份专用隔离CI及适用类型/格式范围，不削弱旧CI |
| `docs/10-deployment/keycloak-identity-runbook.md`、`docs/00-project/validation/t013-keycloak-runtime-report.json` | 真实操作、回滚及脱敏验收证据 |

## 实施步骤

### Task 1: 步骤1：依赖核验、制品锁定与只读预检

**Files:** 新建 `config/identity/versions.json`、`scripts/identity/common.py`、`scripts/identity/preflight.py`、`tests/platform/test_t013_identity_deploy.py`。

**Interfaces:** `preflight.collect() -> dict[str, object]` 返回源码版本、Docker上下文、两个文件系统容量、端口和原7服务摘要；`preflight.validate(snapshot: dict[str, object]) -> list[str]` 返回阻塞原因。CLI `python -m scripts.identity.preflight --report PATH`，失败非零退出，无制品拉取/服务启动。

- [ ] 读取T012代码、0004/0005迁移及真实数据库验证证据；核对当前T013的60项专项和共享回归源码，不仅看台账。若本批所需依赖缺失，停止对应实施并记录原因。
- [ ] 写失败测试：`test_preflight_rejects_port_collision`、`test_vm_space_is_not_host_space`，断言18443/18444冲突或VM不足时阻塞，即使宿主空间足够；断言无Docker修改调用。
- [ ] 运行 `python -m pytest tests/platform/test_t013_identity_deploy.py -q`，新功能尚未实现时应失败；确认失败原因后实现上述接口和明确目标校验。
- [ ] 从官方源取得Keycloak26.8.1、PG16受支持补丁、Nginx稳定版的精确摘要及扫描/SBOM/许可记录，锁入versions；漏洞未处理不能认定准入通过，不用浮动tag替代摘要。
- [ ] 重跑该测试并运行只读CLI，预期退出0且阻塞清单为空；原7服务健康。提交本步代码、实际结果，测试通过后同步源码；未获软件准入仅记录技术结果。

### Task 2: 步骤2：私有CA、服务证书与私密卷传输

**Files:** 新建 `scripts/identity/certificates.py`、`volumes.py`；扩展 `test_t013_identity_operations.py`、`test_t013_identity_deploy.py`。

**Interfaces:** `certificates.prepare(runtime: Path) -> dict[str, str]` 返回公有证书摘要/路径，不返回私钥内容；`volumes.install(runtime: Path) -> dict[str, object]` 仅写入前缀匹配的专用具名卷，验证容器UID权限；拒绝重覆盖CA或现存不一致凭据。

- [ ] 写失败测试 `test_wrong_runtime_root_rejected`、`test_ca_not_recreated`、`test_secret_volume_verifies_content`；断言越界/符号链接拒绝，缺少有效卷内容即失败，输出中无私钥。
- [ ] 运行 `python -m pytest tests/platform/test_t013_identity_operations.py tests/platform/test_t013_identity_deploy.py -q`，先确认失败，再实现安全创建、原子写入和流式私密传输。
- [ ] 签发入口SAN含172.16.58.179/localhost、内部证书含真实容器服务DNS；90天及30天告警；CA私钥不进入容器。生产secret随机生成不放仓库，公有CA另附摘要。
- [ ] 重跑上述测试；真实检查目录0700/私密文件0600、容器属主、SAN/链及到期时间，错误CA/错误SAN连接必须失败。提交并同步代码与脱敏证据，私密运行文件留服务器。

### Task 3: 步骤3：三服务及HTTPS管理边界

**Files:** 新建 `deploy/identity/` 表中5类文件、`scripts/identity/control.py`、`tests/identity/test_tls_gateway.py`；扩展模板测试。

**Interfaces:** `control.status() -> dict[str, object]` 只读；CLI `python -m scripts.identity.control up --apply` 先执行预检再启动身份项目，`down --apply`不删除卷；没有 `--apply` 仅输出脱敏操作预览。

- [ ] 写失败测试 `test_compose_isolates_secrets_ports_and_resources`、`test_control_requires_apply`，精确断言3CPU/6GiB、18444回环、内部端口未发布、DB独立卷、禁止start-dev/latest、原7服务无修改。
- [ ] 运行模板测试确认失败；按设计实现Compose、优化镜像、PG TLS verify-full和Nginx双监听。覆盖外来代理头，配置精确Host及规范化路径拒绝。
- [ ] 重跑单测，执行 `docker --context desktop-linux compose -p media-trace-identity -f deploy/identity/compose.yaml config --quiet`；该命令不得打印含secret展开配置。
- [ ] 源码提交并同步后，使用Linux py310执行显式启动；运行 `python -m pytest tests/identity/test_tls_gateway.py -q`，验证公开admin及绕过变体拒绝、SSH管理完整重定向、4段TLS和内部端口隔离；无目标配置必须失败，不能skip后当通过。
- [ ] 保存实际镜像/资源/服务观察及原7服务健康，补运行手册并提交同步。此处只表示身份服务技术部署，不启用业务provider。

### Task 4: 步骤4：私密配置及后端显式装配

**Files:** 新建 `identity/config.py`、`runtime.py`、`entrypoint.py`，修改 `identity/tokens.py`、`db.py`，新增配置单测并扩展原专项测试及质量范围。

**Interfaces:** `config.load_private_config(path: Path) -> IdentityRuntimeConfig`；frozen配置包含 `introspection: IntrospectionSettings`、`ca_file: Path`、`lookup_dsn: str`、`business_settings: BusinessSettings`，secret/DSN字段 `repr=False`，未知字段拒绝。`runtime.open_identity(config: IdentityRuntimeConfig, policy: AuthorityProvider | None = None) -> IdentityResources`；资源对象有 `authority: MappedTokenAuthority` 和幂等 `close() -> None`。`entrypoint.create_identity_app() -> FastAPI` 通过显式配置路径建立应用并在lifespan关闭资源；复用现有 `main.create_app`，不修改其默认行为。

`IntrospectionVerifier.__init__` 新增仅限关键字 `ssl_context: ssl.SSLContext | None = None`，显式传递给httpx验证；只接受CERT_REQUIRED及check_hostname=True。`Database.__init__(dsn: str, *, connect_timeout_seconds: int = 2, statement_timeout_ms: int = 2000, pool_timeout_seconds: float = 2.0)` 保留现有mt_business_隔离约束，验证边界并传入连接/语句/池超时；不丢弃DSN安全选项。为该变化补完整数据库回归。

- [ ] 写 `test_ca_validation_cannot_be_disabled`、`test_config_permission_and_unknown_fields_rejected`、`test_partial_open_closes_resources`、`test_entrypoint_is_explicit_and_closes_once`，断言缺字段/权限过宽/越界secret路径拒绝、失败关闭资源且默认create_app仍无provider；测试连接/语句/池均有界。
- [ ] 执行 `python -m pytest tests/platform/test_t013_tokens.py tests/platform/test_t013_identity_config.py tests/business/test_token_identity.py -q`，确认新测试先失败；实现配置和资源所有权，不记录secret，不修改公共API/业务SQL。
- [ ] 重跑专项及 `python scripts/verify_business_foundation.py run`，只用既有明确隔离目标；运行 `python scripts/dev.py lint`、`format-check`、`type-check`。预期所有适用检查通过，不跳过原测试。
- [ ] 提交并同步源码，保持默认未启用；私密issuer/client/CA/最小权限DSN通过文件装配，在步骤6前不启用真实用户业务入口。

### Task 5: 步骤5：realm初始化与真实授权码协议验收

**Files:** 新建 `realm.template.json`、`scripts/identity/provision.py`、`tools/identity_oidc_probe.py`、`tests/identity/conftest.py`、`test_oidc_live.py`。

**Interfaces:** CLI `python -m scripts.identity.provision --apply` 幂等创建指定realm与机密API客户端，不授予业务角色；`python tools/identity_oidc_probe.py --config PRIVATE_PATH --report REPORT_PATH` 临时回调仅经SSH回环，运行结束关闭；结果只含脱敏状态/时延，不含token/code/secret。pytest目标由 `MT_IDENTITY_TEST_CONFIG` 私密文件显式给出，未配置则失败并清楚报错。

- [ ] 写 `test_realm_policy_exact_and_no_password_grant`、`test_provision_refuses_unapproved_overwrite` 验证全部设计参数、无通配回调和幂等差异拒绝，先运行失败再实现模板/初始化器。
- [ ] 在隔离验收realm创建随机无敏感测试用户和精确回调；真实项目realm关闭自助注册，不以邓昀姓名自动开账号。初始化凭据不进入参数日志；无人接管实名管理员时保留该阻塞，不能假称bootstrap移除完成。
- [ ] 测试真实浏览器登录、state/nonce、PKCE错verifier、回调不符、授权码重放、ID token拒绝、伪造签名、错误issuer/audience、真正过期/nbf、JWKS轮换，命令 `python -m pytest tests/identity/test_oidc_live.py -q`。
- [ ] 实测禁用/终止会话/退出/撤销四类动作至新请求拒绝的时间，均要求10秒以内；刷新撤销若不使access token失效，实施明确会话终止策略并重测，不能宣称Keycloak默认已满足。
- [ ] 所有真实协议测试通过后提交同步源码与脱敏结果；临时回调关闭，记录管理员MFA/交接的实际结果或未完成条件。

### Task 6: 步骤6：真实身份与既有业务映射联调

**Files:** 新建 `tests/identity/test_mapping_live.py`，扩展 `tests/business/test_token_identity.py` 及运行手册。

**Interfaces:** 复用步骤4的IdentityResources与T012 IdentityDirectory，不新增第二套用户表/角色表；映射仅通过原目录管理接口，测试连接使用隔离mt_business_数据库。

- [ ] 写并先运行失败的 `test_live_issuer_sub_not_email`、`test_keycloak_admin_has_no_business_case`、`test_disabled_org_and_revoked_mapping_deny`、`test_idp_timeout_never_falls_back`，断言同邮箱不同sub不能认领用户、缺案件/来源规则拒绝、超时返回既有错误且不泄密。
- [ ] 用真实Keycloak令牌及自建内部用户/单位/案件夹具建立精确映射，通过显式入口连到隔离业务实例；故障注入TLS/网络/DB不可用并验证资源关闭和总耗时，不能将Mock响应当本步证据。
- [ ] 执行 `python -m pytest tests/identity/test_mapping_live.py -q` 和既有业务完整回归，均需通过。尚无真实业务授权时仅启用隔离验证，不向真实人员授予权限。
- [ ] 提交并同步源码与实际映射/回归报告，准确填写“真实项目身份服务已接通的技术范围”，正式用户交付仍按实际条件判定。

### Task 7: 步骤7：加密备份、隔离恢复与回滚

**Files:** 新建 `scripts/identity/backup.py`、`restore.py`、`tests/identity/test_recovery_live.py`，扩展运维单测/运行手册。

**Interfaces:** CLI `python -m scripts.identity.backup --recipient PUBLIC_KEY_FILE --output PRIVATE_DIR` 流式加密，无明文落盘；`python -m scripts.identity.restore --backup ENCRYPTED_FILE --isolated-project media-trace-identity-restore --apply` 拒绝原卷/现网端口，解密密钥仅从私密文件读取，报告脱敏。恢复入口只作演练，切换需明确单独动作。

- [ ] 写 `test_backup_has_no_plaintext_artifact`、`test_restore_refuses_original_volume`、`test_corrupt_or_missing_key_fails_closed`，先失败再实现；GPG退出码/签名或完整性、备份真实性记录均校验。
- [ ] 真实创建备份，独立卷恢复并验证realm/客户端/密钥/映射；切换前清会话、提升not-before并轮换必要secret，断言备份前token和旧secret不能恢复权限。
- [ ] 运行 `python -m pytest tests/identity/test_recovery_live.py -q`，记录恢复耗时、备份时点、损坏和缺密钥失败；备份必须实际位于Linux宿主私密目标，非原Docker卷。
- [ ] 演练只对身份项目回滚并确认原7服务健康，不删卷；配置每日备份/7份研发保留，缺独立安全解密密钥保管或异地目标时明确未满足灾备。提交同步代码和脱敏报告。

### Task 8: 步骤8：完整门禁、验收记账与三端同步

**Files:** 新建 `.github/workflows/identity.yml`、`scripts/identity/verify.py`、运行报告；更新现有任务卡/台账、docs导航、版本和资源记录、manifest及server-sync-receipt。

**Interfaces:** `python -m scripts.identity.verify --config PRIVATE_PATH --report REPORT_PATH` 汇总IDP-01至22；每项状态为PASS/FAIL/NOT_EXECUTED，任何缺证据不能总PASS；不含凭据、真实主体或完整敏感URL。CI使用随机临时凭据和独立项目，禁止访问内网真实身份配置。

- [ ] 写 `test_verify_rejects_missing_acceptance_evidence`，断言22项任一未执行/失败均不可声称完整技术验收；实现汇总和精确文件摘要引用，不复制旧CI结果作为新代码验证。
- [ ] 新CI实际运行模板、配置、TLS和真实隔离Keycloak测试；浏览器工具不进入100包运行锁。执行原32门禁及适用新门禁，保留实际run/artifact摘要，失败不削减旧断言。
- [ ] 在Linux py310执行全部适用专项、业务回归、lint/format/type、安全扫描和22项实际验收；对照T013源要求“过期、伪造、禁用均拒绝；生产接口可替换统一身份认证”分别记通过/失败/未验证。
- [ ] 按真实证据更新T013的R01/R02，真实负责人/工时及有效验收未落实则R03保留；不自动开始T014，不将T001—T011负责人扩展到本任务。生成170卡/分步导航和阶段状态，检查数量同源。
- [ ] 文档门禁通过后提交推送GitHub，Linux源码快进到同一提交，检查manifest逐文件摘要；部署运行版本另行核验镜像/配置/健康。同步回执后再核验最终三端提交一致；私钥/口令/真实人员不入Git。

## 验收覆盖与交付口径

| 设计验收项 | 主实施步骤 | 缺证据时的状态 |
| --- | --- | --- |
| IDP-01 | 1、8 | 准入或制品未验证 |
| IDP-02—06 | 2、3 | 服务部署/安全边界未通过 |
| IDP-07—12 | 5 | 真实协议和失效验收未通过 |
| IDP-13—15 | 4、6 | 业务映射及默认拒绝未通过 |
| IDP-16 | 5、7 | secret轮换未通过 |
| IDP-17—18 | 2、3、5、8 | 持久化/隐私未通过 |
| IDP-19—21 | 7 | 恢复回滚未通过 |
| IDP-22 | 4、8 | 代码与门禁未通过 |

步骤1—2完成后只有可检查的部署输入；步骤3完成后是独立身份服务；步骤4—6完成后才有经实测的隔离业务接入；步骤7—8及适用实际条件满足后才能判断T013的可关闭范围。GitHub源码、Linux源码和Linux运行服务分别记录，不用其中一项代替其余。

## 本计划自审与执行交接

自审已核对设计12节及22项验收覆盖、步骤间接口类型、5类Review Focus的测试归属、无秘密/虚构摘要/真实账户、原7服务与默认拒绝边界。所有文件已按“新增/修改/既有复用”区分；既有入口为 `backend/business_app/main.py`，不存在的app.py/根pyproject.toml未作为实现依据。

本轮仅发布计划与导航；不将上述勾选项标为完成。执行方式沿用当前会话逐项实施，待用户审阅本计划后开始步骤1；每个实际开发步骤完成测试及记录后同步，无需等全部8步结束才更新仓库。
