import { defineConfig } from '@playwright/test'
export default defineConfig({
  captureGitInfo: { commit: true, diff: false },
  testDir: './e2e-stage-three',
  testMatch: '**/*.pw.ts',
  use: { baseURL: process.env.MT_DEMO_FRONTEND_URL, headless: true },
  reporter: [
    ['list'],
    ['json', { outputFile: '../docs/00-project/validation/stage-three-browser-report.json' }],
  ],
  retries: 0,
})
