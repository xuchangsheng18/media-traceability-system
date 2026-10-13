# 测试与验收

测试策略、场景、模型与安全测试。当前为规划和候选输入，未实现、未冻结。

优先阅读[test-strategy.md](test-strategy.md)。

- [acceptance-criteria.md](acceptance-criteria.md)
- [model-test-scenarios.md](model-test-scenarios.md)
- [security-test-scenarios.md](security-test-scenarios.md)
- [task-test-scenarios.yaml](task-test-scenarios.yaml)
- [test-scenarios.yaml](test-scenarios.yaml)
- [test-strategy.md](test-strategy.md)

## 本轮已执行工程检查

真实CPU最小工程、本机CI、隔离SQL、5项故障恢复、媒体查询和浏览器已运行，见[技术验证报告](../02-architecture/technical-validation-report.md)。原全业务测试计划保留，正式模型/GPU、案件权限、并发和备份恢复未据此自动通过。

## 第一阶段归属

本专题承接第一阶段第18/19步的候选输入，操作、产物和确认要求见[24步对应表](../00-project/stage-one/steps-and-deliverables.md)。专题结构源保持不变，设计/计划与实际实施结果分开。

## 本轮补充（2026-10-13）

[24项验收测量协议](metric-protocols.md)及[机器定义](metric-protocols.json)保持来源目标，明确失败/未知、分母、分层及未执行真实验收。8组公式检查和实际模型/负载验收分开。

## 第一阶段工程控制补充（2026-10-13）

[24验收执行配置](acceptance-execution-configuration.md)及逐项预检查补全真实条件，资料齐全仅READY_FOR_EXECUTION，不自动形成PASS。
