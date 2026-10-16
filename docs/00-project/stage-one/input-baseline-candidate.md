# 当前第一阶段候选输入清单

状态：**NOT_FROZEN**。没有批准编号或实际签认人。本清单标识当前用于评审/研发的输入文件，不表示全部代码任务实施、服务器同步或业务验收完成。机器版本见[input-baseline-candidate.json](input-baseline-candidate.json)。

本次候选共760个文件，按实际字节计算SHA-256；仅覆盖JSON selection定义的输入目录、24步交付及来源章节目标。运行验证报告、历史归档、旧快照、自身两文件与全仓同步清单排除，避免自引用及时间戳变化。校验时重新计算集合/大小/摘要，任何输入变化都需重新生成候选，不能仅修改摘要绕过审查。

旧baseline-file-list.txt和baseline-file-manifest.json保留原字节摘要，仅作为历史输入快照；全仓同步另用repository-file-manifest.json与server-sync-receipt.json。

正式冻结前需按[冻结检查表](../freeze-checklist.md)取得适用范围、权限/规则/指标/用途、人员资源、遗留及授权记录。批准后仍须保存该候选与决定的对应关系，不得从本文件推导批准或自动生成正式标签。
