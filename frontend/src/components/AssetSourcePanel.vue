<script setup lang="ts">
import { computed, onBeforeUnmount } from 'vue'
import type { Schemas } from '../business/api'
import { createAssetSourceReader } from '../business/asset-source'
import { useBusinessSession } from '../business/session'

const props = defineProps<{
  caseId: string
  assetId: string
  asset: Schemas['Asset'] | null
  loaded: boolean
  busy: boolean
}>()
const session = useBusinessSession()
const reader = createAssetSourceReader(session, () => ({ ...props }))
const status = computed(() => {
  if (!session.state.user) return '请先连接业务身份。'
  if (!session.has('asset.read') || !session.has('source.read'))
    return '当前身份没有资产或来源读取权限。'
  if (reader.state.busy) return '正在读取当前资产的来源授权记录…'
  if (reader.state.error) return reader.state.error
  if (reader.state.loaded) return '已读取服务端来源记录；刷新可重新核验当前可见版本。'
  return '尚未读取此资产的来源授权明细。'
})
const labels: Record<Schemas['Source']['authorization_status'], string> = {
  pending: '待核验',
  verified: '已核验',
  expired: '已过期',
  revoked: '已撤销',
}
onBeforeUnmount(reader.dispose)
</script>

<template>
  <section aria-label="资产来源授权">
    <h3 class="panel-heading">来源与授权记录</h3>
    <button
      class="secondary"
      :disabled="!reader.canLoad()"
      @click="reader.load()"
    >
      读取来源授权明细
    </button>
    <p
      class="notice"
      role="status"
    >
      {{ status }}
    </p>
    <dl v-if="reader.state.data">
      <dt>来源编号</dt>
      <dd>{{ reader.state.data.source_id }}</dd>
      <dt>来源名称</dt>
      <dd>{{ reader.state.data.name }}</dd>
      <dt>来源类型</dt>
      <dd>{{ reader.state.data.source_type }}</dd>
      <dt>服务端授权状态</dt>
      <dd data-testid="asset-source-status-value">
        {{ labels[reader.state.data.authorization_status] }}（{{
          reader.state.data.authorization_status
        }}）
      </dd>
      <dt>授权依据编号</dt>
      <dd>{{ reader.state.data.authorization_ref }}</dd>
      <dt>记录用途</dt>
      <dd>
        <ul>
          <li
            v-for="purpose in reader.state.data.purpose"
            :key="purpose"
          >
            {{ purpose }}
          </li>
        </ul>
      </dd>
      <dt>有效期记录</dt>
      <dd>{{ reader.state.data.expires_at ?? '未提供' }}</dd>
      <dt>来源记录版本</dt>
      <dd>{{ reader.state.data.version }}</dd>
    </dl>
    <p class="panel-copy">
      此处显示本次读取的来源记录，后续使用仍由服务端逐次授权；未提供有效期不表示永久授权。
    </p>
  </section>
</template>
