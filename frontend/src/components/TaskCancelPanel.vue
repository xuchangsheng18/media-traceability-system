<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useBusinessSession } from '../business/session'
import { createTaskCancellation } from '../business/task-cancel'

const props = defineProps<{ taskId: string }>()
const session = useBusinessSession()
const control = createTaskCancellation(session)
const reason = ref('')
const approval = ref('')
const confirmed = ref(false)
const locked = computed(() => control.state.busy || control.state.pending || control.state.accepted)
const canInspect = computed(
  () =>
    !!props.taskId &&
    session.has('task.read') &&
    session.has('task.cancel') &&
    !control.state.busy &&
    !control.state.pending,
)
const status = computed(() => {
  if (!session.state.user) return '请先连接业务身份。'
  if (!session.has('task.read') || !session.has('task.cancel'))
    return '当前身份没有任务读取或取消权限。'
  if (control.state.busy) return '正在处理取消操作，请勿重复提交…'
  if (control.state.uncertain) return `结果未确认，请重试原取消申请。${control.state.error}`
  if (control.state.accepted) return '取消申请已受理，尚未确认停止。请重新读取服务端当前执行状态。'
  if (control.state.error) return control.state.error
  if (control.state.execution)
    return `服务端当前执行状态：${control.state.execution.state}。只有符合取消条件的任务可以提交申请。`
  return '选择任务后读取取消条件；提交申请不会立即确认任务已停止。'
})
function clear() {
  control.reset()
  reason.value = ''
  approval.value = ''
  confirmed.value = false
}
async function inspect() {
  confirmed.value = false
  await control.inspect(props.taskId)
}
watch(() => props.taskId, clear, { flush: 'sync' })
watch(
  () => [
    session.state.generation,
    session.state.user?.user_id,
    session.state.user?.org_id,
    session.state.user?.permissions.join('|'),
    session.state.user?.case_ids.join('|'),
    session.state.user?.roles.join('|'),
  ],
  clear,
  { flush: 'sync' },
)
onBeforeUnmount(clear)
</script>
<template>
  <section
    class="panel span-12"
    aria-labelledby="task-cancel-heading"
  >
    <h2
      id="task-cancel-heading"
      class="panel-heading"
    >
      取消当前任务
    </h2>
    <p class="panel-copy">
      先读取当前任务条件，再确认提交取消申请。取消申请被受理后，仍须等待执行方停止确认。
    </p>
    <div class="toolbar">
      <button
        :disabled="!canInspect"
        @click="inspect"
      >
        读取取消条件
      </button>
      <span
        v-if="control.state.execution"
        class="muted"
        >运行版本 {{ control.state.execution.run_version }} ／控制版本
        {{ control.state.execution.version }}</span
      >
    </div>
    <div class="toolbar">
      <label
        >取消原因<textarea
          v-model="reason"
          aria-label="取消原因"
          :disabled="locked || !control.canSubmit()"
          rows="3"
        />
      </label>
      <label
        >批准编号（如需）<input
          v-model="approval"
          aria-label="取消批准编号"
          :disabled="locked || !control.canSubmit()"
          autocomplete="off"
      /></label>
    </div>
    <p class="muted">如该操作要求批准，请填写已获准的批准编号；填写编号本身不授予取消权限。</p>
    <label
      ><input
        v-model="confirmed"
        type="checkbox"
        :disabled="locked || !control.canSubmit()"
      />我确认提交取消申请，受理不代表已停止</label
    >
    <div class="toolbar">
      <button
        :disabled="!control.canSubmit() || !confirmed || !reason.trim()"
        @click="control.request(reason, approval, confirmed)"
      >
        提交取消申请
      </button>
      <button
        v-if="control.state.uncertain"
        :disabled="control.state.busy"
        @click="control.retry()"
      >
        重试原取消申请
      </button>
    </div>
    <p
      class="notice"
      data-testid="task-cancel-status"
      aria-live="polite"
    >
      {{ status }}
    </p>
  </section>
</template>
