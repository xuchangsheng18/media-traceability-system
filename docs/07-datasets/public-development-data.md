# 公开研发样本与使用方法

2026-10-21：用户明确允许从网上获取开发数据。本批已取得两张无人物的公开图片，并在当前 Linux / py310 环境执行实际解码。样本可用于媒体接入、摘要、尺寸及已知变换流程开发；没有据此形成案件数据、风险标签、真实同源关系或模型准确率结论。

## 实际样本

| 文件 | 原始发布版本 | 大小 | 实测尺寸 | 来源与许可 |
| --- | --- | ---: | --- | --- |
| chelsea.png | scikit-image v0.25.2 | 240512字节 | 451 × 300 | Stefan van der Walt；[逐图CC0声明](https://scikit-image.org/docs/0.25.x/api/skimage.data.html#skimage.data.chelsea) |
| horse.png | scikit-image v0.25.2 | 16633字节 | 400 × 328 | Andreas Preuss (marauder)；[逐图CC0声明](https://scikit-image.org/docs/0.25.x/api/skimage.data.html#skimage.data.horse) |

总计257145字节。下载文件的SHA-256与[官方v0.25.2摘要登记](https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/_registry.py)一致。CC0的使用范围见[许可原文入口](https://creativecommons.org/publicdomain/zero/1.0/)；这里依据逐图声明，不把scikit-image软件许可证套用于所有数据。

本地实物：`D:\公安厅项目\_work\public-development-data\scikit-image-v0.25.2`。

Linux实物：`/workspace/glwy/runtime/media-traceability-system/public-development-data/scikit-image-v0.25.2`。

媒体实物位于仓库外；仓库保留[固定清单](../../datasets/public-development/manifest.json)、[工具与命令](../../datasets/public-development/README.md)及[实际回执](../00-project/validation/public-development-data-report.json)。工具只取清单内的小文件，核对版本、大小和摘要，不安装scikit-image或其他包。

## 当前验证范围

两张原始图片已经人工查看，Linux现有`inspect_uploaded_media`完整解码及尺寸检查成功；错误摘要和错误MIME均被拒绝。本地和Linux文件摘要相同。下载工具的离线拒绝测试、实际获取和复用检查分别记录在回执中，不把离线传输夹具标作实际上游下载。

`horse.png`是轮廓样例，不是某张自然照片的分割标注。`chelsea.png`可生成缩放、裁剪等已知变换样本，派生样本须记录父文件摘要和变换参数；同父组不能跨训练与封存测试集合。派生标注只能表明构造变换，不能伪造真实传播链或业务类别。

## 对任务的作用及剩余输入

本批支持T026/T041等现有图片解码的研发回归，也为T043/T079/T109等后续工程提供可追溯的小样本输入；没有替这些任务生成未实现的生产服务。15类业务数据卡保持原规划/授权待定状态，不改成已核验业务数据。

真实视频、多编码/VFR样本、OCR/ASR文本与时间标注、风险/篡改标签、检索与首发真值、独立封存验收集，以及业务模型权重/许可/适配实现仍需逐项建立。尚未选取的网上数据不自动取得可用状态；本批没有下载人物、案件资料、大型语料或模型权重。

返回[数据专题](README.md)、[分步任务导航](../../tasks/README.md#分步任务导航)、[T001—T123逐项审计](../03-development/t001-t123-development-completion-audit.md)。
