# T014逐操作隔离验证范围

2026-10-21目录读取续批：getAsset、listAssets、listTasks按[已确认范围的计划](../03-development/t001-t123-catalog-read-implementation-plan.md)补充；两个列表必填case_id已获用户确认。本文原43/30及更早42/31均为各自历史源码快照，不能据此覆盖新路由计数；当前源码、逐项方法及实际验证分别见[123项清单](../03-development/t001-t123-implementation-inventory.md)和[本批回执](../00-project/validation/t001-t123-catalog-read-report.json)。0012只作源码及隔离测试，不表示共享权限或现有演示实例已采用。

<!-- T016_NATIVE_FINAL_EVIDENCE -->

已核验的原生隔离源码为`b1b79bfb32b7959e63f302bbef22d32e22dc0b8f`：[T014实际报告](../00-project/validation/t014-permissions-report.json)713项、[T015实际报告](../00-project/validation/t015-data-scope-report.json)131项、[T016实际报告](../00-project/validation/t016-operation-token-report.json)187项，均无失败、错误或跳过；三个独立故障探针均按预期识别断言失败，Ruff、格式和mypy检查通过。三套用例有重叠，数量不相加为唯一测试数或170项任务完成数。此结论限Linux／py310／CPU隔离研发，不是正式验收。

托管CI另计：最后观察为run`39478665682`、提交`1b76a46ad52d9f67f549ee59da685ab79e6b9265`，身份检查332项通过，engineering仍在运行；不宣称最终源码的托管CI通过。后续状态与精确报告摘要以[阶段进度](../00-project/validation/t016-development-progress.json)及其最新actual记录为准，源码同步、数据库采用和正式授权分别登记。

2026-10-21增量：当前代码挂载43个契约操作、30个未挂载；T016签发已有完整六角色链的隔离HTTP正例。上方原生通过结论绑定明确源码，后续完整门禁及CI状态从[阶段进度](../00-project/validation/t016-development-progress.json)及其actual报告读取，不扩展成正式授权或整任务验收。原完整隔离回归结果继续作为下述旧源码快照的证据保留。

以[机器清单](t014-isolated-operation-coverage.json)的实际JUnit行和源码为依据：原快照为73契约操作中42已挂载、31未挂载，原1009项回归与旧nodeid不改写。JSON的`t016_increment`单列当前43／30及最新结论的权威入口；原`full_current_revision_verified`只描述其`verified_code_commit`，不表示当前HEAD已全量通过。246格是纯角色资格逻辑，不是246个HTTP允许场景。原拒绝反例检查全部64张mt表和对象字节，机构/服务权威输入为显式合成测试适配器；不登记正式业务授权或整任务验收。

原允许正例仅列确实使用候选权限链的getSource、downloadAuditExport、getImport、getReview、getFirstSource、getPropagation、listReviews、listPendingReviews。T016另增加issueOperationToken的真实SQL角色／对象事实、六角色条件和显式合成机构输入的HTTP正例，不能将其扩大为全部六角色均可签发。取消任务/审批读取的委托适配器证据单列，不冒充HTTP执行成功；上传后台/节点的实际SQL和制品测试见[工作回执](../00-project/validation/t014-isolated-work-report.json)。其他操作的旧业务夹具成功，不升级成候选六角色HTTP允许证明。下表既有行的“实测”仍指原提交，新增签发行单独列明当前范围。

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
| `issueOperationToken` POST | `operation.confirm` | 是 | T016完整六角色链隔离HTTP正例已有证据；最新43项拒绝与全量门禁结论按阶段进度指向的actual报告；不授予seal执行权限 |
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

## T016增量验证状态

[实际阶段进度](../00-project/validation/t016-development-progress.json)分别保留实现快照、业务测试、当时质量失败、后续修复及重跑结果。最新受测源码及门禁结论须沿其actual报告核对，不将任何旧快照永久称作当前版本。签发正例见[`test_http_issuance_uses_real_six_role_facts_and_current_source`](../../tests/business/test_t016_operation_tokens.py)；案件／任务／来源事实、双案件成员越界拒绝及提交前回滚见[事实测试](../../tests/business/test_t016_permission_facts.py)。这些适用证据不替代当前43项四类拒绝的严格门禁，也不代表全部真实高风险消费者已实现。

批准／来源／人员／结果及合成职责变化后的拒绝组合、T014全量、T015原S01—S09及新令牌关联门禁、T016全量、托管CI和三端同步，各自以最新actual报告的精确源码及结果为准。原失败及其修复／重跑记录不抹去；已有门禁不删减，旧1009项或旧42操作记录不改成当前全量通过。单资产任务来源的授权版本／状态／用途／期限／行版本纳入快照摘要，不宣称多输入闭包；合成职责撤销不代表正式跨人执行委托已采用。

`sealEvidence`仍无HTTP业务实现，内部精确动作根不授予权限。当前凭据严格绑定同一主体／动作／批准快照，实际截止可能不足5秒；确认人与封存执行角色尚需核定。见[安全边界](../08-security/t016-operation-token-boundaries.md)和[0011数据库扩展](../04-database/operation-token-extension.md)。共享库和现有预览库均未安装0011，Python候选继续暂缓。
