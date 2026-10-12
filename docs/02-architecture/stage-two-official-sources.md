# 第二阶段官方资料核验

核验日期2026-10-12。外部文档支撑机制、兼容或许可；本项目的部署事实和PASS来自实际运行报告，不由网页推定。

| 官方来源 | 用于本轮的事实/判断 |
| --- | --- |
| [Python维护表](https://devguide.python.org/versions/) | 3.10于2026-10-01结束支持，登记生产迁移 |
| [FastAPI起步](https://fastapi.tiangolo.com/tutorial/first-steps/) | Python与应用入口，实际兼容以锁环境测试为准 |
| [Vite指南](https://vite.dev/guide/) | Node兼容要求；22.21.1满足22.12+ |
| [RabbitMQ队列](https://www.rabbitmq.com/docs/queues) | 4.3默认拒绝非独占临时队列；改客户端配置而非开启弃用项 |
| [Celery配置](https://docs.celeryq.dev/en/stable/userguide/configuration.html) | 事件exclusive、远控开关、持久消息及prefetch |
| [SeaweedFS仓库](https://github.com/seaweedfs/seaweedfs) | 版本/S3服务；标签LICENSE和实际桶版本单独验证 |
| [PyTorch CPU安装](https://docs.pytorch.org/get-started/locally/) | 官方CPU索引；本轮没有GPU结论 |
| [OpenAPI TypeScript](https://openapi-ts.dev/introduction) | 从3.0/3.1生成TS类型；不提供运行时校验 |
| [PostgreSQL16全文](https://www.postgresql.org/docs/16/textsearch.html) | simple文本机制；不能推定中文检索完成 |
| [PostgreSQL16递归查询](https://www.postgresql.org/docs/16/queries-with.html) | 递归SQL及环防护；本轮仅3节点夹具 |
| [Nginx upstream](https://nginx.org/en/docs/http/ngx_http_upstream_module.html) | resolve/共享zone处理服务地址变化 |
| [FFmpeg许可](https://ffmpeg.org/legal.html) | 编译GPL选项影响实际二进制许可 |
| [Docker Desktop条款](https://docs.docker.com/subscription-billing/desktop-license/) | Desktop与Engine不同，政府实体订阅要求需核验 |

所有未选择的产品版本和GPU组合不作已锁定声明。外部信息变化时更新此记录及对应ADR，不能照抄原手册中的环境示例作实际清单。

## 1.1工程补充依据（2026-10-12）

| 官方依据 | 对应项目验证 |
| --- | --- |
| [PostgreSQL16事务锁](https://www.postgresql.org/docs/16/explicit-locking.html) | 迁移串行锁和条件领取/写回；15隔离项 |
| [PostgreSQL16 SQL Dump](https://www.postgresql.org/docs/16/backup-dump.html) | pg_dump/pg_restore隔离开发恢复；不是WAL/PITR |
| [FFmpeg命令文档](https://ffmpeg.org/ffmpeg.html) | copyts/抽帧/PTS保留；5秒原点合成验证，未测VFR |
| [GitHub托管Runner](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) | 独立ubuntu-24.04复建锁定py310，与172主机分开 |
| [Actions安全配置](https://docs.github.com/en/actions/reference/security/secure-use) | Actions提交摘要、read权限、临时配置与制品边界 |

上述说明是机制参考；是否成功以仓库实际报告、环境、源码SHA和未测范围判断，不将官方通用说明当成本项目业务批准。
