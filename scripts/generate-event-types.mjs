import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { tmpdir } from 'node:os'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const temporaryRoot = resolve(tmpdir())
const folder = mkdtempSync(join(temporaryRoot, 'mt-event-types-'))
try {
  const schema = JSON.parse(readFileSync(join(root, 'schemas/events/poc.analysis.requested.v1.schema.json'), 'utf8'))
  delete schema.$id
  delete schema.$schema
  const wrapper = { openapi: '3.1.0', info: { title: 'Generated development event wrapper', version: '1.0.0' }, paths: {}, components: { schemas: { PocAnalysisRequestedEvent: schema } } }
  const path = join(folder, 'event-openapi.json')
  writeFileSync(path, JSON.stringify(wrapper))
  execFileSync(process.execPath, [join(root, 'frontend/node_modules/openapi-typescript/bin/cli.js'), path, '-o', join(root, 'shared-contracts/generated/poc-event.d.ts')], { stdio: 'inherit' })
} finally {
  if (dirname(resolve(folder)) !== temporaryRoot || !basename(folder).startsWith('mt-event-types-')) {
    throw new Error('Unexpected event generation scratch directory')
  }
  rmSync(folder, { recursive: true, force: true })
}
