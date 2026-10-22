<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue'
import { createTaskReviewReader } from '../business/review-read'
import { useBusinessSession } from '../business/session'

const props = defineProps<{ caseId: string; taskId: string }>()
const session = useBusinessSession()
const reader = createTaskReviewReader(session)
const allowed = computed(
  () =>
    !!session.state.user &&
    session.has('review.read') &&
    session.state.user.case_ids.some((id) => id.toLowerCase() === props.caseId.toLowerCase()),
)
watch(() => [props.caseId, props.taskId], reader.clear, { flush: 'sync' })
onBeforeUnmount(reader.dispose)
async function history(next = false) {
  const cursor = next ? reader.state.history.data?.next_cursor : null
  if (next && !cursor) return
  await reader.loadHistory(props.caseId, props.taskId, cursor)
}
</script>

<template>
  <section
    class="panel span-12"
    aria-label="任务复核只读记录"
  >
    <h2 class="panel-heading">任务复核上下文与历史</h2>
    <p class="panel-copy">
      当前案件：{{ caseId }}；所选任务：{{ taskId }}。本面板只读，不授予复核或批准权限。
      当前上下文与历史记录分别读取；历史保留各自运行、结果及策略版本。
    </p>
    <h3>当前复核上下文</h3>
    <button
      :disabled="!allowed || reader.state.context.busy"
      @click="reader.loadContext(caseId, taskId)"
    >
      读取当前复核上下文
    </button>
    <p
      class="notice"
      role="status"
      data-testid="review-context-status"
    >
      {{
        !allowed
          ? '当前身份或案件范围不允许读取。'
          : reader.state.context.busy
            ? '正在读取复核上下文…'
            : reader.state.context.error ||
              (reader.state.context.loaded
                ? '已读取本次服务端上下文；不表示允许提交复核。'
                : '尚未读取当前上下文。')
      }}
    </p>
    <dl
      v-if="reader.state.context.data"
      data-testid="review-context-data"
    >
      <dt>任务编号</dt>
      <dd>{{ reader.state.context.data.task_id }}</dd>
      <dt>运行版本</dt>
      <dd>{{ reader.state.context.data.run_version }}</dd>
      <dt>结果版本</dt>
      <dd>{{ reader.state.context.data.result_version }}</dd>
      <dt>策略版本</dt>
      <dd>{{ reader.state.context.data.policy_version }}</dd>
      <dt>快照SHA-256</dt>
      <dd>{{ reader.state.context.data.snapshot_sha256 }}</dd>
      <dt>对象版本</dt>
      <dd>{{ reader.state.context.data.object_version }}</dd>
      <dt>当前复核版本</dt>
      <dd>{{ reader.state.context.data.review_version }}</dd>
    </dl>
    <h3>历史复核记录</h3>
    <div class="toolbar">
      <button
        :disabled="!allowed || reader.state.history.busy"
        @click="history()"
      >
        读取复核历史／回到首页
      </button>
      <button
        class="secondary"
        :disabled="!allowed || reader.state.history.busy || !reader.state.history.data?.next_cursor"
        @click="history(true)"
      >
        下一页复核历史
      </button>
    </div>
    <p
      class="notice"
      role="status"
      data-testid="review-history-status"
    >
      {{
        !allowed
          ? '当前身份或案件范围不允许读取。'
          : reader.state.history.busy
            ? '正在读取历史复核记录…'
            : reader.state.history.error ||
              (reader.state.history.loaded
                ? `当前页 ${reader.state.history.data?.items.length ?? 0} 条历史复核记录。`
                : '尚未读取历史复核记录。')
      }}
    </p>
    <p
      v-if="
        reader.state.history.loaded &&
        !reader.state.history.error &&
        !reader.state.history.data?.items.length
      "
      class="muted"
      data-testid="review-history-empty"
    >
      当前页无历史复核记录。
    </p>
    <article
      v-for="item in reader.state.history.data?.items"
      :key="item.review_id"
      data-testid="review-history-record"
    >
      <dl>
        <dt>复核编号</dt>
        <dd>{{ item.review_id }}</dd>
        <dt>复核人编号</dt>
        <dd>{{ item.reviewer_id }}</dd>
        <dt>任务编号</dt>
        <dd>{{ item.task_id }}</dd>
        <dt>历史运行／结果版本</dt>
        <dd>{{ item.run_version }} / {{ item.result_version }}</dd>
        <dt>历史策略版本</dt>
        <dd>{{ item.policy_version }}</dd>
        <dt>预期复核版本／已记录版本</dt>
        <dd>{{ item.expected_review_version }} / {{ item.review_version }}</dd>
        <dt>记录决定</dt>
        <dd>{{ item.decision }}</dd>
        <dt>记录原因</dt>
        <dd>{{ item.reason }}</dd>
        <dt>关联证据编号</dt>
        <dd>
          <ul>
            <li
              v-for="id in item.evidence_ids"
              :key="id"
            >
              {{ id }}
            </li>
          </ul>
        </dd>
        <dt>创建时间</dt>
        <dd>{{ item.created_at }}</dd>
      </dl>
    </article>
    <p class="panel-copy">
      记录决定是历史事实；不表示当前批准有效、证据已核验或可以执行后续动作。证据编号供定位，本批不读取或下载证据内容。
    </p>
  </section>
</template>
