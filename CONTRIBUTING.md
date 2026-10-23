# 研发贡献与验证

当前按2026-10-23授权使用Miniforge Python3.11.17 CPU研发组合；正式环境基线与人员权限待确认。完整范围、唯一接口/Schema来源与数据约束见[AGENTS.md](AGENTS.md)，第三阶段[16步状态](docs/03-development/stage-three/readiness.md)给出实际证据和缺项。

从对应T任务卡核验输入、执行依赖、契约、权限及验收，再修改具体代码。候选治理流程为功能分支和评审后合并，实际评审人数、管理员及分支保护尚未生效证明；本次用户明确要求GitHub/服务器同步，不能把该授权推广为任意发布或账号操作。

Linux在仓库根目录使用`/opt/conda/glwy/envs/py311/bin/python scripts/dev.py <命令>`，命令包括help、setup、lint、format-check、type-check、test、contract-test与security-scan。当前服务器make未安装，Makefile只是已有make环境的等价别名，不将其记录为本机已运行成功。Windows默认用`& .\scripts\dev.ps1 help`和`& .\scripts\dev.ps1 status`协调同一Linux仓库；`-Target local`要求另外准备本机3.11.17锁定环境，本次不声称已验证Windows原生安装。

`dev`默认只观察既有7服务；显式`--allow-stack-changes`才启动命名研发栈，且会检查数据库文件系统容量。`build/integration-test/ci`在所有环境均要求该标志；共享服务器容量不足或读不到容量即拒绝执行。冷启动例外仅适用于GitHub托管Runner、与仓库匹配的工作区、Runner临时目录内独立runtime、default Docker上下文且无DOCKER_HOST覆盖的组合；只有GITHUB_ACTIONS标记或自托管Runner仍走共享容量检查。这是操作保护，不代表平台授权或网络隔离。CI使用`python scripts/dev.py ci --allow-stack-changes`执行实际门禁。`stop`不删除卷，`clean`默认仅预览两个精确缓存目录，`--apply`才清理，原件、数据、权重、数据库、运行秘密和Git均不在允许清理范围。

Python格式/静态检查范围以config/stage-three-profile.json为准，独立类型工具不修改原100包运行锁；前端ESLint、Prettier、vue-tsc和真实违规探针均纳入统一入口和托管CI。Ruff负责Python，Prettier负责前端格式，eslint-config-prettier仅关闭与其冲突的格式规则，Vue/TS语义检查保留。实际数量读取本批报告，不沿用旧20/22/52记录。前端`npm --prefix frontend run lint`、`format-check`、`type-check`、`test`和`test:foundation-browser`可分别执行，`node scripts/verify-frontend-quality.mjs`检查违规会被拦截。API与配置说明见[本批实现记录](docs/03-development/stage-three/foundation-closeout-implementation.md)。

`setup --tools`在Git外建立锁定的pre-commit及Python类型工具环境，不修改活动py311运行依赖。选定Linux仓库可显式执行`python scripts/stage_three_quality.py install-hook`，遇到自定义hook或core.hooksPath会拒绝覆盖；随后运行该仓库实际`.git/hooks/pre-commit`或独立工具的`pre_commit run --all-files`核验。安装结果以钩子报告为准；其他开发者端和Windows原生不自动安装。钩子不是分支保护，平台必需检查仍需管理员落实。统一pre-commit入口含秘密、Ruff、格式和Python/前端类型检查，不修改运行依赖。提交钩子只关闭报告写入，仍运行所有检查并保留失败退出码；独立验证及CI正常保存报告。

若网络较慢，可把工具锁中12个包按制品清单核验SHA-256后放到仓库外的`stage-three-quality-wheelhouse`；安装会使用该缓存并继续强制包摘要。也可通过`MT_QUALITY_WHEELHOUSE`指定获准外部缓存。缓存/安装包不提交Git，镜像源凭据由操作者私下提供。

提交说明写明问题、行为变化和实际验证。契约变更同步对应OpenAPI/Schema、SQL映射及生成类型；正式数据、模型、审批、发布和已有数据库变更需各自有效依据。失败检查返回非零，不删除测试或缩小断言以通过。
