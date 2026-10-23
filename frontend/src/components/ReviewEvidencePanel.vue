<script setup lang="ts">
import { computed, onBeforeUnmount } from 'vue'
import {
  createReviewEvidenceReader,
  type ReviewEvidenceSelection,
} from '../business/review-evidence'
import { createReviewEvidenceAsset } from '../business/review-evidence-asset'
import { useBusinessSession } from '../business/session'

const props = defineProps<{ selection: ReviewEvidenceSelection }>()
const session = useBusinessSession()
const reader = createReviewEvidenceReader(session, () => props.selection)
const selected = computed(reader.selected)
const items = computed(reader.visibleItems)
const missing = computed(reader.missingIds)
const original = createReviewEvidenceAsset(session, () => ({
  selection: props.selection,
  evidence: reader.selected(),
  loaded: reader.state.loaded,
  busy: reader.state.busy,
  page: reader.state.data,
}))
onBeforeUnmount(() => {
  original.dispose()
  reader.dispose()
})
</script>

<template>
  <section aria-label="所选版本证据只读定位">
    <h3>所选版本证据定位</h3>
    <p
      class="panel-copy"
      data-testid="review-evidence-binding"
    >
      案件：{{ selection.caseId }}；任务：{{ selection.taskId }}；运行／结果版本：{{
        selection.runVersion
      }}
      / {{ selection.resultVersion }}。
      {{
        selection.evidenceIds === null
          ? '来源：当前复核上下文。'
          : '来源：所选历史复核记录，仅显示其关联证据。'
      }}
      本地定位只显示本次已校验响应内的受控证据元数据，不证明内容、授权或审批有效。
    </p>
    <button
      :disabled="!reader.canLoad() || reader.state.busy"
      @click="reader.load()"
    >
      读取所选版本证据
    </button>
    <button
      class="secondary"
      :disabled="!reader.canLoad() || reader.state.busy || !reader.state.data?.next_cursor"
      @click="reader.load(true)"
    >
      下一页证据
    </button>
    <p
      class="notice"
      role="status"
      data-testid="review-evidence-status"
    >
      {{
        !reader.canLoad() && !reader.state.busy
          ? '当前身份、权限或案件范围不允许证据读取。'
          : reader.state.busy
            ? '正在读取所选版本证据…'
            : reader.state.error ||
              (reader.state.loaded ? '已校验本次证据元数据响应。' : '尚未读取所选版本证据。')
      }}
    </p>
    <p
      v-if="reader.state.loaded && !reader.state.error && !items.length"
      data-testid="review-evidence-empty"
    >
      本次响应中无可显示的所选证据。
    </p>
    <p
      v-if="reader.state.data?.next_cursor"
      class="notice"
      data-testid="review-evidence-incomplete"
    >
      当前为分页结果，未显示引用可继续查询；不自动续取，也不将本页缺失当作证据不存在。
    </p>
    <p
      v-if="missing.length"
      class="notice"
      data-testid="review-evidence-missing"
    >
      历史复核关联编号未在本次响应中找到：{{ missing.join('、') }}。这不证明全量证据中不存在。
    </p>
    <ul>
      <li
        v-for="item in items"
        :key="item.evidence_id"
        data-testid="review-evidence-item"
      >
        {{ item.evidence_id }}；类型：{{ item.kind }}
        <button
          class="secondary"
          @click="reader.locate(item.evidence_id)"
        >
          定位证据 {{ item.evidence_id }}
        </button>
      </li>
    </ul>
    <dl
      v-if="selected"
      data-testid="review-evidence-selected"
    >
      <dt>证据编号</dt>
      <dd>{{ selected.evidence_id }}</dd>
      <dt>案件编号</dt>
      <dd>{{ selected.case_id }}</dd>
      <dt>任务编号</dt>
      <dd>{{ selected.task_id }}</dd>
      <dt>运行版本</dt>
      <dd>{{ selected.run_version }}</dd>
      <dt>结果版本</dt>
      <dd>{{ selected.result_version }}</dd>
      <dt>证据类型</dt>
      <dd>{{ selected.kind }}</dd>
      <dt>资产编号</dt>
      <dd>{{ selected.asset_id }}</dd>
      <dt>受控对象引用</dt>
      <dd v-if="selected.object_ref">
        对象编号：{{ selected.object_ref.object_id }}；对象版本：{{
          selected.object_ref.version_id
        }}；对象SHA-256：{{ selected.object_ref.sha256 }}
      </dd>
      <dd v-else>未提供</dd>
      <dt>原件时间范围（毫秒，左闭右开）</dt>
      <dd>
        {{
          selected.time_range
            ? `[${selected.time_range.start_ms}, ${selected.time_range.end_ms})`
            : '未提供'
        }}
      </dd>
      <dt>原件归一化边界框（x、y、width、height）</dt>
      <dd>
        {{
          selected.bbox
            ? `${selected.bbox.x}、${selected.bbox.y}、${selected.bbox.width}、${selected.bbox.height}`
            : '未提供'
        }}
      </dd>
      <dt>映射版本</dt>
      <dd>{{ selected.mapping_version }}</dd>
      <dt>模型名称</dt>
      <dd>{{ selected.model_name ?? '未提供' }}</dd>
      <dt>模型版本</dt>
      <dd>{{ selected.model_version ?? '未提供' }}</dd>
      <dt>授权版本</dt>
      <dd>{{ selected.authorization_version }}</dd>
      <dt>证据SHA-256</dt>
      <dd>{{ selected.sha256 }}</dd>
      <dt>证据对象版本</dt>
      <dd>{{ selected.version }}</dd>
      <dt>创建时间</dt>
      <dd>{{ selected.created_at }}</dd>
    </dl>
    <section aria-label="证据关联原件">
      <h4>证据关联原件</h4>
      <p
        class="panel-copy"
        data-testid="review-evidence-asset-scope"
      >
        仅对所选原始类型证据显式读取资产详情；当前有效原始资产的案件、编号和固定对象版本、摘要均恰好匹配时才允许下载。
        缺少引用或版本不一致时不回退当前其他原件。本区域不提供媒体播放或派生证据内容，也不证明证据法律效力。
      </p>
      <button
        data-testid="review-evidence-asset-read"
        :disabled="!original.canLoad() || original.state.busy"
        @click="original.load()"
      >
        读取证据关联原件
      </button>
      <button
        class="secondary"
        data-testid="review-evidence-asset-download"
        :disabled="!original.canDownload()"
        @click="original.download()"
      >
        下载证据固定原件
      </button>
      <p
        class="notice"
        role="status"
        data-testid="review-evidence-asset-status"
      >
        {{
          original.state.busy
            ? '正在读取并核对所选原始证据的资产详情…'
            : original.state.error ||
              (original.state.loaded
                ? '已核对当前有效原件与所选证据的固定引用；下载仍须服务端逐次授权。'
                : '尚未核对原件；请先定位原始类型证据，并具备复核、证据和资产读取权限。')
        }}
      </p>
      <p
        class="notice"
        role="status"
        data-testid="review-evidence-download-status"
      >
        {{
          original.downloadState.busy
            ? '正在下载并核验原件字节…'
            : original.downloadState.error ||
              original.downloadState.message ||
              '下载另需资产下载权限；本页不以对象引用直接构造存储地址。'
        }}
      </p>
      <dl
        v-if="original.state.asset"
        data-testid="review-evidence-asset-data"
      >
        <dt>已绑定资产编号</dt>
        <dd>{{ original.state.asset.asset_id }}</dd>
        <dt>已绑定对象编号</dt>
        <dd>{{ original.state.asset.object_ref.object_id }}</dd>
        <dt>固定对象版本</dt>
        <dd>{{ original.state.asset.object_ref.version_id }}</dd>
        <dt>原件SHA-256</dt>
        <dd>{{ original.state.asset.object_ref.sha256 }}</dd>
        <dt>媒体格式／大小</dt>
        <dd>{{ original.state.asset.mime }}／{{ original.state.asset.size_bytes }} 字节</dd>
        <dt>资产状态／记录版本</dt>
        <dd>{{ original.state.asset.state }}／{{ original.state.asset.version }}</dd>
      </dl>
    </section>
  </section>
</template>
