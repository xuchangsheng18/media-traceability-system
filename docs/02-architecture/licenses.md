# 许可、维护与制品边界

2026-10-12；这是工程许可盘点与待办，未代表单位法律审查或生产准入。Python 包声明见 [python-components.json](../00-project/validation/python-components.json)，npm 物料见 [npm-sbom.cdx.json](../00-project/validation/npm-sbom.cdx.json)。安装包元数据并不能证明所有间接依赖或再分发义务已满足。

| 组件 | 上游许可/需要处理的事项 | 本轮处理 |
| --- | --- | --- |
| Python / Miniforge | Python PSF；Miniforge 安装器 BSD-3-Clause；具体库另有许可 | 保存 Conda explicit、精确包锁和包声明，不将安装器许可套给所有包 |
| FastAPI / Vue / Vite / TypeScript 等 | 以锁定包声明及上游 LICENSE 为准，常见 MIT/Apache | 保存元数据；正式制品须打包 notices 和对应许可文本 |
| PostgreSQL | PostgreSQL License | 使用固定16镜像；镜像内 OS/库另行核验 |
| RabbitMQ | MPL-2.0，间接依赖另计 | 版本固定；当前单节点验证不等于长期支持采购 |
| SeaweedFS | Apache-2.0，见4.48标签 LICENSE | 固定版本/摘要；对象锁与许可证审批分开 |
| PyTorch CPU | PyTorch 主项目 BSD 风格，依赖许可证见发行包 | 固定CPU权重生成链；未加载外部业务权重，不借用其他模型许可证 |
| FFmpeg 二进制 | 本轮7.0.2-static含 --enable-gpl、--enable-version3 及 libx264 等编译选项 | 仅内部研发验证；正式再分发需匹配二进制的源码、构建选项、许可证及 notices；不能写成“全栈仅 MIT/Apache” |
| Docker Desktop | Docker Subscription Service Agreement；政府实体使用要求付费订阅 | 当前主机已有 Desktop；组织订阅未提供，保留核验项；生产可评估 Linux Engine，未替换现有服务 |
| 自建训练数据/权重 | 64条随机张量及本轮生成权重 | 未混入第三方训练样本；业务模型须另列权重来源与授权 |

FFmpeg 许可依实际编译选项变化，依据 [FFmpeg 官方说明](https://ffmpeg.org/legal.html)；Desktop 的政府实体条款依据 [Docker 官方说明](https://docs.docker.com/subscription-billing/desktop-license/)。SeaweedFS 标签依据 [4.48 LICENSE](https://github.com/seaweedfs/seaweedfs/blob/4.48/LICENSE)。

Python pip-audit 与 npm audit 已运行；Python 报告跳过 PyPI 不识别的 torch 2.14.1+cpu，不能据“零已知漏洞”声称全部包和 OS 镜像无漏洞。生产补齐容器 OS SBOM/扫描、GPU驱动和模型许可、离线来源核验、软件准入与 Python EOL 迁移。修改许可/分发范围须更新制品清单。
