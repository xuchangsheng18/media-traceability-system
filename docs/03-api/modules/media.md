# MEDIA 媒体预处理接口导航

自动派生，禁止独立修改结构；权威源 `docs/00-project/requirement-traceability.yaml`，SHA-256 `a3a9efd585510c8c0b296f230bf2e15b35b16fa3e6c4526e28151ac089da092b`。契约未冻结，文档存在不代表接口已实现。

整体设计入口见[系统接口说明](../system-interface-specification.md)。模块任务可能在DAG、模型服务或离线流水线中执行，没有独立HTTP入口不一定是遗漏；下表只列主追踪源已有的操作，不补造关联。

| 业务需求 | 已声明operationId | 任务 |
| --- | --- | --- |
| FR-MEDIA-001 解析媒体元数据并保留原件 | 主追踪未直接绑定API，按整体流程/内部能力继续核验 | T041, T042, T043 |
| FR-MEDIA-002 提取关键帧与音轨字幕 | 主追踪未直接绑定API，按整体流程/内部能力继续核验 | T044, T045, T046, T047 |
| FR-MEDIA-003 OCR和ASR对齐统一时间轴 | getTimeline | T048, T049, T050, T066 |

| 详细操作 | 路径 | 实现状态 |
| --- | --- | --- |
| [getTimeline](../operations/getTimeline.md) | GET /api/v1/assets/{id}/timeline | CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API |

模型能力、模块共享入口及异步事件见[内部调用](../inference-interfaces.md)和[服务/消息边界](../service-and-event-contracts.md)。结构覆盖不是完整业务流程覆盖或全部实施；本模块缺口与拟补方案见[缺口登记](../interface-gap-register.md)。
