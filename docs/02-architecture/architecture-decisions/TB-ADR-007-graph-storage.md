# TB-ADR-007 传播关系存储

2026-10-12；accepted-development；适用miniforge-py310-linux-x86_64-cpu。实际执行由本会话完成；正式批准人与生产准入待指定，不填入虚构人名。原设计ADR-01—05不覆盖。

决定：PostgreSQL关系表方向 / 递归SQL。

比较的替代方案：Neo4j；专用图服务。本轮选择理由：3节点带环递归检查可执行，关系事实源保持既有数据库设计。

精确版本/来源：仓库根目录 `config/versions.yaml`，并结合config/versions.yaml和config/locks中的实际包/镜像摘要。未选产品不锁定虚构版本。

验证证据：docs/00-project/validation内的 media-query-report.json；实际命令见ci-all-report.json及运行手册。资源按专用Compose上限和环境快照，不把快照当峰值。

未验证及后续要求：传播事实/推断边与真实图查询接口未实现；Q-09正式选择未关闭。

回退/变更：以旧Git快照和锁文件恢复应用；卷与数据保留，数据库另经版本迁移；新选型新增ADR并引用本记录，不删旧证据。正式环境变化时重测相关CI、契约、恢复和许可。
