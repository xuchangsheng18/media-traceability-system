import { defineConfig } from '@playwright/test'
import { fileURLToPath } from 'node:url'
export default defineConfig({
  captureGitInfo: { commit: true, diff: false },
  testDir: './e2e',
  testMatch: '**/*.pw.ts',
  timeout: 90000,
  workers: 1,
  reporter: [
    ['list'],
    [
      'json',
      {
        outputFile: fileURLToPath(
          new URL('../docs/00-project/validation/poc-browser-report.json', import.meta.url),
        ),
      },
    ],
  ],
  use: {
    baseURL: 'http://127.0.0.1:14180',
    headless: true,
    viewport: { width: 1280, height: 1000 },
  },
})
