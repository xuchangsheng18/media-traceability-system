# N01软件准入与候选制品采用复核

2026-10-18（北京时间）；仅限Linux / Miniforge py310 / CPU团队内部研发。N01仍为`IN_PROGRESS_BLOCKED_ADMISSION`。本页是当前准入和候选采用入口；历史报告保留，不能把旧缺件计数直接当作当前缺口。

[10类软件当前台账](../00-project/validation/native-n01-round9/software-admission-register.json) · [精确候选预选申请](../../config/native/candidate-adoption.proposal.json) · [原生总状态](native-linux-execution-status.json) · [170任务导航](../../tasks/README.md)

## 本轮实际补齐

上一轮最终回执提交`0df5dc5062cd5d77665819de8c0a47dc843042b8`的[CI 39099562000](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39099562000)成功；332134字节制品SHA256为`53d938432e20a9990e203683b8776fbe3d0dc01c8ae9bbc24b42b6fe083c5bda`，32项门禁和6份关键报告已核验。它不代表本页后续提交已经通过CI。

### 候选剩余扫描匹配的适用性

[Go官方记录](https://pkg.go.dev/vuln/GO-2026-5932)针对`golang.org/x/crypto/openpgp`及其6个子包，全部版本无已知修复。模块级匹配不能直接证明这些包已编入目标，也不能仅凭严重级别Unknown忽略它。

在现有私有候选目录核验精确二进制、`go version -m`、与仓库相同的go.mod/go.sum，以及离线`go list -deps`和`go tool nm`。age、age-keygen、weed三个实际入口分别列出200、145、1743个依赖包，均未含官方列出的7个受影响包，也未在可用符号表发现其符号。见[Linux实际核验](../00-project/validation/native-n01-round9/candidate-probe-report.json)和[锁定的官方记录](../00-project/validation/native-n01-round9/GO-2026-5932.json)。

限定技术结论为`NOT_AFFECTED_CANDIDATE_PACKAGE_NOT_LINKED`。原扫描FAIL及3条匹配保留，不新增忽略项、不宣称x/crypto模块本身已修复。结论只覆盖观测到的Linux amd64、CGO关闭、默认标签和三个主入口；不是全调用图证明。改变源码、工具链、构建标签、插件、平台或二进制必须重新核验。本轮没有重编译，也没有启动候选服务。

### 内部许可材料补充

- FontAwesome.otf实际与4.7.0发行成员精确相同，早期报告已有证据；上一轮按文件名分类时漏掉OTF。本轮改回字体专用SIL OFL路线，不能套用PatternFly父项目MIT。
- 三份PatternFly自身pficon字体分别绑定5.4.2、4.224.5固定源码提交及原始MIT正文；没有据此授予商标权，也未修改图标。
- Bootstrap五份字体资产已有精确字节匹配。[Bootstrap 3.4官方说明](https://getbootstrap.com/docs/3.4/components/#glyphicons)说明Halflings为Bootstrap免费提供，并请求尽可能保留回链。本批保留原捆绑使用及署名，不能扩大为独立字体再许可。
- SeaweedFS编译模块`github.com/google/flatbuffers/go`的子目录缺少许可正文；本轮取得其伪版本对应完整提交`3b8644d32c50e86872584829af4b8caf180235ab`的父目录Apache许可证，且go/builder.go与实际模块缓存字节相同。这是父许可材料补齐和单文件对应证据，不是整个上游归档重现。

见[字体逐项依据](../00-project/validation/native-n01-round9/residual-font-internal-review.json)、[Flatbuffers父许可](../00-project/validation/native-n01-round9/flatbuffers-parent-license-review.json)及[本轮署名附录](../02-architecture/third-party-notices/native-n01-round9-internal-supplement.txt)。本轮附件在仓库及服务器单独交付，未改写上一轮485文件的不可变内部材料包；法律/安全整体批准未代签。

## 候选采用的具体申请

申请只针对N01后续原生研发制品的预选，尚无用户采用决定。所有二进制SHA256、归档、源码提交、模块锁摘要均列在[候选申请](../../config/native/candidate-adoption.proposal.json)，可逐项审阅；不使用latest。

| 候选 | 技术复核依据 | 申请采用范围 | 未包含的批准 |
| --- | --- | --- | --- |
| Node22.23.3 | 官方归档摘要、版本探针、既有前端构建/扫描证据；扫描库时间见原报告 | 后续原生研发Web构建工具预选 | 不修改现有前端锁、共享运行环境或原制品锁 |
| age1.3.2重建候选，Go1.27.2、x/crypto0.56.0 | 既有上游测试、加解密/错误密钥探测；本轮分别核验age及age-keygen包图和符号 | 后续N04备份工具制品预选 | 不生成正式密钥、不表示已验证正式备份恢复 |
| SeaweedFS4.48重建候选，Go1.27.2、x/net0.60.0 | 实际完整模块锁还包含x/crypto0.57.0；既有存储单测及S3探测，本轮weed包图/符号及父许可材料 | 后续原生研发对象存储制品预选 | 不切换存储、不替换既有服务、不宣称所有后端/插件可用 |

源码归档摘要中，age/SeaweedFS为HTTPS实际取得归档的摘要，并非上游签名；这一来源强度差别保留。预选即便获认可，仍须N01其他必需项通过后才生成可安装最终制品锁；候选申请不是安装器输入，也不能绕过既有校验器。

## 十类软件当前处置

| 软件 | 本轮可确认内容 | 尚未关闭或后续验收 |
| --- | --- | --- |
| Python3.10.22 | 现有环境和原100包锁保留；3.13/3.12候选继续暂缓 | 生命周期和已记录CVE处置未关闭；暂缓不等于风险接受 |
| Node | 22.23.3候选证据可供预选审阅 | 用户采用决定、最终制品锁待定 |
| PostgreSQL16.15 | 源制品/构建及限定产品边界证据已留存 | 技术误匹配候选仍需安全处置复核；N03/N04会话与恢复验证 |
| RabbitMQ4.3.6 | 精确发行包和OTP组合已识别 | 软件准入待定；N03节点、N04队列恢复 |
| OTP27.3.4.18 | 私有构建及crypto/SSL等限定探测已通过 | 软件准入待定；N03验证最终服务启动环境 |
| SeaweedFS4.48 | 重建候选、剩余包级匹配及Flatbuffers许可材料本轮补充 | 用户采用决定；N03/N04真实存储功能与恢复 |
| Keycloak26.8.1 | 生成物限定复核、字体主题来源及内部材料已交付，限定人工复核已认可 | 整体安全准入待定；N03/N05验证选定功能配置 |
| Java21.0.12.1+1 | 精确JDK和既有模块/TLS/headless探测有记录 | 整体准入待定；N03最终服务环境，不扩大为所有JDK能力通过 |
| Nginx1.30.6 | 签名、源码构建及模块检查有记录 | 整体准入待定；N03代理/TLS及错误证书拒绝 |
| age1.3.2 | age和keygen候选精确摘要及包级复核已补充 | 用户采用决定；N04前由徐昌胜建立正式公钥和保管方式 |

当前没有将所有未知项都交给一次“认可”来关闭。现存[Python/PG逐CVE表](../00-project/validation/native-n01-round4/python-pg-applicability-review.json)保留12条唯一CVE的技术判定及未决事项；正式安全签认与候选预选为两回事。FIPS/HSM、LDAP/Kerberos、GPU、离线、Windows原生和生产不因本轮资料核验而通过；当前内部默认研发功能之外，启用前再确定适用范围和验证。

## 需要用户的决定与操作

徐昌胜可决定是否仅登记以上三项候选的原生研发制品预选；逐项同意或暂缓均可。此决定不接受Python风险，不批准N02安装、停写、迁移或外发。采用意见尚未收到前，状态为`PENDING_EXPLICIT_ADOPTION_DECISION`。

本轮不需执行管理员命令，不需发送密码、Token或私钥。后续N02只有在N01必需项真实关闭后，才交付管理员执行包。任务总数与完成统计保持实际口径，不因材料复核增加整任务验收数。
