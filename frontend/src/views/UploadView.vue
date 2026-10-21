<script setup lang="ts">
import { ref, toRefs } from 'vue'
import { useDevelopmentState } from '../state'
import { request } from '../api'
const { state: shared } = useDevelopmentState()
const { token, state, result, busy } = toRefs(shared)
const file = ref<File>()
function select(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0]
}
async function run() {
  if (!file.value || !token.value) {
    state.value = '请先填写访问令牌并选择测试图片'
    return
  }
  busy.value = true
  result.value = ''
  try {
    if (file.value.size > 1024 * 1024) throw new Error('图片需小于1 MiB')
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = reject
      reader.onload = () => resolve(String(reader.result).split(',')[1])
      reader.readAsDataURL(file.value!)
    })
    state.value = '上传与保存原件'
    const asset = await request('/poc/assets', token.value, {
      filename: file.value.name,
      image_base64: base64,
    })
    state.value = '创建异步分析任务'
    const job = await request(
      '/poc/jobs',
      token.value,
      { asset_id: asset.asset_id },
      crypto.randomUUID(),
    )
    for (let i = 0; i < 60; i++) {
      const status = await request(`/poc/jobs/${job.job_id}`, token.value)
      state.value = status.state
      if (status.state === 'SUCCEEDED') {
        result.value = JSON.stringify(status.result, null, 2)
        return
      }
      if (status.state === 'FAILED') throw new Error('分析失败，请查看任务错误码')
      await new Promise((resolve) => setTimeout(resolve, 1000))
    }
    throw new Error('任务仍在处理，请检查服务状态')
  } catch (error) {
    state.value = error instanceof Error ? error.message : '请求失败'
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <div class="view-grid">
    <section class="panel span-8">
      <h2 class="panel-heading">提交测试图片</h2>
      <p class="panel-copy">请使用无敏感内容的PNG或JPEG，小于1 MiB。</p>
      <ol
        class="upload-flow"
        aria-label="图片验证流程说明"
      >
        <li class="flow-step"><span>01</span>选择图片</li>
        <li class="flow-step"><span>02</span>保存原件</li>
        <li class="flow-step"><span>03</span>异步处理</li>
        <li class="flow-step"><span>04</span>结果读取</li>
      </ol>
      <div class="form-grid">
        <label class="field-full"
          >研发访问令牌<input
            v-model="token"
            aria-label="研发访问令牌"
            type="password"
            autocomplete="off" /></label
        ><label class="file-field field-full"
          >测试图片<input
            aria-label="测试图片"
            type="file"
            accept="image/png,image/jpeg"
            @change="select"
        /></label>
        <div class="form-actions">
          <button
            :disabled="busy"
            @click="run"
          >
            {{ busy ? '处理中…' : '开始验证' }}
          </button>
        </div>
      </div>
      <p
        class="notice"
        role="status"
      >
        {{ state }}
      </p>
    </section>
    <section class="panel span-4">
      <h2 class="panel-heading">处理结果</h2>
      <p class="panel-copy">此处使用合成CPU模型，只验证运行链路，结果不能用于业务研判。</p>
      <pre
        v-if="result"
        data-testid="result"
        >{{ result }}</pre>
      <p
        v-else
        class="muted empty-state"
      >
        完成分析后显示模型版本、向量引用与耗时。
      </p>
    </section>
  </div>
</template>
