# T016 案件操作令牌数据库扩展

2026-10-21。本页说明 `0011_operation_token.sql` 及案件级签发、内部同事务消费的存储边界。适用当前 Linux／Miniforge py310／CPU 内部研发，Python候选继续暂缓。实现依据为[已批准实施计划](../03-development/t016-operation-token-implementation-plan.md)和[源任务T016](../../tasks/platform/T016.md)。本页不登记测试、CI通过或正式软件准入；实际结果以对应提交的执行证据为准。

## 1. 迁移范围与计数

本T016扩展采用的迁移为 [`backend/business_migrations/0011_operation_token.sql`](../../backend/business_migrations/0011_operation_token.sql)，不改0001—0010字节、原始初始化SQL或历史摘要。它扩展既有 `mt.operation_token`，不新增业务表：该表原15列增加12列后为27列，完整0011版本的业务目录为64表、861列。849是此前0010版本的列数；针对历史版本的验证仍须保留历史计数，不把所有旧断言统一替换为861。

这些计数描述应用到0011后的隔离数据库结构，不证明共享环境已采用迁移。**实例状态以2026-10-21交付记录区分**：[交付验证](../00-project/validation/development-delivery-validation.json)的`runtime_migrations`已记录新随机交付预览库应用0001—0011；该新业务API使用Linux回环14212，网关14213。原14202实例及其数据按[运行手册](../10-deployment/business-development-runbook.md)保留，旧共享库和原实例未因新目标创建而升级。此前“现有预览库未安装0011”的结论属于新目标创建前的实例观察，不应继续泛指新14212目标。

当前初始化[字典](data-dictionary.md)的62表825列与完整0011结构属于不同版本；历史0001固定62表824列，0002追加`duplicate_of`后为825列，0004/0008再增加身份及授权代际两表。[PPT前端更新记录](../00-project/validation/ppt-interface-alignment.json)明确数据库未变、后端payload仍为`8b7fc475b5a0e8c3e7687559a6f09b65e39e1373`。本轮后续0012候选仅属源码及隔离验证范围，不据此声称当前14212或共享库已采用。以上是既有证据的文档核对，不是本页新执行数据库查询；源码同步、进程启动、迁移采用与正式验收分别登记。不得为运行本页而向已有数据库执行初始化。

## 2. 新增12列的准确含义

数据库列为内部持久化绑定，公共请求或响应不会因此增加字段。除 `storage_version` 本身的 `NOT NULL` 外，其他新列允许历史行保留NULL；完整版本1记录由组合约束及触发器要求有效值，不能把“历史允许NULL”误解为新令牌可以缺绑定。

| 列 | PostgreSQL类型 | 版本1记录的含义与约束 |
| --- | --- | --- |
| `storage_version` | `smallint NOT NULL` | 升级时既有行为0；迁移后新记录默认1。0仅保留旧记录，不可签发、重放或消费；1须满足完整组合约束。 |
| `action` | `text` | 服务端明确动作。首批仅 `sealEvidence`，不按同purpose推断其他动作。 |
| `object_type` | `text` | 批准所指对象类型，首批仅 `task`；与批准行精确一致。 |
| `approval_version` | `bigint` | 签发时批准行的正 `row_version`；消费及提交前须仍一致。它不等于任务对象版本。 |
| `approval_policy_version` | `text` | 批准使用的业务规则版本，长度1—1024；与当前批准行一致，区别于权限快照版本。 |
| `permission_policy_version` | `text` | 签发授权证据的权限规则版本，长度1—1024且无首尾空白；消费必须匹配当前授权证据。 |
| `rule_version` | `text` | 显式 `(object_type,purpose,policy_version) → action/TTL` 提供方的规则版本；1—128字符，按迁移中的标识符正则限制。 |
| `recovery_generation` | `text` | 独立授权恢复代际，长度1—1024且无首尾空白；旧库恢复不能据旧行恢复旧代际的可用性。 |
| `key_id` | `text` | 独立HMAC密钥的非秘密标识，1—128字符，按迁移正则限制；不是密钥材料。 |
| `principal_sha256` | `text` | 当前actor、issuer、subject的规范摘要；64位小写十六进制。它不包含原JWT，也不能作为凭据使用。 |
| `request_sha256` | `text` | 规范请求、已验证完整批准详情和实际task关联来源快照的SHA-256；绑定对象、批准版本、run/result、决策清单及来源ID／授权版本／状态／用途／截止／行版本。64位小写十六进制，不是令牌摘要。 |
| `idempotency_key` | `text` | 本主体、本单位、本案件内的签发重试键，长度1—128；并非秘密恢复材料。 |

原有15列继续保留：`token_id/org_id/case_id/approval_id/actor_id/purpose/object_id/object_version/token_sha256/expires_at/consumed_at/created_at/updated_at/row_version/created_by`。其中 `token_sha256` 保存完整凭据的SHA-256；`expires_at` 为固定截止，`consumed_at` 为一次消费时刻，`row_version` 从1变为2。版本1要求案件非空、`created_by=actor_id`，批准和对象的ID／版本／用途须与当前批准行一致。

`operation_token_v1_binding` 对组合条件使用 `IS TRUE`，使SQL的NULL三值结果不能绕过版本1约束。唯一部分索引 `operation_token_retry_identity` 仅约束版本1的 `(org_id,case_id,actor_id,idempotency_key)`，保留旧数据并防止同范围重试另建令牌。

## 3. 凭据、摘要与幂等重放

公共签发入口仍是 `POST /api/v1/operation-tokens`，请求仍为 `approval_id/object_id/object_version/purpose`，必需 `Idempotency-Key`；响应仍为 `operation_token/expires_at/object_version`。结构以[唯一业务OpenAPI](../03-api/openapi.yaml)为准，未新增客户端actor、单位、案件、action或额外必需If-Match。UUID先规范化再用于比较与请求摘要。

服务使用独立密钥和域分离的HMAC-SHA256派生凭据。输入绑定令牌ID、actor／单位／案件、批准及其版本、对象类型／ID／版本、用途／动作、两类策略版本、规则版本、恢复代际、key_id、主体与请求摘要、幂等键、存储版本和创建／截止时间。凭据格式含公开的令牌ID及HMAC；公开ID、数据库摘要和元数据都不能单独作为凭据接受。

相同主体、案件、幂等键和请求摘要，在批准、授权、规则、密钥、代际、期限和未消费状态仍有效时，重建同一凭据并保留原截止，不新建第二条记录。不同摘要拒绝；过期、已消费或当前绑定失效的记录不能借重试重签、延长有效期。重放前仍重新核验当前事实。响应设置 `Cache-Control: no-store`。来源快照从同一Connection读取当前单资产task的实际asset_id→source_id关系；主来源替换或纯授权版本变化均改变绑定，提交前能看到本事务自身的来源变更，不只依赖另开连接的状态检查。

数据库不保存明文凭据；签发不把完整响应交给通用 `idempotency_record.response_ref`。日志、异常、审计详情、URL、Git及浏览器持久存储同样不应记录凭据。成功审计只记录允许的令牌记录标识与动作；拒绝路径不能声称在失败事务中已持久化成功审计。

## 4. 截止时间、密钥与恢复代际

签发截止为以下四者最早时间：

```text
expires_at = min(
  签发时刻 + 显式令牌规则TTL,
  批准截止,
  当前JWT主体截止,
  当前授权证据valid_until
)
```

当前对象授权证据通常只覆盖5秒，所以即使隔离测试规则返回60秒，实际凭据也通常不超过该5秒证据窗口。这是本批保守实现，不能将60秒或审批TTL1800秒登记为正式令牌有效期，也不能把5秒事实窗口泛称为所有作业的超时。重试和消费不续期；SQL消费使用实际 `clock_timestamp()`，不只使用事务起始的 `now()`。

规则与密钥均须显式注入；缺少时拒绝，不复用游标密钥、PoC令牌或身份签名密钥，也没有内置默认secret。密钥对象的repr不包含材料。**本批严格要求存储key_id及取回的材料与当前密钥一致**：轮换当前密钥后，旧凭据即使未到期也被拒绝；仅保留历史密钥并不会允许旧凭据继续使用，不实现宽限key ring。恢复后代际改变同样拒绝旧记录；不修改旧记录的代际以使其重新有效。

## 5. 同根事务、约束与审计

签发及内部消费复用当前T014授权与T015数据范围。案件由批准记录服务端解析，批准申请人须为当前主体；独立批准人员、当前来源用途、task/run/result及规则仍由既有批准链核验。

内部 `OperationTokens.consume(...)` 接收调用方已打开的Connection；根事务必须属于该服务的同一Database实例、同一连接、同一actor／单位／案件，并具有该精确action、对象及版本的变更授权。签发权限不是动作执行权限。内核不打开第二个事务，不自行commit，也没有公共消费端点。

消费先无锁定位、按既定顺序共享锁定批准和task，再锁定令牌并核对完整凭据与绑定，再条件更新 `consumed_at` 和 `row_version`，同连接追加消费审计；根提交前重新核验批准、主体、规则、当前key、代际和期限，并保留既有最终权限栅栏。业务异常须传播出根事务，使消费、业务写入和成功审计一起回滚；调用者不得自行提前commit或吞掉应回滚的业务异常。

SQL触发器保留旧记录拒绝、actor／单位／案件绑定、初始状态、原绑定不可变、精确action消费、已消费拒绝、当前批准版本与实际截止检查。固定scope目录仅增加所需签发／内部动作及approval／task定位，不开放 `operation_token` 通用LOOKUP或任意表查询；原RLS与最小角色边界继续适用。

## 6. 真实消费者与迁移采用的保留条件

当前 `sealEvidence` 仅登记内部范围边界，**没有挂载真实HTTP封存消费者**。合成动作授权和合成副作用只说明内核调用边界，不证明实际证据封存、真实人员授权或正式验收。现有 `AuditExport` 无operation_token字段，本批未改其公共契约，也未将其现有真实导出路径接入本内核。

提交前仍要求批准指向的task原版本与run/result快照有效；若业务写入本身改变该task版本，当前批准重验会失败并回滚。本批适用边界是保留该批准目标快照、追加独立产物或明确合成副作用；后续真实消费者必须分别核定原批准快照和最终业务状态，不能据此泛称支持任意同事务写入。

正式共享采用另需制品与配置、真实提供方、备份恢复、升级窗口和采用决定。回退以停用新能力并保留版本化记录、向前修复为原则，不撤掉0011使旧代码重新接受legacy或旧代际凭据。更多人员职责与消费者前置见[安全边界](../08-security/t016-operation-token-boundaries.md)。
