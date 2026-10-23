# main分支保护：已获授权的设置与复验

日期：2026-10-17。执行人：徐昌胜（GitHub `xuchangsheng18`）。用户已在页面保存规则；只读回查确认规则25302203为Active，目标为main，PR、禁止删除和强推规则已启用。必需检查已由用户修正为`engineering`并回查确认，来源为GitHub Actions。当前连接器没有管理写入工具，不能代为改名。源码中的工作流不能代替平台合并拦截。

## 最新回查

[实际规则回查记录](../00-project/validation/main-protection-readback.json)。规则已存在不等于T006已关闭：检查名已修正；普通PR#1预设故障失败后实际禁止合并，见[实际拦截记录](../00-project/validation/main-protection-enforcement-report.json)。同一PR的恢复及关闭结果以该记录为准。响应未给出完整bypass_actors，不能仅凭当前连接器不可绕过推断所有账号均不可绕过。旧branch protection摘要中的检查列表为空不能用于否认新ruleset；本次以具体ruleset详情为准。

## 保存规则

1. 使用仓库所有者账号打开[仓库设置](https://github.com/xuchangsheng18/media-traceability-system/settings)，依次选择 **Rules → Rulesets → New ruleset → New branch ruleset**。
2. 名称填 `main-engineering-protection`，Enforcement status选 **Active**。目标分支只选择默认分支`main`，不要包含本次开发分支。
3. Bypass list保持空；不要加入管理员或GitHub App绕过项。
4. 勾选 **Restrict deletions**、**Block force pushes**。
5. 勾选 **Require a pull request before merging**。当前未决定审批人数，不自行要求一个不存在的第二评审人，也不把PR规则当作业务双人审批。
6. 勾选 **Require status checks to pass**，添加实际检查名 **engineering**，检查来源选择GitHub Actions（若页面支持）。添加后确认它确实出现在必需检查列表中。
7. 保存规则。不要勾选`Restrict updates`或`Lock branch`，避免将正常PR合并也整体锁死。

上述规则及必需状态检查的行为依据[GitHub官方规则说明](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)和[规则创建说明](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)。保存后回复“已保存”；无需提供密码、Token或私密配置。

## 复验与T006关闭证据

- 只读查询`main`和rulesets，确认有效规则的目标为main、状态Active、必需检查包含engineering、PR规则开启且无绕过。
- 在独立测试分支提交一个明确会失败的无敏感测试，创建面向main的PR；等待engineering实际失败，记录GitHub禁止合并的状态。不要将失败代码合入main。
- 修正该分支的失败用例，确认同一PR当前提交的engineering变绿。测试完成后关闭该PR即可，不必为了验收合并测试代码。
- 记录实际PR号、失败/成功提交、检查运行号、规则ID及复核人。只有配置和“失败阻止合并”均有实际证据，才可关闭T006该项。

本次CI工作流增加功能分支push触发，以获得当前代码的托管结果；没有移除main/PR触发或降低既有门禁。PR创建与规则设置仍受当前账号接入能力限制。
