import { test, expect } from '@playwright/test';
import path from 'path';

const distPath = path.resolve(__dirname, '../frontend/dist/index.html');

// Ensure admin page renders some content in the built app
// This guards against blank screens if the admin chunk fails to load

test('admin route is not blank', async ({ page }) => {
  await page.goto('file://' + distPath + '#/admin');
  const body = await page.evaluate(() => document.body.innerText.trim().length);
  expect(body).toBeGreaterThan(0);
});
