# 数据库设计与迁移边界

PostgreSQL16为空库设计候选。保留源12核心表，扩展单位用户角色、案件授权、对象版本、多父血缘、上传导入、运行/结果历史、事务事件、审批、报告、回流、数据版本及索引。字段目录和DDL从同一表定义生成，接口映射列持久化、投影与仅服务端处理的区别。

UUID由应用提供，当前不调用PostgreSQL16不存在的uuidv7函数。TIMESTAMPTZ保存UTC逻辑时间；媒体毫秒用BIGINT。大文件、掩码、向量和模型权重存受控对象，DB保存版本、摘要和引用。JSONB只存扩展明细；主键、作用域、时间、版本和关联关系不能藏在无约束JSON里。

业务关联使用case_id与对象ID复合外键防止串案。案件org_id通过复合外键绑定单位。不可变证据、结果、评测、关系和审计追加记录；需要更正新增版本。media_asset原件对象/摘要/来源不普通覆盖。进度、任务当前投影、队列投递等允许受控更新。

SQL启用业务作用域RLS；运行角色mt_runtime为NOLOGIN且无超级用户/BYPASSRLS。组织级模型和策略不因算法管理角色而开放案件原件。审批用途与当前授权由服务端核验；本DDL的约束不等于完整审批服务或正式制度。

RLS上下文仅由受信后端根据已认证主体在每事务设置app.actor_id/app.org_id，连接池事务后清理。可任意执行SQL/SET的终端用户不适用该信任模型，不授予业务DB直连。case授权函数由受控迁移所有者拥有并固定search_path；所有者权限与上线复核需另审批。超级用户可绕过，SQL不能承诺管理员绝对不可篡改。

初始化仅对新空数据库运行，已存在mt schema则失败，防止重复覆写；角色由迁移身份创建不设默认密码。生产升级应迁移脚本、预检查、回退或恢复/前向修复方案，不直接使用DROP重建。数据备份、对象版本、授权、批准与索引元数据必须对账，RPO/RTO待确认。

## 2026-10-12首发排序增补

首发结果从无批次明细扩展为first_source_ranking头表与first_source_candidate明细，数据库现在62张候选表。头表绑定任务运行/结果版本，0至3个候选一次事务写入。按[排序契约](first-source-ranking.md)实施，不用model_version代替批次。完整字段解释和精确来源见[data-dictionary.md](data-dictionary.md)及[field-provenance.json](field-provenance.json)。

## 0.4证据引用与字段追溯

首发候选的JSON证据引用由明确SQL触发器验证，详细规则见first-source-ranking.md。逐字段来源JSON还提供nullable、default_sql、foreign_keys、sql_line和OpenAPI schema_pointer，开发人员无需根据“来源契约”自行猜测。其余业务表JSON载荷的语义仍按对应契约及应用校验执行。
