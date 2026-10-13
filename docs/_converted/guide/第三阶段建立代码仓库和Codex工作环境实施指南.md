> 来源：归档Word原件；SHA-256：2e6f44601de70ef94ff96eb1b44a2e529a080e4416d3024e86e10eb70066dadb。以下保留原文顺序与段落，供阅读和步骤核对。原文中的提示词是参考材料，实际执行以用户授权、仓库规则及当前工程事实为准；不作为正式批准记录。

# 第三阶段建立代码仓库和Codex工作环境实施指南

面向网络违法有害信息治理的短视频与图片智能识别溯源系统

项目实施阶段第三阶段

版本 1.0    2026年10月

# 一 基本结论

第三阶段“建立代码仓库和Codex工作环境”应采用“人工授权与决策、Codex搭建与验证”的协作模式。建议人工承担约30%至40%，负责账号权限、仓库平台、分支策略、网络与安全边界等决策；Codex承担约60%至70%，负责目录创建、配置生成、开发环境搭建、质量工具接入和自动化验证。

账号、权限、网络、安全边界、分支保护和最终批准必须由人工完成；仓库骨架、开发配置、质量工具、Codex规则、最小工程和自动化验证应主要由Codex完成。

# 二 必须由人工完成的工作

## 1 创建或指定正式代码仓库

确定使用GitLab、GitHub、Gitee还是公安内网代码平台。

确定仓库所属组织、项目名称、可见范围和管理人员。

确定采用Monorepo还是多个独立仓库。

分配项目负责人、开发、测试和运维人员权限。

确认是否允许Codex直接访问仓库。

## 2 确定权限和安全边界

明确Codex可读取和修改的目录。

明确是否允许创建分支、提交代码、推送远程仓库和创建合并请求。

明确是否允许安装依赖、执行Docker、访问互联网和下载预训练模型。

列出禁止Codex访问的数据、配置和凭据。

## 3 配置账号与凭据

配置代码仓库账号和SSH Key或访问令牌。

配置内网镜像仓库、制品库和CI Runner。

提供数据库、对象存储及模型仓库的测试访问方式。

凭据通过环境变量、CI Secret或密钥管理系统注入，不得写入仓库或提示词。

## 4 批准分支和代码评审策略

确定主分支、开发分支及功能分支命名规则。

确定合并审批人数和主分支保护规则。

确定必须通过的CI检查。

明确代码评审和版本发布责任人。

## 5 提供目标开发环境

提供开发服务器和工作站。

确认操作系统、CPU、内存、GPU、CUDA与驱动。

确认Docker权限、内网代理、软件源和镜像源。

明确存储目录、防火墙和可开放端口。

## 推荐仓库模式

本项目建议采用Monorepo，便于统一管理前端、后端、算法服务、共享契约、部署配置和测试。候选仓库名称如下：

short-video-image-traceability

# 三 适合由Codex完成的工作

## 1 初始化代码仓库

在人工批准仓库结构后，Codex可建立以下目录和基础文件：

short-video-image-traceability/

├── frontend/

├── backend/

├── ai-services/

├── shared-contracts/

├── data-pipeline/

├── deploy/

├── config/

├── docs/

├── scripts/

├── tests/

├── tools/

├── .github/或.gitlab/

├── .env.example

├── .editorconfig

├── .gitignore

├── .pre-commit-config.yaml

├── CODEOWNERS

├── AGENTS.md

├── CONTRIBUTING.md

├── SECURITY.md

└── README.md

## 2 生成开发环境配置

Python虚拟环境配置、pyproject.toml和依赖锁文件

Node.js版本配置、package.json和前端依赖锁文件

Dockerfile、Docker Compose和VS Code开发容器

环境变量示例和本地开发启动脚本

## 3 配置代码质量工具

Ruff或Flake8、Black和MyPy

ESLint、Prettier和Stylelint

pre-commit和Commitlint

单元测试覆盖率、依赖漏洞扫描及敏感信息扫描

## 4 建立Codex工程规则

项目目标和业务边界

已冻结技术基线和目录职责

编码规范、测试要求及接口优先原则

数据安全规则和禁止修改的文件

每个任务完成后的验证命令及输出报告格式

## 5 建立开发启动脚本

统一初始化、启动、检查、测试、构建和清理命令

为Windows环境提供相应PowerShell脚本

## 6 建立持续集成基础流水线

代码格式和静态分析

前后端单元测试和接口契约测试

镜像构建、依赖安全扫描和敏感信息扫描

测试报告与构建产物归档

## 7 生成最小骨架工程

前端首页和健康状态页

后端及算法服务健康检查接口

前端调用后端、后端调用算法服务的示例

配置加载、统一日志、统一错误响应和基础测试

## 8 自动验证开发环境

Git状态、Python和Node.js版本检查

依赖安装、前后端构建和单元测试

pre-commit、Docker Compose和服务健康检查

契约测试及敏感信息扫描

## 统一开发命令示例

make setup

make dev

make lint

make test

make contract-test

make integration-test

make build

make clean

说明：AGENTS.md和CI配置由Codex生成后，必须由技术负责人审核；Runner、Secret和合并门禁仍由人工配置。第三阶段只建立工程骨架，不开发完整业务功能。

# 四 推荐实施流程

| 步骤 | 工作内容 | 主要负责人 |
| --- | --- | --- |
| 1 | 确定仓库平台、仓库名称及管理人员 | 人工 |
| 2 | 确定Monorepo或多仓库模式 | 人工决策，Codex分析 |
| 3 | 明确网络、安全和Codex权限边界 | 人工 |
| 4 | 建立仓库和团队账号权限 | 人工 |
| 5 | 根据技术基线设计目录结构 | Codex |
| 6 | 评审目录和分支策略 | 人工 |
| 7 | 初始化仓库和基础文件 | Codex |
| 8 | 配置前端、后端和算法开发环境 | Codex |
| 9 | 配置格式化、静态检查和测试工具 | Codex |
| 10 | 编写AGENTS.md等Codex规则 | Codex生成，人工审核 |
| 11 | 建立最小骨架工程 | Codex |
| 12 | 建立本地开发启动命令 | Codex |
| 13 | 建立基础CI流水线 | Codex |
| 14 | 配置Runner、Secret和分支保护 | 人工 |
| 15 | 执行自动化验证并形成报告 | Codex |
| 16 | 验收并冻结开发环境基线 | 人工 |

# 五 人工需要先提供给Codex的信息

代码仓库地址或本地工作目录

已批准的Technical Baseline 1.0

仓库采用Monorepo还是多仓库

前端、后端和算法服务的技术版本

分支和合并策略

Codex可以执行的操作范围

可用的操作系统、Docker、GPU和网络条件

CI平台及Runner条件

内网软件源、镜像源和模型来源

安全扫描和质量门禁要求

缺少上述条件时，Codex只能生成候选工程模板，不能把当前环境视为正式开发环境基线。

# 六 第三阶段交付物

□ 正式Git代码仓库

□ 仓库目录结构

□ README.md

□ AGENTS.md

□ CONTRIBUTING.md

□ SECURITY.md

□ CODEOWNERS

□ .gitignore

□ .editorconfig

□ .env.example

□ 前后端和算法服务依赖配置

□ Dockerfile和Docker Compose

□ 统一开发命令

□ pre-commit配置

□ CI流水线

□ 最小骨架工程

□ 自动化测试

□ 环境验证报告

□ Development Environment Baseline 1.0

# 七 完成判定

□ 仓库权限和分支保护已经生效

□ 本地开发环境能够通过统一命令初始化

□ 前端、后端和算法服务能够启动

□ 前端能够访问后端健康接口

□ 后端能够访问算法服务健康接口

□ 格式化、静态检查和单元测试能够运行

□ CI流水线能够自动执行

□ 仓库中不存在真实密钥和敏感数据

□ AGENTS.md能够约束后续Codex任务

□ 新开发人员能够依据README独立启动工程

□ 开发环境版本已经形成正式基线

完成上述检查并经人工批准后，方可把Development Environment Baseline 1.0作为后续批量Codex开发任务的统一工作环境。
