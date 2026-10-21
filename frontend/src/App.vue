<script setup lang="ts">
import { computed, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { businessSessionKey, createBusinessSession } from './business/session'
import './styles/workbench.css'

const business = createBusinessSession()
provide(businessSessionKey, business)
const route = useRoute()
const menuOpen = ref(false)
const workspaceMain = ref<HTMLElement | null>(null)
watch(
  () => route.fullPath,
  () => {
    menuOpen.value = false
  },
)

const modules = [
  { label: '数据接入', to: '/', accessibleName: '上传验证' },
  { label: '资源库', to: '/assets', accessibleName: '媒体资产管理' },
  { label: '媒体预处理' },
  { label: '风险识别' },
  { label: '篡改检测' },
  { label: '图片检索' },
  { label: '视频溯源' },
  { label: '首发分析' },
  { label: '传播分析' },
  { label: '证据核查' },
  { label: '审核管理', to: '/reviews/pending', accessibleName: '待复核队列' },
  { label: '系统运维', to: '/health', accessibleName: '系统健康' },
]
const workbench = [
  { label: '任务与结果', to: '/tasks' },
  { label: '模型目录', to: '/models' },
  { label: '业务身份', to: '/business' },
  { label: '审批管理', to: '/approvals' },
  { label: '审计查询', to: '/audit' },
]
const pages: Record<string, { title: string; description: string }> = {
  upload: {
    title: '多源数据接入',
    description: '使用自建图片验证上传、原件保存、异步处理与CPU推理链路。',
  },
  health: {
    title: '综合管理与运维',
    description: '按需检查当前研发服务连接，查看实际返回的运行状态。',
  },
  business: {
    title: '身份与访问管理',
    description: '连接业务身份，核对角色、单位和可访问案件范围。',
  },
  approvals: {
    title: '审批与操作管理',
    description: '在授权案件内查询审批、读取当前版本并提交适用操作。',
  },
  audit: {
    title: '业务操作与审计追踪',
    description: '查询实际审计记录，按已批准范围申请导出和下载。',
  },
  tasks: {
    title: '任务运行与结果总览',
    description: '观察运行节点和事件，按精确版本查看分析结果与证据。',
  },
  assets: {
    title: '媒体资源与资产管理',
    description: '按案件查询可见媒体资产，核对来源编号、只读元数据与固定对象版本。',
  },
  models: {
    title: '模型与评测目录',
    description: '查看当前单位有权访问的模型版本、受控引用与已登记评测元数据。',
  },
  'pending-reviews': {
    title: '审核与证据管理',
    description: '按案件查看待复核任务，区分结果可用性与来源访问状态。',
  },
}
const page = computed(
  () => pages[String(route.name)] ?? { title: '页面导航', description: '请选择可用模块继续操作。' },
)
</script>

<template>
  <div class="application-shell">
    <a
      class="skip-link"
      href="#workspace-main"
      @click.prevent="workspaceMain?.focus()"
      >跳转到主要内容</a
    >
    <header class="app-topbar">
      <button
        class="menu-toggle"
        type="button"
        :aria-label="menuOpen ? '收起功能导航' : '展开功能导航'"
        :aria-expanded="menuOpen"
        aria-controls="application-sidebar"
        @click="menuOpen = !menuOpen"
      >
        <span aria-hidden="true">☰</span>
      </button>
      <h1>短视频与图片智能识别溯源系统</h1>
      <div class="topbar-account">
        <span class="environment-badge">内部研发</span>
        <RouterLink
          class="identity-link"
          to="/business"
          :aria-label="business.state.user ? '业务身份已连接' : '业务身份未连接'"
        >
          <span>{{ business.state.user ? '业务身份已连接' : '业务身份未连接' }}</span>
          <span
            class="account-avatar"
            aria-hidden="true"
            >{{ business.state.user ? '已' : '访' }}</span
          >
        </RouterLink>
      </div>
    </header>
    <div class="application-body">
      <aside
        id="application-sidebar"
        class="app-sidebar"
        :class="{ 'is-open': menuOpen }"
      >
        <nav aria-label="主导航">
          <p class="nav-group-title">功能模块</p>
          <template
            v-for="item in modules"
            :key="item.label"
          >
            <RouterLink
              v-if="item.to"
              class="module-link"
              :to="item.to"
              :aria-label="`${item.label}（${item.accessibleName}）`"
              ><span
                class="module-dot"
                aria-hidden="true"
              /><span>{{ item.label }}</span></RouterLink
            >
            <button
              v-else
              class="module-link module-unavailable"
              type="button"
              disabled
              :aria-label="`${item.label} 暂未接入`"
              title="页面尚未接入，相关分析结果可在任务与结果中按实际权限读取"
            >
              <span
                class="module-dot"
                aria-hidden="true"
              /><span>{{ item.label }}</span
              ><small>待接入</small>
            </button>
          </template>
          <p class="nav-group-title nav-divider">研发工作台</p>
          <RouterLink
            v-for="item in workbench"
            :key="item.to"
            class="module-link"
            :to="item.to"
          >
            <span
              class="module-dot"
              aria-hidden="true"
            /><span>{{ item.label }}</span>
          </RouterLink>
        </nav>
        <p class="sidebar-footnote">Linux研发环境<br />py310 · CPU</p>
      </aside>
      <main
        id="workspace-main"
        ref="workspaceMain"
        class="workspace-main"
        tabindex="-1"
      >
        <div class="page-masthead">
          <div>
            <h2>{{ page.title }}</h2>
            <p>{{ page.description }}</p>
          </div>
          <span class="page-environment">仅限内部研发</span>
        </div>
        <div class="workspace-view"><RouterView :key="business.state.generation" /></div>
        <footer class="workspace-footer">
          当前页面展示实际接口返回；合成CPU链路结果不用于业务研判。
        </footer>
      </main>
    </div>
  </div>
</template>
