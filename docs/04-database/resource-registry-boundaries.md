# 资源、来源及模型读取的数据库边界

本轮使用[0014增量迁移](../../backend/business_migrations/0014_resource_registry.sql)，接续0013，保留0001—0013原字节及摘要。该迁移没有新增业务表或列，不代表所有任务的数据写入方法已经实现。[本轮实际验证、CI及同步](../00-project/validation/t001-t123-resource-registry-report.json)和[123项逐条审计](../03-development/t001-t123-development-completion-audit.md)分别查阅。

| 范围 | 数据来源与约束 | 尚未代表的能力 |
| --- | --- | --- |
| 来源登记 | SourceCreate只提交案件、名称、类型、授权引用、用途及到期。权威端口返回精确单位/案件/用途/期限及授权版本；登记、幂等回执、审计同事务，提交前重读证明 | 客户端不能声明verified；pending不能用于绕过有效来源核验。真实权威、维护/到期告警和管理页面仍待 |
| 原件下载 | media_asset与object_version固定object_id/version_id/SHA/size绑定，核验案件、来源download用途及独立下载用途/分类事实；完整校验及审计提交后才返回内容 | FileStore不等于正式S3/WORM/保留与恢复准入；资产只读权限不自动允许下载 |
| 模型列表 | 认证主体所属单位的model_registry；逐项model_metadata_scope先于分页，模型状态只读已有记录 | 不执行模型、不声明健康、不登记模型准入或上线批准 |
| 评测列表 | 同单位model_evaluation、实际模型与已登记对象引用。固定函数只返回org_id/object_id/version_id/sha256，不能取得案件原件 | 不生成评测指标、分组报告或发布审批；读取历史值不证明模型合格 |

0014只扩展四个既有operation和精确lookup kind/op配对；新增`mt.model_evaluation_artifact_metadata(uuid)`。model_registry、model_evaluation、object_version上的新增SELECT策略仅授予迁移owner，业务连接明确不得继承该owner。没有向runtime追加UPDATE、删除或跨案件权限。不可变对象/评测记录使用普通读取，保留其只读/追加ACL及触发器；可变资产/模型仍使用共享行锁及最终授权复核。

对象的`version_id`是受控版本字符串，不是UUID；`dataset_id`和`protocol_id`也是文本标识，不能按字段后缀误转UUID。ObjectRef.object_id按UUID值比较，大小写不改变身份；版本字符串及小写SHA保持精确匹配。

分页遵循现有协议：身份、操作、页大小或可见事实改变导致旧游标返回`422/PAGE_CURSOR_INVALID`；同次分页读取内签名与最终复核间数据变化返回`409/PAGE_CURSOR_STALE`。两种情况均不返回部分页面。

当前登记Schema要求对象与资产大小为正；零字节登记由约束拒绝，不声称存在成功的零字节业务资产。空字节缓冲与Range边界仅作底层纯测试。下载的`max_upload_bytes`是明确的本批研发内存资源上限，超限拒绝503，不能当作正式业务文件大小政策。

Python3.10的到期时间解析已兼容1—6位小数秒及合法时区。超过6位且后续全零可无损规范；非零亚微秒无法与当前datetime/数据库微秒证明精确等值，返回403，不四舍五入延长或缩短授权。正式精度需求如有变化须另行处理。

现有演示数据库仍为0001—0011。源码推送和服务器快进均不自动安装0012—0014；任何共享采用必须先按原迁移/恢复要求执行，并单列实际回执。Python候选继续暂缓，原100包锁不变。
