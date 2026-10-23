# T034 内部研发采用依据、非算法处理器与初始配置

2026-10-22；用户委托下选定的研发实现输入v1。范围仅同一单位内部、当前 Linux / Miniforge py310 / CPU 研发。依据是用户本日对 E01—E04“全部未确定、由我们自己定制合理依据完成开发”的新授权，以及已批准的 T034 I01—I05 计划。该授权足以制定并实现下列研发配置与适配器，不需要再次就同一范围泛泛请求设计许可；它不是已经存在的人员身份映射、软件发布、当前许可、真实案件授权或恢复证明。

徐昌胜已登记为 T034 开发负责人及指定复核人。这里可以由其组织内部研发材料复核；这个名字及 GitHub 账号不能代替 Keycloak 的 issuer/sub、数据库 user/org/case，也不自动授予业务采用/撤销 EXECUTE。本追加设计未读取私密配置、令牌或密钥，未执行服务或数据库变更；本轮选定下列研发工程初始值，尚未写入运行配置；正式业务事实仍由真实来源提供。

## 1. E01：先建立真正可审计的研发采用渠道

推荐采用身份为 `internal-rnd-task-plan-authority-v1`，适用环境标签为 `linux-py310-cpu-internal-rnd`。两者是新协议/配置名称，不是已登记的受信身份。采用依据记录使用 `研发任务计划采用记录 v1`：必须有环境、具体 request 适用元组、三材料/回执摘要、受控导入工具源码/制品摘要、实际执行身份、徐昌胜限定复核记录、有效期、撤销方式和变更理由。原用户授权引用为“2026-10-22 同单位非算法研发定制授权”，不扩写成正式业务制度。

下一批实现固定管理函数和工具：`prepare → validate → register inactive → activate exact revision / revoke`；register 默认 INACTIVE，active/revoke 只能由单独配置的管理登录执行。runtime、普通前端、HTTP TaskCreate 都不能向自报回执写 validated=True。工具先检查实际 issuer/sub 到 user/org 的唯一有效映射，检查该主体仅在真实登记的研发案件成员范围内，再核对 expected head row_version、材料字节及完整收据。管理登录仅有固定函数 EXECUTE，不直接拥有任意表写权限；私有 NOLOGIN definer 角色不能被 runtime 继承。

采用记录与审计至少保存：`basis_id/version/hash`、`operator issuer/sub + mapped user/org`、`case_id`、policy 完整身份与 hash、plan/capability 三元组、revision/head 期望版本、验证器版本/源码 hash、原始回执 bytes/hash、有效期、环境、批准范围、撤销版本/原因。收据的正式内部 Schema 应新增并版本化，禁止把 I01 离线准备 manifest 或 opaque receipt 自动当该记录。校验器必须覆盖三正文及 Schema/规范化版本；metadata 仍只返回有限投影，不扩公开 API。

真实 subject/org/case、实际管理登录、现有安全管理员授权边界未知。下一批先提供只读 inventory/差异说明和未激活注册工具；实际导入只接管理员确认过的现有身份目录，不能用姓名、测试 UUID、github login 或首个可读案件猜映射。若需要新的纯研发组织/案件，须用现有 IdentityDirectory 受控方法真实创建、记录实际返回 ID，并明确其是新建研发空间；不能冒充公安业务单位或实际案件。本文不代执行，也不替管理员授权。

## 2. E02：最小可实现材料与一节点工程任务

公共 TaskCreate 已允许 `modules=["RESOURCE"]`，三个 scene 枚举为 accident_rumor / harmful_content / repost_tamper_trace。推荐首个计划只针对单一确切元组：`scene=repost_tamper_trace`、`modules=["RESOURCE"]`（顺序固定）、`priority=normal`。scene 在此仅为既有路由适用代号；只做原件完整性读取，绝不声称已做篡改、同源、风险或传播判断。其他 scene、module、priority 不自动匹配；以后需要时逐份新增并独立复核。真实 org/case、policy_id/kind 与现有记录绑定后才能生成完整材料。

建议版本名称（仅候选名称，未登记发布/采用）：

| 项目 | 建议值 | 不能预填的内容 |
| --- | --- | --- |
| policy version | `dev-resource-integrity-1.0.0` | policy_id/kind 必须实际创建或选定且唯一；不是任意同 version 取第一条 |
| plan id / version | `internal-rnd-original-integrity` / `1.0.0` | plan SHA 只能由完成材料的规范字节计算 |
| capability id / version | `internal-rnd-original-integrity` / `1.0.0` | release_id、包摘要、许可采用依据及可用状态不能造值 |
| node_code | `VERIFY_ORIGINAL_BYTES` | 尚无已发布 T034 callable adapter，当前不得派发 |
| required / missing_policy | `true` / `FAIL_REQUIRED` | 失败真实失败，不产生空结果或模拟成功 |
| dependencies | `[]` | 只有一个实际节点，无模型/未来虚构上游 |
| model_dependencies | `[]`，必须显式 | 仅表示本计划不调用模型，不豁免 handler 权威和许可 |
| input/output Schema | `urn:media-trace:api:0.1.0#/$defs/ObjectRef` | 当前实际存在的闭合三字段 Schema；不是任意字典 |
| input_bindings | object_id←asset.object_ref.object_id；version_id←asset.object_ref.version_id；sha256←asset.object_ref.sha256 | 全输入清单另保留真实 asset SHA、来源授权版本及资产身份；不能从客户端读对象存储 URL |
| output_refs | `["verified_original"]` | 仅核验后返回原固定 ObjectRef，不虚造派生对象、模型结果或报告 |
| pre/post protocol | 建议分别 `identity-bytes-v1` / `verified-original-ref-v1` | 必须由新增 adapter 实际实现、测试并纳代码/包摘要后才登记 |
| dispatch protocol | 建议 `internal-task-node-v1` | 当前 T034 派发消费者未实现；不复用上传事件当已接通 |

### 2.1 已存在 callable 与缺口

真实可复用函数：`business_app.asset_download.buffer_verified(stream, size, sha256, limit) -> bytes`，文件 `backend/business_app/asset_download.py` 第58—78行。它实际逐块核对类型、总大小和 SHA-256，超过固定上限拒绝，最终关闭流；不返回未核对前缀。LF 精确函数文本 SHA-256 是 `b4d04e4f437043e95e1078eb001c5c2bb379e40e0c552647eb5e28bb5d5643c7`，完整文件摘要见附录。

该 helper 不是已经存在的 T034 handler：它的 Python 参数不是 ObjectRef JSON，尚无本计划的 release/package/current-state/adoption 记录，也没有 T034 控制节点消费者。故当前可执行 DAG 数仍为零，不能把上述建议写为 ACTIVE 或宣称正常 202 已具备。

建议新增固定 adapter `business_app.handlers.original_integrity.OriginalIntegrityHandler`（当前不存在）：接受严格 ObjectRef 与显式可信 node context，通过现有 ScopedObjects/CASE 根按真实 asset/object/source 绑定读取，size 从同根数据库事实读取，limit 来自显式研发配置，调用上述 helper。成功且末尾授权/固定版本仍有效后，输出同一个已核对 ObjectRef；另外记录实际核验事件、输入/处理器版本与节点状态。该节点只证明这些字节与已登记大小/SHA 一致，不能把它写成取证有效性、真实来源或模型结论。adapter 必须有固定注册表 allowlist；handler_id 不得成为任意 import 路径/命令，材料解析仍不导入模块。

输出是经过完整性检查的原引用，不是新派生对象。TaskCreate 原子受理只能创建任务/节点/计划/事件；不得提前执行此 helper 或将节点标 SUCCEEDED。I03/I04 实现后，实际执行与输入物化仍通过 T036/T037 等依赖接入；新节点未执行时 report_eligibility 只能保持 draft_only，无 result 不插 task_result。

`UploadValidationWorker.consume_validation` 是真实上传校验消费者，但绑定 upload event、owner、来源 upload 用途及上传事务；不能当 analysis/createTask handler。`uploads.validator.inspect_uploaded_media` 是现有 SHA/MIME/尺寸校验 helper，含 PIL 解码且不是登记的 DAG adapter；本最小计划不调用它，不借此扩大 Pillow 使用路径。`backend/app/worker.py` 明确是 `media_trace_poc` / poc.analyze，`task_plan.py` 明确只有不可变工程候选图；两者不提供正式业务执行权威。

### 2.2 软件来源与许可材料建议

项目 LICENSE 声明 Apache-2.0，可作为自有新 adapter 内部研发来源材料之一；并不自动覆盖所有第三方依赖、样本或未核验的历史材料。新 adapter 采用现有依赖，不增加 Python/包候选；本路径只复用现有哈希/对象访问能力，不以“不调用 PIL”宣称原锁或现有扫描全部安全。

release_id 在真正形成发布记录时由受控工具生成，code_sha256 指确定的 adapter/source cohort，package_sha256 指确定性制品清单及实际归档字节的摘要，二者不能把当前 helper 文件 SHA 机械填到两个字段。受控 release/license 状态表保存完整引用、真实归属/许可证据 ref/hash、同单位内部使用范围、审阅人、版本、撤销状态；没有记录时返回未知，不默认 True。只需补包清单、既有 LICENSE/NOTICE/第三方覆盖材料及可复现构建记录；不等待外部业务数据才写这些工具。

## 3. E03：真实事实适配器，不用自由布尔覆盖

| 事实口 | 下一批可实施内容 | 仍须来自实际环境的内容及拒绝方式 |
| --- | --- | --- |
| identity / org / case | 复用现有 token 校验、IdentityDirectory/SqlScopeLookup及 CASE 成员 SQL；提供只读唯一映射 inventory | 真实 issuer/sub、组织、案件及启用状态；缺失/撤销/跨范围继续401/403/503，不创建假映射 |
| source / purpose | 复用实际 source_registry 的 verified、analysis用途、版本/expiry、同案件边界 | 公共样本许可不是案件用途授权；不能因下载了公共图片而自动允许analysis |
| classification | 新增小范围内部研发资料分类记录及显式只读 adapter，带 asset/source/version、分类依据 ref、作用域、撤销/有效期；接现有 supplemental 的独立 classification check | 首批可定义类型 `INTERNAL_RND_PUBLIC_OR_SELF_CREATED`，但每个资产必须实际登记许可/自建依据、内部用途且不含敏感资料；没有记录不能把 label 或 classifier=True 当事实。该名称是新研发规则，不是公安数据分类制度 |
| handler 当前发布/许可/可用 | 新迁移建精确受限登记关系及固定 read/update 函数，按完整 reference 查唯一状态；实现 CurrentCapabilityStateReader，同连接逐项核验真实发布、许可、可用/撤销、来源版本和 evidence_ref | 尚无 handler/release/license 状态关系及真实 adapter；现在该口 None。CASE 持确定行 SHARE锁至commit，所有受控更新先epoch写锁；不能远端HTTP读一个总True或把字符串 CASE_SHARE_LOCKED 当锁 |
| adoption/receipt | 新内部收据 Schema/受控校验工具与采用/撤销函数，把 verifier源码/包/三正文/Schema/规范化/导入身份固定进回执 | 当前 opaque receipt/ACTIVE head不能变成正式采用；实际identity/basis/回执必须先建立并核对 |
| recovery generation | 实现独立 GenerationReader：读取数据库备份之外受控维护的私有权威清单，精确数据库名/OID、generation、minimum_epoch、policy版本/SHA、确认时间/期限；读取必须拒重复键/符号链接/过宽权限/旧或错绑定 | 不从刚恢复库自读自证，不使用常量 fake-generation。清单须通过实际维护过程登记、独立保管/更新，恢复后新OID/代际重新绑定；若选择签名来源，不使用已泄露旧口令或尚未真实验证的签名密钥。T013本人交接仍是原待办 |
| dispatch | 新固定 node handler registry、T034专用事件/消费者与实际幂等/租约/撤销复核 | 上传outbox消费者和PoC不是该消费者；没有当前服务/来源/能力证据则不派发，不把任务入队当执行完成 |

后续迁移只能在0017之后追加，按执行时最新 ledger 取下一个编号；不预占或覆盖别人的迁移、不修改已发布0016/0017。新增表 FORCE RLS；普通 runtime 不读私有采用正文或管理凭据。固定 manager/update函数不得授给未映射实名主体。能够继续写代码和隔离测试，不因缺真实映射停掉所有工程工作；任何缺项只阻断对应真实放行动作。

## 4. E04：建议直接落实的研发配置值

以下为本次新授权下选定的**研发工程初始值**，不是从历史配置发现的已生效数值。下一批在 development/test 专用配置层显式序列化，核心解析器/服务仍要求传入；production 保持拒绝。环境缺配置/非法值不得悄悄回落；不修改原100包锁、现有扫描或CI门禁。

| 配置 | 建议研发值 | 依据与实施约束 |
| --- | --- | --- |
| MaterialBudgets.max_bytes | 262144 B / 每个材料 | 每份256KiB足够一节点引用型JSON；不是媒体限额。各输入及规范字节分别验证，重复键/NaN/非法UTF8照常拒绝 |
| max_nodes | 16 | 首批真实计划仅1节点，16为工程解析上限，便于后续少量工程节点；不为补足上限造节点 |
| max_capabilities | 64 | 沿现解析器含handler及model引用计数定义；首批仅1handler、0model。能力预算不是可用性声明 |
| bundle aggregate budget | 1048576 B | 四份主材料累计不超过1MiB；现 MaterialBudgets仅逐材料，此累计约束需新增工具/服务检查，不能说已实施 |
| snapshot aggregate budget | 4194304 B | 16个node snapshot各不超过256KiB，并另限总和4MiB；避免复制放大。收据/有限事实各同256KiB，另纳请求整体预算 |
| HTTP TaskCreate body | 16384 B | 仅6字段/引用，16KiB足够；需guard在strict解码前检查原始字节，重复头/查询/body校验仍保留 |
| proof_budget_seconds | 30 | 研发短事务余量，不复用旧5秒条件默认。最终valid_until取当前时间+30秒、Principal/来源/成员/采用/能力/独立generation所有真实截止的最小值；明确无截止与未知分开，未知拒绝 |
| control_ttl_seconds | 86400 (24小时) | 显式研发控制回执重试窗口，覆盖同一工作日与跨晚间恢复；不是upload TTL，也不是权限有效期/审计保留期。过期不重放旧成功，仍重新核当前授权/精确revision |
| mapping/adoption maximum duration | 604800秒 (7日) | 初期研发材料变动频繁，避免长期自动采用。每次导入明确valid_from/until，受全部实际许可/授权截止进一步约束；仍需实际采用记录，不设置默认ACTIVE |
| generation evidence max age | 30秒 | 受控独立来源明确续期，reader每次真实读取并校验来源；不是把旧文件有效期自动滚动。维护来源未建立继续None/503 |
| capability evidence lease ceiling | 60秒 | 仅真实提供方可明示的短期可用证据上限，release/license状态仍逐项同事务读/持锁；不以计时器虚造可用，不自动延长源事实期限 |
| node_lease_seconds | 60 | 仅未来工程消费者的显式租约，超过可恢复/重领，完成前核版本/attempt/授权；不是允许运行60秒且免复核。当前未配置者不改现存服务 |
| max_object_bytes | 1048576 B | 与已有 preview 最大上传1MiB一致；是研发目标，不扩用共享容量。第一个helper最多缓冲1MiB，无PIL/模型运行 |
| handler hard deadline | 10秒 | 首批仅1MiB哈希/受控对象读；包含对象读总时长并可取消，不靠将来无法终止线程的wait_for假定执行已结束。实现时用可中止的有界read/子进程或provider deadline并测试 |
| DB connect/pool timeout | 各2秒 | 与现Database默认一致；保持 pool_size=1、max_overflow=0，不提高共享数据库并发 |
| DB statement_timeout | 2000ms | 与现Database默认一致；不因加速交付改大。锁等待建议新增SET LOCAL lock_timeout=1000ms，超时拒绝，不无界重试 |
| create transaction deadline | 10秒 | 独立总预算，涵盖多条2秒SQL；每关键阶段与commit前重验deadline/Proof。未提供真实可中止机制时不能声称总时限已强制 |
| concurrent handler execution | 每个研发worker 1项、prefetch=1 | 先单条真实链路，避免CPU/对象/DB争抢；不等于已达到20/100并发 |
| private temporary per task | 8MiB，最多2个未完成任务缓存 | 足够1MiB原件、少量规范JSON及日志/小输出，超限拒绝；仅新私有目录且失败清理，不删除历史或共享卷 |
| startup free-space guard | 5GiB | 复用 scripts/business_development.py 已有隔离实例5GiB防线；是启动安全余量，不声称服务器当前满足、不替代数据卷扩容 |

不在本文给宿主机新CPU/内存配额：没有重新盘点负载/现有服务可用量，不能把之前候选15.5核/18.5GiB当事实。新增工程worker先限制单并发及上述输入/时间/临时空间，再由现有资源盘点记录决定额外进程上限；不重启共享服务。输出/报告保持草稿及真实状态，无模型输出不得补分数。

建议配置名统一放一个新的 `task_creation_development` 私有对象，包含预算、超时、环境标记与固定adapter allowlist；仅 control_ttl_seconds/node_lease_seconds 可复用已有 BusinessSettings 字段。其余名字是新增配置设计，不谎称现settings已经支持。每个字段必须type严格校验（bool不是int）、有限正数、上界及相互约束；配置摘要加入校验/采用记录，调整影响Proof/快照时必须生成新版本。

## 5. 可以立即推进的下一批与可验收边界

1. 新增 development/test 显式配置解析器及上述预算/TTL测试，保留 production拒绝；配置从仓库外私有文件读取，读取后冻结，禁止前端提交阈值覆盖。
2. 实现一节点 OriginalIntegrityHandler 固定 adapter、输入/输出ObjectRef约束、代码清单/确定性包清单；先真实自建无敏感夹具单测、错误大小/SHA/版本/权限/超时与零输出负例，不下载算法或数据。
3. 追加受控采用/回执、精确handler状态与classification登记关系/固定函数/真实适配器；新随机库串行验证RLS/角色/锁序/撤销/恢复；不预填真实目录、ACTIVE或许可可用True。首次注册INACTIVE。
4. 编写真实身份/研发组织/案件的只读inventory与显式绑定管理工具，读取实际已认证 issuer/sub，生成可核对差异单；执行管理员步骤时给精确ID/命令/影响范围，不再就泛泛“是否继续设计”询问。
5. I03按已批准计划完成同事务 task/run/run_plan/node/event/outbox/control receipt 原子创建，I04接线，I05验证实际失败/重放/恢复。E01—E03实际来源缺失时可验工程拒绝路径和纯组件，不能登记真实正向202。

本追加设计确定下一批研发实现输入，不新增业务完成项。真实管理身份、精确org/case、真实来源用途、可信classification/adoption、当前handler状态及独立恢复来源若尚缺，继续逐项保留未完成；但无需恢复Python候选或算法，亦不影响编写上述工程实现和必要测试。

## 6. 本次只读来源摘要

基线提交：`0d3142cab76d65196593f3588f90bef2b56d0f36`；工作树还含本批I02未提交实现，下面记录的是读取时实际LF字节摘要，不把HEAD等同全部工作树。摘要仅锁定资料，不证明其运行/许可/实际环境状态。部分文件可能由ROOT后续状态更新，整合时需重核。

| 实际读取文件 | SHA-256（LF） |
| --- | --- |
| `AGENTS.md` | `3e8da2f265c6d659519faa3506ed00cf844aa3380450773a3e72391d2a1c9931` |
| `docs/03-development/t034-creation-implementation-plan.md` | `d2417eaf24a85688e8bf82eba0f5ad24c4e8b86104c673b7624f2a3419ff6006` |
| `backend/business_app/task_creation.py` | `5024c68b443b7898e266e4cdff45ba67242a4f17eff58bb47925a04cee87c2d3` |
| `backend/business_app/task_creation_authority.py` | `c08fb7ac51a1300ac349754075de950489962d56035db750ee439fb902ae91e8` |
| `backend/business_app/task_creation_materials.py` | `3728d6fca9efd69766d6e955093933f2c3738eb89cc256304a895643b4392a4e` |
| `backend/business_app/permissions/task_creation_context.py` | `d965a25fe6470c200a93514c0c2fec77ffe56acc294c4a523e6fdfac4c576245` |
| `backend/business_app/permissions/task_creation_facts.py` | `4c5cbf74857d939dd71ac3a62625f65f6752c8839c366b99eb8c21b8c6c9c6a9` |
| `backend/business_app/task_creation_sql_authority.py` | `cc0ae778ff11417f6042d58a024a628b44f38eadd3885f6680c819bdc578ecb9` |
| `backend/business_app/permissions/fence.py` | `f908e17c75fcc1b30ddf4d620710a7bbdd434c255bcf41a7b7ff89f152ecea40` |
| `backend/business_app/settings.py` | `159f270e7339cb39f6ac6b745b8583d55f7fe471c606e5e0c001ba63938daa84` |
| `backend/business_app/db.py` | `8ca7f2131d065dd1fada9332de03a431e655e7113d7b1864a19b1a1490b7a7ff` |
| `backend/business_app/asset_download.py` | `da13f332f7d02586fbde1723966deda0fe5879b56a5805439b9d6a3ee337476b` |
| `backend/business_app/uploads/validator.py` | `d7fed4480d08e337aa4804e5da7dd724e31988b9a3a9e9da879c96e13f4574da` |
| `backend/business_app/uploads/worker.py` | `4402f7afc5c1f1d64a9512a0eb4c7da27b83cdc2756abc35117084d3d82bc4b9` |
| `backend/business_app/task_plan.py` | `42609f5393e5730dea0765c53eaaaa1ed94adbe4a55b444f6736c177b8b010e9` |
| `backend/business_app/development.py` | `3fabb34ae818f385fed5e7210fb6b8dfb6a47eaa5d657f1657cba8f3d096388b` |
| `scripts/business_development.py` | `bd54daa4469e67a08e75e7a7548c13ca8a6a8a5d4d2d20f6ef4c229e3f36ef2b` |
| `backend/app/worker.py` | `71cf642578b91bb45d2f7abab3854e6bd3572fe6d85c8b1f5be2c8cdcc486e89` |
| `backend/business_app/identity/directory.py` | `9cf18a158b7dc6e0205e09280d35b4eabf2ad9b671f837ad1fccbabe7da56a9e` |
| `schemas/api/common.schema.json` | `f0f97b23bf7e6dbf0ffe62b0ac5f55b033b5aa3c24739436d2be0fcf44cfe269` |
| `schemas/development/task-execution-plan.schema.json` | `e1f8d14db844891cdae6906567ebe282f9f9015ef8e40a50a67a09dffdca0c80` |
| `schemas/development/task-capability-manifest.schema.json` | `07fec017f993673ce551d2881baa14adff30bec0bee340b61c843330b4a7b659` |
| `schemas/development/task-input-manifest.schema.json` | `32fa092a1c23234460a867692a7d88a1e27baf09d0c4fddb4feb635e1c53bcf9` |
| `LICENSE` | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |

校验方式：只读源文件/Schema/配置及AST定位函数，无业务模块导入、网络、DB、测试或服务执行。本追加设计未生成新迁移、实际许可文件、人员/案件记录、活跃映射或密钥。
