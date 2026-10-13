# 精确历史结果读取

7个已有读取操作在[OpenAPI](openapi.yaml)中增加扁平deepObject参数history，没有新增HTTP路径。任务路径提交history[run_version]与history[result_version]；资产、簇和传播路径还须history[task_id]。对象字段全部必填，禁止只给一个版本。省略history保留原最新读取行为。

选择历史时先核验当前身份/单位/案件/用途，再查路径对象和精确task/run/result。未命中404、权限拒绝按当前策略，绝不回退最新结果；ranking_id同时给出时必须与同一快照绑定。返回X-Task-Id/X-Run-Version/X-Result-Version供客户端核对。Schema不能自动验证数据库成员或授权，业务实现必须执行这些检查。

历史读取从固定run-result快照投影到当前操作结构；完整能力原响应按对应模型Schema保存在summary或固定对象版本。当前公开Finding不是全部专用payload；不得丢掉掩码、逐段来源、融合冲突、未知区间或版本。34能力的逐payload路径、结构摘要和保存规则另有机器登记。

协议设计已补齐；尚未实现这些正式业务HTTP读取。IF-G09的真实两次重算/旧结果不可变/跨案件测试仍待对应任务执行。来源采用[OpenAPI3.1参数定义](https://spec.openapis.org/oas/v3.1.0.html#parameter-object)，用于扁平对象序列化；项目权限与业务规则来自本仓库输入，不由网页决定。
