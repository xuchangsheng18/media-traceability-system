# T014 接口权限、单位与案件范围矩阵

<!-- T016_NATIVE_FINAL_EVIDENCE -->

已核验的原生隔离源码为`b1b79bfb32b7959e63f302bbef22d32e22dc0b8f`：[T014实际报告](../00-project/validation/t014-permissions-report.json)713项、[T015实际报告](../00-project/validation/t015-data-scope-report.json)131项、[T016实际报告](../00-project/validation/t016-operation-token-report.json)187项，均无失败、错误或跳过；三个独立故障探针均按预期识别断言失败，Ruff、格式和mypy检查通过。三套用例有重叠，数量不相加为唯一测试数或170项任务完成数。此结论限Linux／py310／CPU隔离研发，不是正式验收。

托管CI另计：最后观察为run`39478665682`、提交`1b76a46ad52d9f67f549ee59da685ab79e6b9265`，身份检查332项通过，engineering仍在运行；不宣称最终源码的托管CI通过。后续状态与精确报告摘要以[阶段进度](../00-project/validation/t016-development-progress.json)及其最新actual记录为准，源码同步、数据库采用和正式授权分别登记。

2026-10-21；开发负责人、指定复核人：徐昌胜。统一`require_permission(permission_code)`继续保留，T016已增加案件操作令牌签发，当前实际挂载43个业务操作。先前42项回归的证据仍绑定其原提交；本次原生结果仅适用于上方明确源码，后续门禁及CI结论须从[T016阶段进度](../00-project/validation/t016-development-progress.json)及其最新actual报告核对。正式策略未配置时不产生正式ALLOW。

外部操作及权限码唯一来源：[OpenAPI](../03-api/openapi.yaml)；角色职责来源：[T011候选模型](access-control-model.json)。[机器附表](t014-interface-scope-matrix.json)保留来源SHA-256、逐操作路由位置、检查表达式和响应码；[依赖核对](../03-development/t014-dependency-and-scope-review.md)、[测试设计](../09-testing/t014-authorization-test-design.md)配套阅读。

## 精确范围和判定

共73个契约操作、41个权限码、6类角色、246个角色/权限评审格。其中72个操作要求Bearer，`devLogin`是契约明确的开发登录例外。当前业务应用挂载43个对应操作；另30个未在该应用挂载，其中`health`在独立PoC有同路径令牌门禁。内部推理入口另计，不纳入这73项；`sealEvidence`的内部动作根登记也不增加HTTP挂载数。存在路由不等于完整授权通过，未挂载返回404也不算通过权限测试。

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

当前43项均先经过统一权限入口。既有42项“研发权限边界已测”引用[先前专项报告](../00-project/validation/t014-permissions-report.json)的原提交，不能替代本批全量重跑；新增签发的实际正例与待核验范围见下方T016增量。表中函数保留案件/对象/来源检查，行号见机器附表。30项未挂载操作没有HTTP通过结论。URL前缀统一`/api/v1`。

| 操作ID | 方法和路径 | 契约权限 | 候选范围 | 当前实现 | 检查入口/待补 |
| --- | --- | --- | --- | --- | --- |
| `cancelTask` | `POST /analysis/tasks/{id}/cancel` | `task.cancel` | 案件范围候选 | 已挂载；研发权限边界已测 | [cancel_task](../../backend/business_app/controls/router.py#L688)：authorize_business_route → require_permission(task.cancel)；resource_scope(request, 'task', id, 'task.cancel') |
| `completeUpload` | `POST /uploads/{id}/complete` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [complete_upload](../../backend/business_app/uploads/router.py#L57)：authorize_business_route → require_permission(asset.upload)； |
| `createImport` | `POST /imports` | `asset.import` | 案件范围候选 | 已挂载；研发权限边界已测 | [create_import](../../backend/business_app/controls/router.py#L480)：authorize_business_route → require_permission(asset.import)；authorize_request(request, UUID(body['case_id']), 'asset.import') |
| `createPolicy` | `POST /policies` | `policy.manage` | 单位范围候选 | 已挂载；研发权限边界已测 | [create_policy](../../backend/business_app/controls/router.py#L524)：authorize_business_route → require_permission(policy.manage)；policy_actor(request, 'policy.manage') |
| `createReport` | `POST /reports` | `report.generate` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createReportDraft` | `POST /reports/drafts` | `report.draft` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createReview` | `POST /reviews` | `review.perform` | 案件范围候选 | 已挂载；研发权限边界已测 | [create_review](../../backend/business_app/controls/router.py#L241)：authorize_business_route → require_permission(review.perform)；resource_scope(request, 'task', UUID(body['task_id']), 'review.perform') |
| `createSource` | `POST /sources` | `source.manage` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createTask` | `POST /analysis/tasks` | `task.create` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `createUpload` | `POST /uploads` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [create_upload](../../backend/business_app/uploads/router.py#L19)：authorize_business_route → require_permission(asset.upload)； |
| `decideApproval` | `POST /approvals/{id}/decisions` | `approval.decide` | 案件范围候选 | 已挂载；研发权限边界已测 | [decide_approval](../../backend/business_app/controls/router.py#L127)：authorize_business_route → require_permission(approval.decide)；resource_scope(request, 'approval', id, 'approval.decide') |
| `decidePropagationEdge` | `POST /propagation/edges/{id}/decisions` | `review.perform` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `devLogin` | `POST /auth/login` | `development.login` | 开发登录例外 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `downloadAsset` | `GET /assets/{id}/content` | `asset.download` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `downloadAuditExport` | `GET /audit/exports/{id}/content` | `audit.export` | 案件范围候选 | 已挂载；研发权限边界已测 | [download_export](../../backend/business_app/controls/router.py#L281)：authorize_business_route → require_permission(audit.export)；resource_scope(request, 'export', id, 'audit.export') |
| `downloadReport` | `GET /reports/{id}/content` | `report.export` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `exportAudit` | `POST /audit/exports` | `audit.export` | 案件范围候选 | 已挂载；研发权限边界已测 | [export_audit](../../backend/business_app/controls/router.py#L265)：authorize_business_route → require_permission(audit.export)；authorize_request(request, UUID(body['case_id']), 'audit.export'); actor_for(request) |
| `extractClaims` | `POST /claims/extract` | `claim.analyze` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getApproval` | `GET /approvals/{id}` | `approval.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_approval](../../backend/business_app/controls/router.py#L108)：authorize_business_route → require_permission(approval.read)；resource_scope(request, 'approval', id, 'approval.read') |
| `getAsset` | `GET /assets/{id}` | `asset.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getAuditExport` | `GET /audit/exports/{id}` | `audit.export` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_export](../../backend/business_app/controls/router.py#L275)：authorize_business_route → require_permission(audit.export)；resource_scope(request, 'export', id, 'audit.export') |
| `getCurrentUser` | `GET /auth/me` | `identity.read` | 本人身份 | 已挂载；研发权限边界已测 | [current_user](../../backend/business_app/controls/router.py#L325)：authorize_business_route → require_permission(identity.read)；actor_for(request); authorize_request(request, UUID(identifier), 'case.read') |
| `getFeedback` | `GET /feedback/samples/{id}` | `feedback.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_feedback](../../backend/business_app/controls/router.py#L287)：authorize_business_route → require_permission(feedback.read)；resource_scope(request, 'feedback', id, 'feedback.read') |
| `getFirstSource` | `GET /clusters/{id}/first-source` | `origin.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [first_source](../../backend/business_app/history/router.py#L116)：authorize_business_route → require_permission(origin.read)；read_result(request, id, 'getFirstSource', 'cluster', 'origin.read') |
| `getForensics` | `GET /analysis/tasks/{id}/forensics` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [forensics](../../backend/business_app/history/router.py#L101)：authorize_business_route → require_permission(task.read)；read_result(request, id, 'getForensics', 'task', 'task.read') |
| `getImport` | `GET /imports/{id}` | `asset.import` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_import](../../backend/business_app/controls/router.py#L437)：authorize_business_route → require_permission(asset.import)；resource_scope(request, 'import', id, 'asset.import') |
| `getIndex` | `GET /indices/{id}` | `index.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getModelHealth` | `GET /models/{id}/health` | `model.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getModelOperation` | `GET /model-operations/{id}` | `model.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [model_operation](../../backend/business_app/controls/router.py#L488)：authorize_business_route → require_permission(model.read)；policy_actor(request, 'model.read') |
| `getPolicy` | `GET /policies/{id}` | `policy.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [get_policy](../../backend/business_app/controls/router.py#L644)：authorize_business_route → require_permission(policy.read)；policy_actor(request) |
| `getPolicyDefinition` | `GET /policies/{id}/definition` | `policy.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [get_policy_definition](../../backend/business_app/controls/router.py#L652)：authorize_business_route → require_permission(policy.read)；policy_actor(request) |
| `getPropagation` | `GET /propagation/{cluster_id}` | `propagation.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [propagation](../../backend/business_app/history/router.py#L121)：authorize_business_route → require_permission(propagation.read)；read_result(request, cluster_id, 'getPropagation', 'cluster', 'propagation.read') |
| `getReport` | `GET /reports/{id}` | `report.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getReview` | `GET /reviews/{id}` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_review](../../backend/business_app/controls/router.py#L225)：authorize_business_route → require_permission(review.read)；resource_scope(request, 'review', id, 'review.read') |
| `getReviewContext` | `GET /analysis/tasks/{id}/review-context` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_review_context](../../backend/business_app/controls/router.py#L233)：authorize_business_route → require_permission(review.read)；resource_scope(request, 'task', id, 'review.read') |
| `getRiskFindings` | `GET /analysis/tasks/{id}/risk-findings` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [risk](../../backend/business_app/history/router.py#L96)：authorize_business_route → require_permission(task.read)；read_result(request, id, 'getRiskFindings', 'task', 'task.read') |
| `getSearchJob` | `GET /search/jobs/{id}` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `getSource` | `GET /sources/{id}` | `source.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_source](../../backend/business_app/controls/router.py#L381)：authorize_business_route → require_permission(source.read)；resource_scope(request, 'source', id, 'source.read') |
| `getTask` | `GET /analysis/tasks/{id}` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [task](../../backend/business_app/history/router.py#L91)：authorize_business_route → require_permission(task.read)；read_result(request, id, 'getTask', 'task', 'task.read') |
| `getTaskEvidence` | `GET /analysis/tasks/{id}/evidence` | `evidence.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [evidence](../../backend/business_app/history/router.py#L106)：authorize_business_route → require_permission(evidence.read)；read_result(request, id, 'getTaskEvidence', 'task', 'evidence.read') |
| `getTaskExecution` | `GET /analysis/tasks/{id}/execution` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [task_execution](../../backend/business_app/controls/router.py#L679)：authorize_business_route → require_permission(task.read)；resource_scope(request, 'task', id, 'task.read') |
| `getTimeline` | `GET /assets/{id}/timeline` | `asset.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [timeline](../../backend/business_app/history/router.py#L111)：authorize_business_route → require_permission(asset.read)；read_result(request, id, 'getTimeline', 'asset', 'asset.read') |
| `getUploadStatus` | `GET /uploads/{id}` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [get_status](../../backend/business_app/uploads/router.py#L51)：authorize_business_route → require_permission(asset.upload)； |
| `health` | `GET /health` | `health.read` | 健康状态 | 仅独立PoC令牌入口 | 独立PoC有同路径令牌门禁，不代表health.read角色授权 |
| `issueOperationToken` | `POST /operation-tokens` | `operation.confirm` | 案件范围；首批task／seal | 已挂载；完整六角色链隔离HTTP正例已有证据；最新全门禁结论按阶段进度和actual报告 | [issue_operation_token](../../backend/business_app/controls/router.py#L53)：统一权限 → approval_id服务端定位案件 → CONFIRM_CASE精确任务／来源事实 → 当前独立批准链 → 显式规则和独立密钥；签发不授予seal执行权限 |
| `listApprovals` | `GET /approvals` | `approval.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_approvals](../../backend/business_app/controls/router.py#L90)：authorize_business_route → require_permission(approval.read)；authorize_request(request, case_id, 'approval.read') |
| `listAssets` | `GET /assets` | `asset.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listAuditEvents` | `GET /audit/events` | `audit.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_audit](../../backend/business_app/controls/router.py#L248)：authorize_business_route → require_permission(audit.read)；authorize_request(request, case_id, 'audit.read') |
| `listEvaluations` | `GET /model-evaluations` | `model.read` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listModels` | `GET /models` | `model.read` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listPendingReviews` | `GET /reviews/pending` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [pending_reviews](../../backend/business_app/controls/router.py#L167)：authorize_business_route → require_permission(review.read)；authorize_request(request, case_id, 'review.read') |
| `listPolicies` | `GET /policies` | `policy.read` | 单位范围候选 | 已挂载；研发权限边界已测 | [list_policies](../../backend/business_app/controls/router.py#L606)：authorize_business_route → require_permission(policy.read)；policy_actor(request) |
| `listReviews` | `GET /reviews` | `review.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_reviews](../../backend/business_app/controls/router.py#L143)：authorize_business_route → require_permission(review.read)；authorize_request(request, case_id, 'review.read') |
| `listSources` | `GET /sources` | `source.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_sources](../../backend/business_app/controls/router.py#L364)：authorize_business_route → require_permission(source.read)；authorize_request(request, case_id, 'source.read') |
| `listTaskEvents` | `GET /analysis/tasks/{id}/events` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_events](../../backend/business_app/controls/router.py#L740)：authorize_business_route → require_permission(task.read)；resource_scope(request, 'task', id, 'task.read') |
| `listTaskNodes` | `GET /analysis/tasks/{id}/nodes` | `task.read` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_nodes](../../backend/business_app/controls/router.py#L672)：authorize_business_route → require_permission(task.read)；resource_scope(request, 'task', id, 'task.read') |
| `listTasks` | `GET /analysis/tasks` | `task.read` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `listUploadParts` | `GET /uploads/{id}/parts` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [list_parts](../../backend/business_app/uploads/router.py#L67)：authorize_business_route → require_permission(asset.upload)；current.scope(request, 'asset.upload', upload_id=id) |
| `putUploadPart` | `PUT /uploads/{id}/parts/{part_no}` | `asset.upload` | 案件范围候选 | 已挂载；研发权限边界已测 | [put_upload_part](../../backend/business_app/uploads/router.py#L26)：authorize_business_route → require_permission(asset.upload)；current.scope(request, 'asset.upload', upload_id=id) |
| `recordEvaluation` | `POST /model-evaluations` | `model.evaluate` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `registerModel` | `POST /models` | `model.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `requestApproval` | `POST /approvals` | `approval.request` | 案件范围候选 | 已挂载；研发权限边界已测 | [request_approval](../../backend/business_app/controls/router.py#L116)：authorize_business_route → require_permission(approval.request)；authorize_request(request, UUID(body['case_id']), 'approval.request'); actor_for(request) |
| `requestFeedback` | `POST /feedback/samples` | `feedback.request` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `rerunTask` | `POST /analysis/tasks/{id}/rerun` | `task.rerun` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `revokeApproval` | `POST /approvals/{id}/revoke` | `approval.revoke` | 案件范围候选 | 已挂载；研发权限边界已测 | [revoke_approval](../../backend/business_app/controls/router.py#L135)：authorize_business_route → require_permission(approval.revoke)；resource_scope(request, 'approval', id, 'approval.revoke') |
| `rolloutModel` | `POST /models/{id}/rollouts` | `model.release` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `sealEvidence` | `POST /evidence-packages/{case_id}/seal` | `evidence.seal` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchImage` | `POST /search/image` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchImageRegion` | `POST /search/image-region` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `searchVideo` | `POST /search/video` | `asset.search` | 案件范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `switchIndex` | `POST /indices/{id}/switch` | `index.manage` | 单位范围候选 | 业务应用未挂载 | 当前业务应用未挂载此契约操作；不得以404记权限测试通过 |
| `syncSourceAuthorization` | `POST /sources/{id}/authorization/sync` | `source.manage` | 案件范围候选 | 已挂载；研发权限边界已测 | [sync_source](../../backend/business_app/controls/router.py#L389)：authorize_business_route → require_permission(source.manage)；resource_scope(request, 'source', id, 'source.manage') |
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

统一入口、严格路由覆盖审计及BusinessError的401 Bearer challenge已实现。先前42个真实业务操作的401/403/缺策略503/权威故障503专项断言、新路由及依赖覆盖拒绝回归，仍以[原完整报告](../00-project/validation/t014-full-regression-report.json)的提交为边界；不能将其结果自动扩大为当前43项通过。新增签发及43项逐操作拒绝门禁的最新结果，以阶段进度指向的actual报告、受测提交及源码摘要为准；任何旧快照通过、已修复但未重跑或报告文件仅存在，都不是最新源码通过。该结论不包含未挂载30项或六角色正式ALLOW。

## T016当前增量与证据边界

[T016阶段进度证据](../00-project/validation/t016-development-progress.json)按快照分别保留业务测试、质量失败、修复及重跑结果；最终结论必须绑定它指向的最新干净源码与actual报告。本页不指定某个首批实现提交作为永久的最终版本，也不把旧单项通过提升为当前全门禁通过。`issueOperationToken`的HTTP正例已有真实SQL角色／对象事实及六角色条件引擎的证据，测试位置为[`test_http_issuance_uses_real_six_role_facts_and_current_source`](../../tests/business/test_t016_operation_tokens.py)。身份、分类、独立人员、规则、密钥和恢复代际的机构输入仍使用具名合成适配器；这不是六种角色均允许签发，也不是正式授权采用。

签发只支持服务端明确的`task + seal → sealEvidence`，保持原公共请求／响应；批准、任务、run／result、申请主体及当前analysis来源必须匹配。内部消费要求调用方已取得精确动作授权，并传入同一Database、同一根Connection；它不是公共消费接口，也不自动授予动作权限。`sealEvidence`真实业务消费者仍未挂载，`AuditExport`契约及既有消费者没有被悄悄改为携带令牌。

43项四类拒绝、T014／T015／T016全回归、批准／来源／人员／结果及合成职责撤销组合、最新CI和源码同步均按相应actual报告读取。报告的结果、受测SHA、源码摘要和适用范围必须匹配；不能根据测试文件存在登记通过，原S01—S09数据范围门禁保留。来源快照只声明当前单资产任务`task.asset_id → media_asset.source_id`的授权版本、状态、用途、期限及行版本摘要绑定；没有宣称多输入来源闭包。合成职责撤销也不等于正式跨人委托。令牌实际截止可能不足5秒、严格当前密钥轮换、角色确认／封存主体冲突及真实消费者前置见[安全边界](t016-operation-token-boundaries.md)，0011的64表861列及未升级共享库的边界见[数据库扩展](../04-database/operation-token-extension.md)。

正式六角色逐权限允许值、职责冲突、数据分类、授权用途和策略版本仍待有效规则；候选标签不等同真实密级。上述待决项不阻止当前设计与隔离夹具开发，但不允许启用未确认的正式动作。
