# 接口字段落库与投影

api-field-mapping.csv/json逐操作覆盖请求及响应的顶层和嵌套字段，含直接列、关联对象及服务层输入/投影。嵌套结构见data-dictionary.md与根目录schemas/api/common.schema.json，不能把一个JSONB投影解释为数据库已验证所有外部引用。

| 结构 | 关键字段 | 关系与检查 |
| --- | --- | --- |
| Asset/ObjectRef | asset_id/object_id/version_id/sha256 | media_asset.object_id联object_version；API不直接暴露bucket/key。 |
| Task/VersionBinding | task_id/run_version/result_version/policy_version | analysis_task投影与task_run/task_result复合外键；更新须If-Match。 |
| Evidence | evidence_id/asset_id/model/version/mapping | evidence_item及task_evidence/finding_evidence；原件定位和版本不可替换。 |
| Finding | evidence_ids/bbox/time/mask | risk_finding/tamper_finding与finding_evidence；bbox等payload另做语义检查。 |
| Review/Approval | reviewer/purpose/object_version/policy | actor从认证取得；业务复核与独立审批用途分开，相关版本一致。 |
| SourceMatch | query/source范围/direction/speed | source_match分别引用两端资产；起止检查，速度>0，组合父组隔离。 |
| Report/Seal | approval/object/evidence绑定 | report/evidence_package引用当前task_result及固定object_version；正式授权由服务核验。 |
| Claim/Relation | 未知null/source_segment/evidence_ids | claim.claim_time等字段及claim_evidence_relation；引用存在和语义支持分开。 |

## FirstSource修订

快照层字段来自first_source_ranking；candidates按case_id与ranking_id关联first_source_candidate并按rank排序。asset_id属于已验证cluster_member。evidence_ids与counter_evidence_ids分别来自evidence_refs同名键；JSONB中ID的存在和授权由应用核验，不声称自动拥有外键。新增快照字段已同步CSV/JSON与OpenAPI。

## 首发证据投影的持久化约束

evidence_refs使用evidence_ids/counter_evidence_ids两个数组键，与FirstSource逐项同名投影；列表内部不可重复，支持列表非空。SQL触发器检查引用存在及同案件，应用继续核验具体用途、证据关系和版本适用性。该规则只适用于首发候选，不泛化为所有JSON字段已经自动建立外键。

## 本轮补充（2026-10-13）

insufficient没有证据时使用运行结果summary的Relation结构保留未知结论；不插入证据关联表的虚假evidence_id，不修改真实证据外键。完整投影边界见[结果身份](../05-workflows/result-identity-and-projection.md)。
