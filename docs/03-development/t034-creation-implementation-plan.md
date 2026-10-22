# T034任务创建接线实施计划（I01—I05）

2026-10-22（北京时间）。状态：**IMPLEMENTATION_PLAN_PREPARED_REVIEW_PENDING**。本轮仅编制计划，未实施产品代码、迁移、采用登记、HTTP挂载或数据库验证，不增加业务完成数。

用户已在本次会话认可[创建接入设计](t034-creation-integration-design.md)的D01、D02，并要求继续D03实施计划编制。该确认包含同库current-head/不可变revision方案，以及Proof能力三元组指向执行能力清单版本；不包含本计划执行、真实映射生效、预算采用、共享部署或正式验收。原设计中的历史“待审”文字以其编制时状态理解，执行授权仍须按本计划审阅决定单独记录。

本计划核对基线为`cf3f783b3d4762b415622238099e8097b6256d78`。编制时另有`tests/business/test_upload_worker_process.py`未提交修改，属于并行T024工作；本计划不修改、纳入T034完成证据或覆盖该文件。开始实施前重新核对HEAD、工作区和迁移编号；发生实质差异先更新受影响部分。

开发负责人及指定复核人沿用徐昌胜，责任登记不表示已经复核。源任务为[T034](../../tasks/backend/T034.md)，源前置依赖T033、T015完整保留；这里仅安排已授权非算法工程子范围，不以编号顺序或本计划替代原依赖和验收。

## 1. 执行边界与当前事实

| 已有且须复用 | 本批计划补齐；当前尚未实现 |
| --- | --- |
| `task_creation.py`的不可变TaskCreateRequest、TaskPlanProof、freeze/resolve/recheck及64项内核测试 | 真实SQL计划权威、完整正文、逐项能力与输入核验 |
| `Database`、transaction-local scope、before_commit及AuthorizationFence | createTask专用请求上下文、受限事实/正文函数及原子创建服务 |
| `ControlReceipts`的同主体/案件/operation/key事务锁与回执 | 带精确revision及原Accepted/ETag的createTask内部回执校验 |
| 公共TaskCreate六字段、Accepted三字段及createTask/task.create目录 | POST `/api/v1/analysis/tasks`实际挂载、保护及故障验证 |
| 0001—0015增量迁移、CASE/LOOKUP元数据与RLS | 拟0016权威材料/采用head/run计划快照、限定SQL及ACL |
| `model_registry`、`model_release`登记与版本字段 | 真实许可、普通handler发布/撤销、执行输入及业务采用依据；现有状态或引用不是这些事实的替代 |

禁止改公共TaskCreate字段、三场景/十二模块/priority词表、Accepted、既有HTTP错误及幂等语义；禁止改原100包锁、CI门禁、共享服务和数据库；不实施算法、模型训练、Python候选、任务消费者或正式发布。CandidateDAG仍是工程候选，FileDefinitions仍是正文存取能力，均不自动产生采用权威。

正向隔离测试可在随机新库中使用明确自建的采用者、材料和事实夹具；不得将其配置为业务默认或写入共享ACTIVE行。E01—E04未提供时允许完成相应基础代码和拒绝验证，但不能据此登记真实可用202、T034整卡完成或业务映射已采用。

## 2. 交付批次、顺序及具体文件

下表路径除明确“现有”外均为拟新增。每个批次独立提交代码、必要测试及限定回执，先通过该批验证再进入依赖它的后续批次；失败或外部条件缺失保持失败/未验，不能用计划或空拒绝路径折算整项完成。

| 步骤 | 允许修改/新增文件 | 前置和完成条件 |
| --- | --- | --- |
| I01 同库材料与内部规范 | `backend/business_migrations/0016_task_creation_plan_bindings.sql`；`schemas/development/task-execution-plan.schema.json`、`task-capability-manifest.schema.json`、`task-input-manifest.schema.json`；`backend/business_app/task_creation_materials.py`；`scripts/task_creation_adoption.py`；`tests/business/test_task_creation_materials.py`、`test_task_creation_migration.py`；必要时仅扩展现有`tests/business/conftest.py`空库迁移测试名单 | 再核对0016未占用；严格Schema/规范字节、不可变约束和私有ACL可验证；迁移不seed ACTIVE、不回填历史；受控工具默认只做验证和准备，不给人员授角色 |
| I02 固定SQL、事实与请求上下文 | 同一拟0016中的两个只读函数；`backend/business_app/task_creation_authority.py`、`permissions/task_creation_context.py`、`permissions/task_creation_facts.py`；现有`permissions/object_facts.py`、`permissions/guard.py`、`scope_catalog.py`、`db.py`；`tests/business/test_task_creation_authority.py`、`test_task_creation_scope_sql.py`、`test_task_creation_context.py` | I01成立；LOOKUP无锁/无正文、CASE同根/持锁、请求主体/资产/A与B摘要隔离、动态能力未知拒绝、上下文并发不串用；不配置默认提供方 |
| I03 原子创建及精确重放 | `backend/business_app/task_creation_service.py`；I01迁移中run_plan写约束；`tests/business/test_task_creation_transaction.py`、`test_task_creation_concurrency.py`、`test_task_creation_recovery.py`；复用`task_creation.py`、`controls/receipts.py`、`controls/common.py`和既有事件Schema | I02成立；同连接/savepoint/根栅栏；完整写集合一次提交；每一写入和末检失败零半写；独立双连接竞争、当前head约束和响应丢失重放 |
| I04 HTTP与启动注入 | `backend/business_app/task_creation_router.py`；现有`main.py`及按需`development.py`的显式可选依赖注入；`tests/business/test_task_creation_http.py`；现有`tests/business/t014_requests.py`、`t014_positive_fixtures.py`和路由覆盖断言按实际挂载精确更新 | I03成立；202为Accepted，不含upload_id/伪结果；无真实配置仍拒绝；默认路由保护、精确头/query/body、缓存/Problem/日志边界通过 |
| I05 适用全回归与发布回执 | T034卡、`tasks/execution-status.json`、`tasks/README.md`、docs导航、开发清单/快计划及实际验证回执；新增`docs/04-database/task-creation-plan-bindings.md`逐字段说明本增量表、FK、字节摘要、RLS/ACL和固定函数；公共映射仅在真实字段映射发生变化时同步 | I01—I04的实际代码/输入/验证逐项成立；完整业务DB回归串行；原失败探针及安全扫描保留；精确提交CI与三端源码摘要核对；计划认可或本地测试不等于正式验收 |

`task_creation.py`现有Proof结构原则上保持兼容；新增内部`PlanBinding`保存revision、mapping、policy身份和材料快照，不能把它塞进公共TaskCreate。旧64项绑定测试及原T015/T016/T024断言保留。T024上传worker、outbox pump不承担T034计划派发消费者，不修改其独占文件。

## 3. I01：规范字节、材料模型与迁移约束

### 3.1 三类摘要与规范化

| 名称 | 固定算法/材料 | 不得混淆 |
| --- | --- | --- |
| A：`request_body_sha256` | 沿用`controls.common.canonical`：UTF-8、sort_keys、无多余分隔空白、ensure_ascii=False、拒绝NaN/Infinity；保留modules顺序和原JSON字符串字面形式 | UUID等值不使不同字面大小写的原body幂等摘要相同；不排序modules、不改policy/priority |
| B：`authorization_request_digest` | 沿用`permissions.object_facts.digest({path,query,body})`，包含路径/查询及该函数现有ensure_ascii/default=str语义 | A、B分别保存、分别复核，不能直接要求相等 |
| policy/plan/capability/input | 各自严格JSON Schema与版本后，以同一明确版本的内部规范化函数得到UTF-8字节；保存原规范字节及独立SHA-256 | 不用jsonb::text、文件名、definition_ref或plan hash替代其他摘要；数据库以`encode(sha256(canonical_bytes),'hex')`对精确bytea核验 |

内部解析器拒绝重复JSON键、常量NaN/Infinity、非法UTF-8、额外字段、重复节点/能力、环、未知依赖/绑定/Schema ID、空计划及不一致required/missing_policy；所有字节/节点/能力预算由显式配置传入，缺失或非正数拒绝，不在代码选择业务数值。JSONB仅作已核验正文的投影，不能成为另一份可变执行正文。

拟内部Schema身份分别为`urn:media-trace:task-execution-plan:1.0.0`、`urn:media-trace:task-capability-manifest:1.0.0`、`urn:media-trace:task-input-manifest:1.0.0`；它们是内部格式版本，不是实际计划/能力采用版本。使用现有SCHEMAS/REGISTRY加载机制，不改公共OpenAPI。Schema文件和解析器须一并测试。

执行正文至少固定：plan_id/version、scene/有序modules/priority适用、节点代码/有序依赖、required/missing_policy、显式handler_id/version/code_sha256、模型依赖（可为空但必须显式）、输入输出Schema ID、输入绑定、前后处理版本、输出引用及派发协议版本。能力清单逐项绑定同一实际handler/模型发布、代码/包摘要、输入输出、许可依据和当前状态读取协议；单个Proof capability三元组指整份清单，不指某个M编号。

输入清单保存真实资产SHA、ObjectRef三元组、来源授权版本、适用输入映射及各节点输入规范化清单。`task_run.input_sha256`指本次run输入清单；`task_node_run.input_hash`指对应节点规范化输入清单，符合现有数据字典语义，不冒充已生成的上游输出字节摘要。PENDING清单中的上游引用必须是获准正文明确的固定依赖选择器并标明未物化；不得填假对象、零摘要或成功状态。实际派发者仍须在T036/T037证明依赖已完成、精确版本/输入已物化及handler可执行，不能仅凭本次创建或该描述摘要运行模型。

### 3.2 拟0016数据定义（实施时转为完整DDL）

全局规则：UUID不得为零；身份/版本文本沿用Proof的1—128字符约束；SHA字段为64位小写hex；时间一律timestamptz；各行org必须真实存在，case须`FOREIGN KEY(case_id,org_id)`指向cases；证据来源、创建者和创建时间不得由客户端body代填。下表字段是实施契约，尚未创建。

| 表 | 固定字段与约束 |
| --- | --- |
| `task_policy_artifact` | `org_id uuid, policy_id uuid, policy_kind text, policy_version text, canonical_bytes bytea, policy_sha256 text, schema_version text, canonicalization_version text, provenance_ref text, created_by uuid, created_at timestamptz`；PK/UNIQUE采用org+完整policy身份；补policy_registry的`UNIQUE(org_id,policy_id)`及完整身份唯一键后使用复合FK；不得把DRAFT或APPROVED状态单独当采用依据 |
| `task_plan_artifact` | `org_id uuid, plan_id text, plan_version text, canonical_bytes bytea, plan_sha256 text, schema_version text, canonicalization_version text, provenance_ref text, created_by uuid, created_at timestamptz`；PK`(org_id,plan_id,plan_version)`；CHECK字节摘要一致 |
| `task_capability_manifest` | `org_id uuid, capability_id text, capability_version text, canonical_bytes bytea, capability_sha256 text, schema_version text, canonicalization_version text, provenance_ref text, created_by uuid, created_at timestamptz`；PK`(org_id,capability_id,capability_version)`；清单内容不能代替动态发布/许可状态 |
| `task_plan_mapping_revision` | `revision_id uuid` PK；`org_id uuid,case_id uuid,mapping_id text,mapping_version text,authority_version text,scene text,modules text[],priority text`；完整policy_id/kind/version/hash、plan_id/version/hash、capability_id/version/hash；`valid_from/valid_until timestamptz,adoption_basis_ref text,recovery_generation text,validation_receipt_bytes bytea,validation_receipt_sha256 text,created_by uuid,created_at timestamptz`；UNIQUE`(org_id,mapping_id,mapping_version)`及`(org_id,case_id,revision_id)`；精确复合FK绑定三份正文；期限有序、数组非空无重复，保持顺序 |
| `task_plan_mapping_head` | `org_id uuid,case_id uuid,scene text,policy_id uuid,policy_version text,modules text[],priority text`构成精确适用PK/唯一键；`revision_id uuid,state text,row_version bigint,changed_by uuid,changed_at timestamptz`；state仅内部`INACTIVE/ACTIVE/REVOKED`，无默认ACTIVE；revision复合FK及适用元组一致约束；不同policy kind若同时适用仍拒绝，不择一 |
| `task_run_plan` | PK`(case_id,task_id,run_version)`并FK到task_run；`org_id uuid,created_by uuid,created_at timestamptz`；冻结请求bytea与A/B摘要；mapping revision/authority身份；精确policy/plan/capability身份/摘要与规范字节；输入清单规范字节/摘要、材料校验回执/摘要、proof观测时点/期限、recovery_generation；各bytea与SHA均CHECK；不可UPDATE/DELETE/TRUNCATE |

三份artifact及revision追加不可变；head只可通过受控管理函数改动并递增row_version；run_plan追加不可变。迁移不更改0001—0015摘要，不对既有task/run补造计划，不删除、重算或改写历史。新建任务run_plan的必备性由当前服务原子写入和新增行约束验证；不设会强迫历史数据回填的全表约束。任何后续重算接入同样计划约束须另验，不因本批让现有重算端点伪成功。

所有新表ENABLE/FORCE RLS。五张组织私有权威表在`scope_catalog`显式`runtime_select=False`，不可落入默认组织可读集合。run_plan仅向mt_runtime开放CASE/createTask下必要SELECT/INSERT；FK与插入策略核对同org/case/task/run，其他operation不得借新表读取正文。

### 3.3 管理与读取角色

拟`mt_task_plan_lookup`：NOLOGIN、NOBYPASSRLS、非superuser，不得被mt_runtime或业务登录继承；仅有五张私有材料表及下节固定依赖关系的必要SELECT/EXECUTE和相应SELECT policy，不获写权限。拟`mt_task_plan_manager`为受控管理函数的NOLOGIN受限owner，具备材料追加/head更新/审计及epoch更新必需权限，不向业务登录授继承；`Database._unprivileged`同步禁止任何持上述管理/读取角色成员资格的业务连接。

管理函数采用`SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp`，REVOKE PUBLIC与mt_runtime EXECUTE；先取得epoch写顺序再校验受控导入材料/当前head期望版本、追加revision/材料、切换或撤销head并写审计。受信工具校验回执覆盖三份摘要、Schema/规范化版本、校验器代码版本/摘要和导入身份，数据库复核这些绑定、字节摘要和预期状态，不能接受普通runtime自报validated=True。E01未确认的实际登录映射、采用依据及工具身份不得猜填；本批迁移不创建人类账号、不授真实人员管理EXECUTE、不写生效head。工具默认离线验证/准备，真实采用执行需要E01—E04及明确操作范围。

## 4. I02：请求上下文、SQL接口及动态事实

### 4.1 固定内部类型与上下文

新增frozen `TaskCreationContext`保存Principal、freeze_task_create结果和B摘要；以ContextVar token/contextmanager在guard严格body解析后、首次conditional授权前进入，覆盖authorize_http、yield处理器、Database/fence及finally恢复。父异步任务设置上下文，线程池只读取不可变副本，不依赖子线程修改反向传播。不放app.state可变请求槽，不按actor/task做共享缓存。

新增frozen `PlanBinding`保存`proof: TaskPlanProof`、revision_id、mapping_id/version、完整policy身份、head row_version、材料校验回执和动态事实指纹；`ExecutionMaterials`保存严格解码后的正文与输入清单规范字节。现有Proof缺revision字段，**只调用recheck_task_plan不足以证明同一revision**：服务/事实复核须另行比较完整PlanBinding。即使两revision的plan/capability摘要相同，只要head或revision改变也不能重放或继续旧受理。

Proof期限取实际采用及所需授权/许可等有效期限、经确认Proof预算的最小有效上限；明确无截止时间与未知期限须区分，不把未知当永久有效。控制回执TTL、业务采用期限、认证有效期和Proof预算是不同配置，不互相猜造。现有recheck允许当前证明期限延长但不允许缩短或原证明过期，该行为保留；完整revision/正文/动态事实仍须同时重查。

ObjectFactsReader只在createTask专用口消费上述上下文；其他SupplementalFacts不得覆盖core已有check。同步接线：BODY_SCHEMAS/支持operation/目标验证/resolve_http、scope_catalog asset操作、SQL scope_operation/asset lookup白名单；已有资产是授权目标，purpose为analysis，不给尚未存在task做LOOKUP。guard在建立摘要前验证createTask无query、幂等头单值及严格body，不能先用dict压平重复值再授权。来源`analysis_purpose`必须加入core分支，当前None不能靠extra字典覆盖为True；classification独立真实来源缺失仍未知拒绝。

### 4.2 两个固定SQL接口

以下签名/返回列在I02落实为SQL及frozen Python类型，不使用通用query/任意表名/列名参数。SQL参数全部来自已冻结请求及已核对PlanBinding，不取客户端自由SQL。返回0行或多于1行均由包装器拒绝；不做“取第一条”。

```sql
mt.task_create_plan_metadata(
  wanted_asset uuid, wanted_case uuid, wanted_scene text,
  wanted_policy_version text, wanted_modules text[], wanted_priority text
) RETURNS TABLE(
  revision_id uuid, mapping_id text, mapping_version text,
  authority_version text, head_row_version bigint,
  policy_id uuid, policy_kind text, policy_version text, policy_sha256 text,
  plan_id text, plan_version text, plan_sha256 text,
  capability_id text, capability_version text, capability_sha256 text,
  valid_from timestamptz, valid_until timestamptz, recovery_generation text,
  validation_receipt jsonb, required_capability_refs jsonb,
  current_state_facts jsonb
)

mt.task_create_execution_plan(
  wanted_asset uuid, wanted_case uuid, wanted_scene text,
  wanted_policy_version text, wanted_modules text[], wanted_priority text,
  expected_revision uuid, expected_policy_sha256 text,
  expected_plan_sha256 text, expected_capability_sha256 text
) RETURNS TABLE(
  revision_id uuid, head_row_version bigint,
  policy_bytes bytea, plan_bytes bytea, capability_bytes bytea,
  validation_receipt_bytes bytea, current_state_facts jsonb,
  valid_until timestamptz, recovery_generation text
)
```

`validation_receipt`仅返回采用时已绑定摘要/校验器/格式版本及必要能力索引，不泄露完整正文；required_capability_refs/current_state_facts是严格结构的受限条目列表，不是可覆盖来源/分类权限的自由布尔字典。完整正文函数只允许CASE/createTask，并按完整请求适用元组+current revision+三摘要核对；不能仅凭plan_id/hash读取另一revision。

LOOKUP metadata包装器验证真实Principal、current_scope_transaction/current_data_scope为同一connection、read-only精确asset LOOKUP/createTask、lookup_id/actor/org/case与上下文一致；此时尚无ALLOW，不能调用拒绝LOOKUP的require_root。SQL独立核对transaction_read_only、app.lookup_kind/id、scope_operation、actor_in_org、成员关系以及参数asset确属本org/case；不取行锁、不返回正文。

CASE metadata/正文包装器先require_root，核对同根mutation授权evidence.target、actor/org/case/asset/createTask及A/B绑定，再调用SQL。SQL仍独立核验scope/成员/资产与适用元组，并按下节持锁。PostgreSQL不能直接读取ContextVar，现Database也没有asset/request-digest GUC；本计划不虚称SQL已验证Python请求摘要或CASE evidence精确目标。数据库独立强制目标GUC属于另行设计，不能顺便假设存在。

### 4.3 固定实际依赖、ACL与未知提供方

| 实际存在的关系/机制 | 读取用途及限制 |
| --- | --- |
| 五张拟私有材料/head表 | 唯一采用、精确正文/回执/三摘要、期限与恢复代际；runtime无直接SELECT |
| `media_asset, source_registry` | 已有资产/来源、VALID/用途/有效期/版本及对象输入；同case/org、受限列；CASE沿既有共享锁/复核 |
| `cases, case_membership, users, organizations`及现有actor/org/can_access_case函数 | 本单位真实主体及未撤销/未过期案件成员；按函数实际依赖给最小ACL/policy，不授全目录读取 |
| `policy_registry` | 精确policy_id/kind/version/状态/row_version与不可变正文绑定；登记状态不是批准采用 |
| `model_registry, model_release` | 仅正文明确引用的实际模型/发布条目及摘要/状态；不因ACTIVE、license_record_ref存在或环境字段非空推定许可/部署可用 |
| `authorization_epoch` | 复用既有hold/advance机制与外部GenerationReader核验；不把恢复后的库内值自证为有效 |

当前无可直接证明普通handler发布/许可/撤销的真实SQL关系。新增`CurrentCapabilityStateReader`显式同连接协议：按清单每项返回版本、摘要、发布/许可/可用事实、来源身份/版本和持锁/复核证据；未配置或任何未知均503，绝不默认可执行。SQL固定函数只返回其实际能证明的受限状态，不编造handler/许可表、不授对不存在关系的ACL。E03提供真实同库状态/受控更新通道后须核对具体表、锁、Schema和来源，再登记适配器；远端状态无可验证租约/同库可信同步时不支持严格原子撤销。此限制可能阻止真实正向202，但不妨碍拒绝口、纯解析和隔离基础实现。

### 4.4 锁序与撤销

固定顺序为**epoch共享锁 → 资产/来源共享锁 → policy/映射/head/能力动态状态按固定主键排序共享锁 → 幂等事务advisory锁 → 新task/run/plan/node/event写入**。管理通道先epoch写顺序再操作相关状态；不在已有业务共享epoch事务中盲加需要升级epoch的UPDATE触发器。相关可变授权字段使用FOR SHARE，不能用FOR KEY SHARE假装阻止非键更新。

LOOKUP阶段不持锁；CASE阶段动态状态锁一直保留到commit，before_commit在READ COMMITTED下再次核对Proof期限、PlanBinding、输入、正文和实际能力，之后由Database执行fence.finish。未知GenerationReader、锁等待/死锁/预算耗尽均回滚归一拒绝；不无限重试、不换key绕过未知结果。数据库锁不保证handler进程commit后存活，真实执行故障仍由后续调度/worker处理。

## 5. I03：原子集合、状态及回执

`TaskCreationService.create(scope,body,request,key)`只接受同根CASE/createTask mutation evidence和同一冻结上下文。内部用`connection.begin_nested()`保护整套写集合；根before_commit与fence仍由Database负责。调用者即使捕获业务异常并继续提交外层，也不能留下半写；before_commit中的任务绑定核验应与仍有效的服务状态对应，失败不得被吞掉。

| 顺序 | 必须执行的实际操作 |
| --- | --- |
| 1 | 严格body/头/query及A/B快照核对；require_root检查operation、主体、案件、资产目标、mutation和B；获取并核对当前CASE PlanBinding/精确正文，遵循上节锁序 |
| 2 | ControlReceipts.replay取得同主体/案件/createTask/key事务锁；control_ttl_seconds缺失仍CONTROL_RECEIPT_TTL_UNCONFIRMED/503；不借upload TTL默认冒充已确认控制回执TTL |
| 3 | 旧key：同A、未过期且内部回执完整，重新核对当前授权、task/run/run_plan、完整A/B与原revision；原revision须仍为当前有效head。head升级/撤销不能重绑、重建或凭不可变旧行继续采用；有效proof与原绑定冲突为既有409，guard先无法取得当前授权时保持503 |
| 4 | 新key：验证资产VALID、来源analysis授权/期限、分类、真实能力、完整输入和所有预算；任一未知不插任何任务，不制造FAILED壳任务代替拒绝 |
| 5 | 生成真实新task_id/task_run_id等UUID，先INSERT analysis_task(CREATED)，INSERT task_run(run=1)，INSERT task_run_plan；输入摘要分别按第3节，dag_version为实际plan_version；保存节点规范化输入清单，INSERT获准节点尝试，初始READY/PENDING依真实依赖，attempt=1且无开始/结束/租约，无提前成功 |
| 6 | 同事务条件更新CREATED→QUEUED并递增现有row_version；progress=0、report_eligibility=draft_only，missing_modalities仅来自已核验输入。analysis_task.result_version遵循现有正数结构；无结果不插task_result，事件result_version=null，不能填0 |
| 7 | 构造既有workflow.run.accepted.v1封套，producer_role=scheduler、state=QUEUED、同一event_id写task_event/outbox_event；run先写满足0015复合FK。outbox保存意图，不直接发MQ，不冒用上传outbox pump为任务消费者 |
| 8 | 写audit_event和idempotency_record；校验事件及Accepted响应结构，保存createTask专用内部receipt；注册before_commit完整重查，Database执行fence.finish及commit后才返回202 |

内部回执固定包含`schema_version`、原Accepted、原ETag、case/task/run、A/B、mapping revision、policy/plan/capability三元组及原受理版本快照；字段严格验证，不能把JSONB任意字典直接返回HTTP。对外仅Accepted `{task_id,state,status_url}`；status_url固定为`/api/v1/analysis/tasks/{task_id}/execution`。原ETag采用既有`controls.common.etag(accepted)`，内部另存原QUEUED投影版本；路由复用`reply("Accepted",accepted,202)`，重放验证原Accepted/原ETag相符，不按当前任务状态改写受理响应。后续任务状态改变且current head/当前授权仍有效时，原key返回原受理事实/原ETag，当前状态由status_url另查。

同key同body并发须用独立数据库连接/两个Database实例或明确多连接测试池形成真实竞争，现默认size=1池不能充当并发证据；只生成一个task和一个完整集合。不同key相同body不私自做业务去重。同key改变priority、modules顺序、policy或UUID字面形式按A冲突；actor/org/case改变不能取回另一主体回执。event_receipt用于消费去重，本请求不消费消息，不伪造该表记录。

故障注入点固定为：材料/输入读取，analysis_task、task_run、task_run_plan、每个task_node_run、状态更新、task_event、outbox_event、audit_event、idempotency_record、事件/响应Schema、时钟、before_commit、fence.finish及commit。每点失败都断言本key相关新集合为0、无MQ发送；注入点应通过测试adapter/连接替身或隔离数据库触发器控制，不引入客户端可操纵的生产故障开关。commit成功后响应丢失的重放测试与commit未成功的零半写测试分开。

## 6. I04：HTTP、错误及默认拒绝

新增router复用SourceRegistration路由模式，POST `/api/v1/analysis/tasks`、operationId=createTask、task.create及共享authorize_business_route保护。公共body仅case_id、asset_id、scene、policy_version、modules、priority；不接受org、actor、approved、plan或upload_id代task_id。不新增If-Match要求。Idempotency-Key单值1—128，额外/重复query或重复幂等头拒绝；X-Request-Id按既有UUID及追踪边界处理。

main.create_app显式注入PlanAuthority、TaskCreationFactsReader、CurrentCapabilityStateReader和Service；未提供保持None/不可用并拒绝，不构造FixtureAuthority或默认DAG。development入口也不能因是研发profile而提供假业务成功。已挂载路由投影和audit_protected_routes必须精确反映createTask新增，现有operation白名单只增此operation及asset定位，不扩大其他对象权限。

| 场景 | 保留的HTTP/错误 |
| --- | --- |
| 未认证/无有效身份 | 401及既有认证错误；功能权限拒绝403 |
| case/asset/source未知或不在范围 | 404隐藏，不泄露对象/单位存在性 |
| 资产存在但非VALID | ASSET_STATE_CONFLICT/409 |
| 同key异A、过期/损坏/原绑定失配回执 | IDEMPOTENCY_CONFLICT/409；不换key制造成功 |
| body/头/query非法 | INPUT_INVALID或原框架422；不增加公开TaskPlan错误 |
| 映射、正文、分类、能力或动态事实缺失 | CONDITIONAL_FACTS_UNAVAILABLE/503；明确来源/用途拒绝仍既有403 |
| 最终事实/Proof/代际变化 | AUTHORIZATION_CHANGED/503 |
| 数据库失败/回执TTL未配置 | DATABASE_UNAVAILABLE/503、CONTROL_RECEIPT_TTL_UNCONFIRMED/503 |

成功202只表示受理QUEUED，不证明任务消费者已配置、模型已运行、结果可审或正式证据有效。ETag/trace/request ID和no-store/no-cache/nosniff沿用现有响应框架；HTTP错误、日志、JUnit与公开回执不输出DSN、提供方地址、堆栈、令牌或跨案件对象。

## 7. 实际验证命令、失败探针与发布门槛

本节为**后续实施时执行的命令，不是本轮已运行结果**。全部在当前Linux/Miniforge py310/CPU的私有隔离源码目录执行；测试使用tests/business/conftest的新随机`mt_business_test_<uuid>`及独立loopback测试实例，禁止指向PoC、共享业务库或已有数据。数据库组串行，不并行跑整套DB回归；日志/JUnit留仓库外私有目录，只发布计数和安全选择器。

先用现有私密配置加载器`configured_environment()`和`validate_target()`验证隔离连接，不在命令行、对话或公开文档写入DSN；`PYTHONPATH=backend:.`仅设置模块路径。下列`python`均为既有`/opt/conda/glwy/envs/py310/bin/python`；计划测试文件实施后才存在。

```bash
# 只读预检；不输出DSN、账号或私密配置值。
PYTHONPATH=backend:. python -c 'from scripts.verify_business_foundation import configured_environment,validate_target; validate_target(configured_environment()); print("EXPLICIT_ISOLATED_TARGET_PREFLIGHT_OK")'

# I01：纯规范材料测试；新迁移必须覆盖template0空库及0001—0015历史快照升级。
PYTHONPATH=backend:. python -m pytest tests/business/test_task_creation_materials.py tests/business/test_task_creation_migration.py -q

# I02：请求/Proof旧内核保留；SQL与上下文测试使用已预检的新随机库，串行。
PYTHONPATH=backend:. python -m pytest tests/business/test_task_creation_binding.py tests/business/test_task_creation_authority.py tests/business/test_task_creation_scope_sql.py tests/business/test_task_creation_context.py -q

# I03：真实SQL事务、独立连接并发、隔离恢复/代际失效。
PYTHONPATH=backend:. python -m pytest tests/business/test_task_creation_transaction.py tests/business/test_task_creation_concurrency.py tests/business/test_task_creation_recovery.py -q

# I04：包括缺省应用拒绝、保护覆盖及原资产/任务读取兼容。
PYTHONPATH=backend:. python -m pytest tests/business/test_task_creation_http.py tests/business/test_t014_runtime.py tests/business/test_t014_indirect_reads.py tests/business/test_catalog_reads.py -q

# 各批适用静态/类型/资料检查；不setup、不安装到原py310，不更改锁。
python scripts/dev.py lint
python scripts/dev.py format-check
python scripts/stage_three_types.py check
python scripts/verify_generated_contracts.py
python scripts/validate_database_contracts.py
python scripts/validate_inputs.py --task T034

# I05：在受影响小批通过后执行一次适用整套；下列命令按顺序运行。
python scripts/verify_business_foundation.py run
python scripts/verify_t014_permissions.py run
python scripts/verify_business_foundation.py failure-probe
python scripts/verify_t014_permissions.py failure-probe
python scripts/stage_three_types.py failure-probe
python scripts/stage_three_quality.py secrets
python scripts/stage_three_quality.py dependencies
```

failure-probe成功定义须区分：业务探针为进程1且`expected_assertion_failure_verified=true`及1例受控断言失败；T014探针为进程1且其既有报告的受控拒绝/失败判定正确；类型探针为进程1且精确自建`controlled_error.py`的str赋int类型诊断被检出。类型入口不提供业务探针JSON标记，不能强行要求同一结构；普通执行失败、缺环境或任意非零都不能当探针通过。检查调用器分别记录真实exit code和对应安全诊断，普通验证须0；不得吞掉断言、增加skip或降低条件。

每步先保存有意义的新增拒绝/故障用例在旧实现下的RED（例如错误scope、缺上下文、错误摘要、跨单位FK/ACL、注入半写）并记录具体原因，再补实现取得GREEN；导入错误或测试文件不存在不是业务RED。已通过且不受新改动影响的检查不无故重复。新迁移测试须明确使用template0或从旧迁移目录建出的历史快照，不能只在已含0016的template克隆库上声称升级已验。

I01重点逐项验证：同org复合FK、材料bytea摘要、不可变/历史不回填、重复映射/同版本正文变更、无ACTIVE seed、RLS/FORCE与owner继承/PUBLIC权限。I02增加只读LOOKUP不能拿正文/锁、CASE目标/主体错配、不同A/B、classification未知、analysis_purpose核心、相同hash换revision、恶意临时schema遮蔽；并发双用户/案件、线程池、嵌套和异常finally清理。I03/I04按第5—6节完整故障/HTTP矩阵，外层catch后真实查库确认零半写。`validate_database_contracts.py`等既有基础契约检查只证明其实际覆盖资料，新0016的DDL、升级和行为必须由本批随机新库迁移/事务测试另证，不继承旧字段数量报告为新迁移通过。

恢复测试只在新建隔离备份/恢复库：old database OID、epoch、recovery_generation、旧connection/Proof/采用缓存失效；独立GenerationReader缺失持续拒绝；恢复不能自激活。真实签名、密钥交接、RPO/RTO或共享恢复维护时段仍属于T013等原待办，不把本测试替代其本人操作。

软件扫描失败保留失败。当前既有扫描匹配、软件准入和Python维护风险不因本计划解除；无升级授权不得采用修复包或改原锁。没有有效完整CI就不登记全部门禁通过；资料链接/Schema检查、测试数量和用户认可计划也不等于业务功能或整卡验收。

完成I05后按真实证据更新任务卡、分步/总导航、T001—T123开发清单/快计划；原170任务和剩余条件保留。生成漂移、链接、公开资料检查通过后推送既有开发分支，核对GitHub精确提交的CI、Linux源码提交/逐文件摘要和保留IDE文件；源码同步不触发共享服务重启、迁移、main合并或正式发布。

## 8. 仍需提供的实际输入与本次审阅项

| 项目 | 具体所需；未知时的行为 |
| --- | --- |
| E01 真实采用/撤销权威 | 负责人、批准依据、实际身份映射和受控导入/撤销/审计渠道；徐昌胜开发/指定复核不自动获得业务采用权。未知则不授管理执行权、不激活head |
| E02 映射与三份材料 | 精确org/case、scene、有序modules、priority、policy身份/kind/version/hash、plan正文/版本/摘要、能力清单及真实发布/许可；未知不代填ID、ACTIVE或通配映射 |
| E03 分类/来源/恢复/能力/派发 | 各事实的实际适配器与当前版本/撤销协议；普通handler动态状态关系尚未落实；未知逐项拒绝，不能以无模型声明省略handler或分类授权 |
| E04 预算/期限 | control_ttl_seconds、Proof/采用期限、最大字节/节点/能力、数据库/运行资源上限及合法边界；尚未确认不填生产默认数值，测试值仅为显式自建夹具 |
| 计划执行决定 | 是否按I01→I02→I03→I04→I05由当前会话逐批实施；本文件本身不代表认可执行。认可后仍按每批实际依赖/授权范围推进，不把缺失E01—E04当已经提供 |

本轮不需要密码、Token、私钥或真实案件数据，不要求管理员执行安装/数据库命令。计划认可后可以先实施隔离基础和拒绝验证；真实有效202、共享映射采用与完整T034验收须等实际输入齐备再分别验证。
