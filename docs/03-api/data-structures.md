# 业务接口数据结构详表

自动派生，禁止独立修改结构；权威源 `docs/03-api/openapi.yaml`，SHA-256 `3a19ef745a5d38a26d6c09a735c13d1200c8c46d0b84194862fde2012041d52f`。契约未冻结，文档存在不代表接口已实现。

共102个源组件；先读[整体说明](system-interface-specification.md)。每个组件给出字段表及完整原始Schema；required、null、枚举、引用、条件组合均保留。字段语义尚未独立定义的情况明确标记，不能把UUID当授权或把0—1分数当业务/法律概率。

## Uuid

源指针：`#/components/schemas/Uuid`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "string",
  "format": "uuid"
}
```

## Sha256

源指针：`#/components/schemas/Sha256`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "string",
  "pattern": "^[a-f0-9]{64}$"
}
```

## TimeRange

源指针：`#/components/schemas/TimeRange`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| start_ms | 必须 | integer; minimum=0 | 候选字段来源：risk_finding.start_ms：源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理；shot.start_ms：源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理；source_match.query_start_ms：查询媒体中匹配片段起点，单位毫秒，半开区间包含起点；source_match.source_start_ms：候选来源媒体中匹配片段起点，单位毫秒；tamper_finding.start_ms：源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理；text_segment.start_ms：源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理。来源引用不是写入许可，完整处理按操作核验。 |
| end_ms | 必须 | integer; minimum=1 | 候选字段来源：risk_finding.end_ms：源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms；shot.end_ms：源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms；source_match.query_end_ms：查询媒体中匹配片段终点，单位毫秒，半开区间不包含终点；source_match.source_end_ms：候选来源媒体中匹配片段终点，单位毫秒，必须大于对应起点；tamper_finding.end_ms：源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms；text_segment.end_ms：源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "start_ms": {
      "type": "integer",
      "minimum": 0
    },
    "end_ms": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "start_ms",
    "end_ms"
  ],
  "additionalProperties": false,
  "description": "[start_ms,end_ms)；语义校验要求end_ms>start_ms，并不超过媒体范围。"
}
```

## BoundingBox

源指针：`#/components/schemas/BoundingBox`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| x | 必须 | number; minimum=0; maximum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| y | 必须 | number; minimum=0; maximum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| width | 必须 | number; maximum=1; exclusiveMinimum=0 | 候选字段来源：media_asset.width：媒体帧或图像宽度，单位像素；有值时为正整数。来源引用不是写入许可，完整处理按操作核验。 |
| height | 必须 | number; maximum=1; exclusiveMinimum=0 | 候选字段来源：media_asset.height：媒体帧或图像高度，单位像素；有值时为正整数。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "x": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "y": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "width": {
      "type": "number",
      "exclusiveMinimum": 0,
      "maximum": 1
    },
    "height": {
      "type": "number",
      "exclusiveMinimum": 0,
      "maximum": 1
    }
  },
  "required": [
    "x",
    "y",
    "width",
    "height"
  ],
  "additionalProperties": false,
  "description": "原件归一化坐标；语义校验x+width<=1,y+height<=1。"
}
```

## ObjectRef

源指针：`#/components/schemas/ObjectRef`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| object_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键；audit_event.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键；evidence_item.object_id：所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用；media_asset.object_id：所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用；object_version.object_id：主键，由应用提供UUID；不视为访问凭证；package_item.object_id：所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用；report.object_id：所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用。来源引用不是写入许可，完整处理按操作核验。 |
| version_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：object_version.version_id：对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version。来源引用不是写入许可，完整处理按操作核验。 |
| sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：evidence_item.sha256：该证据版本绑定内容的SHA-256，摘要对象需在证据类型契约中明确；存储64位小写十六进制，正则只检查格式不验证字节真实性；media_asset.sha256：媒体资产字节的SHA-256，应与引用对象版本核对；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；package_item.sha256：清单中引用对象固定版本字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "object_id": {
      "type": "string",
      "format": "uuid"
    },
    "version_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    }
  },
  "required": [
    "object_id",
    "version_id",
    "sha256"
  ],
  "additionalProperties": false,
  "description": "只给受控标识，不给绕过鉴权的存储密钥或永久URL。"
}
```

## VersionBinding

源指针：`#/components/schemas/VersionBinding`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：risk_finding.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本；tamper_finding.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：risk_finding.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算；tamper_finding.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：risk_finding.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果；tamper_finding.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "task_id",
    "run_version",
    "result_version",
    "policy_version"
  ],
  "additionalProperties": false
}
```

## Problem

源指针：`#/components/schemas/Problem`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| type | 必须 | string; format="uri-reference" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| title | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | integer; minimum=400; maximum=599 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| code | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| message | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| details | 必须 | array; minItems=0; items=object; additionalProperties=false | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| details[].field | 必须（父对象存在时） | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| details[].reason | 必须（父对象存在时） | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| instance | 可省略 | string; format="uri-reference" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "format": "uri-reference"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "status": {
      "type": "integer",
      "minimum": 400,
      "maximum": 599
    },
    "code": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "message": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "request_id": {
      "type": "string",
      "format": "uuid"
    },
    "details": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128
          },
          "reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 4096
          }
        },
        "required": [
          "field",
          "reason"
        ],
        "additionalProperties": false
      },
      "minItems": 0
    },
    "instance": {
      "type": "string",
      "format": "uri-reference"
    }
  },
  "required": [
    "type",
    "title",
    "status",
    "code",
    "message",
    "request_id",
    "details"
  ],
  "additionalProperties": false
}
```

## Accepted

源指针：`#/components/schemas/Accepted`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.task_id：主键，由应用提供UUID；不视为访问凭证；task_event.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本；task_run.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["CREATED", "QUEUED", "RUNNING", "CANCEL_REQUESTED"] | 候选字段来源：analysis_task.state：分析任务当前投影的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| status_url | 必须 | string; pattern="^/api/v1/analysis/tasks/" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "CREATED",
        "QUEUED",
        "RUNNING",
        "CANCEL_REQUESTED"
      ]
    },
    "status_url": {
      "type": "string",
      "pattern": "^/api/v1/analysis/tasks/"
    }
  },
  "required": [
    "task_id",
    "state",
    "status_url"
  ],
  "additionalProperties": false
}
```

## ActionAck

源指针：`#/components/schemas/ActionAck`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| object_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键；audit_event.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_export.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_release.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；audit_export.state：审计导出作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；index_registry.state：索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；model_release.state：模型发布包的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.request_id：贯穿接口、任务和审计的请求追踪标识；不充当权限凭证。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "object_id": {
      "type": "string",
      "format": "uuid"
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "state": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "request_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "object_id",
    "version",
    "state",
    "request_id"
  ],
  "additionalProperties": false
}
```

## Health

源指针：`#/components/schemas/Health`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| status | 必须 | string; enum=["ok", "degraded", "unavailable"] | 候选字段来源：model_registry.status：模型版本与许可引用的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": [
        "ok",
        "degraded",
        "unavailable"
      ]
    },
    "request_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "status",
    "request_id"
  ],
  "additionalProperties": false,
  "description": "对外仅给聚合状态；版本、拓扑、依赖错误只对运维授权可见。"
}
```

## AuthLogin

源指针：`#/components/schemas/AuthLogin`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| username | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| password | 必须 | string; minLength=1; writeOnly=true | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "password": {
      "type": "string",
      "minLength": 1,
      "writeOnly": true
    }
  },
  "required": [
    "username",
    "password"
  ],
  "additionalProperties": false,
  "description": "仅开发适配器；正式统一身份接入方式待定。"
}
```

## AuthSession

源指针：`#/components/schemas/AuthSession`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| access_token | 必须 | string; minLength=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| token_type | 必须 | const="Bearer" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expires_in | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "access_token": {
      "type": "string",
      "minLength": 1
    },
    "token_type": {
      "const": "Bearer"
    },
    "expires_in": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "access_token",
    "token_type",
    "expires_in"
  ],
  "additionalProperties": false,
  "description": "不得在日志或测试证据中记录令牌。"
}
```

## CurrentUser

源指针：`#/components/schemas/CurrentUser`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| user_id | 必须 | string; format="uuid" | 候选字段来源：case_membership.user_id：用户与认证主体标识，指向users.user_id；user_roles.user_id：用户与认证主体标识，指向users.user_id；users.user_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| org_id | 必须 | string; format="uuid" | 候选字段来源：case_membership.org_id：记录所属单位标识；单位授权范围由服务端认证上下文确定；users.org_id：记录所属单位标识；单位授权范围由服务端认证上下文确定。来源引用不是写入许可，完整处理按操作核验。 |
| roles | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| permissions | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_ids | 必须 | array; minItems=0; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "format": "uuid"
    },
    "org_id": {
      "type": "string",
      "format": "uuid"
    },
    "roles": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 0
    },
    "permissions": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 0
    },
    "case_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 0
    }
  },
  "required": [
    "user_id",
    "org_id",
    "roles",
    "permissions",
    "case_ids"
  ],
  "additionalProperties": false
}
```

## SourceCreate

源指针：`#/components/schemas/SourceCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：source_registry.name：名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键。来源引用不是写入许可，完整处理按操作核验。 |
| source_type | 必须 | string; enum=["authorized_business", "public_licensed", "user_submission", "synthetic"] | 候选字段来源：source_registry.source_type：素材来源类别的编码；分类词表由接入配置定义，当前DDL未枚举限制。来源引用不是写入许可，完整处理按操作核验。 |
| authorization_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：source_registry.authorization_ref：来源授权凭据的受控引用，供核查用途和期限；不存访问令牌或明文密钥。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | array; minItems=1; uniqueItems=true; items=string; minLength=1; maxLength=128 | 候选字段来源：source_registry.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 候选字段来源：source_registry.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "source_type": {
      "type": "string",
      "enum": [
        "authorized_business",
        "public_licensed",
        "user_submission",
        "synthetic"
      ]
    },
    "authorization_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "purpose": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "expires_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "case_id",
    "name",
    "source_type",
    "authorization_ref",
    "purpose",
    "expires_at"
  ],
  "additionalProperties": false,
  "description": "提交不等于审批授权；服务端核验授权记录，返回pending或verified。"
}
```

## Source

源指针：`#/components/schemas/Source`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| source_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.source_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：source_registry.name：名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键。来源引用不是写入许可，完整处理按操作核验。 |
| source_type | 必须 | string; enum=["authorized_business", "public_licensed", "user_submission", "synthetic"] | 候选字段来源：source_registry.source_type：素材来源类别的编码；分类词表由接入配置定义，当前DDL未枚举限制。来源引用不是写入许可，完整处理按操作核验。 |
| authorization_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：source_registry.authorization_ref：来源授权凭据的受控引用，供核查用途和期限；不存访问令牌或明文密钥。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | array; minItems=1; uniqueItems=true; items=string; minLength=1; maxLength=128 | 候选字段来源：source_registry.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 候选字段来源：source_registry.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| authorization_status | 必须 | string; enum=["pending", "verified", "expired", "revoked"] | 候选字段来源：source_registry.authorization_status：来源或数据集用途授权的当前审核状态，未验证状态不得解释为可正式使用。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：source_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "source_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "source_type": {
      "type": "string",
      "enum": [
        "authorized_business",
        "public_licensed",
        "user_submission",
        "synthetic"
      ]
    },
    "authorization_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "purpose": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "expires_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "authorization_status": {
      "type": "string",
      "enum": [
        "pending",
        "verified",
        "expired",
        "revoked"
      ]
    },
    "version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "source_id",
    "case_id",
    "name",
    "source_type",
    "authorization_ref",
    "purpose",
    "expires_at",
    "authorization_status",
    "version"
  ],
  "additionalProperties": false
}
```

## UploadCreate

源指针：`#/components/schemas/UploadCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；upload_session.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| source_id | 必须 | string; format="uuid" | 候选字段来源：source_registry.source_id：主键，由应用提供UUID；不视为访问凭证；upload_session.source_id：数据来源登记标识，指向source_registry.source_id。来源引用不是写入许可，完整处理按操作核验。 |
| filename | 必须 | string; minLength=1; maxLength=255 | 候选字段来源：upload_session.filename：上传时提供的展示文件名；不得直接拼接为服务器文件路径。来源引用不是写入许可，完整处理按操作核验。 |
| size_bytes | 必须 | integer; minimum=1 | 候选字段来源：upload_session.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0。来源引用不是写入许可，完整处理按操作核验。 |
| mime | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：upload_session.mime：探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名。来源引用不是写入许可，完整处理按操作核验。 |
| sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：upload_session.sha256：上传方声明的完整文件SHA-256，合并后必须以实际字节重新计算核对；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "source_id": {
      "type": "string",
      "format": "uuid"
    },
    "filename": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255
    },
    "size_bytes": {
      "type": "integer",
      "minimum": 1
    },
    "mime": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    }
  },
  "required": [
    "case_id",
    "source_id",
    "filename",
    "size_bytes",
    "mime",
    "sha256"
  ],
  "additionalProperties": false,
  "description": "分片尺寸和总大小上限由经审核配置确定；文件名只作显示，不能形成系统路径。"
}
```

## UploadSession

源指针：`#/components/schemas/UploadSession`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| upload_id | 必须 | string; format="uuid" | 候选字段来源：upload_session.upload_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| part_size_bytes | 必须 | integer; minimum=1 | 候选字段来源：upload_session.part_size_bytes：上传会话约定的标准分片大小，单位字节；末片可小于此值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["UPLOADING", "VALIDATING", "COMPLETED", "REJECTED", "EXPIRED"] | 候选字段来源：upload_session.state：上传会话的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| expires_at | 必须 | string; format="date-time" | 候选字段来源：source_registry.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区；upload_session.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：source_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；upload_session.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "upload_id": {
      "type": "string",
      "format": "uuid"
    },
    "part_size_bytes": {
      "type": "integer",
      "minimum": 1
    },
    "state": {
      "type": "string",
      "enum": [
        "UPLOADING",
        "VALIDATING",
        "COMPLETED",
        "REJECTED",
        "EXPIRED"
      ]
    },
    "expires_at": {
      "type": "string",
      "format": "date-time"
    },
    "version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "upload_id",
    "part_size_bytes",
    "state",
    "expires_at",
    "version"
  ],
  "additionalProperties": false
}
```

## UploadPart

源指针：`#/components/schemas/UploadPart`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| part_no | 必须 | integer; minimum=1 | 候选字段来源：upload_part.part_no：上传分片编号，从1开始；同一会话内不得重复。来源引用不是写入许可，完整处理按操作核验。 |
| sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：media_asset.sha256：媒体资产字节的SHA-256，应与引用对象版本核对；存储64位小写十六进制，正则只检查格式不验证字节真实性；upload_part.sha256：该分片实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；upload_session.sha256：上传方声明的完整文件SHA-256，合并后必须以实际字节重新计算核对；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| size_bytes | 必须 | integer; minimum=1 | 候选字段来源：media_asset.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0；upload_part.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0；upload_session.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "part_no": {
      "type": "integer",
      "minimum": 1
    },
    "sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "size_bytes": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "part_no",
    "sha256",
    "size_bytes"
  ],
  "additionalProperties": false
}
```

## UploadComplete

源指针：`#/components/schemas/UploadComplete`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| parts | 必须 | array; minItems=1; items=UploadPart | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "parts": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/UploadPart"
      },
      "minItems": 1
    }
  },
  "required": [
    "parts"
  ],
  "additionalProperties": false,
  "description": "parts按part_no连续覆盖；服务端复算完整大小与SHA-256。"
}
```

## UploadResult

源指针：`#/components/schemas/UploadResult`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| upload_id | 必须 | string; format="uuid" | 候选字段来源：upload_part.upload_id：所属上传会话标识，指向upload_session.upload_id；upload_session.upload_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证；upload_session.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| validation | 必须 | string; enum=["VALIDATING", "VALID", "REJECTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| duplicate_of | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：upload_session.duplicate_of：同案件重复资产引用；仅在完整摘要/媒体校验成功后登记，读取仍核验当前案件权限；NULL表示未确定重复。。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "upload_id": {
      "type": "string",
      "format": "uuid"
    },
    "asset_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "validation": {
      "type": "string",
      "enum": [
        "VALIDATING",
        "VALID",
        "REJECTED"
      ]
    },
    "duplicate_of": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "request_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "upload_id",
    "asset_id",
    "validation",
    "duplicate_of",
    "request_id"
  ],
  "additionalProperties": false,
  "description": "仅VALID且授权生效的资产可分析；duplicate_of只暴露当前有权对象。"
}
```

## Asset

源指针：`#/components/schemas/Asset`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：asset_lineage.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；media_asset.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| content_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.content_id：所属逻辑内容标识，指向content_item.content_id。来源引用不是写入许可，完整处理按操作核验。 |
| source_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.source_id：数据来源登记标识，指向source_registry.source_id。来源引用不是写入许可，完整处理按操作核验。 |
| kind | 必须 | string; enum=["original", "derived"] | 候选字段来源：media_asset.kind：媒体身份：original为原始输入，derived为派生副本。来源引用不是写入许可，完整处理按操作核验。 |
| object_ref | 必须 | ObjectRef | 候选字段来源：object_version.object_id：主键，由应用提供UUID；不视为访问凭证；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.version_id：对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version。来源引用不是写入许可，完整处理按操作核验。 |
| mime | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：media_asset.mime：探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名。来源引用不是写入许可，完整处理按操作核验。 |
| size_bytes | 必须 | integer; minimum=1 | 候选字段来源：media_asset.size_bytes：文件或分片的字节长度，单位byte；有效值必须大于0。来源引用不是写入许可，完整处理按操作核验。 |
| duration_ms | 必须 | anyOf(integer; minimum=0; null) | 候选字段来源：media_asset.duration_ms：媒体时长，单位毫秒；静态图像或未知时长允许NULL，0不能替代未知。来源引用不是写入许可，完整处理按操作核验。 |
| width | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：media_asset.width：媒体帧或图像宽度，单位像素；有值时为正整数。来源引用不是写入许可，完整处理按操作核验。 |
| height | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：media_asset.height：媒体帧或图像高度，单位像素；有值时为正整数。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["VALIDATING", "VALID", "QUARANTINED", "ARCHIVED"] | 候选字段来源：media_asset.state：原始或派生媒体的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：asset_lineage.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；media_asset.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：asset_lineage.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；media_asset.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "content_id": {
      "type": "string",
      "format": "uuid"
    },
    "source_id": {
      "type": "string",
      "format": "uuid"
    },
    "kind": {
      "type": "string",
      "enum": [
        "original",
        "derived"
      ]
    },
    "object_ref": {
      "$ref": "#/components/schemas/ObjectRef"
    },
    "mime": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "size_bytes": {
      "type": "integer",
      "minimum": 1
    },
    "duration_ms": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 0
        },
        {
          "type": "null"
        }
      ]
    },
    "width": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "height": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "state": {
      "type": "string",
      "enum": [
        "VALIDATING",
        "VALID",
        "QUARANTINED",
        "ARCHIVED"
      ]
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "asset_id",
    "case_id",
    "content_id",
    "source_id",
    "kind",
    "object_ref",
    "mime",
    "size_bytes",
    "duration_ms",
    "width",
    "height",
    "state",
    "version",
    "created_at"
  ],
  "additionalProperties": false
}
```

## ImportEntry

源指针：`#/components/schemas/ImportEntry`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| source_id | 必须 | string; format="uuid" | 候选字段来源：import_item.source_id：数据来源登记标识，指向source_registry.source_id。来源引用不是写入许可，完整处理按操作核验。 |
| object_ref | 必须 | ObjectRef | 候选字段来源：object_version.object_id：主键，由应用提供UUID；不视为访问凭证；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.version_id：对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version。来源引用不是写入许可，完整处理按操作核验。 |
| filename | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mime | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "source_id": {
      "type": "string",
      "format": "uuid"
    },
    "object_ref": {
      "$ref": "#/components/schemas/ObjectRef"
    },
    "filename": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "mime": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "source_id",
    "object_ref",
    "filename",
    "mime"
  ],
  "additionalProperties": false
}
```

## ImportRequest

源指针：`#/components/schemas/ImportRequest`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：import_item.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；import_job.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| entries | 必须 | array; minItems=1; items=ImportEntry | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "entries": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/ImportEntry"
      },
      "minItems": 1
    }
  },
  "required": [
    "case_id",
    "entries"
  ],
  "additionalProperties": false
}
```

## ImportStatus

源指针：`#/components/schemas/ImportStatus`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| import_id | 必须 | string; format="uuid" | 候选字段来源：import_item.import_id：所属批量导入作业标识，指向import_job.import_id；import_job.import_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：import_item.state：逐条导入结果的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；import_job.state：批量清单导入作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| items | 必须 | array; minItems=0; items=object; additionalProperties=false | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].ordinal | 必须（父对象存在时） | integer; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].asset_id | 必须（父对象存在时） | anyOf(string; format="uuid"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].state | 必须（父对象存在时） | string; enum=["pending", "accepted", "rejected"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items[].error_code | 必须（父对象存在时） | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "import_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ordinal": {
            "type": "integer",
            "minimum": 0
          },
          "asset_id": {
            "anyOf": [
              {
                "type": "string",
                "format": "uuid"
              },
              {
                "type": "null"
              }
            ]
          },
          "state": {
            "type": "string",
            "enum": [
              "pending",
              "accepted",
              "rejected"
            ]
          },
          "error_code": {
            "anyOf": [
              {
                "type": "string",
                "minLength": 1,
                "maxLength": 128
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "required": [
          "ordinal",
          "asset_id",
          "state",
          "error_code"
        ],
        "additionalProperties": false
      },
      "minItems": 0
    }
  },
  "required": [
    "import_id",
    "state",
    "items"
  ],
  "additionalProperties": false
}
```

## TaskCreate

源指针：`#/components/schemas/TaskCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；idempotency_record.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；outbox_event.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| scene | 必须 | string; enum=["accident_rumor", "harmful_content", "repost_tamper_trace"] | 候选字段来源：analysis_task.scene：分析场景编码，用于选择任务处理流程；实际场景词表仍依业务配置。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：analysis_task.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| modules | 必须 | array; minItems=1; uniqueItems=true; items=string; enum=["INGEST", "RESOURCE", "MEDIA", "RISK", "FORENSIC", "IMGRET", "VIDTRACE", "ORIGIN", "PROPAGATION", "CLAIM", "REVIEW", "OPS"] | 候选字段来源：analysis_task.modules：任务请求运行的模块编码列表；服务端检查模块是否允许、依赖是否满足。来源引用不是写入许可，完整处理按操作核验。 |
| priority | 必须 | string; enum=["low", "normal", "high"] | 候选字段来源：analysis_task.priority：调度优先级；只影响排队策略，不改变权限或审核要求。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "scene": {
      "type": "string",
      "enum": [
        "accident_rumor",
        "harmful_content",
        "repost_tamper_trace"
      ]
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "modules": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "INGEST",
          "RESOURCE",
          "MEDIA",
          "RISK",
          "FORENSIC",
          "IMGRET",
          "VIDTRACE",
          "ORIGIN",
          "PROPAGATION",
          "CLAIM",
          "REVIEW",
          "OPS"
        ]
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "priority": {
      "type": "string",
      "enum": [
        "low",
        "normal",
        "high"
      ]
    }
  },
  "required": [
    "case_id",
    "asset_id",
    "scene",
    "policy_version",
    "modules",
    "priority"
  ],
  "additionalProperties": false,
  "description": "场景枚举为源三类场景的工程代号；正式适用范围待审核。"
}
```

## NodeStatus

源指针：`#/components/schemas/NodeStatus`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| node_code | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：task_node_run.node_code：任务依赖图中的节点编码，在对应dag_version内解析。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["PENDING", "READY", "RUNNING", "SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "CANCELLED", "NOT_SUPPORTED"] | 候选字段来源：analysis_task.state：分析任务当前投影的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；task_node_run.state：节点尝试与租约的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| attempt | 必须 | integer; minimum=0 | 候选字段来源：task_node_run.attempt：同一任务运行节点的尝试次数，从1开始，重试递增。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：task_node_run.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |
| required | 必须 | boolean | 候选字段来源：task_node_run.required：该节点是否为本次DAG完成所必需；必需节点缺失不能直接当任务成功。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "node_code": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "state": {
      "type": "string",
      "enum": [
        "PENDING",
        "READY",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "SKIPPED",
        "DEFERRED",
        "CANCELLED",
        "NOT_SUPPORTED"
      ]
    },
    "attempt": {
      "type": "integer",
      "minimum": 0
    },
    "reason": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    },
    "required": {
      "type": "boolean"
    }
  },
  "required": [
    "node_code",
    "state",
    "attempt",
    "reason",
    "required"
  ],
  "additionalProperties": false
}
```

## Task

源指针：`#/components/schemas/Task`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.task_id：主键，由应用提供UUID；不视为访问凭证；task_node_run.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；task_node_run.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：analysis_task.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["CREATED", "QUEUED", "RUNNING", "WAIT_REVIEW", "REVIEWING", "SUCCEEDED", "FAILED", "RETURNED", "CANCEL_REQUESTED", "CANCELLED", "ARCHIVED"] | 候选字段来源：analysis_task.state：分析任务当前投影的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；task_node_run.state：节点尝试与租约的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算；task_node_run.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：analysis_task.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；task_node_run.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| progress | 必须 | number; minimum=0; maximum=1 | 候选字段来源：analysis_task.progress：当前运行版本的进度比例，0到1；不是准确率或任务正式通过率。来源引用不是写入许可，完整处理按操作核验。 |
| nodes | 必须 | array; minItems=0; items=NodeStatus | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 候选字段来源：analysis_task.missing_modalities：输入缺失的模态列表，例如无音轨；空数组表示未登记缺失，不等于全部分析成功。来源引用不是写入许可，完整处理按操作核验。 |
| report_eligibility | 必须 | string; enum=["draft_only", "reviewable", "formal_eligible"] | 候选字段来源：analysis_task.report_eligibility：当前结果允许的报告使用等级；正式报告仍需核验审批和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：analysis_task.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；task_node_run.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "CREATED",
        "QUEUED",
        "RUNNING",
        "WAIT_REVIEW",
        "REVIEWING",
        "SUCCEEDED",
        "FAILED",
        "RETURNED",
        "CANCEL_REQUESTED",
        "CANCELLED",
        "ARCHIVED"
      ]
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "progress": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "nodes": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/NodeStatus"
      },
      "minItems": 0
    },
    "missing_modalities": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 0
    },
    "report_eligibility": {
      "type": "string",
      "enum": [
        "draft_only",
        "reviewable",
        "formal_eligible"
      ]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "task_id",
    "case_id",
    "asset_id",
    "state",
    "run_version",
    "result_version",
    "policy_version",
    "version",
    "progress",
    "nodes",
    "missing_modalities",
    "report_eligibility",
    "created_at"
  ],
  "additionalProperties": false,
  "description": "上传状态不混进分析任务；SUCCEEDED算法任务不代表业务批准。"
}
```

## TaskAction

源指针：`#/components/schemas/TaskAction`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：task_event.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |
| expected_run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；outbox_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；task_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "expected_run_version": {
      "type": "integer",
      "minimum": 1
    },
    "expected_version": {
      "type": "integer",
      "minimum": 1
    },
    "approval_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "reason",
    "expected_run_version",
    "expected_version",
    "approval_id"
  ],
  "additionalProperties": false
}
```

## Rerun

源指针：`#/components/schemas/Rerun`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：task_event.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |
| expected_run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：analysis_task.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；outbox_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；task_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；task_run.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| node_codes | 必须 | array; minItems=1; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "expected_run_version": {
      "type": "integer",
      "minimum": 1
    },
    "expected_version": {
      "type": "integer",
      "minimum": 1
    },
    "node_codes": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "approval_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "reason",
    "expected_run_version",
    "expected_version",
    "node_codes",
    "approval_id"
  ],
  "additionalProperties": false
}
```

## Evidence

源指针：`#/components/schemas/Evidence`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| evidence_id | 必须 | string; format="uuid" | 候选字段来源：evidence_item.evidence_id：主键，由应用提供UUID；不视为访问凭证；package_item.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id；task_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；evidence_item.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；evidence_package.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；object_version.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；package_item.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；task_evidence.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：evidence_item.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本；evidence_package.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本；task_evidence.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：evidence_item.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算；evidence_package.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：evidence_item.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果；evidence_package.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| kind | 必须 | string; enum=["original", "frame", "region", "segment", "match", "text", "snapshot", "model_output"] | 候选字段来源：evidence_item.type：证据类别编码，决定对象、时间范围和定位解释。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：evidence_item.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| object_ref | 必须 | anyOf(ObjectRef; null) | 候选字段来源：object_version.object_id：主键，由应用提供UUID；不视为访问凭证；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.version_id：对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version。来源引用不是写入许可，完整处理按操作核验。 |
| time_range | 必须 | anyOf(TimeRange; null) | 候选字段来源：evidence_item.time_range：源媒体时间范围对象，使用start_ms、end_ms；非空时必须校验先后与源媒体范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| bbox | 必须 | anyOf(BoundingBox; null) | 候选字段来源：evidence_item.bbox：源图像归一化定位框对象，使用x、y、width、height；不适用可用空对象，非空须校验边界。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：evidence_item.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本。来源引用不是写入许可，完整处理按操作核验。 |
| model_name | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：evidence_item.model_name：模型注册名称，与model_version共同定位产生该结果的模型。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：evidence_item.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：evidence_item.authorization_version：本次处理采用的来源授权版本，用于撤销核查及历史追溯。来源引用不是写入许可，完整处理按操作核验。 |
| sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：evidence_item.sha256：该证据版本绑定内容的SHA-256，摘要对象需在证据类型契约中明确；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；package_item.sha256：清单中引用对象固定版本字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；evidence_item.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；evidence_package.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；evidence_package.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version；object_version.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；package_item.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；task_evidence.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：audit_event.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；evidence_item.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；evidence_package.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；object_version.created_at：对象版本登记入库时刻；TIMESTAMPTZ保存时间点，显示时区由会话决定，不保留原始时区名称；package_item.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；task_evidence.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "evidence_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "kind": {
      "type": "string",
      "enum": [
        "original",
        "frame",
        "region",
        "segment",
        "match",
        "text",
        "snapshot",
        "model_output"
      ]
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "object_ref": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ObjectRef"
        },
        {
          "type": "null"
        }
      ]
    },
    "time_range": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/TimeRange"
        },
        {
          "type": "null"
        }
      ]
    },
    "bbox": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/BoundingBox"
        },
        {
          "type": "null"
        }
      ]
    },
    "mapping_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "model_name": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    },
    "model_version": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    },
    "authorization_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "evidence_id",
    "case_id",
    "task_id",
    "run_version",
    "result_version",
    "kind",
    "asset_id",
    "object_ref",
    "time_range",
    "bbox",
    "mapping_version",
    "model_name",
    "model_version",
    "authorization_version",
    "sha256",
    "version",
    "created_at"
  ],
  "additionalProperties": false
}
```

## Finding

源指针：`#/components/schemas/Finding`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| finding_id | 必须 | string; format="uuid" | 候选字段来源：risk_finding.finding_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| kind | 必须 | string; enum=["classification", "detection", "temporal", "tamper", "relation", "claim"] | 候选字段来源：tamper_finding.type：疑似篡改类型编码，取值由模型及标签策略约定。来源引用不是写入许可，完整处理按操作核验。 |
| label | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：risk_finding.category：风险分类编码；取值、阈值和法律业务含义由有效标签策略确定；tamper_finding.type：疑似篡改类型编码，取值由模型及标签策略约定。来源引用不是写入许可，完整处理按操作核验。 |
| raw_score | 必须 | number; minimum=0; maximum=1 | 候选字段来源：risk_finding.score：风险候选发现对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较；tamper_finding.score：疑似篡改发现对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较。来源引用不是写入许可，完整处理按操作核验。 |
| calibrated_score | 必须 | anyOf(number; minimum=0; maximum=1; null) | 候选字段来源：risk_finding.calibrated_score：校准后的模型分数，范围0至1；未进行校准时为NULL，必须绑定相应校准版本和评测口径；tamper_finding.calibrated_score：校准后的模型分数，范围0至1；未进行校准时为NULL，必须绑定相应校准版本和评测口径。来源引用不是写入许可，完整处理按操作核验。 |
| threshold_version | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：risk_finding.threshold_version：将模型分数转为候选标签时使用的阈值配置版本；tamper_finding.threshold_version：将模型分数转为候选标签时使用的阈值配置版本。来源引用不是写入许可，完整处理按操作核验。 |
| model_name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：risk_finding.model_name：模型注册名称，与model_version共同定位产生该结果的模型；tamper_finding.model_name：模型注册名称，与model_version共同定位产生该结果的模型。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：risk_finding.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本；tamper_finding.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |
| time_range | 必须 | anyOf(TimeRange; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| bbox | 必须 | anyOf(BoundingBox; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mask_ref | 必须 | anyOf(ObjectRef; null) | 候选字段来源：risk_finding.payload：按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用；tamper_finding.payload：按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：finding_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| status | 必须 | string; enum=["candidate", "insufficient", "reviewed"] | 候选字段来源：risk_finding.status：风险候选发现的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；tamper_finding.status：疑似篡改发现的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| track_id | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| frame_id | 必须 | anyOf(string; format="uuid"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "finding_id": {
      "type": "string",
      "format": "uuid"
    },
    "kind": {
      "type": "string",
      "enum": [
        "classification",
        "detection",
        "temporal",
        "tamper",
        "relation",
        "claim"
      ]
    },
    "label": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "raw_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "calibrated_score": {
      "anyOf": [
        {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "threshold_version": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    },
    "model_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "model_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "time_range": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/TimeRange"
        },
        {
          "type": "null"
        }
      ]
    },
    "bbox": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/BoundingBox"
        },
        {
          "type": "null"
        }
      ]
    },
    "mask_ref": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ObjectRef"
        },
        {
          "type": "null"
        }
      ]
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "status": {
      "type": "string",
      "enum": [
        "candidate",
        "insufficient",
        "reviewed"
      ]
    },
    "mapping_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "track_id": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    },
    "frame_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "finding_id",
    "kind",
    "label",
    "raw_score",
    "calibrated_score",
    "threshold_version",
    "model_name",
    "model_version",
    "time_range",
    "bbox",
    "mask_ref",
    "evidence_ids",
    "status",
    "mapping_version",
    "track_id",
    "frame_id"
  ],
  "additionalProperties": false
}
```

## Findings

源指针：`#/components/schemas/Findings`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| binding | 必须 | VersionBinding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| findings | 必须 | array; minItems=0; items=Finding | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| missing_modalities | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "binding": {
      "$ref": "#/components/schemas/VersionBinding"
    },
    "findings": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Finding"
      },
      "minItems": 0
    },
    "missing_modalities": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 0
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 0
    }
  },
  "required": [
    "binding",
    "findings",
    "missing_modalities",
    "warnings"
  ],
  "additionalProperties": false
}
```

## TimelineItem

源指针：`#/components/schemas/TimelineItem`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| item_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| kind | 必须 | string; enum=["frame", "shot", "ocr", "asr", "subtitle", "audio", "finding"] | 候选字段来源：media_asset.kind：媒体身份：original为原始输入，derived为派生副本；text_segment.type：提取模态类别：OCR、ASR或SUBTITLE。来源引用不是写入许可，完整处理按操作核验。 |
| time_range | 必须 | TimeRange | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：keyframe.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；media_asset.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；shot.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；text_segment.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：keyframe.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证；shot.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；text_segment.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| text | 必须 | anyOf(string; minLength=1; maxLength=4096; null) | 候选字段来源：text_segment.text：OCR、ASR或字幕提取的文本原文；纠错或摘要应另存，不覆盖原文。来源引用不是写入许可，完整处理按操作核验。 |
| bbox | 必须 | anyOf(BoundingBox; null) | 候选字段来源：text_segment.bbox：源图像归一化定位框对象，使用x、y、width、height；不适用可用空对象，非空须校验边界。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_id | 必须 | anyOf(string; format="uuid"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "item_id": {
      "type": "string",
      "format": "uuid"
    },
    "kind": {
      "type": "string",
      "enum": [
        "frame",
        "shot",
        "ocr",
        "asr",
        "subtitle",
        "audio",
        "finding"
      ]
    },
    "time_range": {
      "$ref": "#/components/schemas/TimeRange"
    },
    "mapping_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "text": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ]
    },
    "bbox": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/BoundingBox"
        },
        {
          "type": "null"
        }
      ]
    },
    "evidence_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "item_id",
    "kind",
    "time_range",
    "mapping_version",
    "asset_id",
    "text",
    "bbox",
    "evidence_id"
  ],
  "additionalProperties": false
}
```

## Timeline

源指针：`#/components/schemas/Timeline`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：keyframe.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证；shot.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；text_segment.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| mapping_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：keyframe.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；media_asset.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；shot.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本；text_segment.mapping_version：派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本。来源引用不是写入许可，完整处理按操作核验。 |
| items | 必须 | array; minItems=0; items=TimelineItem | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "mapping_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/TimelineItem"
      },
      "minItems": 0
    }
  },
  "required": [
    "asset_id",
    "mapping_version",
    "items"
  ],
  "additionalProperties": false
}
```

## ImageSearch

源指针：`#/components/schemas/ImageSearch`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；source_match.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：media_asset.asset_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| region | 必须 | anyOf(BoundingBox; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| top_k | 必须 | integer; minimum=1; maximum=100 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| index_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本；source_match.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "region": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/BoundingBox"
        },
        {
          "type": "null"
        }
      ]
    },
    "top_k": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "index_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "case_id",
    "asset_id",
    "region",
    "top_k",
    "index_version"
  ],
  "additionalProperties": false
}
```

## VideoSearch

源指针：`#/components/schemas/VideoSearch`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：source_match.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| range | 必须 | TimeRange | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| top_k | 必须 | integer; minimum=1; maximum=100 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| index_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本；source_match.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "range": {
      "$ref": "#/components/schemas/TimeRange"
    },
    "top_k": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "index_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "case_id",
    "asset_id",
    "range",
    "top_k",
    "index_version"
  ],
  "additionalProperties": false
}
```

## SearchCandidate

源指针：`#/components/schemas/SearchCandidate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| candidate_asset_id | 必须 | string; format="uuid" | 候选字段来源：source_match.candidate_asset_id：被检索返回的候选来源媒体资产标识；候选相似不能直接认定同源。来源引用不是写入许可，完整处理按操作核验。 |
| score | 必须 | number; minimum=0; maximum=1 | 候选字段来源：source_match.score：同源或片段映射候选对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较。来源引用不是写入许可，完整处理按操作核验。 |
| relation | 必须 | string; enum=["similar", "full_copy", "partial_copy", "contains", "unknown"] | 候选字段来源：source_match.relation：查询与候选媒体间的关系类型，整体同源、局部包含和语义相似必须区分。来源引用不是写入许可，完整处理按操作核验。 |
| verification | 必须 | string; enum=["unverified", "geometry", "temporal", "human"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| evidence_ids | 必须 | array; minItems=0; items=string; format="uuid" | 候选字段来源：source_match.evidence_refs：支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| query_range | 必须 | anyOf(TimeRange; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| source_range | 必须 | anyOf(TimeRange; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| direction | 必须 | string; enum=["forward", "reverse", "not_applicable"] | 候选字段来源：source_match.direction：查询与来源片段的播放对应方向，不改变存储区间起点小于终点的约定。来源引用不是写入许可，完整处理按操作核验。 |
| speed_ratio | 必须 | number; exclusiveMinimum=0 | 候选字段来源：source_match.speed_ratio：查询片段时长除以来源片段时长的正比例（本轮工程约定）；倒放由direction单独表示，模型适配器负责转换其原生定义。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "candidate_asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "relation": {
      "type": "string",
      "enum": [
        "similar",
        "full_copy",
        "partial_copy",
        "contains",
        "unknown"
      ]
    },
    "verification": {
      "type": "string",
      "enum": [
        "unverified",
        "geometry",
        "temporal",
        "human"
      ]
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 0
    },
    "query_range": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/TimeRange"
        },
        {
          "type": "null"
        }
      ]
    },
    "source_range": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/TimeRange"
        },
        {
          "type": "null"
        }
      ]
    },
    "direction": {
      "type": "string",
      "enum": [
        "forward",
        "reverse",
        "not_applicable"
      ]
    },
    "speed_ratio": {
      "type": "number",
      "exclusiveMinimum": 0
    }
  },
  "required": [
    "candidate_asset_id",
    "score",
    "relation",
    "verification",
    "evidence_ids",
    "query_range",
    "source_range",
    "direction",
    "speed_ratio"
  ],
  "additionalProperties": false
}
```

## SearchResults

源指针：`#/components/schemas/SearchResults`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| search_id | 必须 | string; format="uuid" | 候选字段来源：search_job.search_id：主键，由应用提供UUID；不视为访问凭证；source_match.search_id：产生匹配候选的异步检索作业标识。来源引用不是写入许可，完整处理按操作核验。 |
| index_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：search_job.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本；source_match.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |
| candidates | 必须 | array; minItems=0; items=SearchCandidate | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| unknown_ranges | 必须 | array; minItems=0; items=TimeRange | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "search_id": {
      "type": "string",
      "format": "uuid"
    },
    "index_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "candidates": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/SearchCandidate"
      },
      "minItems": 0
    },
    "unknown_ranges": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/TimeRange"
      },
      "minItems": 0
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 0
    }
  },
  "required": [
    "search_id",
    "index_version",
    "candidates",
    "unknown_ranges",
    "warnings"
  ],
  "additionalProperties": false
}
```

## FirstSource

源指针：`#/components/schemas/FirstSource`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| cluster_id | 必须 | string; format="uuid" | 候选字段来源：first_source_ranking.cluster_id：高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证。来源引用不是写入许可，完整处理按操作核验。 |
| scope | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：content_cluster.scope：内容簇覆盖的比较范围标识或说明；整体同源与指定片段范围必须区分。来源引用不是写入许可，完整处理按操作核验。 |
| candidates | 必须 | array; minItems=0; maxItems=3; items=object; additionalProperties=false | 候选字段来源：first_source_candidate.ranking_id：所属首发排序快照ID；与案件及簇共同绑定first_source_ranking，不能混合不同计算结果。来源引用不是写入许可，完整处理按操作核验。 |
| candidates[].asset_id | 必须（父对象存在时） | string; format="uuid" | 本批次列为首发候选的媒体资产标识；必须属于同案件及本簇cluster_member，不能引用簇外素材 |
| candidates[].rank | 必须（父对象存在时） | integer; minimum=1; maximum=3 | 本次排序批次内的候选名次，从1连续排列到候选数量，最多3；不是确定首发结论 |
| candidates[].probability | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| candidates[].published_at | 必须（父对象存在时） | anyOf(string; format="date-time"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| candidates[].evidence_ids | 必须（父对象存在时） | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| candidates[].counter_evidence_ids | 必须（父对象存在时） | array; minItems=0; uniqueItems=true; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| status | 必须 | string; enum=["candidate", "insufficient", "reviewed"] | 候选字段来源：first_source_ranking.status：candidate为待核查候选，insufficient为证据不足，reviewed为已复核快照；reviewed仍非法律结论。来源引用不是写入许可，完整处理按操作核验。 |
| coverage_note | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：first_source_ranking.coverage_note：本次观察的平台、时间和素材覆盖范围及缺失说明；不能声称覆盖未知全网。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：first_source_ranking.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |
| ranking_id | 必须 | string; format="uuid" | 候选字段来源：first_source_ranking.ranking_id：一次首发排序结果快照的唯一标识；重算或复核更正生成新快照。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：first_source_ranking.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：first_source_ranking.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：first_source_ranking.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1 | 候选字段来源：first_source_ranking.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| candidate_count | 必须 | integer; minimum=0; maximum=3 | 候选字段来源：first_source_ranking.candidate_count：该快照应包含的候选总数；事务提交时必须与明细数量相等，0表示有结果但无足够候选。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "cluster_id": {
      "type": "string",
      "format": "uuid",
      "description": "高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证"
    },
    "scope": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "candidates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "asset_id": {
            "type": "string",
            "format": "uuid",
            "description": "本批次列为首发候选的媒体资产标识；必须属于同案件及本簇cluster_member，不能引用簇外素材"
          },
          "rank": {
            "type": "integer",
            "minimum": 1,
            "maximum": 3,
            "description": "本次排序批次内的候选名次，从1连续排列到候选数量，最多3；不是确定首发结论"
          },
          "probability": {
            "anyOf": [
              {
                "type": "number",
                "minimum": 0,
                "maximum": 1
              },
              {
                "type": "null"
              }
            ]
          },
          "published_at": {
            "anyOf": [
              {
                "type": "string",
                "format": "date-time"
              },
              {
                "type": "null"
              }
            ]
          },
          "evidence_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "format": "uuid"
            },
            "minItems": 1,
            "uniqueItems": true
          },
          "counter_evidence_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "format": "uuid"
            },
            "minItems": 0,
            "uniqueItems": true
          }
        },
        "required": [
          "asset_id",
          "rank",
          "probability",
          "published_at",
          "evidence_ids",
          "counter_evidence_ids"
        ],
        "additionalProperties": false
      },
      "minItems": 0,
      "maxItems": 3,
      "description": "按rank升序返回，rank恰为1..candidate_count，asset_id不重复；数量等于candidate_count。"
    },
    "status": {
      "type": "string",
      "enum": [
        "candidate",
        "insufficient",
        "reviewed"
      ]
    },
    "coverage_note": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "model_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "ranking_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "policy_version": {
      "type": "string",
      "minLength": 1
    },
    "candidate_count": {
      "type": "integer",
      "minimum": 0,
      "maximum": 3
    }
  },
  "required": [
    "cluster_id",
    "scope",
    "candidates",
    "status",
    "coverage_note",
    "model_version",
    "ranking_id",
    "task_id",
    "run_version",
    "result_version",
    "policy_version",
    "candidate_count"
  ],
  "additionalProperties": false,
  "description": "指定簇的一次不可变首发排序快照；候选最多3条，不等于认定原创。"
}
```

## GraphNode

源指针：`#/components/schemas/GraphNode`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| node_id | 必须 | string; format="uuid" | 候选字段来源：propagation_node.node_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| type | 必须 | string; enum=["content", "account", "platform", "event", "place"] | 候选字段来源：propagation_node.type：传播图节点类型，决定其展示及业务对象解释。来源引用不是写入许可，完整处理按操作核验。 |
| display_label | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：propagation_node.display_label：传播图节点的人类可读展示标签，不作为节点主键或关系证据。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "node_id": {
      "type": "string",
      "format": "uuid"
    },
    "type": {
      "type": "string",
      "enum": [
        "content",
        "account",
        "platform",
        "event",
        "place"
      ]
    },
    "display_label": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "node_id",
    "type",
    "display_label"
  ],
  "additionalProperties": false
}
```

## GraphEdge

源指针：`#/components/schemas/GraphEdge`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| edge_id | 必须 | string; format="uuid" | 候选字段来源：propagation_edge.edge_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| from_node_id | 必须 | string; format="uuid" | 候选字段来源：propagation_edge.from_node_id：传播关系起点节点标识。来源引用不是写入许可，完整处理按操作核验。 |
| to_node_id | 必须 | string; format="uuid" | 候选字段来源：propagation_edge.to_node_id：传播关系终点节点标识。来源引用不是写入许可，完整处理按操作核验。 |
| relation | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：propagation_edge.relation：传播关系类别；是否事实另由origin和证据决定。来源引用不是写入许可，完整处理按操作核验。 |
| origin | 必须 | string; enum=["observed", "inferred", "human"] | 候选字段来源：propagation_edge.origin：传播边依据类别，区分明确记录与算法推断；推断不能展示为事实。来源引用不是写入许可，完整处理按操作核验。 |
| probability | 必须 | anyOf(number; minimum=0; maximum=1; null) | 候选字段来源：propagation_edge.probability：传播关系推断的已校准概率，范围0至1；未校准时为NULL，不能据此把推断边改成事实边。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：propagation_edge.evidence_refs：支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：propagation_edge.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；propagation_node.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；review_record.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["candidate", "confirmed", "rejected"] | 候选字段来源：propagation_edge.state：显式推断传播边的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "edge_id": {
      "type": "string",
      "format": "uuid"
    },
    "from_node_id": {
      "type": "string",
      "format": "uuid"
    },
    "to_node_id": {
      "type": "string",
      "format": "uuid"
    },
    "relation": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "origin": {
      "type": "string",
      "enum": [
        "observed",
        "inferred",
        "human"
      ]
    },
    "probability": {
      "anyOf": [
        {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "state": {
      "type": "string",
      "enum": [
        "candidate",
        "confirmed",
        "rejected"
      ]
    }
  },
  "required": [
    "edge_id",
    "from_node_id",
    "to_node_id",
    "relation",
    "origin",
    "probability",
    "evidence_ids",
    "version",
    "state"
  ],
  "additionalProperties": false
}
```

## Graph

源指针：`#/components/schemas/Graph`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| cluster_id | 必须 | string; format="uuid" | 候选字段来源：propagation_node.cluster_id：高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：propagation_edge.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；propagation_node.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| nodes | 必须 | array; minItems=0; items=GraphNode | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| edges | 必须 | array; minItems=0; items=GraphEdge | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "cluster_id": {
      "type": "string",
      "format": "uuid"
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "nodes": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/GraphNode"
      },
      "minItems": 0
    },
    "edges": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/GraphEdge"
      },
      "minItems": 0
    }
  },
  "required": [
    "cluster_id",
    "version",
    "nodes",
    "edges"
  ],
  "additionalProperties": false
}
```

## ClaimExtract

源指针：`#/components/schemas/ClaimExtract`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：claim.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；text_segment.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：claim.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；text_segment.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| source_segment_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：claim.source_segment_refs：主张对应文本或媒体片段引用对象，需定位到资产、片段和时间或字符范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "source_segment_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1
    }
  },
  "required": [
    "case_id",
    "asset_id",
    "source_segment_ids"
  ],
  "additionalProperties": false
}
```

## Claim

源指针：`#/components/schemas/Claim`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| claim_id | 必须 | string; format="uuid" | 候选字段来源：claim.claim_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：claim.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；text_segment.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| asset_id | 必须 | string; format="uuid" | 候选字段来源：claim.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用；text_segment.asset_id：本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用。来源引用不是写入许可，完整处理按操作核验。 |
| subject | 必须 | anyOf(string; minLength=1; maxLength=4096; null) | 候选字段来源：claim.subject：结构化主张中的主体表述，来自原文或模型抽取；不能当用户身份。来源引用不是写入许可，完整处理按操作核验。 |
| action | 必须 | anyOf(string; minLength=1; maxLength=4096; null) | 候选字段来源：claim.action：主张所描述行为或审计动作编码，具体语义由本表决定。来源引用不是写入许可，完整处理按操作核验。 |
| time | 必须 | anyOf(string; minLength=1; maxLength=4096; null) | 候选字段来源：claim.claim_time：主张原文中的时间表述，可能含模糊日期；未知为NULL，不强行转成精确时间戳。来源引用不是写入许可，完整处理按操作核验。 |
| place | 必须 | anyOf(string; minLength=1; maxLength=4096; null) | 候选字段来源：claim.place：主张原文中的地点表述；未知为空，不自动地理定位。来源引用不是写入许可，完整处理按操作核验。 |
| result | 必须 | anyOf(string; minLength=1; maxLength=4096; null) | 候选字段来源：claim.result：主张所陈述的结果，不代表系统已核实为真。来源引用不是写入许可，完整处理按操作核验。 |
| source_segment_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：claim.source_segment_refs：主张对应文本或媒体片段引用对象，需定位到资产、片段和时间或字符范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：claim.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本；text_segment.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "claim_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "asset_id": {
      "type": "string",
      "format": "uuid"
    },
    "subject": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ]
    },
    "action": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ]
    },
    "time": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ]
    },
    "place": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ]
    },
    "result": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ]
    },
    "source_segment_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1
    },
    "model_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "claim_id",
    "case_id",
    "asset_id",
    "subject",
    "action",
    "time",
    "place",
    "result",
    "source_segment_ids",
    "model_version"
  ],
  "additionalProperties": false
}
```

## ClaimList

源指针：`#/components/schemas/ClaimList`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| claims | 必须 | array; minItems=0; items=Claim | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| warnings | 必须 | array; minItems=0; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "claims": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Claim"
      },
      "minItems": 0
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 0
    }
  },
  "required": [
    "claims",
    "warnings"
  ],
  "additionalProperties": false
}
```

## ClaimVerify

源指针：`#/components/schemas/ClaimVerify`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：claim.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；claim_evidence_relation.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：claim_evidence_relation.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "case_id",
    "evidence_ids",
    "policy_version"
  ],
  "additionalProperties": false
}
```

## Relation

源指针：`#/components/schemas/Relation`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| claim_id | 必须 | string; format="uuid" | 候选字段来源：claim.claim_id：主键，由应用提供UUID；不视为访问凭证；claim_evidence_relation.claim_id：被证据支持、反对或关联的主张标识。来源引用不是写入许可，完整处理按操作核验。 |
| relation | 必须 | string; enum=["supports", "contradicts", "partially_supports", "unrelated", "insufficient"] | 候选字段来源：claim_evidence_relation.relation：主张与证据的关系类别，支持、反对或不足等取值以CHECK枚举为准。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=0; items=string; format="uuid" | 候选字段来源：claim_evidence_relation.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| score | 必须 | number; minimum=0; maximum=1 | 候选字段来源：claim_evidence_relation.score：主张证据关系对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：claim.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本；claim_evidence_relation.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "claim_id": {
      "type": "string",
      "format": "uuid"
    },
    "relation": {
      "type": "string",
      "enum": [
        "supports",
        "contradicts",
        "partially_supports",
        "unrelated",
        "insufficient"
      ]
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 0
    },
    "score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "model_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "claim_id",
    "relation",
    "evidence_ids",
    "score",
    "model_version"
  ],
  "additionalProperties": false,
  "allOf": [
    {
      "if": {
        "properties": {
          "relation": {
            "not": {
              "const": "insufficient"
            }
          }
        },
        "required": [
          "relation"
        ]
      },
      "then": {
        "properties": {
          "evidence_ids": {
            "minItems": 1
          }
        }
      }
    }
  ],
  "description": "insufficient允许没有有效证据并返回空evidence_ids；其他关系至少引用一条同案件有权证据，不得为不足状态伪造证据UUID。"
}
```

## ReviewCreate

源指针：`#/components/schemas/ReviewCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：review_record.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| expected_review_version | 必须 | integer; minimum=0 | 候选字段来源：review_record.review_version：针对结果形成的复核版本号，复核更正不能覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| decision | 必须 | string; enum=["confirm_candidate", "reject_candidate", "return_for_evidence", "request_rerun"] | 候选字段来源：review_record.decision：本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：review_record.comments：复核意见原文，说明证据取舍及处理理由，后续更正追加版本。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：review_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：review_record.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "expected_review_version": {
      "type": "integer",
      "minimum": 0
    },
    "decision": {
      "type": "string",
      "enum": [
        "confirm_candidate",
        "reject_candidate",
        "return_for_evidence",
        "request_rerun"
      ]
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "task_id",
    "run_version",
    "result_version",
    "expected_review_version",
    "decision",
    "reason",
    "evidence_ids",
    "policy_version"
  ],
  "additionalProperties": false,
  "description": "业务复核决定不自动批准导出或训练回流。审批人员身份从服务端认证取得，不接受客户端reviewer_id。"
}
```

## Review

源指针：`#/components/schemas/Review`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| review_id | 必须 | string; format="uuid" | 候选字段来源：review_evidence.review_id：所引用业务复核记录标识；review_record.review_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| reviewer_id | 必须 | string; format="uuid" | 候选字段来源：review_record.reviewer_id：执行本次业务复核的用户标识，需有对应功能和案件权限。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：review_record.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| expected_review_version | 必须 | integer; minimum=0 | 候选字段来源：review_record.review_version：针对结果形成的复核版本号，复核更正不能覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| decision | 必须 | string; enum=["confirm_candidate", "reject_candidate", "return_for_evidence", "request_rerun"] | 候选字段来源：review_record.decision：本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：review_record.comments：复核意见原文，说明证据取舍及处理理由，后续更正追加版本。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：review_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：review_record.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| review_version | 必须 | integer; minimum=1 | 候选字段来源：review_record.review_version：针对结果形成的复核版本号，复核更正不能覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：audit_event.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；review_evidence.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；review_record.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "review_id": {
      "type": "string",
      "format": "uuid"
    },
    "reviewer_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "expected_review_version": {
      "type": "integer",
      "minimum": 0
    },
    "decision": {
      "type": "string",
      "enum": [
        "confirm_candidate",
        "reject_candidate",
        "return_for_evidence",
        "request_rerun"
      ]
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "review_version": {
      "type": "integer",
      "minimum": 1
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "review_id",
    "reviewer_id",
    "task_id",
    "run_version",
    "result_version",
    "expected_review_version",
    "decision",
    "reason",
    "evidence_ids",
    "policy_version",
    "review_version",
    "created_at"
  ],
  "additionalProperties": false
}
```

## ApprovalCreate

源指针：`#/components/schemas/ApprovalCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：approval_request.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限。来源引用不是写入许可，完整处理按操作核验。 |
| object_type | 必须 | string; enum=["task", "report", "evidence_package", "feedback", "model_release", "operation"] | 候选字段来源：approval_request.object_type：审批或审计目标对象类型，决定object_id应指向哪种业务对象。来源引用不是写入许可，完整处理按操作核验。 |
| object_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批；approval_request.result_version：分析对象绑定结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; enum=["review", "seal", "report_export", "training_feedback", "model_release", "confirmation"] | 候选字段来源：approval_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_request.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：approval_request.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.run_version：分析对象绑定运行版本。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.result_version：分析对象绑定结果版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "object_type": {
      "type": "string",
      "enum": [
        "task",
        "report",
        "evidence_package",
        "feedback",
        "model_release",
        "operation"
      ]
    },
    "object_id": {
      "type": "string",
      "format": "uuid"
    },
    "object_version": {
      "type": "integer",
      "minimum": 1
    },
    "purpose": {
      "type": "string",
      "enum": [
        "review",
        "seal",
        "report_export",
        "training_feedback",
        "model_release",
        "confirmation"
      ]
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "run_version": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "result_version": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 1
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "case_id",
    "object_type",
    "object_id",
    "object_version",
    "purpose",
    "policy_version",
    "reason",
    "run_version",
    "result_version"
  ],
  "additionalProperties": false,
  "description": "创建审批申请，不签发批准；confirmation只防误操作。模型发布是组织级审批，case_id必须null，不借此要求算法管理员访问案件。",
  "allOf": [
    {
      "if": {
        "properties": {
          "object_type": {
            "const": "model_release"
          }
        }
      },
      "then": {
        "properties": {
          "case_id": {
            "type": "null"
          },
          "purpose": {
            "const": "model_release"
          }
        }
      },
      "else": {
        "properties": {
          "case_id": {
            "type": "string",
            "format": "uuid"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "object_type": {
            "const": "task"
          }
        }
      },
      "then": {
        "properties": {
          "run_version": {
            "type": "integer",
            "minimum": 1
          },
          "result_version": {
            "type": "integer",
            "minimum": 1
          }
        }
      }
    }
  ]
}
```

## ApprovalDecision

源指针：`#/components/schemas/ApprovalDecision`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：approval_decision.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| decision | 必须 | string; enum=["approve", "reject", "return"] | 候选字段来源：approval_decision.decision：本次审批决定；取值由CHECK限制，不能替代对象版本和权限校验。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：approval_decision.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密；approval_request.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=0; items=string; format="uuid" | 候选字段来源：approval_decision.evidence_refs：支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "expected_version": {
      "type": "integer",
      "minimum": 1
    },
    "decision": {
      "type": "string",
      "enum": [
        "approve",
        "reject",
        "return"
      ]
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 0
    }
  },
  "required": [
    "expected_version",
    "decision",
    "reason",
    "evidence_ids"
  ],
  "additionalProperties": false
}
```

## Approval

源指针：`#/components/schemas/Approval`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：approval_decision.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过；approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["REQUESTED", "APPROVED", "REJECTED", "RETURNED", "REVOKED", "EXPIRED", "INVALIDATED"] | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_decision.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批；approval_request.result_version：分析对象绑定结果版本；audit_event.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：approval_decision.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析；approval_request.policy_version：本记录使用的业务、阈值或流程策略版本，需按其实际用途解析。来源引用不是写入许可，完整处理按操作核验。 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 候选字段来源：approval_request.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| decision_actor_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：approval_decision.decision_actor_id：作出审批决定的用户标识，由认证上下文与职责分离规则核验。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.run_version：分析对象绑定运行版本。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：approval_request.result_version：分析对象绑定结果版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "REQUESTED",
        "APPROVED",
        "REJECTED",
        "RETURNED",
        "REVOKED",
        "EXPIRED",
        "INVALIDATED"
      ]
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "object_version": {
      "type": "integer",
      "minimum": 1
    },
    "purpose": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "expires_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "decision_actor_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "run_version": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "result_version": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 1
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "approval_id",
    "state",
    "version",
    "object_version",
    "purpose",
    "policy_version",
    "expires_at",
    "decision_actor_id",
    "run_version",
    "result_version"
  ],
  "additionalProperties": false
}
```

## OperationTokenRequest

源指针：`#/components/schemas/OperationTokenRequest`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：operation_token.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| object_id | 必须 | string; format="uuid" | 候选字段来源：operation_token.object_id：该记录绑定的业务目标对象ID；沿用关联审批请求的对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：operation_token.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：operation_token.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "object_id": {
      "type": "string",
      "format": "uuid"
    },
    "object_version": {
      "type": "integer",
      "minimum": 1
    },
    "purpose": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "approval_id",
    "object_id",
    "object_version",
    "purpose"
  ],
  "additionalProperties": false,
  "description": "须已有生效授权；token一次性并绑定当前主体、用途和对象版本。"
}
```

## OperationToken

源指针：`#/components/schemas/OperationToken`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| operation_token | 必须 | string; minLength=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expires_at | 必须 | string; format="date-time" | 候选字段来源：operation_token.expires_at：此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | integer; minimum=1 | 候选字段来源：operation_token.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "operation_token": {
      "type": "string",
      "minLength": 1
    },
    "expires_at": {
      "type": "string",
      "format": "date-time"
    },
    "object_version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "operation_token",
    "expires_at",
    "object_version"
  ],
  "additionalProperties": false
}
```

## SealRequest

源指针：`#/components/schemas/SealRequest`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：evidence_package.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：evidence_package.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：package_item.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| operation_token | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| retention_policy_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：evidence_package.retention_policy_version：用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效；object_version.retention_policy_version：用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "operation_token": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "retention_policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "task_id",
    "run_version",
    "result_version",
    "evidence_ids",
    "approval_id",
    "operation_token",
    "retention_policy_version"
  ],
  "additionalProperties": false
}
```

## EvidencePackage

源指针：`#/components/schemas/EvidencePackage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| package_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.package_id：主键，由应用提供UUID；不视为访问凭证；package_item.package_id：固化证据包的版本记录标识。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；evidence_package.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；object_version.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；package_item.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；evidence_package.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；evidence_package.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version；object_version.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；package_item.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| manifest | 必须 | array; minItems=0; items=Evidence | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| manifest_sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：evidence_package.manifest_sha256：固化证据包规范化清单的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：evidence_package.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| signature_status | 必须 | string; enum=["not_signed", "mock", "verified", "failed"] | 候选字段来源：evidence_package.signature_status：证据包签名处理状态；状态文字不能代替签名验证证据。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["DRAFT", "SEALED", "SUPERSEDED"] | 候选字段来源：evidence_package.state：固化证据包版本的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：audit_event.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；evidence_package.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；object_version.created_at：对象版本登记入库时刻；TIMESTAMPTZ保存时间点，显示时区由会话决定，不保留原始时区名称；package_item.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "package_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "manifest": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Evidence"
      },
      "minItems": 0
    },
    "manifest_sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "signature_status": {
      "type": "string",
      "enum": [
        "not_signed",
        "mock",
        "verified",
        "failed"
      ]
    },
    "state": {
      "type": "string",
      "enum": [
        "DRAFT",
        "SEALED",
        "SUPERSEDED"
      ]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "package_id",
    "case_id",
    "task_id",
    "version",
    "manifest",
    "manifest_sha256",
    "approval_id",
    "signature_status",
    "state",
    "created_at"
  ],
  "additionalProperties": false
}
```

## ReportDraft

源指针：`#/components/schemas/ReportDraft`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：report.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；report_evidence.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：report.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：report.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：report.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| template_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：report.template_version：生成报告使用的模板版本，确保历史报告可以重现。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：report_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "template_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1,
      "uniqueItems": true
    }
  },
  "required": [
    "case_id",
    "task_id",
    "run_version",
    "result_version",
    "template_version",
    "evidence_ids"
  ],
  "additionalProperties": false
}
```

## ReportCreate

源指针：`#/components/schemas/ReportCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；report.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；report_evidence.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：report.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.run_version：分析对象绑定运行版本；report.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.result_version：分析对象绑定结果版本；report.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| template_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：report.template_version：生成报告使用的模板版本，确保历史报告可以重现。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; uniqueItems=true; items=string; format="uuid" | 候选字段来源：report_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证；report.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| operation_token | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "template_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "operation_token": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    }
  },
  "required": [
    "case_id",
    "task_id",
    "run_version",
    "result_version",
    "template_version",
    "evidence_ids",
    "approval_id",
    "operation_token"
  ],
  "additionalProperties": false
}
```

## Report

源指针：`#/components/schemas/Report`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| report_id | 必须 | string; format="uuid" | 候选字段来源：report.report_id：主键，由应用提供UUID；不视为访问凭证；report_evidence.report_id：报告版本记录标识。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；report.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验；report_evidence.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| task_id | 必须 | string; format="uuid" | 候选字段来源：report.task_id：关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本。来源引用不是写入许可，完整处理按操作核验。 |
| run_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.run_version：分析对象绑定运行版本；report.run_version：分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算。来源引用不是写入许可，完整处理按操作核验。 |
| result_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.result_version：分析对象绑定结果版本；report.result_version：给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；report.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；report.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version；report_evidence.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["DRAFT", "GENERATING", "READY", "FAILED", "SUPERSEDED"] | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；report.state：报告生成与下载状态的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证；report.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| object_ref | 必须 | anyOf(ObjectRef; null) | 候选字段来源：object_version.object_id：主键，由应用提供UUID；不视为访问凭证；object_version.sha256：该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性；object_version.version_id：对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：evidence_item.evidence_id：主键，由应用提供UUID；不视为访问凭证；report_evidence.evidence_id：所引用证据事实版本标识，指向同案件evidence_item.evidence_id。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：approval_request.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；report.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名；report_evidence.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "report_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "state": {
      "type": "string",
      "enum": [
        "DRAFT",
        "GENERATING",
        "READY",
        "FAILED",
        "SUPERSEDED"
      ]
    },
    "approval_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "object_ref": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ObjectRef"
        },
        {
          "type": "null"
        }
      ]
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "report_id",
    "case_id",
    "task_id",
    "run_version",
    "result_version",
    "version",
    "state",
    "approval_id",
    "object_ref",
    "evidence_ids",
    "created_at"
  ],
  "additionalProperties": false
}
```

## Feedback

源指针：`#/components/schemas/Feedback`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| case_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；feedback_request.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| finding_id | 必须 | string; format="uuid" | 候选字段来源：feedback_request.finding_id：申请回流的风险发现标识；用途审批通过也须另核验来源授权。来源引用不是写入许可，完整处理按操作核验。 |
| label_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：feedback_request.label_version：本次标注使用的标签体系版本。来源引用不是写入许可，完整处理按操作核验。 |
| label | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：feedback_request.label：人工确认或申请使用的训练标签；不可直接把模型预测视为真值。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | const="training" | 候选字段来源：approval_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符；feedback_request.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| source_authorization_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：feedback_request.source_authorization_ref：允许该素材用于指定回流或训练用途的来源授权记录引用。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：approval_request.reason：状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "finding_id": {
      "type": "string",
      "format": "uuid"
    },
    "label_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "label": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "purpose": {
      "const": "training"
    },
    "source_authorization_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    }
  },
  "required": [
    "case_id",
    "finding_id",
    "label_version",
    "label",
    "purpose",
    "source_authorization_ref",
    "reason"
  ],
  "additionalProperties": false
}
```

## FeedbackRecord

源指针：`#/components/schemas/FeedbackRecord`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| feedback_id | 必须 | string; format="uuid" | 候选字段来源：feedback_request.feedback_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证；feedback_request.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["REQUESTED", "APPROVED", "REJECTED", "REVOKED", "APPLIED"] | 候选字段来源：approval_request.state：按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；feedback_request.state：纠错训练用途申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；feedback_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "feedback_id": {
      "type": "string",
      "format": "uuid"
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "REQUESTED",
        "APPROVED",
        "REJECTED",
        "REVOKED",
        "APPLIED"
      ]
    },
    "version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "feedback_id",
    "approval_id",
    "state",
    "version"
  ],
  "additionalProperties": false
}
```

## ModelCreate

源指针：`#/components/schemas/ModelCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.name：名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| capability | 必须 | string; enum=["risk.image_classification", "risk.object_detection", "risk.small_object", "risk.video_action", "risk.temporal_event", "risk.audio_event", "risk.consistency", "risk.fusion", "forensic.image_localization", "forensic.tamper_type", "forensic.video_temporal", "forensic.video_spatial", "forensic.deepfake", "forensic.avsync", "retrieval.image_embedding", "retrieval.local_features", "retrieval.local_match", "retrieval.geometry", "retrieval.frame_embedding", "retrieval.temporal_alignment", "retrieval.segment_localizer", "retrieval.source_boundary", "origin.content_cluster", "origin.first_source_rank", "model.calibration", "propagation.path", "propagation.inferred_edge", "claim.extract", "claim.evidence_relation", "claim.grounding", "media.ocr", "media.asr", "media.audio_fingerprint", "model.compression"] | 候选字段来源：model_registry.capability：模型或索引提供的能力编码，取值对应内部推理能力契约。来源引用不是写入许可，完整处理按操作核验。 |
| digest | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：model_registry.digest：注册模型权重或模型包的SHA-256，具体制品范围记录于模型卡；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| model_card_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.model_card_ref：模型卡的受控版本引用，说明用途、限制和训练评测信息。来源引用不是写入许可，完整处理按操作核验。 |
| license_record_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.license_record_ref：代码与权重许可核查记录引用，需覆盖本项目预定用途。来源引用不是写入许可，完整处理按操作核验。 |
| backend | 必须 | string; enum=["pytorch", "onnxruntime", "triton", "other_reviewed"] | 候选字段来源：model_registry.backend：实际运行推理后端标识，例如经选型的框架适配器；不是模型名称。来源引用不是写入许可，完整处理按操作核验。 |
| environment_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.environment_ref：可重建运行环境说明或镜像摘要的受控引用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "capability": {
      "type": "string",
      "enum": [
        "risk.image_classification",
        "risk.object_detection",
        "risk.small_object",
        "risk.video_action",
        "risk.temporal_event",
        "risk.audio_event",
        "risk.consistency",
        "risk.fusion",
        "forensic.image_localization",
        "forensic.tamper_type",
        "forensic.video_temporal",
        "forensic.video_spatial",
        "forensic.deepfake",
        "forensic.avsync",
        "retrieval.image_embedding",
        "retrieval.local_features",
        "retrieval.local_match",
        "retrieval.geometry",
        "retrieval.frame_embedding",
        "retrieval.temporal_alignment",
        "retrieval.segment_localizer",
        "retrieval.source_boundary",
        "origin.content_cluster",
        "origin.first_source_rank",
        "model.calibration",
        "propagation.path",
        "propagation.inferred_edge",
        "claim.extract",
        "claim.evidence_relation",
        "claim.grounding",
        "media.ocr",
        "media.asr",
        "media.audio_fingerprint",
        "model.compression"
      ]
    },
    "digest": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "dataset_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "model_card_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "license_record_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "backend": {
      "type": "string",
      "enum": [
        "pytorch",
        "onnxruntime",
        "triton",
        "other_reviewed"
      ]
    },
    "environment_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    }
  },
  "required": [
    "name",
    "version",
    "capability",
    "digest",
    "dataset_version",
    "model_card_ref",
    "license_record_ref",
    "backend",
    "environment_ref"
  ],
  "additionalProperties": false
}
```

## Model

源指针：`#/components/schemas/Model`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| model_id | 必须 | string; format="uuid" | 候选字段来源：model_registry.model_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| name | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.name：名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| capability | 必须 | string; enum=["risk.image_classification", "risk.object_detection", "risk.small_object", "risk.video_action", "risk.temporal_event", "risk.audio_event", "risk.consistency", "risk.fusion", "forensic.image_localization", "forensic.tamper_type", "forensic.video_temporal", "forensic.video_spatial", "forensic.deepfake", "forensic.avsync", "retrieval.image_embedding", "retrieval.local_features", "retrieval.local_match", "retrieval.geometry", "retrieval.frame_embedding", "retrieval.temporal_alignment", "retrieval.segment_localizer", "retrieval.source_boundary", "origin.content_cluster", "origin.first_source_rank", "model.calibration", "propagation.path", "propagation.inferred_edge", "claim.extract", "claim.evidence_relation", "claim.grounding", "media.ocr", "media.asr", "media.audio_fingerprint", "model.compression"] | 候选字段来源：model_registry.capability：模型或索引提供的能力编码，取值对应内部推理能力契约。来源引用不是写入许可，完整处理按操作核验。 |
| digest | 必须 | string; pattern="^[a-f0-9]{64}$" | 候选字段来源：model_registry.digest：注册模型权重或模型包的SHA-256，具体制品范围记录于模型卡；存储64位小写十六进制，正则只检查格式不验证字节真实性。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| model_card_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.model_card_ref：模型卡的受控版本引用，说明用途、限制和训练评测信息。来源引用不是写入许可，完整处理按操作核验。 |
| license_record_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.license_record_ref：代码与权重许可核查记录引用，需覆盖本项目预定用途。来源引用不是写入许可，完整处理按操作核验。 |
| backend | 必须 | string; enum=["pytorch", "onnxruntime", "triton", "other_reviewed"] | 候选字段来源：model_registry.backend：实际运行推理后端标识，例如经选型的框架适配器；不是模型名称。来源引用不是写入许可，完整处理按操作核验。 |
| environment_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_registry.environment_ref：可重建运行环境说明或镜像摘要的受控引用。来源引用不是写入许可，完整处理按操作核验。 |
| status | 必须 | string; enum=["REGISTERED", "EVALUATED", "CANDIDATE", "APPROVED", "ACTIVE", "RETIRED"] | 候选字段来源：model_registry.status：模型版本与许可引用的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| row_version | 必须 | integer; minimum=1 | 候选字段来源：model_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "model_id": {
      "type": "string",
      "format": "uuid"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "capability": {
      "type": "string",
      "enum": [
        "risk.image_classification",
        "risk.object_detection",
        "risk.small_object",
        "risk.video_action",
        "risk.temporal_event",
        "risk.audio_event",
        "risk.consistency",
        "risk.fusion",
        "forensic.image_localization",
        "forensic.tamper_type",
        "forensic.video_temporal",
        "forensic.video_spatial",
        "forensic.deepfake",
        "forensic.avsync",
        "retrieval.image_embedding",
        "retrieval.local_features",
        "retrieval.local_match",
        "retrieval.geometry",
        "retrieval.frame_embedding",
        "retrieval.temporal_alignment",
        "retrieval.segment_localizer",
        "retrieval.source_boundary",
        "origin.content_cluster",
        "origin.first_source_rank",
        "model.calibration",
        "propagation.path",
        "propagation.inferred_edge",
        "claim.extract",
        "claim.evidence_relation",
        "claim.grounding",
        "media.ocr",
        "media.asr",
        "media.audio_fingerprint",
        "model.compression"
      ]
    },
    "digest": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "dataset_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "model_card_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "license_record_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "backend": {
      "type": "string",
      "enum": [
        "pytorch",
        "onnxruntime",
        "triton",
        "other_reviewed"
      ]
    },
    "environment_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "status": {
      "type": "string",
      "enum": [
        "REGISTERED",
        "EVALUATED",
        "CANDIDATE",
        "APPROVED",
        "ACTIVE",
        "RETIRED"
      ]
    },
    "row_version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "model_id",
    "name",
    "version",
    "capability",
    "digest",
    "dataset_version",
    "model_card_ref",
    "license_record_ref",
    "backend",
    "environment_ref",
    "status",
    "row_version"
  ],
  "additionalProperties": false
}
```

## Rollout

源指针：`#/components/schemas/Rollout`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| release_bundle_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：approval_request.approval_id：主键，由应用提供UUID；不视为访问凭证；model_release.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| operation_token | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：approval_request.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；model_release.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| mode | 必须 | string; enum=["shadow", "canary", "activate", "rollback"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| percentage | 必须 | number; minimum=0; maximum=100 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| index_version | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：index_registry.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本；model_release.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "release_bundle_id": {
      "type": "string",
      "format": "uuid"
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "operation_token": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "expected_version": {
      "type": "integer",
      "minimum": 1
    },
    "mode": {
      "type": "string",
      "enum": [
        "shadow",
        "canary",
        "activate",
        "rollback"
      ]
    },
    "percentage": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "index_version": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "release_bundle_id",
    "approval_id",
    "operation_token",
    "expected_version",
    "mode",
    "percentage",
    "index_version"
  ],
  "additionalProperties": false
}
```

## EvaluationCreate

源指针：`#/components/schemas/EvaluationCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| model_id | 必须 | string; format="uuid" | 候选字段来源：model_evaluation.model_id：模型注册记录标识，引用同单位的model_registry.model_id。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_id：数据集目录的稳定文本编号，例如D01；不是数据库UUID主键。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| protocol_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.protocol_id：评测协议标识，决定指标公式、样本计数、阈值及统计口径。来源引用不是写入许可，完整处理按操作核验。 |
| split | 必须 | string; enum=["validation", "calibration", "holdout"] | 候选字段来源：model_evaluation.split：此次评测使用的划分用途；封存holdout不能用于训练或调参。来源引用不是写入许可，完整处理按操作核验。 |
| sample_count | 必须 | integer; minimum=1 | 候选字段来源：model_evaluation.sample_count：按照评测协议统计的样本数，必须为正；不能混用帧数、素材组数和文件数。来源引用不是写入许可，完整处理按操作核验。 |
| failure_count | 必须 | integer; minimum=0 | 候选字段来源：model_evaluation.failure_count：处理失败样本数，范围0到sample_count，不应从评测分母中隐式删除。来源引用不是写入许可，完整处理按操作核验。 |
| metrics | 必须 | object; additionalProperties=false | 候选字段来源：model_evaluation.metrics：评测协议规定的指标结果对象；需保留失败计数和适用样本口径。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| metrics.macro_f1 | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.iou | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall_at_k | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.ece | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.boundary_mae_ms | 必须（父对象存在时） | anyOf(number; minimum=0; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifact_ref | 必须 | ObjectRef | 候选字段来源：model_evaluation.artifact_ref：评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "model_id": {
      "type": "string",
      "format": "uuid"
    },
    "dataset_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "dataset_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "protocol_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "split": {
      "type": "string",
      "enum": [
        "validation",
        "calibration",
        "holdout"
      ]
    },
    "sample_count": {
      "type": "integer",
      "minimum": 1
    },
    "failure_count": {
      "type": "integer",
      "minimum": 0
    },
    "metrics": {
      "type": "object",
      "properties": {
        "macro_f1": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "recall": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "iou": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "recall_at_k": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "ece": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "boundary_mae_ms": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "macro_f1",
        "recall",
        "iou",
        "recall_at_k",
        "ece",
        "boundary_mae_ms"
      ],
      "additionalProperties": false
    },
    "artifact_ref": {
      "$ref": "#/components/schemas/ObjectRef"
    }
  },
  "required": [
    "model_id",
    "dataset_id",
    "dataset_version",
    "protocol_id",
    "split",
    "sample_count",
    "failure_count",
    "metrics",
    "artifact_ref"
  ],
  "additionalProperties": false
}
```

## Evaluation

源指针：`#/components/schemas/Evaluation`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| evaluation_id | 必须 | string; format="uuid" | 候选字段来源：model_evaluation.evaluation_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| model_id | 必须 | string; format="uuid" | 候选字段来源：model_evaluation.model_id：模型注册记录标识，引用同单位的model_registry.model_id。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_id：数据集目录的稳定文本编号，例如D01；不是数据库UUID主键。来源引用不是写入许可，完整处理按操作核验。 |
| dataset_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.dataset_version：本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录。来源引用不是写入许可，完整处理按操作核验。 |
| protocol_id | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：model_evaluation.protocol_id：评测协议标识，决定指标公式、样本计数、阈值及统计口径。来源引用不是写入许可，完整处理按操作核验。 |
| split | 必须 | string; enum=["validation", "calibration", "holdout"] | 候选字段来源：model_evaluation.split：此次评测使用的划分用途；封存holdout不能用于训练或调参。来源引用不是写入许可，完整处理按操作核验。 |
| sample_count | 必须 | integer; minimum=1 | 候选字段来源：model_evaluation.sample_count：按照评测协议统计的样本数，必须为正；不能混用帧数、素材组数和文件数。来源引用不是写入许可，完整处理按操作核验。 |
| failure_count | 必须 | integer; minimum=0 | 候选字段来源：model_evaluation.failure_count：处理失败样本数，范围0到sample_count，不应从评测分母中隐式删除。来源引用不是写入许可，完整处理按操作核验。 |
| metrics | 必须 | object; additionalProperties=false | 候选字段来源：model_evaluation.metrics：评测协议规定的指标结果对象；需保留失败计数和适用样本口径。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| metrics.macro_f1 | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.iou | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.recall_at_k | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.ece | 必须（父对象存在时） | anyOf(number; minimum=0; maximum=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| metrics.boundary_mae_ms | 必须（父对象存在时） | anyOf(number; minimum=0; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifact_ref | 必须 | ObjectRef | 候选字段来源：model_evaluation.artifact_ref：评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |
| created_at | 必须 | string; format="date-time" | 候选字段来源：model_evaluation.created_at：记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "evaluation_id": {
      "type": "string",
      "format": "uuid"
    },
    "model_id": {
      "type": "string",
      "format": "uuid"
    },
    "dataset_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "dataset_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "protocol_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "split": {
      "type": "string",
      "enum": [
        "validation",
        "calibration",
        "holdout"
      ]
    },
    "sample_count": {
      "type": "integer",
      "minimum": 1
    },
    "failure_count": {
      "type": "integer",
      "minimum": 0
    },
    "metrics": {
      "type": "object",
      "properties": {
        "macro_f1": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "recall": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "iou": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "recall_at_k": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "ece": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            {
              "type": "null"
            }
          ]
        },
        "boundary_mae_ms": {
          "anyOf": [
            {
              "type": "number",
              "minimum": 0
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "macro_f1",
        "recall",
        "iou",
        "recall_at_k",
        "ece",
        "boundary_mae_ms"
      ],
      "additionalProperties": false
    },
    "artifact_ref": {
      "$ref": "#/components/schemas/ObjectRef"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "evaluation_id",
    "model_id",
    "dataset_id",
    "dataset_version",
    "protocol_id",
    "split",
    "sample_count",
    "failure_count",
    "metrics",
    "artifact_ref",
    "created_at"
  ],
  "additionalProperties": false
}
```

## AuditEvent

源指针：`#/components/schemas/AuditEvent`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| event_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.event_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| actor_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.actor_id：操作主体标识；从服务端认证上下文取得，系统动作的可空条件须另有审计规则。来源引用不是写入许可，完整处理按操作核验。 |
| org_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.org_id：该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：audit_event.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限。来源引用不是写入许可，完整处理按操作核验。 |
| action | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：audit_event.action：被审计业务操作的稳定编码，不是主张文本中的行为。来源引用不是写入许可，完整处理按操作核验。 |
| object_type | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：audit_event.object_type：审批或审计目标对象类型，决定object_id应指向哪种业务对象。来源引用不是写入许可，完整处理按操作核验。 |
| object_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：audit_event.object_id：该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键。来源引用不是写入许可，完整处理按操作核验。 |
| object_version | 必须 | anyOf(integer; minimum=1; null) | 候选字段来源：audit_event.object_version：审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批。来源引用不是写入许可，完整处理按操作核验。 |
| outcome | 必须 | string; enum=["allowed", "denied", "failed"] | 候选字段来源：audit_event.outcome：审计操作的结果编码，例如允许、拒绝或失败；须与实际处理一致。来源引用不是写入许可，完整处理按操作核验。 |
| request_id | 必须 | string; format="uuid" | 候选字段来源：audit_event.request_id：贯穿接口、任务和审计的请求追踪标识；不充当权限凭证。来源引用不是写入许可，完整处理按操作核验。 |
| occurred_at | 必须 | string; format="date-time" | 候选字段来源：audit_event.occurred_at：被审计操作实际发生时刻，区别于记录写入时间created_at；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid"
    },
    "actor_id": {
      "type": "string",
      "format": "uuid"
    },
    "org_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "action": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "object_type": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "object_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "object_version": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "outcome": {
      "type": "string",
      "enum": [
        "allowed",
        "denied",
        "failed"
      ]
    },
    "request_id": {
      "type": "string",
      "format": "uuid"
    },
    "occurred_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "event_id",
    "actor_id",
    "org_id",
    "case_id",
    "action",
    "object_type",
    "object_id",
    "object_version",
    "outcome",
    "request_id",
    "occurred_at"
  ],
  "additionalProperties": false
}
```

## AuditExport

源指针：`#/components/schemas/AuditExport`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| start_at | 必须 | string; format="date-time" | 候选字段来源：audit_export.start_at：审计导出查询的起始时刻；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| end_at | 必须 | string; format="date-time" | 候选字段来源：audit_export.end_at：审计导出查询的结束时刻，必须与起始时刻构成有效区间；存储时间点，显示受会话时区影响，接口必须携带时区。来源引用不是写入许可，完整处理按操作核验。 |
| case_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：audit_event.case_id：案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限；audit_export.case_id：该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验。来源引用不是写入许可，完整处理按操作核验。 |
| purpose | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：audit_export.purpose：本记录声明或申请的处理用途，实际动作需与有效授权用途相符。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | string; format="uuid" | 候选字段来源：audit_export.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "start_at": {
      "type": "string",
      "format": "date-time"
    },
    "end_at": {
      "type": "string",
      "format": "date-time"
    },
    "case_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "purpose": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "start_at",
    "end_at",
    "case_id",
    "purpose",
    "approval_id"
  ],
  "additionalProperties": false
}
```

## IndexVersion

源指针：`#/components/schemas/IndexVersion`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| index_id | 必须 | string; format="uuid" | 候选字段来源：index_registry.index_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| capability | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.capability：模型或索引提供的能力编码，取值对应内部推理能力契约。来源引用不是写入许可，完整处理按操作核验。 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.model_version：生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本。来源引用不是写入许可，完整处理按操作核验。 |
| dimension | 必须 | integer; minimum=1 | 候选字段来源：index_registry.dimension：特征向量维度，必须为正整数并与模型及索引配置一致。来源引用不是写入许可，完整处理按操作核验。 |
| normalization | 必须 | string; enum=["l2", "none"] | 候选字段来源：index_registry.normalization：特征归一化方法，例如l2或none；应与训练、查询和索引构建保持一致。来源引用不是写入许可，完整处理按操作核验。 |
| index_version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：index_registry.index_version：本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["BUILDING", "READY", "ACTIVE", "RETIRED"] | 候选字段来源：index_registry.state：索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| row_version | 必须 | integer; minimum=1 | 候选字段来源：audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "index_id": {
      "type": "string",
      "format": "uuid"
    },
    "capability": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "model_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "dimension": {
      "type": "integer",
      "minimum": 1
    },
    "normalization": {
      "type": "string",
      "enum": [
        "l2",
        "none"
      ]
    },
    "index_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "state": {
      "type": "string",
      "enum": [
        "BUILDING",
        "READY",
        "ACTIVE",
        "RETIRED"
      ]
    },
    "row_version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "index_id",
    "capability",
    "model_version",
    "dimension",
    "normalization",
    "index_version",
    "state",
    "row_version"
  ],
  "additionalProperties": false
}
```

## IndexSwitch

源指针：`#/components/schemas/IndexSwitch`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：audit_event.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；index_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| target_index_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| approval_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "expected_version": {
      "type": "integer",
      "minimum": 1
    },
    "target_index_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "approval_id": {
      "type": "string",
      "format": "uuid"
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    }
  },
  "required": [
    "expected_version",
    "target_index_version",
    "approval_id",
    "reason"
  ],
  "additionalProperties": false
}
```

## PolicyCreate

源指针：`#/components/schemas/PolicyCreate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| kind | 必须 | string; enum=["risk_taxonomy", "threshold", "review", "retention", "analysis"] | 候选字段来源：policy_registry.kind：策略类别，如标签、阈值、流程或保留规则；类别词表由配置登记。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；policy_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| definition_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.definition_ref：完整策略定义文档或配置的受控引用，应可定位不可变版本。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：policy_registry.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| status | 必须 | string; enum=["DRAFT", "APPROVED"] | 候选字段来源：policy_registry.status：标签阈值流程保留等策略的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "kind": {
      "type": "string",
      "enum": [
        "risk_taxonomy",
        "threshold",
        "review",
        "retention",
        "analysis"
      ]
    },
    "version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "definition_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "approval_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "status": {
      "type": "string",
      "enum": [
        "DRAFT",
        "APPROVED"
      ]
    }
  },
  "required": [
    "kind",
    "version",
    "definition_ref",
    "approval_id",
    "status"
  ],
  "additionalProperties": false
}
```

## Policy

源指针：`#/components/schemas/Policy`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| policy_id | 必须 | string; format="uuid" | 候选字段来源：policy_registry.policy_id：主键，由应用提供UUID；不视为访问凭证。来源引用不是写入许可，完整处理按操作核验。 |
| kind | 必须 | string; enum=["risk_taxonomy", "threshold", "review", "retention", "analysis"] | 候选字段来源：policy_registry.kind：策略类别，如标签、阈值、流程或保留规则；类别词表由配置登记。来源引用不是写入许可，完整处理按操作核验。 |
| version | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；policy_registry.version：此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version。来源引用不是写入许可，完整处理按操作核验。 |
| definition_ref | 必须 | string; minLength=1; maxLength=128 | 候选字段来源：policy_registry.definition_ref：完整策略定义文档或配置的受控引用，应可定位不可变版本。来源引用不是写入许可，完整处理按操作核验。 |
| approval_id | 必须 | anyOf(string; format="uuid"; null) | 候选字段来源：policy_registry.approval_id：与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过。来源引用不是写入许可，完整处理按操作核验。 |
| status | 必须 | string; enum=["DRAFT", "APPROVED"] | 候选字段来源：policy_registry.status：标签阈值流程保留等策略的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| row_version | 必须 | integer; minimum=1 | 候选字段来源：policy_registry.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "policy_id": {
      "type": "string",
      "format": "uuid"
    },
    "kind": {
      "type": "string",
      "enum": [
        "risk_taxonomy",
        "threshold",
        "review",
        "retention",
        "analysis"
      ]
    },
    "version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "definition_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "approval_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ]
    },
    "status": {
      "type": "string",
      "enum": [
        "DRAFT",
        "APPROVED"
      ]
    },
    "row_version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "policy_id",
    "kind",
    "version",
    "definition_ref",
    "approval_id",
    "status",
    "row_version"
  ],
  "additionalProperties": false
}
```

## GraphDecision

源指针：`#/components/schemas/GraphDecision`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| expected_version | 必须 | integer; minimum=1 | 候选字段来源：propagation_edge.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值；review_record.row_version：本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值。来源引用不是写入许可，完整处理按操作核验。 |
| decision | 必须 | string; enum=["confirm", "reject"] | 候选字段来源：review_record.decision：本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验。来源引用不是写入许可，完整处理按操作核验。 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 候选字段来源：review_record.comments：复核意见原文，说明证据取舍及处理理由，后续更正追加版本。来源引用不是写入许可，完整处理按操作核验。 |
| evidence_ids | 必须 | array; minItems=1; items=string; format="uuid" | 候选字段来源：propagation_edge.evidence_refs：支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "expected_version": {
      "type": "integer",
      "minimum": 1
    },
    "decision": {
      "type": "string",
      "enum": [
        "confirm",
        "reject"
      ]
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "evidence_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "minItems": 1
    }
  },
  "required": [
    "expected_version",
    "decision",
    "reason",
    "evidence_ids"
  ],
  "additionalProperties": false
}
```

## TaskPage

源指针：`#/components/schemas/TaskPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Task | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Task"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## AssetPage

源指针：`#/components/schemas/AssetPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Asset | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Asset"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## SourcePage

源指针：`#/components/schemas/SourcePage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Source | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Source"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## EvidencePage

源指针：`#/components/schemas/EvidencePage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Evidence | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Evidence"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## ModelPage

源指针：`#/components/schemas/ModelPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Model | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Model"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## EvaluationPage

源指针：`#/components/schemas/EvaluationPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Evaluation | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Evaluation"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## AuditEventPage

源指针：`#/components/schemas/AuditEventPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=AuditEvent | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/AuditEvent"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## PolicyPage

源指针：`#/components/schemas/PolicyPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; minItems=0; items=Policy | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Policy"
      },
      "minItems": 0
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## SearchAccepted

源指针：`#/components/schemas/SearchAccepted`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| search_id | 必须 | string; format="uuid" | 候选字段来源：source_match.search_id：产生匹配候选的异步检索作业标识。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["QUEUED", "RUNNING"] | 候选字段来源：index_registry.state：索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效；media_asset.state：原始或派生媒体的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| status_url | 必须 | string; pattern="^/api/v1/search/jobs/" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "search_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "QUEUED",
        "RUNNING"
      ]
    },
    "status_url": {
      "type": "string",
      "pattern": "^/api/v1/search/jobs/"
    }
  },
  "required": [
    "search_id",
    "state",
    "status_url"
  ],
  "additionalProperties": false
}
```

## SearchJob

源指针：`#/components/schemas/SearchJob`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| search_id | 必须 | string; format="uuid" | 候选字段来源：search_job.search_id：主键，由应用提供UUID；不视为访问凭证；source_match.search_id：产生匹配候选的异步检索作业标识。来源引用不是写入许可，完整处理按操作核验。 |
| state | 必须 | string; enum=["SUCCEEDED", "QUEUED", "RUNNING", "FAILED"] | 候选字段来源：search_job.state：异步检索任务的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效。来源引用不是写入许可，完整处理按操作核验。 |
| result | 必须 | anyOf(SearchResults; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| error_code | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 候选字段来源：search_job.error_code：失败原因的稳定错误码；无失败时允许NULL，用户说明与诊断堆栈分开。来源引用不是写入许可，完整处理按操作核验。 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "search_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "SUCCEEDED",
        "QUEUED",
        "RUNNING",
        "FAILED"
      ]
    },
    "result": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/SearchResults"
        },
        {
          "type": "null"
        }
      ]
    },
    "error_code": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "search_id",
    "state",
    "result",
    "error_code"
  ],
  "additionalProperties": false,
  "allOf": [
    {
      "if": {
        "properties": {
          "state": {
            "const": "SUCCEEDED"
          }
        }
      },
      "then": {
        "properties": {
          "result": {
            "not": {
              "type": "null"
            }
          }
        }
      },
      "else": {
        "properties": {
          "result": {
            "type": "null"
          }
        }
      }
    }
  ]
}
```

## UploadStatus

源指针：`#/components/schemas/UploadStatus`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| session | 必须 | UploadSession | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| result | 必须 | anyOf(UploadResult; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| received_parts_count | 必须 | integer; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| received_bytes | 必须 | integer; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| total_size_bytes | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "session": {
      "$ref": "#/components/schemas/UploadSession"
    },
    "result": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/UploadResult"
        },
        {
          "type": "null"
        }
      ]
    },
    "received_parts_count": {
      "type": "integer",
      "minimum": 0
    },
    "received_bytes": {
      "type": "integer",
      "minimum": 0
    },
    "total_size_bytes": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "session",
    "result",
    "received_parts_count",
    "received_bytes",
    "total_size_bytes"
  ],
  "additionalProperties": false,
  "description": "真实持久化分片进度；UPLOADING/EXPIRED无结果，只有COMPLETED/VALID允许形成有效资产。"
}
```

## UploadPartPage

源指针：`#/components/schemas/UploadPartPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; items=UploadPart | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| session_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/UploadPart"
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1
        },
        {
          "type": "null"
        }
      ]
    },
    "session_version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "items",
    "next_cursor",
    "session_version"
  ],
  "additionalProperties": false
}
```

## ApprovalDetail

源指针：`#/components/schemas/ApprovalDetail`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| approval | 必须 | Approval | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding | 必须 | object; additionalProperties=false | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.case_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.object_type | 必须（父对象存在时） | string; enum=["task", "report", "evidence_package", "feedback", "model_release", "operation"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.object_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| binding.requested_by | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions | 必须 | array; items=object; additionalProperties=false | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].decision_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].decision | 必须（父对象存在时） | string; enum=["approve", "reject", "return", "revoke", "invalidate"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].actor_id | 必须（父对象存在时） | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].reason | 必须（父对象存在时） | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].evidence_ids | 必须（父对象存在时） | array; items=string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| decisions[].created_at | 必须（父对象存在时） | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "approval": {
      "$ref": "#/components/schemas/Approval"
    },
    "binding": {
      "type": "object",
      "properties": {
        "case_id": {
          "type": "string",
          "format": "uuid"
        },
        "object_type": {
          "type": "string",
          "enum": [
            "task",
            "report",
            "evidence_package",
            "feedback",
            "model_release",
            "operation"
          ]
        },
        "object_id": {
          "type": "string",
          "format": "uuid"
        },
        "requested_by": {
          "type": "string",
          "format": "uuid"
        }
      },
      "required": [
        "case_id",
        "object_type",
        "object_id",
        "requested_by"
      ],
      "additionalProperties": false
    },
    "decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "decision_id": {
            "type": "string",
            "format": "uuid"
          },
          "decision": {
            "type": "string",
            "enum": [
              "approve",
              "reject",
              "return",
              "revoke",
              "invalidate"
            ]
          },
          "actor_id": {
            "type": "string",
            "format": "uuid"
          },
          "reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 4096
          },
          "evidence_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "format": "uuid"
            }
          },
          "created_at": {
            "type": "string",
            "format": "date-time"
          }
        },
        "required": [
          "decision_id",
          "decision",
          "actor_id",
          "reason",
          "evidence_ids",
          "created_at"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "approval",
    "binding",
    "decisions"
  ],
  "additionalProperties": false
}
```

## ApprovalPage

源指针：`#/components/schemas/ApprovalPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; items=ApprovalDetail | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/ApprovalDetail"
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## ApprovalRevoke

源指针：`#/components/schemas/ApprovalRevoke`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| expected_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "expected_version": {
      "type": "integer",
      "minimum": 1
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    }
  },
  "required": [
    "expected_version",
    "reason"
  ],
  "additionalProperties": false
}
```

## ReviewPage

源指针：`#/components/schemas/ReviewPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; items=Review | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Review"
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## ReviewContext

源指针：`#/components/schemas/ReviewContext`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| result_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| policy_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| snapshot_sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| object_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| review_version | 必须 | integer; minimum=0 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "policy_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "snapshot_sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "object_version": {
      "type": "integer",
      "minimum": 1
    },
    "review_version": {
      "type": "integer",
      "minimum": 0
    }
  },
  "required": [
    "task_id",
    "run_version",
    "result_version",
    "policy_version",
    "snapshot_sha256",
    "object_version",
    "review_version"
  ],
  "additionalProperties": false
}
```

## AuditExportStatus

源指针：`#/components/schemas/AuditExportStatus`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| export_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| state | 必须 | string; enum=["REQUESTED", "READY", "FAILED", "EXPIRED", "REVOKED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| artifact | 必须 | anyOf(ObjectRef; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| size_bytes | 必须 | anyOf(integer; minimum=0; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| error_code | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "export_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "REQUESTED",
        "READY",
        "FAILED",
        "EXPIRED",
        "REVOKED"
      ]
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "artifact": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ObjectRef"
        },
        {
          "type": "null"
        }
      ]
    },
    "size_bytes": {
      "anyOf": [
        {
          "type": "integer",
          "minimum": 0
        },
        {
          "type": "null"
        }
      ]
    },
    "expires_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "error_code": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "export_id",
    "case_id",
    "state",
    "version",
    "artifact",
    "size_bytes",
    "expires_at",
    "error_code"
  ],
  "additionalProperties": false
}
```

## ModelOperation

源指针：`#/components/schemas/ModelOperation`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| operation_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| org_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| release_bundle_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| mode | 必须 | string; enum=["shadow", "canary", "activate", "rollback"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| state | 必须 | string; enum=["REQUESTED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| progress | 必须 | number; minimum=0; maximum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| model_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| index_version | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| error_code | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "operation_id": {
      "type": "string",
      "format": "uuid"
    },
    "org_id": {
      "type": "string",
      "format": "uuid"
    },
    "release_bundle_id": {
      "type": "string",
      "format": "uuid"
    },
    "model_id": {
      "type": "string",
      "format": "uuid"
    },
    "mode": {
      "type": "string",
      "enum": [
        "shadow",
        "canary",
        "activate",
        "rollback"
      ]
    },
    "state": {
      "type": "string",
      "enum": [
        "REQUESTED",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "CANCELLED"
      ]
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "progress": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "model_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "index_version": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    },
    "error_code": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "operation_id",
    "org_id",
    "release_bundle_id",
    "model_id",
    "mode",
    "state",
    "version",
    "progress",
    "model_version",
    "index_version",
    "error_code"
  ],
  "additionalProperties": false
}
```

## SourceSyncRequest

源指针：`#/components/schemas/SourceSyncRequest`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| expected_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "expected_version": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "expected_version"
  ],
  "additionalProperties": false
}
```

## SourceAuthorizationUpdate

源指针：`#/components/schemas/SourceAuthorizationUpdate`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| source_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_ref | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| purpose | 必须 | array; minItems=1; uniqueItems=true; items=string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| authorization_status | 必须 | string; enum=["pending", "verified", "expired", "revoked"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| expires_at | 必须 | anyOf(string; format="date-time"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "source_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "authorization_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "authorization_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "purpose": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 128
      },
      "minItems": 1,
      "uniqueItems": true
    },
    "authorization_status": {
      "type": "string",
      "enum": [
        "pending",
        "verified",
        "expired",
        "revoked"
      ]
    },
    "expires_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "source_id",
    "case_id",
    "authorization_ref",
    "authorization_version",
    "purpose",
    "authorization_status",
    "expires_at"
  ],
  "additionalProperties": false
}
```

## PolicyDefinition

源指针：`#/components/schemas/PolicyDefinition`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| definition_ref | 必须 | string; minLength=1; maxLength=128; pattern="^urn:sha256:[a-f0-9]{64}$" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| version | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| sha256 | 必须 | string; pattern="^[a-f0-9]{64}$" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| values | 必须 | object; additionalProperties=true | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "definition_ref": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128,
      "pattern": "^urn:sha256:[a-f0-9]{64}$"
    },
    "version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "sha256": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "values": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "required": [
    "definition_ref",
    "version",
    "sha256",
    "values"
  ],
  "additionalProperties": false
}
```

## NodeRun

源指针：`#/components/schemas/NodeRun`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| node_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| node_code | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| attempt | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| state | 必须 | string; enum=["PENDING", "READY", "RUNNING", "SUCCEEDED", "FAILED", "SKIPPED", "DEFERRED", "CANCELLED", "NOT_SUPPORTED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| required | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | anyOf(string; minLength=1; maxLength=4096; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| fencing_epoch | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| started_at | 必须 | anyOf(string; format="date-time"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| ended_at | 必须 | anyOf(string; format="date-time"; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "node_id": {
      "type": "string",
      "format": "uuid"
    },
    "node_code": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "attempt": {
      "type": "integer",
      "minimum": 1
    },
    "state": {
      "type": "string",
      "enum": [
        "PENDING",
        "READY",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "SKIPPED",
        "DEFERRED",
        "CANCELLED",
        "NOT_SUPPORTED"
      ]
    },
    "required": {
      "type": "boolean"
    },
    "reason": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ]
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "fencing_epoch": {
      "type": "integer",
      "minimum": 1
    },
    "started_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    },
    "ended_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "node_id",
    "node_code",
    "attempt",
    "state",
    "required",
    "reason",
    "version",
    "fencing_epoch",
    "started_at",
    "ended_at"
  ],
  "additionalProperties": false
}
```

## NodePage

源指针：`#/components/schemas/NodePage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| items | 必须 | array; items=NodeRun | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/NodeRun"
      }
    }
  },
  "required": [
    "task_id",
    "run_version",
    "items"
  ],
  "additionalProperties": false
}
```

## TaskEventRecord

源指针：`#/components/schemas/TaskEventRecord`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| event_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| from_state | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| to_state | 必须 | string; minLength=1; maxLength=128 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| reason | 必须 | string; minLength=1; maxLength=4096 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| request_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| created_at | 必须 | string; format="date-time" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "from_state": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    },
    "to_state": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "reason": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4096
    },
    "request_id": {
      "type": "string",
      "format": "uuid"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "event_id",
    "task_id",
    "run_version",
    "from_state",
    "to_state",
    "reason",
    "request_id",
    "created_at"
  ],
  "additionalProperties": false
}
```

## TaskEventPage

源指针：`#/components/schemas/TaskEventPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; items=TaskEventRecord | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/TaskEventRecord"
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## PendingReviewItem

源指针：`#/components/schemas/PendingReviewItem`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| task_state | 必须 | enum=["WAIT_REVIEW", "REVIEWING", "RETURNED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| availability | 必须 | enum=["READY", "RESULT_UNAVAILABLE", "SOURCE_BLOCKED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| context | 必须 | anyOf(ReviewContext; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "task_state": {
      "enum": [
        "WAIT_REVIEW",
        "REVIEWING",
        "RETURNED"
      ]
    },
    "availability": {
      "enum": [
        "READY",
        "RESULT_UNAVAILABLE",
        "SOURCE_BLOCKED"
      ]
    },
    "context": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ReviewContext"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "task_id",
    "case_id",
    "task_state",
    "availability",
    "context"
  ],
  "additionalProperties": false
}
```

## PendingReviewPage

源指针：`#/components/schemas/PendingReviewPage`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| items | 必须 | array; items=PendingReviewItem | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| next_cursor | 必须 | anyOf(string; minLength=1; maxLength=128; null) | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/PendingReviewItem"
      }
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "required": [
    "items",
    "next_cursor"
  ],
  "additionalProperties": false
}
```

## TaskExecutionStatus

源指针：`#/components/schemas/TaskExecutionStatus`。

| 字段 | 是否必须出现 | 类型、可空及结构限制 | 说明 |
| --- | --- | --- | --- |
| task_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| case_id | 必须 | string; format="uuid" | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| state | 必须 | string; enum=["CREATED", "QUEUED", "RUNNING", "WAIT_REVIEW", "REVIEWING", "SUCCEEDED", "FAILED", "RETURNED", "CANCEL_REQUESTED", "CANCELLED", "ARCHIVED"] | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| run_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| result_version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| version | 必须 | integer; minimum=1 | 未在源Schema写独立说明；结合业务规则与字段映射评审 |
| result_available | 必须 | boolean | 未在源Schema写独立说明；结合业务规则与字段映射评审 |

是否必须出现与是否允许null是两件事。精确条件、组合与引用以完整源Schema为准；JSON Schema不替代权限、对象存在性、版本和跨字段业务校验。

完整源结构（派生副本）：

```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid"
    },
    "case_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "type": "string",
      "enum": [
        "CREATED",
        "QUEUED",
        "RUNNING",
        "WAIT_REVIEW",
        "REVIEWING",
        "SUCCEEDED",
        "FAILED",
        "RETURNED",
        "CANCEL_REQUESTED",
        "CANCELLED",
        "ARCHIVED"
      ]
    },
    "run_version": {
      "type": "integer",
      "minimum": 1
    },
    "result_version": {
      "type": "integer",
      "minimum": 1
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "result_available": {
      "type": "boolean"
    }
  },
  "required": [
    "task_id",
    "case_id",
    "state",
    "run_version",
    "result_version",
    "version",
    "result_available"
  ],
  "additionalProperties": false
}
```

