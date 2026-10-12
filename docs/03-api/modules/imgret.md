# IMGRET 图片检索接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-IMGRET-001 整图局部及关键帧多路召回 | searchImage, searchImageRegion, getSearchJob, getIndex, switchIndex | T079, T080, T081, T082, T085, T154, T155 |
| FR-IMGRET-002 进行局部几何验证 | searchImage | T083, T084 |
| FR-IMGRET-003 区分相似候选与高可信同源 | searchImage, searchImageRegion, getSearchJob, getIndex, switchIndex | T082, T084, T085, T156, T157 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [searchImage](../operations/searchImage.md) | POST /api/v1/search/image | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [searchImageRegion](../operations/searchImageRegion.md) | POST /api/v1/search/image-region | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getSearchJob](../operations/getSearchJob.md) | GET /api/v1/search/jobs/{id} | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getIndex](../operations/getIndex.md) | GET /api/v1/indices/{id} | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [switchIndex](../operations/switchIndex.md) | POST /api/v1/indices/{id}/switch | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
