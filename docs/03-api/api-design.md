# 接口设计

结构唯一源为openapi.yaml，采用OpenAPI3.1.0、JSON Schema2020-12及/api/v1相对基础路径。该版本是项目约定的契约草案，不表示必须采用在线最新产品版本。原13核心接口及任务书补充接口已登记来源；新增审批、版本、查询与受控下载路径为工程提案，待评审。

请求带X-Request-Id；变更操作带Idempotency-Key，绑定主体、操作和请求摘要。同键同摘要返回原效果；同键不同摘要409。超时后客户端先查询，不能以重复提交造成重复证据或批准。

If-Match使用强ETag绑定对应对象版本。复核需同时绑定run_version/result_version/review_version；客户端body中的expected_version不能替代服务端原子条件更新。缺少条件428，陈旧版本412，状态不允许409。

上传返回upload_id；完成可能仍VALIDATING，只有VALID asset_id可创建分析任务。分析创建和取消/重跑返回202；取消意图不等于已停止。重算创建新run_version，进度单调仅同一运行和固定DAG成立。搜索异步工作需返回search_id并轮询，不能将202视为结果完整。

登录开发适配器是唯一development-only接口，正式身份接入待ADR；正式部署默认关闭。其余接口声明bearer身份，仍须功能权限、单位/案件/对象及用途检查。模型网关单独内部契约，不能自动对外开放。

列表使用opaque cursor与limit，服务端固定稳定排序及授权过滤；游标不可携带可被修改的权限条件。超出配置上限拒绝，不接受任意SQL/字段排序表达式。

错误采用application/problem+json，并保留源code/message/request_id/details。未知异常不回堆栈。403/404隐藏策略保持统一；跨案件重复提示和检索不能旁路暴露对象存在。

所有二进制内容从受控content接口读取，指定对象version_id并逐请求核验；Range返回206/416，Cache-Control:no-store。预签名或已发token不等于持续有效授权，撤销后再次请求须拒绝。

时间用带时区ISO8601，库用TIMESTAMPTZ；媒体半开毫秒区间；UUID结构校验不充当授权；SHA-256小写64位。时间前后、bbox、引用存在、案例域和绑定版本须语义/业务校验，不能仅依JSON Schema。

## 首发候选响应版本增补

FirstSource新增ranking_id、task_id、run_version、result_version、policy_version、candidate_count，返回一份不可变快照。候选数量0—3，rank连续、升序且asset_id不重复；无计算快照404，0候选为insufficient。历史快照通过ranking_id查询。见[详细契约](../04-database/first-source-ranking.md)。这是未发布候选契约的变更，客户端生成物必须重新生成。
