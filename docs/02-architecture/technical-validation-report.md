# 第二阶段技术验证报告

节点172.16.58.179，2026-10-12，Python3.10.22 / Miniforge py310 / CPU。结论：本轮优先的环境清单、版本锁定、最小可运行工程和本机CI已形成实际交付。报告以具体 scope 解释 PASS，未声称生产或真实业务模型验收完成。

| 检查 | 实际证据 | 说明 |
| --- | --- | --- |
| 干净安装 | [lock-reproduction-report.json](../00-project/validation/lock-reproduction-report.json) | 仓库外新建 venv、按精确锁安装；pip check 和实际导入通过 |
| 当前环境锁 | [runtime-lock-report.json](../00-project/validation/runtime-lock-report.json) | Python补丁与全部100个第三方包一致；修改会阻断 |
| 单元/类型/构建 | [ci-all-report.json](../00-project/validation/ci-all-report.json) | 后端7项、前端2项；TS类型、前端生产构建、后端wheel、两类镜像 |
| 输入与字段契约 | [local-validation-report.json](../00-project/validation/local-validation-report.json)、[database-contract-report.json](../00-project/validation/database-contract-report.json) | 资料结构10项、数据库契约17项，含335夹具；不代表业务代码全实现 |
| 隔离数据库 | [database-foundation-report.json](../00-project/validation/database-foundation-report.json) | 25常规SQL断言＋48首发排序/证据案例＝73；报告51条包含执行组/DDL记录；临时容器已清理 |
| 类型生成 | [generated-contract-report.json](../00-project/validation/generated-contract-report.json) | 两份权威OpenAPI生成的TS类型可重复生成，无漂移 |
| 实际链路 | [poc-integration-report.json](../00-project/validation/poc-integration-report.json) | 15项：页面、鉴权、原件/摘要/版本、SQL、队列、幂等、worker、模型与映射版本、实际CPU解释器 |
| 故障恢复 | [poc-resilience-report.json](../00-project/validation/poc-resilience-report.json) | 5项：broker中断任务持久化、过期租约恢复、结果重启持久化、版本向量读回、同键异资产拒绝 |
| 媒体/查询 | [media-query-report.json](../00-project/validation/media-query-report.json) | 6项：10帧实际编码解码、带环SQL、simple全文、3向量精确排序、内部鉴权/契约 |
| 浏览器 | [poc-browser-report.json](../00-project/validation/poc-browser-report.json)、[运行截图](../00-project/validation/poc-ui.png) | Chromium真实上传与异步结果；截图前清空令牌 |
| 合成训练 | [synthetic-training-experiment.json](../00-project/validation/synthetic-training-experiment.json) | 64随机张量、固定种子20261012、120步，损失0.4231→0.03263；不是业务评测 |
| 失败门禁 | [ci-failure-gate-report.json](../00-project/validation/ci-failure-gate-report.json) | 故意失败使实际CI返回非零并停止后续构建/部署；probe FAIL为预期，不是完整CI失败 |
| 凭据与依赖 | [repository-secrets-report.json](../00-project/validation/repository-secrets-report.json)、[python-audit-report.json](../00-project/validation/python-audit-report.json) | 凭据确切值不在交付；pip-audit已知库无发现，CPU torch跳过；npm audit已执行 |

实际修复：Rabbit4.3拒绝非独占临时队列，客户端禁用远控/mingle/gossip；共享主机调度器过多，限定Erlang与Nginx；Seaweed卷不足，改8卷/128MiB；Nginx旧DNS缓存，启用resolve；重启测试显式等待存储依赖。没有删除测试或启用弃用兼容开关来掩盖失败。

未测：GPU/CUDA、正式SSCD及业务模型、中文检索/大规模向量、源时间映射、多worker旧租约拒绝、生产RLS/统一认证/审批/WORM、灾备恢复、正式并发20/100与指标、托管CI执行、完整离线制品和OS漏洞扫描。上述项属于后续生产/业务范围，保留在23步状态和Q记录中。
