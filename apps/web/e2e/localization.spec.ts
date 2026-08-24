// Imports the dependency used by this module.
import { expect, test } from '@playwright/test';

// Calls test with the supplied values.
test('switches from English to Traditional Chinese', async ({ page }) => {
  // Waits for this asynchronous operation to complete.
  await page.goto('/en');
  // Waits for this asynchronous operation to complete.
  await page.getByRole('link', { name: 'Switch language' }).click();
  // Waits for this asynchronous operation to complete.
  await expect(page).toHaveURL(/\/zh-Hant/);
  // Waits for this asynchronous operation to complete.
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hant');
  // Closes the expression, call, or declaration started above.
});

// Calls test with the supplied values.
test('server HTML declares the requested document language', async ({ request }) => {
  // Computes and stores response for subsequent operations.
  const response = await request.get('/zh-Hant');
  // Calls expect with the supplied values.
  expect(response.ok()).toBe(true);
  // Calls expect with the supplied values.
  expect(await response.text()).toMatch(/<html[^>]+lang="zh-Hant"/);
  // Closes the expression, call, or declaration started above.
});

// Calls test with the supplied values.
test('private routes send a no-index directive', async ({ request }) => {
  // Iterates through these values for the nested operation.
  for (const path of [
    // Supplies this item to the surrounding call or collection.
    '/en/rooms',
    // Supplies this item to the surrounding call or collection.
    '/en/challenges/example',
    // Supplies this item to the surrounding call or collection.
    '/en/play/example',
    // Supplies this item to the surrounding call or collection.
    '/zh-Hant/account',
    // Supplies this item to the surrounding call or collection.
    '/en/admin',
    // Begins the nested block or object completed below.
  ]) {
    // Computes and stores response for subsequent operations.
    const response = await request.get(path);
    // Calls expect with the supplied values.
    expect(response.headers()['x-robots-tag'], path).toContain('noindex');
    // Closes the expression, call, or declaration started above.
  }

  // Computes and stores publicResponse for subsequent operations.
  const publicResponse = await request.get('/en/play');
  // Calls expect with the supplied values.
  expect(publicResponse.headers()['x-robots-tag']).toBeUndefined();
  // Closes the expression, call, or declaration started above.
});
