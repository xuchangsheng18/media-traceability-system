# 数据字典与字段来源

版本0.4-review，2026-10-12，NOT_FROZEN。当前62张表、824个字段。字段含义是本项目工程提案；与源设计、机器契约、数据库约束和实际验证分开登记。

## 使用方法

每行同时解释字段、类型、可空性、默认值、业务含义和来源。默认值不等于允许省略：插入触发器仍可能拒绝不完整内容。NULL不等于0、空字符串或空数组；主键隐含NOT NULL。列级CHECK、UNIQUE、表级复合外键及触发器需要一起阅读。

业务总体依据为[DES-001 V1.4](../_converted/revision/项目总体设计方案_技术修订版V1.4.md)§8.3—8.5及相应安全、模型和业务章节。该总体依据不宣称Word已逐字定义每个扩展列；精确工程定义为table-catalog JSON Pointer，接口对应位置列为OpenAPI JSON Pointer，SQL位置记录在field-provenance。新增首发约束见[first-source-ranking.md](first-source-ranking.md)。

[field-provenance.json](field-provenance.json)包含每个字段的可空性、默认表达式、实际外键、SQL行号与API结构位置。内部字段没有外部接口时明确登记，不给一个无法定位的“来源契约”。

TIMESTAMPTZ存储时间点、按会话时区显示；JSONB不自动验证应用Schema；RLS不防超级用户且认证上下文须可信；updated_at及row_version若无触发器由应用维护。官方机制与本项目选择见[database-design-references.md](database-design-references.md)。

## 表目录

- [organizations 单位目录](#organizations)
- [users 用户与认证主体](#users)
- [roles 角色目录](#roles)
- [permissions 权限目录](#permissions)
- [user_roles 用户角色绑定](#user_roles)
- [role_permissions 角色功能权限映射](#role_permissions)
- [cases 案件隔离域](#cases)
- [case_membership 显式案件授权](#case_membership)
- [source_registry 来源与用途授权](#source_registry)
- [content_item 逻辑内容对象](#content_item)
- [object_version 对象版本与摘要清单](#object_version)
- [media_asset 原始或派生媒体](#media_asset)
- [asset_lineage 多父对象血缘](#asset_lineage)
- [upload_session 上传会话](#upload_session)
- [upload_part 分片接收与校验](#upload_part)
- [import_job 批量清单导入作业](#import_job)
- [import_item 逐条导入结果](#import_item)
- [idempotency_record 主体请求摘要幂等](#idempotency_record)
- [policy_registry 标签阈值流程保留等策略](#policy_registry)
- [analysis_task 分析任务当前投影](#analysis_task)
- [task_run 任务运行历史](#task_run)
- [task_result 结果版本快照](#task_result)
- [task_node_run 节点尝试与租约](#task_node_run)
- [task_event 任务状态事件](#task_event)
- [outbox_event 事务发件箱](#outbox_event)
- [event_receipt 消费去重记录](#event_receipt)
- [shot 镜头时间区间](#shot)
- [keyframe 关键帧](#keyframe)
- [text_segment OCR ASR字幕原文](#text_segment)
- [model_registry 模型版本与许可引用](#model_registry)
- [model_evaluation 不可覆盖评测记录](#model_evaluation)
- [model_release 模型发布包](#model_release)
- [index_registry 索引版本不混向量](#index_registry)
- [feature 模型特征元数据](#feature)
- [evidence_item 证据事实版本](#evidence_item)
- [risk_finding 风险候选发现](#risk_finding)
- [tamper_finding 疑似篡改发现](#tamper_finding)
- [finding_evidence 发现与证据多对多](#finding_evidence)
- [task_evidence 任务证据引用](#task_evidence)
- [search_job 异步检索任务](#search_job)
- [source_match 同源或片段映射候选](#source_match)
- [content_cluster 高可信整内容簇](#content_cluster)
- [cluster_member 簇成员整内容证据](#cluster_member)
- [first_source_candidate 首发候选及覆盖范围](#first_source_candidate)
- [propagation_node 传播图节点](#propagation_node)
- [propagation_edge 显式推断传播边](#propagation_edge)
- [claim 结构化主张与来源](#claim)
- [claim_evidence_relation 主张证据关系](#claim_evidence_relation)
- [approval_request 按目的独立审批申请](#approval_request)
- [approval_decision 审批历史决定](#approval_decision)
- [operation_token 一次性确认授权记录](#operation_token)
- [review_record 业务复核事实](#review_record)
- [review_evidence 复核证据引用](#review_evidence)
- [evidence_package 固化证据包版本](#evidence_package)
- [package_item 固化包版本引用](#package_item)
- [report 报告生成与下载状态](#report)
- [report_evidence 报告证据引用](#report_evidence)
- [feedback_request 纠错训练用途申请](#feedback_request)
- [dataset_version 数据版本元数据不存真实样本](#dataset_version)
- [audit_event 追加式审计事实](#audit_event)
- [audit_export 审计导出作业](#audit_export)
- [first_source_ranking 首发排序不可变结果快照](#first_source_ranking)

<a id="organizations"></a>
## organizations 单位目录

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| org_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/organizations/columns/org_id`；[SQL](initial-schema.sql) `mt.organizations.org_id`；内部字段，无外部API映射 |
| name | text | 否 | 无 | NOT NULL | 名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键 | [工程定义](table-catalog.json) `/organizations/columns/name`；[SQL](initial-schema.sql) `mt.organizations.name`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/organizations/columns/created_at`；[SQL](initial-schema.sql) `mt.organizations.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/organizations/columns/updated_at`；[SQL](initial-schema.sql) `mt.organizations.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/organizations/columns/row_version`；[SQL](initial-schema.sql) `mt.organizations.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/organizations/columns/created_by`；[SQL](initial-schema.sql) `mt.organizations.created_by`；内部字段，无外部API映射 |

表级约束：

- 无额外表级约束；仍须查看列级主键和唯一性。

<a id="users"></a>
## users 用户与认证主体

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| user_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/users/columns/user_id`；[SQL](initial-schema.sql) `mt.users.user_id`；[API](../03-api/openapi.yaml) `/components/schemas/CurrentUser/properties/user_id` (getCurrentUser) |
| org_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.organizations(org_id) | 记录所属单位标识；单位授权范围由服务端认证上下文确定 | [工程定义](table-catalog.json) `/users/columns/org_id`；[SQL](initial-schema.sql) `mt.users.org_id`；[API](../03-api/openapi.yaml) `/components/schemas/CurrentUser/properties/org_id` (getCurrentUser) |
| subject | text | 否 | 无 | NOT NULL UNIQUE | 来自批准身份源，开发适配器另存密码散列，不设默认密码 | [工程定义](table-catalog.json) `/users/columns/subject`；[SQL](initial-schema.sql) `mt.users.subject`；内部字段，无外部API映射 |
| enabled | boolean | 否 | false | NOT NULL DEFAULT false | 认证主体是否启用；false禁止建立有效业务身份，true仍需核验角色与案件授权 | [工程定义](table-catalog.json) `/users/columns/enabled`；[SQL](initial-schema.sql) `mt.users.enabled`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/users/columns/created_at`；[SQL](initial-schema.sql) `mt.users.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/users/columns/updated_at`；[SQL](initial-schema.sql) `mt.users.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/users/columns/row_version`；[SQL](initial-schema.sql) `mt.users.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/users/columns/created_by`；[SQL](initial-schema.sql) `mt.users.created_by`；内部字段，无外部API映射 |

表级约束：

- 无额外表级约束；仍须查看列级主键和唯一性。

<a id="roles"></a>
## roles 角色目录

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| role_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/roles/columns/role_id`；[SQL](initial-schema.sql) `mt.roles.role_id`；内部字段，无外部API映射 |
| code | text | 否 | 无 | NOT NULL UNIQUE | 稳定业务编码，供权限检查或角色绑定使用；显示名称变化不应改变该编码 | [工程定义](table-catalog.json) `/roles/columns/code`；[SQL](initial-schema.sql) `mt.roles.code`；内部字段，无外部API映射 |
| description | text | 否 | 无 | NOT NULL | 该目录条目的中文职责或权限说明，不用于替代机器权限编码 | [工程定义](table-catalog.json) `/roles/columns/description`；[SQL](initial-schema.sql) `mt.roles.description`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/roles/columns/created_at`；[SQL](initial-schema.sql) `mt.roles.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/roles/columns/updated_at`；[SQL](initial-schema.sql) `mt.roles.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/roles/columns/row_version`；[SQL](initial-schema.sql) `mt.roles.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/roles/columns/created_by`；[SQL](initial-schema.sql) `mt.roles.created_by`；内部字段，无外部API映射 |

表级约束：

- 无额外表级约束；仍须查看列级主键和唯一性。

<a id="permissions"></a>
## permissions 权限目录

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| permission_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/permissions/columns/permission_id`；[SQL](initial-schema.sql) `mt.permissions.permission_id`；内部字段，无外部API映射 |
| code | text | 否 | 无 | NOT NULL UNIQUE | 稳定业务编码，供权限检查或角色绑定使用；显示名称变化不应改变该编码 | [工程定义](table-catalog.json) `/permissions/columns/code`；[SQL](initial-schema.sql) `mt.permissions.code`；内部字段，无外部API映射 |
| description | text | 否 | 无 | NOT NULL | 该目录条目的中文职责或权限说明，不用于替代机器权限编码 | [工程定义](table-catalog.json) `/permissions/columns/description`；[SQL](initial-schema.sql) `mt.permissions.description`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/permissions/columns/created_at`；[SQL](initial-schema.sql) `mt.permissions.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/permissions/columns/updated_at`；[SQL](initial-schema.sql) `mt.permissions.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/permissions/columns/row_version`；[SQL](initial-schema.sql) `mt.permissions.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/permissions/columns/created_by`；[SQL](initial-schema.sql) `mt.permissions.created_by`；内部字段，无外部API映射 |

表级约束：

- 无额外表级约束；仍须查看列级主键和唯一性。

<a id="user_roles"></a>
## user_roles 用户角色绑定

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| user_role_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/user_roles/columns/user_role_id`；[SQL](initial-schema.sql) `mt.user_roles.user_role_id`；内部字段，无外部API映射 |
| user_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 用户与认证主体标识，指向users.user_id | [工程定义](table-catalog.json) `/user_roles/columns/user_id`；[SQL](initial-schema.sql) `mt.user_roles.user_id`；[API](../03-api/openapi.yaml) `/components/schemas/CurrentUser/properties/user_id` (getCurrentUser) |
| role_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.roles(role_id) | 角色标识，指向roles.role_id | [工程定义](table-catalog.json) `/user_roles/columns/role_id`；[SQL](initial-schema.sql) `mt.user_roles.role_id`；内部字段，无外部API映射 |
| expires_at | timestamptz | 是 | 无 | 无列级约束 | 此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/user_roles/columns/expires_at`；[SQL](initial-schema.sql) `mt.user_roles.expires_at`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/user_roles/columns/created_at`；[SQL](initial-schema.sql) `mt.user_roles.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/user_roles/columns/updated_at`；[SQL](initial-schema.sql) `mt.user_roles.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/user_roles/columns/row_version`；[SQL](initial-schema.sql) `mt.user_roles.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/user_roles/columns/created_by`；[SQL](initial-schema.sql) `mt.user_roles.created_by`；内部字段，无外部API映射 |

表级约束：

- `UNIQUE(user_id,role_id)`

<a id="role_permissions"></a>
## role_permissions 角色功能权限映射

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| role_permission_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/role_permissions/columns/role_permission_id`；[SQL](initial-schema.sql) `mt.role_permissions.role_permission_id`；内部字段，无外部API映射 |
| role_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.roles(role_id) | 角色标识，指向roles.role_id | [工程定义](table-catalog.json) `/role_permissions/columns/role_id`；[SQL](initial-schema.sql) `mt.role_permissions.role_id`；内部字段，无外部API映射 |
| permission_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.permissions(permission_id) | 功能权限标识，指向permissions.permission_id | [工程定义](table-catalog.json) `/role_permissions/columns/permission_id`；[SQL](initial-schema.sql) `mt.role_permissions.permission_id`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/role_permissions/columns/created_at`；[SQL](initial-schema.sql) `mt.role_permissions.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/role_permissions/columns/updated_at`；[SQL](initial-schema.sql) `mt.role_permissions.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/role_permissions/columns/row_version`；[SQL](initial-schema.sql) `mt.role_permissions.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/role_permissions/columns/created_by`；[SQL](initial-schema.sql) `mt.role_permissions.created_by`；内部字段，无外部API映射 |

表级约束：

- `UNIQUE(role_id,permission_id)`

<a id="cases"></a>
## cases 案件隔离域

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| case_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/cases/columns/case_id`；[SQL](initial-schema.sql) `mt.cases.case_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.organizations(org_id) | 记录所属单位标识；单位授权范围由服务端认证上下文确定 | [工程定义](table-catalog.json) `/cases/columns/org_id`；[SQL](initial-schema.sql) `mt.cases.org_id`；内部字段，无外部API映射 |
| display_code | text | 否 | 无 | NOT NULL | 同单位内展示和检索案件使用的业务编号，不是数据库主键 | [工程定义](table-catalog.json) `/cases/columns/display_code`；[SQL](initial-schema.sql) `mt.cases.display_code`；内部字段，无外部API映射 |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('ACTIVE','ARCHIVED')) | 案件隔离域的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/cases/columns/status`；[SQL](initial-schema.sql) `mt.cases.status`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/cases/columns/created_at`；[SQL](initial-schema.sql) `mt.cases.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/cases/columns/updated_at`；[SQL](initial-schema.sql) `mt.cases.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/cases/columns/row_version`；[SQL](initial-schema.sql) `mt.cases.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/cases/columns/created_by`；[SQL](initial-schema.sql) `mt.cases.created_by`；内部字段，无外部API映射 |

表级约束：

- `UNIQUE(case_id,org_id)`
- `UNIQUE(org_id,display_code)`

<a id="case_membership"></a>
## case_membership 显式案件授权

范围：global；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| membership_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/case_membership/columns/membership_id`；[SQL](initial-schema.sql) `mt.case_membership.membership_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限 | [工程定义](table-catalog.json) `/case_membership/columns/case_id`；[SQL](initial-schema.sql) `mt.case_membership.case_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 记录所属单位标识；单位授权范围由服务端认证上下文确定 | [工程定义](table-catalog.json) `/case_membership/columns/org_id`；[SQL](initial-schema.sql) `mt.case_membership.org_id`；[API](../03-api/openapi.yaml) `/components/schemas/CurrentUser/properties/org_id` (getCurrentUser) |
| user_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 用户与认证主体标识，指向users.user_id | [工程定义](table-catalog.json) `/case_membership/columns/user_id`；[SQL](initial-schema.sql) `mt.case_membership.user_id`；[API](../03-api/openapi.yaml) `/components/schemas/CurrentUser/properties/user_id` (getCurrentUser) |
| expires_at | timestamptz | 是 | 无 | 无列级约束 | 此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/case_membership/columns/expires_at`；[SQL](initial-schema.sql) `mt.case_membership.expires_at`；内部字段，无外部API映射 |
| revoked_at | timestamptz | 是 | 无 | 无列级约束 | 授权被撤销的时刻；为空表示尚未登记撤销，不替代到期与成员身份校验；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/case_membership/columns/revoked_at`；[SQL](initial-schema.sql) `mt.case_membership.revoked_at`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/case_membership/columns/created_at`；[SQL](initial-schema.sql) `mt.case_membership.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/case_membership/columns/updated_at`；[SQL](initial-schema.sql) `mt.case_membership.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/case_membership/columns/row_version`；[SQL](initial-schema.sql) `mt.case_membership.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/case_membership/columns/created_by`；[SQL](initial-schema.sql) `mt.case_membership.created_by`；内部字段，无外部API映射 |

表级约束：

- `UNIQUE(case_id,user_id)`
- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`

<a id="source_registry"></a>
## source_registry 来源与用途授权

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| source_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/source_registry/columns/source_id`；[SQL](initial-schema.sql) `mt.source_registry.source_id`；[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/source_id` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/source_id` (listSources)、[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/source_id` (createUpload) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/source_registry/columns/org_id`；[SQL](initial-schema.sql) `mt.source_registry.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/source_registry/columns/case_id`；[SQL](initial-schema.sql) `mt.source_registry.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/SourceCreate/properties/case_id` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/case_id` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/case_id` (listSources)、[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/case_id` (createUpload) |
| name | text | 否 | 无 | NOT NULL | 名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键 | [工程定义](table-catalog.json) `/source_registry/columns/name`；[SQL](initial-schema.sql) `mt.source_registry.name`；[API](../03-api/openapi.yaml) `/components/schemas/SourceCreate/properties/name` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/name` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/name` (listSources) |
| source_type | text | 否 | 无 | NOT NULL | 素材来源类别的编码；分类词表由接入配置定义，当前DDL未枚举限制 | [工程定义](table-catalog.json) `/source_registry/columns/source_type`；[SQL](initial-schema.sql) `mt.source_registry.source_type`；[API](../03-api/openapi.yaml) `/components/schemas/SourceCreate/properties/source_type` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/source_type` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/source_type` (listSources) |
| authorization_ref | text | 否 | 无 | NOT NULL | 来源授权凭据的受控引用，供核查用途和期限；不存访问令牌或明文密钥 | [工程定义](table-catalog.json) `/source_registry/columns/authorization_ref`；[SQL](initial-schema.sql) `mt.source_registry.authorization_ref`；[API](../03-api/openapi.yaml) `/components/schemas/SourceCreate/properties/authorization_ref` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/authorization_ref` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/authorization_ref` (listSources) |
| purpose | text[] | 否 | 无 | NOT NULL | 本记录声明或申请的处理用途，实际动作需与有效授权用途相符 | [工程定义](table-catalog.json) `/source_registry/columns/purpose`；[SQL](initial-schema.sql) `mt.source_registry.purpose`；[API](../03-api/openapi.yaml) `/components/schemas/SourceCreate/properties/purpose` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/purpose` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/purpose` (listSources) |
| authorization_status | text | 否 | 无 | NOT NULL CHECK(authorization_status IN ('pending','verified','expired','revoked')) | 来源或数据集用途授权的当前审核状态，未验证状态不得解释为可正式使用 | [工程定义](table-catalog.json) `/source_registry/columns/authorization_status`；[SQL](initial-schema.sql) `mt.source_registry.authorization_status`；[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/authorization_status` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/authorization_status` (listSources) |
| expires_at | timestamptz | 是 | 无 | 无列级约束 | 此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/source_registry/columns/expires_at`；[SQL](initial-schema.sql) `mt.source_registry.expires_at`；[API](../03-api/openapi.yaml) `/components/schemas/SourceCreate/properties/expires_at` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/expires_at` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/expires_at` (listSources)、[API](../03-api/openapi.yaml) `/components/schemas/UploadSession/properties/expires_at` (createUpload) |
| authorization_version | text | 否 | 无 | NOT NULL | 本次处理采用的来源授权版本，用于撤销核查及历史追溯 | [工程定义](table-catalog.json) `/source_registry/columns/authorization_version`；[SQL](initial-schema.sql) `mt.source_registry.authorization_version`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/source_registry/columns/created_at`；[SQL](initial-schema.sql) `mt.source_registry.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/source_registry/columns/updated_at`；[SQL](initial-schema.sql) `mt.source_registry.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/source_registry/columns/row_version`；[SQL](initial-schema.sql) `mt.source_registry.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/version` (createSource)、[API](../03-api/openapi.yaml) `/components/schemas/Source/properties/version` (listSources)、[API](../03-api/openapi.yaml) `/components/schemas/UploadSession/properties/version` (createUpload) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/source_registry/columns/created_by`；[SQL](initial-schema.sql) `mt.source_registry.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,source_id)`

<a id="content_item"></a>
## content_item 逻辑内容对象

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| content_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/content_item/columns/content_id`；[SQL](initial-schema.sql) `mt.content_item.content_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/content_item/columns/org_id`；[SQL](initial-schema.sql) `mt.content_item.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/content_item/columns/case_id`；[SQL](initial-schema.sql) `mt.content_item.case_id`；内部字段，无外部API映射 |
| source_id | uuid | 否 | 无 | NOT NULL | 数据来源登记标识，指向source_registry.source_id | [工程定义](table-catalog.json) `/content_item/columns/source_id`；[SQL](initial-schema.sql) `mt.content_item.source_id`；内部字段，无外部API映射 |
| platform | text | 是 | 无 | 无列级约束 | 原始内容发布平台的标识或名称；缺失时为空，不推断平台 | [工程定义](table-catalog.json) `/content_item/columns/platform`；[SQL](initial-schema.sql) `mt.content_item.platform`；内部字段，无外部API映射 |
| account_id | text | 是 | 无 | 无列级约束 | 来源平台内的账号标识；属于平台命名空间，不是本系统users主键 | [工程定义](table-catalog.json) `/content_item/columns/account_id`；[SQL](initial-schema.sql) `mt.content_item.account_id`；内部字段，无外部API映射 |
| published_at | timestamptz | 是 | 无 | 无列级约束 | 可核查的来源发布时间；未知为NULL，不用发现时间或当前时间填补；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/content_item/columns/published_at`；[SQL](initial-schema.sql) `mt.content_item.published_at`；内部字段，无外部API映射 |
| discovered_at | timestamptz | 否 | 无 | NOT NULL | 系统首次发现该逻辑内容的时刻，与平台发布时间分开记录；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/content_item/columns/discovered_at`；[SQL](initial-schema.sql) `mt.content_item.discovered_at`；内部字段，无外部API映射 |
| title | text | 是 | 无 | 无列级约束 | 来源内容标题；未知时为空，不强制生成标题代替原文 | [工程定义](table-catalog.json) `/content_item/columns/title`；[SQL](initial-schema.sql) `mt.content_item.title`；内部字段，无外部API映射 |
| status | text | 否 | 无 | NOT NULL | 逻辑内容对象的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/content_item/columns/status`；[SQL](initial-schema.sql) `mt.content_item.status`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/content_item/columns/created_at`；[SQL](initial-schema.sql) `mt.content_item.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/content_item/columns/updated_at`；[SQL](initial-schema.sql) `mt.content_item.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/content_item/columns/row_version`；[SQL](initial-schema.sql) `mt.content_item.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/content_item/columns/created_by`；[SQL](initial-schema.sql) `mt.content_item.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,content_id)`
- `FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id)`

<a id="object_version"></a>
## object_version 对象版本与摘要清单

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| object_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/object_version/columns/object_id`；[SQL](initial-schema.sql) `mt.object_version.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/object_ref` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/object_ref` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/ImportEntry/properties/object_ref` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/object_ref` (getTaskEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/object_ref` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (getReport) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/object_version/columns/org_id`；[SQL](initial-schema.sql) `mt.object_version.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/object_version/columns/case_id`；[SQL](initial-schema.sql) `mt.object_version.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/case_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/case_id` (sealEvidence) |
| bucket_alias | text | 否 | 无 | NOT NULL | 配置别名，不是云账号或外部地址 | [工程定义](table-catalog.json) `/object_version/columns/bucket_alias`；[SQL](initial-schema.sql) `mt.object_version.bucket_alias`；内部字段，无外部API映射 |
| object_key | text | 否 | 无 | NOT NULL | 对象存储内部键，与bucket_alias和version_id共同定位字节版本；不直接作为公开下载地址 | [工程定义](table-catalog.json) `/object_version/columns/object_key`；[SQL](initial-schema.sql) `mt.object_version.object_key`；内部字段，无外部API映射 |
| version_id | text | 否 | 无 | NOT NULL | 对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version | [工程定义](table-catalog.json) `/object_version/columns/version_id`；[SQL](initial-schema.sql) `mt.object_version.version_id`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/object_ref` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/object_ref` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/ImportEntry/properties/object_ref` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/object_ref` (getTaskEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/object_ref` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/version_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (getReport) |
| sha256 | text | 否 | 无 | NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$') | 该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/object_version/columns/sha256`；[SQL](initial-schema.sql) `mt.object_version.sha256`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/object_ref` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/object_ref` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/ImportEntry/properties/object_ref` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/object_ref` (getTaskEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/object_ref` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/sha256` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/sha256` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/object_ref` (getReport) |
| size_bytes | bigint | 否 | 无 | NOT NULL CHECK(size_bytes>0) | 文件或分片的字节长度，单位byte；有效值必须大于0 | [工程定义](table-catalog.json) `/object_version/columns/size_bytes`；[SQL](initial-schema.sql) `mt.object_version.size_bytes`；内部字段，无外部API映射 |
| retention_policy_version | text | 是 | 无 | 无列级约束 | 用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效 | [工程定义](table-catalog.json) `/object_version/columns/retention_policy_version`；[SQL](initial-schema.sql) `mt.object_version.retention_policy_version`；[API](../03-api/openapi.yaml) `/components/schemas/SealRequest/properties/retention_policy_version` (sealEvidence) |
| retain_until | timestamptz | 是 | 无 | 无列级约束 | 对象计划保留截止时刻；NULL表示未登记具体截止时间，不能自动推导可删除；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/object_version/columns/retain_until`；[SQL](initial-schema.sql) `mt.object_version.retain_until`；内部字段，无外部API映射 |
| legal_hold | boolean | 否 | false | NOT NULL DEFAULT false | 对象是否登记暂停删除要求；底层存储的实际执行结果需独立核验 | [工程定义](table-catalog.json) `/object_version/columns/legal_hold`；[SQL](initial-schema.sql) `mt.object_version.legal_hold`；内部字段，无外部API映射 |
| object_lock_verified | boolean | 否 | false | NOT NULL DEFAULT false | 是否已核验对象存储的锁定能力和该对象版本的锁定状态；不是普通文件只读标志 | [工程定义](table-catalog.json) `/object_version/columns/object_lock_verified`；[SQL](initial-schema.sql) `mt.object_version.object_lock_verified`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 对象版本登记入库时刻；TIMESTAMPTZ保存时间点，显示时区由会话决定，不保留原始时区名称 | [工程定义](table-catalog.json) `/object_version/columns/created_at`；[SQL](initial-schema.sql) `mt.object_version.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/created_at` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/created_at` (sealEvidence) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/object_version/columns/updated_at`；[SQL](initial-schema.sql) `mt.object_version.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/object_version/columns/row_version`；[SQL](initial-schema.sql) `mt.object_version.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/version` (sealEvidence) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/object_version/columns/created_by`；[SQL](initial-schema.sql) `mt.object_version.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,object_id)`
- `UNIQUE(bucket_alias,object_key,version_id)`

<a id="media_asset"></a>
## media_asset 原始或派生媒体

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| asset_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/media_asset/columns/asset_id`；[SQL](initial-schema.sql) `mt.media_asset.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/UploadResult/properties/asset_id` (completeUpload)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/asset_id` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/asset_id` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/asset_id` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/asset_id` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/asset_id` (searchImage) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/media_asset/columns/org_id`；[SQL](initial-schema.sql) `mt.media_asset.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/media_asset/columns/case_id`；[SQL](initial-schema.sql) `mt.media_asset.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/case_id` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/case_id` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/case_id` (searchImage) |
| content_id | uuid | 否 | 无 | NOT NULL | 所属逻辑内容标识，指向content_item.content_id | [工程定义](table-catalog.json) `/media_asset/columns/content_id`；[SQL](initial-schema.sql) `mt.media_asset.content_id`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/content_id` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/content_id` (getAsset) |
| source_id | uuid | 否 | 无 | NOT NULL | 数据来源登记标识，指向source_registry.source_id | [工程定义](table-catalog.json) `/media_asset/columns/source_id`；[SQL](initial-schema.sql) `mt.media_asset.source_id`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/source_id` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/source_id` (getAsset) |
| object_id | uuid | 否 | 无 | NOT NULL | 所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用 | [工程定义](table-catalog.json) `/media_asset/columns/object_id`；[SQL](initial-schema.sql) `mt.media_asset.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (getAsset) |
| sha256 | text | 否 | 无 | NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$') | 媒体资产字节的SHA-256，应与引用对象版本核对；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/media_asset/columns/sha256`；[SQL](initial-schema.sql) `mt.media_asset.sha256`；[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/sha256` (completeUpload)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/sha256` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/sha256` (getAsset) |
| mime | text | 否 | 无 | NOT NULL | 探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名 | [工程定义](table-catalog.json) `/media_asset/columns/mime`；[SQL](initial-schema.sql) `mt.media_asset.mime`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/mime` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/mime` (getAsset) |
| size_bytes | bigint | 否 | 无 | NOT NULL CHECK(size_bytes>0) | 文件或分片的字节长度，单位byte；有效值必须大于0 | [工程定义](table-catalog.json) `/media_asset/columns/size_bytes`；[SQL](initial-schema.sql) `mt.media_asset.size_bytes`；[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/size_bytes` (completeUpload)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/size_bytes` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/size_bytes` (getAsset) |
| duration_ms | bigint | 是 | 无 | CHECK(duration_ms>=0) | 媒体时长，单位毫秒；静态图像或未知时长允许NULL，0不能替代未知 | [工程定义](table-catalog.json) `/media_asset/columns/duration_ms`；[SQL](initial-schema.sql) `mt.media_asset.duration_ms`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/duration_ms` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/duration_ms` (getAsset) |
| width | integer | 是 | 无 | CHECK(width>0) | 媒体帧或图像宽度，单位像素；有值时为正整数 | [工程定义](table-catalog.json) `/media_asset/columns/width`；[SQL](initial-schema.sql) `mt.media_asset.width`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/width` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/width` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/BoundingBox/properties/width` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/BoundingBox/properties/width` (searchImage) |
| height | integer | 是 | 无 | CHECK(height>0) | 媒体帧或图像高度，单位像素；有值时为正整数 | [工程定义](table-catalog.json) `/media_asset/columns/height`；[SQL](initial-schema.sql) `mt.media_asset.height`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/height` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/height` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/BoundingBox/properties/height` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/BoundingBox/properties/height` (searchImage) |
| kind | text | 否 | 无 | NOT NULL CHECK(kind IN ('original','derived')) | 媒体身份：original为原始输入，derived为派生副本 | [工程定义](table-catalog.json) `/media_asset/columns/kind`；[SQL](initial-schema.sql) `mt.media_asset.kind`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/kind` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/kind` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/kind` (getTimeline) |
| parent_asset_id | uuid | 是 | 无 | 无列级约束 | 父媒体资产标识；原件可空，多父派生关系同时登记asset_lineage | [工程定义](table-catalog.json) `/media_asset/columns/parent_asset_id`；[SQL](initial-schema.sql) `mt.media_asset.parent_asset_id`；内部字段，无外部API映射 |
| mapping_version | text | 否 | 无 | NOT NULL | 派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本 | [工程定义](table-catalog.json) `/media_asset/columns/mapping_version`；[SQL](initial-schema.sql) `mt.media_asset.mapping_version`；[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/mapping_version` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/mapping_version` (getTimeline) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('VALIDATING','VALID','QUARANTINED','ARCHIVED')) | 原始或派生媒体的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/media_asset/columns/state`；[SQL](initial-schema.sql) `mt.media_asset.state`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/state` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/state` (getAsset)、[API](../03-api/openapi.yaml) `/components/schemas/SearchAccepted/properties/state` (searchImage) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/media_asset/columns/created_at`；[SQL](initial-schema.sql) `mt.media_asset.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/created_at` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/created_at` (getAsset) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/media_asset/columns/updated_at`；[SQL](initial-schema.sql) `mt.media_asset.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/media_asset/columns/row_version`；[SQL](initial-schema.sql) `mt.media_asset.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/version` (listAssets)、[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/version` (getAsset) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/media_asset/columns/created_by`；[SQL](initial-schema.sql) `mt.media_asset.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,asset_id)`
- `FOREIGN KEY (case_id, content_id) REFERENCES mt.content_item (case_id, content_id)`
- `FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id)`
- `FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id)`
- `FOREIGN KEY (case_id, parent_asset_id) REFERENCES mt.media_asset (case_id, asset_id)`

<a id="asset_lineage"></a>
## asset_lineage 多父对象血缘

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| lineage_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/asset_lineage/columns/lineage_id`；[SQL](initial-schema.sql) `mt.asset_lineage.lineage_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/asset_lineage/columns/org_id`；[SQL](initial-schema.sql) `mt.asset_lineage.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/asset_lineage/columns/case_id`；[SQL](initial-schema.sql) `mt.asset_lineage.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/case_id` (getAsset) |
| parent_asset_id | uuid | 否 | 无 | NOT NULL | 父媒体资产标识；原件可空，多父派生关系同时登记asset_lineage | [工程定义](table-catalog.json) `/asset_lineage/columns/parent_asset_id`；[SQL](initial-schema.sql) `mt.asset_lineage.parent_asset_id`；内部字段，无外部API映射 |
| child_asset_id | uuid | 否 | 无 | NOT NULL | 派生得到的子媒体资产标识；不能与本行父资产相同 | [工程定义](table-catalog.json) `/asset_lineage/columns/child_asset_id`；[SQL](initial-schema.sql) `mt.asset_lineage.child_asset_id`；内部字段，无外部API映射 |
| operation | text | 否 | 无 | NOT NULL | 由父媒体生成子媒体的处理操作编码，与参数、代码摘要和映射版本一起重现派生过程 | [工程定义](table-catalog.json) `/asset_lineage/columns/operation`；[SQL](initial-schema.sql) `mt.asset_lineage.operation`；内部字段，无外部API映射 |
| parameters | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 媒体派生操作参数对象，例如抽帧策略和编码设置；值须按操作对应Schema校验并排除秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/asset_lineage/columns/parameters`；[SQL](initial-schema.sql) `mt.asset_lineage.parameters`；内部字段，无外部API映射 |
| code_digest | text | 否 | 无 | NOT NULL CHECK(code_digest ~ '^[a-f0-9]{64}$') | 执行派生处理代码或发布包的SHA-256，摘要范围由发布规范固定；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/asset_lineage/columns/code_digest`；[SQL](initial-schema.sql) `mt.asset_lineage.code_digest`；内部字段，无外部API映射 |
| mapping_version | text | 否 | 无 | NOT NULL | 派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本 | [工程定义](table-catalog.json) `/asset_lineage/columns/mapping_version`；[SQL](initial-schema.sql) `mt.asset_lineage.mapping_version`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/asset_lineage/columns/created_at`；[SQL](initial-schema.sql) `mt.asset_lineage.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/created_at` (getAsset) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/asset_lineage/columns/updated_at`；[SQL](initial-schema.sql) `mt.asset_lineage.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/asset_lineage/columns/row_version`；[SQL](initial-schema.sql) `mt.asset_lineage.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Asset/properties/version` (getAsset) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/asset_lineage/columns/created_by`；[SQL](initial-schema.sql) `mt.asset_lineage.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,lineage_id)`
- `FOREIGN KEY (case_id, parent_asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `FOREIGN KEY (case_id, child_asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `CHECK(parent_asset_id<>child_asset_id)`
- `UNIQUE(case_id,parent_asset_id,child_asset_id,operation,mapping_version)`

<a id="upload_session"></a>
## upload_session 上传会话

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| upload_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/upload_session/columns/upload_id`；[SQL](initial-schema.sql) `mt.upload_session.upload_id`；[API](../03-api/openapi.yaml) `/components/schemas/UploadSession/properties/upload_id` (createUpload)、[API](../03-api/openapi.yaml) `/components/schemas/UploadResult/properties/upload_id` (completeUpload) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/upload_session/columns/org_id`；[SQL](initial-schema.sql) `mt.upload_session.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/upload_session/columns/case_id`；[SQL](initial-schema.sql) `mt.upload_session.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/case_id` (createUpload) |
| source_id | uuid | 否 | 无 | NOT NULL | 数据来源登记标识，指向source_registry.source_id | [工程定义](table-catalog.json) `/upload_session/columns/source_id`；[SQL](initial-schema.sql) `mt.upload_session.source_id`；[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/source_id` (createUpload) |
| filename | text | 否 | 无 | NOT NULL | 上传时提供的展示文件名；不得直接拼接为服务器文件路径 | [工程定义](table-catalog.json) `/upload_session/columns/filename`；[SQL](initial-schema.sql) `mt.upload_session.filename`；[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/filename` (createUpload) |
| size_bytes | bigint | 否 | 无 | NOT NULL CHECK(size_bytes>0) | 文件或分片的字节长度，单位byte；有效值必须大于0 | [工程定义](table-catalog.json) `/upload_session/columns/size_bytes`；[SQL](initial-schema.sql) `mt.upload_session.size_bytes`；[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/size_bytes` (createUpload)、[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/size_bytes` (putUploadPart)、[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/size_bytes` (completeUpload) |
| sha256 | text | 否 | 无 | NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$') | 上传方声明的完整文件SHA-256，合并后必须以实际字节重新计算核对；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/upload_session/columns/sha256`；[SQL](initial-schema.sql) `mt.upload_session.sha256`；[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/sha256` (createUpload)、[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/sha256` (putUploadPart)、[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/sha256` (completeUpload) |
| mime | text | 否 | 无 | NOT NULL | 探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名 | [工程定义](table-catalog.json) `/upload_session/columns/mime`；[SQL](initial-schema.sql) `mt.upload_session.mime`；[API](../03-api/openapi.yaml) `/components/schemas/UploadCreate/properties/mime` (createUpload) |
| part_size_bytes | bigint | 否 | 无 | NOT NULL CHECK(part_size_bytes>0) | 上传会话约定的标准分片大小，单位字节；末片可小于此值 | [工程定义](table-catalog.json) `/upload_session/columns/part_size_bytes`；[SQL](initial-schema.sql) `mt.upload_session.part_size_bytes`；[API](../03-api/openapi.yaml) `/components/schemas/UploadSession/properties/part_size_bytes` (createUpload) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('UPLOADING','VALIDATING','COMPLETED','REJECTED','EXPIRED')) | 上传会话的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/upload_session/columns/state`；[SQL](initial-schema.sql) `mt.upload_session.state`；[API](../03-api/openapi.yaml) `/components/schemas/UploadSession/properties/state` (createUpload) |
| expires_at | timestamptz | 否 | 无 | NOT NULL | 此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/upload_session/columns/expires_at`；[SQL](initial-schema.sql) `mt.upload_session.expires_at`；[API](../03-api/openapi.yaml) `/components/schemas/UploadSession/properties/expires_at` (createUpload) |
| owner_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 创建并持有上传会话的用户标识；不能直接接受客户端冒充 | [工程定义](table-catalog.json) `/upload_session/columns/owner_id`；[SQL](initial-schema.sql) `mt.upload_session.owner_id`；内部字段，无外部API映射 |
| asset_id | uuid | 是 | 无 | 无列级约束 | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/upload_session/columns/asset_id`；[SQL](initial-schema.sql) `mt.upload_session.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/UploadResult/properties/asset_id` (completeUpload) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/upload_session/columns/created_at`；[SQL](initial-schema.sql) `mt.upload_session.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/upload_session/columns/updated_at`；[SQL](initial-schema.sql) `mt.upload_session.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/upload_session/columns/row_version`；[SQL](initial-schema.sql) `mt.upload_session.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/UploadSession/properties/version` (createUpload) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/upload_session/columns/created_by`；[SQL](initial-schema.sql) `mt.upload_session.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,upload_id)`
- `FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`

<a id="upload_part"></a>
## upload_part 分片接收与校验

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| part_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/upload_part/columns/part_id`；[SQL](initial-schema.sql) `mt.upload_part.part_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/upload_part/columns/org_id`；[SQL](initial-schema.sql) `mt.upload_part.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/upload_part/columns/case_id`；[SQL](initial-schema.sql) `mt.upload_part.case_id`；内部字段，无外部API映射 |
| upload_id | uuid | 否 | 无 | NOT NULL | 所属上传会话标识，指向upload_session.upload_id | [工程定义](table-catalog.json) `/upload_part/columns/upload_id`；[SQL](initial-schema.sql) `mt.upload_part.upload_id`；[API](../03-api/openapi.yaml) `/components/schemas/UploadResult/properties/upload_id` (completeUpload) |
| part_no | integer | 否 | 无 | NOT NULL CHECK(part_no>0) | 上传分片编号，从1开始；同一会话内不得重复 | [工程定义](table-catalog.json) `/upload_part/columns/part_no`；[SQL](initial-schema.sql) `mt.upload_part.part_no`；[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/part_no` (putUploadPart)、[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/part_no` (completeUpload) |
| sha256 | text | 否 | 无 | NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$') | 该分片实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/upload_part/columns/sha256`；[SQL](initial-schema.sql) `mt.upload_part.sha256`；[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/sha256` (putUploadPart)、[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/sha256` (completeUpload) |
| size_bytes | bigint | 否 | 无 | NOT NULL CHECK(size_bytes>0) | 文件或分片的字节长度，单位byte；有效值必须大于0 | [工程定义](table-catalog.json) `/upload_part/columns/size_bytes`；[SQL](initial-schema.sql) `mt.upload_part.size_bytes`；[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/size_bytes` (putUploadPart)、[API](../03-api/openapi.yaml) `/components/schemas/UploadPart/properties/size_bytes` (completeUpload) |
| object_id | uuid | 否 | 无 | NOT NULL | 所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用 | [工程定义](table-catalog.json) `/upload_part/columns/object_id`；[SQL](initial-schema.sql) `mt.upload_part.object_id`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/upload_part/columns/created_at`；[SQL](initial-schema.sql) `mt.upload_part.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/upload_part/columns/updated_at`；[SQL](initial-schema.sql) `mt.upload_part.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/upload_part/columns/row_version`；[SQL](initial-schema.sql) `mt.upload_part.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/upload_part/columns/created_by`；[SQL](initial-schema.sql) `mt.upload_part.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,part_id)`
- `FOREIGN KEY (case_id, upload_id) REFERENCES mt.upload_session (case_id, upload_id)`
- `FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id)`
- `UNIQUE(case_id,upload_id,part_no)`

<a id="import_job"></a>
## import_job 批量清单导入作业

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| import_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/import_job/columns/import_id`；[SQL](initial-schema.sql) `mt.import_job.import_id`；[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/import_id` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/import_id` (getImport) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/import_job/columns/org_id`；[SQL](initial-schema.sql) `mt.import_job.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/import_job/columns/case_id`；[SQL](initial-schema.sql) `mt.import_job.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ImportRequest/properties/case_id` (createImport) |
| state | text | 否 | 无 | NOT NULL | 批量清单导入作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/import_job/columns/state`；[SQL](initial-schema.sql) `mt.import_job.state`；[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/state` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/state` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/state` (getImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/state` (getImport) |
| requested_count | integer | 否 | 无 | NOT NULL CHECK(requested_count>0) | 导入作业申请处理的条目总数，必须大于0；不等于成功导入数量 | [工程定义](table-catalog.json) `/import_job/columns/requested_count`；[SQL](initial-schema.sql) `mt.import_job.requested_count`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/import_job/columns/created_at`；[SQL](initial-schema.sql) `mt.import_job.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/import_job/columns/updated_at`；[SQL](initial-schema.sql) `mt.import_job.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/import_job/columns/row_version`；[SQL](initial-schema.sql) `mt.import_job.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/import_job/columns/created_by`；[SQL](initial-schema.sql) `mt.import_job.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,import_id)`

<a id="import_item"></a>
## import_item 逐条导入结果

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| item_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/import_item/columns/item_id`；[SQL](initial-schema.sql) `mt.import_item.item_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/import_item/columns/org_id`；[SQL](initial-schema.sql) `mt.import_item.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/import_item/columns/case_id`；[SQL](initial-schema.sql) `mt.import_item.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ImportRequest/properties/case_id` (createImport) |
| import_id | uuid | 否 | 无 | NOT NULL | 所属批量导入作业标识，指向import_job.import_id | [工程定义](table-catalog.json) `/import_item/columns/import_id`；[SQL](initial-schema.sql) `mt.import_item.import_id`；[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/import_id` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/import_id` (getImport) |
| ordinal | integer | 否 | 无 | NOT NULL CHECK(ordinal>=0) | 导入清单内的条目位置，从0开始；同一导入作业内唯一 | [工程定义](table-catalog.json) `/import_item/columns/ordinal`；[SQL](initial-schema.sql) `mt.import_item.ordinal`；[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/ordinal` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/ordinal` (getImport) |
| source_id | uuid | 否 | 无 | NOT NULL | 数据来源登记标识，指向source_registry.source_id | [工程定义](table-catalog.json) `/import_item/columns/source_id`；[SQL](initial-schema.sql) `mt.import_item.source_id`；[API](../03-api/openapi.yaml) `/components/schemas/ImportEntry/properties/source_id` (createImport) |
| asset_id | uuid | 是 | 无 | 无列级约束 | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/import_item/columns/asset_id`；[SQL](initial-schema.sql) `mt.import_item.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/asset_id` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/asset_id` (getImport) |
| state | text | 否 | 无 | NOT NULL | 逐条导入结果的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/import_item/columns/state`；[SQL](initial-schema.sql) `mt.import_item.state`；[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/state` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/state` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/state` (getImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/state` (getImport) |
| error_code | text | 是 | 无 | 无列级约束 | 失败原因的稳定错误码；无失败时允许NULL，用户说明与诊断堆栈分开 | [工程定义](table-catalog.json) `/import_item/columns/error_code`；[SQL](initial-schema.sql) `mt.import_item.error_code`；[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/error_code` (createImport)、[API](../03-api/openapi.yaml) `/components/schemas/ImportStatus/properties/items/items/properties/error_code` (getImport) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/import_item/columns/created_at`；[SQL](initial-schema.sql) `mt.import_item.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/import_item/columns/updated_at`；[SQL](initial-schema.sql) `mt.import_item.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/import_item/columns/row_version`；[SQL](initial-schema.sql) `mt.import_item.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/import_item/columns/created_by`；[SQL](initial-schema.sql) `mt.import_item.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,item_id)`
- `FOREIGN KEY (case_id, import_id) REFERENCES mt.import_job (case_id, import_id)`
- `FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `UNIQUE(case_id,import_id,ordinal)`

<a id="idempotency_record"></a>
## idempotency_record 主体请求摘要幂等

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| idempotency_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/idempotency_record/columns/idempotency_id`；[SQL](initial-schema.sql) `mt.idempotency_record.idempotency_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/idempotency_record/columns/org_id`；[SQL](initial-schema.sql) `mt.idempotency_record.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/idempotency_record/columns/case_id`；[SQL](initial-schema.sql) `mt.idempotency_record.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/case_id` (createTask) |
| actor_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 操作主体标识；从服务端认证上下文取得，系统动作的可空条件须另有审计规则 | [工程定义](table-catalog.json) `/idempotency_record/columns/actor_id`；[SQL](initial-schema.sql) `mt.idempotency_record.actor_id`；内部字段，无外部API映射 |
| operation | text | 否 | 无 | NOT NULL | 执行操作的稳定名称；用于审计、幂等分域或重现派生步骤，具体取值由对应模块登记 | [工程定义](table-catalog.json) `/idempotency_record/columns/operation`；[SQL](initial-schema.sql) `mt.idempotency_record.operation`；内部字段，无外部API映射 |
| idempotency_key | text | 否 | 无 | NOT NULL | 客户端提交的幂等键；与案件、主体和操作共同分域，同键请求摘要不同应报冲突 | [工程定义](table-catalog.json) `/idempotency_record/columns/idempotency_key`；[SQL](initial-schema.sql) `mt.idempotency_record.idempotency_key`；内部字段，无外部API映射 |
| request_sha256 | text | 否 | 无 | NOT NULL CHECK(request_sha256 ~ '^[a-f0-9]{64}$') | 规范化请求内容的SHA-256，规范化规则由操作契约固定；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/idempotency_record/columns/request_sha256`；[SQL](initial-schema.sql) `mt.idempotency_record.request_sha256`；内部字段，无外部API映射 |
| response_ref | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 首次成功处理的响应或结果引用对象，用于幂等重放；不缓存越权敏感内容。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/idempotency_record/columns/response_ref`；[SQL](initial-schema.sql) `mt.idempotency_record.response_ref`；内部字段，无外部API映射 |
| expires_at | timestamptz | 否 | 无 | NOT NULL | 此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/idempotency_record/columns/expires_at`；[SQL](initial-schema.sql) `mt.idempotency_record.expires_at`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/idempotency_record/columns/created_at`；[SQL](initial-schema.sql) `mt.idempotency_record.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/idempotency_record/columns/updated_at`；[SQL](initial-schema.sql) `mt.idempotency_record.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/idempotency_record/columns/row_version`；[SQL](initial-schema.sql) `mt.idempotency_record.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/idempotency_record/columns/created_by`；[SQL](initial-schema.sql) `mt.idempotency_record.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,idempotency_id)`
- `UNIQUE(case_id,actor_id,operation,idempotency_key)`

<a id="policy_registry"></a>
## policy_registry 标签阈值流程保留等策略

范围：org；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| policy_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/policy_registry/columns/policy_id`；[SQL](initial-schema.sql) `mt.policy_registry.policy_id`；[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/policy_id` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/policy_id` (listPolicies) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/policy_registry/columns/org_id`；[SQL](initial-schema.sql) `mt.policy_registry.org_id`；内部字段，无外部API映射 |
| kind | text | 否 | 无 | NOT NULL | 策略类别，如标签、阈值、流程或保留规则；类别词表由配置登记 | [工程定义](table-catalog.json) `/policy_registry/columns/kind`；[SQL](initial-schema.sql) `mt.policy_registry.kind`；[API](../03-api/openapi.yaml) `/components/schemas/PolicyCreate/properties/kind` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/kind` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/kind` (listPolicies) |
| version | text | 否 | 无 | NOT NULL | 此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version | [工程定义](table-catalog.json) `/policy_registry/columns/version`；[SQL](initial-schema.sql) `mt.policy_registry.version`；[API](../03-api/openapi.yaml) `/components/schemas/PolicyCreate/properties/version` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/version` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/version` (listPolicies) |
| definition_ref | text | 否 | 无 | NOT NULL | 完整策略定义文档或配置的受控引用，应可定位不可变版本 | [工程定义](table-catalog.json) `/policy_registry/columns/definition_ref`；[SQL](initial-schema.sql) `mt.policy_registry.definition_ref`；[API](../03-api/openapi.yaml) `/components/schemas/PolicyCreate/properties/definition_ref` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/definition_ref` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/definition_ref` (listPolicies) |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('DRAFT','APPROVED')) | 标签阈值流程保留等策略的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/policy_registry/columns/status`；[SQL](initial-schema.sql) `mt.policy_registry.status`；[API](../03-api/openapi.yaml) `/components/schemas/PolicyCreate/properties/status` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/status` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/status` (listPolicies) |
| approval_id | uuid | 是 | 无 | 无列级约束 | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/policy_registry/columns/approval_id`；[SQL](initial-schema.sql) `mt.policy_registry.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/PolicyCreate/properties/approval_id` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/approval_id` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/approval_id` (listPolicies) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/policy_registry/columns/created_at`；[SQL](initial-schema.sql) `mt.policy_registry.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/policy_registry/columns/updated_at`；[SQL](initial-schema.sql) `mt.policy_registry.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/policy_registry/columns/row_version`；[SQL](initial-schema.sql) `mt.policy_registry.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/PolicyCreate/properties/version` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/version` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/row_version` (createPolicy)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/version` (listPolicies)、[API](../03-api/openapi.yaml) `/components/schemas/Policy/properties/row_version` (listPolicies) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/policy_registry/columns/created_by`；[SQL](initial-schema.sql) `mt.policy_registry.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `UNIQUE(org_id,kind,version)`

<a id="analysis_task"></a>
## analysis_task 分析任务当前投影

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| task_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/analysis_task/columns/task_id`；[SQL](initial-schema.sql) `mt.analysis_task.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/task_id` (createTask)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/task_id` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/task_id` (getTask)、[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/task_id` (cancelTask)、[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/task_id` (rerunTask) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/analysis_task/columns/org_id`；[SQL](initial-schema.sql) `mt.analysis_task.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/analysis_task/columns/case_id`；[SQL](initial-schema.sql) `mt.analysis_task.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/case_id` (createTask)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/case_id` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/case_id` (getTask) |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/analysis_task/columns/asset_id`；[SQL](initial-schema.sql) `mt.analysis_task.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/asset_id` (createTask)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/asset_id` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/asset_id` (getTask) |
| scene | text | 否 | 无 | NOT NULL | 分析场景编码，用于选择任务处理流程；实际场景词表仍依业务配置 | [工程定义](table-catalog.json) `/analysis_task/columns/scene`；[SQL](initial-schema.sql) `mt.analysis_task.scene`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/scene` (createTask) |
| priority | text | 否 | 无 | NOT NULL CHECK(priority IN ('low','normal','high')) | 调度优先级；只影响排队策略，不改变权限或审核要求 | [工程定义](table-catalog.json) `/analysis_task/columns/priority`；[SQL](initial-schema.sql) `mt.analysis_task.priority`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/priority` (createTask) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('CREATED','QUEUED','RUNNING','WAIT_REVIEW','REVIEWING','SUCCEEDED','FAILED','RETURNED','CANCEL_REQUESTED','CANCELLED','ARCHIVED')) | 分析任务当前投影的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/analysis_task/columns/state`；[SQL](initial-schema.sql) `mt.analysis_task.state`；[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/state` (createTask)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/state` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/NodeStatus/properties/state` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/state` (getTask)、[API](../03-api/openapi.yaml) `/components/schemas/NodeStatus/properties/state` (getTask)、[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/state` (cancelTask)、[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/state` (rerunTask) |
| progress | double precision | 否 | 0 | NOT NULL DEFAULT 0 CHECK(progress>=0 AND progress<=1) | 当前运行版本的进度比例，0到1；不是准确率或任务正式通过率 | [工程定义](table-catalog.json) `/analysis_task/columns/progress`；[SQL](initial-schema.sql) `mt.analysis_task.progress`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/progress` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/progress` (getTask) |
| run_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(run_version>0) | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/analysis_task/columns/run_version`；[SQL](initial-schema.sql) `mt.analysis_task.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/run_version` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/run_version` (getTask) |
| result_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(result_version>0) | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/analysis_task/columns/result_version`；[SQL](initial-schema.sql) `mt.analysis_task.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/result_version` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/result_version` (getTask) |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/analysis_task/columns/policy_version`；[SQL](initial-schema.sql) `mt.analysis_task.policy_version`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/policy_version` (createTask)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/policy_version` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/policy_version` (getTask) |
| modules | text[] | 否 | 无 | NOT NULL | 任务请求运行的模块编码列表；服务端检查模块是否允许、依赖是否满足 | [工程定义](table-catalog.json) `/analysis_task/columns/modules`；[SQL](initial-schema.sql) `mt.analysis_task.modules`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/modules` (createTask) |
| missing_modalities | text[] | 否 | '{}' | NOT NULL DEFAULT '{}' | 输入缺失的模态列表，例如无音轨；空数组表示未登记缺失，不等于全部分析成功 | [工程定义](table-catalog.json) `/analysis_task/columns/missing_modalities`；[SQL](initial-schema.sql) `mt.analysis_task.missing_modalities`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/missing_modalities` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/missing_modalities` (getTask) |
| report_eligibility | text | 否 | 无 | NOT NULL CHECK(report_eligibility IN ('draft_only','reviewable','formal_eligible')) | 当前结果允许的报告使用等级；正式报告仍需核验审批和结果版本 | [工程定义](table-catalog.json) `/analysis_task/columns/report_eligibility`；[SQL](initial-schema.sql) `mt.analysis_task.report_eligibility`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/report_eligibility` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/report_eligibility` (getTask) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/analysis_task/columns/created_at`；[SQL](initial-schema.sql) `mt.analysis_task.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/created_at` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/created_at` (getTask) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/analysis_task/columns/updated_at`；[SQL](initial-schema.sql) `mt.analysis_task.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/analysis_task/columns/row_version`；[SQL](initial-schema.sql) `mt.analysis_task.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/version` (listTasks)、[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/version` (getTask)、[API](../03-api/openapi.yaml) `/components/schemas/TaskAction/properties/expected_version` (cancelTask)、[API](../03-api/openapi.yaml) `/components/schemas/Rerun/properties/expected_version` (rerunTask) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/analysis_task/columns/created_by`；[SQL](initial-schema.sql) `mt.analysis_task.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,task_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`

<a id="task_run"></a>
## task_run 任务运行历史

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| task_run_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/task_run/columns/task_run_id`；[SQL](initial-schema.sql) `mt.task_run.task_run_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/task_run/columns/org_id`；[SQL](initial-schema.sql) `mt.task_run.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/task_run/columns/case_id`；[SQL](initial-schema.sql) `mt.task_run.case_id`；内部字段，无外部API映射 |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/task_run/columns/task_id`；[SQL](initial-schema.sql) `mt.task_run.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/task_id` (rerunTask) |
| run_version | bigint | 否 | 无 | NOT NULL CHECK(run_version>0) | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/task_run/columns/run_version`；[SQL](initial-schema.sql) `mt.task_run.run_version`；内部字段，无外部API映射 |
| input_sha256 | text | 否 | 无 | NOT NULL CHECK(input_sha256 ~ '^[a-f0-9]{64}$') | 本次运行输入清单或输入对象的SHA-256，摘要对象须由DAG契约固定；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/task_run/columns/input_sha256`；[SQL](initial-schema.sql) `mt.task_run.input_sha256`；内部字段，无外部API映射 |
| dag_version | text | 否 | 无 | NOT NULL | 本次运行采用的任务依赖图版本，用于重现节点和执行顺序 | [工程定义](table-catalog.json) `/task_run/columns/dag_version`；[SQL](initial-schema.sql) `mt.task_run.dag_version`；内部字段，无外部API映射 |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/task_run/columns/policy_version`；[SQL](initial-schema.sql) `mt.task_run.policy_version`；内部字段，无外部API映射 |
| fencing_epoch | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(fencing_epoch>0) | 防止旧worker写回的栅栏代数；服务层必须比较最新代数，正整数CHECK本身不阻止旧worker | [工程定义](table-catalog.json) `/task_run/columns/fencing_epoch`；[SQL](initial-schema.sql) `mt.task_run.fencing_epoch`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/task_run/columns/created_at`；[SQL](initial-schema.sql) `mt.task_run.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/task_run/columns/updated_at`；[SQL](initial-schema.sql) `mt.task_run.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/task_run/columns/row_version`；[SQL](initial-schema.sql) `mt.task_run.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Rerun/properties/expected_version` (rerunTask) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/task_run/columns/created_by`；[SQL](initial-schema.sql) `mt.task_run.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,task_run_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `UNIQUE(case_id,task_id,run_version)`

<a id="task_result"></a>
## task_result 结果版本快照

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| result_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/task_result/columns/result_id`；[SQL](initial-schema.sql) `mt.task_result.result_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/task_result/columns/org_id`；[SQL](initial-schema.sql) `mt.task_result.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/task_result/columns/case_id`；[SQL](initial-schema.sql) `mt.task_result.case_id`；内部字段，无外部API映射 |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/task_result/columns/task_id`；[SQL](initial-schema.sql) `mt.task_result.task_id`；内部字段，无外部API映射 |
| run_version | bigint | 否 | 无 | NOT NULL CHECK(run_version>0) | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/task_result/columns/run_version`；[SQL](initial-schema.sql) `mt.task_result.run_version`；内部字段，无外部API映射 |
| result_version | bigint | 否 | 无 | NOT NULL CHECK(result_version>0) | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/task_result/columns/result_version`；[SQL](initial-schema.sql) `mt.task_result.result_version`；内部字段，无外部API映射 |
| sha256 | text | 否 | 无 | NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$') | 结果快照规范化表示的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/task_result/columns/sha256`；[SQL](initial-schema.sql) `mt.task_result.sha256`；内部字段，无外部API映射 |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/task_result/columns/policy_version`；[SQL](initial-schema.sql) `mt.task_result.policy_version`；内部字段，无外部API映射 |
| summary | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 结果快照的结构化摘要对象；不能作为证据事实表的替代。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/task_result/columns/summary`；[SQL](initial-schema.sql) `mt.task_result.summary`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/task_result/columns/created_at`；[SQL](initial-schema.sql) `mt.task_result.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/task_result/columns/updated_at`；[SQL](initial-schema.sql) `mt.task_result.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/task_result/columns/row_version`；[SQL](initial-schema.sql) `mt.task_result.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/task_result/columns/created_by`；[SQL](initial-schema.sql) `mt.task_result.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,result_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY(case_id,task_id,run_version) REFERENCES mt.task_run(case_id,task_id,run_version)`
- `UNIQUE(case_id,task_id,run_version,result_version)`

<a id="task_node_run"></a>
## task_node_run 节点尝试与租约

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| run_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/task_node_run/columns/run_id`；[SQL](initial-schema.sql) `mt.task_node_run.run_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/task_node_run/columns/org_id`；[SQL](initial-schema.sql) `mt.task_node_run.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/task_node_run/columns/case_id`；[SQL](initial-schema.sql) `mt.task_node_run.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/case_id` (getTask) |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/task_node_run/columns/task_id`；[SQL](initial-schema.sql) `mt.task_node_run.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/task_id` (getTask) |
| run_version | bigint | 否 | 无 | NOT NULL CHECK(run_version>0) | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/task_node_run/columns/run_version`；[SQL](initial-schema.sql) `mt.task_node_run.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/run_version` (getTask) |
| node_code | text | 否 | 无 | NOT NULL | 任务依赖图中的节点编码，在对应dag_version内解析 | [工程定义](table-catalog.json) `/task_node_run/columns/node_code`；[SQL](initial-schema.sql) `mt.task_node_run.node_code`；[API](../03-api/openapi.yaml) `/components/schemas/NodeStatus/properties/node_code` (getTask) |
| attempt | integer | 否 | 无 | NOT NULL CHECK(attempt>0) | 同一任务运行节点的尝试次数，从1开始，重试递增 | [工程定义](table-catalog.json) `/task_node_run/columns/attempt`；[SQL](initial-schema.sql) `mt.task_node_run.attempt`；[API](../03-api/openapi.yaml) `/components/schemas/NodeStatus/properties/attempt` (getTask) |
| model_version | text | 是 | 无 | 无列级约束 | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/task_node_run/columns/model_version`；[SQL](initial-schema.sql) `mt.task_node_run.model_version`；内部字段，无外部API映射 |
| input_hash | text | 否 | 无 | NOT NULL CHECK(input_hash ~ '^[a-f0-9]{64}$') | 节点输入规范化清单的SHA-256，用于重试与缓存一致性；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/task_node_run/columns/input_hash`；[SQL](initial-schema.sql) `mt.task_node_run.input_hash`；内部字段，无外部API映射 |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('PENDING','READY','RUNNING','SUCCEEDED','FAILED','SKIPPED','DEFERRED','CANCELLED','NOT_SUPPORTED')) | 节点尝试与租约的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/task_node_run/columns/state`；[SQL](initial-schema.sql) `mt.task_node_run.state`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/state` (getTask)、[API](../03-api/openapi.yaml) `/components/schemas/NodeStatus/properties/state` (getTask) |
| required | boolean | 否 | 无 | NOT NULL | 该节点是否为本次DAG完成所必需；必需节点缺失不能直接当任务成功 | [工程定义](table-catalog.json) `/task_node_run/columns/required`；[SQL](initial-schema.sql) `mt.task_node_run.required`；[API](../03-api/openapi.yaml) `/components/schemas/NodeStatus/properties/required` (getTask) |
| reason | text | 是 | 无 | 无列级约束 | 状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密 | [工程定义](table-catalog.json) `/task_node_run/columns/reason`；[SQL](initial-schema.sql) `mt.task_node_run.reason`；[API](../03-api/openapi.yaml) `/components/schemas/NodeStatus/properties/reason` (getTask) |
| lease_token | text | 是 | 无 | 无列级约束 | worker领取节点时获得的租约标识；写回须同时核验租约和fencing_epoch | [工程定义](table-catalog.json) `/task_node_run/columns/lease_token`；[SQL](initial-schema.sql) `mt.task_node_run.lease_token`；内部字段，无外部API映射 |
| fencing_epoch | bigint | 否 | 无 | NOT NULL CHECK(fencing_epoch>0) | 防止旧worker写回的栅栏代数；服务层必须比较最新代数，正整数CHECK本身不阻止旧worker | [工程定义](table-catalog.json) `/task_node_run/columns/fencing_epoch`；[SQL](initial-schema.sql) `mt.task_node_run.fencing_epoch`；内部字段，无外部API映射 |
| started_at | timestamptz | 是 | 无 | 无列级约束 | 该节点尝试实际开始执行的时刻；尚未开始时为空；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/task_node_run/columns/started_at`；[SQL](initial-schema.sql) `mt.task_node_run.started_at`；内部字段，无外部API映射 |
| ended_at | timestamptz | 是 | 无 | 无列级约束 | 该节点尝试结束时刻；未结束为空，不能早于开始时刻；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/task_node_run/columns/ended_at`；[SQL](initial-schema.sql) `mt.task_node_run.ended_at`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/task_node_run/columns/created_at`；[SQL](initial-schema.sql) `mt.task_node_run.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/created_at` (getTask) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/task_node_run/columns/updated_at`；[SQL](initial-schema.sql) `mt.task_node_run.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/task_node_run/columns/row_version`；[SQL](initial-schema.sql) `mt.task_node_run.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Task/properties/version` (getTask) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/task_node_run/columns/created_by`；[SQL](initial-schema.sql) `mt.task_node_run.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,run_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY(case_id,task_id,run_version) REFERENCES mt.task_run(case_id,task_id,run_version)`
- `UNIQUE(case_id,task_id,run_version,node_code,attempt)`
- `CHECK(ended_at IS NULL OR started_at IS NOT NULL AND ended_at>=started_at)`

<a id="task_event"></a>
## task_event 任务状态事件

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| event_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/task_event/columns/event_id`；[SQL](initial-schema.sql) `mt.task_event.event_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/task_event/columns/org_id`；[SQL](initial-schema.sql) `mt.task_event.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/task_event/columns/case_id`；[SQL](initial-schema.sql) `mt.task_event.case_id`；内部字段，无外部API映射 |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/task_event/columns/task_id`；[SQL](initial-schema.sql) `mt.task_event.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/task_id` (cancelTask)、[API](../03-api/openapi.yaml) `/components/schemas/Accepted/properties/task_id` (rerunTask) |
| run_version | bigint | 否 | 无 | NOT NULL CHECK(run_version>0) | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/task_event/columns/run_version`；[SQL](initial-schema.sql) `mt.task_event.run_version`；内部字段，无外部API映射 |
| from_state | text | 是 | 无 | 无列级约束 | 状态事件发生前的状态；首次创建事件可为空 | [工程定义](table-catalog.json) `/task_event/columns/from_state`；[SQL](initial-schema.sql) `mt.task_event.from_state`；内部字段，无外部API映射 |
| to_state | text | 否 | 无 | NOT NULL | 状态事件发生后的状态；须由所属状态机验证合法转移 | [工程定义](table-catalog.json) `/task_event/columns/to_state`；[SQL](initial-schema.sql) `mt.task_event.to_state`；内部字段，无外部API映射 |
| reason | text | 否 | 无 | NOT NULL | 状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密 | [工程定义](table-catalog.json) `/task_event/columns/reason`；[SQL](initial-schema.sql) `mt.task_event.reason`；[API](../03-api/openapi.yaml) `/components/schemas/TaskAction/properties/reason` (cancelTask)、[API](../03-api/openapi.yaml) `/components/schemas/Rerun/properties/reason` (rerunTask) |
| request_id | uuid | 否 | 无 | NOT NULL | 贯穿接口、任务和审计的请求追踪标识；不充当权限凭证 | [工程定义](table-catalog.json) `/task_event/columns/request_id`；[SQL](initial-schema.sql) `mt.task_event.request_id`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/task_event/columns/created_at`；[SQL](initial-schema.sql) `mt.task_event.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/task_event/columns/updated_at`；[SQL](initial-schema.sql) `mt.task_event.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/task_event/columns/row_version`；[SQL](initial-schema.sql) `mt.task_event.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/TaskAction/properties/expected_version` (cancelTask)、[API](../03-api/openapi.yaml) `/components/schemas/Rerun/properties/expected_version` (rerunTask) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/task_event/columns/created_by`；[SQL](initial-schema.sql) `mt.task_event.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,event_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`

<a id="outbox_event"></a>
## outbox_event 事务发件箱

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| event_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/outbox_event/columns/event_id`；[SQL](initial-schema.sql) `mt.outbox_event.event_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/outbox_event/columns/org_id`；[SQL](initial-schema.sql) `mt.outbox_event.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/outbox_event/columns/case_id`；[SQL](initial-schema.sql) `mt.outbox_event.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/TaskCreate/properties/case_id` (createTask) |
| topic | text | 否 | 无 | NOT NULL | 发件箱消息的逻辑主题名称，由消息契约登记 | [工程定义](table-catalog.json) `/outbox_event/columns/topic`；[SQL](initial-schema.sql) `mt.outbox_event.topic`；内部字段，无外部API映射 |
| aggregate_id | uuid | 否 | 无 | NOT NULL | 事件所属聚合对象标识；具体对象类型由topic确定，不是通用外键 | [工程定义](table-catalog.json) `/outbox_event/columns/aggregate_id`；[SQL](initial-schema.sql) `mt.outbox_event.aggregate_id`；内部字段，无外部API映射 |
| aggregate_version | bigint | 否 | 无 | NOT NULL CHECK(aggregate_version>0) | 该事件所描述聚合对象的版本号，同主题和对象下用于去重及顺序判断 | [工程定义](table-catalog.json) `/outbox_event/columns/aggregate_version`；[SQL](initial-schema.sql) `mt.outbox_event.aggregate_version`；内部字段，无外部API映射 |
| payload | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/outbox_event/columns/payload`；[SQL](initial-schema.sql) `mt.outbox_event.payload`；内部字段，无外部API映射 |
| published_at | timestamptz | 是 | 无 | 无列级约束 | 事件已确认投递至消息后端的时刻；NULL表示未确认投递，与媒体发布时间无关；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/outbox_event/columns/published_at`；[SQL](initial-schema.sql) `mt.outbox_event.published_at`；内部字段，无外部API映射 |
| attempts | integer | 否 | 0 | NOT NULL DEFAULT 0 CHECK(attempts>=0) | 发件箱事件已尝试投递次数，从0开始；成功与否另看published_at | [工程定义](table-catalog.json) `/outbox_event/columns/attempts`；[SQL](initial-schema.sql) `mt.outbox_event.attempts`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/outbox_event/columns/created_at`；[SQL](initial-schema.sql) `mt.outbox_event.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/outbox_event/columns/updated_at`；[SQL](initial-schema.sql) `mt.outbox_event.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/outbox_event/columns/row_version`；[SQL](initial-schema.sql) `mt.outbox_event.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/TaskAction/properties/expected_version` (cancelTask)、[API](../03-api/openapi.yaml) `/components/schemas/Rerun/properties/expected_version` (rerunTask) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/outbox_event/columns/created_by`；[SQL](initial-schema.sql) `mt.outbox_event.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,event_id)`
- `UNIQUE(case_id,topic,aggregate_id,aggregate_version)`

<a id="event_receipt"></a>
## event_receipt 消费去重记录

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| receipt_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/event_receipt/columns/receipt_id`；[SQL](initial-schema.sql) `mt.event_receipt.receipt_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/event_receipt/columns/org_id`；[SQL](initial-schema.sql) `mt.event_receipt.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/event_receipt/columns/case_id`；[SQL](initial-schema.sql) `mt.event_receipt.case_id`；内部字段，无外部API映射 |
| event_id | uuid | 否 | 无 | NOT NULL | 已处理的外部或内部事件标识；与consumer共同去重，未必来自本地发件箱 | [工程定义](table-catalog.json) `/event_receipt/columns/event_id`；[SQL](initial-schema.sql) `mt.event_receipt.event_id`；内部字段，无外部API映射 |
| consumer | text | 否 | 无 | NOT NULL | 消费逻辑的稳定标识，区分不同消费者独立处理同一事件 | [工程定义](table-catalog.json) `/event_receipt/columns/consumer`；[SQL](initial-schema.sql) `mt.event_receipt.consumer`；内部字段，无外部API映射 |
| effect_sha256 | text | 否 | 无 | NOT NULL CHECK(effect_sha256 ~ '^[a-f0-9]{64}$') | 消费已产生效果的规范化结果摘要，用于校验重复消费是否一致；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/event_receipt/columns/effect_sha256`；[SQL](initial-schema.sql) `mt.event_receipt.effect_sha256`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/event_receipt/columns/created_at`；[SQL](initial-schema.sql) `mt.event_receipt.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/event_receipt/columns/updated_at`；[SQL](initial-schema.sql) `mt.event_receipt.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/event_receipt/columns/row_version`；[SQL](initial-schema.sql) `mt.event_receipt.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/event_receipt/columns/created_by`；[SQL](initial-schema.sql) `mt.event_receipt.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,receipt_id)`
- `UNIQUE(case_id,event_id,consumer)`

<a id="shot"></a>
## shot 镜头时间区间

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| shot_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/shot/columns/shot_id`；[SQL](initial-schema.sql) `mt.shot.shot_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/shot/columns/org_id`；[SQL](initial-schema.sql) `mt.shot.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/shot/columns/case_id`；[SQL](initial-schema.sql) `mt.shot.case_id`；内部字段，无外部API映射 |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/shot/columns/asset_id`；[SQL](initial-schema.sql) `mt.shot.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/asset_id` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/asset_id` (getTimeline) |
| start_ms | bigint | 否 | 无 | NOT NULL CHECK(start_ms>=0) | 源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理 | [工程定义](table-catalog.json) `/shot/columns/start_ms`；[SQL](initial-schema.sql) `mt.shot.start_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/start_ms` (getTimeline) |
| end_ms | bigint | 否 | 无 | NOT NULL | 源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms | [工程定义](table-catalog.json) `/shot/columns/end_ms`；[SQL](initial-schema.sql) `mt.shot.end_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/end_ms` (getTimeline) |
| score | double precision | 是 | 无 | CHECK(score>=0 AND score<=1) | 镜头时间区间对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较 | [工程定义](table-catalog.json) `/shot/columns/score`；[SQL](initial-schema.sql) `mt.shot.score`；内部字段，无外部API映射 |
| mapping_version | text | 否 | 无 | NOT NULL | 派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本 | [工程定义](table-catalog.json) `/shot/columns/mapping_version`；[SQL](initial-schema.sql) `mt.shot.mapping_version`；[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/mapping_version` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/mapping_version` (getTimeline) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/shot/columns/created_at`；[SQL](initial-schema.sql) `mt.shot.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/shot/columns/updated_at`；[SQL](initial-schema.sql) `mt.shot.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/shot/columns/row_version`；[SQL](initial-schema.sql) `mt.shot.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/shot/columns/created_by`；[SQL](initial-schema.sql) `mt.shot.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,shot_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `CHECK(end_ms>start_ms)`

<a id="keyframe"></a>
## keyframe 关键帧

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| frame_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/keyframe/columns/frame_id`；[SQL](initial-schema.sql) `mt.keyframe.frame_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/keyframe/columns/org_id`；[SQL](initial-schema.sql) `mt.keyframe.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/keyframe/columns/case_id`；[SQL](initial-schema.sql) `mt.keyframe.case_id`；内部字段，无外部API映射 |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/keyframe/columns/asset_id`；[SQL](initial-schema.sql) `mt.keyframe.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/asset_id` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/asset_id` (getTimeline) |
| shot_id | uuid | 是 | 无 | 无列级约束 | 关键帧所属镜头记录标识；未进行镜头切分时允许为空 | [工程定义](table-catalog.json) `/keyframe/columns/shot_id`；[SQL](initial-schema.sql) `mt.keyframe.shot_id`；内部字段，无外部API映射 |
| timestamp_ms | bigint | 否 | 无 | NOT NULL CHECK(timestamp_ms>=0) | 关键帧在源媒体时间轴上的位置，单位毫秒，非负 | [工程定义](table-catalog.json) `/keyframe/columns/timestamp_ms`；[SQL](initial-schema.sql) `mt.keyframe.timestamp_ms`；内部字段，无外部API映射 |
| object_id | uuid | 否 | 无 | NOT NULL | 所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用 | [工程定义](table-catalog.json) `/keyframe/columns/object_id`；[SQL](initial-schema.sql) `mt.keyframe.object_id`；内部字段，无外部API映射 |
| quality_score | double precision | 是 | 无 | CHECK(quality_score>=0 AND quality_score<=1) | 关键帧对应的质量评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较 | [工程定义](table-catalog.json) `/keyframe/columns/quality_score`；[SQL](initial-schema.sql) `mt.keyframe.quality_score`；内部字段，无外部API映射 |
| mapping_version | text | 否 | 无 | NOT NULL | 派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本 | [工程定义](table-catalog.json) `/keyframe/columns/mapping_version`；[SQL](initial-schema.sql) `mt.keyframe.mapping_version`；[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/mapping_version` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/mapping_version` (getTimeline) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/keyframe/columns/created_at`；[SQL](initial-schema.sql) `mt.keyframe.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/keyframe/columns/updated_at`；[SQL](initial-schema.sql) `mt.keyframe.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/keyframe/columns/row_version`；[SQL](initial-schema.sql) `mt.keyframe.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/keyframe/columns/created_by`；[SQL](initial-schema.sql) `mt.keyframe.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,frame_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `FOREIGN KEY (case_id, shot_id) REFERENCES mt.shot (case_id, shot_id)`
- `FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id)`

<a id="text_segment"></a>
## text_segment OCR ASR字幕原文

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| segment_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/text_segment/columns/segment_id`；[SQL](initial-schema.sql) `mt.text_segment.segment_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/text_segment/columns/org_id`；[SQL](initial-schema.sql) `mt.text_segment.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/text_segment/columns/case_id`；[SQL](initial-schema.sql) `mt.text_segment.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ClaimExtract/properties/case_id` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/case_id` (extractClaims) |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/text_segment/columns/asset_id`；[SQL](initial-schema.sql) `mt.text_segment.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/asset_id` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/asset_id` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/ClaimExtract/properties/asset_id` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/asset_id` (extractClaims) |
| type | text | 否 | 无 | NOT NULL CHECK(type IN ('OCR','ASR','SUBTITLE')) | 提取模态类别：OCR、ASR或SUBTITLE | [工程定义](table-catalog.json) `/text_segment/columns/type`；[SQL](initial-schema.sql) `mt.text_segment.type`；[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/kind` (getTimeline) |
| start_ms | bigint | 是 | 无 | CHECK(start_ms>=0) | 源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理 | [工程定义](table-catalog.json) `/text_segment/columns/start_ms`；[SQL](initial-schema.sql) `mt.text_segment.start_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/start_ms` (getTimeline) |
| end_ms | bigint | 是 | 无 | 无列级约束 | 源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms | [工程定义](table-catalog.json) `/text_segment/columns/end_ms`；[SQL](initial-schema.sql) `mt.text_segment.end_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/end_ms` (getTimeline) |
| text | text | 否 | 无 | NOT NULL | OCR、ASR或字幕提取的文本原文；纠错或摘要应另存，不覆盖原文 | [工程定义](table-catalog.json) `/text_segment/columns/text`；[SQL](initial-schema.sql) `mt.text_segment.text`；[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/text` (getTimeline) |
| confidence | double precision | 是 | 无 | CHECK(confidence>=0 AND confidence<=1) | OCR ASR字幕原文对应的提取置信分数，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较 | [工程定义](table-catalog.json) `/text_segment/columns/confidence`；[SQL](initial-schema.sql) `mt.text_segment.confidence`；内部字段，无外部API映射 |
| bbox | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 源图像归一化定位框对象，使用x、y、width、height；不适用可用空对象，非空须校验边界。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/text_segment/columns/bbox`；[SQL](initial-schema.sql) `mt.text_segment.bbox`；[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/bbox` (getTimeline) |
| mapping_version | text | 否 | 无 | NOT NULL | 派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本 | [工程定义](table-catalog.json) `/text_segment/columns/mapping_version`；[SQL](initial-schema.sql) `mt.text_segment.mapping_version`；[API](../03-api/openapi.yaml) `/components/schemas/Timeline/properties/mapping_version` (getTimeline)、[API](../03-api/openapi.yaml) `/components/schemas/TimelineItem/properties/mapping_version` (getTimeline) |
| model_name | text | 否 | 无 | NOT NULL | 模型注册名称，与model_version共同定位产生该结果的模型 | [工程定义](table-catalog.json) `/text_segment/columns/model_name`；[SQL](initial-schema.sql) `mt.text_segment.model_name`；内部字段，无外部API映射 |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/text_segment/columns/model_version`；[SQL](initial-schema.sql) `mt.text_segment.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/model_version` (extractClaims) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/text_segment/columns/created_at`；[SQL](initial-schema.sql) `mt.text_segment.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/text_segment/columns/updated_at`；[SQL](initial-schema.sql) `mt.text_segment.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/text_segment/columns/row_version`；[SQL](initial-schema.sql) `mt.text_segment.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/text_segment/columns/created_by`；[SQL](initial-schema.sql) `mt.text_segment.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,segment_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `CHECK((start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND end_ms>start_ms))`

<a id="model_registry"></a>
## model_registry 模型版本与许可引用

范围：org；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| model_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/model_registry/columns/model_id`；[SQL](initial-schema.sql) `mt.model_registry.model_id`；[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/model_id` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/model_id` (listModels) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/model_registry/columns/org_id`；[SQL](initial-schema.sql) `mt.model_registry.org_id`；内部字段，无外部API映射 |
| name | text | 否 | 无 | NOT NULL | 名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键 | [工程定义](table-catalog.json) `/model_registry/columns/name`；[SQL](initial-schema.sql) `mt.model_registry.name`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/name` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/name` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/name` (listModels) |
| version | text | 否 | 无 | NOT NULL | 此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version | [工程定义](table-catalog.json) `/model_registry/columns/version`；[SQL](initial-schema.sql) `mt.model_registry.version`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/version` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/version` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/version` (listModels) |
| capability | text | 否 | 无 | NOT NULL | 模型或索引提供的能力编码，取值对应内部推理能力契约 | [工程定义](table-catalog.json) `/model_registry/columns/capability`；[SQL](initial-schema.sql) `mt.model_registry.capability`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/capability` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/capability` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/capability` (listModels) |
| digest | text | 否 | 无 | NOT NULL CHECK(digest ~ '^[a-f0-9]{64}$') | 注册模型权重或模型包的SHA-256，具体制品范围记录于模型卡；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/model_registry/columns/digest`；[SQL](initial-schema.sql) `mt.model_registry.digest`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/digest` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/digest` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/digest` (listModels) |
| metric_json | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 模型评测指标摘要对象，须包含所用指标口径对应值；具体证据引用model_evaluation。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/model_registry/columns/metric_json`；[SQL](initial-schema.sql) `mt.model_registry.metric_json`；内部字段，无外部API映射 |
| dataset_version | text | 否 | 无 | NOT NULL | 本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录 | [工程定义](table-catalog.json) `/model_registry/columns/dataset_version`；[SQL](initial-schema.sql) `mt.model_registry.dataset_version`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/dataset_version` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/dataset_version` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/dataset_version` (listModels) |
| model_card_ref | text | 否 | 无 | NOT NULL | 模型卡的受控版本引用，说明用途、限制和训练评测信息 | [工程定义](table-catalog.json) `/model_registry/columns/model_card_ref`；[SQL](initial-schema.sql) `mt.model_registry.model_card_ref`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/model_card_ref` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/model_card_ref` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/model_card_ref` (listModels) |
| license_record_ref | text | 否 | 无 | NOT NULL | 代码与权重许可核查记录引用，需覆盖本项目预定用途 | [工程定义](table-catalog.json) `/model_registry/columns/license_record_ref`；[SQL](initial-schema.sql) `mt.model_registry.license_record_ref`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/license_record_ref` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/license_record_ref` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/license_record_ref` (listModels) |
| backend | text | 否 | 无 | NOT NULL | 实际运行推理后端标识，例如经选型的框架适配器；不是模型名称 | [工程定义](table-catalog.json) `/model_registry/columns/backend`；[SQL](initial-schema.sql) `mt.model_registry.backend`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/backend` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/backend` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/backend` (listModels) |
| environment_ref | text | 否 | 无 | NOT NULL | 可重建运行环境说明或镜像摘要的受控引用 | [工程定义](table-catalog.json) `/model_registry/columns/environment_ref`；[SQL](initial-schema.sql) `mt.model_registry.environment_ref`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/environment_ref` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/environment_ref` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/environment_ref` (listModels) |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('REGISTERED','EVALUATED','CANDIDATE','APPROVED','ACTIVE','RETIRED')) | 模型版本与许可引用的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/model_registry/columns/status`；[SQL](initial-schema.sql) `mt.model_registry.status`；[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/status` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/status` (listModels)、[API](../03-api/openapi.yaml) `/components/schemas/Health/properties/status` (getModelHealth) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/model_registry/columns/created_at`；[SQL](initial-schema.sql) `mt.model_registry.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/model_registry/columns/updated_at`；[SQL](initial-schema.sql) `mt.model_registry.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/model_registry/columns/row_version`；[SQL](initial-schema.sql) `mt.model_registry.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/ModelCreate/properties/version` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/version` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/row_version` (registerModel)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/version` (listModels)、[API](../03-api/openapi.yaml) `/components/schemas/Model/properties/row_version` (listModels) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/model_registry/columns/created_by`；[SQL](initial-schema.sql) `mt.model_registry.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `UNIQUE(org_id,name,version)`
- `UNIQUE(org_id,model_id)`

<a id="model_evaluation"></a>
## model_evaluation 不可覆盖评测记录

范围：org；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| evaluation_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/model_evaluation/columns/evaluation_id`；[SQL](initial-schema.sql) `mt.model_evaluation.evaluation_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/evaluation_id` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/evaluation_id` (listEvaluations) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/model_evaluation/columns/org_id`；[SQL](initial-schema.sql) `mt.model_evaluation.org_id`；内部字段，无外部API映射 |
| model_id | uuid | 否 | 无 | NOT NULL | 模型注册记录标识，引用同单位的model_registry.model_id | [工程定义](table-catalog.json) `/model_evaluation/columns/model_id`；[SQL](initial-schema.sql) `mt.model_evaluation.model_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/model_id` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/model_id` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/model_id` (listEvaluations) |
| dataset_id | text | 否 | 无 | NOT NULL | 数据集目录的稳定文本编号，例如D01；不是数据库UUID主键 | [工程定义](table-catalog.json) `/model_evaluation/columns/dataset_id`；[SQL](initial-schema.sql) `mt.model_evaluation.dataset_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/dataset_id` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/dataset_id` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/dataset_id` (listEvaluations) |
| dataset_version | text | 否 | 无 | NOT NULL | 本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录 | [工程定义](table-catalog.json) `/model_evaluation/columns/dataset_version`；[SQL](initial-schema.sql) `mt.model_evaluation.dataset_version`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/dataset_version` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/dataset_version` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/dataset_version` (listEvaluations) |
| protocol_id | text | 否 | 无 | NOT NULL | 评测协议标识，决定指标公式、样本计数、阈值及统计口径 | [工程定义](table-catalog.json) `/model_evaluation/columns/protocol_id`；[SQL](initial-schema.sql) `mt.model_evaluation.protocol_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/protocol_id` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/protocol_id` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/protocol_id` (listEvaluations) |
| split | text | 否 | 无 | NOT NULL CHECK(split IN ('validation','calibration','holdout')) | 此次评测使用的划分用途；封存holdout不能用于训练或调参 | [工程定义](table-catalog.json) `/model_evaluation/columns/split`；[SQL](initial-schema.sql) `mt.model_evaluation.split`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/split` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/split` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/split` (listEvaluations) |
| sample_count | integer | 否 | 无 | NOT NULL CHECK(sample_count>0) | 按照评测协议统计的样本数，必须为正；不能混用帧数、素材组数和文件数 | [工程定义](table-catalog.json) `/model_evaluation/columns/sample_count`；[SQL](initial-schema.sql) `mt.model_evaluation.sample_count`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/sample_count` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/sample_count` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/sample_count` (listEvaluations) |
| failure_count | integer | 否 | 无 | NOT NULL CHECK(failure_count>=0 AND failure_count<=sample_count) | 处理失败样本数，范围0到sample_count，不应从评测分母中隐式删除 | [工程定义](table-catalog.json) `/model_evaluation/columns/failure_count`；[SQL](initial-schema.sql) `mt.model_evaluation.failure_count`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/failure_count` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/failure_count` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/failure_count` (listEvaluations) |
| metrics | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 评测协议规定的指标结果对象；需保留失败计数和适用样本口径。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/model_evaluation/columns/metrics`；[SQL](initial-schema.sql) `mt.model_evaluation.metrics`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/metrics` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/metrics` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/metrics` (listEvaluations) |
| artifact_ref | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/model_evaluation/columns/artifact_ref`；[SQL](initial-schema.sql) `mt.model_evaluation.artifact_ref`；[API](../03-api/openapi.yaml) `/components/schemas/EvaluationCreate/properties/artifact_ref` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/artifact_ref` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/artifact_ref` (listEvaluations) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/model_evaluation/columns/created_at`；[SQL](initial-schema.sql) `mt.model_evaluation.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/created_at` (recordEvaluation)、[API](../03-api/openapi.yaml) `/components/schemas/Evaluation/properties/created_at` (listEvaluations) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/model_evaluation/columns/updated_at`；[SQL](initial-schema.sql) `mt.model_evaluation.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/model_evaluation/columns/row_version`；[SQL](initial-schema.sql) `mt.model_evaluation.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/model_evaluation/columns/created_by`；[SQL](initial-schema.sql) `mt.model_evaluation.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `FOREIGN KEY(org_id,model_id) REFERENCES mt.model_registry(org_id,model_id)`

<a id="model_release"></a>
## model_release 模型发布包

范围：org；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| release_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/model_release/columns/release_id`；[SQL](initial-schema.sql) `mt.model_release.release_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/model_release/columns/org_id`；[SQL](initial-schema.sql) `mt.model_release.org_id`；内部字段，无外部API映射 |
| model_id | uuid | 否 | 无 | NOT NULL | 模型注册记录标识，引用同单位的model_registry.model_id | [工程定义](table-catalog.json) `/model_release/columns/model_id`；[SQL](initial-schema.sql) `mt.model_release.model_id`；内部字段，无外部API映射 |
| bundle_sha256 | text | 否 | 无 | NOT NULL CHECK(bundle_sha256 ~ '^[a-f0-9]{64}$') | 完整模型发布包的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/model_release/columns/bundle_sha256`；[SQL](initial-schema.sql) `mt.model_release.bundle_sha256`；内部字段，无外部API映射 |
| calibration_version | text | 是 | 无 | 无列级约束 | 分数校准方法和参数版本；未校准时为空，不把原始分数称为概率 | [工程定义](table-catalog.json) `/model_release/columns/calibration_version`；[SQL](initial-schema.sql) `mt.model_release.calibration_version`；内部字段，无外部API映射 |
| backend | text | 否 | 无 | NOT NULL | 实际运行推理后端标识，例如经选型的框架适配器；不是模型名称 | [工程定义](table-catalog.json) `/model_release/columns/backend`；[SQL](initial-schema.sql) `mt.model_release.backend`；内部字段，无外部API映射 |
| index_version | text | 是 | 无 | 无列级约束 | 本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本 | [工程定义](table-catalog.json) `/model_release/columns/index_version`；[SQL](initial-schema.sql) `mt.model_release.index_version`；[API](../03-api/openapi.yaml) `/components/schemas/Rollout/properties/index_version` (rolloutModel) |
| approval_id | uuid | 是 | 无 | 无列级约束 | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/model_release/columns/approval_id`；[SQL](initial-schema.sql) `mt.model_release.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/Rollout/properties/approval_id` (rolloutModel) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('CANDIDATE','APPROVED','ACTIVE','RETIRED')) | 模型发布包的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/model_release/columns/state`；[SQL](initial-schema.sql) `mt.model_release.state`；[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/state` (rolloutModel) |
| environment_ref | text | 否 | 无 | NOT NULL | 可重建运行环境说明或镜像摘要的受控引用 | [工程定义](table-catalog.json) `/model_release/columns/environment_ref`；[SQL](initial-schema.sql) `mt.model_release.environment_ref`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/model_release/columns/created_at`；[SQL](initial-schema.sql) `mt.model_release.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/model_release/columns/updated_at`；[SQL](initial-schema.sql) `mt.model_release.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/model_release/columns/row_version`；[SQL](initial-schema.sql) `mt.model_release.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Rollout/properties/expected_version` (rolloutModel)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/version` (rolloutModel) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/model_release/columns/created_by`；[SQL](initial-schema.sql) `mt.model_release.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `FOREIGN KEY(org_id,model_id) REFERENCES mt.model_registry(org_id,model_id)`
- `FOREIGN KEY(org_id,approval_id) REFERENCES mt.approval_request(org_id,approval_id)`

<a id="index_registry"></a>
## index_registry 索引版本不混向量

范围：org；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| index_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/index_registry/columns/index_id`；[SQL](initial-schema.sql) `mt.index_registry.index_id`；[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/index_id` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/index_id` (switchIndex) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/index_registry/columns/org_id`；[SQL](initial-schema.sql) `mt.index_registry.org_id`；内部字段，无外部API映射 |
| capability | text | 否 | 无 | NOT NULL | 模型或索引提供的能力编码，取值对应内部推理能力契约 | [工程定义](table-catalog.json) `/index_registry/columns/capability`；[SQL](initial-schema.sql) `mt.index_registry.capability`；[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/capability` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/capability` (switchIndex) |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/index_registry/columns/model_version`；[SQL](initial-schema.sql) `mt.index_registry.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/model_version` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/model_version` (switchIndex) |
| dimension | integer | 否 | 无 | NOT NULL CHECK(dimension>0) | 特征向量维度，必须为正整数并与模型及索引配置一致 | [工程定义](table-catalog.json) `/index_registry/columns/dimension`；[SQL](initial-schema.sql) `mt.index_registry.dimension`；[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/dimension` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/dimension` (switchIndex) |
| normalization | text | 否 | 无 | NOT NULL CHECK(normalization IN ('l2','none')) | 特征归一化方法，例如l2或none；应与训练、查询和索引构建保持一致 | [工程定义](table-catalog.json) `/index_registry/columns/normalization`；[SQL](initial-schema.sql) `mt.index_registry.normalization`；[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/normalization` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/normalization` (switchIndex) |
| index_version | text | 否 | 无 | NOT NULL | 本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本 | [工程定义](table-catalog.json) `/index_registry/columns/index_version`；[SQL](initial-schema.sql) `mt.index_registry.index_version`；[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/index_version` (searchImage)、[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/index_version` (searchImageRegion)、[API](../03-api/openapi.yaml) `/components/schemas/VideoSearch/properties/index_version` (searchVideo)、[API](../03-api/openapi.yaml) `/components/schemas/Rollout/properties/index_version` (rolloutModel)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/index_version` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/index_version` (switchIndex) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('BUILDING','READY','ACTIVE','RETIRED')) | 索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/index_registry/columns/state`；[SQL](initial-schema.sql) `mt.index_registry.state`；[API](../03-api/openapi.yaml) `/components/schemas/SearchAccepted/properties/state` (searchImage)、[API](../03-api/openapi.yaml) `/components/schemas/SearchAccepted/properties/state` (searchImageRegion)、[API](../03-api/openapi.yaml) `/components/schemas/SearchAccepted/properties/state` (searchVideo)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/state` (rolloutModel)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/state` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/state` (switchIndex) |
| configuration | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 索引构建参数对象，包括距离与索引配置；具体字段由所选索引适配器校验。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/index_registry/columns/configuration`；[SQL](initial-schema.sql) `mt.index_registry.configuration`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/index_registry/columns/created_at`；[SQL](initial-schema.sql) `mt.index_registry.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/index_registry/columns/updated_at`；[SQL](initial-schema.sql) `mt.index_registry.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/index_registry/columns/row_version`；[SQL](initial-schema.sql) `mt.index_registry.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Rollout/properties/expected_version` (rolloutModel)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/version` (rolloutModel)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/row_version` (getIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexSwitch/properties/expected_version` (switchIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/row_version` (switchIndex) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/index_registry/columns/created_by`；[SQL](initial-schema.sql) `mt.index_registry.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `UNIQUE(org_id,capability,index_version)`

<a id="feature"></a>
## feature 模型特征元数据

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| feature_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/feature/columns/feature_id`；[SQL](initial-schema.sql) `mt.feature.feature_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/feature/columns/org_id`；[SQL](initial-schema.sql) `mt.feature.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/feature/columns/case_id`；[SQL](initial-schema.sql) `mt.feature.case_id`；内部字段，无外部API映射 |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/feature/columns/asset_id`；[SQL](initial-schema.sql) `mt.feature.asset_id`；内部字段，无外部API映射 |
| model_id | uuid | 否 | 无 | NOT NULL | 模型注册记录标识，引用同单位的model_registry.model_id | [工程定义](table-catalog.json) `/feature/columns/model_id`；[SQL](initial-schema.sql) `mt.feature.model_id`；内部字段，无外部API映射 |
| dimension | integer | 否 | 无 | NOT NULL CHECK(dimension>0) | 特征向量维度，必须为正整数并与模型及索引配置一致 | [工程定义](table-catalog.json) `/feature/columns/dimension`；[SQL](initial-schema.sql) `mt.feature.dimension`；内部字段，无外部API映射 |
| normalization | text | 否 | 无 | NOT NULL | 特征归一化方法，例如l2或none；应与训练、查询和索引构建保持一致 | [工程定义](table-catalog.json) `/feature/columns/normalization`；[SQL](initial-schema.sql) `mt.feature.normalization`；内部字段，无外部API映射 |
| feature_ref | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 特征数据的受控存储定位与版本对象，不在该字段内混入不同模型向量。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/feature/columns/feature_ref`；[SQL](initial-schema.sql) `mt.feature.feature_ref`；内部字段，无外部API映射 |
| index_version | text | 否 | 无 | NOT NULL | 本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本 | [工程定义](table-catalog.json) `/feature/columns/index_version`；[SQL](initial-schema.sql) `mt.feature.index_version`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/feature/columns/created_at`；[SQL](initial-schema.sql) `mt.feature.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/feature/columns/updated_at`；[SQL](initial-schema.sql) `mt.feature.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/feature/columns/row_version`；[SQL](initial-schema.sql) `mt.feature.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/feature/columns/created_by`；[SQL](initial-schema.sql) `mt.feature.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,feature_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `FOREIGN KEY(org_id,model_id) REFERENCES mt.model_registry(org_id,model_id)`

<a id="evidence_item"></a>
## evidence_item 证据事实版本

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| evidence_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/evidence_item/columns/evidence_id`；[SQL](initial-schema.sql) `mt.evidence_item.evidence_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/evidence_id` (getTaskEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/evidence_ids` (getReport) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/evidence_item/columns/org_id`；[SQL](initial-schema.sql) `mt.evidence_item.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/evidence_item/columns/case_id`；[SQL](initial-schema.sql) `mt.evidence_item.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/case_id` (getTaskEvidence) |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/evidence_item/columns/task_id`；[SQL](initial-schema.sql) `mt.evidence_item.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/task_id` (getTaskEvidence) |
| run_version | bigint | 否 | 无 | NOT NULL | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/evidence_item/columns/run_version`；[SQL](initial-schema.sql) `mt.evidence_item.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/run_version` (getTaskEvidence) |
| result_version | bigint | 否 | 无 | NOT NULL | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/evidence_item/columns/result_version`；[SQL](initial-schema.sql) `mt.evidence_item.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/result_version` (getTaskEvidence) |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/evidence_item/columns/asset_id`；[SQL](initial-schema.sql) `mt.evidence_item.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/asset_id` (getTaskEvidence) |
| type | text | 否 | 无 | NOT NULL | 证据类别编码，决定对象、时间范围和定位解释 | [工程定义](table-catalog.json) `/evidence_item/columns/type`；[SQL](initial-schema.sql) `mt.evidence_item.type`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/kind` (getTaskEvidence) |
| object_id | uuid | 是 | 无 | 无列级约束 | 所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用 | [工程定义](table-catalog.json) `/evidence_item/columns/object_id`；[SQL](initial-schema.sql) `mt.evidence_item.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (getTaskEvidence) |
| sha256 | text | 否 | 无 | NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$') | 该证据版本绑定内容的SHA-256，摘要对象需在证据类型契约中明确；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/evidence_item/columns/sha256`；[SQL](initial-schema.sql) `mt.evidence_item.sha256`；[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/sha256` (getTaskEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/sha256` (getTaskEvidence) |
| captured_at | timestamptz | 否 | 无 | NOT NULL | 证据采集或记录的实际时刻；可信时间来源由取证规则确定，不保证机器时钟天然可信；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/evidence_item/columns/captured_at`；[SQL](initial-schema.sql) `mt.evidence_item.captured_at`；内部字段，无外部API映射 |
| model_name | text | 是 | 无 | 无列级约束 | 模型注册名称，与model_version共同定位产生该结果的模型 | [工程定义](table-catalog.json) `/evidence_item/columns/model_name`；[SQL](initial-schema.sql) `mt.evidence_item.model_name`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/model_name` (getTaskEvidence) |
| model_version | text | 是 | 无 | 无列级约束 | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/evidence_item/columns/model_version`；[SQL](initial-schema.sql) `mt.evidence_item.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/model_version` (getTaskEvidence) |
| mapping_version | text | 否 | 无 | NOT NULL | 派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本 | [工程定义](table-catalog.json) `/evidence_item/columns/mapping_version`；[SQL](initial-schema.sql) `mt.evidence_item.mapping_version`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/mapping_version` (getTaskEvidence) |
| authorization_version | text | 否 | 无 | NOT NULL | 本次处理采用的来源授权版本，用于撤销核查及历史追溯 | [工程定义](table-catalog.json) `/evidence_item/columns/authorization_version`；[SQL](initial-schema.sql) `mt.evidence_item.authorization_version`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/authorization_version` (getTaskEvidence) |
| immutable_state | text | 否 | 无 | NOT NULL CHECK(immutable_state IN ('RECORDED','SEALED')) | 证据事实版本的不可变记录状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/evidence_item/columns/immutable_state`；[SQL](initial-schema.sql) `mt.evidence_item.immutable_state`；内部字段，无外部API映射 |
| time_range | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 源媒体时间范围对象，使用start_ms、end_ms；非空时必须校验先后与源媒体范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/evidence_item/columns/time_range`；[SQL](initial-schema.sql) `mt.evidence_item.time_range`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/time_range` (getTaskEvidence) |
| bbox | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 源图像归一化定位框对象，使用x、y、width、height；不适用可用空对象，非空须校验边界。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/evidence_item/columns/bbox`；[SQL](initial-schema.sql) `mt.evidence_item.bbox`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/bbox` (getTaskEvidence) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/evidence_item/columns/created_at`；[SQL](initial-schema.sql) `mt.evidence_item.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/created_at` (getTaskEvidence) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/evidence_item/columns/updated_at`；[SQL](initial-schema.sql) `mt.evidence_item.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/evidence_item/columns/row_version`；[SQL](initial-schema.sql) `mt.evidence_item.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/version` (getTaskEvidence) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/evidence_item/columns/created_by`；[SQL](initial-schema.sql) `mt.evidence_item.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,evidence_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id)`
- `FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)`

<a id="risk_finding"></a>
## risk_finding 风险候选发现

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| finding_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/risk_finding/columns/finding_id`；[SQL](initial-schema.sql) `mt.risk_finding.finding_id`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/finding_id` (getRiskFindings) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/risk_finding/columns/org_id`；[SQL](initial-schema.sql) `mt.risk_finding.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/risk_finding/columns/case_id`；[SQL](initial-schema.sql) `mt.risk_finding.case_id`；内部字段，无外部API映射 |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/risk_finding/columns/task_id`；[SQL](initial-schema.sql) `mt.risk_finding.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/VersionBinding/properties/task_id` (getRiskFindings) |
| run_version | bigint | 否 | 无 | NOT NULL | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/risk_finding/columns/run_version`；[SQL](initial-schema.sql) `mt.risk_finding.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/VersionBinding/properties/run_version` (getRiskFindings) |
| result_version | bigint | 否 | 无 | NOT NULL | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/risk_finding/columns/result_version`；[SQL](initial-schema.sql) `mt.risk_finding.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/VersionBinding/properties/result_version` (getRiskFindings) |
| category | text | 否 | 无 | NOT NULL | 风险分类编码；取值、阈值和法律业务含义由有效标签策略确定 | [工程定义](table-catalog.json) `/risk_finding/columns/category`；[SQL](initial-schema.sql) `mt.risk_finding.category`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/label` (getRiskFindings) |
| score | double precision | 是 | 无 | CHECK(score>=0 AND score<=1) | 风险候选发现对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较 | [工程定义](table-catalog.json) `/risk_finding/columns/score`；[SQL](initial-schema.sql) `mt.risk_finding.score`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/raw_score` (getRiskFindings) |
| calibrated_score | double precision | 是 | 无 | CHECK(calibrated_score>=0 AND calibrated_score<=1) | 校准后的模型分数，范围0至1；未进行校准时为NULL，必须绑定相应校准版本和评测口径 | [工程定义](table-catalog.json) `/risk_finding/columns/calibrated_score`；[SQL](initial-schema.sql) `mt.risk_finding.calibrated_score`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/calibrated_score` (getRiskFindings) |
| start_ms | bigint | 是 | 无 | CHECK(start_ms>=0) | 源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理 | [工程定义](table-catalog.json) `/risk_finding/columns/start_ms`；[SQL](initial-schema.sql) `mt.risk_finding.start_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/start_ms` (getRiskFindings) |
| end_ms | bigint | 是 | 无 | 无列级约束 | 源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms | [工程定义](table-catalog.json) `/risk_finding/columns/end_ms`；[SQL](initial-schema.sql) `mt.risk_finding.end_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/end_ms` (getRiskFindings) |
| model_name | text | 否 | 无 | NOT NULL | 模型注册名称，与model_version共同定位产生该结果的模型 | [工程定义](table-catalog.json) `/risk_finding/columns/model_name`；[SQL](initial-schema.sql) `mt.risk_finding.model_name`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/model_name` (getRiskFindings) |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/risk_finding/columns/model_version`；[SQL](initial-schema.sql) `mt.risk_finding.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/model_version` (getRiskFindings) |
| threshold_version | text | 是 | 无 | 无列级约束 | 将模型分数转为候选标签时使用的阈值配置版本 | [工程定义](table-catalog.json) `/risk_finding/columns/threshold_version`；[SQL](initial-schema.sql) `mt.risk_finding.threshold_version`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/threshold_version` (getRiskFindings) |
| payload | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/risk_finding/columns/payload`；[SQL](initial-schema.sql) `mt.risk_finding.payload`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/mask_ref` (getRiskFindings) |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')) | 风险候选发现的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/risk_finding/columns/status`；[SQL](initial-schema.sql) `mt.risk_finding.status`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/status` (getRiskFindings) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/risk_finding/columns/created_at`；[SQL](initial-schema.sql) `mt.risk_finding.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/risk_finding/columns/updated_at`；[SQL](initial-schema.sql) `mt.risk_finding.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/risk_finding/columns/row_version`；[SQL](initial-schema.sql) `mt.risk_finding.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/risk_finding/columns/created_by`；[SQL](initial-schema.sql) `mt.risk_finding.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,finding_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)`
- `CHECK((start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND end_ms>start_ms))`

<a id="tamper_finding"></a>
## tamper_finding 疑似篡改发现

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| tamper_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/tamper_finding/columns/tamper_id`；[SQL](initial-schema.sql) `mt.tamper_finding.tamper_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/tamper_finding/columns/org_id`；[SQL](initial-schema.sql) `mt.tamper_finding.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/tamper_finding/columns/case_id`；[SQL](initial-schema.sql) `mt.tamper_finding.case_id`；内部字段，无外部API映射 |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/tamper_finding/columns/task_id`；[SQL](initial-schema.sql) `mt.tamper_finding.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/VersionBinding/properties/task_id` (getForensics) |
| run_version | bigint | 否 | 无 | NOT NULL | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/tamper_finding/columns/run_version`；[SQL](initial-schema.sql) `mt.tamper_finding.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/VersionBinding/properties/run_version` (getForensics) |
| result_version | bigint | 否 | 无 | NOT NULL | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/tamper_finding/columns/result_version`；[SQL](initial-schema.sql) `mt.tamper_finding.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/VersionBinding/properties/result_version` (getForensics) |
| type | text | 否 | 无 | NOT NULL | 疑似篡改类型编码，取值由模型及标签策略约定 | [工程定义](table-catalog.json) `/tamper_finding/columns/type`；[SQL](initial-schema.sql) `mt.tamper_finding.type`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/kind` (getForensics)、[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/label` (getForensics) |
| score | double precision | 是 | 无 | CHECK(score>=0 AND score<=1) | 疑似篡改发现对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较 | [工程定义](table-catalog.json) `/tamper_finding/columns/score`；[SQL](initial-schema.sql) `mt.tamper_finding.score`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/raw_score` (getForensics) |
| calibrated_score | double precision | 是 | 无 | CHECK(calibrated_score>=0 AND calibrated_score<=1) | 校准后的模型分数，范围0至1；未进行校准时为NULL，必须绑定相应校准版本和评测口径 | [工程定义](table-catalog.json) `/tamper_finding/columns/calibrated_score`；[SQL](initial-schema.sql) `mt.tamper_finding.calibrated_score`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/calibrated_score` (getForensics) |
| start_ms | bigint | 是 | 无 | CHECK(start_ms>=0) | 源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理 | [工程定义](table-catalog.json) `/tamper_finding/columns/start_ms`；[SQL](initial-schema.sql) `mt.tamper_finding.start_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/start_ms` (getForensics) |
| end_ms | bigint | 是 | 无 | 无列级约束 | 源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms | [工程定义](table-catalog.json) `/tamper_finding/columns/end_ms`；[SQL](initial-schema.sql) `mt.tamper_finding.end_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/end_ms` (getForensics) |
| model_name | text | 否 | 无 | NOT NULL | 模型注册名称，与model_version共同定位产生该结果的模型 | [工程定义](table-catalog.json) `/tamper_finding/columns/model_name`；[SQL](initial-schema.sql) `mt.tamper_finding.model_name`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/model_name` (getForensics) |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/tamper_finding/columns/model_version`；[SQL](initial-schema.sql) `mt.tamper_finding.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/model_version` (getForensics) |
| threshold_version | text | 是 | 无 | 无列级约束 | 将模型分数转为候选标签时使用的阈值配置版本 | [工程定义](table-catalog.json) `/tamper_finding/columns/threshold_version`；[SQL](initial-schema.sql) `mt.tamper_finding.threshold_version`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/threshold_version` (getForensics) |
| payload | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/tamper_finding/columns/payload`；[SQL](initial-schema.sql) `mt.tamper_finding.payload`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/mask_ref` (getForensics) |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')) | 疑似篡改发现的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/tamper_finding/columns/status`；[SQL](initial-schema.sql) `mt.tamper_finding.status`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/status` (getForensics) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/tamper_finding/columns/created_at`；[SQL](initial-schema.sql) `mt.tamper_finding.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/tamper_finding/columns/updated_at`；[SQL](initial-schema.sql) `mt.tamper_finding.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/tamper_finding/columns/row_version`；[SQL](initial-schema.sql) `mt.tamper_finding.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/tamper_finding/columns/created_by`；[SQL](initial-schema.sql) `mt.tamper_finding.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,tamper_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)`
- `CHECK((start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND end_ms>start_ms))`

<a id="finding_evidence"></a>
## finding_evidence 发现与证据多对多

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| link_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/finding_evidence/columns/link_id`；[SQL](initial-schema.sql) `mt.finding_evidence.link_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/finding_evidence/columns/org_id`；[SQL](initial-schema.sql) `mt.finding_evidence.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/finding_evidence/columns/case_id`；[SQL](initial-schema.sql) `mt.finding_evidence.case_id`；内部字段，无外部API映射 |
| risk_finding_id | uuid | 是 | 无 | 无列级约束 | 关联风险发现标识；与tamper_finding_id按表级互斥规则择一 | [工程定义](table-catalog.json) `/finding_evidence/columns/risk_finding_id`；[SQL](initial-schema.sql) `mt.finding_evidence.risk_finding_id`；内部字段，无外部API映射 |
| tamper_finding_id | uuid | 是 | 无 | 无列级约束 | 关联疑似篡改发现标识；与risk_finding_id按表级互斥规则择一 | [工程定义](table-catalog.json) `/finding_evidence/columns/tamper_finding_id`；[SQL](initial-schema.sql) `mt.finding_evidence.tamper_finding_id`；内部字段，无外部API映射 |
| evidence_id | uuid | 否 | 无 | NOT NULL | 所引用证据事实版本标识，指向同案件evidence_item.evidence_id | [工程定义](table-catalog.json) `/finding_evidence/columns/evidence_id`；[SQL](initial-schema.sql) `mt.finding_evidence.evidence_id`；[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/evidence_ids` (getRiskFindings)、[API](../03-api/openapi.yaml) `/components/schemas/Finding/properties/evidence_ids` (getForensics) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/finding_evidence/columns/created_at`；[SQL](initial-schema.sql) `mt.finding_evidence.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/finding_evidence/columns/updated_at`；[SQL](initial-schema.sql) `mt.finding_evidence.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/finding_evidence/columns/row_version`；[SQL](initial-schema.sql) `mt.finding_evidence.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/finding_evidence/columns/created_by`；[SQL](initial-schema.sql) `mt.finding_evidence.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,link_id)`
- `FOREIGN KEY (case_id, risk_finding_id) REFERENCES mt.risk_finding (case_id, finding_id)`
- `FOREIGN KEY (case_id, tamper_finding_id) REFERENCES mt.tamper_finding (case_id, tamper_id)`
- `FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)`
- `CHECK(num_nonnulls(risk_finding_id,tamper_finding_id)=1)`

<a id="task_evidence"></a>
## task_evidence 任务证据引用

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| link_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/task_evidence/columns/link_id`；[SQL](initial-schema.sql) `mt.task_evidence.link_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/task_evidence/columns/org_id`；[SQL](initial-schema.sql) `mt.task_evidence.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/task_evidence/columns/case_id`；[SQL](initial-schema.sql) `mt.task_evidence.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/case_id` (getTaskEvidence) |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/task_evidence/columns/task_id`；[SQL](initial-schema.sql) `mt.task_evidence.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/task_id` (getTaskEvidence) |
| evidence_id | uuid | 否 | 无 | NOT NULL | 所引用证据事实版本标识，指向同案件evidence_item.evidence_id | [工程定义](table-catalog.json) `/task_evidence/columns/evidence_id`；[SQL](initial-schema.sql) `mt.task_evidence.evidence_id`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/evidence_id` (getTaskEvidence) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/task_evidence/columns/created_at`；[SQL](initial-schema.sql) `mt.task_evidence.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/created_at` (getTaskEvidence) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/task_evidence/columns/updated_at`；[SQL](initial-schema.sql) `mt.task_evidence.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/task_evidence/columns/row_version`；[SQL](initial-schema.sql) `mt.task_evidence.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/version` (getTaskEvidence) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/task_evidence/columns/created_by`；[SQL](initial-schema.sql) `mt.task_evidence.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,link_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)`
- `UNIQUE(case_id,task_id,evidence_id)`

<a id="search_job"></a>
## search_job 异步检索任务

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| search_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/search_job/columns/search_id`；[SQL](initial-schema.sql) `mt.search_job.search_id`；[API](../03-api/openapi.yaml) `/components/schemas/SearchJob/properties/search_id` (getSearchJob)、[API](../03-api/openapi.yaml) `/components/schemas/SearchResults/properties/search_id` (getSearchJob) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/search_job/columns/org_id`；[SQL](initial-schema.sql) `mt.search_job.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/search_job/columns/case_id`；[SQL](initial-schema.sql) `mt.search_job.case_id`；内部字段，无外部API映射 |
| query_asset_id | uuid | 否 | 无 | NOT NULL | 作为检索输入的媒体资产标识，需处于当前授权范围 | [工程定义](table-catalog.json) `/search_job/columns/query_asset_id`；[SQL](initial-schema.sql) `mt.search_job.query_asset_id`；内部字段，无外部API映射 |
| kind | text | 否 | 无 | NOT NULL CHECK(kind IN ('image','image_region','video')) | 检索作业类别，用于区分图片与视频等查询流程 | [工程定义](table-catalog.json) `/search_job/columns/kind`；[SQL](initial-schema.sql) `mt.search_job.kind`；内部字段，无外部API映射 |
| state | text | 否 | 无 | NOT NULL | 异步检索任务的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/search_job/columns/state`；[SQL](initial-schema.sql) `mt.search_job.state`；[API](../03-api/openapi.yaml) `/components/schemas/SearchJob/properties/state` (getSearchJob) |
| index_version | text | 否 | 无 | NOT NULL | 本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本 | [工程定义](table-catalog.json) `/search_job/columns/index_version`；[SQL](initial-schema.sql) `mt.search_job.index_version`；[API](../03-api/openapi.yaml) `/components/schemas/SearchResults/properties/index_version` (getSearchJob) |
| error_code | text | 是 | 无 | 无列级约束 | 失败原因的稳定错误码；无失败时允许NULL，用户说明与诊断堆栈分开 | [工程定义](table-catalog.json) `/search_job/columns/error_code`；[SQL](initial-schema.sql) `mt.search_job.error_code`；[API](../03-api/openapi.yaml) `/components/schemas/SearchJob/properties/error_code` (getSearchJob) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/search_job/columns/created_at`；[SQL](initial-schema.sql) `mt.search_job.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/search_job/columns/updated_at`；[SQL](initial-schema.sql) `mt.search_job.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/search_job/columns/row_version`；[SQL](initial-schema.sql) `mt.search_job.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/search_job/columns/created_by`；[SQL](initial-schema.sql) `mt.search_job.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,search_id)`
- `FOREIGN KEY (case_id, query_asset_id) REFERENCES mt.media_asset (case_id, asset_id)`

<a id="source_match"></a>
## source_match 同源或片段映射候选

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| match_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/source_match/columns/match_id`；[SQL](initial-schema.sql) `mt.source_match.match_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/source_match/columns/org_id`；[SQL](initial-schema.sql) `mt.source_match.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/source_match/columns/case_id`；[SQL](initial-schema.sql) `mt.source_match.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/case_id` (searchImage)、[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/case_id` (searchImageRegion)、[API](../03-api/openapi.yaml) `/components/schemas/VideoSearch/properties/case_id` (searchVideo) |
| search_id | uuid | 否 | 无 | NOT NULL | 产生匹配候选的异步检索作业标识 | [工程定义](table-catalog.json) `/source_match/columns/search_id`；[SQL](initial-schema.sql) `mt.source_match.search_id`；[API](../03-api/openapi.yaml) `/components/schemas/SearchAccepted/properties/search_id` (searchImage)、[API](../03-api/openapi.yaml) `/components/schemas/SearchAccepted/properties/search_id` (searchImageRegion)、[API](../03-api/openapi.yaml) `/components/schemas/SearchAccepted/properties/search_id` (searchVideo)、[API](../03-api/openapi.yaml) `/components/schemas/SearchJob/properties/search_id` (getSearchJob)、[API](../03-api/openapi.yaml) `/components/schemas/SearchResults/properties/search_id` (getSearchJob) |
| query_asset_id | uuid | 否 | 无 | NOT NULL | 作为检索输入的媒体资产标识，需处于当前授权范围 | [工程定义](table-catalog.json) `/source_match/columns/query_asset_id`；[SQL](initial-schema.sql) `mt.source_match.query_asset_id`；内部字段，无外部API映射 |
| candidate_asset_id | uuid | 否 | 无 | NOT NULL | 被检索返回的候选来源媒体资产标识；候选相似不能直接认定同源 | [工程定义](table-catalog.json) `/source_match/columns/candidate_asset_id`；[SQL](initial-schema.sql) `mt.source_match.candidate_asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/SearchCandidate/properties/candidate_asset_id` (getSearchJob) |
| score | double precision | 是 | 无 | CHECK(score>=0 AND score<=1) | 同源或片段映射候选对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较 | [工程定义](table-catalog.json) `/source_match/columns/score`；[SQL](initial-schema.sql) `mt.source_match.score`；[API](../03-api/openapi.yaml) `/components/schemas/SearchCandidate/properties/score` (getSearchJob) |
| verification_type | text | 否 | 无 | NOT NULL CHECK(verification_type IN ('unverified','geometry','temporal','human')) | 支持本匹配结果的验证方法编码，例如几何或时序验证；具体取值见约束 | [工程定义](table-catalog.json) `/source_match/columns/verification_type`；[SQL](initial-schema.sql) `mt.source_match.verification_type`；内部字段，无外部API映射 |
| relation | text | 否 | 无 | NOT NULL CHECK(relation IN ('similar','full_copy','partial_copy','contains','segment_map','unknown')) | 查询与候选媒体间的关系类型，整体同源、局部包含和语义相似必须区分 | [工程定义](table-catalog.json) `/source_match/columns/relation`；[SQL](initial-schema.sql) `mt.source_match.relation`；[API](../03-api/openapi.yaml) `/components/schemas/SearchCandidate/properties/relation` (getSearchJob) |
| query_start_ms | bigint | 是 | 无 | CHECK(query_start_ms>=0) | 查询媒体中匹配片段起点，单位毫秒，半开区间包含起点 | [工程定义](table-catalog.json) `/source_match/columns/query_start_ms`；[SQL](initial-schema.sql) `mt.source_match.query_start_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/start_ms` (getSearchJob) |
| query_end_ms | bigint | 是 | 无 | 无列级约束 | 查询媒体中匹配片段终点，单位毫秒，半开区间不包含终点 | [工程定义](table-catalog.json) `/source_match/columns/query_end_ms`；[SQL](initial-schema.sql) `mt.source_match.query_end_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/end_ms` (getSearchJob) |
| source_start_ms | bigint | 是 | 无 | CHECK(source_start_ms>=0) | 候选来源媒体中匹配片段起点，单位毫秒 | [工程定义](table-catalog.json) `/source_match/columns/source_start_ms`；[SQL](initial-schema.sql) `mt.source_match.source_start_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/start_ms` (getSearchJob) |
| source_end_ms | bigint | 是 | 无 | 无列级约束 | 候选来源媒体中匹配片段终点，单位毫秒，必须大于对应起点 | [工程定义](table-catalog.json) `/source_match/columns/source_end_ms`；[SQL](initial-schema.sql) `mt.source_match.source_end_ms`；[API](../03-api/openapi.yaml) `/components/schemas/TimeRange/properties/end_ms` (getSearchJob) |
| direction | text | 否 | 无 | NOT NULL CHECK(direction IN ('forward','reverse','not_applicable')) | 查询与来源片段的播放对应方向，不改变存储区间起点小于终点的约定 | [工程定义](table-catalog.json) `/source_match/columns/direction`；[SQL](initial-schema.sql) `mt.source_match.direction`；[API](../03-api/openapi.yaml) `/components/schemas/SearchCandidate/properties/direction` (getSearchJob) |
| speed_ratio | double precision | 否 | 无 | NOT NULL CHECK(speed_ratio>0) | 查询片段时长除以来源片段时长的正比例（本轮工程约定）；倒放由direction单独表示，模型适配器负责转换其原生定义 | [工程定义](table-catalog.json) `/source_match/columns/speed_ratio`；[SQL](initial-schema.sql) `mt.source_match.speed_ratio`；[API](../03-api/openapi.yaml) `/components/schemas/SearchCandidate/properties/speed_ratio` (getSearchJob) |
| evidence_refs | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/source_match/columns/evidence_refs`；[SQL](initial-schema.sql) `mt.source_match.evidence_refs`；[API](../03-api/openapi.yaml) `/components/schemas/SearchCandidate/properties/evidence_ids` (getSearchJob) |
| index_version | text | 否 | 无 | NOT NULL | 本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本 | [工程定义](table-catalog.json) `/source_match/columns/index_version`；[SQL](initial-schema.sql) `mt.source_match.index_version`；[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/index_version` (searchImage)、[API](../03-api/openapi.yaml) `/components/schemas/ImageSearch/properties/index_version` (searchImageRegion)、[API](../03-api/openapi.yaml) `/components/schemas/VideoSearch/properties/index_version` (searchVideo)、[API](../03-api/openapi.yaml) `/components/schemas/SearchResults/properties/index_version` (getSearchJob) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/source_match/columns/created_at`；[SQL](initial-schema.sql) `mt.source_match.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/source_match/columns/updated_at`；[SQL](initial-schema.sql) `mt.source_match.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/source_match/columns/row_version`；[SQL](initial-schema.sql) `mt.source_match.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/source_match/columns/created_by`；[SQL](initial-schema.sql) `mt.source_match.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,match_id)`
- `FOREIGN KEY (case_id, search_id) REFERENCES mt.search_job (case_id, search_id)`
- `FOREIGN KEY (case_id, query_asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `FOREIGN KEY (case_id, candidate_asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `CHECK(query_asset_id<>candidate_asset_id)`
- `CHECK((query_start_ms IS NULL AND query_end_ms IS NULL) OR (query_start_ms IS NOT NULL AND query_end_ms IS NOT NULL AND query_end_ms>query_start_ms))`
- `CHECK((source_start_ms IS NULL AND source_end_ms IS NULL) OR (source_start_ms IS NOT NULL AND source_end_ms IS NOT NULL AND source_end_ms>source_start_ms))`

<a id="content_cluster"></a>
## content_cluster 高可信整内容簇

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| cluster_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/content_cluster/columns/cluster_id`；[SQL](initial-schema.sql) `mt.content_cluster.cluster_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/content_cluster/columns/org_id`；[SQL](initial-schema.sql) `mt.content_cluster.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/content_cluster/columns/case_id`；[SQL](initial-schema.sql) `mt.content_cluster.case_id`；内部字段，无外部API映射 |
| scope | text | 否 | 无 | NOT NULL | 内容簇覆盖的比较范围标识或说明；整体同源与指定片段范围必须区分 | [工程定义](table-catalog.json) `/content_cluster/columns/scope`；[SQL](initial-schema.sql) `mt.content_cluster.scope`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/scope` (getFirstSource) |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/content_cluster/columns/policy_version`；[SQL](initial-schema.sql) `mt.content_cluster.policy_version`；内部字段，无外部API映射 |
| status | text | 否 | 无 | NOT NULL | 高可信整内容簇的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/content_cluster/columns/status`；[SQL](initial-schema.sql) `mt.content_cluster.status`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/content_cluster/columns/created_at`；[SQL](initial-schema.sql) `mt.content_cluster.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/content_cluster/columns/updated_at`；[SQL](initial-schema.sql) `mt.content_cluster.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/content_cluster/columns/row_version`；[SQL](initial-schema.sql) `mt.content_cluster.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/content_cluster/columns/created_by`；[SQL](initial-schema.sql) `mt.content_cluster.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,cluster_id)`

<a id="cluster_member"></a>
## cluster_member 簇成员整内容证据

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| member_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/cluster_member/columns/member_id`；[SQL](initial-schema.sql) `mt.cluster_member.member_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/cluster_member/columns/org_id`；[SQL](initial-schema.sql) `mt.cluster_member.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/cluster_member/columns/case_id`；[SQL](initial-schema.sql) `mt.cluster_member.case_id`；内部字段，无外部API映射 |
| cluster_id | uuid | 否 | 无 | NOT NULL | 高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证 | [工程定义](table-catalog.json) `/cluster_member/columns/cluster_id`；[SQL](initial-schema.sql) `mt.cluster_member.cluster_id`；内部字段，无外部API映射 |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/cluster_member/columns/asset_id`；[SQL](initial-schema.sql) `mt.cluster_member.asset_id`；内部字段，无外部API映射 |
| relation | text | 否 | 无 | NOT NULL CHECK(relation IN ('full_copy')) | 成员与整内容簇的关系；当前只允许full_copy，片段拼接不能加入为整内容成员 | [工程定义](table-catalog.json) `/cluster_member/columns/relation`；[SQL](initial-schema.sql) `mt.cluster_member.relation`；内部字段，无外部API映射 |
| evidence_id | uuid | 否 | 无 | NOT NULL | 所引用证据事实版本标识，指向同案件evidence_item.evidence_id | [工程定义](table-catalog.json) `/cluster_member/columns/evidence_id`；[SQL](initial-schema.sql) `mt.cluster_member.evidence_id`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/cluster_member/columns/created_at`；[SQL](initial-schema.sql) `mt.cluster_member.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/cluster_member/columns/updated_at`；[SQL](initial-schema.sql) `mt.cluster_member.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/cluster_member/columns/row_version`；[SQL](initial-schema.sql) `mt.cluster_member.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/cluster_member/columns/created_by`；[SQL](initial-schema.sql) `mt.cluster_member.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,member_id)`
- `FOREIGN KEY (case_id, cluster_id) REFERENCES mt.content_cluster (case_id, cluster_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)`
- `UNIQUE(case_id,cluster_id,asset_id)`

<a id="first_source_candidate"></a>
## first_source_candidate 首发候选及覆盖范围

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| candidate_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/first_source_candidate/columns/candidate_id`；[SQL](initial-schema.sql) `mt.first_source_candidate.candidate_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/first_source_candidate/columns/org_id`；[SQL](initial-schema.sql) `mt.first_source_candidate.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/first_source_candidate/columns/case_id`；[SQL](initial-schema.sql) `mt.first_source_candidate.case_id`；内部字段，无外部API映射 |
| cluster_id | uuid | 否 | 无 | NOT NULL | 高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证 | [工程定义](table-catalog.json) `/first_source_candidate/columns/cluster_id`；[SQL](initial-schema.sql) `mt.first_source_candidate.cluster_id`；内部字段，无外部API映射 |
| asset_id | uuid | 否 | 无 | NOT NULL | 本批次列为首发候选的媒体资产标识；必须属于同案件及本簇cluster_member，不能引用簇外素材 | [工程定义](table-catalog.json) `/first_source_candidate/columns/asset_id`；[SQL](initial-schema.sql) `mt.first_source_candidate.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidates/items/properties/asset_id` (getFirstSource) |
| rank | integer | 否 | 无 | NOT NULL CHECK(rank BETWEEN 1 AND 3) | 本次排序批次内的候选名次，从1连续排列到候选数量，最多3；不是确定首发结论 | [工程定义](table-catalog.json) `/first_source_candidate/columns/rank`；[SQL](initial-schema.sql) `mt.first_source_candidate.rank`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidates/items/properties/rank` (getFirstSource) |
| probability | double precision | 是 | 无 | CHECK(probability>=0 AND probability<=1) | 已校准的候选可信度，范围0至1；未校准为NULL，不用于替代候选名次或确定首发结论 | [工程定义](table-catalog.json) `/first_source_candidate/columns/probability`；[SQL](initial-schema.sql) `mt.first_source_candidate.probability`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidates/items/properties/probability` (getFirstSource) |
| published_at | timestamptz | 是 | 无 | 无列级约束 | 可核查的来源发布时间；未知为NULL，不用发现时间或当前时间填补；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/first_source_candidate/columns/published_at`；[SQL](initial-schema.sql) `mt.first_source_candidate.published_at`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidates/items/properties/published_at` (getFirstSource) |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/first_source_candidate/columns/model_version`；[SQL](initial-schema.sql) `mt.first_source_candidate.model_version`；内部字段，无外部API映射 |
| evidence_refs | jsonb | 否 | 无 | NOT NULL | 首发候选证据对象，必须包含evidence_ids和counter_evidence_ids两个数组且无额外键；支持证据至少1项，各数组内UUID不可重复。SQL插入触发器核验ID格式、存在及同案件；证据是否有效支持该候选、实际用途授权与引用语义仍由应用复核 | [工程定义](table-catalog.json) `/first_source_candidate/columns/evidence_refs`；[SQL](initial-schema.sql) `mt.first_source_candidate.evidence_refs`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidates/items/properties/evidence_ids` (getFirstSource)、[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidates/items/properties/counter_evidence_ids` (getFirstSource) |
| coverage_note | text | 否 | 无 | NOT NULL | 本次观察的平台、时间和素材覆盖范围及缺失说明；不能声称覆盖未知全网 | [工程定义](table-catalog.json) `/first_source_candidate/columns/coverage_note`；[SQL](initial-schema.sql) `mt.first_source_candidate.coverage_note`；内部字段，无外部API映射 |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')) | 首发候选及覆盖范围的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/first_source_candidate/columns/status`；[SQL](initial-schema.sql) `mt.first_source_candidate.status`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/first_source_candidate/columns/created_at`；[SQL](initial-schema.sql) `mt.first_source_candidate.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/first_source_candidate/columns/updated_at`；[SQL](initial-schema.sql) `mt.first_source_candidate.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/first_source_candidate/columns/row_version`；[SQL](initial-schema.sql) `mt.first_source_candidate.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/first_source_candidate/columns/created_by`；[SQL](initial-schema.sql) `mt.first_source_candidate.created_by`；内部字段，无外部API映射 |
| ranking_id | uuid | 否 | 无 | NOT NULL | 所属首发排序快照ID；与案件及簇共同绑定first_source_ranking，不能混合不同计算结果 | [工程定义](table-catalog.json) `/first_source_candidate/columns/ranking_id`；[SQL](initial-schema.sql) `mt.first_source_candidate.ranking_id`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidates` (getFirstSource) |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,candidate_id)`
- `FOREIGN KEY (case_id, cluster_id) REFERENCES mt.content_cluster (case_id, cluster_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`
- `FOREIGN KEY(case_id,ranking_id,cluster_id) REFERENCES mt.first_source_ranking(case_id,ranking_id,cluster_id)`
- `FOREIGN KEY(case_id,cluster_id,asset_id) REFERENCES mt.cluster_member(case_id,cluster_id,asset_id)`
- `UNIQUE(case_id,ranking_id,rank)`
- `UNIQUE(case_id,ranking_id,asset_id)`

排序、证据引用与事务完整性由[first-source-ranking.md](first-source-ranking.md)所列触发器执行。证据ID存在不等于证据支持或用途合法。

<a id="propagation_node"></a>
## propagation_node 传播图节点

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| node_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/propagation_node/columns/node_id`；[SQL](initial-schema.sql) `mt.propagation_node.node_id`；[API](../03-api/openapi.yaml) `/components/schemas/GraphNode/properties/node_id` (getPropagation) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/propagation_node/columns/org_id`；[SQL](initial-schema.sql) `mt.propagation_node.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/propagation_node/columns/case_id`；[SQL](initial-schema.sql) `mt.propagation_node.case_id`；内部字段，无外部API映射 |
| cluster_id | uuid | 否 | 无 | NOT NULL | 高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证 | [工程定义](table-catalog.json) `/propagation_node/columns/cluster_id`；[SQL](initial-schema.sql) `mt.propagation_node.cluster_id`；[API](../03-api/openapi.yaml) `/components/schemas/Graph/properties/cluster_id` (getPropagation) |
| type | text | 否 | 无 | NOT NULL | 传播图节点类型，决定其展示及业务对象解释 | [工程定义](table-catalog.json) `/propagation_node/columns/type`；[SQL](initial-schema.sql) `mt.propagation_node.type`；[API](../03-api/openapi.yaml) `/components/schemas/GraphNode/properties/type` (getPropagation) |
| display_label | text | 否 | 无 | NOT NULL | 传播图节点的人类可读展示标签，不作为节点主键或关系证据 | [工程定义](table-catalog.json) `/propagation_node/columns/display_label`；[SQL](initial-schema.sql) `mt.propagation_node.display_label`；[API](../03-api/openapi.yaml) `/components/schemas/GraphNode/properties/display_label` (getPropagation) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/propagation_node/columns/created_at`；[SQL](initial-schema.sql) `mt.propagation_node.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/propagation_node/columns/updated_at`；[SQL](initial-schema.sql) `mt.propagation_node.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/propagation_node/columns/row_version`；[SQL](initial-schema.sql) `mt.propagation_node.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Graph/properties/version` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/version` (getPropagation) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/propagation_node/columns/created_by`；[SQL](initial-schema.sql) `mt.propagation_node.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,node_id)`
- `FOREIGN KEY (case_id, cluster_id) REFERENCES mt.content_cluster (case_id, cluster_id)`

<a id="propagation_edge"></a>
## propagation_edge 显式推断传播边

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| edge_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/propagation_edge/columns/edge_id`；[SQL](initial-schema.sql) `mt.propagation_edge.edge_id`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/edge_id` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/edge_id` (decidePropagationEdge) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/propagation_edge/columns/org_id`；[SQL](initial-schema.sql) `mt.propagation_edge.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/propagation_edge/columns/case_id`；[SQL](initial-schema.sql) `mt.propagation_edge.case_id`；内部字段，无外部API映射 |
| from_node_id | uuid | 否 | 无 | NOT NULL | 传播关系起点节点标识 | [工程定义](table-catalog.json) `/propagation_edge/columns/from_node_id`；[SQL](initial-schema.sql) `mt.propagation_edge.from_node_id`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/from_node_id` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/from_node_id` (decidePropagationEdge) |
| to_node_id | uuid | 否 | 无 | NOT NULL | 传播关系终点节点标识 | [工程定义](table-catalog.json) `/propagation_edge/columns/to_node_id`；[SQL](initial-schema.sql) `mt.propagation_edge.to_node_id`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/to_node_id` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/to_node_id` (decidePropagationEdge) |
| relation | text | 否 | 无 | NOT NULL | 传播关系类别；是否事实另由origin和证据决定 | [工程定义](table-catalog.json) `/propagation_edge/columns/relation`；[SQL](initial-schema.sql) `mt.propagation_edge.relation`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/relation` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/relation` (decidePropagationEdge) |
| origin | text | 否 | 无 | NOT NULL CHECK(origin IN ('observed','inferred','human')) | 传播边依据类别，区分明确记录与算法推断；推断不能展示为事实 | [工程定义](table-catalog.json) `/propagation_edge/columns/origin`；[SQL](initial-schema.sql) `mt.propagation_edge.origin`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/origin` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/origin` (decidePropagationEdge) |
| probability | double precision | 是 | 无 | CHECK(probability>=0 AND probability<=1) | 传播关系推断的已校准概率，范围0至1；未校准时为NULL，不能据此把推断边改成事实边 | [工程定义](table-catalog.json) `/propagation_edge/columns/probability`；[SQL](initial-schema.sql) `mt.propagation_edge.probability`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/probability` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/probability` (decidePropagationEdge) |
| evidence_refs | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/propagation_edge/columns/evidence_refs`；[SQL](initial-schema.sql) `mt.propagation_edge.evidence_refs`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/evidence_ids` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphDecision/properties/evidence_ids` (decidePropagationEdge)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/evidence_ids` (decidePropagationEdge) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('candidate','confirmed','rejected')) | 显式推断传播边的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/propagation_edge/columns/state`；[SQL](initial-schema.sql) `mt.propagation_edge.state`；[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/state` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/state` (decidePropagationEdge) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/propagation_edge/columns/created_at`；[SQL](initial-schema.sql) `mt.propagation_edge.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/propagation_edge/columns/updated_at`；[SQL](initial-schema.sql) `mt.propagation_edge.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/propagation_edge/columns/row_version`；[SQL](initial-schema.sql) `mt.propagation_edge.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Graph/properties/version` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/version` (getPropagation)、[API](../03-api/openapi.yaml) `/components/schemas/GraphDecision/properties/expected_version` (decidePropagationEdge)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/version` (decidePropagationEdge) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/propagation_edge/columns/created_by`；[SQL](initial-schema.sql) `mt.propagation_edge.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,edge_id)`
- `FOREIGN KEY (case_id, from_node_id) REFERENCES mt.propagation_node (case_id, node_id)`
- `FOREIGN KEY (case_id, to_node_id) REFERENCES mt.propagation_node (case_id, node_id)`
- `CHECK(from_node_id<>to_node_id)`

<a id="claim"></a>
## claim 结构化主张与来源

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| claim_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/claim/columns/claim_id`；[SQL](initial-schema.sql) `mt.claim.claim_id`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/claim_id` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/Relation/properties/claim_id` (verifyClaim) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/claim/columns/org_id`；[SQL](initial-schema.sql) `mt.claim.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/claim/columns/case_id`；[SQL](initial-schema.sql) `mt.claim.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ClaimExtract/properties/case_id` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/case_id` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/ClaimVerify/properties/case_id` (verifyClaim) |
| asset_id | uuid | 否 | 无 | NOT NULL | 本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用 | [工程定义](table-catalog.json) `/claim/columns/asset_id`；[SQL](initial-schema.sql) `mt.claim.asset_id`；[API](../03-api/openapi.yaml) `/components/schemas/ClaimExtract/properties/asset_id` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/asset_id` (extractClaims) |
| subject | text | 是 | 无 | 无列级约束 | 结构化主张中的主体表述，来自原文或模型抽取；不能当用户身份 | [工程定义](table-catalog.json) `/claim/columns/subject`；[SQL](initial-schema.sql) `mt.claim.subject`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/subject` (extractClaims) |
| action | text | 是 | 无 | 无列级约束 | 主张所描述行为或审计动作编码，具体语义由本表决定 | [工程定义](table-catalog.json) `/claim/columns/action`；[SQL](initial-schema.sql) `mt.claim.action`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/action` (extractClaims) |
| claim_time | text | 是 | 无 | 无列级约束 | 主张原文中的时间表述，可能含模糊日期；未知为NULL，不强行转成精确时间戳 | [工程定义](table-catalog.json) `/claim/columns/claim_time`；[SQL](initial-schema.sql) `mt.claim.claim_time`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/time` (extractClaims) |
| place | text | 是 | 无 | 无列级约束 | 主张原文中的地点表述；未知为空，不自动地理定位 | [工程定义](table-catalog.json) `/claim/columns/place`；[SQL](initial-schema.sql) `mt.claim.place`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/place` (extractClaims) |
| result | text | 是 | 无 | 无列级约束 | 主张所陈述的结果，不代表系统已核实为真 | [工程定义](table-catalog.json) `/claim/columns/result`；[SQL](initial-schema.sql) `mt.claim.result`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/result` (extractClaims) |
| source_segment_refs | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 主张对应文本或媒体片段引用对象，需定位到资产、片段和时间或字符范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/claim/columns/source_segment_refs`；[SQL](initial-schema.sql) `mt.claim.source_segment_refs`；[API](../03-api/openapi.yaml) `/components/schemas/ClaimExtract/properties/source_segment_ids` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/source_segment_ids` (extractClaims) |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/claim/columns/model_version`；[SQL](initial-schema.sql) `mt.claim.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/Claim/properties/model_version` (extractClaims)、[API](../03-api/openapi.yaml) `/components/schemas/Relation/properties/model_version` (verifyClaim) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/claim/columns/created_at`；[SQL](initial-schema.sql) `mt.claim.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/claim/columns/updated_at`；[SQL](initial-schema.sql) `mt.claim.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/claim/columns/row_version`；[SQL](initial-schema.sql) `mt.claim.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/claim/columns/created_by`；[SQL](initial-schema.sql) `mt.claim.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,claim_id)`
- `FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)`

<a id="claim_evidence_relation"></a>
## claim_evidence_relation 主张证据关系

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| relation_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/relation_id`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.relation_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/org_id`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/case_id`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ClaimVerify/properties/case_id` (verifyClaim) |
| claim_id | uuid | 否 | 无 | NOT NULL | 被证据支持、反对或关联的主张标识 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/claim_id`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.claim_id`；[API](../03-api/openapi.yaml) `/components/schemas/Relation/properties/claim_id` (verifyClaim) |
| evidence_id | uuid | 否 | 无 | NOT NULL | 所引用证据事实版本标识，指向同案件evidence_item.evidence_id | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/evidence_id`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.evidence_id`；[API](../03-api/openapi.yaml) `/components/schemas/ClaimVerify/properties/evidence_ids` (verifyClaim)、[API](../03-api/openapi.yaml) `/components/schemas/Relation/properties/evidence_ids` (verifyClaim) |
| relation | text | 否 | 无 | NOT NULL CHECK(relation IN ('supports','contradicts','partially_supports','unrelated','insufficient')) | 主张与证据的关系类别，支持、反对或不足等取值以CHECK枚举为准 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/relation`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.relation`；[API](../03-api/openapi.yaml) `/components/schemas/Relation/properties/relation` (verifyClaim) |
| score | double precision | 是 | 无 | CHECK(score>=0 AND score<=1) | 主张证据关系对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/score`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.score`；[API](../03-api/openapi.yaml) `/components/schemas/Relation/properties/score` (verifyClaim) |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/model_version`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/Relation/properties/model_version` (verifyClaim) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/created_at`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/updated_at`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/row_version`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/claim_evidence_relation/columns/created_by`；[SQL](initial-schema.sql) `mt.claim_evidence_relation.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,relation_id)`
- `FOREIGN KEY (case_id, claim_id) REFERENCES mt.claim (case_id, claim_id)`
- `FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)`

<a id="approval_request"></a>
## approval_request 按目的独立审批申请

范围：org；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| approval_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/approval_request/columns/approval_id`；[SQL](initial-schema.sql) `mt.approval_request.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/approval_id` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/approval_id` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/approval_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/approval_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/FeedbackRecord/properties/approval_id` (requestFeedback)、[API](../03-api/openapi.yaml) `/components/schemas/Rollout/properties/approval_id` (rolloutModel) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/approval_request/columns/org_id`；[SQL](initial-schema.sql) `mt.approval_request.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 是 | 无 | 无列级约束 | 案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限 | [工程定义](table-catalog.json) `/approval_request/columns/case_id`；[SQL](initial-schema.sql) `mt.approval_request.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/case_id` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/case_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/case_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/case_id` (requestFeedback) |
| object_type | text | 否 | 无 | NOT NULL | 审批或审计目标对象类型，决定object_id应指向哪种业务对象 | [工程定义](table-catalog.json) `/approval_request/columns/object_type`；[SQL](initial-schema.sql) `mt.approval_request.object_type`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/object_type` (requestApproval) |
| object_id | uuid | 否 | 无 | NOT NULL | 该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键 | [工程定义](table-catalog.json) `/approval_request/columns/object_id`；[SQL](initial-schema.sql) `mt.approval_request.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/object_id` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/object_id` (rolloutModel) |
| object_version | bigint | 否 | 无 | NOT NULL CHECK(object_version>0) | 审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批 | [工程定义](table-catalog.json) `/approval_request/columns/object_version`；[SQL](initial-schema.sql) `mt.approval_request.object_version`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/object_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/object_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/object_version` (decideApproval) |
| purpose | text | 否 | 无 | NOT NULL | 本记录声明或申请的处理用途，实际动作需与有效授权用途相符 | [工程定义](table-catalog.json) `/approval_request/columns/purpose`；[SQL](initial-schema.sql) `mt.approval_request.purpose`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/purpose` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/purpose` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/purpose` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/purpose` (requestFeedback) |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/approval_request/columns/policy_version`；[SQL](initial-schema.sql) `mt.approval_request.policy_version`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/policy_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/policy_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/policy_version` (decideApproval) |
| requested_by | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 审批申请人的认证主体标识，由服务端设置 | [工程定义](table-catalog.json) `/approval_request/columns/requested_by`；[SQL](initial-schema.sql) `mt.approval_request.requested_by`；内部字段，无外部API映射 |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('REQUESTED','APPROVED','REJECTED','RETURNED','REVOKED','EXPIRED','INVALIDATED')) | 按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/approval_request/columns/state`；[SQL](initial-schema.sql) `mt.approval_request.state`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/state` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/state` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/state` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/FeedbackRecord/properties/state` (requestFeedback)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/state` (rolloutModel) |
| expires_at | timestamptz | 是 | 无 | 无列级约束 | 此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/approval_request/columns/expires_at`；[SQL](initial-schema.sql) `mt.approval_request.expires_at`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/expires_at` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/expires_at` (decideApproval) |
| reason | text | 否 | 无 | NOT NULL | 状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密 | [工程定义](table-catalog.json) `/approval_request/columns/reason`；[SQL](initial-schema.sql) `mt.approval_request.reason`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/reason` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ApprovalDecision/properties/reason` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/reason` (requestFeedback) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/approval_request/columns/created_at`；[SQL](initial-schema.sql) `mt.approval_request.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/created_at` (createReport) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/approval_request/columns/updated_at`；[SQL](initial-schema.sql) `mt.approval_request.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/approval_request/columns/row_version`；[SQL](initial-schema.sql) `mt.approval_request.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ApprovalDecision/properties/expected_version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/FeedbackRecord/properties/version` (requestFeedback)、[API](../03-api/openapi.yaml) `/components/schemas/Rollout/properties/expected_version` (rolloutModel)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/version` (rolloutModel) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/approval_request/columns/created_by`；[SQL](initial-schema.sql) `mt.approval_request.created_by`；内部字段，无外部API映射 |
| run_version | bigint | 是 | 无 | CHECK(run_version>0) | 分析对象绑定运行版本 | [工程定义](table-catalog.json) `/approval_request/columns/run_version`；[SQL](initial-schema.sql) `mt.approval_request.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/run_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/run_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/run_version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/run_version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/run_version` (createReport) |
| result_version | bigint | 是 | 无 | CHECK(result_version>0) | 分析对象绑定结果版本 | [工程定义](table-catalog.json) `/approval_request/columns/result_version`；[SQL](initial-schema.sql) `mt.approval_request.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/object_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ApprovalCreate/properties/result_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/object_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/result_version` (requestApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/object_version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/result_version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/result_version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/result_version` (createReport) |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `UNIQUE(case_id,approval_id)`
- `UNIQUE(org_id,approval_id)`
- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `CHECK((object_type='model_release' AND case_id IS NULL) OR (object_type<>'model_release' AND case_id IS NOT NULL))`
- `CHECK(object_type<>'task' OR (run_version IS NOT NULL AND result_version IS NOT NULL))`

<a id="approval_decision"></a>
## approval_decision 审批历史决定

范围：org；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| decision_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/approval_decision/columns/decision_id`；[SQL](initial-schema.sql) `mt.approval_decision.decision_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/approval_decision/columns/org_id`；[SQL](initial-schema.sql) `mt.approval_decision.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 是 | 无 | 无列级约束 | 案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限 | [工程定义](table-catalog.json) `/approval_decision/columns/case_id`；[SQL](initial-schema.sql) `mt.approval_decision.case_id`；内部字段，无外部API映射 |
| approval_id | uuid | 否 | 无 | NOT NULL | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/approval_decision/columns/approval_id`；[SQL](initial-schema.sql) `mt.approval_decision.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/approval_id` (decideApproval) |
| decision | text | 否 | 无 | NOT NULL CHECK(decision IN ('approve','reject','return','revoke','invalidate')) | 本次审批决定；取值由CHECK限制，不能替代对象版本和权限校验 | [工程定义](table-catalog.json) `/approval_decision/columns/decision`；[SQL](initial-schema.sql) `mt.approval_decision.decision`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalDecision/properties/decision` (decideApproval) |
| decision_actor_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 作出审批决定的用户标识，由认证上下文与职责分离规则核验 | [工程定义](table-catalog.json) `/approval_decision/columns/decision_actor_id`；[SQL](initial-schema.sql) `mt.approval_decision.decision_actor_id`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/decision_actor_id` (decideApproval) |
| reason | text | 否 | 无 | NOT NULL | 状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密 | [工程定义](table-catalog.json) `/approval_decision/columns/reason`；[SQL](initial-schema.sql) `mt.approval_decision.reason`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalDecision/properties/reason` (decideApproval) |
| evidence_refs | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/approval_decision/columns/evidence_refs`；[SQL](initial-schema.sql) `mt.approval_decision.evidence_refs`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalDecision/properties/evidence_ids` (decideApproval) |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/approval_decision/columns/policy_version`；[SQL](initial-schema.sql) `mt.approval_decision.policy_version`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/policy_version` (decideApproval) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/approval_decision/columns/created_at`；[SQL](initial-schema.sql) `mt.approval_decision.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/approval_decision/columns/updated_at`；[SQL](initial-schema.sql) `mt.approval_decision.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/approval_decision/columns/row_version`；[SQL](initial-schema.sql) `mt.approval_decision.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalDecision/properties/expected_version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/version` (decideApproval) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/approval_decision/columns/created_by`；[SQL](initial-schema.sql) `mt.approval_decision.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `FOREIGN KEY(org_id,approval_id) REFERENCES mt.approval_request(org_id,approval_id)`
- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`

<a id="operation_token"></a>
## operation_token 一次性确认授权记录

范围：org；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| token_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/operation_token/columns/token_id`；[SQL](initial-schema.sql) `mt.operation_token.token_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/operation_token/columns/org_id`；[SQL](initial-schema.sql) `mt.operation_token.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 是 | 无 | 无列级约束 | 案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限 | [工程定义](table-catalog.json) `/operation_token/columns/case_id`；[SQL](initial-schema.sql) `mt.operation_token.case_id`；内部字段，无外部API映射 |
| approval_id | uuid | 否 | 无 | NOT NULL | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/operation_token/columns/approval_id`；[SQL](initial-schema.sql) `mt.operation_token.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/OperationTokenRequest/properties/approval_id` (issueOperationToken) |
| actor_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 操作主体标识；从服务端认证上下文取得，系统动作的可空条件须另有审计规则 | [工程定义](table-catalog.json) `/operation_token/columns/actor_id`；[SQL](initial-schema.sql) `mt.operation_token.actor_id`；内部字段，无外部API映射 |
| purpose | text | 否 | 无 | NOT NULL | 本记录声明或申请的处理用途，实际动作需与有效授权用途相符 | [工程定义](table-catalog.json) `/operation_token/columns/purpose`；[SQL](initial-schema.sql) `mt.operation_token.purpose`；[API](../03-api/openapi.yaml) `/components/schemas/OperationTokenRequest/properties/purpose` (issueOperationToken) |
| object_id | uuid | 否 | 无 | NOT NULL | 该记录绑定的业务目标对象ID；沿用关联审批请求的对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键 | [工程定义](table-catalog.json) `/operation_token/columns/object_id`；[SQL](initial-schema.sql) `mt.operation_token.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/OperationTokenRequest/properties/object_id` (issueOperationToken) |
| object_version | bigint | 否 | 无 | NOT NULL CHECK(object_version>0) | 审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批 | [工程定义](table-catalog.json) `/operation_token/columns/object_version`；[SQL](initial-schema.sql) `mt.operation_token.object_version`；[API](../03-api/openapi.yaml) `/components/schemas/OperationTokenRequest/properties/object_version` (issueOperationToken)、[API](../03-api/openapi.yaml) `/components/schemas/OperationToken/properties/object_version` (issueOperationToken) |
| token_sha256 | text | 否 | 无 | NOT NULL CHECK(token_sha256 ~ '^[a-f0-9]{64}$') | 一次性操作凭据的SHA-256，不保存明文凭据，不能代替有效期与消费检查；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/operation_token/columns/token_sha256`；[SQL](initial-schema.sql) `mt.operation_token.token_sha256`；内部字段，无外部API映射 |
| expires_at | timestamptz | 否 | 无 | NOT NULL | 此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/operation_token/columns/expires_at`；[SQL](initial-schema.sql) `mt.operation_token.expires_at`；[API](../03-api/openapi.yaml) `/components/schemas/OperationToken/properties/expires_at` (issueOperationToken) |
| consumed_at | timestamptz | 是 | 无 | 无列级约束 | 一次性操作凭据被消费的时刻；非空后不得重用；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/operation_token/columns/consumed_at`；[SQL](initial-schema.sql) `mt.operation_token.consumed_at`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/operation_token/columns/created_at`；[SQL](initial-schema.sql) `mt.operation_token.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/operation_token/columns/updated_at`；[SQL](initial-schema.sql) `mt.operation_token.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/operation_token/columns/row_version`；[SQL](initial-schema.sql) `mt.operation_token.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/operation_token/columns/created_by`；[SQL](initial-schema.sql) `mt.operation_token.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `UNIQUE(token_sha256)`
- `FOREIGN KEY(org_id,approval_id) REFERENCES mt.approval_request(org_id,approval_id)`
- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`

<a id="review_record"></a>
## review_record 业务复核事实

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| review_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/review_record/columns/review_id`；[SQL](initial-schema.sql) `mt.review_record.review_id`；[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/review_id` (createReview) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/review_record/columns/org_id`；[SQL](initial-schema.sql) `mt.review_record.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/review_record/columns/case_id`；[SQL](initial-schema.sql) `mt.review_record.case_id`；内部字段，无外部API映射 |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/review_record/columns/task_id`；[SQL](initial-schema.sql) `mt.review_record.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/task_id` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/task_id` (createReview) |
| run_version | bigint | 否 | 无 | NOT NULL | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/review_record/columns/run_version`；[SQL](initial-schema.sql) `mt.review_record.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/run_version` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/run_version` (createReview) |
| result_version | bigint | 否 | 无 | NOT NULL | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/review_record/columns/result_version`；[SQL](initial-schema.sql) `mt.review_record.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/result_version` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/result_version` (createReview) |
| reviewer_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 执行本次业务复核的用户标识，需有对应功能和案件权限 | [工程定义](table-catalog.json) `/review_record/columns/reviewer_id`；[SQL](initial-schema.sql) `mt.review_record.reviewer_id`；[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/reviewer_id` (createReview) |
| decision | text | 否 | 无 | NOT NULL CHECK(decision IN ('confirm_candidate','reject_candidate','return_for_evidence','request_rerun')) | 本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验 | [工程定义](table-catalog.json) `/review_record/columns/decision`；[SQL](initial-schema.sql) `mt.review_record.decision`；[API](../03-api/openapi.yaml) `/components/schemas/GraphDecision/properties/decision` (decidePropagationEdge)、[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/decision` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/decision` (createReview) |
| comments | text | 否 | 无 | NOT NULL | 复核意见原文，说明证据取舍及处理理由，后续更正追加版本 | [工程定义](table-catalog.json) `/review_record/columns/comments`；[SQL](initial-schema.sql) `mt.review_record.comments`；[API](../03-api/openapi.yaml) `/components/schemas/GraphDecision/properties/reason` (decidePropagationEdge)、[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/reason` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/reason` (createReview) |
| review_version | bigint | 否 | 无 | NOT NULL CHECK(review_version>0) | 针对结果形成的复核版本号，复核更正不能覆盖历史记录 | [工程定义](table-catalog.json) `/review_record/columns/review_version`；[SQL](initial-schema.sql) `mt.review_record.review_version`；[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/expected_review_version` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/expected_review_version` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/review_version` (createReview) |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/review_record/columns/policy_version`；[SQL](initial-schema.sql) `mt.review_record.policy_version`；[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/policy_version` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/policy_version` (createReview) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/review_record/columns/created_at`；[SQL](initial-schema.sql) `mt.review_record.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/created_at` (createReview) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/review_record/columns/updated_at`；[SQL](initial-schema.sql) `mt.review_record.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/review_record/columns/row_version`；[SQL](initial-schema.sql) `mt.review_record.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/GraphDecision/properties/expected_version` (decidePropagationEdge)、[API](../03-api/openapi.yaml) `/components/schemas/GraphEdge/properties/version` (decidePropagationEdge) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/review_record/columns/created_by`；[SQL](initial-schema.sql) `mt.review_record.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,review_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)`
- `UNIQUE(case_id,task_id,review_version)`

<a id="review_evidence"></a>
## review_evidence 复核证据引用

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| link_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/review_evidence/columns/link_id`；[SQL](initial-schema.sql) `mt.review_evidence.link_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/review_evidence/columns/org_id`；[SQL](initial-schema.sql) `mt.review_evidence.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/review_evidence/columns/case_id`；[SQL](initial-schema.sql) `mt.review_evidence.case_id`；内部字段，无外部API映射 |
| review_id | uuid | 否 | 无 | NOT NULL | 所引用业务复核记录标识 | [工程定义](table-catalog.json) `/review_evidence/columns/review_id`；[SQL](initial-schema.sql) `mt.review_evidence.review_id`；[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/review_id` (createReview) |
| evidence_id | uuid | 否 | 无 | NOT NULL | 所引用证据事实版本标识，指向同案件evidence_item.evidence_id | [工程定义](table-catalog.json) `/review_evidence/columns/evidence_id`；[SQL](initial-schema.sql) `mt.review_evidence.evidence_id`；[API](../03-api/openapi.yaml) `/components/schemas/ReviewCreate/properties/evidence_ids` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/evidence_ids` (createReview) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/review_evidence/columns/created_at`；[SQL](initial-schema.sql) `mt.review_evidence.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/created_at` (createReview) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/review_evidence/columns/updated_at`；[SQL](initial-schema.sql) `mt.review_evidence.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/review_evidence/columns/row_version`；[SQL](initial-schema.sql) `mt.review_evidence.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/review_evidence/columns/created_by`；[SQL](initial-schema.sql) `mt.review_evidence.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,link_id)`
- `FOREIGN KEY (case_id, review_id) REFERENCES mt.review_record (case_id, review_id)`
- `FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)`

<a id="evidence_package"></a>
## evidence_package 固化证据包版本

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| package_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/evidence_package/columns/package_id`；[SQL](initial-schema.sql) `mt.evidence_package.package_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/package_id` (sealEvidence) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/evidence_package/columns/org_id`；[SQL](initial-schema.sql) `mt.evidence_package.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/evidence_package/columns/case_id`；[SQL](initial-schema.sql) `mt.evidence_package.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/case_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/case_id` (sealEvidence) |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/evidence_package/columns/task_id`；[SQL](initial-schema.sql) `mt.evidence_package.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/SealRequest/properties/task_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/task_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/task_id` (sealEvidence) |
| run_version | bigint | 否 | 无 | NOT NULL | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/evidence_package/columns/run_version`；[SQL](initial-schema.sql) `mt.evidence_package.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/SealRequest/properties/run_version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/run_version` (sealEvidence) |
| result_version | bigint | 否 | 无 | NOT NULL | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/evidence_package/columns/result_version`；[SQL](initial-schema.sql) `mt.evidence_package.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/SealRequest/properties/result_version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/result_version` (sealEvidence) |
| version | bigint | 否 | 无 | NOT NULL CHECK(version>0) | 此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version | [工程定义](table-catalog.json) `/evidence_package/columns/version`；[SQL](initial-schema.sql) `mt.evidence_package.version`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/version` (sealEvidence) |
| manifest_sha256 | text | 否 | 无 | NOT NULL CHECK(manifest_sha256 ~ '^[a-f0-9]{64}$') | 固化证据包规范化清单的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/evidence_package/columns/manifest_sha256`；[SQL](initial-schema.sql) `mt.evidence_package.manifest_sha256`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/manifest_sha256` (sealEvidence) |
| approval_id | uuid | 否 | 无 | NOT NULL | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/evidence_package/columns/approval_id`；[SQL](initial-schema.sql) `mt.evidence_package.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/SealRequest/properties/approval_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/approval_id` (sealEvidence) |
| signature_status | text | 否 | 无 | NOT NULL CHECK(signature_status IN ('not_signed','mock','verified','failed')) | 证据包签名处理状态；状态文字不能代替签名验证证据 | [工程定义](table-catalog.json) `/evidence_package/columns/signature_status`；[SQL](initial-schema.sql) `mt.evidence_package.signature_status`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/signature_status` (sealEvidence) |
| retention_policy_version | text | 否 | 无 | NOT NULL | 用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效 | [工程定义](table-catalog.json) `/evidence_package/columns/retention_policy_version`；[SQL](initial-schema.sql) `mt.evidence_package.retention_policy_version`；[API](../03-api/openapi.yaml) `/components/schemas/SealRequest/properties/retention_policy_version` (sealEvidence) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('DRAFT','SEALED','SUPERSEDED')) | 固化证据包版本的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/evidence_package/columns/state`；[SQL](initial-schema.sql) `mt.evidence_package.state`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/state` (sealEvidence) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/evidence_package/columns/created_at`；[SQL](initial-schema.sql) `mt.evidence_package.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/created_at` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/created_at` (sealEvidence) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/evidence_package/columns/updated_at`；[SQL](initial-schema.sql) `mt.evidence_package.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/evidence_package/columns/row_version`；[SQL](initial-schema.sql) `mt.evidence_package.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/version` (sealEvidence) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/evidence_package/columns/created_by`；[SQL](initial-schema.sql) `mt.evidence_package.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,package_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id)`
- `FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)`
- `UNIQUE(case_id,task_id,version)`

<a id="package_item"></a>
## package_item 固化包版本引用

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| package_item_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/package_item/columns/package_item_id`；[SQL](initial-schema.sql) `mt.package_item.package_item_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/package_item/columns/org_id`；[SQL](initial-schema.sql) `mt.package_item.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/package_item/columns/case_id`；[SQL](initial-schema.sql) `mt.package_item.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/case_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/case_id` (sealEvidence) |
| package_id | uuid | 否 | 无 | NOT NULL | 固化证据包的版本记录标识 | [工程定义](table-catalog.json) `/package_item/columns/package_id`；[SQL](initial-schema.sql) `mt.package_item.package_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/package_id` (sealEvidence) |
| evidence_id | uuid | 否 | 无 | NOT NULL | 所引用证据事实版本标识，指向同案件evidence_item.evidence_id | [工程定义](table-catalog.json) `/package_item/columns/evidence_id`；[SQL](initial-schema.sql) `mt.package_item.evidence_id`；[API](../03-api/openapi.yaml) `/components/schemas/SealRequest/properties/evidence_ids` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/evidence_id` (sealEvidence) |
| object_id | uuid | 否 | 无 | NOT NULL | 所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用 | [工程定义](table-catalog.json) `/package_item/columns/object_id`；[SQL](initial-schema.sql) `mt.package_item.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (sealEvidence) |
| sha256 | text | 否 | 无 | NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$') | 清单中引用对象固定版本字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/package_item/columns/sha256`；[SQL](initial-schema.sql) `mt.package_item.sha256`；[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/sha256` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/sha256` (sealEvidence) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/package_item/columns/created_at`；[SQL](initial-schema.sql) `mt.package_item.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/created_at` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/created_at` (sealEvidence) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/package_item/columns/updated_at`；[SQL](initial-schema.sql) `mt.package_item.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/package_item/columns/row_version`；[SQL](initial-schema.sql) `mt.package_item.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/version` (sealEvidence) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/package_item/columns/created_by`；[SQL](initial-schema.sql) `mt.package_item.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,package_item_id)`
- `FOREIGN KEY (case_id, package_id) REFERENCES mt.evidence_package (case_id, package_id)`
- `FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)`
- `FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id)`
- `UNIQUE(case_id,package_id,evidence_id)`

<a id="report"></a>
## report 报告生成与下载状态

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| report_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/report/columns/report_id`；[SQL](initial-schema.sql) `mt.report.report_id`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/report_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/report_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/report_id` (getReport) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/report/columns/org_id`；[SQL](initial-schema.sql) `mt.report.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/report/columns/case_id`；[SQL](initial-schema.sql) `mt.report.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ReportDraft/properties/case_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/case_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/case_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/case_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/case_id` (getReport) |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/report/columns/task_id`；[SQL](initial-schema.sql) `mt.report.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/ReportDraft/properties/task_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/task_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/task_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/task_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/task_id` (getReport) |
| run_version | bigint | 否 | 无 | NOT NULL | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/report/columns/run_version`；[SQL](initial-schema.sql) `mt.report.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/ReportDraft/properties/run_version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/run_version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/run_version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/run_version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/run_version` (getReport) |
| result_version | bigint | 否 | 无 | NOT NULL | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/report/columns/result_version`；[SQL](initial-schema.sql) `mt.report.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/ReportDraft/properties/result_version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/result_version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/result_version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/result_version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/result_version` (getReport) |
| version | bigint | 否 | 无 | NOT NULL CHECK(version>0) | 此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version | [工程定义](table-catalog.json) `/report/columns/version`；[SQL](initial-schema.sql) `mt.report.version`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (getReport) |
| template_version | text | 否 | 无 | NOT NULL | 生成报告使用的模板版本，确保历史报告可以重现 | [工程定义](table-catalog.json) `/report/columns/template_version`；[SQL](initial-schema.sql) `mt.report.template_version`；[API](../03-api/openapi.yaml) `/components/schemas/ReportDraft/properties/template_version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/template_version` (createReport) |
| approval_id | uuid | 是 | 无 | 无列级约束 | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/report/columns/approval_id`；[SQL](initial-schema.sql) `mt.report.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/approval_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/approval_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/approval_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/approval_id` (getReport) |
| object_id | uuid | 是 | 无 | 无列级约束 | 所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用 | [工程定义](table-catalog.json) `/report/columns/object_id`；[SQL](initial-schema.sql) `mt.report.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (getReport) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('DRAFT','GENERATING','READY','FAILED','SUPERSEDED')) | 报告生成与下载状态的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/report/columns/state`；[SQL](initial-schema.sql) `mt.report.state`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/state` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/state` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/state` (getReport) |
| snapshot_sha256 | text | 否 | 无 | NOT NULL CHECK(snapshot_sha256 ~ '^[a-f0-9]{64}$') | 报告所绑定内容快照的SHA-256，不代表数字签名；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/report/columns/snapshot_sha256`；[SQL](initial-schema.sql) `mt.report.snapshot_sha256`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/report/columns/created_at`；[SQL](initial-schema.sql) `mt.report.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/created_at` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/created_at` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/created_at` (getReport) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/report/columns/updated_at`；[SQL](initial-schema.sql) `mt.report.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/report/columns/row_version`；[SQL](initial-schema.sql) `mt.report.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (getReport) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/report/columns/created_by`；[SQL](initial-schema.sql) `mt.report.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,report_id)`
- `FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)`
- `FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id)`
- `FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id)`
- `FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)`
- `UNIQUE(case_id,task_id,version)`

<a id="report_evidence"></a>
## report_evidence 报告证据引用

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| link_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/report_evidence/columns/link_id`；[SQL](initial-schema.sql) `mt.report_evidence.link_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/report_evidence/columns/org_id`；[SQL](initial-schema.sql) `mt.report_evidence.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/report_evidence/columns/case_id`；[SQL](initial-schema.sql) `mt.report_evidence.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/ReportDraft/properties/case_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/case_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/case_id` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/case_id` (createReport) |
| report_id | uuid | 否 | 无 | NOT NULL | 报告版本记录标识 | [工程定义](table-catalog.json) `/report_evidence/columns/report_id`；[SQL](initial-schema.sql) `mt.report_evidence.report_id`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/report_id` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/report_id` (createReport) |
| evidence_id | uuid | 否 | 无 | NOT NULL | 所引用证据事实版本标识，指向同案件evidence_item.evidence_id | [工程定义](table-catalog.json) `/report_evidence/columns/evidence_id`；[SQL](initial-schema.sql) `mt.report_evidence.evidence_id`；[API](../03-api/openapi.yaml) `/components/schemas/ReportDraft/properties/evidence_ids` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/evidence_ids` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/ReportCreate/properties/evidence_ids` (createReport)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/evidence_ids` (createReport) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/report_evidence/columns/created_at`；[SQL](initial-schema.sql) `mt.report_evidence.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/created_at` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/created_at` (createReport) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/report_evidence/columns/updated_at`；[SQL](initial-schema.sql) `mt.report_evidence.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/report_evidence/columns/row_version`；[SQL](initial-schema.sql) `mt.report_evidence.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (createReportDraft)、[API](../03-api/openapi.yaml) `/components/schemas/Report/properties/version` (createReport) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/report_evidence/columns/created_by`；[SQL](initial-schema.sql) `mt.report_evidence.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,link_id)`
- `FOREIGN KEY (case_id, report_id) REFERENCES mt.report (case_id, report_id)`
- `FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)`

<a id="feedback_request"></a>
## feedback_request 纠错训练用途申请

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| feedback_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/feedback_request/columns/feedback_id`；[SQL](initial-schema.sql) `mt.feedback_request.feedback_id`；[API](../03-api/openapi.yaml) `/components/schemas/FeedbackRecord/properties/feedback_id` (requestFeedback) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/feedback_request/columns/org_id`；[SQL](initial-schema.sql) `mt.feedback_request.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/feedback_request/columns/case_id`；[SQL](initial-schema.sql) `mt.feedback_request.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/case_id` (requestFeedback) |
| finding_id | uuid | 否 | 无 | NOT NULL | 申请回流的风险发现标识；用途审批通过也须另核验来源授权 | [工程定义](table-catalog.json) `/feedback_request/columns/finding_id`；[SQL](initial-schema.sql) `mt.feedback_request.finding_id`；[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/finding_id` (requestFeedback) |
| approval_id | uuid | 否 | 无 | NOT NULL | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/feedback_request/columns/approval_id`；[SQL](initial-schema.sql) `mt.feedback_request.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/FeedbackRecord/properties/approval_id` (requestFeedback) |
| label_version | text | 否 | 无 | NOT NULL | 本次标注使用的标签体系版本 | [工程定义](table-catalog.json) `/feedback_request/columns/label_version`；[SQL](initial-schema.sql) `mt.feedback_request.label_version`；[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/label_version` (requestFeedback) |
| label | text | 否 | 无 | NOT NULL | 人工确认或申请使用的训练标签；不可直接把模型预测视为真值 | [工程定义](table-catalog.json) `/feedback_request/columns/label`；[SQL](initial-schema.sql) `mt.feedback_request.label`；[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/label` (requestFeedback) |
| purpose | text | 否 | 无 | NOT NULL CHECK(purpose='training') | 本记录声明或申请的处理用途，实际动作需与有效授权用途相符 | [工程定义](table-catalog.json) `/feedback_request/columns/purpose`；[SQL](initial-schema.sql) `mt.feedback_request.purpose`；[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/purpose` (requestFeedback) |
| source_authorization_ref | text | 否 | 无 | NOT NULL | 允许该素材用于指定回流或训练用途的来源授权记录引用 | [工程定义](table-catalog.json) `/feedback_request/columns/source_authorization_ref`；[SQL](initial-schema.sql) `mt.feedback_request.source_authorization_ref`；[API](../03-api/openapi.yaml) `/components/schemas/Feedback/properties/source_authorization_ref` (requestFeedback) |
| state | text | 否 | 无 | NOT NULL CHECK(state IN ('REQUESTED','APPROVED','REJECTED','REVOKED','APPLIED')) | 纠错训练用途申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/feedback_request/columns/state`；[SQL](initial-schema.sql) `mt.feedback_request.state`；[API](../03-api/openapi.yaml) `/components/schemas/FeedbackRecord/properties/state` (requestFeedback) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/feedback_request/columns/created_at`；[SQL](initial-schema.sql) `mt.feedback_request.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/feedback_request/columns/updated_at`；[SQL](initial-schema.sql) `mt.feedback_request.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/feedback_request/columns/row_version`；[SQL](initial-schema.sql) `mt.feedback_request.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/FeedbackRecord/properties/version` (requestFeedback) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/feedback_request/columns/created_by`；[SQL](initial-schema.sql) `mt.feedback_request.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,feedback_id)`
- `FOREIGN KEY (case_id, finding_id) REFERENCES mt.risk_finding (case_id, finding_id)`
- `FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id)`

<a id="dataset_version"></a>
## dataset_version 数据版本元数据不存真实样本

范围：org；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| dataset_version_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/dataset_version/columns/dataset_version_id`；[SQL](initial-schema.sql) `mt.dataset_version.dataset_version_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/dataset_version/columns/org_id`；[SQL](initial-schema.sql) `mt.dataset_version.org_id`；内部字段，无外部API映射 |
| dataset_id | text | 否 | 无 | NOT NULL | 数据集目录的稳定文本编号，例如D01；不是数据库UUID主键 | [工程定义](table-catalog.json) `/dataset_version/columns/dataset_id`；[SQL](initial-schema.sql) `mt.dataset_version.dataset_id`；内部字段，无外部API映射 |
| version | text | 否 | 无 | NOT NULL | 此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version | [工程定义](table-catalog.json) `/dataset_version/columns/version`；[SQL](initial-schema.sql) `mt.dataset_version.version`；内部字段，无外部API映射 |
| catalog_sha256 | text | 否 | 无 | NOT NULL CHECK(catalog_sha256 ~ '^[a-f0-9]{64}$') | 数据集版本目录规范化清单的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性 | [工程定义](table-catalog.json) `/dataset_version/columns/catalog_sha256`；[SQL](initial-schema.sql) `mt.dataset_version.catalog_sha256`；内部字段，无外部API映射 |
| authorization_status | text | 否 | 无 | NOT NULL CHECK(authorization_status IN ('pending','verified','expired','revoked')) | 来源或数据集用途授权的当前审核状态，未验证状态不得解释为可正式使用 | [工程定义](table-catalog.json) `/dataset_version/columns/authorization_status`；[SQL](initial-schema.sql) `mt.dataset_version.authorization_status`；内部字段，无外部API映射 |
| split_manifest_ref | text | 否 | 无 | NOT NULL | 数据集训练、验证、校准及封存测试划分清单的版本引用 | [工程定义](table-catalog.json) `/dataset_version/columns/split_manifest_ref`；[SQL](initial-schema.sql) `mt.dataset_version.split_manifest_ref`；内部字段，无外部API映射 |
| actual_count | bigint | 是 | 无 | CHECK(actual_count>=0) | 按数据卡计数单位核验的实际数量；NULL表示未核验，不用预算数量代替 | [工程定义](table-catalog.json) `/dataset_version/columns/actual_count`；[SQL](initial-schema.sql) `mt.dataset_version.actual_count`；内部字段，无外部API映射 |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('PLANNING','DRAFT','RELEASED','FROZEN','REVOKED')) | 数据版本元数据不存真实样本的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/dataset_version/columns/status`；[SQL](initial-schema.sql) `mt.dataset_version.status`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/dataset_version/columns/created_at`；[SQL](initial-schema.sql) `mt.dataset_version.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/dataset_version/columns/updated_at`；[SQL](initial-schema.sql) `mt.dataset_version.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/dataset_version/columns/row_version`；[SQL](initial-schema.sql) `mt.dataset_version.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/dataset_version/columns/created_by`；[SQL](initial-schema.sql) `mt.dataset_version.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `UNIQUE(org_id,dataset_id,version)`

<a id="audit_event"></a>
## audit_event 追加式审计事实

范围：org；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| event_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/audit_event/columns/event_id`；[SQL](initial-schema.sql) `mt.audit_event.event_id`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/event_id` (listAuditEvents) |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/audit_event/columns/org_id`；[SQL](initial-schema.sql) `mt.audit_event.org_id`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/org_id` (listAuditEvents) |
| case_id | uuid | 是 | 无 | 无列级约束 | 案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限 | [工程定义](table-catalog.json) `/audit_event/columns/case_id`；[SQL](initial-schema.sql) `mt.audit_event.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/case_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/case_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/case_id` (listAuditEvents)、[API](../03-api/openapi.yaml) `/components/schemas/AuditExport/properties/case_id` (exportAudit) |
| actor_id | uuid | 否 | 无 | NOT NULL REFERENCES mt.users(user_id) | 操作主体标识；从服务端认证上下文取得，系统动作的可空条件须另有审计规则 | [工程定义](table-catalog.json) `/audit_event/columns/actor_id`；[SQL](initial-schema.sql) `mt.audit_event.actor_id`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/actor_id` (listAuditEvents) |
| action | text | 否 | 无 | NOT NULL | 被审计业务操作的稳定编码，不是主张文本中的行为 | [工程定义](table-catalog.json) `/audit_event/columns/action`；[SQL](initial-schema.sql) `mt.audit_event.action`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/action` (listAuditEvents) |
| object_type | text | 否 | 无 | NOT NULL | 审批或审计目标对象类型，决定object_id应指向哪种业务对象 | [工程定义](table-catalog.json) `/audit_event/columns/object_type`；[SQL](initial-schema.sql) `mt.audit_event.object_type`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/object_type` (listAuditEvents) |
| object_id | uuid | 是 | 无 | 无列级约束 | 该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键 | [工程定义](table-catalog.json) `/audit_event/columns/object_id`；[SQL](initial-schema.sql) `mt.audit_event.object_id`；[API](../03-api/openapi.yaml) `/components/schemas/ObjectRef/properties/object_id` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/object_id` (listAuditEvents)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/object_id` (exportAudit) |
| object_version | bigint | 是 | 无 | CHECK(object_version>0) | 审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批 | [工程定义](table-catalog.json) `/audit_event/columns/object_version`；[SQL](initial-schema.sql) `mt.audit_event.object_version`；[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/object_version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/object_version` (listAuditEvents) |
| outcome | text | 否 | 无 | NOT NULL CHECK(outcome IN ('allowed','denied','failed')) | 审计操作的结果编码，例如允许、拒绝或失败；须与实际处理一致 | [工程定义](table-catalog.json) `/audit_event/columns/outcome`；[SQL](initial-schema.sql) `mt.audit_event.outcome`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/outcome` (listAuditEvents) |
| request_id | uuid | 否 | 无 | NOT NULL | 贯穿接口、任务和审计的请求追踪标识；不充当权限凭证 | [工程定义](table-catalog.json) `/audit_event/columns/request_id`；[SQL](initial-schema.sql) `mt.audit_event.request_id`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/request_id` (listAuditEvents)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/request_id` (exportAudit) |
| occurred_at | timestamptz | 否 | 无 | NOT NULL | 被审计操作实际发生时刻，区别于记录写入时间created_at；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/audit_event/columns/occurred_at`；[SQL](initial-schema.sql) `mt.audit_event.occurred_at`；[API](../03-api/openapi.yaml) `/components/schemas/AuditEvent/properties/occurred_at` (listAuditEvents) |
| details | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 脱敏后的审计上下文对象，记录必要原因和关联ID，不记录令牌、密码或原始敏感内容。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/audit_event/columns/details`；[SQL](initial-schema.sql) `mt.audit_event.details`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/audit_event/columns/created_at`；[SQL](initial-schema.sql) `mt.audit_event.created_at`；[API](../03-api/openapi.yaml) `/components/schemas/Review/properties/created_at` (createReview)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/created_at` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/created_at` (sealEvidence) |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/audit_event/columns/updated_at`；[SQL](initial-schema.sql) `mt.audit_event.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/audit_event/columns/row_version`；[SQL](initial-schema.sql) `mt.audit_event.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/ApprovalDecision/properties/expected_version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/Approval/properties/version` (decideApproval)、[API](../03-api/openapi.yaml) `/components/schemas/EvidencePackage/properties/version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/Evidence/properties/version` (sealEvidence)、[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/version` (exportAudit)、[API](../03-api/openapi.yaml) `/components/schemas/IndexSwitch/properties/expected_version` (switchIndex)、[API](../03-api/openapi.yaml) `/components/schemas/IndexVersion/properties/row_version` (switchIndex) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/audit_event/columns/created_by`；[SQL](initial-schema.sql) `mt.audit_event.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id)`
- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`

<a id="audit_export"></a>
## audit_export 审计导出作业

范围：case；历史不可覆盖：由版本、状态及应用控制更新。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| export_id | uuid | 否 | 无 | PRIMARY KEY | 主键，由应用提供UUID；不视为访问凭证 | [工程定义](table-catalog.json) `/audit_export/columns/export_id`；[SQL](initial-schema.sql) `mt.audit_export.export_id`；内部字段，无外部API映射 |
| org_id | uuid | 否 | 无 | NOT NULL | 该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位 | [工程定义](table-catalog.json) `/audit_export/columns/org_id`；[SQL](initial-schema.sql) `mt.audit_export.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验 | [工程定义](table-catalog.json) `/audit_export/columns/case_id`；[SQL](initial-schema.sql) `mt.audit_export.case_id`；[API](../03-api/openapi.yaml) `/components/schemas/AuditExport/properties/case_id` (exportAudit) |
| approval_id | uuid | 否 | 无 | NOT NULL | 与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过 | [工程定义](table-catalog.json) `/audit_export/columns/approval_id`；[SQL](initial-schema.sql) `mt.audit_export.approval_id`；[API](../03-api/openapi.yaml) `/components/schemas/AuditExport/properties/approval_id` (exportAudit) |
| start_at | timestamptz | 否 | 无 | NOT NULL | 审计导出查询的起始时刻；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/audit_export/columns/start_at`；[SQL](initial-schema.sql) `mt.audit_export.start_at`；[API](../03-api/openapi.yaml) `/components/schemas/AuditExport/properties/start_at` (exportAudit) |
| end_at | timestamptz | 否 | 无 | NOT NULL | 审计导出查询的结束时刻，必须与起始时刻构成有效区间；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/audit_export/columns/end_at`；[SQL](initial-schema.sql) `mt.audit_export.end_at`；[API](../03-api/openapi.yaml) `/components/schemas/AuditExport/properties/end_at` (exportAudit) |
| purpose | text | 否 | 无 | NOT NULL | 本记录声明或申请的处理用途，实际动作需与有效授权用途相符 | [工程定义](table-catalog.json) `/audit_export/columns/purpose`；[SQL](initial-schema.sql) `mt.audit_export.purpose`；[API](../03-api/openapi.yaml) `/components/schemas/AuditExport/properties/purpose` (exportAudit) |
| state | text | 否 | 无 | NOT NULL | 审计导出作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效 | [工程定义](table-catalog.json) `/audit_export/columns/state`；[SQL](initial-schema.sql) `mt.audit_export.state`；[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/state` (exportAudit) |
| artifact_ref | jsonb | 否 | '{}'::jsonb | NOT NULL DEFAULT '{}'::jsonb | 评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用 | [工程定义](table-catalog.json) `/audit_export/columns/artifact_ref`；[SQL](initial-schema.sql) `mt.audit_export.artifact_ref`；内部字段，无外部API映射 |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/audit_export/columns/created_at`；[SQL](initial-schema.sql) `mt.audit_export.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/audit_export/columns/updated_at`；[SQL](initial-schema.sql) `mt.audit_export.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/audit_export/columns/row_version`；[SQL](initial-schema.sql) `mt.audit_export.row_version`；[API](../03-api/openapi.yaml) `/components/schemas/ActionAck/properties/version` (exportAudit) |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/audit_export/columns/created_by`；[SQL](initial-schema.sql) `mt.audit_export.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,export_id)`
- `FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id)`
- `CHECK(end_at>start_at)`

<a id="first_source_ranking"></a>
## first_source_ranking 首发排序不可变结果快照

范围：case；历史不可覆盖：是，普通角色及触发器限制UPDATE/DELETE/TRUNCATE，非超级用户防护。

| 字段 | 类型 | 可空 | 默认值 | 列级约束 | 业务含义 | 精确来源 |
| --- | --- | --- | --- | --- | --- | --- |
| ranking_id | uuid | 否 | 无 | PRIMARY KEY | 一次首发排序结果快照的唯一标识；重算或复核更正生成新快照 | [工程定义](table-catalog.json) `/first_source_ranking/columns/ranking_id`；[SQL](initial-schema.sql) `mt.first_source_ranking.ranking_id`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/ranking_id` (getFirstSource) |
| org_id | uuid | 否 | 无 | NOT NULL | 记录所属单位标识；单位授权范围由服务端认证上下文确定 | [工程定义](table-catalog.json) `/first_source_ranking/columns/org_id`；[SQL](initial-schema.sql) `mt.first_source_ranking.org_id`；内部字段，无外部API映射 |
| case_id | uuid | 否 | 无 | NOT NULL | 案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限 | [工程定义](table-catalog.json) `/first_source_ranking/columns/case_id`；[SQL](initial-schema.sql) `mt.first_source_ranking.case_id`；内部字段，无外部API映射 |
| cluster_id | uuid | 否 | 无 | NOT NULL | 高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证 | [工程定义](table-catalog.json) `/first_source_ranking/columns/cluster_id`；[SQL](initial-schema.sql) `mt.first_source_ranking.cluster_id`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/cluster_id` (getFirstSource) |
| task_id | uuid | 否 | 无 | NOT NULL | 关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本 | [工程定义](table-catalog.json) `/first_source_ranking/columns/task_id`；[SQL](initial-schema.sql) `mt.first_source_ranking.task_id`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/task_id` (getFirstSource) |
| run_version | bigint | 否 | 无 | NOT NULL CHECK(run_version>0) | 分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算 | [工程定义](table-catalog.json) `/first_source_ranking/columns/run_version`；[SQL](initial-schema.sql) `mt.first_source_ranking.run_version`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/run_version` (getFirstSource) |
| result_version | bigint | 否 | 无 | NOT NULL CHECK(result_version>0) | 给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果 | [工程定义](table-catalog.json) `/first_source_ranking/columns/result_version`；[SQL](initial-schema.sql) `mt.first_source_ranking.result_version`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/result_version` (getFirstSource) |
| candidate_count | integer | 否 | 无 | NOT NULL CHECK(candidate_count BETWEEN 0 AND 3) | 该快照应包含的候选总数；事务提交时必须与明细数量相等，0表示有结果但无足够候选 | [工程定义](table-catalog.json) `/first_source_ranking/columns/candidate_count`；[SQL](initial-schema.sql) `mt.first_source_ranking.candidate_count`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/candidate_count` (getFirstSource) |
| model_version | text | 否 | 无 | NOT NULL | 生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本 | [工程定义](table-catalog.json) `/first_source_ranking/columns/model_version`；[SQL](initial-schema.sql) `mt.first_source_ranking.model_version`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/model_version` (getFirstSource) |
| policy_version | text | 否 | 无 | NOT NULL | 本记录使用的业务、阈值或流程策略版本，需按其实际用途解析 | [工程定义](table-catalog.json) `/first_source_ranking/columns/policy_version`；[SQL](initial-schema.sql) `mt.first_source_ranking.policy_version`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/policy_version` (getFirstSource) |
| coverage_note | text | 否 | 无 | NOT NULL | 本次观察的平台、时间和素材覆盖范围及缺失说明；不能声称覆盖未知全网 | [工程定义](table-catalog.json) `/first_source_ranking/columns/coverage_note`；[SQL](initial-schema.sql) `mt.first_source_ranking.coverage_note`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/coverage_note` (getFirstSource) |
| status | text | 否 | 无 | NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')) | candidate为待核查候选，insufficient为证据不足，reviewed为已复核快照；reviewed仍非法律结论 | [工程定义](table-catalog.json) `/first_source_ranking/columns/status`；[SQL](initial-schema.sql) `mt.first_source_ranking.status`；[API](../03-api/openapi.yaml) `/components/schemas/FirstSource/properties/status` (getFirstSource) |
| created_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名 | [工程定义](table-catalog.json) `/first_source_ranking/columns/created_at`；[SQL](initial-schema.sql) `mt.first_source_ranking.created_at`；内部字段，无外部API映射 |
| updated_at | timestamptz | 否 | now() | NOT NULL DEFAULT now() | 更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区 | [工程定义](table-catalog.json) `/first_source_ranking/columns/updated_at`；[SQL](initial-schema.sql) `mt.first_source_ranking.updated_at`；内部字段，无外部API映射 |
| row_version | bigint | 否 | 1 | NOT NULL DEFAULT 1 CHECK(row_version>0) | 本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值 | [工程定义](table-catalog.json) `/first_source_ranking/columns/row_version`；[SQL](initial-schema.sql) `mt.first_source_ranking.row_version`；内部字段，无外部API映射 |
| created_by | uuid | 是 | 无 | 无列级约束 | 创建主体；迁移/系统事件可空，业务应用必须填 | [工程定义](table-catalog.json) `/first_source_ranking/columns/created_by`；[SQL](initial-schema.sql) `mt.first_source_ranking.created_by`；内部字段，无外部API映射 |

表级约束：

- `FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)`
- `UNIQUE(case_id,ranking_id)`
- `UNIQUE(case_id,ranking_id,cluster_id)`
- `UNIQUE(case_id,cluster_id,task_id,run_version,result_version)`
- `FOREIGN KEY(case_id,cluster_id) REFERENCES mt.content_cluster(case_id,cluster_id)`
- `FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)`
- `CHECK(candidate_count<>0 OR status='insufficient')`

排序、证据引用与事务完整性由[first-source-ranking.md](first-source-ranking.md)所列触发器执行。证据ID存在不等于证据支持或用途合法。
