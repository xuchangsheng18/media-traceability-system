# Runner Secret与分支保护操作手册

2026-10-13；第三阶段研发实施候选，正式批准/冻结未完成。

当前使用GitHub临时Ubuntu CPU Runner，安装锁定py310/Node、独立7服务、25门禁及非敏感报告归档；普通CI不依赖GPU。共享Linux研发服务器不充当生产Runner，本次不改外部平台设置。

Runner按用途划分：CPU常规验证、受限Docker构建、可选GPU/大模型、正式发布/签名分别使用获准资源和标签；管理员登记网络/并发/缓存/日志保留/隔离、实际责任人及用途，避免不可信PR读取发布秘密。内网Runner需先落实软件/镜像源与外网禁用条件，不能默认能联网下载。

| 变量类别 | 名称示例 | 用途/限制 |
| --- | --- | --- |
| 测试数据库/对象存储 | TEST_DATABASE_URL、TEST_S3_ACCESS_KEY、TEST_S3_SECRET_KEY | 仅获准隔离测试目标；当前临时PoC在外部运行目录随机生成，不需要正式数据库凭据 |
| 镜像/制品/模型库 | REGISTRY_USER、REGISTRY_TOKEN、ARTIFACT_TOKEN、MODEL_REPOSITORY_TOKEN | 实际来源、权限和有效期待定，本次未发布/下载业务模型 |
| 扫描/签名 | SCANNER_TOKEN、SIGNING_KEY_REF、CERTIFICATE_REF | 当前公开依赖审计无需这些服务；签名平台未配置，不填写真实值 |

示例名称不代表现有代码已消费或Secret已配置。管理员只创建实际需要的变量，注入获准job，限定分支/环境与服务账号权限，保持掩码且不回显；记录轮换和撤销验证。

建议保护main：禁止普通直推/强推/任意删除，要求独立审核、适用CODEOWNERS、required checks通过、旧审核随变化复核；管理员绕过及紧急流程须审批。实际评审人数、套餐及保护能力未确认。当前用户同步授权仍按既有main执行，不能虚构“主分支直推已禁止”。正式平台配置由获授权管理员按当前套餐或批准内网平台实施。

验证方法：平台API/设置读回required checks与保护规则；用获准测试账号尝试直推受保护的非生产测试分支；故意失败的测试PR不能合并；独立评审生效；撤销服务账号后拒绝访问；Secret未出现在日志/制品。不要对main作破坏性探针，不创建额外账号或发外部通知。CODEOWNERS和候选策略文件只是准备材料。

官方依据：[保护分支](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)、[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)。
