# 许可、维护与制品边界

[N01第八轮内部研发材料与未来分发条件](../03-development/native-n01-internal-semantic-license-review.md)及[实际声明附录](third-party-notices/native-n01-round8-font-theme-notices.txt)；当前不制作正式外发运行包，软件准入未批准。

[N01第七轮材料装配与未决义务](../03-development/native-n01-generated-source-and-distribution-kit.md)；来源/字节核验不代替正式软件准入。

[N01第六轮义务登记](../03-development/native-n01-generation-and-distribution-review.md)及[实际vendor声明](third-party-notices/native-n01-vendor-upstream-notices.txt)；审查材料不代表准入批准。

[N01第五轮捆绑许可与来源复核](../03-development/native-n01-bundled-origin-review.md)及[Swagger上游声明附录](third-party-notices/native-n01-swagger-ui-upstream-notices.txt)提供精确材料；它们不是全部第三方软件准入或正式发行许可决定。

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

## 2026-10-13物料补充

新增[实际OS镜像物料](../00-project/validation/image-sbom.spdx.json)和[采集报告](../00-project/validation/stage-two-software-report.json)，当前7服务/5镜像含449项物料；不代表所有未托管二进制/许可证或漏洞扫描完备。旧web运行镜像目录缺失已登记，不能直接当离线镜像包齐备。

## 2026年10月14日Torch来源核查

[开发基础审查](../00-project/validation/stage-three-foundation-audit-report.json)记录官方CPU wheel及安装载荷核验。官方索引列出torch2.14.1+cpu、cp310、manylinux_2_28_x86_64发行包；下载SHA-256匹配官方索引，已安装12,240个有摘要的载荷文件匹配该包RECORD。安装包只在仓库外下载、读取，没有安装或执行，也没有改变原100包锁。

OSV按精确版本2.14.1+cpu及基础版本2.14.1分别查询，当前均未返回漏洞条目；原pip-audit跳过继续保留。此结果证明指定来源载荷与已安装文件匹配、以及查询时点的版本级已知条目情况，不证明随包OS/所有第三方二进制、模型或许可证完成准入。查询方法依据[OSV官方接口](https://google.github.io/osv.dev/quickstart/)，实际官方包链接与摘要见机器报告。

## 本批前端新增物料

以下读取实际安装包package.json的license字段，并由frontend/package-lock.json锁定版本与完整性摘要；是物料登记，不替代组织准入或完整传递依赖审核。原Python100包锁未变。

| 包 | 精确版本 | 发行包license字段 |
| --- | --- | --- |
| vue-router | 4.6.4 | MIT |
| eslint | 10.12.0 | MIT |
| @eslint/js | 10.0.1 | MIT |
| eslint-plugin-vue | 10.11.1 | MIT |
| typescript-eslint | 8.71.2 | MIT |
| vue-eslint-parser | 10.4.1 | MIT |
| prettier | 3.9.10 | MIT |
| eslint-config-prettier | 10.1.8 | MIT |

补充Node类型开发物料：@types/node 22.20.5，发行包license字段MIT；完整传递依赖仍以锁及扫描为准。

当前N01十类软件准入、候选精确摘要及内部字体/Flatbuffers补充见[第九轮复核](../03-development/native-n01-candidate-adoption-review.md)；三项候选仅获原生研发制品预选确认，无安装或整体准入批准。
