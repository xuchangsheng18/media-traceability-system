# 第二阶段23步交付与实际状态

2026-10-12；1.1-py310-cpu。优先要求的环境清单→版本锁定→最小工程→CI已经在用户Miniforge py310实测；新增迁移/事件/租约/追踪/PTS/冷恢复已补齐。开发基线DEVELOPMENT_VALIDATED，正式业务/生产NOT_FROZEN；GitHub平台结论独立记录。不是全部23步正式批准或170任务全实现。

| 步骤 | 工作 | 已完成及剩余范围 | 开发状态 |
| --- | --- | --- | --- |
| 1 | 环境约束 | 已核验开发Linux/py310/Desktop、网络与挂载限制；生产边界待确认 | DEV_RECORDED |
| 2 | 资源与团队 | 宿主/虚拟机/容器配额已盘点；GPU、独占配额和人员待落实 | DEV_RECORDED |
| 3 | 非功能指标 | 沿用需求源，明确实测口径；正式指标与并发未定 | DEV_SCOPED |
| 4 | 候选架构 | 12域比较及本轮选择已记录 | DEV_DECIDED |
| 5 | 前端选型 | Vue/TS/Vite锁与真实构建/browser；组件库未定 | DEV_VALIDATED |
| 6 | 后端选型 | 用户指定py310、FastAPI工程/锁/配置/API已运行 | DEV_VALIDATED |
| 7 | 关系库与访问 | PoC迁移账本/0002升级及15竞态/权限检查；正式62表迁移/RLS仍待验收 | DEV_VALIDATED |
| 8 | 对象存储 | S3版本/摘要/重启及物理冷恢复通过；WORM/生命周期/密钥灾备未验收 | DEV_VALIDATED |
| 9 | 缓存与队列 | Rabbit/Celery、确认/outbox/幂等、原子领取与旧租约写回拒绝通过；真实多worker故障仍待验收 | DEV_VALIDATED |
| 10 | 全文与向量 | simple SQL和3向量机制通过；未完成中文或大型索引/业务API | DEV_PARTIAL |
| 11 | 传播关系存储 | 递归带环微型SQL通过；正式传播图业务待实现 | DEV_PARTIAL |
| 12 | 训练和实验 | 实际合成训练、权重/实验JSON；正式业务模型/实验平台待补 | DEV_VALIDATED_SYNTHETIC |
| 13 | 推理服务 | 独立CPU真实推理与M15契约通过；正式模型/GPU未测 | DEV_VALIDATED_SYNTHETIC |
| 14 | 视频媒体处理 | 合成10帧及非零源PTS抽帧映射通过；VFR/正式视频流水线未验收 | DEV_PARTIAL |
| 15 | 安全认证审计 | 研发鉴权、统一Problem/全任务追踪、普通角色追加审计通过；正式身份/RLS/防篡改未验收 | DEV_PARTIAL |
| 16 | 容器与编排 | 7服务/5卷/配额/健康/重启验证；生产平台未批准 | DEV_VALIDATED |
| 17 | 版本兼容许可 | 精确锁/摘要/兼容与许可盘点；PythonEOL、FFmpeg/Desktop及OS审查待补 | DEV_LOCKED |
| 18 | 规范和目录 | 真实目录、Ruff/TS检查、README与运行手册 | DEV_VALIDATED |
| 19 | 接口事件契约 | [整体说明](../03-api/system-interface-specification.md)/53逐接口/83组件/34能力已详细化；M24副本3项约束修正，PoC实测保留；[13项整体缺口](../03-api/interface-gap-register.md)仍开放 | DEV_VALIDATED_POC_OVERALL_CONTRACT_GAPS |
| 20 | 最小可运行工程 | 浏览器/对象/SQL/queue/worker/真实合成CPU结果已运行 | DEV_VALIDATED |
| 21 | CI质量门禁 | 本机21门禁及失败阻断通过，私有GitHub已接入；平台结论按github-actions-report.json | LOCAL_CI_VALIDATED_HOSTED_RECORDED_SEPARATELY |
| 22 | 基线评审包 | 技术基线、14ADR和实际证据已形成；正式责任人/评审未签署 | REVIEW_PACKAGE_READY |
| 23 | 冻结与变更 | 开发源码快照与变更规则；正式生产NOT_FROZEN | NOT_FROZEN |

[技术基线](../02-architecture/technical-baseline.md)、[实际验证](../02-architecture/technical-validation-report.md)、[机器23步清单](stage-two-deliverables.json)与[剩余条件/关闭标准](stage-two-gap-register.md)一起使用。GitHub实际run、源码SHA及制品校验见[平台报告](../00-project/validation/github-actions-report.json)。

DEV_VALIDATED仅对本行开发范围有效。普通权限追加审计不是管理员不可篡改；8数据库竞争者不是8Celery传输验收；非零PTS不是VFR全视频；冷恢复不是生产灾备；合成模型不是业务模型。生产身份/审批/准入/容量/许可/责任人及冻结不自动关闭。保留12模块、170任务和≥3场景，生产Python迁移仍需重测。
