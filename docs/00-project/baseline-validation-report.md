# 本轮文档检查范围

版本：0.1；整理日期：2026-10-12；状态：规划草案，NOT_FROZEN。

本轮运行scripts/validate_inputs.py验证语法、Schema、OpenAPI、夹具、SQL语法、字段映射、170任务依赖及追踪关系；结果以[输入校验JSON](validation/local-validation-report.json)为准。

运行scripts/validate_repository_docs.py检查Markdown相对链接、规划状态、来源原件摘要及关键目录；结果以[文档校验JSON](validation/repository-docs-validation.json)为准。检查链接文件存在不等于验证所有文字语义，外部网址本轮未逐条联网复核。

历史隔离SQL验证保留在validation/upstream；本轮未重新执行SQL、部署业务或运行模型。输入包的机器契约仍为候选，校验通过不能证明生产正确性或正式冻结。

本轮交付清单为repository-file-manifest.json，排除它自身及同步回执，以避免自引用摘要。旧baseline-file-list及baseline-file-manifest在本轮生成，含义仅为规划资料快照，不是正式冻结标签。

## 本轮数据库修订

当前SQL的实测结果使用[database-foundation-report.json](validation/database-foundation-report.json)，字段和API语义检查使用[database-contract-report.json](validation/database-contract-report.json)。旧SQL报告仍保留为历史，不对应本轮新增头表。文档导航和交付清单在本轮重新生成。


## 第二阶段README补充检查

本轮只改目录说明和交付计划，结果见[stage-two-readme-report.json](validation/stage-two-readme-report.json)。数据库结构和约束未变化，本轮未重复运行隔离数据库或模型测试；上一轮数据库报告继续仅对应其SQL摘要。

## 0.4本轮适用验证

当前SQL和证据规则使用database-foundation-report.json；字典来源及API语义使用database-contract-report.json；详细导航覆盖使用documentation-completion-report.json。READMEs的阶段状态仍为NOT_FROZEN。旧报告仅对其记录的摘要和范围有效，资料检查不替代业务实现。

## 1.0-py310-cpu当前适用验证

此前0.1—0.4各段为历史范围；当前已运行真实CPU工程、同源本机18道CI门禁、SQL/恢复/媒体/浏览器验证，见[技术验证报告](../02-architecture/technical-validation-report.md)及各专项JSON。输入原件摘要、全部实际文件导航、62表824字段来源检查通过。正式生产仍NOT_FROZEN，未用输入检查代替业务模型/权限/性能验收。

## 1.1第一阶段材料与导航补齐

前述0.1—1.0段为各轮历史范围，18门禁不是当前21门禁。第一阶段当前24步、实际材料、来源、历史身份和阶段衔接见[第一阶段入口](stage-one/README.md)；本轮文档与引用核验见[stage-one-validation-report.json](validation/stage-one-validation-report.json)。二阶段实际平台按github-actions-report记录。本轮未改SQL/业务代码或重新向已有数据库执行测试；源SQL摘要一致时引用先前隔离结果。正式输入与技术基线都仍NOT_FROZEN。
