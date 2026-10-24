# Python3.11依赖安全修复续批（2026-10-24）

PR #2在b5精确提交的两路全部门禁通过后正常合并，main为3762949e。合并后的新运行40027591632中身份与基础业务成功，工程执行及汇总失败；实际阻断来自原安全扫描的运行依赖2条、独立质量层3条匹配。此前通过结果仍是各自验证时点的事实，本轮失败不删除、不用历史通过覆盖。

沿用2026-10-23全项目Python/依赖迁移和修复授权，活动Python保持3.11.17、100包名保持，仅将filelock3.32.3改为4.2.1、setuptools84.0.0改为84.1.0；独立质量层filelock4.1.0改为4.2.1，后端构建钉死版本同步。原py310锁、解释器、旧py311归档和本轮修改前的锁均保留回退；不修改公共契约、数据库、算法或CI阈值。

官方依据：[filelock安全公告](https://github.com/tox-dev/filelock/security/advisories/GHSA-v4x8-3wr5-3wq8)、[setuptools安全公告](https://github.com/pypa/setuptools/security/advisories/GHSA-xmj3-9gf7-h52w)、[filelock4.2.1发布元数据](https://pypi.org/pypi/filelock/4.2.1/json)、[setuptools84.1.0发布元数据](https://pypi.org/pypi/setuptools/84.1.0/json)。两项wheel和一项Conda build已逐一核对发布者大小与SHA-256；filelock要求Python>=3.11，setuptools wheel要求>=3.10，选定Conda build要求>=3.11，均适配3.11.17。内嵌通知已更新，通知存在不等于N01正式许可准入。

先在仓库外独立prefix验证100包闭合、pip check、两个真实进程的锁排斥及释放、Torch checkpoint读写、NumPy/Pillow PNG往返。后端初次构建明确因旧setuptools固定版本失败，精确对齐后wheel/sdist通过。核验并保留旧归档后，项目py311已修补并再次核对100包；独立12包工具按原require-hashes安装通过。共享Docker服务及既有API进程未重启，不声称其已加载新依赖。

最终原工程组2095项通过，0失败/错误/跳过；原收集20错误及候选前置未齐时23失败/2072通过均单独保留。前者补齐原PYTHONPATH，后者补齐原Node/类型工具目录并满足实际prefix和新制品清单约束；没有删测试、增加skip或降低断言。新运行归档已按原打包入口产生，原归档未覆盖。

Linux标准安全扫描因对外网络不可达尚未取得有效新鲜回执，不能写0漏洞或安全门禁已通过；初次缺npm路径的诊断也保留，随后按原Node路径重试。精确新head托管CI仍待推送核验，main仍保留3762949e，其他PR不自动合并。算法仍暂缓，T034真实采用/许可/分类和代际事实仍须真实提供方，不能由本批依赖修复替代。

详见[精确限定回执](../00-project/validation/python311-security-followup-20261024.json)及[原迁移说明](python311-migration.md)。本批完成数不增加，不关闭T117或其他整任务；全部170项原任务和剩余条件保留。
