# 技术方案比较与执行选择

2026-10-12；本轮选择适用于 CPU 研发最小工程。源设计候选不全部装入共享主机。每项详细决定见 [TB-ADR 索引](architecture-decisions/README.md)，精确版本见 [versions.yaml](../../config/versions.yaml)。

| 能力 | 本轮选择 | 比较方案 | 本轮理由及边界 |
| --- | --- | --- | --- |
| 前端 | Vue 3 / TypeScript / Vite | React / Vite；纯服务端页面 | 沿用设计方向，构建与浏览器验证通过；组件库暂不引入，不关闭 Q-12 |
| 后端 | FastAPI / SQLAlchemy / psycopg | Django；Java Spring | 使用用户指定 py310，直接复用 JSON Schema；并非正式平台软件准入决定 |
| 事务库 | PostgreSQL 16.15 | MySQL；指定国产关系库 | 既有约束源已按 PostgreSQL 验证；使用独立开发库和版本迁移 |
| 对象 | SeaweedFS 4.48 / S3 | 经许可评审的 MinIO；受控文件系统 | 版本 ID 与摘要实际读写通过；保留策略、对象锁及多节点恢复未通过验收 |
| 消息 | RabbitMQ 4.3.6 / Celery 5.6.3 | Redis broker；数据库轮询 | 有持久队列、发布确认、outbox 与恢复检查；不加入不必要缓存；Kafka 不作为本轮 Celery 执行 broker |
| 搜索 | PostgreSQL simple 全文查询；NumPy 精确向量排序机制检查 | OpenSearch；Milvus / pgvector | 验证基础机制，暂不部署大型索引；没有完成中文分词、业务检索 API 或 ANN 容量验收 |
| 传播图 | PostgreSQL 关系表方向与递归 SQL 检查 | Neo4j；专用图服务 | 3 节点带环查询通过；并未实现业务传播关系分析 |
| 训练 | PyTorch CPU / 固定种子 / 版本化实验 JSON | MLflow；独立训练平台 | 实际训练 64 条自建张量 120 步；不足以替代业务模型训练管理 |
| 推理 | 独立 FastAPI / PyTorch CPU | ONNX Runtime；Triton | 复用 M15 请求/响应 Schema，记录版本与对象引用；不使用 GPU 或未经授权权重 |
| 媒体 | Pillow / imageio-ffmpeg 自带 FFmpeg | PyAV；OpenCV | 图片原件/副本分离；合成视频编码与解码通过；非零原点合成抽帧PTS已核验；VFR/正式视频链路未验收 |
| 认证安全 | 研发 Bearer + 独立内部令牌 | OIDC 统一身份；完整 RBAC/ABAC | 默认拒绝、秘密不入库；单固定测试案件，不能作生产案件隔离方案 |
| 部署 | Docker Compose 独立项目 | 裸进程/systemd；Kubernetes | 共享节点上可运行并有资源限制；没有新增集群，也不改变其他项目 |

扩展触发：业务查询语义、数据量、GPU、正式身份或现场准入明确后，新增 ADR、锁文件与验证证据；不得将未选产品版本写成已锁定。原始12模块170任务保留，本轮 PoC 只验证工程链路。
