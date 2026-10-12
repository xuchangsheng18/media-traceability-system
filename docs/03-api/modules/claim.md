# CLAIM 证据核查接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-CLAIM-001 抽取结构化主张 | extractClaims | T098, T166, T167 |
| FR-CLAIM-002 检索白名单证据并判断关系 | verifyClaim | T099, T168 |
| FR-CLAIM-003 生成带证据引用摘要 | createReportDraft | T106, T169 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [extractClaims](../operations/extractClaims.md) | POST /api/v1/claims/extract | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [verifyClaim](../operations/verifyClaim.md) | POST /api/v1/claims/{id}/verify | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [createReportDraft](../operations/createReportDraft.md) | POST /api/v1/reports/drafts | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
