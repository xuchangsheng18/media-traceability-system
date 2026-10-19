# T014 接口权限、单位与案件范围矩阵

2026-10-20；负责人：徐昌胜。已实现统一`require_permission(permission_code)`和当前42业务操作的适用回归；正式策略未配置，不产生正式ALLOW。

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

当前42项均先经过统一权限入口，具体四类逐操作结果见[专项报告](../00-project/validation/t014-permissions-report.json)；表中函数保留案件/对象/来源检查，行号见机器附表。31项未挂载操作没有HTTP通过结论。URL前缀统一`/api/v1`。

| 操作ID | 方法和路径 | 契约权限 | 候选范围 | 当前实现 | 检查入口/待补 |
| --- | --- | --- | --- | --- | --- |
| `cancelTask` | `POST /analysis/tasks/{id}/cancel` | `task.cancel` | 案件范围候选 | 已挂载；研发权限边界已测 | [cancel_task](../../backend/business_app/controls/router.py#L625)：authorize_business_route → require_permission(task.cancel)；resource_scope(request, 'task', id, 'task.cancel') |
| `completeUpload` | `POST /uploads/{id}/complete` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [complete_upload](../../backend/business_app/uploads/router.py#L57)：authorize_business_route → require_permission(asset.upload)； |
| `createImport` | `POST /imports` | `asset.import` | 案件范围候选 | 已挂载；研发权限边界已测 | [create_import](../../backend/business_app/controls/router.py#L421)：authorize_business_route → require_permission(asset.import)；authorize_request(request, UUID(body['case_id']), 'asset.import') |
| `createPolicy` | `POST /policies` | `policy.manage` | 单位范围候选 | 已挂载；研发权限边界已测 | [create_policy](../../backend/business_app/controls/router.py#L465)：authorize_business_route → require_permission(policy.manage)；policy_actor(request, 'policy.manage') |
| `createReport` | `POST /reports` | `report.generate` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createReportDraft` | `POST /reports/drafts` | `report.draft` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createReview` | `POST /reviews` | `review.perform` | 案件范围候选 | 已挂载；研发权限边界已测 | [create_review](../../backend/business_app/controls/router.py#L193)：authorize_business_route → require_permission(review.perform)；resource_scope(request, 'task', UUID(body['task_id']), 'review.perform') |
| `createSource` | `POST /sources` | `source.manage` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createTask` | `POST /analysis/tasks` | `task.create` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createUpload` | `POST /uploads` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [create_upload](../../backend/business_app/uploads/router.py#L19)：authorize_business_route → require_permission(asset.upload)； |
| `decideApproval` | `POST /approvals/{id}/decisions` | `approval.decide` | 案件范围候选 | 已挂载；研发权限边界已测 | [decide_approval](../../backend/business_app/controls/router.py#L83)：authorize_business_route → require_permission(approval.decide)；resource_scope(request, 'approval', id, 'approval.decide') |
| `decidePropagationEdge` | `POST /propagation/edges/{id}/decisions` | `review.perform` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `devLogin` | `POST /auth/login` | `development.login` | 开发登录例外 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `downloadAsset` | `GET /assets/{id}/content` | `asset.download` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `downloadAuditExport` | `GET /audit/exports/{id}/content` | `audit.export` | 案件范围候选 | 已挂载；研发权限边界已测 | [download_export](../../backend/business_app/controls/router.py#L226)：authorize_business_route → require_permission(audit.export)；resource_scope(request, 'export', id, 'audit.export') |
| `downloadReport` | `GET /reports/{id}/content` | `report.export` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `exportAudit` | `POST /audit/exports` | `audit.export` | 案件范围候选 | 已挂载；研发权限边界已测 | [export_audit](../../backend/business_app/controls/router.py#L210)：authorize_business_route → require_permission(audit.export)；authorize_request(request, UUID(body['case_id']), 'audit.export'); actor_for(request) |
| `extractClaims` | `POST /claims/extract` | `claim.analyze` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getApproval` | `GET /approvals/{id}` | `approval.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_approval](../../backend/business_app/controls/router.py#L64)：authorize_business_route → require_permission(approval.read)；resource_scope(request, 'approval', id, 'approval.read') |
| `getAsset` | `GET /assets/{id}` | `asset.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getAuditExport` | `GET /audit/exports/{id}` | `audit.export` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_export](../../backend/business_app/controls/router.py#L220)：authorize_business_route → require_permission(audit.export)；resource_scope(request, 'export', id, 'audit.export') |
| `getCurrentUser` | `GET /auth/me` | `identity.read` | 本人身份 | 已挂载；研发权限边界已测 | [current_user](../../backend/business_app/controls/router.py#L270)：authorize_business_route → require_permission(identity.read)；actor_for(request); authorize_request(request, UUID(identifier), 'case.read') |
| `getFeedback` | `GET /feedback/samples/{id}` | `feedback.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_feedback](../../backend/business_app/controls/router.py#L232)：authorize_business_route → require_permission(feedback.read)；resource_scope(request, 'feedback', id, 'feedback.read') |
| `getFirstSource` | `GET /clusters/{id}/first-source` | `origin.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [first_source](../../backend/business_app/history/router.py#L116)：authorize_business_route → require_permission(origin.read)；read_result(request, id, 'getFirstSource', 'cluster', 'origin.read') |
| `getForensics` | `GET /analysis/tasks/{id}/forensics` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [forensics](../../backend/business_app/history/router.py#L101)：authorize_business_route → require_permission(task.read)；read_result(request, id, 'getForensics', 'task', 'task.read') |
| `getImport` | `GET /imports/{id}` | `asset.import` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_import](../../backend/business_app/controls/router.py#L378)：authorize_business_route → require_permission(asset.import)；resource_scope(request, 'import', id, 'asset.import') |
| `getIndex` | `GET /indices/{id}` | `index.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getModelHealth` | `GET /models/{id}/health` | `model.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getModelOperation` | `GET /model-operations/{id}` | `model.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [model_operation](../../backend/business_app/controls/router.py#L429)：authorize_business_route → require_permission(model.read)；policy_actor(request, 'model.read') |
| `getPolicy` | `GET /policies/{id}` | `policy.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [get_policy](../../backend/business_app/controls/router.py#L581)：authorize_business_route → require_permission(policy.read)；policy_actor(request) |
| `getPolicyDefinition` | `GET /policies/{id}/definition` | `policy.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [get_policy_definition](../../backend/business_app/controls/router.py#L589)：authorize_business_route → require_permission(policy.read)；policy_actor(request) |
| `getPropagation` | `GET /propagation/{cluster_id}` | `propagation.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [propagation](../../backend/business_app/history/router.py#L121)：authorize_business_route → require_permission(propagation.read)；read_result(request, cluster_id, 'getPropagation', 'cluster', 'propagation.read') |
| `getReport` | `GET /reports/{id}` | `report.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getReview` | `GET /reviews/{id}` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_review](../../backend/business_app/controls/router.py#L177)：authorize_business_route → require_permission(review.read)；resource_scope(request, 'review', id, 'review.read') |
| `getReviewContext` | `GET /analysis/tasks/{id}/review-context` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_review_context](../../backend/business_app/controls/router.py#L185)：authorize_business_route → require_permission(review.read)；resource_scope(request, 'task', id, 'review.read') |
| `getRiskFindings` | `GET /analysis/tasks/{id}/risk-findings` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [risk](../../backend/business_app/history/router.py#L96)：authorize_business_route → require_permission(task.read)；read_result(request, id, 'getRiskFindings', 'task', 'task.read') |
| `getSearchJob` | `GET /search/jobs/{id}` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getSource` | `GET /sources/{id}` | `source.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_source](../../backend/business_app/controls/router.py#L322)：authorize_business_route → require_permission(source.read)；resource_scope(request, 'source', id, 'source.read') |
| `getTask` | `GET /analysis/tasks/{id}` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [task](../../backend/business_app/history/router.py#L91)：authorize_business_route → require_permission(task.read)；read_result(request, id, 'getTask', 'task', 'task.read') |
| `getTaskEvidence` | `GET /analysis/tasks/{id}/evidence` | `evidence.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [evidence](../../backend/business_app/history/router.py#L106)：authorize_business_route → require_permission(evidence.read)；read_result(request, id, 'getTaskEvidence', 'task', 'evidence.read') |
| `getTaskExecution` | `GET /analysis/tasks/{id}/execution` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [task_execution](../../backend/business_app/controls/router.py#L616)：authorize_business_route → require_permission(task.read)；resource_scope(request, 'task', id, 'task.read') |
| `getTimeline` | `GET /assets/{id}/timeline` | `asset.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [timeline](../../backend/business_app/history/router.py#L111)：authorize_business_route → require_permission(asset.read)；read_result(request, id, 'getTimeline', 'asset', 'asset.read') |
| `getUploadStatus` | `GET /uploads/{id}` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_status](../../backend/business_app/uploads/router.py#L51)：authorize_business_route → require_permission(asset.upload)； |
| `health` | `GET /health` | `health.read` | 健康状态 | 仅独立PoC令牌入口 | 独立PoC有同路径令牌门禁，不代表health.read角色授权 |
| `issueOperationToken` | `POST /operation-tokens` | `operation.confirm` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listApprovals` | `GET /approvals` | `approval.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_approvals](../../backend/business_app/controls/router.py#L53)：authorize_business_route → require_permission(approval.read)；authorize_request(request, case_id, 'approval.read') |
| `listAssets` | `GET /assets` | `asset.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listAuditEvents` | `GET /audit/events` | `audit.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_audit](../../backend/business_app/controls/router.py#L200)：authorize_business_route → require_permission(audit.read)；authorize_request(request, case_id, 'audit.read') |
| `listEvaluations` | `GET /model-evaluations` | `model.read` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listModels` | `GET /models` | `model.read` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listPendingReviews` | `GET /reviews/pending` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [pending_reviews](../../backend/business_app/controls/router.py#L121)：authorize_business_route → require_permission(review.read)；authorize_request(request, case_id, 'review.read') |
| `listPolicies` | `GET /policies` | `policy.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [list_policies](../../backend/business_app/controls/router.py#L547)：authorize_business_route → require_permission(policy.read)；policy_actor(request) |
| `listReviews` | `GET /reviews` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_reviews](../../backend/business_app/controls/router.py#L99)：authorize_business_route → require_permission(review.read)；authorize_request(request, case_id, 'review.read') |
| `listSources` | `GET /sources` | `source.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_sources](../../backend/business_app/controls/router.py#L312)：authorize_business_route → require_permission(source.read)；authorize_request(request, case_id, 'source.read') |
| `listTaskEvents` | `GET /analysis/tasks/{id}/events` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_events](../../backend/business_app/controls/router.py#L677)：authorize_business_route → require_permission(task.read)；resource_scope(request, 'task', id, 'task.read') |
| `listTaskNodes` | `GET /analysis/tasks/{id}/nodes` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_nodes](../../backend/business_app/controls/router.py#L609)：authorize_business_route → require_permission(task.read)；resource_scope(request, 'task', id, 'task.read') |
| `listTasks` | `GET /analysis/tasks` | `task.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listUploadParts` | `GET /uploads/{id}/parts` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_parts](../../backend/business_app/uploads/router.py#L67)：authorize_business_route → require_permission(asset.upload)；current.scope(request, 'asset.upload', upload_id=id) |
| `putUploadPart` | `PUT /uploads/{id}/parts/{part_no}` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [put_upload_part](../../backend/business_app/uploads/router.py#L26)：authorize_business_route → require_permission(asset.upload)；current.scope(request, 'asset.upload', upload_id=id) |
| `recordEvaluation` | `POST /model-evaluations` | `model.evaluate` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `registerModel` | `POST /models` | `model.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `requestApproval` | `POST /approvals` | `approval.request` | 案件范围候选 | 已挂载；研发权限边界已测 | [request_approval](../../backend/business_app/controls/router.py#L72)：authorize_business_route → require_permission(approval.request)；authorize_request(request, UUID(body['case_id']), 'approval.request'); actor_for(request) |
| `requestFeedback` | `POST /feedback/samples` | `feedback.request` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `rerunTask` | `POST /analysis/tasks/{id}/rerun` | `task.rerun` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `revokeApproval` | `POST /approvals/{id}/revoke` | `approval.revoke` | 案件范围候选 | 已挂载；研发权限边界已测 | [revoke_approval](../../backend/business_app/controls/router.py#L91)：authorize_business_route → require_permission(approval.revoke)；resource_scope(request, 'approval', id, 'approval.revoke') |
| `rolloutModel` | `POST /models/{id}/rollouts` | `model.release` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `sealEvidence` | `POST /evidence-packages/{case_id}/seal` | `evidence.seal` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchImage` | `POST /search/image` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchImageRegion` | `POST /search/image-region` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchVideo` | `POST /search/video` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `switchIndex` | `POST /indices/{id}/switch` | `index.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `syncSourceAuthorization` | `POST /sources/{id}/authorization/sync` | `source.manage` | 案件范围候选 | 已挂载；研发权限边界已测 | [sync_source](../../backend/business_app/controls/router.py#L330)：authorize_business_route → require_permission(source.manage)；resource_scope(request, 'source', id, 'source.manage') |
| `verifyClaim` | `POST /claims/{id}/verify` | `claim.analyze` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |

## 数据范围和必须关闭的差异

| 范围 | 复用能力 | T014实施与回归要求 |
| --- | --- | --- |
| 主体/单位 | T012外部issuer+subject精确映射，users/organizations启用；identity_transaction设置事务局部user/org | 不信任请求头/请求体单位；禁用或映射撤销后旧令牌重用拒绝；连接复用不能残留上一主体上下文。 |
| 功能权限 | T012角色/权限目录及绑定撤销字段；policy_actor已有部分目录权限检查 | 0006专用mt_permission_lookup只执行固定search_path的只读事实函数；无直接表读写或管理权。DirectoryPermissionAuthority要求显式策略且绑定用户/单位/权限/事实摘要/版本；缺正式策略503。 |
| 案件/对象 | authorize_case、resource_scope/current_scope、mt.can_access_case及RLS | 获准动作也不能越过单位/案件；同单位不同案件、跨单位相同角色、对象替换、历史版本和下载均逐次核验。 |
| 来源/用途 | 上传和相关服务已有authorize_source接口 | 来源过期、撤销、用途改变及后台重试重新核验；授权失败不产生对象写入、任务/outbox或业务成功回执。 |
| 本人身份 | getCurrentUser验证目录绑定、单位和案件交集 | 统一入口已检查identity.read，原本人/单位绑定和case.read案件交集保留；两个权限不互为别名。 |
| 单位策略/模型 | policy_actor检查明确权限、目录精确绑定与同单位记录 | 不授予跨单位权限，不使用零UUID Scope作为真实案件授权；保持单位型查询与案件型检查分开。 |
| 故障拒绝 | 缺身份适配器/正式策略时503；越界资源可隐藏为404 | 区分凭据无效401、明确无功能权限403、资源隐藏404、服务不可用503；不把故障改为成功或通用403。 |
| 撤销与缓存 | 目录有row_version、revoked_at、expires_at；令牌层有过期及失效检查 | 无跨请求权限缓存；策略允许后再读精确事实和策略版本，真实SQL撤销/版本竞争已测。旧游标/成功回执前重新核验功能许可；既有出队/重试/来源重验保留。最后检查与动作之间零延时撤销及正式SLA仍未证明。 |

统一入口、严格路由覆盖审计及BusinessError的401 Bearer challenge已实现。当前42个真实业务操作均有401/403/缺策略503/权威故障503专项断言；新路由、重复/影子/挂载路由和依赖覆盖均有拒绝回归。全业务与T013令牌适用回归见[完整报告](../00-project/validation/t014-full-regression-report.json)。该结论不包含未挂载31项或六角色正式ALLOW。

正式六角色逐权限允许值、职责冲突、数据分类、授权用途和策略版本仍待有效规则；候选标签不等同真实密级。上述待决项不阻止当前设计与隔离夹具开发，但不允许启用未确认的正式动作。
