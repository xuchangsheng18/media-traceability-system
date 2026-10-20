# T013 徐昌胜本人接管、密钥验证与恢复操作清单

最新本人实核（2026-10-20）：A01—A06适用操作已完成，A07已完成批准配置和本人正向管理验证，控制台仅密码/错误OTP负向已由本人反馈通过，见两E恢复、第二轮新保护签名/新备份恢复、四份已知旧导出退役及[本人PKCE/MFA管理回执](../00-project/validation/t013-owner-mfa-management-validation.json)。不要重复已完成命令；下面保留步骤用于追溯。仍待第二独立介质、A08真实身份备份/隔离恢复、A09恢复后旧凭据失效与受控退役/回切、A10实际验收。复制命令时不要复制代码块首尾的三个反引号。

2026-10-20。适用同一单位内部Linux／py310／CPU研发。徐昌胜为开发负责人、身份管理员、密钥保管人及指定复核人。本人已操作并由实际公开状态和安全回执核实的项目按对应证据登记；人员指定不代替验收。四项共享身份采用有单独明确授权，bootstrap仍保留；Python3.13/3.12候选继续暂缓。

顺序及当前状态：**A01公开核对 → A02两E解密 → A03恢复私钥备份新home → A04签名保护 → A05真实签名 → A06签名备份恢复 → A07本人改密/MFA和管理工具**已完成其中明确记录的正向子范围；A07控制台仅密码/错误OTP负向已收到本人实测反馈，未独立关联服务器事件，四份已知旧导出已按明确授权退役。接下来是**A08真实身份备份/隔离恢复 → A09旧凭据失效与受控退役/回切 → A10实际复核登记**；第二独立介质暂无，后续共享恢复/退役仍需形成可审阅方案和实际批准。

## A01：只读核对位置和公开指纹（现在可操作）

U盘当前为 `G:\公安厅项目密钥`，未做整盘/容器加密，按你此前决定暂以GPG口令保护用于内部研发。FAT32不能以NTFS ACL代替加密；本清单不将同一U盘的两个目录当作两份独立介质。

在本机PowerShell执行。以下命令只列文件元信息/公钥指纹，**不把私钥文件内容显示出来**。不要把口令作为PowerShell命令输入，不使用`--passphrase`、聊天代输或`Start-Transcript`记录口令操作。

```powershell
$Gpg = 'D:\GnuPG\bin\gpg.exe'
$GpgConf = 'D:\GnuPG\bin\gpgconf.exe'
$KeyRoot = 'G:\公安厅项目密钥'
$KeyHome = Join-Path $KeyRoot 'recovery-gnupg'
$RecoveryFpr = '1F3B582BCF39F5C8D5C6F698241FF3B8246E99FF'
$SignerFpr = 'C2F06E6116BDE369EE835C5D00AC4AAE1EB66C2D'
$Subkeys = @('74FF3C32A5738FAD98C9A90D97672271E1161785',
             '2A8E86CA40914E1F89A6FA8DCC569FFF970FD133')
foreach ($Required in @($Gpg, $GpgConf, $KeyHome,
    (Join-Path $KeyRoot 'public\recovery-recipient.asc'),
    (Join-Path $KeyRoot 'public\backup-signer.asc'),
    (Join-Path $KeyRoot 'private-backups\recovery-secret-backup.asc'),
    (Join-Path $KeyRoot 'private-backups\backup-signer-secret-reprotected-cycle2-20261020.asc'))) {
    if (-not (Test-Path -LiteralPath $Required)) { throw "缺少文件或目录：$Required；停止" }
}
& $Gpg --version
if ($LASTEXITCODE -ne 0) { throw 'GPG不可用，停止' }
& $Gpg --homedir $KeyHome --with-colons --with-subkey-fingerprint --list-secret-keys $RecoveryFpr
if ($LASTEXITCODE -ne 0) { throw '恢复密钥检查失败，停止；不要重新生成密钥' }
& $Gpg --homedir $KeyHome --with-colons --with-subkey-fingerprint --show-keys (Join-Path $KeyRoot 'public\backup-signer.asc')
if ($LASTEXITCODE -ne 0) { throw '签名公钥检查失败，停止' }
Get-ChildItem -LiteralPath (Join-Path $KeyRoot 'public'), (Join-Path $KeyRoot 'private-backups') -File |
    Select-Object Name, Length, LastWriteTime
```

必须看到恢复主指纹及两把E子密钥，签名公钥必须是上面的SignerFpr；签名密钥没有E能力是预期用途分离。旧记录中的10361字节恢复导出、3486字节签名导出只是结构记录；文件大小一致不能证明成功解密或恢复。不要再执行`quick-add-key`，不要删除多出来的第二把E子密钥。

## A02：逐一证明两把恢复E子密钥能解密（现在可操作）

服务器已有**只含固定无敏感测试文字**、分别仅针对每一把E子密钥的两个密文。本轮只读重核的公开文件摘要：

| 文件 | SHA256 |
| --- | --- |
| key-check.txt | 0ac590181b508886a65acb56dcad6240c0c0a58d940d9408a7521ed644f465ce |
| subkey-74FF3C32A5738FAD98C9A90D97672271E1161785.gpg | 56c6fec647b1317912672a1a125aeb0501f5d04ba628fa00c3e4cc4759ae0263 |
| subkey-2A8E86CA40914E1F89A6FA8DCC569FFF970FD133.gpg | cf34bd6e723d4ba3f5820b49364158456ee5cea56b2139fc066ebf4c2b7290d5 |

沿用A01的变量，在同一个PowerShell窗口执行。创建新的检查目录，拒绝覆盖。`scp`只下载公有测试文字/密文，不上传任何恢复私钥。

```powershell
$CheckDir = Join-Path $KeyRoot ('verification-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
if (Test-Path -LiteralPath $CheckDir) { throw '检查目录已存在，停止' }
New-Item -ItemType Directory -Path $CheckDir -ErrorAction Stop | Out-Null
$RemoteProbe = 'glwy@172.16.58.179:/workspace/glwy/runtime/media-traceability-system/t013-bootstrap-20261019/gpg-public-probes-20261019T105539Z-9b130a/'
$ExpectedHashes = @{
    'key-check.txt' = '0ac590181b508886a65acb56dcad6240c0c0a58d940d9408a7521ed644f465ce'
    'subkey-74FF3C32A5738FAD98C9A90D97672271E1161785.gpg' = '56c6fec647b1317912672a1a125aeb0501f5d04ba628fa00c3e4cc4759ae0263'
    'subkey-2A8E86CA40914E1F89A6FA8DCC569FFF970FD133.gpg' = 'cf34bd6e723d4ba3f5820b49364158456ee5cea56b2139fc066ebf4c2b7290d5'
}
foreach ($Name in $ExpectedHashes.Keys) {
    & scp ($RemoteProbe + $Name) (Join-Path $CheckDir $Name)
    if ($LASTEXITCODE -ne 0) { throw "下载失败：$Name；停止" }
    $ActualHash = (Get-FileHash -LiteralPath (Join-Path $CheckDir $Name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHashes[$Name]) { throw "摘要不一致：$Name；停止" }
}

function Test-RecoverySubkeys {
    param([string]$HomePath, [string]$Prefix)
    foreach ($SubFpr in $Subkeys) {
        $Plain = Join-Path $CheckDir ($Prefix + '-' + $SubFpr + '.txt')
        $Status = Join-Path $CheckDir ($Prefix + '-' + $SubFpr + '.status.txt')
        if ((Test-Path -LiteralPath $Plain) -or (Test-Path -LiteralPath $Status)) { throw '已有输出，停止，不覆盖' }
        & $GpgConf --homedir $HomePath --kill gpg-agent
        if ($LASTEXITCODE -ne 0) { throw '无法清空该home的代理缓存，停止' }
        & $Gpg --homedir $HomePath --no-options --status-fd 1 --output $Plain --decrypt (Join-Path $CheckDir ('subkey-' + $SubFpr + '.gpg')) > $Status
        if ($LASTEXITCODE -ne 0) { throw "解密失败：$SubFpr；停止" }
        if ((Get-FileHash -LiteralPath $Plain -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedHashes['key-check.txt']) { throw '解密文字摘要不一致，停止' }
        $StatusText = Get-Content -LiteralPath $Status -Raw
        $KeyPattern = '(?m)^\[GNUPG:\] DECRYPTION_KEY ' + $SubFpr + ' ' + $RecoveryFpr + ' '
        $AeadPattern = '(?m)^\[GNUPG:\] DECRYPTION_INFO 0 9 2(?: 0)?(?:\r?$)'
        if (($StatusText -notmatch $KeyPattern) -or ($StatusText -notmatch '(?m)^\[GNUPG:\] DECRYPTION_OKAY(?:\s|$)') -or ($StatusText -notmatch $AeadPattern)) { throw '未证明精确子密钥解密及AES256/OCB完整性，停止' }
        Write-Output ('PASS_DECRYPT_EXACT_SUBKEY_' + $SubFpr)
    }
    & $GpgConf --homedir $HomePath --kill gpg-agent
    if ($LASTEXITCODE -ne 0) { throw '结束时代理缓存清理未确认' }
}
Test-RecoverySubkeys -HomePath $KeyHome -Prefix 'original'
```

GPG弹出口令框时由本人输入**恢复密钥口令**，不是Linux签名口令、SSH密码或指纹。如果取消、超时、`No secret key`或摘要/状态不符，停止，只回报错误文字。每个密文只对应一把子密钥，必须有两条不同的`PASS_DECRYPT_EXACT_SUBKEY_...`，只解开包含两收件人的同一个密文不能证明两把都可用。

2026-10-20修正：既有两个固定密文的公开包头是tag20/version1、AES256/OCB AEAD，不是tag18/MDC。GnuPG 2.5.24已将`GOODMDC`列为废弃状态，当前版本仍可能为兼容而输出；本清单不依赖这一兼容标志，要求GPG退出0、精确`DECRYPTION_KEY`、`DECRYPTION_OKAY`、该固定AEAD参数及明文摘要同时成立。这保留完整性核验；未来算法/封装变化应重新核验，不得直接去掉断言。

## A03：从恢复私钥备份建立新的隔离home并重验（现在可操作）

该步骤只在U盘新目录导入已有受保护备份；不修改原home，不导入或激活吊销材料，不重新生成主/子密钥。沿用A01/A02的变量和函数：

```powershell
$RestoreHome = Join-Path $CheckDir 'restored-recovery-gnupg'
if (Test-Path -LiteralPath $RestoreHome) { throw '恢复home已存在，停止' }
New-Item -ItemType Directory -Path $RestoreHome -ErrorAction Stop | Out-Null
& $Gpg --homedir $RestoreHome --no-options --import (Join-Path $KeyRoot 'private-backups\recovery-secret-backup.asc')
if ($LASTEXITCODE -ne 0) { throw '备份导入失败，停止' }
& $Gpg --homedir $RestoreHome --no-options --with-colons --with-subkey-fingerprint --list-secret-keys $RecoveryFpr
if ($LASTEXITCODE -ne 0) { throw '恢复后的完整密钥组检查失败，停止' }
Test-RecoverySubkeys -HomePath $RestoreHome -Prefix 'restored'
```

必须在原home和恢复home分别看到两把子密钥的精确解密标记。此时仅证明**现有备份可导入新home并使用两把E子密钥**；第二个目录仍在同一物理U盘，不是独立介质/异地恢复，也不是Linux身份数据库恢复。独立介质尚未明确：后续需提供另一个实际受保护介质/设备路径，不能把G盘复制到G盘当异地完成。不得上传该新home、恢复私钥或原始吊销证书到Linux/GitHub。

## A04：再次保护已完成结构实核，旧副本待处置

第一轮曾因实际新口令误输入终端确认位置而重新进入保护处理；A05在签名前停止。第二轮首次被取消后已只读核验活动密钥未变、无新导出。随后本人使用专用重试入口得到更换成功标记；助手已核验第二轮新导出、公钥完整指纹及保护结构，并以精确摘要复制到U盘新文件：`private-backups/backup-signer-secret-reprotected-cycle2-20261020.asc`。见[实际观察与历史边界](../00-project/validation/t013-reprotected-signer-owner-validation.json)。

**A04不要再运行。** 原单次入口返回重复保护是正常行为；不删除标记、不覆盖旧输出、不重新生成密钥。此次仅证明活动保护已改变及新导出存在，仍由本人确认设置的是全新、非空、未发送过的口令。所有口令只在GPG框内输入，不在终端文字行/聊天中输入。

已知副本包括Linux旧导出、U盘旧导出以及第一轮新保护导出；第二轮恢复实测前均保留隔离，后续明确处置。没有删除/覆盖这些副本，不宣称FAT32普通删除等于安全擦除。第二独立介质及整盘/容器加密继续保持原待落实边界。

## A05：固定公开文字签名和精确验签（本人已完成，实核通过）

2026-10-20本人已执行下列入口；助手在全新仅公钥home重验，正常退出0、篡改拒绝退出1，完整指纹匹配。以下命令保留作记录，不重复运行。

```powershell
ssh -tt glwy@172.16.58.179 "bash /workspace/glwy/runtime/media-traceability-system/t013-bootstrap-20261019/signer-protection-cycle2-20261020T033608Z-e63bec/test-reprotected-fixed-message.sh"
```

新入口只签固定无敏感测试文字，精确核验完整指纹、GPG退出状态及篡改拒绝；一般签名/旧入口仍暂停。成功应显示`PASS_REAL_REPROTECTED_SIGNER_FIXED_MESSAGE_EXACT_SIGNATURE_AND_TAMPER_REJECTION`。请只回报该标记和“已本人设置全新口令”；不发送口令、私钥或原始秘密日志。

该结果不证明真实身份数据库恢复、旧副本退役、MFA接管或整体验收；助手还会核对实际签名与安全回执。

## A06：第二轮新保护备份恢复（本人已完成，限定实核通过）

已准备本机脚本：`D:\公安厅项目\修订成果\T013_第二轮新保护签名备份恢复验证_20261020.ps1`，已由本人实际执行并通过，助手已核验新home公开元数据、实际签名及独立仅公钥复验。它固定核对第二轮新备份和公钥摘要，在U盘新home导入、清空该home代理缓存，用公开测试文字签名，再用仅有公钥的另一home精确验签及测试篡改拒绝。口令仅由本人在GPG框内输入。以下命令保留作记录，不重复运行：

```powershell
& 'D:\公安厅项目\修订成果\T013_第二轮新保护签名备份恢复验证_20261020.ps1'
```

成功标记为`PASS_NEW_PROTECTED_SIGNER_BACKUP_RESTORE_EXACT_SIGNATURE_AND_TAMPER_REJECTION`。若本机拒绝执行脚本，只回报错误文字，不修改全局执行策略。第一轮旧恢复脚本已暂停，不能误用来证明第二轮保护。

同U盘新home仅证明隔离目录恢复，仍不是第二独立介质/异地恢复；吊销材料可用性和真实身份数据恢复分别验证。旧导出在新备份实测及明确处置前保留，不普通覆盖或提前删除。不上传恢复home、恢复私钥或原始吊销证书到Linux/GitHub。

## A07：实名管理员首次改密、MFA和工具接管（正向回执通过，控制台负向由本人反馈通过）

管理账号`xuchangsheng`已创建，本人首次改密/OTP和专用PKCE/MFA签名管理验证已由服务器回执核实；临时令牌文件已清理。不要再次创建账号或运行初始化。以下为操作时的步骤记录；控制台仅密码/单次错误OTP负向已收到本人反馈，单列为本人实测证据，bootstrap未删除，Keycloak master管理员与六个业务角色无自动继承。

1. **可信入口**。管理端口仅服务器回环，Windows保持下列隧道；本轮只读观察服务器公有CA SHA256为`2798c95c64f424d5ae6ac4e050e557794ad4bad04fe12f90ee05c79b4bf989db`，先按可信SSH来源重新核对再信任本人浏览器。只下载`identity/pki/ca.crt`，不下载`ca.key`；不关闭TLS校验。

   ```powershell
   ssh -N -L 127.0.0.1:18444:127.0.0.1:18444 -L 127.0.0.1:18765:127.0.0.1:18765 glwy@172.16.58.179
   ```

2. **只读预览**。另开 `ssh -tt glwy@172.16.58.179`，在Linux交互终端执行：

   ```sh
   cd /workspace/glwy/projects/media-traceability-system
   export PYTHONPATH=/workspace/glwy/projects/media-traceability-system/backend:/workspace/glwy/projects/media-traceability-system
   export PATH=/home/glwy/.cache/media-trace-node/node-v22.21.1-linux-x64/bin:$PATH
   /opt/conda/glwy/envs/py310/bin/python -m scripts.identity.control status
   /opt/conda/glwy/envs/py310/bin/python -m scripts.identity.handover master-protection
   /opt/conda/glwy/envs/py310/bin/python -m scripts.identity.handover prepare --username xuchangsheng
   /opt/conda/glwy/envs/py310/bin/python -m scripts.identity.management setup
   ```

3. **明确采用后**。先`handover master-protection --apply`，再`handover prepare --username xuchangsheng --apply`。工具本人交互隐藏输入临时密码并确认，14—128字符；不把密码放入参数/环境变量/聊天。master弱/歧义策略或已有账号时停止人工核查，不能重试覆盖。成功返回`account_prepared=true`只说明初始化，不是本人接管。
4. **本人浏览器**。访问`https://localhost:18444/admin/master/console/`，首次登录修改临时密码，绑定本人设备的OTP。新私密会话验证密码单独不能取得授权、错误OTP拒绝、正确OTP成功；不要共享二维码种子、一次性验证码、恢复码、cookie或管理令牌，不连续快速负测导致锁定后再误判正向失败。
5. **管理工具**。执行`python -m scripts.identity.management setup --apply`（使用上面锁定Python），再执行`python -m scripts.identity.management login --apply --username xuchangsheng`。在本人可信浏览器打开终端给出的授权URL完成MFA；URL含一次性会话参数，勿贴聊天。工具返回Git外`session_file`路径后，执行`python -m scripts.identity.management inspect --session-file 实际私密路径`。这里的“实际私密路径”须替换成工具刚返回的路径，不是令牌内容；过期重登，失败不回退bootstrap。
6. 本人首次动作和`signed_mfa_management_session=true`实际回执可以登记对应正向子范围；控制台错误OTP和仅密码拒绝已有单列本人反馈，未独立关联服务器事件或扩大到全部管理客户端拒绝路径；不登记整项接管验收。bootstrap仍存在时如实登记，不标整卡完成。当前300秒管理会话不因权限方案审批TTL建议改变。

准确CLI参数见[管理工具替代](t013-bootstrap-management-replacement.md)和[身份运维手册](../10-deployment/keycloak-identity-runbook.md)。当前阶段不要先删除bootstrap。

## A08：真实身份备份与离线私钥兼容恢复（需要新增实施方案，当前不能直接执行）

现有`python -m scripts.identity.backup`参数为`--recipient/--output/--gpg-home/--signing-fingerprint`，可签名后流式加密数据库、私密配置和CA恢复材料；现有`restore`还要求**Linux本地含解密私钥的GPG home**。你已确定恢复私钥留U盘，所以**不能上传私钥来迁就当前恢复入口，也不能把合成恢复测试当作真实保管方案通过**。

需要下一批形成并验证：离线端校验密文摘要及精确签名 → 本人GPG解密 → 经受控加密通道流入服务端新隔离数据库/卷；不落明文dump，不传恢复私钥；每段管道退出值、断流/篡改/错误签名/错误目标拒绝和清理均实测。Windows PowerShell 5的普通管道不能直接假定二进制无损；传输方案未验收前不给一条表面可用的真实库恢复命令。

本轮只读核对还发现三项真实执行前条件：现有`backup.py`采用`--pinentry-mode error`，不能据此假定会弹出本人签名口令框；主指纹收件人没有显式锁定两把E，尚无新真实备份的双E包头证明；数据库、配置和CA是三份分别签名/加密的文件，尚缺共同绑定本次备份ID、三份精确摘要和版本的经签名组合清单。这些均作为下一批具体设计和必要反例测试的输入，不在本批修改工具、生成真实备份或上传私钥。源码依据：[备份工具](../../scripts/identity/backup.py)、[恢复工具](../../scripts/identity/restore.py)。

本人届时提供：备份存放位置、另一恢复介质/设备、可用维护窗口，以及恢复点/恢复时长的适用要求；不要提供私钥或口令。助手完成具体计划、隔离测试和恢复前检查后，再由本人批准真实备份/恢复动作。

## A09：恢复后旧会话/密钥失效、bootstrap退役及回切（A08通过后）

先隔离恢复并禁止对外认证；清理恢复出来的旧会话、设置not-before、撤下旧签名提供器、轮换API secret并协调后端私密配置。旧access/refresh/secret和旧bootstrap令牌必须失败，新本人MFA和新业务映射仍成功；不把“数据库恢复”当作“恢复后旧会话已安全失效”。当前reconcile只接受临时验收realm，拒绝master/共享realm，不能拿它直接处理真实共享库。

在已确认维护窗口按精确目标采用新私密配置/卷，删除指定bootstrap客户端并重验旧token/secret拒绝；核查启动配置、历史私密文件和旧备份的处置记录，保留可恢复原卷。受控回切也须承接最新撤销、密钥和secret代际，不得复活旧凭据。需要停写/重启/删除的命令须在具体计划、备份实测及批准后才生成执行。本批不执行这些动作。

## A10：只回报最小验证结果，并更新台账

| 步骤 | 本人可回报内容 | 助手据此核验 | 不能据此推断 |
| --- | --- | --- | --- |
| A01 | “公开指纹一致”或错误文字 | 文件路径、公开指纹、结构/摘要 | 已成功解密 |
| A02 | 两条不同的`PASS_DECRYPT_EXACT_SUBKEY_...` | 状态中的完整E指纹/主指纹、明文摘要及完整性 | 独立恢复或签名成功 |
| A03 | 说明在restored新home又出现两条标记 | 新home确来自现有受保护备份，重验相同公开绑定 | 第二介质/异地恢复 |
| A04 | 更换成功标记及“已设置全新口令”，或“继续暂缓” | 新导出实际路径/保护元数据，不读取口令 | 旧副本全部处置 |
| A05/A06 | 精确验签/篡改拒绝及恢复步骤结果，不发原始私钥 | 公钥指纹、签名/测试文字摘要、真实命令退出状态 | 真实身份数据库已恢复 |
| A07 | 本人首次改密/MFA完成情况和inspect布尔结果 | 受控只读检查、实际时间和最小事件摘要 | 业务角色已授权/整卡验收 |
| A08/A09 | 按批准计划的运行编号、成功/错误码 | 隔离目标、恢复/旧凭据拒绝/回切证据 | 生产或软件准入自动通过 |

不发送口令、验证码、MFA种子、私钥、原始吊销证书、会话文件内容或敏感截图。成功标记只是本人反馈；仍需实际文件/公开状态核验，不能直接当所有步骤完成。完成A02/A03后可安全弹出U盘，不自动删除检查目录或备份；新home也含私钥材料，需要本人一并保管登记。

当前T013为13条已验证子步骤、3条剩余工作；C09为两E解密及同U盘恢复，C10为第二轮保护和真实签名，C11为新签名备份同U盘恢复。C12为旧导出双E归档实际解密及四份已知副本限定逻辑退役；C13为实名管理员/本人首次改密及OTP、专用PKCE/签名MFA管理与临时令牌文件清理。第二独立介质暂无；真实身份数据恢复、旧凭据失效及共享退役/回切仍待，整卡未验收。T014规则方案见[六角色具体方案](../08-security/t014-six-role-rule-proposal.md)，当前分步导航与机器台账同源。

命令依据：[GnuPG精确指纹和`!`选择](https://www.gnupg.org/documentation/manuals/gnupg/Specify-a-User-ID.html)、[GnuPG 2.5.24状态协议DETAILS](https://github.com/gpg/gnupg/blob/gnupg-2.5.24/doc/DETAILS)、[Keycloak临时管理员退出](https://www.keycloak.org/server/bootstrap-admin-recovery)。这些技术说明不批准本项目的共享采用或正式业务规则。

最新旧副本状态：本人明确授权的四份已知旧导出已限定逻辑退役，详见[精确清单与边界](t013-known-signer-copy-disposition.md)。第二独立介质本人回复暂无；A01—A07适用操作已完成，不要求重复；继续准备A08/A09。

A07当前实际：四项精确范围已获本人批准并采用；首次改密/OTP及专用签名管理会话已验证，详见[实际采用进度](../00-project/validation/t013-named-admin-adoption-progress.json)和[本人回执](../00-project/validation/t013-owner-mfa-management-validation.json)。A01—A07已完成的动作不重复执行；A08/A09继续准备；控制台仅密码/单次错误OTP拒绝已由本人反馈通过。

本轮本人负向实测：徐昌胜反馈“仅密码不能进入控制台、单次错误OTP被拒绝”，见[本人负向反馈记录](../00-project/validation/t013-owner-mfa-negative-attestation.json)。这属于本人实测反馈，未独立关联服务器负向事件；正向专用MFA会话另有自动回执。已完成的登录不重复，实际身份备份恢复与bootstrap退役仍待。
