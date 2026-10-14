# 详细接口目录

共55个外部业务候选操作、85个组件、34类内部能力，模块覆盖不等于流程/实现完整。先读[整体说明](system-interface-specification.md)、[统一规则](common-interface-rules.md)和[缺口与拟补方案](interface-gap-register.md)。以下由唯一来源生成，禁止直接改字段定义。

| operationId | 方法/路径 | 主业务模块 | 详细文件 |
| --- | --- | --- | --- |
| health | GET /api/v1/health | 共享/工程入口，按来源任务核验 | [逐接口说明](operations/health.md) |
| devLogin | POST /api/v1/auth/login | OPS | [逐接口说明](operations/devLogin.md) |
| getCurrentUser | GET /api/v1/auth/me | OPS, RESOURCE | [逐接口说明](operations/getCurrentUser.md) |
| createSource | POST /api/v1/sources | INGEST, RESOURCE | [逐接口说明](operations/createSource.md) |
| listSources | GET /api/v1/sources | INGEST, RESOURCE | [逐接口说明](operations/listSources.md) |
| createUpload | POST /api/v1/uploads | INGEST | [逐接口说明](operations/createUpload.md) |
| putUploadPart | PUT /api/v1/uploads/{id}/parts/{part_no} | INGEST | [逐接口说明](operations/putUploadPart.md) |
| completeUpload | POST /api/v1/uploads/{id}/complete | INGEST, RESOURCE | [逐接口说明](operations/completeUpload.md) |
| listAssets | GET /api/v1/assets | RESOURCE | [逐接口说明](operations/listAssets.md) |
| getAsset | GET /api/v1/assets/{id} | RESOURCE | [逐接口说明](operations/getAsset.md) |
| downloadAsset | GET /api/v1/assets/{id}/content | INGEST, RESOURCE | [逐接口说明](operations/downloadAsset.md) |
| getTimeline | GET /api/v1/assets/{id}/timeline | MEDIA | [逐接口说明](operations/getTimeline.md) |
| createImport | POST /api/v1/imports | INGEST | [逐接口说明](operations/createImport.md) |
| getImport | GET /api/v1/imports/{id} | INGEST | [逐接口说明](operations/getImport.md) |
| createTask | POST /api/v1/analysis/tasks | 共享/工程入口，按来源任务核验 | [逐接口说明](operations/createTask.md) |
| listTasks | GET /api/v1/analysis/tasks | OPS | [逐接口说明](operations/listTasks.md) |
| getTask | GET /api/v1/analysis/tasks/{id} | OPS | [逐接口说明](operations/getTask.md) |
| cancelTask | POST /api/v1/analysis/tasks/{id}/cancel | OPS | [逐接口说明](operations/cancelTask.md) |
| rerunTask | POST /api/v1/analysis/tasks/{id}/rerun | OPS | [逐接口说明](operations/rerunTask.md) |
| getRiskFindings | GET /api/v1/analysis/tasks/{id}/risk-findings | RISK | [逐接口说明](operations/getRiskFindings.md) |
| getForensics | GET /api/v1/analysis/tasks/{id}/forensics | FORENSIC | [逐接口说明](operations/getForensics.md) |
| getTaskEvidence | GET /api/v1/analysis/tasks/{id}/evidence | REVIEW | [逐接口说明](operations/getTaskEvidence.md) |
| searchImage | POST /api/v1/search/image | IMGRET, RESOURCE | [逐接口说明](operations/searchImage.md) |
| searchImageRegion | POST /api/v1/search/image-region | IMGRET | [逐接口说明](operations/searchImageRegion.md) |
| searchVideo | POST /api/v1/search/video | VIDTRACE | [逐接口说明](operations/searchVideo.md) |
| getSearchJob | GET /api/v1/search/jobs/{id} | IMGRET, RESOURCE, VIDTRACE | [逐接口说明](operations/getSearchJob.md) |
| getFirstSource | GET /api/v1/clusters/{id}/first-source | ORIGIN | [逐接口说明](operations/getFirstSource.md) |
| getPropagation | GET /api/v1/propagation/{cluster_id} | PROPAGATION | [逐接口说明](operations/getPropagation.md) |
| decidePropagationEdge | POST /api/v1/propagation/edges/{id}/decisions | PROPAGATION, REVIEW | [逐接口说明](operations/decidePropagationEdge.md) |
| extractClaims | POST /api/v1/claims/extract | CLAIM | [逐接口说明](operations/extractClaims.md) |
| verifyClaim | POST /api/v1/claims/{id}/verify | CLAIM | [逐接口说明](operations/verifyClaim.md) |
| createReview | POST /api/v1/reviews | PROPAGATION, REVIEW | [逐接口说明](operations/createReview.md) |
| requestApproval | POST /api/v1/approvals | OPS, PROPAGATION, REVIEW | [逐接口说明](operations/requestApproval.md) |
| decideApproval | POST /api/v1/approvals/{id}/decisions | OPS, PROPAGATION, REVIEW | [逐接口说明](operations/decideApproval.md) |
| issueOperationToken | POST /api/v1/operation-tokens | OPS | [逐接口说明](operations/issueOperationToken.md) |
| sealEvidence | POST /api/v1/evidence-packages/{case_id}/seal | REVIEW | [逐接口说明](operations/sealEvidence.md) |
| createReportDraft | POST /api/v1/reports/drafts | CLAIM, REVIEW | [逐接口说明](operations/createReportDraft.md) |
| createReport | POST /api/v1/reports | REVIEW | [逐接口说明](operations/createReport.md) |
| getReport | GET /api/v1/reports/{id} | REVIEW | [逐接口说明](operations/getReport.md) |
| downloadReport | GET /api/v1/reports/{id}/content | REVIEW | [逐接口说明](operations/downloadReport.md) |
| requestFeedback | POST /api/v1/feedback/samples | REVIEW | [逐接口说明](operations/requestFeedback.md) |
| registerModel | POST /api/v1/models | OPS | [逐接口说明](operations/registerModel.md) |
| listModels | GET /api/v1/models | OPS | [逐接口说明](operations/listModels.md) |
| getModelHealth | GET /api/v1/models/{id}/health | OPS | [逐接口说明](operations/getModelHealth.md) |
| rolloutModel | POST /api/v1/models/{id}/rollouts | OPS | [逐接口说明](operations/rolloutModel.md) |
| recordEvaluation | POST /api/v1/model-evaluations | OPS | [逐接口说明](operations/recordEvaluation.md) |
| listEvaluations | GET /api/v1/model-evaluations | OPS | [逐接口说明](operations/listEvaluations.md) |
| listAuditEvents | GET /api/v1/audit/events | OPS | [逐接口说明](operations/listAuditEvents.md) |
| exportAudit | POST /api/v1/audit/exports | OPS | [逐接口说明](operations/exportAudit.md) |
| getIndex | GET /api/v1/indices/{id} | IMGRET, VIDTRACE | [逐接口说明](operations/getIndex.md) |
| switchIndex | POST /api/v1/indices/{id}/switch | IMGRET, VIDTRACE | [逐接口说明](operations/switchIndex.md) |
| createPolicy | POST /api/v1/policies | OPS, PROPAGATION, REVIEW, RISK | [逐接口说明](operations/createPolicy.md) |
| listPolicies | GET /api/v1/policies | OPS, RISK | [逐接口说明](operations/listPolicies.md) |
| getUploadStatus | GET /api/v1/uploads/{id} | 共享/工程入口，按来源任务核验 | [逐接口说明](operations/getUploadStatus.md) |
| listUploadParts | GET /api/v1/uploads/{id}/parts | 共享/工程入口，按来源任务核验 | [逐接口说明](operations/listUploadParts.md) |

## 模块目录

- [INGEST 数据接入](modules/ingest.md)
- [RESOURCE 资源库](modules/resource.md)
- [MEDIA 媒体预处理](modules/media.md)
- [RISK 风险识别](modules/risk.md)
- [FORENSIC 篡改取证](modules/forensic.md)
- [IMGRET 图片检索](modules/imgret.md)
- [VIDTRACE 视频溯源](modules/vidtrace.md)
- [ORIGIN 首发分析](modules/origin.md)
- [PROPAGATION 传播分析](modules/propagation.md)
- [CLAIM 证据核查](modules/claim.md)
- [REVIEW 人工审核与报告](modules/review.md)
- [OPS 系统运维](modules/ops.md)

[完整数据结构](data-structures.md)、[内部34类能力](inference-interfaces.md)、[机器覆盖索引](interface-catalog.json)、[实际PoC接口](poc-api.md)。
