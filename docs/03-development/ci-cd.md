# 持续集成与实际执行范围

统一入口为[run_ci.py](../../scripts/run_ci.py)。服务器本机完整21道门禁已通过。用户提供的实际私有GitHub仓库为[media-traceability-system](https://github.com/xuchangsheng18/media-traceability-system)，使用[ci.yml](../../.github/workflows/ci.yml)接入GitHub Actions；平台实际运行ID、源码SHA、结论和制品验真见[github-actions-report.json](../00-project/validation/github-actions-report.json)，不得将配置文件存在写成执行成功。原.gitlab-ci.yml保留为同源Runner参考，当前平台选择GitHub。

| 阶段 | 门禁与适用范围 |
| --- | --- |
| validate（9） | pip check、100包锁、Ruff、后端15项、输入资料10项、数据库契约17项、npm ci、3份类型无漂移、npm audit |
| build（3） | 后端wheel、核验/打包实际py310、构建API/推理/worker共用镜像及Web镜像；Web构建含2单元、TS及产物 |
| integration（9） | 启动7服务；隔离73SQL案例；迁移/竞态15项；21链路项；5恢复项；6媒体/查询；源PTS抽帧；冷备恢复8项；Chromium端到端1项 |

任一门禁非零立即停止。失败探针返回预期非零、独立报告，验证阻断后续构建/部署；不覆盖完整PASS报告。报告逐命令保存耗时与结果。冷备门禁在本项目维护时段短暂停服务，正式生产环境不直接执行本脚本。

## 两种执行环境

服务器沿用用户指定/opt/conda/glwy/envs/py310（Python3.10.22）及desktop-linux；Node22.21.1和匹配Playwright浏览器在私有缓存，runtime在仓库外。MT_DOCKER_CONTEXT可覆盖；独立Engine可使用default或DOCKER_HOST。

GitHub采用一次性ubuntu-24.04托管Runner，从固定Miniforge安装包URL/SHA-256、conda显式锁及pip精确锁复建同一路径py310，再安装锁定Node/UI/browser、使用Docker Engine。CI临时环境不是原Linux服务器虚拟机，不需要该服务器凭据或内网访问。安装包及Actions提交摘要在config/ci-bootstrap-lock.json和工作流中；checkout不持久化Git凭据。contents仅read，不配置生产发布令牌。

push main、PR或手动触发；并发按ref取消旧任务，同一栈仅在单个一次性Runner执行。始终上传非秘密JSON报告/清空令牌的截图，保留14天，并停止临时服务。仅验证记录、同步回执及文件清单的push不触发，以免归档运行证据形成循环；代码或设计文档变更仍触发。private状态、仓库写权限和Actions启用已通过API实查；实际运行是否成功只认报告与平台run。

## 本机入口与限制

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/run_ci.py all
/opt/conda/glwy/envs/py310/bin/python scripts/verify_ci_failure_gate.py
/opt/conda/glwy/envs/py310/bin/python scripts/check_repository_secrets.py
```

未配置自动发布或生产部署。分支保护/必须检查仍须结合账号套餐、组织管理与有效责任人设置，不能把21门禁等同生产审批。GitHub额度/网络/虚拟机资源变化按实际失败处理，不降低断言。遵循[Runner环境](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)及[Actions安全配置](https://docs.github.com/en/actions/reference/security/secure-use)官方说明，实际以本次制品和运行结果为准。
