# 复现命令

运行目录：工程包根目录。前置：Python3.12及获准网络或离线wheelhouse安装requirements-input-validation.txt。命令：python scripts/validate_inputs.py；可加--task T001，输出仍为资料检查而非实现通过。

SQL复现：有权新建隔离PostgreSQL16空库，psql -v ON_ERROR_STOP=1 -f docs/04-database/initial-schema.sql，然后同连接/同库执行tests/sql/integrity-tests.sql。禁止已有业务数据库初始化。实际本轮引擎与隔离/清理记录见sql-validation-report.json；schema role不含LOGIN和真实密码。
