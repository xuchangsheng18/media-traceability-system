<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBusinessSession } from '../business/session'
import { createTaskReader, routeTaskId } from '../business/task-read'

const session = useBusinessSession()
const route = useRoute()
const taskId = ref('')
const runVersion = ref('')
const resultVersion = ref('')
let historyEditGeneration = 0
const reader = createTaskReader(session)
const { execution, nodes, events, snapshot, risk, forensics, evidence, timeline } = reader
const resultPanels = [
  { title: '风险发现', slot: risk },
  { title: '取证分析', slot: forensics },
]
const resultsBusy = computed(() =>
  [snapshot, risk, forensics, evidence, timeline].some((slot) => slot.state.busy),
)
const status = computed(() => {
  if (!session.state.user) return '请先在业务身份页连接身份。'
  if (!session.has('task.read')) return '当前身份没有任务读取权限。'
  if (execution.state.error) return execution.state.error
  if (execution.state.busy) return '正在读取任务当前执行状态…'
  if (execution.state.loaded) return '已读取当前执行状态；运行记录和历史结果分别列示。'
  return '输入有权访问的任务编号，查询当前执行状态。'
})
watch(
  taskId,
  () => {
    reader.reset()
    runVersion.value = ''
    resultVersion.value = ''
  },
  { flush: 'sync' },
)
watch(
  [runVersion, resultVersion],
  () => {
    historyEditGeneration++
    reader.clearResults()
  },
  { flush: 'sync' },
)
watch(
  () => route.query.task_id,
  (value) => {
    taskId.value = routeTaskId(value)
  },
  { immediate: true },
)
watch(() => session.state.generation, reader.reset, { flush: 'sync' })
onBeforeUnmount(reader.reset)

async function observe() {
  const selected = taskId.value
  const historyVersion = historyEditGeneration
  await reader.observe(selected)
  const current = execution.state.data
  if (current && selected === taskId.value && historyVersion === historyEditGeneration) {
    runVersion.value = String(current.run_version)
    resultVersion.value = current.result_version > 0 ? String(current.result_version) : ''
  }
}
async function loadResults() {
  await reader.loadResults({
    taskId: taskId.value,
    runVersion: Number(runVersion.value),
    resultVersion: Number(resultVersion.value),
  })
}
</script>
<template>
  <section>
    <h2>任务与结果</h2>
    <p>按任务编号读取当前执行状态和运行记录。当前状态不等于已形成结果或业务批准。</p>
    <label
      >任务编号<input
        v-model="taskId"
        aria-label="任务编号"
        autocomplete="off"
    /></label>
    <button
      :disabled="execution.state.busy || !session.has('task.read')"
      @click="observe"
    >
      查询任务状态
    </button>
    <p role="status">{{ status }}</p>
    <dl v-if="execution.state.data">
      <dt>当前状态</dt>
      <dd>{{ execution.state.data.state }}</dd>
      <dt>案件编号</dt>
      <dd>{{ execution.state.data.case_id }}</dd>
      <dt>当前运行／结果／控制版本</dt>
      <dd>
        {{ execution.state.data.run_version }} / {{ execution.state.data.result_version }} /
        {{ execution.state.data.version }}
      </dd>
      <dt>当前结果快照</dt>
      <dd>
        {{
          execution.state.data.result_available
            ? '可读取；仍须逐次授权和版本核验'
            : '结果不可用；当前执行状态仍可观察'
        }}
      </dd>
    </dl>
  </section>
  <section v-if="execution.state.data">
    <h3>运行节点 · 运行 {{ execution.state.data.run_version }}</h3>
    <p
      v-if="nodes.state.busy"
      role="status"
    >
      正在读取节点…
    </p>
    <p
      v-if="nodes.state.error"
      role="status"
    >
      {{ nodes.state.error }}
    </p>
    <div
      v-if="nodes.state.data?.items.length"
      class="table-scroll"
    >
      <table>
        <thead>
          <tr>
            <th>节点</th>
            <th>状态</th>
            <th>尝试</th>
            <th>必需</th>
            <th>原因</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="node in nodes.state.data.items"
            :key="node.node_id"
          >
            <td>{{ node.node_code }}</td>
            <td>{{ node.state }}</td>
            <td>{{ node.attempt }}</td>
            <td>{{ node.required ? '是' : '否' }}</td>
            <td>{{ node.reason || '无' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p
      v-if="nodes.state.loaded && !nodes.state.data?.items.length"
      class="muted"
    >
      此运行尚无节点记录。
    </p>
    <h3>任务事件 · 运行 {{ execution.state.data.run_version }}</h3>
    <p
      v-if="events.state.busy"
      role="status"
    >
      正在读取事件…
    </p>
    <p
      v-if="events.state.error"
      role="status"
    >
      {{ events.state.error }}
    </p>
    <div
      v-if="events.state.data?.items.length"
      class="table-scroll"
    >
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>原状态</th>
            <th>目标状态</th>
            <th>原因</th>
            <th>请求编号</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="event in events.state.data.items"
            :key="event.event_id"
          >
            <td>{{ event.created_at }}</td>
            <td>{{ event.from_state || '无' }}</td>
            <td>{{ event.to_state }}</td>
            <td>{{ event.reason }}</td>
            <td>{{ event.request_id }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p
      v-if="events.state.loaded && !events.state.data?.items.length"
      class="muted"
    >
      当前页无任务事件。
    </p>
    <button
      class="secondary"
      :disabled="events.state.busy || !events.state.data?.next_cursor || !session.has('task.read')"
      @click="reader.loadEvents(true)"
    >
      下一页事件
    </button>
  </section>
  <section>
    <h3>指定版本结果</h3>
    <p>
      结果按指定的运行和结果版本读取；每类结果分别核验访问权限。模型发现供业务复核，不直接表述执法或法律结论。
    </p>
    <label
      >历史运行版本<input
        v-model="runVersion"
        aria-label="历史运行版本"
        inputmode="numeric"
        autocomplete="off"
    /></label>
    <label
      >历史结果版本<input
        v-model="resultVersion"
        aria-label="历史结果版本"
        inputmode="numeric"
        autocomplete="off"
    /></label>
    <button
      :disabled="resultsBusy || !session.has('task.read')"
      @click="loadResults"
    >
      读取指定版本结果
    </button>
    <p
      v-if="resultsBusy"
      role="status"
    >
      正在读取并核对历史结果版本…
    </p>
    <p
      v-if="snapshot.state.error"
      role="status"
    >
      结果快照：{{ snapshot.state.error }}
    </p>
    <dl v-if="snapshot.state.data">
      <dt>历史任务状态</dt>
      <dd>{{ snapshot.state.data.state }}</dd>
      <dt>已核验运行／结果版本</dt>
      <dd>{{ snapshot.state.data.run_version }} / {{ snapshot.state.data.result_version }}</dd>
      <dt>媒体编号</dt>
      <dd>{{ snapshot.state.data.asset_id }}</dd>
      <dt>规则版本</dt>
      <dd>{{ snapshot.state.data.policy_version }}</dd>
      <dt>缺失模态</dt>
      <dd>{{ snapshot.state.data.missing_modalities.join('、') || '无' }}</dd>
      <dt>报告适用状态</dt>
      <dd>{{ snapshot.state.data.report_eligibility }}</dd>
    </dl>
    <p
      v-if="!snapshot.state.loaded && !snapshot.state.error && !resultsBusy"
      class="muted"
    >
      尚未读取指定版本结果。
    </p>
  </section>
  <section
    v-for="panel in resultPanels"
    :key="panel.title"
  >
    <h3>{{ panel.title }}</h3>
    <p
      v-if="panel.slot.state.busy"
      role="status"
    >
      正在读取{{ panel.title }}…
    </p>
    <p
      v-if="panel.slot.state.error"
      role="status"
    >
      {{ panel.slot.state.error }}
    </p>
    <div
      v-if="panel.slot.state.data?.findings.length"
      class="table-scroll"
    >
      <table>
        <thead>
          <tr>
            <th>标签／状态</th>
            <th>原始／校准分数</th>
            <th>模型／版本</th>
            <th>映射版本</th>
            <th>证据编号</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="finding in panel.slot.state.data.findings"
            :key="finding.finding_id"
          >
            <td>{{ finding.label }} / {{ finding.status }}</td>
            <td>{{ finding.raw_score }} / {{ finding.calibrated_score ?? '未校准' }}</td>
            <td>{{ finding.model_name }} / {{ finding.model_version }}</td>
            <td>{{ finding.mapping_version }}</td>
            <td>{{ finding.evidence_ids.join('、') || '无' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p
      v-if="panel.slot.state.loaded && !panel.slot.state.data?.findings.length"
      class="muted"
    >
      该历史版本无{{ panel.title }}记录。
    </p>
    <template v-if="panel.slot.state.data">
      <p>缺失模态：{{ panel.slot.state.data.missing_modalities.join('、') || '无' }}</p>
      <ul v-if="panel.slot.state.data.warnings.length">
        <li
          v-for="(warning, index) in panel.slot.state.data.warnings"
          :key="index"
        >
          {{ warning }}
        </li>
      </ul>
    </template>
  </section>
  <section>
    <h3>证据索引</h3>
    <p
      v-if="evidence.state.busy"
      role="status"
    >
      正在读取证据索引…
    </p>
    <p
      v-if="evidence.state.error"
      role="status"
    >
      {{ evidence.state.error }}
    </p>
    <div
      v-if="evidence.state.data?.items.length"
      class="table-scroll"
    >
      <table>
        <thead>
          <tr>
            <th>证据编号</th>
            <th>类型</th>
            <th>映射版本</th>
            <th>模型／版本</th>
            <th>SHA-256</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in evidence.state.data.items"
            :key="item.evidence_id"
          >
            <td>{{ item.evidence_id }}</td>
            <td>{{ item.kind }}</td>
            <td>{{ item.mapping_version }}</td>
            <td>{{ item.model_name || '无' }} / {{ item.model_version || '无' }}</td>
            <td>{{ item.sha256 }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p
      v-if="evidence.state.loaded && !evidence.state.data?.items.length"
      class="muted"
    >
      该历史版本无证据索引记录。
    </p>
  </section>
  <section>
    <h3>媒体时间轴</h3>
    <p
      v-if="timeline.state.busy"
      role="status"
    >
      正在读取媒体时间轴…
    </p>
    <p
      v-if="timeline.state.error"
      role="status"
    >
      {{ timeline.state.error }}
    </p>
    <p v-if="timeline.state.data">映射版本：{{ timeline.state.data.mapping_version }}</p>
    <div
      v-if="timeline.state.data?.items.length"
      class="table-scroll"
    >
      <table>
        <thead>
          <tr>
            <th>类型</th>
            <th>时间范围（毫秒）</th>
            <th>内容</th>
            <th>映射版本</th>
            <th>证据编号</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in timeline.state.data.items"
            :key="item.item_id"
          >
            <td>{{ item.kind }}</td>
            <td>{{ item.time_range.start_ms }}–{{ item.time_range.end_ms }}</td>
            <td>{{ item.text || '无文本' }}</td>
            <td>{{ item.mapping_version }}</td>
            <td>{{ item.evidence_id || '无' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p
      v-if="timeline.state.loaded && !timeline.state.data?.items.length"
      class="muted"
    >
      该历史版本无时间轴记录。
    </p>
    <p
      v-if="snapshot.state.error && !timeline.state.loaded"
      class="muted"
    >
      需先取得有效的历史任务快照，才能定位对应媒体时间轴。
    </p>
  </section>
</template>
