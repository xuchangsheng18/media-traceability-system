# 接口契约导航

版本：0.1；整理日期：2026-10-12；状态：规划草案，NOT_FROZEN。

[业务OpenAPI](openapi.yaml)是外部接口结构源；[内部推理OpenAPI](inference-openapi.yaml)定义模型调用入口。两者均为0.1.0-review候选，不代表服务已经实现。

- [操作索引](operation-index.json)关联任务与数据表。
- [请求响应样例](examples/)用于结构检查，不能当作运行结果。
- [模型Schema](../../schemas/model/)与[模型契约](../06-algorithms/model-contract.md)定义模型能力输入输出。
- [字段映射](../04-database/api-field-mapping.csv)说明接口与数据库字段关系。

外部OpenAPI组件是API结构源；schemas/model是模型能力结构源；数据集结构在schemas/dataset。共享生成物应注明上游摘要与生成器，不得双向手改。跨来源重复结构变更要同步并校验引用。

## 本轮可运行入口

[PoC接口及边界](poc-api.md)列出现有上传/任务/健康与内部CPU推理。正式53操作设计仍保持唯一来源，本轮没有声称全部实现；[生成流程](../03-development/contract-generation.md)说明两份API的TS类型与消息约定。
