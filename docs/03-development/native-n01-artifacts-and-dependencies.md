# N01原生制品及依赖核验

2026-10-17，适用Linux / Miniforge py310 / CPU研发。**主要制品字节核验通过，N01整体仍在进行；不允许据此安装或切换服务。**

[执行台账](native-linux-execution-status.json) · [制品锁](../../config/native/artifacts.lock.json) · [构建依赖候选锁](../../config/native/os-build-dependencies.lock.json) · [T004任务卡](../../tasks/platform/T004.md)

## 本轮实际结果

| 范围 | 已完成及证据 | 严格边界 |
| --- | --- | --- |
| 10类主要制品 | Python3.10.22对应现有Conda构建、Node22.21.1、PG16.15源包、RabbitMQ4.3.6、OTP27.3.4.18源包、SeaweedFS4.48、Keycloak26.8.1、Temurin21.0.12.1+1、Nginx1.30.6源包、age1.3.2，见[实际核验](../00-project/validation/native-primary-artifact-verification-report.json) | 下载与核验不等于安装；三个源包尚未编译。Python环境未重建，原100包锁未改 |
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

1. 完整核对现有Conda/pip及OS运行与构建依赖，包括文件来源、实际共享库、构建配置、原生软件编译产物及版本探针。当前25份Conda元数据不是完整恢复包。
2. 完成三份源码发行包的构建条件与配置核对；PG的TLS/ICU/readline、OTP的crypto/ssl、Nginx的TLS/代理模块不能因缺库而静默关闭。实际编译和运行验证另留证据。
3. 完成捆绑许可、漏洞及适用软件准入审查。锁中license字段主要标识上游核心许可，不替代全部捆绑组件检查。
4. 由徐昌胜执行经核对的管理员初始化；当前缺少GCC、G++、make、pkg-config及开发头文件。**本页不是安装授权包，不应直接执行未锁版本的apt install或dpkg -i通配符。**精确管理员执行工具须先验证当前状态、全部包摘要、无额外升级/删除和恢复边界，再交接。
5. 用户确认备份由徐昌胜保管、age公钥尚未建立。正式公钥应由保管人在受控环境建立并落实私钥备份/恢复方式，只向项目提供公钥及其服务器文件路径，不向会话提供私钥。本项阻止N04正式备份交付，不影响已完成的包字节核验；临时夹具密钥不可代用。

N02—N08仍按原实施计划逐项执行，未因这批证据自动关闭。T001—T012继续保持按源标准逐项核验与实际复核要求，不能由T004两项新增开发子步骤推导整任务完成。

本轮校验工具源码`259707e23df5345a6e61a361d184e88584847c31`已在Linux py310执行45项原生专项测试，失败/错误/跳过均为0，lint/类型/格式检查通过，见[专项报告](../00-project/validation/native-n01-round2-runtime-report.json)。主要制品报告绑定实际校验器源码和输入锁SHA-256；独立审计报告明确区分当时仓库上下文与临时审计脚本的SHA-256，不借用旧32项或539项回归证明新增代码。
