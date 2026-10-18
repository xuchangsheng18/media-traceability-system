# N01第六轮：生成差异、嵌套许可与分发义务

2026-10-18；Linux / Miniforge py310 / CPU研发。**N01仍为IN_PROGRESS_BLOCKED_ADMISSION**。本轮补充来源、差异解释和可执行的分发检查，不代表软件准入、原生安装或正式交付。Python3.13/3.12候选继续DEFERRED_BY_USER，现有环境及原100包锁未改。

[本轮机器报告](../00-project/validation/native-n01-round6-admission-report.json) · [执行状态](native-linux-execution-status.json) · [第五轮原始观察](native-n01-bundled-origin-review.md) · [CI回执](../00-project/validation/github-actions-report.json)

## 生成差异解释

本轮复用第五轮真实私有重增强的输出，未重新启动服务或反复更换参数追求相同摘要。生成包1394→1281成员，1256相同、114删除、1新增、24修改。固定Keycloak提交的选项、映射和扩展包含规则，与实际输出一起保存于[差异解释](../00-project/validation/native-n01-round6/generation-difference-explanation.json)及[源码证据](../00-project/validation/native-n01-round6/generation-build-source-excerpts.json)。

| 差异 | 已能解释的范围 | 证据边界 |
| --- | --- | --- |
| 114个删除成员 | 按路径分组为OpenAPI/Swagger 23、Health 20、Metrics 23、共享DI/校验/配置48；固定源码中OpenAPI、health、metrics选项默认false，health控制扩展包含、metrics映射micrometer，OpenAPI映射对应扩展开关 | 这些是名称分组及构建规则的一致性解释；未逐类验证全部因果关系，不能声称114项均已精确重放 |
| 新增META-INF/keycloak-persisted.properties | 实际内容记录optimized=true、prod配置及本次生成时间；固定源码PersistedConfigSource定义相同输出路径 | 绑定真实夹具输出和摘要；不是原始发行构建参数的恢复证明，也不以时间戳解释其他全部差异 |
| 24个改变成员 | 完整成员及前后摘要保留；Arc组件/上下文、观察者及记录类随包含的bean/扩展集合重新生成 | 未完成逐指令重放，不能直接判为无害或仅时间差异 |
| transformed包少Validation.class | 其余174个成员逐字节相同，175个原始输入来源已定位 | 此类未进入新输出的精确原因仍未证明，不把输入来源已知当作变换通过 |
| quarkus-run和H2 | 私有重增强前后归档摘要均不变；H2的1070成员逻辑重放沿用第五轮实证 | 全ZIP一致和所有生成物完整源码构建均未声称通过 |

完整位级复现未作为本轮新增的强制政策；应按已有计划审阅来源可信度、差异、许可、安全与实际可用性。当前未决项保留，不用“未完全复现”抹掉已取得的限定证据。

## 嵌套vendor来源与许可

固定Keycloak源码的pnpm锁锁定8份本轮取得的npm归档，均核对registry完整性和锁内同一SRI，未执行npm安装脚本。[逐资源核对](../00-project/validation/native-n01-round6/vendor-npm-origin-report.json)记录421个实际vendor资源，其中417个与上游npm成员摘要一致；跨包存在相同资产，因此各包匹配数量不能直接相加。

直接匹配涵盖rfc4648、PatternFly3/4/5的CSS、字体和图片。剩余4个为React、React JSX runtime、React DOM及web-crypto-shim生成脚本。固定rollup配置展示生产模式替换、压缩、外部React及导入改写；已取得React18.3.1、React DOM18.3.1、scheduler0.23.2及noble/hashes2.0.1精确包和许可。构建输入与规则已找到，4个输出尚未完成打包重放，不将全部传递依赖视为已经覆盖。

PatternFly4.224.5的常规v标签返回404，实际查得prerelease-v4.224.5固定提交98abe75e22c2cabeb5be4510d0217a008a5e206c；其源码247个资产与发布资源相同。该路线作为经字节匹配的源码候选，不冒充npm提供了不存在的gitHead。PatternFly5.4.2采用registry所载固定提交98daf38b464e21a32fe71d275cca0c3530d46087，177个源资产字节匹配。两份源码根许可已取得，见[源码及材料](../00-project/validation/native-n01-round6/patternfly-source-license-report.json)；其余生成CSS及字体、图标、图片的单独权利和商标边界继续待核验。

已将8份实际上游材料汇入[新增声明附录](../02-architecture/third-party-notices/native-n01-vendor-upstream-notices.txt)。该数量是材料份数，不是8种许可或全部资产权利通过。既有[Swagger脚本声明](../02-architecture/third-party-notices/native-n01-swagger-ui-upstream-notices.txt)保留。

进一步读取293个字体/SVG资产：181份SFNT字体的名称表成功解析，未发生解析失败；其他112份SVG/EOT没有按SFNT解析。按nameID13/14线索分组为96份OFL、32份Apache、40份包含LGPL链接、125份未从选定名称记录取得完整许可（含上述非SFNT资产）。这些是记录分组，不能据链接直接裁定许可选择；40份LGPL链接均来自Overpass系列。6份字体还与registry完整性验真的Font Awesome4.7.0包字节相同，该额外包未声称已与Keycloak传递锁绑定。[逐文件元数据](../00-project/validation/native-n01-round6/font-metadata-and-obligations-report.json)保留版权、许可和链接；[字体内嵌正文附录](../02-architecture/third-party-notices/native-n01-vendor-font-notices.txt)保留实际完整文本。分发OFL字体须按原字体版权及保留名称处理，不套用父包MIT，依据[SIL官方条款](https://openfontlicense.org/open-font-license-official-text/)。

swagger-ui-themes v3.0.1标签解析到9290ea507531fb67efd44e633786d59209045ad5；其源码CSS与实际选用npm CSS字节相同。精确源码也没有完整LICENSE文件，README仅声明MIT并链接标准文本。因此来源路线已完成限定核验，**原始版权及完整许可正文缺口继续保留**，不编造年份、著作权人或许可授权。[实际后续核验](../00-project/validation/native-n01-round6/swagger-theme-source-followup.json)

## 实际分发边界与关闭条件

完整登记见[逐对象分发义务](../00-project/validation/native-n01-round6/distribution-obligations-register.json)。这些是按实际材料形成的执行要求，尚无他人签署的准入决定。

| 对象/分发路径 | 交付前必须补齐 | 当前状态 |
| --- | --- | --- |
| Apache组件、生成包及合并包 | 随交付保留适用版权、许可、NOTICE；标记修改，按真实嵌套内容展开，不能用父POM替代 | 已有正文和部分精确声明；全部合并/嵌套组件未关闭。要求依据[Apache第4节](https://www.apache.org/licenses/LICENSE-2.0) |
| npm字体/图片及MIT/BSD组件 | 保留原始版权和许可条件；逐项检查字体、图标及商标，确认生成脚本中的传递组件 | 417个资产来源匹配；权利范围与最终声明装配待完成 |
| H2双许可 | 明确采用的适用路线，提供对应源材料、实际改包步骤和所需声明；不能自行把双许可改成Apache | 原包/源包和逻辑改包已留证，正式路线与交付审阅待决。MPL路线参见[第3节](https://www.mozilla.org/en-US/MPL/2.0/) |
| pglast与完整py310归档/镜像 | 核对最终归档或镜像真实内容，按适用GPLv3分发方式保留许可、对应源码、构建安装材料及接收者获取途径 | 不能因业务代码未直接import就视为未分发；完整环境镜像仍可能包含pglast，未据此改变本项目整体许可 |
| Go、wheel、Conda、OS、JDK、OTP及其他JAR | 按实际交付件绑定摘要、原声明、补丁/构建脚本及适用源码提供方式 | 已验真的恢复包不等于义务已履行；待交付物清单及逐组件审阅 |

[pglast边界实查](../00-project/validation/native-n01-round6/pglast-distribution-boundary.json)记录：直接使用在输入资料校验器；原100包锁含pglast，而现有Docker构建复制完整py310环境归档及scripts。因此“只作为研发工具使用”不足以证明最终镜像没有它。本轮没有拆锁、删除包或改Docker行为。应先盘点真实交付件，再按[GPLv3第6节](https://www.gnu.org/licenses/gpl-3.0.html)选择实际符合的二进制分发/对应源码提供方式；仅放一个上游网址不能作为已履约证据。

本轮另对现有API、worker及推理三个容器只读核验元数据：三者均实际含pglast8.5，License-Expression为GPL-3.0-or-later，来自同一镜像sha256:26ff92ce2c786f40089a4afda300fa56af00bd8dfe829903791e0a1f7a0a1af0，解析扩展文件摘要也一致。[实际镜像观察](../00-project/validation/native-n01-round6/runtime-pglast-presence.json)证明本批研发镜像包含该包，不再仅写“可能包含”。未核验未来交付镜像或全部镜像SBOM，没有导出业务数据或重启容器；正式分发安排仍待完成。

## CI、状态与下一项

上一轮最终回执提交2fd8d49cfb7ff03a515c25a822cae51aa422f7e7的[CI39090305363](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39090305363)成功。已下载322075字节产物并核对API摘要0755aeb8c1f2fe88650022fffc76ee419c3d470212f2c5f988bdbc70c2aea6b9；实际32项门禁及6份关键报告PASS。该结果只绑定该提交，本轮提交须看其独立运行。

本轮只推进N01/T004现有未完成项；170任务完成计数不增加。下一项仍为N01：4份生成脚本构建核验、生成类差异的进一步因果证据、字体/图标及其他嵌套材料、最终分发件与对应源材料装配、软件准入复核。Python候选暂缓不视为接受生命周期/CVE风险。原生安装、恢复和切换N02—N08尚未执行。
