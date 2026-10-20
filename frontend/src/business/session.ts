import { inject, reactive, type InjectionKey } from 'vue'
import { ApiError } from '../api'
import { BusinessClient, errorMessage, type Schemas } from './api'

export function createBusinessSession() {
  const client = new BusinessClient()
  const state = reactive({
    user: null as Schemas['CurrentUser'] | null,
    generation: 0,
    busy: false,
    message: '尚未连接业务身份',
  })
  function disconnect() {
    client.replaceToken('')
    state.user = null
    state.generation++
    state.busy = false
    state.message = '已清除本页业务身份与结果'
  }
  async function call<T>(...args: Parameters<typeof client.call<T>>) {
    try {
      return await client.call<T>(...args)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) disconnect()
      throw error
    }
  }
  async function connect(token: string) {
    disconnect()
    const version = state.generation
    state.busy = true
    try {
      client.replaceToken(token)
      const { data } = await client.call<Schemas['CurrentUser']>('/auth/me')
      if (
        !data ||
        typeof data.user_id !== 'string' ||
        typeof data.org_id !== 'string' ||
        !Array.isArray(data.permissions) ||
        !Array.isArray(data.roles) ||
        !Array.isArray(data.case_ids)
      )
        throw new Error('CURRENT_USER_RESPONSE_INVALID')
      if (version !== state.generation) return
      state.user = data
      state.message = '业务身份已连接；具体操作仍由服务端逐次授权'
    } catch (error) {
      if (version === state.generation) {
        disconnect()
        state.message = errorMessage(error)
      }
    } finally {
      if (version === state.generation) state.busy = false
    }
  }
  function has(permission: string) {
    return state.user?.permissions.includes(permission) ?? false
  }
  return { state, connect, disconnect, has, call }
}
export type BusinessSession = ReturnType<typeof createBusinessSession>
export const businessSessionKey: InjectionKey<BusinessSession> = Symbol('business-session')
export function useBusinessSession(): BusinessSession {
  const value = inject(businessSessionKey)
  if (!value) throw new Error('BUSINESS_SESSION_PROVIDER_MISSING')
  return value
}
