# T014 六角色权限规则具体方案（隔离实现输入已确认）

2026-10-20，候选版本 `t014-six-role-proposal-20261020-v1`。开发负责人、指定复核人徐昌胜；用户已确认PR01、PR02、PR04作为下一批隔离实现与测试输入，未登记正式权限采用或整任务验收。适用当前 Linux／Miniforge py310／CPU、同一单位内部研发。Python 候选继续暂缓。本页补齐 T014-R01 的规则输入，不能关闭 T014 或替代 T013 本人交接。

本页及[机器表](t014-six-role-rule-proposal.json)共覆盖六角色、41 个权限码、246 格和73个契约操作。现有42操作统一权限代码保留，其余31操作不因出现在表中就变为可调用。旧[T011来源矩阵](permission-matrix.md)的“职责/待定/限制”原样保留；本方案把工程建议单独列出，尚未改写来源模型、数据库种子或活动授权。

## 1. 采用哪种方式

建议在现有角色权限目录上增加明确的对象、关系和用途条件：角色先限定功能，单位/案件/来源/版本再共同约束对象。仅按角色名称全局授权容易放大管理员和审核员的访问范围；直接引入外部通用策略平台会增加新的制品、服务和运维依赖。本次选择复用现有 `require_permission`、受限事实查询和各资源授权入口，后续按审定规则逐项实现；不新增平台依赖。

判定链：有效认证 → 已批准且版本一致的角色规则 → 当前功能事实 → 同单位/有效案件关系 → 资源归属 → 来源/用途/分类 → 审批和职责分离 → 实际操作前重验。任一必需项未知或不可读，均不产生允许。当前缺正式策略继续503；已认证但无许可403；对象越界沿既有404隐藏；未认证401。文档中的条件名称和候选数值不是新增API字段。

## 2. 六角色的工作边界

| 角色代码 | 主要工作 | 必须保留的限制 |
| --- | --- | --- |
| system_admin 系统管理员 | 服务配置、用户/角色维护和备份管理 | Keycloak管理身份与业务角色分离；没有案件内容、来源授权或业务策略通配许可。当前41码没有“任意用户/角色写入”API，不能借policy.manage补出该能力。 |
| data_admin 数据管理员 | 来源登记、授权同步、接收/导入和保存策略草稿 | 权威来源决定verified；不能自行签发来源依据、改算法结论、浏览全部案件内容或批准本人回流。 |
| algorithm_admin 算法管理员 | 模型注册、评测、发布执行、算法策略草稿和索引维护 | 仅另行授权脱敏数据；模型发布是组织级，不能借案件成员关系；发布者不能批准自己的制品。 |
| business_reviewer 业务审核员 | 获派案件复核、审批、证据封装和业务规则草稿 | 不修改原始证据、不创建替代来源许可、不批准自己提交或执行的对象。 |
| case_investigator 案件核查人员 | 授权案件的接收、分析、检索、报告及申请 | 同单位并有有效案件成员关系；创建、生成、下载、导出分别判断；申请不算批准。 |
| auditor 审计员 | 获委托范围日志只读及经批准的日志导出 | 不写业务结论、不管理配置、不执行任务或复核；导出作业仅产生受控审计制品。 |

## 3. 全部权限逐格建议

`—` = 本角色没有该项授权来源；不是把其他兼容角色的合法许可一律否决。条件代号 = 建议可授予，但必须满足第4节的全部限定及通用条件。所有格当前 `runtime_allow=false`；缺失条件不能退化为“只要有角色就允许”。`development.login` 六角色均不授予，唯一开发例外未挂载且不能用于正式登录。

| 权限码 | 系统管理员 | 数据管理员 | 算法管理员 | 业务审核员 | 案件核查人员 | 审计员 |
| --- | --- | --- | --- | --- | --- | --- |
| approval.decide | — | — | APPROVE_MODEL | APPROVE_CASE | — | — |
| approval.read | — | REQUEST_DATA_READ | REQUEST_MODEL_READ | APPROVAL_CASE_READ | REQUEST_CASE_READ | REQUEST_AUDIT_READ |
| approval.request | — | REQUEST_DATA | REQUEST_MODEL | REQUEST_CASE | REQUEST_CASE | REQUEST_AUDIT |
| approval.revoke | — | — | REVOKE_MODEL | REVOKE_CASE | — | — |
| asset.download | — | — | — | CASE_DOWNLOAD | CASE_DOWNLOAD | — |
| asset.import | — | INGEST | — | — | INGEST | — |
| asset.read | — | — | — | CASE_READ | CASE_READ | — |
| asset.search | — | — | — | — | CASE_SEARCH | — |
| asset.upload | — | INGEST | — | — | INGEST | — |
| audit.export | — | — | — | — | — | AUDIT_EXPORT |
| audit.read | — | — | — | — | — | AUDIT_READ |
| claim.analyze | — | — | — | — | CASE_ANALYSIS | — |
| development.login | — | — | — | — | — | — |
| evidence.read | — | — | — | CASE_READ | CASE_READ | — |
| evidence.seal | — | — | — | SEAL | — | — |
| feedback.read | — | — | — | FEEDBACK_REVIEW | FEEDBACK_OWN | — |
| feedback.request | — | — | — | — | FEEDBACK_REQUEST | — |
| health.read | OPS | — | — | — | — | — |
| identity.read | SELF | SELF | SELF | SELF | SELF | SELF |
| index.manage | — | — | INDEX | — | — | — |
| model.evaluate | — | — | MODEL | — | — | — |
| model.manage | — | — | MODEL | — | — | — |
| model.read | — | — | MODEL | — | — | — |
| model.release | — | — | MODEL_RELEASE | — | — | — |
| operation.confirm | — | — | CONFIRM_MODEL | — | CONFIRM_CASE | — |
| origin.read | — | — | — | CASE_READ | CASE_READ | — |
| policy.manage | — | POLICY_RETENTION | POLICY_ALGORITHM | POLICY_BUSINESS | — | — |
| policy.read | — | POLICY_RETENTION | POLICY_ALGORITHM | POLICY_BUSINESS | — | — |
| propagation.read | — | — | — | CASE_READ | CASE_READ | — |
| report.draft | — | — | — | — | REPORT_DRAFT | — |
| report.export | — | — | — | — | REPORT_EXPORT | — |
| report.generate | — | — | — | — | REPORT_GENERATE | — |
| report.read | — | — | — | CASE_READ | CASE_READ | — |
| review.perform | — | — | — | REVIEW | — | — |
| review.read | — | — | — | CASE_READ | CASE_READ | — |
| source.manage | — | SOURCE_WRITE | — | — | — | — |
| source.read | — | SOURCE | — | — | SOURCE | — |
| task.cancel | — | — | — | — | TASK_CONTROL | — |
| task.create | — | — | — | — | TASK_CREATE | — |
| task.read | — | — | — | CASE_READ | CASE_READ | — |
| task.rerun | — | — | — | — | TASK_CONTROL | — |

## 4. 每个条件的准确含义

| 条件 | 必须同时满足的要求 |
| --- | --- |
| SELF | 仅已认证主体自身，issuer/sub精确映射；不得传他人user_id扩张。 |
| OPS | 仅脱敏健康元信息；不返回连接串、凭据、案件数据或内部堆栈；业务health契约尚未挂载。 |
| SOURCE | 仅同单位且已授权案件内来源元信息；授权依据按展示规则脱敏，不隐含读取来源原件。 |
| SOURCE_WRITE | 仅授权案件来源登记/同步；verified只能来自权威来源端口，数据管理员不能自报授权成功。 |
| INGEST | 仅同单位有效案件成员和已获准来源；上传及续传核验upload用途，清单导入核验import用途，后续分析另验analysis。上传者不因此获得原件下载、训练或审批权。续传状态/分片列表仍复用asset.upload。 |
| CASE_READ | 同单位有效案件成员、服务端解析对象归属、来源与读取用途有效；历史版本仍核验当前授权，不能跨案件。 |
| CASE_DOWNLOAD | 另有明确原件下载用途、对象/版本绑定与审计；只读页面权限不含原件下载；接口未实现前不放行。 |
| CASE_SEARCH | 仅授权集合建候选并在结果、分页、计数、缓存读取再次过滤；不允许先搜全库再仅隐藏页面。 |
| TASK_CREATE | 仅授权案件/来源的analysis用途，模型/任务版本可用；不自动批准模型能力或创建训练任务。 |
| TASK_CONTROL | 仅本人创建任务，或另有显式案件任务控制委托；取消仍按现有规则核验confirmation审批，重跑生成新版本。 |
| CASE_ANALYSIS | 仅授权案件analysis用途及允许能力；模型结果不是法律结论，原输入/结果历史不得覆盖。 |
| REVIEW | 仅获派复核的案件/对象；与该对象提交者/申请者不同内部user_id，保留证据和追加决策；review.perform不能替代approval.decide。 |
| SEAL | 仅获派业务审核员、固定证据清单/摘要和已批准seal申请；执行者不得作为该申请批准票，保留原件。 |
| REPORT_DRAFT | 仅授权案件形成可追溯草稿；不得用草稿状态绕过正式报告复核/导出。 |
| REPORT_GENERATE | 绑定当前任务/结果/策略版本且满足正式复核规则；生成与导出独立，不自动签发审批。 |
| REPORT_EXPORT | 仅本人或明确委托导出人、固定报告版本和有效report_export批准；交付前重新核验授权/审批/摘要。 |
| REQUEST_CASE | 仅本人负责案件和现有对象类型/purpose，申请不产生批准；禁止模型发布借用案件权限。 |
| REQUEST_CASE_READ | 仅本人发起或被明确委托的申请，仍须案件范围；不能因approval.read读取全部案件申请。 |
| APPROVAL_CASE_READ | 仅本人负责复核队列/申请且案件授权有效；敏感对象按独立读取许可检查。 |
| APPROVE_CASE | 仅review/seal/report_export/training_feedback/confirmation的适用案件对象；批准者非申请者/执行者，同人多账号不算独立人员。 |
| REVOKE_CASE | 仅获派审核员对职责内申请追加撤销和原因；不可删除历史，撤销后旧回执/产物下载重验。 |
| REQUEST_DATA | 仅本人负责的授权数据回流申请，purpose=training_feedback；没有训练用途授权时拒绝，不能自产来源许可。 |
| REQUEST_DATA_READ | 仅本人发起/受托的数据回流申请及其最小必要元信息；无通用案件内容读取许可。 |
| FEEDBACK_OWN | 仅本人申请的回流状态元信息；读取样本内容另需用途授权，不把analysis升级为training。 |
| FEEDBACK_REVIEW | 仅已分派复核对象的回流状态和脱敏依据；训练样本读取不在本次通用业务权限内。 |
| FEEDBACK_REQUEST | 仅来源允许training且批准training_feedback、脱敏和版本绑定有效；不得流入封存测试集。 |
| MODEL | 仅同单位模型元信息/制品操作；评测只用另行授权的脱敏研发数据。无案件原件读取权，公开模型信息不含凭据。 |
| MODEL_RELEASE | 仅发布执行者、固定制品摘要/评测版本、有效model_release组织级批准及回滚目标；执行者不得批准本次发布。现有组织级审批适配缺失，继续拒绝。 |
| INDEX | 仅同单位获派索引及固定版本的维护/切换；不含读取媒体内容；切换须独立变更复核、恢复点和维护窗口。 |
| REQUEST_MODEL | 仅算法管理员提交model_release组织级对象，case_id=null；不把case_id伪造成案件规避适配缺口。 |
| REQUEST_MODEL_READ | 仅本人申请或分派本人的组织级模型发布申请元信息；当前case-only读取不提供此能力。 |
| APPROVE_MODEL | 仅另行登记发布评审资格的算法管理员，且非该制品提交者/评测签记人/发布执行者；仅model_release组织级对象，当前适配缺失。 |
| REVOKE_MODEL | 仅获派发布复核人追加撤销组织级发布批准；回滚不重新激活旧批准，当前适配缺失。 |
| CONFIRM_MODEL | 仅本人执行的已批准模型发布，短时一次性确认绑定对象/动作/版本；confirmation不是批准，当前接口未挂载。 |
| CONFIRM_CASE | 仅本人执行的已批准案件敏感动作，一次性确认与对象/动作/版本绑定；不能签发审批或转交他人。 |
| POLICY_RETENTION | 仅PolicyCreate.kind=retention的同单位草稿/可读版本；不包含正式保存期限制定、删除原件或发布策略。 |
| POLICY_ALGORITHM | 仅kind=threshold/analysis的同单位草稿/可读版本；风险阈值值域须另有有效依据，不能自行启用。 |
| POLICY_BUSINESS | 仅kind=risk_taxonomy/review的同单位草稿/可读版本；业务标签/复核规则正式启用另行批准。 |
| AUDIT_READ | 仅有明确审计委托的同单位/案件日志；不返回原始内容/口令/令牌；跨单位、无案件组织级查询需专门能力且当前不放行。 |
| AUDIT_EXPORT | 仅审计委托、固定时间窗/字段/额度、独立report_export批准和脱敏制品；申请/执行的审计员不参与批准。导出作业不意味着业务内容写权限。 |
| REQUEST_AUDIT | 仅审计范围内日志导出申请，按现有operation对象绑定案件、purpose=report_export；不自创audit_export枚举。 |
| REQUEST_AUDIT_READ | 仅本人审计导出申请的状态元信息，仍保留案件/审计委托核验。 |

## 5. 单位、案件、对象、用途与分类

1. 主体来自已验证issuer/sub及内部用户映射；用户/单位启用、角色绑定未撤销且 `now < expires_at`。客户端自报角色、org_id、actor_id、approved不构成依据。一个用户的多账号仍按同一内部人员识别，不能凑独立批准票。
2. 平台健康仅OPS；本人身份仅SELF；模型/索引/策略为明确组织对象；案件资源要求有效case_membership及对象的真实case_id。对象标识先在受信查询中解析，不能通过传入另一case_id覆盖归属。当前目录部分权限被历史候选标成CASE不等于所有用途均是案件：组织级model_release仍case_id=null；case-only适配器不支持时503，不能伪造案件绕过。
3. 业务读取、下载、分析、训练、审计导出分别校验来源用途。审批purpose沿唯一契约 `review/seal/report_export/training_feedback/model_release/confirmation`，不新增枚举；审计导出申请按现有`operation`对象/案件和`report_export`处理。审批purpose不是来源purpose的自动替换，训练回流须另外取得来源`training`授权。
4. 正式分类制度和持久分类字段仍无有效输入。本方案不虚构“内部/秘密”等法定级别，不按数字或汉字顺序推定包含关系；建议使用经批准标签集合的精确包含关系。正式分类未知的内容动作继续拒绝；自建合成标签仅用于隔离测试。元信息脱敏未实施时，不得把CASE_READ/数据管理员等条件当作已可安全过滤返回。
5. 列表、分页游标、结果数量、导出下载、对象存储地址及缓存都应继承当前范围；不可凭旧游标、旧成功回执、旧批准或恢复出来的旧角色继续访问。历史事实保留并在访问时重验，撤销不删除审计。

## 6. 职责分离、兼任与审批规则建议

| 规则 | 具体建议 | 当前缺口 |
| --- | --- | --- |
| 同一对象的动态冲突 | 申请者、材料提交者、敏感动作执行者不得作为该申请的批准票；复核人不得复核本人提交的结论。 | 当前审批已拒绝申请者自批；执行者/制品提交者/评测签记者的完整关系还需实现，不能宣称已有。 |
| 高风险批准人数 | seal、report_export（含审计导出）、training_feedback、model_release建议2名独立批准者；review、confirmation建议1名独立批准者。 | `ApprovalRule`支持1/2，但本轮未配置。仅徐昌胜一人已确认，无法凑两人，正式敏感动作继续拒绝；两个账号不能代替两个人。 |
| 模型发布分工 | 申请/执行者为算法管理员；批准者为另行登记发布评审资格的算法管理员，并排除本制品提交者/评测签记者/执行者。业务审核员不自动获得组织级模型发布批准权。 | 组织级审批适配尚缺，不能把本表直接接入当前case-only审批。 |
| 静态兼任 | auditor不与任何可写业务/管理角色在同一活动授权配置共存；system_admin/algorithm_admin与案件调查或业务审核在同一活动配置不合并；data_admin可与case_investigator兼任，但仍不得自产来源许可/自批。其他兼任须显式版本化登记。 | 当前未提供活动角色选择机制；不能从HTTP任意角色头选身份，也不能先赋冲突角色再声称前端切换已隔离。 |
| 紧急访问 | 本版不设置管理员万能绕过或break-glass业务通道。 | 将来确有需要时另提可审计、限时、独立批准及恢复方案。 |
| RETURNED/撤销 | RETURNED不得按APPROVED消费；更正后重新申请并绑定新版本，保留旧记录。撤销追加事实并使旧批准/交付失效，不回写为从未发生。 | 当前终态/版本规则保留；正式允许组合仍待验证。 |

候选审批有效期建议1800秒，按用途可收紧，不得在无人批准时自动延长。此数值是待审建议，不改现有超时/令牌/原100包锁；master管理工具已锁定的300秒会话保持。批准人数、TTL、职责分离须一并审阅，不能只勾ALLOW忽略条件。

## 7. 策略类别、版本及撤销

`policy.manage`是业务规则草稿权限，不能当“系统权限管理”。按既有`PolicyCreate.kind`划分：retention归数据管理员；threshold/analysis归算法管理员；risk_taxonomy/review归业务审核员。`createPolicy`现仅接受DRAFT及空approval_id；本表不添加正式策略发布API，未挂载的发布流程按对应任务另建。正式保存期限、阈值和标签值仍需权威依据。

建议后续策略工件包含不可变版本、文件摘要、适用单位、246格及全部条件、职责冲突、分类/用途映射、批准人与生效区间；分发单元要么完整可验证要么拒绝，不能只更新角色表。策略版本变更不可修改旧审计。旧版本只能用于解释历史，不能恢复已撤销授权；回切版本也须承接当前撤销代际。

候选撤销验收：以权威事务提交成功为t0，后续新请求不得使用t0前正向缓存；提出“t0至新请求可观察拒绝最大5秒”的待测上限，不把平均值或95分位当上限。未启动、执行节点前、敏感提交前及产物交付前都应重验身份/角色/案件/来源/审批/策略版本。正在进行且已经读取的字节无法追溯收回；最后一次重读与副作用提交之间的竞态须通过事务/版本条件和受控失败测试解决，不能声称零延时撤销。当前代码仅证明最终事实重读范围，无完整5秒或长任务原子性验收。

## 8. 与现有代码的差距及实施边界

| 后续工作包 | 复用 | 实际还需做什么 |
| --- | --- | --- |
| RP1 规则工件与资格读取 | PermissionPolicy、0006受限功能事实、原六角色/权限目录 | 按审定版本装载规则、读取受信角色/资格与冲突事实、严校246格/条件；当前PermissionFact只有eligible和摘要，不能假称已提供全部角色/目的/对象事实。若需端口或数据库扩展，先形成具体计划及增量迁移。 |
| RP2 对象条件 | resource_scope、AuthorityProvider、RuleProvider和现有来源/对象检查 | case、own-request、任务委托、policy.kind、组织级模型审批、脱敏投影及执行者冲突逐项落地。不能在只有principal+permission的全局guard里假装已判断对象/用途。 |
| RP3 撤销及后台 | 现有最终事实重读、worker重验、版本/幂等和追加审计 | 版本发布原子性、无正向缓存、事务提交和交付重验、故障/并发撤销测量及回切不复活授权。 |
| RP4 回归与采用 | 42操作×4拒绝、真实SQL/对象/消息资源及既有CI | 每一建议允许格分别测满足条件允许和逐项不满足拒绝；职责冲突、组织模型/案件、policy.kind、防自批/伪双人；31未挂载操作实现后才有HTTP结论。共享采用另设维护窗口。 |

本批只交付规则方案、本人步骤和资料一致性验证；不写业务代码/迁移，不注入生产或研发共享ALLOW，也不自动进入T015。

## 9. 需要审阅的六项决定

- **PR01 六角色全部246格、具体对象/用途和策略kind范围**：按本文逐条件采用为后续隔离实现输入；不是直接启用。当前：`CONFIRMED_FOR_NEXT_ISOLATED_IMPLEMENTATION_INPUT_ONLY`。
- **PR02 职责分离与两名独立批准人**：seal/report_export/training_feedback/model_release需2名独立批准人；review/confirmation需1名，均不含申请/执行人；人员不足拒绝。当前：`CONFIRMED_FOR_NEXT_ISOLATED_IMPLEMENTATION_INPUT_ONLY`。
- **PR03 数据分类与用途映射**：不编造正式级别；仅经确认的标签集合精确匹配，未知拒绝；合成夹具可独立开发。当前：`PENDING_AUTHORITY_INPUT`。
- **PR04 审批TTL与撤销时效**：候选审批TTL1800秒；无正向跨请求缓存；撤销提交至新请求拒绝上限5秒候选，节点及提交前重验；现有300秒管理会话保持。当前：`CONFIRMED_FOR_NEXT_ISOLATED_IMPLEMENTATION_INPUT_ONLY`。
- **PR05 共享配置、0006和策略采用及维护窗口**：隔离实现/恢复通过后另提精确安装、备份和回切清单；不随源码同步执行。当前：`NOT_AUTHORIZED_BY_DOCUMENT_SYNC`。
- **PR06 T013保护、本人接管、独立介质及离线恢复**：见t013-owner-action-checklist；当前保留旧配置决定不等于真实交接通过。当前：`PENDING_OWNER_ACTIONS`。

2026-10-20用户已明确回复“认可作为下一批隔离实现输入”，仅覆盖PR01/PR02/PR04；机器表保存原回答和范围。PR03正式分类仍未知，PR05共享采用未批准，PR06按本人步骤分别验证。下一批先细化实际端口/对象条件和实施计划；此确认不批准未形成的实施计划、不启用ALLOW，不代表T013接管或整任务验收。

## 10. 操作到权限与本轮验证

下表直接取唯一契约/现有覆盖矩阵的operationId、方法、完整路径及当前挂载状态；同一权限码可对应多个操作，但所有对象条件仍逐操作核验。表内“已挂载”仅指现有研发入口，不是本方案已经生效。机器表记录四份输入摘要，逐项一致性由本批验证报告登记。

| operationId | 方法/完整路径 | 权限码 | 当前入口 |
| --- | --- | --- | --- |
| cancelTask | POST `/api/v1/analysis/tasks/{id}/cancel` | task.cancel | 已挂载；方案未生效 |
| completeUpload | POST `/api/v1/uploads/{id}/complete` | asset.upload | 已挂载；方案未生效 |
| createImport | POST `/api/v1/imports` | asset.import | 已挂载；方案未生效 |
| createPolicy | POST `/api/v1/policies` | policy.manage | 已挂载；方案未生效 |
| createReport | POST `/api/v1/reports` | report.generate | 未挂载；无HTTP完成结论 |
| createReportDraft | POST `/api/v1/reports/drafts` | report.draft | 未挂载；无HTTP完成结论 |
| createReview | POST `/api/v1/reviews` | review.perform | 已挂载；方案未生效 |
| createSource | POST `/api/v1/sources` | source.manage | 未挂载；无HTTP完成结论 |
| createTask | POST `/api/v1/analysis/tasks` | task.create | 未挂载；无HTTP完成结论 |
| createUpload | POST `/api/v1/uploads` | asset.upload | 已挂载；方案未生效 |
| decideApproval | POST `/api/v1/approvals/{id}/decisions` | approval.decide | 已挂载；方案未生效 |
| decidePropagationEdge | POST `/api/v1/propagation/edges/{id}/decisions` | review.perform | 未挂载；无HTTP完成结论 |
| devLogin | POST `/api/v1/auth/login` | development.login | 未挂载；无HTTP完成结论 |
| downloadAsset | GET `/api/v1/assets/{id}/content` | asset.download | 未挂载；无HTTP完成结论 |
| downloadAuditExport | GET `/api/v1/audit/exports/{id}/content` | audit.export | 已挂载；方案未生效 |
| downloadReport | GET `/api/v1/reports/{id}/content` | report.export | 未挂载；无HTTP完成结论 |
| exportAudit | POST `/api/v1/audit/exports` | audit.export | 已挂载；方案未生效 |
| extractClaims | POST `/api/v1/claims/extract` | claim.analyze | 未挂载；无HTTP完成结论 |
| getApproval | GET `/api/v1/approvals/{id}` | approval.read | 已挂载；方案未生效 |
| getAsset | GET `/api/v1/assets/{id}` | asset.read | 未挂载；无HTTP完成结论 |
| getAuditExport | GET `/api/v1/audit/exports/{id}` | audit.export | 已挂载；方案未生效 |
| getCurrentUser | GET `/api/v1/auth/me` | identity.read | 已挂载；方案未生效 |
| getFeedback | GET `/api/v1/feedback/samples/{id}` | feedback.read | 已挂载；方案未生效 |
| getFirstSource | GET `/api/v1/clusters/{id}/first-source` | origin.read | 已挂载；方案未生效 |
| getForensics | GET `/api/v1/analysis/tasks/{id}/forensics` | task.read | 已挂载；方案未生效 |
| getImport | GET `/api/v1/imports/{id}` | asset.import | 已挂载；方案未生效 |
| getIndex | GET `/api/v1/indices/{id}` | index.manage | 未挂载；无HTTP完成结论 |
| getModelHealth | GET `/api/v1/models/{id}/health` | model.manage | 未挂载；无HTTP完成结论 |
| getModelOperation | GET `/api/v1/model-operations/{id}` | model.read | 已挂载；方案未生效 |
| getPolicy | GET `/api/v1/policies/{id}` | policy.read | 已挂载；方案未生效 |
| getPolicyDefinition | GET `/api/v1/policies/{id}/definition` | policy.read | 已挂载；方案未生效 |
| getPropagation | GET `/api/v1/propagation/{cluster_id}` | propagation.read | 已挂载；方案未生效 |
| getReport | GET `/api/v1/reports/{id}` | report.read | 未挂载；无HTTP完成结论 |
| getReview | GET `/api/v1/reviews/{id}` | review.read | 已挂载；方案未生效 |
| getReviewContext | GET `/api/v1/analysis/tasks/{id}/review-context` | review.read | 已挂载；方案未生效 |
| getRiskFindings | GET `/api/v1/analysis/tasks/{id}/risk-findings` | task.read | 已挂载；方案未生效 |
| getSearchJob | GET `/api/v1/search/jobs/{id}` | asset.search | 未挂载；无HTTP完成结论 |
| getSource | GET `/api/v1/sources/{id}` | source.read | 已挂载；方案未生效 |
| getTask | GET `/api/v1/analysis/tasks/{id}` | task.read | 已挂载；方案未生效 |
| getTaskEvidence | GET `/api/v1/analysis/tasks/{id}/evidence` | evidence.read | 已挂载；方案未生效 |
| getTaskExecution | GET `/api/v1/analysis/tasks/{id}/execution` | task.read | 已挂载；方案未生效 |
| getTimeline | GET `/api/v1/assets/{id}/timeline` | asset.read | 已挂载；方案未生效 |
| getUploadStatus | GET `/api/v1/uploads/{id}` | asset.upload | 已挂载；方案未生效 |
| health | GET `/api/v1/health` | health.read | 未挂载；无HTTP完成结论 |
| issueOperationToken | POST `/api/v1/operation-tokens` | operation.confirm | 未挂载；无HTTP完成结论 |
| listApprovals | GET `/api/v1/approvals` | approval.read | 已挂载；方案未生效 |
| listAssets | GET `/api/v1/assets` | asset.read | 未挂载；无HTTP完成结论 |
| listAuditEvents | GET `/api/v1/audit/events` | audit.read | 已挂载；方案未生效 |
| listEvaluations | GET `/api/v1/model-evaluations` | model.read | 未挂载；无HTTP完成结论 |
| listModels | GET `/api/v1/models` | model.read | 未挂载；无HTTP完成结论 |
| listPendingReviews | GET `/api/v1/reviews/pending` | review.read | 已挂载；方案未生效 |
| listPolicies | GET `/api/v1/policies` | policy.read | 已挂载；方案未生效 |
| listReviews | GET `/api/v1/reviews` | review.read | 已挂载；方案未生效 |
| listSources | GET `/api/v1/sources` | source.read | 已挂载；方案未生效 |
| listTaskEvents | GET `/api/v1/analysis/tasks/{id}/events` | task.read | 已挂载；方案未生效 |
| listTaskNodes | GET `/api/v1/analysis/tasks/{id}/nodes` | task.read | 已挂载；方案未生效 |
| listTasks | GET `/api/v1/analysis/tasks` | task.read | 未挂载；无HTTP完成结论 |
| listUploadParts | GET `/api/v1/uploads/{id}/parts` | asset.upload | 已挂载；方案未生效 |
| putUploadPart | PUT `/api/v1/uploads/{id}/parts/{part_no}` | asset.upload | 已挂载；方案未生效 |
| recordEvaluation | POST `/api/v1/model-evaluations` | model.evaluate | 未挂载；无HTTP完成结论 |
| registerModel | POST `/api/v1/models` | model.manage | 未挂载；无HTTP完成结论 |
| requestApproval | POST `/api/v1/approvals` | approval.request | 已挂载；方案未生效 |
| requestFeedback | POST `/api/v1/feedback/samples` | feedback.request | 未挂载；无HTTP完成结论 |
| rerunTask | POST `/api/v1/analysis/tasks/{id}/rerun` | task.rerun | 未挂载；无HTTP完成结论 |
| revokeApproval | POST `/api/v1/approvals/{id}/revoke` | approval.revoke | 已挂载；方案未生效 |
| rolloutModel | POST `/api/v1/models/{id}/rollouts` | model.release | 未挂载；无HTTP完成结论 |
| sealEvidence | POST `/api/v1/evidence-packages/{case_id}/seal` | evidence.seal | 未挂载；无HTTP完成结论 |
| searchImage | POST `/api/v1/search/image` | asset.search | 未挂载；无HTTP完成结论 |
| searchImageRegion | POST `/api/v1/search/image-region` | asset.search | 未挂载；无HTTP完成结论 |
| searchVideo | POST `/api/v1/search/video` | asset.search | 未挂载；无HTTP完成结论 |
| switchIndex | POST `/api/v1/indices/{id}/switch` | index.manage | 未挂载；无HTTP完成结论 |
| syncSourceAuthorization | POST `/api/v1/sources/{id}/authorization/sync` | source.manage | 已挂载；方案未生效 |
| verifyClaim | POST `/api/v1/claims/{id}/verify` | claim.analyze | 未挂载；无HTTP完成结论 |

本轮状态与资料校验见[方案/本人步骤验证](../00-project/validation/t014-rule-proposal-document-review.json)，本人操作见[T013操作清单](../03-development/t013-owner-action-checklist.md)。当前170任务的C/R计数保持：90条已验证子步骤、621条剩余工作、整任务验收0；本方案是R01内的资料进展，不伪增业务完成数。

技术依据：最小权限、默认拒绝、每请求重验及属性/关系条件参考[OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)。上述具体角色分工、批准人数、TTL和5秒候选上限是项目建议，并非OWASP规定或正式公安业务制度。临时管理员退出参考[Keycloak官方说明](https://www.keycloak.org/server/bootstrap-admin-recovery)，不替代共享环境实测。
