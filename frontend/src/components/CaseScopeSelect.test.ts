import { h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { expect, test } from 'vitest'
import CaseScopeSelect from './CaseScopeSelect.vue'

const first = '11111111-1111-1111-1111-111111111111'
const second = '22222222-2222-2222-2222-222222222222'
async function render(modelValue = '', caseIds = [first], disabled = false) {
  const emitted: string[] = []
  const html = await renderToString(
    h(CaseScopeSelect, {
      modelValue,
      caseIds,
      disabled,
      'onUpdate:modelValue': (value: string) => emitted.push(value),
    }),
  )
  return { html, emitted }
}

test('renders only distinct existing valid UUIDs and an empty accessible choice without auto-selection', async () => {
  const { html, emitted } = await render('', [first, 'invalid', second, first])
  expect(html.match(/<option /g)).toHaveLength(3)
  expect(html).toContain('value=""')
  expect(html).toContain(`value="${first}"`)
  expect(html).toContain(`value="${second}"`)
  expect(html).toContain('aria-label="上传案件"')
  expect(html).toContain('<label>')
  expect(html).not.toContain('invalid')
  expect(html).not.toContain('<input')
  expect(emitted).toEqual([])
})

test('clears an initial selection outside current cases and renders no stale selection', async () => {
  const { html, emitted } = await render(second)
  expect(emitted).toEqual([''])
  expect(html).not.toContain(second)
})

test('busy disabling preserves an existing selection', async () => {
  const { html, emitted } = await render(first, [first], true)
  expect(html).toContain('disabled')
  expect(html).toContain(`value="${first}" disabled`)
  expect(emitted).toEqual([])
})

test('no valid cases disables selection and explains identity or case availability', async () => {
  const { html, emitted } = await render('', ['invalid'])
  expect(html).toContain('disabled')
  expect(html).toContain('连接业务身份')
  expect(html).toContain('无可用案件')
  expect(html.match(/<option /g)).toHaveLength(1)
  expect(emitted).toEqual([])
})
