# T034-I02固定任务计划读口、ACL、RLS与锁契约

本说明绑定[本批精确源码与验证回执](../00-project/validation/t034-i02-integration-report.json)，属于当前Linux/py310研发隔离实现。0017为增量迁移，原0001—0016未修改；未向共享数据库执行。它不形成实际采用、权限ALLOW、任务创建或HTTP202。

## 固定签名

```sql
mt.task_create_plan_metadata(
  wanted_asset uuid, wanted_case uuid, wanted_scene text,
  wanted_policy_version text, wanted_modules text[], wanted_priority text
) RETURNS TABLE (...21列如下...)

mt.task_create_execution_plan(
  wanted_asset uuid, wanted_case uuid, wanted_scene text,
  wanted_policy_version text, wanted_modules text[], wanted_priority text,
  expected_revision uuid, expected_policy_sha256 text,
  expected_plan_sha256 text, expected_capability_sha256 text
) RETURNS TABLE (...9列如下...)
```

两个函数只接受精确请求asset/case/scene/policy_version/有序且非空无重复modules/priority。候选必须唯一；空或多个head、缺依赖行、过期、失活或摘要不符拒绝，不用LIMIT 1、默认DAG或任意handler路径。执行包装器对零行/多行归一拒绝。SQL不是HTTP接口。

### metadata的21列

| 列 | SQL类型 | 含义 |
| --- | --- | --- |
| `revision_id` | `uuid` | 精确当前不可变revision，非任意first |
| `mapping_id` | `text` | 映射身份 |
| `mapping_version` | `text` | 映射版本 |
| `authority_version` | `text` | 原登记权威版本；非实际批准证明 |
| `head_row_version` | `bigint` | 当前ACTIVE head行版本 |
| `policy_id` | `uuid` | 完整策略身份 |
| `policy_kind` | `text` | 策略种类；相同版本跨kind歧义拒绝 |
| `policy_version` | `text` | 请求精确策略版本 |
| `policy_sha256` | `text` | 原policy规范字节SHA-256 |
| `plan_id` | `text` | 计划身份 |
| `plan_version` | `text` | 计划版本 |
| `plan_sha256` | `text` | 原plan规范字节SHA-256 |
| `capability_id` | `text` | 能力声明身份 |
| `capability_version` | `text` | 声明版本 |
| `capability_sha256` | `text` | 原capability规范字节SHA-256 |
| `valid_from` | `timestamptz` | 采用映射有效起点 |
| `valid_until` | `timestamptz` | 采用映射有效终点，不替代Proof最小期限 |
| `recovery_generation` | `text` | 原revision声明恢复代际，须独立真实来源复核 |
| `validation_receipt` | `jsonb` | 闭合受限投影，见下表，非完整receipt |
| `required_capability_refs` | `jsonb` | 闭合完整声明引用，非当前可用/许可 |
| `current_state_facts` | `jsonb` | 闭合9组数据库观测，非ALLOW |

### execution的9列

| 列 | SQL类型 | 含义 |
| --- | --- | --- |
| `revision_id` | `uuid` | 与请求expected_revision精确一致 |
| `head_row_version` | `bigint` | 与最终当前head版本一致 |
| `policy_bytes` | `bytea` | 原规范policy字节 |
| `plan_bytes` | `bytea` | 原规范plan字节 |
| `capability_bytes` | `bytea` | 原规范capability字节 |
| `validation_receipt_bytes` | `bytea` | 原receipt字节，禁止jsonb::text替代 |
| `current_state_facts` | `jsonb` | 与CASE metadata相同的当前观测 |
| `valid_until` | `timestamptz` | 映射窗口终点 |
| `recovery_generation` | `text` | 原revision恢复代际 |

## 身份与事务边界

LOOKUP必须read-only、operation=createTask、lookup_kind=asset、lookup_id精确目标，以及真实actor/org/案件成员关系和参数资产归属。该支路没有行锁、不调用正文函数、不向调用者返回policy/plan/capability/receipt原文字节。完整handlers声明作为受限引用返回，不是状态证明。

CASE包装器必须先验证已绑定请求上下文、同一连接/根mutation授权、evidence精确actor/org/case/asset与独立A/B摘要；SQL另外核验CASE、read-write、当前case及精确请求适用性。PostgreSQL无法读取Python ContextVar，也未新增asset/request-digest GUC，因此SQL本身不声称证明Python根授权或请求摘要。CASE metadata通过固定execution函数取得相同锁和当前观测；execution同时要求expected_revision及三摘要精确匹配。

## 角色、ACL与拒写

| 内部角色或入口 | 实际权限与限制 |
| --- | --- |
| `mt_task_plan_lookup` | 沿用NOLOGIN/NOINHERIT/非SUPER/非BYPASS、非表owner；保持SELECT-only，无UPDATE ACL。metadata函数受限owner；完成安装后无人/业务账号membership，显式安装期间的严格临时例外见下文。 |
| `mt_task_plan_case_reader` | 新增同样受限的内部角色，非表owner；精确依赖列SELECT，只有media_asset/source_registry/policy_registry/task_plan_mapping_head的`UPDATE(row_version)`列ACL用于PG16 FOR SHARE。不是完全没有UPDATE ACL，也不是实际DML批准。 |
| CASE UPDATE策略 | 精确CASE/createTask/org/case的USING；`WITH CHECK(false)`，另加RESTRICTIVE UPDATE检查，防另一permissive policy通过OR放宽写入。INSERT/DELETE/TRUNCATE没有授予；4表另有最先执行的BEFORE STATEMENT SECURITY INVOKER触发器，case_reader无论是否命中行均以42501拒绝，防止语句级epoch副作用。 |
| 两固定函数 | SECURITY DEFINER，固定search_path=pg_catalog,mt,pg_temp，业务表均mt限定；REVOKE PUBLIC EXECUTE。runtime只有精确EXECUTE，不直接获得私有正文表SELECT或内部角色继承。 |
| manager/人 | 不增加实际采用或管理函数，不创建正式账号/授成员，不seed ACTIVE。测试ACTIVE和登录角色仅随机隔离自建夹具。 |

PG16锁定SELECT需要至少一列UPDATE权限，且适用SELECT和UPDATE USING；FOR SHARE本身不执行UPDATE WITH CHECK。故本实现明确区分列ACL和有效DML，真实受限角色测试同时验证锁成功与UPDATE/INSERT/DELETE/TRUNCATE拒绝，不能用迁移superuser成功当权限证明。[PostgreSQL16权限说明](https://www.postgresql.org/docs/16/ddl-priv.html)、[CREATE POLICY](https://www.postgresql.org/docs/16/sql-createpolicy.html)。

## 非超级迁移者的显式安装与撤权

非超级、非runtime的`mt` schema owner先按原0016规则完成旧迁移。0017转移两函数所有权前，管理员必须显式准备两私有角色，并仅给该精确schema owner临时成员：`INHERIT FALSE, SET TRUE, ADMIN FALSE`。0017拒绝其它成员、继承边、runtime成员或属性不符；它不向自己授角色，不RESET ROLE或提升为session_user。函数REVOKE/GRANT/COMMENT在转owner前完成，最后转为受限非表owner。管理员在成功或失败的finally交接中立即REVOKE并核验成员为0；GRANT不是随事务结束自动过期。隔离测试实际用原非超级连接执行0017，管理连接只做明确的临时安装准备及撤权；不可把整段SQL用superuser执行冒充非超级路径通过。共享安装仍未执行。

零行UPDATE也会触发语句触发器，RLS的WITH CHECK(false)只覆盖实际行写入，不能单独证明无副作用。原隔离RED真实复现4表未拒绝，其中head的epoch发生改变。现4表的`aaa_`语句级INVOKER拒写保护先于epoch触发器执行；SELECT FOR SHARE不触发DML拒写。此内部trigger函数不是第三个公开读口，PUBLIC/runtime和两reader的直接EXECUTE均撤销。

## 锁序与撤销

CASE先共享锁authorization epoch，然后精确asset/source FOR SHARE，再读取/锁精确policy与唯一当前head；不可变revision/material/object不为模拟动态事实加行锁。统一顺序与现有core ObjectFacts一致，不在asset/source之前先锁head/policy。锁保留到调用者事务commit/rollback；LOOKUP不锁。未知外部恢复代际、超时、死锁或任何必要事实未知均不能变成ALLOW。

head新增statement级epoch触发器，使INSERT/UPDATE/DELETE/TRUNCATE（包括同请求版本另一policy_id的ACTIVE head幻影插入）先受同一epoch排序；被持有的CASE epoch共享锁挡住。固定读取在锁后重新核对唯一head/revision/三摘要/窗口。该触发器不授予head管理权限或自动搬运/采用任何材料。未授任何现场运行路径。

## 三份闭合JSON投影

### validation_receipt

| 字段 | 类型 | 来源及限制 |
| --- | --- | --- |
| `sha256` | 小写SHA256 | 原revision.validation_receipt_sha256，原bytea摘要；不对jsonb::text回算 |
| `validator_id` | string(1..128)或null | 仅同名原字段满足类型和长度才投影，否则null |
| `validator_version` | string(1..128)或null | 同上 |
| `schema_id` | string(1..128)或null | 同上；不存在已批准语义Schema时不补值 |
| `schema_version` | string(1..128)或null | 同上 |

其余字段、完整receipt bytea不由metadata返回。字符串只是观测，不证明验证者可信、正式采用或许可成立。execution返回原bytea，包装器严格JSON/规范字节/原SHA及metadata投影对照。拒重复JSON键/非法UTF8，不以重新串化显示文本代替原签名/摘要输入。

### required_capability_refs

| 字段 | 类型 | 来源及限制 |
| --- | --- | --- |
| `capability_id` | string | 精确revision声明身份 |
| `capability_version` | string | 精确声明版本 |
| `capability_sha256` | 小写SHA256 | 原规范capability字节摘要 |
| `handlers` | 完整CapabilityManifest.handlers数组 | handler_id/version、release_id、code/package摘要、输入/输出Schema、license_ref、status_protocol_version及显式model_dependencies全部保留；只是声明 |

Python重建既有完整声明Manifest并严格校验Schema/规范SHA；不因为ACTIVE模型、license_ref或空模型依赖自动返回handler已发布、许可有效或available=true。CurrentCapabilityStateReader仍必须显式真实接入，默认None。

### current_state_facts

| 组及字段 | JSON类型/来源 |
| --- | --- |
| `asset.asset_id` | uuid-string |
| `asset.org_id` | uuid-string |
| `asset.case_id` | uuid-string |
| `asset.content_id` | uuid-string非空 |
| `asset.source_id` | uuid-string |
| `asset.kind` | text |
| `asset.object_ref.object_id` | uuid-string非空 |
| `asset.object_ref.version_id` | text非空 |
| `asset.object_ref.sha256` | 小写SHA256 |
| `asset.mime` | text |
| `asset.size_bytes` | integer |
| `asset.duration_ms` | integer|null |
| `asset.width` | integer|null |
| `asset.height` | integer|null |
| `asset.state` | text |
| `asset.version` | integer；media_asset.row_version |
| `asset.created_at` | UTC字符串 |
| `asset.mapping_version` | text非空 |
| `asset.sha256` | 小写SHA256 |
| `source.source_id` | uuid-string |
| `source.org_id` | uuid-string |
| `source.case_id` | uuid-string |
| `source.authorization_status` | text |
| `source.authorization_version` | text |
| `source.purpose` | text[] |
| `source.expires_at` | UTC字符串|null |
| `source.row_version` | integer |
| `policy.policy_id` | uuid-string |
| `policy.kind` | text |
| `policy.version` | text |
| `policy.status` | text |
| `policy.row_version` | integer |
| `case.case_id` | uuid-string |
| `case.status` | text |
| `case.row_version` | integer |
| `memberships[].membership_id` | uuid-string；按ID排序 |
| `memberships[].row_version` | integer |
| `memberships[].expires_at` | UTC字符串|null |
| `actor.user_id` | uuid-string |
| `actor.org_id` | uuid-string |
| `actor.enabled` | 实际boolean列 |
| `actor.row_version` | integer |
| `organization.org_id` | uuid-string |
| `organization.enabled` | 实际boolean列 |
| `organization.row_version` | integer |
| `head.revision_id` | uuid-string |
| `head.state` | text |
| `head.row_version` | integer |
| `generation.database_oid` | integer |
| `generation.epoch` | integer |
| `generation.policy_version` | text|null |
| `generation.policy_sha256` | SHA256|null |
| `generation.recovery_generation` | text|null |

所有对象ref/资产org/case及SHA/size必须同一真实对象匹配；缺行拒绝。时间投影固定UTC，允许微秒；不得放入mode、transaction ID、observed_at或locked等自然随阶段变化的值作为稳定事实。generation三个可空字符串仅是数据库观测，null或同值都不自证独立恢复权威。

## 0018：generation OID的增量类型修复

后续I03隔离连通检查实际取得metadata唯一行，但既有严格Python读口拒绝`generation.database_oid`：原0017将PostgreSQL `oid`值直接放入`jsonb_build_object`，CASE与LOOKUP两支路实际返回JSON字符串。新增两参数回归先直接读取固定SQL，再要求`type(database_oid) is int`；两支路均已实际出现该类型断言失败。这是数据库投影与既有内部整数契约不符，不是SQL超时，也不以修改Python正整数校验或测试夹具内容掩盖。

修复另增[0018_task_creation_generation_json.sql](../../backend/business_migrations/0018_task_creation_generation_json.sql)，原0017及0001—0016保持原字节和迁移摘要。0018只把两个固定函数各自唯一一处JSON实参从`v_generation.database_oid`改为`v_generation.database_oid::bigint`。`bigint`用于保留高于有符号32位整数上限的OID值；不把OID改为业务主键，不更换数据库代际，不改变epoch、有效期、拒绝规则、函数签名或21/9列结构。CASE metadata仍委托原execution路径；LOOKUP仍只读、无正文和行锁。

0018先检查两个固定签名的原正文SHA-256、唯一替换位置，以及预期受限owner、PL/pgSQL、SECURITY DEFINER、VOLATILE和固定search_path。两函数都完成预检后才允许替换，未知或已被篡改的正文/owner拒绝。安装前保存完整`pg_proc`元信息、注释及schema ACL观测；安装后要求除`prosrc`两处精确转换外全部函数元信息、owner、ACL、OID、search_path和注释保持原值，合法的NULL注释同样保留。该比较是与安装前观测值的守恒检查，不把任意未知元信息宣称为已获正式批准。

PostgreSQL 16的[CREATE FUNCTION说明](https://www.postgresql.org/docs/16/sql-createfunction.html)规定替换函数保持既有所有者和权限；[ALTER FUNCTION说明](https://www.postgresql.org/docs/16/sql-alterfunction.html)列明所有者切换及schema权限要求。本迁移仍以本节固定边界和实际非超级用户测试验证安装行为，文档链接不代替执行证据。

非超级迁移者仍须为精确`mt` schema owner，且不继承runtime。管理员按前节协议显式准备两私有角色的临时`INHERIT FALSE, SET TRUE, ADMIN FALSE`成员边；0018不创建或修改角色成员。迁移仅在本事务中临时给固定函数owner schema CREATE权限，分别切换至既有owner执行CREATE OR REPLACE，恢复原迁移者后撤回本次CREATE权限并核对schema ACL原值。成功或失败后，管理员仍须在finally交接中REVOKE临时成员并核验为0；成员GRANT不会因事务结束自动过期，不能留给runtime或业务账号。

版本化runner将0018及其迁移登记置于同一事务，预检、替换、元信息或权限核验任一步失败均须回滚；重放已登记的同摘要迁移应无操作。0018不新增或删除表、字段、索引、RLS策略、触发器或业务行，不seed ACTIVE，不改70张研发业务表及其967列，也不把研发目录与62表业务提案合并。新迁移测试另覆盖0017历史升级、元信息/既有行守恒、重放、非超级SET-only安装及撤权、正文/owner篡改拒绝、NULL注释和高位OID转换；**本节只记录实际RED及实现设计，不将尚未完成的测试登记为GREEN**。

该修复未向共享数据库执行，未形成真实采用、软件许可、独立恢复权威或HTTP202。原业务/权限/软件扫描门禁保持，最终迁移和创建事务验证须以本批精确源码的实际回执分别判定；不能由这两条类型RED或一处类型转换推定I03、I02整步或T034已完成。

## 未完成范围

原0017批次只完成受限SQL、观测包装器、专用有限事实端口及guard上下文接线的隔离工程子范围；本轮另有[I03原子创建组件候选](../03-development/t034-atomic-creation-service.md)，实际结果按其精确回执核验。仍不签发正式采用Proof、不挂载I04 createTask HTTP，不完成I02/I03/I05整步或T034整卡。model_task_version、真实采用/撤销authority、当前handler发布/许可/可用性、分类/用途权威、独立恢复来源和E04实际预算/期限仍待；明确negative按既有拒绝，unknown不填true。原100包锁、CI门禁、公共API/前端/路由保持；Python候选与算法继续暂缓。
