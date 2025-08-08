import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:4173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    // IMPORTANT: run preview from the frontend workspace
    // Option A (preferred): set cwd
    command: 'npm run preview -- --port 4173',
    url: 'http://localhost:4173',
    timeout: 60_000,
    reuseExistingServer: !process.env.CI,
    cwd: 'frontend',
    // Option B (alternative, if you’d rather not use cwd):
    // command: 'npm --prefix frontend run preview -- --port 4173',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
