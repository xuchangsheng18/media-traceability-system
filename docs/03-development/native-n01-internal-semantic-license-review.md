# N01第八轮：内部研发语义复核、字体与主题许可

2026-10-18；用户已确认“目前仅团队内部研发”。本轮仍使用Linux / Miniforge py310 / CPU；**Python3.13/3.12候选继续DEFERRED_BY_USER，原100包锁未改，N01仍未批准软件准入或原生安装。**

[机器报告](../00-project/validation/native-n01-round8-admission-report.json) · [范围确认](../00-project/validation/native-n01-round8/internal-use-and-future-delivery-scope.json) · [N01执行状态](native-linux-execution-status.json) · [上一轮来源与材料包](native-n01-generated-source-and-distribution-kit.md)

## 当前范围与未来分发条件

当前材料包按团队内部研发审查用途编制，未制作或授权正式向公安厅/其他独立单位交付运行包或镜像。未来接收者、完整交付SBOM、对应源码提供及字体修改/保留名称等事项保留为**外部交付发生前的条件**，不把尚未计划的外部交付安排当作本轮已经履行或被豁免的义务。

“内部研发”也不自动证明团队全部人员属于同一法律主体；本轮没有作这种法律认定。既有GitHub源代码/文档公开授权保持不变，运行材料包仍在本地和Linux私有运行目录。当前软件安全与实际准入的未决状态继续保留。

## 24个生成类的指令层复核

在私有Java21下对原发行包和前轮默认重增强包运行JDK javap，逐类绑定原始归档、24个类成员和反汇编输出摘要。对常量池使用原始类文件的类型和值解析；字符串保留空白和转义，分支/异常表目标映射到指令序号，ldc/ldc_w等仅编码宽度差别按明确规则归一化。

| 范围 | 当前实测结果 | 可得结论 |
| --- | --- | --- |
| 24个变化类共同存在的方法 | 525个规范化指令及异常表结构相同，113个仍不同 | 可排除大量常量池索引、编码宽度及显示对齐影响；不等于整个类或程序功能等价 |
| 方法集合 | 69个原方法未进入新包，1个新增方法 | 列出实际增删，按DI/配置/启动记录器职责继续审阅，不能忽略新增或删除行为 |
| 113个结构变化方法 | 19个异常表也变化；其余94个异常表相同；其中8个字符串多重集相同但操作序列变化，4个操作码/字符串多重集/异常表均相同但其他操作数不同 | 分类有助于区分功能配置、注册内容和编号/顺序差别，不能把集合相同直接当作执行顺序无影响 |
| 解析完整度与对照 | 未解析常量池操作数0；未出现invokedynamic；索引/对齐差别应相同、字符串尾空格变化必须不同等受控检查通过 | 仅覆盖本次生成类和所列规则；注解、全部验证元数据及完整运行行为不在等价证明范围内 |

[逐类逐方法简表](../00-project/validation/native-n01-round8/generated-semantic-review.json)保留方法名、前后规范化摘要、指令数、增删字符串和首批具体差别。[输入绑定](../00-project/validation/native-n01-round8/semantic-inputs.json)验证24个原始成员和完整报告摘要。约31.6MB完整指令报告放入私有材料包的压缩附件，仓库保存摘要和简表，避免导航直接展开数十万行数据。

最初按javap显示文本比较得到506相同/132变化；进一步使用原始常量池精确值并处理编码宽度后，当前口径为525/113。初步报告在材料包保留。含`#`的已解析字符串曾被误记为未解析操作数，已按类型区分并修正；没有删除真实字符串差别或放宽为“全部通过”。上一轮421个vendor资源来源及175个变换类字节重建结论保持各自原范围。

## 字体：从链接线索细化到181份实际字体

[逐字体许可路线](../00-project/validation/native-n01-round8/font-license-register.json)核对原版权、字体族、文件摘要和声明来源，覆盖181份可解析字体；另外的SVG/EOT等资产继续沿原资源来源记录单列，不用181代表全部资产。

| 路线 | 字体文件数 | 新增核验 |
| --- | ---: | --- |
| nameID13明确OFL | 136 | 包括40份Overpass，其实际字体内已带完整OFL正文；附加LGPL网址不再单独写成OFL正文缺失或必须采用LGPL |
| nameID13明确Apache | 32 | 原文件声明与版权保留；不套用其他新版字体的许可 |
| Font Awesome4.7来源 | 3 | 沿用前轮精确归档成员匹配及对应许可材料 |
| Font Awesome5.6.3逻辑字体表来源 | 3 | 固定PatternFly字体变更历史及版本声明指向5.6.3；本轮比较所有SFNT字体表，见下文 |
| Bootstrap3.4.1来源 | 3 | 官方npm归档SRI及Keycloak锁一致，5个字体/其他格式资产字节匹配；补到Bootstrap原LICENSE，保留Glyphicons单独使用范围的复核 |
| PatternFly自身图标字体路线 | 4 | 对应固定源码成员和父项目MIT材料，继续核对自身图标与商标边界 |

Font Awesome3份文件与验真5.6.3包整体SHA不同，但所有字体表除head外字节相同；head差别仅限checkSumAdjustment及创建、修改时间字段。仅屏蔽这三个明确字段后，所有字体表全部相同，**name、版权、glyph等表未屏蔽且相同**。见[字体表证据](../00-project/validation/native-n01-round8/font-table-review.json)。这是有边界的逻辑字体来源证据，不能写成WOFF归档字节相同；未来涉及外部分发/修改字体时仍需核对实际许可和保留名称要求。此前5.15.4、5.7.2及5.6.3整体字节未匹配的观察保留。

完整OFL声明优先作为本轮实际字体的许可材料记录，不凭附加链接编造许可选择；条款依据[SIL官方正文](https://openfontlicense.org/open-font-license-official-text/)。这不代替实际权利或软件准入决定。

## Swagger主题：补齐声明与引用条款，避免错误推断

精确3.0.1源码README明确声明MIT并链接标准许可，package.json保留作者Mark Ostrander。缺少独立LICENSE文件本身不足以证明没有许可声明；本轮将**上游声明、作者元数据、MIT标准权限/免责条款**分别收录到[字体与主题附录](../02-architecture/third-party-notices/native-n01-round8-font-theme-notices.txt)，不填造版权年份，也不把其他项目版权人套给主题。

标准条款已通过[OSI官方页面](https://opensource.org/license/mit)阅读核对；直接下载HTML返回403的实际观察保留，未声称取得不存在的HTML摘要。附录条款正文来自既有验真MIT源材料的权限/免责部分，清楚标识为标准条款而非上游补发的LICENSE。[主题审查记录](../00-project/validation/native-n01-round8/font-theme-review.json)保存来源及边界。当前内部审查材料已补齐引用路线；实际归属、对外署名和后续分发适用性继续按实际交付范围审阅，不宣称法律批准。

## 内部审查材料包与验证

本地为`D:\公安厅项目\_work\native-n01-round8-internal-review-kit.tar.gz`；Linux为`/workspace/glwy/runtime/media-traceability-system/native-n01-round8-internal-review-kit.tar.gz`。包内保留上一轮469份去重正文、884条绑定、两份源归档，新增本轮完整语义报告、字体及主题附录、范围确认和索引。旧计数仅描述沿用材料，不直接累加为当前独立许可数量。

[归档与文件清单](../00-project/validation/native-n01-round8/internal-material-kit-report.json)及[Linux实际验证](../00-project/validation/native-n01-round8/materials-verification.json)为字节核对依据。本包标记为内部审查材料，不是正式外发运行发行包；其中对应源码材料的存在不自动证明未来全部源码提供义务已履行。

## 剩余工作与状态

1. 113个指令结构变化方法及新增/删除方法的具体行为影响仍需按最终选定功能配置开展针对性验证；不把所有变化都叫编号差异，也不新增全项目位级复现门槛。
2. 字体/图标及主题的当前材料路线已补充；7份Bootstrap/PatternFly自身字体路线及SVG/EOT等单独边界继续复核，未来对外分发安排列为条件事项。
3. Python3.10生命周期/CVE风险及其他实际软件安全准入未关闭；3.13/3.12候选按用户决定暂缓，不视为风险接受。
4. 候选版本采用、管理员初始化、原生迁移及切换N02—N08未执行。当前无需管理员命令或凭据。

上一轮最终回执1d9758749df755522d3d77392cff972ea807815d的[CI39096961185](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39096961185)成功；327859字节产物SHA256为c918c131b692090c5bfc462c8fa371b78afc5004fdd932e98a19d521b8ccfc17，已核对32项门禁及6份关键报告。本轮提交须看各自CI，参见[当前回执](../00-project/validation/github-actions-report.json)。
