# T034 显式研发配置接入离线材料工具

2026-10-23（北京时间）。本批将[显式研发配置组件](t034-development-configuration.md)接入既有[I01离线材料工具](t034-i01-material-foundation.md)，实际修改 `scripts/task_creation_adoption.py`，并仅在 `tests/platform/test_task_creation_adoption.py`追加配置模式测试。原测试内容和断言保留。精确源码、命令、CI及同步结果由[本批验证回执](../00-project/validation/t034-configured-material-preparation-report.json)记录。

本次已经执行的是离线文件读取、材料校验、明确的字节/数量预算及处理器标识allowlist检查；没有接入业务HTTP、数据库、TaskPlanProof签发、运行处理器或真实采用流程。没有创建任务、ACTIVE映射、真实权限或软件许可事实。原100包锁及CI门禁保持，算法与Python候选继续暂缓。T034整任务、I02整体及I03—I05不能因本工具通过而标完成。

## 1. CLI用法与显式输入

新增两个子命令：`validate-development`只校验；`prepare-development`在全部校验通过后写出规范材料和清单。两者均必须提供 `--runtime-profile`、`--development-config`及四份材料；prepare还必须提供 `--output`。

```bash
python scripts/task_creation_adoption.py validate-development \
  --runtime-profile development \
  --development-config "$PRIVATE_DEVELOPMENT_CONFIG" \
  --policy "$POLICY_FILE" \
  --plan "$PLAN_FILE" \
  --capability "$CAPABILITY_FILE" \
  --input "$INPUT_FILE"

python scripts/task_creation_adoption.py prepare-development \
  --runtime-profile development \
  --development-config "$PRIVATE_DEVELOPMENT_CONFIG" \
  --policy "$POLICY_FILE" \
  --plan "$PLAN_FILE" \
  --capability "$CAPABILITY_FILE" \
  --input "$INPUT_FILE" \
  --output "$NEW_EXTERNAL_OUTPUT"
```

上述变量是执行者在shell中准备并显式传给命令的路径占位，不是工具隐式读取的环境配置。各路径必须为绝对路径；配置必须是仓库外的真实私有文件，输出必须是仓库外尚不存在的新目录。不要直接运行未赋值的示例。完整24项配置结构见[配置组件说明](t034-development-configuration.md#2-24项数值的完整示例)，本页不复制另一份配置模板。

profile只接受精确 `development`或 `test`，不能从JSON覆盖或回落到默认值。CLI拒绝production、缺参数及混用旧式 `--max-bytes`、`--max-nodes`、`--max-capabilities`；固定参数错误为 `TASK_PREPARATION_ARGUMENT_INVALID`，退出2，不回显原参数。内部调用接口为：

```python
run_development(
    action: str,
    paths: dict[str, Path],
    configuration_path: Path,
    *,
    runtime_profile: str,
    output: Path | None = None,
) -> dict[str, Any]
```

`action`只能为新增的两个子命令名称；`paths`必须且只能有 `policy`、`plan`、`capability`和 `input`四个Path。validate不接受output，prepare必须有output。直接API使用未批准profile同样拒绝，不能绕过CLI限制。

## 2. 私有配置冻结与实际调用顺序

工具复用 `load_task_creation_development`，先按既有Linux私有读取边界加载并冻结一次配置，再读取材料。配置缺失、非法、过宽权限、符号链接或未批准profile时，不进入材料读取或输出创建。原有三类固定配置错误由main安全返回，不包含配置正文或实际路径。

同一次调用使用同一个冻结配置构造 `MaterialBudgets`；四份材料分别有界读取一次，之后校验和准备复用这些原始字节，不再按路径重读。即使配置文件在此后改变，本次材料预算、配置摘要及输出记录也不漂移到第二份配置；下一次调用必须重新加载并验证。

依次执行：

1. 校验动作/参数组合，加载并冻结显式私有配置，核对输出路径边界。
2. 按policy、plan、capability、input顺序读取原字节；每次读取受单材料预算约束，并立即累加source总量。超过总量便停止，不解析材料、不继续读取后续材料、不创建输出。
3. 通过既有严格材料解析器校验四份材料、Schema、摘要、版本、图及输入绑定，并生成每个节点的规范输入快照。
4. 分别核对四份规范正文累计、所有节点规范快照累计及capability/plan的每个handler标识。
5. 全部通过后生成清单；validate返回结果，prepare复用既有独占写入与失败清理机制。

这里的配置冻结不是采用批准；有效的私有文件权限也不是操作人员身份、案件授权或业务管理权限。

## 3. 六类实际执行的限制

| `enforced_limits`字段 | 此离线调用实际执行的范围 |
| --- | --- |
| `max_material_bytes` | 每份原始材料及其规范正文、每个生成节点输入快照的单份字节上限；沿用已有 `MaterialBudgets.max_bytes`检查 |
| `max_nodes` | 计划/输入节点数量上限，沿用严格材料解析器 |
| `max_capabilities` | 既有解析器定义的handler/model引用计数上限，不是当前能力可用声明 |
| `max_bundle_bytes` | 四份主材料原字节之和，以及四份主材料规范字节之和，分别核对同一上限 |
| `max_snapshots_bytes` | 每个生成节点输入快照的规范字节全部累计，每个节点复制的资产/输入内容均计入，不去重扣减 |
| `allowed_handler_ids` | capability handlers及plan各节点handler标识均须位于显式预留allowlist；不将标识当import路径或执行命令 |

source、canonical和snapshot是三项独立观测量：raw/canonical不能互相代替，也不是将二者相加后只检查一次。规范化可能扩张合法输入，例如相同浮点值的 `1e2`在规范字节中变成 `100.0`；只核对原始文件大小不足以覆盖规范正文总量。多个节点复制输入可令快照总量大于任一主材料，因此还需要独立snapshot累计。

三项累计均在等于上限时允许、超过1字节时拒绝。四份主材料分别不超限也不能豁免累计限制。raw或canonical累计超限返回 `TASK_PREPARATION_BUNDLE_BUDGET_EXCEEDED`；snapshot累计超限返回 `TASK_PREPARATION_SNAPSHOT_BUDGET_EXCEEDED`；handler不在allowlist返回 `TASK_PREPARATION_HANDLER_NOT_ALLOWED`。这些拒绝发生于输出保存之前，不调用 `_save_prepared`、不产生目录，也不修改已有目标。

上述累计范围分别是明确列出的正文/节点快照；不包含 `manifest.json`自身或所有输出元数据的总大小。允许的handler标识仅表示配置范围匹配，不证明处理器已实现、发布、获许可或可用，也不会导入、实例化或执行它。

## 4. 输出记录、摘要与旧模式兼容

配置模式在结果和准备清单中新增同一份 `development_configuration`投影：

| 字段 | 内容 |
| --- | --- |
| `runtime_profile`、`environment`、`revision` | 本次冻结配置的明确作用域和修订 |
| `canonicalization_version`、`sha256` | 既有配置规范化版本及完整配置摘要，绑定profile、全部24项数值及元数据 |
| `aggregate_bytes.source_documents` | 四份实际读取原字节总量 |
| `aggregate_bytes.canonical_documents` | 四份严格校验后规范正文总量 |
| `aggregate_bytes.node_snapshots` | 全部生成节点输入规范快照总量 |
| `enforced_limits` | 第3节六类在本调用中实际执行的限制 |

配置格式或字段顺序改变但语义不变，摘要和准备字节保持确定；profile、revision或其他配置字段变化会改变配置绑定。原材料摘要仍单独保存，不能用配置SHA替换policy、plan、capability、input或node snapshot的SHA。配置SHA也不是未来采用收据、当前事实或许可证据。

完整配置包含的Proof、控制回执、采用、generation、能力/节点租约、handler期限、DB连接/语句/锁预算、HTTP体限额、临时目录配额及磁盘余量等，其值在此被解析和hash绑定，**没有在此离线调用执行对应运行机制**。不得把这份清单扩写成上述机制已接入、事务已受限、HTTP已保护或空闲磁盘已核对。

validate结果保持 `VALIDATED_OFFLINE_NOT_ADOPTED`；prepare结果保持 `PREPARED_OFFLINE_NOT_ADOPTED`，清单状态仍为 `OFFLINE_MATERIALS_ONLY_NOT_ADOPTED`。数据库、网络、ACTIVE映射、任务创建、handler执行及authority/license核验标志继续为false；结果中原有标志不变，清单另外保留 `handlers_executed=false`。

旧 `validate`/`prepare`的参数、`run(action, paths, limits, output)`接口和显式三限制保留。旧模式不新增 `development_configuration`字段；在相同原材料和原三限制下，旧模式清单保持原字节结构，配置模式剥离新增投影后与其逐字节一致。规范材料文件内容不因配置绑定而改写。

## 5. 输出安全与已执行验证

prepare仍只独占创建新的外部目录，目录0700、文件0600，固定文件名以 `O_EXCL`/`O_NOFOLLOW`写入并执行原持久性屏障。原有输出已存在、输入/输出符号链接、FIFO、父路径替换、植入链接、部分/零字节写入及两进程争用等保护复用。失败只清理本次拥有的已创建文件和空目录，保留未知文件及其链接目标；底层写故障固定脱敏，不输出原始异常或路径。

实际Linux/py310纯测试组合为：

```bash
python -m pytest tests/platform/test_task_creation_adoption.py tests/business/test_task_creation_development.py tests/business/test_task_creation_materials.py -q --tb=short
python scripts/verify_business_foundation.py failure-probe
python scripts/stage_three_types.py check
```

当前精确源码复验观测为 **612 passed in 2.33s**，失败探针实际退出1且确认预期断言失败；Ruff/格式及 **283个源码文件**类型检查通过，最终发布对应的源码摘要和CI终态以本批回执为准。较早源码出现过局部类型推断失败；后续仅补显式 `dict[str, Any]`类型标注后重新执行上述验证，不把早期通过借给修改后源码。

测试覆盖三类累计等界/+1、合法材料的规范扩张、4节点快照放大、配置早于材料I/O、单次冻结、allowlist无import、旧模式兼容及配置模式下复用的23组旧输出安全断言，另验证配置模式两进程竞争和main写故障脱敏。旧文件原内容未改，没有增加skip、放宽断言或绕过门禁。与前批726项纯组合覆盖文件不同，不能相减或合并为业务完成数。

本批没有执行数据库或HTTP整套回归，离线组件结果不等于托管CI或T034整任务验收。真实采用/实名管理与org/case/来源、收据语义、当前handler发布/许可/分类及独立恢复来源、Proof签发、运行预算、原子创建和HTTP接线仍按[实施计划](t034-creation-implementation-plan.md)逐项满足依赖。
