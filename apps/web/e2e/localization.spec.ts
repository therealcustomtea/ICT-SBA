import { expect, test } from '@playwright/test';

test('switches from English to Traditional Chinese', async ({ page }) => {
  await page.goto('/en');
  await page.getByRole('link', { name: 'Switch language' }).click();
  await expect(page).toHaveURL(/\/zh-Hant/);
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hant');
});

test('server HTML declares the requested document language', async ({ request }) => {
  const response = await request.get('/zh-Hant');
  expect(response.ok()).toBe(true);
  expect(await response.text()).toMatch(/<html[^>]+lang="zh-Hant"/);
});

test('private routes send a no-index directive', async ({ request }) => {
  for (const path of [
    '/en/rooms',
    '/en/challenges/example',
    '/en/play/example',
    '/zh-Hant/account',
    '/en/admin',
  ]) {
    const response = await request.get(path);
    expect(response.headers()['x-robots-tag'], path).toContain('noindex');
  }

  const publicResponse = await request.get('/en/play');
  expect(publicResponse.headers()['x-robots-tag']).toBeUndefined();
});
