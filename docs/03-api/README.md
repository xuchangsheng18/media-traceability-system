# 接口契约导航

版本：0.1；整理日期：2026-10-12；状态：规划草案，NOT_FROZEN。

[业务OpenAPI](openapi.yaml)是外部接口结构源；[内部推理OpenAPI](inference-openapi.yaml)定义模型调用入口。两者均为0.1.0-review候选，不代表服务已经实现。

- [操作索引](operation-index.json)关联任务与数据表。
- [请求响应样例](examples/)用于结构检查，不能当作运行结果。
- [模型Schema](../../schemas/model/)与[模型契约](../06-algorithms/model-contract.md)定义模型能力输入输出。
- [字段映射](../04-database/api-field-mapping.csv)说明接口与数据库字段关系。

外部OpenAPI组件是API结构源；schemas/model是模型能力结构源；数据集结构在schemas/dataset。共享生成物应注明上游摘要与生成器，不得双向手改。跨来源重复结构变更要同步并校验引用。

## 案件内资产和任务读取补充

用户已确认两个列表增加必填case_id，具体参数、对象条件及实际状态见[契约变更](catalog-read-contract-change.md)。全部T001—T123的表、迁移、接口和Python方法见[逐项清单](../03-development/t001-t123-implementation-inventory.md)，不以方法定义或表结构代替实际验收。

## 本轮可运行入口

[PoC接口及边界](poc-api.md)列出现有上传/任务/健康与内部CPU推理。候选73操作设计仍保持唯一来源，本轮没有声称全部实现；[生成流程](../03-development/contract-generation.md)说明两份API的TS类型与消息约定。

## 第一阶段归属

本专题承接第一阶段第12步的候选输入，操作、产物和确认要求见[24步对应表](../00-project/stage-one/steps-and-deliverables.md)。专题结构源保持不变，设计/计划与实际实施结果分开。

## 第二阶段整体与详细接口

- [系统整体接口说明](system-interface-specification.md)：七类接口面、服务边界、完整性标准及当前结论。
- [逐接口目录](detailed-interface-index.md)：53份操作说明和12模块导航。
- [83类数据结构](data-structures.md)：必填/可空、枚举/约束、字段与完整源Schema。
- [34类内部模型接口](inference-interfaces.md)：输入/输出字段、能力路径与独立Schema。
- [共用接口规则](common-interface-rules.md)、[服务/事件契约](service-and-event-contracts.md)：权限、幂等、ETag、异步、版本对象与PoC消息。
- [13项缺口及拟补方案](interface-gap-register.md)、[机器缺口](interface-gap-register.json)：候选路径未加入OpenAPI，不可调用。
- [覆盖来源索引](interface-catalog.json)、[生成解释](interface-annotations.json)、[检查报告](../00-project/validation/interface-documentation-report.json)。

明细由scripts/generate_interface_docs.py从唯一结构源生成，--check检查漂移；不独立手改字段。第二阶段第19步现为“PoC验证＋整体详细文档＋开放缺口”，尚不是全系统接口已实现/冻结。
