# TB-ADR-002 后端与Python

2026-10-12；accepted-development；适用miniforge-py310-linux-x86_64-cpu。实际执行由本会话完成；正式批准人与生产准入待指定，不填入虚构人名。原设计ADR-01—05不覆盖。

决定：用户指定Miniforge py310 / FastAPI / SQLAlchemy。

比较的替代方案：Python3.11候选；Django / Java Spring。本轮选择理由：复用现有py310，真实依赖安装、配置、API、wheel和容器通过；源任务3.11文字作为历史依据保留。

精确版本/来源：仓库根目录 `config/locks/requirements-py310.lock`，并结合config/versions.yaml和config/locks中的实际包/镜像摘要。未选产品不锁定虚构版本。

验证证据：docs/00-project/validation内的 runtime-lock-report.json、lock-reproduction-report.json、ci-all-report.json；实际命令见ci-all-report.json及运行手册。资源按专用Compose上限和环境快照，不把快照当峰值。

未验证及后续要求：Python3.10 EOL，正式生产组合与单位准入尚未确认。以下为2026-10-13补入的选型条件，不改变本ADR原有accepted-development状态，不构成生产批准。

## 生产Python选型与验证条件

本项目当前3.10.22已通过研发安装、锁、构建及PoC运行验证，可以继续作为研发环境；这不证明它是新生产系统的最佳长期维护版本。Python3.10已于2026-10-01结束官方支持，3.10.22是最后安全更新版本；安装官方CPython或使用Miniforge都不代表获得额外的上游维护承诺。依据[官方发布说明](https://www.python.org/downloads/release/python-31022/)和[官方维护表](https://devguide.python.org/versions/)。

生产版本建议优先验证3.13，3.12作为兼容备选；维护表所列预计结束支持月份分别为2029-10与2028-10。此顺序是项目选型建议，准确机器条件维护在[versions.yaml](../../../config/versions.yaml)的production_python_selection；当前精确版本、生产锁、验证和批准均未填写。实施时重新查维护状态，并将投产时间、预期维护期及升级责任纳入决定；不把预计日期当无限期支持承诺。

| 验证项 | 所需实际证据和通过标准 |
| --- | --- |
| 支持与现场准入 | 核验官方或有文件依据的供应方补丁支持；明确目标OS/架构/国产化/网络与离线准入、维护窗口和升级计划 |
| 全部依赖与安装 | 在新隔离环境核对全部直接/传递依赖的Requires-Python、原生wheel/系统库和来源；干净安装、pip check和导入通过。项目目前backend/pyproject.toml限定>=3.10,<3.11，必须审核并调整新目标声明；不能直接拿旧锁安装新解释器 |
| 锁和构建 | 新建目标版本独立依赖/Conda/OS及镜像锁和摘要；记录解释器补丁、发行来源、基础镜像与构建工具。原py310锁和运行证据保留，机器候选分支不等同已锁精确版本 |
| 业务模型与媒体 | 对实际启用的OCR/ASR/检索/训练推理等能力逐项验证，按用途授权和封存测试规则执行；CPU与GPU/驱动/CUDA组合分别验收。PyTorch声明支持某Python版本或M15合成CPU成功不能替代完整业务模型兼容与效果验证 |
| 完整工程门禁 | 在新环境执行对应源版本的完整CI、契约/生成类型、SQL迁移、API/队列/worker、媒体、浏览器、失败阻断和恢复检查；保存源码SHA、平台run、实际报告和制品摘要。当前py310的25道PASS不能转记为3.12/3.13 PASS |
| 安全和交付 | 核验OS/二进制/包/权重物料、漏洞处置和许可，按目标完成离线制品校验；收集依赖元信息不等同完成漏洞与许可审查 |
| 回退与决定 | 明确隔离部署、应用回退、数据库迁移与数据恢复方案；落实实际维护人和有效准入决定、适用能力/范围/有效期，再锁定正式生产版本 |

实际记录填写[第二阶段外部输入](../../03-development/stage-two-external-inputs.json)的production_python_validation；缺少证据时保持NOT_PERFORMED和未批准。先核查本次拟启用能力，不能用未实施的能力代替验证，也不能静默删除原12模块170任务范围。当前研发数据卷CRITICAL；新环境和大体积构建须先通过容量条件。

## Python3.10生产例外

仅在确有旧模型/原生依赖或现场平台限制时评估，不能仅以“以前项目常用”或“现有环境能运行”作为依据。须记录具体阻断依赖/版本/错误及其他版本验证结果，提供实际维护发行版和补丁来源、漏洞修复覆盖/响应与维护承诺、隔离范围、到期/退出迁移计划、实际责任人及有效风险/准入决定。供应方维护不等同Python官方恢复支持，发行渠道名称本身也不是延长维护的证明。

当前上述依据全部待填，例外未申请、未批准；production_approved保持false，not_selected.production_python保持null。本次只写入选型与验证条件，不安装生产候选环境、不切换已有服务、不修改既有业务数据。

回退/变更：以旧Git快照和锁文件恢复应用；卷与数据保留，数据库另经版本迁移；新选型新增ADR并引用本记录，不删旧证据。正式环境变化时重测相关CI、契约、恢复和许可。
