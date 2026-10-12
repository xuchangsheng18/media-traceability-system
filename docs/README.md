# 项目文档导航

本导航说明docs中各文档的含义、使用顺序、质量要求和来源关系。2026-10-12修订；当前CPU研发最小工程已运行并通过本机CI；正式业务/生产仍NOT_FROZEN。文档、结构校验、研发闭环与正式业务验收分别判定。

## 建议阅读顺序

1. 先读[当前状态](00-project/repository-readiness.md)、[范围](00-project/project-scope.md)、[来源清单](00-project/source-document-inventory.md)和[未决问题](00-project/open-questions.md)。
2. 再读需求、用例和业务规则，确认系统需要处理什么。
3. 阅读架构、模块边界和仓库目录，确认代码归属与调用关系。
4. 将API、数据库字典、SQL和状态机一起阅读，核对每个字段、关系与行为。
5. 算法工作结合模型契约、数据集和评测规范；业务工作结合权限和审计规则。
6. 从根目录[任务卡](../tasks/README.md)选择工作，读取关联测试、开发规范和部署限制。

## 文档权威与格式

两份修订Word是总体设计和任务来源；docs中的机器契约把设计转为可检验的字段与结构。发生冲突时须登记并协调，不能自动认定新生成文件覆盖了业务决定。原件不改写，候选新增规则要标注工程提案。

Markdown（.md）用于解释；YAML/JSON用于结构化定义和检查；CSV用于表格查看；SQL用于数据库定义；Word/PPT保存来源。格式可机器读取不意味着内容完整、正确或正式生效。

## 目录总览

| 目录 | 职责 |
| --- | --- |
| [00-project](00-project/README.md) | 项目范围 来源 状态和验证 |
| [01-requirements](01-requirements/README.md) | 需求 角色和用例 |
| [02-architecture](02-architecture/README.md) | 架构 模块和目录 |
| [03-api](03-api/README.md) | 业务与内部推理接口 |
| [03-development](03-development/README.md) | 开发约定与建设顺序 |
| [04-database](04-database/README.md) | 数据库定义与字段来源 |
| [05-workflows](05-workflows/README.md) | 任务 审核与证据状态机 |
| [06-algorithms](06-algorithms/README.md) | 模型能力与评测 |
| [07-datasets](07-datasets/README.md) | 数据集 标注与划分 |
| [08-security](08-security/README.md) | 安全 权限和审计 |
| [09-testing](09-testing/README.md) | 测试计划和验收 |
| [10-deployment](10-deployment/README.md) | 环境观测与部署规划 |
| [source](source/) | 原始业务材料和当前修订原件 |
| [_converted](_converted/) | 原件转换稿和转换限制 |
| [guides](guides/) | 阶段工作手册 |
| [assets](assets/) | 来源图像等配套附件 |

## 00-project 项目范围 来源 状态和验证

回答项目做什么、依据是什么、哪些已确认、检查过什么。不能把已同步、结构通过、正式冻结和业务实现混为同一状态。

| 文件 | 含义及使用要求 |
| --- | --- |
| [repository-readiness.md](00-project/repository-readiness.md) | 当前资料、Git、服务和验证状态。历史数量与当前构建统计有差异时，以本轮报告为准。 |
| [project-scope.md](00-project/project-scope.md) | 12模块、170任务及场景的范围与外部边界；分阶段不等于删功能。 |
| [glossary.md](00-project/glossary.md) | 统一业务和工程术语，尤其同源、片段、原件、证据及版本含义。 |
| [source-document-inventory.md](00-project/source-document-inventory.md) | 人类可读的原件、修订稿、流程手册与摘要清单。 |
| [source-inventory.json](00-project/source-inventory.json) | 用于核验源文件未被改写的归档路径、来源路径和SHA-256。 |
| [document-conversion-plan.md](00-project/document-conversion-plan.md) | 转换目标、处理方法及保留原件的规则。 |
| [document-governance.md](00-project/document-governance.md) | 来源优先级、候选身份和变更管理规则。 |
| [open-questions.md](00-project/open-questions.md) | 尚待确定的业务、资源与技术问题说明。 |
| [open-questions.yaml](00-project/open-questions.yaml) | 未决事项的机器索引，不能自动将未知改为已解决。 |
| [requirement-traceability.md](00-project/requirement-traceability.md) | 需求与用例、接口、表、模型、任务和测试的阅读矩阵。 |
| [requirement-traceability.yaml](00-project/requirement-traceability.yaml) | 用于检查追踪覆盖与断链的机器记录。 |
| [review-decisions.yaml](00-project/review-decisions.yaml) | 已记录决定和用户选择；空决定列表不能充当批准。 |
| [review-decision-application-report.md](00-project/review-decision-application-report.md) | 决定如何同步到设计和契约，以及未生效项。 |
| [freeze-checklist.md](00-project/freeze-checklist.md) | 冻结前应检查的项目；不是已通过证明。 |
| [baseline-1.0.md](00-project/baseline-1.0.md) | 开发输入候选基线说明，当前NOT_FROZEN。 |
| [baseline-file-list.txt](00-project/baseline-file-list.txt) | 某次基线整理的文件路径清单，不是执行结果。 |
| [baseline-file-manifest.json](00-project/baseline-file-manifest.json) | 归档的上游输入快照摘要；当前交付用repository-file-manifest。 |
| [baseline-validation-report.md](00-project/baseline-validation-report.md) | 验证范围、报告位置和没有验证的事项。 |
| [build-counts.json](00-project/build-counts.json) | 当前工程输入数量统计；数量不等于功能完成率。 |
| [repository-file-manifest.json](00-project/repository-file-manifest.json) | 本次实际交付文件摘要，用于本地和服务器核对，排除自身及同步回执。 |
| [server-sync-receipt.json](00-project/server-sync-receipt.json) | 服务器同步目标、时间、摘要核验与更新结果。 |
| [upstream-file-manifest.json](00-project/upstream-file-manifest.json) | 本轮仓库适配前的上游文件摘要，供对比。 |
| [upstream-package-readme.md](00-project/upstream-package-readme.md) | 上游资料包原始说明，属于历史状态。 |
| [adaptation-diff.json](00-project/adaptation-diff.json) | 初次仓库适配的新增、修改及保留记录，不覆盖后续修订历史。 |
| [change-log.md](00-project/change-log.md) | 按轮记录修订原因、影响和边界。 |
| [official-sources.md](00-project/official-sources.md) | 原输入包采用的技术来源及对应说明。 |
| [official-sources.yaml](00-project/official-sources.yaml) | 上述技术来源的机器索引。 |
| [补齐完成说明.md](00-project/补齐完成说明.md) | 原输入包补齐内容与状态边界。 |

`review-package/`是范围、业务、权限、算法、数据与验收等分领域审查输入；`validation/`保存检查记录，`validation/upstream/`是上游历史证据。阅读报告须核对文件摘要、时间、环境及未执行项。

## 01-requirements 需求 角色和用例

每项需求应有可验证行为、异常及授权范围。性能等未确定数值保留待定，不把建议值冒充验收阈值。

| 文件 | 含义及使用要求 |
| --- | --- |
| [functional-requirements.md](01-requirements/functional-requirements.md) | 系统必须提供的业务功能及编号。 |
| [non-functional-requirements.md](01-requirements/non-functional-requirements.md) | 性能、可靠性、维护、安全等约束及验证口径。 |
| [business-rules.md](01-requirements/business-rules.md) | 控制业务行为的规则；区分规则建议和已确认决定。 |
| [user-roles.md](01-requirements/user-roles.md) | 角色职责及访问边界，不能只列角色名称。 |
| [engineering-requirements.yaml](01-requirements/engineering-requirements.yaml) | 与工程任务对应的要求和编号。 |

[use-cases/](01-requirements/use-cases/README.md)按12模块分别描述正常、备选、异常和授权流程；不能把页面原型数量直接当作功能穷尽。

## 02-architecture 架构 模块和目录

说明为什么如此拆分、谁负责什么、数据如何流转。架构目录是设计依据，不能被理解成所有服务已经存在。

| 文件 | 含义及使用要求 |
| --- | --- |
| [system-architecture.md](02-architecture/system-architecture.md) | 五层系统架构、服务关系与核心处理链路。 |
| [module-boundaries.md](02-architecture/module-boundaries.md) | 十二业务模块的职责及协作边界。 |
| [repository-layout.md](02-architecture/repository-layout.md) | 顶层和计划子目录的文件归属、依赖方向与禁止内容。 |
| [data-flow.md](02-architecture/data-flow.md) | 原件、派生对象、任务、证据和各存储间的一致性职责。 |
| [technical-baseline.md](02-architecture/technical-baseline.md) | 候选技术和验证要求，尚未锁定生产依赖。 |

[architecture-decisions/](02-architecture/architecture-decisions/README.md)保存决策提案和模板；应记录候选、理由、验证、影响及决定状态。

## 03-api 业务与内部推理接口

接口契约是字段和行为的共同约定。必须同时明确鉴权、状态、错误、版本和业务语义；结构合法不能代替业务正确。

| 文件 | 含义及使用要求 |
| --- | --- |
| [openapi.yaml](03-api/openapi.yaml) | 外部业务API唯一结构源：路径、参数、请求响应、错误和安全声明。 |
| [inference-openapi.yaml](03-api/inference-openapi.yaml) | 业务后端调用内部算法的入口，与外部API隔离。 |
| [api-design.md](03-api/api-design.md) | 幂等、版本条件、异步、分页、媒体访问及通用数据表达规则。 |
| [error-codes.md](03-api/error-codes.md) | 错误分类、稳定错误码、客户端处理及信息泄露边界。 |
| [operation-index.json](03-api/operation-index.json) | 操作ID与任务、数据表的关联索引。 |

[examples/](03-api/examples/)是请求响应合成样例，每个文件名对应Schema；不是服务器实际返回或真实数据。

## 03-development 开发约定与建设顺序

说明如何从当前输入资料进入可运行工程。只有真实安装、构建和测试成功，才能登记对应工程任务完成。

| 文件 | 含义及使用要求 |
| --- | --- |
| [coding-standards.md](03-development/coding-standards.md) | 编码、命名、变更和检查规范；校验依赖不等于业务依赖。 |
| [repository-bootstrap.md](03-development/repository-bootstrap.md) | 仓库、基础环境、最小闭环、算法与交付的推进顺序。 |

## 04-database 数据库定义与字段来源

数据库是工程基础。字段说明必须解释业务含义，并列出精确来源；列约束、表约束、触发器、RLS和应用层规则分别标明，不以“见来源契约”占位。

| 文件 | 含义及使用要求 |
| --- | --- |
| [database-design.md](04-database/database-design.md) | 数据库职责、关系、事务与版本设计的总说明。 |
| [initial-schema.sql](04-database/initial-schema.sql) | 新空库候选初始化SQL，包含表、约束、权限、触发器及字段注释；不能直接覆盖现有业务库。 |
| [data-dictionary.md](04-database/data-dictionary.md) | 数据字典：逐表逐字段的类型、约束、含义与精确来源。 |
| [table-catalog.json](04-database/table-catalog.json) | 结构化表目录，保存字段定义和表级关系；应与SQL和字典同步。 |
| [field-provenance.json](04-database/field-provenance.json) | 逐字段来源索引：定义状态、JSON Pointer、SQL对象和实际API字段映射。 |
| [er-diagram.md](04-database/er-diagram.md) | 表关系图，便于阅读；完整复合外键以SQL和字典为准。 |
| [api-field-mapping.md](04-database/api-field-mapping.md) | 接口到数据库的映射原则与典型对象解释。 |
| [api-field-mapping.csv](04-database/api-field-mapping.csv) | 按操作、方向和字段路径排列的可表格查看映射。 |
| [api-field-mapping.json](04-database/api-field-mapping.json) | 用于校验的机器映射，包括嵌套字段。 |
| [database-validation.md](04-database/database-validation.md) | 初始化与约束验证的方法及环境边界。 |
| [first-source-ranking.md](04-database/first-source-ranking.md) | 首发排序批次、0—3候选、版本、连续名次、唯一性及API语义。 |
| [database-design-references.md](04-database/database-design-references.md) | 本轮查阅的PostgreSQL/OpenAPI/JSON Schema官方机制及采用方式。 |
| [database-revision-audit.md](04-database/database-revision-audit.md) | 本轮修订内容、技术边界与未执行事项。 |

## 05-workflows 任务 审核与证据状态机

应给出合法转移、触发条件、操作者、前置版本、失败和恢复行为。数据库状态枚举只限制取值，不能单独实现完整状态机。

| 文件 | 含义及使用要求 |
| --- | --- |
| [task-state-machine.md](05-workflows/task-state-machine.md) | 分析任务运行、失败、取消、重算与版本行为。 |
| [review-state-machine.md](05-workflows/review-state-machine.md) | 人工复核、退回和结果版本绑定。 |
| [evidence-state-machine.md](05-workflows/evidence-state-machine.md) | 证据记录、固化和更正的状态与历史保护。 |

## 06-algorithms 模型能力与评测

明确模型输入输出、版本和失败语义。候选模型、模拟输出、真实权重运行和验收通过必须分开登记。

| 文件 | 含义及使用要求 |
| --- | --- |
| [model-list.md](06-algorithms/model-list.md) | 模型方向及使用目的的阅读清单。 |
| [model-catalog.yaml](06-algorithms/model-catalog.yaml) | 模型编号、能力、关联任务和数据集的机器目录。 |
| [model-contract.md](06-algorithms/model-contract.md) | 请求响应、缺失模态、错误、证据与模型版本约定。 |
| [model-evaluation.md](06-algorithms/model-evaluation.md) | 评测分组、统计口径、指标及证据要求。 |

## 07-datasets 数据集 标注与划分

数据目录不代表数据已经获取或授权。记录来源、用途、计数单位、标签和版本，避免同源素材跨训练与测试集合泄漏。

| 文件 | 含义及使用要求 |
| --- | --- |
| [dataset-catalog.md](07-datasets/dataset-catalog.md) | 数据集类别、用途及对应模型方向。 |
| [annotation-specification.md](07-datasets/annotation-specification.md) | 标注结构、质量检查和复核要求。 |
| [dataset-split-policy.md](07-datasets/dataset-split-policy.md) | 按来源组等条件划分，隔离验证、校准与封存测试用途。 |
| [data-compliance.md](07-datasets/data-compliance.md) | 来源许可、用途、访问、保留与回流约束。 |
| [data-card-template.md](07-datasets/data-card-template.md) | 新增或发布数据版本需填写的数据卡模板。 |

## 08-security 安全 权限和审计

同时核验功能权限与单位、案件、对象范围。文件写了控制要求不代表已完成安全实现或测评。

| 文件 | 含义及使用要求 |
| --- | --- |
| [security-design.md](08-security/security-design.md) | 安全边界、输入处理、访问和敏感信息保护设计。 |
| [permission-matrix.md](08-security/permission-matrix.md) | 角色与动作权限的对应关系及限制。 |
| [data-classification.md](08-security/data-classification.md) | 数据类别、敏感性和处理要求。 |
| [audit-requirements.md](08-security/audit-requirements.md) | 应记录的主体、对象、版本、动作、结果与追踪信息。 |

## 09-testing 测试计划和验收

每个场景应有输入、步骤、预期及关联需求；只有实际报告和适用环境能证明测试执行。

| 文件 | 含义及使用要求 |
| --- | --- |
| [test-strategy.md](09-testing/test-strategy.md) | 测试层级、数据、环境和执行策略。 |
| [acceptance-criteria.md](09-testing/acceptance-criteria.md) | 交付判定口径和不能省略的证据。 |
| [test-scenarios.yaml](09-testing/test-scenarios.yaml) | 业务功能正常与异常场景。 |
| [task-test-scenarios.yaml](09-testing/task-test-scenarios.yaml) | 各任务的验证场景，不等同已实现测试程序。 |
| [model-test-scenarios.md](09-testing/model-test-scenarios.md) | 模型效果、未知、鲁棒性及评测划分测试。 |
| [security-test-scenarios.md](09-testing/security-test-scenarios.md) | 鉴权、越权、撤销、输入和审计等测试。 |

## 10-deployment 环境观测与部署规划

区分现场事实、资源配额、部署候选和已运行服务。单机容器不是主机级高可用，整机资源不等于项目独占。

| 文件 | 含义及使用要求 |
| --- | --- |
| [deployment-plan.md](10-deployment/deployment-plan.md) | 服务、运行数据、配置和后续部署交付要求。 |
| [server-observation.md](10-deployment/server-observation.md) | 归档前服务器的时点观测；不能当实时环境或归档后文件数。 |

## 来源和转换资料

- [source/original/](source/original/)保存五类原始业务材料：详细设计、任务分解、数据与训练说明、模型推荐、界面原型。
- [source/revisions/](source/revisions/)保存总体设计V1.4和任务书V1.3；两文件保持相对链接和字节摘要。
- [guides/](guides/)保存三份阶段手册，是组织工作的方法依据，不自动成为业务功能。
- [_converted/](_converted/)分original、revision、guide保存检索文本；[转换报告](_converted/conversion-report.md)说明图表和版式限制。
- [assets/](assets/)保存配套图像；来源图和算法证据图不能混作同一类文件。

## 数据字典和来源契约的准确含义

data-dictionary意为数据字典。每行应解释字段类型、可空性、默认值、业务含义和实际约束；每表还应列出复合外键、唯一性及触发器。它不是仅列字段名的清单。

本次已将“见来源契约”占位改成字段定义、SQL对象和实际API映射。“契约”指软件各部分共同遵守的字段和行为约定，不是合同。以首发候选为例：

| 字段 | 含义 | 可定位依据 |
| --- | --- | --- |
| cluster_id | 所属的同案件内容簇 | 字典first_source_candidate；SQL复合外键；FirstSource.cluster_id |
| asset_id | 本簇内被列为候选的媒体资产 | cluster_member成员外键；FirstSource.candidates[].asset_id |
| rank | 同一ranking_id内从1开始的连续名次，最多3 | CHECK、批次内UNIQUE、完整性触发器；FirstSource.candidates[].rank |

详细规则见[首发排序契约](04-database/first-source-ranking.md)和[逐字段来源索引](04-database/field-provenance.json)。CHECK只限制单行名次，不能独自限制总条数；API数组maxItems也不能替代数据库完整性。

## 与docs之外文件的关系

| 根目录位置 | 职责 |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | 已明确的工程修改和验证规则 |
| [tasks/](../tasks/README.md) | 独立任务卡、backlog和依赖；计划输出不等于已有代码 |
| [schemas/](../schemas/) | 模型、数据和API结构；外部API派生结构与OpenAPI同步 |
| [datasets/](../datasets/) | 数据集目录元信息，不保存真实样本 |
| [tests/](../tests/) | 合成夹具、数据库约束检查和后续测试实现 |
| [scripts/](../scripts/) | 文档、输入和隔离数据库校验工具 |
| backend、frontend、ai-services、deploy等 | 当前为规划目录，后续实现归属见架构目录 |

## 使用前检查

确认文件适用版本；确认字段来源可定位；确认表级与应用层约束没有混淆；确认相关测试实际执行而非只写计划；未决事项影响哪项工作就处理哪项，不把全部未知自动当作所有工作的阻断。

文档入口检查使用`python scripts/validate_repository_docs.py`；输入结构检查使用`python scripts/validate_inputs.py`；隔离数据库测试使用`python scripts/validate_database_foundation.py --ssh-host 172.16.58.179`。后者会创建并清理独立临时容器，不操作已有业务库。准确验证范围见报告。

## 第二阶段目录建设说明

根目录README负责全项目入口；截图中的13个顶层目录各自README负责职责、当前文件、第二阶段计划、验证方式及缺项。详见[第二阶段23步状态](03-development/stage-two-readiness.md)和[机器交付清单](03-development/stage-two-deliverables.json)。本轮已补齐这些说明，前后端和最小工程的实现状态仍须分别验证。

目录入口：[frontend](../frontend/README.md)、[backend](../backend/README.md)、[ai-services](../ai-services/README.md)、[shared-contracts](../shared-contracts/README.md)、[schemas](../schemas/README.md)、[config](../config/README.md)、[deploy](../deploy/README.md)、[scripts](../scripts/README.md)、[tests](../tests/README.md)、[datasets](../datasets/README.md)、[prompts](../prompts/README.md)、[tasks](../tasks/README.md)。docs自身使用本导航。

## 本轮数据库基础的补充结果

[data-dictionary.md](04-database/data-dictionary.md)逐项解释62表824字段；[field-provenance.json](04-database/field-provenance.json)列SQL位置、结构指针、可空性、默认值、外键及接口映射。工程解释与总体设计来源分开，不再用一条无法定位的“来源契约”替代字段说明。

首发候选沿用批次、结果版本、Top-3、唯一和完整提交约束，另加入支持/反对证据JSON结构、UUID格式、去重、存在及同案件检查。详见[首发排序与证据契约](04-database/first-source-ranking.md)。证据存在并不自动证明支持关系或授权用途，应用仍须复核。

[官方机制依据](04-database/database-design-references.md)记录本轮查阅的PostgreSQL和JSON Schema资料；[数据库报告](00-project/validation/database-foundation-report.json)、[契约报告](00-project/validation/database-contract-report.json)及[导航覆盖报告](00-project/validation/documentation-completion-report.json)分别表示实际测试范围。当前仍为规划候选，完整应用及生产验收未因本轮补充完成。

## 第二阶段实际工程文档

当前入口与适用要求：

| 文档 | 含义与严格判定要求 |
| --- | --- |
| [02-architecture/environment-constraints.md](<02-architecture/environment-constraints.md>) | 实际Linux、Miniforge py310、Desktop挂载/网络/CPU与PythonEOL边界。 |
| [02-architecture/resource-and-team-inventory.md](<02-architecture/resource-and-team-inventory.md>) | 宿主、Desktop虚拟机与容器配额分别盘点；磁盘、GPU与责任人未决。 |
| [02-architecture/technical-baseline.md](<02-architecture/technical-baseline.md>) | 1.0-py310-cpu研发执行基线，区别于正式生产冻结和全部业务实现。 |
| [02-architecture/technology-options.md](<02-architecture/technology-options.md>) | 12个技术域的替代方案、研发执行选择、实测和扩展边界。 |
| [02-architecture/compatibility-matrix.md](<02-architecture/compatibility-matrix.md>) | 实际锁定组合、安装/构建/运行兼容证据及升级路径。 |
| [02-architecture/licenses.md](<02-architecture/licenses.md>) | 包/镜像/FFmpeg/Desktop与权重的许可盘点、审核缺口和再分发要求。 |
| [02-architecture/security-baseline.md](<02-architecture/security-baseline.md>) | 研发鉴权、秘密、输入、日志和网络措施；正式身份/案件/审计等差距。 |
| [02-architecture/technical-validation-report.md](<02-architecture/technical-validation-report.md>) | 各真实检查结果、证据路径、范围和未测事项。 |
| [02-architecture/technical-baseline-change-control.md](<02-architecture/technical-baseline-change-control.md>) | 开发快照、正式冻结、ADR/锁/迁移变更和恢复规则。 |
| [02-architecture/stage-two-official-sources.md](<02-architecture/stage-two-official-sources.md>) | 本轮官方兼容、机制与许可来源；网页不替代部署实测。 |
| [02-architecture/non-functional-requirements.md](<02-architecture/non-functional-requirements.md>) | 引用原非功能需求源并登记实测口径，不另造正式指标。 |
| [03-development/ci-cd.md](<03-development/ci-cd.md>) | 同源本机CI、失败阻断、Runner前提及尚未运行的托管平台边界。 |
| [03-development/contract-generation.md](<03-development/contract-generation.md>) | 两份权威OpenAPI生成TS类型；当前Celery开发命令及事件缺口。 |
| [03-development/stage-two-readiness.md](<03-development/stage-two-readiness.md>) | 23步实际开发状态和未完成的正式条件。 |
| [03-development/stage-two-deliverables.json](<03-development/stage-two-deliverables.json>) | 逐步机器对照；保留计划并区分开发验证与正式完成。 |
| [10-deployment/development-runbook.md](<10-deployment/development-runbook.md>) | 真实启动、复建、SSH页面访问、令牌、端口、卷、停止与排查。 |
| [03-api/poc-api.md](<03-api/poc-api.md>) | 已实现PoC入口和53操作正式契约的区别，鉴权/错误与合成模型范围。 |
| [04-database/poc-database.md](<04-database/poc-database.md>) | 独立开发3表、outbox、幂等与租约；区别于62表业务字典/SQL。 |
| [00-project/review-package/technical-baseline-review.md](<00-project/review-package/technical-baseline-review.md>) | 实际技术评审输入与待正式确认事项，不能自动充当批准。 |
| [00-project/validation/environment-inventory.json](<00-project/validation/environment-inventory.json>) | 实际宿主/引擎/服务版本、上限和时点快照；不是峰值或独占配额。 |
| [00-project/validation/ci-all-report.json](<00-project/validation/ci-all-report.json>) | 本机完整门禁逐命令实际状态、耗时与执行范围；托管执行为false。 |
| [00-project/validation/ci-report.json](<00-project/validation/ci-report.json>) | 最近一次正常CI入口执行报告；详细阶段与范围须核对。 |
| [00-project/validation/ci-failure-probe-report.json](<00-project/validation/ci-failure-probe-report.json>) | 故意插入失败后的真实非零门禁报告；FAIL为探针预期。 |
| [00-project/validation/ci-failure-gate-report.json](<00-project/validation/ci-failure-gate-report.json>) | 验证故意失败确实阻断构建/部署的判定，PASS不等于探针本身成功。 |
| [00-project/validation/runtime-lock-report.json](<00-project/validation/runtime-lock-report.json>) | 实际Python补丁与全部第三方包是否匹配精确锁。 |
| [00-project/validation/lock-reproduction-report.json](<00-project/validation/lock-reproduction-report.json>) | 全新venv按精确锁安装后的依赖与导入结果。 |
| [00-project/validation/generated-contract-report.json](<00-project/validation/generated-contract-report.json>) | 两份TS类型临时重新生成后的字节一致性。 |
| [00-project/validation/poc-integration-report.json](<00-project/validation/poc-integration-report.json>) | 15项真实浏览器服务/API/对象/SQL/队列/CPU结果检查，不是业务模型验收。 |
| [00-project/validation/poc-resilience-report.json](<00-project/validation/poc-resilience-report.json>) | 5项队列/过期租约/服务及版本对象重启/幂等冲突检查，服务恢复记录。 |
| [00-project/validation/media-query-report.json](<00-project/validation/media-query-report.json>) | 6项合成媒体和微型SQL/向量/鉴权检查；不代表中文或大规模业务。 |
| [00-project/validation/poc-browser-report.json](<00-project/validation/poc-browser-report.json>) | Chromium实际上传与显示异步结果的测试记录。 |
| [00-project/validation/poc-ui.png](<00-project/validation/poc-ui.png>) | 真实浏览器运行截图，保存前已清空研发令牌。 |
| [00-project/validation/synthetic-training-experiment.json](<00-project/validation/synthetic-training-experiment.json>) | 64随机张量120步真实CPU训练种子/损失；不当业务准确率。 |
| [00-project/validation/python-components.json](<00-project/validation/python-components.json>) | 安装包版本与声明许可元信息；不是完整OS SBOM或正式许可审查。 |
| [00-project/validation/python-audit-report.json](<00-project/validation/python-audit-report.json>) | pip-audit发现与跳过原因；CPU torch被跳过，不能声称全部无漏洞。 |
| [00-project/validation/npm-sbom.cdx.json](<00-project/validation/npm-sbom.cdx.json>) | 锁定前端依赖的CycloneDX物料清单；不涵盖OS镜像。 |
| [00-project/validation/repository-secrets-report.json](<00-project/validation/repository-secrets-report.json>) | 确切开发凭据值及已知秘密文件名检查，非完整DLP。 |

源Word、170任务和正式业务契约保持；PoC的可运行/真实合成模型与正式业务/GPU/生产冻结分开。当前版本和完整运行依赖在仓库根config/versions.yaml、config/locks和frontend/package-lock.json，不由旧手册示例推定。

## 当前文件完整索引

以下按实际文件生成，共284份；文件存在不代表正式批准。旧输入快照/历史报告按其时间与scope阅读。

| 实际文件 | 含义与使用要求 |
| --- | --- |
| [00-project/README.md](<00-project/README.md>) | 所在专题的局部导航与阅读入口 |
| [00-project/adaptation-diff.json](<00-project/adaptation-diff.json>) | 初次仓库适配的新增、修改及保留记录，不覆盖后续修订历史。 |
| [00-project/baseline-1.0.md](<00-project/baseline-1.0.md>) | 开发输入候选基线说明，当前NOT_FROZEN。 |
| [00-project/baseline-file-list.txt](<00-project/baseline-file-list.txt>) | 某次基线整理的文件路径清单，不是执行结果。 |
| [00-project/baseline-file-manifest.json](<00-project/baseline-file-manifest.json>) | 归档的上游输入快照摘要；当前交付用repository-file-manifest。 |
| [00-project/baseline-validation-report.md](<00-project/baseline-validation-report.md>) | 验证范围、报告位置和没有验证的事项。 |
| [00-project/build-counts.json](<00-project/build-counts.json>) | 当前工程输入数量统计；数量不等于功能完成率。 |
| [00-project/change-log.md](<00-project/change-log.md>) | 按轮记录修订原因、影响和边界。 |
| [00-project/document-conversion-plan.md](<00-project/document-conversion-plan.md>) | 转换目标、处理方法及保留原件的规则。 |
| [00-project/document-governance.md](<00-project/document-governance.md>) | 来源优先级、候选身份和变更管理规则。 |
| [00-project/freeze-checklist.md](<00-project/freeze-checklist.md>) | 冻结前应检查的项目；不是已通过证明。 |
| [00-project/glossary.md](<00-project/glossary.md>) | 统一业务和工程术语，尤其同源、片段、原件、证据及版本含义。 |
| [00-project/official-sources.md](<00-project/official-sources.md>) | 原输入包采用的技术来源及对应说明。 |
| [00-project/official-sources.yaml](<00-project/official-sources.yaml>) | 上述技术来源的机器索引。 |
| [00-project/open-questions.md](<00-project/open-questions.md>) | 尚待确定的业务、资源与技术问题说明。 |
| [00-project/open-questions.yaml](<00-project/open-questions.yaml>) | 未决事项的机器索引，不能自动将未知改为已解决。 |
| [00-project/project-scope.md](<00-project/project-scope.md>) | 12模块、170任务及场景的范围与外部边界；分阶段不等于删功能。 |
| [00-project/repository-file-manifest.json](<00-project/repository-file-manifest.json>) | 本次实际交付文件摘要，用于本地和服务器核对，排除自身及同步回执。 |
| [00-project/repository-readiness.md](<00-project/repository-readiness.md>) | 当前资料、Git、服务和验证状态。历史数量与当前构建统计有差异时，以本轮报告为准。 |
| [00-project/requirement-traceability.md](<00-project/requirement-traceability.md>) | 需求与用例、接口、表、模型、任务和测试的阅读矩阵。 |
| [00-project/requirement-traceability.yaml](<00-project/requirement-traceability.yaml>) | 用于检查追踪覆盖与断链的机器记录。 |
| [00-project/review-decision-application-report.md](<00-project/review-decision-application-report.md>) | 决定如何同步到设计和契约，以及未生效项。 |
| [00-project/review-decisions.yaml](<00-project/review-decisions.yaml>) | 已记录决定和用户选择；空决定列表不能充当批准。 |
| [00-project/review-package/acceptance-review.md](<00-project/review-package/acceptance-review.md>) | 对应领域的评审问题与确认输入，不是已批准记录 |
| [00-project/review-package/algorithm-review.md](<00-project/review-package/algorithm-review.md>) | 对应领域的评审问题与确认输入，不是已批准记录 |
| [00-project/review-package/business-rule-review.md](<00-project/review-package/business-rule-review.md>) | 对应领域的评审问题与确认输入，不是已批准记录 |
| [00-project/review-package/dataset-review.md](<00-project/review-package/dataset-review.md>) | 对应领域的评审问题与确认输入，不是已批准记录 |
| [00-project/review-package/open-questions-review.md](<00-project/review-package/open-questions-review.md>) | 对应领域的评审问题与确认输入，不是已批准记录 |
| [00-project/review-package/permission-review.md](<00-project/review-package/permission-review.md>) | 对应领域的评审问题与确认输入，不是已批准记录 |
| [00-project/review-package/scope-review.md](<00-project/review-package/scope-review.md>) | 对应领域的评审问题与确认输入，不是已批准记录 |
| [00-project/review-package/technical-baseline-review.md](<00-project/review-package/technical-baseline-review.md>) | 实际技术评审输入与待正式确认事项，不能自动充当批准。 |
| [00-project/server-sync-receipt.json](<00-project/server-sync-receipt.json>) | 服务器同步目标、时间、摘要核验与更新结果。 |
| [00-project/source-document-inventory.md](<00-project/source-document-inventory.md>) | 人类可读的原件、修订稿、流程手册与摘要清单。 |
| [00-project/source-inventory.json](<00-project/source-inventory.json>) | 用于核验源文件未被改写的归档路径、来源路径和SHA-256。 |
| [00-project/upstream-file-manifest.json](<00-project/upstream-file-manifest.json>) | 本轮仓库适配前的上游文件摘要，供对比。 |
| [00-project/upstream-package-readme.md](<00-project/upstream-package-readme.md>) | 上游资料包原始说明，属于历史状态。 |
| [00-project/validation/application-source-binding-report.json](<00-project/validation/application-source-binding-report.json>) | 实际或历史验证记录；须核对时间、status、scope、环境和未执行项，不当正式验收。 |
| [00-project/validation/ci-all-report.json](<00-project/validation/ci-all-report.json>) | 本机完整门禁逐命令实际状态、耗时与执行范围；托管执行为false。 |
| [00-project/validation/ci-failure-gate-report.json](<00-project/validation/ci-failure-gate-report.json>) | 验证故意失败确实阻断构建/部署的判定，PASS不等于探针本身成功。 |
| [00-project/validation/ci-failure-probe-report.json](<00-project/validation/ci-failure-probe-report.json>) | 故意插入失败后的真实非零门禁报告；FAIL为探针预期。 |
| [00-project/validation/ci-report.json](<00-project/validation/ci-report.json>) | 最近一次正常CI入口执行报告；详细阶段与范围须核对。 |
| [00-project/validation/database-contract-report.json](<00-project/validation/database-contract-report.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/database-foundation-report.json](<00-project/validation/database-foundation-report.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/documentation-completion-report.json](<00-project/validation/documentation-completion-report.json>) | 当前全量导航、字段来源及原件摘要的覆盖检查 |
| [00-project/validation/environment-inventory.json](<00-project/validation/environment-inventory.json>) | 实际宿主/引擎/服务版本、上限和时点快照；不是峰值或独占配额。 |
| [00-project/validation/generated-contract-report.json](<00-project/validation/generated-contract-report.json>) | 两份TS类型临时重新生成后的字节一致性。 |
| [00-project/validation/local-attempt-01.json](<00-project/validation/local-attempt-01.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/local-validation-report.json](<00-project/validation/local-validation-report.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/lock-reproduction-report.json](<00-project/validation/lock-reproduction-report.json>) | 全新venv按精确锁安装后的依赖与导入结果。 |
| [00-project/validation/media-query-report.json](<00-project/validation/media-query-report.json>) | 6项合成媒体和微型SQL/向量/鉴权检查；不代表中文或大规模业务。 |
| [00-project/validation/npm-sbom.cdx.json](<00-project/validation/npm-sbom.cdx.json>) | 锁定前端依赖的CycloneDX物料清单；不涵盖OS镜像。 |
| [00-project/validation/poc-browser-report.json](<00-project/validation/poc-browser-report.json>) | Chromium实际上传与显示异步结果的测试记录。 |
| [00-project/validation/poc-integration-report.json](<00-project/validation/poc-integration-report.json>) | 15项真实浏览器服务/API/对象/SQL/队列/CPU结果检查，不是业务模型验收。 |
| [00-project/validation/poc-resilience-report.json](<00-project/validation/poc-resilience-report.json>) | 5项队列/过期租约/服务及版本对象重启/幂等冲突检查，服务恢复记录。 |
| [00-project/validation/poc-ui.png](<00-project/validation/poc-ui.png>) | 真实浏览器运行截图，保存前已清空研发令牌。 |
| [00-project/validation/python-audit-report.json](<00-project/validation/python-audit-report.json>) | pip-audit发现与跳过原因；CPU torch被跳过，不能声称全部无漏洞。 |
| [00-project/validation/python-components.json](<00-project/validation/python-components.json>) | 安装包版本与声明许可元信息；不是完整OS SBOM或正式许可审查。 |
| [00-project/validation/repository-docs-validation.json](<00-project/validation/repository-docs-validation.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/repository-secrets-report.json](<00-project/validation/repository-secrets-report.json>) | 确切开发凭据值及已知秘密文件名检查，非完整DLP。 |
| [00-project/validation/runtime-lock-report.json](<00-project/validation/runtime-lock-report.json>) | 实际Python补丁与全部第三方包是否匹配精确锁。 |
| [00-project/validation/sql-attempt-01.json](<00-project/validation/sql-attempt-01.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/sql-attempt-02.json](<00-project/validation/sql-attempt-02.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/sql-validation-report.json](<00-project/validation/sql-validation-report.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/stage-two-completion-report.json](<00-project/validation/stage-two-completion-report.json>) | 实际或历史验证记录；须核对时间、status、scope、环境和未执行项，不当正式验收。 |
| [00-project/validation/stage-two-readme-report.json](<00-project/validation/stage-two-readme-report.json>) | 根目录和13个目录README、23步及170任务导航的本轮检查 |
| [00-project/validation/synthetic-training-experiment.json](<00-project/validation/synthetic-training-experiment.json>) | 64随机张量120步真实CPU训练种子/损失；不当业务准确率。 |
| [00-project/validation/upstream/local-attempt-01.json](<00-project/validation/upstream/local-attempt-01.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/upstream/local-validation-report.json](<00-project/validation/upstream/local-validation-report.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/upstream/sql-attempt-01.json](<00-project/validation/upstream/sql-attempt-01.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/upstream/sql-attempt-02.json](<00-project/validation/upstream/sql-attempt-02.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/validation/upstream/sql-validation-report.json](<00-project/validation/upstream/sql-validation-report.json>) | 验证记录；核对执行时间、对象摘要和范围，upstream为历史结果 |
| [00-project/补齐完成说明.md](<00-project/补齐完成说明.md>) | 原输入包补齐内容与状态边界。 |
| [01-requirements/README.md](<01-requirements/README.md>) | 所在专题的局部导航与阅读入口 |
| [01-requirements/business-rules.md](<01-requirements/business-rules.md>) | 控制业务行为的规则；区分规则建议和已确认决定。 |
| [01-requirements/engineering-requirements.yaml](<01-requirements/engineering-requirements.yaml>) | 与工程任务对应的要求和编号。 |
| [01-requirements/functional-requirements.md](<01-requirements/functional-requirements.md>) | 系统必须提供的业务功能及编号。 |
| [01-requirements/non-functional-requirements.md](<01-requirements/non-functional-requirements.md>) | 性能、可靠性、维护、安全等约束及验证口径。 |
| [01-requirements/use-cases/README.md](<01-requirements/use-cases/README.md>) | 所在专题的局部导航与阅读入口 |
| [01-requirements/use-cases/UC-CLAIM-001.md](<01-requirements/use-cases/UC-CLAIM-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-FORENSIC-001.md](<01-requirements/use-cases/UC-FORENSIC-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-IMGRET-001.md](<01-requirements/use-cases/UC-IMGRET-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-INGEST-001.md](<01-requirements/use-cases/UC-INGEST-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-MEDIA-001.md](<01-requirements/use-cases/UC-MEDIA-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-OPS-001.md](<01-requirements/use-cases/UC-OPS-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-ORIGIN-001.md](<01-requirements/use-cases/UC-ORIGIN-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-PROPAGATION-001.md](<01-requirements/use-cases/UC-PROPAGATION-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-RESOURCE-001.md](<01-requirements/use-cases/UC-RESOURCE-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-REVIEW-001.md](<01-requirements/use-cases/UC-REVIEW-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-RISK-001.md](<01-requirements/use-cases/UC-RISK-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/use-cases/UC-VIDTRACE-001.md](<01-requirements/use-cases/UC-VIDTRACE-001.md>) | 对应模块用例，描述用户目标、正常异常和权限流程 |
| [01-requirements/user-roles.md](<01-requirements/user-roles.md>) | 角色职责及访问边界，不能只列角色名称。 |
| [02-architecture/README.md](<02-architecture/README.md>) | 所在专题的局部导航与阅读入口 |
| [02-architecture/architecture-decisions/README.md](<02-architecture/architecture-decisions/README.md>) | 所在专题的局部导航与阅读入口 |
| [02-architecture/architecture-decisions/TB-ADR-001-frontend-stack.md](<02-architecture/architecture-decisions/TB-ADR-001-frontend-stack.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-002-backend-stack.md](<02-architecture/architecture-decisions/TB-ADR-002-backend-stack.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-003-relational-database.md](<02-architecture/architecture-decisions/TB-ADR-003-relational-database.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-004-object-storage.md](<02-architecture/architecture-decisions/TB-ADR-004-object-storage.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-005-cache-and-messaging.md](<02-architecture/architecture-decisions/TB-ADR-005-cache-and-messaging.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-006-search-and-vector-database.md](<02-architecture/architecture-decisions/TB-ADR-006-search-and-vector-database.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-007-graph-storage.md](<02-architecture/architecture-decisions/TB-ADR-007-graph-storage.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-008-model-training-stack.md](<02-architecture/architecture-decisions/TB-ADR-008-model-training-stack.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-009-model-serving.md](<02-architecture/architecture-decisions/TB-ADR-009-model-serving.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-010-media-processing.md](<02-architecture/architecture-decisions/TB-ADR-010-media-processing.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-011-security.md](<02-architecture/architecture-decisions/TB-ADR-011-security.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/TB-ADR-012-deployment-platform.md](<02-architecture/architecture-decisions/TB-ADR-012-deployment-platform.md>) | 已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。 |
| [02-architecture/architecture-decisions/template.md](<02-architecture/architecture-decisions/template.md>) | 架构决策记录或模板，状态以文件正文为准 |
| [02-architecture/compatibility-matrix.md](<02-architecture/compatibility-matrix.md>) | 实际锁定组合、安装/构建/运行兼容证据及升级路径。 |
| [02-architecture/data-flow.md](<02-architecture/data-flow.md>) | 原件、派生对象、任务、证据和各存储间的一致性职责。 |
| [02-architecture/environment-constraints.md](<02-architecture/environment-constraints.md>) | 实际Linux、Miniforge py310、Desktop挂载/网络/CPU与PythonEOL边界。 |
| [02-architecture/licenses.md](<02-architecture/licenses.md>) | 包/镜像/FFmpeg/Desktop与权重的许可盘点、审核缺口和再分发要求。 |
| [02-architecture/module-boundaries.md](<02-architecture/module-boundaries.md>) | 十二业务模块的职责及协作边界。 |
| [02-architecture/non-functional-requirements.md](<02-architecture/non-functional-requirements.md>) | 引用原非功能需求源并登记实测口径，不另造正式指标。 |
| [02-architecture/repository-layout.md](<02-architecture/repository-layout.md>) | 顶层和计划子目录的文件归属、依赖方向与禁止内容。 |
| [02-architecture/resource-and-team-inventory.md](<02-architecture/resource-and-team-inventory.md>) | 宿主、Desktop虚拟机与容器配额分别盘点；磁盘、GPU与责任人未决。 |
| [02-architecture/security-baseline.md](<02-architecture/security-baseline.md>) | 研发鉴权、秘密、输入、日志和网络措施；正式身份/案件/审计等差距。 |
| [02-architecture/stage-two-official-sources.md](<02-architecture/stage-two-official-sources.md>) | 本轮官方兼容、机制与许可来源；网页不替代部署实测。 |
| [02-architecture/system-architecture.md](<02-architecture/system-architecture.md>) | 五层系统架构、服务关系与核心处理链路。 |
| [02-architecture/technical-baseline-change-control.md](<02-architecture/technical-baseline-change-control.md>) | 开发快照、正式冻结、ADR/锁/迁移变更和恢复规则。 |
| [02-architecture/technical-baseline.md](<02-architecture/technical-baseline.md>) | 1.0-py310-cpu研发执行基线，区别于正式生产冻结和全部业务实现。 |
| [02-architecture/technical-validation-report.md](<02-architecture/technical-validation-report.md>) | 各真实检查结果、证据路径、范围和未测事项。 |
| [02-architecture/technology-options.md](<02-architecture/technology-options.md>) | 12个技术域的替代方案、研发执行选择、实测和扩展边界。 |
| [03-api/README.md](<03-api/README.md>) | 所在专题的局部导航与阅读入口 |
| [03-api/api-design.md](<03-api/api-design.md>) | 幂等、版本条件、异步、分页、媒体访问及通用数据表达规则。 |
| [03-api/error-codes.md](<03-api/error-codes.md>) | 错误分类、稳定错误码、客户端处理及信息泄露边界。 |
| [03-api/examples/Accepted.json](<03-api/examples/Accepted.json>) | Accepted接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ActionAck.json](<03-api/examples/ActionAck.json>) | ActionAck接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Approval.json](<03-api/examples/Approval.json>) | Approval接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ApprovalCreate.json](<03-api/examples/ApprovalCreate.json>) | ApprovalCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ApprovalDecision.json](<03-api/examples/ApprovalDecision.json>) | ApprovalDecision接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Asset.json](<03-api/examples/Asset.json>) | Asset接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/AssetPage.json](<03-api/examples/AssetPage.json>) | AssetPage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/AuditEvent.json](<03-api/examples/AuditEvent.json>) | AuditEvent接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/AuditEventPage.json](<03-api/examples/AuditEventPage.json>) | AuditEventPage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/AuditExport.json](<03-api/examples/AuditExport.json>) | AuditExport接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/AuthLogin.json](<03-api/examples/AuthLogin.json>) | AuthLogin接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/AuthSession.json](<03-api/examples/AuthSession.json>) | AuthSession接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/BoundingBox.json](<03-api/examples/BoundingBox.json>) | BoundingBox接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Claim.json](<03-api/examples/Claim.json>) | Claim接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ClaimExtract.json](<03-api/examples/ClaimExtract.json>) | ClaimExtract接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ClaimList.json](<03-api/examples/ClaimList.json>) | ClaimList接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ClaimVerify.json](<03-api/examples/ClaimVerify.json>) | ClaimVerify接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/CurrentUser.json](<03-api/examples/CurrentUser.json>) | CurrentUser接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Evaluation.json](<03-api/examples/Evaluation.json>) | Evaluation接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/EvaluationCreate.json](<03-api/examples/EvaluationCreate.json>) | EvaluationCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/EvaluationPage.json](<03-api/examples/EvaluationPage.json>) | EvaluationPage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Evidence.json](<03-api/examples/Evidence.json>) | Evidence接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/EvidencePackage.json](<03-api/examples/EvidencePackage.json>) | EvidencePackage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/EvidencePage.json](<03-api/examples/EvidencePage.json>) | EvidencePage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Feedback.json](<03-api/examples/Feedback.json>) | Feedback接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/FeedbackRecord.json](<03-api/examples/FeedbackRecord.json>) | FeedbackRecord接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Finding.json](<03-api/examples/Finding.json>) | Finding接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Findings.json](<03-api/examples/Findings.json>) | Findings接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/FirstSource.json](<03-api/examples/FirstSource.json>) | FirstSource接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Graph.json](<03-api/examples/Graph.json>) | Graph接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/GraphDecision.json](<03-api/examples/GraphDecision.json>) | GraphDecision接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/GraphEdge.json](<03-api/examples/GraphEdge.json>) | GraphEdge接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/GraphNode.json](<03-api/examples/GraphNode.json>) | GraphNode接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Health.json](<03-api/examples/Health.json>) | Health接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ImageSearch.json](<03-api/examples/ImageSearch.json>) | ImageSearch接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ImportEntry.json](<03-api/examples/ImportEntry.json>) | ImportEntry接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ImportRequest.json](<03-api/examples/ImportRequest.json>) | ImportRequest接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ImportStatus.json](<03-api/examples/ImportStatus.json>) | ImportStatus接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/IndexSwitch.json](<03-api/examples/IndexSwitch.json>) | IndexSwitch接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/IndexVersion.json](<03-api/examples/IndexVersion.json>) | IndexVersion接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Model.json](<03-api/examples/Model.json>) | Model接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ModelCreate.json](<03-api/examples/ModelCreate.json>) | ModelCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ModelPage.json](<03-api/examples/ModelPage.json>) | ModelPage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/NodeStatus.json](<03-api/examples/NodeStatus.json>) | NodeStatus接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ObjectRef.json](<03-api/examples/ObjectRef.json>) | ObjectRef接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/OperationToken.json](<03-api/examples/OperationToken.json>) | OperationToken接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/OperationTokenRequest.json](<03-api/examples/OperationTokenRequest.json>) | OperationTokenRequest接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Policy.json](<03-api/examples/Policy.json>) | Policy接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/PolicyCreate.json](<03-api/examples/PolicyCreate.json>) | PolicyCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/PolicyPage.json](<03-api/examples/PolicyPage.json>) | PolicyPage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Problem.json](<03-api/examples/Problem.json>) | Problem接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Relation.json](<03-api/examples/Relation.json>) | Relation接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Report.json](<03-api/examples/Report.json>) | Report接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ReportCreate.json](<03-api/examples/ReportCreate.json>) | ReportCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ReportDraft.json](<03-api/examples/ReportDraft.json>) | ReportDraft接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Rerun.json](<03-api/examples/Rerun.json>) | Rerun接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Review.json](<03-api/examples/Review.json>) | Review接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/ReviewCreate.json](<03-api/examples/ReviewCreate.json>) | ReviewCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Rollout.json](<03-api/examples/Rollout.json>) | Rollout接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/SealRequest.json](<03-api/examples/SealRequest.json>) | SealRequest接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/SearchAccepted.json](<03-api/examples/SearchAccepted.json>) | SearchAccepted接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/SearchCandidate.json](<03-api/examples/SearchCandidate.json>) | SearchCandidate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/SearchJob.json](<03-api/examples/SearchJob.json>) | SearchJob接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/SearchResults.json](<03-api/examples/SearchResults.json>) | SearchResults接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Source.json](<03-api/examples/Source.json>) | Source接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/SourceCreate.json](<03-api/examples/SourceCreate.json>) | SourceCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/SourcePage.json](<03-api/examples/SourcePage.json>) | SourcePage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Task.json](<03-api/examples/Task.json>) | Task接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/TaskAction.json](<03-api/examples/TaskAction.json>) | TaskAction接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/TaskCreate.json](<03-api/examples/TaskCreate.json>) | TaskCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/TaskPage.json](<03-api/examples/TaskPage.json>) | TaskPage接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/TimeRange.json](<03-api/examples/TimeRange.json>) | TimeRange接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/Timeline.json](<03-api/examples/Timeline.json>) | Timeline接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/TimelineItem.json](<03-api/examples/TimelineItem.json>) | TimelineItem接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/UploadComplete.json](<03-api/examples/UploadComplete.json>) | UploadComplete接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/UploadCreate.json](<03-api/examples/UploadCreate.json>) | UploadCreate接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/UploadPart.json](<03-api/examples/UploadPart.json>) | UploadPart接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/UploadResult.json](<03-api/examples/UploadResult.json>) | UploadResult接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/UploadSession.json](<03-api/examples/UploadSession.json>) | UploadSession接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/VersionBinding.json](<03-api/examples/VersionBinding.json>) | VersionBinding接口结构的合成示例，不是业务运行结果 |
| [03-api/examples/VideoSearch.json](<03-api/examples/VideoSearch.json>) | VideoSearch接口结构的合成示例，不是业务运行结果 |
| [03-api/inference-openapi.yaml](<03-api/inference-openapi.yaml>) | 业务后端调用内部算法的入口，与外部API隔离。 |
| [03-api/openapi.yaml](<03-api/openapi.yaml>) | 外部业务API唯一结构源：路径、参数、请求响应、错误和安全声明。 |
| [03-api/operation-index.json](<03-api/operation-index.json>) | 操作ID与任务、数据表的关联索引。 |
| [03-api/poc-api.md](<03-api/poc-api.md>) | 已实现PoC入口和53操作正式契约的区别，鉴权/错误与合成模型范围。 |
| [03-development/README.md](<03-development/README.md>) | 所在专题的局部导航与阅读入口 |
| [03-development/ci-cd.md](<03-development/ci-cd.md>) | 同源本机CI、失败阻断、Runner前提及尚未运行的托管平台边界。 |
| [03-development/coding-standards.md](<03-development/coding-standards.md>) | 编码、命名、变更和检查规范；校验依赖不等于业务依赖。 |
| [03-development/contract-generation.md](<03-development/contract-generation.md>) | 两份权威OpenAPI生成TS类型；当前Celery开发命令及事件缺口。 |
| [03-development/repository-bootstrap.md](<03-development/repository-bootstrap.md>) | 仓库、基础环境、最小闭环、算法与交付的推进顺序。 |
| [03-development/stage-two-deliverables.json](<03-development/stage-two-deliverables.json>) | 逐步机器对照；保留计划并区分开发验证与正式完成。 |
| [03-development/stage-two-readiness.md](<03-development/stage-two-readiness.md>) | 23步实际开发状态和未完成的正式条件。 |
| [04-database/README.md](<04-database/README.md>) | 所在专题的局部导航与阅读入口 |
| [04-database/api-field-mapping.csv](<04-database/api-field-mapping.csv>) | 按操作、方向和字段路径排列的可表格查看映射。 |
| [04-database/api-field-mapping.json](<04-database/api-field-mapping.json>) | 用于校验的机器映射，包括嵌套字段。 |
| [04-database/api-field-mapping.md](<04-database/api-field-mapping.md>) | 接口到数据库的映射原则与典型对象解释。 |
| [04-database/data-dictionary.md](<04-database/data-dictionary.md>) | 数据字典：逐表逐字段的类型、约束、含义与精确来源。 |
| [04-database/database-design-references.md](<04-database/database-design-references.md>) | 本轮查阅的PostgreSQL/OpenAPI/JSON Schema官方机制及采用方式。 |
| [04-database/database-design.md](<04-database/database-design.md>) | 数据库职责、关系、事务与版本设计的总说明。 |
| [04-database/database-revision-audit.md](<04-database/database-revision-audit.md>) | 本轮修订内容、技术边界与未执行事项。 |
| [04-database/database-validation.md](<04-database/database-validation.md>) | 初始化与约束验证的方法及环境边界。 |
| [04-database/er-diagram.md](<04-database/er-diagram.md>) | 表关系图，便于阅读；完整复合外键以SQL和字典为准。 |
| [04-database/field-provenance.json](<04-database/field-provenance.json>) | 逐字段来源索引：定义状态、JSON Pointer、SQL对象和实际API字段映射。 |
| [04-database/first-source-ranking.md](<04-database/first-source-ranking.md>) | 首发排序批次、0—3候选、版本、连续名次、唯一性及API语义。 |
| [04-database/initial-schema.sql](<04-database/initial-schema.sql>) | 新空库候选初始化SQL，包含表、约束、权限、触发器及字段注释；不能直接覆盖现有业务库。 |
| [04-database/poc-database.md](<04-database/poc-database.md>) | 独立开发3表、outbox、幂等与租约；区别于62表业务字典/SQL。 |
| [04-database/table-catalog.json](<04-database/table-catalog.json>) | 结构化表目录，保存字段定义和表级关系；应与SQL和字典同步。 |
| [05-workflows/README.md](<05-workflows/README.md>) | 所在专题的局部导航与阅读入口 |
| [05-workflows/evidence-state-machine.md](<05-workflows/evidence-state-machine.md>) | 证据记录、固化和更正的状态与历史保护。 |
| [05-workflows/review-state-machine.md](<05-workflows/review-state-machine.md>) | 人工复核、退回和结果版本绑定。 |
| [05-workflows/task-state-machine.md](<05-workflows/task-state-machine.md>) | 分析任务运行、失败、取消、重算与版本行为。 |
| [06-algorithms/README.md](<06-algorithms/README.md>) | 所在专题的局部导航与阅读入口 |
| [06-algorithms/model-catalog.yaml](<06-algorithms/model-catalog.yaml>) | 模型编号、能力、关联任务和数据集的机器目录。 |
| [06-algorithms/model-contract.md](<06-algorithms/model-contract.md>) | 请求响应、缺失模态、错误、证据与模型版本约定。 |
| [06-algorithms/model-evaluation.md](<06-algorithms/model-evaluation.md>) | 评测分组、统计口径、指标及证据要求。 |
| [06-algorithms/model-list.md](<06-algorithms/model-list.md>) | 模型方向及使用目的的阅读清单。 |
| [07-datasets/README.md](<07-datasets/README.md>) | 所在专题的局部导航与阅读入口 |
| [07-datasets/annotation-specification.md](<07-datasets/annotation-specification.md>) | 标注结构、质量检查和复核要求。 |
| [07-datasets/data-card-template.md](<07-datasets/data-card-template.md>) | 新增或发布数据版本需填写的数据卡模板。 |
| [07-datasets/data-compliance.md](<07-datasets/data-compliance.md>) | 来源许可、用途、访问、保留与回流约束。 |
| [07-datasets/dataset-catalog.md](<07-datasets/dataset-catalog.md>) | 数据集类别、用途及对应模型方向。 |
| [07-datasets/dataset-split-policy.md](<07-datasets/dataset-split-policy.md>) | 按来源组等条件划分，隔离验证、校准与封存测试用途。 |
| [08-security/README.md](<08-security/README.md>) | 所在专题的局部导航与阅读入口 |
| [08-security/audit-requirements.md](<08-security/audit-requirements.md>) | 应记录的主体、对象、版本、动作、结果与追踪信息。 |
| [08-security/data-classification.md](<08-security/data-classification.md>) | 数据类别、敏感性和处理要求。 |
| [08-security/permission-matrix.md](<08-security/permission-matrix.md>) | 角色与动作权限的对应关系及限制。 |
| [08-security/security-design.md](<08-security/security-design.md>) | 安全边界、输入处理、访问和敏感信息保护设计。 |
| [09-testing/README.md](<09-testing/README.md>) | 所在专题的局部导航与阅读入口 |
| [09-testing/acceptance-criteria.md](<09-testing/acceptance-criteria.md>) | 交付判定口径和不能省略的证据。 |
| [09-testing/model-test-scenarios.md](<09-testing/model-test-scenarios.md>) | 模型效果、未知、鲁棒性及评测划分测试。 |
| [09-testing/security-test-scenarios.md](<09-testing/security-test-scenarios.md>) | 鉴权、越权、撤销、输入和审计等测试。 |
| [09-testing/task-test-scenarios.yaml](<09-testing/task-test-scenarios.yaml>) | 各任务的验证场景，不等同已实现测试程序。 |
| [09-testing/test-scenarios.yaml](<09-testing/test-scenarios.yaml>) | 业务功能正常与异常场景。 |
| [09-testing/test-strategy.md](<09-testing/test-strategy.md>) | 测试层级、数据、环境和执行策略。 |
| [10-deployment/README.md](<10-deployment/README.md>) | 所在专题的局部导航与阅读入口 |
| [10-deployment/deployment-plan.md](<10-deployment/deployment-plan.md>) | 服务、运行数据、配置和后续部署交付要求。 |
| [10-deployment/development-runbook.md](<10-deployment/development-runbook.md>) | 真实启动、复建、SSH页面访问、令牌、端口、卷、停止与排查。 |
| [10-deployment/server-observation.md](<10-deployment/server-observation.md>) | 归档前服务器的时点观测；不能当实时环境或归档后文件数。 |
| [_converted/conversion-report.md](<_converted/conversion-report.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/guide/第一阶段：Codex整理开发输入材料分步提示词手册.md](<_converted/guide/第一阶段：Codex整理开发输入材料分步提示词手册.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/guide/第二阶段系统技术基线分步提示词手册.md](<_converted/guide/第二阶段系统技术基线分步提示词手册.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/guide/第二阶段系统技术基线确定与Codex协作实施指南.md](<_converted/guide/第二阶段系统技术基线确定与Codex协作实施指南.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/original/短视频与图片智能识别溯源系统开发任务分解书V2.md](<_converted/original/短视频与图片智能识别溯源系统开发任务分解书V2.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/original/短视频与图片智能识别溯源系统算法模型推荐清单.md](<_converted/original/短视频与图片智能识别溯源系统算法模型推荐清单.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/original/短视频与图片智能识别溯源系统算法研发与训练数据集建设说明 (1).md](<_converted/original/短视频与图片智能识别溯源系统算法研发与训练数据集建设说明 (1).md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/original/面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.md](<_converted/original/面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/revision/项目任务书_技术修订版V1.3.md](<_converted/revision/项目任务书_技术修订版V1.3.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [_converted/revision/项目总体设计方案_技术修订版V1.4.md](<_converted/revision/项目总体设计方案_技术修订版V1.4.md>) | 来源材料的检索转换文本或转换报告；图表和原始语义需对照原件 |
| [assets/source/S08-image1.png](<assets/source/S08-image1.png>) | 来源材料配套图像 |
| [assets/source/S08-image2.png](<assets/source/S08-image2.png>) | 来源材料配套图像 |
| [guides/第一阶段：Codex整理开发输入材料分步提示词手册.docx](<guides/第一阶段：Codex整理开发输入材料分步提示词手册.docx>) | 阶段工作流程手册 |
| [guides/第二阶段系统技术基线分步提示词手册.docx](<guides/第二阶段系统技术基线分步提示词手册.docx>) | 阶段工作流程手册 |
| [guides/第二阶段系统技术基线确定与Codex协作实施指南.docx](<guides/第二阶段系统技术基线确定与Codex协作实施指南.docx>) | 阶段工作流程手册 |
| [source/original/短视频与图片智能识别溯源系统功能模块界面原型图.pptx](<source/original/短视频与图片智能识别溯源系统功能模块界面原型图.pptx>) | 按摘要保护的业务来源原件或当前修订原件 |
| [source/original/短视频与图片智能识别溯源系统开发任务分解书V2.docx](<source/original/短视频与图片智能识别溯源系统开发任务分解书V2.docx>) | 按摘要保护的业务来源原件或当前修订原件 |
| [source/original/短视频与图片智能识别溯源系统算法模型推荐清单.docx](<source/original/短视频与图片智能识别溯源系统算法模型推荐清单.docx>) | 按摘要保护的业务来源原件或当前修订原件 |
| [source/original/短视频与图片智能识别溯源系统算法研发与训练数据集建设说明 (1).docx](<source/original/短视频与图片智能识别溯源系统算法研发与训练数据集建设说明 (1).docx>) | 按摘要保护的业务来源原件或当前修订原件 |
| [source/original/面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.docx](<source/original/面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.docx>) | 按摘要保护的业务来源原件或当前修订原件 |
| [source/revisions/项目任务书_技术修订版V1.3.docx](<source/revisions/项目任务书_技术修订版V1.3.docx>) | 按摘要保护的业务来源原件或当前修订原件 |
| [source/revisions/项目总体设计方案_技术修订版V1.4.docx](<source/revisions/项目总体设计方案_技术修订版V1.4.docx>) | 按摘要保护的业务来源原件或当前修订原件 |
