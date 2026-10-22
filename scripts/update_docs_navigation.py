"""Refresh the actual docs file index, retaining specific existing descriptions."""

import json
import re
from pathlib import Path
from urllib.parse import unquote

from generate_remaining_work_navigation import build as remaining_navigation
from generate_requirements_document import build as requirements_document
from generate_stage_status_navigation import build as stage_status_navigation
from generate_stage_three_docs import build as stage_three_documents

ROOT = Path(__file__).resolve().parents[1]


def main():
    for path, content in stage_three_documents().items():
        (ROOT / path).write_bytes(content.encode("utf-8"))
    content, summary = requirements_document()
    (ROOT / summary["document"]).write_bytes(content.encode("utf-8"))
    for path, content in stage_status_navigation().items():
        (ROOT / path).write_bytes(content.encode("utf-8"))
    for path, content in remaining_navigation().items():
        (ROOT / path).write_bytes(content.encode("utf-8"))
    nav = ROOT / "docs/README.md"
    old = nav.read_text(encoding="utf-8")
    descriptions = {}
    for line in old.splitlines():
        match = re.match(r"\| \[[^\]]+\]\((<[^>]+>|[^)]+)\) \| (.+) \|$", line)
        if match:
            descriptions[unquote(match[1].strip("<>"))] = match[2]
    prefix = old.split("## 当前文件完整索引", 1)[0]
    prefix = prefix.split("## 第一阶段实际材料", 1)[0]
    prefix = prefix.split("## 第二阶段实际工程文档", 1)[0]
    prefix = prefix.replace(
        "当前为规划和开发输入候选，NOT_FROZEN。资料已经归档不等于系统已经实现，结构校验也不等于所有业务语义通过。",
        "当前CPU研发最小工程已运行并通过本机CI；正式业务/生产仍NOT_FROZEN。文档、结构校验、研发闭环与正式业务验收分别判定。",
    )
    task_rows = json.loads((ROOT / "tasks/execution-status.json").read_text(encoding="utf-8"))["tasks"]
    completed_count = sum(len(row["completed_steps"]) for row in task_rows)
    remaining_count = sum(len(row["remaining_steps"]) for row in task_rows)
    total_count = completed_count + remaining_count
    prefix = re.sub(
        r"^任务执行入口：.*$",
        f"任务执行入口：[分步任务导航](../tasks/README.md#分步任务导航)、[{len(task_rows)}张独立任务卡](../tasks/README.md)、"
        f"[同源状态台账](../tasks/execution-status.json)、[{total_count}条执行事项逐项清单](00-project/task-execution-steps.txt)。"
        f"当前有{completed_count}条已验证子步骤、{remaining_count}条剩余工作；全局编号0001—{total_count:04}。"
        "任务内C/R编号、实际证据与剩余条件保持对应；子步骤数量不换算为整任务完成率。",
        prefix,
        flags=re.M,
    )
    entries = {
        "03-development/t024-worker-isolated-integration.md": "T024目标绑定修复、独立worker进程与真实队列故障联调；区分启动撤销、回调拒绝、提交后未ACK重投，以及常驻部署、正式授权、队列进展和清理恢复的剩余条件。",
        "00-project/validation/t024-worker-isolated-integration-report.json": "T024限定子范围的实际命令、源码和日志摘要、失败修复、完整业务回归及精确CI/源码同步；不把测试权威或进程重启当正式组合验收。",
        "03-development/t024-object-durability.md": "T024 Linux文件、对象目录及根目录落盘屏障、初始化重试与故障拒绝；区别目录同步实测与断电、孤立对象清理和完整恢复。",
        "00-project/validation/t024-object-durability-report.json": "T024目录持久性限定子范围的精确源码、RED/GREEN、相邻回归、质量检查、CI和源码同步；不登记共享采用或整任务验收。",
        "00-project/validation/t024-durability-final-ci-report.json": "T024精确落盘提交的最终托管证据：业务952/权限1092等通过，整体CI因9条Python发现和Torch未覆盖仍失败；排除产物中的旧副本。",
        "03-development/t031-candidate-task-plan.md": "T031候选DAG不可变解析、显式预算、模型字段绑定、固定摘要和入口选择；未选分支不冒充运行状态，不授予调度或正式策略资格。",
        "00-project/validation/t031-candidate-task-plan-report.json": "T031解析层的精确源码、36候选图、失败修复、77项解析和相邻回归、质量及CI/源码同步；任务创建、真实提供者和整卡验收仍待。",
        "00-project/validation/t031-candidate-plan-final-ci-report.json": "T031精确解析提交的最终CI证据：业务1029、权限1092等通过；整体因12条Python扫描发现及Torch未覆盖失败，旧报告排除，原锁与门禁保留。",
        "04-database/task-event-run-integrity.md": "T032的0015事件固定运行复合外键、现有11态词汇约束、合法历史保留和失败原子回滚；不实现状态迁移或共享升级。",
        "00-project/validation/t032-task-event-integrity-report.json": "T032运行事件约束的RED/GREEN、隔离升级和回滚、相邻权限/恢复回归及源码摘要；CI、同步与整任务验收分开记录。",
        "00-project/validation/t032-task-event-final-ci-report.json": "T032精确提交的完整CI：两份业务回归各1057项含1失败，T014及当前安全扫描未执行；旧副本排除，失败身份未保存，不猜测根因。",
        "03-development/ci-safe-failure-diagnostics.md": "T006安全失败选择器、源码AST绑定、参数及异常文本省略和20条上限；补0015非超级用户测试清单，完整业务失败与T033后续分别记录。",
        "00-project/validation/ci-safe-failure-diagnostics-report.json": "T006失败定位的6项RED/GREEN、37项相邻检查、非超级用户迁移测试复现修复与质量/同步；原业务CI是否恢复以精确新运行核验。",
        "00-project/validation/ci973-final-ci-report.json": "精确973a7d7最终CI：业务1057、T014权限1092等通过；整体安全扫描失败，Python25条及工具1条，Torch未覆盖；不继承为后续源码验收。",
        "03-development/t033-cancellation-atomic-writer.md": "T033两条既有取消路径的统一写入、运行/行版本及范围校验、savepoint/CAS和事件/outbox原子性；全业务状态机及正式规则仍未完成。",
        "00-project/validation/t033-cancellation-atomic-writer-report.json": "取消专用写入器的实际RED/GREEN、受影响数据库回归、故障/并发/撤销、质量与源码同步；只证明T033工程子范围。",
        "00-project/validation/ci18f-final-ci-report.json": "精确18f36bf最终CI：业务1095、权限1092及类型256通过，整体仍因Python25条及工具1条扫描匹配失败；Torch未覆盖，后续前端不继承为通过。",
        "03-development/task-cancellation-console.md": "已有取消后端的页面接线、版本与明确确认、未知结果原请求重试和身份/任务切换；202不当停止，T034可信创建映射及真实worker仍未齐。",
        "00-project/validation/task-cancellation-console-report.json": "T039取消前端的实际RED/GREEN、39项新单元、完整前端与开发/生产浏览器验证、复核补强及三端同步；自建传输夹具不当真实后端E2E。",
        "03-development/backend-frontend-data-test-priority-plan.md": "T001—T123按后端、前端、数据、测试及实际依赖推进；本批来源同步和离线标注工具的具体范围、保留门禁及交付边界。",
        "00-project/validation/backend-frontend-data-test-report.json": "来源授权同步事务/原请求头、前端回执、离线标注质检及原权限门禁的实测证据，精确CI与源码同步分开记录。",
        "07-datasets/annotation-validation.md": "D01—D15显式文件离线质检：本地Schema、时间区域边界、UUID重复冲突、预算与脱敏；真实授权、双人仲裁和抽样仍未验证。",
        "07-datasets/public-development-data.md": "2张官方CC0原图与5个可追溯派生文件，7文件/6唯一摘要、来源和坐标核对；视频未生成，无业务标签、模型精度或正式数据准入推定。",
        "00-project/validation/public-development-data-report.json": "Windows实际下载、Linux同摘要解码、26项无跳过安全测试、240文件类型检查及Linux直连下载失败与替代路径。",
        "00-project/validation/t060-readonly-ui-report.json": "T060只读模型/评测页面的129项单元与36项浏览器传输回归、权限撤销修复及尚缺健康/发布/回滚边界。",
        "03-development/t001-t123-resource-registry-continuation-plan.md": "本轮四接口及资产下载页面的具体实现与验证边界，沿用契约、原锁、门禁和Python候选暂缓。",
        "03-development/t001-t123-development-completion-audit.md": "123项原工作范围及验收逐条复核：真实源码、有限验证、尚缺代码和外部输入分列，不以表或路由代替任务完成。",
        "03-development/t001-t123-development-completion-audit.json": "同源123项验收条款、代码摘要、接口现状、剩余代码和后续批次的机器审计；无虚构整卡完成。",
        "00-project/validation/t001-t123-resource-registry-report.json": "来源登记、受控下载及页面、模型/评测列表、0014的实际检查与失败修复，CI和源码同步分别核验。",
        "04-database/resource-registry-boundaries.md": "0014固定查验函数、owner限定策略、零字节/时间精度、不可变对象读取和运行库采用边界。",
        "08-security/resource-registry-route-registration.json": "四个现有接口的严格47→51后继注册，不改变246格、公共契约或正式拒绝。",
        "08-security/history/resource-registry-predecessor-scope-matrix.json": "本轮之前47项挂载矩阵的原字节，和报告读取历史形成可核验后继链。",
        "03-development/t001-t123-api-continuation-plan.md": "本批续建顺序：权限目录性能、报告读取及0013、真实资产/任务前端、原CI门禁和三端源码同步；保留正式准入边界。",
        "03-development/t001-t123-remaining-interface-register.md": "保留起点27项追踪记录并列当前状态；当前51项已挂载、22项未挂载，逐项区分代码与外部条件。",
        "03-development/t001-t123-remaining-interface-register.json": "27项接口的完整结构、源任务/依赖、SQL定义、实际实现范围和后续执行入口；静态审查与运行证据分列。",
        "00-project/validation/t001-t123-api-continuation-report.json": "本批缓存、报告读取/0013及前端的实际命令、时长、错误修复、完整权限回归、CI与三端同步证据。",
        "08-security/report-read-route-registration.json": "只登记getReport挂载增量，严格绑定46→47的矩阵字节；原246格、正式拒绝与旧采用记录不改。",
        "08-security/history/report-read-predecessor-scope-matrix.json": "新增报告读取之前46项挂载矩阵的原字节历史；对应47项阶段的后继校验，当前总体挂载数见页首及资源接口回执。",
        "03-development/t001-t123-implementation-inventory.md": "T001—T123逐项开发清单：原工作范围、表与版本迁移、HTTP操作、实际Python方法、证据和剩余工作；静态实现、运行验证和整任务验收分别记录。",
        "03-development/t001-t123-implementation-inventory.json": "123任务及后端方法、SQL函数、表和路由的机器索引，绑定源摘要；包含完整验收/测试原要求，不从已有表或方法自动推导完成。",
        "03-development/t001-t123-catalog-read-implementation-plan.md": "已授权资产详情、案件级资产与任务列表的落实计划；复用现有表，0012仅隔离验证，两个必填case_id已由用户确认。",
        "03-api/catalog-read-contract-change.md": "两个列表必填case_id的确认和兼容影响；三个实际读取接口、授权与游标边界、迁移和现有运行库状态分列。",
        "00-project/validation/t001-t123-catalog-read-report.json": "本批三项读取、0012及质量检查的实际结果；完整权限门禁、托管CI、源码同步与现有0011演示库状态分别记录。",
        "08-security/catalog-read-contract-adoption.json": "固定六角色规则的旧源摘要与本批三个读取操作的新契约绑定；只记录已确认参数和挂载增量，不改变角色格或启用正式权限。",
        "08-security/history/t001-t123-catalog-predecessor-openapi.yaml": "本批之前85327689提交的OpenAPI原字节快照，用于核对已确认六角色规则的历史来源，不作为当前调用契约。",
        "08-security/history/t001-t123-catalog-predecessor-scope-matrix.json": "本批之前85327689提交的权限范围矩阵原字节快照；保留历史绑定，当前46项源码挂载与真实验证另列。",
        "03-development/t014-isolated-review-disposition.md": "最终独立复核的7项重要问题、一次TDD修复批次、人员/代际续期与实际来源/列表范围；实际结果和未验收边界分列。",
        "00-project/validation/t013-owner-mfa-negative-attestation.json": "徐昌胜本人反馈仅密码不能进入控制台、单次错误OTP被拒绝；与自动正向回执分开，未独立关联负向事件，不含秘密。",
        "09-testing/t014-isolated-operation-coverage.md": "73操作逐项区分43挂载/30未挂载、实际组件证据及HTTP允许边界；完整当前修订验证状态另列，246格不当HTTP通过数。",
        "09-testing/t014-isolated-operation-coverage.json": "每操作的方法/路径/41权限/六角色条件、实际测试ID、正例/拒绝及未实现条件；保留证据源码范围。",
        "00-project/validation/t014-isolated-work-report.json": "P06提交后76项、39项针对性与质量结果、真实队列/节点/交付及六类三次稳定拒绝测量；非正式服务身份或生产SLA。",
        "03-development/t014-isolated-implementation-decisions.md": "P01—P07全部实施裁定按执行顺序保存，逐项列原因与判断错误代价；与正式业务制度、共享采用和整卡验收区分。",
        "00-project/validation/t015-role-assignment.json": "用户明确T015开发负责人、指定复核人均为徐昌胜；仅登记职责，工时、实际复核和验收仍待，不创建账号或授予权限。",
        "00-project/validation/t015-dependency-preflight.json": "T015只读前置核对：绑定T014隔离通过证据、现有Scope/RLS/对象读取边界及实际旧测试组；不把64表全路径隔离或正式身份联调标为完成。",
        "03-development/t015-data-scope-design.md": "T015本人已批准的三种数据范围、增量RLS、对象/导出绑定及测试设计；实际代码、验证和未完成项以逐项进度为准。",
        "00-project/validation/t015-data-scope-p01-report.json": "P01精确代码及49新范围测试/289既有纯回归、质量和RED证据；仅类型/14种定位目录/64表分类，不是SQL或HTTP接入。",
        "00-project/validation/t015-data-scope-progress.json": "已批准T015计划P01—P07实际逐项状态、精确候选及运行结果；失败与重跑保留，不以编码或测试准备替代完成。",
        "00-project/validation/t015-data-scope-p02-progress.json": "P02三种事务、固定元数据、真实SQL/HTTP/工作链的定向及完整验证；保留461项首轮4失败、前向修复和完整重跑的实际状态。",
        "00-project/validation/t015-current-ci-observation.json": "按精确提交核验托管CI；旧提交类型失败、本地修复和新提交尚未验证分别记录，不用历史成功替代当前结果。",
        "00-project/validation/t015-data-scope-p03-report.json": "精确aa2070b的21项新范围与70项保留适用测试，共91项全部通过及质量结果；仅P03隔离子范围，P02完整CLI和后续字节/恢复/CI另列。",
        "09-testing/t015-data-scope-coverage.md": "数据范围调用导航：64表目录与12类真实调用分别列约束、测试及P04字节边界；30未挂载、正式提供者及最终验收保持待完成。",
        "09-testing/t015-data-scope-coverage.json": "可机器核验的64表分类、12类调用/具体测试、精确源码摘要及30未挂载清单；目录、DAO/HTTP和对象字节验证不混算。",
        "04-database/data-scope-migration.md": "0010数据范围增量、64表分类、三种事务、15种固定元数据及7项函数/ACL；说明实际代码、验证和共享采用边界。",
        "03-development/t015-data-scope-implementation-plan.md": "T015已批准P01—P07：类型、三模式/增量RLS、DAO/集合、对象、恢复、33门禁及交付；各步骤按实际证据勾选，未执行项不预填通过。",
        "03-development/t016-operation-token-implementation-plan.md": "T016已授权隔离实施计划与执行状态；固定案件签发、同根消费、迁移、43/30目录及消费者差异，实际运行结果另见专项报告，不代表正式采用。",
        "04-database/operation-token-extension.md": "0011令牌12项内部绑定字段、27列和64表861列版本边界；摘要存储、幂等秘密重建、共享锁/同事务消费及旧记录保留，不代表共享库升级。",
        "08-security/t016-operation-token-boundaries.md": "案件task/seal令牌的授权、独立批准、当前密钥/代际和TTL边界；真实封存角色冲突、未接入消费者及采用前决定逐项列出。",
        "00-project/validation/t016-operation-token-report.json": "T016严格运行门禁回执：固定六文件、完整实际nodeid与源摘要、无跳过及独立失败探针；仅据实际PASS解释隔离实现，不替代整卡验收。",
        "00-project/validation/t016-development-progress.json": "T016本批实际开发步骤、RED/GREEN和独立复核、源码与运行采用差异、CI及具体剩余事项；不预填正式审批。",
        "00-project/validation/t016-role-assignment.json": "用户确认徐昌胜为T016开发负责人和复核人；仅职责登记，不授予权限，不表示本人已经验收。",
        "00-project/validation/t015-data-scope-report.json": "精确源码提交的T015实际必需范围CLI：具名SQL/HTTP/对象/恢复用例、S01—S09、真实失败探针和64表目录；目录核验不当DAO覆盖，局部通过不当全业务或托管CI通过。",
        "00-project/validation/t015-implementation-plan-review.json": "T015计划覆盖、自查、精确获审版本及本人批准；批准与代码实施、测试、验收分别登记，原1009测试模块保留。",
        "00-project/validation/t014-final-document-ci-observation.json": "3ff文档提交的镜像下载失败与同提交重跑观测；历史代码通过、当前运行和后续提交CI分别记录，不伪称最终通过。",
        "00-project/validation/t015-written-design-review.json": "本人设计方向及书面设计批准、精确获审版本和仅状态更新关系；具体计划亦已获准；代码实际子范围以逐项进度为准，不当整卡验收。",
        "00-project/validation/t014-p07-current-code-ci-report.json": "本批修复后精确代码提交的身份、权限、业务、32工程门禁及13运行检查；独立核对两份制品平台摘要，回执文件自身的未来CI另查Actions。",
        "00-project/validation/t014-p07-ci-c89e75b-report.json": "修复前c89检查点的真实成功CI及平台制品摘要；明确为历史证据，不证明后续7项修复或最终回执通过。",
        "00-project/validation/t014-isolated-validation-report.json": "P07当前完整回归、门禁/类型/资料检查及中断历史；未完成的执行窗口和最终CI保持真实状态。",
        "00-project/validation/t014-isolated-ci-report.json": "按精确提交记录托管身份/engineering、清单摘要失败和修复后结果；最终回执CI未核时不写通过。",
        "04-database/authorization-fence-extension.md": "0007完整角色、0008授权代际表6字段及0009精确工作身份查询；64表849字段适用版本、函数/锁/恢复/真实委托及未共享采用边界。",
        "00-project/validation/t014-isolated-fence-report.json": "P05精确代码提交的99项隔离测试、原失败历史及SQL升级/实际备份恢复；不包含P06后台工作或正式撤销SLA。",
        "03-development/t014-isolated-six-role-implementation-plan.md": "PR01/02/04下一批P01—P07：可信完整角色、对象条件、独立人员、审批TTL及撤销栅栏；具体计划已确认，实际实施/测试结果单列，未共享采用。",
        "03-development/t001-t123-development-sequence.md": "用户确认T001—T123开发范围、逐项依赖及分批顺序；综合专项测试后置、实现必要测试保留，T092依赖T164不删除。",
        "03-development/t001-t123-development-sequence.json": "全部123项授权范围、源/候选依赖、台账子范围与未完成计数；不是实际可执行性或完成证明。",
        "00-project/validation/t014-isolated-plan-review.json": "计划编制时的覆盖/接口/引用历史核查及随后批准记录；当前逐项执行结果另见isolated-rule-progress，不将历史CI当作新代码验证。",
        "00-project/validation/t014-isolated-rule-progress.json": "P01—P07实际完成项、精确源码提交、隔离测试数量、失败历史和质量检查；未执行项和共享采用单列。",
        "03-development/t013-named-admin-adoption-checklist.md": "本人明确批准的四项精确采用范围、采用前历史预检、当前CA/账号/专用MFA配置和实际管理回执；bootstrap仍保留。",
        "03-development/t013-known-signer-copy-disposition.md": "两种旧导出的双E归档实际解密及本人授权四份精确文件逻辑退役；保留现用密钥/新备份，不证明安全擦除或第二介质。",
        "00-project/validation/t013-known-signer-copies-review.json": "旧导出加密归档摘要、实际解密及四份精确旧副本限定退役观察；不收录私钥或口令。",
        "00-project/validation/t013-recovery-subkeys-owner-validation.json": "本人原home及同U盘恢复home的两把精确E子密钥实际解密、状态与明文摘要核查；不是第二独立介质。",
        "00-project/validation/t013-reprotected-signer-owner-validation.json": "第二轮口令保护、真实固定消息签名/篡改拒绝、新保护备份同U盘恢复及失败历史；不含秘密。",
        "00-project/validation/t013-named-admin-adoption-preflight.json": "明确采用前的只读身份配置/本机CA预检历史快照；当前采用结果另见adoption-progress和本人管理回执。",
        "00-project/validation/t013-named-admin-adoption-progress.json": "批准四项身份配置采用后的实际观察及本人首次改密/OTP状态；签名管理会话由单独实际回执证明。",
        "00-project/validation/t013-owner-mfa-management-validation.json": "本人真实密码/OTP与PKCE/nonce/签名管理校验、配置检查及临时令牌文件清理；不含网址/令牌，未关闭真实恢复与bootstrap退役。",
        "08-security/t014-six-role-rule-proposal.md": "六角色41权限246格、73操作及对象/用途条件；PR01/02/04已确认隔离实现输入，PR03/05/06仍待，未变成运行ALLOW。",
        "08-security/t014-six-role-rule-proposal.json": "六角色逐格候选值、完整条件、契约摘要及PR01—PR06待决项；不是活动策略配置。",
        "03-development/t013-owner-action-checklist.md": "徐昌胜本人A01—A10：公开核对、两子密钥解密/备份恢复、签名保护、MFA及共享恢复前置；明确现在可做和暂不能做。",
        "00-project/validation/t014-rule-proposal-document-review.json": "六角色提案和本人清单的实际资料/语法/来源/导航检查；不冒充规则运行测试或本人操作。",
        "09-testing/t014-authorization-test-design.md": "22类权限场景与已有适用测试的对应、部分覆盖及未挂载边界；432为设计组合数，不当运行通过数。",
        "00-project/validation/t014-role-assignment.json": "用户确认T014开发负责人和指定复核人均为徐昌胜；不冒充已实际复核、验收、权限授予或职责冲突制度批准。",
        "03-development/t014-unified-permission-implementation.md": "T014统一权限代码、0006最小权限事实查询、43操作适用回归、源验收逐项对照及正式策略/30未挂载操作/真实交接边界。",
        "00-project/validation/t014-permissions-report.json": "T014实际严格门禁回执：按报告绑定提交核对挂载操作四类拒绝、SQL/撤销/真实资源回归及未挂载清单；历史计数不当当前结果，不证明正式ALLOW。",
        "00-project/validation/t014-full-regression-report.json": "本批完整业务、T014入口及T013令牌适用回归的真实计数、失败ID和源码快照；原始日志不公开。",
        "00-project/validation/t014-gate-execution-report.json": "T014专项门禁与受控失败探针的实际退出状态；失败必须阻止通过。",
        "00-project/validation/t014-implementation-validation-report.json": "本批格式/类型、输入/文档/导航/排期、12份原件及旧锁/旧迁移保全的实际检查，不代替整任务验收。",
        "00-project/validation/t014-implementation-ci-report.json": "当前T014实现提交的托管CI状态、实际检查和制品源码绑定；在途/失败保持实际结论。",
        "03-development/t013-signer-protection-followup.md": "早期密钥保护问题与后续处理入口；当前第二轮保护、实际签名/恢复及旧导出处置以新增精确实际回执为准。",
        "00-project/validation/t013-signer-protection-progress-report.json": "早期备份/吊销副本结构与摘要历史快照；当前保护、签名、解密/恢复及旧副本退役另见新实际回执。",
        "03-development/t013-bootstrap-management-replacement.md": "T013本人MFA/PKCE短期管理会话、无bootstrap回退、独立退役候选与实际操作顺序；不表示共享采用或实名接管。",
        "00-project/validation/t013-bootstrap-management-report.json": "本批管理工具替代、真实隔离MFA/撤销/退役/重启、私密候选及原文件不变的验证；保留失败记录和未验范围。",
        "00-project/validation/t013-bootstrap-management-ci-report.json": "本批精确源码提交的托管CI、两份实际制品摘要及源码映射核对；不能代替整任务验收。",
        "00-project/validation/t013-bootstrap-management-code-review.json": "本批一次独立代码审查、超时清理问题先失败后通过及复核边界；不代替本人验收。",
        "03-development/t013-admin-handover-validation.md": "T013新管理员受控初始化、首次改密/MFA和bootstrap退出的隔离验证、失败记录及本人交接边界。",
        "10-deployment/keycloak-identity-runbook.md": "身份三服务观察、SSH回环管理、实名管理员首次改密/MFA、bootstrap退役顺序及GPG恢复保管要求；不表示已实际接管。",
        "00-project/validation/t013-admin-handover-report.json": "本批T013管理员初始化/MFA/bootstrap/重启的实际验证及精确CI、源码同步；合成管理员不代替实名交接。",
        "03-development/t012-role-model-implementation.md": "T012实际模型补齐、37目录专项/368完整回归、三条源验收对照及正式身份/后续任务边界。",
        "04-database/role-catalog-extension.md": "0005目录开关/撤销三列、旧状态与新默认、唯一/外键/终态、受限DAO和同实例恢复；当前63表843字段。",
        "04-database/role-catalog-extension.json": "0005三列精确类型、默认、源码行与摘要及不改公共API的机器扩展字典；保留历史62/825及0004的63/840。",
        "00-project/validation/t012-role-model-report.json": "真实py310/PostgreSQL的RED/GREEN、368回归、源码摘要、新建空目录库及旧库保留、源验收范围；无连接凭据。",
        "03-development/t001-t011-foundation-review.md": "截至2026-10-17的T001—T011逐项完成和剩余清单：28条已验证子步骤、25条剩余；附最新CI、治理查询及历史验收对照，整任务未关闭。",
        "00-project/validation/t001-t011-foundation-review-report.json": "T001—T011当前同源快照、完成/剩余全文、证据摘要及CI来源；保留早期复核和源验收要求，不把资料复核冒充新功能测试。",
        "00-project/validation/development-container-limits-report.json": "Compose、Docker设置与实际cgroup v2 CPU/内存/pids只读比对；缺失/无限/漂移拒绝，不代表临时盘或压力隔离已验证。",
        "08-security/access-control-model.md": "T011六角色、九个实体及身份/单位/案件关系；候选权限评审与后续0004持久化分别列证据，尚无正式身份授权。",
        "03-development/t012-identity-relations-design.md": "身份提供方与内部用户映射、同单位案件关系、稳定键、软禁用、撤销、管理/查询分权及正式接入边界。",
        "03-development/t012-identity-relations-plan.md": "本批测试、0004增量迁移、内部DAO、空研发库、资料和同步步骤；实际完成状态按实测报告和任务卡核对。",
        "04-database/identity-relations.md": "新增身份映射13列、单位开关和角色撤销2列、复合约束及恢复要求；区分原62表825字段与迁移后63表840字段。",
        "04-database/identity-relations-catalog.json": "0004逐列类型/约束/源码位置和摘要、既有表增量、实际结构版本及没有新增外部API字段的说明。",
        "00-project/validation/t012-identity-relations-report.json": "实际py310/PostgreSQL身份专项、完整回归、源码摘要及独立空研发库验证；不含连接凭据，不代表真实身份认证或整任务验收。",
        "08-security/access-control-model.json": "T011候选机器模型：六角色、41权限码、73操作逐项绑定；职责/限制/待定均非正式ALLOW，分类政策为空。",
        "03-development/t011-access-model-implementation.md": "T002/T010本批依赖、T011四项实施、测试证据与剩余条件；不关闭整任务或正式冻结。",
        "00-project/validation/t011-access-model-report.json": "实际py310专属设计校验与合成评审测试、源码摘要及范围；不证明正式身份或运行时授权。",
        "00-project/validation/t011-dependency-report.json": "T002配置追踪13例及T010模板/本批影响核对，限于T011所需依赖，不关闭上游整卡。",
        "03-development/stage-three/remaining-interface-implementation-plan.md": "剩余11类接口实施范围、顺序及正式前置条件；用户已授权继续实施。",
        "03-development/stage-three/remaining-interface-implementation.md": "剩余11类接口真实代码/数据库/ETag/授权/模型边界说明；73操作102组件、实际43外部及1内部挂载，正式条件另判。",
        "03-development/stage-three/foundation-implementation-plan.md": "六项整改实施顺序、共享维护/平台条件、Codex桌面与环境验收及每批同步；设计范围及详细计划已认可，当前会话实施，计划本身非完成证据。",
        "03-development/stage-three/python-type-check-implementation-plan.md": "独立mypy候选锁/制品、真实类型治理、错误阻断和CI步骤；原100包锁保持，独立检查已实测，CI及后续状态看验证报告。",
        "03-development/stage-three/business-interface-implementation-plan.md": "独立业务迁移/RLS、上传续传和7历史读取的文件/签名/失败测试/恢复计划；73操作825字段0.2快照方案已认可，首批所选工程已实施；后续接口按实际说明和验证报告核验。",
        "03-development/stage-three/readiness.md": "第三阶段16步及57条原验收逐条状态：文档、实测、部分/待落实与适用差异各列证据范围，与24/23步和170任务分开。",
        "03-development/stage-three/deliverables.json": "16源步骤、57条验收审查及实际状态/证据/限制；文档和配置生效独立判定，不伪造人员或批准。",
        "03-development/development-environment-validation-report.md": "第三阶段实际py310/Node/统一命令/独立工具层/三进程浏览器/扫描结果及未执行范围。",
        "03-development/development-environment-baseline.md": "Development Environment Baseline 1.0候选；沿用1.1-py310工程源，正式冻结条件未满足。",
        "00-project/validation/stage-three-runtime-report.json": "实际13项Linux/托管CPU命令与环境；共享栈未重启，GPU/Windows原生/生产未驗。",
        "00-project/validation/stage-three-demo-report.json": "三临时进程11项实测含三服务脱敏日志/trace及依赖停止503/502，1例浏览器；mock标记，无DB/权重/GPU访问。",
        "00-project/validation/stage-three-dependency-scan-report.json": "Python/npm实际已知漏洞扫描、退出状态和包跳过；不是全面安全或PythonEOL/OS准入证明。",
        "00-project/validation/stage-three-foundation-audit-report.json": "开发基础实际审查：共享VM100%及31其他容器、私有保护403、格式AST保全、两端Codex配置启用、Torch官方摘要/12,240载荷和13接口未闭项；正式条件仍待。",
        "00-project/validation/stage-three-platform-observation.json": "只读GitHub真实所有者、私有性、保护标志/规则查询及Actions；不冒充已配置权限。",
        "01-requirements/functional-requirements.md": "单文档详细需求：36业务需求逐项输入/流程/输出/异常/权限/验收与开发关联，全文170任务展开及10NFR/16规则/24协议；源目标、工程证据和未决/正式状态分别标注。",
        "00-project/remaining-work-navigation.md": "两阶段剩余工作总导航：第一阶段6项、第二阶段12项，含已补范围、前置/责任角色/关闭标准、13接口缺口及正式冻结条件；资源位置明确为Linux上的Docker虚拟机数据盘。",
        "00-project/remaining-work-navigation.json": "从19项权威台账与专项来源生成的同源导航索引/摘要；不作新的工作状态源、不关闭任务、不编造人员。",
        "02-architecture/environment-constraints.md": "实际Linux、Miniforge py310、Desktop挂载/网络/CPU与PythonEOL边界。",
        "02-architecture/resource-and-team-inventory.md": "宿主、Desktop虚拟机与容器配额分别盘点；磁盘、GPU与责任人未决。",
        "02-architecture/technical-baseline.md": "1.1-py310-cpu研发执行基线，区别于正式生产冻结和全部业务实现。",
        "02-architecture/technology-options.md": "12个技术域的替代方案、研发执行选择、实测和扩展边界。",
        "02-architecture/compatibility-matrix.md": "实际锁定组合、安装/构建/运行兼容证据及升级路径。",
        "02-architecture/licenses.md": "包/镜像/FFmpeg/Desktop与权重的许可盘点、审核缺口和再分发要求。",
        "02-architecture/security-baseline.md": "研发鉴权、秘密、输入、日志和网络措施；正式身份/案件/审计等差距。",
        "02-architecture/technical-validation-report.md": "各真实检查结果、证据路径、范围和未测事项。",
        "02-architecture/technical-baseline-change-control.md": "开发快照、正式冻结、ADR/锁/迁移变更和恢复规则。",
        "02-architecture/stage-two-official-sources.md": "本轮官方兼容、机制与许可来源；网页不替代部署实测。",
        "02-architecture/non-functional-requirements.md": "引用原非功能需求源并登记实测口径，不另造正式指标。",
        "03-development/ci-cd.md": "本机21及托管25门禁保留为历史；当前扩展检查数量、源码和制品以最新报告为准，非生产发布。",
        "03-development/contract-generation.md": "两份OpenAPI及事件/工作流Schema生成4份TS类型；唯一来源包装、版本信封与旧消息兼容桥接。",
        "03-development/stage-two-readiness.md": "23步实际开发状态和未完成的正式条件。",
        "03-development/stage-two-deliverables.json": "逐步机器对照；保留计划并区分开发验证与正式完成。",
        "10-deployment/development-runbook.md": "真实启动、复建、SSH页面访问、令牌、端口、卷、停止与排查。",
        "03-api/poc-api.md": "已实现PoC入口和73操作正式契约的区别，鉴权/错误与合成模型范围。",
        "04-database/poc-database.md": "独立开发5表含账本/审计、逐字段来源、outbox与旧租约拒绝；区别于62表业务字典/SQL。",
        "00-project/review-package/technical-baseline-review.md": "实际技术评审输入与待正式确认事项，不能自动充当批准。",
        "00-project/validation/environment-inventory.json": "实际宿主/引擎/服务版本、上限和时点快照；不是峰值或独占配额。",
        "00-project/validation/ci-all-report.json": "最近完整门禁逐命令状态、耗时及环境；托管与源码身份按报告实际字段读取。",
        "00-project/validation/ci-report.json": "最近一次正常CI入口执行报告；详细阶段与范围须核对。",
        "00-project/validation/ci-failure-probe-report.json": "故意插入失败后的真实非零门禁报告；FAIL为探针预期。",
        "00-project/validation/ci-failure-gate-report.json": "验证故意失败确实阻断构建/部署的判定，PASS不等于探针本身成功。",
        "00-project/validation/runtime-lock-report.json": "实际Python补丁与全部第三方包是否匹配精确锁。",
        "00-project/validation/lock-reproduction-report.json": "全新venv按精确锁安装后的依赖与导入结果。",
        "00-project/validation/generated-contract-report.json": "4份TS类型临时重新生成后的字节一致性，新增workflow来源包装仍需运行Schema检查。",
        "00-project/validation/poc-integration-report.json": "21项真实API/对象/SQL/队列/CPU/追踪/Problem结果检查，不是业务模型验收。",
        "00-project/validation/poc-resilience-report.json": "5项队列/过期租约/服务及版本对象重启/幂等冲突检查，服务恢复记录。",
        "00-project/validation/media-query-report.json": "6项合成媒体和微型SQL/向量/鉴权检查；不代表中文或大规模业务。",
        "00-project/validation/poc-browser-report.json": "Chromium实际上传与显示异步结果的测试记录。",
        "00-project/validation/poc-ui.png": "真实浏览器运行截图，保存前已清空研发令牌。",
        "00-project/validation/synthetic-training-experiment.json": "64随机张量120步真实CPU训练种子/损失；不当业务准确率。",
        "00-project/validation/python-components.json": "安装包版本与声明许可元信息；不是完整OS SBOM或正式许可审查。",
        "00-project/validation/python-audit-report.json": "pip-audit发现与跳过原因；CPU torch被跳过，不能声称全部无漏洞。",
        "00-project/validation/npm-sbom.cdx.json": "锁定前端依赖的CycloneDX物料清单；不涵盖OS镜像。",
        "00-project/validation/repository-secrets-report.json": "确切开发凭据值及已知秘密文件名检查，非完整DLP。",
    }
    entries.update(
        {
            "00-project/phase-readiness-register.md": "19项工作核查（第一阶段7/第二阶段12）：版式核验按本轮范围完成，18项仍有条件；技术补充与正式/真实交付分开。",
            "00-project/phase-readiness-register.json": "19项非签字工作机器清单，关联原24/23步与已有缺口；无虚构人员/完成/批准。",
            "00-project/requirement-processing-map.md": "36业务需求→来源任务/内部能力→结果身份及读取；逐条技术语义已复核，七条源未绑API保留，正式规则/实现另判。",
            "00-project/requirement-processing-map.json": "上述逐需求源指针/摘要、原始引用与候选流程；不改主追踪或新增可调用HTTP。",
            "00-project/requirement-flow-proposals.json": "12模块默认与36条逐需求复核覆盖：入口/读取/身份/缺口解释；不形成第二API结构源或运行实现证明。",
            "00-project/requirement-semantic-review.md": "36需求逐条复核原验收/任务/能力/入口/结果读取，解释错误映射修正和投影缺口；无正式业务批准。",
            "00-project/requirement-semantic-review.json": "36条技术语义结论、来源摘要、结果身份和明确未实现范围；主追踪原引用保持。",
            "00-project/execution-planning-inputs.json": "可编辑实际人员/有效工时/日历/剩余工时/证据/到位日输入；未知为null，部分证据与tasks/execution-status.json同源，不等于整任务完成。",
            "00-project/execution-schedule.md": "170任务原工时397—491人日、条件依赖计算及人力容量排期规则；实际日历输入不足未生成交付日期。",
            "00-project/execution-schedule.json": "逐任务工时/依赖/证据与未填写实际日期；源状态不改、完整验收未凭PoC归零。",
            "05-workflows/result-identity-and-projection.md": "案件/资产/task/run/result/cluster身份、应用投影及版本化读取规则，含簇成员/首发rank与insufficient零证据处置。",
            "09-testing/metric-protocols.md": "24项验收方法：单位/分母/公式/失败/未知/分层/源目标及真实条件；8组公式夹具不充当算法性能成绩。",
            "09-testing/metric-protocols.json": "24协议机器定义及待填样本/模型/版本/资源字段，approved_target为null、真实验收未执行。",
            "00-project/validation/stage-one-completion-report.json": "本轮5组图表来源/36语义/24协议8公式/170排期容量与循环/6个零证据正反契约案例；非正式验收。",
            "00-project/validation/acceptance-metric-reference-report.json": "8组自建公式计算证据：失败不删分母、未知单列和引用语义支持；不代表真实业务达标。",
            "00-project/validation/phase-readiness-report.json": "4项19缺口分类/36需求来源/派生漂移/快照语义检查，非业务或生产验收。",
            "00-project/validation/resource-readiness-snapshot.json": "2026-10-13只读宿主/研发卷容量及服务/GPU工具观测；非独占配额或GPU缺失/兼容证明。",
            "00-project/validation/repository-governance-snapshot.json": "实际GitHub主分支/规则集查询/Actions时点快照；不可查询不等于不存在，本轮未修改治理配置。",
            "03-api/system-interface-specification.md": "第二阶段整体接口入口：七类服务边界、73操作/102结构/34能力、详细阅读标准及13项开放缺口。",
            "03-api/detailed-interface-index.md": "73份逐操作说明及12模块导航；方法/路径、来源、实现边界和明细落点。",
            "03-api/data-structures.md": "102业务组件逐字段必填/可空/约束与完整源Schema的只读派生，不形成第二编辑源。",
            "03-api/inference-interfaces.md": "34能力逐请求/响应字段、路径、任务/数据及Schema摘要，只有M15合成CPU子范围已实测。",
            "03-api/common-interface-rules.md": "身份/权限、追踪、分页、幂等、ETag、异步、错误/Range和版本；未定配置保持待定。",
            "03-api/service-and-event-contracts.md": "服务/私有存储/DB调用及PoC事件字段和故障边界，全业务消息未完成。",
            "03-api/interface-catalog.json": "73操作、12模块和34能力的唯一来源摘要及详细路径/需求/测试引用，不当实施证明。",
            "03-api/interface-annotations.json": "73操作的工程用途/授权范围/下一步与实现状态解释；不独立定义Schema或授予权限。",
            "03-api/interface-gap-register.md": "13项接口设计/实施缺口、候选路径/方案/影响与关闭标准，候选路径不可调用。",
            "03-api/interface-gap-register.json": "上述开放缺口的机器索引；姓名未知/未批准，不改任务依赖。",
            "00-project/validation/interface-documentation-report.json": "6项明细覆盖/生成漂移/12模块/68能力分支/13缺口/源码实现边界检查，非全接口运行验收。",
            "03-development/migrations-and-events.md": "专用开发迁移/摘要、版本事件、原始追踪与旧租约拒绝；明确旧库接管及并发边界。",
            "03-development/stage-two-gap-register.md": "剩余正式条件、输入、责任角色与关闭标准；不补造姓名和批准。",
            "03-development/stage-two-gap-register.json": "上述条件机器索引，真实状态与负责人未知值保留。",
            "10-deployment/development-backup-restore.md": "维护时段开发冷备、原VersionId/DB/模型隔离恢复；凭据与生产RPO/RTO边界。",
            "00-project/validation/github-actions-report.json": "实际GitHub run、源码SHA、结论、制品摘要/门禁验真；配置和执行严格分开。",
            "00-project/validation/migration-fencing-report.json": "15项隔离迁移/权限/8数据库竞争者检查，非8Celery传输验收。",
            "00-project/validation/media-timestamp-report.json": "真实非零原点合成抽帧PTS和像素核验；未证明VFR业务链路。",
            "00-project/validation/development-recovery-report.json": "8项5表/原对象版本/权重恢复，已有私有凭据保留，非生产灾备。",
        }
    )
    entries.update(
        {
            "03-development/stage-two-completion-matrix.md": "第二阶段12类剩余工作的本轮补齐、实际证据、23步对应与仍需输入/实现；不将后续170业务任务强制当第二阶段全部完成。",
            "03-development/stage-two-completion-matrix.json": "12项阶段核查与补充/实际条件机器台账，正式完成false，真实负责人仍未知。",
            "03-development/stage-two-external-inputs.json": "16类实际资源/身份/数据/模型/GPU/生产/治理输入，未知为null，占位人员不当实际责任人。",
            "03-development/stage-two-implementation-plan.md": "资源、身份、13接口、DAG、模型媒体检索、证据灾备六批工作与实际前置/验收；170任务仍依各任务卡。",
            "04-database/authorization-isolation-prototype.md": "隔离RLS/案件单位/撤销/结果追加真实原型与可信中间件、共享角色和特权绕过边界；非62表部署。",
            "09-testing/stage-two-representative-validation.md": "21项隔离中文、11项VFR媒体、6组运维交付检查与物料采集的实际命令/断言和未测范围。",
            "10-deployment/stage-two-operations-and-offline-delivery.md": "99%容量处理、候选阈值、镜像OS物料、离线摘要/复建与治理；未声称扩容/全部制品/正式保护已完成。",
            "00-project/validation/stage-two-isolation-report.json": "新隔离PostgreSQL16的14权限历史+7中文词项GIN检查，既有数据库未修改，正式身份/业务表未联调。",
            "00-project/validation/stage-two-media-report.json": "11项8帧VFR/非零PTS/抽帧像素/音频/字幕/90度旋转原件摘要检查，不充当真实OCR/ASR或业务媒体验收。",
            "00-project/validation/stage-two-supplement-report.json": "6组材料覆盖/容量分级/离线正反摘要检查；正式和全部业务仍未完成。",
            "00-project/validation/stage-two-completion-report.json": "2026-10-12阶段工程总结历史快照，21门禁及当时run按原时点读；本轮新增6组检查另见stage-two-supplement-report。",
            "00-project/validation/stage-two-resource-report.json": "真实卷容量快照按候选阈值评估；最新状态须看采样时间及同步回执，历史CRITICAL不是当前结论。",
            "00-project/validation/stage-two-software-report.json": "7服务/5镜像的已安装OS物料采集、ID/RepoDigest/缺镜像覆盖；非漏洞扫描或许可批准。",
            "00-project/validation/image-sbom.spdx.json": "实际运行镜像与已安装OS包SPDX2.3清单；许可未知NOASSERTION，未托管二进制/Python/npm/权重另盘。",
        }
    )
    first_entries = {
        "00-project/execution-planning-scenario-inputs.json": "用户授权的10人占位工时/角色/起点/数据和GPU日期假设，后续替换；不填为实际人员或资源事实。",
        "00-project/execution-schedule-scenario.md": "170任务按占位容量生成日期与分期；明确超过源2027年6月末月，需调整投入/分工，未删功能或承诺实际日期。",
        "00-project/execution-schedule-scenario.json": "逐任务假设角色/日期/工时与源周期差异，actual_people_confirmed=false，实际输入表保持未确认。",
        "01-requirements/business-parameter-source-audit.md": "14类参数本地V1.4实际条款与V1.3交叉检查；候选可用率/RETURNED保留性质，未确认值不冒充批准。",
        "01-requirements/business-parameter-source-audit.json": "逐参数精确正文行/文本、来源候选与未定值，登记CLOSED在当前Task枚举未定义的差异。",
        "00-project/stage-one/remaining-work-completion.md": "第一阶段六类工程补充、阶段22—24接入及仍需真实输入；不把配置/Schema/工具当业务运行或正式冻结。",
        "00-project/source-authority-and-change-control.md": "唯一工程结构源、成对修订稿与历史身份、优先关系和变更/迁移/验证记录规则；正式依据仍需确认。",
        "00-project/source-authority-register.json": "10原件摘要/版本身份、2处V2/V1.0冲突及13类唯一结构源；实际负责人/正式依据未填。",
        "00-project/stage-one/review-resolution-inputs.json": "33问题可填写意见/责任人/依据/范围/例外/证据入口；不自动修改主Q或生成正式决定。",
        "01-requirements/business-parameter-contract.md": "14类业务参数的值/状态/依据/版本、RETURNED两路径与未知拒绝，适用规则不凭建议值确定。",
        "03-api/historical-result-reading.md": "7现有操作history成组参数、精确task/run/result与响应绑定头，404不回退最新；正式业务API尚未实现。",
        "05-workflows/workflow-contracts.md": "普通媒体/模型/投影/发布节点、7类事件、旧租约/取消/幂等与完整结果快照的单一Schema设计。",
        "05-workflows/dag-index.json": "36需求保守串行候选节点图、原任务引用和外部输入前提；不是170运行节点或已运行worker。",
        "06-algorithms/capability-projection-register.md": "34能力逐请求/响应/专用payload路径及全量原响应保存规则；公开专用投影实现单独登记。",
        "06-algorithms/capability-projection-register.json": "34结构摘要、输入字段/源任务、summary数组选择器与payload路径；不编造实体表或模型效果。",
        "09-testing/acceptance-execution-configuration.md": "24项实际样本/版本/资源/负载/目标/人员配置与NOT_EVALUABLE缺项，READY也不是验收成绩。",
        "09-testing/acceptance-execution-inputs.json": "24协议待填实际执行配置；正式目标和环境保持null，按Schema及适用指标检查。",
        "07-datasets/actual-input-inventory.md": "D01—D15实际元信息与计数口径，真实授权数量未知；64合成训练样本单列，不计正式数据。",
        "07-datasets/actual-input-inventory.json": "15规划数据卡/目录摘要、未知业务计数及真实合成证明；无真实数据扫描、导入或训练。",
        "00-project/validation/stage-one-controls-report.json": "8组来源、规则、RETURNED、36DAG/34模型快照、7历史读取/事件fencing、15数据卡/计数、24配置/33评审及170占位排期/14本地来源正反检查。",
        "00-project/validation/stage-one-input-preflight-report.json": "真实条件缺项报告：14参数/24验收/15数据/170排期/33评审；状态外部输入待填和NOT_READY，禁止冒称正式PASS。",
        "00-project/stage-one/README.md": "第一阶段24步总入口：本地来源、材料归属、候选状态和正式未冻结边界。",
        "00-project/stage-one/four-item-completion.md": "本轮图表/36语义/24验收协议/170排期四项总览及第二阶段接入；实际人员和日期不足明确保留。",
        "00-project/stage-one/visual-layout-audit.md": "9Word357页＋12页原型全页概览/关键页放大核验，8项阅读处置；保留原件，未声称全页逐像素交付审校。",
        "00-project/stage-one/visual-layout-audit.json": "10原件/PDF/369页PNG摘要、实际Office16.0只读渲染、页级几何/浏览范围和8项发现；CI不冒称重做人工看图。",
        "00-project/stage-one/steps-and-deliverables.md": "已在现有24步对应表更新实际材料/技术状态、操作、产物、待办及正式状态；不另建状态展示页，不与170业务任务完成率混同。",
        "00-project/stage-one/deliverables.json": "24步机器清单、源手册摘要、实际路径、状态和未确认事项；无虚构批准/负责人。",
        "00-project/stage-one/handoff.md": "第一阶段输入如何被第二阶段技术工程消费；两种基线与实际研发任务分别判断。",
        "00-project/stage-one/materials-manifest.json": "14份本地历史材料来源、原始字节摘要与身份；不混入正式业务原件清单。",
        "00-project/stage-one/history/README.md": "历史材料导航，限定旧61表/空服务器/旧工具环境的时点与适用范围。",
        "00-project/consistency-audit-report.md": "当前输入审查、已修复资料缺口和未决正式条件；不拿引用或结构通过代替业务批准。",
        "04-database/table-task-usage.md": "当前62表与任务引用阅读表，区分职责提案、需求引用与API引用，非实际代码使用证明。",
        "04-database/table-task-usage.json": "逐关系来源指针和摘要，完整覆盖62表；职责和实现批准明确为false。",
        "_converted/original/短视频与图片智能识别溯源系统功能模块界面原型图.md": "补回本地PPT逐页文字转换，来源摘要与原件一致；不代表视觉无损还原。",
        "guides/README.md": "三份手册与24/23步、170任务的关系及当前落点；手册是流程来源。",
        "00-project/validation/stage-one-validation-report.json": "12项来源/24步/62表/原件内容/章节映射/33项评审/候选摘要检查；不代替批准。",
        "00-project/stage-one/source-content-audit.md": "历史结构检查：9Word/495表/12PPT/92批注/200链接/2图/1700字段；158目录登记，当时视觉未验证，本轮补充另见visual-layout-audit。",
        "00-project/stage-one/source-content-audit.json": "可复算的原件/转换摘要、段落/表格/批注/链接/形状位置及逐任务字段证据；文字存在性不等于语义或版式一致。",
        "00-project/stage-one/source-section-map.md": "955处来源标题的准确原件位置与候选工程阅读/变更入口；未批准、未宣称全部实现。",
        "00-project/stage-one/source-section-map.json": "上述映射的原件摘要、准确位置、标题、实际目标路径和候选状态；可逐项核验。",
        "00-project/stage-one/review-register.json": "33项主Q的原文/指针/状态、七类主评审、已有任务引用与建议影响、所需输入和关闭条件；无代签。",
        "00-project/stage-one/input-baseline-candidate.md": "当前输入候选的选择范围、排除项、旧快照关系及正式冻结条件；NOT_FROZEN。",
        "00-project/stage-one/input-baseline-candidate.json": "当前第一阶段输入集合、大小与SHA-256，可复算且无批准编号；不当全仓同步凭据。",
        "00-project/review-package/README.md": "七类详细评审导航，覆盖33项主Q，区分台账明确引用和建议检查范围。",
    }
    imported = json.loads((ROOT / "docs/00-project/stage-one/materials-manifest.json").read_text(encoding="utf-8"))
    for item in imported["records"]:
        path = item["archived_path"].removeprefix("docs/")
        first_entries[path] = "第一阶段历史资料，按原始字节归档；旧计数、环境、未同步描述及候选决定不代表当前状态。"
    descriptions.update(first_entries)
    descriptions.update(entries)
    descriptions["00-project/task-execution-steps.txt"] = (
        f"{len(task_rows)}任务内{total_count}条执行事项逐条编号：{completed_count}条已验证子步骤、"
        f"{remaining_count}条剩余工作；保留C/R编号、具体证据及源依赖、测试和验收要求。"
    )
    for path in (ROOT / "docs/05-workflows/dags").glob("*.json"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "该需求的普通处理/模型/投影/发布候选节点图，模型输入与原任务引用保留；外部输入未落实，未运行。"
        )
    for path in (ROOT / "docs/07-datasets/data-cards").glob("*.json"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "该数据集实际来源/授权/计数/标签/质检/切分/负责人/到位日填写入口；未知null，不自动发布或冻结。"
        )
    for path in (ROOT / "docs/03-api/operations").glob("*.md"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "逐操作派生说明：参数/请求/响应/结构样例、授权/版本/异步下一步、字段映射及任务/测试计划；未实现与缺口明确。"
        )
    for path in (ROOT / "docs/03-api/modules").glob("*.md"):
        descriptions[path.relative_to(ROOT / "docs").as_posix()] = (
            "该模块三条来源业务需求、已有操作/任务及详细入口；直接API未绑定不等于需求删除或全部内部处理已完成。"
        )
    first_section = (
        "\n## 第一阶段实际材料\n\n第一阶段来源、做法与当前交付入口：\n\n| 文档 | 含义与严格判定要求 |\n| --- | --- |\n"
    )
    for path, description in first_entries.items():
        first_section += f"| [{path}](<{path}>) | {description} |\n"
    section = "\n## 第二阶段实际工程文档\n\n当前入口与适用要求：\n\n| 文档 | 含义与严格判定要求 |\n| --- | --- |\n"
    for path, description in entries.items():
        section += f"| [{path}](<{path}>) | {description} |\n"
    section += "\n源Word、170任务和正式业务契约保持；PoC的可运行/真实合成模型与正式业务/GPU/生产冻结分开。当前版本和完整运行依赖在仓库根config/versions.yaml、config/locks和frontend/package-lock.json，不由旧手册示例推定。\n"
    files = sorted(p for p in (ROOT / "docs").rglob("*") if p.is_file() and p != nav)
    index = f"\n## 当前文件完整索引\n\n以下按实际文件生成，共{len(files)}份；文件存在不代表正式批准。旧输入快照/历史报告按其时间与scope阅读。\n\n| 实际文件 | 含义与使用要求 |\n| --- | --- |\n"
    for path in files:
        relative = path.relative_to(ROOT / "docs").as_posix()
        description = descriptions.get(relative)
        if not description:
            if "architecture-decisions/TB-ADR-" in relative:
                description = (
                    "已执行的研发技术选择：替代方案、版本来源、实际证据、资源、未测范围与回退；非正式生产批准。"
                )
            elif path.suffix == ".md":
                title = next(
                    (
                        line.lstrip("# ")
                        for line in path.read_text(encoding="utf-8").splitlines()
                        if line.startswith("# ")
                    ),
                    path.stem,
                )
                description = "说明文档：" + title.replace("|", "\\|") + "；结合正文的状态、来源和适用范围阅读。"
            elif "validation/" in relative:
                description = "实际或历史验证记录；须核对时间、status、scope、环境和未执行项，不当正式验收。"
            else:
                description = "项目结构化资料或来源附件；按所在专题的来源、版本与质量要求使用。"
        index += f"| [{relative}](<{relative}>) | {description} |\n"
    nav.write_bytes((prefix.rstrip() + "\n" + first_section + section + index).encode("utf-8"))
    print(f"Indexed {len(files)} actual docs files")


if __name__ == "__main__":
    main()
