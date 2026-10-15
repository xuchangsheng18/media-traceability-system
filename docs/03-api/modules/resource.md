# RESOURCE 资源库接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-RESOURCE-001 管理原始及派生媒体 | listAssets, getAsset, downloadAsset | T019, T020, T025, T030 |
| FR-RESOURCE-002 区分完全重复与近重复候选 | completeUpload, searchImage, getSearchJob | T027, T079, T082, T090 |
| FR-RESOURCE-003 按权限及生命周期检索资产 | getCurrentUser, createSource, listSources, listAssets, getAsset, downloadAsset | T015, T021, T025, T030 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [getCurrentUser](../operations/getCurrentUser.md) | GET /api/v1/auth/me | DEV_PARTIAL |
| [createSource](../operations/createSource.md) | POST /api/v1/sources | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [listSources](../operations/listSources.md) | GET /api/v1/sources | DEV_PARTIAL |
| [completeUpload](../operations/completeUpload.md) | POST /api/v1/uploads/{id}/complete | DEV_PARTIAL |
| [listAssets](../operations/listAssets.md) | GET /api/v1/assets | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getAsset](../operations/getAsset.md) | GET /api/v1/assets/{id} | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [downloadAsset](../operations/downloadAsset.md) | GET /api/v1/assets/{id}/content | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [searchImage](../operations/searchImage.md) | POST /api/v1/search/image | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [getSearchJob](../operations/getSearchJob.md) | GET /api/v1/search/jobs/{id} | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
