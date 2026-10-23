# T109离线标注质检工具

这是T109的限定开发子范围：检查显式提供的D01—D15标注JSON文件，不修改既有DatasetSchema、输入、数据卡或业务库，不执行训练、冻结、正式数据准入或T126。结构通过不证明标签正确或来源授权有效。

使用既有`jsonschema`、`referencing`环境，不安装新依赖。Linux原py310示例（显式选择自建夹具，不默认扫描目录）：

```text
/opt/conda/glwy/envs/py310/bin/python scripts/validate_annotations.py --input-root /absolute/private/annotation-inputs --inputs example.json nested/second.json
```

`--input-root`必须是现有绝对目录，`--inputs`是该目录内明确列出的相对文件名。不接受绝对输入名、`..`、Windows驱动器/设备路径、符号链接或Windows reparse point；检查根目录及各级路径。输出仅为stdout JSON，不创建报告文件、不访问网络、不读取未指定样本，也不默认读取holdout。使用方须提供有读取权限的私人目录；路径检查不声称能抵抗有权并发替换父目录的其他用户。

退出码：0为本次限定结构/语义检查通过；1为文件、预算、Schema或语义拒绝；2为命令行参数错误。JSON中的`input_index`对应参数顺序，不回显输入路径、标签、个人字段或Schema异常原文。有效记录提供输入字节的SHA-256、字节数和固定D编号，便于调用方自行关联；报告不是业务数据卡或训练版本清单。

## 实际检查

- 固定读取`schemas/dataset/D01.annotation.schema.json`至D15及`schemas/api/common.schema.json`，由`dataset_id`选择对应Schema，使用JSON Schema 2020-12和FormatChecker。本地Registry只允许这16份Schema的URN引用及内部片段，拒绝网络引用。
- 拒绝重复JSON键、NaN/Infinity、非有限指数结果、非对象及未知D编号；按原Schema检查必填、额外字段、UUID、枚举、引用形状和reviewer_refs。`reviewed`按原Schema至少有一项reviewer_refs；D15还要求`human_confirmed=true`。不擅自改成“两人即已仲裁”。
- 时间范围满足`end_ms > start_ms`，起止下限由Schema检查；D03/D04使用自身`payload.duration_ms`检查结束时间不超过时长，等于时长允许。其他D记录不虚构时长，也不把查询素材与来源素材的时间轴混为一个时长。
- 框采用原件归一化坐标，宽高大于0，检查`x+width<=1`、`y+height<=1`，沿用现有资料校验器的`1e-12`浮点容差。
- `unknown`、`disputed`及合法`insufficient`保留，不强制改成正负标签。D14即使`insufficient`仍按原Schema要求非空evidence_ids。
- 同一批内相同`dataset_id/sample_id/annotation_version`重复记录返回`BATCH_DUPLICATE`，内容不同返回`BATCH_CONFLICT`。`sample_id`按UUID身份规范化后比较，大小写不能绕过重复或冲突；输入文件保持原样。这是机械一致性检查，不证明独立提交、业务矛盾裁决或正式仲裁；不设置业务抽样率或一致性阈值。

## 可选机械抽样

默认不抽样。只有同时显式提供`--sample-count`和`--sample-seed`才进行选择，例如：

```text
/opt/conda/glwy/envs/py310/bin/python scripts/validate_annotations.py --input-root /absolute/private/annotation-inputs --inputs example.json nested/second.json --sample-count 1 --sample-seed self-owned-review-seed
```

全部指定文件仍先完整执行预算、Schema、语义和批内冲突检查；任一失败都不产生`sampling`结果。数量必须为1至本批全部有效记录数之间的整数；Python入口还明确拒绝布尔值和浮点数。种子必须为可编码为UTF-8、非空白且不超过128个字符的字符串，两项不能单边提供。参数格式错误的CLI退出码为2；输入验证或数量超过实际有效记录数时退出码为1。任何拒绝均不回显种子原文。

对每个已验证输入，计算`SHA256(seed的UTF-8字节 || 输入字节SHA256的32字节摘要)`，按该32字节排序键升序、同分按`input_index`升序，取前`sample_count`项，不放回。算法标识为`sha256-seed-utf8-input-sha256-bytes-v1`；固定种子、输入顺序和逐文件字节时选择可重现。修改字节（包括JSON空白）可能改变选择；不同种子不承诺每次都产生不同子集。复用完整验证所得摘要，不重新读取文件或增加未指定样本。

报告仅增加`sampling.algorithm`、`sampling.seed_digest`（种子的SHA-256）和`sampling.input_indices`；所选索引顺序是排序后的抽取顺序，对应原始`--inputs`参数。它只提供机械抽查入口，不证明正式抽样率、质量达标、双人一致性或仲裁，也不划分训练集、测试集或封存集。

## 工程预算与未验证项

一次最多64个文件，每文件最多1MiB，总计最多8MiB，解析后嵌套深度最多64，每记录最多统计100个Schema错误。预算是研发资源保护，不是正式数据规模或业务阈值；超限拒绝，不默默截断输入后宣布通过。

每条有效记录明确列出`not_verified`：掩码字节/尺寸、映射正确性、真实来源授权、真实人工身份、独立双人标注、仲裁、正式标签词典及标签正确性。D03/D04之外还列`media_duration`。ObjectRef只检查结构，不读取它指向的对象；标注版本与授权引用只是字段，不当作真实版本证明或授权决定。

测试入口：

```text
python -m pytest tests/data/test_annotation_validation.py -q
```

统一`python scripts/dev.py test`已包含`tests/data`，并保留原PoC、平台、第三阶段、业务和前端测试；脚本及数据测试进入原格式、Lint和类型检查范围，不修改依赖锁或放宽扫描。

测试使用仓库既有15组自建正反例及临时生成边界文件，包括CLI退出码和原文不回显；不运行数据库、模型或真实人工标注验收。Windows无符号链接创建权限时，实际链接测试明确skip；reparse属性拒绝有独立纯测试，Linux实际符号链接结果另按原py310回执登记。
