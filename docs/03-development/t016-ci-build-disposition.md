# T016 CI 构建输入与回归基线修订

核对日期：2026-10-21。此处记录已有 CI 构建失败及独立目录中的真实编译验证，不将本地布局验证计为容器构建或新提交的 CI 通过。

## 已观察的失败

[GitHub Actions run 39463909701](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39463909701) 对应基线 `00725b051dbd735fdb60cdde33bbb7179cc2cdc9`，工程总报告为 `FAIL`。同一基线的 T014、T015 报告分别为 709、128 项通过且无失败、错误或跳过；这些历史结果不证明当前 T016 未提交改动通过 CI。

失败发生在前端 Docker 构建阶段的 `npm run test && npm run build`：`src/business/api.ts` 引入 `../../../shared-contracts/generated/business-api`，但构建阶段的 `/ui` 仅取得 `frontend`，没有 `/shared-contracts`。`vue-tsc` 因此报告 TS2307，继而在 `AuditView.vue` 报告 TS7006。生产构建输入缺失是这两项错误的共同原因。

Compose 已将仓库根目录作为构建上下文。现有 `/ui/src/business/api.ts` 的该相对路径解析到 `/shared-contracts/generated/business-api.d.ts`，故在 [frontend/Dockerfile](../../frontend/Dockerfile) 的 `COPY frontend ./` 后补入：

```dockerfile
COPY shared-contracts /shared-contracts
```

两个基础镜像的版本与 digest、`npm ci`、`npm run test && npm run build`、`/ui/dist` 和 nginx 运行产物位置均保留。业务 API、AuditView、TypeScript 严格规则及依赖锁没有为此修改。

## 隔离目录中的 RED / GREEN

使用已存在的 Windows Node `v22.21.1`，在 `_work/t016-ui-docker-layout-f5fc919232734806a350e1a0c8e4af96` 新建 `ui`，只复制 Git 跟踪的公开前端文件，并完整复制现有 `node_modules`。没有安装依赖，也没有通过共享依赖目录运行编译。

两次执行使用相同的 `npm run build`、工作目录、锁和前端文件；GREEN 唯一增加的构建输入是同级 `shared-contracts` 目录。实际命令由锁定的 `node.exe` 调用同目录的 npm CLI，并将该 Node 目录置于子进程 PATH 首位。

| 阶段 | 实际开始／结束（UTC） | 退出码 | 实际结果 |
| --- | --- | --- | --- |
| RED：仅 `ui` | 2026-10-20 18:25:31／18:25:45 | 2 | 复现 TS2307 和 TS7006，未生成 `dist/index.html` |
| GREEN：补充 `shared-contracts` | 2026-10-20 18:26:02／18:26:09 | 0 | `vue-tsc --noEmit` 与 Vite 构建完成，生成 `ui/dist/index.html` |

RED、GREEN 前后对 `package.json`、`package-lock.json`、`tsconfig.json`、业务 API、AuditView 和生成契约逐一核对 SHA-256，均保持一致。`package-lock.json` 为 `1b4c6eb93df7f3e67bfb76751915f0ebf0d2c8cefb72e5eb0cbfeaaccccbb0e5`。修复后的 Dockerfile 为 `af65cd617fa8b37ad2fc1c336c435fa57897ea732749ea71bc757cfe93253aa2`。

安全结果保存在上述隔离目录的 `safe-result.json`，单次入口为仓库外 `_work/t016-frontend-layout-check.py`；原始 CI／编译日志只保留在 `_work` 私有材料中，不复制到本页。

## 尚未执行的验证

本次 `container_build_executed=false`。未运行 Docker 构建、共享栈、SQL 或服务重启，未改动源前端的 `dist`、`node_modules` 或现有预览进程。真实 Linux／Alpine 容器构建及修复提交对应的完整托管 CI 仍由主会话后续执行并记录确切 SHA、run URL 和结果。

## 完整 CI 回归发现的两项旧基线断言

[GitHub Actions run 39478665682](https://github.com/xuchangsheng18/media-traceability-system/actions/runs/39478665682) 对应提交 `1b76a46ad52d9f67f549ee59da685ab79e6b9265`。该 workflow 整体最终为 `cancelled`，但工程中的完整 business 步骤已经实际执行失败：611 项、2 个失败、0 个错误、0 个跳过，并非超时。workflow 的取消状态不能覆盖该步骤及其安全制品记录的实际失败；本轮不将此提交登记为完整 CI 通过。

完整 business 制品未提供失败 nodeid。随后在隔离环境中保留旧断言，实际执行以下定向 RED 命令；`PRIVATE_PATH` 是安全报告对私有 JUnit 路径的占位符：

```text
python -m pytest tests/business/test_remaining_contracts.py::test_runtime_openapi_is_authoritative_and_only_publishes_mounted_operations tests/business/test_t015_scope_owner.py::test_non_super_owner_metadata_port_and_runtime_acl -q --tb=short --junitxml PRIVATE_PATH
```

实际 RED job 为 `94b39d889f31425cbb314b2713b355d4`，源码基线为 `672b321f47d686765d3024d4a984244685061f6a`；2026-10-20 19:43:54.266897—19:44:35.200835 UTC 执行，退出码 1。安全结果 `_work/t014-rule-test-94b39d889f31425cbb314b2713b355d4.json` 逐项确认这两个 nodeid 均失败，共 2 项、2 个失败、0 个错误、0 个跳过：

| 实际失败 nodeid | 旧断言与本轮修订边界 |
| --- | --- |
| `tests/business/test_remaining_contracts.py::test_runtime_openapi_is_authoritative_and_only_publishes_mounted_operations` | 旧总数 43 已包含 `internalInference`，新增签发路由后应分列 43 个外部操作及唯一内部操作 `internalInference`，总数 44；同时要求外部集合含 `issueOperationToken`。未挂载操作排除、102 个组件、审批结构引用、内部鉴权和请求标识拒绝断言均保留。 |
| `tests/business/test_t015_scope_owner.py::test_non_super_owner_metadata_port_and_runtime_acl` | 旧完整迁移期待只列 0001—0010；改为逐项匹配 0001—0011。真实非超级用户 owner、固定函数 owner/search_path、PUBLIC 无 EXECUTE、runtime 显式授权、元数据读取及特权连接拒绝断言全部保留。 |

这两项此前不在 T014／T015／T016 专项门禁选择的测试集合中，专项通过未覆盖其旧基线断言。此次保留完整 business 范围及现有超时、全部专项门禁和故障探针，不删除、跳过或缩选测试，也不降低权限、ACL 或其他语义断言。原始 0001—0010 迁移和原始 825 字段 SQL 基线不因本轮修订重写。

修订后的定向 GREEN job `8889f55ee91a4d938c7fcc67fe748384` 已于 2026-10-20 19:45:32.717019—19:46:22.856690 UTC 实际执行完成，退出码 0：上述 2 项均通过，0 个失败、0 个错误、0 个跳过；Ruff lint、Ruff format 和 mypy 三项也均通过。安全结果保存在 `_work/t014-rule-test-8889f55ee91a4d938c7fcc67fe748384.json`，源码基线仍为 `672b321f47d686765d3024d4a984244685061f6a`，并绑定本批修订的工作树摘要。

这 2 项定向 GREEN 不表示完整 611 项通过。修订后的完整 business 回归及新提交对应的托管 CI 尚待验证；实际后续状态统一见[本批开发进度](../00-project/validation/t016-development-progress.json)。本节记录回归基线修订，不扩展上节 `container_build_executed=false` 的局部验证范围。
