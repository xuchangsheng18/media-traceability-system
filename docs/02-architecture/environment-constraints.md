# 环境约束与适用范围

2026-10-12；研发配置 `miniforge-py310-linux-x86_64-cpu`。本轮由用户指定已有 py310 环境，替代源设计中的 Python 3.11 候选；原 Word 与源任务目标文字保留，实际执行差异在本基线登记。

| 项目 | 已核验事实 | 工程处理 |
| --- | --- | --- |
| 运行节点 | Linux 172.16.58.179，账户 glwy，Ubuntu 24.04，x86_64 | 仓库位于 `/workspace/glwy/projects/media-traceability-system` |
| Miniforge | 基础目录 `/opt/apps/miniforge3`；py310 位于 `/opt/conda/glwy/envs/py310` | 所有工程命令明确使用该环境的 Python 3.10.22 |
| 容器解释器 | 实际 py310 打包到 `/opt/py310` | API、worker、推理全部使用 `/opt/py310/bin/python`；镜像基础层的 Python 3.12 不作为应用解释器 |
| 容器引擎 | Docker Desktop 的 desktop-linux 上下文，服务端 29.8.2 | 与宿主机分别核算资源；不修改其他项目或全局引擎配置 |
| 挂载 | 当前 Desktop 不共享 `/workspace` | 使用构建上下文、命名卷和标准输入注入配置，不依赖宿主路径绑定挂载 |
| 网络 | 本轮能够取得官方包与镜像；专用 bridge 网络，发布端口仅绑定 127.0.0.1 | 开发网络允许容器出站；没有声称生产内网隔离、断网或跨网审批已验证 |
| GPU | 未核验可用 GPU、驱动与 CUDA | 锁定 CPU PyTorch；GPU 单列待验证 |
| 输入 | 自建无敏感图片、视频及随机训练张量 | 不接入真实案件、互联网采集或生产平台 |
| Python 维护 | 3.10 已于 2026-10-01 结束支持 | py310 是用户要求的研发验证配置；正式生产前需迁移到受支持版本并重跑兼容门禁 |

Python 维护状态依据 [Python 官方版本表](https://devguide.python.org/versions/)。本轮实际事实见 [environment-inventory.json](../00-project/validation/environment-inventory.json)，快照不是长期资源承诺。

公安现场软件准入、国产化、统一认证、离线部署、GPU、等保、保存期限及生产部署节点仍沿用 Q-01—Q-20 等未决记录。当前开发选择不能自动关闭这些生产问题。
