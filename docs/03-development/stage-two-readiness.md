# 第二阶段23步交付与实际状态

2026-10-12；1.0-py310-cpu。用户优先要求的环境清单→版本锁定→最小可运行工程→CI，本轮已在指定Miniforge py310真实执行。当前为CPU研发基线DEVELOPMENT_VALIDATED，正式业务/生产NOT_FROZEN；不能把这四项完成扩大为全部23步正式批准或170项业务实现。

| 步骤 | 工作 | 已完成及剩余范围 | 开发状态 |
| --- | --- | --- | --- |
| 1 | 环境约束 | 已核验开发Linux/py310/Desktop、网络与挂载限制；生产边界待确认 | DEV_RECORDED |
| 2 | 资源与团队 | 宿主/虚拟机/容器配额已盘点；GPU、独占配额和人员待落实 | DEV_RECORDED |
| 3 | 非功能指标 | 沿用需求源，明确实测口径；正式指标与并发未定 | DEV_SCOPED |
| 4 | 候选架构 | 12域比较及本轮选择已记录 | DEV_DECIDED |
| 5 | 前端选型 | Vue/TS/Vite锁与真实构建/browser；组件库未定 | DEV_VALIDATED |
| 6 | 后端选型 | 用户指定py310、FastAPI工程/锁/配置/API已运行 | DEV_VALIDATED |
| 7 | 关系库与访问 | PostgreSQL16.15、PoC迁移、隔离73SQL案例通过；正式迁移/RLS未验收 | DEV_VALIDATED |
| 8 | 对象存储 | S3版本/摘要/重启读回通过；WORM/保留/撤销未验收 | DEV_VALIDATED |
| 9 | 缓存与队列 | 固定Rabbit/Celery，确认/outbox/幂等/单worker恢复通过 | DEV_VALIDATED |
| 10 | 全文与向量 | simple SQL和3向量机制通过；未完成中文或大型索引/业务API | DEV_PARTIAL |
| 11 | 传播关系存储 | 递归带环微型SQL通过；正式传播图业务待实现 | DEV_PARTIAL |
| 12 | 训练和实验 | 实际合成训练、权重/实验JSON；正式业务模型/实验平台待补 | DEV_VALIDATED_SYNTHETIC |
| 13 | 推理服务 | 独立CPU真实推理与M15契约通过；正式模型/GPU未测 | DEV_VALIDATED_SYNTHETIC |
| 14 | 视频媒体处理 | PNG/JPEG及合成10帧编解码通过；源时间映射未测 | DEV_PARTIAL |
| 15 | 安全认证审计 | 研发Bearer/秘密/Problem与日志；正式身份/RLS/审计待补 | DEV_PARTIAL |
| 16 | 容器与编排 | 7服务/5卷/配额/健康/重启验证；生产平台未批准 | DEV_VALIDATED |
| 17 | 版本兼容许可 | 精确锁/摘要/兼容与许可盘点；PythonEOL、FFmpeg/Desktop及OS审查待补 | DEV_LOCKED |
| 18 | 规范和目录 | 真实目录、Ruff/TS检查、README与运行手册 | DEV_VALIDATED |
| 19 | 接口事件契约 | 两份API类型生成无漂移、模型Schema实际执行；完整事件信封未完成 | DEV_PARTIAL |
| 20 | 最小可运行工程 | 浏览器/对象/SQL/queue/worker/真实合成CPU结果已运行 | DEV_VALIDATED |
| 21 | CI质量门禁 | 同源本机完整CI和失败阻断通过；托管Runner未注册 | LOCAL_CI_VALIDATED |
| 22 | 基线评审包 | 技术基线、12ADR和证据已形成；正式评审未签署 | REVIEW_PACKAGE_READY |
| 23 | 冻结与变更 | 开发源码快照与变更规则；正式生产NOT_FROZEN | NOT_FROZEN |

## 证据与使用

[技术基线](../02-architecture/technical-baseline.md)汇总环境、技术比较、12项ADR、锁与运行入口；[技术验证报告](../02-architecture/technical-validation-report.md)列出实际结果及未测项；[机器清单](stage-two-deliverables.json)保留原计划字段并区分development_status与formal_completion_asserted。

DEV_VALIDATED只对本行研发范围有效。搜索/图/媒体/安全/事件为部分机制或基础验证；正式身份、案件策略、审批/WORM、业务模型、GPU、并发、备份、现场准入、责任人和正式冻结没有被自动关闭。托管CI配置与本机执行分开记录。

原手册与Word继续作来源。实际执行由用户指定py310替代3.11候选；3.10已EOL，生产需迁移后重测。API与Schema唯一源、12模块、170任务和≥3场景保持。新增实现应按任务卡和其具体完成条件逐项验收。
