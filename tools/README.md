# 工程辅助工具

工程入口集中在[scripts/dev.py](../scripts/dev.py)，质量工具版本按[第三阶段工具锁](../config/locks/requirements-stage-three-quality.lock)管理，工具运行缓存位于仓库外。本目录为后续开发辅助工具预留，不重复业务API、模型能力或数据Schema。

不得纳入系统安装包、大型二进制、真实秘密、模型权重和数据。工具引入须明确用途、版本/许可、可复现安装及实际验证；预留目录不计作业务任务实现。
