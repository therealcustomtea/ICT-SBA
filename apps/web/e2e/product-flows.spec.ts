// Imports the dependency used by this module.
import { expect, test } from '@playwright/test';
// Imports the dependency used by this module.
import {
  // Supplies this item to the surrounding call or collection.
  apiOrigin,
  // Supplies this item to the surrounding call or collection.
  apiRequest,
  // Supplies this item to the surrounding call or collection.
  captureSession,
  // Supplies this item to the surrounding call or collection.
  chooseDuelGuess,
  // Supplies this item to the surrounding call or collection.
  chooseGuess,
  // Supplies this item to the surrounding call or collection.
  createKnownGame,
  // Supplies this item to the surrounding call or collection.
  enumerateMastermindCandidates,
  // Supplies this item to the surrounding call or collection.
  expectActiveSecretOmitted,
  // Supplies this item to the surrounding call or collection.
  narrowMastermindCandidates,
  // Declares the GameResponse data shape or implementation.
  type GameResponse,
  // Declares the RoomResponse data shape or implementation.
  type RoomResponse,
  // Supplies this item to the surrounding call or collection.
  submitGuess,
  // Executes this line as the next step in the surrounding logic.
} from './helpers';

// Calls test.describe with the supplied values.
test.describe('real product flows', () => {
  // Calls test.describe.configure with the supplied values.
  test.describe.configure({ mode: 'serial' });
  // Calls test.beforeEach with the supplied values.
  test.beforeEach(async ({ isMobile }) => {
    // Calls test.skip with the supplied values.
    test.skip(Boolean(isMobile), 'The desktop project owns these multi-step product flows.');
    // Closes the expression, call, or declaration started above.
  });

  // Calls test with the supplied values.
  test('anonymous guest launches Easy, Hard, Expert, and custom games', async ({ page }) => {
    // Calls test.setTimeout with the supplied values.
    test.setTimeout(60_000);
    // Executes this line as the next step in the surrounding logic.
    const { token, profile } = await captureSession(page);
    // Calls expect with the supplied values.
    expect(profile.isAnonymous).toBe(true);

    // Computes and stores presets for subsequent operations.
    const presets = [
      // Begins the nested block or object completed below.
      {
        // Defines the value field in the surrounding object or type.
        value: 'easy',
        // Defines the label field in the surrounding object or type.
        label: 'Easy',
        // Defines the expected field in the surrounding object or type.
        expected: { colours: 5, codeLength: 4, maxAttempts: 12, duplicatesAllowed: false },
        // Closes the expression, call, or declaration started above.
      },
      // Begins the nested block or object completed below.
      {
        // Defines the value field in the surrounding object or type.
        value: 'hard',
        // Defines the label field in the surrounding object or type.
        label: 'Hard',
        // Defines the expected field in the surrounding object or type.
        expected: { colours: 8, codeLength: 5, maxAttempts: 8, duplicatesAllowed: true },
        // Closes the expression, call, or declaration started above.
      },
      // Begins the nested block or object completed below.
      {
        // Defines the value field in the surrounding object or type.
        value: 'expert',
        // Defines the label field in the surrounding object or type.
        label: 'Expert',
        // Defines the expected field in the surrounding object or type.
        expected: { colours: 10, codeLength: 6, maxAttempts: 8, duplicatesAllowed: true },
        // Closes the expression, call, or declaration started above.
      },
      // Executes this line as the next step in the surrounding logic.
    ] as const;

    // Iterates through these values for the nested operation.
    for (const preset of presets) {
      // Waits for this asynchronous operation to complete.
      await page.goto('/en/play');
      // Waits for this asynchronous operation to complete.
      await page.getByText(preset.label, { exact: true }).click();
      // Computes and stores responsePromise for subsequent operations.
      const responsePromise = page.waitForResponse(
        // Executes this line as the next step in the surrounding logic.
        (response) =>
          // Calls response.url with the supplied values.
          response.url() === `${apiOrigin}/v1/games` && response.request().method() === 'POST',
        // Closes the expression, call, or declaration started above.
      );
      // Waits for this asynchronous operation to complete.
      await page.getByRole('button', { name: 'Start game', exact: true }).click();
      // Computes and stores game for subsequent operations.
      const game = await expectActiveSecretOmitted(await responsePromise);
      // Calls expect with the supplied values.
      expect(game.difficulty).toBe(preset.value);
      // Calls expect with the supplied values.
      expect(game.config.colours).toHaveLength(preset.expected.colours);
      // Calls expect with the supplied values.
      expect(game.config.codeLength).toBe(preset.expected.codeLength);
      // Calls expect with the supplied values.
      expect(game.config.maxAttempts).toBe(preset.expected.maxAttempts);
      // Calls expect with the supplied values.
      expect(game.config.duplicatesAllowed).toBe(preset.expected.duplicatesAllowed);
      // Waits for this asynchronous operation to complete.
      await expect(page).toHaveURL(new RegExp(`/en/play/${game.id}$`));

      // Computes and stores abandon for subsequent operations.
      const abandon = await apiRequest(page, token, `/v1/games/${game.id}/abandon`, {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Closes the expression, call, or declaration started above.
      });
      // Calls expect with the supplied values.
      expect(abandon.ok()).toBe(true);
      // Closes the expression, call, or declaration started above.
    }

    // Waits for this asynchronous operation to complete.
    await page.goto('/en/play');
    // Waits for this asynchronous operation to complete.
    await page.getByText('Custom', { exact: true }).click();
    // Waits for this asynchronous operation to complete.
    await page.locator('input[name="colour-count"]').fill('7');
    // Waits for this asynchronous operation to complete.
    await page.locator('input[name="code-length"]').fill('5');
    // Waits for this asynchronous operation to complete.
    await page.locator('input[name="maximum-attempts"]').fill('3');
    // Computes and stores customResponse for subsequent operations.
    const customResponse = page.waitForResponse(
      // Executes this line as the next step in the surrounding logic.
      (response) =>
        // Calls response.url with the supplied values.
        response.url() === `${apiOrigin}/v1/games` && response.request().method() === 'POST',
      // Closes the expression, call, or declaration started above.
    );
    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Start game', exact: true }).click();
    // Computes and stores custom for subsequent operations.
    const custom = await expectActiveSecretOmitted(await customResponse);
    // Calls expect with the supplied values.
    expect(custom.difficulty).toBeNull();
    // Calls expect with the supplied values.
    expect(custom.ranked).toBe(false);
    // Calls expect with the supplied values.
    expect(custom.config).toMatchObject({
      // Defines the codeLength field in the surrounding object or type.
      codeLength: 5,
      // Defines the maxAttempts field in the surrounding object or type.
      maxAttempts: 3,
      // Defines the duplicatesAllowed field in the surrounding object or type.
      duplicatesAllowed: true,
      // Closes the expression, call, or declaration started above.
    });
    // Calls expect with the supplied values.
    expect(custom.config.colours).toHaveLength(7);
    // Closes the expression, call, or declaration started above.
  });

  // Calls test with the supplied values.
  test('human Code Maker game rejects duplicates without consuming a turn, restores, and wins on the final attempt', async ({
    // Supplies this item to the surrounding call or collection.
    context,
    // Supplies this item to the surrounding call or collection.
    page,
    // Begins the nested block or object completed below.
  }) => {
    // Waits for this asynchronous operation to complete.
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    // Waits for this asynchronous operation to complete.
    await page.addInitScript(() => {
      // Calls Object.defineProperty with the supplied values.
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      // Closes the expression, call, or declaration started above.
    });
    // Executes this line as the next step in the surrounding logic.
    const { token } = await captureSession(page);
    // Waits for this asynchronous operation to complete.
    await page.evaluate(() => {
      // Calls localStorage.setItem with the supplied values.
      localStorage.setItem(
        // Supplies this item to the surrounding call or collection.
        'cipherboard:preferences',
        // Calls JSON.stringify with the supplied values.
        JSON.stringify({
          // Defines the theme field in the surrounding object or type.
          theme: 'light',
          // Defines the pegStyle field in the surrounding object or type.
          pegStyle: 'patterns',
          // Defines the reducedMotion field in the surrounding object or type.
          reducedMotion: false,
          // Defines the sound field in the surrounding object or type.
          sound: false,
          // Defines the analytics field in the surrounding object or type.
          analytics: true,
          // Closes the expression, call, or declaration started above.
        }),
        // Closes the expression, call, or declaration started above.
      );
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores analyticsBodies for subsequent operations.
    const analyticsBodies: string[] = [];
    // Calls page.on with the supplied values.
    page.on('request', (request) => {
      // Checks this condition before running the nested branch.
      if (request.url() === `${apiOrigin}/v1/analytics/events` && request.postData())
        // Calls analyticsBodies.push with the supplied values.
        analyticsBodies.push(request.postData()!);
      // Closes the expression, call, or declaration started above.
    });

    // Waits for this asynchronous operation to complete.
    await page.goto('/en/play');
    // Waits for this asynchronous operation to complete.
    await page.getByText('Pass-and-play Code Maker', { exact: true }).click();
    // Waits for this asynchronous operation to complete.
    await page.getByText('Custom', { exact: true }).click();
    // Waits for this asynchronous operation to complete.
    await page.locator('input[name="maximum-attempts"]').fill('2');
    // Waits for this asynchronous operation to complete.
    await page.getByText('Allow duplicate colours', { exact: true }).click();
    // Iterates through these values for the nested operation.
    for (const name of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square'])
      // Waits for this asynchronous operation to complete.
      await page.getByRole('button', { name, exact: true }).click();

    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Confirm and conceal code', exact: true }).click();
    // Waits for this asynchronous operation to complete.
    await expect(page.getByText('Code concealed', { exact: true })).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('button', { name: 'Red circle', exact: true })).toHaveCount(0);

    // Computes and stores creationResponse for subsequent operations.
    const creationResponse = page.waitForResponse(
      // Executes this line as the next step in the surrounding logic.
      (response) =>
        // Calls response.url with the supplied values.
        response.url() === `${apiOrigin}/v1/games` && response.request().method() === 'POST',
      // Closes the expression, call, or declaration started above.
    );
    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Begin Code Breaker turn', exact: true }).click();
    // Computes and stores secret for subsequent operations.
    const secret = ['R', 'B', 'G', 'Y'];
    // Computes and stores game for subsequent operations.
    const game = await expectActiveSecretOmitted(await creationResponse, secret);
    // Waits for this asynchronous operation to complete.
    await expect(page).toHaveURL(new RegExp(`/en/play/${game.id}$`));
    // Waits for this asynchronous operation to complete.
    await expect(page.getByText('Revealed code', { exact: true })).toHaveCount(0);
    // Computes and stores browserStorage for subsequent operations.
    const browserStorage = await page.evaluate(() => JSON.stringify({ ...localStorage }));
    // Calls expect with the supplied values.
    expect(browserStorage).not.toContain(JSON.stringify(secret));

    // Waits for this asynchronous operation to complete.
    await chooseGuess(page, ['R', 'R', 'R', 'R']);
    // Computes and stores invalidResponse for subsequent operations.
    const invalidResponse = await submitGuess(page);
    // Calls expect with the supplied values.
    expect(invalidResponse.status()).toBe(422);
    // Waits for this asynchronous operation to complete.
    await expect(page.locator('.inline-error[role="alert"]')).toContainText(
      // Supplies this item to the surrounding call or collection.
      'does not allow repeated pegs',
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores unchanged for subsequent operations.
    const unchanged = await apiRequest(page, token, `/v1/games/${game.id}`);
    // Calls expect with the supplied values.
    expect((await unchanged.json()).attemptsUsed).toBe(0);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('button', { name: 'Retry game restore', exact: true })).toHaveCount(
      // Supplies this item to the surrounding call or collection.
      0,
      // Closes the expression, call, or declaration started above.
    );
    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Clear row', exact: true }).click();

    // Waits for this asynchronous operation to complete.
    await chooseGuess(page, ['W', 'R', 'B', 'G']);
    // Computes and stores firstAttempt for subsequent operations.
    const firstAttempt = await submitGuess(page);
    // Computes and stores afterFirst for subsequent operations.
    const afterFirst = await expectActiveSecretOmitted(firstAttempt, secret);
    // Calls expect with the supplied values.
    expect(afterFirst.attemptsUsed).toBe(1);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('group', { name: /^Attempt 1:/ })).toBeVisible();

    // Waits for this asynchronous operation to complete.
    await page.reload();
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('group', { name: /^Attempt 1:/ })).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await expect(page.getByText('Revealed code', { exact: true })).toHaveCount(0);

    // Waits for this asynchronous operation to complete.
    await chooseGuess(page, secret);
    // Computes and stores finalAttemptResponse for subsequent operations.
    const finalAttemptResponse = await submitGuess(page);
    // Calls expect with the supplied values.
    expect(finalAttemptResponse.ok()).toBe(true);
    // Computes and stores completed for subsequent operations.
    const completed = (await finalAttemptResponse.json()) as GameResponse;
    // Calls expect with the supplied values.
    expect(completed.status).toBe('won');
    // Calls expect with the supplied values.
    expect(completed.attemptsUsed).toBe(2);
    // Calls expect with the supplied values.
    expect(completed.secret).toEqual(secret);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('heading', { name: 'Code broken', exact: true })).toBeVisible();

    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Share result', exact: true }).click();
    // Computes and stores shared for subsequent operations.
    const shared = await page.evaluate(() => navigator.clipboard.readText());
    // Calls expect with the supplied values.
    expect(shared).toContain('Solved in 2/2');
    // Calls expect with the supplied values.
    expect(shared).not.toContain(JSON.stringify(secret));
    // Calls expect with the supplied values.
    expect(shared).not.toContain(secret.join(''));

    // Waits for this asynchronous operation to complete.
    await expect.poll(() => analyticsBodies.length).toBeGreaterThan(0);
    // Iterates through these values for the nested operation.
    for (const body of analyticsBodies) {
      // Computes and stores payload for subsequent operations.
      const payload = JSON.parse(body) as Record<string, unknown>;
      // Calls expect with the supplied values.
      expect(body).not.toContain(JSON.stringify(secret));
      // Calls expect with the supplied values.
      expect(payload).not.toHaveProperty('secret');
      // Calls expect with the supplied values.
      expect(payload).not.toHaveProperty('guess');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  });

  // Calls test with the supplied values.
  test('a final failed attempt ends the game as a loss and remains terminal after refresh', async ({
    // Supplies this item to the surrounding call or collection.
    page,
    // Begins the nested block or object completed below.
  }) => {
    // Executes this line as the next step in the surrounding logic.
    const { token } = await captureSession(page);
    // Computes and stores game for subsequent operations.
    const game = await createKnownGame(page, token, { maxAttempts: 1 });
    // Waits for this asynchronous operation to complete.
    await page.goto(`/en/play/${game.id}`);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('heading', { name: 'Code-breaking board' })).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await chooseGuess(page, ['W', 'R', 'B', 'G']);
    // Computes and stores response for subsequent operations.
    const response = await submitGuess(page);
    // Computes and stores lost for subsequent operations.
    const lost = (await response.json()) as GameResponse;
    // Calls expect with the supplied values.
    expect(lost.status).toBe('lost');
    // Calls expect with the supplied values.
    expect(lost.attemptsRemaining).toBe(0);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('heading', { name: 'The code held', exact: true })).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('button', { name: 'Submit guess', exact: true })).toHaveCount(0);
    // Waits for this asynchronous operation to complete.
    await page.reload();
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('heading', { name: 'The code held', exact: true })).toBeVisible();
    // Closes the expression, call, or declaration started above.
  });

  // Calls test with the supplied values.
  test('daily play supports keyboard input, Traditional Chinese, dark mode, reduced motion, and denies guest admin access', async ({
    // Supplies this item to the surrounding call or collection.
    page,
    // Begins the nested block or object completed below.
  }) => {
    // Executes this line as the next step in the surrounding logic.
    const { token } = await captureSession(page);
    // Waits for this asynchronous operation to complete.
    await page.goto('/en/daily');
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('heading', { name: 'Daily challenge', exact: true })).toBeVisible();
    // Computes and stores startResponse for subsequent operations.
    const startResponse = page.waitForResponse(
      // Executes this line as the next step in the surrounding logic.
      (response) =>
        // Calls response.url with the supplied values.
        response.url() === `${apiOrigin}/v1/daily/start` && response.request().method() === 'POST',
      // Closes the expression, call, or declaration started above.
    );
    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Begin game', exact: true }).click();
    // Computes and stores game for subsequent operations.
    const game = await expectActiveSecretOmitted(await startResponse);

    // Computes and stores firstSlot for subsequent operations.
    const firstSlot = page.getByRole('button', { name: /^Position 1:/ });
    // Waits for this asynchronous operation to complete.
    await firstSlot.focus();
    // Iterates through these values for the nested operation.
    for (const key of ['1', '2', '3', '4']) await page.keyboard.press(key);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('button', { name: /Position 4: Yellow square/ })).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Submit guess', exact: true }).focus();
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('button', { name: 'Submit guess', exact: true })).toBeFocused();

    // Computes and stores restoreResponse for subsequent operations.
    const restoreResponse = page.waitForResponse(
      // Executes this line as the next step in the surrounding logic.
      (response) =>
        // Calls response.url with the supplied values.
        response.url() === `${apiOrigin}/v1/games/${game.id}` &&
        // Calls response.request with the supplied values.
        response.request().method() === 'GET',
      // Closes the expression, call, or declaration started above.
    );
    // Waits for this asynchronous operation to complete.
    await page.getByRole('link', { name: 'Switch language' }).click();
    // Waits for this asynchronous operation to complete.
    await expect(page).toHaveURL(new RegExp(`/zh-Hant/daily$`));
    // Waits for this asynchronous operation to complete.
    await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hant');
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('heading', { name: '每日挑戰', exact: true })).toBeVisible();
    // Calls expect with the supplied values.
    expect((await (await restoreResponse).json()).id).toBe(game.id);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('button', { name: '開始遊戲', exact: true })).toHaveCount(0);
    // Waits for this asynchronous operation to complete.
    await expect(page.getByRole('button', { name: '提交猜測', exact: true })).toBeEnabled();

    // Waits for this asynchronous operation to complete.
    await page.goto('/en/settings');
    // Waits for this asynchronous operation to complete.
    await page.locator('select[name="theme"]').selectOption('dark');
    // Waits for this asynchronous operation to complete.
    await page.getByText('Reduce motion', { exact: true }).click();
    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Save changes', exact: true }).click();
    // Waits for this asynchronous operation to complete.
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    // Waits for this asynchronous operation to complete.
    await expect(page.locator('html')).toHaveAttribute('data-reduce-motion', 'true');
    // Computes and stores transitionDuration for subsequent operations.
    const transitionDuration = await page
      // Executes this line as the next step in the surrounding logic.
      .getByRole('button', { name: 'Use light appearance' })
      // Executes this line as the next step in the surrounding logic.
      .evaluate((element) => getComputedStyle(element).transitionDuration);
    // Calls expect with the supplied values.
    expect(transitionDuration.split(',').every((value) => Number.parseFloat(value) <= 0.001)).toBe(
      // Supplies this item to the surrounding call or collection.
      true,
      // Closes the expression, call, or declaration started above.
    );

    // Computes and stores adminResponse for subsequent operations.
    const adminResponse = await apiRequest(page, token, '/v1/admin/summary');
    // Calls expect with the supplied values.
    expect(adminResponse.status()).toBe(403);
    // Calls expect with the supplied values.
    expect((await adminResponse.json()).code).toBe('ADMIN_REQUIRED');
    // Waits for this asynchronous operation to complete.
    await page.goto('/en/admin');
    // Waits for this asynchronous operation to complete.
    await expect(page.locator('.state-panel[role="alert"]')).toContainText(
      // Supplies this item to the surrounding call or collection.
      'You do not have permission to access administration.',
      // Closes the expression, call, or declaration started above.
    );

    // Computes and stores abandon for subsequent operations.
    const abandon = await apiRequest(page, token, `/v1/games/${game.id}/abandon`, {
      // Defines the method field in the surrounding object or type.
      method: 'POST',
      // Closes the expression, call, or declaration started above.
    });
    // Calls expect with the supplied values.
    expect(abandon.ok()).toBe(true);
    // Closes the expression, call, or declaration started above.
  });

  // Calls test with the supplied values.
  test('manual friend challenge crosses guest browsers and records a verified win', async ({
    // Supplies this item to the surrounding call or collection.
    browser,
    // Supplies this item to the surrounding call or collection.
    page,
    // Begins the nested block or object completed below.
  }) => {
    // Executes this line as the next step in the surrounding logic.
    const { token: creatorToken } = await captureSession(page);
    // Waits for this asynchronous operation to complete.
    await page.goto('/en/challenges/new');
    // Waits for this asynchronous operation to complete.
    await page.locator('input[name="challenge-title"]').fill('E2E private challenge');
    // Waits for this asynchronous operation to complete.
    await page.getByText('Easy', { exact: true }).click();
    // Waits for this asynchronous operation to complete.
    await page.getByText('Enter the code myself', { exact: true }).click();
    // Computes and stores secret for subsequent operations.
    const secret = ['R', 'B', 'G', 'Y'];
    // Iterates through these values for the nested operation.
    for (const name of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square'])
      // Waits for this asynchronous operation to complete.
      await page.getByRole('button', { name, exact: true }).click();
    // Computes and stores creationResponse for subsequent operations.
    const creationResponse = page.waitForResponse(
      // Executes this line as the next step in the surrounding logic.
      (response) =>
        // Calls response.url with the supplied values.
        response.url() === `${apiOrigin}/v1/challenges` && response.request().method() === 'POST',
      // Closes the expression, call, or declaration started above.
    );
    // Waits for this asynchronous operation to complete.
    await page.getByRole('button', { name: 'Create challenge', exact: true }).click();
    // Computes and stores rawChallenge for subsequent operations.
    const rawChallenge = await (await creationResponse).text();
    // Computes and stores challenge for subsequent operations.
    const challenge = JSON.parse(rawChallenge) as { id: string; shareCode: string };
    // Calls expect with the supplied values.
    expect(rawChallenge).not.toContain(JSON.stringify(secret));
    // Calls expect with the supplied values.
    expect(challenge.shareCode).toMatch(/^[A-Za-z0-9_-]{20,}$/);
    // Computes and stores shareUrl for subsequent operations.
    const shareUrl = await page.locator('input[name="share-url"]').inputValue();
    // Calls expect with the supplied values.
    expect(new URL(shareUrl).search).toBe('');
    // Calls expect with the supplied values.
    expect(shareUrl).not.toContain(secret.join(''));

    // Computes and stores playerContext for subsequent operations.
    const playerContext = await browser.newContext();
    // Computes and stores playerPage for subsequent operations.
    const playerPage = await playerContext.newPage();
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await captureSession(playerPage);
      // Waits for this asynchronous operation to complete.
      await playerPage.goto(`/en/challenges/${challenge.shareCode}`);
      // Waits for this asynchronous operation to complete.
      await expect(
        // Calls playerPage.getByRole with the supplied values.
        playerPage.getByRole('heading', {
          // Defines the level field in the surrounding object or type.
          level: 1,
          // Defines the name field in the surrounding object or type.
          name: 'E2E private challenge',
          // Defines the exact field in the surrounding object or type.
          exact: true,
          // Closes the expression, call, or declaration started above.
        }),
        // Executes this line as the next step in the surrounding logic.
      ).toBeVisible();
      // Computes and stores startResponse for subsequent operations.
      const startResponse = playerPage.waitForResponse(
        // Executes this line as the next step in the surrounding logic.
        (response) =>
          // Calls response.url with the supplied values.
          response.url() === `${apiOrigin}/v1/challenges/${challenge.shareCode}/start` &&
          // Calls response.request with the supplied values.
          response.request().method() === 'POST',
        // Closes the expression, call, or declaration started above.
      );
      // Waits for this asynchronous operation to complete.
      await playerPage.getByRole('button', { name: 'Begin game', exact: true }).click();
      // Waits for this asynchronous operation to complete.
      await expectActiveSecretOmitted(await startResponse, secret);
      // Waits for this asynchronous operation to complete.
      await chooseGuess(playerPage, secret);
      // Computes and stores winResponse for subsequent operations.
      const winResponse = await submitGuess(playerPage);
      // Calls expect with the supplied values.
      expect(((await winResponse.json()) as GameResponse).status).toBe('won');
      // Waits for this asynchronous operation to complete.
      await expect(
        // Calls playerPage.getByRole with the supplied values.
        playerPage.getByRole('heading', { name: 'Code broken', exact: true }),
        // Executes this line as the next step in the surrounding logic.
      ).toBeVisible();

      // Waits for this asynchronous operation to complete.
      await expect
        // Begins the nested block or object completed below.
        .poll(async () => {
          // Computes and stores results for subsequent operations.
          const results = await apiRequest(
            // Supplies this item to the surrounding call or collection.
            page,
            // Supplies this item to the surrounding call or collection.
            creatorToken,
            // Supplies this item to the surrounding call or collection.
            `/v1/challenges/${challenge.id}/results?page=1&page_size=10`,
            // Closes the expression, call, or declaration started above.
          );
          // Returns this result to the caller and ends the current function.
          return ((await results.json()) as { completedCount: number }).completedCount;
          // Closes the expression, call, or declaration started above.
        })
        // Executes this line as the next step in the surrounding logic.
        .toBe(1);
      // Runs cleanup regardless of the protected result.
    } finally {
      // Waits for this asynchronous operation to complete.
      await playerContext.close();
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  });

  // Calls test with the supplied values.
  test('two anonymous browsers solve a duel, reconcile its terminal event, and restore persisted state', async ({
    // Supplies this item to the surrounding call or collection.
    browser,
    // Supplies this item to the surrounding call or collection.
    page,
    // Begins the nested block or object completed below.
  }) => {
    // Calls test.setTimeout with the supplied values.
    test.setTimeout(90_000);
    // Computes and stores creatorSession for subsequent operations.
    const creatorSession = await captureSession(page);
    // Computes and stores opponentContext for subsequent operations.
    const opponentContext = await browser.newContext();
    // Computes and stores opponent for subsequent operations.
    const opponent = await opponentContext.newPage();
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores opponentSession for subsequent operations.
      const opponentSession = await captureSession(opponent);
      // Waits for this asynchronous operation to complete.
      await page.goto('/en/rooms');
      // Waits for this asynchronous operation to complete.
      await page.getByText('Easy', { exact: true }).click();
      // Computes and stores createResponse for subsequent operations.
      const createResponse = page.waitForResponse(
        // Executes this line as the next step in the surrounding logic.
        (response) =>
          // Calls response.url with the supplied values.
          response.url() === `${apiOrigin}/v1/rooms` && response.request().method() === 'POST',
        // Closes the expression, call, or declaration started above.
      );
      // Waits for this asynchronous operation to complete.
      await page.getByRole('button', { name: 'Create room', exact: true }).click();
      // Computes and stores created for subsequent operations.
      const created = (await (await createResponse).json()) as RoomResponse;
      // Calls expect with the supplied values.
      expect(created.status).toBe('waiting');
      // Calls expect with the supplied values.
      expect(created.roomCode).toMatch(/^[A-Za-z0-9_-]{20,64}$/);
      // Calls expect with the supplied values.
      expect(created.config).toMatchObject({
        // Defines the codeLength field in the surrounding object or type.
        codeLength: 4,
        // Defines the maxAttempts field in the surrounding object or type.
        maxAttempts: 12,
        // Defines the duplicatesAllowed field in the surrounding object or type.
        duplicatesAllowed: false,
        // Closes the expression, call, or declaration started above.
      });
      // Calls expect with the supplied values.
      expect(created.config.colours).toHaveLength(5);
      // Waits for this asynchronous operation to complete.
      await expect(page).toHaveURL(new RegExp(`/en/rooms/${created.id}$`));

      // Waits for this asynchronous operation to complete.
      await opponent.goto(`/en/rooms?code=${created.roomCode}`);
      // Computes and stores joinResponse for subsequent operations.
      const joinResponse = opponent.waitForResponse(
        // Executes this line as the next step in the surrounding logic.
        (response) =>
          // Calls response.url with the supplied values.
          response.url().endsWith(`/v1/rooms/${created.roomCode}/join`) &&
          // Calls response.request with the supplied values.
          response.request().method() === 'POST',
        // Closes the expression, call, or declaration started above.
      );
      // Waits for this asynchronous operation to complete.
      await opponent.getByRole('button', { name: 'Join room', exact: true }).click();
      // Computes and stores joined for subsequent operations.
      const joined = (await (await joinResponse).json()) as RoomResponse;
      // Calls expect with the supplied values.
      expect(joined.members).toHaveLength(2);
      // Waits for this asynchronous operation to complete.
      await expect(page.locator('.member-list li')).toHaveCount(2, { timeout: 10_000 });

      // Waits for this asynchronous operation to complete.
      await page.getByRole('button', { name: 'I’m ready', exact: true }).click();
      // Computes and stores opponentReadyResponse for subsequent operations.
      const opponentReadyResponse = opponent.waitForResponse(
        // Executes this line as the next step in the surrounding logic.
        (response) =>
          // Calls response.url with the supplied values.
          response.url().endsWith(`/v1/rooms/${created.id}/ready`) &&
          // Calls response.request with the supplied values.
          response.request().method() === 'POST',
        // Closes the expression, call, or declaration started above.
      );
      // Waits for this asynchronous operation to complete.
      await opponent.getByRole('button', { name: 'I’m ready', exact: true }).click();
      // Calls expect with the supplied values.
      expect(((await (await opponentReadyResponse).json()) as RoomResponse).status).toBe('active');

      // Waits for this asynchronous operation to complete.
      await expect(page.getByRole('link', { name: 'Start duel', exact: true })).toBeVisible({
        // Defines the timeout field in the surrounding object or type.
        timeout: 10_000,
        // Closes the expression, call, or declaration started above.
      });
      // Waits for this asynchronous operation to complete.
      await expect(opponent.getByRole('link', { name: 'Start duel', exact: true })).toBeVisible();
      // Computes and stores creatorSockets for subsequent operations.
      let creatorSockets = 0;
      // Calls page.on with the supplied values.
      page.on('websocket', () => {
        // Executes this line as the next step in the surrounding logic.
        creatorSockets += 1;
        // Closes the expression, call, or declaration started above.
      });
      // Waits for this asynchronous operation to complete.
      await Promise.all([
        // Calls page.getByRole with the supplied values.
        page.getByRole('link', { name: 'Start duel', exact: true }).click(),
        // Calls opponent.getByRole with the supplied values.
        opponent.getByRole('link', { name: 'Start duel', exact: true }).click(),
        // Closes the expression, call, or declaration started above.
      ]);
      // Waits for this asynchronous operation to complete.
      await expect(page.locator('.duel-layout')).toBeVisible({ timeout: 15_000 });
      // Waits for this asynchronous operation to complete.
      await expect(opponent.locator('.duel-layout')).toBeVisible({ timeout: 15_000 });

      // Reconnect before guessing so state restoration never depends on whether a random guess wins.
      // Waits for this asynchronous operation to complete.
      await page.reload();
      // Waits for this asynchronous operation to complete.
      await expect(page.locator('.duel-layout')).toBeVisible({ timeout: 15_000 });
      // Waits for this asynchronous operation to complete.
      await expect(page.locator('.duel-layout .attempt-row')).toHaveCount(0);
      // Waits for this asynchronous operation to complete.
      await expect.poll(() => creatorSockets).toBeGreaterThanOrEqual(2);

      // Computes and stores creatorRoomResponse for subsequent operations.
      const creatorRoomResponse = await apiRequest(
        // Supplies this item to the surrounding call or collection.
        page,
        // Supplies this item to the surrounding call or collection.
        creatorSession.token,
        // Supplies this item to the surrounding call or collection.
        `/v1/rooms/${created.id}`,
        // Closes the expression, call, or declaration started above.
      );
      // Computes and stores opponentRoomResponse for subsequent operations.
      const opponentRoomResponse = await apiRequest(
        // Supplies this item to the surrounding call or collection.
        opponent,
        // Supplies this item to the surrounding call or collection.
        opponentSession.token,
        // Supplies this item to the surrounding call or collection.
        `/v1/rooms/${created.id}`,
        // Closes the expression, call, or declaration started above.
      );
      // Computes and stores creatorRoom for subsequent operations.
      const creatorRoom = (await creatorRoomResponse.json()) as RoomResponse;
      // Computes and stores opponentRoom for subsequent operations.
      const opponentRoom = (await opponentRoomResponse.json()) as RoomResponse;
      // Computes and stores creatorGameId for subsequent operations.
      const creatorGameId = creatorRoom.members.find(
        // Supplies this item to the surrounding call or collection.
        (member) => member.userId === creatorSession.profile.id,
        // Executes this line as the next step in the surrounding logic.
      )?.gameId;
      // Computes and stores opponentGameId for subsequent operations.
      const opponentGameId = opponentRoom.members.find(
        // Supplies this item to the surrounding call or collection.
        (member) => member.userId === opponentSession.profile.id,
        // Executes this line as the next step in the surrounding logic.
      )?.gameId;
      // Calls expect with the supplied values.
      expect(creatorGameId).toBeTruthy();
      // Calls expect with the supplied values.
      expect(opponentGameId).toBeTruthy();

      // Easy has 5P4 = 120 candidates. Selecting the first consistent candidate has a
      // six-attempt worst case, comfortably inside Easy's twelve server-authoritative turns.
      // Computes and stores candidates for subsequent operations.
      let candidates = enumerateMastermindCandidates(
        // Supplies this item to the surrounding call or collection.
        created.config.colours,
        // Supplies this item to the surrounding call or collection.
        created.config.codeLength,
        // Supplies this item to the surrounding call or collection.
        created.config.duplicatesAllowed,
        // Closes the expression, call, or declaration started above.
      );
      // Calls expect with the supplied values.
      expect(candidates).toHaveLength(120);
      // Computes and stores creatorGame for subsequent operations.
      let creatorGame: GameResponse | null = null;
      // Computes and stores opponentGame for subsequent operations.
      let opponentGame: GameResponse | null = null;

      // Iterates through these values for the nested operation.
      for (let attemptNumber = 1; attemptNumber <= 6; attemptNumber += 1) {
        // Computes and stores guess for subsequent operations.
        const guess = candidates[0];
        // Calls expect with the supplied values.
        expect(guess).toHaveLength(created.config.codeLength);
        // Waits for this asynchronous operation to complete.
        await Promise.all([chooseDuelGuess(page, guess!), chooseDuelGuess(opponent, guess!)]);
        // Waits for this asynchronous operation to complete.
        await Promise.all([
          // Calls expect with the supplied values.
          expect(page.getByRole('button', { name: 'Submit guess', exact: true })).toBeEnabled(),
          // Calls expect with the supplied values.
          expect(opponent.getByRole('button', { name: 'Submit guess', exact: true })).toBeEnabled(),
          // Closes the expression, call, or declaration started above.
        ]);
        // Waits for this asynchronous operation to complete.
        await Promise.all([
          // Calls page.getByRole with the supplied values.
          page.getByRole('button', { name: 'Submit guess', exact: true }).dispatchEvent('click'),
          // Executes this line as the next step in the surrounding logic.
          opponent
            // Executes this line as the next step in the surrounding logic.
            .getByRole('button', { name: 'Submit guess', exact: true })
            // Supplies this item to the surrounding call or collection.
            .dispatchEvent('click'),
          // Closes the expression, call, or declaration started above.
        ]);

        // Waits for this asynchronous operation to complete.
        await expect
          // Executes this line as the next step in the surrounding logic.
          .poll(
            // Begins the nested block or object completed below.
            async () => {
              // Executes this line as the next step in the surrounding logic.
              const [creatorResult, opponentResult] = await Promise.all([
                // Calls apiRequest with the supplied values.
                apiRequest(page, creatorSession.token, `/v1/games/${creatorGameId}`),
                // Calls apiRequest with the supplied values.
                apiRequest(opponent, opponentSession.token, `/v1/games/${opponentGameId}`),
                // Closes the expression, call, or declaration started above.
              ]);
              // Provides the creatorGame value to the surrounding call or element.
              creatorGame = (await creatorResult.json()) as GameResponse;
              // Provides the opponentGame value to the surrounding call or element.
              opponentGame = (await opponentResult.json()) as GameResponse;
              // Returns this result to the caller and ends the current function.
              return [creatorGame, opponentGame].every(
                // Supplies this item to the surrounding call or collection.
                (game) => game.attemptsUsed >= attemptNumber || game.status !== 'active',
                // Closes the expression, call, or declaration started above.
              );
              // Closes the expression, call, or declaration started above.
            },
            // Supplies this item to the surrounding call or collection.
            { timeout: 10_000 },
            // Closes the expression, call, or declaration started above.
          )
          // Executes this line as the next step in the surrounding logic.
          .toBe(true);

        // Checks this condition before running the nested branch.
        if (creatorGame!.status !== 'active' || opponentGame!.status !== 'active') break;
        // Calls expect with the supplied values.
        expect(creatorGame!.attemptsUsed).toBe(attemptNumber);
        // Calls expect with the supplied values.
        expect(opponentGame!.attemptsUsed).toBe(attemptNumber);
        // Calls expect with the supplied values.
        expect(opponentGame!.attempts.at(-1)?.feedback).toEqual(
          // Supplies this item to the surrounding call or collection.
          creatorGame!.attempts.at(-1)?.feedback,
          // Closes the expression, call, or declaration started above.
        );
        // Waits for this asynchronous operation to complete.
        await Promise.all([
          // Calls expect with the supplied values.
          expect(page.locator('.duel-layout .attempt-row')).toHaveCount(attemptNumber),
          // Calls expect with the supplied values.
          expect(opponent.locator('.duel-layout .attempt-row')).toHaveCount(attemptNumber),
          // Closes the expression, call, or declaration started above.
        ]);
        // Provides the candidates value to the surrounding call or element.
        candidates = narrowMastermindCandidates(
          // Supplies this item to the surrounding call or collection.
          candidates,
          // Supplies this item to the surrounding call or collection.
          guess!,
          // Supplies this item to the surrounding call or collection.
          creatorGame!.attempts.at(-1)!.feedback,
          // Closes the expression, call, or declaration started above.
        );
        // Calls expect with the supplied values.
        expect(candidates.length).toBeGreaterThan(0);
        // Closes the expression, call, or declaration started above.
      }

      // Calls expect with the supplied values.
      expect(creatorGame).not.toBeNull();
      // Calls expect with the supplied values.
      expect(opponentGame).not.toBeNull();
      // Calls expect with the supplied values.
      expect([creatorGame!.status, opponentGame!.status]).toContain('won');

      // Computes and stores finalCreatorRoom for subsequent operations.
      let finalCreatorRoom: RoomResponse | null = null;
      // Computes and stores finalOpponentRoom for subsequent operations.
      let finalOpponentRoom: RoomResponse | null = null;
      // Waits for this asynchronous operation to complete.
      await expect
        // Executes this line as the next step in the surrounding logic.
        .poll(
          // Begins the nested block or object completed below.
          async () => {
            // Executes this line as the next step in the surrounding logic.
            const [creatorResult, opponentResult] = await Promise.all([
              // Calls apiRequest with the supplied values.
              apiRequest(page, creatorSession.token, `/v1/rooms/${created.id}`),
              // Calls apiRequest with the supplied values.
              apiRequest(opponent, opponentSession.token, `/v1/rooms/${created.id}`),
              // Closes the expression, call, or declaration started above.
            ]);
            // Provides the finalCreatorRoom value to the surrounding call or element.
            finalCreatorRoom = (await creatorResult.json()) as RoomResponse;
            // Provides the finalOpponentRoom value to the surrounding call or element.
            finalOpponentRoom = (await opponentResult.json()) as RoomResponse;
            // Returns this result to the caller and ends the current function.
            return [finalCreatorRoom.status, finalOpponentRoom.status];
            // Closes the expression, call, or declaration started above.
          },
          // Supplies this item to the surrounding call or collection.
          { timeout: 10_000 },
          // Closes the expression, call, or declaration started above.
        )
        // Executes this line as the next step in the surrounding logic.
        .toEqual(['completed', 'completed']);

      // Calls expect with the supplied values.
      expect(finalOpponentRoom).toMatchObject({
        // Defines the status field in the surrounding object or type.
        status: finalCreatorRoom!.status,
        // Defines the winnerId field in the surrounding object or type.
        winnerId: finalCreatorRoom!.winnerId,
        // Defines the isTie field in the surrounding object or type.
        isTie: finalCreatorRoom!.isTie,
        // Closes the expression, call, or declaration started above.
      });
      // Calls expect with the supplied values.
      expect(finalCreatorRoom!.members.every((member) => member.completed)).toBe(true);
      // Calls expect with the supplied values.
      expect(finalOpponentRoom!.members.every((member) => member.completed)).toBe(true);

      // Executes this line as the next step in the surrounding logic.
      const [persistedCreatorResponse, persistedOpponentResponse] = await Promise.all([
        // Calls apiRequest with the supplied values.
        apiRequest(page, creatorSession.token, `/v1/games/${creatorGameId}`),
        // Calls apiRequest with the supplied values.
        apiRequest(opponent, opponentSession.token, `/v1/games/${opponentGameId}`),
        // Closes the expression, call, or declaration started above.
      ]);
      // Computes and stores persistedCreator for subsequent operations.
      const persistedCreator = (await persistedCreatorResponse.json()) as GameResponse;
      // Computes and stores persistedOpponent for subsequent operations.
      const persistedOpponent = (await persistedOpponentResponse.json()) as GameResponse;
      // Calls expect with the supplied values.
      expect(['won', 'lost']).toContain(persistedCreator.status);
      // Calls expect with the supplied values.
      expect(['won', 'lost']).toContain(persistedOpponent.status);

      // Checks this condition before running the nested branch.
      if (finalCreatorRoom!.isTie) {
        // Calls expect with the supplied values.
        expect(finalCreatorRoom!.winnerId).toBeNull();
        // Calls expect with the supplied values.
        expect([persistedCreator.status, persistedOpponent.status]).toEqual(['won', 'won']);
        // Handles the remaining unmatched case.
      } else {
        // Calls expect with the supplied values.
        expect([creatorSession.profile.id, opponentSession.profile.id]).toContain(
          // Supplies this item to the surrounding call or collection.
          finalCreatorRoom!.winnerId,
          // Closes the expression, call, or declaration started above.
        );
        // Calls expect with the supplied values.
        expect(persistedCreator.status).toBe(
          // Supplies this item to the surrounding call or collection.
          finalCreatorRoom!.winnerId === creatorSession.profile.id ? 'won' : 'lost',
          // Closes the expression, call, or declaration started above.
        );
        // Calls expect with the supplied values.
        expect(persistedOpponent.status).toBe(
          // Supplies this item to the surrounding call or collection.
          finalCreatorRoom!.winnerId === opponentSession.profile.id ? 'won' : 'lost',
          // Closes the expression, call, or declaration started above.
        );
        // Closes the expression, call, or declaration started above.
      }

      // Computes and stores creatorResult for subsequent operations.
      const creatorResult = finalCreatorRoom!.isTie
        ? // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          'The duel ended in a tie'
        : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          finalCreatorRoom!.winnerId === creatorSession.profile.id
          ? // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            'You won the duel'
          : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            'Your opponent won the duel';
      // Computes and stores opponentResult for subsequent operations.
      const opponentResult = finalCreatorRoom!.isTie
        ? // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          'The duel ended in a tie'
        : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          finalCreatorRoom!.winnerId === opponentSession.profile.id
          ? // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            'You won the duel'
          : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            'Your opponent won the duel';
      // Waits for this asynchronous operation to complete.
      await Promise.all([
        // Calls expect with the supplied values.
        expect(page.getByRole('heading', { name: creatorResult, exact: true })).toBeVisible({
          // Defines the timeout field in the surrounding object or type.
          timeout: 10_000,
          // Closes the expression, call, or declaration started above.
        }),
        // Calls expect with the supplied values.
        expect(opponent.getByRole('heading', { name: opponentResult, exact: true })).toBeVisible({
          // Defines the timeout field in the surrounding object or type.
          timeout: 10_000,
          // Closes the expression, call, or declaration started above.
        }),
        // Closes the expression, call, or declaration started above.
      ]);

      // Waits for this asynchronous operation to complete.
      await Promise.all([page.reload(), opponent.reload()]);
      // Waits for this asynchronous operation to complete.
      await Promise.all([
        // Calls expect with the supplied values.
        expect(page.getByRole('heading', { name: creatorResult, exact: true })).toBeVisible({
          // Defines the timeout field in the surrounding object or type.
          timeout: 15_000,
          // Closes the expression, call, or declaration started above.
        }),
        // Calls expect with the supplied values.
        expect(opponent.getByRole('heading', { name: opponentResult, exact: true })).toBeVisible({
          // Defines the timeout field in the surrounding object or type.
          timeout: 15_000,
          // Closes the expression, call, or declaration started above.
        }),
        // Closes the expression, call, or declaration started above.
      ]);
      // Waits for this asynchronous operation to complete.
      await expect(page.locator('.duel-layout .attempt-row')).toHaveCount(
        // Supplies this item to the surrounding call or collection.
        persistedCreator.attemptsUsed,
        // Closes the expression, call, or declaration started above.
      );
      // Waits for this asynchronous operation to complete.
      await expect(opponent.locator('.duel-layout .attempt-row')).toHaveCount(
        // Supplies this item to the surrounding call or collection.
        persistedOpponent.attemptsUsed,
        // Closes the expression, call, or declaration started above.
      );
      // Runs cleanup regardless of the protected result.
    } finally {
      // Waits for this asynchronous operation to complete.
      await opponentContext.close();
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
