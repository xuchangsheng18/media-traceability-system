# 原件图表与版式核验

2026-10-13。10份来源文件以原字节保存；9份Word共357页、原型12页，共369页/幻灯片。完成全部66张概览页浏览、全页文本边界/重叠/替换字符检查，并按下表放大检查关键页。核验者为Codex技术核验，未代替业务方审签。

原件由Word/PowerPoint16.0以只读方式导出PDF，未保存原件；PyMuPDF1.26.5按110dpi渲染。标准render_docx.py因本机缺少soffice.exe未能运行，已记录实际替代方式。PDF和逐页PNG摘要保存在[机器证据](visual-layout-audit.json)，渲染中间文件在本地工作区，未提交仓库。CI检查证据和来源摘要，不声称在Linux重新运行Word或再次人工看图。

**范围限制：**本轮是全页概览＋关键页放大＋几何检查，未宣称369页全部100%逐像素审校，也未宣称批注气泡视觉审查。先前[source-content-audit.md](source-content-audit.md)的视觉未验证描述是历史检查范围；本报告补充当前证据，未倒改历史。全页几何未发现页外文字、强文本重叠或替换字符；这不单独证明图形语义、所有箭头或所有字形无误。

| 来源 | 页数 | 本轮全页概览 | 放大核验页 |
| --- | --- | --- | --- |
| [面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.docx](<../../source/original/面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.docx>) | 24 | 1—24 | 6,8 |
| [短视频与图片智能识别溯源系统开发任务分解书V2.docx](<../../source/original/短视频与图片智能识别溯源系统开发任务分解书V2.docx>) | 57 | 1—57 | 未额外逐页放大 |
| [短视频与图片智能识别溯源系统算法研发与训练数据集建设说明 (1).docx](<../../source/original/短视频与图片智能识别溯源系统算法研发与训练数据集建设说明 (1).docx>) | 13 | 1—13 | 未额外逐页放大 |
| [短视频与图片智能识别溯源系统算法模型推荐清单.docx](<../../source/original/短视频与图片智能识别溯源系统算法模型推荐清单.docx>) | 9 | 1—9 | 未额外逐页放大 |
| [短视频与图片智能识别溯源系统功能模块界面原型图.pptx](<../../source/original/短视频与图片智能识别溯源系统功能模块界面原型图.pptx>) | 12 | 1—12 | 7,9,12 |
| [项目总体设计方案_技术修订版V1.4.docx](<../../source/revisions/项目总体设计方案_技术修订版V1.4.docx>) | 80 | 1—80 | 48,60 |
| [项目任务书_技术修订版V1.3.docx](<../../source/revisions/项目任务书_技术修订版V1.3.docx>) | 111 | 1—111 | 73,96 |
| [第一阶段：Codex整理开发输入材料分步提示词手册.docx](<../../guides/第一阶段：Codex整理开发输入材料分步提示词手册.docx>) | 28 | 1—28 | 未额外逐页放大 |
| [第二阶段系统技术基线确定与Codex协作实施指南.docx](<../../guides/第二阶段系统技术基线确定与Codex协作实施指南.docx>) | 8 | 1—8 | 未额外逐页放大 |
| [第二阶段系统技术基线分步提示词手册.docx](<../../guides/第二阶段系统技术基线分步提示词手册.docx>) | 27 | 1—27 | 未额外逐页放大 |

## 发现与仓库处置

| 编号/原件位置 | 核验发现 | 处置与准确读取入口 |
| --- | --- | --- |
| VL-01：短视频与图片智能识别溯源系统开发任务分解书V2.docx 第5,6,11,12,15,16,56,57页 | 历史V2任务表跨页时缺少重复任务标识/字段表头；附录表头与正文分离。 | 保留历史原件；开发使用当前170张独立Markdown任务卡，跨页信息不从截图拼接。任务书V1.3重点任务页73/96完整显示两张任务卡。<br>[README.md](<../../../tasks/README.md>)、[backlog.yaml](<../../../tasks/backlog.yaml>)、[项目任务书_技术修订版V1.3.docx](<../../source/revisions/项目任务书_技术修订版V1.3.docx>) |
| VL-02：第一阶段：Codex整理开发输入材料分步提示词手册.docx 第28页 | 历史第一阶段手册末页只有收尾段落。 | 属于历史分页可读性问题，未发现内容丢失；当前操作由24步Markdown交付表承担，不重写历史手册。<br>[steps-and-deliverables.md](<../../00-project/stage-one/steps-and-deliverables.md>) |
| VL-03：第二阶段系统技术基线分步提示词手册.docx 第27页 | 历史第二阶段手册末页只有收尾句。 | 保留原件；使用当前23步状态和运行手册开展工程工作。<br>[stage-two-readiness.md](<../../03-development/stage-two-readiness.md>)、[development-runbook.md](<../../10-deployment/development-runbook.md>) |
| VL-04：项目总体设计方案_技术修订版V1.4.docx 第48页 | MEDIA_SECURITY_REJECTED等长错误码在窄表格内换行，字符完整但不便人工抄录。 | 错误码从仓库结构源读取；详细接口与错误说明保持完整标识，禁止将视觉换行当标识字符。没有修改归档V1.4。<br>[error-codes.md](<../../03-api/error-codes.md>)、[openapi.yaml](<../../03-api/openapi.yaml>) |
| VL-05：项目任务书_技术修订版V1.3.docx 第73页 | T124长依赖列表中的T170显示为跨行T17/0，字符未丢失。 | 依赖以backlog.yaml及排期CSV的完整任务ID为准；源/执行依赖分别保留，不从截图重建。<br>[backlog.yaml](<../../../tasks/backlog.yaml>)、[execution-schedule.csv](<../../../tasks/execution-schedule.csv>)、[execution-schedule.md](<../../00-project/execution-schedule.md>) |
| VL-06：短视频与图片智能识别溯源系统功能模块界面原型图.pptx 第9页 | 传播原型关系线没有明确方向箭头；颜色和时间不能独自定义传播方向。 | 实现读取GraphEdge.from_node_id/to_node_id及证据/版本；确认与推测边分别解释，不能由图的左右位置构造事实。<br>[data-structures.md](<../../03-api/data-structures.md>)、[result-identity-and-projection.md](<../../05-workflows/result-identity-and-projection.md>)、[requirement-semantic-review.md](<../../00-project/requirement-semantic-review.md>) |
| VL-07：短视频与图片智能识别溯源系统功能模块界面原型图.pptx 第7,12页 | 覆盖率92%、GPU72%、成功率93.6%和示例版本属于界面原型示意数据。 | 不记为项目实际进度、模型成绩或资源实测；真实结果另按验收协议和实际报告判定。<br>[metric-protocols.md](<../../09-testing/metric-protocols.md>)、[resource-readiness-snapshot.json](<../../00-project/validation/resource-readiness-snapshot.json>) |
| VL-08：面向网络违法有害信息治理的短视频与图片智能识别溯源系统详细设计实现方案V2.docx 第6,8页 | 分层图和主流程图在渲染图中可读，主流程箭头和受控回流可辨；历史技术建议含Python3.11，图未展开全部取消/退回/版本状态。 | 图作架构和主流程概览；实际研发沿用用户py310锁，完整状态按当前状态机/事件契约读取，不由示意图补造完整转移。<br>[system-architecture.md](<../../02-architecture/system-architecture.md>)、[versions.yaml](<../../../config/versions.yaml>)、[task-state-machine.md](<../../05-workflows/task-state-machine.md>)、[service-and-event-contracts.md](<../../03-api/service-and-event-contracts.md>) |

处置采用归档保留＋当前可执行阅读入口，并没有将历史文档重新排版为新Word交付版。后续若需要正式Word出版件，应按正式版本另行修订并逐页进行交付版核验。
