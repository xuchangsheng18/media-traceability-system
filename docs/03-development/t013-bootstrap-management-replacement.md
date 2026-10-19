# T013 bootstrap管理工具替代与退役准备

本批承接已批准的[身份设计](t013-keycloak-identity-design.md)与[8步计划](t013-keycloak-implementation-plan.md)第5、8步，按2026-10-19用户明确要求补齐管理调用及退役准备。适用当前Linux／py310／CPU研发；Python候选继续暂缓。真实结果见[本批报告](../00-project/validation/t013-bootstrap-management-report.json)和[精确提交CI](../00-project/validation/t013-bootstrap-management-ci-report.json)。本文不代表共享配置已采用、实际管理员已接管或软件准入已通过。

## 管理调用如何替代

| 位置 | 本批作用 | 边界 |
| --- | --- | --- |
| `scripts/identity/management_config.py` | 建立专用公开客户端`media-trace-admin-tools`，绑定专用必需密码／OTP流程 | 只创建专用流程，不改变master默认浏览器流程；已有不一致对象拒绝覆盖；共享采用需显式操作 |
| `scripts/identity/management.py` | 临时回环授权码入口、PKCE S256、state／nonce／issuer核验及管理会话 | 本人在可信浏览器输入口令和OTP；工具不收集它们、不持久化refresh token；回调不记录查询串 |
| `tools/identity_admin_tokens.mjs` | 使用已锁定Node及内建crypto验证RS256、用途、客户端、有效期和签名`amr` | 复用既有ID token签名／nonce校验；不新增Python或npm包，不把解析JWT当认证 |
| `scripts/identity/provision.py` | `AdminClient(session_file=...)`或环境变量`MT_IDENTITY_ADMIN_SESSION`显式选择本人会话 | 环境变量仅放私密文件路径；选定会话失败直接拒绝，绝不回退bootstrap |
| `scripts/identity/retirement.py` | 从当前私密配置生成独立退役候选、摘要清单和禁止重建bootstrap标记 | 保留数据库凭据及原文件；不删除客户端、不替换共享文件、不安装卷或重启服务 |
| `scripts/identity/control.py` | 已移除bootstrap字段的配置继续可准备；退役标记下缺凭据时拒绝重建 | 初次空环境仍可显式初始化；不能在已退役环境悄悄重新生成bootstrap |

管理访问令牌最长300秒，与既有研发设计一致；不允许密码grant、隐式流、设备grant、服务账号和offline scope。新专用客户端不返回refresh token。JWT必须包含正确master issuer、专用audience／azp及签名`pwd`和`otp`引用，且签名和时间检查通过；会话文件还绑定本次指定登录名与subject。每次管理请求重新核对服务端会话、用户启用状态、待办动作、OTP凭据、管理角色及master保护，不使用业务角色或案件授权兜底。

本人会话是Git外0700目录下的0600文件，仅保存短期access token和绑定元信息。过期、服务不可用、TLS错误、失效会话、用户禁用或角色撤销均拒绝；需要本人重新登录。关闭客户端连接不等于Keycloak会话已撤销，删除本地文件也不等于服务端退出。master管理角色不会生成内部用户、单位、案件或来源授权。

`sid`按[OpenID定义](https://openid.net/specs/openid-connect-backchannel-1_0.html#OPSupport)作为不透明字符串处理，本工具限制为1—256个可打印ASCII字符，拒绝控制字符及非字符串；不能要求它是UUID。当前自建服务的实际会话ID为24字符，已保留格式误判的失败证据及回归。内部用户`subject`仍按当前Keycloak本地用户UUID核对，二者不能混用。

`AdminClient()`原调用签名保持兼容，因此初始化器、管理员交接CLI和常规验收夹具可在显式选择会话后复用管理调用。未选择时的旧bootstrap仅保留初次设置用途；退役标记或移除的secret会阻止默认bootstrap路径。临时`RecoveryLab`及托管CI使用其自建bootstrap完成独立夹具初始化，这属于测试资源生命周期，不是共享环境的长期管理身份。Git外历史操作脚本同样须通过显式会话路径调用，不能仅凭源码更新宣称它们已经切换。

## 实际验证及未完成状态

先运行新增回调、签名、选择失败和候选文件测试，保留实际失败，再实现及复测。真实演练使用独立三服务、端口／网络／数据卷和`synthetic-admin-*`账号；核验真实MFA授权码交换、弱化配置拒绝、撤销、删除bootstrap后既有初始化器操作及重启、管理员禁用拒绝。它不创建`xuchangsheng`真实账号，也不代替徐昌胜本人改密、设备绑定和复核。

当前数量、失败过程和通过范围以本批报告及CI为准；不同测试集重叠，不把相加数量当170任务完成数。正式的历史配置／备份中的secret退役和实际新卷采用仍需完成，不因数据库客户端删除或演练成功就认为整个退役过程结束。

### CI的固定摘要与下载路径

源码提交`431f337`的CI运行`39217811049`前两次尝试均在PostgreSQL镜像拉取阶段失败，测试未执行；engineering依赖门禁据此拒绝继续。锁定引用使用镜像代理，而同一PostgreSQL摘要在官方仓库返回200。本批对托管临时VM的下载路径作修复，不把这些失败登记为功能测试通过。

`scripts/identity/ci.py`只允许PostgreSQL和Nginx转到锁文件已经列明的`docker.io/library`官方源，保留同一个`sha256`。拉取后核对内容ID格式及实际仓库摘要，通过[BuildKit固定来源策略](https://docs.docker.com/build/building/variables/#experimental_buildkit_source_policy)使构建解析到官方同摘要。策略及仅覆盖网关镜像引用的Compose文件留在临时VM的私密目录，原Dockerfile、Compose及四份原版本锁保持不变。Keycloak仍使用原Quay固定摘要，启动仍禁止重新拉取。

CI进程显式选择`official-pinned-v1`时，必须同时满足托管环境标识、精确仓库和工作目录、本人所有的临时目录及本次运行的归属标记；未知配置或普通机器拒绝。运行用镜像与构建使用同一官方摘要，避免依赖不同Docker引擎的仓库别名解析行为。读取临时Compose覆盖文件时核对所有者、权限及完整预期字节，不接受任意镜像、附加服务或其他配置。默认未选择该配置时，Linux共享环境仍返回原镜像引用，不读取临时覆盖文件。

独立缓存探针验证了本机的同摘要解析及来源策略构建；随后源码`4377b13`的托管运行`39220993572`在缓存引用观察阶段失败，说明不能将本机别名行为直接当作托管环境证明。本批改用上述显式运行覆盖，保留13项针对性测试的失败再通过记录，覆盖未知源、未锁定摘要、摘要不一致、重复文件、默认引用不变及配置/归属/覆盖异常拒绝。最终托管结果以本批CI报告为准，不能用本地探针替代它。

## 本人操作顺序

先在Linux交互终端准备本次命令环境，沿用已锁定的解释器及Node：

```sh
cd /workspace/glwy/projects/media-traceability-system
export PYTHONPATH=/workspace/glwy/projects/media-traceability-system/backend:/workspace/glwy/projects/media-traceability-system
export PATH=/home/glwy/.cache/media-trace-node/node-v22.21.1-linux-x64/bin:$PATH
```

1. 按[身份运维手册](../10-deployment/keycloak-identity-runbook.md)核对CA／SSH入口，由徐昌胜建立master保护，创建已登记的`xuchangsheng`账号并首次改密、绑定本人MFA；这些实际操作尚未完成。
2. 在Linux交互终端执行以下预览及显式配置命令。缺master密码、暴破及管理事件保护会拒绝；不覆盖已有不一致配置。工具先保持新客户端禁用，显式清空创建时推导的浏览器跨域来源，启用时再次指定空来源，再完整读回核对；配置或传输失败会尝试禁用已确认的新客户端并读回，无法确认时报告状态不确定，要求人工核查。

```sh
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.management setup
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.management setup --apply
```
3. Windows保持SSH隧道，同时转发管理口和临时回调口：

```text
ssh -N -L 127.0.0.1:18444:127.0.0.1:18444 -L 127.0.0.1:18765:127.0.0.1:18765 glwy@172.16.58.179
```

4. Linux运行下列命令；把终端显示的授权地址放入本人已信任项目CA的浏览器，在Keycloak页面输入密码和OTP。短期回调收到后自动关闭，不保存查询串或口令。

```text
cd /workspace/glwy/projects/media-traceability-system
export PYTHONPATH=/workspace/glwy/projects/media-traceability-system/backend:/workspace/glwy/projects/media-traceability-system
export PATH=/home/glwy/.cache/media-trace-node/node-v22.21.1-linux-x64/bin:$PATH
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.management login --apply --username xuchangsheng
```

5. 将返回的`session_file`真实路径作为下列参数；不要粘贴token。`inspect`只读核对；环境变量方式供现有管理CLI复用。文件过期需重新登录。

```text
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.management inspect --session-file ACTUAL_PRIVATE_SESSION_PATH
export MT_IDENTITY_ADMIN_SESSION=ACTUAL_PRIVATE_SESSION_PATH
```

6. 完成实际GPG公钥／独立私钥保管、可恢复备份、维护安排和制品／配置采用复核后，重新核对候选摘要与当前来源。采用新私密卷、移除bootstrap客户端及验证旧token／secret、重启和历史值保管为后续明确动作，本批不执行。不要在替代入口和恢复条件未满足时先删除共享bootstrap。

## 退役候选的生成与使用边界

`python -m scripts.identity.retirement`默认预览；`--apply --output`只允许运行根目录同级`identity-retirement`的新子目录。包含去除bootstrap的`credentials.json`／`keycloak-v2.conf`、禁止自动重建标记和候选摘要。文件包含保留的数据库私密值，必须留Git外，不能同步到GitHub或发到对话。

候选标记中的`bootstrap_retirement_verified=false`明确表示未核实实际退役；它的作用是阻止旧初始化路径重建身份，不是验收证明。候选生成过程的`bootstrap_deleted=false`表示工具未执行删除，不能据此推断独立测试环境内对象是否存在。部分失败目录不得直接复用；先核查实际文件及manifest，再另建新目录。

配置键两侧空格会先规范后检查；发现重复或不一致bootstrap项、其他字段仍含旧secret时拒绝生成，要求人工审查来源。不会通过删除其他字段来掩盖残留。当前共享配置的候选生成结果及原文件不变检查以本批报告为准。

依据：[Keycloak授权码流程](https://www.keycloak.org/securing-apps/oidc-layers)、[26.8.1 AMR映射实现](https://github.com/keycloak/keycloak/blob/26.8.1/services/src/main/java/org/keycloak/protocol/oidc/mappers/AmrProtocolMapper.java)、[AMR执行引用有效期](https://github.com/keycloak/keycloak/blob/26.8.1/services/src/main/java/org/keycloak/protocol/oidc/utils/AmrUtils.java)。这些协议依据不替代项目的软件准入或正式安全验收。
