# 查询审计事件：listAuditEvents

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `bffa82adf57b9ccf1888d5589e7b3d54f03915c7b150bac6dcc627779d4769b4`。契约未冻结，文档存在不代表接口已实现。

`GET /api/v1/audit/events`；operationId=`listAuditEvents`；源指针=`/paths/~1audit~1events/get`。

实现范围：**CONTRACT_ONLY_NOT_IMPLEMENTED_AS_BUSINESS_API**；当前无此正式业务端点完成证据。正式55业务操作仍为候选，当前PoC只有专门列出的开发入口。

## 调用目的与权限

查询审计事件；按已授权流程及以下源契约提交或读取。

OpenAPI身份声明：`[{"bearerAuth": []}]`；功能权限候选：`audit.read`。

核验审计组织/案件范围；case_id=null不是全库许可，跨范围策略待确认。

来源任务：[T018 开发审计查询页面与接口](../../../tasks/frontend/T018.md)。

关联需求：FR-OPS-001、ER-T018、NFR-SEC-001、NFR-AUDIT-001；关联候选表：audit_event。表引用不证明代码已使用或有访问授权。

## 参数与请求

| 参数 | 位置 | 必填 | 结构限制 |
| --- | --- | --- | --- |
| X-Request-Id | header | False | string; format="uuid" |
| limit | query | False | integer; minimum=1; maximum=100; default=20 |
| cursor | query | False | string; minLength=1; maxLength=128 |

源契约未定义请求体；查询通过上述路径/查询参数传入。

## 响应、状态与下一步

| HTTP | 描述 | 媒体类型/结构 | 响应头 |
| --- | --- | --- | --- |
| 200 | 契约成功响应；异步受理不代表结果完成 | application/json: AuditEventPage | X-Request-Id: string; format="uuid"; ETag: string; minLength=1; maxLength=128 |
| 400 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 401 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 403 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 404 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 409 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 422 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 429 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |
| 503 | 失败，错误码见error-codes.md | application/problem+json: Problem |  |

成功结构：`AuditEventPage`，详细字段见[数据结构](../data-structures.md#auditeventpage)。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=AuditEvent | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

成功结构样例（不证明实际执行）：

```json
{
  "items": [
    {
      "event_id": "3acba418-ba90-511c-9ab9-44cd4f56dbfc",
      "actor_id": "131fd3ec-4600-5eaf-889e-e5fa979b3e32",
      "org_id": "25b9ef1e-28bc-5e80-bf76-98eb857c30ef",
      "case_id": "2bb114bb-cc5f-52d3-a6e3-507cf6726bf1",
      "action": "synthetic-v1",
      "object_type": "synthetic-v1",
      "object_id": "93f1c664-1f6a-5642-8936-b67a474600cc",
      "object_version": 1,
      "outcome": "allowed",
      "request_id": "96985bd1-b8a4-5942-adc6-19fb6b7227f0",
      "occurred_at": "2030-01-01T00:00:00Z"
    }
  ],
  "next_cursor": "synthetic-v1"
}
```

按响应对象/结果及实际版本读取；再核验状态、缺失模态/证据和权限。候选结果不等于业务批准。

该接口未声明If-Match，不能从全局说明擅自增加必填请求头；业务对象/结果版本仍按请求结构和操作语义校验。

声明Idempotency-Key的操作按主体、操作和请求摘要去重；同键不同摘要409。有效保存期、超时/背压具体数值见待评审配置缺口，不能假定任意TTL。错误结构与恢复见[统一规则](../common-interface-rules.md)和[错误码](../error-codes.md)。

## 字段与数据库对应

| 方向/字段 | 当前映射 | 处理说明 |
| --- | --- | --- |
| response/items | 服务层输入/聚合，不直接生成数据库列 | 分页/聚合投影，明细按子结构对应表 |
| response/items[].event_id | audit_event.event_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].actor_id | audit_event.actor_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].org_id | audit_event.org_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].case_id | audit_event.case_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].action | audit_event.action | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].object_type | audit_event.object_type | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].object_id | audit_event.object_id | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].object_version | audit_event.object_version | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].outcome | audit_event.outcome | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/items[].request_id | audit_event.request_id | 请求追踪/审计，不作为业务对象ID |
| response/items[].occurred_at | audit_event.occurred_at | 服务层契约输入/聚合结果；下层关联与持久化按操作表清单及源任务核验；不生成无依据列。 |
| response/next_cursor | 服务层输入/聚合，不直接生成数据库列 | 服务端根据稳定排序与授权条件编码，不持久化权限范围 |

映射源：[api-field-mapping.json](../../04-database/api-field-mapping.json)。必须继续核验外键、案件域、版本、授权用途与SQL迁移，不能直接把任意字段写入表。

## 联调与验收条件

关联计划用例：TC-OPS-001-E、TC-OPS-001-N、TV-T008-E、TV-T008-N、TV-T011-E、TV-T011-N、TV-T012-E、TV-T012-N、TV-T013-E、TV-T013-N、TV-T014-E、TV-T014-N、TV-T015-E、TV-T015-N、TV-T016-E、TV-T016-N、TV-T017-E、TV-T017-N、TV-T018-E、TV-T018-N、TV-T102-E、TV-T102-N、TV-T104-E、TV-T104-N、TV-T107-E、TV-T107-N、TV-T108-E、TV-T108-N、TV-T118-E、TV-T118-N。这些ID是测试计划引用，不是本页接口的运行通过证据。

实施至少核验正常请求、Schema/跨字段错误、身份与跨案件拒绝、声明的幂等/条件并发、异步完成/失败及权限撤销；下载另测Range与版本完整性。实际端点的测试和证据按任务卡登记。未完成项见[接口缺口](../interface-gap-register.md)。
