# 资源与责任清单

2026-10-12 实测，容量均为时点观测。整机不是本项目独占配额。机器记录见 [environment-inventory.json](../00-project/validation/environment-inventory.json)。

| 层次 | CPU / 内存 | 磁盘及限制 |
| --- | --- | --- |
| Linux 宿主 | 96 物理核、192 逻辑线程；总内存约 125.7 GiB | `/workspace` 与 `/opt` 分别约 9.1 TiB；空闲见快照 |
| Docker Desktop 虚拟机 | 128 可见逻辑 CPU；总内存约 31.3 GiB | 虚拟磁盘约 95.8 GiB，观测空闲约 1.9 GiB、使用率 98%；不能用宿主剩余磁盘代替 |
| 开发服务总限制 | CPU 上限合计 6.5；内存上限合计 6.5 GiB | 命名卷隔离；服务上限不是预留资源或峰值测量 |
| 临时 SQL 验证 | 额外 2 CPU / 512 MiB | 无网络、无发布端口、tmpfs；退出后仅删除本轮临时容器 |

| 服务 | CPU 上限 | 内存上限 | PID 上限 |
| --- | --- | --- | --- |
| PostgreSQL | 1 | 1 GiB | 128 |
| RabbitMQ | 1 | 768 MiB | 256 |
| SeaweedFS | 1 | 1 GiB | 128 |
| API | 1 | 768 MiB | 128 |
| CPU 推理 | 1 | 2 GiB | 128 |
| worker | 1 | 768 MiB | 128 |
| Web | 0.5 | 256 MiB | 64 |

RabbitMQ 显式限制 Erlang 调度器；Nginx 按容器配额调整 worker 数，避免按虚拟机 128 核启动过多进程。SeaweedFS 单卷上限 128 MiB、最多 8 卷，不预分配全部容量；这些是小样本开发设置。

当前虚拟磁盘余量只适合本轮小素材验证。批量数据、模型或大型索引引入前必须落实项目磁盘配额或专用 Linux Engine/存储位置。本轮没有执行全局清理、删除其他项目镜像/卷或重新配置 Desktop。内存与 CPU 快照不是压力测试峰值。

| 责任角色 | 本阶段职责 | 实际人员 |
| --- | --- | --- |
| 项目/架构负责人 | 范围、技术决定、变更评审 | 待 Q-33 指定 |
| 后端/前端 | 契约、工程实现、依赖升级 | 待指定 |
| 算法/数据负责人 | 权重、实验、授权、业务指标 | 待指定 |
| DevOps | 配额、备份、制品、CI Runner | 待指定 |
| 安全/业务代表 | 软件准入、身份、案件权限、审计和正式验收 | 待指定 |

本会话完成自动化实现与研发验证，不虚构岗位人员、正式批准人或设备采购结论。样例配置见 [hardware-inventory.example.yaml](../../config/hardware-inventory.example.yaml)。

## 2026-10-13只读容量补查

此前表为2026-10-12环境时点。当前研发PostgreSQL卷所在文件系统的容量、观测时间和服务健康情况直接读取[resource-readiness-snapshot.json](../00-project/validation/resource-readiness-snapshot.json)，容量分级读取[stage-two-resource-report.json](../00-project/validation/stage-two-resource-report.json)；当前为CRITICAL/NOT_READY。不能用宿主机空闲量代替，也不表示已分配项目独占配额。CPU/内存与旧VM观察按各自时点阅读。快照采集不重启、扩容、清理其他项目或读写业务行。nvidia-smi工具不可用不证明物理GPU不存在或GPU兼容已验证。批量素材/模型/索引引入前落实真实存储位置、余量/告警、GPU与责任人。
