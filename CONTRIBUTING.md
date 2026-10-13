# 研发贡献与验证

当前使用既有Miniforge py310 CPU研发组合；正式环境基线与人员权限待确认。完整范围、唯一接口/Schema来源与数据约束见[AGENTS.md](AGENTS.md)，第三阶段[16步状态](docs/03-development/stage-three/readiness.md)给出实际证据和缺项。

从对应T任务卡核验输入、执行依赖、契约、权限及验收，再修改具体代码。候选治理流程为功能分支和评审后合并，实际评审人数、管理员及分支保护尚未生效证明；本次用户明确要求GitHub/服务器同步，不能把该授权推广为任意发布或账号操作。

Linux在仓库根目录使用`/opt/conda/glwy/envs/py310/bin/python scripts/dev.py <命令>`，命令包括help、setup、lint、format-check、type-check、test、contract-test与security-scan。当前服务器make未安装，Makefile只是已有make环境的等价别名，不将其记录为本机已运行成功。Windows默认用`& .\scripts\dev.ps1 help`和`& .\scripts\dev.ps1 status`协调同一Linux仓库；`-Target local`要求另外准备本机3.10.22锁定环境，本次不声称已验证Windows原生安装。

`dev`默认只观察既有7服务；显式`--allow-stack-changes`才启动命名研发栈，且会检查数据库文件系统容量。`build/integration-test/ci`在共享服务器上受到同一保护；当前容量不足时拒绝执行。GitHub临时CPU Runner执行完整工程门禁。`stop`不删除卷，`clean`默认仅预览两个精确缓存目录，`--apply`才清理，原件、数据、权重、数据库、运行秘密和Git均不在允许清理范围。

代码格式检查当前覆盖第三阶段新增Python；现有应用按原Ruff与TS检查，已有格式债务不以一次性改写解决。Black/MyPy/ESLint/Stylelint等未选工具不冒充已启用。新增适用工具需另锁版本并验证；本机与CI均使用同一任务入口。

`setup --tools`在仓库外建立单独锁定的pre-commit工具层，保留项目100包锁与py310。先运行`pre-commit run --all-files`验证，再由开发人员选择安装本地hook；本次不重写现有Git hooks。该工具层不作为生产Python或业务依赖变更。

若网络较慢，可把工具锁中12个包按制品清单核验SHA-256后放到仓库外的`stage-three-quality-wheelhouse`；安装会使用该缓存并继续强制包摘要。也可通过`MT_QUALITY_WHEELHOUSE`指定获准外部缓存。缓存/安装包不提交Git，镜像源凭据由操作者私下提供。

提交说明写明问题、行为变化和实际验证。契约变更同步对应OpenAPI/Schema、SQL映射及生成类型；正式数据、模型、审批、发布和已有数据库变更需各自有效依据。失败检查返回非零，不删除测试或缩小断言以通过。
