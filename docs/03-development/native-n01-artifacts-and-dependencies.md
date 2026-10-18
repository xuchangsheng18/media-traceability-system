# N01原生制品及依赖核验

[第八轮最新：内部研发语义、字体与主题许可](native-n01-internal-semantic-license-review.md)按用户确认的内部研发范围更新；本页前轮数字/未决项保留历史范围。

[第七轮最新：421个vendor来源与实际审查材料包](native-n01-generated-source-and-distribution-kit.md)已更新；本页前轮数字按当时观察阅读。4份vendor脚本已重建匹配，其他来源/许可准入仍有未决。

[第六轮最新生成差异、嵌套许可与分发义务](native-n01-generation-and-distribution-review.md)已补充；本页旧观察按当时范围保留，N01仍受软件准入阻塞，Python候选暂缓。

[第五轮捆绑许可、H2与生成物来源核验](native-n01-bundled-origin-review.md)为最新技术复核入口；H2逻辑重放及启动描述已核验，生成差异和全部许可准入仍未完成。前轮数值/未决项按当时范围阅读；Python候选继续暂缓。

[N01最新许可、漏洞及运行路径复核](native-n01-license-vulnerability-runtime-review.md)记录2026-10-18本轮实际结果。旧批次数值按观察时点保留；N01仍受许可、Python维护/安全和最终运行范围阻塞，未原生安装或切换。

2026-10-17，适用Linux / Miniforge py310 / CPU研发。**主要制品字节核验通过，N01整体仍在进行；不允许据此安装或切换服务。**

[执行台账](native-linux-execution-status.json) · [制品锁](../../config/native/artifacts.lock.json) · [构建依赖候选锁](../../config/native/os-build-dependencies.lock.json) · [T004任务卡](../../tasks/platform/T004.md)

2026-10-18补充状态：已完成三份源码私有构建、95份wheel/25份Conda及89份目标OS恢复包核验，并执行三项隔离修补候选验证。最新结果与仍未关闭的软件准入见[补充复核](native-n01-build-and-admission-review.md)。下表保留前一批证据范围，不应据旧40包数字推断当前只有40份恢复输入。

## 本轮实际结果

| 范围 | 已完成及证据 | 严格边界 |
| --- | --- | --- |
| 10类主要制品 | Python3.10.22对应现有Conda构建、Node22.21.1、PG16.15源包、RabbitMQ4.3.6、OTP27.3.4.18源包、SeaweedFS4.48、Keycloak26.8.1、Temurin21.0.12.1+1、Nginx1.30.6源包、age1.3.2，见[实际核验](../00-project/validation/native-primary-artifact-verification-report.json) | 下载与核验不等于安装；三个源包已在私有目录编译及特性探测通过，见本页补充复核入口。Python环境未重建，原100包锁未改 |
| Nginx签名 | [OpenPGP核验](../00-project/validation/native-nginx-signature-report.json)，官方签名、公钥及包摘要绑定；隔离临时钥匙环，不自动联网取钥 | 固定官方签名人指纹；错误、过期、撤销签名拒绝。无系统钥匙环修改 |
| 构建包候选 | 官方Ubuntu三套InRelease及对应Packages摘要，经服务器gpgv和私有APT索引验证。求解新增40包、升级0、删除0，40包字节、版本、架构及控制字段全部核对，见[依赖包验证](../00-project/validation/native-build-package-verification-report.json) | 只覆盖本次新增候选包，不证明服务器所有现有运行依赖的完整闭包或全部许可/漏洞准入；模拟不能代替安装前复检 |
| 已有运行依赖 | [25个Conda包元数据及现有Python/PG/Node动态链接](../00-project/validation/native-runtime-dependency-inventory-report.json)已盘点，未见探测对象缺失共享库 | 元数据和少量入口探针不证明全环境文件完整性；完整闭包仍待核验 |
| 原生二进制探测 | Node、Java和age仅解压到私有探测目录，版本检查通过；[自建夹具age加密/恢复](../00-project/validation/native-binary-probe-report.json)字节一致，临时测试密钥已销毁 | 无服务监听、无系统安装；不是N03全栈验收，也不是正式备份能力 |

制品及包缓存均在服务器私有运行目录，二进制、索引和数据没有加入Git。仓库只保存锁、摘要、工具、测试与脱敏证据。旧三份发行包记录保留原时间与适用范围。

## 来源和核验方法

官方来源：[Node固定版本目录](https://nodejs.org/dist/v22.21.1/)、[PG16.15](https://ftp.postgresql.org/pub/source/v16.15/)、[OTP精确发行](https://github.com/erlang/otp/releases/tag/OTP-27.3.4.18)、[Temurin精确发行](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.12.1%2B1)、[age1.3.2](https://github.com/FiloSottile/age/releases/tag/v1.3.2)、[Nginx下载](https://nginx.org/en/download.html)、[官方签名公钥入口](https://nginx.org/en/pgp_keys.html)、[Conda-forge Python3.10.22元数据](https://api.anaconda.org/release/conda-forge/python/3.10.22)。精确下载URL、文件大小与SHA-256以锁和实际报告为准；不以latest作为安装输入。

服务器直连Ubuntu官方HTTPS时证书验证失败；HTTP尝试也被APT拒绝。没有关闭TLS校验、允许不安全仓库或修改系统源。改从Windows经HTTPS获取Ubuntu官方InRelease及其绑定的Packages.xz，传到私有目录，由服务器Ubuntu archive keyring执行gpgv，再通过私有file源进行APT签名、有效期和依赖求解。40个deb的SHA-256来自已验签索引，分别在本地和Linux复算，随后使用`dpkg-deb --field`核对包名、版本和架构。

主要制品可复核：

```bash
/opt/conda/glwy/envs/py310/bin/python scripts/native/artifacts.py verify \
  --lock config/native/artifacts.lock.json \
  --root /workspace/glwy/runtime/media-traceability-system/native-artifacts
```

该命令的PASS仅表示声明范围内的包字节和来源匹配；返回字段`installation_ready=false`及`complete_os_dependency_and_signature_admission_asserted=false`保持。不得据status单字段自动开始安装。

Ubuntu验签可对私有目录内三套`repository/dists/<suite>/InRelease`分别执行`gpgv --keyring /usr/share/keyrings/ubuntu-archive-keyring.gpg <InRelease>`；包文件需逐一对照构建候选锁复算SHA-256和大小，不能仅相信文件名。管理员执行前必须重新核对当前系统状态及模拟变更集合。

## 尚需关闭的工作

1. 完整核对现有Conda/pip及OS运行与构建依赖，包括文件来源、实际共享库、构建配置、原生软件编译产物及版本探针。本批已取得25份Conda包及95份wheel，限定依赖核验见补充复核；完整宿主依赖与恢复路径仍未关闭。
2. 三份源码构建与配置探测已执行；后续服务运行、回归与恢复仍需验证。PG的TLS/ICU/readline、OTP的crypto/ssl、Nginx的TLS/代理模块不能因缺库而静默关闭。实际源码编译和特性探测结果见补充复核，不能据此判服务运行验收。
3. 完成捆绑许可、漏洞及适用软件准入审查。锁中license字段主要标识上游核心许可，不替代全部捆绑组件检查。
4. 由徐昌胜执行经核对的管理员初始化；当前缺少GCC、G++、make、pkg-config及开发头文件。**本页不是安装授权包，不应直接执行未锁版本的apt install或dpkg -i通配符。**精确管理员执行工具须先验证当前状态、全部包摘要、无额外升级/删除和恢复边界，再交接。
5. 用户确认备份由徐昌胜保管、age公钥尚未建立。正式公钥应由保管人在受控环境建立并落实私钥备份/恢复方式，只向项目提供公钥及其服务器文件路径，不向会话提供私钥。本项阻止N04正式备份交付，不影响已完成的包字节核验；临时夹具密钥不可代用。

N02—N08仍按原实施计划逐项执行，未因这批证据自动关闭。T001—T012继续保持按源标准逐项核验与实际复核要求，不能由T004两项新增开发子步骤推导整任务完成。

本轮校验工具源码`259707e23df5345a6e61a361d184e88584847c31`已在Linux py310执行45项原生专项测试，失败/错误/跳过均为0，lint/类型/格式检查通过，见[专项报告](../00-project/validation/native-n01-round2-runtime-report.json)。主要制品报告绑定实际校验器源码和输入锁SHA-256；独立审计报告明确区分当时仓库上下文与临时审计脚本的SHA-256，不借用旧32项或539项回归证明新增代码。

[许可材料盘点](../00-project/validation/native-license-materials-round2-report.json)已从主要归档记录257份许可/声明材料；40个构建包中15个记录到常规copyright文件，其余不能据此判无许可，还须追踪共享版权文件、Conda格式及嵌套JAR/Go依赖。该结果仅为材料清单，不是语义审查或准入通过。补充资料已在Linux执行[输入与导航检查](../00-project/validation/native-n01-round2-documentation-report.json)，11项/335夹具、第一阶段12项及10,245处链接通过。

## 后续实际复核

[源码构建、运行依赖和准入复核](native-n01-build-and-admission-review.md)记录三份源码构建、95份wheel/25份Conda、403个ELF解析、捆绑许可及漏洞匹配与候选修补；准入未通过，N01继续进行。此处状态更新优先于上文历史批次说明。
