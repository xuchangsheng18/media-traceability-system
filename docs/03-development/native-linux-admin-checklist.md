# 原生研发环境：徐昌胜的管理员执行清单

日期：2026-10-17。用户已确认徐昌胜可以承担一次性管理员操作。设计/实施计划及候选资源上限已获认可，N01只读工具已实现；原生制品、服务账号和单元尚未安装，不能将本页当安装已完成。

## 现在可执行的只读预检

在172.16.58.179上执行，结果仅需告知是否具备权限、失败单元是否影响本项目及路径是否可用；不要发送密码、私钥、cookie、完整环境变量或数据库连接串。

```bash
sudo -v
systemctl --failed --no-pager
findmnt -T /workspace -o TARGET,SOURCE,FSTYPE,OPTIONS
findmnt -T /opt -o TARGET,SOURCE,FSTYPE,OPTIONS
df -h /workspace /opt
test -x /opt/conda/glwy/envs/py310/bin/python
test -x /workspace/glwy/runtime/media-traceability-system/business-postgres-tools/bin/postgres
```

`sudo -v`由徐昌胜在服务器本地交互完成；密码不交给Codex。只读结果不授权修复其他项目的失败单元、改变全机安全策略或增加广泛sudo权限。

## 设计和实施计划认可后的一次性工作

1. 核对最终软件清单：版本、架构、官方来源、包签名/摘要、依赖、许可和漏洞记录齐全。原生包锁单独存放；不得用`apt install`未锁版本或解包容器根文件系统代替可维护的原生发行包。
2. 按最终清单创建专用无登录系统账号：PoC/业务/身份数据库分别隔离，broker、对象、身份、网关按职责分别设置；不得给账号交互登录、广泛sudo或互读全部秘密的公共组。
3. 建立`/opt/media-trace-native/`只读制品根、`/etc/media-trace-native/`私密配置根和`/workspace/media-trace-native/`新数据根。父目录由管理员控制，子目录按具体服务分配；不更改已有数据库/卷所有权来代替迁移。
4. 安装经核对的原生运行时或复制已核验工具制品；保持现有Miniforge py310及其100包锁。精确安装命令、包文件和摘要将在实施计划中生成；当前没有可盲执行的安装脚本。
5. 安装已审阅的`mt-native-*.service`和项目slice。先运行`systemd-analyze verify`检查具体单元文件，再`daemon-reload`，只启动独立暂存实例。
6. 校验每单元User、UMask、路径所有权、私密文件可读范围、网络监听、CPU/内存/PID和临时目录限制；核对真实cgroup读值。安装配置不能当作实际生效证明。
7. 按隔离恢复计划创建新PG数据目录、broker节点和对象目录；旧容器、现有原生业务实例和现用端口继续保留。不要执行`docker compose down -v`、`docker volume rm`或全局清理。
8. 完成恢复与故障演练，审阅实际停写/切换和数据水位报告后，再执行本项目切换清单；不要提前开启新实例对现用业务的写入口。

每步记录：执行人徐昌胜、实际时间、源码/制品摘要、目标路径或单元名、结果、失败与恢复动作。只有实做结果才能写为PASS；没有执行仍记NOT_EXECUTED。

## 当前交接状态

| 项目 | 状态 |
| --- | --- |
| 管理员参与能力 | 用户确认可以，由徐昌胜执行 |
| 书面迁移设计 | 用户已认可 |
| 精确安装/迁移实施计划 | 已编制并获用户认可，见[native-linux-implementation-plan.md](native-linux-implementation-plan.md) |
| N01制品与工具 | 只读工具已实现；实际制品及完整依赖锁未齐，尚未生成可执行管理员安装包 |
| 服务器原生安装/切换 | 未执行 |
| 旧数据备份及可恢复验证 | 待新迁移批次执行；旧研发恢复报告仅作参考 |
| 旧容器/卷撤销 | 未授权删除；本阶段保留 |

架构与恢复依据见[原生迁移设计](native-linux-migration-design.md)。
