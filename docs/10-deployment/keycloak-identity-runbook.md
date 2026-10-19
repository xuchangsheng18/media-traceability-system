# 身份服务研发运行与实名管理员交接

适用：当前 Linux／py310／CPU 研发节点。身份系统管理员、开发负责人及指定复核人均已登记为徐昌胜；这不是账号、MFA、实际复核或验收完成记录。实际结果见[当前22项登记](../00-project/validation/t013-keycloak-acceptance-ledger.json)、[恢复说明](../03-development/t013-recovery-validation.md)和[管理员交接验证](../03-development/t013-admin-handover-validation.md)。

## 入口及观察

Linux 源码为 `/workspace/glwy/projects/media-traceability-system`，运行目录为 `/workspace/glwy/runtime/media-traceability-system/identity`。私密目录0700、文件0600，文件不进入Git。当前身份服务仍为独立三容器；全原生迁移按N01及后续计划执行，不能把源码同步当运行服务迁移。

```sh
cd /workspace/glwy/projects/media-traceability-system
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.control status
```

公开协议入口 `https://172.16.58.179:18443`；管理入口仅服务器回环 `https://localhost:18444`。在Windows终端建立隧道后，访问 `https://localhost:18444/admin/master/console/`：

```sh
ssh -N -L 18444:127.0.0.1:18444 glwy@172.16.58.179
```

先核对服务器公有CA证书 `identity/pki/ca.crt` 的摘要及来源，再按所在单位流程导入本人浏览器的信任库。CA私钥不复制到客户端；不得跳过证书校验、使用公开管理端口或把SSH凭据写入仓库。当前尚未完成实名管理员接管，不能假定已有可登录的用户名和密码。

## 实名账号初始化

徐昌胜已确认实际登录名为`xuchangsheng`，当前仍只是登录名登记，账号尚未创建。工具只接受小写字母开头的3—64位字母、数字、点、下划线或连字符，不使用bootstrap或service-account保留前缀。先审阅本轮代码和验证报告；下面第一条只预览，不创建账号：

```sh
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.handover prepare --username xuchangsheng
```

创建账号前必须核对master域自己的密码与暴破保护，不能借用`media-trace`业务域设置。初始研发下限为14字符；工具还检查内建暴破保护开启、失败次数及等待窗口为正值。下面的第一条只预览；第二条由操作者在交互终端显式建立缺省策略，不创建账号：

```sh
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.handover master-protection
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.handover master-protection --apply
```

工具只在密码策略原本为空时建立`length(14)`，已有满足下限的更强策略原样保留；遇到现有弱策略、重复长度项或无法明确识别的长度表达式时拒绝，要求人工审阅，不能覆盖成较弱默认值。开启暴破保护时沿用master已有的正值失败/等待配置，不自行生成正式业务阈值；原值无效或变更后不能读回核实则拒绝继续创建管理员。该操作本轮仅在临时服务测试，未在共享master执行。

同一显式保护动作还启用master管理事件记录并关闭请求表示详情；创建管理员、赋角色等重要操作需有事件，密码等请求正文不作为审计内容保存。未满足这两项也拒绝创建账号。master事件保存期限、集中归档及访问权限仍需按实际环境复核，本工具不代替正式审计制度，也不自动改写现有保存期限。

准备好本人管理设备、管理入口CA信任和保管安排后，由操作者在交互终端执行：

```sh
/opt/conda/glwy/envs/py310/bin/python -m scripts.identity.handover prepare --username xuchangsheng --apply
```

工具从服务器Git外配置访问既有bootstrap管理端口，只在明确`--apply`时写入；临时密码在终端隐藏输入并再次确认，不能放进参数、环境变量、脚本、对话或Git。无交互终端会拒绝。密码长度14—128位，遵循后续实际密码制度。

工具只创建新账号：先禁用创建、赋予master管理角色、保留`UPDATE_PASSWORD`和`CONFIGURE_TOTP`首次动作，再启用账号。已有账号一律拒绝，不自动改绑或覆盖。角色配置失败时尝试禁用并核实；如果服务失败导致状态不确定，必须人工核查新账号是否存在、是否禁用以及角色状态，不能再次盲目创建或声称已回滚。初始化不删除bootstrap，不改变业务角色、单位/案件范围或来源授权。初始化完成也不是本人交接完成。

## 本人接管及bootstrap退出

1. 徐昌胜通过已验证的SSH回环管理入口首次登录，补齐本人资料，修改临时密码，用本人控制的验证器完成MFA。密码、二维码种子、一次性验证码、恢复码、浏览器会话及令牌不得发送到对话或Git。
2. 使用新的浏览器会话实际验证：只有密码不应取得授权码；错误验证码被拒绝；正确验证码后可以访问master管理控制台。检查本人账号启用、MFA凭据存在及所需管理角色，不能只看配置行。
3. 先按[管理工具替代及退役准备](../03-development/t013-bootstrap-management-replacement.md)建立专用客户端，使用本人密码/MFA取得最长300秒的管理会话，再用`inspect`验证。既有管理CLI通过`MT_IDENTITY_ADMIN_SESSION`显式选择私密会话文件；失败不回退bootstrap。测试夹具仍以自己的临时bootstrap初始化，不是共享管理身份。共享入口的实际配置和本人验证仍待执行。
4. 只有替代入口、可恢复备份、独立密钥保管和维护安排均满足后，才安排共享bootstrap退役。届时精确定位master中的`bootstrap-project-service`，核对对象及来源，移除后验证旧机器secret不能取得令牌、旧bootstrap access token不能调用管理API；不删除其他客户端或业务用户。当前仅做退役准备，不执行这一步。
5. bootstrap启动参数、私密文件和卷中历史值的退役，以及共享候选镜像/网关配置采用、重启验证，须按上述维护安排执行。新工具只生成独立私密候选及禁止重建标记，不替换共享文件或卷。删除数据库客户端本身不能证明磁盘/旧备份中的secret已经清除。工具不会自动擦写共享私密卷或重启服务。
6. 记录实际操作时间、执行人、证据摘要、成功/失败/未执行和后续问题；不附敏感截图和原始凭据。指定复核人登记为徐昌胜，不自动形成独立双人复核或验收签字。

[Keycloak官方bootstrap说明](https://www.keycloak.org/server/bootstrap-admin-recovery)要求临时管理员在取得长期、安全管理访问后人工移除，并说明启动bootstrap只在master尚未存在的初次启动时创建。仍需实际重启验证和历史凭据退役，不能仅据此推断共享环境已经完成交接。

## 备份、恢复及失败处理

当前内部研发密钥组、公钥/受保护备份复制及加密吊销材料结构已核验，进度见[密钥保护跟进](../03-development/t013-signer-protection-followup.md)。真实签名、两把子密钥实际解密、独立恢复、暴露口令及旧副本处置仍待完成。恢复私钥留在已指定U盘；现有Linux本地GPG-home恢复入口不能通过上传该私钥来满足，真实离线解密/流式恢复需按保管边界另行设计和验证。

身份备份采用既有GPG签名与流式加密；N01的age方案另行管理，两者的公钥和验收证据不能互相替代。由保管人提供GPG接收/签名公钥文件路径、指纹与独立私钥保管安排；禁止提交私钥或将解密私钥与在线备份同放。正式材料尚未提供，临时测试密钥不算正式保管证明。

`scripts.identity.backup`与`restore`的准确参数以各自`--help`及[8步计划](../03-development/t013-keycloak-implementation-plan.md)为准。先做独立新卷恢复；旧备份可能恢复已经撤销的会话。恢复后的会话清理、not-before、签名密钥撤换和APIsecret更新必须与后端私密配置协调。现有`reconcile`只允许临时验收realm，不能直接用于共享master或正式realm。具体实测与失败记录见[恢复批说明](../03-development/t013-recovery-validation.md)。

共享切换、真实停写、候选采用和正式验收都尚未执行。当前缺少正式密钥保管、软件准入和维护窗口时，只能继续隔离研发和准备工作；保留旧卷、现有服务及失败记录。
