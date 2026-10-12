# 第一阶段开发输入工程资料包

本包依据当前DES-001 V1.4及TASK-001 V1.3，补齐接口与模型/数据契约、SQL与字典、独立任务卡与追踪、测试设计及工程规则。当前为待评审候选输入，不是正式批准基线；结构和数据库验证结果见docs/00-project/validation/。

## 阅读和使用顺序

1. docs/00-project/补齐完成说明.md、source-document-inventory.md及open-questions.md。
2. docs/03-api/openapi.yaml、inference-openapi.yaml、schemas/model/与schemas/dataset/。
3. docs/04-database/initial-schema.sql、data-dictionary.md、api-field-mapping.csv。
4. tasks/README.md、backlog.yaml及逐项任务卡。
5. docs/09-testing/test-strategy.md、场景YAML与模型/安全测试说明。
6. docs/00-project/baseline-1.0.md及baseline-validation-report.md。

原件保留在docs/source，阶段手册在docs/guides；更新后的Word转换稿在docs/_converted。不得将旧专题稿直接当新执行基线。资料复制进Linux工程根目录后，使用相对路径；Python校验工具依赖单独安装，未确定业务依赖版本不写成生产锁定。

本包未初始化Git、未上传服务器、未实现业务服务或训练真实模型。SQL只在新建隔离测试数据库验证，不能直接运行到已有业务数据库。
