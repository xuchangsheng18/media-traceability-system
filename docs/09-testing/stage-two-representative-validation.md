# 第二阶段新增代表性运行验证

2026-10-13。环境为用户现有Miniforge py310。所有素材和主体为自建测试数据，测试不承接真实业务授权或法定结论。

| 执行入口 | 实際断言与证据 | 范围限制 |
| --- | --- | --- |
| scripts/verify_stage_two_isolation.py | 21项：缺上下文不可读、单位/案件隔离、跨界INSERT拒绝、历史版本追加、UPDATE/DELETE/ACL修改拒绝、事务上下文清除、ACL撤销后读写拒绝、角色与RLS标记；中文词项/AND/未知/空查询/标点/正规化/GIN计划 | 新隔离PostgreSQL16；未接正式身份，未修改已有数据库；4条文本，仅词项匹配，没有中文语义准确率、大规模索引或业务API |
| scripts/verify_stage_two_media.py | 11项：8帧无损VFR的精确PTS、非等间隔、帧无丢失重复、每隔一帧源PTS及像素绑定、音频5秒原点和12800样本、字幕5.1—5.4秒、顺时针90度半开坐标与像素、原件摘要不变 | 自建视频/PCM/字幕；非真实OCR/ASR、全部编码/裁剪/转码/长视频性能 |
| scripts/validate_stage_two_completion.py | 6组：容量分级/最小余量、非法快照拒绝、离线摘要核对、篡改/缺失/越界/重复/空清单拒绝、12项覆盖与真实条件、23步/170任务/py310/未冻结 | 控制工具和材料验证，不是生产运行/业务指标 |
| scripts/collect_stage_two_software.py | 读取7个项目服务、去重5镜像和已安装OS包，生成SPDX2.3物料与摘要 | 采集不是漏洞扫描；没有许可结论，未托管二进制/Conda/npm/权重另行盘点；镜像ID不自动等于分发摘要 |

```sh
PY=/opt/conda/glwy/envs/py310/bin/python
$PY scripts/verify_stage_two_isolation.py
$PY scripts/verify_stage_two_media.py
$PY scripts/validate_stage_two_completion.py
$PY scripts/collect_stage_two_software.py
```

隔离数据库在tmpfs内，用固定本机已有PostgreSQL16镜像，不拉取镜像，测试后仅删除本次临时容器。已有7服务无重启。媒体文件在临时目录生成后清理，报告保留源摘要、PTS和抽帧映射。

VFR原始时轴为5000、5100、5400、5500、6000、6100、6400、6500毫秒；不能按帧序号除以平均帧率取代PTS。旋转坐标使用整数像素半开边界：64×48源框[4,8,14,20]顺时针旋转到48×64的[28,4,40,14]。新报告不改写旧CFR/非零PTS报告的未验证字段。机制参见[FFmpeg官方文档](https://www.ffmpeg.org/ffmpeg.html)。

中文实验采用NFKC、连续汉字二元词项、标点断开、查询词项AND与GIN text[]；单字保留，无词项拒绝查询。它可复现“证据/溯源”词项机制，不支持拼音、词义、同义词、OCR纠错或业务排序。正式分词须单独选型、版本化且按案件权限过滤。

CI在原21道门禁之外增加材料控制、隔离/中文、VFR和镜像物料采集4道，共25道。实际托管run/源码SHA/制品摘要以[GitHub报告](../00-project/validation/github-actions-report.json)为准；新代码入库本身不等于已经通过本轮CI。
