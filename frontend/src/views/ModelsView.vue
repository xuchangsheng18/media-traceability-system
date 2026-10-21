<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { createModelsReader } from '../business/models'
import { useBusinessSession } from '../business/session'

const session = useBusinessSession()
const catalog = createModelsReader(session)
const modelLimit = ref(20)
const evaluationLimit = ref(20)
const metrics = [
  { key: 'macro_f1', label: 'Macro F1' },
  { key: 'recall', label: 'Recall' },
  { key: 'iou', label: 'IoU' },
  { key: 'recall_at_k', label: 'Recall@K' },
  { key: 'ece', label: 'ECE' },
  { key: 'boundary_mae_ms', label: '边界 MAE（毫秒）' },
] as const

watch(modelLimit, catalog.models.clear, { flush: 'sync' })
watch(evaluationLimit, catalog.evaluations.clear, { flush: 'sync' })
onBeforeUnmount(catalog.dispose)
</script>

<template>
  <div class="view-grid">
    <section class="panel span-12">
      <h2 class="panel-heading">当前单位模型目录</h2>
      <p class="panel-copy">
        按当前业务身份对应的单位分页查询，具体可见范围由服务端逐条核验。模型登记状态与运行健康分别管理。
      </p>
      <p
        v-if="!session.state.user"
        class="notice"
        role="status"
      >
        请先在业务身份页连接身份。
      </p>
      <p
        v-else-if="!session.has('model.read')"
        class="notice"
        role="status"
      >
        当前身份没有模型目录读取权限。
      </p>
      <p
        v-else
        class="notice"
      >
        当前单位：{{ session.state.user.org_id }}
      </p>
      <div class="toolbar">
        <label>
          每页模型条数
          <select
            v-model="modelLimit"
            aria-label="模型每页条数"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </label>
        <button
          :disabled="catalog.models.state.busy || !session.has('model.read')"
          @click="catalog.models.load(modelLimit)"
        >
          查询模型／回到首页
        </button>
        <button
          class="secondary"
          :disabled="
            catalog.models.state.busy ||
            !catalog.models.state.data?.next_cursor ||
            !session.has('model.read')
          "
          @click="catalog.models.next()"
        >
          下一页模型
        </button>
      </div>
      <p
        v-if="catalog.models.state.busy"
        class="notice"
        role="status"
      >
        正在读取模型目录…
      </p>
      <p
        v-else-if="catalog.models.state.error"
        class="notice"
        role="status"
      >
        {{ catalog.models.state.error }} 分页失败后请重新查询首页。
      </p>
      <p
        v-else-if="catalog.models.state.loaded"
        class="notice"
        role="status"
      >
        模型第 {{ catalog.models.state.pageNumber }} 页，返回
        {{ catalog.models.state.data?.items.length ?? 0 }} 条。
      </p>
      <p
        v-else
        class="empty-state"
      >
        点击查询，读取当前身份可见的模型登记记录。
      </p>
      <div
        v-if="catalog.models.state.data?.items.length"
        class="table-scroll"
      >
        <table>
          <thead>
            <tr>
              <th>名称／模型编号</th>
              <th>模型版本</th>
              <th>能力</th>
              <th>登记状态</th>
              <th>后端</th>
              <th>资料与固定版本</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in catalog.models.state.data.items"
              :key="item.model_id"
            >
              <td>{{ item.name }}<br />{{ item.model_id }}</td>
              <td>{{ item.version }}</td>
              <td>{{ item.capability }}</td>
              <td>{{ item.status }}</td>
              <td>{{ item.backend }}</td>
              <td>
                <details>
                  <summary>查看模型资料</summary>
                  <dl>
                    <dt>模型包摘要</dt>
                    <dd>{{ item.digest }}</dd>
                    <dt>数据集版本</dt>
                    <dd>{{ item.dataset_version }}</dd>
                    <dt>模型卡引用</dt>
                    <dd>{{ item.model_card_ref }}</dd>
                    <dt>许可记录引用</dt>
                    <dd>{{ item.license_record_ref }}</dd>
                    <dt>环境引用</dt>
                    <dd>{{ item.environment_ref }}</dd>
                    <dt>记录版本</dt>
                    <dd>{{ item.row_version }}</dd>
                  </dl>
                </details>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p
        v-if="catalog.models.state.loaded && !catalog.models.state.data?.items.length"
        class="empty-state"
      >
        当前页没有可见模型记录；这不表示单位内没有其他模型。
      </p>
    </section>

    <section class="panel span-12">
      <h2 class="panel-heading">已登记评测元数据</h2>
      <p class="panel-copy">
        单独分页读取当前身份可见的评测记录，模型编号用于关联。指标按返回值展示；未提供的指标保持未知。
      </p>
      <div class="toolbar">
        <label>
          每页评测条数
          <select
            v-model="evaluationLimit"
            aria-label="评测每页条数"
          >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </label>
        <button
          :disabled="catalog.evaluations.state.busy || !session.has('model.read')"
          @click="catalog.evaluations.load(evaluationLimit)"
        >
          查询评测／回到首页
        </button>
        <button
          class="secondary"
          :disabled="
            catalog.evaluations.state.busy ||
            !catalog.evaluations.state.data?.next_cursor ||
            !session.has('model.read')
          "
          @click="catalog.evaluations.next()"
        >
          下一页评测
        </button>
      </div>
      <p
        v-if="catalog.evaluations.state.busy"
        class="notice"
        role="status"
      >
        正在读取评测元数据…
      </p>
      <p
        v-else-if="catalog.evaluations.state.error"
        class="notice"
        role="status"
      >
        {{ catalog.evaluations.state.error }} 分页失败后请重新查询首页。
      </p>
      <p
        v-else-if="catalog.evaluations.state.loaded"
        class="notice"
        role="status"
      >
        评测第 {{ catalog.evaluations.state.pageNumber }} 页，返回
        {{ catalog.evaluations.state.data?.items.length ?? 0 }} 条。
      </p>
      <p
        v-else
        class="empty-state"
      >
        点击查询，读取可用的评测记录。
      </p>
      <div
        v-if="catalog.evaluations.state.data?.items.length"
        class="table-scroll"
      >
        <table>
          <thead>
            <tr>
              <th>评测编号／模型编号</th>
              <th>数据集／版本</th>
              <th>协议／划分</th>
              <th>样本数／失败数</th>
              <th>指标</th>
              <th>评测产物</th>
              <th>记录时间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in catalog.evaluations.state.data.items"
              :key="item.evaluation_id"
            >
              <td>{{ item.evaluation_id }}<br />{{ item.model_id }}</td>
              <td>{{ item.dataset_id }} / {{ item.dataset_version }}</td>
              <td>{{ item.protocol_id }} / {{ item.split }}</td>
              <td>{{ item.sample_count }} / {{ item.failure_count }}</td>
              <td>
                <details>
                  <summary>查看评测指标</summary>
                  <dl>
                    <template
                      v-for="metric in metrics"
                      :key="metric.key"
                    >
                      <dt>{{ metric.label }}</dt>
                      <dd>{{ item.metrics[metric.key] ?? '未提供' }}</dd>
                    </template>
                  </dl>
                </details>
              </td>
              <td>
                <details>
                  <summary>查看产物引用</summary>
                  <dl>
                    <dt>对象编号</dt>
                    <dd>{{ item.artifact_ref.object_id }}</dd>
                    <dt>固定版本</dt>
                    <dd>{{ item.artifact_ref.version_id }}</dd>
                    <dt>SHA-256</dt>
                    <dd>{{ item.artifact_ref.sha256 }}</dd>
                  </dl>
                </details>
              </td>
              <td>{{ item.created_at }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p
        v-if="catalog.evaluations.state.loaded && !catalog.evaluations.state.data?.items.length"
        class="empty-state"
      >
        当前页没有可见评测记录；这不表示模型从未评测。
      </p>
      <p class="panel-copy">
        模型卡、许可、环境与评测产物以受控引用展示。模型健康、灰度发布、漂移与回滚信息尚未接入本页。
      </p>
    </section>
  </div>
</template>

<style scoped>
summary {
  cursor: pointer;
  white-space: nowrap;
}
td {
  overflow-wrap: anywhere;
}
details dl {
  min-width: 290px;
}
</style>
