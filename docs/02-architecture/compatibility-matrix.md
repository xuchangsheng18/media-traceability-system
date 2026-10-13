# 兼容与升级矩阵

实际锁定而非“最新版本承诺”。版本及摘要源见 [versions.yaml](../../config/versions.yaml) 和 [locks](../../config/locks/)。

| 组合 | 本轮版本 | 验证 | 限制/升级路径 |
| --- | --- | --- | --- |
| Miniforge / Python / Linux | Python 3.10.22；Linux x86_64 | 原环境与全新 venv 安装、pip check、容器实际版本 | 已验证研发组合；生产按[选型标准](architecture-decisions/TB-ADR-002-backend-stack.md)另核验支持、依赖/模型与完整CI。3.10例外未批准 |
| 生产Python主候选 | 3.13分支；精确补丁/发行/OS未选 | 未安装、未运行本项目兼容验证、未批准 | 预计上游支持至2029-10；实施时复核官方维护、实际模型/原生依赖及现场准入后独立锁定 |
| 生产Python兼容备选 | 3.12分支；精确补丁/发行/OS未选 | 未安装、未运行本项目兼容验证、未批准 | 预计上游支持至2028-10；选择需实际兼容结果和维护期/升级责任；旧py310锁不可直接复用 |
| FastAPI / Pydantic / SQLAlchemy | 0.143.0 / 2.14.1 / 2.0.54 | API、配置、鉴权、错误、任务接口 | 保持 Python 版本约束；Starlette 测试客户端有 httpx 迁移提示，当前检查通过 |
| psycopg / PostgreSQL | 3.3.6 / 16.15 | SQL、事务、scope FK、独立角色 | PoC 迁移与 62 表业务提案分别验证；不把初始化当升级 |
| Celery / Kombu / RabbitMQ | 5.6.3 / 5.6.2 / 4.3.6 | 真队列、确认、outbox、中断和租约恢复 | 禁用远控/mingle/gossip；事件队列 exclusive；不开启已弃用的非独占临时队列兼容开关 |
| boto3 / SeaweedFS | 1.43.111 / 4.48 | 创建桶、版本开关、原件与向量按版本读写、重启恢复 | 开发 8 卷/128 MiB；WORM、跨节点恢复未验证 |
| PyTorch / NumPy / CPU | 2.14.1+cpu / 2.2.6 | 训练、8 维推理、Schema；真实执行 mock=false | NumPy 2.2.6 为当前 py310 可安装组合；没有 CUDA/GPU 或业务准确率结论 |
| Node / Vite / Vue / TS | 22.21.1 / 8.3.4 / 3.5.43 / 5.9.3 | npm ci、类型、单元、生产构建、Chromium | Node 满足 Vite 对 22.12+ 的要求；镜像和宿主使用同一 Node 版本 |
| Playwright / Chromium | Playwright 1.64.0；匹配其下载版本 | 浏览器端到端 | 浏览器缓存位于仓库外；必须用锁定 Playwright 下载兼容浏览器 |
| imageio-ffmpeg / FFmpeg | 0.6.0 / 7.0.2-static | 1 秒、10 帧合成视频实际编码解码 | 当前二进制含 GPL 配置；分发前核验相应源码及许可义务 |

第三方 Python 依赖精确到全部100个包；npm 锁含传递依赖及 integrity；基础镜像按 digest；自建镜像记录 image_id；打包环境和权重记录摘要。没有宣称二进制位级可重现、完整离线供应链或全部 OS 包漏洞扫描已完成。

外部支持依据见 [官方来源](stage-two-official-sources.md)。升版应创建新 ADR，重新生成类型、运行完整 CI 和故障恢复，并保留旧摘要与报告。

候选顺序及维护月份是截至2026-10-13的选型信息，依据[官方版本表](https://devguide.python.org/versions/)，不证明100包、OCR/ASR/真实模型或GPU组合已经兼容。选型标准与3.10生产例外维护在TB-ADR-002；实际验证记录保持待填，正式选定后的新ADR须引用原研发决定。
