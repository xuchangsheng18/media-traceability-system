# 第二阶段系统技术基线确定与Codex协作实施指南

短视频与图片智能识别溯源系统

项目实施阶段第二阶段

## 一 基本结论

第二阶段“确定系统技术基线”应采用“人工决策、Codex整理验证”的方式。与第一阶段相比，本阶段对人工决策的依赖更高。建议人工承担约40%至50%，重点负责技术选型、部署边界和质量门槛；Codex承担约50%至60%，重点负责候选方案比较、兼容性检查、配置生成、最小验证工程和文档固化。

技术基线一旦冻结，将直接约束后续代码、数据库、接口、模型服务和部署环境，因此不能让Codex自主决定后直接投入开发。最终技术选择必须由技术负责人作出，并由项目负责人批准。

## 二 人工与Codex职责划分

| 基线内容 | Codex负责 | 人工负责 |
| --- | --- | --- |
| 总体技术架构 | 生成候选架构并比较优缺点 | 确定最终架构 |
| 前端技术栈 | 比较Vue和React等方案 | 选择框架及版本 |
| 后端技术栈 | 比较FastAPI和Spring Boot等 | 确定语言和框架 |
| 关系数据库 | 分析PostgreSQL等适用性 | 确定数据库及版本 |
| 向量数据库 | 比较Milvus和pgvector等 | 确定产品及部署方式 |
| 消息队列 | 比较RabbitMQ和Kafka | 确定最终选型 |
| 对象存储 | 生成MinIO配置和验证方案 | 确定是否采用MinIO或现有存储 |
| 图数据存储 | 比较Neo4j与PostgreSQL方案 | 确定是否引入新数据库 |
| 模型训练框架 | 生成PyTorch工程规范 | 确定框架和版本 |
| 模型推理框架 | 比较FastAPI Triton TorchServe | 确定推理服务方式 |
| 容器与编排 | 生成Docker和K8s方案 | 确定是否使用Kubernetes |
| 国产化适配 | 形成适配清单和风险分析 | 确定必须适配的软硬件 |
| 安全架构 | 提出技术控制建议 | 确定等级 部署边界和制度 |
| 依赖版本 | 检查依赖兼容性 | 批准最终版本 |
| 编码规范 | 生成规范及检查配置 | 确认采用的规范 |
| CI流水线 | 生成流水线配置 | 确定质量门槛 |
| 性能指标 | 提供建议值和测算方法 | 确定正式验收值 |
| 模型阈值 | 提供校准和验证方法 | 批准上线阈值 |


## 三 不能完全交给Codex的原因

Codex可以从技术角度给出合理候选方案，但无法自行确定实际建设环境、管理制度和长期维护条件。以下事项必须由项目组确认：

公安内网允许部署哪些基础软件

是否允许使用开源软件及其许可证

是否必须使用国产服务器 操作系统和数据库

现有机房是否已经部署Kubernetes

是否允许引入Neo4j Milvus OpenSearch等组件

是否需要与公安统一身份认证对接

开发团队主要掌握Python Java还是其他语言

后期由谁负责系统运维

是否有采购授权和商业软件预算

最终验收采用什么技术标准

如果缺少上述约束，Codex可能生成技术上可行但无法在目标网络、软硬件和运维条件下落地的方案。

## 四 推荐协作流程

| 序号 | 工作内容 |
| --- | --- |
| 1 | 人工提供环境和约束 |
| 2 | Codex形成候选技术方案 |
| 3 | Codex开展兼容性与风险分析 |
| 4 | 人工组织技术评审 |
| 5 | Codex根据决策生成技术基线文件 |
| 6 | Codex建立最小验证工程 |
| 7 | 运行自动化验证 |
| 8 | 人工批准并冻结Technical Baseline 1.0 |


## 五 人工需要先提供的信息

建议在docs/02-architecture/environment-constraints.md中形成环境约束清单。

### 1 部署环境

公安内网 政务云 学校实验室或混合部署

是否允许访问互联网和拉取Docker镜像

是否允许使用Kubernetes

是否已有虚拟化或容器平台

是否必须离线部署

是否需要多节点高可用

### 2 服务器资源

结合现有资源，可登记3台深度学习服务器、3台大模型一体机、RTX 3080和RTX 3090工作站以及鲲鹏920服务器，并进一步确认GPU型号和显存、操作系统、驱动、CUDA、节点网络、共享存储和正式部署设备。

### 3 软件限制

允许使用的操作系统和开发语言版本

是否允许PostgreSQL MinIO Milvus OpenSearch Neo4j Redis RabbitMQ和Triton

是否存在国产操作系统 国产数据库或国产中间件要求

开源许可证是否需要专门审核

### 4 团队技术能力

前端团队熟悉Vue还是React

后端团队熟悉Python还是Java

算法团队是否统一使用PyTorch

运维团队是否掌握Docker和Kubernetes

是否有专职数据库管理员和安全人员

## 六 Codex适合承担的工作

### 1 候选技术方案比较

Codex可比较FastAPI与Spring Boot、Vue与React、Milvus与pgvector、RabbitMQ与Kafka、Neo4j与PostgreSQL、Triton与普通FastAPI推理以及Docker Compose与Kubernetes，但应输出比较结果和推荐，不直接宣布最终决策。

### 2 兼容性检查

Python与PyTorch版本

CUDA 驱动 PyTorch与Triton关系

FastAPI与Pydantic版本

PostgreSQL与SQLAlchemy版本

Milvus客户端与服务端版本

Vue Vite TypeScript与Node.js版本

Kubernetes与容器运行时版本

开源许可证和依赖许可证风险

正式版本冻结应以实际离线环境、硬件驱动和官方兼容矩阵验证结果为准。

### 3 架构决策记录

Codex可为后端框架、前端框架、关系数据库、向量数据库、消息队列、对象存储、模型服务、容器平台和图数据存储生成ADR。每份ADR包含背景、候选方案、比较维度、最终决策、理由、负面影响、替代方案、适用范围、日期、决策人和状态。

### 4 版本锁定和工程配置

backend/pyproject.toml及锁文件

frontend/package.json及package-lock.json

ai-services运行环境锁定文件

docker-compose.yml

Dockerfile和.env.example

pre-commit配置及CI流水线

### 5 最小验证工程

前端能够调用后端

后端能够连接PostgreSQL

后端能够访问MinIO

Redis能够读写

消息队列能够投递和消费

GPU容器能够识别显卡

PyTorch能够执行一次推理

模型服务返回统一JSON

日志能够进入监控系统

Docker Compose能够启动全部基础服务

## 七 单项技术决策执行方法

### 1 Codex生成比较报告

请比较Milvus、pgvector和OpenSearch向量检索在本项目中的适用性。

已知条件：

- 需要支持图片和视频关键帧向量检索；

- 预计后期向量规模较大；

- 系统需要离线部署；

- 团队主要使用Python；

- 需要与PostgreSQL业务数据关联；

- 项目已有GPU服务器；

- 运维人员数量有限。

请比较检索规模、性能、部署复杂度、运维复杂度、数据一致性、备份恢复、国产化适配、Python支持、开源许可证和项目风险。只给出候选方案和推荐，不要直接形成最终决策。

### 2 人工组织评审

人工结合实际规模、运维能力、内网软件许可、国产化要求、采购条件和长期维护成本作出决定。

### 3 Codex生成ADR

技术评审决定采用Milvus作为向量数据库。

请创建docs/02-architecture/architecture-decisions/ADR-004-vector-database.md。

内容包括决策背景、候选方案、最终选择、选择理由、适用范围、主要风险、规避措施、版本要求、备份恢复要求、决策日期、决策人占位符和状态“待批准”。不得补充本次评审未确认的部署规模和性能指标。

### 4 Codex建立最小验证环境

请根据ADR-004建立Milvus最小验证环境。

当前只验证：

1. Docker Compose能够启动Milvus；

2. Python客户端能够连接；

3. 能够创建测试集合；

4. 能够写入100条模拟向量；

5. 能够执行Top-10检索；

6. 能够删除测试集合；

7. 提供自动化验证脚本；

8. 不接入真实业务数据。

完成后输出环境配置、运行命令、测试结果和已发现问题。

### 5 人工批准冻结

验证通过后，将ADR状态改为“已批准”，并纳入Technical Baseline 1.0。

## 八 本项目候选技术基线

| 技术领域 | 候选基线 |
| --- | --- |
| 前端 | Vue 3 TypeScript Vite Element Plus ECharts |
| 后端 | Python FastAPI Pydantic SQLAlchemy |
| 关系数据库 | PostgreSQL |
| 缓存 | Redis |
| 消息队列 | RabbitMQ |
| 对象存储 | MinIO |
| 全文检索 | OpenSearch |
| 向量检索 | Milvus |
| 传播关系 | 一期优先PostgreSQL 复杂图分析再评估Neo4j |
| 模型训练 | PyTorch Transformers MMEngine |
| 模型管理 | MLflow |
| 视频处理 | FFmpeg OpenCV |
| OCR | PaddleOCR |
| ASR | Whisper或符合部署要求的语音模型 |
| 模型推理 | FastAPI推理服务 性能瓶颈模型使用Triton |
| 服务容器 | Docker |
| 开发集成环境 | Docker Compose |
| 正式部署 | 根据目标环境决定是否采用Kubernetes |
| 监控 | Prometheus Grafana Loki |
| 测试 | Pytest Playwright Vitest |
| 持续集成 | GitLab CI或现有代码管理平台流水线 |


以下内容不能直接冻结：是否采用Kubernetes、是否部署Neo4j、是否必须使用国产数据库、OCR和ASR最终模型、CUDA与PyTorch及Triton版本、模型正式验收指标、正式服务器数量以及是否允许访问外部网络平台。

## 九 第二阶段交付物

### 文档与决策记录

docs/02-architecture/environment-constraints.md

docs/02-architecture/technology-options.md

docs/02-architecture/technical-baseline.md

docs/02-architecture/compatibility-matrix.md

docs/02-architecture/system-architecture.md

docs/02-architecture/deployment-architecture.md

docs/02-architecture/architecture-decisions/目录中的ADR

### 配置与工程文件

config/versions.yaml

config/environments.yaml

config/ports.yaml

backend/pyproject.toml及锁文件

frontend/package.json及锁文件

ai-services运行环境锁定文件

deploy/docker-compose.yml

各服务Dockerfile

deploy/.env.example

### 配套成果

技术栈验证报告

软件许可证清单

兼容性检查报告

最小验证工程

技术基线评审记录

Technical Baseline 1.0

## 十 第二阶段完成判定

部署环境和网络边界已经明确

前端 后端和算法框架已经确定

数据库 对象存储 缓存和消息队列已经确定

关键软件版本已经锁定

最小验证工程能够启动

前端 后端 数据库 存储和消息队列能够连通

GPU容器能够正常识别显卡

模型服务契约已经验证

CI能够完成构建 测试和镜像生成

技术选型已经形成ADR

技术基线已经由项目负责人批准

后续技术变更具有审批和记录机制

只有上述条件基本满足后，才适合批量启动具体Codex开发任务。最终协作模式应为：Codex提出并验证，技术负责人决策，项目负责人批准，Codex固化并执行。

