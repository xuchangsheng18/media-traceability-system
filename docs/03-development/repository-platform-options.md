# 仓库平台选择与实际执行依据

2026-10-13；第三阶段研发实施候选，正式批准/冻结未完成。

用户已指定并授权同步现有私有GitHub仓库`xuchangsheng18/media-traceability-system`，保留实际名称，不按手册示例另建short-video-image-traceability。当前仓库可访问且托管CPU CI已实测；这属于研发执行依据，不是公安生产代码平台准入。

| 比较项 | 现有私有GitHub | 经批准的内网自建GitLab |
| --- | --- | --- |
| 前提与网络 | 当前账号/仓库已建立；需要获准外网连接 | 需内网可用节点、合法软件准入与实际运维人；本次未部署 |
| 账号与权限 | 实际所有者账号已知；其他人员/角色待确定 | 需实际身份源和最小权限开通，不能只提供角色模板 |
| 评审与分支保护 | 当前主分支保护未证实生效，私有功能受套餐/权限影响 | 按部署版本/许可核实保护分支、审批与所有者能力 |
| CI与Runner | 当前GitHub托管Ubuntu CPU运行已验证；无需GPU | 需内网CPU/Docker Runner资源、标签/网络/并发与管理员配置 |
| 制品、模型与大文件 | Git只保存代码、契约和小型自建夹具；实际权重/素材置于批准外部存储 | 同样不能把Git当素材库；镜像/制品/模型仓库及备份另规划 |
| 离线、审计与恢复 | 完全离线目标需另交付批准依赖/镜像缓存；私有可见性不代表业务安全准入 | 可控制内网访问；身份/审计/备份仍需真实配置和演练 |
| 许可、国产化、成本 | 当前套餐及相关准入未确认，不承诺免费保护功能或价格 | 软件版本、许可、OS准入、运维/容量投入待确认，不编造采购成本 |

研发继续使用用户指定GitHub与现有Monorepo。若生产必须完全内网/离线，应由项目/安全/运维根据实际条件决定是否采用自建GitLab或批准的政务平台；当前不自动迁移、不创建账号、不改变可见性。人员使用项目负责人、技术负责人、仓库管理员及各开发/测试/运维/安全角色，实际姓名均待填写。

官方依据：[GitHub保护分支](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)、[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)、[GitLab Runner](https://docs.gitlab.com/runner/)。这些页面提供功能说明，不能代替本项目账号、许可或实测。
