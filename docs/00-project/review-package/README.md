# 第一阶段评审材料导航

七类清单覆盖33项主Q，每项仅设一个主评审入口；可跨专题会审。来源文字、状态和指针、已有任务引用、建议影响范围、所需输入和关闭条件见[机器登记](../stage-one/review-register.json)。当前所有Q仍待确认，正式决定列表为空。

| 问题 | 主评审 | 台账明确任务引用数 |
| --- | --- | --- |
| Q-01 公安内网允许部署哪些基础软件 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-02 是否必须使用国产服务器、操作系统和数据库 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-03 现有平台是否有Kubernetes及运维能力（不自动要求采用） | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-04 是否允许引入  Neo4j 、 Milvus 、 OpenSearch  等组件 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-05 是否需要与公安统一身份认证对接 | [permission-review.md](<permission-review.md>) | 0 |
| Q-06 是否允许访问互联网和拉取  Docker  镜像 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-07 是否必须离线部署 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-08 是否采用  Kubernetes  正式部署 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-09 是否部署  Neo4j （一期是否用  PostgreSQL  替代） | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-10 OCR  与  ASR  的最终模型选择 | [algorithm-review.md](<algorithm-review.md>) | 0 |
| Q-11 GPU来源、驱动及CUDA/PyTorch/推理框架兼容组合 | [algorithm-review.md](<algorithm-review.md>) | 0 |
| Q-12 前端使用  Ant Design Vue  还是  Element Plus | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-13 模型正式验收指标的定值 | [acceptance-review.md](<acceptance-review.md>) | 3 |
| Q-14 20及100并发的正式性质、统计口径与资源安排 | [acceptance-review.md](<acceptance-review.md>) | 3 |
| Q-15 现有主机项目配额、GPU来源及最终部署节点 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-16 安全等级（等保级别） | [permission-review.md](<permission-review.md>) | 0 |
| Q-17 是否允许访问外部网络平台 | [dataset-review.md](<dataset-review.md>) | 0 |
| Q-18 风险定性标准 | [business-rule-review.md](<business-rule-review.md>) | 0 |
| Q-19 证据保存期限 | [dataset-review.md](<dataset-review.md>) | 0 |
| Q-20 双人审批事项范围 | [permission-review.md](<permission-review.md>) | 0 |
| Q-21 全部12模块、≥3场景的阶段边界；用户已确认保留全范围 | [scope-review.md](<scope-review.md>) | 0 |
| Q-22 测试条件是否按  §11.1  建议基线冻结 | [acceptance-review.md](<acceptance-review.md>) | 0 |
| Q-23 详细设计与任务书文件名V2、正文V1.0差异 | [scope-review.md](<scope-review.md>) | 0 |
| Q-24 任务状态机退回路径（ RETURNED →  何状态） | [business-rule-review.md](<business-rule-review.md>) | 0 |
| Q-25 受托方在环境数据边界中的权限档位 | [permission-review.md](<permission-review.md>) | 0 |
| Q-26 取证规范（可信时间源、固化标准）适用性 | [permission-review.md](<permission-review.md>) | 0 |
| Q-27 代码仓库顶层目录命名与划分方式 | [scope-review.md](<scope-review.md>) | 0 |
| Q-28 当前172.16.58.179属于研发/测试/试运行还是最终生产；网络、离线及数据准入 \| 项目负责人、安全与运维；真实业务接入/最终拓扑前 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-29 96核/192线程、内存与存储的项目配额；A100/4×4090来源 \| 资源管理员、算法负责人；资源配置及GPU实施前 | [algorithm-review.md](<algorithm-review.md>) | 0 |
| Q-30 Python 3.11候选与主机3.12.3适配；Node.js/FFmpeg位置；镜像与版本许可 \| 技术与算法负责人；对应组件开发和PoC前 | [open-questions-review.md](<open-questions-review.md>) | 0 |
| Q-31 各类数据保留、备份域、RPO/RTO、恢复权限与演练 \| 数据、安全与运维；真实数据导入及发布前 | [dataset-review.md](<dataset-review.md>) | 0 |
| Q-32 人工复核阈值、首发未知、报告审批、回流和样本计数规则 \| 业务、数据与测试负责人；正式结论及数据集发布前 | [business-rule-review.md](<business-rule-review.md>) | 0 |
| Q-33 剩余实际进度、人力、样本及GPU日期与37周工作量重排 \| 项目负责人及各工作流负责人；阶段交付计划冻结前 | [scope-review.md](<scope-review.md>) | 170 |

技术基线的开发实测另见[technical-baseline-review.md](technical-baseline-review.md)；其通过不替代业务审批。用户已确认全范围、py310及实际私有GitHub选择，执行应用见[应用记录](../review-decision-application-report.md)，并不自动关闭涉及正式准入的问题。
