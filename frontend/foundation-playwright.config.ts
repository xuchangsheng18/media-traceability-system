import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/foundation.pw.ts',
  workers: 1,
  timeout: 20000,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:14281',
    headless: true,
    launchOptions: process.env.MT_TEST_BROWSER_EXECUTABLE
      ? { executablePath: process.env.MT_TEST_BROWSER_EXECUTABLE }
      : {},
  },
  webServer: {
    command: 'npm run dev -- --port 14281 --strictPort',
    url: 'http://127.0.0.1:14281',
    reuseExistingServer: false,
  },
})
