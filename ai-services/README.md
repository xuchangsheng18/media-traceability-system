# 训练与推理服务

2026-10-13文档状态更新；CPU研发工程已验证，正式业务/生产NOT_FROZEN。

inference/service.py首次启动真实训练64条随机张量120步，保存权重/实验；后续只加载固定权重。独立CPU推理复用M15 Schema并写版本化8维向量。实际服务经Compose启动。

## 验证入口

Linux仓库根目录运行，前置为已锁py310、Node及独立开发栈（适用时）：

```sh
/opt/conda/glwy/envs/py310/bin/python scripts/verify_poc.py
```

详细启动、资源、影响与排查见[运行手册](../docs/10-deployment/development-runbook.md)，结果见[验证报告](../docs/02-architecture/technical-validation-report.md)。

## 来源与完成边界

外部API源docs/03-api/openapi.yaml；内部入口源inference-openapi.yaml；模型/数据结构源schemas/model及schemas/dataset。任务范围仍为12模块170项。

synthetic-cpu-encoder/demo-1不是SSCD；业务权重、OCR/ASR等模型、GPU/CUDA、准确率/校准和容量均未验收。

1.1内部推理共用安全Problem与任务原始request_id；worker实际校验M15响应Schema及任务/run/model/mapping身份。原CPU权重保持，恢复不得以重训代替。
