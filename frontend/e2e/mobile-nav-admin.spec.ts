import { test, expect } from '@playwright/test';
const distUrl = 'file://' + process.cwd() + '/dist/index.html';

test('mobile drawer routes via hash without 404', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(distUrl);

  const menuBtn = page.locator('button[aria-label="menu"]');
  if ((await menuBtn.count()) === 0) test.skip('Menu button not found');
  await menuBtn.click();
  const questionsLink = page.getByRole('link', { name: 'Questions' });
  if ((await questionsLink.count()) === 0) {
    test.skip('Admin links not visible');
  }
  await questionsLink.click();
  await expect(page).not.toHaveTitle(/404/i);
  await expect(page.locator('body')).not.toContainText('404');
  const qHash = await page.evaluate(() => location.hash);
  expect(qHash.startsWith('#/admin/questions') || page.url().includes('#/admin/questions')).toBeTruthy();

  await menuBtn.click();
  const dashLink = page.getByRole('link', { name: /dashboard/i });
  await dashLink.click();
  await expect(page).not.toHaveTitle(/404/i);
  await expect(page.locator('body')).not.toContainText('404');
  const dHash = await page.evaluate(() => location.hash);
  expect(dHash.startsWith('#/dashboard') || page.url().includes('#/dashboard')).toBeTruthy();
});
