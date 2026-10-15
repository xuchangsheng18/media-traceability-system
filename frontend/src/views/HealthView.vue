<script setup lang="ts">
import { useDevelopmentState } from '../state'
const { state, checkHealth } = useDevelopmentState()
</script>
<template>
  <section>
    <h2>系统健康</h2>
    <p>检查当前研发服务连接。需要访问权限时，请填写研发令牌。</p>
    <label
      >研发访问令牌<input
        v-model="state.token"
        aria-label="研发访问令牌"
        type="password"
        autocomplete="off"
    /></label>
    <button
      :disabled="state.checking"
      @click="checkHealth"
    >
      {{ state.checking ? '检查中…' : '检查状态' }}
    </button>
    <p
      role="status"
      aria-live="polite"
    >
      {{ state.healthMessage }}
    </p>
  </section>
</template>
