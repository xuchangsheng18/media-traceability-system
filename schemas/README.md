# 结构Schema和字段校验

版本1.0-py310-cpu；2026-10-12。CPU研发基线已验证，正式业务/生产NOT_FROZEN；本目录的完整业务完成条件仍保留。

## 职责与阶段位置

保存JSON Schema：api为业务API派生结构，model为模型能力请求/响应，dataset为数据目录及标注结构。结构约束与业务语义检查共同工作。

关联第二阶段手册步骤：19，关联13、17、20、21。详见[23步交付清单](../docs/03-development/stage-two-readiness.md)。

## 当前已存在内容

api/common.schema.json、model和dataset结构文件已形成。已有86个独立Schema的元结构与本地引用校验记录；这不是业务实现完成证明。

## 第二阶段应形成的文件

下面的路径或名称是计划交付位置，未形成时不能当作可运行文件。

| 计划交付 | 内容与要求 |
| --- | --- |
| `结构来源与版本登记` | api从OpenAPI同步；模型与数据结构分别保持其能力与用途来源 |
| `生成与更新规则` | 输入摘要、生成方式、兼容变更策略 |
| `正反例和语义检查` | 覆盖字段、类型、边界、版本、区间、重复资产及排序数量 |
| `服务集成校验` | 接入后端和推理服务的真实输入输出，禁止只在离线样例校验 |

## 输入依据

- [业务OpenAPI](../docs/03-api/openapi.yaml)
- [算法契约](../docs/06-algorithms/model-contract.md)
- [数据标注](../docs/07-datasets/annotation-specification.md)

## 验证与完成条件

从仓库根运行python scripts/validate_inputs.py；数据库与首发语义另运行python scripts/validate_database_contracts.py。实际服务集成测试在工程建立后执行并记录。

## 依赖和待补事项

具体版本、产品、资源及适用环境以技术候选、相关ADR和实际验证落实。未知项保留待确认；目录说明完成只代表本目录规划输入已补齐。每项交付记录版本、来源、运行命令、结果、未执行项和影响。

## 使用边界

JSON合法不表示证据引用存在、主体授权有效或状态转移合法。maxItems限制长度；逐字段唯一、连续名次和版本一致性仍需语义和数据库检查。

返回[项目入口](../README.md)或[文档总导航](../docs/README.md)。

## 本轮实际使用与生成

独立推理服务已实际按M15请求/响应Schema验证合成CPU模型；不是SSCD业务效果验收。两份OpenAPI的TS类型生成到shared-contracts/generated；不复制Schema作第二编辑源。整体资料/夹具、字段契约和隔离SQL检查已运行，报告见docs/00-project/validation。正式其他模型与业务接口仍按任务实现。

## 1.1工程补充

events/poc.analysis.requested.v1.schema.json定义版本化PoC信封1.0.0，extra字段拒绝；生产全模块事件另按业务任务建设，勿从PoC推出完整事件总线。
