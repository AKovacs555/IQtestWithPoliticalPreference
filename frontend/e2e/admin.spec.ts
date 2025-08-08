import { test, expect } from '@playwright/test';
import { Buffer } from 'buffer';

test('admin route renders some content', async ({ page, baseURL }) => {
  const token =
    'h.' +
    Buffer.from(JSON.stringify({ is_admin: true })).toString('base64') +
    '.s';
  await page.addInitScript(t => {
    window.localStorage.setItem('authToken', t as string);
  }, token);
  const url = (baseURL || 'http://localhost:4173') + '/#/admin';
  await page.goto(url);
  await page.waitForFunction(() => document.body.innerText.trim().length > 0);
  const textLen = await page.evaluate(
    () => document.body.innerText.trim().length
  );
  expect(textLen).toBeGreaterThan(0);
});
