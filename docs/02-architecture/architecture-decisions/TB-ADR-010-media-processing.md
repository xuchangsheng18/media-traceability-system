# TB-ADR-010 媒体处理

2026-10-12；accepted-development；适用miniforge-py310-linux-x86_64-cpu。实际执行由本会话完成；正式批准人与生产准入待指定，不填入虚构人名。原设计ADR-01—05不覆盖。

决定：Pillow / imageio-ffmpeg0.6.0 / FFmpeg7.0.2-static。

比较的替代方案：PyAV；OpenCV。本轮选择理由：图片原件与分析副本分离，实际10帧视频编码解码；不过度安装未用媒体栈。

精确版本/来源：仓库根目录 `config/versions.yaml`，并结合config/versions.yaml和config/locks中的实际包/镜像摘要。未选产品不锁定虚构版本。

验证证据：docs/00-project/validation内的 media-query-report.json、poc-integration-report.json；实际命令见ci-all-report.json及运行手册。资源按专用Compose上限和环境快照，不把快照当峰值。

未验证及后续要求：源时间戳映射、异常视频、真实格式、正式再分发许可。

回退/变更：以旧Git快照和锁文件恢复应用；卷与数据保留，数据库另经版本迁移；新选型新增ADR并引用本记录，不删旧证据。正式环境变化时重测相关CI、契约、恢复和许可。

## 1.1证据补充

非零5秒原点的合成FFV1视频抽源帧0/5，实际PTS和像素标记核对通过，见[media-timestamp-report.json](../../00-project/validation/media-timestamp-report.json)。VFR、正式视频流水线与跨模态时轴仍未验收。
