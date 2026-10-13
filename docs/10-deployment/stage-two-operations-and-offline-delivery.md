# 第二阶段容量、软件物料与离线交付操作

2026-10-13。当前7服务运行；现有py310保持。实际容量和软件记录见[资源快照](../00-project/validation/resource-readiness-snapshot.json)、[容量判定](../00-project/validation/stage-two-resource-report.json)和[镜像物料](../00-project/validation/stage-two-software-report.json)。

## 容量处理

本轮数据卷所在Docker虚拟机文件系统可用约1.63GiB、df使用率99%，候选策略判CRITICAL/NOT_READY。宿主/workspace另有大量空间，不能直接当虚拟机卷余量。85%预警、95%严重或不足5GiB是研发候选阈值，不是正式生产指标；[配置](../../config/stage-two-operations.candidate.json)可在实测容量规划后改版。

```sh
PY=/opt/conda/glwy/envs/py310/bin/python
$PY scripts/collect_readiness_resources.py
$PY scripts/stage_two_readiness.py
```

正式开始大体积构建前可加`--require-capacity`，当快照为CRITICAL时返回非零；必须先刷新快照，本轮服务器实际容量未通过。

必须先采集再判定，报告标明快照时点；它不是已安装的持续监控。下一步由实际运维选择Docker Desktop虚拟机盘扩容或批准迁移目标，先核验整盘备份与全部服务/其他项目占用，再按当前Desktop支持的操作处理；[Docker官方资源设置说明](https://docs.docker.com/desktop/settings-and-maintenance/settings/)为操作依据。迁移后在PostgreSQL容器内重新df，并复验对象VersionId、SQL结果/审计、模型权重和7服务健康。没有批准配额/目标时不删除其他项目或未核验镜像/卷，也不将宿主free数写成项目独占容量。

## 物料和许可

[image-sbom.spdx.json](../00-project/validation/image-sbom.spdx.json)按实际运行容器去重5镜像，含449条镜像/已安装OS包物料。每个OS包记录名称/版本/架构、未知许可NOASSERTION；镜像本地ID与仓库RepoDigests分别保存。web运行容器关联的旧镜像当前无法在引擎镜像目录inspect，此事实不代表容器停止；直接离线save该ID前必须补齐实际镜像制品。

SPDX物料不是漏洞扫描或许可决定，格式参考[SPDX2.3规范](https://spdx.github.io/spdx-spec/v2.3/)。Python/Conda/npm沿用各锁和物料；FFmpeg静态二进制、未托管编译库、业务模型/驱动不在OS包清单中自动完备。需补匹配二进制源码/构建参数、实际LICENSE/NOTICE和再分发决定，保留torch CPU审计被跳过事项，不能写全栈无漏洞。详见[许可盘点](../02-architecture/licenses.md)。

## 离线交付步骤

1. 在容量充足且受控的构建主机按精确锁复建环境/镜像，执行全部25工程门禁；保留测试源码SHA和实际报告。CI托管工作区不能代替正式生产仓库。
2. 收集源码快照、Conda包/pip wheel和npm缓存、py310归档、5个实际镜像导出、对应权重/用途许可/源码notices和SBOM。每件记录相对路径、字节数、SHA-256、来源版本/摘要；镜像打包先核验可inspect且镜像内容匹配本次通过CI的源码。现阶段源码可交付，全部依赖和镜像包尚未实际齐备。
3. 对象原件/业务数据库和密钥不混入软件交付；凭据使用独立授权的密钥恢复/注入流程。未知模型许可不把权重塞入离线包。
4. 从可信CI记录或受控签名通道取得摘要清单，运行以下检查；篡改/缺失/重复/路径越界/空清单全部拒绝。摘要和包若同时可被篡改，SHA-256不能独自证明来源；正式签名/密钥管理待接入。
5. 无外网的隔离验收环境导入经过验证的制品，先dry-run解析配置，再启动/健康/集成/故障/恢复检查，记录实际结果。输入/环境缺失时不记离线复建PASS。

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/stage_two_readiness.py \
  --offline-manifest /approved/delivery-manifest.json --artifact-root /approved/artifacts
```

manifest须含artifacts数组，每条path/size_bytes/sha256均为真实值。仓库中未知正式地址仍为null，不能复制示意路径就视为已建立镜像库。源码交付的实际摘要记录放validation，完整镜像/依赖复建另记。

## 托管治理

当前Actions已实际运行；main protected=false和rulesets查询403按[观测记录](../00-project/validation/repository-governance-snapshot.json)读取，403不等于规则不存在。建议必须检查为工作流实际engineering job（配置前核对GitHubCheck名称）；保护主分支、PR评审、禁止force-push/删除和管理员绕过范围，均由正式治理记录明确。私有仓库的保护功能受套餐影响，依据[GitHub官方说明](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)。未提供实际套餐/管理员决议时不伪造保护已启用。当前制品14天保留不是正式备份或长期留档；正式镜像库、签名/离线保留与访问范围仍需落实。

可直接评审的设置体见[github-branch-protection.candidate.json](../../config/github-branch-protection.candidate.json)：严格检查、1人PR评审、旧评审失效、管理员约束、禁止强推/删分支。approved=false；未调用平台更新，实际套餐/管理员与适用决议仍需填入。
