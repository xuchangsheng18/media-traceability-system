# TB-ADR-014 私有GitHub与一次性托管CI

状态accepted-development；2026-10-12。用户明确提供xuchangsheng18/media-traceability-system.git；API实查为私有空仓库、具有推送权限、Actions已启用。正式部署平台仍未批准。

采用GitHub-hosted ubuntu-24.04，每次复建锁定Miniforge py310（与用户环境同Python/包版本）及Node，再运行同一21门禁脚本。无需将内网Linux主机注册成Runner或复制其秘密；一次性开发凭据仅存在Runner临时目录。Actions固定提交摘要、安装包核验SHA，checkout不保存凭据，权限contents:read，仅非秘密验证制品留存14天。

备选为内网self-hosted或GitLab Runner。内网地址/权限/隔离和组织治理尚未落实，当前用户指定GitHub；GitLab模板保留参考。托管容量/网络/额度失败如实记录，不能跳过测试；托管run及制品是否通过以[github-actions-report.json](../../00-project/validation/github-actions-report.json)为准，文件存在不是执行证据。

没有自动生产部署或发布权限。分支保护/必须检查、组织负责人和制品库是后续治理条件。若托管不可用，保留服务器本机21门禁证据并标平台未通过，不以本机结果冒充托管。更多见[CI说明](../../03-development/ci-cd.md)。
