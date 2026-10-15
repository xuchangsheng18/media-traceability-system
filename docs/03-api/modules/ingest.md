# INGEST 数据接入接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-INGEST-001 登记来源与授权用途 | createSource, listSources, createImport, getImport | T021, T028, T029 |
| FR-INGEST-002 分片上传及断点续传 | createUpload, putUploadPart, completeUpload | T022, T023, T024 |
| FR-INGEST-003 合并哈希和格式安全校验 | completeUpload, downloadAsset | T024, T025, T026, T027 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [createSource](../operations/createSource.md) | POST /api/v1/sources | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [listSources](../operations/listSources.md) | GET /api/v1/sources | DEV_PARTIAL |
| [createUpload](../operations/createUpload.md) | POST /api/v1/uploads | DEV_PARTIAL |
| [putUploadPart](../operations/putUploadPart.md) | PUT /api/v1/uploads/{id}/parts/{part_no} | DEV_PARTIAL |
| [completeUpload](../operations/completeUpload.md) | POST /api/v1/uploads/{id}/complete | DEV_PARTIAL |
| [downloadAsset](../operations/downloadAsset.md) | GET /api/v1/assets/{id}/content | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |
| [createImport](../operations/createImport.md) | POST /api/v1/imports | DEV_PARTIAL |
| [getImport](../operations/getImport.md) | GET /api/v1/imports/{id} | DEV_PARTIAL |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
