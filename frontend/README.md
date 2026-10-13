# 前端工程

2026-10-13文档状态更新；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

Vue3/TypeScript/Vite研发验证台；package.json和package-lock.json精确锁；src/api.test.ts两项；e2e/workflow.pw.ts实际浏览器上传与结果；界面明确合成模型身份。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
npm --prefix frontend ci
npm --prefix frontend run test
npm --prefix frontend run build
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

正式页面、组件库Q-12、案件/审核/证据/报告流程尚未实现；类型生成物不等于全部API已有实现。

1.1类型生成增事件声明；端到端通过MT_RUNTIME_DIR读取当前临时凭据，支持GitHub一次性Runner。截图前清空令牌，禁止凭据进入报告。
