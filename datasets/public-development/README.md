# 两张公开开发图片

本目录只保存固定版本的来源、逐图许可和预期字节摘要。原始图片放用户显式指定的仓库外目录。目录存在不代表已下载或解码。

首包限定 scikit-image v0.25.2 的 `chelsea.png`（240512字节）和 `horse.png`（16633字节），共257145字节。逐图官方文档声明 CC0，创作者分别为 Stefan van der Walt 和 Andreas Preuss (marauder)；许可与官方摘要登记页见 [manifest.json](manifest.json)。没有从项目软件许可证推断全部示例图片均可使用。

从仓库根目录执行，仅使用 Python 标准库：

```powershell
python scripts/fetch_public_development_data.py --destination 'D:\公安厅项目\_work\public-development-data\scikit-image-v0.25.2'
```

`--destination` 必填，必须为用户控制的私有绝对路径，不能位于仓库内或为仓库的祖先目录；不要选择可由其他用户或进程随意替换目录层级的共享位置。默认总预算512KiB，最大预算严格低于1MiB；只能获取清单固定的两个HTTPS官方URL，禁止重定向。响应必须是PNG，大小、PNG签名和SHA256均须匹配。工具核验已有文件并复用，不覆盖篡改文件；临时文件验证后通过同目录硬链接原子发布，遇到同名写入则重新核验。符号链接、`..`路径与Windows重解析点被拒绝。

下载成功后，仓库外目录包含两张图片和来源清单副本；标准输出的 `PINNED_BYTES_VERIFIED_NOT_DECODED` 仅表示字节检查通过，解码、视觉检查及使用任务须另外实际执行。离线安全测试命令：

```text
python -m pytest tests/platform/test_public_development_data.py -q
```

样例只用于图像解码、元数据解析及变换/坐标工程检查。猫图的发布说明不构成业务标签；马轮廓不是一对自然照片分割真值。没有由此得到模型准确率、案件结论、真实来源授权或模型准入。清单的 `formal_case_import/training_authorized/acceptance_use` 均为false，表示本包没有授予这些项目权限；不否定CC0本身的版权许可。工具不连接数据库、不调用业务导入接口、不下载权重或其他素材、不执行远端内容，也不更改D01—D15业务数据卡。
