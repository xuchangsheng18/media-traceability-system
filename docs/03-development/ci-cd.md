# 持续集成与实际执行范围

统一入口为 [run_ci.py](../../scripts/run_ci.py)。当前已在连接的Linux主机本地shell真实运行；[.gitlab-ci.yml](../../.gitlab-ci.yml)配置同一脚本，未虚构远程GitLab项目、Runner注册或托管流水线成功。

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py310/bin/python scripts/run_ci.py all
/opt/conda/glwy/envs/py310/bin/python scripts/verify_ci_failure_gate.py
/opt/conda/glwy/envs/py310/bin/python scripts/check_repository_secrets.py
```

| 阶段 | 门禁 |
| --- | --- |
| validate | pip check、精确环境锁、Ruff、后端7项、输入/契约、npm ci、生成类型无漂移、npm audit |
| build | 后端wheel、核验或打包真实py310、按摘要构建API/推理/worker共用镜像与Web镜像；Web镜像内执行单元、TS与构建 |
| integration | 启动专用开发栈；独立临时数据库SQL；真实15项链路；5项故障恢复；6项媒体/查询；Chromium端到端 |

任一门禁非零立即停止。主动失败探针只写独立报告，不覆盖完整PASS报告，不进行构建/部署。脚本仅在本开发栈停止或重启服务；GitLab integration用resource_group避免同项目并发操作。报告保留每条命令、状态、耗时和开始/结束时间。

Runner前提：该py310及已锁依赖；Node22.21.1；Docker desktop-linux权限；基础镜像；Playwright1.64.0匹配浏览器；仓库外私有runtime配置与开发节点资源。浏览器首次安装详见运行手册。干净checkout不包含环境tar，build自动根据锁核验原环境并打包；不假设Git里存有几百MB环境。

当前固定同一开发主机、项目名及端口，不能让来自其他项目或不可信分支的任务使用这些凭据。正式CI接入需配置实际托管地址、受信Runner、保护变量/分支、制品仓库、隔离环境与清理策略，随后留存平台流水线ID和真实成功记录。未配置发布/生产自动部署。
