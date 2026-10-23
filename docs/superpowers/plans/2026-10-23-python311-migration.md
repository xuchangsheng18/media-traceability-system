# Python 3.11 全项目迁移与 CI 修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前工程活动基线由Python3.10.22迁移至3.11.17，采用Pillow13.0.0和certifi2026.10.19，真实验证并修复CI安全失败。

**Architecture:** 保留旧py310、原100包锁和既有快照作为回退证据；新建明确的py311环境、依赖/Conda/制品锁及归档。统一更换活动入口和CI解释器，沿用所有现有业务、权限、身份、扫描、失败探针与普通PR门禁；历史材料和数据库持久卷标识保留原身份。

**Tech Stack:** Linux x86_64 / Miniforge Python3.11.17 / CPU；原包名集合为基线，Pillow13.0.0、certifi2026.10.19；Node/数据库/队列/对象存储版本沿用。

**Spec:** 2026-10-23用户新授权“整个项目直接替换更加合适的python>=3.11版本，并对应修复问题”，覆盖此前py310/原锁不变及Python候选暂缓在本次迁移中的限制。具体依据见 `docs/00-project/validation/python311-migration-authorization-20261023.json`；此前CI失败及私有36条处置矩阵保留。

## Global Constraints

- 新活动目标精确为3.11.17；旧py310目录及 `config/locks/requirements-py310.lock`、原Conda显式锁保留原字节。新活动锁为 `requirements-py311.lock` 和 `conda-linux-64-py311.explicit.txt`。
- 不修改业务公共接口、权限规则或数据库结构；不删除测试、降低断言、增加skip、放宽扫描或伪造包版本。
- 保留170项任务及全部原依赖；算法、模型/训练和效果评测仍暂缓。Windows不做Python业务验证，Linux数据库回归串行且只用随机隔离库。
- 保留数据库卷、服务器IDE文件及未提交内容，不重置、清空或迁移共享数据库。项目开发环境的可回退迁移按新授权执行；生产发布及无关服务不在范围。
- 源PR当前8c42c0e5在途检查结束前不推送新head；新head完整门禁全部成功后才能绑定SHA普通合并PR2，不绕过main规则。

## Review Focus

- ABI：全部原包在cp311的真实制品可用性、Torch CPU/NumPy/Pillow及类型工具的实际导入与链接；不重贴cp310标签。
- 回退：旧环境、旧锁和历史制品未被覆盖，部署项目/持久卷旧名字不是活动Python版本。
- 一致性：CI、包元数据、类型/格式配置、启动脚本、Docker打包与运行锁均使用同一活动基线，验证器继续精确拒绝漂移。
- 来源：每个新增制品来自官方源，记录精确URL/大小/摘要/许可，下载与磁盘有预算；扫描结果对应实际活动锁。
- 身份/权限：迁移不创造采用、许可、分类或代际事实；缺提供方仍拒绝，真实业务验收与工程CI分开。

## Task 1：建立新环境与闭合修订锁

Files：创建 `config/locks/requirements-py311.lock`、`config/locks/conda-linux-64-py311.explicit.txt`；更新类型工具制品锁/哈希；保存迁移实测回执。

- [x] 核验既有Miniforge安装器固定SHA及Linux磁盘空间，新建仓库外迁移目录和 `/opt/conda/glwy/envs/py311`，不覆盖旧prefix。
- [x] 原100包名集合保持，先仅调整Pillow13.0.0和certifi2026.10.19；执行实际解析/下载/安装及 `pip check`。如cp311存在必须调整的传递约束，在执行记录逐项列依据和差异，不偷偷漂移。
- [x] 核验官方制品摘要/许可并生成真实Conda显式锁、制品清单；更新cp311类型工具wheel哈希并放入独立工具目录。
- [x] 新解释器下运行原精确运行时断言观察RED，随后把断言改为新活动基线；执行完整包集合/补丁版本检查，未闭合不得进入部署打包。

## Task 2：统一活动入口、校验器与 CI

Files：`config/versions.yaml`、`config/stage-three-profile.json`、`.python-version`、`backend/pyproject.toml`、`ruff.toml`、`config/mypy.ini`、`.github/workflows/ci.yml`、`identity.yml`、`scripts/dev.py`、`dev.ps1`、`run_ci.py`、`poc_control.py`、`stage_three_quality.py`、`stage_three_types.py`、`verify_runtime_lock.py`及实际依赖它们的身份/权限/运行探针；新增 `deploy/Dockerfile.py311` 并接线现有compose。

- [x] 按实际调用列举所有活动py310路径/版本断言，逐一迁移为py311；旧历史、原锁和持久卷身份不做全局文本替换。
- [x] 原测试在新环境先实际失败，再更新精确目标与必要API兼容实现；保持原错误、鉴权、越权、撤销和故障断言。
- [x] 活动扫描改读新锁，保留原相同扫描算法/阈值及失败语义；目标为真实无已知阻断匹配，未知包覆盖限制照实记录。
- [ ] 使用新归档打包并验证实际容器解释器、业务入口及回退路径，既有共享栈不因源码同步自动重启。

## Task 3：全量验证、文档和三端同步

Files：运行基线/开发说明、相关生成器、阶段台账、任务T004/T006/T016、总导航及实测报告；自动任务说明同步新授权。

- [ ] Linux执行新基线的Ruff/格式/类型、输入/契约、单元、完整业务、完整权限/身份、上传到资产浏览器、构建/集成、原故意失败探针及安全扫描；数据库套件串行，未受影响检查不无故重复。
- [x] 一次新鲜整批源码审查，重要问题只作一次有RED/GREEN的修复轮；未验证与失败保留。
- [x] 更新当前活动文档/生成器和任务导航，旧原件、旧报告及正式生产未验条件保留；生成/漂移/链接及当前输入快照验证。
- [ ] 在途旧CI结束后提交推送既有开发分支，核验新head CI；Linux源码无冲突快进，比较全部受版本管理文件摘要。仅全部必需检查通过才普通合并PR2，之后对齐本地主仓库/开发工作区/Linux与GitHub main。

## 执行记录

- 2026-10-23：已收到全项目Python>=3.11迁移授权；以刚核验的3.11.17作为最小必要迁移目标，生产基线仍NOT_FROZEN。
- 已确认 `/workspace` 可用8.8TiB、`/opt`可用9.1TiB，旧py310为3.10.22；现有prefix无可直接调用的conda基础管理器，拟复用已锁Miniforge安装器建立独立管理层。
- 已更新原每小时自动任务的新授权与迁移优先级；仍保留原频率、截止及main门禁，不创建重复任务。

- 2026-10-23实际：新3.11.17/100包精确闭合、100wheel与26Conda官方摘要一致，0已报告扫描匹配（Torch覆盖限制保留）；最终2080项平台/原生回归、302份类型、前端测试/构建及后端wheel/sdist/运行打包通过。审查3项Important及1项经重评级问题已一次修复，新增2项回归RED→GREEN，完整业务/权限与新head CI待提交后执行。
