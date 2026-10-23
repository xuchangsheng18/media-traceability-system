# N01嵌套许可使用范围与软件准入复核

2026-10-18（北京时间）；当前为Linux / Miniforge py310 / CPU团队内部研发。**N01仍为IN_PROGRESS_BLOCKED_ADMISSION，未批准安装、迁移或切换。** Node、age和SeaweedFS三项原生制品预选已确认，不再作为待确认事项；Python候选继续暂缓。

[当前十类软件台账](../00-project/validation/native-n01-round10/software-admission-register.json) · [31项特殊许可逐项依据](../00-project/validation/native-n01-round10/special-jar-use-scope-register.json) · [5个合并JAR及40坐标](../00-project/validation/native-n01-round10/nested-coordinate-declarations.json) · [原生状态](native-linux-execution-status.json) · [分步任务导航](../../tasks/README.md)

## 本轮实际完成的内容

1. 核验上轮最终回执提交`592c2c21a5b2ccb871786f9dafea46542f294405`的[CI39107719597](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39107719597)：成功，32项门禁及6份关键报告通过；333065字节制品SHA256为`4cbf867e879940e18354242faf9e415119e30000f806b5d81b055b536083b8f3`。后续提交按各自CI判定。
2. 对5个含多组Maven坐标的JAR提取40个去重坐标，40个均取得自身或父POM许可声明。保存[原始POM与摘要](../00-project/validation/native-n01-round10/nested-pom-source-materials.json)。元数据坐标不是全部内含字节清单，不能据此宣称穷尽所有阴影组件或完成对应源码交付。
3. 31项已识别特殊许可JAR逐项关联精确归档摘要、原包正文或对应源码材料/文件头，并记录当前使用和后续转交条件。没有将POM中的多个许可名称自动改写为OR，也没有把“不启用某驱动”当成不必保留其许可。
4. 验证沿用的469份许可正文和884条绑定；两份AGPL关键词命中均来自GPLv3第13节兼容性条款，不是对应组件采用AGPL的证明。关键词筛查只用于定位，不能自动批准全部许可。
5. 补齐is-reference1.2.1构建工具的精确包、锁定SRI、package.json/README中的MIT声明、原作者元数据与标准条款引用。没有伪造上游缺失的独立LICENSE、版权年份或权利人。
6. Linux只读重验原有内部材料包：485个文件无差异，包摘要不变；本轮附件另存，不改写旧包。见[实际保留验证](../00-project/validation/native-n01-round10/material-retention-verification.json)。

## 当前使用与公开资料的边界

用户确认的是运行包目前仅供团队内部研发。**仓库源码和资料已经公开，不能把它们描述为未对外公开。** 自有成果的Apache-2.0不替代第三方许可正文、POM和源代码片段自身的条款、版权及例外；公开资料保留对应上游来源与原声明。

本轮观察到当前Git树没有所列JAR/wheel/DEB/Conda/运行归档后缀文件；本次核验的CI包含92个JSON/PNG成员，GitHub Releases为0。见[实际观察范围](../00-project/validation/native-n01-round10/publication-use-boundary.json)。这不是所有Git历史、旧CI、其他镜像仓库或所有可能二进制格式的空集证明。

“内部团队”不自动等同许可证定义的同一法律主体。发生实际运行包复制、委托构建、跨独立单位转交时，应按接收关系及许可证核对义务；不能仅凭“内部”两字豁免。当前没有请求这类运行发行，未来条件不是本批已经履行的义务，也不应被误列为现在必须完成的对外发行工程。

## 特殊许可的具体使用规则

| 范围 | 当前记录与处理 | 转交运行包或改变组合时必须复核 |
| --- | --- | --- |
| Apache / MIT / BSD / EDL及其他随包声明 | 保留原版权、许可、NOTICE及修改来源，不用父项目许可覆盖内含组件 | 按实际许可证保留正文和署名；Apache修改标识、NOTICE及商标边界分别处理 |
| GPLv3的pglast | 实际环境及既有镜像中有此组件；保留GPL及libpg_query独立声明、已取得源码与构建材料 | 发生convey时按实际方式复核完整对应源码及取得途径；不凭一次工具导入就把全仓库改标GPL |
| MySQL Connector/J9.7.0 | 原LICENSE明确GPLv2、Universal FOSS Exception1.0和单独许可的随附技术，原文均保留 | 不套用已废弃的旧FOSS例外；不预先认定当前组合自动满足Universal FOSS例外 |
| MariaDB JDBC3.5.10 / LGPL组件 | 精确源码头为LGPL-2.1-or-later；保留原包/来源；没有删除或替换库 | 复核源码、重新链接/替换库、逆向调试等适用权利和通知；未修改不能等同无义务 |
| JDK、Nashorn、classfile backport | GPL与Classpath例外逐文件适用，另外许可的部分保留原条款 | Classpath例外不是全部组件免责，也不代替相应源码/通知义务 |
| Jakarta / Angus / Vert.x / JTS | 分别保留EPL/EDL/Apache/GPL+Classpath声明及来源；不根据名称列表自动选择最宽松许可 | 先核对具体文件、实际组合和例外，再确定许可路线及源码提供方式 |
| H2改包 | 维持已取得的精确源码、MPL/EPL声明和1070成员逻辑重放记录 | 对实际修改与源码、通知、可执行发行安排逐项核验；逻辑重放不是完整ZIP再现 |
| 字体、主题和构建工具 | 沿用前轮实际声明/精确来源，本轮补充is-reference声明及条款路线 | 修改字体的保留名称、图标商标及工具重新分发按实际对象核对；不把主题MIT套给所有字体 |

本表是基于已取得材料的技术使用范围复核，不是代签安全/法律批准。GPL原文网络获取失败的观察保留，使用既有验真正文并通过[SPDX收录正文](https://spdx.org/licenses/GPL-3.0-or-later.html)核对相关条款。其他依据为[Apache官方第4节](https://www.apache.org/licenses/LICENSE-2.0)、[MPL官方第2—3节](https://www.mozilla.org/en-US/MPL/2.0/)、[EPL官方正文](https://www.eclipse.org/legal/epl-2.0/)、[Oracle Universal FOSS例外](https://oss.oracle.com/licenses/universal-foss-exception/)及[OSI MIT正文](https://opensource.org/license/mit)。具体组件仍以自己的声明和正文为准。

## 未关闭事项的准确归属

| 编号 | 当前状态 | 关闭条件 |
| --- | --- | --- |
| N01-A：Python维护与安全处置 | 阻塞；3.13/3.12候选DEFERRED_BY_USER | 明确现有3.10生命周期及已记录CVE处置依据；不把暂缓当风险接受，不擅自创建候选 |
| N01-B：实际软件准入决定 | 尚未作出；已有有限资料复核与三项预选不能代替整体准入 | 按十类软件的精确制品、当前使用范围和未解风险形成实际决定；不得把未知项一并签成通过 |
| N01-C：最终可安装制品锁 | 尚未形成 | N01必需准入项关闭后，才根据已确认三项预选及其他精确制品生成和验证可安装锁；原锁继续保留 |
| N03/N05：最终功能配置 | 后续步骤；尚未通过 | 按选定身份、TLS、数据库、队列、对象存储等配置实测；本轮材料复核不代替服务功能 |
| 未来运行发行 | 当前未请求；条件保留 | 确定接收对象、实际包内容、源码/NOTICE/例外及取得途径，再执行对应验证 |

本轮已完成所列嵌套坐标、31项特殊许可、构建工具及材料保留的限定技术复核；不再笼统地将它们全部列为“尚未采集”。未证明的穷尽性或未来转交事项按各自边界保留，不能升级成已取得正式软件准入。

目前无需管理员安装命令、密码或私钥。正式age公钥仍是N04前置；本轮不生成正式身份密钥或备份密钥。更新仅涉及审查材料、导航、任务台账及实际验证回执，不增加整任务验收数。

当前需要确认的信息、12条CVE及实际游标观察见[统一准入清单](native-n01-admission-decisions.md)；嵌套许可的限定材料复核保留，Python候选仍暂缓。
