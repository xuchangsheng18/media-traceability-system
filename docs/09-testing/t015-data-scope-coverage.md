# T015 数据范围调用与验证矩阵

<!-- T016_NATIVE_FINAL_EVIDENCE -->

已核验的原生隔离源码为`b1b79bfb32b7959e63f302bbef22d32e22dc0b8f`：[T014实际报告](../00-project/validation/t014-permissions-report.json)713项、[T015实际报告](../00-project/validation/t015-data-scope-report.json)131项、[T016实际报告](../00-project/validation/t016-operation-token-report.json)187项，均无失败、错误或跳过；三个独立故障探针均按预期识别断言失败，Ruff、格式和mypy检查通过。三套用例有重叠，数量不相加为唯一测试数或170项任务完成数。此结论限Linux／py310／CPU隔离研发，不是正式验收。

托管CI另计：最后观察为run`39478665682`、提交`1b76a46ad52d9f67f549ee59da685ab79e6b9265`，身份检查332项通过，engineering仍在运行；不宣称最终源码的托管CI通过。后续状态与精确报告摘要以[阶段进度](../00-project/validation/t016-development-progress.json)及其最新actual记录为准，源码同步、数据库采用和正式授权分别登记。

2026-10-21：T016增加案件签发和内部同事务消费，当前实际43个操作已挂载、30个未挂载。上方原生结果绑定明确源码；后续结论以[阶段进度](../00-project/validation/t016-development-progress.json)及其最新actual报告、受测提交与摘要为准，不把任何首批快照永久称为当前版本。原S01—S09全部保留。JSON的`t016_increment`记录该增量及结论入口；原P03及P02字段继续指其历史提交。

原P03代码候选`aa2070b0740884e9619370355aebe3b0532afdae`的适用回归91项0失败／错误／跳过，格式、静态及类型检查通过，见[P03实际报告](../00-project/validation/t015-data-scope-p03-report.json)。原P02的461项业务测试0失败/错误/跳过及当时CLI报告生成问题保留为历史事实，不能将旧结果当成本批当前源码的完整入口结果。

64表目录、真实DAO/HTTP和对象字节读取分别登记。目录分类不代表64表全部CRUD已测；下表原P03证据仍绑定其42／31快照，当前43／30及0011增量另列，不覆盖旧列数、nodeid或摘要。

| 调用范围 | 真实代码入口 | 固定约束 | 当前证据 |
| --- | --- | --- | --- |
| 上传会话、分片列表与续传元数据 | [session/parts/status](../../backend/business_app/uploads/repository.py) | CASE + exact upload; current source/owner rules retained | P03适用91项回归通过；P04_PENDING |
| 不可变历史任务、运行及结果 | [append_snapshot/load_exact/load_latest](../../backend/business_app/history/repository.py) | org/case/task/run/result and exact projection resource; existing source and SHA checks retained | P03适用91项回归通过；P04_PENDING |
| 审批候选与明细 | [bind/detail](../../backend/business_app/controls/approvals.py) | exact approval parent and task/run/result; existing independent-duty and version rules | P03适用91项回归通过；NOT_A_BYTE_ENTRY |
| 复核候选与证据关联 | [context/wire](../../backend/business_app/controls/reviews.py) | exact task/run/result; original 0003 validate_control_link rejects mismatched associations | P03适用91项回归通过；P04_PENDING |
| 六类列表统一允许集合 | [page](../../backend/business_app/controls/common.py) | minimum in-scope candidates -> original-operation per-item proof -> SQL filter -> cursor/page -> receipt recheck | P03适用91项回归通过；NOT_A_BYTE_ENTRY |
| 任务节点、事件与执行 | [status/nodes](../../backend/business_app/controls/execution.py) | exact parent task and fixed run; existing lease/epoch/cancellation checks retained | P03适用91项回归通过；NOT_A_BYTE_ENTRY |
| 来源元数据及用途 | [list_sources/get_source/sync_source](../../backend/business_app/controls/router.py) | case + original source.read; source purpose ARRAY remains metadata, not scalar action purpose | P03适用91项回归通过；NOT_A_BYTE_ENTRY |
| 单位策略元数据 | [list_policies](../../backend/business_app/controls/router.py) | ORGANIZATION + actual policy kind; legacy zero cursor placeholder never becomes a DB case | P03适用91项回归通过；NOT_A_BYTE_ENTRY |
| 审计事件元数据 | [list_audit](../../backend/business_app/controls/router.py) | CASE + original listAuditEvents delegation/metadata conditions per event; no details projection | P03适用91项回归通过；NOT_A_BYTE_ENTRY |
| 已登记对象导入元数据 | [create](../../backend/business_app/controls/imports.py) | existing exact case/source/object/version/SHA and composite FKs; common row parent checks | P03适用91项回归通过；P04_PENDING |
| 审计导出元数据与工作范围 | [process/check/status/download](../../backend/business_app/controls/exports.py) | exact export parent; existing approval, explicit time window/field projection, expiry and quota checks; no fabricated audit-event principal | P03适用91项回归通过；P04_PENDING |
| 受控内部推理输入元数据 | [check_inputs/infer](../../backend/business_app/inference.py) | existing trusted service + exact task work proof, current inputs and response binding; real model producer not implied | P03适用91项回归通过；P04_PENDING |
| T016案件签发与内部消费增量 | [issue/consume](../../backend/business_app/controls/operation_tokens.py)、[对象事实](../../backend/business_app/permissions/object_facts.py) | approval固定服务端案件；task/run/result/policy及当前单资产非空analysis来源快照；消费为精确动作／对象的同一Database和根Connection，保留提交前栅栏 | 完整六角色HTTP签发及事实测试已有证据；全量门禁、来源与合成职责等撤销组合的最新结论从阶段进度及actual报告核对 |

列表保留既有items／next_cursor格式，不新增total字段。允许集合先于SQL分页、签名和实际计数；单个条目证明不能提升成集合头证明。缺权威事实或查询故障整体拒绝，明确403／404条目排除；合法空集合仍返回空页。

复核关联的错误任务／运行／结果已由0003触发器阻止，不把无法写入的状态伪称新增DAO缺口。导出后台继续使用精确工作身份、既有批准、窗口与字段投影，不制造审计事件用户身份。

源表分类、原P03测试ID／31项未挂载列表／源码摘要，及当前T016的43／30范围分别见[结构化矩阵](t015-data-scope-coverage.json)。原`unmounted_operations`是历史快照；当前未挂载列表见`t016_increment.current_unmounted_operation_ids`，已移除issueOperationToken，仍保留sealEvidence。对象字节、故障／恢复、全部门禁和最终CI必须以当前提交的真实执行结果更新，不能仅凭本页目录证明通过。

新增0011后隔离结构为64表861列，原0010为849列；令牌表27列，legacy记录不可消费。共享库和现有预览库未安装0011。内部消费根登记不是封存消费者实现或业务授权，确认／执行主体规则与可能不足5秒的实际令牌截止见[安全边界](../08-security/t016-operation-token-boundaries.md)，逐字段及迁移采用条件见[数据库扩展](../04-database/operation-token-extension.md)。Python候选继续暂缓。

单资产来源快照沿`task.asset_id → media_asset.source_id`读取授权版本、状态、用途、到期时间和行版本并纳入摘要；公共请求／响应及数据库列未因此扩展。本页未宣称多输入来源闭包。职责撤销组合使用具名合成适配器，不登记正式跨人委托、共享采用或整卡验收。
