import { expect, test } from '@playwright/test';
import { apiOrigin, captureSession, createKnownGame, type GameResponse } from './helpers';

test('mobile guest completes a game with touch targets and no horizontal overflow', async ({
  isMobile,
  page,
}) => {
  test.skip(!isMobile, 'The mobile project owns this touch-specific product flow.');
  const { token } = await captureSession(page);
  const secret = ['R', 'B', 'G', 'Y'];
  const game = await createKnownGame(page, token, { secret, maxAttempts: 1 });
  await page.goto(`/en/play/${game.id}`);
  await expect(page.locator('.game-workspace')).toBeVisible();

  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth,
  }));
  expect(dimensions.content).toBeLessThanOrEqual(dimensions.viewport);

  for (const colour of secret) await page.locator(`.game-workspace .palette .peg-${colour}`).tap();
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url() === `${apiOrigin}/v1/games/${game.id}/attempts` &&
      response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Submit guess', exact: true }).tap();
  const completed = (await (await responsePromise).json()) as GameResponse;
  expect(completed.status).toBe('won');
  await expect(page.getByRole('heading', { name: 'Code broken', exact: true })).toBeVisible();
});
