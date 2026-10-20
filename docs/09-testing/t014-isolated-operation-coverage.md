# T014逐操作隔离验证范围

当前完整隔离回归已通过，实际结果仍受下述范围限制。

以[机器清单](t014-isolated-operation-coverage.json)的实际JUnit行和源码为依据。73契约操作中42已挂载、31未挂载；246格是纯角色资格逻辑，不是246个HTTP允许场景。拒绝反例检查全部64张mt表和对象字节，机构/服务权威输入为显式合成测试适配器；不登记正式业务授权或整任务验收。

允许正例仅列确实使用候选权限链的getSource、downloadAuditExport、getImport、getReview、getFirstSource、getPropagation、listReviews、listPendingReviews。取消任务/审批读取的委托适配器证据单列，不冒充HTTP执行成功；上传后台/节点的实际SQL和制品测试见[工作回执](../00-project/validation/t014-isolated-work-report.json)。其他操作的旧业务夹具成功，不升级成候选六角色HTTP允许证明。

| 操作/方法 | 权限 | 已挂载 | 实际边界/剩余 |
| --- | --- | --- | --- |
| `cancelTask` POST | `task.cancel` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `completeUpload` POST | `asset.upload` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `createImport` POST | `asset.import` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `createPolicy` POST | `policy.manage` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `createReport` POST | `report.generate` | 否 | 未实现，无HTTP结论 |
| `createReportDraft` POST | `report.draft` | 否 | 未实现，无HTTP结论 |
| `createReview` POST | `review.perform` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `createSource` POST | `source.manage` | 否 | 未实现，无HTTP结论 |
| `createTask` POST | `task.create` | 否 | 未实现，无HTTP结论 |
| `createUpload` POST | `asset.upload` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `decideApproval` POST | `approval.decide` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `decidePropagationEdge` POST | `review.perform` | 否 | 未实现，无HTTP结论 |
| `devLogin` POST | `development.login` | 否 | 未实现，无HTTP结论 |
| `downloadAsset` GET | `asset.download` | 否 | 未实现，无HTTP结论 |
| `downloadAuditExport` GET | `audit.export` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `downloadReport` GET | `report.export` | 否 | 未实现，无HTTP结论 |
| `exportAudit` POST | `audit.export` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `extractClaims` POST | `claim.analyze` | 否 | 未实现，无HTTP结论 |
| `getApproval` GET | `approval.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getAsset` GET | `asset.read` | 否 | 未实现，无HTTP结论 |
| `getAuditExport` GET | `audit.export` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getCurrentUser` GET | `identity.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getFeedback` GET | `feedback.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getFirstSource` GET | `origin.read` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `getForensics` GET | `task.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getImport` GET | `asset.import` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `getIndex` GET | `index.manage` | 否 | 未实现，无HTTP结论 |
| `getModelHealth` GET | `model.manage` | 否 | 未实现，无HTTP结论 |
| `getModelOperation` GET | `model.read` | 是 | 缺组织级适配，候选链503 |
| `getPolicy` GET | `policy.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getPolicyDefinition` GET | `policy.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getPropagation` GET | `propagation.read` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `getReport` GET | `report.read` | 否 | 未实现，无HTTP结论 |
| `getReview` GET | `review.read` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `getReviewContext` GET | `review.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getRiskFindings` GET | `task.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getSearchJob` GET | `asset.search` | 否 | 未实现，无HTTP结论 |
| `getSource` GET | `source.read` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `getTask` GET | `task.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getTaskEvidence` GET | `evidence.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getTaskExecution` GET | `task.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getTimeline` GET | `asset.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `getUploadStatus` GET | `asset.upload` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `health` GET | `health.read` | 否 | 未实现，无HTTP结论 |
| `issueOperationToken` POST | `operation.confirm` | 否 | 未实现，无HTTP结论 |
| `listApprovals` GET | `approval.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `listAssets` GET | `asset.read` | 否 | 未实现，无HTTP结论 |
| `listAuditEvents` GET | `audit.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `listEvaluations` GET | `model.read` | 否 | 未实现，无HTTP结论 |
| `listModels` GET | `model.read` | 否 | 未实现，无HTTP结论 |
| `listPendingReviews` GET | `review.read` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `listPolicies` GET | `policy.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `listReviews` GET | `review.read` | 是 | 合成权威允许/撤销及拒绝实测；正式验收另列 |
| `listSources` GET | `source.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `listTaskEvents` GET | `task.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `listTaskNodes` GET | `task.read` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `listTasks` GET | `task.read` | 否 | 未实现，无HTTP结论 |
| `listUploadParts` GET | `asset.upload` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `putUploadPart` PUT | `asset.upload` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `recordEvaluation` POST | `model.evaluate` | 否 | 未实现，无HTTP结论 |
| `registerModel` POST | `model.manage` | 否 | 未实现，无HTTP结论 |
| `requestApproval` POST | `approval.request` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `requestFeedback` POST | `feedback.request` | 否 | 未实现，无HTTP结论 |
| `rerunTask` POST | `task.rerun` | 否 | 未实现，无HTTP结论 |
| `revokeApproval` POST | `approval.revoke` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `rolloutModel` POST | `model.release` | 否 | 未实现，无HTTP结论 |
| `sealEvidence` POST | `evidence.seal` | 否 | 未实现，无HTTP结论 |
| `searchImage` POST | `asset.search` | 否 | 未实现，无HTTP结论 |
| `searchImageRegion` POST | `asset.search` | 否 | 未实现，无HTTP结论 |
| `searchVideo` POST | `asset.search` | 否 | 未实现，无HTTP结论 |
| `switchIndex` POST | `index.manage` | 否 | 未实现，无HTTP结论 |
| `syncSourceAuthorization` POST | `source.manage` | 是 | 拒绝/资源完整性实测；完整允许场景未登记 |
| `verifyClaim` POST | `claim.analyze` | 否 | 未实现，无HTTP结论 |

逐角色条件、全部实际测试ID及路径见同名JSON；条件文本见[规则提案](../08-security/t014-six-role-rule-proposal.md)。机构分类、用途、人员、委托、组织模型适配、共享采用及未实现接口按对应任务补齐，不使用一个汇总PASS替代这些事项。
