# 仓库目录与文件归属

版本：0.1；整理日期：2026-10-12；状态：规划草案，NOT_FROZEN。

沿用已存在的服务器目录，新增datasets仅存数据目录元信息；本轮已有backend/app（main.py、worker.py等）、backend/migrations、frontend/src和ai-services/inference。下面的表还保留完整业务规划位置，其中app/modules、app/workers等未按完整业务生成；不能把规划位置当现有入口。

```text
media-traceability-system/
  README.md  AGENTS.md  .gitignore  .gitattributes
  frontend/           页面、路由、API客户端和页面测试
  backend/            业务API、模块、任务进程和数据库迁移
  ai-services/        推理网关适配、模型加载、前后处理
  shared-contracts/   从权威契约生成的客户端与共享类型
  schemas/            模型、数据集及公共结构
  datasets/catalog/   数据卡和版本、用途元信息
  docs/               设计、来源、决策、开发和交付说明
  tasks/              170独立任务卡及候选执行依赖
  config/             非敏感配置模板
  deploy/             已有开发编排/网关，生产监控待补
  scripts/            输入校验及后续初始化、备份工具
  tests/              合成夹具、SQL检查及后续集成测试
  prompts/            提示词模板和评测版本
```

| 路径 | 保存内容 | 不应保存 |
| --- | --- | --- |
| backend/app/modules | 业务模块及数据范围核验 | 模型大权重、页面源码 |
| backend/app/workers | 幂等执行、租约、重试、任务状态协调 | 独立于数据库的最终业务状态 |
| backend/migrations | 有版本的增量迁移 | 对生产直接执行的空库重建 |
| frontend/src | 页面、组件、API调用 | 数据库密码、算法私有密钥 |
| ai-services | 模型适配与运行依赖声明 | 直接写业务审核结论 |
| shared-contracts | 生成物及生成说明 | 手工维护的第二份OpenAPI源 |
| docs/03-api | 外部和内部OpenAPI源 | 业务实现代码 |
| docs/04-database | 候选SQL、字典、字段映射 | 实际数据库目录和备份 |
| datasets/catalog | 数据集元数据 | 真实媒体和训练样本 |
| tests/fixtures | 自建无敏感正反例 | 未授权真实案件材料 |

业务模块依赖公共基础设施和接口适配器；模块间通过应用接口协作，不能随意跨模块修改表。前端不依赖数据库模型；算法环境独立锁版本。docs、任务卡和生成代码出现冲突时登记并修正来源，禁止以复制一份契约解决冲突。

本地资料包与服务器采用相同相对路径，避免引用Windows绝对路径作为运行前提。source-inventory中的本地路径仅作来源追溯。

新增模块需同时补范围与责任、契约、数据归属、迁移、测试、部署影响及任务追踪。本目录决定仅作为规划提案；Q-27正式确认状态保留。
