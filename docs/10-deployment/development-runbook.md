# py311最小工程启动与排查

实际Linux目录 `/workspace/glwy/projects/media-traceability-system`；Miniforge `/opt/conda/glwy/envs/py311`。本轮独立开发项目 `media-trace-py310`，仅处理自建素材。凭据由启动工具随机生成并保存仓库外，不复制进代码、日志或聊天。

## 已有环境启动

第三阶段已提供[统一入口与验证](../03-development/stage-three/readiness.md)。当前服务器优先执行`/opt/conda/glwy/envs/py311/bin/python scripts/dev.py status`观察现有7服务；共享Docker数据盘容量问题未整改时不执行重建/恢复。下列低层生命周期命令用于说明工程机制，不能绕过统一入口的容量保护而视作当前安全的直接操作步骤。

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py311/bin/python scripts/verify_runtime_lock.py
/opt/conda/glwy/envs/py311/bin/python scripts/poc_control.py prepare
/opt/conda/glwy/envs/py311/bin/python scripts/poc_control.py pack
/opt/conda/glwy/envs/py311/bin/python scripts/poc_control.py build
/opt/conda/glwy/envs/py311/bin/python scripts/poc_control.py up
/opt/conda/glwy/envs/py311/bin/python scripts/poc_control.py status
```

成功条件：7服务健康；前端页面可见；verify_poc.py输出PASS且模型为cpu、business_model=false、mock=false。up幂等创建专用schema/角色/桶并启用版本；不向任何既有业务数据库执行62表初始化。

## 依赖复建

在新的专用目录创建环境；禁止直接覆盖正在使用的py310。Conda系统库与Python版本按 `config/locks/conda-linux-64-py311.explicit.txt` 创建，再使用该环境Python安装 `config/locks/requirements-py311.lock`。此锁针对Linux x86_64 / CPython3.11.17 / CPU，Windows不可直接套用。PyTorch CPU源已经写进锁文件；pip-freeze-observed里的conda构建机file://路径仅作观测，不是安装入口。

本轮100包锁已在仓库外干净venv安装通过。首次构建需已有基础镜像摘要、Node官方归档或镜像；前端执行npm ci。Node缓存路径为 `/home/glwy/.cache/media-trace-node/node-v22.21.1-linux-x64/bin`。浏览器在此前缀PATH下于frontend目录执行 `PLAYWRIGHT_BROWSERS_PATH=/home/glwy/.cache/media-trace-browsers npx playwright install chromium --only-shell`。真正离线环境仍需另外准备已核验的轮子、Conda包、镜像和浏览器包。

## 访问页面

服务器上打开 `http://127.0.0.1:14180`。本机使用：

```sh
ssh -N -L 14180:127.0.0.1:14180 glwy@172.16.58.179
```

在本机浏览器访问同一地址。研发令牌仅由操作者在服务器终端显式运行 `.../python scripts/poc_control.py token` 取得并填入页面；不要发到聊天或提交Git。页面选择自建PNG/JPEG，点击开始验证，预期任务最终SUCCEEDED并返回8维合成CPU结果。

| 服务 | 宿主回环端口 | 容器端口 |
| --- | --- | --- |
| 页面 | 14180 | 80 |
| API | 14200 | 8000 |
| 推理 | 14201 | 8001 |
| PostgreSQL | 14432 | 5432 |
| RabbitMQ AMQP | 14672 | 5672 |
| S3 | 14833 | 8333 |

网络 `media-trace-py310-development`。卷前缀 `media-trace-py310_`，后缀db-data、queue-data、object-data、model-data、secrets-data。runtime根目录可通过MT_RUNTIME_DIR配置，但CI和浏览器测试当前以本节点目录为基线，变更时同步配置。

## 验证和停止

`python scripts/dev.py ci --allow-stack-changes`是完整研发门禁的受保护入口，内部委托run_ci.py；共享数据卷不足5GiB或不能读到容量时拒绝开始。故障恢复会短暂停止本项目worker/broker并重启本项目API、S3、推理，结束恢复，因此当前共享栈不得跳过入口直接运行完整恢复门禁。GitHub托管独立临时Runner按工作区/runtime/Docker条件适用冷启动例外，单一环境标记不够。`python scripts/poc_control.py down`停止并移除本项目容器/网络，保留数据卷。没有提供默认删除卷命令；复建不得清理其他项目。

## 已遇到的故障

| 现象 | 原因/排查 |
| --- | --- |
| Docker拉取GPG超时 | 工具使用专用无登录CLI配置，只针对公开镜像；不覆盖用户全局认证 |
| workspace绑定挂载被拒 | Desktop未共享该路径；本工程改命名卷/构建上下文，不改变全局共享 |
| Rabbit 541非独占临时队列 | 使用已配置的exclusive事件队列，禁用远控/mingle/gossip；不得开弃用开关掩盖 |
| Erlang调度器创建失败 | 保持ERL_FLAGS与RABBITMQ_CTL_ERL_ARGS限制，勿按128核自动展开 |
| S3无可写卷 | 保持8卷与128MiB设置；实际桶版本化必须Enabled；先看磁盘余量 |
| 重启后页面502 | Nginx使用Docker DNS动态resolve，等待服务与存储就绪，不把API存活等同全部依赖就绪 |
| CI锁漂移 | 明确新增ADR/锁更新和测试；不临时降低门禁 |

虚拟机磁盘观测98%使用，应先落实容量再加入大素材/新索引；没有进行大并发或GPU测试。备份/灾备/生产部署参见原计划，不把本轮“重启持久化”替代备份恢复。

## 1.1运行补充

初始化调用版本迁移和账本，应用5表含审计/账本；升级前先停旧worker/API并留备份。冷恢复会短停本项目服务，见[备份手册](development-backup-restore.md)。GitHub一次性Engine通过MT_DOCKER_CONTEXT=default、MT_RUNTIME_DIR复用同一入口，无需服务器私有凭据。
