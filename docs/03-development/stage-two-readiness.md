# 第二阶段23步交付与实际状态

第7/19/20步直接文件入口：[接口与数据库文件导航](../02-architecture/technical-baseline.md#接口与数据库文件导航)、[整体接口](../03-api/README.md)、[业务数据库](../04-database/README.md)。第一阶段对应入口为[24步实际状态](../00-project/stage-one/steps-and-deliverables.md)。

2026-10-13更新；1.1-py310-cpu。优先要求的环境清单→版本锁定→最小工程→CI已经在用户Miniforge py310实测；现有迁移、事件、租约、追踪、PTS和冷恢复均有对应工程证据；文档、验证与实际待办统一记录在下表。开发基线DEVELOPMENT_VALIDATED，正式业务/生产NOT_FROZEN；GitHub平台结论独立记录。不是全部23步正式批准或170任务全实现。

## 技术完成程度与开发准入

基础开发可以开始，第一阶段工程输入与第二阶段最小工程/CI已具备；两阶段整体技术闭环和正式冻结仍未完成。实际资源、接口/身份/真实模型/数据及后续业务/生产验收不能省略。准入范围及逐任务检查直接维护在[23步机器清单](stage-two-deliverables.json)的development_entry，并呈现在[技术基线](../02-architecture/technical-baseline.md#技术完成程度与开发准入)。

Linux服务器Docker虚拟机研发数据卷最新快照仍df99%、约1.62GiB可用，容量判定CRITICAL。代码/文档/生成类型、现有框架完善和独立CI可推进；该卷上的大体积镜像构建、真实权重/素材导入和容量测试须先完成扩容/迁移并重新验证。

第一批按T001—T010任务卡逐项复核和完善现有框架/配置/追踪/错误/CI，再根据所选业务卡补本次必需接口和迁移/权限/事件子范围。不改任务源状态，不把PoC部分证据当全部任务验收。

| 步骤 | 工作 | 已完成及剩余范围 | 开发状态 |
| --- | --- | --- | --- |
| 1 | 环境约束 | 已核验开发Linux/py310/Desktop、网络与挂载限制；生产边界待确认；生产3.13主候选/3.12备选及3.10例外标准已登记，候选未安装/验证/批准 | DEV_RECORDED |
| 2 | 资源与团队 | 宿主/虚拟机/容器资源已盘点，170任务容量排期输入表及输入控制已建立；GPU、独占配额、实际人员和日期待落实 | DEV_RECORDED |
| 3 | 非功能指标 | 沿用需求源，24项测量协议、8组公式夹具及验收输入预检查已建立；正式指标、并发口径和真实测量条件待确认 | DEV_SCOPED |
| 4 | 候选架构 | 12域比较及本轮选择已记录 | DEV_DECIDED |
| 5 | 前端选型 | Vue/TS/Vite锁与真实构建/browser；组件库未定 | DEV_VALIDATED |
| 6 | 后端选型 | 用户指定py310、FastAPI工程/锁/配置/API已运行；生产3.13主候选/3.12备选及3.10例外标准已登记，候选未安装/验证/批准 | DEV_VALIDATED |
| 7 | 关系库与访问 | 代表性隔离RLS、追加历史及连接上下文实测通过；正式62表业务迁移与逐表隔离未部署 | DEV_VALIDATED |
| 8 | 对象存储 | S3版本/摘要/重启及物理冷恢复通过；WORM/生命周期/密钥灾备未验收 | DEV_VALIDATED |
| 9 | 缓存与队列 | Rabbit/Celery、确认/outbox/幂等、原子领取与旧租约写回拒绝通过；真实多worker故障仍待验收 | DEV_VALIDATED |
| 10 | 全文与向量 | 4条自建中文字符词项及GIN查询/边界实测通过；大规模、语义和业务检索未验收 | DEV_PARTIAL |
| 11 | 传播关系存储 | 递归带环微型SQL通过；正式传播图业务待实现 | DEV_PARTIAL |
| 12 | 训练和实验 | 实际合成训练、权重/实验JSON；正式业务模型/实验平台待补 | DEV_VALIDATED_SYNTHETIC |
| 13 | 推理服务 | 独立CPU真实推理与M15契约通过；正式模型/GPU未测 | DEV_VALIDATED_SYNTHETIC |
| 14 | 视频媒体处理 | 11项8帧VFR、非零PTS、音频、字幕及旋转像素坐标实测通过；真实媒体/OCR/ASR链路待实现和验收 | DEV_PARTIAL |
| 15 | 安全认证审计 | 代表性跨单位/案件、ACL撤销后读写拒绝与追加历史实测通过；正式身份与特权防篡改未验收 | DEV_PARTIAL |
| 16 | 容器与编排 | 7服务/5卷/配额/健康/重启验证；生产平台未批准 | DEV_VALIDATED |
| 17 | 版本兼容许可 | 服务器5镜像、449条SPDX物料记录已盘点；旧web镜像目录缺失、漏洞扫描、许可审查及生产版本仍待落实；生产3.13主候选/3.12备选及3.10例外标准已登记，候选未安装/验证/批准 | DEV_LOCKED |
| 18 | 规范和目录 | 真实目录、Ruff/TS检查、README与运行手册 | DEV_VALIDATED |
| 19 | 接口事件契约 | 53业务操作/83组件/34能力已详细化，4份生成类型与M24内部副本约束已校验；36需求技术语义、结果身份、history/DAG/事件/快照设计已复核，insufficient零证据冲突已修复；PoC实测范围保持，13项整体接口缺口和正式规则/真实业务联调仍开放 | DEV_VALIDATED_POC_OVERALL_CONTRACT_GAPS |
| 20 | 最小可运行工程 | 浏览器/对象/SQL/queue/worker/真实合成CPU结果已运行 | DEV_VALIDATED |
| 21 | CI质量门禁 | 25道CI工程门禁配置已完成；托管实际运行、源码SHA和制品验真见最新GitHub报告，未作生产发布 | LOCAL_CI_VALIDATED_HOSTED_RECORDED_SEPARATELY |
| 22 | 基线评审包 | 技术基线、14ADR和实际证据已形成；正式责任人/评审未签署 | REVIEW_PACKAGE_READY |
| 23 | 冻结与变更 | 开发源码快照与变更规则；正式生产NOT_FROZEN | NOT_FROZEN |

[技术基线](../02-architecture/technical-baseline.md)、[实际验证](../02-architecture/technical-validation-report.md)、[机器23步清单](stage-two-deliverables.json)与[剩余条件/关闭标准](stage-two-gap-register.md)一起使用。GitHub实际run、源码SHA及制品校验见[平台报告](../00-project/validation/github-actions-report.json)。

DEV_VALIDATED仅对本行开发范围有效。普通权限追加审计不是管理员不可篡改；8数据库竞争者不是8Celery传输验收；非零PTS不是VFR全视频；冷恢复不是生产灾备；合成模型不是业务模型。生产身份/审批/准入/容量/许可/责任人及冻结不自动关闭。保留12模块、170任务和≥3场景，生产Python迁移仍需重测。

## 审批之外的实际剩余工作

[统一19项清单](../00-project/phase-readiness-register.md)区分第一阶段7项与第二阶段12项，不将资料/规则/资源/实现/实测欠缺概括成只缺签字。[36需求内部处理与结果读取](../00-project/requirement-processing-map.md)已补候选映射，七条未直接绑API的需求保留；技术语义已复核，完整业务契约缺口和运行仍待对应任务核验。全部170业务任务不是第二阶段结束前一律完成的条件，关键设计/技术验证和后续业务/生产交付分别判断。
