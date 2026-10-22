<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { errorMessage, FormError, uuid } from '../business/api'
import { useBusinessSession } from '../business/session'
import { createPendingReviewReader } from '../business/task-read'
import TaskReviewHistoryPanel from '../components/TaskReviewHistoryPanel.vue'
const session = useBusinessSession()
const caseId = ref('')
const queue = createPendingReviewReader(session)
const selectedTaskId = ref('')
const localError = ref('')
const selected = computed(() =>
  !queue.state.busy && queue.state.loaded
    ? queue.state.data?.items.find((item) => item.task_id === selectedTaskId.value)
    : undefined,
)
const availability = {
  READY: '可读取结果（READY）',
  RESULT_UNAVAILABLE: '结果不可用（RESULT_UNAVAILABLE）',
  SOURCE_BLOCKED: '来源访问受阻（SOURCE_BLOCKED）',
}
function clear() {
  selectedTaskId.value = ''
  localError.value = ''
  queue.clear()
}
watch(caseId, clear, { flush: 'sync' })
watch(
  () =>
    JSON.stringify([
      session.state.generation,
      session.state.user?.user_id,
      session.state.user?.org_id,
      session.state.user?.roles,
      session.state.user?.permissions,
      session.state.user?.case_ids,
      session.has('review.read'),
    ]),
  clear,
  { flush: 'sync' },
)
watch(
  [() => queue.state.data, () => queue.state.loaded, () => queue.state.busy],
  () => {
    if (!selected.value || selected.value.case_id !== caseId.value.toLowerCase())
      selectedTaskId.value = ''
  },
  { flush: 'sync' },
)
onBeforeUnmount(clear)
async function list(next = false) {
  const cursor = next ? queue.state.data?.next_cursor : null
  if (next && !cursor) return
  clear()
  try {
    const id = uuid(caseId.value).toLowerCase()
    if (!session.state.user?.case_ids.some((visible) => visible.toLowerCase() === id))
      throw new FormError('请选择当前身份可见的案件；未向服务端发送查询。')
    await queue.load(id, cursor)
  } catch (error) {
    localError.value = errorMessage(error)
  }
}
</script>
<template>
  <div class="view-grid">
    <section class="panel span-12">
      <h2 class="panel-heading">待复核队列</h2>
      <p class="panel-copy">
        按有权访问的案件分页查询。选择任务后可读取上下文与历史；复核提交另需执行权限及服务端有效条件。
      </p>
      <div class="toolbar">
        <label
          >案件编号<input
            v-model="caseId"
            list="review-cases"
            aria-label="队列案件编号"
            autocomplete="off"
        /></label>
        <datalist id="review-cases">
          <option
            v-for="id in session.state.user?.case_ids"
            :key="id"
            :value="id"
          />
        </datalist>
        <button
          :disabled="queue.state.busy || !session.has('review.read')"
          @click="list()"
        >
          查询待复核
        </button>
        <button
          class="secondary"
          :disabled="
            queue.state.busy || !queue.state.data?.next_cursor || !session.has('review.read')
          "
          @click="list(true)"
        >
          下一页
        </button>
      </div>
      <p
        v-if="!session.state.user"
        class="notice"
        role="status"
      >
        请先在业务身份页连接身份。
      </p>
      <p
        v-else-if="!session.has('review.read')"
        class="notice"
        role="status"
      >
        当前身份没有待复核队列读取权限。
      </p>
      <p
        v-else-if="queue.state.busy"
        class="notice"
        role="status"
      >
        正在读取待复核队列…
      </p>
      <p
        v-else-if="localError || queue.state.error"
        class="notice"
        role="status"
      >
        {{ localError || queue.state.error }}
      </p>
      <p
        v-else-if="queue.state.loaded"
        class="notice"
        role="status"
      >
        当前页 {{ queue.state.data?.items.length || 0 }} 条待复核记录。
      </p>
      <p
        v-else
        class="notice"
        role="status"
      >
        请选择案件并查询待复核记录。
      </p>
      <div
        v-if="queue.state.data?.items.length"
        class="table-scroll"
      >
        <table>
          <thead>
            <tr>
              <th>任务编号</th>
              <th>任务状态</th>
              <th>结果可用性</th>
              <th>运行／结果版本</th>
              <th>查看</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in queue.state.data.items"
              :key="`${item.task_id}-${index}`"
            >
              <td>{{ item.task_id }}</td>
              <td>{{ item.task_state }}</td>
              <td>{{ availability[item.availability] }}</td>
              <td>
                {{
                  item.context
                    ? `${item.context.run_version} / ${item.context.result_version}`
                    : '不可用'
                }}
              </td>
              <td>
                <button
                  class="secondary"
                  :disabled="!session.has('review.read')"
                  @click="selectedTaskId = item.task_id"
                >
                  选择复核记录
                </button>
                <RouterLink :to="{ name: 'tasks', query: { task_id: item.task_id } }"
                  >查看任务</RouterLink
                >
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p
        v-if="queue.state.loaded && !queue.state.error && !queue.state.data?.items.length"
        class="muted empty-state"
      >
        当前页无待复核记录。
      </p>
    </section>
    <TaskReviewHistoryPanel
      v-if="selected"
      :key="`${selected.case_id}-${selected.task_id}`"
      :case-id="selected.case_id"
      :task-id="selected.task_id"
    />
  </div>
</template>
