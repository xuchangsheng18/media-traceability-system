<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import type { Schemas } from '../business/api'
import { useBusinessSession } from '../business/session'
import { createSources } from '../business/sources'

const session = useBusinessSession()
const caseId = ref('')
const limit = ref(20)
const fields = reactive({
  name: '',
  sourceType: '',
  authorizationRef: '',
  purpose: '',
  expiresAt: '',
})
const draft = computed<Schemas['SourceCreate']>(() => ({
  case_id: caseId.value,
  name: fields.name,
  source_type: fields.sourceType as Schemas['SourceCreate']['source_type'],
  authorization_ref: fields.authorizationRef,
  purpose: fields.purpose === '' ? [] : fields.purpose.split(/\r?\n/),
  expires_at: fields.expiresAt === '' ? null : fields.expiresAt,
}))
const sources = createSources(
  session,
  () => caseId.value,
  () => draft.value,
)
const registration = sources.registration.state
const authorizationSync = sources.authorizationSync.state
const locked = computed(() => registration.busy || registration.uncertain)
const syncLocked = computed(() => authorizationSync.busy || authorizationSync.uncertain)
const types = [
  { value: 'authorized_business', label: '已获授权的业务来源' },
  { value: 'public_licensed', label: '公开且已获许可的来源' },
  { value: 'user_submission', label: '用户提交' },
  { value: 'synthetic', label: '合成数据' },
]
const listStatus = computed(() => {
  if (!session.state.user) return '请先在业务身份页连接身份。'
  if (!session.has('source.read')) return '当前身份没有来源读取权限。'
  if (sources.list.state.busy) return '正在读取案件内来源…'
  if (sources.list.state.error) return `${sources.list.state.error} 分页失败后请重新查询首页。`
  if (sources.list.state.loaded)
    return `来源第 ${sources.list.state.pageNumber} 页，返回 ${sources.list.state.data?.items.length ?? 0} 条。`
  return '请选择有权访问的案件并查询；候选案件编号不能替代服务端授权。'
})

watch(limit, sources.list.clear, { flush: 'sync' })
watch(
  () => [
    caseId.value,
    session.state.generation,
    session.state.user?.user_id,
    session.state.user?.org_id,
    session.has('source.manage'),
  ],
  () =>
    Object.assign(fields, {
      name: '',
      sourceType: '',
      authorizationRef: '',
      purpose: '',
      expiresAt: '',
    }),
  { flush: 'sync' },
)
onBeforeUnmount(sources.dispose)
async function list(next = false) {
  if (syncLocked.value) return
  sources.detail.clear()
  if (next) await sources.list.next()
  else await sources.list.load(limit.value)
}
</script>

<template>
  <div class="view-grid">
    <section class="panel span-12">
      <h2 class="panel-heading">案件来源管理</h2>
      <p class="panel-copy">
        读取案件内可见来源，或提交来源登记。授权状态、版本和单位由服务端确定；登记成功仍须满足后续操作的用途与有效期核验。
      </p>
      <div class="toolbar">
        <label>
          来源案件编号
          <input
            v-model="caseId"
            aria-label="来源案件编号"
            list="source-case-options"
            placeholder="完整案件 UUID"
          />
        </label>
        <datalist id="source-case-options">
          <option
            v-for="id in session.state.user?.case_ids ?? []"
            :key="id"
            :value="id"
          />
        </datalist>
        <label>
          每页条数
          <select
            v-model="limit"
            aria-label="来源每页条数"
            :disabled="syncLocked"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </label>
        <button
          :disabled="sources.list.state.busy || syncLocked || !session.has('source.read')"
          @click="list()"
        >
          查询来源／回到首页
        </button>
        <button
          class="secondary"
          :disabled="
            sources.list.state.busy ||
            syncLocked ||
            !sources.list.state.data?.next_cursor ||
            !session.has('source.read')
          "
          @click="list(true)"
        >
          下一页来源
        </button>
      </div>
      <p
        class="notice"
        role="status"
      >
        {{ listStatus }}
      </p>
      <div
        v-if="sources.list.state.data?.items.length"
        class="table-scroll"
      >
        <table>
          <thead>
            <tr>
              <th>名称／来源编号</th>
              <th>来源类型</th>
              <th>授权状态／版本</th>
              <th>用途</th>
              <th>有效期</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in sources.list.state.data.items"
              :key="item.source_id"
            >
              <td>{{ item.name }}<br />{{ item.source_id }}</td>
              <td>{{ item.source_type }}</td>
              <td>{{ item.authorization_status }}／{{ item.version }}</td>
              <td>{{ item.purpose.join('、') }}</td>
              <td>{{ item.expires_at ?? '未提供到期时间（不表示永久授权）' }}</td>
              <td>
                <button
                  class="secondary"
                  :disabled="sources.detail.state.busy || syncLocked || !session.has('source.read')"
                  @click="sources.detail.load(item.source_id)"
                >
                  查看来源详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p
        v-if="sources.list.state.loaded && !sources.list.state.data?.items.length"
        class="empty-state"
      >
        当前页没有可见来源记录；这不表示案件内没有其他来源。
      </p>
      <p class="panel-copy">
        pending 尚不能作为有效用途授权；expired、revoked 均不能作为当前有效授权。
      </p>
    </section>

    <section class="panel span-12">
      <h2 class="panel-heading">来源详情</h2>
      <p class="panel-copy">
        授权同步只向服务端请求读取来源权威记录，不构成人工业务批准。授权状态、依据、用途和有效期均由真实权威决定；依赖缺失时服务端拒绝。
      </p>
      <div class="toolbar">
        <button
          :disabled="
            !sources.detail.state.data ||
            !sources.detail.state.etag ||
            sources.detail.state.busy ||
            syncLocked ||
            !session.has('source.read') ||
            !session.has('source.manage')
          "
          @click="sources.authorizationSync.submit()"
        >
          同步来源授权
        </button>
        <button
          class="secondary"
          :disabled="
            !sources.detail.state.sourceId ||
            sources.detail.state.busy ||
            authorizationSync.busy ||
            !session.has('source.read')
          "
          @click="sources.detail.load(sources.detail.state.sourceId)"
        >
          重新读取来源详情
        </button>
      </div>
      <p
        v-if="sources.detail.state.data && !sources.detail.state.etag"
        class="notice"
        role="status"
      >
        当前详情缺少服务端强 ETag，授权同步不可用；请重新读取详情。
      </p>
      <p
        v-if="authorizationSync.busy"
        class="notice"
        role="status"
      >
        正在请求来源授权同步…
      </p>
      <p
        v-if="authorizationSync.error"
        class="notice"
        role="status"
      >
        {{ authorizationSync.error }}
      </p>
      <p
        v-if="authorizationSync.uncertain"
        class="notice"
        role="status"
      >
        原授权同步结果尚未确认，请使用原请求重试。重新读取详情不会改变原版本、幂等键或
        ETag。原请求仅保存在本页内存；切换身份、案件或离开本页会清除它。
      </p>
      <button
        v-if="authorizationSync.uncertain"
        class="secondary"
        :disabled="
          authorizationSync.busy || !session.has('source.manage') || !session.has('source.read')
        "
        @click="sources.authorizationSync.retry()"
      >
        重试原授权同步请求
      </button>
      <p
        v-if="authorizationSync.message"
        class="notice"
        role="status"
      >
        {{ authorizationSync.message }}
      </p>
      <dl
        v-if="authorizationSync.data"
        class="source-detail"
      >
        <dt>同步回执来源编号</dt>
        <dd>{{ authorizationSync.data.source_id }}</dd>
        <dt>同步回执状态／版本</dt>
        <dd>
          {{ authorizationSync.data.authorization_status }}／{{ authorizationSync.data.version }}
        </dd>
      </dl>
      <p
        v-if="sources.detail.state.busy"
        class="notice"
        role="status"
      >
        正在读取来源详情…
      </p>
      <p
        v-else-if="sources.detail.state.error"
        class="notice"
        role="status"
      >
        {{ sources.detail.state.error }}
      </p>
      <dl
        v-else-if="sources.detail.state.data"
        class="source-detail"
      >
        <dt>来源名称</dt>
        <dd>{{ sources.detail.state.data.name }}</dd>
        <dt>来源编号</dt>
        <dd>{{ sources.detail.state.data.source_id }}</dd>
        <dt>案件编号</dt>
        <dd>{{ sources.detail.state.data.case_id }}</dd>
        <dt>来源类型</dt>
        <dd>{{ sources.detail.state.data.source_type }}</dd>
        <dt>授权依据</dt>
        <dd>{{ sources.detail.state.data.authorization_ref }}</dd>
        <dt>用途</dt>
        <dd>{{ sources.detail.state.data.purpose.join('、') }}</dd>
        <dt>有效期</dt>
        <dd>{{ sources.detail.state.data.expires_at ?? '未提供到期时间（不表示永久授权）' }}</dd>
        <dt>授权状态</dt>
        <dd>{{ sources.detail.state.data.authorization_status }}</dd>
        <dt>记录版本</dt>
        <dd>{{ sources.detail.state.data.version }}</dd>
      </dl>
      <p
        v-else
        class="empty-state"
      >
        {{
          sources.detail.state.sourceId
            ? '当前详情已清空，请点击“重新读取来源详情”查看当前状态。'
            : '查询来源后，点击“查看来源详情”读取所选来源。'
        }}
      </p>
    </section>

    <section class="panel span-12">
      <h2 class="panel-heading">登记来源</h2>
      <p class="panel-copy">
        按当前案件填写真实登记依据；真实权威或权限条件缺失时服务端将拒绝登记。登记后可在来源详情请求权威同步；来源修改与到期后台告警另待实现。
      </p>
      <p
        v-if="!session.has('source.manage')"
        class="notice"
        role="status"
      >
        当前身份没有来源登记权限。
      </p>
      <form
        class="source-form"
        @submit.prevent="sources.registration.submit()"
      >
        <fieldset :disabled="locked || !session.has('source.manage')">
          <legend>当前案件：{{ caseId || '尚未选择' }}</legend>
          <label
            >来源名称<input
              v-model="fields.name"
              aria-label="来源名称"
              required
          /></label>
          <label
            >来源类型<select
              v-model="fields.sourceType"
              aria-label="来源类型"
              required
            >
              <option
                disabled
                value=""
              >
                请选择实际来源类型
              </option>
              <option
                v-for="item in types"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select></label
          >
          <label
            >授权依据<input
              v-model="fields.authorizationRef"
              aria-label="授权依据"
              required
          /></label>
          <label
            >用途（每行一项）<textarea
              v-model="fields.purpose"
              aria-label="用途（每行一项）"
              required
              rows="3"
            />
          </label>
          <p class="panel-copy">
            填写来源依据所覆盖的用途，不重复、不留空行；页面不代替服务端用途规则。
          </p>
          <label
            >来源有效期<input
              v-model="fields.expiresAt"
              aria-label="来源有效期"
              placeholder="RFC3339，例如 2026-11-21T08:00:00+08:00；可留空"
          /></label>
          <p class="panel-copy">
            可留空，发送 null；这不表示永久授权。填写时须为带时区的 RFC3339
            时间，原始小数精度将保留。当前权威精度限制可能拒绝非零的微秒以下时间。
          </p>
          <button
            type="submit"
            :disabled="!!registration.data"
          >
            登记来源
          </button>
        </fieldset>
      </form>
      <p
        v-if="registration.busy"
        class="notice"
        role="status"
      >
        正在提交来源登记，请等待服务端结果…
      </p>
      <p
        v-if="registration.error"
        class="notice"
        role="status"
      >
        {{ registration.error }}
      </p>
      <p
        v-if="registration.uncertain"
        class="notice"
        role="status"
      >
        原登记结果尚未确认，输入暂时保留。请使用原请求重试，避免重复登记。幂等键仅保存在当前页面内存，离开页面后将丢失。
      </p>
      <button
        v-if="registration.uncertain"
        class="secondary"
        :disabled="registration.busy || !session.has('source.manage')"
        @click="sources.registration.retry()"
      >
        重试原登记请求
      </button>
      <p
        v-if="registration.message"
        class="notice"
        role="status"
      >
        {{ registration.message }}
      </p>
      <p
        v-if="registration.data"
        class="panel-copy"
      >
        相同输入已确认登记。编辑字段后才能提交另一条登记；列表与详情须主动重新查询。
      </p>
      <dl
        v-if="registration.data"
        class="source-detail"
      >
        <dt>已登记来源编号</dt>
        <dd>{{ registration.data.source_id }}</dd>
        <dt>来源名称</dt>
        <dd>{{ registration.data.name }}</dd>
        <dt>授权状态／版本</dt>
        <dd>{{ registration.data.authorization_status }}／{{ registration.data.version }}</dd>
      </dl>
    </section>
  </div>
</template>

<style scoped>
.source-form fieldset {
  display: grid;
  gap: 12px;
  margin: 16px 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}
.source-form label {
  display: grid;
  gap: 6px;
}
.source-form textarea {
  width: 100%;
  font: inherit;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid var(--line);
  background: #fff;
  color: inherit;
}
.source-detail {
  display: grid;
  grid-template-columns: minmax(100px, auto) 1fr;
  gap: 8px 16px;
  overflow-wrap: anywhere;
}
.source-detail dd {
  margin: 0;
}
@media (max-width: 600px) {
  .source-detail {
    grid-template-columns: 1fr;
  }
}
</style>
