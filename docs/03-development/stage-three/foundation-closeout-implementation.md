# 前三阶段研发基础补齐与验证范围

2026-10-16；按用户已认可的方案在既有仓库实施。原100包Python运行锁、12份原件、14份历史材料和170项源任务保留；本批修改现有应用基础代码，服务器既有7服务部署未更新。阶段仍NOT_FROZEN，不能把基础子范围通过当成全部业务或生产验收。

| 原任务 | 本批实际修改 | 验证入口与边界 |
| --- | --- | --- |
| T001 | 统一贡献入口、任务卡当前步骤/剩余工作、现有阶段导航和变更模板 | 资料生成漂移检查；实际负责人及整任务验收另行落实 |
| T002/T007 | 显式development/test/production选择，必要配置校验，URL/密钥不进入配置输出；非法连接串安全拒绝 | tests/stage_three/test_foundation_configuration.py；生产profile始终拒绝，尚未实现和批准生产配置 |
| T003 | Vue Router哈希路由、上传/健康/未知路径页、应用内存共享状态、API基地址校验和安全错误信息 | 前端单元、构建及foundation浏览器检查；刷新清除令牌，不使用持久存储 |
| T005/T006 | ESLint/Prettier/TS、实际违规探针及统一提交前入口；CI执行同一检查 | scripts/verify-frontend-quality.mjs；检查基线先成功，再逐一放入自建违规文件验证失败，最后移除；平台必需检查仍待配置 |
| T008 | 统一安全JSON日志，API上下文隔离，响应X-Trace-ID；现有队列及推理HTTP传播request_id/trace_id和task/run/attempt | tests/stage_three/test_foundation_tracing.py；覆盖并发请求和选定发布/消费边界，未宣称完整业务DAG及采样/指标平台已交付 |
| T009 | 唯一错误码注册、安全500/404/405/HTTPException和Allow头处理 | tests/business/test_foundation_errors.py；业务回归与PoC历史浏览器流程需共同通过 |
| T010 | PR及需求、模型、数据库、ADR变更模板 | 本记录按模板核对影响、版本、验证与恢复；不把模板当实际审批 |

统一入口见[贡献说明](../../../CONTRIBUTING.md)。本批新增前端依赖精确记录在[package.json](../../../frontend/package.json)与锁文件；Python工具仍位于仓库外的独立工具层。Linux提交钩子使用锁定py310，安装器遇到自定义hook或core.hooksPath会拒绝覆盖。是否已安装并执行须读取[钩子验证报告](../../00-project/validation/development-hook-report.json)，其他开发者工作区不自动安装；Windows默认经SSH使用同一Linux入口，未证明Windows原生py310/钩子可用。

## 配置与运行

复制根目录和frontend中的.env.example只能取得变量说明，不含实际秘密。PoC必要连接值仍由Git外私密runtime注入；业务应用使用MT_BUSINESS_*明确隔离数据库、对象目录、上传限制和游标密钥，不能从PoC身份或固定案件推出业务授权。运行profile选择不代表获得部署权限。

前端默认同源请求；Vite开发服务把/api及/poc代理到127.0.0.1:14200，容器部署继续使用既有反向代理。VITE_API_BASE_URL可为空或配置获准的同源前缀/HTTP(S)地址，拒绝凭据、查询、片段及路径穿越。VITE变量会进入浏览器包，禁止放秘密；跨域地址需另验证服务端CORS和现场网络，不自动开放。健康页实际调用已鉴权/api/v1/health，失败显示失败；并非无需身份的业务就绪证明。

## 错误与追踪

错误码唯一源为backend/business_app/errors.py的不可变注册表；重复码、未注册码或状态不匹配会失败。业务错误响应保留code/message/request_id/details，未知异常不回显堆栈。PoC兼容原有安全错误码，任意HTTPException.detail不得直接回显。注册表中的HTTP_STATUS_4xx/5xx是安全框架映射，不表示这些状态均对应已实现业务功能。

trace_id由合法UUID请求编号确定性转换成32位十六进制，跨异步边界使用持久化事件中的请求身份，不能用当前线程上下文替代。日志只收固定事件、路由模板、方法、状态、时长及UUID/task/run/attempt，不记录原始URL、查询、令牌、文本或连接串。它是现有链路的关联机制，未宣称W3C Trace Context/OpenTelemetry或完整观测平台。

## 验证证据及状态规则

本地独立Python3.12工具环境只作初步检查；最终研发依据是Linux py310 3.10.22和托管隔离Runner实测。真实数量、源码SHA和托管结论读取[GitHub制品记录](../../00-project/validation/github-actions-report.json)、[业务回归](../../00-project/validation/business-foundation-report.json)、[类型检查](../../00-project/validation/stage-three-python-types-report.json)、[前端违规探针](../../00-project/validation/frontend-quality-report.json)及[同步回执](../../00-project/server-sync-receipt.json)。旧报告只有在源码、时间和范围相符时才能证明本批；本记录不预先断言新CI通过。

任务台账保留早期实现审查及归档CI身份作为历史，当前步骤新增本批代码/测试和此记录；不伪造全部任务验收。当前容量以最近同步观测为准，13%/约644GiB仅是时点快照，重操作仍实时检查。实际配额、维护人、备份和整盘/异机恢复未验收。

## 本批变更复核与恢复

输入：T001—T010和已认可实施计划。影响：应用配置/错误/追踪、研发前端及质量工具；业务OpenAPI、数据库结构及事件payload未扩展，无新增数据库迁移。前端新增Vue Router和检查工具精确锁定，原Python运行锁不变。验证覆盖见上表，完整回归及负向检查通过后才能交付；新业务身份/规则适配仍需对应测试。

恢复：本批尚未部署共享服务；需要撤回时先选定先前源码提交与原前端锁，在隔离环境复建和验证，再按适用流程发布。不得用git reset清掉未知用户修改，不删除数据库/对象卷。新增钩子仅在确认归属本安装器时由实际开发者卸载，不覆盖其余控制。

未完成：真实责任人/账号ACL、GitHub分支保护与必需检查、生产版本及软件准入、正式规则/身份/数据/GPU、现场离线及Windows原生适用性、完整业务DAG/所有业务接口、正式灾备和性能。可以按具备输入的任务继续基础开发；这些条件按实际所选任务和环境逐项落实，不要求先实现170项再启动研发。

## 独立审查整改

本批独立只读审查发现5项重要问题，均纳入单次修复与回归：补齐/poc开发代理，实际自建HTTP服务验证健康/上传路径转发；在URL规范化前拒绝绝对地址原始路径越界及控制字符；worker导入及推理lifespan在消费/模型初始化前验证profile；关闭Uvicorn原始访问日志并让Nginx只记录方法/状态/耗时，原始错误日志关闭；阶段容量由带时间资源快照生成；最新同步观察另见回执，缺字段显示未知。新增真实进程拒绝4例、前端拒绝及代理5例、日志行为1例及生成容量2例均先观察失败再修复。实际容器日志的合成标记验证纳入独立CI门禁，以http-log-privacy-report.json为准，本批未在共享旧部署上运行该检查。

并发内部日志和嵌套上下文回归已补齐：同事件循环8请求交错时，逐条核对内部日志的request_id/trace_id与task_id；异常退出恢复外层上下文，离开作用域后不残留。真实隔离数据库中，同一上传事件在其他请求上下文内重复消费两次，日志仍使用事件自身身份，只生成一条资产，外层上下文保持。另在Git外隔离副本中分别破坏上下文读取、异常清理和事件身份优先级，3项受控变异均被测试拒绝；原始文件最终恢复。详见[追踪回归证据](../../00-project/validation/trace-regression-report.json)。生产代码无需改动；完整跨进程DAG、采样及聚合仍需后续实际集成验证。

实际钩子首轮检查全部成功，但报告写入被pre-commit判定为修改工作区，因此未记成功。已补只读报告控制（保留所有检查及失败退出码），新增安全/拒绝回归后重新验证；独立检查与CI仍正常保存报告。钩子报告只有实际退出0才记录PASS。

严格状态复核同时修正任务台账中残留的“500为text/plain”“404未统一”和“未验证钩子”等旧审计值；原观测保留在audit_observation_history。当前应用HTTP结果指隔离源码实测，Linux钩子与Windows原生分开登记。任务卡归档实现引用更新到最近已核验源码/CI；新一轮测试与同步仍以最终制品及回执为准。第二阶段表格同步已有访问层/迁移与接口子范围，正式身份和完整业务仍保持待落实。
