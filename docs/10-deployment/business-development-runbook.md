# 业务前后端开发启动与当前边界

本入口用于Linux／现有Miniforge py310／CPU内部研发。原上传验证页与七服务保留；新增业务控制台复用同一Vue工程，业务API单独运行。Python候选暂缓，不安装新Python或替换原100包锁。

## 当前页面和API

本机开发页面：`http://127.0.0.1:14182/#/business`；审批页`#/approvals`，审计页`#/audit`。原上传验证在`#/`，系统健康在`#/health`。Vite将`/api`、`/poc`交给原API的14200端口，将`/business`交给独立业务API的14202端口并去掉此前缀。

业务API只绑定Linux的`127.0.0.1:14202`。可检查`/openapi.json`，当前业务操作仍逐请求鉴权；未装配身份和正式策略时应返回401或503。API进程运行、数据库结构存在、页面可打开三者均不代表已有正式用户授权或可处理真实业务。

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
