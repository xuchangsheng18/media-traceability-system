# N01第五轮：捆绑许可、H2改包与生成物来源

2026-10-18；Linux / py310 / CPU研发。本轮补充可核对的技术来源证据，**N01仍为IN_PROGRESS_BLOCKED_ADMISSION**。Python3.13/3.12候选按用户决定暂缓，未创建环境、未改原100包锁；没有原生安装或共享服务切换。

[本轮机器报告](../00-project/validation/native-n01-round5-admission-report.json) · [逐对象准入台账](../00-project/validation/native-n01-round5/technical-origin-and-admission-register.json) · [N01执行状态](native-linux-execution-status.json) · [前轮漏洞及许可](native-n01-license-vulnerability-runtime-review.md)

## H2：改包差异已有实际来源与逻辑重放

Keycloak26.8.1标签解析为提交24ed1dadf3f246a555adb6d3d4a99e9b3003fb3b；其四份POM与固定提交归档内成员字节一致。根POM锁Quarkus3.40.1、H2 2.4.240，与发行包build-system.properties一致。源码归档摘要、固定提交和Maven源包摘要均保留；HTTPS取得和标签/提交对应不冒充签名或完整源码构建证明。

精确版本JDBCH2Processor明确产生RemovedResourceBuildItem，删除com.h2database:h2的META-INF/native-image/reflect-config.json；AbstractFastJarBuilder复制有删除项的依赖时调用JarUnsigner，后者重写Manifest并过滤成员。这与前轮实际差异对应。将上游H2原包删除该成员，并用既有JDK的java.util.jar.Manifest重新序列化，**成员集合及1070个成员字节全部匹配发行包，清单也精确匹配**。

因此“删除该反射配置及清单改写的技术解释”已通过逻辑重放，不再笼统写成H2来源完全未知。归档整体SHA仍不同，没有声称ZIP时间戳/顺序/压缩流重建一致，也没有据此批准H2安全或许可准入。[实际重放](../00-project/validation/native-n01-round5/h2-logical-replay-report.json)保存每个成员期望/实际摘要。

H2精确版本POM及源码归档也已取得，Maven主域超时后使用Maven Central另一官方域并保留失败；POM声明MPL2.0及EPL1.0，源码Driver头部保留相应说明。[来源材料](../00-project/validation/native-n01-round5/h2-license-source-report.json)与[官方条款正文](../00-project/validation/native-n01-round5/canonical-license-texts-and-mapping.json)均可核对。具体分发/修改边界及选择适用条款仍须审阅，不能把MPL/EPL当Apache。[上游MPL正文](https://www.mozilla.org/en-US/MPL/2.0/)、[EPL1正文](https://www.eclipse.org/legal/epl/epl-v10.html)为条款依据。

## 三个Quarkus包：区分启动描述、变换类与生成类

| 对象 | 已核验事实 | 仍未证明的事项 |
| --- | --- | --- |
| quarkus-run.jar | 仅有1个Manifest，类文件0；18个Class-Path均定位到发行包内文件，主类唯一来自quarkus-bootstrap-runner3.40.1；私有重增强后整个JAR摘要不变 | 是启动描述文件，不能据此宣称18个依赖都已完成许可或安全审查 |
| transformed-bytecode.jar | 175个类逐一在同一发行包找到唯一同路径原始类并绑定摘要；重增强后174个成员与原变换包相同，少了jakarta/validation/Validation.class | 原始类是变换输入，不表示变换后字节与输入相同；完整发行构建参数和全量字节复现仍未完成 |
| generated-bytecode.jar | 1394个成员含1378个类与16个资源；1373个类有常量池引用可映射到发行包输入，322个有基础类候选；另5个ComponentsProvider辅助类对应精确版本Arc生成器规则 | 类型引用和名称关联不等于独占著作权归属，也不是每个生成类的完整可复现证明 |

[成员/常量池盘点](../00-project/validation/native-n01-round5/generated-and-h2-inventory.json)、[生成输入关联](../00-project/validation/native-n01-round5/generated-input-attribution-report.json)、[启动描述核验](../00-project/validation/native-n01-round5/boot-descriptor-report.json)保留各自范围。Quarkus3.40.1的AbstractFastJarBuilder、FastJarFormat、Arc生成器等源文件已按精确源包留档；不是用当前主分支泛泛说明旧发行包。

从已验真Keycloak归档新解包到私有夹具目录，以私有Java21、最多4个活动处理器及1536MiB Java堆运行默认kc.sh build，退出0。生成包1394→1281成员，1256成员字节相同，有114删除、1新增、24修改；变换包175→174成员。完整增删改列表与日志保留在[重增强报告](../00-project/validation/native-n01-round5/reaugmentation-report.json)。这是发行包的重新增强，不是从全部源码重建Keycloak。不得将这些差异删去、调整参数只追求摘要一致，或把1256个相同成员扩展成整包可复现。

该探测仅隔离文件目录与运行参数，没有网络/系统调用命名空间隔离；日志出现DBus传输发现信息，已原样保留。未向该夹具提供真实身份配置，未运行show-config或启动服务，不修改原审计目录、共享容器或数据。不能把私有目录称为完整操作系统沙箱。

## 捆绑许可：具体正文、上游源包和Web资源同时复核

本轮改为识别LICENSE/NOTICE等名称边界及前后缀，排除.class、.java等代码和META-INF/services服务注册描述。实际486个JAR收集到285份匹配文本，270个JAR仍无本规则匹配的内嵌文本。前轮279及本轮初次286按各自采集口径保留；计数变化是规则修正，未改上游归档。[当前全文](../00-project/validation/native-n01-round5/bundled-text-complement-report.json)逐项绑定成员和归档SHA。

针对缺正文JAR的263组主组件坐标，已取到261份精确版本Maven源码归档；192组有保留的版权/许可头，2组另找到完整匹配文本。两项404继续保留：MSSQL内嵌版本与发行文件的JRE分类器映射、Keycloak themes-vendor源码路径。没有sources.jar不等于无合法源码，但必须继续核对真实来源，不能随意换版本补齐数字。

新采集器最初将License.java、Notice.java及一个服务注册描述误收为许可文本；已先执行负向断言并观察失败，再排除代码/服务路径，修正后断言及正文摘要验证通过。初次与修正前报告保留；不把这类文件当LICENSE正文。[源码材料](../00-project/validation/native-n01-round5/missing-jar-source-materials.json)还区分头部摘录与完整文本，不能将192组头部当192套完整再分发材料。

另取得5种官方条款正文，将418个单一Apache2主组件POM声明关联到官方Apache2正文摘要。此处只补标准条款，不代替组件版权、NOTICE、合并JAR、生成物或嵌套依赖义务；也不能因找到标准文本就宣布270个缺口全部关闭。[正文与映射](../00-project/validation/native-n01-round5/canonical-license-texts-and-mapping.json)明确保留这一边界；依据为[Apache官方第4节](https://www.apache.org/licenses/LICENSE-2.0.txt)。

### Swagger实际脚本与漏带声明

生成包中的两个Swagger脚本分别引用.js.LICENSE.txt，但这些声明文件未在发行包JAR匹配材料中找到。精确SmallRye OpenAPI UI4.3.5 POM锁swagger-ui-dist5.32.8及swagger-ui-themes3.0.1，并明确只复制一组JS/CSS/映射文件；因此不能把SmallRye自身Apache声明当作所有Web依赖的完整材料。

已从官方npm registry取得两份精确版本归档，验证其sha512 integrity；两份实际脚本及theme-feeling-blue.css与生成包字节一致。swagger-ui-dist取得6份上游许可/声明，含两个实际引用的脚本许可文件、LICENSE和NOTICE。相关4份实际材料已补入[上游声明附录](../02-architecture/third-party-notices/native-n01-swagger-ui-upstream-notices.txt)，并保留[归档完整性、版本及脚本字节对应](../00-project/validation/native-n01-round5/swagger-ui-notice-recovery-report.json)。其他ES构建材料仅作该源包证据，不声称被本系统使用。

themes3.0.1元数据声明MIT，但归档未带许可正文，仍须继续查对应源码及版权声明；全部嵌套前端依赖、Go/wheel/Conda/OS的组合与分发义务也未因此关闭。上述附录是审查材料，正式交付包的装配及审阅仍待执行。

## 状态及后续

1. H2改包逻辑来源、启动清单来源和175个变换输入已形成实际证据；生成物重放及全部许可准入继续逐项保留未决，不填他人的批准。
2. Python候选继续[DEFERRED_BY_USER](native-n01-python-candidate-decision.json)，现有风险不视为接受。未新建3.13/3.12环境。
3. 继续处理生成差异、MSSQL分类器/Keycloak themes-vendor源材料、theme许可和其他传递组件/分发义务；然后才讨论实际软件准入与候选采用。N02安装、最终服务环境及恢复切换另有前置条件。
4. 最新已核验CI及被测提交见[CI回执](../00-project/validation/github-actions-report.json)。同步仅指源码和审计文档，见[服务器回执](../00-project/server-sync-receipt.json)，不代表原生部署完成。
