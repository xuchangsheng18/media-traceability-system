# 容器与代理

2026-10-12；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

docker-compose.yml定义7服务、5卷、专用网络和回环端口；Dockerfile.py310打包实际环境，frontend/Dockerfile构建静态页面；nginx.conf动态解析API地址。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py pack
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py build
/opt/conda/glwy/envs/py310/bin/python scripts/poc_control.py up
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

开发环境包不提交Git；没有生产自动部署。down保留卷，禁止直接对既有业务库初始化或清理其他项目。Desktop磁盘/许可和生产Engine需落实。

## 1.1工程补充

1.1 Seaweed master关闭telemetry，/data同时保留filerldb2及volume；冷备在新卷恢复原VersionId。支持MT_DOCKER_CONTEXT=default的托管Engine；生产部署未批准。
