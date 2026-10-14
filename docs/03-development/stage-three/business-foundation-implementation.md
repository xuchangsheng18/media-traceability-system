# 首批业务基础实际实现及验收边界

本批依据用户2026-10-14认可的[详细计划](business-interface-implementation-plan.md)执行。实际结果分别见[业务验证报告](../../00-project/validation/business-foundation-report.json)、[恢复报告](../../00-project/validation/business-recovery-report.json)、[类型报告](../../00-project/validation/stage-three-python-types-report.json)及[GitHub实际检查](../../00-project/validation/github-actions-report.json)。报告的提交、工作区是否有未提交修改、执行平台和范围必须一起阅读；旧CI不能证明新代码。

## 实际代码与数据结构

| 交付 | 代码入口 | 已实现的行为 |
| --- | --- | --- |
| 独立迁移 | [runner](../../../backend/business_migrations/runner.py)、[0001](../../../backend/business_migrations/0001_business_baseline.sql)、[0002](../../../backend/business_migrations/0002_upload_result.sql) | 0001保留原62表824字段；0002新增upload_session.duplicate_of，当前62表825字段；账本在mt_meta，不计入业务表。摘要漂移、无账本旧schema及中途失败均拒绝/回滚；迁移仅允许显式mt_business_目标。 |
| 独立业务应用 | [应用工厂](../../../backend/business_app/main.py)、[授权边界](../../../backend/business_app/auth.py)、[事务/RLS](../../../backend/business_app/db.py) | 与原backend/app的PoC分开；业务LOGIN拒绝superuser/BYPASSRLS，事务设置当前actor/org并核验现行案件成员关系；未配置权威提供方503、无效凭证401、不可见资源404。 |
| 对象存储 | [私有固定版本适配器](../../../backend/business_app/objects.py) | 自有研发文件目录、随机对象/固定版本、服务端摘要、私有权限和实际字节核验；提交失败或并发未登记对象保留恢复标记，不自动删数据。当前适配器为私有文件，尚未验证业务S3适配器、WORM或管理员防篡改。 |
| 上传与消息 | [上传路由](../../../backend/business_app/uploads/router.py)、[账本](../../../backend/business_app/uploads/repository.py)、[校验worker](../../../backend/business_app/uploads/worker.py)、[消息泵](../../../backend/business_app/uploads/messaging.py) | 连续分片/总量/完整摘要、到期、幂等及实际接收进度；complete原子提交VALIDATING与outbox。真实RabbitMQ持久消息确认后登记published，消费提交后确认，重复消费不重复建资产。消息泵为单次执行边界，常驻调度/完整事件总线尚未实现。 |
| 历史结果 | [快照仓储](../../../backend/business_app/history/repository.py)、[投影](../../../backend/business_app/history/projection.py)、[7读取路由](../../../backend/business_app/history/router.py) | 按task/run/result追加不可变快照、规范JSON摘要、当前权限/来源和固定对象版本核验；精确未命中404，不回退最新；响应版本头与投影一致。 |

仓库[唯一API源](../../03-api/openapi.yaml)为55操作85响应/请求Schema；其中本批独立业务应用实际挂载12操作（5上传、7历史），原PoC健康检查另计1个研发部分实现。其余操作仍为契约设计。62表完成冷迁移不代表62表DAO、170业务任务、34算法能力或全DAG已实现。

## 实际HTTP范围

服务根为`/api/v1`。上传：POST `/uploads`（201）、PUT `/uploads/{id}/parts/{part_no}`（200）、GET `/uploads/{id}`、GET `/uploads/{id}/parts`、POST `/uploads/{id}/complete`（202）。202表示受理，只有实际拼接字节/摘要及媒体解析检查成功后才创建VALID资产。当前媒体校验支持PNG/JPEG；其他媒体拒绝，尚非视频/音频全链路或病毒扫描验收。研发大小、分片大小、期限、像素限制为实现边界，不是正式业务阈值或20/100并发目标。

历史读取：GET `/analysis/tasks/{id}`、`/analysis/tasks/{id}/risk-findings`、`/analysis/tasks/{id}/forensics`、`/analysis/tasks/{id}/evidence`、`/assets/{id}/timeline`、`/clusters/{id}/first-source`、`/propagation/{id}`。任务路径必须成组提供`history[run_version]`和`history[result_version]`；其他3路径还需`history[task_id]`。半组、未知history键或重复版本键422。省略history只选择同案件/路径已有的最新快照；ranking_id须匹配同一首发快照。当前所选实现不支持额外分页/过滤参数，显式拒绝，不能默默忽略。详细说明见[历史协议](../../03-api/historical-result-reading.md)和[逐操作导航](../../03-api/README.md)。

## 快照格式与真实业务结果边界

新写入[run-result 0.2](../../../schemas/workflow/run-result.schema.json)含api_projections。projection_refs的RFC6901指针指向同一快照的`/api_projections/N/response`，映射版本为`history-api-projection/1`；指针不是ObjectRef。完整快照规范化为UTF-8、排序键、紧凑分隔、保留Unicode且禁止NaN/Infinity后计算SHA-256。数据库summary存放明确的schema_id与snapshot封套，数据库拒绝UPDATE/DELETE/TRUNCATE。

旧[0.1 Schema](../../../schemas/workflow/run-result.v0_1.schema.json)按原字节保留供识别；没有登记且能验证的0.1投影映射时503，未编造兼容成功。持久化边界允许本批已验证的draft_only结果，不准入reviewable/formal_eligible。主任务对象必须属于input_refs，同一运行的input_sha256不可变；所有嵌套固定对象引用、资产来源及证据绑定重新核验。尚未建立能力/普通媒体结果生产事务时，非空capability_outputs/ordinary_media_outputs明确拒绝，不能借读取基础伪造生产器。首发ranking及候选与结果原子登记并绑定同一案件/簇/任务/版本；候选数量、连续名次、簇成员和证据受校验。非空证据/候选需要真实同版本证据生产事务，该生产器不在本批。测试使用自有生成图片、独立来源/身份夹具与“analysis-not-executed”快照，7读取测试证明存储、选择和授权行为；空候选/节点标明未执行算法，不能作为首发、风险、取证或传播算法结论。

## 运行、验证和恢复

实际Linux验证采用用户指定Miniforge py310 Python3.10.22与原100包锁；类型工具另设12包精确摘要锁。共享Docker数据卷不足且影响其他项目，本批没有在共享引擎构建/重建新栈。测试PostgreSQL16.15位于宿主机独立工具环境、仅监听回环独立端口；消息测试使用本项目RabbitMQ的独立测试用户/vhost/队列。测试集不连接原PoC数据库，测试库和角色每次随机建立并清理。共享Docker业务栈正式部署尚未完成。

统一验证入口：项目py310执行`scripts/verify_business_foundation.py run`；配置须显式给出`MT_BUSINESS_TEST_ADMIN_DSN`、`MT_BUSINESS_TEST_BROKER_URL`、PostgreSQL16恢复工具目录`MT_BUSINESS_PG_BIN`，或由仓库外私有运行配置提供。缺配置、PoC目标、无匹配实际测试结果均失败，不记PASS。`failure-probe`只有实测到单个受控断言失败才返回预期码1，其他异常返回2；CI分别核验退出码。`scripts/dev.py test`包含既有测试、业务验证和前端测试，不能只运行旧测试宣称新业务通过。

恢复测试实际执行pg_dump/pg_restore到另一随机隔离空数据库、复制私有固定版本对象，核对上传/分片/对象/资产/两次运行快照和迁移账本。恢复后的业务LOGIN/RLS读取两份精确快照并核验对象真实摘要。只证明本批自有数据恢复，不覆盖共享Docker离线整盘备份、生产PITR、异地恢复、密钥或模型恢复。

GitHub托管CI新增独立PostgreSQL/RabbitMQ服务与业务验证步骤，沿用精确镜像摘要。CI中的字面凭证仅用于当次Runner的自有测试服务，不是正式身份、平台Secret或现场凭证。托管成功必须以该源码SHA实际工作流为准。

## 仍需实际条件

IF-G01/IF-G09只按所选技术范围判断，完整正式关闭仍依赖权威身份/来源、业务媒体/结果生产和最终验收；其他11项依[总计划](foundation-implementation-plan.md)继续。共享数据卷扩容/完整恢复、真实责任人、私有分支保护套餐/规则、Runner/Secret正式治理、桌面当前会话实际规则边界、现场/离线/Windows原生/GPU适用范围和有效验收决定均未完成。源码同步、CLI加载或CPU夹具不能替代这些条件。

本轮审查记录：并发重复对象恢复标记、worker提交失败恢复、永久损坏对象拒绝、JPEG完整解码、主任务/同运行输入一致性、嵌套版本/引用授权、跨任务最新选择、ranking不可重绑及duplicate_of撤销后隐藏均有回归检查。读取资产/簇的最新快照按实际入库时间选择，不跨任务比较各自run计数。首次完整读写/恢复证据仍为自有测试数据。

容量复查（2026-10-14）：实际Docker数据文件系统13%使用、约644GiB可用，已满足5GiB研发构建保护值。此前容量不足为早期事实；本会话未执行扩容/停机，实际维护记录、整盘备份及正式恢复仍未核验，不能填作维护验收通过。
