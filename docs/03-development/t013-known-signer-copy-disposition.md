# T013 已知旧签名导出副本处置清单

2026-10-20。适用同一单位内部研发；不批准安装、真实服务切换或整卡验收。以下是已实际核对的已知位置，不声称已扫描全盘、聊天备份、快照或不可见副本。

## 已通过的恢复保障

- 第二轮新口令保护已改变，公开指纹仍为C2F06E6116BDE369EE835C5D00AC4AAE1EB66C2D。
- 真实固定文字签名、仅公钥精确验签及篡改拒绝通过。
- 第二轮新保护导出已按摘要复制到U盘，导入新home后实际签名及仅公钥独立复验通过。
- 两把恢复E子密钥在原home和从备份导入的同U盘新home均实际解密通过。

证据：[签名与新备份限定实核](../00-project/validation/t013-reprotected-signer-owner-validation.json)、[两E限定实核](../00-project/validation/t013-recovery-subkeys-owner-validation.json)。同U盘恢复不是第二独立介质/异地恢复。

## 四份旧副本：已按明确授权限定逻辑退役

| 位置 | 精确路径 | 原因 |
| --- | --- | --- |
| Linux 原导出 | `/workspace/glwy/runtime/media-traceability-system/identity-custody/private-backups/backup-signer-secret.asc` | 对应先前已暴露口令 |
| Linux 第一轮更换导出 | `/workspace/glwy/runtime/media-traceability-system/t013-bootstrap-20261019/signer-protection-20261019T140715Z-2464a8/backup-signer-secret-reprotected.asc` | 第一轮新口令随后亦误发 |
| U盘 原导出 | `G:\公安厅项目密钥\private-backups\backup-signer-secret.asc` | 与Linux原导出摘要一致 |
| U盘 第一轮更换导出 | `G:\公安厅项目密钥\private-backups\backup-signer-secret-reprotected-20261020.asc` | 与Linux第一轮更换导出摘要一致 |

四份都是受保护私钥导出，不是公钥。口令更换不会追溯改变旧文件。已核对两组各3486字节及精确副本关系；私钥内容/私有导出摘要不入公开报告。

## 已准备双E外层加密归档

两个不同旧版本已分别用两把恢复公钥精确子指纹加密，公钥固定摘要及完整指纹核对；外层为AES256/OCB。U盘归档目录为 `G:\公安厅项目密钥\signer-old-exports-20261020T035359Z-ad9d9e`，Linux受限目录为 `/workspace/glwy/runtime/media-traceability-system/identity-custody/signer-old-exports-20261020T035359Z-ad9d9e`，两端密文摘要一致；无恢复私钥上传、无旧导出覆盖。

归档文件是`original-export.asc.gpg`和`first-reprotected-export.asc.gpg`。本人已完成两份归档实际解密及内存中原导出精确摘要核对；助手已核验两个实际状态文件的完整恢复指纹、AES256/OCB、完成标志、密文摘要及安全回执。验证目录只有状态/结果，无解封旧导出文件；没有由助手解锁或读取口令。本人核验脚本在本机修订成果目录`T013_旧导出加密归档验证_20261020.py`，只在内存核对，不显示/落盘解封后的旧导出。此步骤使用U盘恢复密钥口令，不是Linux签名新口令。

## 已执行的限定退役范围

本人明确回复“确认仅退役清单四份旧导出”后，已对上表四个精确旧文件做逻辑退役删除，保留双E外层加密归档、当前活动签名home、第二轮新导出、U盘第二轮新导出/已恢复home、公钥、恢复主密钥/两E、恢复备份及所有吊销材料。不会删除目录、递归扫描后自动删除，或匹配通配符删除。

执行前再次按精确摘要、非符号链接、归属及边界核验；任一变化即停。Linux和Windows分别用本系统工具处理，不跨Shell构造删除命令。本次已有本人明确确认；实核Linux两份及U盘两份均不存在，新备份/活动密钥/加密归档保留不变。不得据此扩大删除其他文件。

普通文件删除不证明SSD/FAT32/快照/备份的底层数据安全擦除，也不证明过去没有泄露私钥。若发现私钥材料本身曾外泄，需要重新评估替换密钥及对旧签名的信任，不能只靠换口令或删文件宣称闭环。

## 仍待的T013事项

第二独立离线介质/设备、与离线私钥相容的真实身份备份恢复、恢复后旧会话/密钥失效、共享bootstrap退役/回切及实际验收仍单列。本人首次改密/OTP和专用签名MFA管理会话已核实，见[实际回执](../00-project/validation/t013-owner-mfa-management-validation.json)。软件准入和Python候选暂停状态保持。

依据：[GnuPG精确指纹选择](https://www.gnupg.org/documentation/manuals/gnupg/Specify-a-User-ID.html)、[GnuPG状态输出及算法选项](https://www.gnupg.org/documentation/manuals/gnupg/GPG-Esoteric-Options.html)。实际元数据见[已知副本与归档观察](../00-project/validation/t013-known-signer-copies-review.json)。

本人已回复第二独立离线介质“否”，登记暂无，保持待落实；不重复要求本批已经完成的GPG步骤。
