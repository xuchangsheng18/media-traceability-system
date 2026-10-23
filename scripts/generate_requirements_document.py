"""Consolidate existing requirements into one readable document without changing their sources."""
import argparse
import hashlib
import json
import posixpath
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TARGET = "docs/01-requirements/functional-requirements.md"
DES = "docs/_converted/revision/项目总体设计方案_技术修订版V1.4.md"
OLD_DES = "docs/_converted/original/面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.md"
TASK = "docs/_converted/revision/项目任务书_技术修订版V1.3.md"
TRACE = "docs/00-project/requirement-traceability.yaml"
SOURCES = [DES, OLD_DES, TASK, TRACE, "docs/00-project/source-inventory.json",
           "docs/00-project/requirement-processing-map.json", "docs/00-project/requirement-semantic-review.json",
           "docs/01-requirements/engineering-requirements.yaml", "docs/01-requirements/business-rules.md",
           "docs/01-requirements/user-roles.md", "docs/01-requirements/non-functional-requirements.md",
           "docs/09-testing/test-scenarios.yaml", "docs/09-testing/task-test-scenarios.yaml",
           "docs/09-testing/metric-protocols.json", "docs/07-datasets/dataset-catalog.md",
           "docs/06-algorithms/model-catalog.yaml", "docs/03-api/operation-index.json",
           "docs/03-api/interface-gap-register.json", "docs/00-project/open-questions.md",
           "tasks/source-task-cards.json", "tasks/backlog.yaml", "config/versions.yaml",
           "scripts/generate_requirements_document.py"]
MODULES = [
    ("INGEST", "多源数据接入", "5.1", "数据管理员、案件核查人员"),
    ("RESOURCE", "数据治理与资源库", "5.2", "数据管理员、案件核查人员"),
    ("MEDIA", "媒体智能预处理", "5.3", "案件核查人员、算法管理员"),
    ("RISK", "多模态风险识别", "5.4", "案件核查人员、业务审核员"),
    ("FORENSIC", "篡改与深度伪造检测", "5.5", "案件核查人员、业务审核员"),
    ("IMGRET", "图片同源检索", "5.6", "案件核查人员、业务审核员"),
    ("VIDTRACE", "视频同源与片段溯源", "5.7", "案件核查人员、业务审核员"),
    ("ORIGIN", "首发候选分析", "5.8", "案件核查人员、业务审核员"),
    ("PROPAGATION", "传播路径分析", "5.9", "案件核查人员、业务审核员"),
    ("CLAIM", "谣言证据核查", "5.10", "案件核查人员、业务审核员"),
    ("REVIEW", "审核与证据管理", "5.11", "业务审核员、案件核查人员、审计员"),
    ("OPS", "综合管理与运维", "5.12", "系统管理员、算法管理员、数据管理员、审计员"),
]
# Source-grounded editorial steps. These are candidate engineering explanations, not new API definitions.
STEPS = {
    "FR-INGEST-001": ["登记来源类型、链接/平台/账号、授权依据、用途、有效期和责任范围。", "服务端核验当前身份、案件范围及来源用途授权，再创建获准导入批次。", "保留来源和导入状态版本、拒绝/到期原因及审计，授权到期后复核后续动作。"],
    "FR-INGEST-002": ["为声明素材创建upload_id，按片号和摘要记录分片。", "同片号同摘要重复提交不增计，内容冲突或他人会话访问拒绝。", "断点恢复读取已接收状态；合并仅进入校验阶段，通过后才能使用asset_id。"],
    "FR-INGEST-003": ["核对合并字节数、完整SHA-256和实际媒体类型。", "执行内容安全检查并保存检查结果；检查不可用时保留待检查或明确拒绝。", "仅将合格资产标为VALID；隔离/拒绝资产显示原因并阻止分析。"],
    "FR-RESOURCE-001": ["分别登记原始资产、媒体版本和派生对象的固定ObjectRef。", "保存父对象、转换参数及mapping_version；多源派生记录全部父关系。", "读取指定资产和历史版本，原件字节与来源记录不普通覆盖。"],
    "FR-RESOURCE-002": ["在当前有权范围内按字节摘要判断完全重复，来源和授权分别保留。", "将近重复送入复制检测及几何/时序验证，而非直接确认同源。", "分别展示完全重复、相似候选、部分复制与高可信整内容关系。"],
    "FR-RESOURCE-003": ["按单位/案件、用途、资源类型、来源和有效状态过滤资产。", "列表、详情、下载及每次Range读取均复核当前权限与到期/撤销。", "依获准生命周期管理各类数据，保留法律冻结/保留例外和访问审计。"],
    "FR-MEDIA-001": ["从原件读取容器、编码、流、尺寸、时长、时基和元数据。", "生成独立分析副本并登记变换，不覆盖原字节及原编码结构。", "保存源PTS/time_base、起点与缺失标记，提供可诊断解析结果。"],
    "FR-MEDIA-002": ["按间隔、镜头代表帧或事件策略抽取关键帧。", "分别提取有实际存在的音轨/字幕，登记对象版本、源时间和映射。", "将帧、音轨、字幕与原件区间对应；无音轨/字幕保留缺失而非伪造内容。"],
    "FR-MEDIA-003": ["对有需要且获准的图帧/音轨调用OCR与ASR能力。", "将文本框逆映射原件坐标，词句时间按原音轨和mapping_version对齐。", "在统一时间轴显示文本、片段与缺失/失败范围，不将空文本等同完成识别。"],
    "FR-RISK-001": ["固定获准标签、模型、前处理及策略版本。", "分别输出多标签分类、敏感目标和区域/时间候选，保留原始分数。", "将候选与证据及结果版本绑定，展示标签/模型/阈值来源。"],
    "FR-RISK-002": ["按原时间区间组织文字、语音、视觉、动作与音频事件。", "融合相应能力输出，记录对齐证据、缺失模态和冲突范围。", "呈现一致或矛盾的候选解释，不能将跨模态矛盾直接定性为违法。"],
    "FR-RISK-003": ["保存融合结果、原始分数、适用域校准值及证据。", "按有效policy_version/threshold_version判断人工分流；未确认规则不自动批准。", "展示风险证据、冲突/不确定性和转人工理由，计算完成与审核通过分别管理。"],
    "FR-FORENSIC-001": ["按取证输入规范读取原图及所需噪声/元数据线索。", "产生疑似区域和类型，掩码/框回映射到原件尺寸与方向。", "以固定对象版本保存掩码和解释，避免只给不可定位的真假分数。"],
    "FR-FORENSIC-002": ["对原视频进行空间、时间、深伪或音画同步的适用分析。", "定位原件半开时间区间及轨迹，保留缺失/失败能力和坐标变换。", "展示异常类型、片段和证据，不以未命中自动断言真实。"],
    "FR-FORENSIC-003": ["识别对应模型/任务/数据域的可靠性、校准和域外条件。", "将低可靠性、缺失信息及证据不足作为可见状态输出。", "按获准规则请求复核，不能以通用warnings替代全部可靠性字段的契约。"],
    "FR-IMGRET-001": ["选择有权查询资产及整图/局部/关键帧范围，固定模型与索引版本。", "执行摘要、复制向量、语义或局部特征等适用召回并进行授权过滤。", "通过search_id读取终态与实际候选，202受理不等同检索成功。"],
    "FR-IMGRET-002": ["针对召回候选提取并匹配局部特征。", "检验几何变换与内点证据，保存查询/来源区域及原件坐标映射。", "呈现可解释匹配点和验证类型，不能用召回相似度代替几何验证。"],
    "FR-IMGRET-003": ["结合复制与几何证据区分semantic_candidate、partial_copy/contains与full_copy。", "将相似非同源作为明确候选关系显示，禁止直接并入整内容簇。", "难负样本处理遵守独立集合与用途规则，不使用封存验收集调参。"],
    "FR-VIDTRACE-001": ["将查询关键帧及适用音频指纹带源时间组织为检索输入。", "按帧召回并按候选来源视频聚合，保留索引/模型和有权过滤。", "展示查询与来源区间及候选证据，索引管理状态不能充当视频检索结果。"],
    "FR-VIDTRACE-002": ["建立查询与候选来源的帧序列对齐。", "分别保存query_range、source_range、方向及speed_ratio，并校验映射。", "展示片段边界、未知段和校准解释；时间与像素定位可回查原件。"],
    "FR-VIDTRACE-003": ["按镜头或片段识别拼接边界并分别检索来源。", "为每段保存来源、时间/区域变换和覆盖解释，未知段明确标记。", "允许一个查询映射多个父来源，不把片段关系闭包当整内容同源簇。"],
    "FR-ORIGIN-001": ["以经验证的整内容复制关系建立候选簇。", "拒绝由语义相似、部分包含或多源拼接关系直接闭包合簇。", "保存簇成员、验证证据及版本，为簇内首发排序提供明确范围。"],
    "FR-ORIGIN-002": ["固定案件/内容簇、task/run/result、模型与策略版本。", "在获准观察范围内结合可核查时间和版本证据排序，未知发布时间单列。", "同一ranking_id事务保存0至3个真实候选；rank只属于该批次，不编造补足Top-3。"],
    "FR-ORIGIN-003": ["为当前排序快照分别组织支持、反对证据和观察覆盖。", "核对证据存在、同案件、用途及语义支持，保留时间可信度与不足原因。", "展示候选与未知/不足状态及历史快照，不输出确定性全网原创结论。"],
    "FR-PROPAGATION-001": ["登记内容、账号、平台等有权节点及显式来源关系。", "对隐式关系保留同源、时间方向和其他依据，区分事实边与推断边。", "存储关系版本、概率适用性和证据，推断不冒充显式转发事实。"],
    "FR-PROPAGATION-002": ["按节点/关系版本组织时间线与图视图。", "联动展示发布时间、发现时间、版本差异和关键节点，未知时间不虚造顺序。", "读取当前有权快照并保留查询范围、关系出处和历史版本。"],
    "FR-PROPAGATION-003": ["有权人员读取待复核的推断关系及原始证据。", "按当前版本提交确认/驳回/调整理由，并处理并发版本冲突。", "追加关系版本和审计；原推断及意见可追溯，当前接口缺口另列。"],
    "FR-CLAIM-001": ["从标题、正文及实际OCR/ASR片段抽取主张。", "组织主体、行为、时间、地点、结果等结构，并保留来源片段及模型版本。", "对缺失或无法抽取的槽位保留未知，不自动补成事实。"],
    "FR-CLAIM-002": ["在获准白名单范围检索证据，记录来源、时间和观察范围。", "分别判断支持、反驳、部分支持、无关或证据不足。", "将关系与实际证据绑定，引用存在不等同语义支持，来源不足不判事实为假。"],
    "FR-CLAIM-003": ["对有证据的主张生成候选摘要与逐句引用。", "分别核对引用可读取性和对句子含义的支持，隔离外部文本中的不可信指令。", "无有效依据的句子不进入正式报告，正式文本仍须对应复核和批准。"],
    "FR-REVIEW-001": ["按task/run/result和review_version读取原件、证据及当前待审对象。", "提交有理由和证据的确认/驳回/补证/重算，并按有效策略处理会审。", "补证追加结果版本，改变输入/模型/策略时新建运行；旧结果和意见保留。"],
    "FR-REVIEW-002": ["核验指定对象版本、摘要及当前seal用途授权。", "形成原件、来源页面、参数、模型、结果和审计组成的版本化清单。", "按获准只读/WORM与可信时间措施固化，更正追加版本；技术固化不自动认定证据效力。"],
    "FR-REVIEW-003": ["以指定已复核结果和固化证据版本创建报告草稿。", "按当前用途/范围/策略/对象版本执行报告审批，变更后重新核验批准。", "经受控下载导出并逐请求复核撤销/到期，保留导出人、用途、摘要和审计。"],
    "FR-OPS-001": ["按职责管理角色/范围及模型、标签、阈值、规则和策略版本。", "区分草案、批准与生效，算法管理角色不因此取得案件内容或业务审批权。", "记录变更、许可和模型包版本，未验证能力不计作正式发布。"],
    "FR-OPS-002": ["观察任务、服务、GPU/CPU、队列、存储和索引的实际状态。", "关联request_id及版本定位耗时、错误、缺失能力和容量告警。", "按实测设置背压/资源处理；无GPU实测不能显示GPU达标。"],
    "FR-OPS-003": ["按受控版本执行模型/服务灰度与回滚，明确索引兼容和生效范围。", "备份与恢复固定SQL、对象VersionId、结果、审计及所需密钥。", "在授权隔离目标演练恢复与对账，按正式RPO/RTO验收；开发冷备不等同生产灾备。"],
}
NFR_EVIDENCE = {
    "NFR-SEC-001": ("PoC Bearer拒绝与新隔离库RLS/ACL撤销有代表性证据。", "正式身份、完整案件/单位授权及62表逐表部署仍待。", ["poc-integration-report.json", "stage-two-isolation-report.json"]),
    "NFR-AVAIL-001": ("outbox、原子领取、旧租约拒绝及开发恢复已验证。", "全业务DAG、真实多worker消息故障/取消/长任务续租待实现和验收。", ["migration-fencing-report.json", "poc-resilience-report.json"]),
    "NFR-COMPAT-001": ("4份生成类型漂移、PoC事件及M15结果身份有检查。", "34能力的真实后端、旧版本迁移和生产Python候选兼容未全部验证。", ["generated-contract-report.json", "poc-integration-report.json"]),
    "NFR-AUDIT-001": ("请求追踪、安全Problem和普通应用追加审计已验证。", "正式审批审计、特权防篡改、WORM/可信时间尚待。", ["migration-fencing-report.json", "repository-secrets-report.json"]),
    "NFR-MAINTAIN-001": ("历史py310托管门禁及失败阻断保留实际run/制品；新py311迁移CI仍待新精确head验证，不继承历史通过。", "生产版本新锁/新环境及受控制品治理另验，不能转记其他Python PASS。", ["github-actions-report.json", "ci-failure-gate-report.json"]),
    "NFR-DATA-001": ("合成元信息、父组计数与泄漏边界有控制检查。", "真实用途授权、样本质检和独立封存清单未落实，未据此训练业务模型。", ["stage-one-controls-report.json"]),
    "NFR-AI-001": ("合成CPU训练/推理和8组验收公式夹具有证据。", "正式业务模型/校准、授权盲测及批准目标未验收。", ["synthetic-training-experiment.json", "acceptance-metric-reference-report.json"]),
    "NFR-PERF-001": ("微型SQL/检索、代表性媒体与竞争边界已执行。", "20/100性质与混合负载/大索引、正式时延吞吐和项目配额未验收。", ["media-query-report.json", "stage-two-media-report.json"]),
    "NFR-DEPLOY-001": ("已盘点Linux/VM/容器，旧py310锁与7服务保留历史证据，新py311迁移另验。", "容量按当前快照判定；生产节点/准入、GPU和3.12/3.13候选待验证。", ["environment-inventory.json", "resource-readiness-snapshot.json"]),
    "NFR-AVAIL-002": ("开发5表、对象固定版本/摘要及权重冷恢复有代表性证据。", "生产异机PITR/WAL、密钥恢复及正式RPO/RTO/保留期待落实。", ["development-recovery-report.json"]),
}


def read(path):
    content = (ROOT / path).read_text(encoding="utf-8")
    return json.loads(content) if path.endswith(".json") else yaml.safe_load(content)


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def link(path, label=None, anchor=""):
    assert (ROOT / path).exists(), path
    target = posixpath.relpath(path, posixpath.dirname(TARGET))
    return f"[{label or path.rsplit('/', 1)[-1]}](<{target}{anchor}>)"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def table(headers, rows):
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "".join(
        "| " + " | ".join(cell(value) for value in row) + " |\n" for row in rows) + "\n"


def markdown_rows(path, prefix=None):
    rows = []
    for line in text(path).splitlines():
        if line.startswith("| ") and not line.startswith("| ---"):
            columns = [column.strip() for column in line.strip().strip("|").split("|")]
            if prefix is None or columns[0].startswith(prefix):
                rows.append(columns)
    return rows


def source_module(clause, title):
    header = f"### {clause} {title}\n"
    block = text(OLD_DES).split(header, 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
    return [line.strip() for line in block.splitlines() if line.strip()]


def build():
    trace = read(TRACE)["requirements"]
    functional = [item for item in trace if item["requirement_id"].startswith("FR-")]
    engineering = read("docs/01-requirements/engineering-requirements.yaml")["requirements"]
    nfr = [item for item in trace if item["requirement_id"].startswith("NFR-")]
    cards = read("tasks/source-task-cards.json")
    backlog = {item["id"]: item for item in read("tasks/backlog.yaml")["tasks"]}
    flows = {item["requirement_id"]: item for item in read("docs/00-project/requirement-processing-map.json")["records"]}
    reviews = {item["requirement_id"]: item for item in read("docs/00-project/requirement-semantic-review.json")["records"]}
    cases = {item["id"]: item for item in read("docs/09-testing/test-scenarios.yaml")["scenarios"]}
    task_cases = {item["id"]: item for item in read("docs/09-testing/task-test-scenarios.yaml")["scenarios"]}
    operations = {item["id"]: item for item in read("docs/03-api/operation-index.json")}
    models = read("docs/06-algorithms/model-catalog.yaml")["models"]
    metrics = read("docs/09-testing/metric-protocols.json")["metrics"]
    gaps = read("docs/03-api/interface-gap-register.json")["items"]
    roles = markdown_rows("docs/01-requirements/user-roles.md")[1:]
    rules = markdown_rows("docs/01-requirements/business-rules.md", "BR-")
    questions = markdown_rows("docs/00-project/open-questions.md", "Q-")
    datasets = markdown_rows("docs/07-datasets/dataset-catalog.md", "D")
    nfr_rows = {row[0]: row for row in markdown_rows("docs/01-requirements/non-functional-requirements.md", "NFR-")}
    assert len(trace) == 216 and len(functional) == len(STEPS) == len(flows) == len(reviews) == 36
    assert len(engineering) == len(cards) == len(backlog) == 170
    assert len(nfr) == len(NFR_EVIDENCE) == len(nfr_rows) == 10
    assert len(models) == 34 and len(datasets) == 15 and len(metrics) == 24
    assert len(rules) == 16 and len(questions) == 33 and len(cases) == 72 and len(gaps) == 13
    assert len(roles) == 6 and len(task_cases) == 340
    assert {item["requirement_id"] for item in functional} == set(STEPS) == set(flows) == set(reviews)
    assert {item["source_task_id"] for item in engineering} == set(cards) == set(backlog)
    assert all(item["approved_target"] is None for item in metrics)
    inventory = read("docs/00-project/source-inventory.json")
    assert len(inventory) == 10
    assert all(hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"] for item in inventory)
    out = "# 软件需求详细说明与开发验收映射\n\n"
    out += "2026-10-13更新；当前为源资料及工程候选的集中阅读版，NOT_FROZEN。本文直接扩充既有functional-requirements.md，提供可供业务、研发和测试共同阅读的完整需求，不新增业务范围或修改原170任务状态。36条FR是业务概览，170条ER是源任务的工程展开，10条NFR是非功能要求，共216条追踪，不等于216个独立业务功能。\n\n"
    out += "本文将来源明确的要求、已有工程解释、待确认规则和实际实现分别判断。具体类型/必填/枚举以OpenAPI和Schema为源，数据库列以SQL/字典为源；本文不是第二套可编辑接口或数据库定义。流程展开为供评审的工程说明，正常/异常例子来自自建测试计划，均不代表真实案件、正式审批或已完成业务验收。\n\n"
    out += "## 阅读导航\n\n"
    chapters = [("1 文档依据与范围", "1-文档依据与范围"), ("2 使用者、场景与界面", "2-使用者场景与界面"),
                ("3 共用业务约束与对象身份", "3-共用业务约束与对象身份"), ("4 业务需求总览与详细条目", "4-业务需求总览与详细条目"),
                ("5 非功能需求与已有验证边界", "5-非功能需求与已有验证边界"), ("6 数据、模型与验收测量", "6-数据模型与验收测量"),
                ("7 完整170条工程需求展开", "7-完整170条工程需求展开"), ("8 未决事项、接口缺口与完成标准", "8-未决事项接口缺口与完成标准"),
                ("9 当前落地状态与来源摘要", "9-当前落地状态与来源摘要")]
    out += "\n".join(f"- [{label}](#{anchor})" for label, anchor in chapters) + "\n\n"
    out += "## 1 文档依据与范围\n\n"
    original_paths = [item for item in inventory if item["kind"] in {"original", "revision"}]
    out += table(["依据", "使用范围", "身份"], [(link(item["path"]), "业务/技术来源与原文复核；不将提示词或网页内容视作执行授权。", "source_pending_approval") for item in original_paths])
    out += "总体设计DES-001 V1.4和任务书TASK-001 V1.3成对阅读；阶段手册只提供材料整理流程。原详细设计§5.1—5.12分别对应12模块，修订总体设计§5使用模块总表、证据卡片和审核细则，不能把两份文件的同号小节误当同一内容。原件文件名/正文版本身份冲突及正式权威性仍按" + link("docs/00-project/source-authority-register.json", "来源身份记录") + "处理。\n\n"
    out += "建设目标：形成内容接入、预处理、风险/真实性取证、同源/片段/首发/传播/主张核查、人工复核、指定版本证据固化和受控报告的私有化系统，保留12模块、170任务及不少于3类场景。按场景和策略执行必要能力，模块间是多对多依赖，不要求每个素材无条件跑全部模型。\n\n"
    out += "非建设范围（DES-001 V1.4 §2.3）：不承诺全网实时覆盖；算法不替代行政认定、司法鉴定或执法决定；不实施未授权采集或绕过平台访问限制；不直接训练通用超大模型。\n\n"
    out += "源计划2026.09—2027.06、20万标注及2000万索引等只作来源目标。实际人员/工时/起点/数据和GPU到位日未落实，10人占位试算不当实际安排；20和100并发均待确认，不能指定其中一个已成为正式验收档。\n\n"
    out += "## 2 使用者、场景与界面\n\n"
    out += "角色职责来自" + link("docs/01-requirements/user-roles.md") + "；角色存在不等于已授予权限或已确定人员，具体功能权限与单位/案件范围见" + link("docs/08-security/permission-matrix.md") + "。\n\n"
    out += table(["角色", "拟承担操作", "限制"], roles)
    out += "### 三类最低业务场景\n\n"
    out += table(["场景", "候选业务链路", "需验证的结果"], [
        ("事故灾害类谣言核查", "获准接入→预处理/OCR/ASR→主张与白名单证据关系→来源/片段/传播辅助→人工复核→报告", "主张逐句引用、来源时间与观察范围、证据不足/未知、人工版本和批准可查。"),
        ("违法有害视听内容识别", "获准接入→视觉/文字/音频/时序候选→风险融合与冲突→依有效规则转人工→证据/报告", "标签/模型/阈值版本、原件区域/时间定位、缺失模态、跨案件拒绝与复核依据。"),
        ("搬运篡改内容溯源", "获准接入→原件取证→图像/视频召回和几何/时序验证→片段映射/内容簇→首发候选/传播→人工复核", "相似/部分复制/整内容关系分开，查询和来源区间可回映射，Top-3真实候选与不足状态。"),
    ])
    out += "以上是源场景的候选展开，不是已完成三场景实测。每一场景须有本次用途授权的素材、固定版本、独立封存输入、正式指标与正反结果证据。\n\n"
    out += "### 全流程与页面交互\n\n```mermaid\nflowchart TD\n A[来源及用途授权] --> B[上传或导入与安全校验]\n B --> C[有效资产与独立任务运行]\n C --> D[原件保护及媒体预处理]\n D --> E[按场景执行风险 取证 同源 主张等能力]\n E --> F[版本化候选结果及证据卡片]\n F --> G[人工复核 补证或新运行重算]\n G --> H[指定版本证据固化与报告审批]\n H --> I[重新鉴权后的受控导出]\n G --> J[另经用途授权和质检的数据回流]\n```\n\n"
    out += "前端7类核心页面为导航归纳，12页原型不等于12模块逐页实现。来源DES §5.1/5.2：\n\n"
    out += table(["页面", "需要显示", "关键交互/限制"], [
        ("综合工作台", "任务/队列/告警/场景与授权域", "只展示有权范围；状态跳转可定位具体任务版本。"),
        ("任务创建", "来源/用途、上传进度、场景与策略", "校验未完成不能使用资产；来源/策略未知不可默认放行。"),
        ("任务详情", "原件播放器、统一时间轴、证据卡片、能力完成矩阵", "点击结果定位原件帧/区域；缺失、延期、取消与历史运行可区分。"),
        ("同源检索", "查询资产/区域、候选、匹配点/几何和区间对齐", "相似、部分复制、整内容同源分开；异步任务终态与无匹配可诊断。"),
        ("传播研判", "关系图、时间线、版本差异和节点证据", "推断边明确标识；人工调整追加版本，不把推断展示成事实。"),
        ("人工审核", "当前task/run/result、原件、证据、理由和策略", "版本冲突/退回/无审批资格有明确提示；二次确认不构成独立会审。"),
        ("证据与报告", "固定对象版本、清单摘要、批准用途和报告预览", "更正重新绑定版本和批准；导出及Range逐请求复核当前授权。"),
    ])
    out += "统一证据卡片至少显示结论类型、业务标签、模型原始/校准分数、阈值、帧/区域/时间、来源对象、模型/算法版本、生成时间、可靠性及人工状态；未知值与不适用值明确区分。字段唯一结构见" + link("docs/03-api/data-structures.md") + "及" + link("docs/05-workflows/result-identity-and-projection.md") + "，不在本页重新规定枚举。\n\n"
    out += "## 3 共用业务约束与对象身份\n\n"
    out += table(["对象/标识", "含义与必须保持的关系"], [
        ("source_id / 授权版本", "来源与用途记录；客户端声明不能替代当前有效授权核验。"),
        ("upload_id / asset_id", "前者是上传会话，后者是有效媒体资产；VALIDATING受理不能当有效资产。"),
        ("ObjectRef", "固定object_id、version_id与SHA-256；原件、分析副本、掩码/向量各自引用。"),
        ("case_id / org_id", "单位与案件作用域；UUID或对象存在不构成访问权。"),
        ("task_id / run_version / result_version", "任务、执行与结果快照分别绑定；重算不覆盖旧结果，旧批准不能自动继承。"),
        ("cluster_id / ranking_id / rank", "经整内容验证的簇与一次排序批次；rank在批次内1—3，0候选保存insufficient头表而不编造资产。"),
        ("mapping_version", "派生时间/坐标回到原件的变换版本；保留源PTS/time_base与半开区间。"),
        ("policy/review/report/evidence版本", "规则生效、复核意见、报告和证据固定版本分别管理；更正追加记录。"),
    ])
    out += "具体类型/必填/外键/投影由" + link("docs/03-api/openapi.yaml", "业务OpenAPI") + "、" + link("docs/04-database/data-dictionary.md", "62表数据字典") + "和" + link("docs/04-database/field-provenance.json", "逐字段来源") + "定义；首发批次规则见" + link("docs/04-database/first-source-ranking.md") + "。\n\n"
    out += table(["规则", "触发", "共用要求", "来源关联任务"], [(row[0] + " " + row[1], row[2], row[3], row[4]) for row in rules])
    out += "规则编号为工程整理，不代表获得业务批准。阈值、RETURNED适用模式、保留天数、双人审批范围及20/100性质等14类参数继续按" + link("docs/01-requirements/business-parameter-contract.md") + "和" + link("config/business-parameters.candidate.json") + "维护；未确认保持null并拒绝依赖其生效的正式动作。\n\n"
    out += "任务状态、审核状态、证据状态和审批对象状态分别管理。SUCCEEDED表示所选运行按策略完成，不等同人工通过或报告获批；FAILED/DEFERRED不能伪装成功。RETURNED补证与重算分别保留原运行追加结果或新建run，适用规则待确认时不自动流转。详情见" + link("docs/05-workflows/task-state-machine.md") + "、" + link("docs/05-workflows/review-state-machine.md") + "与" + link("docs/05-workflows/workflow-contracts.md") + "。\n\n"
    out += "## 4 业务需求总览与详细条目\n\n"
    out += "每条FR保持原编号、名称、源验收语句和主追踪关联。下文候选处理步骤与语义复核用于解释开发闭环，不变更主追踪；测试输入是自建例子，不规定生产文件大小或正式业务阈值。接口表只复用已声明operationId，13项缺口的拟补路径仍不可调用。\n\n"
    out += table(["需求", "名称", "源验收", "原关联任务"], [(f"[{item['requirement_id']}](#{item['requirement_id'].lower()})", item["name"], item["acceptance"], ", ".join(item["task_ids"])) for item in functional])
    for module, title, clause, actors in MODULES:
        subset = [item for item in functional if item["requirement_id"].startswith("FR-" + module + "-")]
        assert len(subset) == 3
        out += f"### {module} {title}\n\n"
        out += "原详细设计§" + clause + "明确的模块范围（来源评审稿，不是当前实现结果）：\n\n"
        out += "\n".join("- " + line for line in source_module(clause, title)) + "\n\n"
        for item in subset:
            identity = item["requirement_id"]
            flow, review = flows[identity], reviews[identity]
            assert review["source_acceptance"] == item["acceptance"] and flow["declared_task_ids"] == item["task_ids"]
            normal, exception = cases[identity.replace("FR-", "TC-") + "-N"], cases[identity.replace("FR-", "TC-") + "-E"]
            assert normal["requirement_ids"] == exception["requirement_ids"] == [identity]
            out += f"#### {identity}\n\n**{item['name']}**\n\n"
            out += "状态：工程候选；源验收及正式业务实现/验收未由本文补造完成。建议业务使用者：" + actors + "，实际权限需核验正式矩阵和案件范围。\n\n"
            out += "来源：原详细设计§" + clause + "；配套修订总体设计DES-001 V1.4 §5及下列任务的具体设计条款；TASK-001 V1.3同号任务。主追踪精确指针：`/requirements/" + str(trace.index(item)) + "`，见" + link(TRACE) + "。\n\n"
            out += "**输入、正常处理与输出**\n\n"
            out += "前置：核验当前身份与适用功能权限；涉及案件/来源时同时核验单位/案件范围和用途。涉及既有资产/对象时核验固定版本，涉及模型/规则/前处理时使用已登记版本；上传会话尚未通过校验时不要求已存在asset_id。管理配置不因此取得案件内容权限。无适用条件不能直接进入正式动作。\n\n"
            out += "候选执行步骤（从源范围及技术语义展开）：\n\n" + "\n".join(f"{number}. {value}" for number, value in enumerate(STEPS[identity], 1)) + "\n\n"
            out += table(["案例性质", "自建输入/故障", "期望行为", "测试ID与状态"], [
                ("正常设计案例", normal["input"], normal["expected"], normal["id"] + "；计划，非真实验收结果"),
                ("异常设计案例", exception["input"], exception["expected"], exception["id"] + "；计划，非真实验收结果"),
            ])
            out += "结果身份与读取范围：" + flow["result_identity_note"] + "。技术语义复核：" + flow["processing_and_reading_note"] + "\n\n"
            out += "**接口、持久化与内部能力关联**\n\n"
            declared = ", ".join(item["operation_ids"]) or "原主追踪未直接绑定HTTP操作；保留该需求，通过任务/内部节点继续核验。"
            out += "原主追踪operation_ids：" + declared + "。候选执行入口与结果读取分别列下表；配置/索引管理前置不能替代业务结果查询。\n\n"
            operation_rows = []
            for purpose, ids in [("候选入口/处理", flow["candidate_entry_operations"]), ("候选结果读取", flow["candidate_result_operations"])]:
                for operation_id in ids:
                    op = operations[operation_id]
                    operation_rows.append((purpose, operation_id, op["method"].upper() + " /api/v1" + op["path"], op["request"] or "按该操作参数/头部", op["response"] or "无JSON成功体/见操作定义", op["permission"]))
            out += table(["用途", "已有operationId", "候选方法/路径", "请求结构", "响应结构", "功能权限"], operation_rows) if operation_rows else "该需求未直接绑定候选HTTP入口，须核验内部节点及读取投影，不新增伪端点。\n\n"
            out += "完整字段与错误/版本规则统一读" + link("docs/03-api/detailed-interface-index.md", "逐操作说明") + "、" + link("docs/03-api/openapi.yaml") + "；路径存在不表示已运行。\n\n"
            out += "原主追踪候选表：" + (", ".join(item["table_names"]) or "未声明直接表关联；不能补造已有访问层。") + "。持久化/仅服务处理/公开投影分别按" + link("docs/04-database/api-field-mapping.md") + "核验，表关联不证明业务访问层已实现。\n\n"
            model_links = "、".join(link(f"schemas/model/{model}.request.schema.json", model + "请求") + "/" + link(f"schemas/model/{model}.response.schema.json", "响应") for model in item["model_ids"])
            out += "模型能力声明关联：" + (model_links or "没有直接模型绑定；普通媒体处理、授权、存储或审核不强行算作算法能力。") + "\n\n"
            out += "数据集声明关联：" + (", ".join(item["dataset_ids"]) or "无直接规划数据集绑定") + "；见" + link("docs/07-datasets/dataset-catalog.md") + "。这些是来源关联，不证明已获得数据/许可，也不要求本功能训练所有关联数据域。\n\n"
            out += "**规则、验收、异常与待确认**\n\n"
            proposed_rules = [row[0] for row in rules if set(re.findall(r"T\d{3}", row[4])) & set(item["task_ids"])]
            out += "源验收语句：**" + item["acceptance"] + "**。正式测量另按第6节协议与获准条件执行；上述N/E计划不能当已执行记录。\n\n"
            out += "原主追踪rule_ids：" + (", ".join(item["rule_ids"]) or "未直接绑定") + "；按任务交集建议复核" + (", ".join(proposed_rules) or "第3节共用约束") + "，此建议不写回主追踪或自动取得业务批准。\n\n"
            out += "权限与审计：按表中功能权限和当前单位/案件/用途核验；记录request_id、主体、对象/运行/结果版本、前后状态、拒绝原因和审计引用。模型输出的概率不赋予批准权；管理员角色不默认获得案件内容权限。\n\n"
            question_ids = sorted({question for task in item["task_ids"] for question in backlog[task]["blocking_questions"]})
            out += "当前关联缺口：" + (", ".join(flow["interface_gap_ids"]) or "未直接归入13项缺口，不等于已完成全部契约或实现。") + "；待核验Q事项：" + (", ".join(question_ids) or "按具体功能的正式规则/数据/资源条件核验。") + "\n\n"
            usecase_links = "、".join(link("docs/01-requirements/use-cases/" + usecase + ".md", usecase) for usecase in item["usecase_ids"])
            out += "相关工程需求：" + "、".join(f"[ER-{task}](#er-{task.lower()})" for task in item["task_ids"]) + "；业务用例见" + (usecase_links or "尚无直接用例绑定，须另行核验") + "。\n\n"
    out += "## 5 非功能需求与已有验证边界\n\n"
    out += "需求/统计定义沿用" + link("docs/01-requirements/non-functional-requirements.md") + "和主追踪；完整正式验收未执行不等于所有工程检查未开展。下表代表性证据只给出实际范围，最新run/源码SHA/原始结果在报告中读取。\n\n"
    out += table(["编号/要求", "原统计与验证条件", "已有工程证据范围", "仍需完成的正式/全业务条件"], [
        (item["requirement_id"] + " " + item["name"], nfr_rows[item["requirement_id"]][3], NFR_EVIDENCE[item["requirement_id"]][0] + "<br>" + "、".join(link("docs/00-project/validation/" + name) for name in NFR_EVIDENCE[item["requirement_id"]][2]), NFR_EVIDENCE[item["requirement_id"]][1]) for item in nfr])
    out += "## 6 数据、模型与验收测量\n\n"
    out += "### 15类规划数据与用途\n\n"
    out += table(["ID", "名称", "源规模建议", "规划/授权状态", "实际数量"], datasets)
    out += "五类资源包括公开基准、授权业务、可控增强、困难/对抗与封存验收。公开许可、业务用途、标签/真值、脱敏、父组切分与保留分别核验；增强/裁切/帧/向量不可隐式多计为独立原件。数据卡、实际数量和元信息清单见" + link("docs/07-datasets/actual-input-inventory.md") + "；封存验收集不参与训练、阈值、校准或难例挖掘。\n\n"
    out += "### 34能力的声明与边界\n\n"
    out += table(["ID/能力", "名称", "候选方向/训练", "输入路径/输出类型", "源任务/数据", "来源许可/业务运行状态"], [(item["id"] + " / " + item["capability"], item["name"], item["candidate"] + "；" + item["training"], item["input_kind"] + " / " + item["output_kind"], ", ".join(item["task_ids"]) + "；" + ", ".join(item["dataset_ids"]), item["license_status"] + " / " + item["runtime_status"]) for item in models])
    out += "34能力线不等于34个已训练模型或批准成果；包含几何、校准和压缩方法。版本、输入路径、许可和Schema以" + link("docs/06-algorithms/model-catalog.yaml") + "及" + link("docs/06-algorithms/model-contract.md") + "为源。当前M15采用真实合成CPU演示编码器，不是候选SSCD业务效果；其余真实模型/GPU不能由Schema或Mock通过替代。\n\n"
    out += "### 24项候选测量协议\n\n"
    out += "以下源目标均未自动成为批准目标；approved_target当前全部为null。数值保留来源单位和比较方式，比例不是法律概率，P95等需要完整计时范围与真实负载。\n\n"
    for metric in metrics:
        out += f"#### {metric['id']} {metric['name']}\n\n"
        target = (metric.get("source_comparison") or "") + str(metric["source_target"]) if metric["source_target"] is not None else "待确认/源存在多个候选，不能自行定值"
        if metric.get("source_target_candidates"):
            target += "；原文候选值：" + json.dumps(metric["source_target_candidates"], ensure_ascii=False)
        if metric.get("source_separate_index_target"):
            target += "；另有源索引目标" + str(metric["source_separate_index_target"])
        out += table(["项目", "详细要求"], [("源目标/出处", target + "；" + metric["source_clause"]),
                    ("统计单位与分母", metric["statistical_unit_and_denominator"]), ("公式/方法", metric["formula"]),
                    ("失败、未知与零值处理", metric["failure_unknown_zero_handling"]), ("必须分层", metric["required_strata"]),
                    ("正式目标/结果", "未批准；未在真实验收数据上执行，不能填写正式PASS")])
    out += "执行前提供协议/目标、用途授权和独立样本清单摘要、标签真值/分母、代码/模型/阈值/索引/映射版本、实际资源/负载、分组数量/重复/区间方案、逐样本失败日志与执行复核人。任一所需输入缺失只能记NOT_EXECUTED或NOT_EVALUABLE。源协议详情与8组公式夹具见" + link("docs/09-testing/metric-protocols.json") + "、" + link("docs/09-testing/metric-protocols.md") + "及" + link("docs/09-testing/acceptance-execution-configuration.md") + "。\n\n"
    out += "## 7 完整170条工程需求展开\n\n"
    out += "ER编号直接对应原T任务，不新增功能；源角色/工时与依赖原文保留，执行依赖候选分列，实际责任人/完成证据另填。全量工作范围和验收在本页展示，单任务执行仍以原卡及唯一契约为输入。源任务中的Python3.11等历史候选与当前已授权py311迁移执行、生产3.13/3.12待验证选择分别判断，见" + link("docs/02-architecture/architecture-decisions/TB-ADR-002-backend-stack.md") + "。\n\n"
    for requirement in engineering:
        task_id = requirement["source_task_id"]
        card, task = cards[task_id], backlog[task_id]
        fields = card["fields"]
        assert requirement["id"] == "ER-" + task_id and requirement["name"] == card["name"] == task["name"]
        assert requirement["scope"].strip() == fields["工作范围"].strip(), task_id + " scope"
        assert requirement["acceptance"].strip() == fields["验收标准"].strip(), task_id + " acceptance"
        assert all(test in task_cases or test in cases for test in task["test_refs"]), task_id + " tests"
        out += f"### ER-{task_id}\n\n**{requirement['name']}**；源候选任务，不因本页展示而完成。\n\n"
        out += table(["项", "源要求/执行说明"], [("来源设计", requirement["source_design"]), ("完整工作范围", requirement["scope"]),
                    ("源验收标准", requirement["acceptance"]), ("源测试要求", fields.get("测试要求", "按原任务适用测试要求核验")),
                    ("源角色/工时", task["source_role"] + "；" + task["source_effort"] + "；实际人员/投入未确认"),
                    ("源前置依赖", task["source_dependencies"]), ("执行依赖候选", ", ".join(task["execution_dependencies_candidate"]) or "无；以已核验输入为准"),
                    ("追踪/测试/未决", ", ".join(task["requirement_ids"]) + "；" + ", ".join(task["test_refs"]) + "；" + ", ".join(task["blocking_questions"]))])
        out += "单任务输入、预期产物及操作卡：" + link(task["doc_file"], task_id) + "。资料、PoC部分证据与完整任务验收分别登记，不以建议工时承诺真实完成日。\n\n"
    out += "## 8 未决事项、接口缺口与完成标准\n\n"
    out += "### 33项源Q记录\n\n"
    out += table(["事项", "需确认内容", "来源状态", "处理原则"], questions)
    out += "来源状态未因文档汇总改变；项目范围、GitHub与当前已授权py311迁移等已收到的用户工程选择可作为相应执行依据，但不替代正式业务规则、人员授权或验收批准。\n\n"
    out += "### 13项已登记接口缺口\n\n"
    out += "完整拟补方案在" + link("docs/03-api/interface-gap-register.md") + "；候选路径未加入OpenAPI、不可调用。表内具体缺口与阶段18项实际条件有交叉，不能相加计算完成率。\n\n"
    out += table(["缺口", "主题", "严格状态"], [(item["id"], item.get("title", item.get("name", "见源登记")), "OPEN；候选路径不可调用；关闭须唯一契约/实现和对应证据") for item in gaps])
    out += "### 文档、开发与验收分别完成\n\n"
    out += "1. 文档层：36/170/10覆盖、原件摘要、任务/契约/表/能力/测试引用与生成文档同源无漂移；不以引用完整替代正式语义确认。\n2. 对应任务开发层：本次所需输入、契约/迁移/权限/事件先明确，再记录真实实现、正反测试与结果；不能用资料通过代替代码实现。\n3. 算法与场景层：按批准协议、授权封存样本、真实模型/硬件/负载和不少于3场景执行，保存逐项原始结果；失败和未知不能从分母隐去。\n4. 冻结/生产层：有效责任人与决定、实际资源/安全/软件准入、灾备/密钥和受控制品落实后再冻结，未满足仍NOT_FROZEN。\n\n"
    out += "## 9 当前落地状态与来源摘要\n\n"
    out += "历史py310 CPU最小工程与托管门禁已有其时点证据；当前已授权py311迁移，托管门禁仍待新精确head验证，不继承旧run通过；7服务工程、5表PoC、M15合成CPU及代表性RLS/媒体/恢复范围见" + link("docs/00-project/repository-readiness.md") + "和" + link("docs/02-architecture/technical-validation-report.md") + "。本页不将73业务操作、62表访问迁移、全DAG、34真实能力或三场景验收写成已完成。\n\n"
    out += "生产Python条件已登记，3.13/3.12仍未验证候选，3.10例外未批准；旧研发环境与锁保留回退，活动研发已授权迁移至Python3.11.17。真实数据、规则、GPU与容量/配额仍需落实。阶段状态见" + link("docs/00-project/stage-one/steps-and-deliverables.md", "第一阶段24步") + "、" + link("docs/03-development/stage-two-readiness.md", "第二阶段23步") + "和" + link("docs/00-project/remaining-work-navigation.md", "实际剩余条件") + "。\n\n"
    out += "### 本集中阅读版的输入摘要\n\n"
    out += "由既有来源和工程展开生成，维护输入后重新生成本文；输入摘要和--check发现内容漂移。生成器不修改原件、主追踪、任务状态、接口/SQL/Schema或业务参数。\n\n"
    out += table(["输入来源", "SHA-256"], [(link(path), hashlib.sha256((ROOT / path).read_bytes()).hexdigest()) for path in SOURCES])
    summary = {"business_modules": 12, "functional_requirements": 36, "engineering_requirements": 170,
               "non_functional_requirements": 10, "trace_records": 216, "business_rules": 16,
               "business_case_plans": 72, "task_case_plans": 340, "model_capabilities": 34, "dataset_categories": 15,
               "metric_protocols": 24, "open_questions": 33, "interface_gaps": 13,
               "document": TARGET, "formal_frozen": False, "full_business_completion_asserted": False}
    return out.rstrip() + "\n", summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content, summary = build()
    raw = content.encode("utf-8")
    if args.check:
        assert (ROOT / TARGET).read_bytes() == raw, "CONSOLIDATED_REQUIREMENTS_DOCUMENT_DRIFT"
    else:
        (ROOT / TARGET).write_bytes(raw)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "generate", **summary}))


if __name__ == "__main__":
    main()
