import { createRouter, createWebHashHistory, type RouterHistory } from 'vue-router'
import UploadView from './views/UploadView.vue'
import HealthView from './views/HealthView.vue'
import NotFoundView from './views/NotFoundView.vue'
import BusinessView from './views/BusinessView.vue'
import ApprovalsView from './views/ApprovalsView.vue'
import AuditView from './views/AuditView.vue'

export function createAppRouter(history: RouterHistory = createWebHashHistory()) {
  return createRouter({
    history,
    routes: [
      { path: '/', name: 'upload', component: UploadView },
      { path: '/health', name: 'health', component: HealthView },
      { path: '/business', name: 'business', component: BusinessView },
      { path: '/approvals', name: 'approvals', component: ApprovalsView },
      { path: '/audit', name: 'audit', component: AuditView },
      { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
    ],
  })
}
