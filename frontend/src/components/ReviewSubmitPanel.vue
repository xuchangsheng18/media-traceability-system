<script setup lang="ts">
import { onBeforeUnmount } from 'vue'
import { createReviewSubmitter, type ReviewSubmissionSelection } from '../business/review-submit'
import { useBusinessSession } from '../business/session'

const props = defineProps<ReviewSubmissionSelection>()
const control = createReviewSubmitter(useBusinessSession(), () => props)
onBeforeUnmount(control.dispose)
</script>

<template>
  <section
    class="panel span-12"
    aria-label="受控复核提交"
  >
    <h3>受控复核记录</h3>
    <p
      class="panel-copy"
      data-testid="review-submit-draft-notice"
    >
      本页输入仅保存在当前页面内存，未保存到服务器；刷新、离开、身份或上下文变化会清空。
      离开后请先读取当前上下文与复核历史，再核对是否已形成记录，不能跨刷新重试原请求。
      证据编号由你引用，仍需服务端核验案件、固定版本、来源授权和完整性。
    </p>
    <p class="panel-copy">
      仅当前上下文可提交。历史记录不会变成当前条件；缺少正式规则或独立职责提供者时，服务端继续拒绝。
      二次确认仅防误操作，不等于独立复核或批准；记录决定不代表退回已执行、重算已启动或允许导出。
    </p>
    <label
      >复核决定
      <select
        v-model="control.draft.decision"
        :disabled="!control.canEdit()"
        aria-label="复核决定"
      >
        <option value="">请选择决定</option>
        <option value="confirm_candidate">确认候选（confirm_candidate）</option>
        <option value="reject_candidate">驳回候选（reject_candidate）</option>
        <option value="return_for_evidence">请求补证（return_for_evidence）</option>
        <option value="request_rerun">请求重算（request_rerun）</option>
      </select>
    </label>
    <label
      >复核理由
      <textarea
        v-model="control.draft.reason"
        :disabled="!control.canEdit()"
        aria-label="复核理由"
        autocomplete="off"
      />
    </label>
    <label
      >关联证据编号
      <textarea
        v-model="control.draft.evidenceIds"
        :disabled="!control.canEdit()"
        aria-label="关联证据编号"
        autocomplete="off"
      />
    </label>
    <p class="muted">
      至少填写一个完整UUID，多个编号以逗号或空白分隔，不得重复；不是新增证据或服务端标注。
    </p>
    <label
      ><input
        v-model="control.draft.confirmed"
        type="checkbox"
        :disabled="!control.canEdit()"
        aria-label="确认本次复核内容"
      />确认本次复核内容</label
    >
    <div class="toolbar">
      <button
        :disabled="!control.canSubmit()"
        @click="control.submit"
      >
        提交受控复核
      </button>
      <button
        class="secondary"
        :disabled="control.state.busy || !control.state.uncertain"
        @click="control.retry"
      >
        原请求重试
      </button>
      <button
        class="secondary"
        :disabled="!control.canEdit()"
        @click="control.clearDraft"
      >
        清空本页草稿
      </button>
    </div>
    <p
      class="notice"
      role="status"
      data-testid="review-submit-status"
    >
      {{
        control.state.busy
          ? '正在提交原定复核内容…'
          : control.state.error ||
            control.state.message ||
            (!control.canEdit()
              ? '当前身份、案件或写入条件不足，请重新读取当前上下文；只读记录仍可查看。'
              : !control.canSubmit()
                ? '请填写决定、1至4096字理由、不重复的证据编号并确认；缺少服务端强ETag时不可提交。'
                : '本页草稿尚未提交，不是正式批准。')
      }}
    </p>
    <p
      v-if="control.state.uncertain"
      class="notice"
    >
      请求结果尚未确认；只允许原请求重试。请勿另建相同复核请求。
    </p>
    <p
      v-if="control.state.stale"
      class="notice"
    >
      写入条件已失效，请重新读取当前复核上下文。
    </p>
    <dl
      v-if="control.state.receipt"
      data-testid="review-submit-receipt"
    >
      <dt>已追加复核编号</dt>
      <dd>{{ control.state.receipt.review_id }}</dd>
      <dt>记录人编号</dt>
      <dd>{{ control.state.receipt.reviewer_id }}</dd>
      <dt>任务／运行／结果</dt>
      <dd>
        {{ control.state.receipt.task_id }} / {{ control.state.receipt.run_version }} /
        {{ control.state.receipt.result_version }}
      </dd>
      <dt>策略／复核版本</dt>
      <dd>
        {{ control.state.receipt.policy_version }} / {{ control.state.receipt.review_version }}
      </dd>
      <dt>记录决定</dt>
      <dd>{{ control.state.receipt.decision }}</dd>
      <dt>记录理由</dt>
      <dd>{{ control.state.receipt.reason }}</dd>
    </dl>
  </section>
</template>
