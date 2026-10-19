# T014 接口权限、单位与案件范围矩阵

2026-10-19；负责人：徐昌胜。本批为开发准备，尚未实现统一`require_permission(permission_code)`，不产生正式ALLOW。

外部操作及权限码唯一来源：[OpenAPI](../03-api/openapi.yaml)；角色职责来源：[T011候选模型](access-control-model.json)。[机器附表](t014-interface-scope-matrix.json)保留来源SHA-256、逐操作路由位置、检查表达式和响应码；[依赖核对](../03-development/t014-dependency-and-scope-review.md)、[测试设计](../09-testing/t014-authorization-test-design.md)配套阅读。

## 精确范围和判定

共73个契约操作、41个权限码、6类角色、246个角色/权限评审格。其中72个操作要求Bearer，`devLogin`是契约明确的开发登录例外。业务应用挂载42个对应操作；另31个未在该应用挂载，其中`health`在独立PoC有同路径令牌门禁。存在路由不等于完整授权通过，未挂载返回404也不算通过权限测试。

本表的“案件范围候选”沿用既有`case_review_permissions`；其他范围是按操作语义整理的实施审查项，不是已批准的公共契约扩展。单位权限不可通过虚构案件成员替代，管理员没有跨单位/跨案件通配许可。客户端提交的org_id、case_id、角色、来源、游标和对象ID都是待核验输入。请求必须同时通过功能权限、主体单位、适用案件成员、对象归属、来源/用途及已确认规则；任何缺项都不形成正式允许。

## 六角色与全部权限码

“责”=SOURCE_RESPONSIBILITY，“限”=SOURCE_RESTRICTION，“待”=PENDING_CONFIRMATION。三者均不是正式ALLOW；正式值继续待审。每格逐字复用T011机器模型，不据名称推断授权。

| 权限码 | 系统管理员 | 数据管理员 | 算法管理员 | 业务审核员 | 案件核查人员 | 审计员 |
| --- | --- | --- | --- | --- | --- | --- |
| `approval.decide` | 待 | 待 | 待 | 待 | 待 | 待 |
| `approval.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `approval.request` | 待 | 待 | 待 | 待 | 待 | 待 |
| `approval.revoke` | 待 | 待 | 待 | 待 | 待 | 待 |
| `asset.download` | 待 | 待 | 待 | 待 | 待 | 待 |
| `asset.import` | 待 | 待 | 待 | 待 | 待 | 待 |
| `asset.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `asset.search` | 待 | 待 | 待 | 待 | 待 | 待 |
| `asset.upload` | 待 | 待 | 待 | 待 | 待 | 待 |
| `audit.export` | 待 | 待 | 待 | 待 | 待 | 待 |
| `audit.read` | 待 | 待 | 待 | 待 | 待 | 责 |
| `claim.analyze` | 待 | 待 | 待 | 待 | 待 | 待 |
| `development.login` | 待 | 待 | 待 | 待 | 待 | 待 |
| `evidence.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `evidence.seal` | 待 | 待 | 待 | 待 | 待 | 限 |
| `feedback.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `feedback.request` | 待 | 待 | 待 | 待 | 待 | 待 |
| `health.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `identity.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `index.manage` | 待 | 待 | 待 | 待 | 待 | 待 |
| `model.evaluate` | 待 | 待 | 责 | 待 | 待 | 待 |
| `model.manage` | 待 | 待 | 责 | 待 | 待 | 限 |
| `model.read` | 待 | 待 | 责 | 待 | 待 | 待 |
| `model.release` | 待 | 待 | 责 | 待 | 待 | 待 |
| `operation.confirm` | 待 | 待 | 待 | 待 | 待 | 待 |
| `origin.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `policy.manage` | 待 | 待 | 待 | 待 | 待 | 限 |
| `policy.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `propagation.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `report.draft` | 待 | 待 | 待 | 待 | 待 | 待 |
| `report.export` | 待 | 待 | 待 | 待 | 待 | 待 |
| `report.generate` | 待 | 待 | 待 | 待 | 责 | 待 |
| `report.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `review.perform` | 待 | 待 | 待 | 责 | 待 | 限 |
| `review.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `source.manage` | 待 | 责 | 待 | 待 | 待 | 待 |
| `source.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `task.cancel` | 待 | 待 | 待 | 待 | 待 | 待 |
| `task.create` | 待 | 待 | 待 | 待 | 责 | 限 |
| `task.read` | 待 | 待 | 待 | 待 | 待 | 待 |
| `task.rerun` | 待 | 待 | 待 | 待 | 待 | 待 |

## 73项接口逐条清单

“检查入口”是源码观察，不是动态全路径证明；间接调用、复查次序及差异见机器附表。URL前缀统一`/api/v1`。

| 操作ID | 方法和路径 | 契约权限 | 候选范围 | 当前实现 | 检查入口/待补 |
| --- | --- | --- | --- | --- | --- |
| `cancelTask` | `POST /analysis/tasks/{id}/cancel` | `task.cancel` | 案件范围候选 | 已挂载；仅源码审查 | [cancel_task](../../backend/business_app/controls/router.py)：resource_scope(request, 'task', id, 'task.cancel') |
| `completeUpload` | `POST /uploads/{id}/complete` | `asset.upload` | 案件范围候选 | 已挂载；仅源码审查 | [complete_upload](../../backend/business_app/uploads/router.py)：UploadService.complete间接调用scope(asset.upload)；来源用途另验 |
| `createImport` | `POST /imports` | `asset.import` | 案件范围候选 | 已挂载；仅源码审查 | [create_import](../../backend/business_app/controls/router.py)：authorize_request(request, UUID(body['case_id']), 'asset.import') |
| `createPolicy` | `POST /policies` | `policy.manage` | 单位范围候选 | 已挂载；仅源码审查 | [create_policy](../../backend/business_app/controls/router.py)：policy_actor(request, 'policy.manage') |
| `createReport` | `POST /reports` | `report.generate` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createReportDraft` | `POST /reports/drafts` | `report.draft` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createReview` | `POST /reviews` | `review.perform` | 案件范围候选 | 已挂载；仅源码审查 | [create_review](../../backend/business_app/controls/router.py)：resource_scope(request, 'task', UUID(body['task_id']), 'review.perform') |
| `createSource` | `POST /sources` | `source.manage` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createTask` | `POST /analysis/tasks` | `task.create` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createUpload` | `POST /uploads` | `asset.upload` | 案件范围候选 | 已挂载；仅源码审查 | [create_upload](../../backend/business_app/uploads/router.py)：UploadService.create间接调用scope(asset.upload)；来源用途另验 |
| `decideApproval` | `POST /approvals/{id}/decisions` | `approval.decide` | 案件范围候选 | 已挂载；仅源码审查 | [decide_approval](../../backend/business_app/controls/router.py)：resource_scope(request, 'approval', id, 'approval.decide') |
| `decidePropagationEdge` | `POST /propagation/edges/{id}/decisions` | `review.perform` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `devLogin` | `POST /auth/login` | `development.login` | 开发登录例外 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `downloadAsset` | `GET /assets/{id}/content` | `asset.download` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `downloadAuditExport` | `GET /audit/exports/{id}/content` | `audit.export` | 案件范围候选 | 已挂载；仅源码审查 | [download_export](../../backend/business_app/controls/router.py)：resource_scope(request, 'export', id, 'audit.export') |
| `downloadReport` | `GET /reports/{id}/content` | `report.export` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `exportAudit` | `POST /audit/exports` | `audit.export` | 案件范围候选 | 已挂载；仅源码审查 | [export_audit](../../backend/business_app/controls/router.py)：authorize_request(request, UUID(body['case_id']), 'audit.export'); actor_for(request) |
| `extractClaims` | `POST /claims/extract` | `claim.analyze` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getApproval` | `GET /approvals/{id}` | `approval.read` | 案件范围候选 | 已挂载；仅源码审查 | [get_approval](../../backend/business_app/controls/router.py)：resource_scope(request, 'approval', id, 'approval.read') |
| `getAsset` | `GET /assets/{id}` | `asset.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getAuditExport` | `GET /audit/exports/{id}` | `audit.export` | 案件范围候选 | 已挂载；仅源码审查 | [get_export](../../backend/business_app/controls/router.py)：resource_scope(request, 'export', id, 'audit.export') |
| `getCurrentUser` | `GET /auth/me` | `identity.read` | 本人身份 | 已挂载；仅源码审查 | [current_user](../../backend/business_app/controls/router.py)：actor_for + IdentityDirectory绑定校验 + 单位RLS + 各案件case.read；未见identity.read统一入口 |
| `getFeedback` | `GET /feedback/samples/{id}` | `feedback.read` | 案件范围候选 | 已挂载；仅源码审查 | [get_feedback](../../backend/business_app/controls/router.py)：resource_scope(request, 'feedback', id, 'feedback.read') |
| `getFirstSource` | `GET /clusters/{id}/first-source` | `origin.read` | 案件范围候选 | 已挂载；仅源码审查 | [first_source](../../backend/business_app/history/router.py)：read_result(request, id, 'getFirstSource', 'cluster', 'origin.read') |
| `getForensics` | `GET /analysis/tasks/{id}/forensics` | `task.read` | 案件范围候选 | 已挂载；仅源码审查 | [forensics](../../backend/business_app/history/router.py)：read_result(request, id, 'getForensics', 'task', 'task.read') |
| `getImport` | `GET /imports/{id}` | `asset.import` | 案件范围候选 | 已挂载；仅源码审查 | [get_import](../../backend/business_app/controls/router.py)：resource_scope(request, 'import', id, 'asset.import') |
| `getIndex` | `GET /indices/{id}` | `index.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getModelHealth` | `GET /models/{id}/health` | `model.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getModelOperation` | `GET /model-operations/{id}` | `model.read` | 单位范围候选 | 已挂载；仅源码审查 | [model_operation](../../backend/business_app/controls/router.py)：policy_actor(request, 'model.read') |
| `getPolicy` | `GET /policies/{id}` | `policy.read` | 单位范围候选 | 已挂载；仅源码审查 | [get_policy](../../backend/business_app/controls/router.py)：policy_actor(request) |
| `getPolicyDefinition` | `GET /policies/{id}/definition` | `policy.read` | 单位范围候选 | 已挂载；仅源码审查 | [get_policy_definition](../../backend/business_app/controls/router.py)：policy_actor(request) |
| `getPropagation` | `GET /propagation/{cluster_id}` | `propagation.read` | 案件范围候选 | 已挂载；仅源码审查 | [propagation](../../backend/business_app/history/router.py)：read_result(request, cluster_id, 'getPropagation', 'cluster', 'propagation.read') |
| `getReport` | `GET /reports/{id}` | `report.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getReview` | `GET /reviews/{id}` | `review.read` | 案件范围候选 | 已挂载；仅源码审查 | [get_review](../../backend/business_app/controls/router.py)：resource_scope(request, 'review', id, 'review.read') |
| `getReviewContext` | `GET /analysis/tasks/{id}/review-context` | `review.read` | 案件范围候选 | 已挂载；仅源码审查 | [get_review_context](../../backend/business_app/controls/router.py)：resource_scope(request, 'task', id, 'review.read') |
| `getRiskFindings` | `GET /analysis/tasks/{id}/risk-findings` | `task.read` | 案件范围候选 | 已挂载；仅源码审查 | [risk](../../backend/business_app/history/router.py)：read_result(request, id, 'getRiskFindings', 'task', 'task.read') |
| `getSearchJob` | `GET /search/jobs/{id}` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getSource` | `GET /sources/{id}` | `source.read` | 案件范围候选 | 已挂载；仅源码审查 | [get_source](../../backend/business_app/controls/router.py)：resource_scope(request, 'source', id, 'source.read') |
| `getTask` | `GET /analysis/tasks/{id}` | `task.read` | 案件范围候选 | 已挂载；仅源码审查 | [task](../../backend/business_app/history/router.py)：read_result(request, id, 'getTask', 'task', 'task.read') |
| `getTaskEvidence` | `GET /analysis/tasks/{id}/evidence` | `evidence.read` | 案件范围候选 | 已挂载；仅源码审查 | [evidence](../../backend/business_app/history/router.py)：read_result(request, id, 'getTaskEvidence', 'task', 'evidence.read') |
| `getTaskExecution` | `GET /analysis/tasks/{id}/execution` | `task.read` | 案件范围候选 | 已挂载；仅源码审查 | [task_execution](../../backend/business_app/controls/router.py)：resource_scope(request, 'task', id, 'task.read') |
| `getTimeline` | `GET /assets/{id}/timeline` | `asset.read` | 案件范围候选 | 已挂载；仅源码审查 | [timeline](../../backend/business_app/history/router.py)：read_result(request, id, 'getTimeline', 'asset', 'asset.read') |
| `getUploadStatus` | `GET /uploads/{id}` | `asset.upload` | 案件范围候选 | 已挂载；仅源码审查 | [get_status](../../backend/business_app/uploads/router.py)：UploadService.status间接调用scope(asset.upload)；来源用途另验 |
| `health` | `GET /health` | `health.read` | 健康状态 | 仅独立PoC令牌入口 | 独立PoC有同路径令牌门禁，不代表health.read角色授权 |
| `issueOperationToken` | `POST /operation-tokens` | `operation.confirm` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listApprovals` | `GET /approvals` | `approval.read` | 案件范围候选 | 已挂载；仅源码审查 | [list_approvals](../../backend/business_app/controls/router.py)：authorize_request(request, case_id, 'approval.read') |
| `listAssets` | `GET /assets` | `asset.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listAuditEvents` | `GET /audit/events` | `audit.read` | 案件范围候选 | 已挂载；仅源码审查 | [list_audit](../../backend/business_app/controls/router.py)：authorize_request(request, case_id, 'audit.read') |
| `listEvaluations` | `GET /model-evaluations` | `model.read` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listModels` | `GET /models` | `model.read` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listPendingReviews` | `GET /reviews/pending` | `review.read` | 案件范围候选 | 已挂载；仅源码审查 | [pending_reviews](../../backend/business_app/controls/router.py)：authorize_request(request, case_id, 'review.read') |
| `listPolicies` | `GET /policies` | `policy.read` | 单位范围候选 | 已挂载；仅源码审查 | [list_policies](../../backend/business_app/controls/router.py)：policy_actor(request) |
| `listReviews` | `GET /reviews` | `review.read` | 案件范围候选 | 已挂载；仅源码审查 | [list_reviews](../../backend/business_app/controls/router.py)：authorize_request(request, case_id, 'review.read') |
| `listSources` | `GET /sources` | `source.read` | 案件范围候选 | 已挂载；仅源码审查 | [list_sources](../../backend/business_app/controls/router.py)：authorize_request(request, case_id, 'source.read') |
| `listTaskEvents` | `GET /analysis/tasks/{id}/events` | `task.read` | 案件范围候选 | 已挂载；仅源码审查 | [list_events](../../backend/business_app/controls/router.py)：resource_scope(request, 'task', id, 'task.read') |
| `listTaskNodes` | `GET /analysis/tasks/{id}/nodes` | `task.read` | 案件范围候选 | 已挂载；仅源码审查 | [list_nodes](../../backend/business_app/controls/router.py)：resource_scope(request, 'task', id, 'task.read') |
| `listTasks` | `GET /analysis/tasks` | `task.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listUploadParts` | `GET /uploads/{id}/parts` | `asset.upload` | 案件范围候选 | 已挂载；仅源码审查 | [list_parts](../../backend/business_app/uploads/router.py)：current.scope(request, 'asset.upload', upload_id=id) |
| `putUploadPart` | `PUT /uploads/{id}/parts/{part_no}` | `asset.upload` | 案件范围候选 | 已挂载；仅源码审查 | [put_upload_part](../../backend/business_app/uploads/router.py)：current.scope(request, 'asset.upload', upload_id=id) |
| `recordEvaluation` | `POST /model-evaluations` | `model.evaluate` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `registerModel` | `POST /models` | `model.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `requestApproval` | `POST /approvals` | `approval.request` | 案件范围候选 | 已挂载；仅源码审查 | [request_approval](../../backend/business_app/controls/router.py)：authorize_request(request, UUID(body['case_id']), 'approval.request'); actor_for(request) |
| `requestFeedback` | `POST /feedback/samples` | `feedback.request` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `rerunTask` | `POST /analysis/tasks/{id}/rerun` | `task.rerun` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `revokeApproval` | `POST /approvals/{id}/revoke` | `approval.revoke` | 案件范围候选 | 已挂载；仅源码审查 | [revoke_approval](../../backend/business_app/controls/router.py)：resource_scope(request, 'approval', id, 'approval.revoke') |
| `rolloutModel` | `POST /models/{id}/rollouts` | `model.release` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `sealEvidence` | `POST /evidence-packages/{case_id}/seal` | `evidence.seal` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchImage` | `POST /search/image` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchImageRegion` | `POST /search/image-region` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchVideo` | `POST /search/video` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `switchIndex` | `POST /indices/{id}/switch` | `index.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `syncSourceAuthorization` | `POST /sources/{id}/authorization/sync` | `source.manage` | 案件范围候选 | 已挂载；仅源码审查 | [sync_source](../../backend/business_app/controls/router.py)：resource_scope(request, 'source', id, 'source.manage') |
| `verifyClaim` | `POST /claims/{id}/verify` | `claim.analyze` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |

## 数据范围和必须关闭的差异

| 范围 | 复用能力 | T014实施与回归要求 |
| --- | --- | --- |
| 主体/单位 | T012外部issuer+subject精确映射，users/organizations启用；identity_transaction设置事务局部user/org | 不信任请求头/请求体单位；禁用或映射撤销后旧令牌重用拒绝；连接复用不能残留上一主体上下文。 |
| 功能权限 | T012角色/权限目录及绑定撤销字段；policy_actor已有部分目录权限检查 | permission_bindings目前是manager-only目录读取，不能直接当路由授权；建立最小权限查询边界和权威策略接入；未知权限码、漏标注和角色冲突默认拒绝。 |
| 案件/对象 | authorize_case、resource_scope/current_scope、mt.can_access_case及RLS | 获准动作也不能越过单位/案件；同单位不同案件、跨单位相同角色、对象替换、历史版本和下载均逐次核验。 |
| 来源/用途 | 上传和相关服务已有authorize_source接口 | 来源过期、撤销、用途改变及后台重试重新核验；授权失败不产生对象写入、任务/outbox或业务成功回执。 |
| 本人身份 | getCurrentUser验证目录绑定、单位和案件交集 | 契约要求identity.read，现有函数主要验证本人及case.read；需决定统一检查位置后实测，不能把case.read当成identity.read的别名。 |
| 单位策略/模型 | policy_actor检查明确权限、目录精确绑定与同单位记录 | 不授予跨单位权限，不使用零UUID Scope作为真实案件授权；保持单位型查询与案件型检查分开。 |
| 故障拒绝 | 缺身份适配器/正式策略时503；越界资源可隐藏为404 | 区分凭据无效401、明确无功能权限403、资源隐藏404、服务不可用503；不把故障改为成功或通用403。 |
| 撤销与缓存 | 目录有row_version、revoked_at、expires_at；令牌层有过期及失效检查 | 明确版本与缓存一致性后再验；不得编造撤销SLA。写入/出队/重试的检查点、并发撤销与TOCTOU仍需实现和测试。 |

当前没有通用require_permission实现；新路由漏鉴权的自动门禁和全部接口权限参数化回归也未完成。业务异常401返回头需要专项核验：HTTPException分支已有Bearer challenge，BusinessError分支未见同样设置。本批只登记缺口，不修改外部响应行为。

正式六角色逐权限允许值、职责冲突、数据分类、授权用途和策略版本仍待有效规则；候选标签不等同真实密级。上述待决项不阻止当前设计与隔离夹具开发，但不允许启用未确认的正式动作。
