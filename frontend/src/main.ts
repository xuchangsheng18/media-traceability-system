import { createApp } from 'vue'
import App from './App.vue'
import { createAppRouter } from './router'
import { createDevelopmentState, developmentStateKey } from './state'
createApp(App)
  .provide(developmentStateKey, createDevelopmentState())
  .use(createAppRouter())
  .mount('#app')
