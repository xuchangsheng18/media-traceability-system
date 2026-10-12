# 官方来源与适用边界

只采用官方标准、维护方文档或作者仓库。技术资料支持机制设计，不替代公安厅内部要求、数据授权、正式批准和实测。网页机制在选型冻结前再按实际版本核验。

| 编号 | 官方来源 | 引用位置 | 本包用途 |
| --- | --- | --- | --- |
| W01 | [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html) | §4.8.24、§4.8.30 | Schema基于2020-12；安全方案声明不替代对象授权。 |
| W02 | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation) | format、required、additionalProperties | 结构校验及format断言需分别验证；跨字段关系由语义校验补充。 |
| W03 | [PostgreSQL 16约束](https://www.postgresql.org/docs/16/ddl-constraints.html) | CHECK、UNIQUE、FOREIGN KEY | 列约束与关联完整性需分别建模；跨案件复合外键是项目设计。 |
| W04 | [PostgreSQL 16行安全](https://www.postgresql.org/docs/16/ddl-rowsecurity.html) | 默认拒绝、owner/BYPASSRLS | RLS与表权限叠加；超级用户绕过边界，运行角色不得为超级用户。 |
| W05 | [PostgreSQL 16触发器](https://www.postgresql.org/docs/16/sql-createtrigger.html) | BEFORE与TRUNCATE事件 | 追加记录保护同时考虑UPDATE、DELETE和TRUNCATE；不作为管理员防篡改保证。 |
| W06 | [HTTP Semantics RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) | §13.1.1、§14、§15.5.13 | If-Match控制旧版本更新；受控下载Range需要再次授权。 |
| W07 | [HTTP Problem Details RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) | §3、§5 | 项目保留原code/message/request_id/details并增加Problem字段；不泄露堆栈。 |
| W08 | [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | 默认拒绝、逐请求授权 | 授权覆盖每次请求及对象范围；角色本身不代表所有案件可见。 |
| W09 | [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | 类型、大小、存储、安全扫描 | 类型签名与资源限制共同设计；查毒不可用不能静默作为安全通过。 |
| W10 | [jsonschema校验器](https://python-jsonschema.readthedocs.io/en/stable/validate/) | Draft202012Validator、FormatChecker | 显式启用格式校验与本地引用注册，防止只检查Schema不检查实例。 |
| W11 | [OpenAPI Spec Validator](https://openapi-spec-validator.readthedocs.io/en/latest/) | OpenAPI 3.1支持 | 仅验证契约文档，不证明HTTP服务鉴权与业务执行正确。 |
| W12 | [scikit-learn校准](https://scikit-learn.org/stable/modules/calibration.html) | 校准数据独立于训练拟合 | 训练、阈值选择与独立验收用途分开，不用封存测试集选择模型。 |
| W13 | [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) | 对象版本锁、删除标记 | 锁保护指定version_id；同键新版本不等于修改已固化证据。 |
| W14 | [S3预签名访问](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html) | Bearer与到期 | 项目受控代理负责逐请求撤销；预签名不能宣称立即撤销。 |
| W15 | [GB/T 22239-2019公开状态](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=BAFB47E8874764186BDB7865E8344DAF) | 标准登记信息 | 作为安全要求审查来源；系统等级与公安厅具体准入仍待专责确认。 |
| W16 | [个人信息保护法公开文本](https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm) | 处理规则与安全责任 | 仅建立法律适用性审查入口，不据公开文本宣称本项目已合规批准。 |
| W17 | [TruFor作者仓库](https://github.com/grip-unina/TruFor) | 输入机制与许可 | 原RGB与学习噪声指纹机制和项目扩展分开；许可用途逐组件核验。 |
| W18 | [LightGlue作者仓库](https://github.com/cvg/LightGlue) | 特征组件许可 | 匹配器许可不能覆盖SuperPoint特征模型；候选许可未核准不得正式交付。 |
| W19 | [Celery broker文档](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/index.html) | broker能力 | 执行broker与Kafka事件用途分开，故障验证在第二阶段实际运行。 |
| W20 | [PostgreSQL 16 JSON类型](https://www.postgresql.org/docs/16/datatype-json.html) | JSONB与索引 | JSONB可保存可扩展发现明细；主关联、版本、权限不得仅藏入无约束JSON。 |
