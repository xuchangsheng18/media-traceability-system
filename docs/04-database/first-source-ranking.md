# 首发候选排序与版本契约

版本0.4-review，2026-10-12。依据总体设计的观察范围内Top-3候选原则、T091—T093及M24能力，补充可执行的工程约束。属于本轮设计提案，不将候选排序当作确定首发或原创认定。

## 排序单位与版本

`first_source_ranking`保存一次完整、不可变的排序结果。主键为`ranking_id`；业务唯一键为`case_id, cluster_id, task_id, run_version, result_version`。它通过复合外键绑定同案件内容簇和`task_result`快照。

`first_source_candidate`保存该快照的0至3条候选。`cluster_id`是所属内容簇，`asset_id`是已在该簇登记的媒体资产，`rank`是在该快照内的名次。它们不能单独表达一次计算，必须同时绑定`ranking_id`。同一簇多次计算形成多个快照，不能把所有历史行拼成一份Top-3。

不使用`model_version`区分计算批次：同一模型可能多次运行。`row_version`也不是结果版本。重算或复核更正创建新的结果版本和ranking_id；旧快照、候选及元数据不可UPDATE、DELETE或TRUNCATE。

## 数据库强制约束

| 规则 | 实际执行机制 |
| --- | --- |
| 同批次最多3条 | rank为1—3，且UNIQUE(case_id,ranking_id,rank) |
| 同资产不能重复入选 | UNIQUE(case_id,ranking_id,asset_id) |
| 候选必须属于本簇 | FOREIGN KEY(case_id,cluster_id,asset_id)引用cluster_member唯一键 |
| 不混用案件或簇 | 带case_id的外键，候选同时绑定ranking_id和cluster_id |
| 排序结果对应确定运行 | 头表复合外键引用task_result的任务、运行及结果版本 |
| 名次连续且数量完整 | candidate_count为0—3；延迟约束触发器在事务结束检查实际数量及最小、最大名次 |
| 候选元信息一致 | BEFORE INSERT触发器比较单位、簇、model_version、status、coverage_note与头表 |
| 0候选结果 | 头表candidate_count=0且status=insufficient；不插入占位候选 |
| 历史不可覆盖 | 头表和明细追加式触发器；普通运行角色只有SELECT、INSERT |
| 案件访问隔离 | 新头表启用并强制RLS，复用案件访问函数 |

头表和全部候选必须在同一事务写入，提交前可执行`SET CONSTRAINTS ALL IMMEDIATE`主动检查。事务失败整体回滚，不允许先提交一个candidate_count=3的空头表再慢慢补齐。快照提交后数量固定，后续不能向旧快照追加第四条或缺失名次。

这些控制不防数据库超级用户或禁用触发器的运维操作；应用认证上下文仍须可信。首发候选JSON证据ID现在由SQL插入触发器检查结构、ID格式、存在及同案件。它不是所有JSONB字段的通用外键；证据支持关系、具体用途和有效性仍须应用复核。

## 排序和证据语义

排名表示所选模型与策略在已登记观察范围内的候选顺序。用于排序的证据、特征、时间可信度和阈值由`model_version`及`policy_version`对应的版本化策略定义；本轮不捏造权重公式或业务阈值。

工程层要求模型适配器输出全序：先按已选策略分数排序；策略分数完全相同时，可核查发布时间升序、未知时间置后，再按asset_id字典序稳定打破并列。该稳定规则只用于复现列表，不提高首发真实性。适配器要保留原始分数及理由，不用rank冒充概率。未校准概率为NULL，未知发布时间为NULL。

候选不足3条时返回实际数量，不能补虚拟资产。证据不足可返回0条或带insufficient标记的候选；0条必须是insufficient。尚未完成计算则没有快照，不把“未计算”伪装成“计算后0候选”。

## API与模型契约

`GET /api/v1/clusters/{id}/first-source`返回一份`FirstSource`。新增字段为ranking_id、task_id、run_version、result_version、policy_version和candidate_count。可选查询参数ranking_id定位历史快照；未指定时按created_at降序、ranking_id降序选一份当前授权簇的最新快照。最新只表示登记顺序，不代表最可信或已批准。无对应快照返回404，并沿用对象存在性隐藏规则。

候选数组设置maxItems=3；每项rank设置minimum=1、maximum=3。响应数组必须按rank升序，rank为1至candidate_count且资产ID无重复。JSON Schema的uniqueItems比较整个数组元素，不能单独保证rank或asset_id唯一；因此仍需语义检查和SQL约束。校验实现见[scripts/validate_inputs.py](../../scripts/validate_inputs.py)。

M24的原始模型响应只限制候选不超过3条及名次语义，不要求模型自己生成数据库ranking_id。业务层完成授权、证据校验、版本绑定后才生成持久化快照。

## 升级与兼容

当前无业务数据库，修订后的initial-schema.sql仅用于新空库。API新增必填响应字段属于契约变更，客户端和合成样例一起更新；当前未发布生产客户端。若已有旧库，禁止直接运行本SQL覆盖。先备份、盘点旧候选来源，再为每条旧数据核实任务/运行/结果和批次；不能仅按相同簇或模型猜测批次。无法核实的数据隔离待核查；完成回填和约束验证后再切换。该存量迁移尚无实际旧库可验证，不提供伪造的自动回填脚本。

## 验证要求

测试覆盖合法0/1/2/3候选、第四条、重复名次、重复资产、缺名次、缺明细、头表状态不符、跨案件、簇外资产、跨簇/批次、模型和覆盖信息不符、运行结果不存在、重复运行快照、旧版本保护以及普通角色RLS。外部API测试验证数量、连续名次、重复资产、计数一致及空结果状态。具体实测以本轮验证报告为准。


## 证据引用补充约束

首发候选evidence_refs必须显式提供，仅允许两个键：evidence_ids和counter_evidence_ids。两者均为数组；支持证据至少1条，反对证据可为空。每项是带连字符的UUID字符串，各数组内不可重复（大小写表示的同一UUID也算重复）。SQL触发器检查每个ID在同案件evidence_item存在且当前运行角色可见；不存在或跨案件引用拒绝。

删除此列的默认空对象，避免遗漏证据仍产生候选。SQL NULL、JSON null、缺键、错误类型、空支持列表、非UUID、额外键和重复引用均拒绝。数据库UUID类型可接受更多输入形式，本项目JSON证据ID选择标准连字符形式以保持API格式一致。

两个数组之间不自动强制互斥：同一证据可能包含不同方面，是否能同时作为支持与反对由证据解释决定。本轮只强制各列表内部唯一，不擅自增加业务含义。证据存在和同案件不是“证据足以证明首发”的判定。

新增18项数据库案例覆盖上述边界，结合原30项首发排序检查和25项既有检查。当前报告以database-foundation-report.json及其SQL摘要为准，未声明完成并发压测、旧库迁移或全部应用安全验证。
