# VIDTRACE 视频溯源接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-VIDTRACE-001 按关键帧召回候选来源 | getIndex, switchIndex | T080, T081, T086, T158, T159 |
| FR-VIDTRACE-002 时序对齐定位来源区间 | 主追踪未直接绑定API，按整体流程/内部能力继续核验 | T087, T088, T160, T161, T163 |
| FR-VIDTRACE-003 多源拼接逐段映射 | searchVideo, getSearchJob | T089, T162 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [searchVideo](../operations/searchVideo.md) | POST /api/v1/search/video | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getSearchJob](../operations/getSearchJob.md) | GET /api/v1/search/jobs/{id} | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getIndex](../operations/getIndex.md) | GET /api/v1/indices/{id} | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [switchIndex](../operations/switchIndex.md) | POST /api/v1/indices/{id}/switch | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
