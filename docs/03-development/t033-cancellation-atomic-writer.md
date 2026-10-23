# T033取消专用原子写入

2026-10-22：按已批准的[非算法工程版计划](non-algorithm-fast-delivery-plan-20261028.md)收拢现有取消路径。本批仅交付内部工程子范围；不增加公共状态、接口字段、业务规则或数据库迁移，不关闭T033整卡。

## 依赖和范围

T032的0015迁移已有事件所属运行外键与状态词表约束；T017的追加审计、幂等回执和事务末授权复核已在当前取消HTTP路径使用。本批沿用这些实现。前置实现提交`973a7d7`的完整业务回归1057项、T014权限回归1092项通过；整体CI仍因软件安全扫描失败，精确结果见[最终CI回执](../00-project/validation/ci973-final-ci-report.json)。这不等于生产准入或先前失败原因已唯一确定。

修改`backend/business_app/controls/execution.py`及`router.py`，复用现有数据库授权事务、任务范围绑定、行锁、JSON Schema、事件/outbox及HTTP审计能力。取消申请仍经过身份、功能权限、单位/案件范围、取消规则、适用批准、ETag、运行/行版本和幂等检查。后台协调仍需`cancelTaskWork`工作授权及真实取消权限。

## 固定的两条既有路径

| 路径 | 前态及条件 | 原子产物 |
| --- | --- | --- |
| 请求取消 | CREATED、QUEUED、RUNNING、WAIT_REVIEW、REVIEWING、RETURNED之一，符合现有HTTP规则 | CANCEL_REQUESTED投影、`workflow.run.cancel_requested.v1`事件和outbox |
| 确认取消 | CANCEL_REQUESTED；仅工作授权入口；本运行待执行节点已取消，运行中节点已真实确认停止 | CANCELLED投影、`workflow.run.cancelled.v1`事件和outbox |

新增内部`Execution.cancel_transition`，显式接收任务、期望run/行版本和前后态。拒绝非取消迁移；只允许取消操作的授权上下文；核对上下文操作者、单位、案件及任务目标。锁定投影后核对当前运行、版本和前态，用包含单位/案件/任务/run/行版本/前态的条件更新递增行版本，事件绑定同一固定运行。

写入器使用已有事务内的savepoint，投影、事件或outbox失败时回滚本写入单元，即使内部调用方捕获异常后继续外层事务也不能留下半次迁移。它不自行提交外层事务；HTTP幂等回执、审计和事务末授权复核仍由现有根事务统一提交或回滚。SQL历史及结果快照保持追加和不可覆盖。

HTTP保留`TASK_CONTROL_VERSION_CONFLICT`、`TASK_CONTROL_STATE_CONFLICT`及既有ETag响应；工作协调保留`CANCEL_REQUEST_STALE`和完成后幂等返回。源卡提出的全业务`TASK_STATE_CONFLICT`统一口径仍待完整状态机契约对齐，本批不暗改响应。

## 核验和复现

新增[取消写入测试](../../tests/business/test_cancel_state_writer.py)，使用新建随机隔离PostgreSQL16数据库及显式自建测试身份。夹具不代表正式身份、来源或批准已经接入。

```text
python -m pytest -q tests/business/test_cancel_state_writer.py tests/business/test_execution_cancel.py tests/business/test_adapters_and_execution.py tests/business/test_t014_work.py tests/business/test_task_event_constraints.py --tb=short
python scripts/verify_business_foundation.py failure-probe
python scripts/stage_three_types.py check
```

测试覆盖六种前态、非法迁移、旧run/行版本/前态、错误单位/案件/操作者/任务、缺授权或非取消授权、未停止节点、同事务故障回滚、并发HTTP请求及幂等、事务末撤销。代码复核另发现并补测“历史run范围不能写当前新run”，保留旧版本冲突的响应顺序。原工作租约、fencing、当前过期租约停止确认及历史不可变回归继续保留。并发HTTP用例沿用单连接池，证明请求串行后的幂等和版本行为，不证明两个独立数据库连接的重叠锁竞争或性能；该覆盖补强保留后续。实际RED/GREEN、受影响回归、类型与同步结果以[本批限定回执](../00-project/validation/t033-cancellation-atomic-writer-report.json)为准，不把命令清单当通过结果。

## 仍未完成

全业务分析任务状态机、可信计划到正式策略/提供者的映射、任务创建与调度、节点聚合、RETURNED补证/重算/复核/归档路径及全部合法非法转换仍未由本批交付。未配置正式策略或提供者继续拒绝，不能聚合成模型成功。

T033实际负责人、实际复核人及剩余工时尚未确认；既有人员职责不自动沿用。源码同步不等于共享环境采用；本批不执行共享数据库迁移、服务重启、main合并或发布。Python候选、算法、权重和训练继续暂缓，安全门禁保持原状。
