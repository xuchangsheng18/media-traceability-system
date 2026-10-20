# T013 徐昌胜本人接管、密钥验证与恢复操作清单

2026-10-20。适用同一单位内部 Linux／py310／CPU 研发。徐昌胜为开发负责人、身份管理员、密钥保管人及指定复核人。人员指定不代替实际登录、密码/MFA、签名、恢复或验收。本清单按当前实际文件和工具参数整理；**本轮没有替你执行私钥操作、创建实名账号、停服务或删除bootstrap。** Python 3.13/3.12候选继续暂缓。

先看顺序：**A01只读核对 → A02两把恢复子密钥解密 → A03从恢复私钥备份建立新home → A04签名密钥保护决定 → A05真实签名及精确验签 → A06签名备份恢复 → A07本人改密/MFA与管理工具 → A08真实身份备份/隔离恢复 → A09受控退役/回切 → A10实际复核登记。** A01—A03可先做；A04未改变原决定时，A05/A06的正式保护闭环保持未完成；A07涉及共享配置的显式写入须单独核对前置及确认范围，A08/A09目前不能直接执行。

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
    (Join-Path $KeyRoot 'private-backups\backup-signer-secret.asc'))) {
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
        if (($StatusText -notmatch $KeyPattern) -or ($StatusText -notmatch '(?m)^\[GNUPG:\] DECRYPTION_OKAY(?:\s|$)') -or ($StatusText -notmatch '(?m)^\[GNUPG:\] GOODMDC(?:\s|$)')) { throw '未证明精确子密钥解密及完整性，停止' }
        Write-Output ('PASS_DECRYPT_EXACT_SUBKEY_' + $SubFpr)
    }
    & $GpgConf --homedir $HomePath --kill gpg-agent
    if ($LASTEXITCODE -ne 0) { throw '结束时代理缓存清理未确认' }
}
Test-RecoverySubkeys -HomePath $KeyHome -Prefix 'original'
```

GPG弹出口令框时由本人输入**恢复密钥口令**，不是Linux签名口令、SSH密码或指纹。如果取消、超时、`No secret key`或摘要/状态不符，停止，只回报错误文字。每个密文只对应一把子密钥，必须有两条不同的`PASS_DECRYPT_EXACT_SUBKEY_...`，只解开包含两收件人的同一个密文不能证明两把都可用。状态条件按本项目现有固定密文与GnuPG版本编制，未来算法/封装变化应重新核验，不能随意去掉完整性断言。

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

## A04：Linux签名密钥保护和旧副本（需要本人决定，当前暂缓）

实际签名口令曾出现在对话中，随后你选择保留原配置继续内部研发；本轮沿用这一决定，没有代输、改口令、吊销、删除或恢复已暂停的真实签名入口。当前脚本实际返回`SIGNING_SUSPENDED_OWNER_PROTECTION_CHANGE_AND_OLD_BACKUP_REVIEW_REQUIRED`并退出1，不能反复运行它期待成功。

若选择完成正式保护闭环，可沿用已准备的交互更换脚本，由本人在SSH内部GPG口令框输入旧口令并设定**全新、非空、未出现在对话中的口令**；下面这条是条件步骤，当前暂缓决定未改变时不要执行：

```powershell
ssh -tt glwy@172.16.58.179 "bash /workspace/glwy/runtime/media-traceability-system/t013-bootstrap-20261019/signer-protection-20261019T140715Z-2464a8/change-existing-signer-passphrase-once.sh"
```

成功时应出现`PASS_SIGNER_PASSPHRASE_CHANGE_AND_NEW_PROTECTED_EXPORT_STRUCTURE_ONLY`及`OLD_EXPORTS_STILL_REQUIRE_DISPOSITION_AND_NEW_BACKUP_RESTORE_TEST`。**仅该标记不代表真实签名、旧备份处置或独立恢复完成。** 新导出路径须由后续只读核验取得再传输并核对，不自行猜文件名。

旧副本至少包括Linux的`identity-custody/private-backups/backup-signer-secret.asc`和U盘同名文件。更换活动口令不会改变它们；新备份实测前保留隔离，登记全部已知副本。后续明确重新加密/隔离/退役方式后才执行，不能无恢复保障地删除，也不能宣称FAT32普通删除等于安全擦除。备份导出在本地目录的保护方式和独立介质仍须落实。

## A05：真实签名和精确验签（A04之后，由本人操作）

完成保护、新导出和公开指纹复核后，在自己的交互SSH终端操作。签名只针对A02的固定无敏感测试文字，不签真实业务结论；使用新独立验证目录，**不绕过之前暂停的签名脚本，不代输口令**。以下是后续技术步骤，当前A04未完成时不执行。

```sh
cd /workspace/glwy/projects/media-traceability-system
umask 077
SignerHome=/workspace/glwy/runtime/media-traceability-system/identity-custody/signer-gnupg
SignerFpr=C2F06E6116BDE369EE835C5D00AC4AAE1EB66C2D
Probe=/workspace/glwy/runtime/media-traceability-system/t013-bootstrap-20261019/gpg-public-probes-20261019T105539Z-9b130a/key-check.txt
SignDir=$(mktemp -d /workspace/glwy/runtime/media-traceability-system/identity-custody/sign-test-XXXXXXXX) || exit 1
export GPG_TTY=$(tty)
case "${TERM:-dumb}" in ''|dumb) export TERM=xterm ;; esac
gpgconf --homedir "$SignerHome" --kill gpg-agent || exit 1
gpg --homedir "$SignerHome" --no-options --local-user "${SignerFpr}!" --armor --output "$SignDir/key-check.txt.asc" --detach-sign "$Probe" || exit 1
mkdir -m 700 "$SignDir/public-verify" || exit 1
gpg --homedir "$SignDir/public-verify" --no-options --import /workspace/glwy/runtime/media-traceability-system/identity-custody/public/backup-signer.asc || exit 1
gpg --homedir "$SignDir/public-verify" --no-options --status-fd 1 --verify "$SignDir/key-check.txt.asc" "$Probe" > "$SignDir/verify.status" || exit 1
if ! grep -Eq "^\[GNUPG:\] VALIDSIG ${SignerFpr} " "$SignDir/verify.status"; then
  echo SIGNER_FINGERPRINT_NOT_CONFIRMED
  exit 1
fi
gpgconf --homedir "$SignerHome" --kill gpg-agent || exit 1
echo PASS_REAL_SIGNER_DETACHED_SIGNATURE_AND_EXACT_VERIFICATION
printf 'PUBLIC_TEST_DIRECTORY=%s\n' "$SignDir"
```

必须同时满足GPG退出0和`VALIDSIG`完整指纹匹配，不能只看“Good signature”或名字。另做篡改测试时只复制该无敏感测试文字到新文件，修改后验签必须非0；不得修改原测试文字、私钥或业务文件。此成功标记仅证明测试签名，不证明旧备份已退役或身份数据恢复。

## A06：签名私钥备份恢复与独立介质（需A04/A05成果）

1. 先只读核验A04新受保护导出的实际路径、公钥不变、保护结构、传输摘要；复制到U盘**新文件**，不覆盖旧备份。只复制受保护导出和公钥，不传口令。
2. 在受保护离线介质上新建空GPG home，导入核验后的新备份；杀掉该新home自己的代理缓存后，用同一无敏感测试文字做签名，再在只有公钥的另一新home精确验证指纹及篡改拒绝。口令只由本人在本机GPG提示框输入；不把恢复home或明文私钥上传Linux。
3. G盘内新目录只是隔离home验证；要登记独立介质恢复，还需另一实际介质/设备，以及核对副本摘要、重新导入/签名/验签证据。当前未确定第二介质，不预填路径或PASS。
4. 恢复吊销材料只验证受保护副本的可读性与指纹，不把吊销证书导入活动home，也不为测试撤销仍在使用的密钥。若需要解封吊销材料，另提供不落明文/不激活的受控步骤，不能在FAT32留下原始吊销证书。

A06先等A04实际新导出路径再填精确命令，避免误用仍受旧口令保护的副本。不要自行执行历史`--export-secret-keys`覆写已有文件。

## A07：实名管理员首次改密、MFA和工具接管（条件满足后由本人操作）

管理账号登录名已确认 `xuchangsheng`；尚未证明已创建。Keycloak master管理员与六个业务角色无自动继承。先由助手只读检查共享现状、准入/配置前置和维护范围，再确认下列共享显式写入范围；这些`--apply`命令不是本次文档同步已经执行的动作。

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
6. 只有`signed_mfa_management_session=true`、本人首次动作完成及负向验证证据齐全，才能分别登记“本人管理会话已验证”。bootstrap仍存在时如实登记，不标整卡完成。当前300秒管理会话不因权限方案审批TTL建议改变。

准确CLI参数见[管理工具替代](t013-bootstrap-management-replacement.md)和[身份运维手册](../10-deployment/keycloak-identity-runbook.md)。当前阶段不要先删除bootstrap。

## A08：真实身份备份与离线私钥兼容恢复（需要新增实施方案，当前不能直接执行）

现有`python -m scripts.identity.backup`参数为`--recipient/--output/--gpg-home/--signing-fingerprint`，可签名后流式加密数据库、私密配置和CA恢复材料；现有`restore`还要求**Linux本地含解密私钥的GPG home**。你已确定恢复私钥留U盘，所以**不能上传私钥来迁就当前恢复入口，也不能把合成恢复测试当作真实保管方案通过**。

需要下一批形成并验证：离线端校验密文摘要及精确签名 → 本人GPG解密 → 经受控加密通道流入服务端新隔离数据库/卷；不落明文dump，不传恢复私钥；每段管道退出值、断流/篡改/错误签名/错误目标拒绝和清理均实测。Windows PowerShell 5的普通管道不能直接假定二进制无损；传输方案未验收前不给一条表面可用的真实库恢复命令。

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

当前T013保持8条已验证子步骤、3条剩余工作；本清单只是R01/R02内的具体操作准备，不增加真实密钥验证完成数。T014规则方案见[六角色具体方案](../08-security/t014-six-role-rule-proposal.md)，当前分步导航与机器台账同源。

命令依据：[GnuPG精确指纹和`!`选择](https://www.gnupg.org/documentation/manuals/gnupg/Specify-a-User-ID.html)、[GnuPG 2.5.24状态协议DETAILS](https://github.com/gpg/gnupg/blob/gnupg-2.5.24/doc/DETAILS)、[Keycloak临时管理员退出](https://www.keycloak.org/server/bootstrap-admin-recovery)。这些技术说明不批准本项目的共享采用或正式业务规则。
