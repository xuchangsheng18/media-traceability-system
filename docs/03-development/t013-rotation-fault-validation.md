# T013：密钥轮换、故障拒绝与CI补齐

2026-10-19。本批执行已批准的[T013设计](t013-keycloak-identity-design.md)及[8步计划](t013-keycloak-implementation-plan.md)中第5、6、8步的剩余研发范围。当前结果以[专属执行报告](../00-project/validation/t013-rotation-fault-report.json)、[身份CI报告](../00-project/validation/t013-identity-ci-report.json)和[22项登记](../00-project/validation/t013-keycloak-acceptance-ledger.json)为准；源码提交、运行时间和摘要分别保留。T013整卡未因本批测试通过而关闭。

## 本批实现与验证

| 范围 | 实际行为和验证 |
| --- | --- |
| 签名密钥轮换 | 只在随机临时验收realm生成高优先级RSA签名密钥；真实浏览器取得轮换前后令牌，校验不同kid及公开JWKS。旧密钥保留时旧令牌继续有效；显式撤下旧密钥后旧令牌拒绝，新令牌仍有效。未读取或导出签名私钥。 |
| 客户端secret轮换 | 真实轮换临时客户端secret；旧适配器返回既有503，新secret核验同一真实令牌成功。两种密钥轮换分别记录，不相互替代。 |
| 网络及协议故障 | 对真实身份服务的有效令牌先做正向核验，再经本机临时TLS故障端点注入断连、等待超时、慢速响应、401/500、重定向、损坏/重复JSON、超大响应及错误类型；均拒绝，无模拟身份回退。 |
| TLS与令牌边界 | 配置真实身份目标，验证错误信任链、畸形、空、空白及超长令牌被拒绝。空白、空和超长值由本地输入校验拒绝，不冒充全部请求均送达Keycloak。原签名伪造、错误issuer/audience、实际过期和撤销测试保留重跑。 |
| 数据库故障 | 先建立真实令牌与隔离业务数据库映射，再分别验证错误口令、拒绝连接、语句锁等待超时及连接池耗尽；均返回既有503，不返回Actor。锁只作用于本次随机测试数据库，结束后释放。 |
| 响应耗时修复 | 初次真实TLS慢速响应测试失败：配置窗口已过，但原实现仍按完整响应处理。现增加单调时钟检查并按小块消费响应，超时拒绝为503；保留初次失败和后续通过证据。 |
| 报告门禁 | 三组实际JUnit必须存在、有执行用例且无失败/错误/跳过；元数据须与用例节点一致。缺件、空执行、失败、错误、跳过、计数矛盾和损坏XML均不能得到PASS。原始日志和失败正文不进入公开报告。 |

响应进度检查与HTTPX逐次I/O超时共同工作；这是实际已测响应路径的拒绝控制，不是操作系统级硬实时中断，也不保证所有调度、连接阶段或任意第三方协议都严格在同一个秒数结束。没有将本批加固记为CPython补丁或N01九条漏洞整体关闭。

## 修改位置及复用

- `backend/business_app/identity/tokens.py`：复用逐次introspection、既有401/503及T012身份映射，增加响应耗时检查；接口、表结构、签发格式与权限策略保持既有契约。
- `tests/identity/test_key_rotation_live.py`、`test_faults_live.py`：真实轮换及故障用例。既有映射夹具归入同目录`conftest.py`供各测试复用，原断言保留。
- `scripts/identity/checks.py`、`tests/platform/test_t013_identity_checks.py`：可重复执行三组专项、汇总脱敏结果并验证报告失败路径。
- `.github/workflows/identity.yml`、`scripts/identity/ci.py`：在一次性GitHub托管VM中按原镜像摘要及原py310锁重建测试身份栈。脚本先验证托管环境，普通机器拒绝；固定身份地址仅在该VM的回环上重现，不改Linux服务器网络。
- `.github/workflows/ci.yml`：调用身份工作流；即使其失败，原必需`engineering`检查仍执行失败守卫，不能因依赖失败而跳过为成功。平台保护规则未改动。
- 类型检查：身份测试目录纳入原质量范围；统一脚本类型检查的模块命名。旧独立脚本的运行导入分支保留，未增加缺失导入豁免、删除测试或降低断言。
- 导航：任务卡以本任务实际更新日期显示；总导航从台账计算完成/剩余数量，消除旧74/695等硬编码说明。

## 实际执行入口

在现有Linux py310、显式私密身份目标及隔离业务数据库下执行：

```text
python -m scripts.identity.checks run --private-root <新的Git外0700结果目录> --output <脱敏报告路径>
python -m pytest tests/platform tests/stage_three tests/poc tests/native -q
python scripts/verify_business_foundation.py run
python scripts/dev.py format-check
python scripts/dev.py lint
python scripts/stage_three_types.py check
```

精确参数、测试数量、源码摘要和初次失败见专属执行报告。各组测试有重叠，不把225专项、单元及业务回归数量相加当独立功能数。私密配置、原始JUnit与日志保存在Git外；CI仅上传脱敏报告，制品大小及SHA256由实际平台回读核验。

## 验收边界与剩余事项

本批补齐IDP-07、IDP-15的限定技术证据；IDP-11/16关联新增负向和secret适配器验证；IDP-22按本批源码对应的实际托管运行判定。当前逐项状态及计数以22项登记为准，不用历史CI或文件存在替代执行。

2026-10-19用户已确认T013实际开发负责人为徐昌胜，随后又明确将身份管理员和T013指定复核人均登记为徐昌胜，见[责任登记](repository-access-control.md)和[人员确认记录](../00-project/validation/t013-role-assignment.json)。T013仍需剩余工时、实际复核记录及适用正式条件。重启、日志/历史凭据及恢复回切的后续范围见[恢复批说明](t013-recovery-validation.md)；软件准入、实名管理员/MFA与bootstrap实际交接仍分别验收。本轮轮换批未实施正式账号交付、服务切换或生产恢复。六角色候选设计继续默认拒绝未配置的案件/来源权限。

Python3.13/3.12候选继续暂缓；原Python3.10.22及100包锁保持。GitHub与Linux同步指源码和证据，运行中业务服务版本另行记录；没有自动开始T014。
