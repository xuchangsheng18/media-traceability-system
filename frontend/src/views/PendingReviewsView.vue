<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useBusinessSession } from '../business/session'
import { createPendingReviewReader } from '../business/task-read'
const session = useBusinessSession()
const caseId = ref('')
const queue = createPendingReviewReader(session)
const availability = {
  READY: '可读取结果（READY）',
  RESULT_UNAVAILABLE: '结果不可用（RESULT_UNAVAILABLE）',
  SOURCE_BLOCKED: '来源访问受阻（SOURCE_BLOCKED）',
}
watch(caseId, queue.clear, { flush: 'sync' })
watch(() => session.state.generation, queue.clear, { flush: 'sync' })
onBeforeUnmount(queue.clear)
async function list(next = false) {
  const cursor = next ? queue.state.data?.next_cursor : null
  if (next && !cursor) return
  await queue.load(caseId.value, cursor)
}
</script>
<template>
  <section>
    <h2>待复核队列</h2>
    <p>按有权访问的案件分页查询。结果可用性与复核任务状态分别展示；此页提供任务查看入口。</p>
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
      :disabled="queue.state.busy || !queue.state.data?.next_cursor || !session.has('review.read')"
      @click="list(true)"
    >
      下一页
    </button>
    <p
      v-if="!session.state.user"
      role="status"
    >
      请先在业务身份页连接身份。
    </p>
    <p
      v-else-if="!session.has('review.read')"
      role="status"
    >
      当前身份没有待复核队列读取权限。
    </p>
    <p
      v-else-if="queue.state.busy"
      role="status"
    >
      正在读取待复核队列…
    </p>
    <p
      v-else-if="queue.state.error"
      role="status"
    >
      {{ queue.state.error }}
    </p>
    <p
      v-else-if="queue.state.loaded"
      role="status"
    >
      当前页 {{ queue.state.data?.items.length || 0 }} 条待复核记录。
    </p>
    <p
      v-else
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
              <RouterLink :to="{ name: 'tasks', query: { task_id: item.task_id } }"
                >查看任务</RouterLink
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p
      v-if="queue.state.loaded && !queue.state.data?.items.length"
      class="muted"
    >
      当前页无待复核记录。
    </p>
  </section>
</template>
