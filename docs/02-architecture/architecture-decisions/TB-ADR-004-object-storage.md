# TB-ADR-004 对象存储

2026-10-12；accepted-development；适用miniforge-py310-linux-x86_64-cpu。实际执行由本会话完成；正式批准人与生产准入待指定，不填入虚构人名。原设计ADR-01—05不覆盖。

决定：SeaweedFS4.48 / S3版本化。

比较的替代方案：经许可评审的MinIO；受控文件系统。本轮选择理由：真实version_id、原件SHA256、独立副本与向量重启读回通过；卷配置适配小磁盘。

精确版本/来源：仓库根目录 `config/locks/docker-images.json`，并结合config/versions.yaml和config/locks中的实际包/镜像摘要。未选产品不锁定虚构版本。

验证证据：docs/00-project/validation内的 poc-integration-report.json、poc-resilience-report.json；实际命令见ci-all-report.json及运行手册。资源按专用Compose上限和环境快照，不把快照当峰值。

未验证及后续要求：WORM/保留、撤销、容灾、许可与大容量配置。

回退/变更：以旧Git快照和锁文件恢复应用；卷与数据保留，数据库另经版本迁移；新选型新增ADR并引用本记录，不删旧证据。正式环境变化时重测相关CI、契约、恢复和许可。
