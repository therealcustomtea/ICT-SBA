// Imports the dependency used by this module.
import { expect, test } from '@playwright/test';
// Imports the dependency used by this module.
import { apiOrigin, captureSession, createKnownGame, type GameResponse } from './helpers';

// Calls test with the supplied values.
test('mobile guest completes a game with touch targets and no horizontal overflow', async ({
  // Supplies this item to the surrounding call or collection.
  isMobile,
  // Supplies this item to the surrounding call or collection.
  page,
  // Begins the nested block or object completed below.
}) => {
  // Calls test.skip with the supplied values.
  test.skip(!isMobile, 'The mobile project owns this touch-specific product flow.');
  // Executes this line as the next step in the surrounding logic.
  const { token } = await captureSession(page);
  // Computes and stores secret for subsequent operations.
  const secret = ['R', 'B', 'G', 'Y'];
  // Computes and stores game for subsequent operations.
  const game = await createKnownGame(page, token, { secret, maxAttempts: 1 });
  // Waits for this asynchronous operation to complete.
  await page.goto(`/en/play/${game.id}`);
  // Waits for this asynchronous operation to complete.
  await expect(page.locator('.game-workspace')).toBeVisible();

  // Computes and stores dimensions for subsequent operations.
  const dimensions = await page.evaluate(() => ({
    // Defines the viewport field in the surrounding object or type.
    viewport: document.documentElement.clientWidth,
    // Defines the content field in the surrounding object or type.
    content: document.documentElement.scrollWidth,
    // Closes the expression, call, or declaration started above.
  }));
  // Calls expect with the supplied values.
  expect(dimensions.content).toBeLessThanOrEqual(dimensions.viewport);

  // Iterates through these values for the nested operation.
  for (const colour of secret) await page.locator(`.game-workspace .palette .peg-${colour}`).tap();
  // Computes and stores responsePromise for subsequent operations.
  const responsePromise = page.waitForResponse(
    // Executes this line as the next step in the surrounding logic.
    (response) =>
      // Calls response.url with the supplied values.
      response.url() === `${apiOrigin}/v1/games/${game.id}/attempts` &&
      // Calls response.request with the supplied values.
      response.request().method() === 'POST',
    // Closes the expression, call, or declaration started above.
  );
  // Waits for this asynchronous operation to complete.
  await page.getByRole('button', { name: 'Submit guess', exact: true }).tap();
  // Computes and stores completed for subsequent operations.
  const completed = (await (await responsePromise).json()) as GameResponse;
  // Calls expect with the supplied values.
  expect(completed.status).toBe('won');
  // Waits for this asynchronous operation to complete.
  await expect(page.getByRole('heading', { name: 'Code broken', exact: true })).toBeVisible();
  // Closes the expression, call, or declaration started above.
});
