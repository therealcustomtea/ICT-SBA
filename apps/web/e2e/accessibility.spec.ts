// Imports the dependency used by this module.
import AxeBuilder from '@axe-core/playwright';
// Imports the dependency used by this module.
import { expect, test } from '@playwright/test';

// Computes and stores publicPages for subsequent operations.
const publicPages = [
  // Supplies this item to the surrounding call or collection.
  '/en',
  // Supplies this item to the surrounding call or collection.
  '/en/play',
  // Supplies this item to the surrounding call or collection.
  '/en/guide',
  // Supplies this item to the surrounding call or collection.
  '/en/privacy',
  // Supplies this item to the surrounding call or collection.
  '/en/terms',
  // Supplies this item to the surrounding call or collection.
  '/en/accessibility',
  // Supplies this item to the surrounding call or collection.
  '/en/support',
  // Supplies this item to the surrounding call or collection.
  '/zh-Hant',
  // Supplies this item to the surrounding call or collection.
  '/zh-Hant/play',
  // Closes the expression, call, or declaration started above.
];

// Iterates through these values for the nested operation.
for (const path of publicPages) {
  // Calls test with the supplied values.
  test(`${path} has no serious automated accessibility violations @a11y`, async ({ page }) => {
    // Waits for this asynchronous operation to complete.
    await page.goto(path);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    // Computes and stores results for subsequent operations.
    const results = await new AxeBuilder({ page }).analyze();
    // Calls expect with the supplied values.
    expect(results.violations).toEqual([]);
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
}

// Calls test with the supplied values.
test('skip link moves focus to the main content @a11y', async ({ page }, testInfo) => {
  // Waits for this asynchronous operation to complete.
  await page.goto('/en');
  // Waits for this asynchronous operation to complete.
  await page.waitForFunction(() => Boolean(document.documentElement.dataset.theme));
  // Computes and stores skipLink for subsequent operations.
  const skipLink = page.getByRole('link', { name: /skip to main content/i });
  // Checks this condition before running the nested branch.
  if (testInfo.project.name === 'mobile') await skipLink.focus();
  // Executes this line as the next step in the surrounding logic.
  else await page.keyboard.press('Tab');
  // Waits for this asynchronous operation to complete.
  await expect(skipLink).toBeFocused();
  // Checks this condition before running the nested branch.
  if (testInfo.project.name === 'mobile')
    // Waits for this asynchronous operation to complete.
    await skipLink.evaluate((element) => (element as HTMLElement).click());
  // Executes this line as the next step in the surrounding logic.
  else await page.keyboard.press('Enter');
  // Waits for this asynchronous operation to complete.
  await expect(page.locator('#main-content')).toBeFocused();
  // Closes the expression, call, or declaration started above.
});

// Calls test with the supplied values.
test('reduced motion removes nonessential transitions @a11y', async ({ page }) => {
  // Waits for this asynchronous operation to complete.
  await page.emulateMedia({ reducedMotion: 'reduce' });
  // Waits for this asynchronous operation to complete.
  await page.goto('/en');
  // Computes and stores duration for subsequent operations.
  const duration = await page
    // Executes this line as the next step in the surrounding logic.
    .locator('.hero-copy')
    // Executes this line as the next step in the surrounding logic.
    .getByRole('link', { name: 'Play now', exact: true })
    // Executes this line as the next step in the surrounding logic.
    .evaluate((element) => getComputedStyle(element).transitionDuration);
  // Calls expect with the supplied values.
  expect(duration.split(',').every((value) => Number.parseFloat(value) <= 0.001)).toBe(true);
  // Closes the expression, call, or declaration started above.
});
