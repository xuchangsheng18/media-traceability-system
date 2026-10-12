# TB-ADR-005 缓存与消息

2026-10-12；accepted-development；适用miniforge-py310-linux-x86_64-cpu。实际执行由本会话完成；正式批准人与生产准入待指定，不填入虚构人名。原设计ADR-01—05不覆盖。

决定：RabbitMQ4.3.6 / Celery5.6.3，无业务缓存。

比较的替代方案：Redis broker；数据库轮询。本轮选择理由：确认发布、持久消息、outbox、幂等与单worker租约恢复；不引入与本轮无关的缓存。

精确版本/来源：仓库根目录 `config/locks/requirements-py310.lock`，并结合config/versions.yaml和config/locks中的实际包/镜像摘要。未选产品不锁定虚构版本。

验证证据：docs/00-project/validation内的 poc-resilience-report.json、poc-integration-report.json；实际命令见ci-all-report.json及运行手册。资源按专用Compose上限和环境快照，不把快照当峰值。

1.0时未验证；1.1已补旧租约写回拒绝，见TB-ADR-013。后续要求：集群、死信、真实多worker传输故障演练；禁用远控/mingle/gossip后再引入需复测。

回退/变更：以旧Git快照和锁文件恢复应用；卷与数据保留，数据库另经版本迁移；新选型新增ADR并引用本记录，不删旧证据。正式环境变化时重测相关CI、契约、恢复和许可。
