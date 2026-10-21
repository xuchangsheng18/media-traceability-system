<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import CaseScopeSelect from '../components/CaseScopeSelect.vue'
import type { Schemas } from '../business/api'
import { useBusinessSession } from '../business/session'
import { createSources } from '../business/sources'
import { createBusinessUploadController } from '../business/uploads'

const session = useBusinessSession()
const caseId = ref('')
const sourceId = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
// A visible browser resource cap, not the server's approved business quota.
const budgetMiB = ref(8)
const autoRefresh = ref(true)
const sources = createSources(
  session,
  () => caseId.value,
  () => ({
    case_id: caseId.value,
    name: '',
    source_type: 'synthetic',
    authorization_ref: '',
    purpose: [],
    expires_at: null,
  }),
)
const source = computed(
  () => sources.list.state.data?.items.find((item) => item.source_id === sourceId.value) ?? null,
)
const selection = () => ({ caseId: caseId.value, source: source.value })
const controller = shallowRef(
  createBusinessUploadController(session, selection, budgetMiB.value * 1024 * 1024),
)
const state = computed(() => controller.value.state)
const locked = computed(() => state.value.busy || state.value.uncertain)
const uploadAllowed = computed(() => !!session.state.user && session.has('asset.upload'))
function available(item: Schemas['Source'] | null) {
  return (
    !!item &&
    item.case_id === caseId.value &&
    item.authorization_status === 'verified' &&
    item.purpose.includes('upload') &&
    (item.expires_at === null ||
      (Number.isFinite(Date.parse(item.expires_at)) && Date.parse(item.expires_at) > Date.now()))
  )
}
const canChoose = computed(
  () => uploadAllowed.value && available(source.value) && !locked.value && !state.value.session,
)
const writable = computed(
  () =>
    uploadAllowed.value &&
    !locked.value &&
    state.value.session?.state === 'UPLOADING' &&
    !state.value.completionReceipt,
)
const count = computed(() =>
  state.value.session ? Math.ceil(state.value.sizeBytes / state.value.session.part_size_bytes) : 0,
)
const confirmedBytes = computed(() =>
  state.value.parts.reduce((total, part) => total + part.size_bytes, 0),
)
const notice = computed(() => {
  if (!session.state.user) return '请先在业务身份页连接身份。'
  if (!uploadAllowed.value) return '当前身份没有业务上传权限。'
  return (
    state.value.error ||
    sources.list.state.error ||
    state.value.message ||
    '请选择已有案件、有效来源和PNG/JPEG文件。'
  )
})
function clearFileInput() {
  if (fileInput.value) fileInput.value.value = ''
}
watch(
  () => [
    caseId.value,
    session.state.generation,
    session.state.user?.user_id,
    session.state.user?.org_id,
  ],
  () => {
    sourceId.value = ''
    clearFileInput()
  },
  { flush: 'sync' },
)
watch(
  () => [source.value, session.has('asset.upload'), session.state.user?.case_ids],
  clearFileInput,
  { flush: 'sync', deep: true },
)
watch(
  budgetMiB,
  () => {
    controller.value.dispose()
    controller.value = createBusinessUploadController(
      session,
      selection,
      budgetMiB.value * 1024 * 1024,
    )
    clearFileInput()
  },
  { flush: 'sync' },
)
async function loadSources(next = false) {
  sourceId.value = ''
  if (next) await sources.list.next()
  else await sources.list.load(20)
}
async function choose(event: Event) {
  await controller.value.choose((event.target as HTMLInputElement).files?.[0] ?? null)
  if (!state.value.digest) clearFileInput()
}
function startAnother() {
  controller.value.reset()
  clearFileInput()
}
let timer: ReturnType<typeof setTimeout> | undefined
let polls = 0
watch(
  () => [
    autoRefresh.value,
    state.value.busy,
    state.value.error,
    state.value.completionReceipt,
    state.value.status,
    session.state.generation,
  ],
  () => {
    clearTimeout(timer)
    const validating =
      state.value.status?.session.state === 'VALIDATING' ||
      (!!state.value.completionReceipt && !state.value.status)
    if (
      autoRefresh.value &&
      validating &&
      !state.value.busy &&
      !state.value.uncertain &&
      !state.value.error &&
      polls < 30
    ) {
      timer = setTimeout(() => {
        polls++
        void controller.value.refresh()
      }, 2000)
    }
  },
  { flush: 'post' },
)
onBeforeUnmount(() => {
  clearTimeout(timer)
  controller.value.dispose()
  sources.dispose()
})
</script>

<template>
  <div class="view-grid">
    <section class="panel span-12">
      <h2 class="panel-heading">业务文件接入</h2>
      <p class="panel-copy">
        选择已有案件与有效来源，将PNG/JPEG分片上传。业务身份和授权由服务端逐次核验；校验完成前不会登记为可用资产。
      </p>
      <div class="toolbar">
        <CaseScopeSelect
          v-model="caseId"
          :case-ids="session.state.user?.case_ids ?? []"
          :disabled="!session.state.user || locked"
        />
        <button
          :disabled="!caseId || !session.has('source.read') || locked || sources.list.state.busy"
          @click="loadSources()"
        >
          查询上传来源
        </button>
        <button
          class="secondary"
          :disabled="
            locked ||
            sources.list.state.busy ||
            !sources.list.state.data?.next_cursor ||
            !session.has('source.read')
          "
          @click="loadSources(true)"
        >
          下一页上传来源
        </button>
        <label
          >上传来源
          <select
            v-model="sourceId"
            aria-label="上传来源"
            :disabled="locked || !caseId || !session.has('source.read')"
          >
            <option value="">请选择已核验来源</option>
            <option
              v-for="item in sources.list.state.data?.items ?? []"
              :key="item.source_id"
              :value="item.source_id"
              :disabled="!available(item)"
            >
              {{ item.name }}（{{ item.authorization_status }}）
            </option>
          </select>
        </label>
      </div>
      <div class="toolbar">
        <label
          >浏览器摘要内存预算（MiB）
          <input
            v-model.number="budgetMiB"
            aria-label="浏览器摘要内存预算（MiB）"
            type="number"
            min="1"
            step="1"
            :disabled="locked || !!state.session"
          />
        </label>
        <label
          >业务上传文件
          <input
            ref="fileInput"
            aria-label="业务上传文件"
            type="file"
            accept="image/png,image/jpeg"
            :disabled="!canChoose"
            @change="choose"
          />
        </label>
      </div>
      <p class="panel-copy">
        本页只支持预算内的PNG/JPEG，每会话最多10,000片；服务端仍执行自己的大小、授权和媒体安全校验。恢复仅适用于本页保留的文件绑定，刷新或离开页面后不能凭会话编号重建绑定。
      </p>
      <p
        class="notice"
        role="status"
      >
        {{ notice
        }}<span v-if="state.completionReceipt">
          完成请求原回执：{{ state.completionReceipt.validation }}。</span
        ><span v-if="state.uncertain"> 结果尚未确认，其他变更已锁定；请重试原请求。</span>
      </p>
      <dl
        v-if="state.digest"
        class="metadata-grid"
      >
        <dt>文件</dt>
        <dd>{{ state.filename }}（{{ state.sizeBytes }}字节）</dd>
        <dt>文件SHA-256</dt>
        <dd>{{ state.digest }}</dd>
        <dt v-if="state.session">上传会话</dt>
        <dd v-if="state.session">{{ state.session.upload_id }}</dd>
        <dt v-if="state.session">上次会话状态／版本</dt>
        <dd v-if="state.session">{{ state.session.state }}／{{ state.session.version }}</dd>
        <dt>已核对分片／字节</dt>
        <dd>{{ state.parts.length }} / {{ count }}片；{{ confirmedBytes }}字节</dd>
      </dl>
      <div class="toolbar">
        <button
          :disabled="
            !uploadAllowed || !state.digest || !!state.session || locked || !available(source)
          "
          @click="controller.create()"
        >
          初始化业务上传
        </button>
        <button
          :disabled="!writable || state.parts.length >= count"
          @click="controller.sendRemaining()"
        >
          发送剩余分片
        </button>
        <button
          class="secondary"
          :disabled="!uploadAllowed || !state.session || locked"
          @click="controller.reconcile()"
        >
          核对服务端分片
        </button>
        <button
          :disabled="!writable || !count || state.parts.length !== count"
          @click="controller.complete()"
        >
          完成上传并校验
        </button>
        <button
          class="secondary"
          :disabled="!uploadAllowed || !state.session || locked"
          @click="controller.refresh()"
        >
          刷新校验进度
        </button>
        <button
          :disabled="!uploadAllowed || !state.uncertain || state.busy"
          @click="controller.retry()"
        >
          重试原请求
        </button>
        <button
          class="secondary"
          :disabled="locked"
          @click="startAnother()"
        >
          开始另一文件
        </button>
      </div>
      <label
        ><input
          v-model="autoRefresh"
          type="checkbox"
        />
        自动刷新受理后的进度（最多30次，可停止并手动查询）</label
      >
      <p
        v-if="state.assetId"
        class="panel-copy"
      >
        校验通过的资产：{{ state.assetId }}。<RouterLink
          :to="{ path: '/assets', query: { case_id: caseId, asset_id: state.assetId } }"
          >前往资产管理核对并读取</RouterLink
        >
      </p>
      <p
        v-if="state.status?.session.state === 'REJECTED'"
        class="panel-copy"
      >
        服务端已拒绝该文件，请检查实际校验结果；不会显示为有效资产。
      </p>
    </section>
  </div>
</template>
