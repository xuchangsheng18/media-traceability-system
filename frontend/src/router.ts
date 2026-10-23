import { createRouter, createWebHashHistory, type RouterHistory } from 'vue-router'
import UploadView from './views/UploadView.vue'
import HealthView from './views/HealthView.vue'
import NotFoundView from './views/NotFoundView.vue'
import BusinessView from './views/BusinessView.vue'
import ApprovalsView from './views/ApprovalsView.vue'
import AuditView from './views/AuditView.vue'
import TasksView from './views/TasksView.vue'
import PendingReviewsView from './views/PendingReviewsView.vue'
import AssetsView from './views/AssetsView.vue'
import ModelsView from './views/ModelsView.vue'
import SourcesView from './views/SourcesView.vue'
import BusinessUploadsView from './views/BusinessUploadsView.vue'

export function createAppRouter(history: RouterHistory = createWebHashHistory()) {
  return createRouter({
    history,
    routes: [
      { path: '/', name: 'upload', component: UploadView },
      { path: '/health', name: 'health', component: HealthView },
      { path: '/business', name: 'business', component: BusinessView },
      { path: '/business/uploads', name: 'business-uploads', component: BusinessUploadsView },
      { path: '/approvals', name: 'approvals', component: ApprovalsView },
      { path: '/audit', name: 'audit', component: AuditView },
      { path: '/tasks', name: 'tasks', component: TasksView },
      { path: '/assets', name: 'assets', component: AssetsView },
      { path: '/models', name: 'models', component: ModelsView },
      { path: '/sources', name: 'sources', component: SourcesView },
      { path: '/reviews/pending', name: 'pending-reviews', component: PendingReviewsView },
      { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
    ],
  })
}
