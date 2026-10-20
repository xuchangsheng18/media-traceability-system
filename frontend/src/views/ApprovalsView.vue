<script setup lang="ts">
import { ref, watch } from 'vue'
import { errorMessage, pageQuery, uuid, type Schemas } from '../business/api'
import { useBusinessSession } from '../business/session'
const session = useBusinessSession()
const caseId = ref(''),
  items = ref<Schemas['ApprovalDetail'][]>([]),
  cursor = ref<string | null>(null)
const selected = ref<Schemas['ApprovalDetail'] | null>(null),
  etag = ref<string | null>(null)
const message = ref('请连接业务身份并选择案件'),
  busy = ref(false),
  confirmed = ref(false)
const decision = ref<'approve' | 'reject' | 'return' | 'revoke'>('approve'),
  reason = ref('')
const objectId = ref(''),
  objectVersion = ref(1),
  runVersion = ref(1),
  resultVersion = ref(1),
  policyVersion = ref('')
const purpose = ref<Schemas['ApprovalCreate']['purpose']>('confirmation'),
  objectType = ref<Schemas['ApprovalCreate']['object_type']>('task')
let intent: { signature: string; key: string } | null = null
function keyFor(path: string, body: object) {
  const signature = JSON.stringify([path, body, etag.value])
  if (intent?.signature !== signature) intent = { signature, key: crypto.randomUUID() }
  return intent.key
}
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
function reset() {
  items.value = []
  cursor.value = null
  selected.value = null
  etag.value = null
  intent = null
  confirmed.value = false
}
watch(caseId, reset)
async function list(next = false) {
  await action(async () => {
    const { data } = await session.call<Schemas['ApprovalPage']>(
      `/approvals?${pageQuery(caseId.value, 20, next ? cursor.value : null)}`,
    )
    items.value = data.items
    cursor.value = data.next_cursor
    selected.value = null
    etag.value = null
    message.value = `当前页 ${data.items.length} 条审批记录`
  })
}
async function detail(id: string) {
  await action(async () => {
    const response = await session.call<Schemas['ApprovalDetail']>(`/approvals/${uuid(id)}`)
    selected.value = response.data
    etag.value = response.etag
    intent = null
    message.value = '已读取当前审批版本'
  })
}
async function create() {
  if (!confirmed.value || !reason.value.trim() || !policyVersion.value.trim()) return
  await action(async () => {
    const body: Schemas['ApprovalCreate'] = {
      case_id: objectType.value === 'model_release' ? null : uuid(caseId.value),
      object_type: objectType.value,
      object_id: uuid(objectId.value),
      object_version: objectVersion.value,
      purpose: objectType.value === 'model_release' ? 'model_release' : purpose.value,
      policy_version: policyVersion.value,
      reason: reason.value,
      run_version: objectType.value === 'task' ? runVersion.value : null,
      result_version: objectType.value === 'task' ? resultVersion.value : null,
    }
    const response = await session.call<Schemas['Approval']>(
      '/approvals',
      body,
      keyFor('/approvals', body),
    )
    intent = null
    selected.value = null
    etag.value = null
    message.value = `申请已登记：${response.data.approval_id}，状态 ${response.data.state}。申请不代表批准。`
  })
}
async function decide() {
  const current = selected.value
  if (!current || !etag.value || !confirmed.value || !reason.value.trim()) return
  await action(async () => {
    const version = current.approval.version
    const path = `/approvals/${uuid(current.approval.approval_id)}/${decision.value === 'revoke' ? 'revoke' : 'decisions'}`
    const body =
      decision.value === 'revoke'
        ? { expected_version: version, reason: reason.value }
        : {
            expected_version: version,
            decision: decision.value,
            reason: reason.value,
            evidence_ids: [],
          }
    const { data } = await session.call<Schemas['Approval']>(
      path,
      body,
      keyFor(path, body),
      etag.value!,
    )
    intent = null
    selected.value = null
    etag.value = null
    message.value = `服务端已记录结果：${data.state}，版本 ${data.version}。请重新读取详情。`
  })
}
</script>
<template>
  <section>
    <h2>审批与二次确认</h2>
    <p>
      二次确认用于防误操作；业务审批、独立人员及版本条件由服务端核验。一个人的多个账号不代表多名批准人。
    </p>
    <label
      >案件编号<input
        v-model="caseId"
        :disabled="busy"
        list="approval-cases"
        aria-label="审批案件编号"
    /></label>
    <datalist id="approval-cases">
      <option
        v-for="id in session.state.user?.case_ids"
        :key="id"
        :value="id"
      />
    </datalist>
    <button
      :disabled="busy || !session.has('approval.read')"
      @click="list()"
    >
      查询审批
    </button>
    <button
      :disabled="busy || !cursor"
      class="secondary"
      @click="list(true)"
    >
      下一页
    </button>
    <ul>
      <li
        v-for="item in items"
        :key="item.approval.approval_id"
      >
        <button
          class="secondary"
          :disabled="busy"
          @click="detail(item.approval.approval_id)"
        >
          {{ item.approval.approval_id }} · {{ item.approval.state }}
        </button>
      </li>
    </ul>
    <dl v-if="selected">
      <dt>审批编号</dt>
      <dd>{{ selected.approval.approval_id }}</dd>
      <dt>当前状态／版本</dt>
      <dd>{{ selected.approval.state }} / {{ selected.approval.version }}</dd>
      <dt>用途</dt>
      <dd>{{ selected.approval.purpose }}</dd>
      <dt>案件</dt>
      <dd>{{ selected.binding.case_id }}</dd>
      <dt>实际审批对象／版本</dt>
      <dd>
        {{ selected.binding.object_type }} · {{ selected.binding.object_id }} /
        {{ selected.approval.object_version }}
      </dd>
      <dt>申请人</dt>
      <dd>{{ selected.binding.requested_by }}</dd>
      <dt>规则版本</dt>
      <dd>{{ selected.approval.policy_version }}</dd>
      <dt>运行／结果版本</dt>
      <dd>
        {{ selected.approval.run_version ?? '不适用' }} /
        {{ selected.approval.result_version ?? '不适用' }}
      </dd>
      <dt>有效期</dt>
      <dd>{{ selected.approval.expires_at || '未签发' }}</dd>
    </dl>
    <ul v-if="selected">
      <li
        v-for="record in selected.decisions"
        :key="record.decision_id"
      >
        {{ record.created_at }} · {{ record.actor_id }} · {{ record.decision }}：{{ record.reason }}
      </li>
    </ul>
  </section>
  <section>
    <h3>登记申请</h3>
    <label
      >对象类别<select v-model="objectType">
        <option value="task">任务</option>
        <option value="report">报告</option>
        <option value="evidence_package">证据包</option>
        <option value="feedback">反馈</option>
        <option value="operation">操作</option>
        <option value="model_release">组织级模型发布</option>
      </select></label
    >
    <label>对象编号<input v-model="objectId" /></label
    ><label
      >对象版本<input
        v-model.number="objectVersion"
        type="number"
        min="1"
        step="1"
    /></label>
    <label
      >用途<select v-model="purpose">
        <option value="confirmation">防误操作确认</option>
        <option value="review">复核</option>
        <option value="seal">封存</option>
        <option value="report_export">导出</option>
        <option value="training_feedback">训练回流</option>
        <option value="model_release">模型发布</option>
      </select></label
    >
    <label>生效规则版本<input v-model="policyVersion" /></label>
    <template v-if="objectType === 'task'"
      ><label
        >运行版本<input
          v-model.number="runVersion"
          type="number"
          min="1" /></label
      ><label
        >结果版本<input
          v-model.number="resultVersion"
          type="number"
          min="1" /></label
    ></template>
    <label
      >申请／决定／撤销的理由<textarea
        v-model="reason"
        maxlength="4096"
      />
    </label>
    <label class="check"
      ><input
        v-model="confirmed"
        type="checkbox"
      />我已核对本次对象、版本、用途和理由；此确认不代替审批。</label
    >
    <button
      :disabled="busy || !confirmed || !session.has('approval.request')"
      @click="create"
    >
      提交申请
    </button>
    <template v-if="selected"
      ><label
        >审批动作<select v-model="decision">
          <option value="approve">同意</option>
          <option value="reject">拒绝</option>
          <option value="return">退回补充</option>
          <option value="revoke">撤销</option>
        </select></label
      ><button
        :disabled="
          busy ||
          !confirmed ||
          !etag ||
          !session.has(decision === 'revoke' ? 'approval.revoke' : 'approval.decide')
        "
        @click="decide"
      >
        按当前版本提交决定
      </button></template
    >
    <p role="status">{{ message }}</p>
  </section>
</template>
