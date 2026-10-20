# T015 数据范围调用与验证矩阵

P03代码候选`aa2070b0740884e9619370355aebe3b0532afdae`。当前P03完整适用回归91项0失败／错误／跳过，格式、静态及类型检查通过；见[P03实际报告](../00-project/validation/t015-data-scope-p03-report.json)。P02已有461项业务测试0失败/错误/跳过，但隔离启动路径导致CLI报告生成失败，修正后的实际完整入口仍待核验。

64表目录、真实DAO/HTTP和对象字节读取分别登记。目录分类不代表64表全部CRUD已测；42个已挂载操作及31个未挂载操作的原范围均保留。

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

列表保留既有items／next_cursor格式，不新增total字段。允许集合先于SQL分页、签名和实际计数；单个条目证明不能提升成集合头证明。缺权威事实或查询故障整体拒绝，明确403／404条目排除；合法空集合仍返回空页。

复核关联的错误任务／运行／结果已由0003触发器阻止，不把无法写入的状态伪称新增DAO缺口。导出后台继续使用精确工作身份、既有批准、窗口与字段投影，不制造审计事件用户身份。

源表分类、具体测试ID、31项未挂载列表、精确源码摘要及未验证项见[结构化矩阵](t015-data-scope-coverage.json)。对象字节统一约束、故障／恢复、新门禁和最终CI在对应步骤真实执行后更新。
