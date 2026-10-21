<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { errorMessage, FormError, pageQuery, saveBlob, uuid, type Schemas } from '../business/api'
import { useBusinessSession } from '../business/session'
const session = useBusinessSession()
const caseId = ref(''),
  events = ref<Schemas['AuditEvent'][]>([]),
  cursor = ref<string | null>(null)
const message = ref('请连接业务身份并选择案件'),
  busy = ref(false),
  detail = ref<Schemas['AuditEvent'] | null>(null)
const actorFilter = ref(''),
  objectFilter = ref(''),
  from = ref(''),
  to = ref('')
const start = ref(''),
  end = ref(''),
  purpose = ref(''),
  approvalId = ref(''),
  exportId = ref('')
const exportStatus = ref<Schemas['AuditExportStatus'] | null>(null),
  confirmed = ref(false)
const loaded = ref(false)
let intent: { signature: string; key: string } | null = null
const visible = computed(() =>
  events.value.filter(
    (event) =>
      (!actorFilter.value || event.actor_id === actorFilter.value) &&
      (!objectFilter.value || event.object_id === objectFilter.value) &&
      (!from.value || Date.parse(event.occurred_at) >= Date.parse(from.value)) &&
      (!to.value || Date.parse(event.occurred_at) <= Date.parse(to.value)),
  ),
)
watch(caseId, () => {
  events.value = []
  loaded.value = false
  cursor.value = null
  detail.value = null
  exportStatus.value = null
  exportId.value = ''
  intent = null
})
async function action(work: () => Promise<void>) {
  if (busy.value) return
  busy.value = true
  try {
    await work()
  } catch (error) {
    message.value = errorMessage(error)
  } finally {
    busy.value = false
    confirmed.value = false
  }
}
async function list(next = false) {
  const following = next ? cursor.value : null
  events.value = []
  detail.value = null
  cursor.value = null
  loaded.value = false
  await action(async () => {
    const { data } = await session.call<Schemas['AuditEventPage']>(
      `/audit/events?${pageQuery(caseId.value, 20, following)}`,
    )
    events.value = data.items
    cursor.value = data.next_cursor
    detail.value = null
    loaded.value = true
    message.value = `服务端当前页 ${events.value.length} 条；筛选只影响当前页，下一页需继续查询。`
  })
}
async function requestExport() {
  if (!confirmed.value) return
  await action(async () => {
    const startAt = new Date(start.value),
      endAt = new Date(end.value)
    if (
      !Number.isFinite(startAt.getTime()) ||
      !Number.isFinite(endAt.getTime()) ||
      startAt >= endAt ||
      !purpose.value.trim()
    )
      throw new FormError('请填写有效的开始、结束时间和用途；结束时间须晚于开始时间。')
    const body: Schemas['AuditExport'] = {
      case_id: uuid(caseId.value),
      approval_id: uuid(approvalId.value),
      start_at: startAt.toISOString(),
      end_at: endAt.toISOString(),
      purpose: purpose.value,
    }
    const signature = JSON.stringify(body)
    if (intent?.signature !== signature) intent = { signature, key: crypto.randomUUID() }
    const { data } = await session.call<Schemas['ActionAck']>('/audit/exports', body, intent.key)
    exportStatus.value = null
    exportId.value = data.object_id
    intent = null
    message.value = `导出申请已登记：${data.state}；仅READY且权限仍有效时允许下载。`
  })
}
async function checkExport() {
  await action(async () => {
    const { data } = await session.call<Schemas['AuditExportStatus']>(
      `/audit/exports/${uuid(exportId.value)}`,
    )
    exportStatus.value = data
    message.value = `导出状态：${data.state}`
  })
}
async function download() {
  await action(async () => {
    const identifier = uuid(exportId.value)
    const { data: current } = await session.call<Schemas['AuditExportStatus']>(
      `/audit/exports/${identifier}`,
    )
    exportStatus.value = current
    if (current.state !== 'READY') {
      message.value = '导出尚不可下载，请核对状态。'
      return
    }
    const { data } = await session.call<Blob>(
      `/audit/exports/${identifier}/content`,
      undefined,
      undefined,
      undefined,
      true,
    )
    saveBlob(data, `audit-${identifier}.json`)
    message.value = '已通过受控接口取得下载内容；后续访问仍须重新授权。'
  })
}
</script>
<template>
  <div class="view-grid">
    <section class="panel span-7">
      <h2 class="panel-heading">审计查询</h2>
      <div class="toolbar">
        <label
          >案件编号<input
            v-model="caseId"
            :disabled="busy"
            list="audit-cases"
            aria-label="审计案件编号"
        /></label>
        <datalist id="audit-cases">
          <option
            v-for="id in session.state.user?.case_ids"
            :key="id"
            :value="id"
          />
        </datalist>
        <button
          :disabled="busy || !session.has('audit.read')"
          @click="list()"
        >
          查询审计</button
        ><button
          class="secondary"
          :disabled="busy || !cursor"
          @click="list(true)"
        >
          下一页
        </button>
      </div>
      <details>
        <summary>筛选当前页</summary>
        <p class="panel-copy">
          当前接口按案件分页；下列条件只筛选已返回的当前页，不代表全部记录筛选结果。
        </p>
        <div class="form-grid">
          <label>用户编号<input v-model="actorFilter" /></label
          ><label>对象编号<input v-model="objectFilter" /></label
          ><label
            >开始时间<input
              v-model="from"
              type="datetime-local" /></label
          ><label
            >结束时间<input
              v-model="to"
              type="datetime-local"
          /></label>
        </div>
      </details>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>动作</th>
              <th>结果</th>
              <th>对象</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="event in visible"
              :key="event.event_id"
            >
              <td>{{ event.occurred_at }}</td>
              <td>{{ event.action }}</td>
              <td>{{ event.outcome }}</td>
              <td>{{ event.object_type }}</td>
              <td>
                <button
                  class="secondary"
                  @click="detail = event"
                >
                  查看
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p
        v-if="loaded && !visible.length"
        class="muted empty-state"
      >
        当前页无匹配记录；未授权和查询失败不会显示为成功的空结果。
      </p>
      <dl v-if="detail">
        <dt>事件编号</dt>
        <dd>{{ detail.event_id }}</dd>
        <dt>操作者</dt>
        <dd>{{ detail.actor_id }}</dd>
        <dt>对象编号／版本</dt>
        <dd>{{ detail.object_id || '无' }} / {{ detail.object_version ?? '无' }}</dd>
        <dt>请求编号</dt>
        <dd>{{ detail.request_id }}</dd>
      </dl>
    </section>
    <section class="panel span-5">
      <h3 class="panel-heading">受控审计导出</h3>
      <p class="panel-copy">
        须有对应批准记录。此处的人工勾选只防误操作；服务端继续核验审批、案件、时间窗、大小和有效期。
      </p>
      <div class="form-grid">
        <label class="field-full">批准编号<input v-model="approvalId" /></label
        ><label
          >开始时间<input
            v-model="start"
            type="datetime-local" /></label
        ><label
          >结束时间<input
            v-model="end"
            type="datetime-local" /></label
        ><label class="field-full"
          >用途<input
            v-model="purpose"
            maxlength="128"
        /></label>
        <label class="check field-full"
          ><input
            v-model="confirmed"
            type="checkbox"
          />已核对案件、批准编号、时间和用途。</label
        >
        <div class="form-actions">
          <button
            :disabled="busy || !confirmed || !session.has('audit.export')"
            @click="requestExport"
          >
            申请导出
          </button>
        </div>
        <label class="field-full">导出编号<input v-model="exportId" /></label>
        <div class="form-actions">
          <button
            class="secondary"
            :disabled="busy || !session.has('audit.export')"
            @click="checkExport"
          >
            读取导出状态</button
          ><button
            :disabled="busy || exportStatus?.state !== 'READY' || !session.has('audit.export')"
            @click="download"
          >
            受控下载
          </button>
        </div>
      </div>
      <p v-if="exportStatus">
        状态：{{ exportStatus.state }}；有效期：{{ exportStatus.expires_at || '尚未生成' }}
      </p>
      <p
        class="notice"
        role="status"
      >
        {{ message }}
      </p>
    </section>
  </div>
</template>
