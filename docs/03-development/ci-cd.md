# 持续集成与实际执行范围

第三阶段由[dev.py](../../scripts/dev.py)提供统一入口，ci命令委托原run_ci.py的25门禁，不改计数。工作流另外核验第三阶段10项来源/配置、13项实际运行、25例Python单元（15原PoC+10新增入口）、2例前端单元及三服务模拟夹具9项/1例浏览器；这些是独立范围，不能当成额外业务任务完成。

开发命令、独立pre-commit工具层及Python/npm扫描见[第三阶段验证报告](development-environment-validation-report.md)。扫描不把被跳过CPU Torch发行包记为安全通过。服务器make未安装，实际使用Python入口；共享Docker数据盘不足时统一入口拒绝构建/恢复，完整复建仍在独立托管Runner进行。

统一入口为[run_ci.py](../../scripts/run_ci.py)，当前共25道工程门禁；服务器本机21道完整门禁记录属于原1.1历史范围。用户提供的实际私有GitHub仓库为[media-traceability-system](https://github.com/xuchangsheng18/media-traceability-system)，使用[ci.yml](../../.github/workflows/ci.yml)接入GitHub Actions；当前25道的托管实际运行ID、源码SHA、结论和制品验真见[github-actions-report.json](../00-project/validation/github-actions-report.json)，不得将配置文件存在写成执行成功。原.gitlab-ci.yml保留为同源Runner参考，当前平台选择GitHub。

| 阶段 | 门禁与适用范围 |
| --- | --- |
| validate（10） | pip check、100包锁、Ruff、后端15项、第二阶段运维/交付控制6组、输入资料10项、数据库契约17项、npm ci、4份类型无漂移、npm audit |
| build（3） | 后端wheel、核验/打包实际py310、构建API/推理/worker共用镜像及Web镜像；Web构建含2单元、TS及产物 |
| integration（12） | 启动7服务；隔离73SQL案例；迁移/竞态15项；21链路项；5恢复项；6媒体/查询；源PTS抽帧；冷备恢复8项；隔离RLS/中文词项21项；VFR媒体11项；镜像OS物料采集；Chromium端到端1项 |

工作流另外执行阶段材料、接口明细及导航校验，并保存失败探针的预期阻断证据；这些步骤不另加到run_ci.py的25条命令计数。各门禁可能包含多项断言，门禁数、断言数和170业务任务数不能混用。

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

未配置自动发布或生产部署。分支保护/必须检查仍须结合账号套餐、组织管理与有效责任人设置，不能把工程门禁等同生产审批。GitHub额度/网络/虚拟机资源变化按实际失败处理，不降低断言。遵循[Runner环境](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)及[Actions安全配置](https://docs.github.com/en/actions/reference/security/secure-use)官方说明，实际以本次制品和运行结果为准。

材料控制、隔离、媒体报告与SPDX清单分别保存。正式资源容量报告CRITICAL不冒充工程测试失败或生产就绪，功能/生产条件仍按第二阶段清单。服务器研发数据卷处于CRITICAL时不执行本机全量构建/恢复；先落实容量。托管25道在一次性隔离Runner执行，不借用该服务器已有业务数据或凭据。
