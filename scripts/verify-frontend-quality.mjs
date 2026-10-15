// Exercise the same tools as CI with disposable, self-owned invalid source.
import { spawnSync } from 'node:child_process'
import { randomUUID } from 'node:crypto'
import { existsSync, unlinkSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const frontend = join(root, 'frontend')
const probe = join(frontend, 'src', `__quality_probe_${randomUUID().replaceAll('-', '')}.ts`)
const checks = [
  ['lint', 'eslint/bin/eslint.js', ['src', 'e2e', '*.ts', '*.mjs', '--max-warnings=0'],
    'const unusedProbe = 1\nexport {}\n', /no-unused-vars/],
  ['format', 'prettier/bin/prettier.cjs', ['--check', 'src/**/*.{ts,vue}', 'e2e/**/*.ts', '*.{ts,mjs,json,html}'],
    'export const formatProbe={value:1};\n', /Code style issues/],
  ['types', 'vue-tsc/bin/vue-tsc.js', ['--noEmit'],
    "export const typeProbe: number = 'self-owned-invalid-type'\n", /TS2322/],
]
const results = []
let status = 'FAIL'
try {
  for (const [name, tool, args, content, diagnostic] of checks) {
    const executable = join(frontend, 'node_modules', tool)
    if (!existsSync(executable)) throw new Error('REQUIRED_FRONTEND_TOOL_MISSING')
    const run = () => spawnSync(process.execPath, [executable, ...args], {
      cwd: frontend, encoding: 'utf8', timeout: 120000, maxBuffer: 1024 * 1024,
    })
    const baseline = run()
    if (baseline.error || baseline.status !== 0) throw new Error('BASELINE_FRONTEND_CHECK_FAILED')
    writeFileSync(probe, content, { flag: 'wx' })
    const invalid = run()
    unlinkSync(probe)
    const rejected = !invalid.error && invalid.status !== null && invalid.status !== 0 &&
      diagnostic.test((invalid.stdout ?? '') + (invalid.stderr ?? ''))
    results.push({ name, baseline_exit: baseline.status, invalid_exit: invalid.status, rejected })
    if (!rejected) throw new Error('INVALID_FRONTEND_SOURCE_NOT_REJECTED')
  }
  // The process wrapper also fails closed when its required executable is missing.
  const missing = spawnSync(join(frontend, '__missing_quality_executable__'), [], { cwd: frontend })
  if (missing.error?.code !== 'ENOENT' || missing.status === 0) throw new Error('MISSING_TOOL_NOT_REJECTED')
  results.push({ name: 'missing_executable', rejected: true })
  status = 'PASS'
} finally {
  if (existsSync(probe)) unlinkSync(probe)
  const report = { status, checks: results, disposable_probe_removed: !existsSync(probe),
    scope: 'frontend_lint_format_types_negative_checks_no_business_acceptance' }
  writeFileSync(join(root, 'docs/00-project/validation/frontend-quality-report.json'), JSON.stringify(report, null, 2) + '\n')
  process.stdout.write(JSON.stringify(report) + '\n')
}
