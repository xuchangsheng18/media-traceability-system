# N01第七轮：生成资源来源闭合与分发审查材料包

[第八轮最新：内部研发语义、字体与主题许可](native-n01-internal-semantic-license-review.md)按用户确认的内部研发范围更新；本页前轮数字/未决项保留历史范围。

2026-10-18；Linux / Miniforge py310 / CPU研发。**N01仍为IN_PROGRESS_BLOCKED_ADMISSION**。Python3.13/3.12候选继续暂缓，原100包锁与既有服务未修改。本轮推进实际构建和材料装配，不把来源验证、材料齐备程度与软件准入混为一项。

[本轮机器报告](../00-project/validation/native-n01-round7-admission-report.json) · [N01状态](native-linux-execution-status.json) · [上一轮差异和义务](native-n01-generation-and-distribution-review.md) · [T004任务卡](../../tasks/platform/T004.md)

## 已关闭：剩余4份vendor生成脚本的技术来源

沿用验真的Keycloak26.8.1固定提交24ed1dadf3f246a555adb6d3d4a99e9b3003fb3b，其源码归档及pnpm锁摘要均与前轮一致。从锁文件提取本次Rollup构建所需的43个精确包节点，分别核对registry完整性、锁内同一SRI和实际归档SHA256；明确排除25条非Linux/x64/glibc目标的可选依赖，未更换锁版本。

在Linux新建私有fixture/store，按固定依赖关系链接包，未运行任何依赖生命周期安装脚本；用既有隔离Node22.23.3候选直接运行原版rollup配置及原版导入改写脚本。两个进程均退出0。没有安装pnpm、创建Python候选、修改共享依赖或启动服务。运行环境限制JavaScript堆为1024MiB并降低调度优先级；仅隔离文件目录和环境变量，不冒充网络或系统命名空间沙箱。

| 生成脚本 | 与原发行包结果 |
| --- | --- |
| react.production.min.js | 7395字节，SHA256相同 |
| react-jsx-runtime.production.min.js | 939字节，SHA256相同 |
| react-dom.production.min.js | 132826字节，SHA256相同 |
| web-crypto-shim.js | 9773字节，SHA256相同 |

完整命令、输入和输出摘要见[实际构建](../00-project/validation/native-n01-round7/vendor-build-report.json)与[43包构建输入](../00-project/validation/native-n01-round7/vendor-build-inputs.json)。结合此前417个直接复制资源，**421/421个vendor资源已具备精确直接匹配或实际生成重建的技术来源证据**，见[闭合清单](../00-project/validation/native-n01-round7/vendor-origin-closure.json)。此结论只覆盖该vendor JAR内的421个资源，不扩大为整个Keycloak源码构建、Java生成包、字体权利或安全验收。

## 补核：Validation遗漏原因及175个变换类

取得Quarkus3.40.1的HibernateValidatorProcessor精确源包：构建步骤会变换Validation.buildDefaultValidatorFactory并转向ValidationSupport。固定Keycloak源码的IgnoredArtifacts则在CLIENT_ADMIN_API_V2未启用时移除Hibernate Validator相关扩展；Profile将该版本标为PREVIEW。配置拦截调用及规则原文保存在[精确源码](../00-project/validation/native-n01-round7/java-transform-source-report.json)。因此前轮默认重增强少一个Validation类有具体构建规则依据。

为验证因果，从同一验真发行归档新建私有目录，只将构建特性改为`--features=client-admin-api:v2`，其余沿用私有Java21、1536MiB堆、4活动处理器和低调度优先级。构建退出0，Validation类重新出现且摘要等于原发行包，**175个变换类的成员集合及每个成员字节全部相同**，见[实际单特性对照](../00-project/validation/native-n01-round7/validation-feature-report.json)。未声称ZIP容器整体字节相同，也未把预览特性用于共享环境、启动服务或正式采用。此前默认174类的原始结果继续保留，不以新探测覆盖。

因此Validation遗漏的限定因果核验及175个变换类字节来源不再笼统列为未知；生成包24个变化成员和整个Keycloak源码构建仍是独立范围，未由本结果自动证明。

对24个变化生成类已追加[结构差异清单](../00-project/validation/native-n01-round7/generated-class-diff.json)：按正式Class/Fieldref/Methodref/InterfaceMethodref常量项解析，逐类记录增删引用、方法签名和属性载荷摘要。4个类的删除引用能直接对应已移除的生成类，589个方法的属性载荷有摘要变化；后者含常量池编号等变化，**不是589项语义或业务行为变更**。本清单不再把所有UTF-8字符串当成类引用，也不凭字符串相关性宣称独占作者来源或安全通过。审计解析器初次接口计数偏移错误已定位、保留并修正；实际24类解析、最小合法类及非法头拒绝检查通过。

## 嵌套声明及实际未决项

- Go两个候选的260条实际编译模块记录递归收集到328份根目录/嵌套声明候选。唯一没有在模块目录找到文本的flatbuffers/go，补绑定此前已取得的精确提交仓库根许可。递归材料可能含未进入最终二进制的子目录，不按材料数量推算实际许可数量；候选也尚未采用。见[Go材料](../00-project/validation/native-n01-round7/go-nested-notice-texts.json)。
- 95份已验真wheel提取197份匹配正文，排除代码文件名误匹配。packageurl-python和pglast两项缺少匹配wheel正文的观察保留；已将精确验真的源包、packageurl的MIT正文及pglast内libpg_query许可补入材料包，不以嵌套库许可替代pglast自身GPL声明。见[wheel材料](../00-project/validation/native-n01-round7/wheel-notice-texts.json)。
- 43个私有构建包取得40份包内匹配声明；is-module额外取得精确版本源码许可及源码成员匹配，Rollup原生工具沿registry所载相同gitHead取得固定源码声明。is-reference1.2.1的精确源码仍仅有MIT声明，没有完整许可正文，不能编造。它属于此次构建工具；是否随未来交付件提供，应按实际交付边界判断，不直接冒充业务运行依赖。见[工具后续核验](../00-project/validation/native-n01-round7/tool-and-font-candidate-followup.json)。
- Font Awesome Free5.15.4来源候选及固定PatternFly源码中CDN所提5.7.2候选，均未与当前字体文件字节匹配。两份原始负向结果均保留；其许可文本只作候选审阅材料，不认定当前字体已经映射到这两个版本，也不再反复更换版本追求摘要。具体字体/图标的原始版权、OFL保留名称、适用条款及商标边界继续待核验。字体分发条件依据[SIL官方条款](https://openfontlicense.org/open-font-license-official-text/)，不能用父包MIT覆盖。

## 实际审查材料包及使用方法

本地私有归档为`D:\公安厅项目\_work\native-n01-round7-review-kit.tar.gz`；Linux对应路径为`/workspace/glwy/runtime/media-traceability-system/native-n01-round7-review-kit.tar.gz`。展开材料位于同一运行根目录下`native-n01-r7-materials/native-n01-review-kit/`。**这些是审查材料，不是已批准的正式软件发行包。** 源包、工具缓存和二进制不加入Git，仓库保存生成方法、来源、摘要、验证结果及未决项。

材料包包含469份按内容去重的正文、884条来源/成员绑定、两份完整源归档。去重只减少副本，NOTICE-INDEX仍保留对应来源。正文包括已收集的Keycloak、Swagger、npm、Go、wheel及官方标准条款；并不表示已穷尽Conda/OS、合并包或全部嵌套权利。

1. 先对照[材料包清单](../00-project/validation/native-n01-round7/distribution-material-kit-report.json)核对归档SHA256及大小。
2. 查看`NOTICE-INDEX.json`，按来源报告和成员定位`texts/<SHA256>.txt`；标准条款与组件原始声明分别标识，候选字体文本不当成已匹配声明。
3. 查看`sources/`中的pglast8.5和packageurl-python0.17.6精确源包。pglast源包包含libpg_query源码及构建文件；尚未从该源包重建并验证当前镜像内的parser扩展，不能把“源包存在”自动等同完整对应源码义务已履行。
4. Linux已验证内部清单473个文件，摘要和大小全部一致；受控检查确认改字节摘要不匹配、目录穿越被拒绝。见[实际材料验证](../00-project/validation/native-n01-round7/materials-verification.json)。这只验证材料字节和装配，不是法律或软件准入决定。

## 当前剩余及人工操作边界

| 剩余项 | 下一步要求 |
| --- | --- |
| Java生成包 | 对第五轮保留的24个变化成员继续补具体因果证据；4份vendor脚本及175个变换类已取得限定重建实证，不新增“所有组件必须位级复现”的政策 |
| 字体、图标、主题及其他嵌套组件 | 精确来源、版权/NOTICE、适用条款和源码提供义务逐项审阅；Swagger主题仍缺完整版权许可正文 |
| 交付件及对应源材料 | 在实际交付镜像/原生运行包确定后绑定完整SBOM、声明位置、对应源码/构建材料及接收者获取方式，特别是已观察到镜像含pglast8.5 |
| Python及安全准入 | 3.10生命周期和CVE风险未关闭；候选按用户决定暂缓，不代表风险接受 |
| 软件采用及迁移 | 候选版本采用、实际准入和N02—N08另有前置条件；未执行管理员安装、数据迁移或切换 |

当前技术核验不需要提供密码、密钥或执行管理员命令。后续确需选择正式交付范围、批准候选或执行安装时，再给出具体交付清单、差异、验收项和操作步骤；不要求用户现在笼统批准尚未核清的全部软件。

上一轮最终回执提交e4bb9656070af3b0d127753ddcc672318c07c965的[CI39095357141](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39095357141)已成功；324798字节产物SHA256为dc66263387ee91af04e0324c8fdbe09b1d590939b8db0f0da66a46f43d439854，32项门禁及6份关键报告PASS。本轮后续提交的CI按各自提交号独立记录，参见[当前CI回执](../00-project/validation/github-actions-report.json)。
