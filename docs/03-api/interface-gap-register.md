# 接口缺口台账：技术子范围与正式条件

当前73个外部契约操作、102组件；13类正式条件仍开放。首批上传/历史读取及本批剩余11类的技术实现分别核验，不能把可调用或测试夹具当正式接入。详细入口：[实际实现说明](../03-development/stage-three/remaining-interface-implementation.md)、[逐操作目录](detailed-interface-index.md)、[机器台账](interface-gap-register.json)。

## IF-G01 上传续传与校验状态查询

已实现首批独立业务HTTP/持久化/异常检查；具体证据和限制见首批实现说明。正式权威、媒体/模型及剩余业务条件仍未满足。

当前子范围状态：`VERIFIED_SELECTED_SCOPE`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`GET /uploads/{id}`、`GET /uploads/{id}/parts`。

原拟议方案：复用UploadSession/UploadPart/UploadResult组成投影，定义已接收分片、总量/摘要、到期/校验终态，asset_id仅VALID后可分析。

正式关闭要求：补唯一契约/样例/映射/类型，测中断续传、重复/摘要冲突、到期和异步成功/失败。

## IF-G02 审批读取与撤销链路

本批已实现的操作：requestApproval、decideApproval、listApprovals、getApproval、revokeApproval；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`POST /approvals`、`POST /approvals/{id}/decisions`、`GET /approvals`、`GET /approvals/{id}`、`POST /approvals/{id}/revoke`。

原拟议方案：复用Approval，定义有权对象列表/详情/决定历史、游标/ETag、目的/版本/到期；撤销是否走现有decisions需规则决定，不能自动赋予审批权。

正式关闭要求：正式规则确认后补契约/SQL映射/追踪，测跨案件、两人独立性、到期与重算使旧批准失效。

## IF-G03 复核工作台读取与版本冲突

本批已实现的操作：createReview、listReviews、getReview、getReviewContext、listPendingReviews；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`POST /reviews`、`GET /reviews`、`GET /reviews/{id}`、`GET /analysis/tasks/{id}/review-context`、`GET /reviews/pending`。

原拟议方案：复用Review设计有权待办/记录读取，明确task/run/result/review绑定、筛选、ETag和只追加历史，不自动放行报告。

正式关闭要求：补源契约和追踪，测提交前读取版本、同时复核冲突、退回后历史可查。

## IF-G04 反馈审批与回流状态读取

本批已实现的操作：getFeedback；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`GET /feedback/samples/{id}`。

原拟议方案：复用反馈结构补受控数据版本投影、撤销停止/去重；用途/划分核验，禁止封存测试集回流。

正式关闭要求：补契约/数据卡/审批引用，测拒绝、撤销、重复消费与样本计数不重复。

## IF-G05 模型灰度及回滚操作查询

本批已实现的操作：getModelOperation；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`GET /model-operations/{id}`。

原拟议方案：以ActionAck.object_id绑定发布操作，定义状态、release_bundle/模型/索引版本、失败/进度/回滚终态。

正式关闭要求：补操作Schema/映射与受理至终态链路，测不兼容拒绝、幂等/失败后回滚、许可/批准。

## IF-G06 审计导出作业及产物读取

本批已实现的操作：exportAudit、listAuditEvents、getAuditExport、downloadAuditExport；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`POST /audit/exports`、`GET /audit/events`、`GET /audit/exports/{id}`、`GET /audit/exports/{id}/content`。

原拟议方案：以object_id绑定导出，补状态和固定ObjectRef；限定组织/案件/时间、批准目的、脱敏/到期；下载按Range/当前授权核验。

正式关闭要求：补唯一结构/投影及来源确认，测受理/失败/终态/摘要下载和撤销后下一Range拒绝。

## IF-G07 正式身份与角色案件授权边界

本批已实现的操作：getCurrentUser；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`GET /auth/me`。

原拟议方案：确认身份方协议、主体映射、令牌/撤销、授权同步/审计；先确定统一平台或仓库管理API的责任，不能制造第二权限源。

正式关闭要求：取得Q-05/Q-16/Q-25决定和实际材料，补协议/Schema与授权、撤销、越权联调证据。

## IF-G08 来源授权验证和失效同步

本批已实现的操作：listSources、getSource、syncSourceAuthorization；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`GET /sources`、`GET /sources/{id}`、`POST /sources/{id}/authorization/sync`。

原拟议方案：明确权威授权记录、用途/到期/撤销版本及适配器/事件；客户端authorization_status不能完成授权。确定动作后才加入OpenAPI。

正式关闭要求：补核验协议与追踪，撤销后分析/导出/训练回流拒绝且历史和审计可追溯。

## IF-G09 按历史运行结果查询

已实现首批独立业务HTTP/持久化/异常检查；具体证据和限制见首批实现说明。正式权威、媒体/模型及剩余业务条件仍未满足。

当前子范围状态：`VERIFIED_SELECTED_SCOPE`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

原拟议方案：版本字段成组必填；严格按当前案件/对象和task/run/result匹配、404不回退最新。快照保存34能力原响应，列表/完整专用公开投影及后端联调仍待实现。

正式关闭要求：补路径/参数/字段/追踪，测两次重算后精确版本、旧结果不可变和跨案件拒绝。

## IF-G10 第三方数据平台适配器协议

本批已实现的操作：createImport、getImport；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`POST /imports`、`GET /imports/{id}`。

原拟议方案：逐平台登记批准方式/版本、来源标识、发布时间/观测时间/可见范围、签验、游标/去重/限流，不虚构URL或账号。

正式关闭要求：取得Q-17/Q-28和平台资料后补协议，测重复、签验/到期错误、字段缺失及限流。

## IF-G11 全业务DAG与跨模块事件

本批已实现的操作：listTaskNodes、listTaskEvents、getTaskExecution、cancelTask；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`GET /analysis/tasks/{id}/nodes`、`GET /analysis/tasks/{id}/events`、`GET /analysis/tasks/{id}/execution`、`POST /analysis/tasks/{id}/cancel`。

原拟议方案：先决定API/消息边界，定义必要事件的结构版本、生产消费方、运行身份、去重/租约fencing、顺序/重试/取消/死信与授权；每个实际事件单独Schema。

正式关闭要求：确定DAG/取消后补必要Schema/类型，测真实多worker、重复乱序、旧运行/超时及死信恢复。

## IF-G12 配置值、聚合ETag及策略生效

本批已实现的操作：createPolicy、listPolicies、getPolicy、getPolicyDefinition；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

本批实际挂载：`POST /policies`、`GET /policies`、`GET /policies/{id}`、`GET /policies/{id}/definition`。

原拟议方案：明确资源/聚合强ETag与原子更新；配置引用唯一版本，数值待资源/规则决定；草案、批准和生效分别定义。

正式关闭要求：形成决定及适用契约，测同键不同摘要、旧ETag、权限/重算失效、稳定分页/背压。

## IF-G13 内部34能力服务语义与一致性

本批已实现的操作：内部34能力网关的结构/身份/输入/输出边界；Linux隔离真实数据库/HTTP全量122项业务检查通过，74源文件类型检查通过。实际范围及尚缺的正式协议/规则/模型见remaining-interface-implementation.md；精确托管源码与同步以最终报告为准。

当前子范围状态：`VERIFIED_SELECTED_DEVELOPMENT_SCOPE_FORMAL_CONDITIONS_OPEN`。正式状态仍`OPEN_CONTRACT_OR_FORMAL_DESIGN_GAP`；formal_frozen=false，approved=false。

原拟议方案：模型Schema保持唯一；调用/响应核验path/body能力、model/run/request身份、对象版本/摘要、授权、deadline和输出语义；支持列表应匹配实际部署。

正式关闭要求：逐能力补实现/授权样本验证，测能力错配、非法对象、超时/取消；不拿mock或Schema当准确率通过。
