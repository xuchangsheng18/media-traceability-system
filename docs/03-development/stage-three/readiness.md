# 第三阶段16步实际状态与导航

2026-10-14；仓库和Codex研发环境实施，正式Development Environment Baseline 1.0仍NOT_FROZEN。第一阶段24步、第二阶段23步、第三阶段16步与170业务任务分别管理；本阶段不开展完整业务研发。

两份Word原件已按字节归档，正文阅读版保留来源与提示词参考身份。当前用户已指定GitHub和Miniforge py310并要求同步，可继续已授权工程工作；原手册中的已批准Technical Baseline 1.0前提并未自动满足，当前实际为研发1.1-py310-cpu。审批、人事、正式网络/分支保护与资源条件分别登记。

- [第三阶段建立代码仓库和Codex工作环境分步提示词手册.docx](<../../guides/第三阶段建立代码仓库和Codex工作环境分步提示词手册.docx>)；[全文阅读版](<../../_converted/guide/第三阶段建立代码仓库和Codex工作环境分步提示词手册.md>)；SHA-256 `6a308104713810bfd3fee23584cddc42473ebf74e2c3b2124366f5aaf1aa7fd9`。
- [第三阶段建立代码仓库和Codex工作环境实施指南.docx](<../../guides/第三阶段建立代码仓库和Codex工作环境实施指南.docx>)；[全文阅读版](<../../_converted/guide/第三阶段建立代码仓库和Codex工作环境实施指南.md>)；SHA-256 `2e6f44601de70ef94ff96eb1b44a2e529a080e4416d3024e86e10eb70066dadb`。

第三阶段已有产物的机器对照见[deliverables.json](<deliverables.json>)，正式输入见[external-inputs.json](<external-inputs.json>)；完整执行报告见[development-environment-validation-report.md](<../development-environment-validation-report.md>)。

| 步 | 原步骤与责任 | 已落实内容/产物 | 当前工程判定 | 正式/实际剩余条件 |
| --- | --- | --- | --- | --- |
| 1 | 确定仓库平台 仓库名称及管理人员<br>人工决策，Codex形成比较报告和决策表 | 保留用户指定私有GitHub仓库和实际名称，补内网平台比较与职责/准入条件。<br>[repository-platform-options.md](<../repository-platform-options.md>) | 工程产物/实际证据分别核验；正式条件待落实 | 实际项目/技术/仓库管理人员及正式生产代码平台准入未落实。 |
| 2 | 确定Monorepo或多仓库模式<br>人工决策，Codex分析 | 沿用既有Monorepo，比较多仓模式并生成独立ADR-013候选，不搬迁旧文件。<br>[repository-structure-decision.md](<../repository-structure-decision.md>)、[ADR-013-repository-structure.md](<../../02-architecture/architecture-decisions/ADR-013-repository-structure.md>) | 工程产物/实际证据分别核验；正式条件待落实 | 实际团队边界和结构正式批准待填。 |
| 3 | 明确网络 安全和Codex权限边界<br>人工确定，Codex生成模板与权限矩阵 | 区分本次会话授权、正式环境边界和禁止数据；保留操作审计与撤销要求。<br>[codex-permission-boundary.md](<../codex-permission-boundary.md>) | 工程产物/实际证据分别核验；正式条件待落实 | 正式网络、生产目录、审批角色/期限及真实数据用途授权待落实。 |
| 4 | 建立仓库和团队账号权限<br>仓库管理员执行，Codex生成配置建议 | 登记真实仓库所有者与专业角色候选矩阵，不创建账号或虚构团队。<br>[repository-access-control.md](<../repository-access-control.md>) | 工程产物/实际证据分别核验；正式条件待落实 | 真实团队账号、最小权限开通/回收及主分支/Secret管理权限未验收。 |
| 5 | 根据技术基线设计目录结构<br>Codex设计，技术负责人评审 | 说明原13目录与data-pipeline/tools的用途、依赖与禁止内容。<br>[repository-layout.md](<../repository-layout.md>) | 工程产物/实际证据分别核验；正式条件待落实 | 实际责任团队、目录/模块发布边界评审待确认。 |
| 6 | 人工评审目录和分支策略<br>人工评审，Codex准备评审包 | 准备评审议程、分支/审核/标签/紧急流程与决定模板，不代签。<br>[repository-review-package.md](<../repository-review-package.md>) | 评审/验收材料已准备，实际决定待填 | 实际评审者、会议/日期、分支及审核人数决定未提供。 |
| 7 | 初始化仓库和基础文件<br>Codex执行，技术负责人监督 | 补贡献/安全/所有者/格式/环境模板等基础文件，保留全部原件与历史。<br>[CONTRIBUTING.md](<../../../CONTRIBUTING.md>)、[SECURITY.md](<../../../SECURITY.md>)、[CODEOWNERS](<../../../CODEOWNERS>)、[.editorconfig](<../../../.editorconfig>)、[.env.example](<../../../.env.example>)、[.pre-commit-config.yaml](<../../../.pre-commit-config.yaml>)、[README.md](<../../../data-pipeline/README.md>)、[README.md](<../../../tools/README.md>) | 工程产物/实际证据分别核验；正式条件待落实；一致性检查PASS | 治理文件正式审核与实际人员策略待确认；只证明创建和验证。 |
| 8 | 配置前端 后端和算法开发环境<br>Codex执行，相关负责人评审 | 沿用原100包py310/Node/前端/合成推理，另锁pre-commit工具层，不升级业务栈。<br>[versions.yaml](<../../../config/versions.yaml>)、[requirements-stage-three-quality.lock](<../../../config/locks/requirements-stage-three-quality.lock>)、[.python-version](<../../../.python-version>)、[.nvmrc](<../../../.nvmrc>) | 工程产物/实际证据分别核验；正式条件待落实；一致性检查PASS | Linux CPU组合可验证；Windows原生安装、生产新Python/GPU/离线准入未完成。 |
| 9 | 配置格式化 静态检查和测试工具<br>Codex执行，测试负责人评审 | 统一原Ruff/TS/测试与新增格式、pre-commit、依赖/秘密扫描，记录工具适用范围与跳过项。<br>[stage_three_quality.py](<../../../scripts/stage_three_quality.py>)、[stage-three-profile.json](<../../../config/stage-three-profile.json>)、[test_dev.py](<../../../tests/stage_three/test_dev.py>) | 工程产物/实际证据分别核验；正式条件待落实；一致性检查PASS | 未选择工具不当已启用；旧代码格式债务/完整静态类型方案与正式质量制度待定，Torch发行包审计覆盖仍待。 |
| 10 | 编写AGENTS.md等Codex规则<br>Codex生成，技术负责人审核 | 补根规则的阶段/命令/冲突要求和项目Codex配置，继承用户模型及权限设置。<br>[AGENTS.md](<../../../AGENTS.md>)、[config.toml](<../../../.codex/config.toml>)、[CONTRIBUTING.md](<../../../CONTRIBUTING.md>)、[SECURITY.md](<../../../SECURITY.md>)、[CODEOWNERS](<../../../CODEOWNERS>) | 工程产物/实际证据分别核验；正式条件待落实 | 项目层信任/不同客户端加载及实际审核待确认，不将文档当技术强制控制。 |
| 11 | 建立最小骨架工程<br>Codex实现，技术负责人监督 | 沿用7服务真实合成链路，另实现三进程Vue/FastAPI/模拟推理夹具，具备health/ready/安全错误/trace和实际浏览器测试。<br>[README.md](<../../../tools/stage_three_demo/README.md>)、[app.py](<../../../tools/stage_three_demo/app.py>)、[mock-connectivity.response.schema.json](<../../../schemas/development/mock-connectivity.response.schema.json>)、[verify_stage_three_demo.py](<../../../scripts/verify_stage_three_demo.py>) | 工程产物/实际证据分别核验；正式条件待落实 | 夹具只是模拟连通性；现有PoC依旧真实合成M15，53接口/62表/34能力及完整业务不在本阶段完成。 |
| 12 | 建立本地开发启动命令<br>Codex执行，开发负责人评审 | 建立Linux Make/Python入口与Windows PowerShell经SSH入口，非零失败、缓存清理保护和共享栈容量保护。<br>[Makefile](<../../../Makefile>)、[dev.py](<../../../scripts/dev.py>)、[dev.ps1](<../../../scripts/dev.ps1>) | 工程产物/实际证据分别核验；正式条件待落实；一致性检查PASS | 共享Docker盘容量不足；build/integration/ci受保护，Windows原生/正式现场安装仍待。 |
| 13 | 建立基础CI流水线<br>Codex生成，测试和技术负责人审核 | 沿用25门禁CPU托管CI，接入第三阶段原件/16步/统一命令/夹具与质量检查，不发布生产。<br>[ci.yml](<../../../.github/workflows/ci.yml>)、[.gitlab-ci.yml](<../../../.gitlab-ci.yml>) | 工程产物/实际证据分别核验；正式条件待落实；一致性检查PASS | 主分支required checks/签名/受控制品与正式Runner治理未验收。 |
| 14 | 配置Runner Secret和分支保护<br>平台管理员执行，Codex生成操作手册 | 给出CPU/Docker/GPU Runner用途、Secret示例及主分支保护实测方法，只读观察平台。<br>[ci-administrator-guide.md](<../ci-administrator-guide.md>) | 工程产物/实际证据分别核验；正式条件待落实 | 平台套餐/实际管理员、保护生效及未授权直推/失败不可合并正反验证待落实。 |
| 15 | 执行自动化验证并形成报告<br>Codex执行，人工复核失败项 | 执行来源/配置一致性、实际py310版本和启动/质量/测试/扫描/夹具，记录未执行与正式阻断。<br>[development-environment-validation-report.md](<../development-environment-validation-report.md>)、[validate_stage_three.py](<../../../scripts/validate_stage_three.py>)、[stage-three-runtime-report.json](<../../00-project/validation/stage-three-runtime-report.json>) | 工程产物/实际证据分别核验；正式条件待落实；一致性检查PASS | GPU/真实模型/业务数据/正式网络/Windows原生未验；共享栈未重建/恢复；扫描跳过不判安全。 |
| 16 | 验收并冻结开发环境基线<br>人工批准后Codex固化 | 形成开发环境基线/变更/验收候选与真实缺项，未获完整决定不冻结/改ADR/打标签。<br>[development-environment-baseline.md](<../development-environment-baseline.md>)、[development-environment-change-request.md](<../development-environment-change-request.md>)、[development-environment-acceptance-record.md](<../development-environment-acceptance-record.md>) | 评审/验收材料已准备，实际决定待填 | 完整实际决定、责任人、技术/安全输入、主分支保护及资源整改待落实，NOT_FROZEN。 |

## 各步骤原输入和验收要求

### 第1步 确定仓库平台 仓库名称及管理人员

源责任方式：人工决策，Codex形成比较报告和决策表。必要输入：仓库平台候选、内外网条件、团队角色、运维和采购约束。

源目标产物：docs/03-development/repository-platform-options.md；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 至少比较两种可落地平台
- 推荐方案说明适用前提
- 未创建外部仓库或账号
- 管理人员使用角色占位符

实际操作：保留用户指定私有GitHub仓库和实际名称，补内网平台比较与职责/准入条件。。剩余条件：实际项目/技术/仓库管理人员及正式生产代码平台准入未落实。

### 第2步 确定Monorepo或多仓库模式

源责任方式：人工决策，Codex分析。必要输入：项目模块、团队边界、发布节奏及权限隔离要求。

源目标产物：repository-structure-decision.md及ADR-013草案；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 比较两种模式
- 模型权重不进入普通Git
- ADR状态为待批准

实际操作：沿用既有Monorepo，比较多仓模式并生成独立ADR-013候选，不搬迁旧文件。。剩余条件：实际团队边界和结构正式批准待填。

### 第3步 明确网络 安全和Codex权限边界

源责任方式：人工确定，Codex生成模板与权限矩阵。必要输入：网络边界、允许操作、数据分类和审批角色。

源目标产物：docs/03-development/codex-permission-boundary.md；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 覆盖文件、Git、网络、容器、数据和GPU
- 每项有审批与审计方式
- 未把建议写成已授权

实际操作：区分本次会话授权、正式环境边界和禁止数据；保留操作审计与撤销要求。。剩余条件：正式网络、生产目录、审批角色/期限及真实数据用途授权待落实。

### 第4步 建立仓库和团队账号权限

源责任方式：仓库管理员执行，Codex生成配置建议。必要输入：已批准平台、团队角色和最小权限原则。

源目标产物：docs/03-development/repository-access-control.md；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 主分支合并严格受控
- Secret与Runner权限单列
- 有权限回收机制

实际操作：登记真实仓库所有者与专业角色候选矩阵，不创建账号或虚构团队。。剩余条件：真实团队账号、最小权限开通/回收及主分支/Secret管理权限未验收。

### 第5步 根据技术基线设计目录结构

源责任方式：Codex设计，技术负责人评审。必要输入：Technical Baseline 1.0、系统设计方案和任务分解书。

源目标产物：docs/03-development/repository-layout.md；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 目录职责无重叠
- 禁止提交内容明确
- 未迁移文件

实际操作：说明原13目录与data-pipeline/tools的用途、依赖与禁止内容。。剩余条件：实际责任团队、目录/模块发布边界评审待确认。

### 第6步 人工评审目录和分支策略

源责任方式：人工评审，Codex准备评审包。必要输入：目录方案、结构决策、访问控制和技术基线。

源目标产物：docs/03-development/repository-review-package.md；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 评审点可逐项确认
- 含批准角色和日期
- 未提前冻结方案

实际操作：准备评审议程、分支/审核/标签/紧急流程与决定模板，不代签。。剩余条件：实际评审者、会议/日期、分支及审核人数决定未提供。

### 第7步 初始化仓库和基础文件

源责任方式：Codex执行，技术负责人监督。必要输入：获批目录和分支策略。

源目标产物：仓库目录与基础治理文件；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 结构与批准方案一致
- 基础文件齐全
- 未破坏已有文件
- 无真实凭据

实际操作：补贡献/安全/所有者/格式/环境模板等基础文件，保留全部原件与历史。。剩余条件：治理文件正式审核与实际人员策略待确认；只证明创建和验证。

### 第8步 配置前端 后端和算法开发环境

源责任方式：Codex执行，相关负责人评审。必要输入：批准的框架和版本、离线软件源条件。

源目标产物：前后端和算法依赖配置与锁文件；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 版本与基线一致
- 模块依赖隔离
- 锁文件已生成
- 未验证项明确

实际操作：沿用原100包py310/Node/前端/合成推理，另锁pre-commit工具层，不升级业务栈。。剩余条件：Linux CPU组合可验证；Windows原生安装、生产新Python/GPU/离线准入未完成。

### 第9步 配置格式化 静态检查和测试工具

源责任方式：Codex执行，测试负责人评审。必要输入：仓库结构、语言版本和编码规范。

源目标产物：质量工具配置和统一检查命令；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 前后端检查完整
- 本地与CI一致
- 未大规模改写
- 结果可机器读取

实际操作：统一原Ruff/TS/测试与新增格式、pre-commit、依赖/秘密扫描，记录工具适用范围与跳过项。。剩余条件：未选择工具不当已启用；旧代码格式债务/完整静态类型方案与正式质量制度待定，Torch发行包审计覆盖仍待。

### 第10步 编写AGENTS.md等Codex规则

源责任方式：Codex生成，技术负责人审核。必要输入：项目资料、技术基线、目录与安全要求。

源目标产物：AGENTS.md、CONTRIBUTING.md、SECURITY.md和CODEOWNERS候选版；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 边界和停止条件清楚
- 验证命令明确
- 状态为待审核

实际操作：补根规则的阶段/命令/冲突要求和项目Codex配置，继承用户模型及权限设置。。剩余条件：项目层信任/不同客户端加载及实际审核待确认，不将文档当技术强制控制。

### 第11步 建立最小骨架工程

源责任方式：Codex实现，技术负责人监督。必要输入：已批准仓库结构和接口约定。

源目标产物：前端 后端 算法服务最小骨架及测试；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 三类服务可独立启动
- 调用链可验证
- 使用模拟数据和模型
- 具备测试与日志

实际操作：沿用7服务真实合成链路，另实现三进程Vue/FastAPI/模拟推理夹具，具备health/ready/安全错误/trace和实际浏览器测试。。剩余条件：夹具只是模拟连通性；现有PoC依旧真实合成M15，53接口/62表/34能力及完整业务不在本阶段完成。

### 第12步 建立本地开发启动命令

源责任方式：Codex执行，开发负责人评审。必要输入：现有模块启动测试构建方式。

源目标产物：Makefile或等价任务文件及README更新；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 统一入口可用
- Windows与Linux方式明确
- clean无误删风险
- README与命令一致

实际操作：建立Linux Make/Python入口与Windows PowerShell经SSH入口，非零失败、缓存清理保护和共享栈容量保护。。剩余条件：共享Docker盘容量不足；build/integration/ci受保护，Windows原生/正式现场安装仍待。

### 第13步 建立基础CI流水线

源责任方式：Codex生成，测试和技术负责人审核。必要输入：代码平台、质量工具和测试命令。

源目标产物：GitLab CI或GitHub Actions配置；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 普通Runner不依赖GPU
- 含安全与契约测试
- 未发布或部署

实际操作：沿用25门禁CPU托管CI，接入第三阶段原件/16步/统一命令/夹具与质量检查，不发布生产。。剩余条件：主分支required checks/签名/受控制品与正式Runner治理未验收。

### 第14步 配置Runner Secret和分支保护

源责任方式：平台管理员执行，Codex生成操作手册。必要输入：CI平台、Runner资源、Secret类别和分支策略。

源目标产物：docs/03-development/ci-administrator-guide.md；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- Runner按用途隔离
- Secret无真实值
- 主分支保护明确
- 有验证方法

实际操作：给出CPU/Docker/GPU Runner用途、Secret示例及主分支保护实测方法，只读观察平台。。剩余条件：平台套餐/实际管理员、保护生效及未授权直推/失败不可合并正反验证待落实。

### 第15步 执行自动化验证并形成报告

源责任方式：Codex执行，人工复核失败项。必要输入：完整仓库骨架、开发环境和CI配置。

源目标产物：development-environment-validation-report.md；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 结果可复核
- 状态严格区分
- 失败项有修复建议
- 明确冻结条件

实际操作：执行来源/配置一致性、实际py310版本和启动/质量/测试/扫描/夹具，记录未执行与正式阻断。。剩余条件：GPU/真实模型/业务数据/正式网络/Windows原生未验；共享栈未重建/恢复；扫描跳过不判安全。

### 第16步 验收并冻结开发环境基线

源责任方式：人工批准后Codex固化。必要输入：明确批准记录和完整验证报告。

源目标产物：Development Environment Baseline 1.0及变更文件；本仓实际位置按上表输出阅读。

原验收要求（要求本身不等于已完成的判断）：

- 冻结依据存在
- 只冻结获批内容
- 版本配置文档一致
- 有变更和回滚机制

实际操作：形成开发环境基线/变更/验收候选与真实缺项，未获完整决定不冻结/改ADR/打标签。。剩余条件：完整实际决定、责任人、技术/安全输入、主分支保护及资源整改待落实，NOT_FROZEN。

## 源建议与既有工程的适用差异

- 仓库名称沿用用户指定media-traceability-system；不另建示例名、不重复账号/环境。
- 一级目录沿用原13目录，补data-pipeline/tools预留职责；不搬移原文件，不增加重复Schema。
- Element Plus/ECharts、Transformers/MMEngine、Black/MyPy/ESLint/Stylelint等并未由实际技术源选定；本次不将它们伪装为已安装或冻结。当前实际质量范围是Ruff、TS、Pytest/Vitest、契约、pre-commit和依赖/秘密检查。新增工具或全量旧代码格式规范另评审/验证。
- 最小工程复用已有7服务和真实合成M15，mock=false并有明确非业务标识；不会改成假业务模型。已有后端/api/v1/health是鉴权后的数据库SELECT1，进程存活用/healthz，内部推理有/healthz。另建仓库内tools/stage_three_demo夹具实现三独立进程的Vue健康页、/api/v1/health、/api/v1/ready和模拟推理入口，并经浏览器实际验证。夹具不连已有数据库/对象存储、不加载权重，不是53业务API或34能力的新增实现。
- Windows默认入口经SSH协调Linux py310，实际Windows原生py310安装未开展；Linux与GitHub隔离Runner是当前可验证的组合。
- pre-commit配置与隔离工具层可以运行，Git hook是否安装由开发者选择；配置存在不等于实际钩子/平台保护已生效。

## 开发入口与容量保护

Linux使用已验证的`/opt/conda/glwy/envs/py310/bin/python scripts/dev.py help`；当前服务器make未安装，Makefile仅作已有make环境的可选等价入口。Windows：`& .\scripts\dev.ps1 help`，SSH协调入口已验证，原生安装未验证。全部命令、环境与审计见[CONTRIBUTING.md](<../../../CONTRIBUTING.md>)。dev默认观察已运行栈，clean默认只预览缓存；完整构建/集成在共享服务器上须显式命令标志和足够容量。

服务器研发数据盘位于Linux的Docker Desktop虚拟机，既有快照为99%使用率；本次未扩容，不能把宿主/workspace空闲容量当卷内容量。当前防护阈值5GiB只是研发操作保护，正式项目配额仍待确定。Docker服务变化和恢复类验证优先在GitHub独立临时Runner执行；当前共享栈维持运行。

## 正式完成与下一阶段

当前允许按已明确输入继续合成CPU基础开发；不能将第三阶段文档或CI转为生产准入、真实数据授权、真实GPU/34模型达标或全部170任务完成。正式冻结还需人员/账号权限、实际技术与安全输入、主分支保护、资源整改、适用质量结果及完整批准。三服务夹具的ready/健康页/模拟入口与原PoC均有独立范围说明，不能把夹具成功充当真实模型/业务实现。

第一/第二阶段剩余工作仍按[remaining-work-navigation.md](<../../00-project/remaining-work-navigation.md>)管理，未因此自动关闭；第三阶段正式基线见[development-environment-baseline.md](<../development-environment-baseline.md>)及[development-environment-acceptance-record.md](<../development-environment-acceptance-record.md>)。
