# Linux全原生研发迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在Linux/Miniforge py310/CPU研发范围完成本项目服务原生托管、可核对的数据迁移和实际恢复验证。

**Architecture:** 先建立只读清单与锁定制品，再由徐昌胜执行管理员初始化；使用独立暂存实例恢复并验证，最后在明确停写窗口切换。现有容器及数据卷保留，业务原生PostgreSQL单列纳管；其他项目不操作。

**Tech Stack:** Ubuntu24.04 amd64、systemd、Python3.10.22、Node22.21.1、PostgreSQL16.15、RabbitMQ4.3.6/兼容OTP27、SeaweedFS4.48、Keycloak26.8.1/Java21；具体原生制品须经过N01实际锁定。

**Spec:** [已获认可的原生设计](native-linux-migration-design.md)。2026-10-17用户回复“认可，继续编制精确实施计划”。本计划及候选资源上限已获用户认可，从N01开始；尚不表示已安装或已获停写切换确认。执行方式沿用当前会话直接实施，管理员步骤由徐昌胜执行。

## Global Constraints

- 保留原100包运行锁、原170任务字段及12模块；T004以变更`CR-T004-NATIVE-20261017`追溯，源容器要求不重写。
- 生产、离线、GPU和Windows原生单独验收；本次不扩展真实业务权限、样本或模型训练范围。
- 原生制品不得使用容器digest代替文件SHA256；版本/签名/摘要缺失即阻断安装，不能下载latest代替目标版。
- 禁止全局停机、覆盖原数据目录、自动清队列、删除旧容器/卷，或未经对账把目标新写入丢弃后回退。
- 管理员不向会话提供密码、Token、数据库连接串或私钥；不开放广泛免密sudo。
- 以下文件表保留原计划路径；`inventory.py`、`artifacts.py`及其测试已实现，其余工具、单元和配置须按对应任务状态核对，不能把拟建命令当成已有工具。管理员步骤须等待实际制品准入和对应执行授权。

## Review Focus

1. 包源版本偏旧或缓存过期：N01拒绝RabbitMQ3.12/OTP25组合及缺失制品，不自动降级。
2. 目录/端口已被其他项目使用：N02拒绝非空数据目录、符号链接和占用端口，不改变既有所有权。
3. 备份缺件、错误密钥或对象内容不一致：N04停止恢复交付，保留源数据，输出脱敏差异。
4. 队列未排空或仍有未确认任务：N04/N07阻断切换，不用purge伪造通过。
5. 目标产生新事实后请求回退：N06/N07先停写并收敛差异，再决定回退，不能直接恢复旧数据副本。

## 真实预检与制品边界

2026-10-17只读预检：宿主x86_64/amd64；`/workspace`为独立ext4，约8.9T可用；`/opt`约9.1T可用。这是宿主空间，不能替代Docker VM卷或项目配额。失败单元为`systemd-networkd-wait-online.service`，本计划不自行修复网络配置。

| 组件 | 实际观察 | N01动作 |
| --- | --- | --- |
| PostgreSQL | 已有私有原生工具实际为16.15；APT候选16.15-0ubuntu0.24.04.1，未安装 | 核对现有工具来源/全部文件摘要/依赖；不足时取官方16.15源包构建独立prefix，不直接安装自动创建集群的全局服务器包 |
| RabbitMQ | 容器实际4.3.6；系统源候选3.12.1-1ubuntu1.7 | 取官方4.3.6 Generic Unix发行包；不安装系统旧候选 |
| Erlang | 容器为OTP27，ERTS15.2.7.13，精确OTP27.3.4.18；系统源OTP25 | 从源发行信息读取精确OTP补丁，取官方同补丁源包构建独立prefix；依赖包锁定，不能仅锁27大版本 |
| Java | Keycloak容器实际Java21.0.12.1；APT候选21.0.12.1+1-1~24.04.4 | 核对26.8.1支持矩阵后锁定Java21制品，保留发行版差异验证 |
| Nginx | APT候选1.24.0-2ubuntu7.18，未安装 | 源身份网关实际1.30.6；与该版本/模块比较；优先匹配现有版本独立构建，不在迁移中悄悄降级或覆盖宿主Nginx |
| SeaweedFS/Keycloak | 目标4.48/26.8.1 | 官方对应归档，锁URL/架构/签名或官方摘要及本地摘要 |
| 备份加密工具 | APT候选age1.1.1-1ubuntu0.24.04.3，未安装 | 先确定保管人、公钥和还原方式；测试密钥仅用于夹具 |

APT候选来自服务器已有缓存，未执行更新或安装；它不证明包仍可获取或已经验签。官方规则依据：[RabbitMQ安装](https://www.rabbitmq.com/docs/install-debian)、[OTP兼容](https://www.rabbitmq.com/docs/which-erlang)、[PostgreSQL Ubuntu](https://www.postgresql.org/download/linux/ubuntu/)、[Keycloak生产配置](https://www.keycloak.org/server/configuration-production)、[SeaweedFS4.48](https://github.com/seaweedfs/seaweedfs/releases/tag/4.48)。安装前重新核对精确版本的文档和发行清单。

## 文件结构及共享接口

| 拟新增路径 | 单一职责 |
| --- | --- |
| `scripts/native/inventory.py` | 只读清单及端口/路径/进程归属摘要 |
| `scripts/native/artifacts.py` | 验证制品锁、签名证据及完整依赖 |
| `scripts/native/units.py` | 渲染和验证项目systemd单元，不默认安装 |
| `scripts/native/backup.py` | 一致性水位、加密备份清单、解密恢复前校验 |
| `scripts/native/reconcile.py` | 数据库、队列、对象、身份映射差异对账 |
| `scripts/native/cutover.py` | 明确状态机、停写许可和回退拒绝条件 |
| `config/native/artifacts.lock.json` | 实际制品版本、来源、摘要、依赖、许可；缺项不得标READY |
| `config/native/staging.json` | 无秘密的暂存端口/路径/候选限制 |
| `deploy/native/systemd/` | 项目slice及各服务模板 |
| `tests/native/` | 独立原生工具测试，不复用容器运行结果冒称原生通过 |

共用JSON记录字段：`schema_version=1`、`source_commit`、`observed_at`（带时区）、`scope`、`status`、`blockers`。状态只允许`PASS`、`FAIL`、`NOT_EXECUTED`；任何必需项NOT_EXECUTED都不能聚合为PASS。具体实例标识不得只使用模糊项目名前缀。

所有原生命令由指定Python执行；不把Windows辅助解释器的通过结果当项目Linux结果。参数使用文件路径，秘密仅从管理员受控文件读取，不从命令行传值。

## N01：原生清单与完整制品锁

**Files:** 创建`inventory.py`、`artifacts.py`、制品锁及`tests/native/test_artifacts.py`。

**Interfaces:** `collect_inventory() -> dict`只读；`validate_artifacts(lock: dict, artifact_root: Path) -> dict`校验输入锁中所列条目。该工具的`status=PASS`只表示本次包字节及来源检查通过；还必须满足完整依赖、逐软件准入、最终安装锁和对应管理员步骤条件，才可安装。现有返回值明确保持`installation_ready=false`。锁项包含精确版本、官方URL、文件名、amd64、SHA256、签名依据、依赖列表、许可和实际版本探针输出。

- [x] 写测试`test_missing_or_wrong_digest_refuses_install`：缺SHA256、文件损坏、非目标架构、相对路径逃逸均返回FAIL；`test_cached_old_broker_is_not_selected`拒绝3.12和OTP25。
- [ ] 运行`python -m pytest tests/native/test_artifacts.py -q`，确认缺失实现导致失败。
- [ ] 实现只读清单与锁校验；盘点全部10容器、原生业务PG和其他容器集合。读取挂载源只输出脱敏标识，不输出环境/密钥。下载到私有暂存目录，按官方签名及摘要验证；包依赖也锁，不修改全机APT源。
- [x] 重新运行专项测试及制品校验。实际已核验命令为`python scripts/native/artifacts.py verify --lock config/native/artifacts.lock.json --root /workspace/glwy/runtime/media-traceability-system/native-artifacts`；原示例`/workspace/media-trace-native/artifacts`为未来管理员根目录，不冒充已存在缓存。缺少任何制品时预期非零并列出组件，不能跳过继续N02安装。
- [ ] 提交N01代码、无秘密锁和实际记录。完整锁尚未取得时明确BLOCKED_ARTIFACT，不填虚构摘要。

### N01五项计划的实际状态

最新补验见[9条官方CVE源及96wheel检查](../00-project/validation/native-n01-admission-decisions/cve-wheel-review.json)和[71项现有回归](../00-project/validation/native-n01-admission-decisions/cve-wheel-regression-report.json)。其中原生工具45项、游标21项、消息边界5项；下表保留原五项计划的工具核验粒度。wheel检查是当前归档的只读证据，尚未成为部署的恢复门禁，不是解释器或依赖修补。

以下对应原五项，不新增任务编号或整卡验收数；[本次Linux证据](../00-project/validation/native-n01-admission-decisions/n01-plan-verification.json)记录实际源码、命令、输入摘要、前后清单及测试计数。

| 原项 | 当前可证明的结果 | 尚未完成或证明的部分 |
| --- | --- | --- |
| 1．失败输入测试 | 现有`test_invalid_installation_inputs_fail_closed`覆盖缺摘要、损坏、架构、路径逃逸、旧RabbitMQ/OTP等；两测试文件共45项通过，0失败/错误/跳过。原计划测试名是用例意图，实际参数化测试名见证据。 | 不将拒绝非法输入当作完整安装准入。 |
| 2．首次RED过程 | 本批复跑现有实现为GREEN；原历史代码和早期报告保留。 | 本批未核得首次“缺实现导致失败”的运行原文，保持未验证，不补造、不要求删除现有实现重演，也不将此信息限制新增为软件准入阻塞。 |
| 3．只读盘点及完整锁 | 10个项目容器、原生业务PG16.15、Python3.10.22及31个相邻容器集合已只读重验；十类原始制品字节和来源校验通过。恢复组合/Go缓存沿用已有精确证据。 | 最终可安装组合仍待R1—R3必要处置/准入；当前原始锁不包含三项预选采用决定。 |
| 4．专项与真实缓存重验 | 上述45项和实际私有缓存校验通过；前后容器ID、相邻集合相同，暂存端口未占用。 | 不替代N02账号/目录及N03服务/N04业务数据恢复验收。 |
| 5．提交可核对成果 | 现有代码、原始锁、中间恢复证据已入库；本次同步以[源文件清单](../00-project/repository-file-manifest.json)和[同步回执](../00-project/server-sync-receipt.json)为准。 | 最终可安装锁尚未生成，N01仍`IN_PROGRESS_BLOCKED_ADMISSION`；不能勾选整项完成。 |

包校验报告不是三项候选采用、漏洞风险接受或安装许可。两处许可询问均已发送且当前无新增答复；Python候选继续暂缓。[统一剩余与确认清单](native-n01-admission-decisions.md)区分已验证材料、外部等待和后续管理员步骤。

## N02：管理员目录、账户、单元及资源限制

**Files:** 创建`units.py`、`config/native/staging.json`、`deploy/native/systemd/mt-native.slice`、各服务模板及`tests/native/test_units.py`；更新[管理员清单](native-linux-admin-checklist.md)。

**Interfaces:** `render_units(inventory: dict, profile: dict) -> dict[str, str]`；`validate_install_targets(profile: dict) -> dict`拒绝符号链接、非空目标和现用端口；输出单元仅写项目新目录。

- [ ] 写`test_existing_path_or_port_refuses_initialization`和`test_every_service_has_identity_and_limits`；缺User、MemoryMax、CPUQuota、TasksMax、UMask或私密配置路径均失败。先运行失败，再实现。
- [ ] 服务账号分别规划为`mt-pocpg`、`mt-businesspg`、`mt-idpg`、`mt-broker`、`mt-object`、`mt-identity`、`mt-gateway`、`mt-web`；无登录无sudo。应用沿用glwy及现有py310，不能开放主目录全部秘密。保留现有业务PG账户/路径至迁移对账，不强行chown。
- [ ] 新建根为`/opt/media-trace-native/releases`、`/etc/media-trace-native`、`/workspace/media-trace-native`；管理员确认挂载和路径后仅创建新子目录。权限按设计0700/0600及最小服务组。制品root所有、服务不可改写。
- [ ] 暂存拟端口：PG24432、broker24672、S324833、API24200、推理24201、Web24180、身份28443/28444、业务PG45432。预检时均未监听，启动前再次检查；filer/master/volume/Keycloak内部端口和Erlang分布端口必须同时纳入清单且只绑定回环，不能默认空闲。
- [ ] 候选预算：原七服务10.5核/10.5GiB、身份3核/6GiB、业务PG2核/2GiB；项目合计15.5核/18.5GiB，slice候选MemoryHigh16GiB/MemoryMax20GiB/CPUQuota1550%。这是用户已认可、仍需隔离验证的候选上限，不保证无影响；隔离实测后按相邻项目健康和资源再调整。临时目录使用独立有上限文件系统，并计入MemoryMax；PG排序临时文件另限。PID上限逐服务压测后记录，不用无限值。
- [ ] 徐昌胜核对渲染结果，执行具体单元的`systemd-analyze verify`、安装、`daemon-reload`；只启动暂存目标。验证真实cgroup、账号权限和退出SSH后的持续运行，再提交N02记录。未取得管理员回执不能记PASS。

## N03：原生暂存中间件与健康检查

**Files:** 新增各服务无秘密配置模板、`scripts/native/health.py`、`tests/native/test_health.py`；复用现有业务迁移/身份策略，不改公共API。

**Interfaces:** `probe_services(profile: dict) -> dict`输出版本/连接/权限/端口检查；连接失败、错误证书或跨实例访问均FAIL。单元以N01制品锁的绝对路径启动，不依赖交互shell PATH。

- [ ] 先写`test_wrong_instance_or_certificate_fails`，运行看到失败，再实现探针和模板。
- [ ] 在新目录初始化PoC/身份/业务PG独立实例；业务测试PG35432保持运行，新45432只用夹具验证。Rabbit新节点名/数据/cookie独立，vhost权限最小；Seaweed明确filer后端并迁移所有依赖。
- [ ] Keycloak用正式启动方式及隔离测试realm/issuer，保持管理入口与公开入口隔离；Nginx独立prefix/端口/PID/日志，不能覆盖全机配置。Java构建与运行参数固定。
- [ ] 验证版本与N01匹配、TLS/角色/健康及重启数据持久性；依赖停止必须让相应ready失败。运行`python scripts/native/health.py --profile config/native/staging.json`，预期必需项全部PASS。
- [ ] 提交N03模板、测试和实际证据，注明测试身份不是正式业务授权。

## N04：一致性备份、隔离恢复及全量对账

**Files:** 创建`backup.py`、`reconcile.py`、`tests/native/test_backup.py`、`tests/native/test_reconcile.py`。

**Interfaces:** `validate_backup(manifest: dict, root: Path) -> dict`；`reconcile(source: dict, target: dict) -> dict`；清单含每实例ID、加密文件摘要、版本、迁移号、数据库/角色、对象完整摘要及消息水位，秘密和实际数据不入Git。

- [ ] 写失败测试：错误密钥、缺PG globals、遗漏filer元数据、对象字节篡改、队列未确认消息不为零、数据库外对象或对象外引用均FAIL；先运行失败再实现。
- [ ] 徐昌胜落实真实备份公钥/保管方式；没有公钥时仅对自建夹具演练，正式源备份交付保持阻塞。`pg_dump`逻辑归档与globals分别加密，恢复只到新目录；不搬Alpine PG物理目录。
- [ ] 对源库的无停写备份仅验证可恢复性，不宣称跨数据库/对象/队列最终一致。最终一致备份在N07获准停写、排空并对账后再做。
- [ ] Rabbit导出definitions并核对配置；它不含消息。默认停写后排空+outbox对账，有未确认消息时阻断；如要保留消息，另验证同节点恢复路线，不能自动切换策略。
- [ ] Seaweed源volume、filer元数据和S3配置同步备份；逐对象长度/SHA256及元数据对账，不把ETag当内容摘要。身份库、映射、CA/证书、secret和模型配置单列。
- [ ] 隔离还原后运行`python scripts/native/reconcile.py --manifest /etc/media-trace-native/restore-manifest.json --profile config/native/staging.json`；摘要不符返回非零，输出只含脱敏计数/差异标识。通过后提交N04记录。

## N05：原生应用联调及身份边界

**Files:** 原生API/worker/推理/Web模板、`scripts/native/integration.py`、`tests/native/test_integration.py`。

**Interfaces:** `run_integration(profile: dict) -> dict`引用N03实例ID、N04恢复批次，输出实际HTTP/队列/SQL/对象/模型/日志链证据。

- [ ] 写`test_container_dns_or_demo_success_is_not_native_evidence`，拒绝容器DNS、Mock标记或缺原生进程/cgroup证据；先失败后实现。
- [ ] 私密profile把容器DNS替换为明确原生回环地址，分别启动指定py310的应用进程；Web用构建静态制品，调试Vite端口单独管理。
- [ ] 验证上传/续传、历史读取及已实现接口、队列消费、SQL/对象/合成CPU推理闭环；检查跨进程trace、统一错误、脱敏、配置缺失及依赖中断，正式身份/来源缺失时仍拒绝动作。
- [ ] 在暂存身份realm验证issuer+sub映射、错误aud/签名/过期拒绝和单位案件隔离。不得将测试issuer或邮箱映射成正式人员。
- [ ] 运行原生专项、现有业务回归及前端浏览器测试；保存精确源码/命令/时间/无跳过计数，再提交N05记录。

## N06：故障恢复、容量及回退演练

**Files:** `scripts/native/recovery.py`、`tests/native/test_recovery.py`、恢复报告模板。

**Interfaces:** `assess_rollback(source_watermark: dict, target_watermark: dict) -> dict`有目标新增事实或未对账项时返回FAIL，不执行回退。

- [ ] 写`test_new_writes_block_blind_rollback`及`test_resource_failure_does_not_touch_neighbor`，先失败后实现。
- [ ] 只在暂存目录与单元触发CPU/内存/临时空间/PID限制、依赖中断及重启；采集真实限制与相邻健康，不能填满共享宿主盘。
- [ ] 实演缺件/错密钥恢复失败、干净恢复成功，以及新写入后的差异收敛；记录实测耗时，不先编造RPO/RTO或正式容量指标。
- [ ] 核对其他项目集合与状态、持久服务退出SSH后状态；提交N06结果，失败保留源服务不切换。

## N07：受控切换与管理员执行包

**Files:** `cutover.py`、`tests/native/test_cutover.py`、按实际清单生成的`native-linux-cutover-runbook.md`和管理员专用执行包。

**Interfaces:** `transition(state: str, evidence: dict) -> str`状态固定为PREPARED → QUIESCED → BACKED_UP → RESTORED → VERIFIED → SWITCHED → ACCEPTED。缺签认、非零待处理消息、缺实际备份或错误目标ID时拒绝跃迁。

- [ ] 写`test_no_window_or_dirty_watermark_refuses_switch`、`test_post_write_rollback_requires_reconciliation`，先失败后实现。
- [ ] 取得实际切换窗口和批准范围；锁定本项目容器精确ID及端口，不用广泛名称匹配停止服务。退出窗口不继续操作。
- [ ] 停入口新写入/发布/登录，处理在途任务并对账，记录水位；重新做N04最终一致备份、恢复、验证。
- [ ] 只停止占用目标端口的本项目旧服务，启用原生稳定端口；保持身份外部issuer，验证旧会话失效、secret轮换及管理员/公开入口边界。未通过不得重新开放写入。
- [ ] 目标未写入可恢复旧入口；目标已写入必须先停写收敛再决定。保留原生失败实例、旧卷和所有记录；备份保留期、旧服务撤销时间由徐昌胜明确后单独执行。
- [ ] 提交N07执行记录。计划审阅不等于已批准实际停写窗口。

## N08：验收、门禁和三端同步

**Files:** 更新T001—T012任务卡/台账、原生验证报告、README/阶段导航、同步清单；CI加入原生配置静态测试，真实宿主探针不伪装为GitHub临时容器结果。

- [ ] 先写`test_missing_native_runtime_evidence_prevents_acceptance`；缺管理员回执、真实cgroup/恢复/停写记录，任务不能整项PASS。
- [ ] 逐项匹配原源验收/测试及明确的py310/原生变更，不把未来业务功能强塞回基础任务，也不以资料齐全代替运行验收。
- [ ] 在GitHub核对main ruleset及engineering；创建隔离失败PR验证禁止合并，修正同PR变绿后关闭测试PR。当前集成创建PR返回403，需有权限的徐昌胜在页面创建，不提取Token或绕过保护。
- [ ] 完整原生测试、当前源码CI、无秘密报告、实际复核由徐昌胜给出；真实未知项仍保持待确认。
- [ ] 使用同一提交同步本地/GitHub开发分支/Linux源码，逐文件摘要校验；受保护main经PR合入，源码同步与运行部署分别写回执。原100包锁/原件摘要保持不变。

## 管理员现在做什么

现在仍可执行[只读预检清单](native-linux-admin-checklist.md)。下一批先实施N01及N02的可测试工具；完成制品锁和单元渲染后，再交付带真实文件摘要的管理员安装包。当前没有可盲执行的全局安装脚本，也不要求徐昌胜先安装不匹配的系统RabbitMQ。

## 自查与当前状态

设计§1—5由N01—N03覆盖，§6由N04覆盖，§7由N02/N06覆盖，§8由N06/N07覆盖，§9—10及任务收口由N08覆盖。共享字段/命令均在上文定义；拟建工具仅在对应任务完成后可执行。

**当前：N01工具、制品与恢复材料已形成限定证据，整体准入仍未完成。** 最新Linux/py310的71项现有原生/游标/消息回归通过；固定9条官方CVE源并补核96wheel的21,826条RECORD、21,730个有摘要成员及18个非法夹具。八项已认可的内部限定技术状态完成校准，正式软件决定仍未记录；两条上游询问仍无有效许可答复。Python维护/9条正式处置、两项精确通知及必要准入未关闭，最终安装锁未生成。N02—N08未执行，Python候选继续暂缓。详见[执行台账](native-linux-execution-status.json)和[统一剩余事项](native-n01-admission-decisions.md)。继续当前会话的已授权范围，不自动进入T014。
