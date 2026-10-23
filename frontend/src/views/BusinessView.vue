<script setup lang="ts">
import { ref } from 'vue'
import { useBusinessSession } from '../business/session'
const session = useBusinessSession()
const token = ref('')
async function connect() {
  const submitted = token.value
  token.value = ''
  await session.connect(submitted)
}
</script>
<template>
  <div class="view-grid">
    <section class="panel span-12">
      <h2 class="panel-heading">业务身份</h2>
      <p class="panel-copy">
        使用业务身份系统签发的访问令牌。令牌仅保留在当前页面内存；刷新或清除身份后失效。上传验证令牌不能代替业务身份。
      </p>
      <form
        class="form-grid"
        @submit.prevent="connect"
      >
        <label class="field-full"
          >业务访问令牌<input
            v-model="token"
            type="password"
            autocomplete="off"
            required
            aria-label="业务访问令牌"
        /></label>
        <div class="form-actions">
          <button :disabled="session.state.busy">连接身份</button>
          <button
            type="button"
            class="secondary"
            @click="session.disconnect"
          >
            清除身份与结果
          </button>
        </div>
      </form>
      <p
        class="notice"
        role="status"
      >
        {{ session.state.message }}
      </p>
      <dl v-if="session.state.user">
        <dt>用户编号</dt>
        <dd>{{ session.state.user.user_id }}</dd>
        <dt>单位编号</dt>
        <dd>{{ session.state.user.org_id }}</dd>
        <dt>角色</dt>
        <dd>{{ session.state.user.roles.join('、') || '无' }}</dd>
        <dt>可访问案件</dt>
        <dd>{{ session.state.user.case_ids.join('、') || '无' }}</dd>
      </dl>
      <p
        v-else
        class="muted empty-state"
      >
        身份或正式规则尚未接入时，页面会显示拒绝原因，不生成演示业务成功。
      </p>
    </section>
  </div>
</template>
