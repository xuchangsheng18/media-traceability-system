<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { createTaskCatalog } from '../business/catalog'
import { useBusinessSession } from '../business/session'

const emit = defineEmits<{ select: [taskId: string]; clear: [] }>()
const session = useBusinessSession()
const caseId = ref('')
const limit = ref(20)
const stateFilter = ref('')
const catalog = createTaskCatalog(session)
const states = [
  'CREATED',
  'QUEUED',
  'RUNNING',
  'WAIT_REVIEW',
  'REVIEWING',
  'SUCCEEDED',
  'FAILED',
  'RETURNED',
  'CANCEL_REQUESTED',
  'CANCELLED',
  'ARCHIVED',
]
const stateLabels: Record<string, string> = {
  CREATED: '已创建',
  QUEUED: '已排队',
  RUNNING: '运行中',
  WAIT_REVIEW: '待复核',
  REVIEWING: '复核中',
  SUCCEEDED: '任务成功',
  FAILED: '失败',
  RETURNED: '已退回',
  CANCEL_REQUESTED: '请求取消',
  CANCELLED: '已取消',
  ARCHIVED: '已归档',
}
const rows = computed(() =>
  (catalog.state.data?.items ?? []).filter(
    (item) => !stateFilter.value || item.state === stateFilter.value,
  ),
)
const status = computed(() => {
  if (!session.state.user) return '请先在业务身份页连接身份。'
  if (!session.has('task.read')) return '当前身份没有任务读取权限。'
  if (catalog.state.busy) return '正在读取案件内当前任务…'
  if (catalog.state.error) return `${catalog.state.error} 分页失败后请重新查询首页。`
  if (catalog.state.loaded)
    return `第 ${catalog.state.pageNumber} 页，返回 ${catalog.state.data?.items.length ?? 0} 条，当前筛选显示 ${rows.value.length} 条。`
  return '请选择有权访问的案件并查询；无结果版本的任务也可查看当前状态。'
})
function clear() {
  catalog.clear()
  emit('clear')
}
watch([caseId, limit], clear, { flush: 'sync' })
watch(() => session.state.generation, clear, { flush: 'sync' })
onBeforeUnmount(catalog.clear)
async function list(next = false) {
  emit('clear')
  if (next) await catalog.next()
  else await catalog.load(caseId.value, limit.value)
}
</script>
<template>
  <section class="panel span-12">
    <h2 class="panel-heading">案件任务列表</h2>
    <p class="panel-copy">
      列表读取当前任务和当前运行的节点状态；任务成功不代表业务批准。真实DAG进度计算尚待验证，本页不推算完成百分比。
    </p>
    <div class="toolbar">
      <label
        >案件编号（必填）<input
          v-model="caseId"
          list="task-cases"
          aria-label="任务列表案件编号"
          autocomplete="off"
      /></label>
      <datalist id="task-cases">
        <option
          v-for="id in session.state.user?.case_ids"
          :key="id"
          :value="id"
        />
      </datalist>
      <label
        >每页条数<select
          v-model="limit"
          aria-label="任务每页条数"
        >
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select></label
      >
      <button
        :disabled="catalog.state.busy || !session.has('task.read')"
        @click="list()"
      >
        查询任务／回到首页
      </button>
      <button
        class="secondary"
        :disabled="
          catalog.state.busy || !catalog.state.data?.next_cursor || !session.has('task.read')
        "
        @click="list(true)"
      >
        下一页任务
      </button>
    </div>
    <label
      >当前页状态筛选<select
        v-model="stateFilter"
        aria-label="任务当前页状态"
      >
        <option value="">全部状态</option>
        <option
          v-for="state in states"
          :key="state"
          :value="state"
        >
          {{ stateLabels[state] }}（{{ state }}）
        </option>
      </select></label
    >
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
            <th>任务／媒体编号</th>
            <th>当前状态</th>
            <th>运行／结果版本</th>
            <th>当前节点</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in rows"
            :key="item.task_id"
          >
            <td>
              {{ item.task_id }}<br /><RouterLink
                :to="{ name: 'assets', query: { case_id: item.case_id, asset_id: item.asset_id } }"
                >{{ item.asset_id }}</RouterLink
              >
            </td>
            <td class="catalog-state">{{ item.state }}</td>
            <td>
              {{ item.run_version }} /
              {{ item.result_version > 0 ? item.result_version : '尚无结果版本' }}
            </td>
            <td>
              <template
                v-for="node in item.nodes"
                :key="node.node_code"
                ><div>
                  {{ node.node_code }} · {{ node.state }} · 尝试 {{ node.attempt }} ·
                  {{ node.required ? '必需' : '可选'
                  }}<span v-if="node.reason"> · {{ node.reason }}</span>
                </div></template
              ><span v-if="!item.nodes.length">尚无节点记录</span>
            </td>
            <td>{{ item.created_at }}</td>
            <td class="catalog-actions">
              <button
                class="secondary"
                :disabled="!session.has('task.read')"
                @click="emit('select', item.task_id)"
              >
                查看任务
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
      当前页没有符合条件的可见任务；筛选仅作用于当前页。
    </p>
  </section>
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
