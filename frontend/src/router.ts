import { createRouter, createWebHashHistory, type RouterHistory } from 'vue-router'
import UploadView from './views/UploadView.vue'
import HealthView from './views/HealthView.vue'
import NotFoundView from './views/NotFoundView.vue'

export function createAppRouter(history: RouterHistory = createWebHashHistory()) {
  return createRouter({
    history,
    routes: [
      { path: '/', name: 'upload', component: UploadView },
      { path: '/health', name: 'health', component: HealthView },
      { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
    ],
  })
}
