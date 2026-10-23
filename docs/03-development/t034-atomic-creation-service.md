# T034原子创建与精确重放：I03隔离候选

2026-10-23补齐T034-I03隔离原子创建候选：同根CASE/createTask、明确受信材料端口、A/B及当前采用绑定，双savepoint内完整八表和CREATED→QUEUED、精确历史Accepted/ETag重放及提交前复读已实现；新增0018只修generation.database_oid的JSON整数投影，0001—0017及严格reader不改。事务/新迁移组合82项、受影响组375项、原失败探针及Ruff/格式/288文件类型检查符合预期；完整business实际结果TIMEOUT另列原始汇总，T014未单独重跑，重叠数量不相加。本批无默认权威、可信采用/Proof、HTTP挂载、共享迁移或算法执行；并发、恢复、未知commit结果及E04运行预算仍未齐，0新增C，T034保持4C/4R。

依据[已批准I01—I05计划](t034-creation-implementation-plan.md)第5节，实现[TaskCreationService](../../backend/business_app/task_creation_service.py)。仅为Linux/py310/CPU隔离工程候选；不挂载HTTP，不生成真实采用、Proof或ACTIVE，不执行handler，也不发送MQ。完整源验收仍见[T034任务卡](../../tasks/backend/T034.md)。

## 接口与同根边界

构造器显式接收Database、BusinessSettings、MaterialBudgets及可选材料端口；端口缺省为None并拒绝。`create(scope, body, *, idempotency_key, request_id)`沿用公共TaskCreate正文；request_id必须为非零UUID。调用者须已有同根CASE/createTask mutation、匹配主体/单位/案件/资产/analysis用途及B摘要，并绑定相同冻结上下文；同库不代表授权，结构正确的自建材料也不是机构批准。

A为原正文规范字节摘要，保留UUID字面形式和modules顺序；B沿用权限请求封套摘要，二者独立保存。受信端口在同连接返回完整PlanBinding/ExecutionMaterials，服务复用严格复制与重查，不从metadata拼造authorized=True。来源须有analysis用途、verified状态和有效期限，资产须VALID且对象版本/SHA及来源授权版本与输入清单一致。

## 原子写集合

| 表 | 本批保存的实际内容与边界 |
| --- | --- |
| analysis_task | 先CREATED，条件更新为QUEUED；row_version从1到2，progress=0，run/result版本均1，draft_only，无伪结果 |
| task_run | 原run1、实际输入manifest摘要、实际plan_version及policy_version |
| task_run_plan | 0016既有36列完整不可变快照：正文A/B、revision/head、policy/plan/capability规范字节、原始采用回执、输入、有效期及恢复代际 |
| task_node_run | 每节点attempt1，输入摘要来自对应规范snapshot；无依赖READY，有依赖PENDING；无开始/结束/租约/提前成功 |
| task_event | CREATED→QUEUED、run1、原request_id及受理event_id |
| outbox_event | 与task_event同一event_id，workflow.run.accepted.v1、scheduler、QUEUED；只记派发意图，无MQ发布 |
| audit_event | 原主体、请求、task受理版本及A/B/revision关联审计事实 |
| idempotency_record | 同主体/案件/createTask/key的严格内部回执，绑定key、原Accepted/ETag、完整材料身份、原run_plan摘要及节点snapshot |

task_result不新增；事件result_version和result_snapshot_ref均为null。输入Schema未声明missing_modalities，本批存空数组，不伪造缺失判断。队列受理也不代表后续消费者或算法具备实际执行能力。

## 锁、savepoint与提交

先核对同根及已知幂等A/过期冲突。该幂等预读只拒绝，不返回受理，也不取得advisory锁。材料提供方按现有epoch、资产/来源、采用/正文锁序读取，随后才取得同key事务advisory锁；锁后再次核对root、材料新鲜性和来源期限，等待跨越有效期时首INSERT之前拒绝。

资产和来源使用既有FOR SHARE；object_version依其既有不可变约束及SELECT读取，不为锁对象增授UPDATE。内层savepoint完成整套写入及响应校验；外层savepoint包住内层释放和before_commit注册。注册失败或外层释放失败回滚本批，并仅清理本次callback；调用者捕获错误后继续提交外层也不得留下半写。

before_commit同根复读当前PlanBinding/ExecutionMaterials、资产/来源和完整持久集合，再采样时间；新任务总集合必须精确、结果数为0。Database随后执行既有fence.finish和根commit。拥有根事务的调用返回前须完成这些步骤；继承外层根时返回只是内部候选，外层尚未commit，不能宣称HTTP202已发出。聚合预算、运行预算和硬截止未因本批自动生效。

## 原响应重放

同key、同A、未过期且完整回执可读时，仍要求当前有效head、授权、材料及原revision绑定成立。回执严格闭合并核对B、原run1、36列快照、节点输入、原事件和审计；损坏或不匹配拒绝。可接受当前任务/节点合法进展，后续run、attempt和result数量不作新建总数限制；原Accepted始终QUEUED，原ETag不随当前任务状态重写。当前状态从status_url另查。已过期的历史Proof有效期不作为新许可；当前端口仍须提供新鲜有效材料。串行重放不能替代独立连接竞争或灾后恢复证明。

## 0018增量与实际失败保留

真实CASE/LOOKUP投影RED发现PostgreSQL oid的JSON表示为字符串，严格reader要求正整数；新增[0018](../../backend/business_migrations/0018_task_creation_generation_json.sql)只在两处generation.database_oid构造中增加bigint转换。0001—0017和Python类型断言保持。该迁移先核对原函数字面源码摘要、固定签名和owner边界，再由原NOLOGIN owner执行精确替换；OID、ACL、search_path、其余pg_proc属性及comment守恒。临时schema CREATE位在同一迁移事务内撤回；非超级schema owner沿用管理员准备的SET-only/NOINHERIT/no-ADMIN前提，不新增角色继承。异常自定义源码/owner拒绝并回滚。

首个组件缺失RED、实际metadata smoke失败、CASE/LOOKUP整数RED、首次0018后42501及静态类型失败均保留独立原回执摘要；不以最终通过抹掉失败。42501修复去掉只读不可变object的行锁，未给它UPDATE；类型修复仅收窄新返回值/局部变量和夹具存在性断言，无ignore、skip、删测试或放宽断言。validator_id=7不是本轮已证根因，原SQL已将非字符串投影null。

## 实际验证与验收

精确命令、时间、源码、失败历史和CI状态见[机器回执](../00-project/validation/t034-atomic-creation-service-report.json)。本批组合82项、受影响组375项及Ruff/格式/288文件类型符合预期，原故意失败探针保留；完整business原汇总状态为`TIMEOUT`，T014本批未单独运行，数量不相加。

| 核验项 | 本批结论 |
| --- | --- |
| 同根/A/B/材料与来源绑定、首次完整写集合、精确重放及损坏拒绝 | 隔离适用范围通过 |
| 逐写入/响应/注册/最终提供方/fence/commit失败，以及外层捕获后零半写 | 隔离适用范围通过 |
| 0018空库/升级、原owner/ACL/config/comment和管理员SET-only安装边界 | 隔离适用范围通过 |
| 独立连接并发、灾后代际/回切、commit结果未知或响应丢失 | 本批未完成完整证明 |
| 真实采用/许可/分类/handler提供方、Proof签发、HTTP挂载和正式202 | 未提供或未实现，不验收 |
| 整卡、共享环境、生产与算法能力 | 未验收，未变更 |

## 完整回归门禁：未通过

本批最终源码的完整business组实际达到既有1800秒上限，终态TIMEOUT，退出2（预期0）。最后安全进度为`tests/business/test_t014_runtime.py::test_function_permission_never_grants_unrelated_case_or_unit_resources`的setup。没有生成完整JUnit统计，汇总tests=0表示统计不可用，不能解释为没有执行、已经通过或没有失败。该完整组后续失败探针未运行；此前82项组合后的原故意失败探针单独已验证，不代替完整组终态。强制超时后的隔离资源清理尚未核验。

下一批优先定位这个精确源码/环境的限时原因，核对隔离资源及每段耗时后保持原1800秒、原断言和扫描门禁再验证；不借上一版CI通过关闭本版失败，也不推断为某个业务断言或环境随机故障。本批仅同步有明确限制的研发代码候选，不合并main或标完整门禁通过。

## 剩余工作

继续按真实依赖补I03独立连接并发、恢复和未知commit结果验证，再做I04显式HTTP/启动注入及I05完整适用门禁。真实管理/采用/分类/handler/许可事实与E04运行预算独立补齐；现有算法与Python候选继续暂缓。内部隔离批不要求用户提供密钥；真实采用和部署所缺资料仍按既有待决清单确认，不用自建夹具代替。

下一批并发测试使用两个独立Database连接、各自上下文/材料reader/fence与request_id，以有界屏障及pg_blocking_pids确认实际advisory等待，不能用单连接池或sleep冒充竞争。同key同A应仅写一套8集合并返回相同原Accepted/ETag；同key异A须让两个请求都具备有效隔离材料，再确认409且只保留赢家事件/request_id。撤销竞争分别验证“创建先取得真实SQL epoch共享锁，撤销等待后提交”和“撤销先提交，创建随后拒绝”；不把FixtureFence当真实GenerationReader或正式撤销账号。

未知提交须另设计安全的私有短生命周期PG代理，区分真实COMMIT完成应答丢失与发送前断链；协议/TLS阶段无法确认时保留未验。重试沿用原key/body并通过新的完整授权/材料上下文调用create，管理SELECT仅可作测试oracle。现有commit事件注入只能证明driver提交前回滚，不能替代此验证或备份恢复验收。

全部170项仍154条已证子步骤、622组剩余，T001—T123仍434组剩余，0整卡验收；T034保持4C/4R。新候选、测试数量和源码同步均不自动新增完成步骤。
