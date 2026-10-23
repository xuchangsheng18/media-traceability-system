# T001—T123数据表、接口与方法落实计划：案件内资产和任务读取

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development. Only tick steps after actual evidence exists.

**Goal:** 提取T001—T123全部任务的表、接口、方法及实际状态；首先补齐真实资产详情、案件内资产列表和任务列表，复用现有数据库与权限体系。

**Architecture:** 沿用已有FastAPI业务应用、SQLAlchemy访问、统一权限、请求事务和RLS，不另建权限源或增加服务端口。历史0001—0011不修改；用0012增量迁移扩展固定操作和元数据查找清单。用户本轮明确同意给尚未挂载的listAssets/listTasks增加必填case_id，同时更新公共契约和生成类型。

**Tech Stack:** 现有Linux、Miniforge py310、PostgreSQL16、FastAPI、Vue。原100包锁不改，Python候选继续暂缓。

**Spec:** [执行顺序及既有批量授权](t001-t123-development-sequence.md)、源T019/T020/T030/T035/T040、[公共接口](../03-api/openapi.yaml)、[数据字典](../04-database/data-dictionary.md)、T014 PR01/PR02/PR04及T015已批准范围设计。用户本轮要求落实数据表、HTTP接口和方法；名单与方法存在不等于对应全部任务验收完成。

## Global Constraints

- 保留12模块和170任务；本轮开发授权止于T123，T124—T170不自动实施。T092依赖T164继续单列。
- 已有62张业务基础表，最新0011隔离结构为64表861列；优先复用，不批量重复建表。新增业务实体必须另有契约依据和增量迁移。
- 只在随机命名的新隔离测试数据库验证；不改当前演示库、PoC库、现有服务、共享身份与正式策略。
- getAsset只返回既有Asset契约的元数据和固定ObjectRef，不增加直接对象下载或来源授权旁路。
- listAssets、listTasks固定于服务端校验后的case_id；列表逐项校验来源、分类和读取用途，不能因能访问案件就展示其所有行。缺可信事实保持拒绝；有权范围内没有记录才返回有效空列表。
- 使用现有游标签名和规范编码校验。绑定身份、组织、案件、操作和请求限制；禁止跨案件/跨操作重放。先授权再分页，不返回未授权记录、计数或未授权对象位置。
- 任务列表读取当前analysis_task元数据，不依赖task_result历史投影；排队/运行中无结果的任务应能列出，不伪造分析成功。
- 保留已有CI门禁，执行本批正常、越权、来源撤销、错误游标和迁移回归。综合性能、真实业务模型和正式验收仍按源任务后置。

## Review Focus

1. 案件成员资格、来源或读取许可在查询中途撤销：事务尾部重新核验，不能返回旧授权数据。
2. 请求缺case_id、重复参数、其他案件、非法UUID或未知参数：拒绝，不从客户端猜默认案件。
3. 有效签名游标跨用户、案件、操作或参数使用：拒绝；非规范base64同样拒绝。
4. 任务没有历史结果：列表使用当前任务表，不以历史快照缺失漏掉任务。
5. 0012从最新0011函数扩展：保留issueOperationToken、sealEvidence及所有既有读取/消费权限边界。

## Task 1：补充三个读取操作

**Files:** 新增`backend/business_app/catalog_reads.py`、`backend/business_app/catalog_router.py`、`backend/business_migrations/0012_catalog_reads.sql`及`tests/business/test_catalog_reads.py`；修改`main.py`及现有对象事实、集合授权和固定查找清单。

**Interfaces:** `GET /api/v1/assets/{id}` → `getAsset`/Asset；`GET /api/v1/assets?case_id=…&limit=…&cursor=…` → `listAssets`/AssetPage；`GET /api/v1/analysis/tasks?case_id=…&limit=…&cursor=…` → `listTasks`/TaskPage。响应沿用现有Schema，不增加业务字段。

- [x] 先写失败测试：真实数据库元数据读取、列表空页/分页、当前无结果任务、来源撤销、跨组织/案件、无身份/无角色、非法/跨范围游标。
- [x] 记录失败，再实现路由、实际SQL访问、每项授权和事务尾部复核；不使用通用空返回填接口。
- [x] 新增0012并核验SQL/Python注册清单一致，历史迁移保持原字节。
- [ ] 执行新测试及受影响的权限、范围、迁移和类型检查；记录精确命令及结果。

## Task 2：同步契约、任务总清单与实际状态

**Files:** 修改`docs/03-api/openapi.yaml`的两个列表参数和派生文档/类型；增加T001—T123逐项表/接口/方法清单及本批验证回执，更新任务卡与总导航。

- [x] 加入已获用户确认的两个必填case_id参数，同步操作索引、样例、共享类型和契约校验；不修改其他公共字段。
- [x] 为123任务逐条列原范围、表、迁移证据、HTTP操作及实际Python方法、已验证步骤、未完成事项；所有映射区分静态证据和运行证据。
- [x] 修正数据库导航中过时的实例状态，区分0001—0011新预览与未切换的旧库；不把创建脚本当实际部署证明。
- [x] 更新实际通过的开发子范围，未满足整任务标准仍保留剩余工作；无模型/规则/外部数据时不批量勾选。
- [ ] 执行适用资料生成漂移、引用、输入与代码校验；正常提交到既有开发分支并同步Linux源码，分别记录CI及运行库版本。

## 本批之外仍需实施

本批开始时有30个未挂载操作，新增三个读取后仍有27个未在业务应用挂载。本计划不会将它们一并关闭。任务生产/DAG、检索索引、真实模型、主张、封存、报告、回流等按各自契约和实际依赖继续；devLogin不替代正式OIDC。真实来源服务、分类/用途规则、模型制品及用途数据等尚缺输入，须逐项保留，不能用模拟结果替代。

2026-10-21验证记录：完整权限门禁首轮触发既有1200秒超时；该次不是通过。专项读取、迁移、范围、令牌及后续托管CI分别记录在本批回执，未执行或失败的检查不能由源码完成替代。
