# 三服务连通性夹具

本夹具使用原锁定Vue、FastAPI和py310，分别启动前端、后端、模拟推理三进程，只绑定127.0.0.1临时端口，不连接数据库/对象存储、不开启GPU、不加载权重、不持久化模型结果。验证入口为`python scripts/verify_stage_three_demo.py`，过程会自动停止自己创建的进程。

提供独立health/ready、统一request_id、内部Bearer拒绝、UUID输入和显式mock=true/business_result=false的开发响应；结构源为[夹具Schema](../../schemas/development/mock-connectivity.response.schema.json)。这是第三阶段测试夹具，不是53项业务API或34项真实能力的扩展，不把模拟输出写入业务结果。

页面使用已安装的Vue发行文件，不访问CDN；流程为页面→前端代理→后端→模拟推理。令牌只在临时进程环境中随机生成，不写入Git/报告/浏览器。现有7服务和synthetic-cpu-encoder/demo-1真实合成模型保留，二者不混淆。

每个请求向标准输出写固定字段JSON：event、role、method、route模板、status、request_id、elapsed_ms及模拟标识。日志不记录原始URL、查询参数、请求头、请求体或令牌。验证器将日志临时保存在仓库外，检查三服务同一request_id、字段白名单和敏感值缺失，只将脱敏关联记录写入报告，结束清理临时文件。

验证包含11项检查及1例实际浏览器测试；浏览器检查后只停止自建模拟推理进程，核对后端ready返回503、调用返回502且不回显输入，再停止另外两个自建进程。它是研发连通性与错误处理证据，不代表业务审计系统已实现。
