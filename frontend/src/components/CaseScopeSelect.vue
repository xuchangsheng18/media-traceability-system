<script setup lang="ts">
import { computed, watch } from 'vue'
import { uuid } from '../business/api'

const props = defineProps<{
  modelValue: string
  caseIds: readonly string[]
  disabled: boolean
}>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const cases = computed(() => [
  ...new Set(
    props.caseIds.filter((id) => {
      try {
        uuid(id)
        return true
      } catch {
        return false
      }
    }),
  ),
])
const selected = computed(() => (cases.value.includes(props.modelValue) ? props.modelValue : ''))
watch(
  [() => props.modelValue, cases],
  () => {
    if (props.modelValue && !cases.value.includes(props.modelValue)) emit('update:modelValue', '')
  },
  { immediate: true, flush: 'sync' },
)
function change(event: Event) {
  if (props.disabled || !cases.value.length) return
  const value = (event.target as HTMLSelectElement).value
  if ((value === '' || cases.value.includes(value)) && value !== props.modelValue)
    emit('update:modelValue', value)
}
</script>

<template>
  <div class="case-scope-select">
    <label>
      上传案件
      <select
        aria-label="上传案件"
        :value="selected"
        :disabled="disabled || !cases.length"
        @change="change"
      >
        <option value="">请选择已有案件</option>
        <option
          v-for="caseId in cases"
          :key="caseId"
          :value="caseId"
        >
          {{ caseId }}
        </option>
      </select>
    </label>
    <p
      v-if="!cases.length"
      class="panel-copy"
    >
      当前无可用案件；请先连接业务身份。已连接时，请联系管理员核对案件访问范围。
    </p>
  </div>
</template>
