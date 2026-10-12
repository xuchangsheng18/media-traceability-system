# 开发数据冷备份与隔离恢复演练

适用1.1-py310-cpu，自建非敏感数据、专用media-trace-py310开发栈。实际入口为[scripts/verify_development_recovery.py](../../scripts/verify_development_recovery.py)，运行前确认开发维护时段，因为会短暂停止本项目worker、API、推理与S3；不会暂停其他项目。

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py310/bin/python scripts/verify_development_recovery.py
```

## 备份与核验对象

| 对象 | 方式和恢复要求 |
| --- | --- |
| 数据库 | pg_dump自定义格式、无owner/ACL；恢复5表所有行、任务结果和迁移账本到临时PostgreSQL；普通角色授权由初始化重新配置 |
| 版本化对象 | 枚举所有现存对象版本及SHA-256；停S3后复制整个/data物理卷，包含filerldb2、master及volume数据；保留原VersionId，不能用重新上传代替 |
| 模型 | 停推理后复制/runtime权重/实验记录；恢复到新卷，摘要一致，禁止重新训练后冒充恢复 |
| 摘要清单 | 备份文件逐份SHA-256，恢复前校验；故意损坏数据库备份必须先被拒绝 |
| 凭据 | 不写备份包和Git；S3读回沿用已有私有凭据卷，完全丢失密钥场景仍待另设恢复流程 |

产物位于MT_RUNTIME_DIR/backups/mt-recovery-<随机标识>，默认服务器路径在仓库外；目录0700、文件0600。具体路径、时间、行数和版本数见[development-recovery-report.json](../00-project/validation/development-recovery-report.json)。备份不自动外传、不自动删除；容量规划须单独落实，不能无限积累在接近满的Desktop虚拟磁盘内。

在临时internal网络、新对象/模型卷及临时数据库恢复，比较全部数据库行和每个原VersionId/SHA，再验证缺失版本拒绝与权重一致。服务finally恢复，临时资源按本次唯一名称清理；只读挂载原凭据卷，不向原数据卷写入。S3临时启动的500/502/503/504最多重试20次，摘要或权限错误不能重试为通过。

8项检查已通过；截至本轮服务器完整CI，核验45个对象版本。版本数会随后续测试增加，以报告时点为准。耗时是开发演练观测值，不是批准的RTO。未验证生产WAL/PITR、异机/异地密钥恢复、全业务数据、删除标记/生命周期/WORM、索引重建、长期备份保留或正式RPO/RTO；T121仅有开发子范围证据。

数据库工具依据[PostgreSQL16 SQL Dump](https://www.postgresql.org/docs/16/backup-dump.html)，物理对象恢复仍须与实际SeaweedFS锁定版本、完整卷及网络标识一起验证。
