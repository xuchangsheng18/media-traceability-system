# 数据分组与集合隔离

所有原始来源组以及压缩、裁剪、篡改、帧、音轨和增强派生版本进入同一集合。多源组合样本关联的全部来源组必须整体同集合，按父组连通分量划分；这只是防泄漏分组，不据此认定业务整内容同源簇。

split-manifest使用train、validation、calibration、holdout，记录seed、grouping_policy_version、sample_id、source_group_ids、父样本、人物/事件组及SHA-256。人员/事件外推任务另检查对应组隔离。封存时holdout_access=acceptance_only。

训练比例源70/15/15为建议，加入独立calibration后的比例需重评，不能让各份额相加超过1，也不能据同名validation默许校准泄漏。比例不是本包已批准验收规则。

CI仅使用公开许可核验后的开发夹具或自建合成数据；日常基线不读封存验收样本。封存访问、解封、独立执行与统计由责任方记录用途、授权和日志。回流数据先用途批准、脱敏、去重/父组检查，不自动落入训练或修改冻结标签。
