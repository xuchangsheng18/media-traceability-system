# T034 实名身份、单位与案件只读核验

2026-10-23。按已批准 I01—I05 和 E01/E03 继续实施；本批完成管理工具的只读盘点部分，未实施采用激活、许可或分类登记。开发负责人及指定复核人徐昌胜的责任登记保持；程序观察不代替本人复核或业务授权。精确源码与 Linux 实测见[回执](../00-project/validation/t034-identity-inventory-report.json)。

## 已实现的边界

`backend/business_app/task_creation_identity_inventory.py` 在同一 REPEATABLE READ、READ ONLY 事务中读取数据库身份及精确目录关系。固定参数化 SQL 同时绑定 issuer/sub、user_id、org_id、case_id，核对身份、用户、单位启用状态、身份有效期/撤销、ACTIVE 案件及当前案件成员关系；不枚举其他案件、不选第一条可见映射。输出包含数据库名/OID、观察时间和相关行版本，不能缓存为运行授权证明。

登录必须已有 `mt_directory_manager` 成员资格，且不是超级用户、BYPASSRLS、CREATEROLE、CREATEDB 或 REPLICATION 角色；拒绝 runtime、广泛数据/服务器文件权限以及通过 SET ROLE 冒用其他登录。工具不创建账号、不授予权限，不增加迁移或公开 HTTP 接口。

`scripts/task_creation_identity_inventory.py` 只接收仓库外私有 JSON 文件和全新输出目录。配置严格六字段：`database_dsn`、`issuer`、`subject`、`user_id`、`org_id`、`case_id`。UUID 必须是精确规范形式，数据库目标仍受现有 Database 的业务库限制。Linux 私有文件须为当前用户所有且 0400/0600，保管目录 0700，拒绝重复键、额外字段、链接及不安全祖先目录。配置和结果均不能提交公开仓库。

从任意工作目录启动时不依赖继承 PYTHONPATH；使用现有 py310，在实际部署源码目录执行：

```text
/opt/conda/glwy/envs/py310/bin/python scripts/task_creation_identity_inventory.py --private-configuration <仓库外已有私有配置文件> --output <仓库外尚不存在的私有结果目录>
```

这只是命令格式，尖括号内必须替换实际路径；本批没有创建可直接运行的真实配置。请勿把 DSN、口令或完整私密配置发到对话中。结果 `identity-directory-observation.json` 以 0600 独占创建，目录 0700；存在则停止，不覆盖。终端仅输出固定状态及摘要，不输出身份、连接串和内部错误。

匹配成功仅表示 `IDENTITY_MEMBERSHIP_OBSERVED_NOT_ADOPTED`，退出码0；缺少当前精确关系为 `DIRECTORY_BINDING_NOT_CURRENT`，退出码1；权限、配置或数据库异常统一拒绝。两者均不签发 Proof，不创建 ACTIVE 映射。`external_authentication_verified`、`adoption_authorized`、`license_verified`、`classification_verified`、`active_mapping_created`、`database_written` 始终为 false。观察时间不是有效期，不能通过不断重跑盘点工具延长采用或代际依据。

## 实际验证

验证仅在 Linux 原 py310 与新建随机隔离库执行；Windows 只编辑及同步。42项新增测试和原身份目录28项组成70项回归通过，覆盖精确范围错配、禁用/撤销/过期、SQL注入文本、低权限及高权限角色拒绝、SET ROLE、只读事务、私有文件和独占输出。组件缺失及独立启动失败均先复现后修复；独立审查提出的角色和私有配置负例已补齐。

Ruff/格式通过，现有类型入口301文件通过；资料文本检查及保留报告写入的秘密扫描通过。原业务及权限故意失败探针均按预期退出1。测试使用自建身份夹具与临时管理角色，不能当真实人员/案件映射或共享环境权限。

上一批 Linux 完整业务回归已取得 TIMEOUT 终态：上限仍1800秒，partial JUnit 观察873项、0失败，complete=false；这不是整套通过。组清理与数据库清理未验证，不宣称超时根因已修复。当前 GitHub 83c492fa 的精确 CI 状态另见本批回执，不借用旧提交成绩。

## 仍需落实的真实依据

1. 由管理员提供已有实名身份映射的私有配置路径：实际 issuer/sub、业务 user/org/case，以及已受限的管理登录。没有则先按现有受控身份目录流程建立真实研发空间，不用测试 UUID 或 GitHub 姓名代填。本批没有操作共享目录。
2. 后续受控采用工具须登记实际采用/撤销责任、依据版本/摘要、精确材料及期望 head 版本、有效期和范围；本批盘点不能代替该记录。
3. handler 的实际发布制品、许可/归属证据、当前可用状态和撤销维护；资料分类须有逐资产/来源及版本、内部用途、有效期、依据与实际复核。尚未形成的登记关系及只读适配器继续按 E03 隔离实现，不接受自由 true 标志。
4. 独立代际权威文件的最终服务器路径、保管/更新负责人和恢复后数据库 OID/代际重新绑定流程；不能从恢复库自证或自动续期。

本批无需用户安装、重启或迁移共享环境。原100包锁、CI门禁、算法及 Python 候选暂缓不变；T034 保持4条已证子步骤/4组剩余，170任务的154条已证/622组剩余及整任务验收0项不因组件测试增加而改写。下一批继续受限采用、许可/分类记录与真实提供方组合，仍无默认 ACTIVE。
