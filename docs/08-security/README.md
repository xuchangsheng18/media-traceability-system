# 权限与审计

安全设计、数据分类、权限矩阵与审计。当前42个业务操作的统一权限入口及适用拒绝回归已实现；正式六角色允许策略、共享采用和整任务验收仍未完成。

- [T014六角色具体规则方案](t014-six-role-rule-proposal.md)及[机器表](t014-six-role-rule-proposal.json)：41权限246格、73操作、职责冲突和对象/用途条件；状态为待审方案，未启用ALLOW。
- [T014当前实施与验证](../03-development/t014-unified-permission-implementation.md)：代码与精确CI证据，明确42个挂载和31个未挂载操作的边界。
- [T013本人A01—A10清单](../03-development/t013-owner-action-checklist.md)：密钥、本人MFA和恢复步骤，保留口令保护/独立介质及离线恢复待办。
- [来源职责与T011历史评审矩阵](permission-matrix.md)：保留原文职责、限制与待定值；新方案不覆盖来源。

优先阅读[security-design.md](security-design.md)。

- [audit-requirements.md](audit-requirements.md)
- [data-classification.md](data-classification.md)
- [permission-matrix.md](permission-matrix.md)
- [security-design.md](security-design.md)

## 第一阶段归属

本专题承接第一阶段第6/16步的候选输入，操作、产物和确认要求见[24步对应表](../00-project/stage-one/steps-and-deliverables.md)。专题结构源保持不变，设计/计划与实际实施结果分开。
