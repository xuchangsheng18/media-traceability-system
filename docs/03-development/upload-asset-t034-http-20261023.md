# 上传到资产真实传输联调与T034创建接口

2026-10-23。范围为当前Linux／Miniforge py310／CPU的隔离研发验证。上传到资产的浏览器、HTTP、数据库、消息队列和对象字节链路已实际贯通；身份、来源与机构权限事实使用明确自建夹具，不能登记为真实身份接管、正式授权或共享环境部署。T034创建HTTP入口已挂载，默认仍无受信材料提供方。精确结果及后续完整回归状态见[验证记录](../00-project/validation/upload-asset-t034-http-20261023.json)。

## 上传到资产

新增[隔离浏览器测试](../../tests/business_browser/test_upload_asset_live.py)及[浏览器驱动](../../frontend/e2e-live/upload-asset.mjs)。不拦截或伪造API响应：运行实际前端构建、随机回环端口的业务应用及网关、随机新建PostgreSQL测试库、真实RabbitMQ、上传校验worker及FileObjectStore。只创建无敏感的8×8 PNG，不下载外部数据，不向正式案件库写入。

浏览器连接自建测试身份，选择实际测试案件和来源，初始化上传，发送3个二进制分片，核对服务端分片，提交校验并轮询。worker从持久outbox发布到该上传独占的v2队列，实际消费后登记COMPLETED和VALID资产。页面跳转资产详情、读取元数据、下载固定版本并核对原始SHA-256，再从资产列表找到同一资产。测试同时检查原数据库记录、真实发布／消费次数及下载摘要，清理仅针对本次随机上传队列和测试数据库。

初次运行中，测试身份缺少`asset.download`，页面禁止下载；补齐后，来源仍未包含download用途，服务端继续拒绝。修正自建测试输入后完整链路通过，产品权限检查未放宽。该测试的成功标记明确为`PASS_REAL_TRANSPORT_SYNTHETIC_TRUST`。

共享研发入口仍未配置业务身份、机构策略及工作委托提供方，且运行构建早于本批源码。源码同步不更新该实例，不自动授予账号、迁移共享数据库或重启服务。因此“真实传输隔离联调通过”和“本人身份下的共享业务演示已完成”分别登记。

## T034接口接线

按[已批准I01—I05计划](t034-creation-implementation-plan.md)的I04接入现有`POST /api/v1/analysis/tasks`，复用原TaskCreate六字段、Accepted三字段、幂等规则及统一权限guard，不改变公共OpenAPI。基线失败用例实际返回405；实施后未认证请求返回401，接口进入原有默认保护。

[路由](../../backend/business_app/task_creation_router.py)复用案件授权、冻结请求上下文、[原子创建服务](../../backend/business_app/task_creation_service.py)和事务末尾栅栏；202仅表示任务QUEUED受理，不产生业务结果或运行算法。原回执重放保留原Accepted和ETag。

`create_app`新增显式可选的`task_creation_materials`和`task_creation_budgets`注入。没有预算不构造服务；仅提供材料而缺少预算时拒绝启动。缺少真实事实、策略、材料或有效期仍拒绝，不从元数据推造Proof，不建立默认ACTIVE映射。开发启动工厂不注入测试提供方。

[专项HTTP测试](../../tests/business/test_task_creation_http.py)验证真实SQL原子写集合、无结果的202受理、精确重放，以及无权限、提供方缺失、额外查询、重复幂等头、重复JSON键等拒绝和零半写。夹具不是部署用的采用或Proof签发者。

原权限门禁按实际路由扩展到52个已挂载业务操作，剩余21个未挂载。原51操作矩阵保存到[历史副本](../08-security/history/task-creation-predecessor-scope-matrix.json)，通过[单接口增量核验](../../scripts/verify_task_creation_registration.py)接续原严格注册链；六角色246格设计输入与默认拒绝不变。CI保留原全部步骤和失败探针，另加构建及真实传输浏览器检查，没有删除、跳过或降低安全扫描。

## 剩余工作与交接

- T034的真实映射采用、当前事实、Proof和handler能力／许可来源、聚合运行预算与执行截止约束仍需落地；I03未知提交结果与恢复代际验证、I05完整门禁及整卡验收继续保留。
- 上传的常驻worker启动与健康检查、真实工作委托、完整媒体安全覆盖、配额及恢复仍待。当前PNG测试不能代替视频、全媒体和容量验收。
- 本人业务演示前须完成T013本人管理员接管、改密和MFA；口令不得发送到对话。需要明确实际单位、研发案件及来源用途依据，以及使用的权限／工作委托提供方。未知项继续拒绝，不把自建夹具配置为共享业务授权。
- 本轮不增加整任务完成数或自动折算子步骤，170任务与源验收标准保留。算法、Python候选和原100包锁不变。

执行入口：先`npm --prefix frontend run build`，再在既有锁定Node／浏览器及显式隔离PostgreSQL／RabbitMQ配置下运行`PYTHONPATH=backend python -m pytest tests/business_browser -q --tb=short`。数据库整套回归与权限整套回归串行执行；不得指向PoC或共享业务库。
