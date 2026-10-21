<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { createAssetCatalog, createAssetReader } from '../business/catalog'
import { useBusinessSession } from '../business/session'
import { routeTaskId } from '../business/task-read'

const session = useBusinessSession()
const route = useRoute()
const caseId = ref(routeTaskId(route.query.case_id))
const assetId = ref(routeTaskId(route.query.asset_id))
const limit = ref(20)
const stateFilter = ref('')
const kindFilter = ref('')
const catalog = createAssetCatalog(session)
const detail = createAssetReader(session)
const rows = computed(() =>
  (catalog.state.data?.items ?? []).filter(
    (item) =>
      (!stateFilter.value || item.state === stateFilter.value) &&
      (!kindFilter.value || item.kind === kindFilter.value),
  ),
)
const status = computed(() => {
  if (!session.state.user) return '请先在业务身份页连接身份。'
  if (!session.has('asset.read')) return '当前身份没有资产读取权限。'
  if (catalog.state.busy) return '正在读取案件内资产…'
  if (catalog.state.error) return `${catalog.state.error} 分页失败后请重新查询首页。`
  if (catalog.state.loaded)
    return `第 ${catalog.state.pageNumber} 页，返回 ${catalog.state.data?.items.length ?? 0} 条，当前筛选显示 ${rows.value.length} 条。`
  return '请选择有权访问的案件并查询。案件编号与可见候选均不能替代服务端授权。'
})
function clear() {
  catalog.clear()
  detail.clear()
}
watch(
  [caseId, limit],
  () => {
    clear()
    assetId.value = ''
  },
  { flush: 'sync' },
)
watch(assetId, detail.clear, { flush: 'sync' })
watch(
  () => route.query,
  (query) => {
    caseId.value = routeTaskId(query.case_id)
    assetId.value = routeTaskId(query.asset_id)
    detail.clear()
  },
)
watch(() => session.state.generation, clear, { flush: 'sync' })
onBeforeUnmount(clear)
async function list(next = false) {
  detail.clear()
  assetId.value = ''
  if (next) await catalog.next()
  else await catalog.load(caseId.value, limit.value)
}
async function show(id = assetId.value) {
  assetId.value = id
  await detail.load(caseId.value, id)
}
</script>
<template>
  <div class="view-grid">
    <section class="panel span-12">
      <h2 class="panel-heading">媒体资产库</h2>
      <p class="panel-copy">
        按案件读取当前有权访问的资产。筛选仅作用于当前页，不代表案件内全部资产或总数。
      </p>
      <div class="toolbar">
        <label
          >案件编号（必填）<input
            v-model="caseId"
            list="asset-cases"
            aria-label="资产案件编号"
            autocomplete="off"
        /></label>
        <datalist id="asset-cases">
          <option
            v-for="id in session.state.user?.case_ids"
            :key="id"
            :value="id"
          />
        </datalist>
        <label
          >每页条数<select
            v-model="limit"
            aria-label="资产每页条数"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select></label
        >
        <button
          :disabled="catalog.state.busy || !session.has('asset.read')"
          @click="list()"
        >
          查询资产／回到首页
        </button>
        <button
          class="secondary"
          :disabled="
            catalog.state.busy || !catalog.state.data?.next_cursor || !session.has('asset.read')
          "
          @click="list(true)"
        >
          下一页资产
        </button>
      </div>
      <div class="toolbar">
        <label
          >当前页状态<select
            v-model="stateFilter"
            aria-label="资产当前页状态"
          >
            <option value="">全部状态</option>
            <option value="VALIDATING">VALIDATING</option>
            <option value="VALID">VALID</option>
            <option value="QUARANTINED">QUARANTINED</option>
            <option value="ARCHIVED">ARCHIVED</option>
          </select></label
        >
        <label
          >当前页类型<select
            v-model="kindFilter"
            aria-label="资产当前页类型"
          >
            <option value="">全部类型</option>
            <option value="original">原始媒体</option>
            <option value="derived">派生媒体</option>
          </select></label
        >
      </div>
      <p
        class="notice"
        role="status"
      >
        {{ status }}
      </p>
      <div
        v-if="rows.length"
        class="table-scroll"
      >
        <table>
          <thead>
            <tr>
              <th>资产编号</th>
              <th>类型／媒体格式</th>
              <th>状态</th>
              <th>大小（字节）</th>
              <th>记录版本</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in rows"
              :key="item.asset_id"
            >
              <td>{{ item.asset_id }}</td>
              <td>{{ item.kind === 'original' ? '原始媒体' : '派生媒体' }} / {{ item.mime }}</td>
              <td class="catalog-state">{{ item.state }}</td>
              <td>{{ item.size_bytes }}</td>
              <td>{{ item.version }}</td>
              <td>{{ item.created_at }}</td>
              <td class="catalog-actions">
                <button
                  class="secondary"
                  :disabled="detail.state.busy || !session.has('asset.read')"
                  @click="show(item.asset_id)"
                >
                  查看详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p
        v-if="catalog.state.loaded && !rows.length"
        class="empty-state"
      >
        当前页没有符合条件的可见资产；这不表示案件内没有其他资产。
      </p>
    </section>
    <section class="panel span-12">
      <h3 class="panel-heading">资产详情</h3>
      <div class="toolbar">
        <label
          >资产编号<input
            v-model="assetId"
            aria-label="资产详情编号"
            autocomplete="off"
        /></label>
        <button
          :disabled="detail.state.busy || !session.has('asset.read')"
          @click="show()"
        >
          读取资产详情
        </button>
      </div>
      <p
        v-if="detail.state.busy"
        class="notice"
        role="status"
      >
        正在读取并核对案件与资产编号…
      </p>
      <p
        v-else-if="detail.state.error"
        class="notice"
        role="status"
      >
        {{ detail.state.error }}
      </p>
      <p
        v-else-if="!detail.state.loaded"
        class="empty-state"
      >
        从列表选择资产，或填写当前案件内的资产编号。
      </p>
      <template v-if="detail.state.data">
        <p class="notice">
          本次读取已通过服务端授权；后续操作仍须逐次核验。原始对象及其固定版本仅供查看。
        </p>
        <dl>
          <dt>资产编号</dt>
          <dd>{{ detail.state.data.asset_id }}</dd>
          <dt>案件编号</dt>
          <dd>{{ detail.state.data.case_id }}</dd>
          <dt>内容编号</dt>
          <dd>{{ detail.state.data.content_id }}</dd>
          <dt>来源编号</dt>
          <dd>{{ detail.state.data.source_id }}</dd>
          <dt>类型／状态</dt>
          <dd>{{ detail.state.data.kind }} / {{ detail.state.data.state }}</dd>
          <dt>媒体格式</dt>
          <dd>{{ detail.state.data.mime }}</dd>
          <dt>大小（字节）</dt>
          <dd>{{ detail.state.data.size_bytes }}</dd>
          <dt>宽／高（像素）</dt>
          <dd>
            {{ detail.state.data.width ?? '未知' }} / {{ detail.state.data.height ?? '未知' }}
          </dd>
          <dt>时长（毫秒）</dt>
          <dd>{{ detail.state.data.duration_ms ?? '未知或不适用' }}</dd>
          <dt>记录版本</dt>
          <dd>{{ detail.state.data.version }}</dd>
          <dt>固定对象编号</dt>
          <dd>{{ detail.state.data.object_ref.object_id }}</dd>
          <dt>固定对象版本</dt>
          <dd>{{ detail.state.data.object_ref.version_id }}</dd>
          <dt>SHA-256</dt>
          <dd>{{ detail.state.data.object_ref.sha256 }}</dd>
          <dt>创建时间</dt>
          <dd>{{ detail.state.data.created_at }}</dd>
        </dl>
      </template>
      <p class="panel-copy">
        完整血缘、来源授权明细及受控下载尚未接入本页；来源编号和派生类型不能代替血缘关系。下载须另经适用权限与审计流程。
      </p>
    </section>
  </div>
</template>
<style scoped>
.catalog-state,
.catalog-actions button {
  white-space: nowrap;
}
.catalog-actions button {
  min-width: 80px;
}
</style>
