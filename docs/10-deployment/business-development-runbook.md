# 业务前后端开发启动与当前边界

本入口用于Linux／现有Miniforge py310／CPU内部研发。原上传验证页与七服务保留；新增业务控制台复用同一Vue工程，业务API单独运行。Python候选暂缓，不安装新Python或替换原100包锁。

## 本轮Linux演示入口

本轮使用新的独立业务实例（Linux回环14212）和[`business_demo_gateway.py`](../../scripts/business_demo_gateway.py)（回环14213）。网关托管`npm run build`实际生成的前端文件，`/api`、`/poc`转发到既有CPU PoC 14200，`/business/api/v1`转发到新业务实例14212。它只提供研发入口，固定回环上游，不产生业务身份/案件/授权或结果；静态文件和API响应禁止缓存，不转发Cookie，不跟随上游跳转。

Windows只需转发新网关端口，访问`http://127.0.0.1:14183/`；不要求Windows安装Python、数据库或消息队列：

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:14183:127.0.0.1:14213 glwy@172.16.58.179
```

如果该端口已有本批SSH监听，可直接打开页面，不重复绑定。本轮独立源码、构建、实例路径与PID由维护人在服务器仓库外`runtime/media-traceability-system/development-delivery-current.private.json`核对；该文件不含于Git。实际进程存活、源码摘要和CI见[本批验证](../00-project/validation/development-delivery-validation.json)。后台进程不承诺系统重启后自动恢复；正式systemd迁移仍按原生迁移计划进行。

页面入口如下：

| 地址片段 | 功能与使用边界 |
| --- | --- |
| `#/`、`#/health` | 原自建图片上传→对象存储→队列→合成CPU推理及健康检查；不是正式识别模型。研发令牌由操作者在服务器本地使用既有`python scripts/poc_control.py token`取得，填入页面，不发送到聊天或URL。 |
| `#/business` | 连接实际业务访问令牌；原PoC令牌不能代替。身份或策略未装配时如实拒绝。 |
| `#/tasks` | 按已有任务编号读取当前执行、节点、事件；另选精确运行/结果版本读取快照、发现、证据和媒体时间轴。三枚历史绑定响应头缺失/不符即拒绝显示，无快照不造空成功。 |
| `#/reviews/pending` | 按案件游标分页查询待复核队列；READY、RESULT_UNAVAILABLE、SOURCE_BLOCKED分别显示，可进入任务页，不自动作出复核决定。 |
| `#/approvals`、`#/audit` | 保留审批、审计查询和批准绑定导出；仍由后端逐次核验权限、范围与业务规则。 |

任务/案件/历史版本切换会清空旧结果，晚到响应不覆盖新查询。尚未挂载的资产/任务列表、任务创建、重跑等接口不显示成可用功能；当前监控为主动查询，不声称自动刷新、图形DAG或真实任务生产者已完成。

新建实例仍按下文`prepare`流程，仅向新的随机数据库应用0001—0011迁移；旧14202进程及其数据保留。**不要把当前0011代码直接切到旧实例数据库，也不要对已存在实例重复prepare。**

## 当前页面和API

本机开发页面：`http://127.0.0.1:14182/#/business`；审批页`#/approvals`，审计页`#/audit`。原上传验证在`#/`，系统健康在`#/health`。Vite将`/api`、`/poc`交给原API的14200端口，将`/business`交给独立业务API的14202端口并去掉此前缀。

原业务实例只绑定Linux的`127.0.0.1:14202`，本轮新实例使用14212；原文下面14202启动命令保留为旧实例/新部署示例。可检查各实例`/openapi.json`，业务操作仍逐请求鉴权；未装配身份和正式策略时应返回401或503。API进程运行、数据库结构存在、页面可打开三者均不代表已有正式用户授权或可处理真实业务。

Windows通过SSH转发14200和14202，Vite使用锁定Node22.21.1运行，不使用PoC访问令牌冒充业务身份。页面令牌仅在内存；清除身份或刷新后不保留。不要将令牌、口令、MFA或私钥发送到聊天、写进源码或URL。

## 新建独立Linux研发数据库

工具[`scripts/business_development.py`](../../scripts/business_development.py)仅接受显式的隔离测试实例配置和**尚不存在**的仓库外私密目录。它检查PostgreSQL16、同机数据目录容量至少5GiB和凭据语句日志条件；只在随机命名的新`mt_business_preview_…`数据库应用版本迁移，创建随机口令的最小`mt_runtime`成员。不改已有数据库，不创建业务用户、案件、正式审批或测试成功数据。

下面路径是新部署示例；**已建立的当前实例不要重复prepare**。实际当前目录保存在服务器仓库外`runtime/media-traceability-system/business-preview-current.private.json`，只由维护人本地读取，不提交其中内容。

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py310/bin/python scripts/business_development.py prepare \
  --private-directory /workspace/glwy/runtime/media-traceability-system/business-preview-NEW-ID \
  --admin-config /workspace/glwy/runtime/media-traceability-system/business-test-postgres-private.json \
  --create-isolated-database
```

失败时保留私密目录内`setup-intent.json`供维护人检查，只含本次新数据库及角色名称；工具不自动删除数据库，也不改全局配置以绕过失败。容量不可核验或不足时停止，不能用宿主大盘余量代替另一Docker数据卷的余量。

启动使用既有私密目录，在当前终端前台运行：

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/business_development.py serve \
  --private-directory /workspace/glwy/runtime/media-traceability-system/business-preview-NEW-ID \
  --port 14202
```

启动会核验实际数据库角色非超级用户、非BYPASSRLS、非目录管理员、无跨表读写和角色/库管理权；默认不安装身份、六角色候选或合成提供者。日志关闭访问凭据输出。停止仅结束这一个已核对来源的进程，前台可按Ctrl+C；不清理数据库、对象或其他服务。临时后台进程不承诺重启/退出登录后持久性，正式systemd采用仍属原生迁移后续工作。

## 前端启动

在前端目录用既有锁定Node执行`npm ci`及`npm run dev -- --port 14182 --strictPort`。Windows远程入口另开终端：

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 14200:127.0.0.1:14200 -L 14202:127.0.0.1:14202 glwy@172.16.58.179
```

若端口已有监听，先核对现有进程，不杀进程或重复绑定。前端依赖只按`package-lock.json`安装；不执行全局npm升级。

## 已实现与未验证的区分

- 业务身份连接与内存清理、审批列表/详情/申请/决定/撤销、审计游标查询和批准绑定导出页面已实现；详情使用服务端ETag，变更使用幂等键。
- 审计时间/用户/对象筛选明确只筛当前页。完整服务端过滤尚未进入当前OpenAPI，仍是T018剩余工作；不增加未确认字段冒充完成。
- 导出返回202回执后，使用`object_id`查询状态；仅READY后经鉴权下载端点取得JSON文件，不直连对象存储。
- 当前启动是无业务授权的真实开发框架；正式身份/权限提供者、端到端成功操作、全量权限/安全/性能和正式验收分别登记，不能用默认拒绝或页面截图替代。
- [T013本人待办](../03-development/t013-owner-action-checklist.md)仍有第二独立介质、真实身份恢复及旧凭据失效/退役；已完成的密钥和MFA动作不要重复。

当前实际源码、测试和CI见[本批开发记录](../03-development/business-console-implementation-plan.md)及任务卡；源码同步不等于共享迁移或正式策略采用。
