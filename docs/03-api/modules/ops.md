# OPS 系统运维接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-OPS-001 管理角色模型标签阈值规则 | devLogin, getCurrentUser, requestApproval, decideApproval, issueOperationToken, registerModel, listModels, getModelHealth, rolloutModel, recordEvaluation, listEvaluations, listAuditEvents, exportAudit, createPolicy, listPolicies | T011, T012, T013, T014, T016, T017, T018, T051, T052, T058, T060, T061 |
| FR-OPS-002 监控任务GPU队列存储及索引 | listTasks, getTask, cancelTask, rerunTask, getModelHealth | T035, T040, T055, T056, T059, T117, T118, T119, T120 |
| FR-OPS-003 灰度回滚及备份恢复 | listModels, getModelHealth, rolloutModel | T057, T060, T121, T122, T123, T124, T170 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [devLogin](../operations/devLogin.md) | POST /api/v1/auth/login | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getCurrentUser](../operations/getCurrentUser.md) | GET /api/v1/auth/me | DEV_PARTIAL |
| [listTasks](../operations/listTasks.md) | GET /api/v1/analysis/tasks | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getTask](../operations/getTask.md) | GET /api/v1/analysis/tasks/{id} | DEV_PARTIAL |
| [cancelTask](../operations/cancelTask.md) | POST /api/v1/analysis/tasks/{id}/cancel | DEV_PARTIAL |
| [rerunTask](../operations/rerunTask.md) | POST /api/v1/analysis/tasks/{id}/rerun | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [requestApproval](../operations/requestApproval.md) | POST /api/v1/approvals | DEV_PARTIAL |
| [decideApproval](../operations/decideApproval.md) | POST /api/v1/approvals/{id}/decisions | DEV_PARTIAL |
| [issueOperationToken](../operations/issueOperationToken.md) | POST /api/v1/operation-tokens | DEV_PARTIAL |
| [registerModel](../operations/registerModel.md) | POST /api/v1/models | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [listModels](../operations/listModels.md) | GET /api/v1/models | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getModelHealth](../operations/getModelHealth.md) | GET /api/v1/models/{id}/health | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [rolloutModel](../operations/rolloutModel.md) | POST /api/v1/models/{id}/rollouts | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [recordEvaluation](../operations/recordEvaluation.md) | POST /api/v1/model-evaluations | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [listEvaluations](../operations/listEvaluations.md) | GET /api/v1/model-evaluations | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [listAuditEvents](../operations/listAuditEvents.md) | GET /api/v1/audit/events | DEV_PARTIAL |
| [exportAudit](../operations/exportAudit.md) | POST /api/v1/audit/exports | DEV_PARTIAL |
| [createPolicy](../operations/createPolicy.md) | POST /api/v1/policies | DEV_PARTIAL |
| [listPolicies](../operations/listPolicies.md) | GET /api/v1/policies | DEV_PARTIAL |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
