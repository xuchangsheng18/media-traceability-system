# T013管理员接管的技术补齐

本轮沿用已批准的[T013设计](t013-keycloak-identity-design.md)与[8步计划](t013-keycloak-implementation-plan.md)第5、8步，补齐管理员首次改密/MFA、bootstrap退出的隔离验证和原计划缺失的[身份运维手册](../10-deployment/keycloak-identity-runbook.md)。不改变公共API、业务数据库、原100包锁或Python候选暂缓决定。

## 代码及边界

`scripts/identity/handover.py`提供新账号受控初始化和只读配置检查。`prepare`默认预览；`--apply`由操作者在交互终端执行，密码不进入命令行或报告。新账号从禁用状态创建，拒绝覆盖旧账号；首次必须改密及配置MFA。失败时尝试禁用并核实；网络故障导致无法核实的状态明确转人工核查。它不自动移除共享bootstrap或修改私密启动卷。

独立审查指出master域没有继承业务域的密码策略，初版可能接受短的首次修改密码。已追加master自己的14位下限与内建暴破保护前置检查，缺失时拒绝建号及配置就绪；单独的`master-protection`命令默认预览，显式执行时只为原本空策略建立下限，保留现有更强策略，弱/歧义策略转人工审阅。真实首次改密用例同时验证13字符替换被拒绝，再验证足够长的替换成功。新检查和工具不自动修改共享master，也不把内建保护的配置检查说成完整暴破/安全验收。

启用保护后的首轮演练实际记录了`user_temporarily_disabled`：连续负向场景进入快速失败窗口，后续正确登录因此被拒绝。对照[26.8.1保护器实现](https://github.com/keycloak/keycloak/blob/26.8.1/services/src/main/java/org/keycloak/services/managers/DefaultBruteForceProtector.java)，测试现在读取当前服务的快速检测窗口，按该窗口分隔独立场景；不关闭保护、不清除失败计数、不改变业务超时，也不将锁定中的拒绝冒充正向成功。原失败与复测分别保留在报告。

`inspect_handover`使用调用方已经认证的管理读取端口，检查精确master/user标识、master密码/暴破/管理事件保护、启用状态、OTP凭据、待办动作、master管理角色、bootstrap是否已移除和admin-cli密码grant是否关闭。管理事件必须开启且不保存请求表示详情；真实测试读取新管理员创建事件并确认没有请求表示。配置就绪不能证明新MFA登录、旧bootstrap凭据拒绝、本人保管或实际交接；返回值始终将这些实际事项保持未核实。配置检查不接受“指定了姓名”替代运行证据。

真实演练复用`RecoveryLab`的独立三服务、随机端口/网络/数据卷，全部绑定回环。新建的是`synthetic-admin-*`测试管理员，不是徐昌胜的真实账号。通过真实TLS/HTTP授权码、PKCE和MFA表单交换令牌；这条新增测试不声称是浏览器视觉验收，既有真实浏览器OIDC用例继续保留。

测试范围：首次改密与OTP注册、密码单独不能取得授权码、错误及重复OTP拒绝、新会话正确OTP取得管理访问、移除bootstrap后旧token/secret拒绝、重启后MFA/管理员及bootstrap退出状态保留。表单字段依据精确[26.8.1注册模板](https://github.com/keycloak/keycloak/blob/26.8.1/themes/src/main/resources/theme/base/login/login-config-totp.ftl)和[26.8.1登录模板](https://github.com/keycloak/keycloak/blob/26.8.1/themes/src/main/resources/theme/base/login/login-otp.ftl)核对；OTP算法仅用于自建测试夹具，不是正式因素保管工具。

## 实际验证记录

本轮先运行新增测试看到缺少实现的失败，再实现并复测。首轮只读检查9项通过，真实独立服务的MFA/bootstrap/重启演练1项通过；随后增加受控初始化及首次改密的真实联测。最终源码、数量及失败记录以[本轮报告](../00-project/validation/t013-admin-handover-report.json)、[本轮精确提交CI](../00-project/validation/t013-admin-handover-ci-report.json)及[限定代码审查](../00-project/validation/t013-admin-handover-code-review.json)为准，不能借用恢复批的旧CI证明新代码。

```text
python -m pytest tests/platform/test_t013_handover.py -q
python -m pytest tests/identity/test_admin_handover_live.py -q
python -m scripts.identity.checks run --private-root <新的Git外0700目录> --output <脱敏报告路径>
python scripts/dev.py format-check
python scripts/dev.py lint
python scripts/stage_three_types.py check
```

真实组需已有显式私密身份目标及隔离业务数据库；缺配置不能skip后标记成功。原有50项live、适配器和业务映射测试继续执行；不降低既有断言或扩大认证超时。后台测试日志及TOTP种子留Git外，公开报告仅留测试名、数量、源码/产物摘要和限定结果。

## 尚需本人及实际环境完成

1. 徐昌胜确定真实登录名并实际首次改密/MFA接管；现有姓名登记与合成演练均不能代替。
2. 软件准入、正式身份适用范围/撤销SLA；候选制品/网关配置采用及维护窗口。
3. GPG公钥路径、独立私钥保管与恢复APIsecret/后端私密配置协调；共享bootstrap及历史值退役不能由本轮临时服务证明。
4. 徐昌胜实际复核、适用验收及剩余工时记录。T013保持部分验证，T014不因本轮增加测试而自动取得完整依赖验收。

具体本人操作及失败后的核查顺序见[身份运维手册](../10-deployment/keycloak-identity-runbook.md)。本轮没有创建真实管理员、删除共享bootstrap、采用共享候选、重启共享服务或开展T014。
