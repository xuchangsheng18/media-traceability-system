# T034 显式研发配置组件与验证边界

2026-10-23（北京时间）。本批落实 [E04 研发配置设计](t034-internal-development-decisions.md#4-e04建议直接落实的研发配置值)中的纯配置解析、冻结和私有文件读取组件，为 [I01—I05 实施计划](t034-creation-implementation-plan.md)提供后续接线输入。实际结果见[本批验证回执](../00-project/validation/t034-development-configuration-report.json)。

本批新增 `backend/business_app/task_creation_development.py` 和 `tests/business/test_task_creation_development.py`。尚未接入 `BusinessSettings`、应用启动、HTTP guard、SQL事务、处理器或worker；配置中的限额和期限目前是已校验的输入值，不能据此声称对应运行预算、取消、超时或磁盘防线已经执行。没有创建真实采用、ACTIVE映射、权限事实或成功202，也未写共享运行配置、迁移数据库或重启服务。原100包锁和CI门禁保留，算法与Python候选继续暂缓。

本批新增已完成步骤为0：保持154条已验证子步骤、T001—T123剩余434组、全部170任务剩余622组、整任务验收0。E04的整体运行接入及T034剩余依赖仍未完成；纯配置组件通过不能关闭整任务。

## 1. 明确API与失败方式

```python
parse_task_creation_development(
    raw: bytes, *, runtime_profile: str
) -> TaskCreationDevelopmentSettings

load_task_creation_development(
    path: Path, *, runtime_profile: str
) -> TaskCreationDevelopmentSettings
```

两入口均要求调用方显式传入 `runtime_profile`，只接受精确字符串 `development` 或 `test`；`production`、大小写变体、空白和其他类型均拒绝。不读取环境变量或默认配置，不允许JSON覆盖profile。返回冻结的 `TaskCreationDevelopmentSettings`；直接构造和 `dataclasses.replace` 同样执行字段、类型和交叉约束校验。

| 情况 | 对外固定错误 |
| --- | --- |
| 未批准的profile | `ValueError("TASK_CREATION_DEVELOPMENT_PROFILE_NOT_APPROVED")` |
| 非法JSON、字段、数值或配置关系 | `ValueError("TASK_CREATION_DEVELOPMENT_CONFIG_INVALID")` |
| 非法私有文件、路径、平台或读取/关闭异常 | `ValueError("TASK_CREATION_DEVELOPMENT_PRIVATE_FILE_REQUIRED")` |

错误不包含配置正文、路径或底层异常中的私有标记。`raw`必须为精确 `bytes`，长度1—16384字节；JSON必须只有一个根字段 `task_creation_development`，且该对象必须显式提供下例全部字段。拒绝未知字段、重复键、非UTF-8、非有限数值、非法代理字符及过深/非法结构，不进行类型强转。

元数据固定为 `schema_version="1.0.0"` 和 `environment="linux-py310-cpu-internal-rnd"`；`revision`满足 `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`。`allowed_handler_ids`在JSON中必须是无重复非空列表，目前仅允许预留标识 `internal-rnd-original-integrity`，输出冻结为tuple。该标识不触发模块导入、处理器注册、发布、执行或许可采用。

## 2. 24项数值的完整示例

以下是E04研发初始值的完整结构示例，没有私有路径、身份、案件或凭据。它不是已写入共享环境的配置。除 `min_free_space_bytes`外，24项中的其他23项均要求精确正整数且不得超过示例值；`bool`、浮点、数字字符串及null均拒绝。`min_free_space_bytes`要求 `5368709120 <= value <= 2**63-1`，表示至少5GiB的安全余量输入，而不是5GiB的最大允许值。

```json
{
  "task_creation_development": {
    "schema_version": "1.0.0",
    "environment": "linux-py310-cpu-internal-rnd",
    "revision": "e04-v1",
    "allowed_handler_ids": ["internal-rnd-original-integrity"],
    "max_material_bytes": 262144,
    "max_nodes": 16,
    "max_capabilities": 64,
    "max_bundle_bytes": 1048576,
    "max_snapshots_bytes": 4194304,
    "max_http_body_bytes": 16384,
    "proof_budget_seconds": 30,
    "control_ttl_seconds": 86400,
    "adoption_max_seconds": 604800,
    "generation_max_age_seconds": 30,
    "capability_lease_seconds": 60,
    "node_lease_seconds": 60,
    "max_object_bytes": 1048576,
    "handler_deadline_seconds": 10,
    "db_connect_timeout_seconds": 2,
    "db_pool_timeout_seconds": 2,
    "db_statement_timeout_ms": 2000,
    "db_lock_timeout_ms": 1000,
    "create_deadline_seconds": 10,
    "max_concurrent_handlers": 1,
    "prefetch_count": 1,
    "max_task_temp_bytes": 8388608,
    "max_incomplete_temp_tasks": 2,
    "min_free_space_bytes": 5368709120
  }
}
```

字节字段以B计；`db_statement_timeout_ms`和 `db_lock_timeout_ms`以毫秒计，其余期限字段以秒计。节点、能力、并发、prefetch及未完成缓存任务字段为计数。较小值只在同时满足下列关系时接受：

- `max_material_bytes <= max_bundle_bytes <= 4 * max_material_bytes`；`max_material_bytes <= max_snapshots_bytes <= max_nodes * max_material_bytes`。
- `max_http_body_bytes <= max_material_bytes`；`max_object_bytes + max_bundle_bytes + max_snapshots_bytes <= max_task_temp_bytes`。
- `create_deadline_seconds <= proof_budget_seconds`；`handler_deadline_seconds <= node_lease_seconds`。
- DB连接和pool期限各自不超过创建事务期限；`db_lock_timeout_ms <= db_statement_timeout_ms <= 1000 * create_deadline_seconds`。
- `prefetch_count == max_concurrent_handlers`，两者当前上界均为1。

Proof预算、控制回执重试窗口、采用期限、能力证据租约及节点租约具有各自语义，不强加一条共同有效期链。允许较短的独立证据/重试窗口不表示权限、采用或当前能力有效；运行接线仍须读取真实事实，并依据各真实截止决定是否拒绝。

`material_budgets()`返回已有的 `MaterialBudgets(max_bytes, max_nodes, max_capabilities)`，取值分别来自 `max_material_bytes`、`max_nodes`及 `max_capabilities`。本方法仅构造已有预算对象，不执行材料读取或聚合预算检查。

## 3. 冻结、规范字节与profile绑定摘要

`as_dict()`返回独立副本，其根仍为 `task_creation_development`，不包含profile。修改原JSON或导出的dict/list不能改变冻结实例。`canonical_bytes`按以下外层结构进行UTF-8序列化：`sort_keys=True`、紧凑分隔符、`ensure_ascii=False`及 `allow_nan=False`；`sha256`是这些规范字节的SHA-256。

```text
{
  "runtime_profile": <调用方显式profile>,
  "canonicalization_version": "task-creation-development-json-v1",
  "configuration": <as_dict()返回的完整根对象>
}
```

对第2节示例，规范字节与摘要固定如下，缩进或原字段顺序不参与摘要：

| profile | 规范字节数 | SHA-256 |
| --- | --- | --- |
| `development` | 955 | `65e408f67f97e8c93de68b6d095dba7ef5e68dc14bda5070cc5e428e05e2f703` |
| `test` | 948 | `b44c72b7511c41f69869a72fd0cfc7530d7b109e915a1218f557874ffdbaffd8` |

profile、修订或数值变化会改变摘要。该摘要仅标识配置快照，不能代替执行计划、采用收据、许可、真实事实或签名验证的摘要，也未在本批写入任何采用记录。

## 4. Linux私有文件读取边界

loader只允许Linux，要求绝对 `Path`、不得含 `..`，且词法路径和解析路径均不能位于仓库内。它从根目录逐分量以 `O_NOFOLLOW`打开目录和文件，拒绝任何路径分量的符号链接。直接父目录须属于当前UID且无group/other访问位；测试覆盖0700和0500接受、较宽父目录权限拒绝。

末级文件须为当前UID所有的正规文件，精确权限0400或0600、硬链接计数1、大小1—16384字节。读取使用有界循环；比较实际读取长度、文件及直接父目录读前后的设备/inode、UID/GID、mode、链接数、size及mtime/ctime，并复核父目录内末级名称仍绑定原文件。追加、同尺寸重写、权限/链接/替换或直接父目录变更均拒绝。配置文件16KiB格式上限与HTTP体预算虽然初值相同，属于两个不同边界。

打开的描述符按逆序关闭；一次关闭报告异常时仍继续尝试关闭其他描述符，最终返回固定私有文件错误。不同UID场景采用针对末级inode的 `fstat`注入验证，没有进行真实chown或管理员操作；8类读中变化则实际修改自建临时文件/直接父目录。非Linux拒绝使用局部platform注入验证，不能将其表述成已经在其他操作系统运行通过。

此组件不管理文件部署、口令、密钥、人员身份、信任或备份；没有复制真实私有配置。它也没有验证服务器当前空闲空间满足示例值。

## 5. 已执行验证及适用边界

Linux / Miniforge py310隔离源码快照中，最终两文件LF摘要为：

| 文件 | SHA-256（LF） |
| --- | --- |
| `backend/business_app/task_creation_development.py` | `c7b7de3b5f7c778a44f2ed010d603d725494b5612956ffdc9e9f08b79175f823` |
| `tests/business/test_task_creation_development.py` | `a2de6585cbc4b120986bfb2d48e686e1fa4f08b5422c7f36a12b07d64b845e2e` |

实际执行的纯组合命令为：

```bash
python -m pytest tests/business/test_task_creation_development.py tests/business/test_task_creation_materials.py tests/business/test_task_creation_context.py tests/business/test_task_creation_authority.py tests/business/test_task_creation_binding.py -q --tb=short
python scripts/verify_business_foundation.py failure-probe
python scripts/stage_three_types.py check
```

纯组合实际结果为 **726 passed in 2.44s**，退出0；范围包含配置测试及既有材料、请求上下文、authority纯边界和binding测试，不涉及真实采用或数据库事务。故意失败探针实际退出1，且 `expected_assertion_failure_verified=true`，证明该探针仍能失败。完整适用Ruff、格式检查均退出0；既有类型门禁覆盖 **283个源码文件**且无问题，完整命令范围由验证回执记录。上述范围不能相加为另一个测试总数。

较早723项结果对应追加UID、非Linux及关闭异常测试之前的源码，不作为最终726项的替代证据；最终两文件摘要、命令和结果须共同核对。组件最初未实现时availability用例已实际失败，保留该用例，未增加skip、降低断言或改变既有门禁。

本批未运行数据库整套或完整T014权限回归。纯组合、质量及类型通过不等于托管CI终态通过；CI须按实际发布提交另行核验。真实采用渠道、实名映射、精确org/case/来源用途、当前handler发布/许可/分类/独立恢复来源、运行预算接线、I03原子创建、I04 HTTP及I05完整验收继续按各自实际依赖推进。
