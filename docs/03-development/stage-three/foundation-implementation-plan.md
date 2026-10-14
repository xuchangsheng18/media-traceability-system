# 第三阶段开发基础整改实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把六项开发基础整改变成可执行、可复核的任务，并明确工程实现与外部决定的边界。

**Architecture:** 质量工具和业务接口各用独立计划；容量与平台按实际权限处理。当前PoC继续保留，业务工程使用独立数据库和部署项目；每个交付按源码、运行证据、GitHub及Linux同步分别判定。

**Tech Stack:** Miniforge Python 3.10.22、Node 22.21.1、PostgreSQL 16.15；当前精确依赖以config/versions.yaml和config/locks为准。

**Spec:** [用户认可的设计范围](../development-environment-change-request.md)。用户于2026-10-14明确回复“认可，继续制定实现计划”；这批准了制定计划，尚不等于以下详细计划审阅通过或正式基线批准。

## Global Constraints

- 保留原100包运行锁、现有PoC及合成M15；不把演示夹具、契约或初始化SQL称为完整业务实现。
- 原12份来源和14份历史材料保持字节不变；第一阶段24步、第二阶段23步、第三阶段16步及170任务分别管理。
- 实际人员和现场/离线/Windows原生/GPU均未确定，不补造姓名，不自动填“不适用”。
- 当前Docker VM数据卷约98GiB、df显示100%；共享引擎38个运行容器中31个属于其他项目。全局停机需要明确维护授权。
- 当前私有GitHub保护接口403；不自行公开仓库、购买套餐或把文档策略标为平台已强制执行。
- 正式批准、正式冻结、生产发布和正式数据授权均保持false。

## Review Focus

- 共享存储：停机或恢复不得改变维护前其他项目的运行集合；任务1逐容器对账。
- 平台权限：实际保护读取失败不能报告保护成功；任务2记录HTTP状态和规则实值。
- 客户端配置：CLI新配置验证不能代替当前桌面线程加载；任务3分别记录。
- 未知环境：未提供用途/设备/网络条件不能生成验收通过；任务4逐适用场景核验。
- 同步证据：旧CI或旧服务器SHA不能证明新版本；任务5绑定精确提交及制品摘要。

## 实施顺序及文件边界

| 顺序 | 工作/入口 | 本轮交付及关闭标准 | 当前状态 |
| --- | --- | --- | --- |
| 1 | 共享容量、平台条件 | 下列任务1、2；真实维护/平台决定后执行 | 等待外部条件 |
| 2 | [Python类型检查计划](python-type-check-implementation-plan.md) | 独立锁、实际类型错误治理、失败探针和必需CI步骤 | 详细计划待审阅，未实施 |
| 3 | [首批业务接口与数据库计划](business-interface-implementation-plan.md) | 独立迁移/RLS、上传续传、7项精确历史读取、异常与真实DB测试 | 详细计划待审阅，未实施 |
| 4 | IF-G02/G03/G06/G12 | 审批、复核、导出、配置；从首批的身份/事务基础承接 | 后续批次，另写详细计划 |
| 5 | IF-G04/G05/G07/G08/G10/G11/G13 | 回流、灰度、权威接入、完整事件/DAG及真实模型 | 外部协议/规则/数据依赖未满足 |
| 6 | Codex与环境验收 | 下列任务3、4；明确适用范围，保存有效决定 | CLI已核验，其余待实证 |
| 每批 | GitHub/Linux同步 | 下列任务5；对应提交检查、清单摘要和回执 | 不用材料归档代替运行 |

当前实际完成范围见[基础审查报告](../../00-project/validation/stage-three-foundation-audit-report.json)：旧13文件AST保持的格式治理、两端精确项目trust及CLI规则/配置层核验、Torch官方载荷核对和补充查询。Python类型工具、新业务HTTP/迁移、容量扩展均未因此完成。

### Task 1: 共享数据卷扩容与恢复核验

**Files:** 更新`docs/00-project/validation/stage-three-foundation-audit-report.json`、`docs/03-development/stage-three/external-inputs.json`及`docs/03-development/development-environment-acceptance-record.md`；完整离线磁盘/配置备份只放Linux私有运行目录，不进Git。

**Interfaces:** 消费明确的维护窗口、受影响项目许可及当前容器清单；产出维护前后镜像路径/容量/空余量、备份摘要、逐容器恢复结果和本项目实际恢复报告。

- [ ] **Step 1:** 取得共享停机授权，记录38个运行容器的ID/项目/重启策略和31个外部容器影响；未获授权保持运行。
- [ ] **Step 2:** 核对磁盘实路径`/workspace/glwy/projects/easyaiot-docker-storage/Docker.raw`，停止引擎后备份该文件及配置，校验摘要和备份可读取性；在线24,129字节数据库导出不能替代此备份。
- [ ] **Step 3:** 用Docker Desktop支持的资源设置扩至候选512GiB；当前CLI没有扩容命令，未取得支持的设置通道时停止此步骤，不猜配置键、不在线修改raw文件。
- [ ] **Step 4:** 启动引擎，比较维护前后的运行集合，核验本项目7个服务、数据库/对象/模型，并读取卷内df。容量须高于现有研发构建保护值5GiB；这不等于生产资源验收。
- [ ] **Step 5:** 在独立恢复目标执行实际数据库及对象恢复，比较数据/版本/摘要后记录结果；失败使用离线备份恢复原磁盘及配置，不能缩容当回滚。
- [ ] **Step 6:** 提交脱敏证据和状态，完整备份不进仓库。只有实际扩容及恢复检查通过才填capacity_closed_ref。

### Task 2: 团队、分支、Runner和Secret治理

**Files:** 更新`CODEOWNERS`、`docs/03-development/repository-access-control.md`、`docs/03-development/stage-three/external-inputs.json`和平台观测报告；新建`docs/03-development/stage-three/platform-control-verification.md`记录实值。

**Interfaces:** 消费实际责任人/账号和平台能力决定；产出实际最小权限清单、规则API回读、必需检查上下文及Runner/Secret管理记录。

- [ ] **Step 1:** 由实际人员提供项目/技术/仓库/安全责任及账号；当前所有者xuchangsheng18不自动兼任全部责任人或独立审核人。
- [ ] **Step 2:** 保留私有仓库，记录当前403；取得支持私有保护的套餐或批准平台后才配置main禁止直接推送、至少一名独立审核及实际CI检查上下文。不预先编造检查名称。
- [ ] **Step 3:** 从最新成功提交读取检查名称，配置后API回读，再用测试分支验证未满足检查/审核时禁止合并；回读或合并约束失败则未完成。
- [ ] **Step 4:** Runner明确专属标签、受信分支和网络范围；Secret记录名称/用途/持有人/轮换，不保存值。当前临时托管CPU CI无仓库Secret，不为充数新建。
- [ ] **Step 5:** 提交规则及权限证据；实际平台保护、账号和正式治理批准分别更新，不因文件存在判完成。

### Task 3: Codex桌面实际加载与操作边界

**Files:** 更新基础审查报告、`docs/03-development/codex-permission-boundary.md`及环境验收记录；用户配置备份保留仓库外。

**Interfaces:** 消费已验证的两端CLI精确trust/完整AGENTS/config/read；产出桌面新会话的实际项目根、规则来源、权限与边界证据。

- [ ] **Step 1:** 对用户实际选定的桌面项目建立新会话，核对项目层启用和完整根AGENTS加载；不声称旧运行线程已重载。
- [ ] **Step 2:** 仅在本项目临时目录执行允许的可逆读写，记录实际权限显示；不通过访问真实密钥、生产数据或其他项目验证边界。
- [ ] **Step 3:** 比对本项目路径、配置层和明确授权范围；规则文本不当作系统ACL。不得扩大全局trust、模型或权限。
- [ ] **Step 4:** 提交脱敏结果，区分CLI已验证、桌面已验证、正式权限仍待决定。

### Task 4: 正式环境适用范围与验收

**Files:** 更新`docs/03-development/development-environment-acceptance-record.md`、`docs/03-development/stage-three/external-inputs.json`及readiness派生视图。

**Interfaces:** 消费真实环境选择、规则/数据依据和负责人决定；产出每个适用环境的验收结果及有效决定引用。

- [ ] **Step 1:** 实际负责人分别确认现场、内网离线、Windows原生、Linux CPU、GPU用途/设备/网络/数据；未知仍标未知。
- [ ] **Step 2:** 对适用环境验证精确锁冷安装、镜像/模型摘要、离线包完整性、身份/来源边界及本批API测试；CPU合成结论不能覆盖GPU或真实业务准确率。
- [ ] **Step 3:** 执行资源/恢复验证，生产Python版本与维护例外依既有第二阶段政策单独决定；不由本计划批准Python3.10生产使用。
- [ ] **Step 4:** 实际负责人形成接受/有条件接受/拒绝及范围决定，记录事实及引用；没有有效决定不更新正式批准/冻结。

### Task 5: 每批回归、同步与状态更新

**Files:** 更新既有docs导航、stage-three/deliverables.json、验证报告、文件摘要清单和server-sync-receipt.json；不另建互相矛盾的完成台账。

**Interfaces:** 消费本批真实源码提交和通过的检查；产出GitHub当前提交CI制品、Linux同源摘要、Git状态及服务健康回执。

- [ ] **Step 1:** 跑本批专项测试及现有资料/契约/PoC检查；新实现还需独立业务DB/HTTP检查。记录失败，修复后重跑相关检查。
- [ ] **Step 2:** 更新生成导航并核对所有链接、原始材料摘要和严格计数；计划文件不能把13个OPEN改为CLOSED。
- [ ] **Step 3:** 提交并同步GitHub，确认该源码SHA对应的实际工作流和制品摘要通过。
- [ ] **Step 4:** 通过清单逐文件核对Linux后对齐Git提交，再检查工作区/服务；当前共享容量不足时不能绕过保护重建。
- [ ] **Step 5:** 补同步回执及证据提交，比较本地/GitHub/Linux最终SHA。回执同时引用被CI测试的源码SHA，不能把证据提交当作已重新运行CI。

## 自检与审阅状态

六项要求均有计划或独立子计划；13个缺口都有后续批次和前置条件。当前只完成计划编制，未补造外部协议、人员、验收或排期。详细任务按技术依赖排序，不是人员已确认的日历工期。

推荐由本会话直接逐任务实施：类型层与新业务工程有连续依赖，便于保持原运行栈和契约一致。用户需审阅本计划及两个子计划后选定执行方式；未选定前保留“详细计划待审阅”。

## 用户审阅决定

2026-10-14：用户明确回复“认可计划，由当前会话直接逐项实施（推荐）”。详细计划已认可，按当前会话直接实施；正文中的“待审阅”为编制时状态，具体完成情况仍按实测台账判定。此决定不批准共享引擎停机或正式生产冻结。
