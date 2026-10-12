# PROPAGATION 传播分析接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-PROPAGATION-001 管理显式及推断传播关系 | getPropagation, decidePropagationEdge | T094, T095, T096 |
| FR-PROPAGATION-002 展示时间线和版本差异 | getPropagation, decidePropagationEdge | T095, T097 |
| FR-PROPAGATION-003 人工确认或驳回推断边 | getPropagation, decidePropagationEdge, createReview, requestApproval, decideApproval, createPolicy | T096, T097, T102 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [getPropagation](../operations/getPropagation.md) | GET /api/v1/propagation/{cluster_id} | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [decidePropagationEdge](../operations/decidePropagationEdge.md) | POST /api/v1/propagation/edges/{id}/decisions | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [createReview](../operations/createReview.md) | POST /api/v1/reviews | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [requestApproval](../operations/requestApproval.md) | POST /api/v1/approvals | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [decideApproval](../operations/decideApproval.md) | POST /api/v1/approvals/{id}/decisions | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [createPolicy](../operations/createPolicy.md) | POST /api/v1/policies | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
