# T001—T011研发基础逐项复核

本轮范围来自用户“T012之前的任务请完善”，只补齐和核验T001—T011；保留既有T012数据库成果，不新增T012/T013功能。源角色、依赖、范围、契约、验收、测试和CI要求在机器报告中逐字保留，原170项任务内容不变。

[逐项复核报告](../00-project/validation/t001-t011-foundation-review-report.json) · [分步任务导航](../../tasks/README.md) · [当前任务台账](../../tasks/execution-status.json)

## 本轮修复和验证边界

1. T005改用目录范围运行Ruff格式检查，新增模块自动继承门禁；同一目录下Git已跟踪和未忽略Python文件同时进入UTF-8/LF/末尾换行检查。原运行包锁不变，旧脚本不扩大为全仓格式改写。真实格式命令分别覆盖format-check和pre-commit：新建违规模块必须失败，修正后成功。
2. T004增加只读核验，将Compose声明、Docker实际设置和容器内cgroup v2的CPU/内存/进程限制逐项比较；缺容器、无限值、漂移或不可读均失败。服务器7服务实测通过，CI也运行同一脚本。它不改变配额，不证明临时盘、耗尽隔离或生产高可用。
3. T006重新读取GitHub当前状态：Public，main protected=false，规则集查询200且为空，分支保护查询404；Actions默认工作流权限read且不能批准PR。旧private/403只作历史。没有改平台设置。

## 按任务书逐项对照

“通过”仅指表中写明的技术范围。真实责任人、正式适用环境和有效验收决定尚未落实，整任务关闭仍为0；未完成项同时留在各任务卡，不能把它们合并成“只差签字”。

### T001 建立单仓库目录与基础README

[任务卡](../../tasks/platform/T001.md)；源依赖：无。

原验收标准：仓库结构与设计一致；README包含启动、测试、提交规范；不得包含真实密钥。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 目录与设计映射 | 通过 | [repository-layout.md](../../docs/02-architecture/repository-layout.md) |
| 启动、测试、提交说明 | 通过 | [CONTRIBUTING.md](../../CONTRIBUTING.md) |
| 已知私密值和基础密钥模式扫描 | 通过（扫描范围内） | [stage_three_quality.py](../../scripts/stage_three_quality.py) |

### T002 配置Python后端工程

[任务卡](../../tasks/platform/T002.md)；源依赖：T001。

原验收标准：服务可启动；缺少必要配置时给出明确错误；依赖版本锁定。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 启动、健康、必需/非法配置和依赖锁 | 通过（py310研发） | [test_foundation_configuration.py](../../tests/stage_three/test_foundation_configuration.py) |
| 源Python 3.11与当前3.10.22差异 | 已记录用户选择；正式版本未冻结 | [technical-baseline.md](../../docs/02-architecture/technical-baseline.md) |

### T003 配置Vue前端工程

[任务卡](../../tasks/frontend/T003.md)；源依赖：T001。

原验收标准：开发服务器可启动；严格类型检查通过；API地址环境化。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 开发启动、严格类型、环境化API和组件冒烟 | 通过（研发前端） | [package.json](../../frontend/package.json) |
| 源/health映射到现有业务/api/v1/health | 已记录；保留现有契约 | [foundation-closeout-implementation.md](../../docs/03-development/stage-three/foundation-closeout-implementation.md) |

### T004 建立本地容器开发环境

[任务卡](../../tasks/platform/T004.md)；源依赖：T002,T003。

原验收标准：一条命令启动；隔离数据卷和密钥；按获准项目配额设置CPU、内存、进程和临时盘限制，核对实际cgroup生效；不认定单机容器为生产高可用。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 单命令启动、服务ready、卷与密钥隔离 | 已有研发验证 | [ci-all-report.json](../../docs/00-project/validation/ci-all-report.json) |
| Compose与Docker及真实cgroup v2的CPU/内存/pids一致 | 通过（7服务，只读） | [development-container-limits-report.json](../../docs/00-project/validation/development-container-limits-report.json) |
| 获准配额、临时盘限制、资源耗尽隔离、介质/间接依赖 | 未完成；需单独验证 | [resource-and-team-inventory.md](../../docs/02-architecture/resource-and-team-inventory.md) |

### T005 配置代码格式化与静态检查

[任务卡](../../tasks/platform/T005.md)；源依赖：T002,T003。

原验收标准：本地和CI命令一致；示例违规代码能被拦截。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 本地/提交钩子/CI使用同一门禁 | 通过（选定Linux） | [dev.py](../../scripts/dev.py) |
| 新增模块自动纳入格式与文本检查，违规真实Ruff拒绝 | 通过；新增3项回归 | [test_dev.py](../../tests/stage_three/test_dev.py) |
| 其他开发者和Windows原生钩子 | 未验证 | [development-hook-report.json](../../docs/00-project/validation/development-hook-report.json) |

### T006 建立基础持续集成流水线

[任务卡](../../tasks/platform/T006.md)；源依赖：T004,T005。

原验收标准：任一门禁失败阻止合并；产出测试报告；缓存不影响正确性。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 后端/前端/迁移/测试/构建、失败探针及报告 | 已有CI实测；本批按新CI核验 | [github-actions-report.json](../../docs/00-project/validation/github-actions-report.json) |
| 失败阻止main合并 | 未通过：main未保护，规则集为空 | [repository-governance-snapshot.json](../../docs/00-project/validation/repository-governance-snapshot.json) |
| 平台维护人及权限/Secret治理 | 未确认 | [repository-access-control.md](../../docs/03-development/repository-access-control.md) |

### T007 建立统一配置和密钥规范

[任务卡](../../tasks/platform/T007.md)；源依赖：T002,T004。

原验收标准：仓库无真实密钥；敏感配置不写日志；启动时校验必需项。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 环境/Secret注入、启动校验、秘密不回显 | 通过（开发/测试范围） | [test_foundation_configuration.py](../../tests/stage_three/test_foundation_configuration.py) |
| 生产配置、轮换/撤销与实际维护权限 | 未完成；production当前拒绝启动 | [settings.py](../../backend/business_app/settings.py) |

### T008 建立统一日志与请求追踪

[任务卡](../../tasks/platform/T008.md)；源依赖：T002。

原验收标准：所有API日志可关联请求；令牌、密码、原始敏感文本被过滤。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 既有API/队列/推理关联、并发隔离及脱敏 | 通过（既有链路范围） | [test_foundation_tracing.py](../../tests/stage_three/test_foundation_tracing.py) |
| 完整DAG/网关、跨进程聚合、采样及指标标签脱敏 | 未完成 | [foundation-closeout-implementation.md](../../docs/03-development/stage-three/foundation-closeout-implementation.md) |

### T009 建立统一异常与错误码框架

[任务卡](../../tasks/platform/T009.md)；源依赖：T002。

原验收标准：未知异常不泄露堆栈；已知异常映射稳定；错误码不可重复。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 未知异常不泄密、稳定HTTP映射和错误码唯一 | 通过（现有基础接口） | [test_foundation_errors.py](../../tests/business/test_foundation_errors.py) |

### T010 建立架构决策记录和变更模板

[任务卡](../../tasks/platform/T010.md)；源依赖：T001。

原验收标准：重要决策有状态、背景、方案、影响和回滚；模板可直接复用。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| ADR/需求/模型/数据库/PR模板的状态、背景、方案、影响、恢复及可复用性 | 通过（文档结构范围） | [t011-dependency-report.json](../../docs/00-project/validation/t011-dependency-report.json) |
| 实际团队使用和有效复核 | 未验证 | [repository-access-control.md](../../docs/03-development/repository-access-control.md) |

### T011 设计用户角色与数据范围模型

[任务卡](../../tasks/platform/T011.md)；源依赖：T002,T010。

原验收标准：覆盖管理员、数据管理员、算法管理员、审核员、核查人员和审计员；默认拒绝。

| 核验内容 | 结论及边界 | 证据 |
| --- | --- | --- |
| 九实体关系、六角色权限矩阵、默认拒绝及越权用例 | 通过（候选设计及56例合成评审） | [t011-access-model-report.json](../../docs/00-project/validation/t011-access-model-report.json) |
| 权威身份、正式六角色规则/分类、真实责任人与有效决定 | 未确认；不放行正式业务 | [access-control-model.md](../../docs/08-security/access-control-model.md) |

## 实施决定和恢复

沿用已认可的foundation-closeout-plan，新增文件覆盖和cgroup读取是既有T005/T004验收证据补齐。公共API、身份权限规则、数据库迁移及100包运行锁不变。新增脚本只执行查询和cat，不调用up/down/restart或执行资源压力。GitHub新检查使用Runner自有临时栈。若cgroup v2不可读则失败，不将未知当通过；其他cgroup环境须先单独适配和验证。

本轮代码未部署到共享7服务。需要撤回时对本轮源码提交作独立revert并重新检查，不删除库/卷或回滚已存在0004迁移。

## 后续可执行范围

T011的六角色、实体关系、默认拒绝候选设计已可作为后续数据库工作的研发输入；正式身份/单位/案件映射和角色规则仍按任务卡落实。下一条为T012“实现用户角色数据库模型”：先复核既有0004及其剩余项，按真实输入补齐和验收；本轮不自动实施。T006需仓库管理者批准和设置分支保护后，用失败PR验证无法合并。生产profile、完整观测、临时盘/资源压力、真实人员/规则及正式环境不是本轮可自动确认的条件。

实际命令、Python版本、测试数量、当前CI源码与三地同步以本轮验证记录、GitHub制品和同步回执为准，资料结构检查不替代业务测试。

## 本轮实际命令和结果

在Linux既有Miniforge py310 3.10.22的Git外隔离源码副本执行；命令中的python指该解释器。

| 命令 | 实际结果 |
| --- | --- |
| `python -m pytest tests/business tests/platform tests/stage_three tests/poc -q --tb=short` | 328 passed；含167项业务/数据库测试，不重复相加；无失败和跳过 |
| `python scripts/dev.py format-check` | 88个Python文件格式、100个所选文本文件、前端Prettier通过 |
| `python scripts/dev.py lint` | Ruff、ESLint、88文件mypy和前端严格类型通过 |
| `python scripts/stage_three_quality.py secrets` | 当前所选Git外副本的已跟踪/未忽略文件、已知runtime私密值及基础模式扫描通过；不是历史全量DLP |
| `python scripts/verify_development_limits.py` | 7服务声明/设置/cgroup v2逐项一致；只读，未重启 |
| `python scripts/dev.py status` | 原7服务running/healthy，未变更服务 |

新增17项回归在实现前观察到失败，修复后纳入Linux328项回归。初次类型检查发现空列表缺少类型标注，已修复并重新通过。前端离线安装因缓存不全失败，联网安装亦未成功；最终复用了package-lock字节完全相同的现有安装，未修改前端锁。托管Runner仍从锁文件全新安装并独立验证，具体结论见GitHub制品记录。
