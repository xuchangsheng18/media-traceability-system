# T001—T123剩余接口逐项台账

本台账保留起点27项记录便于追踪；当前73项业务契约中51项已挂载、22项未挂载。getReport此前已实现，本轮新增downloadAsset、createSource、listModels、listEvaluations。挂载数量不是整任务完成数量。实际命令、失败修复、CI及同步见[本轮回执](../00-project/validation/t001-t123-resource-registry-report.json)，全部123项的具体缺口见[逐任务审计](t001-t123-development-completion-audit.md)。原100包锁、CI门禁保持，Python候选继续暂缓。

这些缺口包含待实现代码与待提供真实条件，不能一概归因于上游或等待审批。缺模型时可继续完成协议适配和拒绝路径，但不能登记真实推理成功。devLogin继续使用正式OIDC边界，不能为减少未挂载数开设密码旁路。

以下“已有”路径为当前源码；“拟新增”文件/方法仅表示后续代码位置，尚未创建或验证。表名均以现有版本迁移为依据；新增目标、操作目录或约束须使用后续迁移，不能改写0001—0013。各项均须保持统一认证、功能与对象条件、数据范围和提交前授权复查；权威事实缺失时默认拒绝，合成提供方仅用于隔离测试。

## 01. health

`GET /api/v1/health`；权限`health.read`；源任务：[T002](../../tasks/platform/T002.md), [T003](../../tasks/frontend/T003.md), [T004](../../tasks/platform/T004.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `backend/app/main.py` 的受保护原型健康接口仅检查其自身数据库；业务应用应复用 `backend/business_app/permissions/guard.py` 的身份与 `health.read` 功能检查，响应仍受既有 `Health` 契约约束。不得由进程存活推断模型、队列或业务全链路可用。

**下一段代码：** 拟新增 `backend/business_app/health_router.py` 与健康探测提供方协议；在既有 `main.py` 显式装配受保护路由。先补统一条件授权当前缺失的OPS分支、健康操作目标和最小运维事实解析，保持角色规则未满足时拒绝；再实现未配置探测提供方、探测超时和依赖失败的拒绝路径及合成探测隔离测试，最后接实际探测。探测不读取案件表，不泄露地址和诊断细节。

**必须补齐/保留的回归：** 补无身份401、缺功能权限403、提供方未配置503、超时/异常、实际失败不报ok、请求ID与响应Schema、探测结果变化及日志脱敏回归。

**实际资料与代码缺口：** 代码缺口是业务应用路由、探测协议及状态聚合语义；这些可继续实现。真实运行验证还需明确纳入检查的依赖、探测超时配置和实际部署提供方；不需要模型权重即可先完成基础设施探测适配与拒绝测试。

## 02. devLogin

`POST /api/v1/auth/login`；权限`development.login`；源任务：[T013](../../tasks/platform/T013.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 历史 `AuthLogin` 密码登录提案不等于现有OIDC。已有 `backend/business_app/identity/entrypoint.py`、`runtime.py`、`tokens.py` 和 `directory.py` 提供显式身份配置、令牌核验与目录映射；复用统一认证和权限检查，不增加密码旁路。

**下一段代码：** 继续完善既有身份入口的配置缺失、发行方/受众/签名验证和目录映射拒绝路径及联调测试；将本操作保持历史排除项。若以后调整公共登录契约，应单独提出OIDC入口与客户端会话流程的兼容方案，不能把现有密码提案直接挂载。

**必须补齐/保留的回归：** 保留并补充错误发行方/受众、过期与撤销令牌、未知主体、停用单位/人员、错误映射版本和直接请求密码接口不能取得业务身份的回归。

**实际资料与代码缺口：** 代码与配置校验仍可推进；真实身份联调需要实际OIDC发行方、受众、公钥发现入口、人员与单位映射及授权环境。缺这些输入不阻止拒绝测试，也不能用自建密码登录代替正式身份。

## 03. createSource

`POST /api/v1/sources`；权限`source.manage`；源任务：[T021](../../tasks/backend/T021.md)。

**当前状态：** `source_registration.py`已实现登记、权威证明及同事务幂等/审计；未配置权威与权限事实仍拒绝。 实测见[本轮回执](../00-project/validation/t001-t123-resource-registry-report.json)。

**复用与限制：** 已有 `mt.source_registry`、`backend/business_app/controls/router.py` 的来源读取/授权同步、`controls/providers.py` 的 `SourceSynchronization` 协议；可复用 `contracts.py` 校验、案件授权、`db.py` 的事务与RLS、`controls/receipts.py` 的幂等回执及 `controls/common.py` 的审计。客户端只提交 `SourceCreate` 既有字段，不提交可信verified事实。

**本轮代码及后续：** 本轮实际位置为`backend/business_app/source_registration.py`和`source_registration_router.py`；登记、读取和授权同步页面已有隔离验证；后续接真实权威、落实来源责任人，补来源修改维护和后台到期告警。

**必须补齐/保留的回归：** 补跨单位/案件、来源用途和期限不合法、伪授权引用、幂等重放/换体、回滚无半行记录、授权同步撤销及提交前事实变化回归。

**实际资料与代码缺口：** 原起点缺口包含创建服务、创建目标解析和来源依据核验适配；登记与默认拒绝可先编码。真实授权通过仍需来源依据的实际受控版本、适用用途/期限与可核验提供方，不能从授权引用字符串推导已获授权。

## 04. downloadAsset

`GET /api/v1/assets/{id}/content`；权限`asset.download`；源任务：[T025](../../tasks/backend/T025.md), [T030](../../tasks/frontend/T030.md)。

**当前状态：** 固定资产/ObjectRef、下载用途及分类、完整内容校验、Range、审计和最终权限复核已实现；资产页核验后保存。 实测见[本轮回执](../00-project/validation/t001-t123-resource-registry-report.json)。

**复用与限制：** 已有 `catalog_reads.py` 的资产与对象版本对应检查、`objects.py` 的不可变文件完整性读取、`scoped_objects.py` 的受控对象封装，以及 `controls/exports.py` 的单Range/If-Range处理；必须另建asset.download动作根，复用单位/案件/来源、密级及事务结束授权复查。

**本轮代码及后续：** 实际服务`backend/business_app/asset_download.py`，范围读取`scoped_objects.py`，页面`frontend/src/views/AssetsView.vue`；正式S3/WORM和真实后端组合E2E仍待。

**必须补齐/保留的回归：** 补无下载权限、用途/密级未知、跨案件对象引用、摘要/长度不符、文件缺失、来源撤销、读取途中授权变化、200/206/416、If-Range与审计失败回滚回归。

**实际资料与代码缺口：** 不需要模型制品；缺的是下载条件实现、对象消费入口和测试。真实下载需已有合法对象字节及适用下载用途/密级事实；可先用自建文件覆盖完整成功与拒绝流程，无需等待真实敏感样本。

## 05. createTask

`POST /api/v1/analysis/tasks`；权限`task.create`；源任务：[T034](../../tasks/backend/T034.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `controls/execution.py` 的节点执行和状态迁移、`history/repository.py` 的版本结果历史、`mt.analysis_task`/`mt.outbox_event`/`mt.idempotency_record`；可复用TASK_CREATE条件、案件来源用途、事务栅栏和幂等回执。它们尚不构成任务创建器。

**下一段代码：** 拟新增 `backend/business_app/task_creation.py`；按TaskCreate校验资产、scene、policy_version与modules，建立可信策略/能力版本解析协议。获完整授权后同事务写任务、运行/节点记录及outbox，后台按既有工作身份再次授权；提供方缺失时明确拒绝，先做合成计划隔离测试。

**必须补齐/保留的回归：** 补缺模型/策略版本、无分析用途、跨案件资产、不支持模块组合、同幂等键换体、并发重复创建、outbox与任务原子性、后台撤销及不生成伪结果回归。

**实际资料与代码缺口：** 可继续实现创建事务和计划解析协议；真实推理需实际scene/模块到策略、模型能力/前后处理版本的获准配置及执行提供方。任务入队只能表示接受调度，不能当作模型成功。

## 06. rerunTask

`POST /api/v1/analysis/tasks/{id}/rerun`；权限`task.rerun`；源任务：[T039](../../tasks/backend/T039.md), [T040](../../tasks/frontend/T040.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `controls/execution.py` 的状态迁移/租约、`history/repository.py` 的不可变版本和工作授权；复用task.rerun权限、精确任务范围、强ETag、幂等回执、`mt.task_run`/`mt.task_event`/outbox事务。

**下一段代码：** 拟新增 `backend/business_app/task_reruns.py`；锁定任务并核对expected_version、expected_run_version与node_codes，解析当前适用策略和批准要求，在新run版本建立重算计划，保留所有旧结果。重算计划和outbox须同事务写入，旧租约不能发布到新运行。

**必须补齐/保留的回归：** 补旧ETag/旧运行版本、并发重算、未知/不允许节点、批准撤销、来源变化、旧消息/旧租约结果拒绝、幂等重试和失败整笔回滚回归。

**实际资料与代码缺口：** 代码缺口是重算消费者与计划解析，不是缺少整套执行框架。真实执行仍需有效重算策略、模块/模型版本及适用批准事实；这些未齐时可完成拒绝与合成计划测试，但不产出伪模型结果。

## 07. searchImage

`POST /api/v1/search/image`；权限`asset.search`；源任务：[T082](../../tasks/algorithm/T082.md), [T084](../../tasks/algorithm/T084.md), [T085](../../tasks/algorithm/T085.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `inference.py` 的模型注册/能力契约校验、`scoped_objects.py` 的受控输入读取、`mt.search_job`/`mt.source_match`/`mt.index_registry`；须复用案件输入资产授权与来源用途，候选对象还要逐项核验可见性，不能只授权查询图。

**下一段代码：** 拟新增 `backend/business_app/search_jobs.py` 与检索提供方协议；先补统一条件授权当前缺失的CASE_SEARCH分支，再固定输入资产/索引版本、模型与预处理绑定，原子登记检索作业及调度消息。先实现未注册索引/模型、版本不兼容的拒绝，再用自建候选测试完整投影和授权过滤。

**必须补齐/保留的回归：** 补跨案件输入/候选、索引模型或维度不匹配、已退役索引、幂等重放、提供方超时/失败、不可见候选过滤与top_k/游标旁路、撤销前后读取回归。

**实际资料与代码缺口：** 真实搜索需要实际可用的图片特征/匹配模型、前后处理定义、已构建兼容索引和授权语料。协议、持久化、拒绝和隔离安全测试可以先完成；空候选响应不能充当已跑真实检索的证据。

## 08. searchImageRegion

`POST /api/v1/search/image-region`；权限`asset.search`；源任务：[T085](../../tasks/algorithm/T085.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 复用图片检索的 `inference.py`、受控对象读取和检索作业/索引表；既有ImageSearch含region字段，但公共字段存在不代表已实现区域裁剪、局部匹配或几何验证。

**下一段代码：** 在拟新增 `search_jobs.py` 的区域分支验证region与图像尺寸，固定坐标/裁剪映射和局部特征/几何匹配提供方，记录原图至区域的可追溯映射。先实现越界、缺局部能力和索引不兼容拒绝，复用同一作业事务和候选授权。

**必须补齐/保留的回归：** 补空/越界区域、坐标映射错误、裁剪后摘要变化、局部与全图接口混用、几何验证失败、无授权候选、重复请求及来源撤销回归。

**实际资料与代码缺口：** 真实结果还需获准的区域坐标约定、局部特征/匹配与几何模型及对应索引。先核对已有模型Schema能否完整表达映射；不足时提出契约差异，不自行新增公共参数。

## 09. searchVideo

`POST /api/v1/search/video`；权限`asset.search`；源任务：[T089](../../tasks/algorithm/T089.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 复用 `inference.py`、案件对象读取和检索作业/索引表；视频时间范围、帧映射与候选片段都须绑定来源和版本，不能把帧相似直接解释为整内容同源。

**下一段代码：** 在拟新增 `search_jobs.py` 建视频分支，核对VideoSearch.range、时间基与抽帧映射，接帧特征、时间对齐和片段定位提供方；持久化候选范围及未知区间，按候选逐项授权后投影。先编码缺能力、时轴错配与无兼容索引的拒绝。

**必须补齐/保留的回归：** 补范围越界、可变帧率/时间基映射、空音轨/缺帧、片段包含不等于整体同源、跨案件候选、提供方失败和unknown_ranges不被丢弃回归。

**实际资料与代码缺口：** 真实搜索需视频特征/时间对齐/片段定位模型、可追溯抽帧流程、兼容索引和授权语料；可先完成任务调度、协议校验与合成片段测试，不依赖真实敏感视频。

## 10. getSearchJob

`GET /api/v1/search/jobs/{id}`；权限`asset.search`；源任务：[T082](../../tasks/algorithm/T082.md), [T085](../../tasks/algorithm/T085.md), [T089](../../tasks/algorithm/T089.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `mt.search_job`/`mt.source_match` 和SearchJob/SearchResults契约；可借鉴 `registry_reads.py` 的精确对象读取、`scope_lookup.py` 的最小定位以及 `scope_collections.py` 的逐项对象核验。当前search作业尚无对应lookup与完整结果投影。

**下一段代码：** 拟新增 `backend/business_app/search_reads.py`；扩固定search目标与最小元数据定位，解析作业所属案件、输入资产和实际候选来源。按作业状态构造响应：未完成/失败保留空result，成功必须有完整已持久化结果和索引版本；候选权限在投影前核验。

**必须补齐/保留的回归：** 补跨单位/案件作业、来源撤销、不可见候选、FAILED错误码、SUCCEEDED无结果、部分片段/unknown_ranges完整性、状态变化及交付前权限复查回归。

**实际资料与代码缺口：** 读取已有合法作业不需要现场运行模型；缺的是目标解析、结果持久化到契约的映射与读取测试。真实成功作业仍需上列检索执行链产物；不能把缺结果的作业改成空成功。

## 11. decidePropagationEdge

`POST /api/v1/propagation/edges/{id}/decisions`；权限`review.perform`；源任务：[T096](../../tasks/backend/T096.md), [T097](../../tasks/frontend/T097.md), [T102](../../tasks/backend/T102.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `history/projection.py` 的传播图历史读取、`controls/reviews.py` 的复核职责/证据/版本核验及 `mt.propagation_edge`/`mt.review_record`。应复用review.perform权限、案件来源、独立人员事实、强ETag与同事务审计。

**下一段代码：** 拟新增 `backend/business_app/propagation_decisions.py`；先实现边ID到案件/簇/任务结果版本的可信解析，核对GraphDecision的expected_version与证据清单，再追加决策记录或新图版本。若现表不足以保留决策历史，用新迁移补结构，不覆盖历史事实。

**必须补齐/保留的回归：** 补跨簇/跨结果证据、自己复核自己的结论、职责未知、旧ETag/并发决定、撤销与新版本、审计回滚，以及图读取可追溯新旧决定的回归。

**实际资料与代码缺口：** 边目标解析与追加记录服务尚待编码；需核实边到任务结果的实际绑定结构，及适用复核职责/独立人员规则。可先做结构差异、默认拒绝和合成复核测试，不必把所有代码工作列成等待回复。

## 12. extractClaims

`POST /api/v1/claims/extract`；权限`claim.analyze`；源任务：[T098](../../tasks/algorithm/T098.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `mt.claim`/`mt.text_segment` 和 `inference.py` 的claim.extract能力调用框架；复用案件资产、来源分析用途、模型版本/前后处理与mapping_version校验。文本是外部不可信输入，不能成为权限或工具指令。

**下一段代码：** 拟新增 `backend/business_app/claim_operations.py`；读取获准文本片段，固定原文位置与映射版本，调用提取提供方并校验每条主张的来源引用后同事务追加claim记录。先补缺模型、无源文本、引用越界的拒绝和合成提供方测试。

**必须补齐/保留的回归：** 补跨案件片段、OCR/ASR映射错位、提示注入文本、无引用/伪引用主张、缺模型/超时、重复请求、来源撤销及落库失败原子性回归。

**实际资料与代码缺口：** 真实提取需要claim.extract模型制品、实际OCR/ASR或其他获准原文及对应映射。代码适配与安全测试可以先做；不能用模板文本或空列表冒充模型已提取主张。

## 13. verifyClaim

`POST /api/v1/claims/{id}/verify`；权限`claim.analyze`；源任务：[T099](../../tasks/algorithm/T099.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有claim与 `mt.claim_evidence_relation`，以及 `inference.py` 的关系/grounding能力契约框架；复用精确案件主张定位、受控证据读取和任务/来源边界，模型输出只表示证据关系。

**下一段代码：** 在拟新增 `claim_operations.py` 实现主张到案件/资产的定位，核对请求证据引用与模型/映射版本，接关系判断和grounding提供方，验证支持位置后追加关系历史。先完成无证据、缺grounding、错绑任务的拒绝。

**必须补齐/保留的回归：** 补不存在/跨案件主张、跨版本证据、关系与定位矛盾、伪引用、提供方失败、重复写入、来源撤销和模型措辞被误写成法律结论的回归。

**实际资料与代码缺口：** 真实核查需关系/grounding模型、可追溯证据片段和适用输出映射；这些不齐仍可实现定位、协议校验、拒绝与隔离测试。不能把缺证据推断为主张为真或为假。

## 14. sealEvidence

`POST /api/v1/evidence-packages/{case_id}/seal`；权限`evidence.seal`；源任务：[T104](../../tasks/backend/T104.md), [T105](../../tasks/backend/T105.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `controls/operation_tokens.py` 的同Connection一次性令牌消费、`controls/approvals.py`、不可变task_result及 `mt.evidence_package`/`mt.package_item`/对象版本；复用动作根、批准/用途/版本、来源及提交前复查。当前令牌支持范围限单资产案件task/seal，不自动支持任意封存。

**下一段代码：** 拟新增 `backend/business_app/evidence_sealing.py`；先补统一条件授权当前缺失的SEAL分支，再核对请求case/task/run/result及所有证据，生成实际包清单与不可变对象，再在同一数据库事务消费令牌、写包/条目/对象登记及审计。处理文件已写而数据库回滚的孤儿产物，不将文件写入与SQL误称单一原子事务。

**必须补齐/保留的回归：** 补令牌重放/过期/换用途/换对象、批准和来源撤销、混入其他结果证据、摘要或清单不符、并发封存、字节写入失败、SQL回滚及孤儿清理可追溯回归。

**实际资料与代码缺口：** 需编码真实封存消费者、包清单格式与存储协调；正式执行还需保留策略版本、批准职责和已登记真实证据。先用自建文件验证全过程；二次确认不能代替批准，也不等于已完成封存。

## 15. createReportDraft

`POST /api/v1/reports/drafts`；权限`report.draft`；源任务：[T106](../../tasks/backend/T106.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `history/repository.py` 的结果快照、`registry_reads.py` 的报告/证据元数据核验，以及 `mt.report`/`mt.report_evidence`。草稿应复用report.draft功能条件、同案件task/run/result、来源与逐句证据引用核验，不从草稿状态推导正式资格。

**下一段代码：** 拟新增 `backend/business_app/report_generation.py` 的草稿服务和文本提供方协议；先补当前缺失的REPORT_DRAFT条件分支，再按ReportDraft固定模板、结果版本和evidence_ids，验证输出每句话的证据映射后追加草稿与引用关系。先实现模板未知、证据不全、文本提供方缺失和失败回滚路径。

**必须补齐/保留的回归：** 补跨结果证据、无依据句子、模型编造引用、模板版本变化、幂等重放、来源撤销、旧结果读取和草稿不能直接下载为正式报告回归。

**实际资料与代码缺口：** 真实语义草稿需实际模板/引用规则与M30适用文本生成能力及受控输入；服务协议、版本绑定和拒绝测试可先完成。已有getReport只读取已存元数据，不会生成草稿内容。

## 16. createReport

`POST /api/v1/reports`；权限`report.generate`；源任务：[T107](../../tasks/backend/T107.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有批准、令牌、结果快照、报告元数据读取与不可变对象能力；需复用report.generate动作、确切task/run/result/evidence/template及批准用途/有效期/版本的同事务核验。`ReportCreate`已有operation_token字段，但当前令牌消费者仅覆盖seal，不能据此自动放行报告。

**下一段代码：** 在拟新增 `report_generation.py` 建正式渲染服务，先补当前缺失的REPORT_GENERATE条件分支，再接可重建Word/PDF模板渲染器和受控对象输出。先明确报告动作令牌绑定并扩对应受限消费者，生成/登记版本化文件、report及report_evidence并审计；文件与SQL失败均有恢复记录。

**必须补齐/保留的回归：** 补未批准/已撤销/过期、批准对象或模板/结果版本错配、令牌重放、证据变更、渲染失败/对象摘要不符、并发版本和事务回滚；验证报告状态不替代批准状态。

**实际资料与代码缺口：** 代码缺口是正式报告消费者、渲染器及报告令牌范围；真实生成需获准模板、适用批准/职责/确认规则和真实证据输入。可先实现缺配置拒绝、合成渲染和回滚测试，不能凭审批记录生成空报告。

## 17. getReport

`GET /api/v1/reports/{id}`；权限`report.read`；源任务：[T107](../../tasks/backend/T107.md)。

**当前状态：** 已挂载本批实际数据库元数据读取；32项专项实跑通过，不含报告生成、下载或正式验收。

**复用与限制：** 本批已有 `registry_reads.py`、`registry_router.py`、`0013_report_reads.sql`；统一report.read→CASE_READ、精确report定位、案件/任务历史绑定、全部证据来源与事务栅栏复查。只投影已持久化report/report_evidence及同案件object_version，不读文件、不新增公共参数。

**下一段代码：** 保持本批读取子范围，完成正在运行的完整回归并按回执归档；继续验证前端报告详情和拒绝提示。后续若改投影或范围条件，增补对应回归；报告创建/渲染/下载应分别按第15、16、18项开发，不能登记为此读取项的完成部分。

**必须补齐/保留的回归：** 本批32项已实跑通过：13项纯投影、17项HTTP/SQL、2项0012→0013升级/回滚；覆盖源撤销、密级/用途事实缺失、跨案件、弱动作根、证据/对象错绑、缺证据和提交前授权变化。47接口完整权限回归保留原1200秒上限，实际结果见本批回执，不由专项通过推导全量通过。

**实际资料与代码缺口：** 本批元数据读取无需真实模型制品；隔离测试使用自建事实/数据，正式身份、人员/密级用途事实和真实报告产物联调仍未完成。1000条证据上限是显式研发资源拒绝，非已批准业务阈值；生成、下载及T107整卡验收均未包含。

## 18. downloadReport

`GET /api/v1/reports/{id}/content`；权限`report.export`；源任务：[T107](../../tasks/backend/T107.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 复用 `registry_reads.py` 的报告/证据/对象版本绑定、`controls/approvals.py` 的批准核验、`scoped_objects.py` 和 `controls/exports.py` 的受控对象/Range模式；report.export须独立授权，READY、非空approval_id或getReport成功均不能代替导出授权。

**下一段代码：** 拟新增 `backend/business_app/report_downloads.py`；补齐当前缺失的REPORT_EXPORT条件分支及精确产物读取绑定，核对实际批准用途、对象/结果/模板版本与有效期，读取不可变字节后在交付前重核来源/批准/身份，并记录导出审计。先实现缺实际产物、缺规则或不满足批准的拒绝。

**必须补齐/保留的回归：** 补未READY/产物不存在、批准撤销/过期/错用途、旧报告替换、文件摘要/长度不符、Range/If-Range、跨案件、交付前权限变化和审计失败不交付回归。

**实际资料与代码缺口：** 不需要再次运行模型；需补下载消费者与实际报告产物/导出规则。自建报告文件足以先测协议与安全链，真实报告下载验收仍需合法生成产物及适用批准事实。

## 19. requestFeedback

`POST /api/v1/feedback/samples`；权限`feedback.request`；源任务：[T108](../../tasks/backend/T108.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `controls/router.py` 的反馈读取、`mt.feedback_request`、批准链和幂等/审计事务；沿用训练用途、来源、案件职责与对象绑定的核验思路；六角色规则指向FEEDBACK_REQUEST，但当前条件要求尚缺此分支，须补完整需求，不能从分析用途授权推导训练回流授权。

**下一段代码：** 拟新增 `backend/business_app/feedback_requests.py`；将Feedback中的发现/标注/批准引用解析到案件、任务结果和来源，核验训练用途与批准后仅登记回流申请及审计。将实际数据出域/入训练集作为独立受控消费者，不因申请成功自动复制样本。

**必须补齐/保留的回归：** 补分析可用但训练不可用、来源/批准撤销、标注/发现跨结果、封存holdout被回流、幂等重试、并发申请与写入失败回滚回归。

**实际资料与代码缺口：** 可先完成申请登记、引用校验和拒绝测试；真实回流需样本用途/许可、数据集划分、标注版本及受控目标。申请记录成功只表示已登记，不表示数据已获准训练或已完成回流。

## 20. registerModel

`POST /api/v1/models`；权限`model.manage`；源任务：[T052](../../tasks/algorithm/T052.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `mt.model_registry`、ModelCreate契约和 `inference.py` 的后端注册框架；可复用单位身份、MODEL条件中的model_metadata_scope、ORGANIZATION DataScope及RLS。客户端digest、模型卡和许可引用只提供待核对标识。

**下一段代码：** 拟新增 `backend/business_app/model_registry.py`；先设计并实现单位模型创建目标、制品/模型卡/许可引用核验协议与默认拒绝，再接实际受控登记。登记事务写名称/版本/能力/制品摘要和环境绑定，不能顺带变为APPROVED或ACTIVE；不新增case_id公共参数。

**必须补齐/保留的回归：** 补跨单位制品、摘要与实际字节不符、许可/环境引用缺失、能力/版本重复、未配置可信元数据范围、同幂等键换体及登记失败回滚。

**实际资料与代码缺口：** 代码缺口是组织目标、登记服务和核验提供方；可先以自建制品覆盖正常登记和拒绝。真实模型登记需实际制品字节/范围、可追溯模型卡/许可与环境记录，不能把字符串检查称为许可核验。

## 21. listModels

`GET /api/v1/models`；权限`model.read`；源任务：[T052](../../tasks/algorithm/T052.md), [T060](../../tasks/frontend/T060.md)。

**当前状态：** 同单位真实元数据列表已实现，逐条范围先于分页，游标及提交前复核保留；不生成健康或准入结论。 实测见[本轮回执](../00-project/validation/t001-t123-resource-registry-report.json)。

**复用与限制：** `mt.model_registry`、Model/ModelPage契约和ORGANIZATION模式已存在，读取目录不需要执行模型；可复用MODEL条件、单位RLS、`controls/common.py` 的游标绑定思路。现有CASE分页不能用伪造case_id直接套用，模型集合目标尚未实现。

**本轮代码及后续：** 实际服务`backend/business_app/model_catalog.py`及`model_catalog_router.py`；继续模型写入/卡片/唯一版本和管理页面，真实模型准入另验。

**必须补齐/保留的回归：** 补缺可信元数据范围503、跨单位行不可见、合法空目录、隐藏行不影响计数/游标、游标换单位/用户/limit/过滤条件、未知/重复参数、授权撤销及提交前复查回归。

**实际资料与代码缺口：** 主要是可继续编码的集合解析、组织分页、投影和安全测试，缺模型权重不阻塞这些工作。正式展示需明确实际元数据可见范围及可信提供方；单个角色名称不能自动授予全单位模型目录。

## 22. getModelHealth

`GET /api/v1/models/{id}/health`；权限`model.manage`；源任务：[T056](../../tasks/algorithm/T056.md), [T060](../../tasks/frontend/T060.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有模型注册表和Health响应结构，`controls/providers.py` 的DeploymentOperations仅能读取部署操作，尚无模型健康探测方法。复用model.manage、精确单位模型目标、MODEL条件及健康信息最小披露；REGISTERED或ACTIVE状态不能证明运行健康。

**下一段代码：** 拟新增 `backend/business_app/model_health.py` 的模型健康探测协议/路由，先完成精确model_id定位和未配置/超时/错误模型版本的拒绝，再对绑定实际制品/后端/环境的服务实施有界探测。业务聚合health与单模型探测分开装配，响应不外泄运行拓扑。

**必须补齐/保留的回归：** 补跨单位模型、无model.manage、元数据范围未知、探测超时/异常、错误版本/后端、注册但未加载不报ok、请求ID和Schema回归。

**实际资料与代码缺口：** 路由、协议、拒绝与合成探测可先实现；真实健康成功需实际运行服务/模型版本和可核验探测结果。无需先补所有模型训练，但不能用数据库状态代替真实服务探测。

## 23. rolloutModel

`POST /api/v1/models/{id}/rollouts`；权限`model.release`；源任务：[T057](../../tasks/algorithm/T057.md), [T060](../../tasks/frontend/T060.md), [T170](../../tasks/README.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `mt.model_release`、批准记录和DeploymentOperations读取协议；没有实际发布/回退方法，`permissions/object_facts.py` 对组织模型动作仍保留适配器缺失拒绝。应复用MODEL/APPROVE_MODEL条件、制品与索引版本绑定和审计，不能只改数据库ACTIVE标志。

**下一段代码：** 拟新增 `backend/business_app/model_rollouts.py` 与部署执行协议；先补当前缺失的MODEL_RELEASE条件分支，再实现单位release目标、准入条件、批准/确认绑定、幂等发布请求和后台工作身份，再接真实部署/健康检查/回退。T170仅为本接口引用的范围外后续依赖，本批不将其整卡纳入T001—T123完成。

**必须补齐/保留的回归：** 补无实际制品/评测/许可、批准撤销/错版本、无独立人员事实、并发发布、重复消息、服务切换失败/回退失败、部分索引切换、操作状态与实际部署不一致回归。

**实际资料与代码缺口：** 可先完成发布状态机、请求事务和默认拒绝；真实发布需获准的模型/评测/许可/环境、实际部署与回退提供方及组织批准/确认规则。当前令牌seal范围不得直接移用为模型发布授权。

## 24. recordEvaluation

`POST /api/v1/model-evaluations`；权限`model.evaluate`；源任务：[T058](../../tasks/algorithm/T058.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有追加写入的 `mt.model_evaluation`、EvaluationCreate契约和单位模型目录；复用组织身份/模型元数据范围、数据库追加保护、对象摘要与数据集用途边界。提交metrics数字不等于已执行评测。

**下一段代码：** 在拟新增 `model_registry.py` 的评测服务中核对同单位model、dataset/version/protocol/split、样本与失败计数，建立评测产物真实性/摘要核验提供方；验证后追加记录，未知协议或无实际产物明确拒绝，不覆盖旧评测。

**必须补齐/保留的回归：** 补跨单位模型/产物、指标Schema/区间不合法、failure_count超过sample_count、协议与划分不符、伪产物/错误摘要、重复提交、holdout用途违规、更新/删除被拒绝及事务回滚。

**实际资料与代码缺口：** 校验、追加事务和合成产物测试可继续编码；真实评测登记需实际执行产物、协议口径、数据集版本/划分与适用用途。接口不负责凭用户数字补造评测证据。

## 25. listEvaluations

`GET /api/v1/model-evaluations`；权限`model.read`；源任务：[T058](../../tasks/algorithm/T058.md)。

**当前状态：** 真实已存评测记录读取已实现，同单位模型及登记对象的版本/摘要均核验；不运行评测或生成指标。 实测见[本轮回执](../00-project/validation/t001-t123-resource-registry-report.json)。

**复用与限制：** 已有评测表与Evaluation/EvaluationPage契约；组织DataScope/RLS和MODEL条件可复用，但集合目标、组织分页和每项模型/产物元数据披露尚待实现。不能借案件授权或零UUID读取组织目录。

**本轮代码及后续：** 实际服务`backend/business_app/model_catalog.py`；固定对象查验在0014；继续评测登记/生产、分组指标与发布审批引用。

**必须补齐/保留的回归：** 补跨单位评测/模型、无元数据范围、隐藏评测不泄露总数/游标、指标与artifact_ref契约缺失、游标重放/换绑定及授权变化回归。

**实际资料与代码缺口：** 可继续实现集合目标、分页和投影；读取不需要模型制品。真实记录来源仍须可追溯评测，正式组织元数据可见范围须有可信事实；无记录是合法空目录，不得补造指标。

## 26. getIndex

`GET /api/v1/indices/{id}`；权限`index.manage`；源任务：[T081](../../tasks/algorithm/T081.md), [T157](../../tasks/README.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有 `mt.index_registry` 与IndexVersion契约及组织RLS；复用index.manage功能校验、精确定位和事务栅栏；六角色规则指向INDEX分支，但 `permissions/conditional.py` 尚缺对应条件要求，必须补齐可信索引元数据范围，不能直接套用MODEL放行。当前也没有index lookup/组织对象目标，公共契约没有case_id参数。

**下一段代码：** 拟新增 `backend/business_app/index_registry.py`；实现固定index_id最小定位、可信单位索引目标与IndexVersion投影，核对模型版本/维度/归一化等登记字段，元数据范围缺失拒绝。先用合成索引目录完成同单位正常读取和越权测试；不让目录读取隐含索引已构建或服务可用。

**必须补齐/保留的回归：** 补跨单位索引、无index.manage、元数据范围未知、额外/重复case_id参数、缺模型/维度字段、状态变化与提交前权限复查回归。

**实际资料与代码缺口：** 读取所需代码可继续实现，不依赖真实特征索引。真实索引状态/可用性须另由构建与运行证据证明；T157是范围外依赖，不能因本接口挂载就记其完成，也不能自行授予跨案件索引数据访问。

## 27. switchIndex

`POST /api/v1/indices/{id}/switch`；权限`index.manage`；源任务：[T081](../../tasks/algorithm/T081.md), [T157](../../tasks/README.md)。

**当前状态：** 业务应用仍未挂载；以下为后续实施导航，不表示已实现或测试通过。

**复用与限制：** 已有索引登记表、IndexSwitch契约和审计能力；尚无实际索引切换提供方。复用index.manage组织对象、强ETag、当前批准和模型/维度/归一化兼容核验，数据库状态更新不能代替服务端原子切换。

**下一段代码：** 在拟新增 `index_registry.py` 实现切换请求与状态协调，增加真实索引提供方的准备/切换/确认/回退协议，并补齐INDEX条件分支及可信索引范围；先锁定expected_version、目标版本和批准，默认拒绝未构建或不兼容索引。核对现有Schema能否表达进行中/失败恢复；有契约差异先列明，不自行扩公共字段。

**必须补齐/保留的回归：** 补旧ETag、跨单位目标、未READY/模型维度或归一化不兼容、批准撤销、并发切换、服务失败/回退、数据库与服务状态分歧、审计回滚和查询中版本固定回归。

**实际资料与代码缺口：** 可先实现兼容校验、请求事务、提供方边界和失败测试；真实切换需实际构建索引、服务适配器、批准用途及回退能力。T157为范围外依赖；批准语义和恢复表示未明确前保持拒绝，不用空成功挂载。

本批来源登记/授权同步内核及页面已有[限定实测](../00-project/validation/backend-frontend-data-test-report.json)；syncSourceAuthorization原已挂载，不增加接口数。当前源码仍为51项已挂载、22项未挂载；原27项捕获字段及旧回执保留作历史依据，JSON的current字段为当前观察。

本批来源登记/授权同步内核及页面已有[限定实测](../00-project/validation/backend-frontend-data-test-report.json)；syncSourceAuthorization原已挂载，不增加接口数。当前源码仍为51项已挂载、22项未挂载；原27项捕获字段及旧回执保留作历史依据，JSON的current字段为当前观察。
