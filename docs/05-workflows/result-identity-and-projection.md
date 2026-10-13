# 处理结果身份与读取投影

本文将36条需求的技术语义复核落实为处理、持久化和读取规则。它是实现输入，覆盖现有契约与明确的待补字段；未把建议字段写成当前已可调用接口。来源为[逐需求复核](../00-project/requirement-semantic-review.md)、[业务OpenAPI](../03-api/openapi.yaml)、[34能力结构](../03-api/inference-openapi.yaml)和[数据库表目录](../04-database/table-catalog.json)。正式策略与实际联调分别记录。

## 唯一来源与身份

业务请求/响应结构以OpenAPI为源，模型结构以schemas/model为源，数据库物理字段以table-catalog/DDL为源。普通媒体解码、探测、摘要、存储、权限和编排不凭空成为模型能力。任务卡/主追踪中未绑定API或表的七条需求保持原值，补充映射只说明技术路径。

| 身份 | 技术含义与一致性要求 | 当前结构依据 |
| --- | --- | --- |
| org_id / case_id | 由服务端身份范围确定；不因UUID或文件摘要相同获得跨案件访问权 | 数据库各案件域表；Task/Asset的case_id |
| asset_id | 特定案件/来源/用途下的原件或派生资产；不同于内容标识、簇标识或对象键 | Asset；media_asset |
| ObjectRef | bucket/key/version_id/SHA-256固定指向读取的字节版本；同名新版本不改变旧引用 | ObjectRef；object_version |
| task_id / run_version | 逻辑任务与一次执行；重算新run_version，旧租约和旧运行不得写新执行 | Task；task_run/task_node_run |
| result_version | 一次发布的结果集合版本；复核/报告绑定该版本，不能将当前结果隐式代替历史 | VersionBinding；task_result |
| request_id / attempt / fencing | 一次调用追踪与执行提交权；重复消息不能重复产生有效效果 | 模型公共封套；租约/运行记录及相应协议 |
| model/preprocessing/mapping/index/policy版本 | 算法、前处理、原件坐标/时间、索引与规则解释均固定 | 模型公共封套；对应DB列/API字段；未有唯一投影的项仍待补 |
| search_id / ranking_id / cluster_id | 检索作业、不可变排序批次与高可信内容簇分别标识，不能互换 | SearchJob；FirstSource；content_cluster/cluster_member |

身份字段部分出现在DB或模型响应、部分出现在业务投影。完整内部追踪存在不代表每个公开读取已提供历史选择；当前未覆盖处按下表处理。

## 接收、处理与发布

1. 当前来源/用途和资产VALID状态满足后，业务入口受理并返回task_id或search_id；202只表示受理。
2. 调度器创建固定dag_version的运行；每个节点记录输入ObjectRef、摘要、映射、模型/索引/规则版本及当前租约。普通媒体节点与模型节点分开。
3. 响应核验request/task/run/capability身份、状态、结构和对象版本。FAILED/SKIPPED/DEFERRED/NOT_SUPPORTED不得形成正式候选；缺失模态及影响区间保留。
4. 应用层按源模型payload转换为业务结果。转换登记字段来源、单位、枚举解释、缺失/失败处理，不能直接把通用findings当全部专用payload。
5. 条件事务校验当前案件、运行和fencing后写结果/证据/关联，再发布一个完整result_version。原模型响应或固定对象引用保留；取消、过期或旧运行的提交拒绝并记录。
6. 用户读取指定身份和有权版本。尚无历史选择的API只能解释为现有投影，正式历史读取按IF-G09补契约。复核、批准和正式报告不得自动继承新结果。

这六步是完整业务的实现要求。当前PoC只验证其中部分机制，不据此登记完整DAG或业务事务已完成。

## 本轮复核定位的投影差异

| 事项 | 已有结构能表达什么 | 实现前须补齐的确定内容 | 承接 |
| --- | --- | --- | --- |
| 普通媒体元数据/派生血缘 | Asset含宽高/时长等摘要，Timeline含映射及时间线 | 完整流/编码信息与parent/child、转换参数及派生ObjectRef读取；不得编造不存在的media_metadata/audio_track表 | IF-G11/13；T041—T050 |
| 风险/取证专用payload | Findings含VersionBinding和通用Finding | 框、掩码ObjectRef、异常轨迹/时间区间、可靠性/OOD、融合冲突的逐字段公开投影；不得把warnings字符串当所有结构化字段 | IF-G09/13；T070/T078 |
| 视频逐段来源 | M20/M21/M22与source_match能分别保存query/source区间、方向、速度等 | 全部未知区间、多个来源、查询/来源原时间及索引/映射版本在同一读取中可核对 | IF-G09/13；T087—T089 |
| 高可信内容簇 | M23只输出relations，content_cluster/cluster_member存在 | 应用验证整内容full_copy后分配cluster_id、保存同案成员和证据；任务/运行到簇身份、成员版本及完整读取还需唯一契约 | IF-G09/11/13；T090/T164 |
| 首发排序 | M24给候选，FirstSource给不可变ranking_id及task/run/result/cluster绑定 | 应用落批次、同簇成员检查、连续rank1..N≤3及证据；按ranking_id读取。与聚类成员读取分开 | 现有[首发排序规则](../04-database/first-source-ranking.md)及IF-G09/13 |
| 传播时间线与差异 | Graph有cluster_id/version与节点/边；origin区分observed/inferred/human | 源时间/观测时间与created_at分开，task/run/result映射及前后版本差异投影明确；更正追加版本 | IF-G09/11/13；T094—T097 |
| 无证据主张核查 | 本轮已修正Relation、M29与其内部入口：insufficient允许空证据，其他关系仍要求证据 | 0证据状态写入固定task_result.summary并按Relation校验，不虚构claim_evidence_relation行；有真实证据才按同案外键写关联。共享类型同步生成，实际业务联调仍需执行 | IF-G13；T099/T168 |
| 固化包、复核、审批与反馈历史 | 提交响应能返回对象，但缺完整工作台/历史选择 | 明确读取与撤销入口、版本/目的/到期及固定产物；报告查询不能代替这些对象读取 | IF-G02/03/04/09 |

以上差异有明确字段和实施任务。它们属于接口/数据访问实现交付，不能在“语义复核已执行”时一起标运行通过。

## 首发与内容关系的具体规则

cluster_id由应用生成UUID并对应同案件的content_cluster；asset_id对应media_asset且必须属于该簇的cluster_member。rank是同一次ranking_id批次中的候选名次，不是资产创建顺序或全网发布时间，最多三条、从1连续排列且资产不重复。

只有可核验整内容同源关系才进入相应整内容簇。partial_copy、contains、segment_map仍可作来源证据；A和B分别被拼接Q包含，不据A—Q—B连通合并A/B整内容簇。M23响应不含cluster_id，因此不能声称模型直接生成完整簇或把getFirstSource作为聚类成员查询。

候选发布时间来自可核验发布证据；discovered_at不能默认为published_at。未查明时间/概率保留null，覆盖不足保留insufficient，不跨簇、不凑满三条，不输出确定原创结论。

## 对应验证

每条需求至少运行正常和异常用例；各相关链路还须验证跨案件拒绝、授权撤销、重复消息、旧租约、取消、两次重算后精确历史读取、同名对象新版本、无证据/未知模态、部分payload和原时间/坐标边界。保存输入/预期/实际、命令、源码/契约/模型/索引摘要、实际资源和执行/复核记录。字段缺失先改唯一结构并生成共享类型，不用应用私自附加未声明JSON掩盖。

## 第一阶段工程控制补充（2026-10-13）

[运行快照/事件/节点契约](workflow-contracts.md)、[34能力原响应登记](../06-algorithms/capability-projection-register.md)和[精确历史读取](../03-api/historical-result-reading.md)已补。结构可验证，实际业务读取/投影及调度实现仍需对应任务。
