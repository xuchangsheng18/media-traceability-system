# N01剩余准入事项与确认清单

2026-10-18（北京时间）。本页统一记录当前剩余工作和需要确认的事项，不再通过不断新增材料轮次代替实际风险处置。**N01仍未通过整体准入；Python候选继续暂缓，原100包锁和共享服务保持。**

[机器确认清单](../00-project/validation/native-n01-admission-decisions/confirmation-register.json) · [12条CVE逐项状态](../00-project/validation/native-n01-admission-decisions/python-pg-open-items.json) · [游标具体修复申请](native-n01-cursor-hardening-change-request.md) · [原生状态](native-linux-execution-status.json) · [任务导航](../../tasks/README.md)

## 这次实际核验与新增发现

上一轮最终回执提交`fd428efc464ab0bcfbd0299bfaaf74fe56313f97`的[CI39109417756](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39109417756)成功。336201字节制品SHA256为`20150addfaef46e281811c4845d2a4d97c7b0b7e7fda542dd40b09c5b8f952a2`；32项门禁及6份关键报告已核对。后续提交以各自CI为准。

本轮在既有Linux py310中完成[11项解析观察](../00-project/validation/native-n01-admission-decisions/cursor-parser-observations.json)，直接调用当前解析函数、使用自有内存数据库协作者，未连接真实数据库或网络，未运行HTTP/RLS验收，不能把夹具返回当业务实现通过。

控制分页仍接受同一已签名原始游标的跨字母表编码别名；夹具中记录范围不变，载荷和调用者变更被HMAC拒绝。上传分页先校验编码文本HMAC，拒绝未重新签名的文本变更，但未强制规范编码；持有合成测试签名密钥的夹具签发方仍可生成被接收的非规范文本。没有据此认定发生无密钥伪造或越权，也没有把这些行为称为已修复。

现有默认解码行为仍可观察到填充后内容被忽略。[Python官方版本表](https://devguide.python.org/versions/)本次仍列3.10为2026-10-01停止支持；[本次上游记录核对](../00-project/validation/native-n01-admission-decisions/upstream-review.json)说明相关兼容性补丁不等于立即严格拒绝其他字母表。应用约束与解释器维护是两个事项，不能互相替代。

## 当前答复与影响边界

2026-10-18用户希望继续使用Python3.10，并询问取消N01阻塞对项目影响是否很小；这是一项影响提问，未提供供应商延长维护证明，也不是明确的风险接受或整体准入决定。Python候选继续暂缓，现有解释器、原100包锁及共享服务不变。

当前已验证的Linux/py310/CPU内部研发可以继续开展满足依赖的工作；N01是全原生迁移的制品与软件准入步骤，其未通过不等于全部业务开发必须停下。现有功能通过测试只能证明已测功能在当前环境运行，不能证明未来维护、安全补丁、迁移恢复和正式交付风险很小。取消状态文字不会补齐技术证据，故保留N01的未通过状态；生产、离线及GPU仍另行验收。若未来提出有期限的研发例外，须单独明确用途、控制措施、责任、截止和退出条件，本次不代填或视为已批准。

| 编号 | 当前状态 | 后续动作 |
| --- | --- | --- |
| D01：Python3.10维护依据 | 未提供延长维护或补丁支持证明；已记录继续使用意向及影响提问，未接受风险 | 有材料时核对发行者、精确版本与补丁范围；候选继续暂缓。当前不需要为了继续已验证研发而重复确认相同意向。 |
| D02：下一批游标修复范围 | 用户明确答复“同意下一批按申请实施”；`APPROVED_NEXT_BATCH_NOT_IMPLEMENTED` | 下一批按[已批准申请](native-n01-cursor-hardening-change-request.md)完成代码、回归与说明。本轮仅登记决定；无需重复确认同一修改范围。 |

D02授权不改变合法签发格式、密钥、端点或数据库结构，也不接受Python生命周期风险。授权、实现、测试通过和整体准入是不同状态；当前业务代码未修改。

## 以后才需要：当前不要一并批准

| 编号 | 时点与内容 |
| --- | --- |
| D03：整体软件准入 | Python维护/CVE和具体技术处置有证据后，再逐组件作实际决定。当前不要求“全部同意”，不能用审批掩盖技术缺口。 |
| D04：最终可安装锁 | 这是前置准入通过后由执行方完成的工作；三项预选已有确认，不需要重复选择。 |
| D05：N02管理员初始化 | N01通过、执行包就绪后再交徐昌胜操作；当前没有安装或sudo步骤。 |
| D06：N04备份公钥/保管 | 已明确徐昌胜保管且公钥尚未建立；到该步骤再按清单建立，不上传私钥。 |
| D07：停写、切换和实际运行发行 | 演练及接收范围明确后再决定窗口、保留与转交条件；当前不编造日期或对外运行发行许可。 |

已经确认的Python候选暂缓、三项原生制品预选、当前内部研发范围及此前有限材料复核均保留；不重复提问，也不扩大认可范围。生产、离线、Windows原生及GPU仍按原决定另行验收。

## 未关闭的12条CVE，一个不遗漏

下表沿用原逐项技术状态：3条限定不受影响候选、2条争议、7条行为或条件复核。原扫描与空缺的正式决定保留；“候选”“争议”都不自动变成安全通过。前轮31项特殊许可、40嵌套坐标及材料保留的[限定技术复核](native-n01-nested-license-use-review.md)仍有效，不重新写成尚未采集。

| CVE | 保留的技术状态 | 还需要的处置 |
| --- | --- | --- |
| CVE-2017-8806 | NOT_AFFECTED_CANDIDATE_PRODUCT_NOT_PRESENT | 复核产品边界后可按本精确制品签认，保留原扫描；未来APT安装该包必须重新核版本。 |
| CVE-2023-36632 | DISPUTED_REVIEW_REQUIRED | 确认实际邮件解析/输入限额与错误处理；争议不能直接当修复。 |
| CVE-2024-3220 | NOT_AFFECTED_CANDIDATE_PLATFORM | 只适用当前Linux；Windows原生部署另审，不改扫描忽略列表。 |
| CVE-2025-12781 | OBSERVED_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 已增加本轮生产解析函数合成探测；修复未实施 |
| CVE-2025-15366 | OBSERVED_COMMAND_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 不能声称当前模块已修补；核对正式用途和传递调用，采用受维护补丁或有时限的范围限制；启用邮件功能前必须处置。 |
| CVE-2025-15367 | OBSERVED_COMMAND_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 不能声称当前模块已修补；核对用途及传递调用，采用受维护补丁或范围限制；保留控制字符拒绝测试要求。 |
| CVE-2026-12003 | CONDITIONAL_SCOPE_REVIEW_REQUIRED | 还须核对父目录所有权/写权限、Conda补丁与启动策略；当前不存在不是长期不可利用证明。 |
| CVE-2026-12345 | CONDITIONAL_SCOPE_REVIEW_REQUIRED | 以非特权、私有0700目录和无不可信并发写入约束临时操作；核对源码修补、权限和使用者，不实施共享目录攻击。 |
| CVE-2026-3298 | NOT_AFFECTED_CANDIDATE_PLATFORM_AND_API | 限定当前解释器与平台，保留正式安全复核。 |
| CVE-2026-3446 | OBSERVED_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 已增加本轮生产解析函数合成探测；修复未实施 |
| CVE-2026-3479 | DISPUTED_REVIEW_REQUIRED | 不允许未授权路径作为resource；保留争议与软件准入决定。 |
| CVE-2026-6019 | OBSERVED_BEHAVIOR_APPLICATION_REVIEW_REQUIRED | 不将不可信cookie嵌入脚本；核对实际模板/传递调用，记录修补或有条件例外。 |

本页不修改解释器、依赖锁、业务代码、服务、卷或数据库；不增加170任务中的整任务验收数。后续依据D01实际证据及已批准D02范围推进相应工作，不自动实施后续业务任务或原生安装。
