# 开发环境基线候选

> 2026-10-23活动基线变更：用户已批准全项目迁移至Python3.11.17、Pillow13.0.0及certifi2026.10.19。当前执行按[迁移计划](../superpowers/plans/2026-10-23-python311-migration.md)与config/versions.yaml；旧py310、原锁及历史记录仅保留回退和来源。新环境已闭合100包且扫描无已报告阻断匹配，完整CI与运行验证尚需按新源码核验；生产未冻结，算法仍暂缓。

2026-10-14；第三阶段研发实施候选，正式批准/冻结未完成。

Development Environment Baseline 1.0候选，NOT_FROZEN。此名称来自第三阶段手册，不取代实际Technical Baseline 1.1-py310-cpu的工程版本，也不是已批准的生产Python基线。

配置源：config/versions.yaml与原锁；Python为Miniforge3.10.22，Node22.21.1，FastAPI/Vue、CPU Torch、PostgreSQL/对象/队列与镜像组合按原源，不自行升级。新增pre-commit仅是独立研发工具层，另锁和验真，不改变项目100包。统一入口、质量范围及容量保护见config/stage-three-profile.json。

已有7服务、5表PoC和合成M15链路沿用；不将真实34能力、GPU、55业务接口/62业务表、3场景或全部170任务写成完成。接口命名/模拟例子的手册建议与现有PoC的等价/差异见[第三阶段状态](stage-three/readiness.md)。源码与运行镜像一致性、CI源码SHA和报告制品以实际回执为准。

冻结必须具备：获准平台/模式/分支和人员权限、有效技术输入与软件准入、受控Runner/Secret和主分支保护、足够资源及实际网络边界、适用质量/安全结果、可复现启动和用户验收、明确责任人与完整决定。当前正式输入未齐，阶段1/2冻结仍未完成；本文件只记录候选，不创建标签/发布或自动批准ADR。

源手册的比例30%—40%人工/60%—70%Codex是协作建议，不是本项目实测完成率。

16步及57条原验收要求分别登记工程状态、证据范围和剩余条件，避免用统一“已补材料”代替实际进度。模拟骨架具备脱敏结构日志、三服务trace关联、独立浏览器验证及依赖停止后的503/502测试；它们属于研发连通性验证。共享栈修改均要求显式标志，CI环境名不能单独跳过容量保护，无法读取容量也停止。

开发基础整改见[实际审查](../00-project/validation/stage-three-foundation-audit-report.json)及[变更和恢复要求](development-environment-change-request.md)：旧应用指定范围格式统一且AST保持；两端CLI规则及可信项目配置层已验证；Torch官方制品和安装载荷已核对。共享VM容量、私有平台保护套餐、实际人员、Python静态类型和正式环境决定仍未齐备，NOT_FROZEN保持。
