import { reactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, uuid, type Schemas } from './api'
import { validateReviewContext, validateReviewRecord } from './review-read'
import type { BusinessSession } from './session'

type Session = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
export type ReviewSubmissionSelection = {
  caseId: string
  taskId: string
  context: Schemas['ReviewContext'] | null
  etag: string | null
}
type Intent = {
  body: Readonly<Schemas['ReviewCreate']>
  key: string
  etag: string
  identity: string
  source: string
  reviewer: string
}
const decisions = [
  'confirm_candidate',
  'reject_candidate',
  'return_for_evidence',
  'request_rerun',
] as const

/** Page-memory intent only. This is neither a server draft nor an approval provider. */
export function createReviewSubmitter(
  session: Session,
  selection: () => ReviewSubmissionSelection,
) {
  const draft = reactive({ decision: '', reason: '', evidenceIds: '', confirmed: false })
  const state = reactive({
    busy: false,
    error: '',
    message: '',
    uncertain: false,
    stale: false,
    receipt: null as Schemas['Review'] | null,
  })
  let intent: Intent | null = null
  let generation = 0
  let disposed = false
  function identity() {
    const user = session.state.user
    return JSON.stringify([
      session.state.generation,
      user?.user_id,
      user?.org_id,
      user?.roles,
      user?.permissions,
      user?.case_ids,
      session.has('review.read'),
      session.has('review.perform'),
    ])
  }
  function source() {
    const value = selection()
    return JSON.stringify([value.caseId, value.taskId, value.context, value.etag])
  }
  function reset() {
    generation++
    intent = null
    Object.assign(draft, { decision: '', reason: '', evidenceIds: '', confirmed: false })
    Object.assign(state, {
      busy: false,
      error: '',
      message: '',
      uncertain: false,
      stale: false,
      receipt: null,
    })
  }
  function permitted() {
    const value = selection()
    return (
      !!session.state.user &&
      session.has('review.read') &&
      session.has('review.perform') &&
      session.state.user.case_ids.some((id) => id.toLowerCase() === value.caseId.toLowerCase())
    )
  }
  function canEdit() {
    return (
      !disposed &&
      permitted() &&
      !!selection().context &&
      !state.busy &&
      !intent &&
      !state.receipt &&
      !state.stale
    )
  }
  function condition() {
    if (!permitted()) throw new FormError('当前身份、复核执行权限或案件范围不足。')
    const value = selection()
    uuid(value.caseId)
    const task = uuid(value.taskId).toLowerCase()
    const context = validateReviewContext(value.context, task)
    if (!value.etag || !/^"[\x21\x23-\x7e]{1,126}"$/.test(value.etag))
      throw new FormError('缺少服务端强ETag，当前上下文只能读取；请重新读取后提交。')
    return { context, etag: value.etag }
  }
  function canSubmit() {
    if (!canEdit()) return false
    try {
      const binding = condition()
      validateDraft()
      return Number.isSafeInteger(binding.context.review_version + 1)
    } catch {
      return false
    }
  }
  function validateDraft() {
    if (!draft.confirmed) throw new FormError('请先确认本次复核内容；确认仅防误操作，不代替审批。')
    if (!decisions.includes(draft.decision as (typeof decisions)[number]))
      throw new FormError('请选择契约允许的复核决定。')
    const reason = draft.reason.trim()
    if (!reason || [...reason].length > 4096) throw new FormError('请填写1至4096字的复核理由。')
    const evidence = draft.evidenceIds
      .trim()
      .split(/[\s,，;；]+/)
      .filter(Boolean)
      .map((id) => uuid(id).toLowerCase())
    if (!evidence.length || new Set(evidence).size !== evidence.length)
      throw new FormError('请填写至少一条不重复的完整证据编号。')
    return { reason, evidence }
  }
  function clearDraft() {
    if (canEdit()) {
      Object.assign(draft, { decision: '', reason: '', evidenceIds: '', confirmed: false })
      state.error = ''
    }
  }
  function current(version: number, request: Intent) {
    return (
      !disposed &&
      generation === version &&
      request.identity === identity() &&
      request.source === source()
    )
  }
  function validateReceipt(value: unknown, request: Intent) {
    const data = validateReviewRecord(value, request.body.task_id)
    const original = request.body
    if (
      data.reviewer_id.toLowerCase() !== request.reviewer ||
      data.run_version !== original.run_version ||
      data.result_version !== original.result_version ||
      data.policy_version !== original.policy_version ||
      data.expected_review_version !== original.expected_review_version ||
      data.review_version !== original.expected_review_version + 1 ||
      data.decision !== original.decision ||
      data.reason !== original.reason ||
      JSON.stringify(data.evidence_ids.map((id) => id.toLowerCase()).sort()) !==
        JSON.stringify([...original.evidence_ids].sort())
    )
      throw new FormError('复核回执与原请求不一致，结果尚未确认；只能重试原请求。')
    return data
  }
  async function send(request: Intent) {
    const version = generation
    if (!current(version, request) || !permitted()) return
    const wasUncertain = state.uncertain
    state.busy = true
    state.error = ''
    try {
      const { data } = await session.call<Schemas['Review']>(
        '/reviews',
        request.body,
        request.key,
        request.etag,
      )
      if (!current(version, request)) return
      const receipt = validateReceipt(data, request)
      state.receipt = receipt
      state.uncertain = false
      intent = null
      state.message =
        '服务端已确认追加复核记录；不表示批准、已完成退回或重算已开始。新记录请重新读取当前上下文。'
    } catch (error) {
      if (!current(version, request)) return
      state.error = errorMessage(error)
      const definitive =
        error instanceof ApiError &&
        error.status >= 400 &&
        error.status < 500 &&
        ![408, 429].includes(error.status)
      // A retry refusal cannot prove whether the first uncertain write committed.
      if (definitive && !wasUncertain) {
        intent = null
        state.stale = true
        state.uncertain = false
        state.message = '原写入条件已失效；请重新读取当前上下文，再填写新的复核内容。'
      } else {
        state.uncertain = true
        state.message = '请求结果尚未确认；输入已锁定，只能使用原始内容、幂等键和条件手动重试。'
      }
    } finally {
      if (current(version, request)) state.busy = false
    }
  }
  async function submit() {
    if (disposed || state.busy || intent || state.receipt || state.stale) return
    state.error = ''
    try {
      const binding = condition()
      const { reason, evidence } = validateDraft()
      const context = binding.context
      if (!Number.isSafeInteger(context.review_version + 1))
        throw new FormError('复核版本超出安全整数范围，已拒绝提交。')
      const body: Schemas['ReviewCreate'] = {
        task_id: context.task_id.toLowerCase(),
        run_version: context.run_version,
        result_version: context.result_version,
        expected_review_version: context.review_version,
        policy_version: context.policy_version,
        decision: draft.decision as Schemas['ReviewCreate']['decision'],
        reason,
        evidence_ids: evidence,
      }
      Object.freeze(body.evidence_ids)
      intent = Object.freeze({
        body: Object.freeze(body),
        key: crypto.randomUUID(),
        etag: binding.etag,
        identity: identity(),
        source: source(),
        reviewer: uuid(session.state.user!.user_id).toLowerCase(),
      })
      await send(intent)
    } catch (error) {
      if (!disposed) state.error = errorMessage(error)
    }
  }
  async function retry() {
    if (!disposed && !state.busy && state.uncertain && intent) await send(intent)
  }
  const stops = [watch(identity, reset, { flush: 'sync' }), watch(source, reset, { flush: 'sync' })]
  function dispose() {
    disposed = true
    stops.forEach((stop) => stop())
    reset()
  }
  return { draft, state, canEdit, canSubmit, submit, retry, clearDraft, dispose }
}
