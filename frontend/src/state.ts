import { inject, reactive, type InjectionKey } from 'vue'
import { request } from './api'

export function createDevelopmentState() {
  const state = reactive({
    token: '',
    state: '等待上传',
    result: '',
    busy: false,
    health: 'unknown',
    healthMessage: '尚未检查',
    checking: false,
  })
  async function checkHealth() {
    if (state.checking) return
    state.checking = true
    try {
      const response = await request('/api/v1/health', state.token)
      if (response?.status !== 'ok' && response?.status !== 'unavailable')
        throw new Error('HEALTH_RESPONSE_INVALID')
      state.health = response.status === 'ok' ? 'ready' : 'unavailable'
      state.healthMessage = response.status === 'ok' ? '服务可用' : '依赖暂不可用'
    } catch {
      state.health = 'error'
      state.healthMessage = '检查失败，请检查服务连接或访问权限。'
    } finally {
      state.checking = false
    }
  }
  return { state, checkHealth }
}

type DevelopmentState = ReturnType<typeof createDevelopmentState>
export const developmentStateKey: InjectionKey<DevelopmentState> = Symbol('development-state')
export function useDevelopmentState(): DevelopmentState {
  const value = inject(developmentStateKey)
  if (!value) throw new Error('APP_STATE_PROVIDER_MISSING')
  return value
}
