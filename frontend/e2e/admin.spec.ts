import { test, expect } from '@playwright/test';

test('admin route renders some content', async ({ page, baseURL }) => {
  const url = (baseURL || 'http://localhost:4173') + '/#/admin';
  await page.goto(url);
  await page.waitForFunction(() => document.body.innerText.trim().length > 0);
  const textLen = await page.evaluate(() => document.body.innerText.trim().length);
  expect(textLen).toBeGreaterThan(0);
});
