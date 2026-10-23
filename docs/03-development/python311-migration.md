# Python3.11迁移与CI修复

2026-10-24当前状态：2026-10-24安全续批：main40027591632实际因运行2/质量3条依赖匹配失败；filelock4.2.1、setuptools84.1.0已核验官方制品并完成Linux工程验证，新精确head CI及有效扫描仍待，不计新增完成。 [新依赖与验证范围](python311-security-followup-20261024.md)。下文“仅Pillow/certifi变化”和0匹配属于初次迁移验证时点，本批在其后追加两项实际安全修复。

2026-10-23用户已批准全项目采用合适的Python>=3.11，并修复阻断CI的依赖问题。本次活动目标为Linux x86_64/CPU、Miniforge Python3.11.17；这是研发环境迁移，生产仍为NOT_FROZEN，算法、权重和训练不在本次范围。

新环境位于`/opt/conda/glwy/envs/py311`，100个包名完整保留，仅将Pillow12.3.0升级至13.0.0、certifi2026.7.22升级至2026.10.19。已完成实际安装、`pip check`及精确集合核对。当前新锁扫描100个条目、0条已报告漏洞匹配；Torch CPU包仍不能由PyPI扫描覆盖，这不构成安全或软件准入结论。

已更新项目元数据、统一命令、CI、格式/类型目标、前端环境标识和新Dockerfile；4个ABI相关工具制品已替换为官方cp311 wheel并核对大小及SHA-256。所有原测试、权限/身份断言、安全扫描、失败探针和main的engineering要求保留。完整回归、新head CI、镜像和运行切换按实测逐项记录，不能凭新解释器安装成功登记全部完成。

证据：[授权](../00-project/validation/python311-migration-authorization-20261023.json)、[迁移实测](../00-project/validation/python311-migration-report.json)、[实际制品与241份内嵌通知摘要](../00-project/validation/python311-artifact-inventory.json)、[新锁扫描原始结果](../00-project/validation/python311-runtime-audit.json)、[实施计划](../superpowers/plans/2026-10-23-python311-migration.md)。

活动锁为`config/locks/requirements-py311.lock`和`config/locks/conda-linux-64-py311.explicit.txt`。Conda锁对应实际安装的26个精确build，通过官方conda-forge URL及MD5复建，SHA-256与许可记录另列制品清单；运行依赖与独立质量/类型工具仍分层。包内通知盘点不是嵌套许可使用范围的最终准入，N01仍不能整体标完成。

旧`/opt/conda/glwy/envs/py310`、原requirements/Conda锁及旧Dockerfile保留回退。compose项目/网络/持久卷中的py310名称是已有数据身份，不随解释器升级重命名。当前迁移不执行共享数据库迁移，不因源码同步自动重启共享栈。回退必须同时选回旧解释器、原锁和对应旧镜像/源码，不能把新包安装进旧prefix，也不能向已有库重新初始化。

Linux及GitHub执行Python验证，Windows仅协调和编辑。T034的真实采用、许可、分类和恢复代际事实仍按原条件拒绝缺失输入，不因Python迁移自动创造这些依据。PR #2只有新精确head全部有效必需检查成功才能普通合并；旧head的通过项不能借给本次提交。
