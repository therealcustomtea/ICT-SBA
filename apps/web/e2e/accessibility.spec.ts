import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const publicPages = [
  '/en',
  '/en/play',
  '/en/guide',
  '/en/privacy',
  '/en/terms',
  '/en/accessibility',
  '/en/support',
  '/zh-Hant',
  '/zh-Hant/play',
];

for (const path of publicPages) {
  test(`${path} has no serious automated accessibility violations @a11y`, async ({ page }) => {
    await page.goto(path);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
}

test('skip link moves focus to the main content @a11y', async ({ page }, testInfo) => {
  await page.goto('/en');
  await page.waitForFunction(() => Boolean(document.documentElement.dataset.theme));
  const skipLink = page.getByRole('link', { name: /skip to main content/i });
  if (testInfo.project.name === 'mobile') await skipLink.focus();
  else await page.keyboard.press('Tab');
  await expect(skipLink).toBeFocused();
  if (testInfo.project.name === 'mobile')
    await skipLink.evaluate((element) => (element as HTMLElement).click());
  else await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();
});

test('reduced motion removes nonessential transitions @a11y', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/en');
  const duration = await page
    .locator('.hero-copy')
    .getByRole('link', { name: 'Play now', exact: true })
    .evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(duration.split(',').every((value) => Number.parseFloat(value) <= 0.001)).toBe(true);
});
