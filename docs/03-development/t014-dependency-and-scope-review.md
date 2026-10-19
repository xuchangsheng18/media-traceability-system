# T014 前置依赖核对与本批开发边界

2026-10-19；T014实际开发负责人：徐昌胜（用户本轮明确确认）。本批只完成依赖证据复核、接口/单位/案件矩阵、异常权限测试设计；没有修改业务接口、数据库迁移、身份服务或运行版本。

## 三项成果

| 本批要求 | 可核验交付 | 当前判定 |
| --- | --- | --- |
| 核对T012、T013实际实现与测试 | 本文、本轮[依赖回归报告](../00-project/validation/t014-dependency-regression-report.json) | 当前Linux/py310/CPU隔离研发子范围有代码和实测；两项整卡仍未关闭。 |
| 接口权限、单位与案件范围矩阵 | [73操作/41权限/6角色矩阵](../08-security/t014-interface-scope-matrix.md)及同名JSON | 从既有契约派生并核对路由；职责/候选范围不当正式ALLOW。 |
| 未认证、无权限、撤销与越权测试设计 | [场景与逐操作覆盖计划](../09-testing/t014-authorization-test-design.md)及同名JSON | 设计完成；新的T014业务测试尚未实现和执行。 |

## 代码与证据逐项核对

当前审查源码`de6c086a91a2d68a7bc4d0c8daf510ac927f44dc`。本轮执行`python -m pytest tests/business tests/platform/test_t013_tokens.py -q --tb=short --junitxml PRIVATE_PATH`，Linux Miniforge Python 3.10.22；结果293项，失败0、错误0、跳过0。报告保存分组数量及源码SHA-256；私密连接资料、原始日志和JUnit不入库。只使用原有专用测试实例及每例新建/清理数据库，未切换共享服务。完整T014接口权限尚未由这些回归证明。

| 依赖 | 实际复用能力 | 证据与限制 | 本批进入条件 |
| --- | --- | --- | --- |
| T012 | identity/directory.py的issuer+subject映射、单位/用户/案件、成员及角色/权限绑定；版本迁移、启用/撤销/到期；db.py事务局部上下文和RLS | test_identity_directory、test_role_directory、test_migrations、test_authorization及test_token_identity真实隔离库回归；permission_bindings是manager-only目录接口，注释明确不是路由或正式策略ALLOW | 可复用数据模型和隔离测试基础；不据此判定有生产授权服务。 |
| T013 | RFC7662自省校验、精确映射、Keycloak隔离重启/轮换/故障/恢复与替代管理工具 | 本轮令牌/映射回归；[最近已完整归档CI](../00-project/validation/t013-bootstrap-management-ci-report.json)源码`aff738a3e6636c1254326b55ac25197c9251e80f`、run 39226217064，330身份测试、246业务测试、32工程门禁；其53个指定身份/工具/配置/测试文件与本轮逐字相同 | 可用作身份边界设计与隔离夹具基础；共享正式策略仍缺失。 |

现有完整测试会临时重写business-recovery-report与database-foundation-report两份验证输出；本轮已核对写入时间及对应测试，先保留到服务器私密工作区，再恢复各自测试前Git原字节，随后才同步源码。未覆盖其他工作流改动；应用代码和共享服务未变。清理摘要附在本轮依赖回归报告中。

## 历史报告与当前源码不能混用

| 历史报告 | 绑定文件数 | 当前差异文件 | 本轮处理 |
| --- | --- | --- | --- |
| [t012-identity-relations-report.json](../00-project/validation/t012-identity-relations-report.json) | 9 | backend/business_app/identity/directory.py, tests/business/test_migrations.py | 保留历史PASS原范围；变更文件以本轮回归和精确摘要复核，不覆盖原报告。 |
| [t012-role-model-report.json](../00-project/validation/t012-role-model-report.json) | 5 | 无 | 保留历史PASS原范围；变更文件以本轮回归和精确摘要复核，不覆盖原报告。 |
| [t013-token-validation-report.json](../00-project/validation/t013-token-validation-report.json) | 3 | backend/business_app/identity/tokens.py | 保留历史PASS原范围；变更文件以本轮回归和精确摘要复核，不覆盖原报告。 |

## 当前缺口和后续边界

1. `require_permission(permission_code)`尚未实现为统一入口；现有检查分散于authorize_request、UploadService.scope、resource_scope/current_scope和policy_actor。每个入口须按契约权限统一核验，不能从一个辅助测试路由推断全量覆盖。
2. `getCurrentUser`契约是identity.read，现有代码主要校验本人目录绑定和逐案件case.read；需要补齐明确的功能权限检查。TestAuthority只按合成令牌/案件放行，不足以验证真实角色权限。
3. 新路由漏权限标记的自动拒绝门禁、全部受保护接口401/403、角色/权限/案件撤销后的完整回归仍缺；BusinessError的401 challenge与HTTPException分支存在差异，已列专项测试设计。
4. T013-R01仍有软件准入、正式范围/规则、本人账号/MFA接管、共享采用与bootstrap退役；R02真实密钥虽已生成并验证保护结构，USB签名备份、实际签名/两把子密钥解密验签/独立恢复和真实身份备份恢复尚待完成。不能把“已生成密钥”当成恢复演练通过。
5. T012正式角色/权限授权与数据规则、T013真实交接和恢复证据仍未关闭，故本批结论仅为“可开展T014限定开发准备”；不作完整依赖通过或正式联调启用结论。

实际负责人已登记为徐昌胜，仅用于任务分工，不创建账号、授予权限、指定T014复核人或代签。剩余工时、实际开始/完成日期、T014复核人与验收决定继续未填。六角色是主要候选设计，正式允许值、职责冲突、数据分类/用途和撤销一致性规则仍待输入。本批无需新增个人操作即可完成上述三项准备；未来正式授权及真实密钥操作需要对应输入和本人操作后另验。

## 状态与同步口径

已补内容登记到T014-R01/R02的部分里程碑，R03登记责任人；原C01表述收紧为已有检查入口，避免暗示所有已挂载操作都实现完整功能权限。没有增加完成子步骤或关闭任务：全库仍87条已验证子步骤、621条剩余工作、0项完整任务验收；T014仍1条C/3条R。

源码同步和托管CI状态分别以[最新同步回执](../00-project/server-sync-receipt.json)的精确提交及观测时间为准。已通过的旧CI不能自动覆盖新文档提交；新CI在运行时保留in_progress，不写PASS。Python候选继续暂缓，原py310/100包锁、公共接口/迁移和共享服务保持本批边界。

上一批导航提交的CI run 39255897321已核验：身份任务成功，engineering在候选输入清单摘要检查失败。原因是任务/导航更新后未重新生成NOT_FROZEN候选；本批审查文件差异后按既有生成器刷新，未修改或放宽检查。原失败及修复范围见[CI观察记录](../00-project/validation/t014-preparation-ci-observation.json)。本轮新提交的托管结果另按精确提交核验，不用上一轮状态替代。
