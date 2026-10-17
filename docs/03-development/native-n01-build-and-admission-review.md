# N01源码构建、运行依赖和准入复核

[N01最新许可、漏洞及运行路径复核](native-n01-license-vulnerability-runtime-review.md)记录2026-10-18本轮实际结果。旧批次数值按观察时点保留；N01仍受许可、Python维护/安全和最终运行范围阻塞，未原生安装或切换。

本批适用 Linux / Miniforge py310 / CPU 研发环境。源码构建和以下限定范围的依赖核验已执行，**N01整体仍未完成，不具备原生安装或切换条件**。原100包锁、现有服务及持久数据保留。

[机器判定与证据摘要](../00-project/validation/native-n01-round3-admission-report.json) · [N01统一入口](native-n01-artifacts-and-dependencies.md) · [执行状态](native-linux-execution-status.json) · [候选变更范围](native-n01-security-remediation-change-request.md)

## 已执行的核验及其边界

| 对象 | 实际结果 | 尚不能据此认定的事项 |
| --- | --- | --- |
| PostgreSQL16.15 | 私有目录配置、编译及版本探测通过；TLS/ICU/readline配置保留 | 未初始化或运行数据库；未执行数据库回归、备份恢复、迁移或服务验收 |
| Nginx1.30.6 | 私有目录编译及版本/配置探测通过，包含TLS、HTTP/2、realip等 | 未安装系统单元或代理现用服务；不是部署成品 |
| OTP27.3.4.18 | 私有目录编译，crypto/ssl启动及密码库探测通过；调度器限制为2、异步线程1 | 未启动RabbitMQ、未做队列恢复；未覆盖所有OTP应用 |
| 原生工具链 | 40份已验真deb仅私有解包，C编译运行通过；未向系统包数据库安装 | 仍复用宿主cc1、头文件及运行库；不能声称40包自包含完整编译环境 |
| Python活动依赖 | 100分发包，137条活动Requires-Dist全部解析；25个Conda节点、64条依赖边解析通过 | 声明依赖满足不等于所有动态加载和业务路径都运行通过 |
| 恢复制品 | [95份wheel](../../config/native/python-runtime-wheels.lock.json)与[25份Conda包](../../config/native/conda-runtime-packages.lock.json)已下载并核对上游摘要，Linux再次核对wheel字节 | 100个Python分发包中packaging、pip、setuptools、tzdata、wheel由Conda包覆盖，不能误写96份wheel；未重建环境或完成全量恢复演练 |
| 安装文件来源差异 | 初查7项RECORD差异，逐项对照Conda归档、Conda26.7.2入口模板或已核验源码生成的字节码，剩余未解释项0 | 初始失败报告保留，不覆盖RECORD；本项不是整个环境逐文件校验通过 |
| ELF动态链接 | 排除1250个可重定位中间对象，403个运行文件、85个实际库文件摘要已登记；显式私有库路径下未解析依赖0 | JDK/Torch/PG需要各自库目录；仅构建探测环境，不能把路径直接复制为全局服务配置；dlopen、插件、宿主依赖恢复包仍待补齐 |

构建结果见[源码报告](../00-project/validation/native-n01-round3/source-build-report.json)。私有前缀与RPATH不是可部署发行制品。首次多架构OpenSSL头文件查找失败、OTP默认创建过多调度线程失败均保留；修正包含路径和调度参数后通过，没有通过关闭TLS规避问题。批次报告绑定实际审计脚本摘要；文本快照只是执行方法留档，不是经过通用参数化和测试的管理员安装工具。

## 捆绑许可：材料有进展，准入尚未通过

95份wheel收集到200份许可/声明材料；packageurl-python、pglast未发现归档内许可材料，仍需追溯对应版本的官方源码。Keycloak中486个JAR已逐个盘点，其中260个未发现内嵌许可材料；这些数字不能解释为260个组件无许可证，需结合POM、发行包共同LICENSE/NOTICE及精确版本源码核实。

[材料明细](../00-project/validation/native-n01-round3/wheel-and-jar-license-materials-report.json)、[Conda来源与许可材料](../00-project/validation/native-n01-round3/conda-origin-and-record-difference-report.json)保留路径、摘要与声明字段。Go模块及Ubuntu共享copyright仍需完成传递组件追踪、再分发义务、NOTICE/源码提供义务及适用软件准入审查。Apache-2.0只表示仓库自有成果的许可选择，不能替第三方组件签认。

补充追溯：已按PyPI摘要取得上述两包的精确版本源码归档，找到packageurl-python的MIT许可与pglast捆绑libpg_query的LICENSE，见[源码许可材料](../00-project/validation/native-n01-round3/missing-wheel-license-source-report.json)。pglast自身声明GPL-3.0-or-later，不能用其捆绑库的许可替代自身许可。当前代码在输入校验脚本使用pglast，不能仅因它存在于研发Python环境就断言业务应用链接或发行了它；正式分发角色与义务仍须逐项核对。

## 漏洞扫描与适用性

扫描器固定为Syft1.54.1、Grype0.120.1，归档摘要已核对；数据库v6.1.10、构建时间2026-10-17T06:27:09Z，实际db status为valid。数据库导入命令曾超时，随后单独核对数据库有效性；没有将超时改写成成功。扫描未设置忽略项或“只看有修复版本”等过滤。

| 原版本扫描对象 | 原始匹配数 | 执行结果和准入区别 |
| --- | ---: | --- |
| Python现有环境 | 22 | 扫描执行通过，适用性与处置尚未全部完成 |
| Node22.21.1 | 27 | 含严重/高危匹配，不能准入 |
| age1.3.2发行二进制 | 112 | 含Go和x/crypto匹配，不能准入 |
| SeaweedFS4.48发行二进制 | 19 | 含Go和x/net匹配，不能准入 |
| Java、RabbitMQ、Keycloak | 各0 | 当前SBOM/数据库无匹配，不表示没有漏洞 |
| PostgreSQL源码构建目录 | 1 | CVE-2017-8806，CPE匹配约束unknown，须专门判断 |
| Nginx、OTP源码构建目录 | 各0 | 仅说明本次目录扫描结果，不覆盖宿主OS全部组件 |

上述合计180条运行目录匹配和1条源码构建目录匹配，**不是181个独立且可利用的漏洞**。Conda/二进制和Go别名会重复计数；全部原始匹配保留，不能直接批量忽略。[运行扫描](../00-project/validation/native-n01-round3/runtime-vulnerability-report.json)与[构建目录扫描](../00-project/validation/native-n01-round3/source-vulnerability-report.json)给出包、版本、匹配器、修复范围及来源。

Python候选适用性说明：CVE-2026-3298涉及Windows的Proactor及3.11新增API，当前Linux3.10的BaseEventLoop未提供该方法；这支持本环境不适用的候选结论。CVE-2023-36632的CVE记录存在disputed标签。两者均不得伪造安全审阅人签认，其他Python匹配仍需逐项判断。依据：[Python3.11变更](https://docs.python.org/3.11/whatsnew/3.11.html)、[CPython问题148808](https://github.com/python/cpython/issues/148808)、[争议问题103800](https://github.com/python/cpython/issues/103800)。

Node官方将CVE-2025-55130定为High，部分扫描来源定为Critical，需同时保留来源差异，见[官方安全公告](https://nodejs.org/en/blog/vulnerability/december-2025-security-releases)。Go修复依据见[GO-2026-6612](https://pkg.go.dev/vuln/GO-2026-6612)；不能只升级应用版本号而继续携带旧工具链和旧模块。

已进一步取得[11条Python及1条PG匹配对应的CVE权威记录](../00-project/validation/native-n01-round3/python-and-postgresql-cve-source-report.json)，保留来源、摘要、affected范围、争议标签和上游链接。处理队列如下，均不是他人签认的例外：

| 匹配项 | 精确复核要点及当前处理 |
| --- | --- |
| CVE-2017-8806 | 记录针对Debian/Ubuntu的postgresql-common脚本及符号链接处理，不是上游PG源码本身；私有PG构建的CPE结果需按产品范围判断，宿主若安装该包仍需另核版本 |
| CVE-2024-3220、CVE-2026-3298 | 记录明确Windows条件；支持当前Linux研发范围的不适用候选判断，不扩展至Windows原生验收 |
| CVE-2026-12003 | 涉及构建VPATH、源码树识别和Windows路径条件；需结合实际Conda构建配置确认，不能仅凭修复版本大于3.10就排除 |
| CVE-2023-36632、CVE-2026-3479 | 权威记录标有disputed；保留原始匹配和上游说明，争议不等于正式豁免 |
| CVE-2025-12781、CVE-2026-3446 | base64字符集/填充后额外内容的处理；仍需对实际输入规范及调用路径复核，不能因JWT使用签名就自动排除全部base64风险 |
| CVE-2025-15366、CVE-2025-15367 | IMAP/POP命令中的控制字符注入；核对运行用途及调用路径，不将未搜索到直接import当不存在传递调用的证明 |
| CVE-2026-12345 | TemporaryDirectory清理竞态；需核对平台、rmtree能力和目录写权限，不能把一次合成夹具清理成功当漏洞修补 |
| CVE-2026-6019 | cookies.Morsel.js_output中的脚本上下文转义；需核对是否调用或输出此API |

这些记录说明Python准入仍有实质待核项。本批未变更Python3.10.22或原100包锁，也没有用Go/Node候选通过替代Python安全处置。

## 隔离修补候选

用户已确认候选验证范围，[输入锁](../../config/native/security-candidate-inputs.lock.json)与原基线分开。Node22.23.3已核对官方摘要，版本、现有前端单元、构建和3条浏览器测试通过，相同数据库下漏洞匹配0。首次浏览器测试因未指定项目已有缓存目录而失败，使用项目既有PLAYWRIGHT_BROWSERS_PATH后重跑通过；未下载或放宽测试。见[前端结果](../00-project/validation/native-n01-round3/node-frontend-validation-report.json)、[候选扫描](../00-project/validation/native-n01-round3/node-candidate-vulnerability-report.json)。这只是候选验证，不表示已采用或已替换共享Web服务。

age/SeaweedFS候选采用官方Go1.27.2；分别目标修补x/crypto0.56.0、x/net0.60.0。源码锁绑定官方仓库精确提交；源码归档SHA是HTTPS取得后的观测摘要，不能冒称上游签名。Linux直连Go模块/校验数据库超时，改由仅绑定回环地址的临时SSH通道获取Windows经官方HTTPS缓存的文件，Go校验数据库签名验证保持开启。下载错误、构建和上游测试结果须全部记录，尚不能据Node候选通过宣布三项修补全部通过。

age修补候选已通过`go mod verify`、上游`go test ./...`、编译、版本及构建信息探测，并通过合成数据加密恢复和错误密钥拒绝；临时私钥已销毁。见[构建与测试](../00-project/validation/native-n01-round3/age-candidate-validation-report.json)、[恢复探测](../00-project/validation/native-n01-round3/age-candidate-roundtrip-report.json)。重扫剩余2条Unknown匹配均为GO-2026-5932，来源为同一模块在两个二进制中的记录；[上游说明](https://pkg.go.dev/vuln/GO-2026-5932)影响的是x/crypto/openpgp系列包。对这两个CGO关闭的静态候选列出实际编译导入包，未包含该系列，支持“本候选不受影响、待安全复核”的判断；原始匹配不删除，不作整个x/crypto模块的通用豁免。

SeaweedFS候选已通过存储相关上游测试`go test ./weed/storage/...`、完整二进制编译、版本/构建信息探测，以及[S3合成夹具的6项隔离检查](../00-project/validation/native-n01-round3/seaweed-candidate-s3-report.json)：启动、不同版本、两次内容摘要、错误凭据403拒绝及重启后读取历史版本。第一次选用的端口预检发现占用后即停止，未终止占用进程；改用经检查的回环端口48111—48118完成测试，随后测试进程、凭据和夹具清理。此处“恢复”仅指候选自身合成数据重启保留，不是原项目数据迁移或正式备份恢复。

[候选构建记录](../00-project/validation/native-n01-round3/seaweedfs-candidate-validation-report.json)保留首次下载失败和后续离线恢复构建结果；仅向Go模块缓存补入官方HTTPS取得的字节，未手工生成ziphash，也未关闭go.sum或校验数据库验证。[重扫](../00-project/validation/native-n01-round3/seaweed-candidate-vulnerability-report.json)剩余1条Unknown，同为GO-2026-5932，实际编译导入列表未包含OpenPGP系列包，仍作限定候选判断。

[Go捆绑模块材料](../00-project/validation/native-n01-round3/go-bundled-license-materials-report.json)登记age的7个模块和SeaweedFS的253个模块，所有模块对应源码目录均存在，补充构建后模块校验通过。除flatbuffers/go子模块外均找到顶层许可/声明材料；已按其伪版本的精确提交追溯[仓库根许可](../00-project/validation/native-n01-round3/flatbuffers-license-source-report.json)。这是实际编译模块的来源/材料清单，不是全部嵌套许可义务已审阅。修补后的[go.mod/go.sum](../../config/native/security-candidate-module-locks/)独立归档，不替换已确认基线。

宿主来源映射为[23个OS包及86个文件来源](../00-project/validation/native-n01-round3/os-runtime-package-origin-report.json)，其中86含85个已解析库和1个实际存在的宿主编译器前端。私有工具目录中与宿主库摘要相同的副本已标识；Conda、JDK和私有构建库不能因没有dpkg归属而误判无来源。对应精确恢复包与声明依赖已按下段补齐，可选动态加载范围仍需另外核对。

进一步补齐：[声明依赖图](../00-project/validation/native-n01-round3/os-dependency-graph-report.json)将这23个宿主来源包与40个构建候选包展开为89个节点、232条Depends/Pre-Depends边，未解析0；限定使用所观察到的依赖表达式、已安装提供者及原APT候选计划，不冒充通用求解器。已按官方签名索引取得[全部89个精确版本恢复包](../../config/native/os-runtime-recovery-packages.lock.json)，Linux重新gpgv验签并检查Valid-Until、索引摘要、89个包摘要/大小及deb控制字段，全部一致。

[实际包与载荷核验](../00-project/validation/native-n01-round3/os-recovery-package-verification-report.json)还对照了32个有OS包归属的已解析宿主库/编译器文件，全部摘要一致；89个包的copyright材料（含跨包符号链接）均已解析。初次4项失败是采集器只保存了符号链接名称、未收集实际.so版本文件，签名载荷为空引用；补收真实目标后核验通过，初始观察保留，没有修改宿主库。其余Conda/JDK/私有构建库须看各自来源证据，不能说86个文件都属于OS包。

以上关闭了这组目标包的恢复输入缺口，**不等于整台宿主机镜像、所有可选插件/dlopen路径或恢复演练已完成**。包内版权材料找到也不是全部许可义务审阅通过；N01继续受软件准入阻塞。

## 徐昌胜需要操作的事项

1. **现在不要安装或切换**。N01仍有安全和依赖阻塞，本页不提供未经验证的apt安装、全局环境修改或停写指令。此前管理员清单的只读预检可以执行，见[管理员清单](native-linux-admin-checklist.md)。
2. 候选验证已获确认，无需重复批准。候选结果全部具备后，需审阅实际依赖补丁、测试与重扫结果，决定是否采用新候选；当前不能对旧版本作整体安全放行。
3. 正式备份公钥尚未建立，这是N04前置条件。准备到该步时由徐昌胜在受控位置生成、保管私钥并验证恢复，只提供age公钥或服务器公钥路径，不发送私钥。临时夹具密钥不可替用。
4. 后续管理员账号、目录、systemd初始化仅执行经过验证、绑定包摘要和准确目标的交接包；其生成和执行状态仍为未完成。完成后回传执行时间与脱敏结果，不能仅回复“已安装”就填写验收通过。

N01之后的N02—N08、原生配额、服务恢复和实际切换仍按原实施计划执行；本批成果不替代它们，也不自动关闭T004或T001—T012。
