# T034 离线材料结构回执

2026-10-23活动示例更新：当前Python3.11迁移使用下列py311环境标识；具名历史回执仍保留原生成时点内容，不改写历史摘要。

2026-10-23（北京时间）。本批为已配置的离线材料工具增加可选结构回执及独立复核入口。实现包括[回执Schema](../../schemas/development/task-material-structure-receipt.schema.json)、[纯结构回执模块](../../backend/business_app/task_creation_receipt.py)和[CLI接线](../../scripts/task_creation_adoption.py)。材料解析、显式研发配置与文件写出继续复用[配置接线说明](t034-configured-material-preparation.md)和[I01材料基础](t034-i01-material-foundation.md)。

回执记录材料结构校验、精确输入绑定以及本地观察。它没有签名、可信发布者身份或正式采用效力，不能作为 `TaskPlanProof`、正式采用回执、授权事实或模型可执行证明。T034整卡、I02整体及I03—I05仍未完成；原100包锁、公共接口、17份既有SQL和CI门禁不因本批改变。算法与Python候选继续暂缓。

精确源码、实际测试命令和数量、质量检查、CI及同步结果统一由[本批验证报告](../00-project/validation/t034-material-structure-receipt-report.json)记录。本页不预填尚未形成终态的测试数量或通过结论。

## 1. 实际命令与输入

在当前Linux／py310研发环境的仓库根目录执行。以下变量由执行者明确赋为绝对路径；不是工具隐式读取的环境配置。配置文件应满足既有私有文件要求，输出应为仓库外尚不存在的新目录，其父目录需已存在。四份材料按 `policy`、`plan`、`capability`、`input` 提供；不从回执或输出目录猜测原始材料。

```bash
python scripts/task_creation_adoption.py prepare-development \
  --runtime-profile development \
  --development-config "$PRIVATE_DEVELOPMENT_CONFIG" \
  --policy "$POLICY_FILE" \
  --plan "$PLAN_FILE" \
  --capability "$CAPABILITY_FILE" \
  --input "$INPUT_FILE" \
  --structure-receipt \
  --output "$NEW_EXTERNAL_OUTPUT"

python scripts/task_creation_adoption.py verify-development-receipt \
  --runtime-profile development \
  --development-config "$PRIVATE_DEVELOPMENT_CONFIG" \
  --policy "$POLICY_FILE" \
  --plan "$PLAN_FILE" \
  --capability "$CAPABILITY_FILE" \
  --input "$INPUT_FILE" \
  --receipt "$NEW_EXTERNAL_OUTPUT/material-structure-receipt.json"
```

profile只接受精确的 `development` 或 `test`，复核时必须使用原profile及相同的有效配置。`--structure-receipt` 只属于 `prepare-development`；`verify-development-receipt` 必须提供 `--receipt`，不接受输出目录，也不写出新文件。两种模式均不接受旧式手工 `--max-bytes`／`--max-nodes`／`--max-capabilities` 参数替代配置。

启用开关后，输出包含原有四份规范材料、按原顺序编号的 `node-input-000001.canonical.json` 等节点快照、`material-structure-receipt.json` 和 `manifest.json`。`manifest.structure_receipt` 及prepare标准输出中的同名记录具有以下字段：

| 字段 | 精确含义 |
| --- | --- |
| `file_name` | 固定为 `material-structure-receipt.json`；注意它不同于既有材料条目使用的 `filename`。 |
| `sha256` | 回执实际规范字节的SHA-256。 |
| `size_bytes` | 回执实际字节数。 |
| `status` | 固定为 `MATERIAL_STRUCTURE_VALIDATED_NOT_ADOPTED`。 |

回执记录单列于 `manifest.structure_receipt`，不并入原有 `manifest.artifacts` 材料列表。标准输出 `artifact_count` 包含回执文件，仍不包含 `manifest.json`；其数量随节点数变化，不能作为已完成业务功能数。

prepare成功状态仍为 `PREPARED_OFFLINE_NOT_ADOPTED`。复核成功状态为 `STRUCTURE_RECEIPT_VERIFIED_NOT_ADOPTED`，输出 `receipt_sha256`、`receipt_source_sha256` 和研发配置观察；在严格规范字节校验通过时，两项回执摘要一致。复核输出的 `output_written`、`database_written`、`network_accessed`、`active_mapping_created`、`task_created`、`handlers_executed`、`authority_or_license_verified` 均为false。

## 2. 回执字段契约

Schema使用JSON Schema Draft 2020-12。顶层及各记录边界采用闭合字段定义；实现还会从实际输入重算并比较整份规范回执，不以单次Schema校验替代绑定检查。

| 字段组 | 固定内容或绑定对象 |
| --- | --- |
| `schema_id`、`schema_version` | 分别为 `urn:media-trace:task-material-structure-receipt:1.0.0`、`1.0.0`，是结构格式身份。 |
| `canonicalization_version` | 固定为 `task-structure-receipt-json-utf8-sortkeys-v1`。 |
| `material_canonicalization_version` | 固定为既有 `task-material-json-utf8-sortkeys-v1`。 |
| `status` | 固定为 `MATERIAL_STRUCTURE_VALIDATED_NOT_ADOPTED`。 |
| `validator_protocol` | 固定为 `offline-task-material-structure-validation-v1`，表示本地协议约定，不是经认证的验证者身份或发布版本证明。 |
| `development_configuration` | `runtime_profile`、`environment`、`revision`、配置规范化版本与摘要，以及实际 `aggregate_bytes` 和 `enforced_limits`。环境为 `linux-py311-cpu-internal-rnd`。 |
| `materials` | 严格按policy、plan、capability、input顺序保存四条记录；每条包括kind、Schema身份、文档身份／版本、规范化版本、原字节摘要／长度和规范字节摘要／长度。 |
| `node_inputs` | 按生成的节点快照顺序保存 `node_code`、`schema_id`、`input_version`、`canonical_sha256`、`canonical_size_bytes`。这些是输入快照描述，不是已执行节点或上游产物的证明。 |
| `schema_registry` | 当前已加载Schema映射的规范化版本、内容摘要和数量。 |
| `observed_source_inventory` | 固定五份本地源码文件的路径、原字节SHA-256和长度，带明确的“观察而非执行认证”语义标记。 |
| `limitations` | 下述九项全部为严格布尔false；不接受true、数字0／1、字符串或null替代。 |

`limitations` 的九个字段为 `adopted`、`authority_verified`、`licence_verified`、`current_facts_verified`、`handlers_executed`、`database_written`、`network_accessed`、`task_created`、`active_mapping_created`。其中 `licence_verified` 是回执Schema的实际拼写；CLI原有汇总字段仍为 `authority_or_license_verified`。

## 3. 严格规范字节与重新绑定

回执采用实现中明确版本化的JSON编码：UTF-8、`sort_keys=True`、分隔符为逗号及冒号且不插入额外空白、`ensure_ascii=False`、`allow_nan=False`。这是本项目编码约定，不能冒称数字签名或第三方规范认证。

`verify_structure_receipt` 先严格解析，再检查回执原字节是否与重新编码的规范字节完全相等。因此重复键、NaN／Infinity、非法UTF-8、无效根结构、额外字段、非规范缩进以及末尾新增换行均不能通过。不要用编辑器美化生成的回执。校验失败不退回旧格式、不跳过绑定，也不把调用者自报的“已校验”标志当作依据。

绑定对象需要分别理解：

| 对象 | 绑定语义 |
| --- | --- |
| 四份原始材料 | `source_sha256` 和 `source_size_bytes` 直接对应实际读入的原始bytes；即使只改空白且解析后的JSON相同，也会使旧回执绑定失效。 |
| 四份规范材料与节点快照 | 复用材料解析器重新形成规范bytes，逐项核对身份、版本、摘要、长度及顺序；不能用文件名、其他材料摘要或假上游值替代。 |
| 研发配置 | 绑定解析后的完整settings及显式profile的规范摘要，版本为 `task-creation-development-json-v1`；不是配置文件原始字节摘要。即使某个配置项本次没有实际使用，其有效值改变也会改变配置绑定。 |
| Schema与源码观察 | 使用复核进程中的已加载Schema内容和重新读取的固定源码原字节重算；改变其绑定内容会拒绝旧回执，但这不赋予观察可信发布者身份。 |

纯接口为 `create_structure_receipt(raw_materials, settings)` 和 `verify_structure_receipt(raw, raw_materials, settings)`。`raw_materials` 必须是依上述顺序组成的四项bytes元组，settings必须是实际 `TaskCreationDevelopmentSettings`。返回的 `StructureReceipt` 保存不可变 `canonical_bytes` 与 `sha256`；`as_dict()` 每次产生分离的字典，不用调用者可修改的字典替代规范字节。

## 4. 102项已加载Schema与五份源码观察

[现有注册机制](../../backend/business_app/contracts.py)在导入时加载 `schemas` 下的Schema，以 `$id` 建立 `SCHEMAS` 映射及本地引用注册表。本批完整加载对应102个Schema身份。回执的 `schema_count` 实际取 `len(SCHEMAS)`，不是写死102作为永久规则；其摘要对完整已加载 `SCHEMAS` 解析内容按 `local-schema-registry-json-v1` 规范编码后计算。

因此该摘要不是102个磁盘文件的原始字节摘要，不是只计算本张回执Schema，也不证明进程已重新加载磁盘上的后续修改。Schema的纯格式变化不必改变解析内容摘要；加载状态、结构内容与文件原字节不能混用。

`observed_source_inventory.files` 固定按路径排序读取以下五份文件，不接受调用者另外指定路径：

- `backend/business_app/contracts.py`
- `backend/business_app/task_creation_development.py`
- `backend/business_app/task_creation_materials.py`
- `backend/business_app/task_creation_receipt.py`
- `scripts/task_creation_adoption.py`

源码观察复用Linux目录描述符、拒绝符号链接和非普通文件，并核对读取前后的文件身份、大小和时间元数据。每份固定源码的技术读取上限为1 MiB。不能满足读取条件时拒绝生成或复核，不以空摘要代替。Windows仅作为远程入口；不把这段Linux安全I/O行为标记为Windows原生已验证。

其语义固定为 `LOCAL_SOURCE_BYTES_OBSERVED_NOT_EXECUTED_CODE_OR_RELEASE_ATTESTATION`。这只说明读取时观察到这些文件的bytes，不证明这些bytes就是已执行的字节码、签名发行制品或经批准验证者实现；也不是五个文件的全程原子快照或handler执行记录。

## 5. 预算、输出及错误边界

仍需显式研发配置提供 `max_material_bytes`、`max_nodes`、`max_capabilities`、`max_bundle_bytes`、`max_snapshots_bytes` 和 `allowed_handler_ids`。模块会重新解析材料、执行既有材料预算及handler标识allowlist检查。allowlist只限制声明标识，不能证明handler存在、已发布、已获许可或能够执行。

`aggregate_bytes.source_documents` 只累计四份原始材料；`canonical_documents` 只累计四份规范材料；`node_snapshots` 只累计全部节点快照。原材料和规范材料聚合分别受 `max_bundle_bytes` 约束，快照聚合受 `max_snapshots_bytes` 约束。回执bytes另受 `max_material_bytes` 约束，不能把这些计数扩大解释为包含清单、全部文件、进程峰值内存或整盘占用的总配额。配置中的运行期限、取消、并发、临时盘等其他预算也未因此接入HTTP或执行路径。

prepare在生成和校验回执完成后，才进入既有排他输出流程：新目录0700、文件0600、拒绝覆盖已有目录／文件。写出失败时只回收本次创建且身份匹配的文件，保留未知文件，不递归删除其他内容。verify仅读取，不改写材料、配置、回执或既有准备目录。

回执专用错误码为 `TASK_STRUCTURE_RECEIPT_INVALID`、`TASK_STRUCTURE_RECEIPT_BUDGET_EXCEEDED`、`TASK_STRUCTURE_RECEIPT_BINDING_INVALID`、`TASK_STRUCTURE_RECEIPT_INVENTORY_UNAVAILABLE`；既有配置、材料和安全文件I/O拒绝仍沿用各自固定码。CLI失败退出2，成功退出0；不把原始路径、材料内容或底层异常直接回显。结构核验不连接数据库、不联网、不导入或执行材料声明中的handler。

## 6. 兼容、验证与剩余范围

旧 `validate`／`prepare` 的显式三预算模式保留。原 `validate-development` 及不带 `--structure-receipt` 的 `prepare-development` 不自动增加回执；原规范材料、节点快照、清单结构及未启用开关时的输出bytes保持兼容。新verify命令不会读取一个成功布尔标志后直接放行，而是要求原材料、配置、当前Schema内容及固定源码观察全部重新绑定。

[回执测试文件](../../tests/platform/test_task_material_structure_receipt.py)及[既有CLI测试](../../tests/platform/test_task_creation_adoption.py)定义了生成／复核、旧输出兼容、原材料仅格式变化、配置／profile变化、顺序与摘要篡改、闭合字段、严格false标记、非法JSON、超限和无写出等检查。实际运行数量、源码摘要、RED／GREEN范围与质量结果以[本批验证报告](../00-project/validation/t034-material-structure-receipt-report.json)的最终记录为准；参见[测试判定约定](../../tests/README.md)，不由本页列举覆盖点折算为通过或任务验收。

上一提交 `eb28208f310fc6765257dc1ec85b8104edc77760` 的[CI 39840316466](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39840316466)已失败：身份检查332项中1项失败，适配器200项、映射80项通过；唯一失败selector为 `tests/identity/test_recovery_live.py::test_restart_and_database_dependency_readiness`。上传的安全报告没有具体失败断言，不能据此判定为CLI回归、数据库就绪超时或随机故障。foundation及实际engineering作业被跳过，不能记为本批已执行。该历史与本批精确源码结果分开记录，现有失败探针、安全扫描和CI门禁继续保留。

本批离线子范围无需新增用户本人接管、账号授权或密钥操作。正式采用／可信回执语义、Proof签发、当前handler发布与许可事实、分类和独立恢复、运行预算接线、I03原子创建／幂等回放、I04 HTTP及I05适用验收仍需各自实际实现和验证。结构回执不能填补这些事实，也不创建ACTIVE映射、业务任务或真实202响应。
