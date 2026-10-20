# 剩余11类接口的工程实现与正式边界

<!-- T016_NATIVE_FINAL_EVIDENCE -->

已核验的原生隔离源码为`b1b79bfb32b7959e63f302bbef22d32e22dc0b8f`：[T014实际报告](../../00-project/validation/t014-permissions-report.json)713项、[T015实际报告](../../00-project/validation/t015-data-scope-report.json)131项、[T016实际报告](../../00-project/validation/t016-operation-token-report.json)187项，均无失败、错误或跳过；三个独立故障探针均按预期识别断言失败，Ruff、格式和mypy检查通过。三套用例有重叠，数量不相加为唯一测试数或170项任务完成数。此结论限Linux／py310／CPU隔离研发，不是正式验收。

托管CI另计：最后观察为run`39478665682`、提交`1b76a46ad52d9f67f549ee59da685ab79e6b9265`，身份检查332项通过，engineering仍在运行；不宣称最终源码的托管CI通过。后续状态与精确报告摘要以[阶段进度](../../00-project/validation/t016-development-progress.json)及其最新actual记录为准，源码同步、数据库采用和正式授权分别登记。

本批承接用户2026-10-14/15的继续实施授权。已增加代码、真实数据库访问、版本约束、适配边界和专项测试；本批完整验证及同步结果以[业务验证报告](../../00-project/validation/business-foundation-report.json)和[同步回执](../../00-project/server-sync-receipt.json)绑定的实际源码为准。当前文件不提供正式生产冻结或完整业务验收决定。

唯一业务结构源为[OpenAPI](../../03-api/openapi.yaml)：累计73个候选外部操作、102个组件。2026-10-21的T016增量加入issueOperationToken后，独立业务工程实际挂载43个外部操作和1个内部推理入口，30个契约操作仍未挂载；既有PoC另有与候选契约匹配的health。实际挂载的操作可能仍需要权威提供方，默认503不表示已经接入。34类能力结构不能当34个真实模型已实现。运行时/openapi.json从唯一源选取实际挂载操作，避免发布尚未实现的路径或仅展示通用dict字段。

| 缺口 | 本批实际代码范围 | 仍未完成的正式或完整业务内容 |
| --- | --- | --- |
| IF-G02 | 案件内审批申请、列表、聚合详情、决定、撤销；有效期、当前对象/结果/来源、独立审批人、强ETag、原子幂等和追加历史 | 实际审批规则/角色、组织级模型审批及正式制度；未配置规则不批准 |
| IF-G03 | 待复核工作台、复核记录列表/详情、聚合版本上下文、追加复核及证据绑定；无结果或来源受限明确显示不可用 | 正式复核阈值及RETURNED后继流程；不由一条意见自动改变正式报告资格 |
| IF-G04 | 读取真实反馈请求，交叉核验用途审批/绑定/撤销；没有真实数据集来源时拒绝APPLIED成功状态 | 实际反馈申请生产器、用途授权、分割清单和回流执行器；封存测试集不得回流 |
| IF-G05 | 发布操作读取适配端口、组织权限、操作/发布包/模型版本绑定及终态检查 | 实际部署平台的操作账本、灰度/回滚执行和制品/许可/健康规则 |
| IF-G06 | 真实审计列表、导出作业申请、受控执行器、状态及固定产物读取；Range每次重核审批、期限、案件、版本和摘要；失败不报告READY，孤立文件留下恢复记录 | 现场脱敏/保存制度、正式用途审批、生产对象存储和持续执行器部署；本批私有文件为隔离研发目标 |
| IF-G07 | 当前用户查询适配、主体/单位一致性，案件范围与数据库现行成员交集；策略/模型组织权限与案件权限分开 | 正式身份平台、角色/案件映射、令牌撤销及新鲜度协议；无提供方无模拟登录 |
| IF-G08 | 来源清单/详情和条件同步；授权状态/用途/版本只从显式权威提供方取得，同版本变内容拒绝，失效后业务使用拒绝 | 正式授权机构、材料用途依据和权威失效同步协议；客户端登记不等于验证 |
| IF-G10 | 导入已登记的同案件/同来源固定对象，真实字节/摘要/媒体元数据核验、原子导入账本、输入引用保存及状态读取；未知对象拒绝 | 外部平台首次下载、身份签名、网络、游标和重试协议；第三方适配端口不等于实际平台接通 |
| IF-G11 | 指定运行的节点/事件读取，当前控制状态，原子租约/栅栏及旧worker拒绝；取消请求/停止确认、域事件和outbox事务；历史结果不覆盖 | 全业务DAG、真实节点、完整跨模块消息生产/消费、取消信号部署及死信运维；超时不冒充进程已停止 |
| IF-G12 | 策略草稿登记/唯一版本/组织读取，不可变私有参数定义保存，版本/摘要固定引用和强ETag；控制幂等TTL/导入/租约限额须显式配置 | 真实正式参数、批准/激活/撤销流程和生产策略治理；DRAFT或已有APPROVED字段不自动意味着正在生效 |
| IF-G13 | 独立服务身份入口，34能力请求/响应Schema，路径/请求/任务/运行/模型版本/期限/固定对象/来源一致性；执行后重核取消与撤销 | 实际34能力执行器、发布包/许可、逐能力语义校验器和评测；缺能力503；mock或缺批准包的SUCCEEDED拒绝 |

## T016操作令牌的当前补充

T016增加`POST /api/v1/operation-tokens`；实现快照、修复及最终受测版本按[阶段进度](../../00-project/validation/t016-development-progress.json)及其actual报告核对，不用一个过去的提交代指最终版本。公共请求／响应和Idempotency-Key保持原结构。案件来自服务端批准记录，首批仅支持显式规则确定的`task + seal → sealEvidence`；签发重核功能、案件、申请主体、对象／run／result、来源用途及当前独立批准链。独立HMAC密钥用于重建同键原凭据，数据库只保存摘要和非秘密绑定，不将明文响应放入通用回执。

内部消费接收调用方已授权的精确动作根Connection，在同一事务核验、一次消费及成功审计，与调用方适用业务写入一起提交或回滚，不自行commit、不新增公共消费端点。**sealEvidence真实HTTP消费者仍未挂载**；内部动作目录不是业务权限。AuditExport公共结构与现有导出消费者保持原状态，不能声称其已经使用该令牌。

完整六角色链的隔离HTTP签发和适用事实测试已有证据；业务测试、质量失败、修复和重跑分别留存于阶段进度。43项四类拒绝、T014／T015／T016全量门禁、批准／来源／人员／结果及合成职责撤销组合、CI和源码同步的最终结论，分别从最新actual报告核对受测源码及结果，旧通过和修复但未重跑都不自动升级为当前通过。单资产任务来源授权版本／状态／用途／期限／行版本已纳入快照摘要，公共及数据库列不变，不宣称多输入来源闭包；合成职责撤销不代表正式跨人委托。真实确认／封存执行主体规则、实际不足5秒的可能截止及严格当前密钥轮换见[安全边界](../../08-security/t016-operation-token-boundaries.md)。Python候选继续暂缓，正式策略／共享采用和整任务验收未因本增量完成。

## 可调用入口与契约导航

具体参数、状态码、权限和字段以[逐操作目录](../../03-api/detailed-interface-index.md)为准。新增18个操作为：listApprovals、getApproval、revokeApproval、listReviews、getReview、getReviewContext、listPendingReviews、getAuditExport、downloadAuditExport、getFeedback、getModelOperation、getSource、syncSourceAuthorization、getPolicy、getPolicyDefinition、listTaskNodes、listTaskEvents、getTaskExecution。另实际实现了已有requestApproval、decideApproval、createReview、exportAudit、getCurrentUser、listSources、createImport、getImport、createPolicy、listPolicies、listAuditEvents、cancelTask。

复核提交的If-Match来自getReviewContext；审批决定/撤销来自getApproval聚合。取消的If-Match来自getTaskExecution，202的status_url也是当前控制入口。不可变历史getTask不因取消被更新成新的状态；result_available仅说明登记的快照存在，不说明算法执行或准确率通过。

分页按UUID键有界读取，签名游标绑定主体、单位、案件、过滤、页大小和账本版本；任务工作台还绑定结果摘要和复核版本。伪造/错范围422，账本变化409。控制写入的幂等按主体/操作/请求摘要保存，重放保留首次回执；当前状态需再GET，回执不能充当现行审批或授权。control_ttl_seconds、node_lease_seconds、max_import_entries未配置时相关写入/执行拒绝，不能沿用上传期限当正式控制制度。

## 数据库与恢复边界

最初本批0003版本为62业务表、825字段；后续目录迁移到0010为64表849列，本次0011完整隔离结构为64表861列，operation_token由15列扩为27列。历史版本计数与摘要分别保留。当前共享库和现有预览库未安装0011，源码同步不证明数据库升级。[0003_control_integrity.sql](../../../backend/business_migrations/0003_control_integrity.sql)继续保留原增量约束，不重写原0001/0002：审批决定绑定案件/单位/策略与有效主体，复核证据精确绑定task/run/result及唯一引用，导出READY必须带固定产物元数据，策略定义修改必须新建版本。0011字段、legacy拒绝及向前修复边界见[操作令牌数据库扩展](../../04-database/operation-token-extension.md)；不能拿初始化SQL升级现有库。

审计导出使用规范JSON和私有固定文件版本；文件写入但数据库提交失败时保留孤立对象记录，不生成成功账本。参数定义以组织、版本和内容摘要固定在仓库外的私有目录；发布先写临时文件并同步，再原子登记，读取重算摘要；此存储不替代生产WORM、整盘备份、离线包或正式灾备验收。

所有测试只使用自建PNG、合成组织/案件/主体、测试规则和明确不执行算法的协议夹具。应用工厂没有开启假身份或假审批的环境开关；测试提供方不由默认启动配置装载。Linux测试在独立源码副本及随机隔离PostgreSQL目标运行，既有7服务和其他项目不因测试重启。

## 启动与接入条件

`business_app.main.create_app`接收BusinessSettings及显式提供方。AuthorityProvider负责真实认证、功能/案件和来源用途；RuleProvider负责审批、复核、导出和取消规则；IdentityDirectory负责当前权限声明；SourceSynchronization负责权威授权更新；DeploymentOperations读取真实部署操作；FileDefinitions或DefinitionProvider提供固定参数定义；ServiceAuthority/BackendRegistration接入独立工作负载身份与实际模型。缺失依赖返回不可用，不能为通过验收注入测试实现。

托管CI验证自建数据的数据库/HTTP/故障边界，服务器同步验证文件及提交一致；源码同步不是新业务栈已上线。正式身份/规则/数据/平台/GPU/现场条件继续在[13项台账](../../03-api/interface-gap-register.md)开放，逐项联调并形成有效验收决定后才能关闭。
