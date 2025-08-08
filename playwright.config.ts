import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Discover tests from the repository root's e2e directory.
  testDir: './e2e',

  // Keep the config minimal and CI-friendly.
  timeout: 30 * 1000,
  expect: { timeout: 5 * 1000 },

  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',

  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // If your tests rely on a running site, set baseURL here or via env:
    // baseURL: process.env.E2E_BASE_URL || 'http://localhost:4173',
  },

  // (Optional) If the app needs to be served locally for the tests, uncomment:
  // webServer: {
  //   command: 'npm run preview -- --port 4173',
  //   url: 'http://localhost:4173',
  //   timeout: 60_000,
  //   reuseExistingServer: !process.env.CI,
  // },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    // Add firefox/webkit here if needed.
  ],
});
