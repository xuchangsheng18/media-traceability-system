# 开发规范输入

Python、TypeScript、SQL、YAML保持一致命名和UTF-8。接口、Schema、数据库及错误码以本包机器源为依据；业务依赖版本由第二阶段ADR确定，不把本包校验工具锁当业务生产锁。

代码提交前运行格式/静态检查、适用单元/契约/SQL和安全扫描；重要事务、并发/幂等、租约与权限处理有有意义测试。迁移使用版本脚本，生产禁止直接初始化空库脚本；错误处理有稳定code/request_id，不泄露堆栈和敏感字段。

代码质量、格式和开发命令范围见[贡献规则](../../CONTRIBUTING.md)与[第三阶段验证](development-environment-validation-report.md)；格式检查覆盖20文件，其中既有应用/推理/PoC测试13文件的11处文件调整已核对AST不变。其他历史脚本及未来模块按各自范围纳入，不将部分格式治理当全仓治理。pre-commit保持独立工具层，Python静态类型范围见下文，CI接入按实际证据判定。

本轮已有py310/FastAPI/Vue工程、Ruff根配置、TS类型检查、真实合成训练与CI构建/集成。CI严格核验完整第三方包锁和生成类型；具体命令见ci-cd.md。正式日志审计/权限和全部业务仍按任务实现，源任务的计划位置不代表现有入口。

## Python类型检查实际范围

独立mypy2.4.0及完整12包工具闭包在仓库外安装，精确锁和制品摘要见config/locks/requirements-stage-three-types.lock及stage-three-type-artifacts.json；原100包运行锁与12包pre-commit锁保持。当前检查22个源文件，首次43项错误已修至0，6项工具/范围测试及既有测试共51项通过。范围为profile.type_scope，新业务目录存在后自动加入；不能称全部历史scripts已治理。

Pydantic插件正确解析BaseSettings环境字段，依据[Pydantic官方说明](https://pydantic.dev/docs/validation/latest/integrations/dev-tools/mypy/)。PyYAML/jsonschema使用独立精确stub；仅boto3/botocore/Celery缺失声明保留对应命名空间例外，不作全局忽略。JSON审计根对象在加载边界标注dict[str,Any]，模型请求仍由JSON Schema验证；新business_app额外禁止未注解定义和Any返回。

类型修订含4,000,000像素上限的明确本地常量、动态加载spec/loader存在性断言，以及已知合成Sequential中只对Linear重置参数。后者对当前模型结构等价，不属于此前AST相同的纯格式修改，真实冷训练验证另记录。
