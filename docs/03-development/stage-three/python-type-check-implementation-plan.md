# Python静态类型检查 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变原py310运行锁的情况下加入可阻断真实类型错误的Python检查。

**Architecture:** 新建仓库外的独立类型工具环境和单独精确锁，读取原环境依赖供解析但不写入原环境。统一入口调用mypy，真实错误清单与明确的第三方缺失stub边界分别记录，再加入CI。

**Tech Stack:** Python 3.10.22；候选mypy==2.4.0；现有Ruff、Pytest和GitHub Actions保持。

**Spec:** [开发环境变更和恢复要求](../development-environment-change-request.md)；[总体实施顺序](foundation-implementation-plan.md)。设计范围已认可，本详细计划待审阅。

## Global Constraints

- 原`config/locks/requirements-py310.lock`100包及12包pre-commit质量锁不改；类型工具另锁，不写成已安装。
- 项目Python仍为3.10.22，mypy配置python_version="3.10"；不使用桌面辅助Python代替实际项目执行。
- 禁止全局ignore_errors、全局ignore_missing_imports、排除报错文件或无错误代码的type: ignore来换取通过。
- 本批不改变业务行为、模型/镜像版本、生产Python决定或正式冻结。

## Review Focus

- 依赖制品损坏：安装前摘要校验失败必须中止（任务1）。
- 工具误装到原环境：原100包锁/实际包集合前后保持（任务1）。
- 第三方动态返回值：仅对应库采用局部Protocol/类型边界，不扩大Any到业务路径（任务2）。
- 新目录漏检：入口覆盖既有范围并自动包含新业务目录（任务2、3）。
- 检查伪通过：故意的类型错误必须令本机及CI步骤失败（任务3）。

## 文件与接口

| 文件 | 职责 |
| --- | --- |
| 新建config/mypy.ini | 文件范围、Python版本、错误代码、第三方局部配置 |
| 新建config/locks/requirements-stage-three-types.lock | 仅类型环境的完整精确依赖及hash |
| 新建config/locks/stage-three-type-artifacts.json | 对应版本、wheel URL/文件/平台/hash及解析报告摘要 |
| 新建scripts/stage_three_types.py | 安装目标保护、摘要验证、检查及失败探针 |
| 修改scripts/dev.py、Makefile、scripts/dev.ps1 | 接入统一type-check，默认仍经Linux实际py310执行 |
| 修改backend/app、ai-services/inference及现有检查范围 | 修正真实类型/注解问题，单独审核行为差异 |
| 修改.github/workflows/ci.yml | 必需Python类型步骤和脱敏报告制品 |
| 修改docs/03-development/coding-standards.md及第三阶段状态 | 如实记录范围、局部例外和实测 |

`scripts/stage_three_types.py`产出`verify_artifacts(lock_path: Path, artifacts_path: Path) -> None`、`setup_type_environment(runtime_dir: Path, base_python: Path) -> Path`（返回专属Python路径）、`run_type_check(tool_python: Path, root: Path) -> subprocess.CompletedProcess[str]`；错误返回非零。CLI为`setup`、`check`、`failure-probe`，失败探针只在仓库外临时目录运行。

### Task 1: 可复建的独立工具锁与环境

**Files:** 创建上述两个锁/制品文件和scripts/stage_three_types.py；测试`tests/stage_three/test_types.py`；安装目标`$MT_RUNTIME_DIR/stage-three-type-tools`。

**Interfaces:** 输入原py310解释器及实际解析报告；输出专属工具Python和完整制品锁，供任务2、3消费。

- [x] **Step 1: 编写失败测试。** `test_bad_artifact_digest_rejected`修改临时wheel的一个字节，断言verify_artifacts抛出校验异常且无安装动作；`test_runtime_target_inside_repo_rejected`断言repo内/符号链接目标被拒绝，原环境包集合不变。
- [x] **Step 2:** 运行`python -m pytest tests/stage_three/test_types.py -k 'artifact or target' -q`，确认失败源于功能尚不存在。
- [x] **Step 3:** 用实际py310对mypy==2.4.0做`pip download`/解析报告，记录完整传递闭包后生成精确hash锁；再实现verify_artifacts和setup_type_environment，只允许仓库外目标。使用`--require-hashes --no-deps`从完整锁安装；不忽略解析依赖，也不把计划中的主包hash当作完整闭包。
- [x] **Step 4:** 重跑上述测试，并实际冷建工具环境、核对mypy版本及原100包集合/锁摘要保持；输出脱敏`stage-three-python-types-report.json`。版本/下载/安装失败则本任务失败。
- [x] **Step 5:** 提交锁、制品来源及安装保护；不提交环境目录、wheel或凭据。

候选官方cp310 Linux wheel SHA-256：`13fa24f439c0e48a290a3922fa14ccd22f2762bae99d2142931b3e40a9055080`。版本依赖Python>=3.10，见[mypy官方发行信息](https://pypi.org/project/mypy/2.4.0/)；该hash仅对应主wheel，不能用于其他平台或传递包。候选版本仍需实际解析、安装与检查后定为本批执行版本。

### Task 2: 明确范围并治理真实错误

**Files:** 创建config/mypy.ini；修改现有profile、范围内Python文件和coding-standards；报告中保存错误数量/范围，原始输出置仓库外。

**Interfaces:** 消费任务1返回的tool_python；实现run_type_check。初始范围为backend/app、ai-services/inference、tests/poc，以及profile中7个原新增Python入口/测试；新backend/business_app、tests/business、业务迁移Python入口存在后必须包含。

- [x] **Step 1:** 写`test_type_error_returns_nonzero`：临时模块内容`value: int = "wrong"`，调用run_type_check，断言returncode非零且输出含`assignment`；写`test_new_business_directory_included`核对临时business_app中的同类错误也被检测。
- [x] **Step 2:** 运行对应测试，确认FAIL，随后对真实初始范围执行mypy，保存未经删改的错误清单。
- [x] **Step 3:** 配置show_error_codes、check_untyped_defs、warn_unused_ignores、no_implicit_optional、disallow_any_generics。逐文件补返回/参数/空值类型，明确Celery/boto3等第三方边界；局部缺stub必须记录模块与原因，不能全局忽略。新business_app在该基线之上开启disallow_untyped_defs和warn_return_any。
- [x] **Step 4:** 跑范围检查及现有45个Python单元、PoC集成和契约检查；注解改动以外的行为修正单独记录并测试，不再宣称AST保持的纯格式修改。
- [x] **Step 5:** 提交具体类型治理和边界记录；仅修完当前范围才更新Python类型状态，不称全仓所有历史脚本已治理。

### Task 3: 统一入口和CI阻断

**Files:** 修改scripts/dev.py、Makefile、scripts/dev.ps1、.github/workflows/ci.yml；补tests/stage_three/test_types.py及报告/状态。

**Interfaces:** 统一`python scripts/dev.py type-check`调用任务2检查；工具异常/类型错误都返回非零。CI单独步骤名`Python static type check`，制品记录工具/锁/范围/source SHA。

- [x] **Step 1:** 编写`test_type_failure_propagates_to_dev_command`，给真实检查插入受控临时错误，断言统一入口失败；临时文件在finally清除，不改已有源码/锁。
- [x] **Step 2:** 跑入口测试确认FAIL，再实现入口和CI步骤，不使用`continue-on-error`。
- [x] **Step 3:** 在实际Linuxpy310跑正常检查及failure-probe，分别确认0与非0；前端类型检查继续保留。
- [x] **Step 4:** 当前源码提交的GitHub正常步骤实际通过；在测试分支运行受控失败探针，确认失败能阻断检查。只有平台保护具备并回读成功后才称为合并门禁。
- [x] **Step 5:** 按总体计划任务5更新报告/导航和同步，报告区分Python检查通过与私有分支保护尚不可用。

## 自检与实施边界

所有接口签名均在本计划定义；制品损坏、安装隔离、缺stub、新目录及失败传播有具体检查。尚未生成候选依赖闭包、未安装mypy、未修类型错误、未接入CI。不得仅凭主包兼容说明关闭质量任务。

## 用户审阅决定

2026-10-14：用户明确回复“认可计划，由当前会话直接逐项实施（推荐）”。详细计划已认可，按当前会话直接实施；正文中的“待审阅”为编制时状态，具体完成情况仍按实测台账判定。此决定不批准共享引擎停机或正式生产冻结。

当前实测：独立12包工具锁，原100包锁保留；类型范围含独立业务包/迁移/测试，数量和源码身份以类型报告为准。此前22源文件为早期批次结果。
