# 第二阶段23步交付与实际状态

第7/19/20步直接文件入口：[接口与数据库文件导航](stage-two-interface-database-navigation.md)、[整体接口](../03-api/README.md)、[业务数据库](../04-database/README.md)。第一阶段对应入口为[24步实际状态](../00-project/stage-one/stage-one-readiness.md)。

2026-10-12；1.1-py310-cpu。优先要求的环境清单→版本锁定→最小工程→CI已经在用户Miniforge py310实测；新增迁移/事件/租约/追踪/PTS/冷恢复已补齐。开发基线DEVELOPMENT_VALIDATED，正式业务/生产NOT_FROZEN；GitHub平台结论独立记录。不是全部23步正式批准或170任务全实现。

| 步骤 | 工作 | 已完成及剩余范围 | 开发状态 |
| --- | --- | --- | --- |
| 1 | 环境约束 | 已核验开发Linux/py310/Desktop、网络与挂载限制；生产边界待确认 | DEV_RECORDED |
| 2 | 资源与团队 | 宿主/虚拟机/容器配额已盘点；GPU、独占配额和人员待落实；170任务容量排期输入表已建立，实际人员/日期待输入；第一阶段工程控制补充已接入，正式/实际输入未填时保持待定 | DEV_RECORDED |
| 3 | 非功能指标 | 沿用需求源，明确实测口径；正式指标与并发未定；24项测量协议与8组公式夹具已补；第一阶段工程控制补充已接入，正式/实际输入未填时保持待定 | DEV_SCOPED |
| 4 | 候选架构 | 12域比较及本轮选择已记录 | DEV_DECIDED |
| 5 | 前端选型 | Vue/TS/Vite锁与真实构建/browser；组件库未定 | DEV_VALIDATED |
| 6 | 后端选型 | 用户指定py310、FastAPI工程/锁/配置/API已运行 | DEV_VALIDATED |
| 7 | 关系库与访问 | 补隔离RLS/追加历史/连接上下文实测；正式62表业务迁移与逐表隔离未部署 | DEV_VALIDATED |
| 8 | 对象存储 | S3版本/摘要/重启及物理冷恢复通过；WORM/生命周期/密钥灾备未验收 | DEV_VALIDATED |
| 9 | 缓存与队列 | Rabbit/Celery、确认/outbox/幂等、原子领取与旧租约写回拒绝通过；真实多worker故障仍待验收 | DEV_VALIDATED |
| 10 | 全文与向量 | 补4条自建中文字符词项及真实GIN查询/边界；大规模/语义/业务检索未验收 | DEV_PARTIAL |
| 11 | 传播关系存储 | 递归带环微型SQL通过；正式传播图业务待实现 | DEV_PARTIAL |
| 12 | 训练和实验 | 实际合成训练、权重/实验JSON；正式业务模型/实验平台待补 | DEV_VALIDATED_SYNTHETIC |
| 13 | 推理服务 | 独立CPU真实推理与M15契约通过；正式模型/GPU未测 | DEV_VALIDATED_SYNTHETIC |
| 14 | 视频媒体处理 | 补11项8帧VFR/非零PTS/音频/字幕/旋转像素坐标实测；真实媒体/OCR/ASR链路仍待 | DEV_PARTIAL |
| 15 | 安全认证审计 | 补跨单位/案件、ACL撤销后读写拒绝与追加历史实测；正式身份/特权防篡改仍待 | DEV_PARTIAL |
| 16 | 容器与编排 | 7服务/5卷/配额/健康/重启验证；生产平台未批准 | DEV_VALIDATED |
| 17 | 版本兼容许可 | 补5镜像/449物料记录SPDX盘点；运行旧web镜像目录缺失、漏洞/许可/生产版本仍待 | DEV_LOCKED |
| 18 | 规范和目录 | 真实目录、Ruff/TS检查、README与运行手册 | DEV_VALIDATED |
| 19 | 接口事件契约 | 53业务操作/83组件/34能力已详细化；4份类型沿用并检查，M24内部副本3项约束已同步；PoC实测范围保持，13项整体接口缺口开放；36需求语义及结果身份已复核，insufficient零证据冲突已修复；第一阶段工程控制补充已接入，正式/实际输入未填时保持待定 | DEV_VALIDATED_POC_OVERALL_CONTRACT_GAPS |
| 20 | 最小可运行工程 | 浏览器/对象/SQL/queue/worker/真实合成CPU结果已运行 | DEV_VALIDATED |
| 21 | CI质量门禁 | CI新增4道检查，共25道工程门禁；本轮托管运行和制品验真以最新GitHub报告为准，非生产发布 | LOCAL_CI_VALIDATED_HOSTED_RECORDED_SEPARATELY |
| 22 | 基线评审包 | 技术基线、14ADR和实际证据已形成；正式责任人/评审未签署 | REVIEW_PACKAGE_READY |
| 23 | 冻结与变更 | 开发源码快照与变更规则；正式生产NOT_FROZEN | NOT_FROZEN |

[技术基线](../02-architecture/technical-baseline.md)、[实际验证](../02-architecture/technical-validation-report.md)、[机器23步清单](stage-two-deliverables.json)与[剩余条件/关闭标准](stage-two-gap-register.md)一起使用。GitHub实际run、源码SHA及制品校验见[平台报告](../00-project/validation/github-actions-report.json)。

DEV_VALIDATED仅对本行开发范围有效。普通权限追加审计不是管理员不可篡改；8数据库竞争者不是8Celery传输验收；非零PTS不是VFR全视频；冷恢复不是生产灾备；合成模型不是业务模型。生产身份/审批/准入/容量/许可/责任人及冻结不自动关闭。保留12模块、170任务和≥3场景，生产Python迁移仍需重测。

## 审批之外的实际剩余工作

[统一19项清单](../00-project/phase-readiness-register.md)区分第一阶段7项与第二阶段12项，不将资料/规则/资源/实现/实测欠缺概括成只缺签字。[36需求内部处理与结果读取](../00-project/requirement-processing-map.md)已补候选映射，七条未直接绑API的需求保留；技术语义已复核，完整业务契约缺口和运行仍待对应任务核验。全部170业务任务不是第二阶段结束前一律完成的条件，关键设计/技术验证和后续业务/生产交付分别判断。

## 第一阶段补充接入第二阶段（2026-10-13）

[四项总览](../00-project/stage-one/four-item-completion.md)已加入项目导航。第2步补170任务人员容量输入，第3步补24测量协议，第19步补36需求技术语义与结果身份，并修复Relation/M29的insufficient零证据冲突，第21步加入5项补充检查。实际排期仍缺人员/投入/剩余工时/日历/到位日期，13接口缺口与真实业务验收继续按对应任务处理。

## 第一阶段工程控制补充（2026-10-13）

[第一阶段工程补充](../00-project/stage-one/remaining-work-completion.md)向第2/3/19/21步提供人员/验收、history选择、DAG/事件/快照和第四份共享类型。全部业务HTTP/worker未因此实现。

## 2026-10-13第二阶段补充

本轮具体状态以[23步机器清单](stage-two-deliverables.json)和[12项补齐/剩余对照](stage-two-completion-matrix.md)为准。权限隔离与中文词项21项、VFR音视频字幕坐标11项、运维离线摘要6组及7服务/5镜像OS物料采集已补入；CI工程门禁扩为25道。正式身份、62表业务/DAG/真实模型与媒体、独占资源、生产灾备/版本/治理仍未验收。

| 原23步 | 本輪变化与严格边界 |
| --- | --- |
| 7 关系库与访问 | 补隔离RLS/追加历史/连接上下文实测；正式62表业务迁移与逐表隔离未部署 |
| 10 全文与向量 | 补4条自建中文字符词项及真实GIN查询/边界；大规模/语义/业务检索未验收 |
| 14 视频媒体处理 | 补11项8帧VFR/非零PTS/音频/字幕/旋转像素坐标实测；真实媒体/OCR/ASR链路仍待 |
| 15 安全认证审计 | 补跨单位/案件、ACL撤销后读写拒绝与追加历史实测；正式身份/特权防篡改仍待 |
| 17 版本兼容许可 | 补5镜像/449物料记录SPDX盘点；运行旧web镜像目录缺失、漏洞/许可/生产版本仍待 |
| 21 CI质量门禁 | CI新增4道检查，共25道工程门禁；本轮托管运行和制品验真以最新GitHub报告为准，非生产发布 |

研发卷实际余量1.63GiB/df99%，已判断CRITICAL/NOT_READY；未扩容或清理其他项目。源码/报告同步与服务部署分别判定；本轮不重启已有服务、不修改已有业务数据。
