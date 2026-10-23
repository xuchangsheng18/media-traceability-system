# Pillow／py310隔离实施回执与构建前缺口

2026-10-21；D05-E已获用户确认，仅实施独立目录内的PL01—PL05。**当前完成源码层回移与静态核验；PL02未通过，PL03—PL05按批准的前置条件停止，8条漏洞均未关闭。**

[批准计划](pillow-py310-remediation-plan.md) · [逐项机器证据](../00-project/validation/t016-pillow-py310-isolated-execution.json) · [T016任务卡](../../tasks/platform/T016.md)

## 1. 实际状态

| 步骤 | 实际操作与结果 | 不能据此声称 |
| --- | --- | --- |
| PL01 | 官方12.3.0源码归档47,025,035字节、1723文件；11项修复移植到13个私有文件，保留12个上游测试定义。Linux py310下68项静态检查、9项前置/完整性变异检查通过。 | 未编译C扩展，未运行上游安全测试；不证明实际漏洞修复有效。 |
| PL02 | 盘点工具、native来源/头文件/许可，保留6份源码及通知材料；12项输入检查单元测试从11失败变为全通过。真实输入检查拒绝13项条件。 | 单元测试通过只证明检查器能拒绝缺项；完整输入闭包仍未通过。 |
| PL03 | 未执行；没有构建/安装wheel，没有创建site候选。 | 不能标cp310 ABI、重建或SBOM通过。 |
| PL04 | 未执行；没有解析漏洞图片/PDF/GIF/EPS，没有运行CVE样例。 | 9项源码检查器测试和12项输入检查器测试不是8族漏洞回归。 |
| PL05 | 未执行；没有绑定API/worker/推理或镜像的Pillow候选。 | 未完成真实项目联调、当前锁扫描修复或整体CI。 |
| PL06 | 采用、共享环境/锁/镜像更改仍未批准。 | 既有隔离授权不等于正式准入或N01整体批准。 |

T016仍4条已验证业务子步骤、4组剩余；170任务仍110条已验证子步骤、622条剩余、0项整卡验收。本批没有新增业务完成数量。

## 2. 八条漏洞的当前处理层次

| 漏洞 | 源码状态 | 实际运行与采用 |
| --- | --- | --- |
| CVE-2026-112895 / GHSA-p4wg-p73j-c528 | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |
| CVE-2026-112400 / GHSA-65qm-jvmh-6pqg | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |
| CVE-2026-112397 / GHSA-58r4-6rv3-gfh8 | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |
| CVE-2026-112896 / GHSA-pchr-8j38-3x4p | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |
| CVE-2026-112897 / GHSA-q45j-58j2-45rg | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |
| CVE-2026-112395 / GHSA-462x-pgg6-55fp | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |
| CVE-2026-112404 / GHSA-c6hw-5grf-ff96 | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |
| CVE-2026-112899 / GHSA-vx6w-vv9f-6gvg | 必要修复已移植，静态核对 | 未构建、未执行漏洞回归、未采用、未关闭 |

原100包锁与版本文件未改；certifi候选此前隔离通过但未采用，因此已完成的原锁扫描仍保留certifi 1＋Pillow 8。Pillow私有回移不能使默认按PyPI版本匹配的原CI自动认可；未知版本skip不算修复通过。Torch旧skip和N01原CPython 9条另列，Python候选继续暂缓。

## 3. 移植差异与来源

PDF旧测试文件没有较新上游测试的上下文；未模糊强套测试hunk，而是保留失败dry-run，并按精确提交/函数名移植12个完整测试定义及装饰器。补充旧模块缺少的BytesIO、assert_image_equal导入；静态未定义名称检查通过，测试定义尚未执行。

TIFF两项修复（1d4773、76869ef）的上游父文件已去掉部分TRACE行，而12.3.0仍保留。记录原dry-run失败后，生成两份有hash的本地上下文patch：前者保持realloc→清零扩容差值→更新长度，并将TRACE保留在长度提交后；后者在TIFFRGBAImageOK/Begin之前检查bits!=32，保留原TRACE及tile行宽守卫。未以整份13.0.0模块覆盖旧模块。两份派生patch和13个文件的原/新hash保存在私有manifest。

缺PDF visited、缺ColorMap类型纠偏、缺TIFF行宽守卫的三个静态变异均被拒绝；另补6项完整性反例，覆盖未列源码改变/删除/新增、派生patch、测试来源及QA源码摘要。9项源码检查器测试及12项输入检查器测试均通过，只证明检查器对这些缺项敏感。独立复核发现完整性检查最初只覆盖13个变更文件；已用6失败RED和全套GREEN补齐原1723/派生1724文件集合与摘要。Windows测试导入/CRLF差异、Linux派生patch路径的Windows反斜杠问题也已修正并保留原失败记录；68项最终Linux静态检查通过，patch字节与预期hash未改变。

新增TIFF夹具仅取得不可变提交来源及SHA-256 `4eb2d302c93f4ca3c67e3b9dea1ec54b1da618b4a4669acc207270a4d14e0139`，并核对Git blob前缀；未执行、未发布其字节，其许可用途仍待复核。

## 4. 为什么现在没有进入构建

以下都是当前实际缺项，不是用户尚未批准PL01—PL05：

1. 独立构建工具未闭合。pybind11精确元数据已找到，制品未取得/核验；共享site-packages并存setuptools 44.1.1/84.0.0元数据，默认解析44.1.1。后续只能在独立工具层解决，不能清理共享环境。
2. 与现有功能匹配的TIFF/JPEG/WebP/OpenJPEG/FreeType/LCMS/AVIF等开发头、源码、补丁及实际链接提供者未闭合；libavif还有AOM/dav1d/libyuv/sharpyuv和meson/ninja等传递输入。41个既有缓存制品hash及固定Git提交索引可复用，不能替代完整归档来源。
3. 完整嵌套许可及夹具用途未闭合。已保留Pillow LICENSE、raqm COPYING/AUTHORS、FriBiDi shim两文件、pythoncapi_compat源码；SBOM声明与shim独立通知/实际linkage仍须核对。保留材料不等于许可复核或外发批准。
4. 原生诊断器尚未完整验证。越界和未初始化读需不同诊断能力，不能用ASan替代全部MSan/Valgrind要求。
5. 功能隔离探针失败。临时用户unit请求1核/128MiB/32任务/15秒，bwrap请求PID/网络等namespace、只读根及16MiB私有临时盘；在执行内部断言前报`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`。请求值不等于已验证硬限额，故没有运行安全样例，也不删除网络隔离来获取通过。

## 5. 管理员需要做什么

glwy已读到同刻AppArmor `userns_create`由unconfined转换至unprivileged_userns的AUDIT事件；磁盘上的对应profile含`audit deny capability`。这提示核查方向，但不证明已加载策略模式或具体RTM拒绝规则。`aa-status`返回4、提示权限不足，虚拟化探测返回none。徐昌胜需以管理员身份先补加载状态及拒绝规则的只读诊断。以下为**只读诊断**，不是要求安装、关闭AppArmor或放宽共享服务策略：

```bash
sudo journalctl -k --no-pager --since '2026-10-21 03:19:00 UTC' --until '2026-10-21 03:21:00 UTC' --grep 'apparmor|DENIED|userns|bwrap|RTM_NEWADDR'
sudo aa-status
systemd-detect-virt
systemctl --user show --property=ControlGroup --property=Delegate --property=DelegateControllers
```

在glwy用户登录会话中执行最后一条，不用sudo切换用户manager。请提供相关诊断文字或服务器上的结果文件路径，不发送密码、密钥或Token。管理员日志若已轮转/不存在则明确写无日志，不编造拒绝原因。仅需提供bwrap／unprivileged_userns相关的加载与模式信息及对应拒绝记录；不用公开其他应用配置。当前仍未定位到具体AppArmor／Seccomp拒绝规则，不能用磁盘profile或一条AUDIT事件替代已加载策略/明确拒绝的证明。

取得依据后再选择专用受限runner的最小权限方案或独立隔离节点，并重新验证实际cpu.max/memory.max/pids.max、namespace和私有临时盘。任何需管理员修改系统策略的动作先给精确清单；不要全局关闭保护，不要以sudo直接运行漏洞夹具。其余构建输入、许可和工具闭包由后续隔离工作继续核对，无需重新批准同一PL01—PL05范围。

## 6. 保存位置与未变范围

- 本地私有资料：`D:\公安厅项目\_work\pillow-py310-isolated-20261021-9c4f20af`。
- Linux私有资料：`/workspace/glwy/runtime/media-traceability-system/pillow-py310-isolated-20261021-9c4f20af`。
- 原始下载、patch、派生源码、未执行夹具及日志只保留在上述私有目录；本仓库公开归一化说明和hash，不公开原始CVE样例/差分归档。
- Linux核对239个PIL/pillow.libs/pillow dist-info文件的路径、大小与hash前后一致；原锁、版本和CI关键文件hash一致，源码状态保持。这个结论不扩张为整个site-packages的全量取证。
- 没有改共享Python包、原100包锁、CI门禁、数据库、服务或Python候选；没有main合并、正式采用或N01整体准入。

本批CI观察及实际源码同步仍按进度记录中的精确SHA/run判定；源码同步不等于服务采用。
