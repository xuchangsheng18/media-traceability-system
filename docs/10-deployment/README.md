# 部署与资源

当前可启动py310 CPU最小工程；正式业务/生产NOT_FROZEN。

- [实际启动与排查](development-runbook.md)：可执行命令、6个回环端口、7服务和5个卷。
- [环境约束](../02-architecture/environment-constraints.md)、[资源清单](../02-architecture/resource-and-team-inventory.md)。
- [环境原始快照](../00-project/validation/environment-inventory.json)；[历史服务器观测](server-observation.md)按其时点阅读。
- [原部署计划](deployment-plan.md)仍用于后续生产、备份和恢复设计。

开发栈独立，不修改其他项目。默认停止保留数据卷；重启持久化检查不等于正式灾备恢复通过。

## 1.1工程补充

开发数据备份与隔离恢复的范围、维护时段、VersionId保留和密钥边界见[冷备恢复手册](development-backup-restore.md)。
